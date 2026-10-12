"""Phase 4A.2 feel scoring and H02 delta helpers."""

from __future__ import annotations

from skyjump_v2_phase4a_simulate import (
    FEATURE_RTP_HI,
    FEATURE_RTP_LO,
    TARGET_FEATURE_RTP,
    simulate_candidate,
)

FEEL_TARGET_LO = 0.25
FEEL_TARGET_HI = 0.35
DEAD_SOFT = 0.75
DEAD_HARD = 0.80
MEDIAN_MIN = 1.0
MEDIAN_TARGET_LO = 2.0
MEDIAN_TARGET_HI = 4.0
AVG_TARGET_LO = 3.0
AVG_TARGET_HI = 5.0
LINE_RTP_LO = 0.57
LINE_RTP_HI = 0.60
PANY_LO = 0.07
PANY_HI = 0.11
PGE2_LO = 0.001
PGE2_HI = 0.006
IMPLIED_BONUS_LO = 30.0
IMPLIED_BONUS_HI = 45.0


def score_feel_report(report: dict) -> dict:
    """Player-feel weighted score. RTP band is necessary but not primary."""
    feature = report["featureRtpCapped"]
    dead = report["pDeadCoach"]
    feel = report["pFeatureWinGivenCoach"]
    median = report["medianFeatureWinGivenWin"]
    avg = report["avgFeatureWinGivenWin"]
    p_ge2 = report["coachExact"]["pGe2"]
    p_any = report["coachExact"]["pAny"]
    line = report["theoreticalLineRtp"]
    remaining = report["remainingFsRtp"]
    implied = report.get("impliedAvgBonusPerScatterTrigger") or 0.0
    cap_f = report["capFrequency"]
    tail100 = report["tailFeatureRaw"].get("100", 0.0)
    tail50k = report["tailFeatureRaw"].get("50000", 0.0)

    in_band = FEATURE_RTP_LO <= feature <= FEATURE_RTP_HI
    prefer_band = 0.095 <= feature <= 0.105
    score = 0.0

    # A. Feature RTP within 9–11pp (soft preference for 9.5–10.5)
    if in_band:
        score += 3.0
    else:
        score -= abs(feature - TARGET_FEATURE_RTP) * 35
    if prefer_band:
        score += 1.0
    else:
        score -= abs(feature - 0.10) * 8

    # B/C. Dead Coach / feel
    score += min(feel, 0.40) * 18
    if FEEL_TARGET_LO <= feel <= FEEL_TARGET_HI:
        score += 2.5
    if dead > DEAD_HARD:
        score -= (dead - DEAD_HARD) * 40
    elif dead > DEAD_SOFT:
        score -= (dead - DEAD_SOFT) * 20
    else:
        score += (DEAD_SOFT - dead) * 6

    # D. Multi-Coach retained
    if p_ge2 > 0:
        score += 1.5
        if PGE2_LO <= p_ge2 <= PGE2_HI:
            score += 1.0
    else:
        score -= 1.2

    # E. Median / average collected win
    if median < MEDIAN_MIN:
        score -= 4.0
    elif MEDIAN_TARGET_LO <= median <= MEDIAN_TARGET_HI:
        score += 1.5
    else:
        score -= abs(median - 3.0) * 0.15
    if AVG_TARGET_LO <= avg <= AVG_TARGET_HI:
        score += 1.0
    elif avg > 8:
        score -= 0.8

    # F. Tail preservation
    score += min(tail100 * 40, 1.2)
    if report["candidate"]["tokenTierWeights"].get("6", 0) > 0:
        score += 0.3
    if tail50k > 0:
        score += 0.4

    # G. Cap
    score -= cap_f * 250
    score -= report.get("capDragRtp", 0.0) * 50

    # H. Free Spin reserve / implied bonus
    if remaining < 0.20:
        score -= 3.0
    elif remaining > 0.22:
        score += 0.5
    if IMPLIED_BONUS_LO <= implied <= IMPLIED_BONUS_HI:
        score += 1.0
    elif implied > 60:
        score -= 1.5

    # I. Line RTP stability + Coach band
    if LINE_RTP_LO <= line <= LINE_RTP_HI:
        score += 1.0
    else:
        score -= abs(line - 0.585) * 20
    if PANY_LO <= p_any <= PANY_HI:
        score += 0.8

    # Prefer independent tables for promotion path unless conditioned is clearly better.
    if report["candidate"].get("conditionalCollectors"):
        score -= 0.25

    return {
        "score": score,
        "inFeatureBand": in_band,
        "preferBand": prefer_band,
        "deadCoach": dead,
        "feel": feel,
        "multiCoach": p_ge2 > 0,
        "median": median,
    }


def delta_vs_h02(report: dict, h02: dict) -> dict:
    keys = [
        ("pCoachAny", lambda r: r["coachExact"]["pAny"]),
        ("pCoachGe2", lambda r: r["coachExact"]["pGe2"]),
        ("featureRtpCapped", lambda r: r["featureRtpCapped"]),
        ("pFeatureWinGivenCoach", lambda r: r["pFeatureWinGivenCoach"]),
        ("pDeadCoach", lambda r: r["pDeadCoach"]),
        ("avgFeatureWinGivenWin", lambda r: r["avgFeatureWinGivenWin"]),
        ("medianFeatureWinGivenWin", lambda r: r["medianFeatureWinGivenWin"]),
        ("p99FeatureWinGivenWin", lambda r: r["p99FeatureWinGivenWin"]),
        ("capFrequency", lambda r: r["capFrequency"]),
        ("remainingFsRtp", lambda r: r["remainingFsRtp"]),
        ("baseRtpBeforeFs", lambda r: r["baseRtpBeforeFs"]),
        ("theoreticalLineRtp", lambda r: r["theoreticalLineRtp"]),
    ]
    out = {}
    for name, getter in keys:
        a = getter(h02)
        b = getter(report)
        out[name] = {"h02": a, "candidate": b, "delta": b - a}
    return out


def run_sim(candidate: dict, *, spins: int, seed: int, coach_bundle: dict) -> dict:
    report = simulate_candidate(candidate, spins=spins, seed=seed, coach_bundle=coach_bundle)
    report["phase"] = candidate.get("phase", "4A.2")
    report["feelScore"] = score_feel_report(report)
    return report
