"""Phase 4C BASE feature RTP tail certification runner (measurement only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_exact import exact_line_rtp, exact_scatter_distribution, exact_symbol_window_distribution
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase4c_exact import config_fingerprint, exact_flight_token_joint
from skyjump_v2_phase4c_forced import run_forced_tier_batch
from skyjump_v2_phase4c_strata import (
    bulk_low_tier_mc,
    certified_from_strata,
    conditional_given_forced_tier,
    mix_over_n,
    probe_mystery_count_distribution,
)
from skyjump_v2_reels import COACH_ID

CONFIG_PATH = HERE / "skyjump_v2_config.json"
OUT_DIR = HERE / "phase4c_research"
OUT_REPORT = HERE / "skyjump_v2_phase4c_cert_report.json"
HASH_PATH = OUT_DIR / "live_config_sha256.txt"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dominant_cap_route(cond_t6: dict) -> str:
    routes = cond_t6.get("routes") or {}
    if not routes:
        return "unknown"
    # Prefer routes that appear often and pay large when capping.
    best = max(routes.items(), key=lambda kv: kv[1]["share"] * kv[1]["E_raw"])
    return best[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-spins", type=int, default=500_000)
    parser.add_argument("--bulk-spins", type=int, default=5_000_000)
    parser.add_argument("--cond-spins", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_v2_config()
    digest = sha256_file(CONFIG_PATH)
    HASH_PATH.write_text(digest + "\n", encoding="utf-8")
    fingerprint = config_fingerprint(config)
    joint = exact_flight_token_joint(config)
    strips = config["reelModel"]["strips"]
    line_exact = exact_line_rtp(strips, config["paylines"], config["paytable"]["awards"])["lineRtp"]
    scatter = exact_scatter_distribution(strips)
    ge3 = sum(p for n, p in scatter.items() if n >= 3)
    coach = exact_symbol_window_distribution(strips, COACH_ID)
    p_coach = 1.0 - coach.get(0, 0.0)

    print("probe mystery N...", flush=True)
    probe = probe_mystery_count_distribution(args.probe_spins, args.seed, config)
    p_tier_m = joint["pFlightAndTier"]
    p_stratum = mix_over_n(probe["pN"], p_tier_m)
    # sanity: strata for max-tier partition should sum ~1
    part_sum = (
        p_stratum["NO_T4PLUS"]
        + p_stratum["T4_NO_T5PLUS"]
        + p_stratum["T5_NO_T6"]
        + p_stratum["T6_PRESENT"]
    )

    print("bulk MC...", flush=True)
    bulk = bulk_low_tier_mc(args.bulk_spins, args.seed + 1, config)

    print("conditional T4...", flush=True)
    cond_t4 = conditional_given_forced_tier(spins=args.cond_spins, seed=args.seed + 2, forced_tier=4, config=config)
    print("conditional T5...", flush=True)
    cond_t5 = conditional_given_forced_tier(spins=args.cond_spins, seed=args.seed + 3, forced_tier=5, config=config)
    print("conditional T6...", flush=True)
    cond_t6 = conditional_given_forced_tier(
        spins=max(args.cond_spins, 150_000), seed=args.seed + 4, forced_tier=6, config=config
    )

    # Per-face T6 detail
    print("forced T6 faces...", flush=True)
    t6_faces = {}
    for face in (10000.0, 25000.0, 50000.0):
        t6_faces[str(int(face))] = run_forced_tier_batch(
            spins=80_000,
            seed=args.seed + int(face),
            forced_tier=6,
            forced_face=face,
            config=config,
        )

    certified = certified_from_strata(
        p_stratum=p_stratum,
        bulk=bulk,
        cond_t4=cond_t4,
        cond_t5=cond_t5,
        cond_t6=cond_t6,
    )

    cert_raw = certified["featureRtpRaw"]
    cert_cap = certified["featureRtpCapped"]
    unc = certified["uncertaintyAbs"]
    # Prefer not understating uncertainty vs ±0.10pp target
    precision_ok = unc <= 0.0010

    remaining = 0.965 - line_exact - cert_cap
    implied = remaining / ge3
    remaining_lo = 0.965 - line_exact - (cert_cap + unc)
    remaining_hi = 0.965 - line_exact - (cert_cap - unc)

    drag = certified["capDragRtp"]
    waste = drag / max(cert_raw, 1e-12)
    if unc > 0.0020:
        classification = "NOT STABLE"
        ready = False
    elif waste > 0.12 or (cert_raw - cert_cap) > 0.012:
        classification = "STABLE BUT ECONOMICALLY POOR"
        ready = True
    else:
        classification = "STABLE"
        ready = True

    # Tier RTP contributions from pieces (T1-T3 collapsed into NO_T4PLUS; report exclusive max-tier from bulk for T1-T3)
    tier_contrib = {
        "T1_T2_T3_bulk_exclusive": {
            "cappedRtp": sum(
                bulk["byMaxTierExclusive"].get(f"T{t}", {}).get("cappedRtp", 0.0) for t in (1, 2, 3)
            ),
            "rawRtp": sum(bulk["byMaxTierExclusive"].get(f"T{t}", {}).get("rawRtp", 0.0) for t in (1, 2, 3)),
        },
        "T4": {
            "p": p_stratum["T4_NO_T5PLUS"],
            "cappedRtp": p_stratum["T4_NO_T5PLUS"] * cond_t4["E_capped"],
            "rawRtp": p_stratum["T4_NO_T5PLUS"] * cond_t4["E_raw"],
        },
        "T5": {
            "p": p_stratum["T5_NO_T6"],
            "cappedRtp": p_stratum["T5_NO_T6"] * cond_t5["E_capped"],
            "rawRtp": p_stratum["T5_NO_T6"] * cond_t5["E_raw"],
        },
        "T6": {
            "p": p_stratum["T6_PRESENT"],
            "cappedRtp": p_stratum["T6_PRESENT"] * cond_t6["E_capped"],
            "rawRtp": p_stratum["T6_PRESENT"] * cond_t6["E_raw"],
            "capDragRtp": p_stratum["T6_PRESENT"] * cond_t6["pCap"] * cond_t6.get("E_excess_given_cap", 0.0),
        },
    }

    report = {
        "nonProduction": True,
        "phase": "4C",
        "liveConfigSha256": digest,
        "liveConfigFingerprint": fingerprint,
        "exact": {
            "lineRtp": line_exact,
            "pCoachAny": p_coach,
            "pScatterGe3": ge3,
            "scatterGe3OneInN": 1.0 / ge3,
            "mysteryTokenJoint": {
                "pFlightToken": joint["pFlightToken"],
                "pTierGivenFlight": joint["pTierGivenFlight"],
                "pFlightAndTier": joint["pFlightAndTier"],
                "pFlightAndT6Face": joint["pFlightAndT6Face"],
                "evFaceGivenTier": joint["evFaceGivenTier"],
                "pMysteryResults": joint["pMysteryResults"],
            },
            "stratumPartitionSum": part_sum,
        },
        "mysteryCountProbe": probe,
        "pStratumExactMix": p_stratum,
        "bulkNaturalMc": bulk,
        "conditional": {"T4": cond_t4, "T5": cond_t5, "T6": cond_t6},
        "t6FaceForced": t6_faces,
        "stratifiedCertified": certified,
        "naturalMcEstimate": {
            "featureRtpRaw": bulk["featureRtpRaw"],
            "featureRtpCapped": bulk["featureRtpCapped"],
            "uncertaintyAbs": None,
            "note": "Bulk natural Monte Carlo only; rare-tier noisy.",
        },
        "semiExactEstimate": {
            "featureRtpRaw": cert_raw,
            "featureRtpCapped": cert_cap,
            "uncertaintyAbs": unc,
            "note": "P(stratum) from exact mix over probed N × E[X|forced tier]",
        },
        "certifiedBestEstimate": {
            "lineRtp": line_exact,
            "featureRtpRaw": cert_raw,
            "featureRtpCapped": cert_cap,
            "baseTotalBeforeFs": line_exact + cert_cap,
            "uncertaintyAbs": unc,
            "uncertaintyPp": unc * 100.0,
            "precisionTargetPp": 0.10,
            "precisionAchieved": precision_ok,
            "method": "exact stratum probs (mix over mystery-count probe) × conditional forced-tier expectations; bulk fills NO_T4PLUS",
        },
        "cap": {
            "probability": certified["pCap"],
            "oneInN": (1.0 / certified["pCap"]) if certified["pCap"] > 0 else None,
            "dragRtp": drag,
            "E_excess_given_cap": cond_t6.get("E_excess_given_cap"),
            "rawThresholds_bulk": bulk["rawThresholds"],
            "rawThresholds_given_T6": cond_t6.get("rawThresholdsGiven"),
        },
        "rtpContributionByTier": tier_contrib,
        "rtpContributionByCollectorPasses": bulk["byCollectorPasses"],
        "dominantCapRoute": dominant_cap_route(cond_t6),
        "freeSpinBudgetPlanningOnly": {
            "remainingRtp": remaining,
            "remainingRtpLow": remaining_lo,
            "remainingRtpHigh": remaining_hi,
            "impliedAverageBonusX": implied,
            "impliedAverageBonusLow": remaining_lo / ge3,
            "impliedAverageBonusHigh": remaining_hi / ge3,
            "pScatterGe3": ge3,
        },
        "classification": classification,
        "readyForFreeSpinDesign": ready,
    }

    OUT_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "phase4c_cert_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT_REPORT)
    print("sha256", digest)
    print("p stratum", {k: p_stratum[k] for k in ("NO_T4PLUS", "T4_NO_T5PLUS", "T5_NO_T6", "T6_PRESENT")})
    print("cert raw/capped", cert_raw, cert_cap, "+/-", unc)
    print("bulk capped", bulk["featureRtpCapped"])
    print("T6 E_raw/E_cap/pCap", cond_t6["E_raw"], cond_t6["E_capped"], cond_t6["pCap"])
    print("classification", classification)


if __name__ == "__main__":
    main()
