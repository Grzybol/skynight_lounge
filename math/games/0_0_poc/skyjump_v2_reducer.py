"""Pure schema-v2 feature reducer. No RNG. Replay events to rebuild state."""

from __future__ import annotations

from copy import deepcopy

from skyjump_v2_reels import COACH_ID, MYSTERY_ID, REGULAR_IDS, SCATTER_ID

TOKEN_IDS = {"T1", "T2", "T3", "T4", "T5", "T6"}
RESULT_SYMBOLS = {
    "THERMAL_LIFT": "THERMAL",
    "GATE_UPGRADE": "GATE",
    "JUDGE": "JUDGE",
    "HEAD_JUDGE": "HEAD_JUDGE",
    "REJUMP": "REJUMP",
    "WIND_KEY": "WIND",
}


def cell_from_symbol(symbol_id: str) -> dict:
    if symbol_id in REGULAR_IDS:
        kind = "regular"
    elif symbol_id == SCATTER_ID:
        kind = "scatter"
    elif symbol_id == COACH_ID:
        kind = "coach"
    elif symbol_id == MYSTERY_ID:
        kind = "mystery"
    elif symbol_id in TOKEN_IDS:
        kind = "token"
    elif symbol_id in {"THERMAL", "THERMAL_LIFT"}:
        kind = "thermal"
    elif symbol_id in {"GATE", "GATE_UPGRADE"}:
        kind = "gate"
    elif symbol_id == "JUDGE":
        kind = "judge"
    elif symbol_id == "HEAD_JUDGE":
        kind = "head_judge"
    elif symbol_id == "REJUMP":
        kind = "rejump"
    elif symbol_id in {"WIND", "WIND_KEY"}:
        kind = "wind"
    else:
        kind = "unknown"
    return {
        "kind": kind,
        "symbolId": symbol_id,
        "tokenTier": None,
        "tokenValueX": None,
        "faceValueX": None,
        "effectiveValueX": None,
        "thermalMult": None,
        "appliedThermals": [],
    }


def initial_state() -> dict:
    return {
        "board": None,
        "lineWinX": 0.0,
        "featureWinX": 0.0,
        "featureWinXRaw": 0.0,
        "totalWinX": 0.0,
        "totalWinXRaw": 0.0,
        "scatterCount": 0,
        "perfectV": False,
        "featureChainStep": 0,
        "coachesResolved": 0,
        "mysteriesOpen": 0,
        "capReached": False,
        "tokenFloorTier": 1,
        "collectorPasses": 0,
        "persistentMysteryTargets": [],
        "runUpMultiplier": 1,
        "takeoffMultiplier": 1,
        "flightMultiplier": {
            "runUp": {"value": 1, "charge": 0},
            "takeoff": {"value": 1, "charge": 0},
            "flight": {"value": 1, "charge": 0},
        },
        "freeSpinsRemaining": 0,
        "amount": 0,
        "bonusActive": False,
        "bonusTier": None,
        "freeSpinsInitial": 0,
        "freeSpinsPlayed": 0,
        "totalFreeSpinsAwarded": 0,
        "upgradeCount": 0,
        "retriggerCount": 0,
        "guaranteedGateUsed": False,
        "coachGuaranteeState": {},
        "bonusWinXRaw": 0.0,
        "bonusWinXCapped": 0.0,
        "triggerSpinWinX": 0.0,
        "roundWinXRaw": 0.0,
        "roundWinXCapped": 0.0,
        "maxWinReached": False,
        "pendingTierUpgrade": None,
        "flightMultiplierRunUp": 1.0,
        "flightMultiplierTakeoff": 1.0,
        "flightMultiplierFlight": 1.0,
        "windKeysCollected": 0,
        "rejumpsThisBonus": 0,
        "featureBatchIndex": 0,
        "globalFlightMultiplier": 1,
        "rejumpState": None,
    }


def clone_board(board: list[list[dict]]) -> list[list[dict]]:
    return [[dict(cell) for cell in col] for col in board]


def _set_cells(state: dict, positions: list[dict], **fields) -> None:
    board = clone_board(state["board"])
    for pos in positions:
        cell = dict(board[pos["reel"]][pos["row"]])
        cell.update(fields)
        board[pos["reel"]][pos["row"]] = cell
    state["board"] = board


def reduce_event(state: dict, event: dict) -> dict:
    next_state = deepcopy(state)
    event_type = event["type"]
    if event_type == "skyjumpSpinStart":
        next_state = initial_state()
        next_state["mode"] = event.get("mode", "BASE")
        next_state["isFreeSpin"] = bool(event.get("isFreeSpin", False))
        next_state["stops"] = list(event.get("stops") or [])
    elif event_type == "skyjumpBoardReveal":
        next_state["board"] = [[cell_from_symbol(symbol) for symbol in col] for col in event["board"]]
    elif event_type == "skyjumpLineWins":
        next_state["lineWinX"] = float(event["lineWinX"])
        next_state["wins"] = event["wins"]
    elif event_type == "skyjumpScatterResult":
        next_state["scatterCount"] = int(event["count"])
        next_state["perfectV"] = bool(event["perfectV"])
        next_state["scatterPositions"] = event["positions"]
    elif event_type == "skyjumpCoachSignal":
        next_state["coachesResolved"] = next_state.get("coachesResolved", 0) + 1
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
        next_state["lastCoach"] = {
            "selectedSymbolId": event.get("selectedSymbolId"),
            "noOp": bool(event.get("noOp")),
        }
    elif event_type == "skyjumpMysteryTransform":
        positions = event["positions"]
        _set_cells(
            next_state,
            positions,
            kind="mystery",
            symbolId=MYSTERY_ID,
            tokenTier=None,
            tokenValueX=None,
            faceValueX=None,
            effectiveValueX=None,
            thermalMult=None,
            appliedThermals=[],
        )
        next_state["mysteriesOpen"] = next_state.get("mysteriesOpen", 0) + len(positions)
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
    elif event_type == "skyjumpMysteryResolve":
        result_type = event["resultType"]
        pos = event["position"]
        if result_type == "FLIGHT_TOKEN":
            face = float(event.get("faceValueX", event["tokenValueX"]))
            if face < 0:
                raise ValueError("token face value cannot be negative")
            _set_cells(
                next_state,
                [pos],
                kind="token",
                symbolId=event["tokenId"],
                tokenTier=event["tokenTier"],
                tokenValueX=face,
                faceValueX=face,
                effectiveValueX=float(event.get("effectiveValueX", face)),
                thermalMult=None,
                appliedThermals=[],
            )
        elif result_type == "THERMAL_LIFT":
            _set_cells(
                next_state,
                [pos],
                kind="thermal",
                symbolId="THERMAL",
                thermalMult=int(event["thermalMult"]),
                tokenTier=None,
                tokenValueX=None,
                faceValueX=None,
                effectiveValueX=None,
                appliedThermals=[],
            )
        elif result_type == "GATE_UPGRADE":
            _set_cells(
                next_state,
                [pos],
                kind="gate",
                symbolId="GATE",
                tokenTier=None,
                tokenValueX=None,
                faceValueX=None,
                effectiveValueX=None,
                thermalMult=None,
                appliedThermals=[],
            )
        elif result_type == "JUDGE":
            _set_cells(
                next_state,
                [pos],
                kind="judge",
                symbolId="JUDGE",
                tokenTier=None,
                tokenValueX=None,
                faceValueX=None,
                effectiveValueX=None,
                thermalMult=None,
                appliedThermals=[],
            )
        elif result_type == "HEAD_JUDGE":
            _set_cells(
                next_state,
                [pos],
                kind="head_judge",
                symbolId="HEAD_JUDGE",
                tokenTier=None,
                tokenValueX=None,
                faceValueX=None,
                effectiveValueX=None,
                thermalMult=None,
                appliedThermals=[],
            )
        elif result_type == "REJUMP":
            _set_cells(
                next_state,
                [pos],
                kind="rejump",
                symbolId="REJUMP",
                tokenTier=None,
                tokenValueX=None,
                faceValueX=None,
                effectiveValueX=None,
                thermalMult=None,
                appliedThermals=[],
            )
        elif result_type == "WIND_KEY":
            _set_cells(
                next_state,
                [pos],
                kind="wind",
                symbolId="WIND",
                tokenTier=None,
                tokenValueX=None,
                faceValueX=None,
                effectiveValueX=None,
                thermalMult=None,
                appliedThermals=[],
            )
        else:
            raise ValueError(f"unsupported mystery result {result_type}")
        next_state["mysteriesOpen"] = max(0, next_state.get("mysteriesOpen", 0) - 1)
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
    elif event_type == "skyjumpGateUpgrade":
        next_state["tokenFloorTier"] = int(event["floorAfter"])
        for rep in event.get("replacements") or []:
            after = rep["after"]
            _set_cells(
                next_state,
                [{"reel": rep["reel"], "row": rep["row"]}],
                kind="token",
                symbolId=f"T{after['tier']}",
                tokenTier=after["tier"],
                tokenValueX=float(after["face"]),
                faceValueX=float(after["face"]),
                effectiveValueX=float(after["face"]),
                appliedThermals=[],
            )
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
        next_state["lastGate"] = {
            "floorBefore": event["floorBefore"],
            "floorAfter": event["floorAfter"],
        }
    elif event_type == "skyjumpThermalLift":
        for token in event.get("affectedTokens") or []:
            cell_pos = {"reel": token["reel"], "row": token["row"]}
            board = clone_board(next_state["board"])
            cell = dict(board[cell_pos["reel"]][cell_pos["row"]])
            # Face stays immutable; only effective + appliedThermals update.
            face = float(cell.get("faceValueX") if cell.get("faceValueX") is not None else cell.get("tokenValueX") or 0)
            if abs(face - float(token["faceValueX"])) > 1e-9:
                raise ValueError("thermal event face mismatch")
            cell["faceValueX"] = face
            cell["tokenValueX"] = face
            cell["effectiveValueX"] = float(token["effectiveValueX"])
            cell["appliedThermals"] = list(token.get("appliedThermals") or [])
            board[cell_pos["reel"]][cell_pos["row"]] = cell
            next_state["board"] = board
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
        next_state["lastThermal"] = {
            "position": event["position"],
            "thermalMult": event["thermalMult"],
        }
    elif event_type in {"skyjumpJudgeCollect", "skyjumpHeadJudgeCollect"}:
        collected = float(event["collectedX"])
        if collected < 0:
            raise ValueError("collection cannot be negative")
        next_state["featureWinX"] = float(next_state.get("featureWinX", 0)) + collected
        next_state["featureWinXRaw"] = float(next_state.get("featureWinXRaw", 0)) + collected
        next_state["collectorPasses"] = int(next_state.get("collectorPasses", 0)) + 1
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
        if "batchIndex" in event:
            next_state["featureBatchIndex"] = int(event["batchIndex"])
        next_state["lastCollection"] = {
            "type": event_type,
            "passIndex": event.get("passIndex"),
            "collectedX": collected,
            "batchIndex": event.get("batchIndex"),
            "flightMultiplierX": event.get("flightMultiplierX"),
        }
    elif event_type == "skyjumpWindKey":
        stages = next_state.get("flightMultiplier")
        if not isinstance(stages, dict):
            stages = {
                "runUp": {"value": 1, "charge": 0},
                "takeoff": {"value": 1, "charge": 0},
                "flight": {"value": 1, "charge": 0},
            }
        else:
            stages = {
                "runUp": dict(stages.get("runUp") or {"value": 1, "charge": 0}),
                "takeoff": dict(stages.get("takeoff") or {"value": 1, "charge": 0}),
                "flight": dict(stages.get("flight") or {"value": 1, "charge": 0}),
            }
        stage_map = {"RUN_UP": "runUp", "TAKEOFF": "takeoff", "FLIGHT": "flight"}
        stage_key = stage_map.get(event.get("selectedStage"))
        if stage_key and event.get("action") != "NO_OP":
            stages[stage_key] = {
                "value": int(event.get("newStageValue", stages[stage_key]["value"])),
                "charge": int(event.get("newCharge", stages[stage_key]["charge"])),
            }
        next_state["flightMultiplier"] = stages
        next_state["flightMultiplierRunUp"] = float(stages["runUp"]["value"])
        next_state["flightMultiplierTakeoff"] = float(stages["takeoff"]["value"])
        next_state["flightMultiplierFlight"] = float(stages["flight"]["value"])
        next_state["runUpMultiplier"] = int(stages["runUp"]["value"])
        next_state["takeoffMultiplier"] = int(stages["takeoff"]["value"])
        next_state["globalFlightMultiplier"] = (
            int(stages["runUp"]["value"])
            * int(stages["takeoff"]["value"])
            * int(stages["flight"]["value"])
        )
        next_state["windKeysCollected"] = int(
            event.get("windKeysCollected", int(next_state.get("windKeysCollected") or 0) + 1)
        )
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
        next_state["lastWindKey"] = {
            "selectedStage": event.get("selectedStage"),
            "action": event.get("action"),
            "oldStageValue": event.get("oldStageValue"),
            "newStageValue": event.get("newStageValue"),
            "oldCharge": event.get("oldCharge"),
            "newCharge": event.get("newCharge"),
            "oldGlobalMultiplier": event.get("oldGlobalMultiplier"),
            "newGlobalMultiplier": event.get("newGlobalMultiplier"),
        }
    elif event_type == "skyjumpRejumpStart":
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
        next_state["rejumpsThisBonus"] = int(next_state.get("rejumpsThisBonus") or 0) + 1
        rejump_state = dict(next_state.get("rejumpState") or {})
        rejump_state.update(
            {
                "chainIndex": int(event["chainIndex"]),
                "rejumpsThisSpin": int(event["rejumpsThisSpin"]),
                "preservedPositions": event.get("preservedPositions"),
                "redroppedPositions": event.get("redroppedPositions"),
            }
        )
        next_state["rejumpState"] = rejump_state
        next_state["lastRejump"] = {"chainIndex": int(event["chainIndex"])}
    elif event_type == "skyjumpRejumpBoard":
        if event.get("board") is not None:
            next_state["board"] = [[cell_from_symbol(symbol) for symbol in col] for col in event["board"]]
        elif event.get("changedCells") and next_state.get("board"):
            board = clone_board(next_state["board"])
            for cell in event["changedCells"]:
                board[cell["reel"]][cell["row"]] = cell_from_symbol(cell["symbolId"])
            next_state["board"] = board
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
    elif event_type == "skyjumpRejumpLineWins":
        line_win = float(event.get("lineWinX") or 0)
        next_state["featureWinX"] = float(next_state.get("featureWinX", 0)) + line_win
        next_state["featureWinXRaw"] = float(next_state.get("featureWinXRaw", 0)) + line_win
        next_state["wins"] = event.get("lineWins", event.get("wins"))
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
    elif event_type == "skyjumpRejumpEnd":
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
        next_state["lastRejump"] = {
            "chainIndex": int(event["chainIndex"]),
            "applied": bool(event.get("applied")),
            "truncated": bool(event.get("truncated")),
            "reason": event.get("reason"),
        }
        rejump_state = dict(next_state.get("rejumpState") or {})
        rejump_state["chainIndex"] = int(event["chainIndex"])
        if event.get("truncated"):
            rejump_state["truncatedThisSpin"] = int(rejump_state.get("truncatedThisSpin") or 0) + 1
        next_state["rejumpState"] = rejump_state
    elif event_type == "skyjumpCapReached":
        next_state["capReached"] = True
        next_state["totalWinXRaw"] = float(event["rawTotalWinX"])
        next_state["totalWinX"] = float(event["cappedTotalWinX"])
        next_state["capDragX"] = float(event["capDragX"])
        # Cap may reduce feature portion.
        line = float(next_state.get("lineWinX", 0))
        next_state["featureWinX"] = max(0.0, float(event["cappedTotalWinX"]) - line)
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
    elif event_type == "skyjumpWorldRecord":
        pos = event.get("position") or {}
        symbol_id = str(event.get("symbolId") or "SPECIAL_WORLD_RECORD")
        if next_state.get("board") and isinstance(pos, dict) and "reel" in pos and "row" in pos:
            reel = int(pos["reel"])
            row = int(pos["row"])
            board = next_state["board"]
            if 0 <= reel < len(board) and 0 <= row < len(board[reel]):
                cell = cell_from_symbol(symbol_id)
                cell["kind"] = "unknown"
                board[reel][row] = cell
        next_state["maxWinReached"] = True
        next_state["capReached"] = True
        next_state["freeSpinsRemaining"] = 0
        next_state["worldRecord"] = {
            "position": pos,
            "bonusTier": str(event.get("bonusTier")),
            "freeSpinIndex": int(event.get("freeSpinIndex") or 0),
            "accruedRoundWinXBefore": float(event.get("accruedRoundWinXBefore") or 0),
            "worldRecordIncrementX": float(event.get("worldRecordIncrementX") or 0),
            "maxWinX": float(event.get("maxWinX") or 50_000),
            "finalRoundWinX": float(event["finalRoundWinX"]),
            "remainingFreeSpinsCancelled": int(event.get("remainingFreeSpinsCancelled") or 0),
            "pendingRejumpsCancelled": bool(event.get("pendingRejumpsCancelled")),
        }
        next_state["roundWinXCapped"] = float(event["finalRoundWinX"])
        next_state["totalWinX"] = float(event["finalRoundWinX"])
        next_state["featureChainStep"] = next_state.get("featureChainStep", 0) + 1
    elif event_type == "skyjumpFreeSpinsStart":
        next_state["bonusActive"] = True
        next_state["bonusTier"] = event["initialTier"]
        next_state["freeSpinsInitial"] = int(event["spinsAwarded"])
        next_state["freeSpinsRemaining"] = int(event["spinsAwarded"])
        next_state["freeSpinsPlayed"] = 0
        next_state["totalFreeSpinsAwarded"] = int(event["spinsAwarded"])
        next_state["triggerSpinWinX"] = float(event.get("triggerSpinWinX") or next_state.get("totalWinX") or 0)
        next_state["tokenFloorTier"] = 1
        next_state["persistentMysteryTargets"] = []
        next_state["guaranteedGateUsed"] = False
        next_state["bonusWinXRaw"] = 0.0
        next_state["bonusWinXCapped"] = 0.0
        next_state["maxWinReached"] = False
        next_state["pendingTierUpgrade"] = None
        next_state["flightMultiplier"] = {
            "runUp": {"value": 1, "charge": 0},
            "takeoff": {"value": 1, "charge": 0},
            "flight": {"value": 1, "charge": 0},
        }
        next_state["flightMultiplierRunUp"] = 1.0
        next_state["flightMultiplierTakeoff"] = 1.0
        next_state["flightMultiplierFlight"] = 1.0
        next_state["runUpMultiplier"] = 1
        next_state["takeoffMultiplier"] = 1
        next_state["globalFlightMultiplier"] = 1
        next_state["windKeysCollected"] = 0
        next_state["rejumpsThisBonus"] = 0
        next_state["featureBatchIndex"] = 0
        next_state["rejumpState"] = None
    elif event_type == "skyjumpFreeSpinStart":
        next_state["isFreeSpin"] = True
        next_state["bonusActive"] = True
        next_state["bonusTier"] = event["currentTier"]
        next_state["freeSpinsRemaining"] = int(event["spinsRemainingBefore"])
        next_state["board"] = None
        next_state["lineWinX"] = 0.0
        next_state["featureWinX"] = 0.0
        next_state["featureWinXRaw"] = 0.0
        next_state["coachesResolved"] = 0
        next_state["mysteriesOpen"] = 0
        next_state["pendingTierUpgrade"] = None
    elif event_type == "skyjumpPersistentTargetsApply":
        _set_cells(
            next_state,
            event["positions"],
            kind="mystery",
            symbolId=MYSTERY_ID,
            tokenTier=None,
            tokenValueX=None,
            faceValueX=None,
            effectiveValueX=None,
            thermalMult=None,
            appliedThermals=[],
        )
    elif event_type == "skyjumpPersistentTargetsUpdate":
        next_state["persistentMysteryTargets"] = list(event["persistentMysteryTargets"])
    elif event_type == "skyjumpGuaranteedGate":
        next_state["guaranteedGateUsed"] = True
        _set_cells(
            next_state,
            [event["position"]],
            kind="gate",
            symbolId="GATE",
            tokenTier=None,
            tokenValueX=None,
            faceValueX=None,
            effectiveValueX=None,
            thermalMult=None,
            appliedThermals=[],
        )
    elif event_type == "skyjumpBonusUpgrade":
        added = int(event["spinsAdded"])
        next_state["totalFreeSpinsAwarded"] = int(event.get("totalFreeSpinsAwarded") or (int(next_state.get("totalFreeSpinsAwarded") or 0) + added))
        if "spinsRemainingAfter" in event:
            next_state["freeSpinsRemaining"] = int(event["spinsRemainingAfter"])
        if added or int(event.get("spinsRequested") or 0):
            next_state["retriggerCount"] = int(next_state.get("retriggerCount") or 0) + 1
        if event.get("tierChanged"):
            next_state["upgradeCount"] = int(next_state.get("upgradeCount") or 0) + 1
            next_state["pendingTierUpgrade"] = event["toTier"]
    elif event_type == "skyjumpFreeSpinEnd":
        next_state["freeSpinsPlayed"] = int(event["spinIndex"])
        next_state["freeSpinsRemaining"] = int(event["spinsRemainingAfter"])
        next_state["bonusWinXCapped"] = float(event["bonusWinRunningX"])
        next_state["board"] = None
        next_state["lineWinX"] = 0.0
        next_state["featureWinX"] = 0.0
    elif event_type == "skyjumpFreeSpinState":
        for key in (
            "bonusActive",
            "bonusTier",
            "freeSpinsInitial",
            "freeSpinsRemaining",
            "freeSpinsPlayed",
            "totalFreeSpinsAwarded",
            "upgradeCount",
            "retriggerCount",
            "tokenFloorTier",
            "guaranteedGateUsed",
            "bonusWinXRaw",
            "bonusWinXCapped",
            "triggerSpinWinX",
            "roundWinXRaw",
            "roundWinXCapped",
            "maxWinReached",
            "pendingTierUpgrade",
            "flightMultiplierRunUp",
            "flightMultiplierTakeoff",
            "flightMultiplierFlight",
            "windKeysCollected",
            "rejumpsThisBonus",
            "featureBatchIndex",
            "globalFlightMultiplier",
            "rejumpState",
        ):
            if key in event:
                next_state[key] = event[key]
        next_state["persistentMysteryTargets"] = list(event.get("persistentMysteryTargets") or [])
        next_state["coachGuaranteeState"] = dict(event.get("coachGuaranteeState") or {})
        if isinstance(event.get("flightMultiplier"), dict):
            stages = event["flightMultiplier"]
            next_state["flightMultiplier"] = {
                "runUp": {
                    "value": int((stages.get("runUp") or {}).get("value", event.get("flightMultiplierRunUp", 1))),
                    "charge": int((stages.get("runUp") or {}).get("charge", 0)),
                },
                "takeoff": {
                    "value": int((stages.get("takeoff") or {}).get("value", event.get("flightMultiplierTakeoff", 1))),
                    "charge": int((stages.get("takeoff") or {}).get("charge", 0)),
                },
                "flight": {
                    "value": int((stages.get("flight") or {}).get("value", event.get("flightMultiplierFlight", 1))),
                    "charge": int((stages.get("flight") or {}).get("charge", 0)),
                },
            }
        else:
            next_state["flightMultiplier"] = {
                "runUp": {"value": int(event.get("flightMultiplierRunUp", 1)), "charge": 0},
                "takeoff": {"value": int(event.get("flightMultiplierTakeoff", 1)), "charge": 0},
                "flight": {"value": int(event.get("flightMultiplierFlight", 1)), "charge": 0},
            }
        stages = next_state["flightMultiplier"]
        next_state["runUpMultiplier"] = int(stages["runUp"]["value"])
        next_state["takeoffMultiplier"] = int(stages["takeoff"]["value"])
        if "globalFlightMultiplier" not in event:
            next_state["globalFlightMultiplier"] = (
                int(stages["runUp"]["value"])
                * int(stages["takeoff"]["value"])
                * int(stages["flight"]["value"])
            )
        next_state["board"] = None
    elif event_type == "skyjumpFreeSpinsEnd":
        next_state["bonusActive"] = False
        next_state["freeSpinsRemaining"] = 0
        next_state["freeSpinsPlayed"] = int(event["totalSpinsPlayed"])
        next_state["bonusTier"] = event["finalTier"]
        next_state["bonusWinXCapped"] = float(event["bonusWinX"])
        next_state["bonusWinXRaw"] = float(event.get("bonusWinXRaw") or event["bonusWinX"])
        next_state["triggerSpinWinX"] = float(event["triggerSpinWinX"])
        next_state["roundWinXRaw"] = float(event["roundWinXRaw"])
        next_state["roundWinXCapped"] = float(event["roundWinXCapped"])
        next_state["upgradeCount"] = int(event["upgradeCount"])
        next_state["retriggerCount"] = int(event["retriggerCount"])
        next_state["maxWinReached"] = bool(event["maxWinReached"])
        next_state["tokenFloorTier"] = int(event["tokenFloorTier"])
        next_state["persistentMysteryTargets"] = list(event.get("persistentMysteryTargets") or [])
        next_state["guaranteedGateUsed"] = bool(event["guaranteedGateUsed"])
        next_state["totalWinX"] = float(event["roundWinXCapped"])
        next_state["board"] = None
        if next_state["roundWinXCapped"] > 50_000 + 1e-6:
            raise ValueError("capped round cannot exceed max win")
    elif event_type == "skyjumpResult":
        next_state["featureWinX"] = float(event["totalFeatureWinX"])
        next_state["featureWinXRaw"] = float(event.get("totalFeatureWinXRaw", event["totalFeatureWinX"]))
        next_state["totalWinX"] = float(event["totalWinX"])
        next_state["totalWinXRaw"] = float(event.get("totalWinXRaw", event["totalWinX"]))
        next_state["amount"] = int(event["amount"])
        next_state["tokenFloorTier"] = int(event.get("tokenFloorTier", next_state.get("tokenFloorTier", 1)))
        next_state["capReached"] = bool(event.get("capHit", next_state.get("capReached", False)))
        if next_state["featureWinX"] < 0 or next_state["totalWinX"] < 0:
            raise ValueError("payout cannot be negative")
        if next_state["totalWinX"] > 50_000 + 1e-9:
            raise ValueError("capped total cannot exceed max win")
    elif event_type in {"setTotalWin", "finalWin"}:
        next_state["amount"] = int(event["amount"])
    else:
        raise ValueError(f"unsupported event {event_type}")
    return next_state


def reduce_events(events: list[dict], state: dict | None = None) -> dict:
    current = initial_state() if state is None else deepcopy(state)
    for event in events:
        current = reduce_event(current, event)
    return current


def board_symbol_grid(state: dict) -> list[list[str]]:
    return [[cell["symbolId"] for cell in col] for col in state["board"]]
