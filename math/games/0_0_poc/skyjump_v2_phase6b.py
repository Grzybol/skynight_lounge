"""Live Phase 6B Free Spin features: R-BATCH Rejump + W-CHARGE Wind Key.

Promoted candidate: P6A1_E_E1. Free-spin only. Does not alter BASE.
"""

from __future__ import annotations

from copy import deepcopy

from skyjump_v2_lines import evaluate_paylines
from skyjump_v2_phase4a_economy import (
    build_token_tables,
    empty_cell,
    neighbours,
    sample_token_at_floor,
)
from skyjump_v2_phase5a_engine import FreeSpinState, apply_persistent_targets
from skyjump_v2_phase6a_engine import (
    KIND_GATE,
    KIND_HEAD,
    KIND_JUDGE,
    KIND_REJUMP,
    KIND_THERMAL,
    KIND_TOKEN,
    KIND_WIND,
    LADDERS,
    _locked_positions,
    _materialise,
    _mystery_positions,
    _paint_specials,
    _redrop,
    _resolve_mysteries,
    _run_coaches,
    _symbol_for,
    _take_rejumps,
    draw_mystery,
    refill_catalogs,
)
from skyjump_v2_reels import COACH_ID, MYSTERY_ID

STAGES = ("RUN_UP", "TAKEOFF", "FLIGHT")
LADDER = "K1"
MAX_REJUMPS = 2
MAX_CHAIN = 8


def _stage_bundle(state: FreeSpinState) -> dict[str, dict[str, int]]:
    fm = getattr(state, "flightMultiplier", None)
    if isinstance(fm, dict) and "runUp" in fm:
        return {
            "RUN_UP": {
                "value": int(fm["runUp"]["value"]),
                "charge": int(fm["runUp"]["charge"]),
            },
            "TAKEOFF": {
                "value": int(fm["takeoff"]["value"]),
                "charge": int(fm["takeoff"]["charge"]),
            },
            "FLIGHT": {
                "value": int(fm["flight"]["value"]),
                "charge": int(fm["flight"]["charge"]),
            },
        }
    return {
        "RUN_UP": {"value": int(getattr(state, "flightMultiplierRunUp", 1) or 1), "charge": int(getattr(state, "runUpCharge", 0) or 0)},
        "TAKEOFF": {"value": int(getattr(state, "flightMultiplierTakeoff", 1) or 1), "charge": int(getattr(state, "takeoffCharge", 0) or 0)},
        "FLIGHT": {"value": int(getattr(state, "flightMultiplierFlight", 1) or 1), "charge": int(getattr(state, "flightCharge", 0) or 0)},
    }


def _write_stages(state: FreeSpinState, stages: dict[str, dict[str, int]]) -> None:
    state.flightMultiplier = {
        "runUp": dict(stages["RUN_UP"]),
        "takeoff": dict(stages["TAKEOFF"]),
        "flight": dict(stages["FLIGHT"]),
    }
    state.flightMultiplierRunUp = float(stages["RUN_UP"]["value"])
    state.flightMultiplierTakeoff = float(stages["TAKEOFF"]["value"])
    state.flightMultiplierFlight = float(stages["FLIGHT"]["value"])
    state.runUpCharge = int(stages["RUN_UP"]["charge"])
    state.takeoffCharge = int(stages["TAKEOFF"]["charge"])
    state.flightCharge = int(stages["FLIGHT"]["charge"])


def global_flight_multiplier(state: FreeSpinState) -> int:
    stages = _stage_bundle(state)
    return int(stages["RUN_UP"]["value"]) * int(stages["TAKEOFF"]["value"]) * int(stages["FLIGHT"]["value"])


def stages_maxed(state: FreeSpinState) -> bool:
    stages = _stage_bundle(state)
    order = LADDERS[LADDER]
    return all(int(stages[name]["value"]) == order[-1] for name in STAGES)


def ensure_phase6_state(state: FreeSpinState) -> None:
    if getattr(state, "flightMultiplier", None) is None:
        _write_stages(
            state,
            {
                "RUN_UP": {"value": 1, "charge": 0},
                "TAKEOFF": {"value": 1, "charge": 0},
                "FLIGHT": {"value": 1, "charge": 0},
            },
        )
    if not hasattr(state, "windKeysCollected"):
        state.windKeysCollected = 0
    if not hasattr(state, "rejumpsThisBonus"):
        state.rejumpsThisBonus = 0
    if not hasattr(state, "featureBatchIndex"):
        state.featureBatchIndex = 0
    if getattr(state, "rejumpState", None) is None:
        state.rejumpState = {
            "rejumpsThisSpin": 0,
            "chainDepth": 0,
            "truncatedThisSpin": 0,
        }


# Optional research-parity audit: when True, append Coach selections to
# state.persistentMysteryTargets immediately (incl. after Rejump coaches).
# Default False = live Phase 5B/6C.1 canonical end-of-spin append via resolve_fs_spin.
_MID_SPIN_PERSIST_APPEND = False


def set_mid_spin_persist_append(enabled: bool) -> bool:
    global _MID_SPIN_PERSIST_APPEND
    previous = _MID_SPIN_PERSIST_APPEND
    _MID_SPIN_PERSIST_APPEND = bool(enabled)
    return previous


def _maybe_append_persist_targets(state: FreeSpinState, symbols: list, max_targets: int) -> None:
    if not _MID_SPIN_PERSIST_APPEND:
        return
    if state.bonusTier not in ("SKI_FLYING", "WORLD_CUP", "PERFECT_V"):
        return
    for symbol in symbols:
        if symbol is None:
            continue
        if symbol in state.persistentMysteryTargets:
            continue
        if len(state.persistentMysteryTargets) >= max_targets:
            break
        state.persistentMysteryTargets.append(symbol)


# Live Phase 6C.1 default: PURE W2 (approved E1). Historical priority kept for audit only.
_STAGE_SELECTION_MODE = "W2_PURE"


def set_stage_selection_mode(mode: str | None) -> str:
    """Override Wind stage selection (research/counterfactual). Does not mutate config."""
    global _STAGE_SELECTION_MODE
    previous = _STAGE_SELECTION_MODE
    _STAGE_SELECTION_MODE = mode or "W2_PURE"
    return previous


def choose_stage_charge_priority(rng, state: FreeSpinState) -> tuple[str | None, str]:
    """Historical Phase 6B rule — audit/counterfactual only. Not live payout authority."""
    stages = _stage_bundle(state)
    order = LADDERS[LADDER]
    eligible = [name for name in STAGES if int(stages[name]["value"]) != order[-1]]
    if not eligible:
        return None, "NONE"
    charged = [name for name in eligible if int(stages[name]["charge"]) == 1]
    if charged:
        lowest = min(int(stages[name]["value"]) for name in charged)
        pool = [name for name in charged if int(stages[name]["value"]) == lowest]
        return rng.choice(pool), "UPGRADE"
    lowest = min(int(stages[name]["value"]) for name in eligible)
    pool = [name for name in eligible if int(stages[name]["value"]) == lowest]
    return rng.choice(pool), "CHARGE"


def choose_stage_pure_w2(rng, state: FreeSpinState) -> tuple[str | None, str]:
    """Approved E1 / Phase 6C.1 live: W2 ignores charge when selecting."""
    stages = _stage_bundle(state)
    order = LADDERS[LADDER]
    eligible = [name for name in STAGES if int(stages[name]["value"]) != order[-1]]
    if not eligible:
        return None, "NONE"
    lowest = min(int(stages[name]["value"]) for name in eligible)
    pool = [name for name in eligible if int(stages[name]["value"]) == lowest]
    stage = rng.choice(pool)
    action = "UPGRADE" if int(stages[stage]["charge"]) == 1 else "CHARGE"
    return stage, action


def choose_stage(rng, state: FreeSpinState) -> tuple[str | None, str]:
    """Live payout authority: PURE W2 unless an explicit research override is set."""
    if _STAGE_SELECTION_MODE == "W2_CHARGE_PRIORITY":
        return choose_stage_charge_priority(rng, state)
    return choose_stage_pure_w2(rng, state)


def apply_wind_key(state: FreeSpinState, rng, cell: dict) -> dict:
    stage, action = choose_stage(rng, state)
    stages = _stage_bundle(state)
    old_global = global_flight_multiplier(state)
    if stage is None:
        cell["processed"] = True
        cell["noOp"] = True
        return {
            "selectedStage": None,
            "action": "NO_OP",
            "oldStageValue": None,
            "newStageValue": None,
            "oldCharge": None,
            "newCharge": None,
            "oldGlobalMultiplier": old_global,
            "newGlobalMultiplier": old_global,
        }
    old_value = int(stages[stage]["value"])
    old_charge = int(stages[stage]["charge"])
    if action == "UPGRADE":
        order = LADDERS[LADDER]
        new_value = order[order.index(old_value) + 1]
        stages[stage]["value"] = int(new_value)
        stages[stage]["charge"] = 0
        new_charge = 0
    else:
        stages[stage]["charge"] = 1
        new_value = old_value
        new_charge = 1
    _write_stages(state, stages)
    state.windKeysCollected = int(getattr(state, "windKeysCollected", 0)) + 1
    cell["processed"] = True
    cell["stage"] = stage
    cell["action"] = action
    cell["oldValue"] = old_value
    cell["newValue"] = new_value
    cell["oldCharge"] = old_charge
    cell["newCharge"] = new_charge
    new_global = global_flight_multiplier(state)
    cell["oldGlobal"] = old_global
    cell["newGlobal"] = new_global
    return {
        "selectedStage": stage,
        "action": action,
        "oldStageValue": old_value,
        "newStageValue": new_value,
        "oldCharge": old_charge,
        "newCharge": new_charge,
        "oldGlobalMultiplier": old_global,
        "newGlobalMultiplier": new_global,
        "windKeysCollected": state.windKeysCollected,
    }


def _apply_thermals(specials) -> float:
    for cell in specials.values():
        if cell["kind"] == KIND_TOKEN:
            cell["appliedThermals"] = []
    thermals = [(pos, int(cell["thermalMult"])) for pos, cell in specials.items() if cell["kind"] == KIND_THERMAL]
    for (reel, row), mult in thermals:
        for nr, nc in neighbours(reel, row):
            token = specials.get((nr, nc))
            if not token or token["kind"] != KIND_TOKEN:
                continue
            token["appliedThermals"].append(mult)
    raw_sum = 0.0
    for cell in specials.values():
        if cell["kind"] != KIND_TOKEN:
            continue
        product = 1.0
        for mult in cell["appliedThermals"]:
            product *= float(mult)
        effective = float(cell["faceValueX"]) * product
        cell["effectiveValueX"] = effective
        raw_sum += effective
    return raw_sum


def _token_contributions(specials) -> list[dict]:
    rows = []
    for (reel, row), token in sorted(specials.items()):
        if token["kind"] != KIND_TOKEN:
            continue
        rows.append(
            {
                "reel": reel,
                "row": row,
                "tokenTier": int(token["tokenTier"]),
                "tokenId": token["tokenId"],
                "faceValueX": float(token["faceValueX"]),
                "effectiveValueX": float(token["effectiveValueX"]),
                "appliedThermals": list(token.get("appliedThermals") or []),
            }
        )
    return rows


def _settle_unpaid(specials, state: FreeSpinState, batch_index: int, collections: list, phase6_events: list) -> float:
    raw_sum = _apply_thermals(specials)
    unpaid = []
    for pos, cell in specials.items():
        if cell["kind"] == KIND_JUDGE and not cell.get("paid"):
            unpaid.append(("JUDGE", pos))
        elif cell["kind"] == KIND_HEAD and not cell.get("paid"):
            unpaid.append(("HEAD_JUDGE", pos))
    unpaid.sort(key=lambda row: (row[1][0], row[1][1], 0 if row[0] == "JUDGE" else 1))
    mult = global_flight_multiplier(state)
    paid_total = 0.0
    contrib = _token_contributions(specials)
    for kind, pos in unpaid:
        passes = 1 if kind == "JUDGE" else 2
        for pass_index in range(1, passes + 1):
            raw = raw_sum
            paid = raw * float(mult)
            paid_total += paid
            collections.append(
                {
                    "type": kind,
                    "pass": pass_index,
                    "position": {"reel": pos[0], "row": pos[1]},
                    "collectedX": paid,
                    "rawTokenCollectionX": raw,
                    "flightMultiplierX": mult,
                    "paidCollectionX": paid,
                    "effectiveTokenSumX": raw,
                    "tokenContributions": contrib,
                    "batchIndex": batch_index,
                    "payoutSpentAfter": True,
                }
            )
        specials[pos]["paid"] = True
        specials[pos]["payoutSpent"] = True
    return paid_total


def _apply_gates(specials, floor: int, rng, tables, scale: float, max_floor: int, gate_events: list) -> int:
    gates = sorted(pos for pos, cell in specials.items() if cell["kind"] == KIND_GATE and not cell.get("processed"))
    for pos in gates:
        before = floor
        replacements = []
        if floor < max_floor:
            floor = min(max_floor, floor + 1)
        if floor > before:
            for token_pos, token in list(specials.items()):
                if token["kind"] != KIND_TOKEN:
                    continue
                if int(token["tokenTier"]) >= floor:
                    continue
                old = {"tier": token["tokenTier"], "face": token["faceValueX"]}
                replacement = sample_token_at_floor(rng, tables, floor, scale=scale)
                token.clear()
                token.update(replacement)
                replacements.append(
                    {
                        "reel": token_pos[0],
                        "row": token_pos[1],
                        "before": old,
                        "after": {"tier": token["tokenTier"], "face": token["faceValueX"]},
                    }
                )
        specials[pos]["processed"] = True
        gate_events.append(
            {
                "position": {"reel": pos[0], "row": pos[1]},
                "floorBefore": before,
                "floorAfter": floor,
                "replacements": replacements,
            }
        )
    return floor


def resolve_phase6b_features(
    board_after_persist: list[list[str]],
    rng,
    *,
    config: dict,
    candidate: dict,
    state: FreeSpinState,
    line_win_x: float,
    start_floor: int,
    coach_exclude_types: set[str],
    coach_prefer_non_excluded: bool,
    force_coach_if_none: bool,
    guaranteed_gate: bool,
    guaranteed_gate_policy: str,
    strips: list[list[str]],
    catalogs: list[tuple[str, ...]],
    scatter_cells: set[tuple[int, int]],
    max_rejumps: int = MAX_REJUMPS,
    max_chain: int = MAX_CHAIN,
) -> dict:
    """R-BATCH feature resolve for one Free Spin. Mutates state wind/rejump fields."""
    del guaranteed_gate_policy, line_win_x
    ensure_phase6_state(state)
    state.rejumpState = {"rejumpsThisSpin": 0, "chainDepth": 0, "truncatedThisSpin": 0}
    state.featureBatchIndex = 0

    working = [col[:] for col in board_after_persist]
    regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    mystery_id = config["mysteryModel"]["id"]
    coach_id = config["coachModel"]["id"]
    token_tables = build_token_tables(candidate)
    scale = float(candidate.get("tokenValueScale", 1.0) or 1.0)
    thermal_weights = {str(k): int(v) for k, v in candidate["thermalWeights"].items()}
    max_floor = int(candidate.get("gateMaxFloor", 3))
    weights = {k: int(v) for k, v in candidate["mysteryResultWeights"].items()}

    coaches = []
    transforms = []
    selected_hist = []
    selected, resolved_coach_pos, synthetic = _run_coaches(
        working,
        rng,
        regular_ids=regular_ids,
        coach_id=coach_id,
        mystery_id=mystery_id,
        exclude=set(coach_exclude_types),
        prefer_b=coach_prefer_non_excluded,
        force_if_none=force_coach_if_none,
    )
    for index, symbol in enumerate(selected):
        positions = [
            {"reel": reel, "row": row}
            for reel in range(5)
            for row in range(5)
            if board_after_persist[reel][row] == symbol or working[reel][row] == mystery_id
        ]
        # Rebuild selected positions from transforms applied
        pos_list = []
        for reel in range(5):
            for row in range(5):
                if working[reel][row] == mystery_id and board_after_persist[reel][row] == symbol:
                    pos_list.append({"reel": reel, "row": row})
        coaches.append(
            {
                "coachPosition": (
                    {"reel": resolved_coach_pos[index][0], "row": resolved_coach_pos[index][1]}
                    if index < len(resolved_coach_pos)
                    else {"reel": -1, "row": -1}
                ),
                "selectedSymbolId": symbol,
                "selectedPositions": pos_list,
                "sequenceIndex": index,
                "noOp": False,
                "synthetic": bool(synthetic and index == 0 and not resolved_coach_pos),
            }
        )
        transforms.append({"sourceSymbolId": symbol, "positions": pos_list, "sequenceIndex": index})
        selected_hist.append(symbol)
    _maybe_append_persist_targets(
        state,
        [s for s in selected_hist if s],
        int(config.get("freeSpins", {}).get("maxPersistentTargets", 3)),
    )
    resolved_coaches = set(resolved_coach_pos)

    allow_wind = not stages_maxed(state)
    positions = _mystery_positions(working, mystery_id, None)
    specials: dict[tuple[int, int], dict] = {}
    resolves = []
    for pos, cell in _resolve_mysteries(
        working, positions, rng, weights, token_tables, scale, thermal_weights, allow_wind=allow_wind
    ):
        specials[pos] = cell
        resolves.append({"position": {"reel": pos[0], "row": pos[1]}, **{k: v for k, v in cell.items()}})

    guaranteed_gate_applied = False
    guaranteed_gate_replaced = None
    if guaranteed_gate and not any(cell["kind"] == KIND_GATE for cell in specials.values()):
        candidates = []
        for pos, cell in specials.items():
            if cell["kind"] == KIND_THERMAL:
                candidates.append((0, pos))
            elif cell["kind"] == KIND_TOKEN and int(cell.get("tokenTier") or 9) <= 4:
                candidates.append((1, pos))
        if candidates:
            candidates.sort()
            pos = candidates[0][1]
            old = specials[pos]
            guaranteed_gate_replaced = {
                "position": {"reel": pos[0], "row": pos[1]},
                "replacedResultType": old.get("resultType"),
                "replacedTokenTier": old.get("tokenTier"),
            }
            specials[pos] = _materialise(rng, "GATE_UPGRADE", token_tables, scale, thermal_weights)
            working[pos[0]][pos[1]] = "GATE"
            guaranteed_gate_applied = True
            for entry in resolves:
                if entry["position"]["reel"] == pos[0] and entry["position"]["row"] == pos[1]:
                    entry.clear()
                    entry.update(
                        {
                            "position": {"reel": pos[0], "row": pos[1]},
                            **{k: v for k, v in specials[pos].items()},
                        }
                    )
                    break

    phase6_events: list[dict] = []
    collections: list[dict] = []
    gate_events: list[dict] = []
    floor = max(1, min(max_floor, int(start_floor)))
    feature_raw = 0.0
    batch_index = 0
    rejumps_this_spin = 0
    truncated = 0

    def consume_batch() -> int:
        nonlocal floor, feature_raw, batch_index
        state.featureBatchIndex = batch_index
        floor = _apply_gates(specials, floor, rng, token_tables, scale, max_floor, gate_events)
        _paint_specials(working, specials)
        winds = sorted(
            pos for pos, cell in specials.items() if cell["kind"] == KIND_WIND and not cell.get("processed")
        )
        for pos in winds:
            detail = apply_wind_key(state, rng, specials[pos])
            phase6_events.append(
                {
                    "type": "skyjumpWindKey",
                    "schemaVersion": 2,
                    "position": {"reel": pos[0], "row": pos[1]},
                    **detail,
                }
            )
        feature_raw += _settle_unpaid(specials, state, batch_index, collections, phase6_events)
        return _take_rejumps(specials)

    queue = consume_batch()
    chain = 0
    while queue > 0:
        if chain >= max_chain or rejumps_this_spin >= max_rejumps:
            truncated += queue
            state.rejumpState["truncatedThisSpin"] = truncated
            for _ in range(queue):
                phase6_events.append(
                    {
                        "type": "skyjumpRejumpEnd",
                        "schemaVersion": 2,
                        "chainIndex": chain,
                        "applied": False,
                        "truncated": True,
                        "reason": "MAX_REJUMPS_PER_SPIN" if rejumps_this_spin >= max_rejumps else "MAX_CHAIN_DEPTH",
                    }
                )
            queue = 0
            break
        queue -= 1
        chain += 1
        rejumps_this_spin += 1
        state.rejumpsThisBonus = int(getattr(state, "rejumpsThisBonus", 0)) + 1
        state.rejumpState["rejumpsThisSpin"] = rejumps_this_spin
        state.rejumpState["chainDepth"] = chain
        locked = _locked_positions(working, specials, scatter_cells, resolved_coaches)
        preserved, redropped = _redrop(working, locked, strips, catalogs, rng)
        phase6_events.append(
            {
                "type": "skyjumpRejumpStart",
                "schemaVersion": 2,
                "chainIndex": chain,
                "preservedPositions": preserved,
                "redroppedPositions": redropped,
                "rejumpsThisSpin": rejumps_this_spin,
            }
        )
        phase6_events.append(
            {
                "type": "skyjumpRejumpBoard",
                "schemaVersion": 2,
                "chainIndex": chain,
                "board": [col[:] for col in working],
                "changedCells": [
                    {"reel": cell["reel"], "row": cell["row"], "symbolId": working[cell["reel"]][cell["row"]]}
                    for cell in redropped
                ],
            }
        )
        rejump_eval = evaluate_paylines(
            working,
            paylines=config["paylines"],
            paytable=config["paytable"]["awards"],
            scatter_id=config["symbols"]["scatter"]["id"],
            regular_ids=regular_ids,
        )
        feature_raw += float(rejump_eval["lineWinX"])
        phase6_events.append(
            {
                "type": "skyjumpRejumpLineWins",
                "schemaVersion": 2,
                "chainIndex": chain,
                "lineWins": rejump_eval["wins"],
                "lineWinX": float(rejump_eval["lineWinX"]),
            }
        )
        fresh = {(reel, row) for reel in range(5) for row in range(5) if (reel, row) not in locked}
        working = apply_persistent_targets(working, list(state.persistentMysteryTargets), mystery_id)
        coach_cells = {(reel, row) for reel, row in fresh if working[reel][row] == coach_id}
        selected_new, resolved_new, _unused = _run_coaches(
            working,
            rng,
            regular_ids=regular_ids,
            coach_id=coach_id,
            mystery_id=mystery_id,
            exclude=set(state.persistentMysteryTargets),
            prefer_b=coach_prefer_non_excluded,
            force_if_none=False,
            only_positions=coach_cells,
        )
        for index, symbol in enumerate(selected_new):
            coaches.append(
                {
                    "coachPosition": {"reel": -1, "row": -1},
                    "selectedSymbolId": symbol,
                    "selectedPositions": [],
                    "sequenceIndex": len(coaches),
                    "noOp": False,
                    "synthetic": False,
                    "fromRejump": True,
                }
            )
            selected_hist.append(symbol)
        _maybe_append_persist_targets(
            state,
            [s for s in selected_new if s],
            int(config.get("freeSpins", {}).get("maxPersistentTargets", 3)),
        )
        resolved_coaches.update(resolved_new)
        spawned = [pos for pos in _mystery_positions(working, mystery_id, None) if pos not in specials]
        allow_wind = not stages_maxed(state)
        for pos, cell in _resolve_mysteries(
            working, spawned, rng, weights, token_tables, scale, thermal_weights, allow_wind=allow_wind
        ):
            specials[pos] = cell
            resolves.append({"position": {"reel": pos[0], "row": pos[1]}, **{k: v for k, v in cell.items()}, "fromRejump": True})
        _paint_specials(working, specials)
        batch_index += 1
        queue += consume_batch()
        phase6_events.append(
            {
                "type": "skyjumpRejumpEnd",
                "schemaVersion": 2,
                "chainIndex": chain,
                "applied": True,
                "truncated": False,
                "reason": None,
            }
        )

    # Thermal presentation events from final board specials
    cells = [[empty_cell() for _ in range(5)] for _ in range(5)]
    for (reel, row), cell in specials.items():
        cells[reel][row] = cell

    judge_count = sum(1 for c in collections if c["type"] == "JUDGE")
    head_count = sum(1 for c in collections if c["type"] == "HEAD_JUDGE" and c["pass"] == 1)
    return {
        "paying": True,
        "boardSymbols": working,
        "cells": cells,
        "coaches": coaches,
        "transforms": transforms,
        "resolves": resolves,
        "gateEvents": gate_events,
        "collections": collections,
        "phase6Events": phase6_events,
        "selectedSymbolIds": selected_hist,
        "tokenFloorTier": floor,
        "totalFeatureWinXRaw": feature_raw,
        "coachCount": len([c for c in coaches if not c.get("noOp")]),
        "judgeCount": judge_count,
        "headJudgeCount": head_count,
        "gateCount": len(gate_events),
        "thermalCount": sum(1 for cell in specials.values() if cell["kind"] == KIND_THERMAL),
        "guaranteedGateApplied": guaranteed_gate_applied,
        "guaranteedGateReplaced": guaranteed_gate_replaced,
        "rejumpCount": rejumps_this_spin,
        "windKeyCount": sum(1 for e in phase6_events if e["type"] == "skyjumpWindKey"),
        "truncatedRejumps": truncated,
        "globalFlightMultiplier": global_flight_multiplier(state),
    }


def phase6_enabled(config: dict) -> bool:
    return bool(config.get("freeSpins", {}).get("phase6", {}).get("enabled"))
