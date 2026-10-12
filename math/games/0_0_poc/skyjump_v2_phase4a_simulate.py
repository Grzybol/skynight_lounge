"""Phase 4A Monte Carlo for paying-feature economy research."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_exact import exact_line_rtp, exact_scatter_distribution
from skyjump_v2_lines import line_win_summary, load_v2_config
from skyjump_v2_phase4a_candidates import coach_models
from skyjump_v2_phase4a_economy import resolve_paying_features
from skyjump_v2_reels import board_from_stops

TARGET_FULL_RTP = 0.965
FEATURE_RTP_LO = 0.09
FEATURE_RTP_HI = 0.11
FEATURE_RTP_SOFT_LO = 0.085
FEATURE_RTP_SOFT_HI = 0.125
TARGET_FEATURE_RTP = 0.10
TAIL_THRESHOLDS = (10, 50, 100, 500, 1000, 5000, 10000, 50000)


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(math.ceil(q / 100.0 * len(ordered)) - 1)))
    return float(ordered[index])


def simulate_candidate(
    candidate: dict,
    *,
    spins: int,
    seed: int,
    coach_bundle: dict | None = None,
    enable_thermal: bool = True,
    enable_gate: bool = True,
    enable_head_judge: bool = True,
    enable_judge: bool = True,
) -> dict:
    config = load_v2_config()
    coaches = coach_bundle or coach_models(config)
    coach = coaches[candidate["coachModelId"]]
    strips = coach["strips"]
    paytable = config["paytable"]["awards"]
    paylines = config["paylines"]
    scatter_id = config["symbols"]["scatter"]["id"]
    regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    rng = random.Random(seed)

    line_total = 0.0
    feature_raw_total = 0.0
    feature_capped_total = 0.0
    cap_hits = 0
    cap_drag = 0.0
    feature_wins = 0
    coach_spins = 0
    feature_given_coach = 0
    dead_coach = 0
    tokens_no_collect = 0
    win_sizes: list[float] = []
    judge_spins = 0
    head_spins = 0
    thermal_spins = 0
    gate_spins = 0
    collector_passes = 0
    raw_face = 0.0
    effective = 0.0
    judge_contrib = 0.0
    head_contrib = 0.0
    thermal_uplift = 0.0
    gate_face_uplift = 0.0
    upgraded = 0
    thermal_hits = 0
    tokens_ge2 = 0
    tail = {key: 0 for key in TAIL_THRESHOLDS}
    mystery_hist = {
        "FLIGHT_TOKEN": 0,
        "THERMAL_LIFT": 0,
        "GATE_UPGRADE": 0,
        "JUDGE": 0,
        "HEAD_JUDGE": 0,
    }
    conditional = {
        "t5plus": {"n": 0, "featureRaw": 0.0, "cap": 0},
        "t6": {"n": 0, "featureRaw": 0.0, "cap": 0},
        "thermal2plus": {"n": 0, "featureRaw": 0.0, "cap": 0},
        "multiCollector": {"n": 0, "featureRaw": 0.0, "cap": 0},
        "multiCoach": {"n": 0, "featureRaw": 0.0, "cap": 0},
        "gateAndCollector": {"n": 0, "featureRaw": 0.0, "cap": 0},
        "raw50kplus": {"n": 0, "featureRaw": 0.0, "cap": 0},
    }
    dead_reasons = {
        "tokens_no_collector": 0,
        "collector_no_tokens": 0,
        "modifier_only": 0,
        "other": 0,
    }
    win_buckets = [
        ("0", lambda x: x == 0),
        ("0_1", lambda x: 0 < x <= 1),
        ("1_2", lambda x: 1 < x <= 2),
        ("2_5", lambda x: 2 < x <= 5),
        ("5_10", lambda x: 5 < x <= 10),
        ("10_25", lambda x: 10 < x <= 25),
        ("25_50", lambda x: 25 < x <= 50),
        ("50_100", lambda x: 50 < x <= 100),
        ("100_500", lambda x: 100 < x <= 500),
        ("500_1000", lambda x: 500 < x <= 1000),
        ("1000_5000", lambda x: 1000 < x <= 5000),
        ("5000_plus", lambda x: x > 5000),
    ]
    coach_win_dist = {key: 0 for key, _ in win_buckets}
    paid_win_dist = {key: 0 for key, _ in win_buckets}

    for _ in range(spins):
        stops = [rng.randrange(len(strip)) for strip in strips]
        board = board_from_stops(strips, stops)
        line_win, _hits = line_win_summary(
            board,
            paylines=paylines,
            paytable=paytable,
            scatter_id=scatter_id,
            regular_ids=regular_ids,
        )
        features = resolve_paying_features(
            board,
            rng,
            config=config,
            candidate=candidate,
            line_win_x=line_win,
            enable_thermal=enable_thermal,
            enable_gate=enable_gate,
            enable_head_judge=enable_head_judge,
            enable_judge=enable_judge,
        )
        line_total += line_win
        feature_raw_total += features["totalFeatureWinXRaw"]
        feature_capped_total += features["totalFeatureWinXCapped"]
        raw_feat = features["totalFeatureWinXRaw"]
        if features["capHit"]:
            cap_hits += 1
            cap_drag += features["capDragX"]
        if features["hasFeatureWin"]:
            feature_wins += 1
            win_sizes.append(raw_feat)
        if features["coachCount"]:
            coach_spins += 1
            if features["hasFeatureWin"]:
                feature_given_coach += 1
            if features["deadCoach"]:
                dead_coach += 1
                reason = features.get("deadReason") or "other"
                dead_reasons[reason] = dead_reasons.get(reason, 0) + 1
            for key, pred in win_buckets:
                if pred(raw_feat):
                    coach_win_dist[key] += 1
                    break
        for key, pred in win_buckets:
            if pred(raw_feat):
                paid_win_dist[key] += 1
                break
        if features["tokensWithoutCollector"]:
            tokens_no_collect += 1
        if features["judgeCount"]:
            judge_spins += 1
        if features["headJudgeCount"]:
            head_spins += 1
        if features["thermalCount"]:
            thermal_spins += 1
        if features["gateCount"]:
            gate_spins += 1
        collector_passes += features["collectorPasses"]
        raw_face += features["rawFaceSumX"]
        effective += features["effectiveTokenSumX"]
        judge_contrib += features["judgeContributionX"]
        head_contrib += features["headJudgeContributionX"]
        thermal_uplift += features["thermalUpliftProxyX"]
        gate_face_uplift += features["gateFaceUpliftX"]
        upgraded += features["upgradedTokens"]
        thermal_hits += features["thermalHitsOnTokens"]
        tokens_ge2 += features["tokensHitByGe2Thermals"]
        for resolve in features["resolves"]:
            mystery_hist[resolve["resultType"]] += 1
        for threshold in TAIL_THRESHOLDS:
            if raw_feat >= threshold:
                tail[threshold] += 1

        has_t5 = any(
            r["resultType"] == "FLIGHT_TOKEN" and int(r.get("tokenTier") or 0) >= 5 for r in features["resolves"]
        )
        has_t6 = any(
            r["resultType"] == "FLIGHT_TOKEN" and int(r.get("tokenTier") or 0) == 6 for r in features["resolves"]
        )
        if has_t5:
            conditional["t5plus"]["n"] += 1
            conditional["t5plus"]["featureRaw"] += raw_feat
            conditional["t5plus"]["cap"] += int(features["capHit"])
        if has_t6:
            conditional["t6"]["n"] += 1
            conditional["t6"]["featureRaw"] += raw_feat
            conditional["t6"]["cap"] += int(features["capHit"])
        if features["tokensHitByGe2Thermals"] > 0 or features["thermalCount"] >= 2:
            conditional["thermal2plus"]["n"] += 1
            conditional["thermal2plus"]["featureRaw"] += raw_feat
            conditional["thermal2plus"]["cap"] += int(features["capHit"])
        if features["collectorPasses"] >= 2:
            conditional["multiCollector"]["n"] += 1
            conditional["multiCollector"]["featureRaw"] += raw_feat
            conditional["multiCollector"]["cap"] += int(features["capHit"])
        if features.get("multiCoach"):
            conditional["multiCoach"]["n"] += 1
            conditional["multiCoach"]["featureRaw"] += raw_feat
            conditional["multiCoach"]["cap"] += int(features["capHit"])
        if features["gateCount"] > 0 and (features["judgeCount"] > 0 or features["headJudgeCount"] > 0):
            conditional["gateAndCollector"]["n"] += 1
            conditional["gateAndCollector"]["featureRaw"] += raw_feat
            conditional["gateAndCollector"]["cap"] += int(features["capHit"])
        if raw_feat >= 50000:
            conditional["raw50kplus"]["n"] += 1
            conditional["raw50kplus"]["featureRaw"] += raw_feat
            conditional["raw50kplus"]["cap"] += int(features["capHit"])

    line_rtp = line_total / spins
    feature_raw = feature_raw_total / spins
    feature_capped = feature_capped_total / spins
    exact_line = exact_line_rtp(strips, paylines, paytable)["lineRtp"]
    scatter = exact_scatter_distribution(strips)
    scatter_ge3 = sum(prob for count, prob in scatter.items() if count >= 3)
    base_before_fs = exact_line + feature_capped
    remaining_fs = TARGET_FULL_RTP - base_before_fs
    implied_bonus = remaining_fs / scatter_ge3 if scatter_ge3 > 0 else None

    mystery_total = max(1, sum(mystery_hist.values()))
    return {
        "nonProduction": True,
        "phase": "4A",
        "candidateId": candidate["id"],
        "notes": candidate.get("notes", ""),
        "spins": spins,
        "seed": seed,
        "coachModelId": candidate["coachModelId"],
        "coachLabel": coach["label"],
        "coachExact": {
            "pAny": coach["meta"]["pAny"],
            "pGe2": coach["meta"]["pGe2"],
            "lineRtp": coach["meta"]["lineRtp"],
        },
        "theoreticalLineRtp": exact_line,
        "simulatedLineRtp": line_rtp,
        "featureRtpRaw": feature_raw,
        "featureRtpCapped": feature_capped,
        "baseRtpBeforeFs": base_before_fs,
        "remainingFsRtp": remaining_fs,
        "scatterGe3": scatter_ge3,
        "impliedAvgBonusPerScatterTrigger": implied_bonus,
        "pFeatureWin": feature_wins / spins,
        "pFeatureWinGivenCoach": (feature_given_coach / coach_spins) if coach_spins else 0.0,
        "pDeadCoach": (dead_coach / coach_spins) if coach_spins else 0.0,
        "pCoachSpin": coach_spins / spins,
        "pTokensWithoutCollector": tokens_no_collect / spins,
        "avgFeatureWinGivenWin": (sum(win_sizes) / len(win_sizes)) if win_sizes else 0.0,
        "medianFeatureWinGivenWin": _pct(win_sizes, 50),
        "p90FeatureWinGivenWin": _pct(win_sizes, 90),
        "p95FeatureWinGivenWin": _pct(win_sizes, 95),
        "p99FeatureWinGivenWin": _pct(win_sizes, 99),
        "p999FeatureWinGivenWin": _pct(win_sizes, 99.9),
        "maxFeatureWinObserved": max(win_sizes) if win_sizes else 0.0,
        "pAnyJudge": judge_spins / spins,
        "pAnyHeadJudge": head_spins / spins,
        "pAnyThermal": thermal_spins / spins,
        "pAnyGate": gate_spins / spins,
        "avgCollectorPasses": collector_passes / spins,
        "avgRawFaceSum": raw_face / spins,
        "avgEffectiveTokenSum": effective / spins,
        "judgeContributionRtp": judge_contrib / spins,
        "headJudgeContributionRtp": head_contrib / spins,
        "gateFaceUpliftRtp": gate_face_uplift / spins,
        "thermalUpliftRtp": thermal_uplift / spins,
        "avgUpgradedTokens": upgraded / spins,
        "avgThermalHitsOnTokens": thermal_hits / spins,
        "avgTokensHitByGe2Thermals": tokens_ge2 / spins,
        "capFrequency": cap_hits / spins,
        "capDragRtp": cap_drag / spins,
        "tailFeatureRaw": {str(key): tail[key] / spins for key in TAIL_THRESHOLDS},
        "mysteryResultMix": {key: mystery_hist[key] / mystery_total for key in mystery_hist},
        "deadCoachReasons": {
            key: (dead_reasons[key] / coach_spins) if coach_spins else 0.0 for key in dead_reasons
        },
        "deadCoachReasonCounts": dead_reasons,
        "featureWinDistGivenCoach": {
            key: (coach_win_dist[key] / coach_spins) if coach_spins else 0.0 for key in coach_win_dist
        },
        "featureWinDistPerSpin": {key: paid_win_dist[key] / spins for key in paid_win_dist},
        "candidate": candidate,
        "flags": {
            "enableThermal": enable_thermal,
            "enableGate": enable_gate,
            "enableHeadJudge": enable_head_judge,
            "enableJudge": enable_judge,
        },
        "conditional": {
            key: {
                "n": row["n"],
                "rate": row["n"] / spins,
                "avgFeatureRaw": (row["featureRaw"] / row["n"]) if row["n"] else 0.0,
                "capRate": (row["cap"] / row["n"]) if row["n"] else 0.0,
            }
            for key, row in conditional.items()
        },
    }


def score_report(report: dict) -> dict:
    feature = report["featureRtpCapped"]
    rtp_err = abs(feature - TARGET_FEATURE_RTP)
    in_band = FEATURE_RTP_LO <= feature <= FEATURE_RTP_HI
    in_soft = FEATURE_RTP_SOFT_LO <= feature <= FEATURE_RTP_SOFT_HI
    dead = report["pDeadCoach"]
    feel = report["pFeatureWinGivenCoach"]
    # Prefer RTP near ~10pp AND playable Coach feel. Exact midpoint is secondary.
    score = 0.0
    score -= rtp_err * 25
    if in_band:
        score += 2.0
    elif in_soft:
        score += 1.0
    # Dead-Coach is the main feel failure mode for this economy.
    score -= max(0.0, dead - 0.55) * 12
    score += min(feel, 0.55) * 8
    score -= report["capFrequency"] * 200
    score -= max(0.0, 0.20 - report["remainingFsRtp"]) * 12
    if report["remainingFsRtp"] < 0.15:
        score -= 4
    implied = report.get("impliedAvgBonusPerScatterTrigger")
    if implied and implied > 80:
        score -= 2
    if implied and implied < 20:
        score -= 1
    score += min(report["tailFeatureRaw"].get("100", 0) * 20, 1.0)
    # Mild preference for keeping multi-Coach option available later (Coach A/C),
    # but never enough to outweigh a large dead-Coach gap.
    if report["coachModelId"] == "B":
        score += 0.35
    return {
        "score": score,
        "inFeatureBand": in_band,
        "inSoftBand": in_soft,
        "rtpError": rtp_err,
        "deadCoach": dead,
        "feel": feel,
    }


def counterfactual_stack(candidate: dict, spins: int, seed: int, coach_bundle: dict) -> dict:
    layers = [
        ("judge_only", dict(enable_thermal=False, enable_gate=False, enable_head_judge=False, enable_judge=True)),
        ("judge_head", dict(enable_thermal=False, enable_gate=False, enable_head_judge=True, enable_judge=True)),
        ("judge_head_thermal", dict(enable_thermal=True, enable_gate=False, enable_head_judge=True, enable_judge=True)),
        ("full", dict(enable_thermal=True, enable_gate=True, enable_head_judge=True, enable_judge=True)),
    ]
    out = {}
    for name, flags in layers:
        report = simulate_candidate(candidate, spins=spins, seed=seed, coach_bundle=coach_bundle, **flags)
        out[name] = {
            "featureRtpRaw": report["featureRtpRaw"],
            "featureRtpCapped": report["featureRtpCapped"],
            "capFrequency": report["capFrequency"],
            "pFeatureWin": report["pFeatureWin"],
            "avgFeatureWinGivenWin": report["avgFeatureWinGivenWin"],
            "p99FeatureWinGivenWin": report["p99FeatureWinGivenWin"],
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-json", type=str, required=True)
    parser.add_argument("--spins", type=int, default=5_000_000)
    parser.add_argument("--seed", type=int, default=20260921)
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()
    candidate = json.loads(Path(args.candidate_json).read_text(encoding="utf-8"))
    report = simulate_candidate(candidate, spins=args.spins, seed=args.seed)
    report["score"] = score_report(report)
    print(
        json.dumps(
            {
                "id": report["candidateId"],
                "line": report["theoreticalLineRtp"],
                "featRaw": report["featureRtpRaw"],
                "featCap": report["featureRtpCapped"],
                "base": report["baseRtpBeforeFs"],
                "dead": report["pDeadCoach"],
                "feel": report["pFeatureWinGivenCoach"],
                "score": report["score"]["score"],
            },
            indent=2,
        )
    )
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
