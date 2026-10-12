"""Phase 5A deep finalists: 1M mix-weighted triggered bonuses + per-tier strata."""

from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, simulate_bonus
from skyjump_v2_phase5a_search import (
    BASE_BEFORE_FS,
    FULL_TARGET,
    LINE_RTP,
    BASE_FEATURE_CAPPED,
    OUT,
    SCREEN_CANDIDATES,
    build_candidate,
    base_trigger_mix,
    percentile,
    run_start_tier_batch,
)
from skyjump_v2_phase5a_reels import summarize_strips


FINALIST_IDS = [
    "FS5A_U3_P2_M40_mid_E32",
    "FS5A_U1_P2_M40_mid_E15j2",
    "FS5A_U2_P2_M40_mid_E15j2",
    "FS5A_U3_P2_M40_mid_E253",
    "FS5A_U3_P1_M40_mid_E32",
    "FS5A_U1_P2_M40_mid_E25j15",
]


def _sample_tier(rng: random.Random, conditional: dict) -> str:
    roll = rng.random()
    acc = 0.0
    for tier in TIERS:
        acc += conditional[tier]
        if roll <= acc:
            return tier
    return "PERFECT_V"


def run_mix_weighted(candidate, *, n: int, seed: int, config, paying, mix) -> dict:
    rng = random.Random(seed)
    awards = []
    spins = []
    upgrades = 0
    retriggers = 0
    reach = {tier: 0 for tier in TIERS}
    start_counts = {tier: 0 for tier in TIERS}
    no_coach = 0
    no_collector = 0
    below5 = 0
    below10 = 0
    gt15 = gt20 = gt30 = gt50 = 0
    max_spins = 0
    cap_hits = 0
    by_start = {tier: [] for tier in TIERS}

    for _ in range(n):
        start = _sample_tier(rng, mix["conditional"])
        start_counts[start] += 1
        result = simulate_bonus(
            rng, start, candidate, config=config, paying_candidate=paying
        )
        x = result["bonusWinXCapped"]
        awards.append(x)
        by_start[start].append(x)
        spins.append(result["freeSpinsPlayed"])
        max_spins = max(max_spins, result["freeSpinsPlayed"])
        if result["upgradeCount"] > 0:
            upgrades += 1
        if result["retriggerCount"] > 0:
            retriggers += 1
        for tier in result["stats"]["tiersVisited"]:
            reach[tier] += 1
        if not result["stats"]["hadCoach"]:
            no_coach += 1
        if not result["stats"]["hadCollector"]:
            no_collector += 1
        if x < 5:
            below5 += 1
        if x < 10:
            below10 += 1
        played = result["freeSpinsPlayed"]
        if played > 15:
            gt15 += 1
        if played > 20:
            gt20 += 1
        if played > 30:
            gt30 += 1
        if played > 50:
            gt50 += 1
        if result["maxWinReached"]:
            cap_hits += 1

    awards_sorted = sorted(awards)
    mean_x = sum(awards) / n

    def rate(threshold: float) -> float:
        return sum(1 for value in awards if value >= threshold) / n

    per_start_means = {
        tier: (sum(by_start[tier]) / len(by_start[tier]) if by_start[tier] else None)
        for tier in TIERS
    }
    return {
        "n": n,
        "seed": seed,
        "meanX": mean_x,
        "medianX": percentile(awards_sorted, 0.5),
        "meanMedianRatio": mean_x / percentile(awards_sorted, 0.5)
        if percentile(awards_sorted, 0.5)
        else None,
        "p25": percentile(awards_sorted, 0.25),
        "p75": percentile(awards_sorted, 0.75),
        "p90": percentile(awards_sorted, 0.90),
        "p95": percentile(awards_sorted, 0.95),
        "p99": percentile(awards_sorted, 0.99),
        "p999": percentile(awards_sorted, 0.999),
        "pGe": {
            "10": rate(10),
            "25": rate(25),
            "50": rate(50),
            "100": rate(100),
            "250": rate(250),
            "500": rate(500),
            "1000": rate(1000),
            "5000": rate(5000),
        },
        "pBelow5": below5 / n,
        "pBelow10": below10 / n,
        "meanSpins": sum(spins) / n,
        "pSpinsGt15": gt15 / n,
        "pSpinsGt20": gt20 / n,
        "pSpinsGt30": gt30 / n,
        "pSpinsGt50": gt50 / n,
        "maxSpinsObserved": max_spins,
        "pTierUpgrade": upgrades / n,
        "pRetrigger": retriggers / n,
        "pReach": {tier: reach[tier] / n for tier in TIERS},
        "pNoCoach": no_coach / n,
        "pNoCollector": no_collector / n,
        "pCap": cap_hits / n,
        "startCounts": start_counts,
        "perStartMeans": per_start_means,
        "fsRtpContribution": mean_x * mix["P_scatterGe3"],
        "fsRtpPp": mean_x * mix["P_scatterGe3"] * 100,
        "basePlusFs": BASE_BEFORE_FS + mean_x * mix["P_scatterGe3"],
        "futureReservePp": (FULL_TARGET - (BASE_BEFORE_FS + mean_x * mix["P_scatterGe3"]))
        * 100,
    }


def main():
    n_mix = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    n_tier = int(sys.argv[2]) if len(sys.argv) > 2 else 100_000
    ids = [a for a in sys.argv[3:] if not a.isdigit()] or FINALIST_IDS
    config = load_v2_config()
    paying = live_candidate_from_config(config)
    mix = base_trigger_mix(config)
    by_id = {spec[0]: spec for spec in SCREEN_CANDIDATES}
    rows = []
    for cid in ids:
        spec = by_id[cid]
        print(f"=== {cid} mix={n_mix} tier={n_tier} ===", flush=True)
        candidate = build_candidate(
            cid,
            upgrade=spec[1],
            max_persist=spec[2],
            max_spins=spec[3],
            families=spec[4],
            base_strips=config["reelModel"]["strips"],
            dup=spec[5],
            economy_id=spec[6],
        )
        reel_stats = {
            tier: summarize_strips(
                candidate.tierReels[tier], config["paylines"], config["paytable"]["awards"]
            )
            for tier in TIERS
        }
        t0 = time.perf_counter()
        mix_stats = run_mix_weighted(
            candidate, n=n_mix, seed=20260921, config=config, paying=paying, mix=mix
        )
        print(
            f"  mix weightedX={mix_stats['meanX']:.3f} fsPp={mix_stats['fsRtpPp']:.3f} "
            f"res={mix_stats['futureReservePp']:.3f} upg={mix_stats['pTierUpgrade']:.4f} "
            f"retrig={mix_stats['pRetrigger']:.4f} t={time.perf_counter()-t0:.1f}s",
            flush=True,
        )
        per_tier = {}
        for index, tier in enumerate(TIERS):
            per_tier[tier] = run_start_tier_batch(
                candidate,
                tier,
                n=n_tier,
                seed=20260921 + index * 100_003,
                config=config,
                paying=paying,
            )
            print(
                f"  {tier}: mean={per_tier[tier]['meanX']:.2f} med={per_tier[tier]['medianX']:.2f} "
                f"spins={per_tier[tier]['meanSpins']:.2f} upg={per_tier[tier]['pUpgrade']:.4f}",
                flush=True,
            )
        row = {
            "id": cid,
            "upgradeRule": spec[1],
            "maxPersistentTargets": spec[2],
            "maxFreeSpins": spec[3],
            "duplicateTargetBehaviour": spec[5],
            "economyId": spec[6],
            "families": spec[4],
            "mysteryWeights": candidate.mysteryResultWeights,
            "tokenValueScale": candidate.tokenValueScale,
            "reelStats": reel_stats,
            "mixWeighted": mix_stats,
            "perTier": per_tier,
            "budget": {
                "lineRtp": LINE_RTP,
                "baseFeatureCapped": BASE_FEATURE_CAPPED,
                "baseBeforeFs": BASE_BEFORE_FS,
                "fullTarget": FULL_TARGET,
            },
            "mix": mix,
            "nMix": n_mix,
            "nTier": n_tier,
        }
        path = OUT / f"finalist_{cid}_mix{n_mix}_tier{n_tier}.json"
        path.write_text(json.dumps(row, indent=2), encoding="utf-8")
        print("  wrote", path, flush=True)
        rows.append(row)
    summary_path = OUT / f"finalists_deep_mix{n_mix}.json"
    summary_path.write_text(json.dumps({"finalists": rows}, indent=2), encoding="utf-8")
    print("wrote", summary_path)


if __name__ == "__main__":
    main()
