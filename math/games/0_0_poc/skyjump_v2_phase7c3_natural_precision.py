"""Phase 7C.3 — large natural conditional MC until contribution SE target (LH-dominated)."""

from __future__ import annotations

import argparse
import math
import multiprocessing as mp
import random
import time
from pathlib import Path

from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import ConditionalBaseSampler, wr_off_config
from skyjump_v2_phase7c3_common import OUT, classify_bonus_row, dump_json, mean_se

P_LH = 0.0062135906602437665
TARGET_RTP_SE = 0.00050  # 0.05 pp


def _batch(args):
    leaf, seed0, n = args
    cfg = wr_off_config(load_v2_config())
    sampler = ConditionalBaseSampler(load_v2_config())
    xs = []
    bonus = []
    trig = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        stops = sampler.sample(rng, leaf)
        res = resolve_v2_round(rng, config=cfg, base_stops=stops)
        row = classify_bonus_row(res)
        xs.append(row["x"])
        bonus.append(row["bonusOnly"])
        trig.append(row["trig"])
    # Welford summaries to reduce memory
    def moments(vs):
        n_ = len(vs)
        mean = sum(vs) / n_
        m2 = sum((v - mean) ** 2 for v in vs)
        return n_, mean, m2

    return moments(xs), moments(bonus), moments(trig)


def combine(moments_list):
    # parallel combine of (n, mean, m2)
    n = 0
    mean = 0.0
    m2 = 0.0
    for n_a, mean_a, m2_a in moments_list:
        if n_a == 0:
            continue
        if n == 0:
            n, mean, m2 = n_a, mean_a, m2_a
            continue
        delta = mean_a - mean
        n_ab = n + n_a
        mean = (n * mean + n_a * mean_a) / n_ab
        m2 = m2 + m2_a + delta * delta * n * n_a / n_ab
        n = n_ab
    var = m2 / (n - 1) if n > 1 else 0.0
    se = math.sqrt(var / n) if n > 0 else float("inf")
    return {"n": n, "mean": mean, "se": se, "sd": math.sqrt(var) if n > 1 else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-n", type=int, default=3_000_000)
    ap.add_argument("--batch", type=int, default=25_000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=401)
    ap.add_argument("--leaf", default="BASE_TRIGGER_LH_WR_OFF")
    ap.add_argument("--p-start", type=float, default=P_LH)
    ap.add_argument("--target-rtp-se", type=float, default=TARGET_RTP_SE)
    ap.add_argument("--name", default="LH_NATURAL")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lh_strata").mkdir(exist_ok=True)

    t0 = time.time()
    mean_se_target = args.target_rtp_se / args.p_start
    xs_m = []
    b_m = []
    t_m = []
    done = 0
    round_i = 0
    while done < args.target_n:
        take = min(args.batch * args.workers, args.target_n - done)
        chunk = max(1, take // args.workers)
        jobs = []
        left = take
        w = 0
        while left > 0:
            n = min(chunk, left)
            jobs.append((args.leaf, args.seed + done + w * 100003 + round_i * 17, n))
            left -= n
            w += 1
        with mp.Pool(min(args.workers, len(jobs))) as pool:
            parts = pool.map(_batch, jobs)
        for xm, bm, tm in parts:
            xs_m.append(xm)
            b_m.append(bm)
            t_m.append(tm)
        done += take
        round_i += 1
        summary = combine(xs_m)
        rtp_se = summary["se"] * args.p_start
        print(
            f"{args.name} n={summary['n']} mean={summary['mean']:.4f} seX={summary['se']:.4f} "
            f"rtpSePp={rtp_se*100:.4f} targetSeX={mean_se_target:.4f} elapsed={time.time()-t0:.1f}s",
            flush=True,
        )
        if summary["se"] <= mean_se_target:
            print("TARGET MET", flush=True)
            break

    x = combine(xs_m)
    b = combine(b_m)
    tr = combine(t_m)
    out = {
        "name": args.name,
        "leaf": args.leaf,
        "pStart": args.p_start,
        "targetRtpSe": args.target_rtp_se,
        "meanXSeTarget": mean_se_target,
        "x": x,
        "bonusOnly": b,
        "trig": tr,
        "rtpContribution": x["mean"] * args.p_start,
        "rtpContributionSe": x["se"] * args.p_start,
        "passTarget": x["se"] <= mean_se_target * 1.02,
        "wallSeconds": time.time() - t0,
    }
    dump_json(OUT / "lh_strata" / f"{args.name}.json", out)
    print(
        f"DONE {args.name}: mean={x['mean']:.4f} se={x['se']:.4f} "
        f"rtpSePp={out['rtpContributionSe']*100:.4f} pass={out['passTarget']}",
        flush=True,
    )


if __name__ == "__main__":
    mp.freeze_support()
    main()
