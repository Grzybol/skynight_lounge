"""Phase 7C buy-mode EV + cost search (live resolver, no table retune)."""

from __future__ import annotations

import json
import math
import multiprocessing as mp
import random
import statistics
from pathlib import Path

from skyjump_v2_freespins import resolve_v2_buy_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_world_record import wr_probability

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c_research"
TIERS = ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
N_PER_TIER = 200_000
N_FILL = 5_000
TARGET_RTP = 0.965
RTP_LO = 0.964
RTP_HI = 0.966
CEILING = 0.967
COST_CANDIDATES_STEP = 0.1


def _chunk_buy(args):
    tier, seed0, n, force_wr = args
    cfg = load_v2_config()
    if force_wr:
        cfg = json.loads(json.dumps(cfg))
        cfg["worldRecord"]["byTierPSpin"] = {t: 1.0 for t in TIERS}
    rows = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        result = resolve_v2_buy_round(rng, config=cfg, start_tier=tier)
        rows.append(
            {
                "x": float(result["roundWinXCapped"]),
                "spins": int(result["bonus"]["freeSpinsPlayed"]),
                "cap": bool(result["bonus"]["maxWinReached"]),
                "wr": any(e.get("type") == "skyjumpWorldRecord" for e in result["events"]),
            }
        )
    return rows


def parallel_rows(tier: str, n: int, seed: int, *, force_wr: bool, workers: int = 8):
    chunk = max(1, n // workers)
    jobs = []
    done = 0
    w = 0
    while done < n:
        take = min(chunk, n - done)
        jobs.append((tier, seed + done * 1_000_003 + w * 17, take, force_wr))
        done += take
        w += 1
    with mp.Pool(processes=min(workers, len(jobs))) as pool:
        parts = pool.map(_chunk_buy, jobs)
    rows = []
    for part in parts:
        rows.extend(part)
    return rows


def pct(xs, p):
    if not xs:
        return 0.0
    ordered = sorted(xs)
    return ordered[min(len(ordered) - 1, int(p * (len(ordered) - 1)))]


def summarize(rows, *, wr_p: float, e_fill: float):
    xs = [r["x"] for r in rows]
    n = len(xs)
    mean = statistics.fmean(xs)
    # Rare WR almost never hits in natural MC — add analytical contribution
    mean_with_wr = mean + wr_p * e_fill
    var = statistics.pvariance(xs) if n > 1 else 0.0
    se = math.sqrt(var / n) if n else 0.0
    return {
        "n": n,
        "meanNaturalX": mean,
        "wrP": wr_p,
        "eFill": e_fill,
        "meanX": mean_with_wr,
        "se": se,
        "ci95": [mean_with_wr - 1.96 * se, mean_with_wr + 1.96 * se],
        "median": statistics.median(xs),
        "p75": pct(xs, 0.75),
        "p90": pct(xs, 0.90),
        "p95": pct(xs, 0.95),
        "p99": pct(xs, 0.99),
        "p99_9": pct(xs, 0.999),
        "pCap": sum(1 for r in rows if r["cap"]) / n,
        "pWrNatural": sum(1 for r in rows if r["wr"]) / n,
        "meanSpins": statistics.fmean(r["spins"] for r in rows),
    }


def estimate_wr_p(tier: str, rows, cfg) -> float:
    """Approx P(WR|buy start) from observed spin paths using live per-spin rates.

    Conservative: use start-tier rate × mean spins (upgrades raise rate — slight undercount).
    Better: re-sim with instrumentation; for pricing use start-tier × meanSpins upper-bound mix.
    """
    # Use geometric approximation with start tier only (slightly low for upgrade paths)
    p = wr_probability(cfg, tier)
    mean_spins = statistics.fmean(r["spins"] for r in rows) if rows else 10.0
    return 1.0 - (1.0 - p) ** mean_spins


def round_cost(ev: float, target: float = TARGET_RTP) -> list[dict]:
    raw = ev / target
    # Stake-friendly: prefer .0 / .5 endings, then 0.1 grain
    candidates = set()
    for base in (round(raw), round(raw * 2) / 2, round(raw, 1), math.floor(raw * 10) / 10, math.ceil(raw * 10) / 10):
        if base > 0:
            candidates.add(round(base, 1))
    # Expand nearby
    center = round(raw, 1)
    for d in range(-20, 21):
        c = round(center + d * 0.1, 1)
        if c > 0:
            candidates.add(c)
    ranked = []
    for cost in sorted(candidates):
        rtp = ev / cost
        ranked.append(
            {
                "cost": cost,
                "rtp": rtp,
                "rtpPct": rtp * 100.0,
                "inPreferred": RTP_LO <= rtp <= RTP_HI,
                "underCeiling": rtp <= CEILING,
                "distFromTargetPp": abs(rtp - target) * 100.0,
            }
        )
    ranked.sort(key=lambda r: (not r["underCeiling"], not r["inPreferred"], r["distFromTargetPp"]))
    return ranked


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_v2_config()
    # Fill expectation from forced WR (incremental ≈ fill-to-cap from 0)
    fills = {}
    for tier in TIERS:
        forced = parallel_rows(tier, N_FILL, 900_000 + hash(tier) % 10_000, force_wr=True, workers=8)
        fills[tier] = statistics.fmean(r["x"] for r in forced)
        print("fill", tier, fills[tier], flush=True)

    reports = {}
    for tier in TIERS:
        print("ev", tier, N_PER_TIER, flush=True)
        rows = parallel_rows(tier, N_PER_TIER, 800_000_000 + TIERS.index(tier) * 1_000_000, force_wr=False)
        wr_p = estimate_wr_p(tier, rows, cfg)
        e_fill = fills[tier]
        # When WR triggers from 0 accrued, incremental ≈ full round win under force
        # Natural mean already includes rare natural WR (~0); analytical add uses e_fill as incremental
        summary = summarize(rows, wr_p=wr_p, e_fill=e_fill)
        costs = round_cost(summary["meanX"])
        best = next((c for c in costs if c["inPreferred"] and c["underCeiling"]), costs[0])
        reports[tier] = {
            **summary,
            "costCandidates": costs[:12],
            "proposed": best,
        }
        print(
            tier,
            f"EV={summary['meanX']:.4f}",
            f"cost={best['cost']}",
            f"RTP={best['rtpPct']:.3f}%",
            flush=True,
        )

    # Cross-mode: pick jointly so spread <= 0.50 and all in band if possible
    chosen = {t: reports[t]["proposed"]["cost"] for t in TIERS}
    # Refine: search integer/0.5 costs near proposed jointly
    def rtp_map(costs):
        return {t: reports[t]["meanX"] / costs[t] for t in TIERS}

    rtps = rtp_map(chosen)
    spread = (max(rtps.values()) - min(rtps.values())) * 100.0

    # If spread too wide, nudge costs
    if spread > 0.50 or any(r > CEILING for r in rtps.values()) or any(r < RTP_LO for r in rtps.values()):
        # Scale costs so each hits TARGET_RTP exactly then round
        chosen = {t: round(reports[t]["meanX"] / TARGET_RTP, 1) for t in TIERS}
        rtps = rtp_map(chosen)
        spread = (max(rtps.values()) - min(rtps.values())) * 100.0

    out = {
        "nPerTier": N_PER_TIER,
        "nFill": N_FILL,
        "targetRtp": TARGET_RTP,
        "preferredBand": [RTP_LO, RTP_HI],
        "ceiling": CEILING,
        "tiers": reports,
        "chosenCosts": chosen,
        "chosenRtps": {t: rtps[t] * 100.0 for t in TIERS},
        "crossModeSpreadPp": spread,
        "crossModePass": spread <= 0.50 and all(r <= CEILING for r in rtps.values()),
    }
    (OUT / "buy_ev.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("chosenCosts", "chosenRtps", "crossModeSpreadPp", "crossModePass")}, indent=2))


if __name__ == "__main__":
    mp.freeze_support()
    main()
