"""Phase 7C.3 — hierarchical LH (also SF/WC) stratified conditional means.

Uses a large natural pilot for stratum probabilities, then rejection-oversamples
high-variance strata until allocated RTP contribution SE targets are met.
"""

from __future__ import annotations

import argparse
import math
import multiprocessing as mp
import random
import statistics
import time
from collections import defaultdict
from pathlib import Path

from skyjump_v2_freespins import resolve_v2_buy_round, resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import ConditionalBaseSampler, wr_off_config
from skyjump_v2_phase7c3_common import (
    LH_STRATA,
    OUT,
    buy_stratum_id,
    classify_bonus_row,
    dump_json,
    lh_stratum_id,
    mean_se,
)

# Paid-round start probs (exact mix; WR mass removed later at auth layer)
P_LH_START = 0.0062135906602437665
P_SF_START = 0.00030991400836999946
P_WC_START = 6.171610276639861e-06

# Contribution SE targets (absolute RTP fraction)
TARGET_LH_RTP_SE = 0.00050  # 0.05 pp
TARGET_SF_RTP_SE = 0.00020  # 0.02 pp
TARGET_WC_RTP_SE = 0.00010  # 0.01 pp

# Required mean-X SE for LH: TARGET / p
LH_MEAN_SE_TARGET = TARGET_LH_RTP_SE / P_LH_START  # ~0.0805


def _worker_base(args):
    leaf, seed0, n = args
    cfg = wr_off_config(load_v2_config())
    sampler = ConditionalBaseSampler(load_v2_config())
    out = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        stops = sampler.sample(rng, leaf)
        res = resolve_v2_round(rng, config=cfg, base_stops=stops)
        row = classify_bonus_row(res)
        row["stratum"] = lh_stratum_id(row)
        out.append(row)
    return out


def _worker_buy(args):
    tier, seed0, n = args
    cfg = wr_off_config(load_v2_config())
    out = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        res = resolve_v2_buy_round(rng, config=cfg, start_tier=tier)
        # buy: treat full round as bonus (trig=0)
        fake = {
            "bonus": res["bonus"],
            "roundWinXCapped": res["roundWinXCapped"],
            "triggerSpinWinX": 0.0,
            "spins": res.get("spins") or [],
            "events": res.get("events") or [],
        }
        row = classify_bonus_row(fake)
        row["stratum"] = buy_stratum_id(row)
        out.append(row)
    return out


def parallel_map(worker, jobs, workers: int):
    if not jobs:
        return []
    with mp.Pool(min(workers, len(jobs))) as pool:
        parts = pool.map(worker, jobs)
    rows = []
    for p in parts:
        rows.extend(p)
    return rows


def chunk_jobs(tag, seed, n, workers, leaf_or_tier):
    chunk = max(1, n // max(1, workers))
    jobs = []
    done = 0
    w = 0
    while done < n:
        take = min(chunk, n - done)
        jobs.append((leaf_or_tier, seed + done * 19 + w * 10007, take))
        done += take
        w += 1
    return jobs


def summarize_strata(rows: list[dict], value_key: str = "x") -> dict:
    by = defaultdict(list)
    for r in rows:
        by[r["stratum"]].append(float(r[value_key]))
    n = len(rows)
    out = {}
    for s in LH_STRATA:
        xs = by.get(s) or []
        m, se = mean_se(xs)
        out[s] = {
            "n": len(xs),
            "pHat": (len(xs) / n) if n else 0.0,
            "mean": m,
            "se": se if xs else float("inf"),
            "sd": statistics.stdev(xs) if len(xs) > 1 else 0.0,
        }
    # residual unknown keys
    for s, xs in by.items():
        if s in out:
            continue
        m, se = mean_se(xs)
        out[s] = {
            "n": len(xs),
            "pHat": len(xs) / n,
            "mean": m,
            "se": se,
            "sd": statistics.stdev(xs) if len(xs) > 1 else 0.0,
        }
    return {"n": n, "strata": out}


def stratified_estimate(p_hat: dict[str, float], means: dict[str, dict], se_p_n: int) -> dict:
    """E = sum p_s * mu_s with delta-method SE (independent mu oversamples approx)."""
    est = 0.0
    var = 0.0
    detail = {}
    for s, p in p_hat.items():
        mu_row = means.get(s) or {"mean": 0.0, "se": 0.0, "n": 0}
        mu = float(mu_row["mean"])
        se_mu = float(mu_row["se"]) if mu_row.get("n", 0) > 1 else 0.0
        est += p * mu
        # multinomial p SE (diagonal approx)
        se_p = math.sqrt(max(0.0, p * (1.0 - p) / max(1, se_p_n)))
        var += (mu * se_p) ** 2 + (p * se_mu) ** 2
        detail[s] = {
            "p": p,
            "mean": mu,
            "seMean": se_mu,
            "nMean": int(mu_row.get("n") or 0),
            "contrib": p * mu,
            "contribSe": math.sqrt((mu * se_p) ** 2 + (p * se_mu) ** 2),
        }
    se = math.sqrt(var)
    return {"mean": est, "se": se, "strata": detail}


def neyman_extra(p_hat: dict, sd_hat: dict, target_mean_se: float, already_n: dict, max_extra: int) -> dict[str, int]:
    """Allocate extra mean-samples only for rare/hot strata (rejection-friendly).

    Common cold strata keep pilot samples; oversampling them via rejection wastes draws.
    """
    # Only oversample high-variance / rare tails
    HOT = {"JUDGE_HOT", "BOTH_WARM", "BOTH_RJ2", "BOTH_GFM2P"}
    weights = {}
    for s, p in p_hat.items():
        if s not in HOT:
            continue
        sd = max(1e-9, float(sd_hat.get(s) or 0.0))
        weights[s] = max(p, 1e-6) * sd
    if not weights:
        return {s: 0 for s in p_hat}
    wsum = sum(weights.values()) or 1.0
    # Budget for hot-only Neyman piece of variance
    # Remaining var from cold ≈ sum_{cold} p^2 σ^2/n_pilot; allocate hot to finish target
    cold_var = 0.0
    for s, p in p_hat.items():
        if s in HOT:
            continue
        sd = float(sd_hat.get(s) or 0.0)
        n = max(1, int(already_n.get(s) or 1))
        cold_var += (p * sd / math.sqrt(n)) ** 2
    remain_se2 = max(0.0, target_mean_se**2 - cold_var)
    remain_se = math.sqrt(remain_se2) if remain_se2 > 0 else target_mean_se * 0.5
    need_n_total = (wsum / max(1e-12, remain_se)) ** 2
    out = {s: 0 for s in p_hat}
    for s, w in weights.items():
        ideal = int(math.ceil(need_n_total * (w / wsum)))
        have = int(already_n.get(s) or 0)
        floor = 800 if s == "BOTH_GFM2P" else 500
        want = max(floor, ideal)
        # Cap per-stratum to keep rejection feasible (n/p attempts)
        p = max(1e-6, float(p_hat.get(s) or 1e-6))
        max_by_cost = int(1_500_000 * p)  # at most ~1.5M attempts worth
        out[s] = max(0, min(want, max_by_cost) - have)
    total = sum(out.values())
    if total > max_extra and total > 0:
        scale = max_extra / total
        out = {s: int(math.floor(v * scale)) for s, v in out.items()}
    return out


def rejection_fill(worker, leaf_or_tier, targets: dict[str, int], seed: int, workers: int, mode: str):
    """Rejection-sample until each stratum reaches target counts (adaptive batches)."""
    have = defaultdict(list)
    remaining = {s: n for s, n in targets.items() if n > 0}
    attempts = 0
    batch = 8000
    round_i = 0
    t0 = time.time()
    while remaining and attempts < 8_000_000:
        jobs = chunk_jobs(mode, seed + round_i * 1_000_003, batch, workers, leaf_or_tier)
        rows = parallel_map(worker, jobs, workers)
        attempts += batch
        round_i += 1
        for r in rows:
            s = r["stratum"]
            if s in remaining and len(have[s]) < remaining[s]:
                have[s].append(r)
                if len(have[s]) >= remaining[s]:
                    del remaining[s]
        # shrink batch near the end
        need = sum(remaining.values())
        if need < batch // 2:
            batch = max(2000, need * 4)
        need_left = {s: max(0, remaining[s] - len(have[s])) for s in remaining}
        print(
            f"  rej {mode} attempts={attempts} need={need_left} elapsed={time.time()-t0:.1f}s",
            flush=True,
        )
        if not remaining:
            break
    filled = {s: list(have[s]) for s in targets}
    return filled, attempts, time.time() - t0


def run_mode(
    *,
    name: str,
    leaf: str | None,
    buy_tier: str | None,
    p_start: float,
    target_rtp_se: float,
    pilot_n: int,
    max_extra: int,
    seed: int,
    workers: int,
) -> dict:
    t0 = time.time()
    worker = _worker_base if leaf else _worker_buy
    key = leaf or buy_tier
    assert key
    print(f"=== {name} pilot n={pilot_n} ===", flush=True)
    jobs = chunk_jobs(name, seed, pilot_n, workers, key)
    pilot = parallel_map(worker, jobs, workers)
    pilot_sum = summarize_strata(pilot, "x")
    p_hat = {s: pilot_sum["strata"][s]["pHat"] for s in LH_STRATA}
    sd_hat = {s: pilot_sum["strata"][s]["sd"] for s in LH_STRATA}
    already = {s: pilot_sum["strata"][s]["n"] for s in LH_STRATA}
    mean_target = target_rtp_se / p_start
    extras = neyman_extra(p_hat, sd_hat, mean_target, already, max_extra=max_extra)
    print(f"  meanX SE target={mean_target:.5f} extras={extras}", flush=True)

    # Merge means: start from pilot, replace/extend with rejection fills
    means_rows = defaultdict(list)
    for r in pilot:
        means_rows[r["stratum"]].append(r)

    filled, attempts, rej_time = rejection_fill(worker, key, extras, seed + 9_000_000, workers, name)
    for s, rows in filled.items():
        # Always merge extras into pilot (never discard pilot mass)
        means_rows[s].extend(rows)

    mean_stats = {}
    for s in LH_STRATA:
        xs = [float(r["x"]) for r in means_rows[s]]
        bonus = [float(r["bonusOnly"]) for r in means_rows[s]]
        trig = [float(r["trig"]) for r in means_rows[s]]
        m, se = mean_se(xs)
        mb, seb = mean_se(bonus)
        mt, set_ = mean_se(trig)
        mean_stats[s] = {
            "n": len(xs),
            "mean": m,
            "se": se,
            "meanBonusOnly": mb,
            "seBonusOnly": seb,
            "meanTrig": mt,
            "seTrig": set_,
            "sd": statistics.stdev(xs) if len(xs) > 1 else 0.0,
            "pCap": (sum(1 for r in means_rows[s] if r["cap"]) / len(xs)) if xs else 0.0,
            "meanLength": statistics.mean([r["length"] for r in means_rows[s]]) if xs else 0.0,
        }

    est = stratified_estimate(p_hat, mean_stats, se_p_n=pilot_n)
    # Also report crude pilot mean for sanity
    crude_m, crude_se = mean_se([float(r["x"]) for r in pilot])
    trig_m, trig_se = mean_se([float(r["trig"]) for r in pilot])
    bonus_m, bonus_se = mean_se([float(r["bonusOnly"]) for r in pilot])

    out = {
        "name": name,
        "leaf": leaf,
        "buyTier": buy_tier,
        "pStart": p_start,
        "targetRtpSe": target_rtp_se,
        "meanXSeTarget": mean_target,
        "pilotN": pilot_n,
        "pilot": pilot_sum,
        "pHat": p_hat,
        "extrasRequested": extras,
        "rejectionAttempts": attempts,
        "rejectionSeconds": rej_time,
        "meanStats": mean_stats,
        "stratified": est,
        "crudePilot": {"meanX": crude_m, "seX": crude_se, "meanTrig": trig_m, "seTrig": trig_se, "meanBonus": bonus_m, "seBonus": bonus_se},
        "rtpContribution": est["mean"] * p_start,
        "rtpContributionSe": est["se"] * p_start,
        "wallSeconds": time.time() - t0,
        "passTarget": (est["se"] * p_start) <= target_rtp_se * 1.05,
    }
    dump_json(OUT / "lh_strata" / f"{name}.json", out)
    print(
        f"  {name}: meanX={est['mean']:.4f} seX={est['se']:.4f} "
        f"rtp={out['rtpContribution']*100:.4f}% ±{out['rtpContributionSe']*100:.4f}pp "
        f"pass={out['passTarget']} wall={out['wallSeconds']:.1f}s",
        flush=True,
    )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--lh-pilot", type=int, default=400_000)
    ap.add_argument("--sf-pilot", type=int, default=120_000)
    ap.add_argument("--wc-pilot", type=int, default=60_000)
    ap.add_argument("--lh-extra", type=int, default=120_000)
    ap.add_argument("--sf-extra", type=int, default=40_000)
    ap.add_argument("--wc-extra", type=int, default=20_000)
    ap.add_argument("--seed", type=int, default=73)
    ap.add_argument("--modes", default="LH,SF,WC")
    ap.add_argument("--log", default="")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lh_strata").mkdir(exist_ok=True)
    if args.log:
        import sys

        log_path = Path(args.log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_f = open(log_path, "w", encoding="utf-8")

        class Tee:
            def write(self, data):
                sys.__stdout__.write(data)
                log_f.write(data)
                log_f.flush()

            def flush(self):
                sys.__stdout__.flush()
                log_f.flush()

        sys.stdout = Tee()  # type: ignore
        sys.stderr = Tee()  # type: ignore

    results = {}
    if "LH" in args.modes:
        results["LH"] = run_mode(
            name="BASE_LH",
            leaf="BASE_TRIGGER_LH_WR_OFF",
            buy_tier=None,
            p_start=P_LH_START,
            target_rtp_se=TARGET_LH_RTP_SE,
            pilot_n=args.lh_pilot,
            max_extra=args.lh_extra,
            seed=args.seed,
            workers=args.workers,
        )
    if "SF" in args.modes:
        results["SF"] = run_mode(
            name="BASE_SF",
            leaf="BASE_TRIGGER_SF_WR_OFF",
            buy_tier=None,
            p_start=P_SF_START,
            target_rtp_se=TARGET_SF_RTP_SE,
            pilot_n=args.sf_pilot,
            max_extra=args.sf_extra,
            seed=args.seed + 100,
            workers=args.workers,
        )
    if "WC" in args.modes:
        results["WC"] = run_mode(
            name="BASE_WC",
            leaf="BASE_TRIGGER_WC_WR_OFF",
            buy_tier=None,
            p_start=P_WC_START,
            target_rtp_se=TARGET_WC_RTP_SE,
            pilot_n=args.wc_pilot,
            max_extra=args.wc_extra,
            seed=args.seed + 200,
            workers=args.workers,
        )
    dump_json(
        OUT / "base_trigger_strata.json",
        {
            "modes": {
                k: {
                    "meanX": v["stratified"]["mean"],
                    "seX": v["stratified"]["se"],
                    "rtpPp": v["rtpContribution"] * 100,
                    "rtpSePp": v["rtpContributionSe"] * 100,
                    "pass": v["passTarget"],
                    "wallSeconds": v["wallSeconds"],
                }
                for k, v in results.items()
            }
        },
    )
    print("DONE base trigger strata", flush=True)


if __name__ == "__main__":
    mp.freeze_support()
    main()
