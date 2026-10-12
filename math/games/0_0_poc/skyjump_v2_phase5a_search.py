"""Phase 5A Free Spin candidate search + Monte Carlo screening."""

from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path

from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, BonusCandidate, base_trigger_mix, simulate_bonus
from skyjump_v2_phase5a_reels import materialize_family, summarize_strips

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase5a_research"
OUT.mkdir(exist_ok=True)

LIVE_HASH = "d932065b36a626c7cd9a818bd8c401559e6270c434622d32d1fb640e3d8d7803"
LINE_RTP = 0.596962
BASE_FEATURE_CAPPED = 0.11516
BASE_BEFORE_FS = LINE_RTP + BASE_FEATURE_CAPPED
FULL_TARGET = 0.9650

BASE_MYSTERY = {
    "FLIGHT_TOKEN": 855,
    "THERMAL_LIFT": 42,
    "GATE_UPGRADE": 3,
    "JUDGE": 85,
    "HEAD_JUDGE": 15,
}


def boost_collectors(mult_j: float, mult_hj: float, mult_g: float = 1.0) -> dict[str, int]:
    weights = dict(BASE_MYSTERY)
    weights["JUDGE"] = max(1, int(round(weights["JUDGE"] * mult_j)))
    weights["HEAD_JUDGE"] = max(1, int(round(weights["HEAD_JUDGE"] * mult_hj)))
    weights["GATE_UPGRADE"] = max(1, int(round(weights["GATE_UPGRADE"] * mult_g)))
    other = (
        weights["THERMAL_LIFT"]
        + weights["GATE_UPGRADE"]
        + weights["JUDGE"]
        + weights["HEAD_JUDGE"]
    )
    weights["FLIGHT_TOKEN"] = max(100, 1000 - other)
    return weights


ECONOMY_PROFILES = {
    "E_s3_j3": {"tokenValueScale": 3.0, "mysteryResultWeights": boost_collectors(3, 3, 3)},
    "E_s3_j2": {"tokenValueScale": 3.0, "mysteryResultWeights": boost_collectors(2, 2, 2)},
    "E_s35_j3": {"tokenValueScale": 3.5, "mysteryResultWeights": boost_collectors(3, 3, 3)},
    "E_s25_j3": {"tokenValueScale": 2.5, "mysteryResultWeights": boost_collectors(3, 3, 2)},
    "E_s4_j2": {"tokenValueScale": 4.0, "mysteryResultWeights": boost_collectors(2, 2, 2)},
    "E_s15_j2": {"tokenValueScale": 1.5, "mysteryResultWeights": boost_collectors(2, 2, 2)},
    "E_s25_j15": {"tokenValueScale": 2.5, "mysteryResultWeights": boost_collectors(1.5, 1.5, 2)},
}

def percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def run_start_tier_batch(
    candidate: BonusCandidate,
    start_tier: str,
    *,
    n: int,
    seed: int,
    config: dict,
    paying: dict,
) -> dict:
    rng = random.Random(seed)
    awards: list[float] = []
    spins: list[int] = []
    upgrades = 0
    reach = {tier: 0 for tier in TIERS}
    no_coach = 0
    no_collector = 0
    below5 = 0
    below10 = 0
    gt15 = 0
    gt20 = 0
    gt30 = 0
    gt50 = 0
    max_spins = 0
    cap_hits = 0
    floor_sum = {"1": 0.0, "5": 0.0, "10": 0.0, "end": 0.0}
    persist_sum = {"1": 0.0, "5": 0.0, "10": 0.0, "end": 0.0}
    floor_n = {"1": 0, "5": 0, "10": 0, "end": 0}
    line_sum = 0.0
    feat_sum = 0.0
    mystery_sum = 0.0
    coach_spins = 0
    total_spins = 0
    p_judge = 0
    p_hj = 0
    p_gate = 0
    p_therm = 0

    for _ in range(n):
        result = simulate_bonus(
            rng,
            start_tier,
            candidate,
            config=config,
            paying_candidate=paying,
            round_prior_win_x=0.0,
        )
        x = result["bonusWinXCapped"]
        awards.append(x)
        spins.append(result["freeSpinsPlayed"])
        max_spins = max(max_spins, result["freeSpinsPlayed"])
        if result["upgradeCount"] > 0:
            upgrades += 1
        for tier in result["stats"]["tiersVisited"]:
            if tier in reach:
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
        for key in ("1", "5", "10", "end"):
            if key in result["stats"]["floorAt"]:
                floor_sum[key] += result["stats"]["floorAt"][key]
                floor_n[key] += 1
            if key in result["stats"]["persistAt"]:
                persist_sum[key] += result["stats"]["persistAt"][key]
        line_sum += result["stats"]["lineSum"]
        feat_sum += result["stats"]["featureSum"]
        mystery_sum += result["stats"]["mysteries"]
        total_spins += played
        if result["stats"]["judges"]:
            p_judge += 1
        if result["stats"]["headJudges"]:
            p_hj += 1
        if result["stats"]["gates"]:
            p_gate += 1
        if result["stats"]["thermals"]:
            p_therm += 1
        if result["stats"]["coaches"]:
            coach_spins += 1

    awards_sorted = sorted(awards)
    mean_x = sum(awards) / n
    median_x = percentile(awards_sorted, 0.5)
    mean_spins = sum(spins) / n

    def rate(threshold: float) -> float:
        return sum(1 for value in awards if value >= threshold) / n

    return {
        "n": n,
        "seed": seed,
        "startTier": start_tier,
        "meanX": mean_x,
        "medianX": median_x,
        "meanMedianRatio": mean_x / median_x if median_x > 0 else None,
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
        "meanSpins": mean_spins,
        "pSpinsGt15": gt15 / n,
        "pSpinsGt20": gt20 / n,
        "pSpinsGt30": gt30 / n,
        "pSpinsGt50": gt50 / n,
        "maxSpinsObserved": max_spins,
        "pUpgrade": upgrades / n,
        "pReach": {tier: reach[tier] / n for tier in TIERS},
        "pNoCoach": no_coach / n,
        "pNoCollector": no_collector / n,
        "pCap": cap_hits / n,
        "avgLinePerBonus": line_sum / n,
        "avgFeaturePerBonus": feat_sum / n,
        "avgLinePerSpin": line_sum / total_spins if total_spins else 0,
        "avgFeaturePerSpin": feat_sum / total_spins if total_spins else 0,
        "avgMysteriesPerSpin": mystery_sum / total_spins if total_spins else 0,
        "pBonusHadJudge": p_judge / n,
        "pBonusHadHeadJudge": p_hj / n,
        "pBonusHadGate": p_gate / n,
        "pBonusHadThermal": p_therm / n,
        "avgFloor": {k: (floor_sum[k] / floor_n[k] if floor_n[k] else None) for k in floor_sum},
        "avgPersist": {
            k: (persist_sum[k] / floor_n[k] if floor_n.get(k) else None) for k in persist_sum
        },
    }


def weighted_summary(per_tier: dict, mix: dict) -> dict:
    abs_p = mix["absolute"]
    p_ge3 = mix["P_scatterGe3"]
    weighted_x = 0.0
    for tier in TIERS:
        weighted_x += abs_p[tier] * per_tier[tier]["meanX"]
    # FS RTP = sum P(trigger_i) * EV(bonus_i)  — absolute paid-spin probability
    fs_rtp = weighted_x  # since abs_p already absolute; wait: abs_p sums to p_ge3
    # Correct: FS_RTP = Σ P(trigger_i) × EV(bonus_i) where P is absolute over paid spins
    # weighted_x above IS that sum.
    # Conditional average bonus given trigger:
    cond_avg = sum(mix["conditional"][tier] * per_tier[tier]["meanX"] for tier in TIERS)
    return {
        "weightedAverageBonusX_givenTrigger": cond_avg,
        "fsRtpContribution": fs_rtp,
        "fsRtpPp": fs_rtp * 100,
        "basePlusFs": BASE_BEFORE_FS + fs_rtp,
        "futureReservePp": (FULL_TARGET - (BASE_BEFORE_FS + fs_rtp)) * 100,
    }


def build_candidate(
    cid: str,
    *,
    upgrade: str,
    max_persist: int,
    max_spins: int,
    families: dict[str, str],
    base_strips,
    dup: str = "B",
    economy_id: str = "E_s3_j3",
) -> BonusCandidate:
    tier_reels = {tier: materialize_family(base_strips, families[tier]) for tier in TIERS}
    eco = ECONOMY_PROFILES[economy_id]
    return BonusCandidate(
        id=cid,
        upgradeRule=upgrade,
        initialSpins=10,
        maxFreeSpins=max_spins,
        maxPersistentTargets=max_persist,
        duplicateTargetBehaviour=dup,
        tierReels=tier_reels,
        mysteryResultWeights=eco["mysteryResultWeights"],
        tokenValueScale=eco["tokenValueScale"],
    )


def score_candidate(weighted: dict, lh: dict) -> float:
    """Lower is better."""
    target = 32.5
    err = abs(weighted["weightedAverageBonusX_givenTrigger"] - target)
    reserve = weighted["futureReservePp"]
    reserve_pen = 0.0
    if reserve < 3.0:
        reserve_pen += (3.0 - reserve) * 2
    if reserve > 8.0:
        reserve_pen += (reserve - 8.0) * 0.5
    feel_pen = 0.0
    if lh["pBelow5"] > 0.35:
        feel_pen += (lh["pBelow5"] - 0.35) * 20
    if lh["meanMedianRatio"] and lh["meanMedianRatio"] > 3.5:
        feel_pen += (lh["meanMedianRatio"] - 3.5) * 4
    if lh["pNoCoach"] > 0.20:
        feel_pen += (lh["pNoCoach"] - 0.20) * 15
    if lh["pUpgrade"] < 0.06:
        feel_pen += (0.06 - lh["pUpgrade"]) * 40
    if lh["pUpgrade"] > 0.35:
        feel_pen += (lh["pUpgrade"] - 0.35) * 10
    if lh["pSpinsGt30"] > 0.05:
        feel_pen += lh["pSpinsGt30"] * 20
    progress_pen = 0.0
    if lh["pReach"]["SKI_FLYING"] < 0.05:
        progress_pen += (0.05 - lh["pReach"]["SKI_FLYING"]) * 40
    return err + reserve_pen + feel_pen + progress_pen


MID_FAM = {
    "LARGE_HILL": "LH_C2_Smid",
    "SKI_FLYING": "SF_C3_Smid",
    "WORLD_CUP": "WC_C4_Smid",
    "PERFECT_V": "PV_C5_Smid",
}
HOT_FAM = {
    "LARGE_HILL": "LH_C2_Shot",
    "SKI_FLYING": "SF_C3_Shot",
    "WORLD_CUP": "WC_C4_Shot",
    "PERFECT_V": "PV_C6_Shot",
}

# id, upgrade, max_persist, max_spins, families, dup, economy_id
SCREEN_CANDIDATES = [
    ("FS5A_U3_P2_M40_mid_E33", "U3", 2, 40, MID_FAM, "B", "E_s3_j3"),
    ("FS5A_U3_P2_M40_mid_E32", "U3", 2, 40, MID_FAM, "B", "E_s3_j2"),
    ("FS5A_U3_P2_M40_mid_E353", "U3", 2, 40, MID_FAM, "B", "E_s35_j3"),
    ("FS5A_U3_P2_M40_mid_E253", "U3", 2, 40, MID_FAM, "B", "E_s25_j3"),
    ("FS5A_U3_P2_M40_hot_E33", "U3", 2, 40, HOT_FAM, "B", "E_s3_j3"),
    ("FS5A_U3_P2_M40_hot_E32", "U3", 2, 40, HOT_FAM, "B", "E_s3_j2"),
    ("FS5A_U1_P2_M40_mid_E33", "U1", 2, 40, MID_FAM, "B", "E_s3_j3"),
    ("FS5A_U1_P2_M40_mid_E32", "U1", 2, 40, MID_FAM, "B", "E_s3_j2"),
    ("FS5A_U2_P2_M40_mid_E33", "U2", 2, 40, MID_FAM, "B", "E_s3_j3"),
    ("FS5A_U2_P2_M40_mid_E32", "U2", 2, 40, MID_FAM, "B", "E_s3_j2"),
    ("FS5A_U3_P1_M40_mid_E33", "U3", 1, 40, MID_FAM, "B", "E_s3_j3"),
    ("FS5A_U3_P1_M40_mid_E32", "U3", 1, 40, MID_FAM, "B", "E_s3_j2"),
    ("FS5A_U3_P3_M40_mid_E33", "U3", 3, 40, MID_FAM, "B", "E_s3_j3"),
    ("FS5A_U3_P3_M40_mid_E32", "U3", 3, 40, MID_FAM, "B", "E_s3_j2"),
    ("FS5A_U3_P2_M30_mid_E33", "U3", 2, 30, MID_FAM, "B", "E_s3_j3"),
    ("FS5A_U3_P2_M50_mid_E33", "U3", 2, 50, MID_FAM, "B", "E_s3_j3"),
    ("FS5A_U3_P2_M40_dupA_E33", "U3", 2, 40, MID_FAM, "A", "E_s3_j3"),
    ("FS5A_U3_P2_M40_dupA_E32", "U3", 2, 40, MID_FAM, "A", "E_s3_j2"),
    (
        "FS5A_U3_P2_M40_r124_E33",
        "U3",
        2,
        40,
        {
            "LARGE_HILL": "LH_C2r124_Smid",
            "SKI_FLYING": "SF_C3_Smid",
            "WORLD_CUP": "WC_C4_Smid",
            "PERFECT_V": "PV_C5_Smid",
        },
        "B",
        "E_s3_j3",
    ),
    ("FS5A_U3_P2_M40_mid_E42", "U3", 2, 40, MID_FAM, "B", "E_s4_j2"),
    ("FS5A_U1_P2_M40_mid_E15j2", "U1", 2, 40, MID_FAM, "B", "E_s15_j2"),
    ("FS5A_U2_P2_M40_mid_E15j2", "U2", 2, 40, MID_FAM, "B", "E_s15_j2"),
    ("FS5A_U1_P2_M40_mid_E25j15", "U1", 2, 40, MID_FAM, "B", "E_s25_j15"),
]


def evaluate_candidate(spec, *, n_per_tier: int, seed: int, config, paying, mix) -> dict:
    cid, upgrade, max_persist, max_spins, families, dup, economy_id = spec
    candidate = build_candidate(
        cid,
        upgrade=upgrade,
        max_persist=max_persist,
        max_spins=max_spins,
        families=families,
        base_strips=config["reelModel"]["strips"],
        dup=dup,
        economy_id=economy_id,
    )
    reel_stats = {
        tier: summarize_strips(
            candidate.tierReels[tier], config["paylines"], config["paytable"]["awards"]
        )
        for tier in TIERS
    }
    per_tier = {}
    t0 = time.perf_counter()
    for index, tier in enumerate(TIERS):
        per_tier[tier] = run_start_tier_batch(
            candidate,
            tier,
            n=n_per_tier,
            seed=seed + index * 100_003,
            config=config,
            paying=paying,
        )
    elapsed = time.perf_counter() - t0
    weighted = weighted_summary(per_tier, mix)
    lh = per_tier["LARGE_HILL"]
    return {
        "id": cid,
        "upgradeRule": upgrade,
        "maxPersistentTargets": max_persist,
        "maxFreeSpins": max_spins,
        "duplicateTargetBehaviour": dup,
        "economyId": economy_id,
        "families": families,
        "reelStats": reel_stats,
        "perTier": per_tier,
        "weighted": weighted,
        "score": score_candidate(weighted, lh),
        "elapsedSec": elapsed,
        "nPerTier": n_per_tier,
        "seed": seed,
        "mysteryWeights": candidate.mysteryResultWeights,
        "tokenValueScale": candidate.tokenValueScale,
    }


def main_screen(n_per_tier: int = 20_000, seed: int = 42) -> dict:
    config = load_v2_config()
    paying = live_candidate_from_config(config)
    mix = base_trigger_mix(config)
    rows = []
    for spec in SCREEN_CANDIDATES:
        print(f"screening {spec[0]} n={n_per_tier}...", flush=True)
        row = evaluate_candidate(
            spec, n_per_tier=n_per_tier, seed=seed, config=config, paying=paying, mix=mix
        )
        print(
            f"  weightedX={row['weighted']['weightedAverageBonusX_givenTrigger']:.2f} "
            f"fsPp={row['weighted']['fsRtpPp']:.2f} reserve={row['weighted']['futureReservePp']:.2f} "
            f"score={row['score']:.2f} t={row['elapsedSec']:.1f}s",
            flush=True,
        )
        rows.append(row)
    rows.sort(key=lambda r: r["score"])
    payload = {
        "liveConfigHashExpected": LIVE_HASH,
        "mix": mix,
        "baseBeforeFs": BASE_BEFORE_FS,
        "fullTarget": FULL_TARGET,
        "nPerTier": n_per_tier,
        "seed": seed,
        "candidates": rows,
    }
    path = OUT / f"screen_n{n_per_tier}_seed{seed}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", path)
    return payload


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20_000
    main_screen(n_per_tier=n)
