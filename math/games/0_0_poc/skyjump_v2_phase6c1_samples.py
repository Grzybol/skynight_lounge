"""Append Phase 6C.1 PURE W2 deterministic DEV samples. Not production."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "skyjump_v2_phase6_samples.json"
BOARD = [["L1"] * 5 for _ in range(5)]


def _mult(ru, tc, fl, *, rc=0, tcc=0, fc=0):
    return {
        "runUp": {"value": ru, "charge": rc},
        "takeoff": {"value": tc, "charge": tcc},
        "flight": {"value": fl, "charge": fc},
    }


def _snap(index: int, *, tier: str, mult: dict, global_m: int, keys: int, remaining: int = 8):
    return {
        "index": index,
        "type": "skyjumpFreeSpinState",
        "schemaVersion": 2,
        "spinIndex": 0,
        "bonusTier": tier,
        "freeSpinsRemaining": remaining,
        "tokenFloorTier": 1,
        "persistentMysteryTargets": [],
        "guaranteedGateUsed": False,
        "flightMultiplier": mult,
        "globalFlightMultiplier": global_m,
        "windKeysCollected": keys,
        "rejumpsThisBonus": 0,
        "featureBatchIndex": 0,
    }


def _wind(index: int, *, stage: str, action: str, old_v: int, new_v: int, old_c: int, new_c: int, old_g: int, new_g: int):
    return {
        "index": index,
        "type": "skyjumpWindKey",
        "schemaVersion": 2,
        "selectedStage": stage,
        "action": action,
        "oldStageValue": old_v,
        "newStageValue": new_v,
        "oldCharge": old_c,
        "newCharge": new_c,
        "oldGlobalMultiplier": old_g,
        "newGlobalMultiplier": new_g,
    }


def _book(sample_id: str, title: str, events: list[dict], *, resume_type: str = "skyjumpWindKey") -> dict:
    resume = next((i for i, e in enumerate(events) if e["type"] == resume_type), 0)
    return {
        "id": sample_id,
        "seed": None,
        "title": title,
        "resumeIndex": resume,
        "flags": {"pureW2": True, "synthetic": True},
        "eventCount": len(events),
        "events": events,
        "roundWinXCapped": 0.0,
        "synthetic": True,
    }


def sequence_a_through_e() -> list[dict]:
    """A–E: charge RUN_UP, TAKEOFF, FLIGHT then complete one to x2."""
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
        {
            "index": 2,
            "type": "skyjumpFreeSpinsStart",
            "schemaVersion": 2,
            "initialTier": "LARGE_HILL",
            "spinsAwarded": 10,
            "directTriggerType": "SCATTER",
            "triggeringScatterPositions": [],
            "bonusTier": "LARGE_HILL",
            "freeSpinsAwarded": 10,
            "freeSpinsRemaining": 10,
            "tokenFloorTier": 1,
            "persistentMysteryTargets": [],
            "guaranteedGateUsed": False,
            "flightMultiplier": _mult(1, 1, 1),
            "globalFlightMultiplier": 1,
            "windKeysCollected": 0,
            "rejumpsThisBonus": 0,
            "featureBatchIndex": 0,
        },
        _wind(3, stage="RUN_UP", action="CHARGE", old_v=1, new_v=1, old_c=0, new_c=1, old_g=1, new_g=1),
        _snap(4, tier="LARGE_HILL", mult=_mult(1, 1, 1, rc=1), global_m=1, keys=1),
        _wind(5, stage="TAKEOFF", action="CHARGE", old_v=1, new_v=1, old_c=0, new_c=1, old_g=1, new_g=1),
        _snap(6, tier="LARGE_HILL", mult=_mult(1, 1, 1, rc=1, tcc=1), global_m=1, keys=2),
        _wind(7, stage="FLIGHT", action="CHARGE", old_v=1, new_v=1, old_c=0, new_c=1, old_g=1, new_g=1),
        _snap(8, tier="LARGE_HILL", mult=_mult(1, 1, 1, rc=1, tcc=1, fc=1), global_m=1, keys=3),
        _wind(9, stage="TAKEOFF", action="UPGRADE", old_v=1, new_v=2, old_c=1, new_c=0, old_g=1, new_g=2),
        _snap(10, tier="LARGE_HILL", mult=_mult(1, 2, 1, rc=1, tcc=0, fc=1), global_m=2, keys=4),
    ]
    return [
        _book("c1_a_first_key_charges_run_up", "PURE W2: first Key charges RUN_UP", events[:5]),
        _book(
            "c1_b_second_key_charges_takeoff",
            "PURE W2: second Key charges TAKEOFF (not forced RUN_UP complete)",
            events[:7],
        ),
        _book("c1_c_third_key_charges_flight", "PURE W2: third Key charges FLIGHT", events[:9]),
        _book("c1_d_complete_one_to_x2", "PURE W2: later Key completes TAKEOFF to x2", events),
        _book(
            "c1_e_three_partial_charges",
            "PURE W2: all three stages charged at x1 — valid HUD state",
            events[:9],
            resume_type="skyjumpFreeSpinState",
        ),
    ]


def sample_f_across_spins() -> dict:
    events = [
        {"index": 0, "type": "skyjumpSpinStart", "schemaVersion": 2, "gameType": "freespin"},
        _snap(1, tier="LARGE_HILL", mult=_mult(1, 1, 1, rc=1, tcc=1, fc=1), global_m=1, keys=3, remaining=7),
        {
            "index": 2,
            "type": "skyjumpFreeSpinStart",
            "schemaVersion": 2,
            "spinIndex": 1,
            "bonusTier": "LARGE_HILL",
            "freeSpinsRemaining": 6,
        },
        _snap(3, tier="LARGE_HILL", mult=_mult(1, 1, 1, rc=1, tcc=1, fc=1), global_m=1, keys=3, remaining=6),
    ]
    return _book(
        "c1_f_partial_charges_across_spins",
        "PURE W2: three partial charges persist across Free Spins",
        events,
        resume_type="skyjumpFreeSpinState",
    )


def sample_g_tier_upgrade() -> dict:
    events = [
        _snap(0, tier="LARGE_HILL", mult=_mult(1, 1, 1, rc=1, tcc=1), global_m=1, keys=2, remaining=5),
        {
            "index": 1,
            "type": "skyjumpFreeSpinUpgrade",
            "schemaVersion": 2,
            "fromTier": "LARGE_HILL",
            "toTier": "SKI_FLYING",
            "spinsAdded": 5,
        },
        _snap(2, tier="SKI_FLYING", mult=_mult(1, 1, 1, rc=1, tcc=1), global_m=1, keys=2, remaining=10),
    ]
    return _book(
        "c1_g_tier_upgrade_preserves_charges",
        "PURE W2: tier upgrade preserves stage charges",
        events,
        resume_type="skyjumpFreeSpinUpgrade",
    )


def sample_h_saturated() -> dict:
    events = [
        _snap(0, tier="LARGE_HILL", mult=_mult(3, 1, 1, rc=0), global_m=3, keys=6),
        _wind(1, stage="TAKEOFF", action="CHARGE", old_v=1, new_v=1, old_c=0, new_c=1, old_g=3, new_g=3),
        _snap(2, tier="LARGE_HILL", mult=_mult(3, 1, 1, tcc=1), global_m=3, keys=7),
    ]
    return _book(
        "c1_h_saturated_excluded",
        "PURE W2: saturated x3 RUN_UP excluded from selection",
        events,
    )


def sample_i_saturation_b() -> dict:
    events = [
        _snap(0, tier="LARGE_HILL", mult=_mult(3, 3, 3), global_m=27, keys=18),
        {
            "index": 1,
            "type": "skyjumpMysteryResolve",
            "schemaVersion": 2,
            "position": {"reel": 1, "row": 1},
            "resultType": "FLIGHT_TOKEN",
            "batchIndex": 0,
            "note": "saturation B: WIND_KEY remapped / unavailable when all stages x3",
        },
        _snap(2, tier="LARGE_HILL", mult=_mult(3, 3, 3), global_m=27, keys=18),
    ]
    return _book(
        "c1_i_all_x3_saturation_b",
        "PURE W2: all x3 → saturation B removes WIND_KEY",
        events,
        resume_type="skyjumpMysteryResolve",
    )


def main() -> None:
    existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"samples": []}
    samples = list(existing.get("samples") or [])
    by_id = {s["id"]: i for i, s in enumerate(samples)}
    fresh = (
        sequence_a_through_e()
        + [sample_f_across_spins(), sample_g_tier_upgrade(), sample_h_saturated(), sample_i_saturation_b()]
    )
    for sample in fresh:
        if sample["id"] in by_id:
            samples[by_id[sample["id"]]] = sample
        else:
            samples.append(sample)
            by_id[sample["id"]] = len(samples) - 1
    payload = {
        "schemaVersion": 2,
        "phase": "6C.1",
        "pureW2": True,
        "nonProduction": True,
        "missing": existing.get("missing") or [],
        "samples": samples,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", OUT, "total", len(samples), "pureW2", [s["id"] for s in fresh])


if __name__ == "__main__":
    main()
