"""Phase 4A.2 feel-refinement search. Research only; does not touch live config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_phase4a2_candidates import (
    coach_models_4a2,
    feel_handcrafted_seeds,
    feel_search_space,
    h02_benchmark,
)
from skyjump_v2_phase4a2_simulate import delta_vs_h02, run_sim

OUT_DIR = HERE / "phase4a2_research"
SEED = 20260922


def _slim(report: dict) -> dict:
    return {
        "id": report["candidateId"],
        "coach": report["coachModelId"],
        "conditional": bool(report["candidate"].get("conditionalCollectors")),
        "pAny": report["coachExact"]["pAny"],
        "pGe2": report["coachExact"]["pGe2"],
        "lineRtp": report["theoreticalLineRtp"],
        "featureRtpCapped": report["featureRtpCapped"],
        "baseRtpBeforeFs": report["baseRtpBeforeFs"],
        "pDeadCoach": report["pDeadCoach"],
        "pFeatureWinGivenCoach": report["pFeatureWinGivenCoach"],
        "median": report["medianFeatureWinGivenWin"],
        "avgWin": report["avgFeatureWinGivenWin"],
        "remainingFsRtp": report["remainingFsRtp"],
        "impliedBonus": report["impliedAvgBonusPerScatterTrigger"],
        "capFrequency": report["capFrequency"],
        "score": report["feelScore"]["score"],
        "inFeatureBand": report["feelScore"]["inFeatureBand"],
        "deadReasons": report.get("deadCoachReasons"),
    }


def pick_finalists(screen_rows: list[dict], reports_by_id: dict[str, dict]) -> list[dict]:
    """Ensure required finalist roles are covered."""
    picked: list[dict] = []
    used = set()

    def add(row: dict | None):
        if row is None:
            return
        cid = row["id"]
        if cid in used:
            return
        used.add(cid)
        picked.append(row)

    add(next((r for r in screen_rows if r["id"] == "H02_B_R1"), None))

    two_reel = [
        r
        for r in screen_rows
        if r["coach"] in ("D", "E", "F") and not r["conditional"] and r["inFeatureBand"]
    ]
    two_reel.sort(key=lambda r: r["score"], reverse=True)
    add(two_reel[0] if two_reel else next((r for r in screen_rows if r["coach"] in ("D", "E", "F") and not r["conditional"]), None))

    lower = [r for r in screen_rows if r["coach"] == "E" and not r["conditional"]]
    lower.sort(key=lambda r: r["score"], reverse=True)
    add(lower[0] if lower else None)

    higher_collect = sorted(
        [
            r
            for r in screen_rows
            if (not r["conditional"])
            and r["id"] != "H02_B_R1"
            and r["featureRtpCapped"] <= 0.14
        ],
        key=lambda r: (r["pFeatureWinGivenCoach"], r["score"]),
        reverse=True,
    )
    add(higher_collect[0] if higher_collect else None)

    cond = [r for r in screen_rows if r["conditional"]]
    cond.sort(key=lambda r: r["score"], reverse=True)
    add(cond[0] if cond else None)

    for row in screen_rows:
        if len(picked) >= 5:
            break
        add(row)
    return picked[: max(5, len(picked))]


def run_search(screen_spins: int, finalist_spins: int, top_spins: int) -> dict:
    OUT_DIR.mkdir(exist_ok=True)
    coaches = coach_models_4a2()
    hand = feel_handcrafted_seeds()
    space = feel_search_space()
    sampled = hand + [space[i] for i in range(0, len(space), max(1, len(space) // 24))]
    seen = set()
    candidates = []
    for row in sampled:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        candidates.append(row)

    screen_rows = []
    reports_by_id = {}
    for candidate in candidates:
        report = run_sim(candidate, spins=screen_spins, seed=SEED, coach_bundle=coaches)
        reports_by_id[candidate["id"]] = report
        slim = _slim(report)
        slim["candidate"] = candidate
        screen_rows.append(slim)
        print(
            "screen",
            slim["id"],
            "feat",
            round(slim["featureRtpCapped"] * 100, 2),
            "feel",
            round(slim["pFeatureWinGivenCoach"], 3),
            "dead",
            round(slim["pDeadCoach"], 3),
            "score",
            round(slim["score"], 3),
            flush=True,
        )
    screen_rows.sort(key=lambda row: row["score"], reverse=True)
    (OUT_DIR / "skyjump_v2_phase4a2_screen.json").write_text(
        json.dumps({"seed": SEED, "screenSpins": screen_spins, "rows": screen_rows}, indent=2) + "\n",
        encoding="utf-8",
    )

    finalist_meta = pick_finalists(screen_rows, reports_by_id)
    deep = []
    for meta in finalist_meta:
        spins = top_spins if meta["id"] in {finalist_meta[0]["id"], finalist_meta[1]["id"]} else finalist_spins
        # Always deep-sim H02 and recommended candidates at least finalist_spins.
        if meta["id"] == "H02_B_R1":
            spins = max(spins, finalist_spins)
        print("deep", meta["id"], "spins", spins, flush=True)
        report = run_sim(meta["candidate"], spins=spins, seed=SEED, coach_bundle=coaches)
        path = OUT_DIR / f"finalist_{meta['id']}.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        deep.append(report)

    h02 = next(row for row in deep if row["candidateId"] == "H02_B_R1")
    # Recommend best non-benchmark by feel score among deep sims.
    ranked = sorted(
        [row for row in deep if row["candidateId"] != "H02_B_R1"],
        key=lambda row: row["feelScore"]["score"],
        reverse=True,
    )
    recommended = ranked[0] if ranked else deep[0]
    # Prefer in-band + multi-coach if close.
    for row in ranked:
        if row["feelScore"]["inFeatureBand"] and row["coachExact"]["pGe2"] > 0:
            if row["feelScore"]["score"] >= recommended["feelScore"]["score"] - 1.5:
                recommended = row
                break

    # Top-2 10M if not already.
    top_two = sorted(deep, key=lambda row: row["feelScore"]["score"], reverse=True)[:2]
    for row in top_two:
        if row["spins"] < top_spins and row["candidateId"] != "H02_B_R1":
            print("top-up", row["candidateId"], "to", top_spins, flush=True)
            upgraded = run_sim(row["candidate"], spins=top_spins, seed=SEED, coach_bundle=coaches)
            (OUT_DIR / f"finalist_{row['candidateId']}.json").write_text(
                json.dumps(upgraded, indent=2) + "\n", encoding="utf-8"
            )
            for index, existing in enumerate(deep):
                if existing["candidateId"] == row["candidateId"]:
                    deep[index] = upgraded
            if recommended["candidateId"] == row["candidateId"]:
                recommended = upgraded

    for row in deep:
        row["deltaVsH02"] = delta_vs_h02(row, h02)

    recommended["deltaVsH02"] = delta_vs_h02(recommended, h02)

    # Export candidates
    for candidate in feel_handcrafted_seeds():
        (OUT_DIR / f"candidate_{candidate['id']}.json").write_text(
            json.dumps(candidate, indent=2) + "\n", encoding="utf-8"
        )

    summary = {
        "nonProduction": True,
        "phase": "4A.2",
        "seed": SEED,
        "screenSpins": screen_spins,
        "finalistSpins": finalist_spins,
        "topSpins": top_spins,
        "coachModels": {
            key: {
                "label": val["label"],
                "pAny": val["meta"]["pAny"],
                "pGe2": val["meta"]["pGe2"],
                "lineRtp": val["meta"]["lineRtp"],
                "reels0": val["reels0"],
                "stripLengths": val.get("stripLengths"),
            }
            for key, val in coaches.items()
            if key in ("A", "B", "D", "E", "F")
        },
        "screened": len(candidates),
        "finalists": [_slim(row) | {"deltaVsH02": row.get("deltaVsH02")} for row in deep],
        "recommendedId": recommended["candidateId"],
        "recommended": recommended,
        "benchmarkId": "H02_B_R1",
        "benchmark": h02,
        "phase3LiveConfigModified": False,
        "phase4aH02Preserved": True,
        "readyForHumanApproval": True,
        "readyForPhase4B": False,
    }
    (OUT_DIR / "skyjump_v2_phase4a2_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "recommended": recommended["candidateId"],
                "feat": recommended["featureRtpCapped"],
                "feel": recommended["pFeatureWinGivenCoach"],
                "dead": recommended["pDeadCoach"],
                "pGe2": recommended["coachExact"]["pGe2"],
                "score": recommended["feelScore"]["score"],
            },
            indent=2,
        ),
        flush=True,
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--screen-spins", type=int, default=150_000)
    parser.add_argument("--finalist-spins", type=int, default=5_000_000)
    parser.add_argument("--top-spins", type=int, default=10_000_000)
    args = parser.parse_args()
    run_search(args.screen_spins, args.finalist_spins, args.top_spins)


if __name__ == "__main__":
    main()
