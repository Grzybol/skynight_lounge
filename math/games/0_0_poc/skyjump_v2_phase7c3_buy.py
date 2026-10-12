"""Phase 7C.3 — high-precision buy EV / LUT + PRICE_A / PRICE_B design (no promotion)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import random
import statistics
import time
from collections import defaultdict
from pathlib import Path

import zstandard as zstd

from skyjump_v2_events import round_book_amount
from skyjump_v2_freespins import resolve_v2_buy_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import TIERS, wr_force_config, wr_off_config
from skyjump_v2_phase7c3_common import (
    LH_STRATA,
    OUT,
    WEIGHT_SCALE,
    assert_frozen,
    buy_stratum_id,
    ci95,
    classify_bonus_row,
    dump_json,
    mean_se,
    percentile,
)
from skyjump_v2_phase7c3_lh_strata import (
    chunk_jobs,
    neyman_extra,
    parallel_map,
    rejection_fill,
    stratified_estimate,
    summarize_strata,
    _worker_buy,
)
from skyjump_v2_world_record import wr_probability

LIB = Path(__file__).resolve().parent / "library_v2_phase7c3" / "publish_files"


def dist_stats(xs: list[float]) -> dict:
    n = len(xs)
    m, se = mean_se(xs)
    return {
        "n": n,
        "meanX": m,
        "se": se,
        "ci95": ci95(m, se),
        "median": percentile(xs, 50),
        "p75": percentile(xs, 75),
        "p90": percentile(xs, 90),
        "p95": percentile(xs, 95),
        "p99": percentile(xs, 99),
        "p999": percentile(xs, 99.9),
        "pCap": sum(1 for x in xs if x >= 50_000 - 1e-9) / n if n else 0.0,
    }


def certify_buy_tier(tier: str, pilot_n: int, max_extra: int, seed: int, workers: int) -> dict:
    t0 = time.time()
    print(f"=== BUY {tier} pilot={pilot_n} ===", flush=True)
    jobs = chunk_jobs(tier, seed, pilot_n, workers, tier)
    pilot = parallel_map(_worker_buy, jobs, workers)
    pilot_sum = summarize_strata(pilot, "x")
    p_hat = {s: pilot_sum["strata"][s]["pHat"] for s in LH_STRATA}
    sd_hat = {s: pilot_sum["strata"][s]["sd"] for s in LH_STRATA}
    already = {s: pilot_sum["strata"][s]["n"] for s in LH_STRATA}
    # Target SE on mean X so EV uncertainty is tight (≈0.15% relative or se<=0.4)
    target_se = max(0.25, 0.002 * max(1.0, pilot_sum["strata"]["NONE"]["mean"] + 1))
    # Better: aim se such that se/mean < 0.5% for pricing
    crude_m, crude_se = mean_se([r["x"] for r in pilot])
    # Pricing-grade SE: ~0.8% relative or absolute 0.35 on mean X
    target_se = max(0.35, 0.008 * crude_m)
    extras = neyman_extra(p_hat, sd_hat, target_se, already, max_extra=max_extra)
    print(f"  targetSe={target_se:.4f} extras={extras}", flush=True)

    means_rows = defaultdict(list)
    for r in pilot:
        means_rows[r["stratum"]].append(r)
    filled, attempts, rej_t = rejection_fill(_worker_buy, tier, extras, seed + 7_000_000, workers, f"BUY_{tier}")
    for s, rows in filled.items():
        means_rows[s].extend(rows)

    mean_stats = {}
    all_xs = []
    lengths = []
    caps = 0
    for s in LH_STRATA:
        xs = [float(r["x"]) for r in means_rows[s]]
        all_xs.extend(xs)
        lengths.extend([r["length"] for r in means_rows[s]])
        caps += sum(1 for r in means_rows[s] if r["cap"])
        m, se = mean_se(xs)
        mean_stats[s] = {"n": len(xs), "mean": m, "se": se, "sd": statistics.stdev(xs) if len(xs) > 1 else 0.0}

    est = stratified_estimate(p_hat, mean_stats, se_p_n=pilot_n)
    # Distribution from pilot (natural) for percentiles
    nat_xs = [float(r["x"]) for r in pilot]
    dist = dist_stats(nat_xs)
    # WR probability approx via mean length
    cfg = load_v2_config()
    mean_len = statistics.mean(lengths) if lengths else 10.0
    p_wr_spin = wr_probability(cfg, tier)
    p_wr = 1.0 - (1.0 - p_wr_spin) ** max(1.0, mean_len)

    out = {
        "tier": tier,
        "pilotN": pilot_n,
        "pHat": p_hat,
        "meanStats": mean_stats,
        "stratified": est,
        "crudePilot": {"meanX": crude_m, "seX": crude_se},
        "distributionNatural": dist,
        "meanBonusLength": mean_len,
        "pWrApprox": p_wr,
        "pCapStratified": caps / max(1, sum(mean_stats[s]["n"] for s in LH_STRATA)),
        "rejectionAttempts": attempts,
        "wallSeconds": time.time() - t0,
        "evX": est["mean"],
        "evSe": est["se"],
        "evCi95": ci95(est["mean"], est["se"]),
    }
    dump_json(OUT / "buy" / f"ev_{tier}.json", out)
    print(
        f"  BUY {tier}: EV={out['evX']:.4f} se={out['evSe']:.4f} "
        f"CI=[{out['evCi95'][0]:.2f},{out['evCi95'][1]:.2f}] wall={out['wallSeconds']:.1f}s",
        flush=True,
    )
    return out


def _buy_lut_sim(args):
    tier_, seed0, n = args
    cfg = wr_off_config(load_v2_config())
    out = []
    for i in range(n):
        r = resolve_v2_buy_round(random.Random(seed0 + i), config=cfg, start_tier=tier_)
        out.append(
            {
                "id": 0,
                "payoutMultiplier": round_book_amount(float(r["roundWinXCapped"])),
                "events": [{k: v for k, v in e.items() if k != "devSyntheticCapPrior"} for e in r["events"]],
                "criteria": "freegame",
                "mode": tier_,
                "x": float(r["roundWinXCapped"]),
            }
        )
    return out


def build_buy_lut(tier: str, ev: dict, n_nat: int, n_wr: int, seed: int, workers: int) -> dict:
    cfg0 = assert_frozen()
    jobs = chunk_jobs(tier, seed, n_nat, workers, tier)
    books = parallel_map(_buy_lut_sim, jobs, workers)
    # WR books
    wr_books = []
    cfg_wr = wr_force_config(cfg0)
    for i in range(n_wr):
        r = resolve_v2_buy_round(random.Random(seed + 50_000 + i), config=cfg_wr, start_tier=tier)
        wr_books.append(
            {
                "id": 0,
                "payoutMultiplier": round_book_amount(float(r["roundWinXCapped"])),
                "events": [{k: v for k, v in e.items() if k != "devSyntheticCapPrior"} for e in r["events"]],
                "criteria": "world_record",
                "mode": tier,
                "x": float(r["roundWinXCapped"]),
            }
        )

    p_wr = float(ev["pWrApprox"])
    p_nat = 1.0 - p_wr
    all_b = books + wr_books
    for i, b in enumerate(all_b, start=1):
        b["id"] = i
    w_nat = max(1, int(round(p_nat * WEIGHT_SCALE / max(1, len(books)))))
    w_wr = max(1, int(round(p_wr * WEIGHT_SCALE / max(1, len(wr_books)))))
    for b in books:
        b["weight"] = w_nat
    for b in wr_books:
        b["weight"] = w_wr

    mode_dir = LIB / tier.lower()
    mode_dir.mkdir(parents=True, exist_ok=True)
    books_path = mode_dir / "books.jsonl.zst"
    cctx = zstd.ZstdCompressor(level=3)
    with open(books_path, "wb") as f:
        with cctx.stream_writer(f) as compressor:
            for b in all_b:
                row = {k: v for k, v in b.items() if k not in {"x", "weight"}}
                compressor.write((json.dumps(row, separators=(",", ":")) + "\n").encode())
    lut_path = mode_dir / "lookUpTable.csv"
    scale = float(round_book_amount(1.0))
    with lut_path.open("w", encoding="utf-8") as f:
        for b in all_b:
            f.write(f"{b['id']},{b['weight']},{b['payoutMultiplier']}\n")

    total_w = sum(b["weight"] for b in all_b)
    lut_mean = sum(b["weight"] * (b["payoutMultiplier"] / scale) for b in all_b) / total_w
    auth_mean = (1.0 - p_wr) * float(ev["evX"]) + p_wr * 50_000.0
    mean_delta = abs(lut_mean - auth_mean)
    out = {
        "tier": tier,
        "lutMeanX": lut_mean,
        "authMeanX": auth_mean,
        "authWrOffMeanX": float(ev["evX"]),
        "pWr": p_wr,
        "meanDelta": mean_delta,
        "nNat": len(books),
        "nWr": len(wr_books),
        "shaBook": hashlib.sha256(books_path.read_bytes()).hexdigest(),
        "shaLut": hashlib.sha256(lut_path.read_bytes()).hexdigest(),
    }
    dump_json(OUT / "buy" / f"lut_{tier}.json", out)
    return out


def pricing(auth_base_pct: float, buy_ev: dict[str, dict]) -> dict:
    """PRICE_A: no BASE retune; costs so buy RTP within 0.50pp of BASE.
    PRICE_B: informational uplift to ~96.45% family.
    """
    # Prefer buys slightly above BASE: target_rtp = base + 0.25pp, clipped to ceiling-0.05
    base = auth_base_pct / 100.0
    ceiling = 0.9670
    spread_lim = 0.0050

    def costs_for_target(target_rtp: float) -> dict:
        out = {}
        for tier, ev in buy_ev.items():
            mean = float(ev["authMeanX"]) if "authMeanX" in ev else float(ev["evX"])
            # If auth includes WR:
            if "authMeanX" in ev:
                mean = float(ev["authMeanX"])
            else:
                mean = (1.0 - float(ev.get("pWrApprox") or 0.0)) * float(ev["evX"]) + float(ev.get("pWrApprox") or 0.0) * 50_000.0
            cost = mean / target_rtp
            # Round to 1 decimal clean
            cost_r = round(cost, 1)
            rtp = mean / cost_r
            out[tier] = {"cost": cost_r, "rtp": rtp, "rtpPct": rtp * 100, "meanX": mean}
        return out

    # PRICE_A: target near base+0.20pp but ensure max-min <=0.50pp including BASE
    target_a = min(ceiling - 0.0005, base + 0.0020)
    # Ensure target_a - base <= 0.50pp (always) and ceiling ok
    price_a = costs_for_target(target_a)
    rtps_a = [base] + [v["rtp"] for v in price_a.values()]
    spread_a = max(rtps_a) - min(rtps_a)

    # If any buy would exceed ceiling with clean cost, nudge cost up
    for tier, row in price_a.items():
        if row["rtp"] > ceiling:
            row["cost"] = round(row["meanX"] / (ceiling - 0.0003), 1)
            row["rtp"] = row["meanX"] / row["cost"]
            row["rtpPct"] = row["rtp"] * 100
    rtps_a = [base] + [v["rtp"] for v in price_a.values()]
    spread_a = max(rtps_a) - min(rtps_a)

    # PRICE_B informational: family at 96.45%
    target_b = 0.9645
    uplift_pp = (target_b - base) * 100
    price_b = costs_for_target(target_b)
    rtps_b = [target_b] + [v["rtp"] for v in price_b.values()]
    spread_b = max(rtps_b) - min(rtps_b)

    return {
        "PRICE_A": {
            "baseRtpPct": auth_base_pct,
            "targetBuyRtpPct": target_a * 100,
            "modes": price_a,
            "crossModeSpreadPp": spread_a * 100,
            "spreadPass": spread_a <= spread_lim + 1e-12,
            "ceilingPass": max(rtps_a) <= ceiling + 1e-12,
        },
        "PRICE_B": {
            "hypotheticalBaseTargetPct": target_b * 100,
            "requiredBaseUpliftPp": uplift_pp,
            "modes": price_b,
            "crossModeSpreadPp": spread_b * 100,
            "note": "Informational only — do not apply BASE uplift in 7C.3",
        },
    }


def wr_uplift_analysis(auth: dict) -> dict:
    wr_pp = float(auth["components"]["wrPp"])
    p = float(auth["pWr"])
    # To lift BASE to 96.45%: need delta = 96.45 - auth
    need = 96.45 - float(auth["authoritativeRtpPct"])
    # Extra WR contribution needed
    # contribution = p * 50000 * 100 (in pp) = p * 5e6
    # currently wr_pp; target wr_pp' = wr_pp + need
    target_wr_pp = wr_pp + max(0.0, need)
    target_p = target_wr_pp / (50_000.0 * 100.0) * 100.0  # wr_pp = p*50000*100 → p = wr_pp/(5e6)
    target_p = target_wr_pp / 5_000_000.0
    return {
        "currentContributionPp": wr_pp,
        "paidP": p,
        "oneInN": (1.0 / p) if p > 0 else None,
        "optionalUplift": {
            "targetBasePct": 96.45,
            "requiredUpliftPp": need,
            "targetWrContributionPp": target_wr_pp,
            "targetPaidP": target_p,
            "targetOneInN": (1.0 / target_p) if target_p > 0 else None,
            "aestheticNote": (
                "OK"
                if need <= 0.8
                else "WR-only uplift is large vs design intent — consider small BODY/paytable uplift instead (not applied)."
            ),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=113)
    ap.add_argument("--pilot", type=int, default=120_000)
    ap.add_argument("--extra", type=int, default=100_000)
    ap.add_argument("--skip-lut", action="store_true")
    args = ap.parse_args()
    (OUT / "buy").mkdir(parents=True, exist_ok=True)

    buy_ev = {}
    for i, tier in enumerate(TIERS):
        buy_ev[tier] = certify_buy_tier(tier, args.pilot, args.extra, args.seed + i * 1000, args.workers)

    lut = {}
    if not args.skip_lut:
        for i, tier in enumerate(TIERS):
            lut[tier] = build_buy_lut(tier, buy_ev[tier], n_nat=60_000, n_wr=20, seed=args.seed + 5000 + i, workers=args.workers)
            # RTP delta vs authority at PRICE_A cost later
            auth_mean = (1.0 - buy_ev[tier]["pWrApprox"]) * buy_ev[tier]["evX"] + buy_ev[tier]["pWrApprox"] * 50_000.0
            lut[tier]["authMeanX"] = auth_mean
            lut[tier]["meanDelta"] = abs(lut[tier]["lutMeanX"] - auth_mean)
            print(f"  LUT {tier}: lut={lut[tier]['lutMeanX']:.4f} auth={auth_mean:.4f} d={lut[tier]['meanDelta']:.4f}", flush=True)

    auth = json.loads((OUT / "base_authoritative.json").read_text(encoding="utf-8"))
    # Attach authMeanX onto buy for pricing
    buy_for_price = {}
    for tier, ev in buy_ev.items():
        buy_for_price[tier] = {
            **ev,
            "authMeanX": (1.0 - ev["pWrApprox"]) * ev["evX"] + ev["pWrApprox"] * 50_000.0,
        }
    prices = pricing(auth["authoritativeRtpPct"], buy_for_price)
    wr = wr_uplift_analysis(auth)

    # LUT RTP delta at PRICE_A costs
    lut_gate = {}
    for tier, row in lut.items():
        cost = prices["PRICE_A"]["modes"][tier]["cost"]
        auth_rtp = buy_for_price[tier]["authMeanX"] / cost
        lut_rtp = row["lutMeanX"] / cost
        dpp = abs(lut_rtp - auth_rtp) * 100
        lut_gate[tier] = {
            "cost": cost,
            "lutMean": row["lutMeanX"],
            "authMean": buy_for_price[tier]["authMeanX"],
            "rtpDeltaPp": dpp,
            "pass_0_05": dpp <= 0.05,
            "pass_0_03": dpp <= 0.03,
        }

    summary = {
        "buyEv": {t: {"evX": buy_ev[t]["evX"], "se": buy_ev[t]["evSe"], "ci95": buy_ev[t]["evCi95"],
                       "dist": buy_ev[t]["distributionNatural"], "meanLen": buy_ev[t]["meanBonusLength"],
                       "pWr": buy_ev[t]["pWrApprox"], "pCap": buy_ev[t]["pCapStratified"]} for t in TIERS},
        "buyLut": lut_gate,
        "pricing": prices,
        "wrUplift": wr,
    }
    dump_json(OUT / "buy_certification.json", summary)
    print(json.dumps({"PRICE_A_spreadPp": prices["PRICE_A"]["crossModeSpreadPp"], "PASS": prices["PRICE_A"]["spreadPass"]}, indent=2))


if __name__ == "__main__":
    mp.freeze_support()
    main()
