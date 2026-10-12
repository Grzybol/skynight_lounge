"""Live Phase 5B Free Spin rounds. One economic book. No extra wager.

Uses the promoted `freeSpins` section. Does not alter BASE resolution when
no bonus triggers.
"""

from __future__ import annotations

from skyjump_v2_events import round_book_amount, round_to_v2_events
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import (
    TIERS,
    BonusCandidate,
    FreeSpinState,
    new_bonus_state,
    resolve_fs_spin,
)
from skyjump_v2_resolve import resolve_v2_base

TIER_ORDER = list(TIERS)


def bonus_candidate_from_config(config: dict) -> BonusCandidate:
    section = config["freeSpins"]
    if section.get("candidateOrigin") != "FS5A_U1_P2_M40_mid_E15j2":
        raise ValueError("live free spins are pinned to the approved Phase 5A candidate")
    tiers = section["tiers"]
    by_tier = None
    if section.get("phase6", {}).get("enabled"):
        by_tier = {
            tier: {key: int(value) for key, value in tiers[tier]["mysteryResultWeights"].items()}
            for tier in TIER_ORDER
        }
        for tier, table in by_tier.items():
            if sum(table.values()) != 1000:
                raise ValueError(f"{tier} mystery weights sum {sum(table.values())}")
            if "REJUMP" not in table or "WIND_KEY" not in table:
                raise ValueError(f"{tier} missing Phase 6 mystery keys")
    return BonusCandidate(
        id=section["candidateOrigin"],
        upgradeRule=section["upgradeModel"],
        initialSpins=int(section["initialSpins"]),
        maxFreeSpins=int(section["maxSpins"]),
        maxPersistentTargets=int(section["maxPersistentTargets"]),
        duplicateTargetBehaviour=section["duplicateTargetBehaviour"],
        guaranteedGatePolicy=section["guaranteedGatePolicy"],
        tierReels={tier: [list(strip) for strip in tiers[tier]["strips"]] for tier in TIER_ORDER},
        maxWinX=float(section.get("maxWinX", 50_000)),
        mysteryResultWeights={
            key: int(value) for key, value in section["economy"]["mysteryResultWeights"].items()
        },
        mysteryResultWeightsByTier=by_tier,
        tokenValueScale=float(section["economy"]["tokenValueScale"]),
    )


def classify_base_trigger(scatter: dict) -> tuple[str | None, str | None]:
    """Perfect V pattern overrides scatter-count tier selection."""
    if scatter.get("perfectV"):
        return "PERFECT_V", "PERFECT_V"
    count = int(scatter.get("count") or 0)
    if count >= 5:
        return "WORLD_CUP", "SCATTER_5_PLUS"
    if count == 4:
        return "SKI_FLYING", "SCATTER_4"
    if count == 3:
        return "LARGE_HILL", "SCATTER_3"
    return None, None


def _persist_positions(board: list[list[str]], targets: list[str]) -> list[dict]:
    wanted = set(targets)
    found = []
    if not wanted:
        return found
    for reel, col in enumerate(board):
        for row, symbol in enumerate(col):
            if symbol in wanted:
                found.append({"reel": reel, "row": row, "symbolId": symbol})
    return found


def _feature_events(features: dict) -> list[dict]:
    events = []
    for coach in features.get("coaches") or []:
        events.append(
            {
                "type": "skyjumpCoachSignal",
                "schemaVersion": 2,
                "coachPosition": coach["coachPosition"],
                "selectedSymbolId": coach["selectedSymbolId"],
                "selectedPositions": coach["selectedPositions"],
                "sequenceIndex": coach["sequenceIndex"],
                "noOp": bool(coach.get("noOp")),
                "reason": coach.get("reason"),
                "synthetic": bool(coach.get("synthetic")),
                "guaranteed": bool(coach.get("synthetic")),
            }
        )
        if coach.get("noOp"):
            continue
        match = next(
            (
                row
                for row in features.get("transforms") or []
                if row["sequenceIndex"] == coach["sequenceIndex"]
            ),
            None,
        )
        if match:
            events.append(
                {
                    "type": "skyjumpMysteryTransform",
                    "schemaVersion": 2,
                    "sourceSymbolId": match["sourceSymbolId"],
                    "positions": match["positions"],
                    "sequenceIndex": match["sequenceIndex"],
                    "persistent": False,
                }
            )
    for row in features.get("resolves") or []:
        result_type = row.get("resultType") or "FLIGHT_TOKEN"
        payload = {
            "type": "skyjumpMysteryResolve",
            "schemaVersion": 2,
            "position": row["position"],
            "resultType": result_type,
        }
        if result_type == "FLIGHT_TOKEN":
            face = float(row.get("faceValueX") if row.get("faceValueX") is not None else row["tokenValueX"])
            payload.update(
                {
                    "tokenTier": row["tokenTier"],
                    "tokenId": row["tokenId"],
                    "tokenName": row["tokenName"],
                    "tokenValueX": face,
                    "faceValueX": face,
                    "effectiveValueX": float(row.get("effectiveValueX") if row.get("effectiveValueX") is not None else face),
                }
            )
        elif result_type == "THERMAL_LIFT":
            payload["thermalMult"] = int(row["thermalMult"])
        events.append(payload)
    replaced = features.get("guaranteedGateReplaced")
    if features.get("guaranteedGateApplied") and replaced:
        events.append(
            {
                "type": "skyjumpGuaranteedGate",
                "schemaVersion": 2,
                "position": replaced["position"],
                "replacedResultType": replaced["replacedResultType"],
                "replacedTokenTier": replaced["replacedTokenTier"],
            }
        )
    for gate in features.get("gateEvents") or []:
        events.append(
            {
                "type": "skyjumpGateUpgrade",
                "schemaVersion": 2,
                "position": gate["position"],
                "floorBefore": gate["floorBefore"],
                "floorAfter": gate["floorAfter"],
                "replacements": gate["replacements"],
            }
        )
    if features.get("paying"):
        for reel, col in enumerate(features.get("cells") or []):
            for row_index, cell in enumerate(col):
                if cell.get("kind") != "thermal":
                    continue
                affected = []
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = reel + dr, row_index + dc
                        if not (0 <= nr < 5 and 0 <= nc < 5):
                            continue
                        token = features["cells"][nr][nc]
                        if token.get("kind") != "token":
                            continue
                        affected.append(
                            {
                                "reel": nr,
                                "row": nc,
                                "faceValueX": float(token["faceValueX"]),
                                "effectiveValueX": float(token["effectiveValueX"]),
                                "appliedThermals": list(token.get("appliedThermals") or []),
                            }
                        )
                events.append(
                    {
                        "type": "skyjumpThermalLift",
                        "schemaVersion": 2,
                        "position": {"reel": reel, "row": row_index},
                        "thermalMult": int(cell["thermalMult"]),
                        "affectedTokens": affected,
                    }
                )
    for collection in features.get("collections") or []:
        ctype = collection["type"]
        events.append(
            {
                "type": "skyjumpJudgeCollect" if ctype == "JUDGE" else "skyjumpHeadJudgeCollect",
                "schemaVersion": 2,
                "position": collection["position"],
                "passIndex": int(collection.get("pass", 1)),
                "collectedX": float(collection["collectedX"]),
                "effectiveTokenSumX": float(collection.get("effectiveTokenSumX") or 0),
                "tokenContributions": list(collection.get("tokenContributions") or []),
                "batchIndex": int(collection.get("batchIndex") or 0),
                "rawTokenCollectionX": float(
                    collection.get("rawTokenCollectionX")
                    if collection.get("rawTokenCollectionX") is not None
                    else collection.get("effectiveTokenSumX") or 0
                ),
                "flightMultiplierX": float(collection.get("flightMultiplierX") or 1),
                "paidCollectionX": float(
                    collection.get("paidCollectionX")
                    if collection.get("paidCollectionX") is not None
                    else collection["collectedX"]
                ),
                "payoutSpentAfter": bool(collection.get("payoutSpentAfter", True)),
            }
        )
    for event in features.get("phase6Events") or []:
        events.append(dict(event))
    return events


def _snapshot(state: FreeSpinState, *, trigger_win_x: float, round_capped: float, initial_spins: int) -> dict:
    return {
        "type": "skyjumpFreeSpinState",
        "schemaVersion": 2,
        "bonusActive": True,
        "bonusTier": state.bonusTier,
        "freeSpinsInitial": initial_spins,
        "freeSpinsRemaining": state.freeSpinsRemaining,
        "freeSpinsPlayed": state.freeSpinsPlayed,
        "totalFreeSpinsAwarded": state.spinsAwardedTotal,
        "upgradeCount": state.upgradeCount,
        "retriggerCount": state.retriggerCount,
        "tokenFloorTier": state.tokenFloorTier,
        "persistentMysteryTargets": list(state.persistentMysteryTargets),
        "guaranteedGateUsed": state.guaranteedGateUsed,
        "coachGuaranteeState": dict(state.coachGuaranteeState),
        "bonusWinXRaw": state.bonusWinXRaw,
        "bonusWinXCapped": state.bonusWinXCapped,
        "triggerSpinWinX": trigger_win_x,
        "roundWinXRaw": trigger_win_x + state.bonusWinXRaw,
        "roundWinXCapped": round_capped,
        "maxWinReached": state.maxWinReached,
        "pendingTierUpgrade": state.pendingTier,
        "flightMultiplierRunUp": state.flightMultiplierRunUp,
        "flightMultiplierTakeoff": state.flightMultiplierTakeoff,
        "flightMultiplierFlight": state.flightMultiplierFlight,
        "flightMultiplier": dict(state.flightMultiplier)
        if getattr(state, "flightMultiplier", None)
        else {
            "runUp": {"value": int(state.flightMultiplierRunUp), "charge": int(getattr(state, "runUpCharge", 0))},
            "takeoff": {"value": int(state.flightMultiplierTakeoff), "charge": int(getattr(state, "takeoffCharge", 0))},
            "flight": {"value": int(state.flightMultiplierFlight), "charge": int(getattr(state, "flightCharge", 0))},
        },
        "windKeysCollected": int(getattr(state, "windKeysCollected", 0)),
        "rejumpsThisBonus": int(getattr(state, "rejumpsThisBonus", 0)),
        "featureBatchIndex": int(getattr(state, "featureBatchIndex", 0)),
        "rejumpState": state.rejumpState,
        "globalFlightMultiplier": int(state.flightMultiplierRunUp)
        * int(state.flightMultiplierTakeoff)
        * int(state.flightMultiplierFlight),
    }


def _index(events: list[dict]) -> list[dict]:
    for index, event in enumerate(events):
        event["index"] = index
    return events


def resolve_v2_buy_round(
    rng,
    *,
    config: dict,
    start_tier: str,
    wager_cost_multiplier: float = 0.0,
    next_fs_stops=None,
) -> dict:
    """Direct-start Free Spin buy: one book, one settlement. No BASE spin."""
    if start_tier not in TIER_ORDER:
        raise ValueError(f"invalid buy tier {start_tier}")
    candidate = bonus_candidate_from_config(config)
    paying = live_candidate_from_config(config)
    state = new_bonus_state(start_tier, initial_spins=candidate.initialSpins)
    state.guaranteedGateUsed = False
    trigger_win = 0.0
    trigger_raw = 0.0
    events = [
        {
            "type": "skyjumpSpinStart",
            "schemaVersion": 2,
            "mode": start_tier,
            "isFreeSpin": True,
            "source": "math",
            "buyMode": True,
        },
        {
            "type": "skyjumpFreeSpinsStart",
            "schemaVersion": 2,
            "initialTier": start_tier,
            "spinsAwarded": candidate.initialSpins,
            "directTriggerType": "BUY",
            "triggeringScatterPositions": [],
            "triggerSpinWinX": 0.0,
            "wagerCostMultiplier": float(wager_cost_multiplier),
        },
    ]
    spins = []
    while state.freeSpinsRemaining > 0 and not state.maxWinReached:
        targets_before = list(state.persistentMysteryTargets)
        tier_before = state.bonusTier
        played_before = state.freeSpinsPlayed
        planned_stops = next_fs_stops(state) if next_fs_stops is not None else None
        result = resolve_fs_spin(
            rng,
            state,
            candidate,
            config=config,
            paying_candidate=paying,
            round_prior_win_x=trigger_win,
            stops=planned_stops,
        )
        features = result["features"]
        wr_hit = result.get("worldRecord")
        spins_remaining_before = (
            int(result["spinsRemainingBefore"])
            if wr_hit is not None and "spinsRemainingBefore" in result
            else state.freeSpinsRemaining + 1 - int(result["spinsAdded"])
        )
        events.append(
            {
                "type": "skyjumpFreeSpinStart",
                "schemaVersion": 2,
                "spinIndex": played_before + 1,
                "currentTier": tier_before,
                "spinsRemainingBefore": spins_remaining_before,
            }
        )
        events.append(
            {
                "type": "skyjumpBoardReveal",
                "schemaVersion": 2,
                "board": result["board"],
                "isFreeSpin": True,
            }
        )
        scatter_spin = result["scatter"]
        events.append(
            {
                "type": "skyjumpScatterResult",
                "schemaVersion": 2,
                "positions": scatter_spin["positions"],
                "count": scatter_spin["count"],
                "perfectV": scatter_spin["perfectV"],
                "trigger": None,
                "fromBoard": "initialReveal",
            }
        )
        if wr_hit is not None:
            events.append(
                {
                    "type": "skyjumpWorldRecord",
                    "schemaVersion": 2,
                    "position": wr_hit["position"],
                    "bonusTier": wr_hit["bonusTier"],
                    "freeSpinIndex": wr_hit["freeSpinIndex"],
                    "accruedRoundWinXBefore": wr_hit["accruedRoundWinXBefore"],
                    "worldRecordIncrementX": wr_hit["worldRecordIncrementX"],
                    "maxWinX": wr_hit["maxWinX"],
                    "finalRoundWinX": wr_hit["finalRoundWinX"],
                    "terminated": True,
                    "remainingFreeSpinsCancelled": wr_hit["remainingFreeSpinsCancelled"],
                    "pendingRejumpsCancelled": True,
                    "tierIntensity": wr_hit.get("tierIntensity"),
                    "symbolId": wr_hit.get("symbolId", "SPECIAL_WORLD_RECORD"),
                    "candidateOrigin": wr_hit.get("candidateOrigin"),
                }
            )
        else:
            events.append(
                {
                    "type": "skyjumpLineWins",
                    "schemaVersion": 2,
                    "wins": result["wins"],
                    "lineWinX": result["lineWinX"],
                }
            )
            persist_board = result.get("boardPreOverlay") or result["board"]
            persist_hits = _persist_positions(persist_board, targets_before)
            if persist_hits:
                events.append(
                    {
                        "type": "skyjumpPersistentTargetsApply",
                        "schemaVersion": 2,
                        "targets": list(targets_before),
                        "positions": persist_hits,
                    }
                )
            events.extend(_feature_events(features))
            added_targets = [
                symbol for symbol in state.persistentMysteryTargets if symbol not in targets_before
            ]
            if added_targets:
                events.append(
                    {
                        "type": "skyjumpPersistentTargetsUpdate",
                        "schemaVersion": 2,
                        "added": added_targets,
                        "persistentMysteryTargets": list(state.persistentMysteryTargets),
                    }
                )
            upgrade = result["upgrade"]
            if upgrade["retriggered"] or upgrade["upgraded"]:
                events.append(
                    {
                        "type": "skyjumpBonusUpgrade",
                        "schemaVersion": 2,
                        "fromTier": tier_before,
                        "toTier": upgrade["newTier"],
                        "triggeringScatterCount": int(scatter_spin["count"]),
                        "perfectV": bool(scatter_spin["perfectV"]),
                        "spinsRequested": int(upgrade["addSpins"]),
                        "spinsAdded": int(result["spinsAdded"]),
                        "spinsRemainingAfter": state.freeSpinsRemaining,
                        "totalFreeSpinsAwarded": state.spinsAwardedTotal,
                        "activatesFromSpinIndex": (
                            state.freeSpinsPlayed + 1 if state.freeSpinsRemaining > 0 else None
                        ),
                        "tierChanged": bool(upgrade["upgraded"]),
                    }
                )
        round_raw = trigger_raw + state.bonusWinXRaw
        round_capped = min(50_000.0, trigger_win + state.bonusWinXCapped)
        if result["capHit"] or state.maxWinReached:
            events.append(
                {
                    "type": "skyjumpCapReached",
                    "schemaVersion": 2,
                    "rawTotalWinX": round_raw,
                    "cappedTotalWinX": round_capped,
                    "capDragX": max(0.0, round_raw - round_capped),
                    "maxWinX": 50_000,
                    "terminated": True,
                    "reason": "WORLD_RECORD" if wr_hit is not None else "ROUND_CAP",
                }
            )
        events.append(
            {
                "type": "skyjumpFreeSpinEnd",
                "schemaVersion": 2,
                "spinIndex": state.freeSpinsPlayed,
                "spinWinX": result["spinWinXCapped"],
                "spinWinXRaw": result["spinWinXRaw"],
                "bonusWinRunningX": state.bonusWinXCapped,
                "spinsRemainingAfter": state.freeSpinsRemaining,
                "currentTier": tier_before,
            }
        )
        events.append(
            _snapshot(state, trigger_win_x=trigger_win, round_capped=round_capped, initial_spins=candidate.initialSpins)
        )
        events.append({"type": "setTotalWin", "amount": round_book_amount(round_capped)})
        spins.append(result)
        if state.maxWinReached:
            break

    round_raw = trigger_raw + state.bonusWinXRaw
    round_capped = min(50_000.0, trigger_win + state.bonusWinXCapped)
    events.append(
        {
            "type": "skyjumpFreeSpinsEnd",
            "schemaVersion": 2,
            "totalSpinsPlayed": state.freeSpinsPlayed,
            "finalTier": state.bonusTier,
            "bonusWinX": state.bonusWinXCapped,
            "bonusWinXRaw": state.bonusWinXRaw,
            "triggerSpinWinX": trigger_win,
            "roundWinXRaw": round_raw,
            "roundWinXCapped": round_capped,
            "upgradeCount": state.upgradeCount,
            "retriggerCount": state.retriggerCount,
            "maxWinReached": state.maxWinReached,
            "tokenFloorTier": state.tokenFloorTier,
            "persistentMysteryTargets": list(state.persistentMysteryTargets),
            "guaranteedGateUsed": state.guaranteedGateUsed,
        }
    )
    amount = round_book_amount(round_capped)
    events.append({"type": "setTotalWin", "amount": amount})
    events.append({"type": "finalWin", "amount": amount})
    return {
        "base": None,
        "bonus": {
            "startTier": start_tier,
            "directTriggerType": "BUY",
            "freeSpinsPlayed": state.freeSpinsPlayed,
            "finalTier": state.bonusTier,
            "upgradeCount": state.upgradeCount,
            "retriggerCount": state.retriggerCount,
            "bonusWinXRaw": state.bonusWinXRaw,
            "bonusWinXCapped": state.bonusWinXCapped,
            "maxWinReached": state.maxWinReached,
            "tokenFloorTier": state.tokenFloorTier,
            "persistentMysteryTargets": list(state.persistentMysteryTargets),
            "guaranteedGateUsed": state.guaranteedGateUsed,
        },
        "events": _index(events),
        "triggerSpinWinX": 0.0,
        "bonusWinXRaw": state.bonusWinXRaw,
        "bonusWinXCapped": state.bonusWinXCapped,
        "roundWinXRaw": round_raw,
        "roundWinXCapped": round_capped,
        "isBonus": True,
        "spins": spins,
        "mode": start_tier,
        "wagerCostMultiplier": float(wager_cost_multiplier),
    }


# Keep resolve_v2_round below — buy helper inserted above.


def resolve_v2_round(
    rng,
    *,
    config: dict,
    base_stops: list[int] | None = None,
    next_fs_stops=None,
    round_prior_win_x: float | None = None,
) -> dict:
    """One paid BASE spin plus the full Free Spin sequence when triggered.

    Optional stop hooks and a cap prior are for deterministic DEV samples.
    Omitted, they leave the live draw and the trigger-win cap prior unchanged.
    """
    base = resolve_v2_base(rng, stops=base_stops, config=config)
    scatter = base["scatter"]
    tier, trigger_type = classify_base_trigger(scatter)
    trigger_win = float(base["totalWinX"])
    trigger_raw = float(base["totalWinXRaw"])
    if round_prior_win_x is not None:
        trigger_win = float(round_prior_win_x)
        trigger_raw = max(trigger_raw, trigger_win)
    if tier is None:
        events = round_to_v2_events(base)
        return {
            "base": base,
            "bonus": None,
            "events": events,
            "triggerSpinWinX": trigger_win,
            "bonusWinXRaw": 0.0,
            "bonusWinXCapped": 0.0,
            "roundWinXRaw": trigger_raw,
            "roundWinXCapped": min(trigger_raw, 50_000.0),
            "isBonus": False,
        }

    scatter = dict(scatter)
    scatter["trigger"] = {"tier": tier, "directTriggerType": trigger_type}
    base = dict(base)
    base["scatter"] = scatter
    base_events = round_to_v2_events(base)
    # Settlement is once, after the bonus. Drop the trigger spin's terminal pair.
    while base_events and base_events[-1]["type"] in {"finalWin", "setTotalWin"}:
        base_events.pop()
    if round_prior_win_x is not None:
        for event in base_events:
            if event["type"] == "skyjumpResult":
                event["totalWinX"] = trigger_win
                event["totalWinXRaw"] = trigger_raw
                event["amount"] = round_book_amount(trigger_win)
                event["devSyntheticCapPrior"] = True

    candidate = bonus_candidate_from_config(config)
    paying = live_candidate_from_config(config)
    state = new_bonus_state(tier, initial_spins=candidate.initialSpins)
    state.guaranteedGateUsed = False
    events = list(base_events)
    events.append(
        {
            "type": "skyjumpFreeSpinsStart",
            "schemaVersion": 2,
            "initialTier": tier,
            "spinsAwarded": candidate.initialSpins,
            "directTriggerType": trigger_type,
            "triggeringScatterPositions": scatter["positions"],
            "triggerSpinWinX": trigger_win,
            "wagerCostMultiplier": 0,
        }
    )
    spins = []
    while state.freeSpinsRemaining > 0 and not state.maxWinReached:
        targets_before = list(state.persistentMysteryTargets)
        tier_before = state.bonusTier
        played_before = state.freeSpinsPlayed
        planned_stops = next_fs_stops(state) if next_fs_stops is not None else None
        result = resolve_fs_spin(
            rng,
            state,
            candidate,
            config=config,
            paying_candidate=paying,
            round_prior_win_x=trigger_win,
            stops=planned_stops,
        )
        features = result["features"]
        wr_hit = result.get("worldRecord")
        spins_remaining_before = (
            int(result["spinsRemainingBefore"])
            if wr_hit is not None and "spinsRemainingBefore" in result
            else state.freeSpinsRemaining + 1 - int(result["spinsAdded"])
        )
        events.append(
            {
                "type": "skyjumpFreeSpinStart",
                "schemaVersion": 2,
                "spinIndex": played_before + 1,
                "currentTier": tier_before,
                "spinsRemainingBefore": spins_remaining_before,
            }
        )
        # Board reveal uses display board (WR overlay when triggered).
        events.append(
            {
                "type": "skyjumpBoardReveal",
                "schemaVersion": 2,
                "board": result["board"],
                "isFreeSpin": True,
            }
        )
        scatter_spin = result["scatter"]
        # Scatter count/state always from the pre-overlay Math board.
        events.append(
            {
                "type": "skyjumpScatterResult",
                "schemaVersion": 2,
                "positions": scatter_spin["positions"],
                "count": scatter_spin["count"],
                "perfectV": scatter_spin["perfectV"],
                "trigger": None,
                "fromBoard": "initialReveal",
            }
        )
        if wr_hit is not None:
            # WR terminates: no line evaluation, features, upgrades, or pending Rejumps.
            events.append(
                {
                    "type": "skyjumpWorldRecord",
                    "schemaVersion": 2,
                    "position": wr_hit["position"],
                    "bonusTier": wr_hit["bonusTier"],
                    "freeSpinIndex": wr_hit["freeSpinIndex"],
                    "accruedRoundWinXBefore": wr_hit["accruedRoundWinXBefore"],
                    "worldRecordIncrementX": wr_hit["worldRecordIncrementX"],
                    "maxWinX": wr_hit["maxWinX"],
                    "finalRoundWinX": wr_hit["finalRoundWinX"],
                    "terminated": True,
                    "remainingFreeSpinsCancelled": wr_hit["remainingFreeSpinsCancelled"],
                    "pendingRejumpsCancelled": True,
                    "tierIntensity": wr_hit.get("tierIntensity"),
                    "symbolId": wr_hit.get("symbolId", "SPECIAL_WORLD_RECORD"),
                    "candidateOrigin": wr_hit.get("candidateOrigin"),
                }
            )
        else:
            events.append(
                {
                    "type": "skyjumpLineWins",
                    "schemaVersion": 2,
                    "wins": result["wins"],
                    "lineWinX": result["lineWinX"],
                }
            )
            persist_board = result.get("boardPreOverlay") or result["board"]
            persist_hits = _persist_positions(persist_board, targets_before)
            if persist_hits:
                events.append(
                    {
                        "type": "skyjumpPersistentTargetsApply",
                        "schemaVersion": 2,
                        "targets": list(targets_before),
                        "positions": persist_hits,
                    }
                )
            events.extend(_feature_events(features))
            added_targets = [
                symbol for symbol in state.persistentMysteryTargets if symbol not in targets_before
            ]
            if added_targets:
                events.append(
                    {
                        "type": "skyjumpPersistentTargetsUpdate",
                        "schemaVersion": 2,
                        "added": added_targets,
                        "persistentMysteryTargets": list(state.persistentMysteryTargets),
                    }
                )
            upgrade = result["upgrade"]
            if upgrade["retriggered"] or upgrade["upgraded"]:
                events.append(
                    {
                        "type": "skyjumpBonusUpgrade",
                        "schemaVersion": 2,
                        "fromTier": tier_before,
                        "toTier": upgrade["newTier"],
                        "triggeringScatterCount": int(scatter_spin["count"]),
                        "perfectV": bool(scatter_spin["perfectV"]),
                        "spinsRequested": int(upgrade["addSpins"]),
                        "spinsAdded": int(result["spinsAdded"]),
                        "spinsRemainingAfter": state.freeSpinsRemaining,
                        "totalFreeSpinsAwarded": state.spinsAwardedTotal,
                        "activatesFromSpinIndex": (
                            state.freeSpinsPlayed + 1 if state.freeSpinsRemaining > 0 else None
                        ),
                        "tierChanged": bool(upgrade["upgraded"]),
                    }
                )
        round_raw = trigger_raw + state.bonusWinXRaw
        round_capped = min(50_000.0, trigger_win + state.bonusWinXCapped)
        if result["capHit"] or state.maxWinReached:
            events.append(
                {
                    "type": "skyjumpCapReached",
                    "schemaVersion": 2,
                    "rawTotalWinX": round_raw,
                    "cappedTotalWinX": round_capped,
                    "capDragX": max(0.0, round_raw - round_capped),
                    "maxWinX": 50_000,
                    "terminated": True,
                    "reason": "WORLD_RECORD" if wr_hit is not None else "ROUND_CAP",
                }
            )
        events.append(
            {
                "type": "skyjumpFreeSpinEnd",
                "schemaVersion": 2,
                "spinIndex": state.freeSpinsPlayed,
                "spinWinX": result["spinWinXCapped"],
                "spinWinXRaw": result["spinWinXRaw"],
                "bonusWinRunningX": state.bonusWinXCapped,
                "spinsRemainingAfter": state.freeSpinsRemaining,
                "currentTier": tier_before,
            }
        )
        events.append(_snapshot(state, trigger_win_x=trigger_win, round_capped=round_capped, initial_spins=candidate.initialSpins))
        events.append(
            {
                "type": "setTotalWin",
                "amount": round_book_amount(round_capped),
            }
        )
        spins.append(result)
        if state.maxWinReached:
            break

    round_raw = trigger_raw + state.bonusWinXRaw
    round_capped = min(50_000.0, trigger_win + state.bonusWinXCapped)
    events.append(
        {
            "type": "skyjumpFreeSpinsEnd",
            "schemaVersion": 2,
            "totalSpinsPlayed": state.freeSpinsPlayed,
            "finalTier": state.bonusTier,
            "bonusWinX": state.bonusWinXCapped,
            "bonusWinXRaw": state.bonusWinXRaw,
            "triggerSpinWinX": trigger_win,
            "roundWinXRaw": round_raw,
            "roundWinXCapped": round_capped,
            "upgradeCount": state.upgradeCount,
            "retriggerCount": state.retriggerCount,
            "maxWinReached": state.maxWinReached,
            "tokenFloorTier": state.tokenFloorTier,
            "persistentMysteryTargets": list(state.persistentMysteryTargets),
            "guaranteedGateUsed": state.guaranteedGateUsed,
        }
    )
    amount = round_book_amount(round_capped)
    events.append({"type": "setTotalWin", "amount": amount})
    events.append({"type": "finalWin", "amount": amount})
    return {
        "base": base,
        "bonus": {
            "startTier": tier,
            "directTriggerType": trigger_type,
            "freeSpinsPlayed": state.freeSpinsPlayed,
            "finalTier": state.bonusTier,
            "upgradeCount": state.upgradeCount,
            "retriggerCount": state.retriggerCount,
            "bonusWinXRaw": state.bonusWinXRaw,
            "bonusWinXCapped": state.bonusWinXCapped,
            "maxWinReached": state.maxWinReached,
            "tokenFloorTier": state.tokenFloorTier,
            "persistentMysteryTargets": list(state.persistentMysteryTargets),
            "guaranteedGateUsed": state.guaranteedGateUsed,
        },
        "events": _index(events),
        "triggerSpinWinX": trigger_win,
        "bonusWinXRaw": state.bonusWinXRaw,
        "bonusWinXCapped": state.bonusWinXCapped,
        "roundWinXRaw": round_raw,
        "roundWinXCapped": round_capped,
        "isBonus": True,
        "spins": spins,
    }
