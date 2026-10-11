"""Phase 4A research-only paying feature economy.

Does NOT modify live Phase 3 config. Tokens keep immutable face values.
Thermal multiplies into effective value only. Collectors pay feature RTP.
"""

from __future__ import annotations

from copy import deepcopy

from skyjump_v2_features import coach_positions, eligible_regular_types, mystery_positions, positions_of
from skyjump_v2_reels import COACH_ID, MYSTERY_ID
from skyjump_v2_tokens import DEFAULT_VALUES, TIER_IDS, TIER_NAMES, sample_token

RESULT_ORDER = ("FLIGHT_TOKEN", "THERMAL_LIFT", "GATE_UPGRADE", "JUDGE", "HEAD_JUDGE")
THERMAL_MULTS = (2, 3, 4, 5, 10, 20)
MAX_WIN_X = 50_000.0
BOARD_SYMBOL_FOR_RESULT = {
    "THERMAL_LIFT": "THERMAL",
    "GATE_UPGRADE": "GATE",
    "JUDGE": "JUDGE",
    "HEAD_JUDGE": "HEAD_JUDGE",
}


def _weighted_pick(rng, items: list, weights: list[int]):
    return rng.choices(items, weights=weights, k=1)[0]


def build_token_tables(candidate: dict) -> dict:
    tier_weights = [int(candidate["tokenTierWeights"][str(tier)]) for tier in range(1, 7)]
    value_weights = {
        tier: [int(candidate["tokenValueWeights"][str(tier)][str(value)]) for value in DEFAULT_VALUES[tier]]
        for tier in range(1, 7)
    }
    return {
        "doNotAutoPay": False,
        "t6Id": TIER_NAMES[6],
        "specialWorldRecordId": "SPECIAL_WORLD_RECORD",
        "order": list(range(1, 7)),
        "ids": dict(TIER_IDS),
        "names": dict(TIER_NAMES),
        "tierWeights": tier_weights,
        "values": {tier: list(DEFAULT_VALUES[tier]) for tier in range(1, 7)},
        "valueWeights": value_weights,
    }


def _mystery_weights_for_state(candidate: dict, tokens_so_far: int) -> dict[str, int]:
    """Independent table by default; optional conditioned collector tables for 4A.2 research."""
    if candidate.get("conditionalCollectors"):
        if tokens_so_far > 0:
            table = candidate.get("mysteryResultWeightsWhenToken") or candidate["mysteryResultWeights"]
        else:
            table = candidate.get("mysteryResultWeightsNoToken") or candidate["mysteryResultWeights"]
        return {label: int(table[label]) for label in RESULT_ORDER}
    return {label: int(candidate["mysteryResultWeights"][label]) for label in RESULT_ORDER}


def sample_mystery_result(rng, candidate: dict, token_tables: dict, *, tokens_so_far: int = 0) -> dict:
    labels = list(RESULT_ORDER)
    weight_map = _mystery_weights_for_state(candidate, tokens_so_far)
    weights = [weight_map[label] for label in labels]
    kind = _weighted_pick(rng, labels, weights)
    if kind == "FLIGHT_TOKEN":
        token = sample_token(rng, token_tables)
        scale = float(candidate.get("tokenValueScale", 1.0) or 1.0)
        return {
            "resultType": "FLIGHT_TOKEN",
            "kind": "token",
            "tokenTier": token["tokenTier"],
            "tokenId": token["tokenId"],
            "tokenName": token["tokenName"],
            "tokenValueX": float(token["tokenValueX"]) * scale,
            "thermalMult": None,
        }
    if kind == "THERMAL_LIFT":
        mults = list(THERMAL_MULTS)
        weights_t = [int(candidate["thermalWeights"][str(mult)]) for mult in mults]
        return {
            "resultType": "THERMAL_LIFT",
            "kind": "thermal",
            "thermalMult": int(_weighted_pick(rng, mults, weights_t)),
            "tokenTier": None,
            "tokenValueX": None,
        }
    if kind == "GATE_UPGRADE":
        return {"resultType": "GATE_UPGRADE", "kind": "gate", "thermalMult": None, "tokenTier": None, "tokenValueX": None}
    if kind == "JUDGE":
        return {"resultType": "JUDGE", "kind": "judge", "thermalMult": None, "tokenTier": None, "tokenValueX": None}
    return {"resultType": "HEAD_JUDGE", "kind": "head_judge", "thermalMult": None, "tokenTier": None, "tokenValueX": None}


def neighbours(reel: int, row: int) -> list[tuple[int, int]]:
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = reel + dr, row + dc
            if 0 <= nr < 5 and 0 <= nc < 5:
                out.append((nr, nc))
    return out


def sample_token_at_floor(rng, token_tables: dict, floor_tier: int, *, scale: float = 1.0) -> dict:
    """Replacement when Gate raises floor: legal value for tier == floor_tier."""
    values = token_tables["values"][floor_tier]
    weights = token_tables["valueWeights"][floor_tier]
    value = float(_weighted_pick(rng, values, weights)) * float(scale)
    return {
        "kind": "token",
        "resultType": "FLIGHT_TOKEN",
        "tokenTier": floor_tier,
        "tokenId": token_tables["ids"][floor_tier],
        "tokenName": token_tables["names"][floor_tier],
        "tokenValueX": value,
        "thermalMult": None,
        "faceValueX": value,
        "effectiveValueX": value,
        "appliedThermals": [],
    }


def empty_cell() -> dict:
    return {
        "kind": "empty",
        "resultType": None,
        "tokenTier": None,
        "tokenId": None,
        "tokenName": None,
        "tokenValueX": None,
        "faceValueX": None,
        "effectiveValueX": None,
        "thermalMult": None,
        "appliedThermals": [],
    }


def resolve_paying_features(
    board: list[list[str]],
    rng,
    *,
    config: dict,
    candidate: dict,
    line_win_x: float = 0.0,
    enable_thermal: bool = True,
    enable_gate: bool = True,
    enable_head_judge: bool = True,
    enable_judge: bool = True,
    start_floor: int = 1,
    coach_exclude_types: set[str] | None = None,
    coach_prefer_non_excluded: bool = False,
    force_coach_if_none: bool = False,
    guaranteed_gate: bool = False,
    guaranteed_gate_policy: str = "token_or_thermal",
) -> dict:
    """Research resolver. Does not mutate the live Phase 3 config path.

    Optional Free Spin hooks (Phase 5A) default off / BASE-compatible:
    - start_floor: persist Gate floor across bonus spins
    - coach_prefer_non_excluded: behaviour B for persistent Mystery targets
    - force_coach_if_none: Perfect V guaranteed Coach activation
    - guaranteed_gate: replace one eligible Mystery with GATE_UPGRADE if none natural
    """
    working_symbols = [col[:] for col in board]
    regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    coach_id = config["coachModel"]["id"]
    mystery_id = config["mysteryModel"]["id"]
    token_tables = build_token_tables(candidate)
    max_floor = int(candidate["gateMaxFloor"])
    max_win = float(candidate.get("maxWinX", MAX_WIN_X))
    exclude = set(coach_exclude_types or ())

    coaches = []
    transforms = []
    selected_hist: list[str] = []
    mystery_counts: list[int] = []

    coach_list = coach_positions(board, coach_id)
    synthetic_coach = False
    if force_coach_if_none and not coach_list:
        coach_list = [{"reel": -1, "row": -1}]
        synthetic_coach = True

    for sequence, coach in enumerate(coach_list):
        eligible = eligible_regular_types(working_symbols, regular_ids)
        payload = {
            "coachPosition": coach,
            "sequenceIndex": sequence,
            "eligibleSymbolIds": eligible,
            "synthetic": synthetic_coach and sequence == 0 and coach.get("reel", 0) < 0,
        }
        if not eligible:
            payload.update(
                {
                    "selectedSymbolId": None,
                    "selectedPositions": [],
                    "noOp": True,
                    "reason": "noEligibleRegularType",
                }
            )
            coaches.append(payload)
            continue
        pool = eligible
        if coach_prefer_non_excluded:
            preferred = [symbol for symbol in eligible if symbol not in exclude]
            if preferred:
                pool = preferred
        selected = rng.choice(pool)
        selected_positions = positions_of(working_symbols, selected)
        for pos in selected_positions:
            working_symbols[pos["reel"]][pos["row"]] = mystery_id
        payload.update(
            {
                "selectedSymbolId": selected,
                "selectedPositions": selected_positions,
                "noOp": False,
            }
        )
        coaches.append(payload)
        selected_hist.append(selected)
        mystery_counts.append(len(selected_positions))
        transforms.append(
            {
                "sourceSymbolId": selected,
                "positions": selected_positions,
                "sequenceIndex": sequence,
            }
        )

    cells = [[empty_cell() for _ in range(5)] for _ in range(5)]
    resolves = []
    tokens_so_far = 0
    for pos in mystery_positions(working_symbols, mystery_id):
        result = sample_mystery_result(rng, candidate, token_tables, tokens_so_far=tokens_so_far)
        # Soft-disable flags keep identity for board geometry but mute payment effects.
        # (Hard-resample-as-token would bias counterfactuals by adding extra faces.)
        if result["resultType"] == "THERMAL_LIFT" and not enable_thermal:
            # Keep thermal cell but multiplier will be ignored later.
            result = {**result, "thermalMult": 1, "_muted": True}
        if result["resultType"] == "GATE_UPGRADE" and not enable_gate:
            result = {**result, "_muted": True}
        if result["resultType"] == "HEAD_JUDGE" and not enable_head_judge:
            result = {**result, "_muted": True}
        if result["resultType"] == "JUDGE" and not enable_judge:
            result = {**result, "_muted": True}

        cell = empty_cell()
        cell.update(result)
        if cell.get("_muted") and cell["resultType"] in ("JUDGE", "HEAD_JUDGE"):
            # Muted collectors occupy a cell but pay nothing / are not collected.
            cell["kind"] = "muted_collector"
        if cell.get("_muted") and cell["resultType"] == "GATE_UPGRADE":
            cell["kind"] = "muted_gate"
        if cell.get("_muted") and cell["resultType"] == "THERMAL_LIFT":
            cell["kind"] = "muted_thermal"
        if cell["kind"] == "token":
            cell["faceValueX"] = float(cell["tokenValueX"])
            cell["effectiveValueX"] = float(cell["tokenValueX"])
            cell["appliedThermals"] = []
            working_symbols[pos["reel"]][pos["row"]] = cell["tokenId"]
            tokens_so_far += 1
        else:
            working_symbols[pos["reel"]][pos["row"]] = BOARD_SYMBOL_FOR_RESULT[cell["resultType"]]
        cell["position"] = pos
        cells[pos["reel"]][pos["row"]] = cell
        resolves.append({"position": pos, **{k: v for k, v in cell.items() if k != "position"}})

    # Optional World Cup / Perfect V guaranteed Gate (research): replace one eligible
    # non-collector Mystery identity — never add a hidden Mystery, never touch T5/T6.
    guaranteed_gate_applied = False
    guaranteed_gate_replaced = None
    if guaranteed_gate:
        natural_gate = any(cell["kind"] == "gate" for col in cells for cell in col)
        if not natural_gate:
            candidates_pos = []
            for reel in range(5):
                for row in range(5):
                    cell = cells[reel][row]
                    if cell["kind"] == "thermal":
                        candidates_pos.append((0, reel, row))
                    elif cell["kind"] == "token":
                        tier = int(cell["tokenTier"] or 0)
                        if tier <= 4:
                            candidates_pos.append((1, reel, row))
                        # T5/T6 deliberately ineligible
                    # Judge / Head Judge excluded under default policy
            if guaranteed_gate_policy == "token_thermal_or_judge":
                for reel in range(5):
                    for row in range(5):
                        if cells[reel][row]["kind"] in ("judge", "head_judge"):
                            candidates_pos.append((2, reel, row))
            if candidates_pos:
                candidates_pos.sort()
                _prio, reel, row = candidates_pos[0]
                cell = cells[reel][row]
                guaranteed_gate_replaced = {
                    "position": {"reel": reel, "row": row},
                    "replacedResultType": cell.get("resultType"),
                    "replacedKind": cell.get("kind"),
                    "replacedTokenTier": cell.get("tokenTier"),
                }
                if cell["kind"] == "token":
                    tokens_so_far = max(0, tokens_so_far - 1)
                cell.clear()
                cell.update(empty_cell())
                cell.update(
                    {
                        "resultType": "GATE_UPGRADE",
                        "kind": "gate",
                        "thermalMult": None,
                        "tokenTier": None,
                        "tokenValueX": None,
                        "position": {"reel": reel, "row": row},
                    }
                )
                working_symbols[reel][row] = BOARD_SYMBOL_FOR_RESULT["GATE_UPGRADE"]
                guaranteed_gate_applied = True
                # Keep resolves list coherent for audits
                for entry in resolves:
                    if entry["position"]["reel"] == reel and entry["position"]["row"] == row:
                        entry.clear()
                        entry.update({"position": {"reel": reel, "row": row}, **{k: v for k, v in cell.items() if k != "position"}})
                        break

    # 2. Gate upgrades (sequential)
    floor = max(1, min(max_floor, int(start_floor)))
    gate_events = []
    upgraded_tokens = 0
    face_sum_before_gate = 0.0
    for reel in range(5):
        for row in range(5):
            cell = cells[reel][row]
            if cell["kind"] == "token":
                face_sum_before_gate += float(cell["faceValueX"])
    gates = [
        (reel, row)
        for reel in range(5)
        for row in range(5)
        if cells[reel][row]["kind"] == "gate"
    ]
    gates.sort()
    for reel, row in gates:
        before = floor
        if floor < max_floor:
            floor = min(max_floor, floor + 1)
        replacements = []
        if floor > before:
            for tr in range(5):
                for tc in range(5):
                    cell = cells[tr][tc]
                    if cell["kind"] != "token":
                        continue
                    if int(cell["tokenTier"]) >= floor:
                        continue
                    replacement = sample_token_at_floor(
                        rng,
                        token_tables,
                        floor,
                        scale=float(candidate.get("tokenValueScale", 1.0) or 1.0),
                    )
                    old = {
                        "tier": cell["tokenTier"],
                        "face": cell["faceValueX"],
                    }
                    cell.update(replacement)
                    working_symbols[tr][tc] = cell["tokenId"]
                    upgraded_tokens += 1
                    replacements.append(
                        {
                            "reel": tr,
                            "row": tc,
                            "before": old,
                            "after": {"tier": cell["tokenTier"], "face": cell["faceValueX"]},
                        }
                    )
        gate_events.append(
            {
                "position": {"reel": reel, "row": row},
                "floorBefore": before,
                "floorAfter": floor,
                "replacements": replacements,
                "guaranteed": guaranteed_gate_applied
                and reel == gates[0][0]
                and row == gates[0][1]
                if gates
                else False,
            }
        )

    # 3. Thermal effective values (faces immutable)
    thermal_hits_on_tokens = 0
    tokens_hit_ge2 = 0
    thermals = [
        (reel, row, cells[reel][row]["thermalMult"])
        for reel in range(5)
        for row in range(5)
        if cells[reel][row]["kind"] == "thermal"
    ]
    for reel, row, mult in thermals:
        for nr, nc in neighbours(reel, row):
            cell = cells[nr][nc]
            if cell["kind"] != "token":
                continue
            cell["appliedThermals"].append(int(mult))
            thermal_hits_on_tokens += 1

    raw_face_sum = 0.0
    effective_sum = 0.0
    token_count = 0
    for reel in range(5):
        for row in range(5):
            cell = cells[reel][row]
            if cell["kind"] != "token":
                continue
            token_count += 1
            face = float(cell["faceValueX"])
            raw_face_sum += face
            product = 1.0
            for mult in cell["appliedThermals"]:
                product *= float(mult)
            if len(cell["appliedThermals"]) >= 2:
                tokens_hit_ge2 += 1
            effective = face * product
            cell["effectiveValueX"] = effective
            # Face remains stored separately and unchanged.
            assert cell["faceValueX"] == face
            effective_sum += effective
    gate_face_uplift = max(0.0, raw_face_sum - face_sum_before_gate)

    # 4. Collectors
    collections = []
    feature_raw = 0.0
    judge_count = 0
    head_judge_count = 0
    judge_contrib = 0.0
    head_contrib = 0.0
    collectors = []
    for reel in range(5):
        for row in range(5):
            kind = cells[reel][row]["kind"]
            if kind == "judge":
                collectors.append(("judge", reel, row))
            elif kind == "head_judge":
                collectors.append(("head_judge", reel, row))
    collectors.sort(key=lambda row: (row[1], row[2], 0 if row[0] == "judge" else 1))

    def _token_contributions() -> list[dict]:
        rows = []
        for tr in range(5):
            for tc in range(5):
                token = cells[tr][tc]
                if token["kind"] != "token":
                    continue
                rows.append(
                    {
                        "reel": tr,
                        "row": tc,
                        "tokenTier": int(token["tokenTier"]),
                        "tokenId": token["tokenId"],
                        "faceValueX": float(token["faceValueX"]),
                        "effectiveValueX": float(token["effectiveValueX"]),
                        "appliedThermals": list(token.get("appliedThermals") or []),
                    }
                )
        return rows

    for kind, reel, row in collectors:
        if kind == "judge":
            payout = effective_sum
            contributions = _token_contributions()
            collections.append(
                {
                    "type": "JUDGE",
                    "pass": 1,
                    "position": {"reel": reel, "row": row},
                    "collectedX": payout,
                    "tokenContributions": contributions,
                    "effectiveTokenSumX": effective_sum,
                }
            )
            feature_raw += payout
            judge_contrib += payout
            judge_count += 1
        else:
            # Two consecutive passes, nothing between them in Phase 4B.
            for pass_index in (1, 2):
                payout = effective_sum
                contributions = _token_contributions()
                collections.append(
                    {
                        "type": "HEAD_JUDGE",
                        "pass": pass_index,
                        "position": {"reel": reel, "row": row},
                        "collectedX": payout,
                        "tokenContributions": contributions,
                        "effectiveTokenSumX": effective_sum,
                    }
                )
                feature_raw += payout
                head_contrib += payout
            head_judge_count += 1

    total_raw = float(line_win_x) + feature_raw
    total_capped = min(total_raw, max_win)
    feature_capped = max(0.0, total_capped - float(line_win_x))
    cap_hit = total_raw > max_win
    cap_drag = total_raw - total_capped if cap_hit else 0.0

    n_coach = len(coaches)
    has_feature_win = feature_raw > 0
    dead_coach = n_coach > 0 and not has_feature_win
    tokens_no_collect = token_count > 0 and judge_count == 0 and head_judge_count == 0
    has_collector = judge_count > 0 or head_judge_count > 0
    has_modifier_only = (
        token_count == 0
        and not has_collector
        and (len(thermals) > 0 or len(gates) > 0)
    )
    if dead_coach:
        if token_count > 0 and not has_collector:
            dead_reason = "tokens_no_collector"
        elif has_collector and token_count == 0:
            dead_reason = "collector_no_tokens"
        elif has_modifier_only:
            dead_reason = "modifier_only"
        else:
            dead_reason = "other"
    else:
        dead_reason = None

    return {
        "coaches": coaches,
        "transforms": transforms,
        "resolves": resolves,
        "selectedSymbolIds": selected_hist,
        "mysteriesPerCoach": mystery_counts,
        "cells": cells,
        "workingBoard": working_symbols,
        "gateEvents": gate_events,
        "tokenFloorTier": floor,
        "collections": collections,
        "tokenCount": token_count,
        "rawFaceSumX": raw_face_sum,
        "effectiveTokenSumX": effective_sum,
        "thermalCount": len(thermals),
        "gateCount": len(gates),
        "judgeCount": judge_count,
        "headJudgeCount": head_judge_count,
        "collectorPasses": len(collections),
        "upgradedTokens": upgraded_tokens,
        "thermalHitsOnTokens": thermal_hits_on_tokens,
        "tokensHitByGe2Thermals": tokens_hit_ge2,
        "judgeContributionX": judge_contrib,
        "headJudgeContributionX": head_contrib,
        "faceSumBeforeGateX": face_sum_before_gate,
        "gateFaceUpliftX": gate_face_uplift,
        "thermalUpliftProxyX": max(0.0, effective_sum - raw_face_sum),
        "totalFeatureWinXRaw": feature_raw,
        "totalFeatureWinXCapped": feature_capped,
        "totalWinXRaw": total_raw,
        "totalWinXCapped": total_capped,
        "capHit": cap_hit,
        "capDragX": cap_drag,
        "hasFeatureWin": has_feature_win,
        "deadCoach": dead_coach,
        "deadReason": dead_reason,
        "tokensWithoutCollector": tokens_no_collect,
        "coachCount": n_coach,
        "multiCoach": n_coach >= 2,
        "conditionalCollectors": bool(candidate.get("conditionalCollectors")),
        "guaranteedGateApplied": guaranteed_gate_applied,
        "guaranteedGateReplaced": guaranteed_gate_replaced,
        "startFloor": max(1, min(max_floor, int(start_floor))),
    }
