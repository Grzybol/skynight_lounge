"""DEV-only Phase 6B sample books for /dev-preview. Not production."""

from __future__ import annotations

import json
import random
from pathlib import Path

from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config

HERE = Path(__file__).resolve().parent
OUT = HERE / "skyjump_v2_phase6_samples.json"


def classify(events: list[dict]) -> dict:
    types = [e["type"] for e in events]
    winds = [e for e in events if e["type"] == "skyjumpWindKey"]
    charges = [e for e in winds if e.get("action") == "CHARGE"]
    upgrades = [e for e in winds if e.get("action") == "UPGRADE"]
    rj_starts = [e for e in events if e["type"] == "skyjumpRejumpStart"]
    trunc = [e for e in events if e["type"] == "skyjumpRejumpEnd" and e.get("truncated")]
    snaps = [e for e in events if e["type"] == "skyjumpFreeSpinState"]
    max_mult = max((int(s.get("globalFlightMultiplier") or 1) for s in snaps), default=1)
    judges = [e for e in events if e["type"] in ("skyjumpJudgeCollect", "skyjumpHeadJudgeCollect")]
    hj = [e for e in events if e["type"] == "skyjumpHeadJudgeCollect"]
    mult_on_judge = any(int(j.get("flightMultiplierX") or 1) >= 2 for j in judges)
    mult4_judge = any(int(j.get("flightMultiplierX") or 1) >= 4 for j in judges)
    rejump_lines = [e for e in events if e["type"] == "skyjumpRejumpLineWins"]
    line_win = any(float(e.get("lineWinX") or 0) > 0 for e in rejump_lines)
    tiers = [s.get("bonusTier") for s in snaps if s.get("bonusTier")]
    tier_upgrade = len(set(tiers)) > 1 if tiers else False
    ski = any(t == "SKI_FLYING" for t in tiers)
    pv = any(t == "PERFECT_V" for t in tiers)
    coaches = [e for e in events if e["type"] == "skyjumpCoach"]
    coach_after_rj = False
    if rj_starts and coaches:
        first_rj = next(i for i, e in enumerate(events) if e["type"] == "skyjumpRejumpStart")
        coach_after_rj = any(
            i > first_rj for i, e in enumerate(events) if e["type"] == "skyjumpCoach"
        )
    # spent judge then later judge: two judge events with different batchIndex
    batches = [j.get("batchIndex") for j in judges if j.get("batchIndex") is not None]
    multi_batch_judges = len(set(batches)) >= 2
    cap = any(e["type"] == "skyjumpCapReached" for e in events)
    return {
        "hasBonus": "skyjumpFreeSpinsStart" in types,
        "windCount": len(winds),
        "chargeCount": len(charges),
        "upgradeCount": len(upgrades),
        "rejumpCount": len(rj_starts),
        "truncated": bool(trunc),
        "maxMult": max_mult,
        "judgeCount": len(judges),
        "headJudgeCount": len(hj),
        "multOnJudge": mult_on_judge,
        "mult4Judge": mult4_judge,
        "rejumpLineWin": line_win,
        "tierUpgrade": tier_upgrade,
        "skiFlying": ski,
        "perfectV": pv,
        "coachAfterRejump": coach_after_rj,
        "multiBatchJudges": multi_batch_judges,
        "cap": cap,
    }


def resume_for(events: list[dict], prefer: tuple[str, ...]) -> int | None:
    for want in prefer:
        for index, event in enumerate(events):
            if event["type"] == want:
                return index
    for index, event in enumerate(events):
        if event["type"] in ("skyjumpWindKey", "skyjumpRejumpStart", "skyjumpJudgeCollect"):
            return index
    return None


def main() -> None:
    cfg = load_v2_config()
    wants = {
        "01_wind_charge": (
            lambda c: c["chargeCount"] >= 1 and c["upgradeCount"] == 0 and c["maxMult"] == 1,
            ("skyjumpWindKey",),
        ),
        "02_wind_upgrade": (
            lambda c: c["upgradeCount"] >= 1 and c["maxMult"] >= 2,
            ("skyjumpWindKey",),
        ),
        "03_mult_ge4": (lambda c: c["maxMult"] >= 4, ("skyjumpWindKey",)),
        "04_mult_ge8": (lambda c: c["maxMult"] >= 8, ("skyjumpWindKey",)),
        "05_mult_ge12": (lambda c: c["maxMult"] >= 12, ("skyjumpWindKey",)),
        "06_judge": (lambda c: c["judgeCount"] >= 1 and c["maxMult"] == 1, ("skyjumpJudgeCollect",)),
        "07_judge_mult2": (lambda c: c["multOnJudge"] and c["maxMult"] >= 2, ("skyjumpJudgeCollect",)),
        "08_head_judge_mult4": (
            lambda c: c["headJudgeCount"] >= 1 and c["mult4Judge"],
            ("skyjumpHeadJudgeCollect",),
        ),
        "09_rejump_line": (
            lambda c: c["rejumpCount"] >= 1 and c["rejumpLineWin"],
            ("skyjumpRejumpStart",),
        ),
        "10_rejump": (lambda c: c["rejumpCount"] >= 1, ("skyjumpRejumpStart",)),
        "11_judge_before_rejump": (
            lambda c: c["judgeCount"] >= 1 and c["rejumpCount"] >= 1,
            ("skyjumpJudgeCollect",),
        ),
        "12_multi_batch_judges": (
            lambda c: c["multiBatchJudges"],
            ("skyjumpJudgeCollect",),
        ),
        "14_two_rejumps": (lambda c: c["rejumpCount"] >= 2, ("skyjumpRejumpStart",)),
        "15_truncated": (lambda c: c["truncated"], ("skyjumpRejumpEnd",)),
        "16_coach_after_rejump": (
            lambda c: c["coachAfterRejump"],
            ("skyjumpRejumpStart",),
        ),
        "19_ski_flying_mult": (
            lambda c: c["skiFlying"] and c["maxMult"] >= 2,
            ("skyjumpWindKey",),
        ),
        "20_tier_upgrade_mult": (
            lambda c: c["tierUpgrade"] and c["maxMult"] >= 2,
            ("skyjumpWindKey",),
        ),
        "21_resume_charge": (
            lambda c: c["chargeCount"] >= 1,
            ("skyjumpWindKey",),
        ),
        "22_resume_rejump": (
            lambda c: c["rejumpCount"] >= 1,
            ("skyjumpRejumpBoard",),
        ),
        "23_perfect_v_mult": (
            lambda c: c["perfectV"] and c["maxMult"] >= 2,
            ("skyjumpWindKey",),
        ),
        "24_cap": (lambda c: c["cap"], ("skyjumpCapReached",)),
    }
    found: dict[str, dict | None] = {key: None for key in wants}
    for seed in range(0, 120_000):
        book = resolve_v2_round(random.Random(seed), config=cfg)
        if not book["isBonus"]:
            continue
        flags = classify(book["events"])
        for key, (pred, prefer) in wants.items():
            if found[key] is None and pred(flags):
                found[key] = {
                    "id": key,
                    "seed": seed,
                    "title": key.replace("_", " "),
                    "resumeIndex": resume_for(book["events"], prefer),
                    "flags": flags,
                    "eventCount": len(book["events"]),
                    "events": book["events"],
                    "roundWinXCapped": book["roundWinXCapped"],
                }
        if all(found.values()):
            break
    missing = [k for k, v in found.items() if v is None]
    catalog = [found[k] for k in wants if found[k] is not None]
    # Synthetic resume variants for charge mid-step / between batches when natural found
    OUT.write_text(
        json.dumps(
            {
                "schemaVersion": 2,
                "phase": "6B",
                "nonProduction": True,
                "missing": missing,
                "samples": catalog,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("wrote", OUT, "count", len(catalog), "missing", missing)


if __name__ == "__main__":
    main()
