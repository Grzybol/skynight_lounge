"""Deterministic Phase 4A candidate search. Research only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_phase4a_candidates import coach_models, handcrafted_finalist_seeds, search_space
from skyjump_v2_phase4a_simulate import counterfactual_stack, score_report, simulate_candidate

OUT_DIR = HERE / "phase4a_research"
SEED = 20260921


def run_search(screen_spins: int, finalist_spins: int, top_n: int = 5) -> dict:
    OUT_DIR.mkdir(exist_ok=True)
    coaches = coach_models()
    hand = handcrafted_finalist_seeds()
    space = search_space()
    # Keep all handcrafted + a fixed stride through search space.
    sampled = hand + [space[i] for i in range(0, len(space), max(1, len(space) // 40))]
    seen = set()
    candidates = []
    for row in sampled:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        candidates.append(row)

    screen_rows = []
    for candidate in candidates:
        report = simulate_candidate(candidate, spins=screen_spins, seed=SEED, coach_bundle=coaches)
        scored = score_report(report)
        screen_rows.append(
            {
                "id": candidate["id"],
                "coach": candidate["coachModelId"],
                "gateMaxFloor": candidate["gateMaxFloor"],
                "featureRtpCapped": report["featureRtpCapped"],
                "featureRtpRaw": report["featureRtpRaw"],
                "baseRtpBeforeFs": report["baseRtpBeforeFs"],
                "pDeadCoach": report["pDeadCoach"],
                "pFeatureWinGivenCoach": report["pFeatureWinGivenCoach"],
                "pFeatureWin": report["pFeatureWin"],
                "capFrequency": report["capFrequency"],
                "remainingFsRtp": report["remainingFsRtp"],
                "impliedBonus": report["impliedAvgBonusPerScatterTrigger"],
                "score": scored["score"],
                "inFeatureBand": scored["inFeatureBand"],
                "candidate": candidate,
            }
        )
    screen_rows.sort(key=lambda row: row["score"], reverse=True)
    (OUT_DIR / "skyjump_v2_phase4a_screen.json").write_text(
        json.dumps({"seed": SEED, "screenSpins": screen_spins, "rows": screen_rows}, indent=2) + "\n",
        encoding="utf-8",
    )

    # Prefer handcrafted in-band, then other in-band, then score order. Always keep >=5.
    hand_ids = {row["id"] for row in hand}
    finalists = [row for row in screen_rows if row["id"] in hand_ids and row["inFeatureBand"]]
    for row in screen_rows:
        if len(finalists) >= top_n:
            break
        if row["id"] not in {f["id"] for f in finalists} and row["inFeatureBand"]:
            finalists.append(row)
    for row in screen_rows:
        if len(finalists) >= top_n:
            break
        if row["id"] not in {f["id"] for f in finalists}:
            finalists.append(row)
    # Cap at top_n but never drop below the primary handcrafted set size if smaller screen.
    finalists = finalists[: max(top_n, min(5, len(finalists)))]
    finalists = finalists[:top_n]

    deep = []
    for row in finalists:
        report = simulate_candidate(row["candidate"], spins=finalist_spins, seed=SEED, coach_bundle=coaches)
        report["score"] = score_report(report)
        path = OUT_DIR / f"finalist_{row['id']}.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        deep.append(report)

    deep.sort(key=lambda row: row["score"]["score"], reverse=True)
    recommended = deep[0]
    counter = counterfactual_stack(
        recommended["candidate"],
        spins=min(finalist_spins, 1_000_000),
        seed=SEED + 11,
        coach_bundle=coaches,
    )
    summary = {
        "nonProduction": True,
        "phase": "4A",
        "seed": SEED,
        "screenSpins": screen_spins,
        "finalistSpins": finalist_spins,
        "coachModels": {
            key: {
                "label": val["label"],
                "pAny": val["meta"]["pAny"],
                "pGe2": val["meta"]["pGe2"],
                "lineRtp": val["meta"]["lineRtp"],
                "reels0": val["reels0"],
            }
            for key, val in coaches.items()
        },
        "screened": len(candidates),
        "finalists": [
            {
                "id": row["candidateId"],
                "coach": row["coachModelId"],
                "featureRtpCapped": row["featureRtpCapped"],
                "pDeadCoach": row["pDeadCoach"],
                "pFeatureWinGivenCoach": row["pFeatureWinGivenCoach"],
                "baseRtpBeforeFs": row["baseRtpBeforeFs"],
                "remainingFsRtp": row["remainingFsRtp"],
                "score": row["score"]["score"],
            }
            for row in deep
        ],
        "recommendedId": recommended["candidateId"],
        "recommended": recommended,
        "counterfactual": counter,
        "phase3LiveConfigModified": False,
    }
    (OUT_DIR / "skyjump_v2_phase4a_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "screened": len(candidates),
                "recommended": recommended["candidateId"],
                "featureRtp": recommended["featureRtpCapped"],
                "dead": recommended["pDeadCoach"],
                "feel": recommended["pFeatureWinGivenCoach"],
                "base": recommended["baseRtpBeforeFs"],
                "fsRemain": recommended["remainingFsRtp"],
            },
            indent=2,
        )
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--screen-spins", type=int, default=200_000)
    parser.add_argument("--finalist-spins", type=int, default=5_000_000)
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()
    run_search(args.screen_spins, args.finalist_spins, args.top)


if __name__ == "__main__":
    main()
