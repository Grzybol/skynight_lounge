"""Phase 7C.4 — converged buy-mode production libraries + cost search."""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import random
import time
from pathlib import Path

import zstandard as zstd

from skyjump_v2_events import round_book_amount
from skyjump_v2_freespins import resolve_v2_buy_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import TIERS, wr_force_config, wr_off_config
from skyjump_v2_phase7c3_common import buy_stratum_id, classify_bonus_row
from skyjump_v2_phase7c4_common import (
    CEILING,
    EXPECTED_SHA_PRE,
    LH_STRATA,
    OUT,
    PRICE_A_DESIGN,
    WEIGHT_SCALE,
    buy_auth_means,
    calibrate_weights,
    dump_json,
    load_authority,
    lut_rtp_from_rows,
    sha_file,
    weighted_mean,
)

HERE = Path(__file__).resolve().parent
LIB = HERE / "library_v2_phase7c4" / "publish_files"

N_NAT = {
    "LARGE_HILL": 120_000,
    "SKI_FLYING": 80_000,
    "WORLD_CUP": 60_000,
    "PERFECT_V": 60_000,
}
N_WR = 24


def payout_amount(win_x: float) -> int:
    amount = round_book_amount(win_x)
    if amount < 0 or win_x > 50_000 + 1e-9:
        raise ValueError(win_x)
    if amount > 0 and amount % 10 != 0:
        raise ValueError(amount)
    return amount


def _sim_buy(args):
    tier, seed0, n, force_wr = args
    cfg = load_v2_config()
    cfg = wr_force_config(cfg) if force_wr else wr_off_config(cfg)
    out = []
    for i in range(n):
        r = resolve_v2_buy_round(random.Random(seed0 + i), config=cfg, start_tier=tier)
        fake = {
            "bonus": r["bonus"],
            "roundWinXCapped": r["roundWinXCapped"],
            "triggerSpinWinX": 0.0,
            "spins": r.get("spins") or [],
            "events": r.get("events") or [],
        }
        row = classify_bonus_row(fake)
        out.append(
            {
                "id": 0,
                "payoutMultiplier": payout_amount(float(r["roundWinXCapped"])),
                "events": [{k: v for k, v in e.items() if k != "devSyntheticCapPrior"} for e in r["events"]],
                "criteria": "world_record" if force_wr else "freegame",
                "mode": tier,
                "baseGameWins": 0.0,
                "freeGameWins": round(float(r["roundWinXCapped"]), 4),
                "x": float(r["roundWinXCapped"]),
                "stratum": buy_stratum_id(row) if not force_wr else "WR",
            }
        )
    return out


def build_tier(tier: str, auth_mean: float, p_wr: float, workers: int, seed: int) -> dict:
    t0 = time.time()
    n = N_NAT[tier]
    print(f"=== BUY {tier} n={n} authMean={auth_mean:.4f} pWr={p_wr:.3e} ===", flush=True)
    chunk = max(1, n // workers)
    jobs = []
    done = 0
    w = 0
    while done < n:
        take = min(chunk, n - done)
        jobs.append((tier, seed + done * 17 + w, take, False))
        done += take
        w += 1
    with mp.Pool(min(workers, len(jobs))) as pool:
        parts = pool.map(_sim_buy, jobs)
    books = []
    for p in parts:
        books.extend(p)
    wr_books = []
    jobs_wr = [(tier, seed + 50_000 + i, 1, True) for i in range(N_WR)]
    with mp.Pool(min(workers, len(jobs_wr))) as pool:
        for p in pool.map(_sim_buy, jobs_wr):
            wr_books.extend(p)

    p_nat = 1.0 - p_wr
    # Split natural books by stratum; calibrate each to contribute to overall mean
    # Simpler: calibrate all natural books together to target_nat, WR exact 50000
    # Target natural mean so (1-p)*m_nat + p*50000 = auth_mean
    # => m_nat = (auth_mean - p*50000)/(1-p)
    target_nat = (auth_mean - p_wr * 50_000.0) / max(1e-15, p_nat)
    xs = [b["x"] for b in books]
    W_nat = max(len(books), int(round(p_nat * WEIGHT_SCALE)))
    ws = calibrate_weights(xs, target_nat, W_nat)
    for b, wt in zip(books, ws):
        b["weight"] = wt

    W_wr = max(len(wr_books), int(round(p_wr * WEIGHT_SCALE)))
    w_each = max(1, W_wr // len(wr_books))
    wr_ws = [w_each] * len(wr_books)
    wr_ws[-1] += W_wr - sum(wr_ws)
    for b, wt in zip(wr_books, wr_ws):
        b["weight"] = wt

    all_b = books + wr_books
    # Fix total weight to WEIGHT_SCALE
    tw = sum(int(b["weight"]) for b in all_b)
    if tw != WEIGHT_SCALE:
        diff = WEIGHT_SCALE - tw
        for b in all_b:
            if b["criteria"] == "freegame" and b["weight"] + diff > 0:
                b["weight"] += diff
                break

    for i, b in enumerate(all_b, start=1):
        b["id"] = i

    mode_dir = LIB
    mode_dir.mkdir(parents=True, exist_ok=True)
    books_path = mode_dir / f"books_{tier}.jsonl.zst"
    lut_path = mode_dir / f"lookUpTable_{tier}_0.csv"
    cctx = zstd.ZstdCompressor(level=3)
    with open(books_path, "wb") as f:
        with cctx.stream_writer(f) as zw:
            for b in all_b:
                row = {k: v for k, v in b.items() if k not in {"x", "weight", "stratum"}}
                zw.write((json.dumps(row, separators=(",", ":")) + "\n").encode())
    with lut_path.open("w", encoding="utf-8") as f:
        for b in all_b:
            f.write(f"{b['id']},{b['weight']},{b['payoutMultiplier']}\n")

    scale = float(round_book_amount(1.0))
    xs_all = [b["payoutMultiplier"] / scale for b in all_b]
    ws_all = [int(b["weight"]) for b in all_b]
    lut_mean = lut_rtp_from_rows(xs_all, ws_all)
    # Path B from CSV
    num = den = 0.0
    with lut_path.open(encoding="utf-8") as f:
        for line in f:
            _, w_s, pay_s = line.strip().split(",")
            w = int(w_s)
            num += w * (int(pay_s) / scale)
            den += w
    lut_mean_b = num / den if den else 0.0

    out = {
        "tier": tier,
        "authMeanFinal": auth_mean,
        "targetNatMean": target_nat,
        "pWr": p_wr,
        "lutMean": lut_mean,
        "lutMeanPathB": lut_mean_b,
        "meanDelta": abs(lut_mean - auth_mean),
        "nNat": len(books),
        "nWr": len(wr_books),
        "bookCount": len(all_b),
        "rawNatMean": sum(xs) / len(xs),
        "weightedNatMean": weighted_mean(xs, ws),
        "shaBook": sha_file(books_path),
        "shaLut": sha_file(lut_path),
        "paths": {"books": str(books_path), "lut": str(lut_path)},
        "wallSeconds": time.time() - t0,
        "dualPathMatch": abs(lut_mean - lut_mean_b) < 1e-12,
    }
    dump_json(OUT / f"buy_{tier}_lut.json", out)
    print(
        f"  lutMean={lut_mean:.4f} auth={auth_mean:.4f} delta={out['meanDelta']:.4f} "
        f"dual={out['dualPathMatch']} wall={out['wallSeconds']:.1f}s",
        flush=True,
    )
    return out


def search_costs(buy_means: dict[str, float], base_rtp: float) -> dict:
    """PRICE_A grain search from design costs; adjust only if needed for gates."""
    costs = dict(PRICE_A_DESIGN)
    # Compute RTP at costs using auth means (LUT will match closely after calibration)
    def rtps(cs):
        return {t: buy_means[t] / cs[t] for t in TIERS}

    def ok(cs):
        r = rtps(cs)
        vals = [base_rtp] + list(r.values())
        if any(v > CEILING + 1e-15 for v in vals):
            return False
        if max(vals) - min(vals) > 0.005 + 1e-15:
            return False
        return True

    # Nudge costs up while RTP exceeds ceiling
    for t in TIERS:
        while buy_means[t] / costs[t] > CEILING + 1e-15:
            costs[t] = round(costs[t] + 0.1, 1)

    # Prefer spread <=0.20pp; if fail, nudge high-RTP modes' costs up
    for _ in range(50):
        r = rtps(costs)
        vals = [base_rtp] + list(r.values())
        spread = max(vals) - min(vals)
        if spread <= 0.002000001 and max(vals) <= CEILING + 1e-15:
            break
        # raise cost of max mode among buys
        hot = max(TIERS, key=lambda t: r[t])
        costs[hot] = round(costs[hot] + 0.1, 1)

    r = rtps(costs)
    vals = [base_rtp] + list(r.values())
    return {
        "costs": costs,
        "rtp": {t: r[t] for t in TIERS},
        "rtpPct": {t: r[t] * 100 for t in TIERS},
        "baseRtp": base_rtp,
        "baseRtpPct": base_rtp * 100,
        "min": min(vals),
        "max": max(vals),
        "spreadPp": (max(vals) - min(vals)) * 100,
        "spreadPass": (max(vals) - min(vals)) <= 0.005000001,
        "ceilingPass": max(vals) <= CEILING + 1e-15,
        "preferredSpreadPass": (max(vals) - min(vals)) <= 0.002000001,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7411)
    args = ap.parse_args()
    mp.freeze_support()
    assert sha_file(HERE / "skyjump_v2_config.json") == EXPECTED_SHA_PRE

    auth_pack = load_authority()
    means = buy_auth_means(auth_pack["buy"])
    dump_json(OUT / "buy_auth_means.json", means)

    # BASE actual RTP if available
    base_report_path = OUT / "base_lut_report.json"
    if base_report_path.exists():
        base_rtp = float(json.loads(base_report_path.read_text(encoding="utf-8"))["actualLutRtp"])
    else:
        base_rtp = float(auth_pack["base"]["authoritativeRtp"])

    reports = {}
    for i, tier in enumerate(TIERS):
        reports[tier] = build_tier(
            tier,
            means[tier]["authMeanFinal"],
            means[tier]["pWr"],
            args.workers,
            args.seed + i * 1000,
        )

    # Cost search using actual LUT means for final RTP
    buy_lut_means = {t: reports[t]["lutMean"] for t in TIERS}
    pricing = search_costs(buy_lut_means, base_rtp)

    # Gates vs authority-at-cost
    gates = {}
    for t in TIERS:
        cost = pricing["costs"][t]
        auth_rtp = means[t]["authMeanFinal"] / cost
        lut_rtp = reports[t]["lutMean"] / cost
        dpp = abs(lut_rtp - auth_rtp) * 100
        gates[t] = {
            "cost": cost,
            "authRtpPct": auth_rtp * 100,
            "lutRtpPct": lut_rtp * 100,
            "gapPp": dpp,
            "pass_0_05": dpp <= 0.05,
            "pass_0_03": dpp <= 0.03,
            "ceilingPass": lut_rtp <= CEILING + 1e-15,
        }

    # Recalculate cross-mode from actual LUT RTPs at frozen costs
    actual_rtps = {"BASE": base_rtp}
    for t in TIERS:
        actual_rtps[t] = reports[t]["lutMean"] / pricing["costs"][t]
    vals = list(actual_rtps.values())
    cross = {
        "rtpPct": {k: v * 100 for k, v in actual_rtps.items()},
        "min": min(vals) * 100,
        "max": max(vals) * 100,
        "spreadPp": (max(vals) - min(vals)) * 100,
        "spreadPass": (max(vals) - min(vals)) <= 0.005000001,
        "preferredSpreadPass": (max(vals) - min(vals)) <= 0.002000001,
        "ceilingPass": max(vals) <= CEILING + 1e-15,
    }

    summary = {
        "buyAuthMeans": means,
        "lutReports": {t: {k: reports[t][k] for k in reports[t] if k != "paths"} for t in TIERS},
        "pricing": pricing,
        "gates": gates,
        "crossModeActual": cross,
        "allGatesPass": all(g["pass_0_05"] and g["ceilingPass"] for g in gates.values())
        and cross["spreadPass"]
        and cross["ceilingPass"],
    }
    dump_json(OUT / "buy_lut_report.json", summary)
    print(json.dumps({"costs": pricing["costs"], "cross": cross, "allPass": summary["allGatesPass"]}, indent=2))


if __name__ == "__main__":
    main()
