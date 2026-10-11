"""Phase 4B Monte Carlo on LIVE F01 paying economy. Non-production research."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_exact import (
    exact_line_rtp,
    exact_perfect_v_prob,
    exact_scatter_distribution,
    exact_symbol_window_distribution,
)
from skyjump_v2_lines import load_v2_config
from skyjump_v2_reels import COACH_ID
from skyjump_v2_resolve import resolve_v2_base

OUT = HERE / "skyjump_v2_phase4b_sim_report.json"

FEATURE_BUCKETS = [
    ("0", 0.0, 0.0),
    (">0-1", 0.0, 1.0),
    ("1-2", 1.0, 2.0),
    ("2-5", 2.0, 5.0),
    ("5-10", 5.0, 10.0),
    ("10-25", 10.0, 25.0),
    ("25-50", 25.0, 50.0),
    ("50-100", 50.0, 100.0),
    ("100-500", 100.0, 500.0),
    ("500-1000", 500.0, 1000.0),
    ("1000-5000", 1000.0, 5000.0),
    ("5000+", 5000.0, float("inf")),
]


def _bucket(value: float) -> str:
    if value <= 0:
        return "0"
    for name, lo, hi in FEATURE_BUCKETS[1:]:
        if value > lo and value <= hi:
            return name
        if hi == float("inf") and value > lo:
            return name
    return "0"


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(math.ceil(q / 100.0 * len(ordered)) - 1)))
    return float(ordered[index])


def simulate(spins: int, seed: int) -> dict:
    config = load_v2_config()
    strips = config["reelModel"]["strips"]
    rng = random.Random(seed)

    line_sum = 0.0
    feature_raw_sum = 0.0
    feature_capped_sum = 0.0
    total_capped_sum = 0.0
    cap_hits = 0
    cap_drag_sum = 0.0
    max_raw = 0.0
    max_capped = 0.0

    coach_any = 0
    coach_ge2 = 0
    feature_wins = 0
    feature_wins_given_coach = 0
    dead_coach = 0
    dead_reasons = Counter()
    feature_win_values: list[float] = []
    feature_buckets = {name: 0 for name, _, _ in FEATURE_BUCKETS}

    # Conditional tail counters (observation only).
    cond = {
        "t5_plus": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
        "t6": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
        "thermal_ge2": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
        "gate_and_thermal": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
        "gate_and_collector": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
        "multi_collector": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
        "multi_coach_collectors": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
        "t6_and_thermal": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
        "t6_and_head_judge": {"n": 0, "maxRaw": 0.0, "maxCapped": 0.0},
    }

    for _ in range(spins):
        result = resolve_v2_base(rng, config=config)
        features = result["features"]
        line = float(result["lineWinX"])
        feat_raw = float(result.get("totalFeatureWinXRaw", 0) or 0)
        feat_cap = float(result.get("totalFeatureWinX", 0) or 0)
        total_cap = float(result["totalWinX"])
        total_raw = float(result.get("totalWinXRaw", line + feat_raw))

        line_sum += line
        feature_raw_sum += feat_raw
        feature_capped_sum += feat_cap
        total_capped_sum += total_cap
        max_raw = max(max_raw, total_raw)
        max_capped = max(max_capped, total_cap)

        if features.get("capHit"):
            cap_hits += 1
            cap_drag_sum += float(features.get("capDragX") or 0)

        n_coach = len(features.get("coaches") or [])
        if n_coach > 0:
            coach_any += 1
        if n_coach >= 2:
            coach_ge2 += 1

        has_feat = feat_raw > 0
        if has_feat:
            feature_wins += 1
            feature_win_values.append(feat_cap)
            if n_coach > 0:
                feature_wins_given_coach += 1
        feature_buckets[_bucket(feat_cap)] += 1

        if features.get("deadCoach"):
            dead_coach += 1
            dead_reasons[features.get("deadReason") or "other"] += 1

        tiers = features.get("tokenTiers") or []
        has_t5 = any(t >= 5 for t in tiers)
        has_t6 = any(t >= 6 for t in tiers)
        thermals = int(features.get("thermalCount") or 0)
        gates = int(features.get("gateCount") or 0)
        judges = int(features.get("judgeCount") or 0)
        heads = int(features.get("headJudgeCount") or 0)
        collectors = judges + heads

        def _note(key: str, ok: bool) -> None:
            if not ok:
                return
            row = cond[key]
            row["n"] += 1
            row["maxRaw"] = max(row["maxRaw"], total_raw)
            row["maxCapped"] = max(row["maxCapped"], total_cap)

        _note("t5_plus", has_t5)
        _note("t6", has_t6)
        _note("thermal_ge2", thermals >= 2)
        _note("gate_and_thermal", gates > 0 and thermals > 0)
        _note("gate_and_collector", gates > 0 and collectors > 0)
        _note("multi_collector", collectors >= 2)
        _note("multi_coach_collectors", n_coach >= 2 and collectors > 0)
        _note("t6_and_thermal", has_t6 and thermals > 0)
        _note("t6_and_head_judge", has_t6 and heads > 0)

    scatter = exact_scatter_distribution(strips)
    ge3 = sum(p for n, p in scatter.items() if n >= 3)
    line_exact = exact_line_rtp(strips, config["paylines"], config["paytable"]["awards"])["lineRtp"]
    coach_dist = exact_symbol_window_distribution(strips, COACH_ID)
    p_coach = 1.0 - coach_dist.get(0, 0.0)
    p_coach2 = sum(p for n, p in coach_dist.items() if n >= 2)
    perfect = exact_perfect_v_prob(strips)

    feature_rtp_raw = feature_raw_sum / spins
    feature_rtp_capped = feature_capped_sum / spins
    line_rtp_sim = line_sum / spins
    base_before_fs = line_exact + feature_rtp_capped
    fs_reserve = 0.965 - base_before_fs
    implied_bonus = fs_reserve / ge3 if ge3 > 0 else float("inf")

    positive = [v for v in feature_win_values if v > 0]
    return {
        "nonProduction": True,
        "candidateOrigin": config["featureEconomy"]["candidateOrigin"],
        "featureEconomyVersion": config["featureEconomy"]["featureEconomyVersion"],
        "spins": spins,
        "seed": seed,
        "exact": {
            "lineRtp": line_exact,
            "pCoachAny": p_coach,
            "pCoachGe2": p_coach2,
            "scatter": {str(k): scatter.get(k, 0.0) for k in range(0, 6)},
            "pScatterGe3": ge3,
            "scatterGe3OneInN": (1.0 / ge3) if ge3 else None,
            "perfectV": perfect,
            "perfectVOneInN": (1.0 / perfect) if perfect else None,
        },
        "simulated": {
            "lineRtp": line_rtp_sim,
            "featureRtpRaw": feature_rtp_raw,
            "featureRtpCapped": feature_rtp_capped,
            "baseRtpBeforeFs": base_before_fs,
            "fsRtpReservePp": fs_reserve * 100.0,
            "impliedAvgFsBonusX": implied_bonus,
            "pCoachAny": coach_any / spins,
            "pCoachGe2": coach_ge2 / spins,
            "pFeatureWin": feature_wins / spins,
            "pFeatureWinGivenCoach": (feature_wins_given_coach / coach_any) if coach_any else 0.0,
            "pDeadCoach": (dead_coach / coach_any) if coach_any else 0.0,
            "deadReasons": dict(dead_reasons),
            "featureWinBuckets": {k: v / spins for k, v in feature_buckets.items()},
            "featureWinAvg": (sum(positive) / len(positive)) if positive else 0.0,
            "featureWinMedian": _pct(positive, 50),
            "featureWinP90": _pct(positive, 90),
            "featureWinP95": _pct(positive, 95),
            "featureWinP99": _pct(positive, 99),
            "featureWinP999": _pct(positive, 99.9),
            "capFrequency": cap_hits / spins,
            "capDragTotalX": cap_drag_sum,
            "capDragPerSpin": cap_drag_sum / spins,
            "maxRawTotalWinX": max_raw,
            "maxCappedTotalWinX": max_capped,
            "conditionalTails": cond,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spins", type=int, default=10_000_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    report = simulate(args.spins, args.seed)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    sim = report["simulated"]
    exact = report["exact"]
    print("wrote", OUT)
    print("line exact", exact["lineRtp"], "sim", sim["lineRtp"])
    print("feature raw", sim["featureRtpRaw"], "capped", sim["featureRtpCapped"])
    print("P(coach)", exact["pCoachAny"], "sim", sim["pCoachAny"])
    print("P(feat|coach)", sim["pFeatureWinGivenCoach"], "dead", sim["pDeadCoach"])
    print("scatter3+", exact["pScatterGe3"], "1in", exact["scatterGe3OneInN"])
    print("FS reserve pp", sim["fsRtpReservePp"], "implied bonus", sim["impliedAvgFsBonusX"])
    print("cap freq", sim["capFrequency"], "max raw", sim["maxRawTotalWinX"])


if __name__ == "__main__":
    main()
