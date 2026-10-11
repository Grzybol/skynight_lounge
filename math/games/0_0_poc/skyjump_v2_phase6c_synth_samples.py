"""Deterministic synthetic Phase 6 DEV books for missing QA cases. Not production."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE / "skyjump_v2_phase6_samples.json"
OUT = HERE / "skyjump_v2_phase6_samples.json"

BOARD = [["L1"] * 5 for _ in range(5)]


def _fs_start(index: int, *, tier: str, mult: dict, global_m: int, keys: int = 0) -> dict:
    return {
        "index": index,
        "type": "skyjumpFreeSpinsStart",
        "schemaVersion": 2,
        "initialTier": tier,
        "spinsAwarded": 10,
        "directTriggerType": "SCATTER",
        "triggeringScatterPositions": [],
        "bonusTier": tier,
        "freeSpinsAwarded": 10,
        "freeSpinsRemaining": 10,
        "tokenFloorTier": 1,
        "persistentMysteryTargets": [],
        "guaranteedGateUsed": False,
        "flightMultiplier": mult,
        "globalFlightMultiplier": global_m,
        "windKeysCollected": keys,
        "rejumpsThisBonus": 0,
        "featureBatchIndex": 0,
    }


def synthetic_coach_after_rejump() -> dict:
    mult = {
        "runUp": {"value": 1, "charge": 0},
        "takeoff": {"value": 1, "charge": 0},
        "flight": {"value": 1, "charge": 0},
    }
    events = [
        {"index": 0, "type": "skyjumpSpinStart", "schemaVersion": 2, "gameType": "freespin"},
        {
            "index": 1,
            "type": "skyjumpBoardReveal",
            "schemaVersion": 2,
            "board": BOARD,
            "paddingPositions": [],
            "gameType": "freespin",
        },
        _fs_start(2, tier="SKI_FLYING", mult=mult, global_m=1),
        {
            "index": 3,
            "type": "skyjumpFreeSpinStart",
            "schemaVersion": 2,
            "spinIndex": 0,
            "bonusTier": "SKI_FLYING",
            "freeSpinsRemaining": 10,
        },
        {
            "index": 4,
            "type": "skyjumpBoardReveal",
            "schemaVersion": 2,
            "board": BOARD,
            "paddingPositions": [],
            "gameType": "freespin",
        },
        {
            "index": 5,
            "type": "skyjumpMysteryResolve",
            "schemaVersion": 2,
            "position": {"reel": 0, "row": 0},
            "resultType": "REJUMP",
            "batchIndex": 0,
        },
        {
            "index": 6,
            "type": "skyjumpRejumpStart",
            "schemaVersion": 2,
            "chainIndex": 0,
            "preservedPositions": [{"reel": 1, "row": 1}],
            "redroppedPositions": [{"reel": 2, "row": 2}],
            "rejumpsThisSpin": 1,
        },
        {
            "index": 7,
            "type": "skyjumpRejumpBoard",
            "schemaVersion": 2,
            "chainIndex": 0,
            "board": BOARD,
            "changedPositions": [{"reel": 2, "row": 2, "symbolId": "C"}],
        },
        {
            "index": 8,
            "type": "skyjumpRejumpLineWins",
            "schemaVersion": 2,
            "chainIndex": 0,
            "lineWins": [],
            "lineWinX": 0,
        },
        {
            "index": 9,
            "type": "skyjumpCoach",
            "schemaVersion": 2,
            "coachPosition": {"reel": 2, "row": 2},
            "selectedSymbolId": "M2",
            "selectedPositions": [{"reel": 3, "row": 3}],
            "sequenceIndex": 0,
            "noOp": False,
            "afterRejump": True,
        },
        {
            "index": 10,
            "type": "skyjumpRejumpEnd",
            "schemaVersion": 2,
            "chainIndex": 0,
            "applied": True,
            "truncated": False,
            "reason": None,
        },
        {
            "index": 11,
            "type": "skyjumpFreeSpinState",
            "schemaVersion": 2,
            "bonusTier": "SKI_FLYING",
            "freeSpinsRemaining": 9,
            "freeSpinsPlayed": 1,
            "bonusWinX": 0,
            "tokenFloorTier": 1,
            "persistentMysteryTargets": ["M2"],
            "flightMultiplier": mult,
            "globalFlightMultiplier": 1,
            "windKeysCollected": 0,
            "rejumpsThisBonus": 1,
            "featureBatchIndex": 1,
        },
        {"index": 12, "type": "setTotalWin", "amount": 0},
        {"index": 13, "type": "finalWin", "amount": 0},
    ]
    return {
        "id": "16_coach_after_rejump",
        "seed": -1601,
        "title": "synthetic coach after rejump",
        "resumeIndex": 6,
        "flags": {"synthetic": True, "coachAfterRejump": True},
        "eventCount": len(events),
        "events": events,
        "roundWinXCapped": 0,
    }


def synthetic_cap_multiplied_collector() -> dict:
    mult = {
        "runUp": {"value": 3, "charge": 0},
        "takeoff": {"value": 3, "charge": 0},
        "flight": {"value": 3, "charge": 0},
    }
    events = [
        {"index": 0, "type": "skyjumpSpinStart", "schemaVersion": 2, "gameType": "freespin"},
        {
            "index": 1,
            "type": "skyjumpBoardReveal",
            "schemaVersion": 2,
            "board": BOARD,
            "paddingPositions": [],
            "gameType": "freespin",
        },
        _fs_start(2, tier="PERFECT_V", mult=mult, global_m=27, keys=12),
        {
            "index": 3,
            "type": "skyjumpFreeSpinStart",
            "schemaVersion": 2,
            "spinIndex": 0,
            "bonusTier": "PERFECT_V",
            "freeSpinsRemaining": 10,
            "flightMultiplier": mult,
            "globalFlightMultiplier": 27,
        },
        {
            "index": 4,
            "type": "skyjumpBoardReveal",
            "schemaVersion": 2,
            "board": BOARD,
            "paddingPositions": [],
            "gameType": "freespin",
        },
        {
            "index": 5,
            "type": "skyjumpJudgeCollect",
            "schemaVersion": 2,
            "position": {"reel": 0, "row": 0},
            "passIndex": 1,
            "batchIndex": 0,
            "rawTokenCollectionX": 2000.0,
            "flightMultiplierX": 27,
            "paidCollectionX": 54000.0,
            "tokenContributions": [{"reel": 1, "row": 1, "effectiveX": 2000.0}],
            "payoutSpentAfter": True,
            "amount": 54000.0,
        },
        {
            "index": 6,
            "type": "skyjumpCapReached",
            "schemaVersion": 2,
            "rawTotalWinX": 54000.0,
            "cappedTotalWinX": 50000.0,
            "capDragX": 4000.0,
            "maxWinX": 50000.0,
            "terminated": True,
        },
        {
            "index": 7,
            "type": "skyjumpFreeSpinState",
            "schemaVersion": 2,
            "bonusTier": "PERFECT_V",
            "freeSpinsRemaining": 0,
            "freeSpinsPlayed": 1,
            "bonusWinX": 50000.0,
            "tokenFloorTier": 6,
            "persistentMysteryTargets": [],
            "maxWinReached": True,
            "flightMultiplier": mult,
            "globalFlightMultiplier": 27,
            "windKeysCollected": 12,
            "rejumpsThisBonus": 0,
            "featureBatchIndex": 0,
        },
        {
            "index": 8,
            "type": "skyjumpResult",
            "schemaVersion": 2,
            "totalLineWinX": 0,
            "totalFeatureWinX": 50000.0,
            "totalWinX": 50000.0,
            "amount": 50000,
            "capHit": True,
        },
        {"index": 9, "type": "setTotalWin", "amount": 50000},
        {"index": 10, "type": "finalWin", "amount": 50000},
    ]
    return {
        "id": "24_cap",
        "seed": -2401,
        "title": "synthetic cap via multiplied collector",
        "resumeIndex": 5,
        "flags": {"synthetic": True, "cap": True, "multOnJudge": True},
        "eventCount": len(events),
        "events": events,
        "roundWinXCapped": 50000,
    }


def main() -> None:
    data = json.loads(LIVE.read_text(encoding="utf-8"))
    existing = {s["id"]: s for s in data.get("samples", [])}
    for synth in (synthetic_coach_after_rejump(), synthetic_cap_multiplied_collector()):
        existing[synth["id"]] = synth
    order = [
        "01_wind_charge",
        "02_wind_upgrade",
        "03_mult_ge4",
        "04_mult_ge8",
        "05_mult_ge12",
        "06_judge",
        "07_judge_mult2",
        "08_head_judge_mult4",
        "09_rejump_line",
        "10_rejump",
        "11_judge_before_rejump",
        "12_multi_batch_judges",
        "14_two_rejumps",
        "15_truncated",
        "16_coach_after_rejump",
        "19_ski_flying_mult",
        "20_tier_upgrade_mult",
        "21_resume_charge",
        "22_resume_rejump",
        "23_perfect_v_mult",
        "24_cap",
    ]
    samples = [existing[i] for i in order if i in existing]
    for sid, sample in existing.items():
        if sid not in {s["id"] for s in samples}:
            samples.append(sample)
    payload = {
        "schemaVersion": 2,
        "phase": "6B",
        "nonProduction": True,
        "missing": [i for i in order if i not in existing],
        "samples": samples,
        "note": "Includes deterministic synthetic books for rare QA cases (16, 24).",
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", OUT, "count", len(samples))


if __name__ == "__main__":
    main()
