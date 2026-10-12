"""Phase 5A Free Spin research engine (math-only, no frontend).

Serialisable bonus state + spin / bonus simulation with persistence, upgrades,
and guaranteed Gate. Does NOT mutate live BASE F01 config.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable

from skyjump_v2_exact import scatter_on_board
from skyjump_v2_lines import evaluate_paylines, load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase4a_economy import resolve_paying_features
from skyjump_v2_reels import board_from_stops

TIERS = ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
TIER_INDEX = {name: index for index, name in enumerate(TIERS)}


@dataclass
class FreeSpinState:
    bonusTier: str = "LARGE_HILL"
    freeSpinsRemaining: int = 10
    freeSpinsPlayed: int = 0
    bonusWinXRaw: float = 0.0
    bonusWinXCapped: float = 0.0
    tokenFloorTier: int = 1
    persistentMysteryTargets: list[str] = field(default_factory=list)
    coachGuaranteeState: dict = field(default_factory=dict)
    guaranteedGateUsed: bool = False
    upgradeCount: int = 0
    retriggerCount: int = 0
    maxWinReached: bool = False
    # Phase 6B flight multiplier (K1 values + W-CHARGE charges)
    flightMultiplierRunUp: float = 1.0
    flightMultiplierTakeoff: float = 1.0
    flightMultiplierFlight: float = 1.0
    flightMultiplier: dict | None = None
    runUpCharge: int = 0
    takeoffCharge: int = 0
    flightCharge: int = 0
    windKeysCollected: int = 0
    rejumpsThisBonus: int = 0
    featureBatchIndex: int = 0
    rejumpState: dict | None = None
    # Pending next-spin activation
    pendingTier: str | None = None
    spinsAwardedTotal: int = 10


def new_bonus_state(tier: str, *, initial_spins: int = 10) -> FreeSpinState:
    return FreeSpinState(
        bonusTier=tier,
        freeSpinsRemaining=initial_spins,
        spinsAwardedTotal=initial_spins,
    )


def apply_persistent_targets(board: list[list[str]], targets: list[str], mystery_id: str) -> list[list[str]]:
    """Transform visible regular symbols matching persistent targets → Mystery.

    Applied AFTER line + scatter evaluation on the initial board.
    """
    if not targets:
        return [col[:] for col in board]
    target_set = set(targets)
    working = [col[:] for col in board]
    for reel, col in enumerate(working):
        for row, symbol in enumerate(col):
            if symbol in target_set:
                working[reel][row] = mystery_id
    return working


def upgrade_tier(current: str, steps: int = 1) -> str:
    index = min(len(TIERS) - 1, TIER_INDEX[current] + steps)
    return TIERS[index]


def apply_upgrade_rule(rule: str, scatter_count: int, perfect_v: bool, current_tier: str) -> dict:
    """Return {addSpins, newTier, upgraded, retriggered} for a Free Spin scatter event."""
    if perfect_v:
        # Pattern always jumps to Perfect V + spins (treat as strongest U2/U3 path)
        add = 5
        return {
            "addSpins": add,
            "newTier": "PERFECT_V",
            "upgraded": current_tier != "PERFECT_V",
            "retriggered": True,
        }
    if scatter_count < 3:
        return {"addSpins": 0, "newTier": current_tier, "upgraded": False, "retriggered": False}

    if rule == "U1":
        add = 5
        new_tier = upgrade_tier(current_tier, 1) if current_tier != "PERFECT_V" else current_tier
        return {
            "addSpins": add,
            "newTier": new_tier,
            "upgraded": new_tier != current_tier,
            "retriggered": True,
        }
    if rule == "U2":
        if scatter_count == 3:
            add, steps, jump_pv = 3, 1, False
        elif scatter_count == 4:
            add, steps, jump_pv = 5, 1, False
        else:
            add, steps, jump_pv = 5, 0, True
        if jump_pv:
            new_tier = "PERFECT_V"
        else:
            new_tier = upgrade_tier(current_tier, steps) if current_tier != "PERFECT_V" else current_tier
        return {
            "addSpins": add,
            "newTier": new_tier,
            "upgraded": new_tier != current_tier,
            "retriggered": True,
        }
    if rule == "U3":
        if scatter_count == 3:
            return {
                "addSpins": 5,
                "newTier": current_tier,
                "upgraded": False,
                "retriggered": True,
            }
        if scatter_count == 4:
            new_tier = upgrade_tier(current_tier, 1) if current_tier != "PERFECT_V" else current_tier
            return {
                "addSpins": 5,
                "newTier": new_tier,
                "upgraded": new_tier != current_tier,
                "retriggered": True,
            }
        new_tier = "PERFECT_V"
        return {
            "addSpins": 5,
            "newTier": new_tier,
            "upgraded": new_tier != current_tier,
            "retriggered": True,
        }
    raise ValueError(f"unknown upgrade rule {rule}")


@dataclass
class BonusCandidate:
    id: str
    upgradeRule: str = "U3"
    initialSpins: int = 10
    maxFreeSpins: int = 40
    maxPersistentTargets: int = 2
    duplicateTargetBehaviour: str = "B"  # A = waste; B = pick other eligible
    guaranteedGatePolicy: str = "token_or_thermal"
    tierReels: dict[str, list[list[str]]] = field(default_factory=dict)
    maxWinX: float = 50_000.0
    # Research-only Mystery weight overrides (None = live BASE F01 table)
    mysteryResultWeights: dict[str, int] | None = None
    mysteryResultWeightsByTier: dict[str, dict[str, int]] | None = None
    tokenValueScale: float = 1.0
    conditionalCollectors: bool | None = None


def paying_for_candidate(base_paying: dict, candidate: BonusCandidate, tier: str) -> dict:
    paying = dict(base_paying)
    paying["mysteryResultWeights"] = dict(base_paying["mysteryResultWeights"])
    if candidate.mysteryResultWeightsByTier and tier in candidate.mysteryResultWeightsByTier:
        paying["mysteryResultWeights"] = dict(candidate.mysteryResultWeightsByTier[tier])
    elif candidate.mysteryResultWeights:
        paying["mysteryResultWeights"] = dict(candidate.mysteryResultWeights)
    if candidate.conditionalCollectors is not None:
        paying["conditionalCollectors"] = bool(candidate.conditionalCollectors)
    paying["tokenValueScale"] = float(candidate.tokenValueScale)
    return paying


def resolve_fs_spin(
    rng,
    state: FreeSpinState,
    candidate: BonusCandidate,
    *,
    config: dict,
    paying_candidate: dict,
    round_prior_win_x: float = 0.0,
    stops: list[int] | None = None,
) -> dict:
    """Resolve one Free Spin under the tier that started the spin (next-spin upgrades)."""
    tier = state.bonusTier
    strips = candidate.tierReels[tier]
    if stops is None:
        stops = [rng.randrange(len(strip)) for strip in strips]
    board = board_from_stops(strips, stops)

    # Phase 7B WR-C: trial AFTER initial board, BEFORE line evaluation (FS only).
    from skyjump_v2_world_record import try_world_record

    scatter_id = config["symbols"]["scatter"]["id"]
    accrued_before = float(round_prior_win_x) + float(state.bonusWinXCapped)
    wr_hit = try_world_record(
        rng,
        board=board,
        config=config,
        bonus_tier=tier,
        free_spin_index=state.freeSpinsPlayed + 1,
        accrued_round_win_x=accrued_before,
        free_spins_remaining_before_consume=state.freeSpinsRemaining,
    )
    if wr_hit is not None:
        spins_remaining_before = int(state.freeSpinsRemaining)
        increment = float(wr_hit["worldRecordIncrementX"])
        state.bonusWinXRaw += increment
        state.bonusWinXCapped += increment
        state.maxWinReached = True
        state.freeSpinsRemaining = 0
        # Consume this spin index for book coherence; cancel all remaining.
        state.freeSpinsPlayed += 1
        scatter = scatter_on_board(
            board,
            scatter_id,
            tuple(config["scatterModel"]["perfectVRows"]),
        )
        return {
            "stops": stops,
            "board": wr_hit["boardDisplay"],
            "boardPreOverlay": board,
            "wins": [],
            "lineWinX": 0.0,
            "featureWinXRaw": 0.0,
            "spinWinXRaw": increment,
            "spinWinXCapped": increment,
            "scatter": scatter,
            "upgrade": {
                "addSpins": 0,
                "newTier": tier,
                "upgraded": False,
                "retriggered": False,
            },
            "spinsAdded": 0,
            "spinsRemainingBefore": spins_remaining_before,
            "features": {
                "totalFeatureWinXRaw": 0.0,
                "tokenFloorTier": state.tokenFloorTier,
                "selectedSymbolIds": [],
                "resolves": [],
                "coachCount": 0,
                "judgeCount": 0,
                "headJudgeCount": 0,
                "gateCount": 0,
                "thermalCount": 0,
                "worldRecord": wr_hit,
            },
            "tierAtStart": tier,
            "tokenFloorTier": state.tokenFloorTier,
            "persistentMysteryTargets": list(state.persistentMysteryTargets),
            "capHit": True,
            "mysteries": 0,
            "coachCount": 0,
            "judgeCount": 0,
            "headJudgeCount": 0,
            "gateCount": 0,
            "thermalCount": 0,
            "worldRecord": wr_hit,
        }

    paytable = config["paytable"]["awards"]
    evaluated = evaluate_paylines(
        board,
        paylines=config["paylines"],
        paytable=paytable,
        scatter_id=scatter_id,
        regular_ids={row["id"] for row in config["symbols"]["regular"]},
    )
    line_win = float(evaluated["lineWinX"])
    scatter = scatter_on_board(
        board,
        scatter_id,
        tuple(config["scatterModel"]["perfectVRows"]),
    )

    mystery_id = config["mysteryModel"]["id"]
    # Persist targets apply AFTER lines + scatter on initial board
    after_persist = apply_persistent_targets(board, state.persistentMysteryTargets, mystery_id)

    prefer_b = candidate.duplicateTargetBehaviour == "B"
    force_coach = tier == "PERFECT_V"
    want_gate = (tier in ("WORLD_CUP", "PERFECT_V")) and (not state.guaranteedGateUsed)

    # Feature room under shared round cap (trigger BASE already counted in prior)
    # Cap accounting: we pass line_win only into feature resolver; round cap applied after.
    spin_paying = paying_for_candidate(paying_candidate, candidate, tier)
    scatter_cells = {
        (reel, row)
        for reel in range(5)
        for row in range(5)
        if board[reel][row] == config["symbols"]["scatter"]["id"]
    }
    from skyjump_v2_phase6a_engine import refill_catalogs
    from skyjump_v2_phase6b import phase6_enabled, resolve_phase6b_features

    if phase6_enabled(config):
        catalogs = refill_catalogs(strips)
        features = resolve_phase6b_features(
            after_persist,
            rng,
            config=config,
            candidate=spin_paying,
            state=state,
            line_win_x=line_win,
            start_floor=state.tokenFloorTier,
            coach_exclude_types=set(state.persistentMysteryTargets),
            coach_prefer_non_excluded=prefer_b,
            force_coach_if_none=force_coach,
            guaranteed_gate=want_gate,
            guaranteed_gate_policy=candidate.guaranteedGatePolicy,
            strips=strips,
            catalogs=catalogs,
            scatter_cells=scatter_cells,
            max_rejumps=int(config["freeSpins"]["phase6"].get("maxRejumpsPerSpin", 2)),
            max_chain=int(config["freeSpins"]["phase6"].get("maxFeatureChainDepth", 8)),
        )
    else:
        features = resolve_paying_features(
            after_persist,
            rng,
            config=config,
            candidate=spin_paying,
            line_win_x=line_win,
            start_floor=state.tokenFloorTier,
            coach_exclude_types=set(state.persistentMysteryTargets),
            coach_prefer_non_excluded=prefer_b,
            force_coach_if_none=force_coach,
            guaranteed_gate=want_gate,
            guaranteed_gate_policy=candidate.guaranteedGatePolicy,
        )

    if features.get("guaranteedGateApplied"):
        state.guaranteedGateUsed = True

    # Persistence: floor carries; Mystery targets grow on Ski Flying+
    state.tokenFloorTier = int(features["tokenFloorTier"])

    if tier in ("SKI_FLYING", "WORLD_CUP", "PERFECT_V"):
        for symbol in features.get("selectedSymbolIds") or []:
            if symbol is None:
                continue
            if symbol in state.persistentMysteryTargets:
                continue
            if len(state.persistentMysteryTargets) >= candidate.maxPersistentTargets:
                break
            state.persistentMysteryTargets.append(symbol)

    feature_raw = float(features["totalFeatureWinXRaw"])
    spin_raw = line_win + feature_raw

    # Shared round cap with BASE trigger win (incremental FS accounting)
    room = max(0.0, candidate.maxWinX - round_prior_win_x - state.bonusWinXCapped)
    spin_capped = min(spin_raw, room)
    cap_hit = spin_raw > room and room < spin_raw

    state.bonusWinXRaw += spin_raw
    state.bonusWinXCapped += spin_capped
    if state.bonusWinXCapped + round_prior_win_x >= candidate.maxWinX - 1e-12:
        state.maxWinReached = True

    # Scatter upgrade / retrigger — NEXT spin activation for tier
    upgrade = apply_upgrade_rule(
        candidate.upgradeRule,
        int(scatter["count"]),
        bool(scatter["perfectV"]),
        state.bonusTier,
    )
    spins_added = 0
    if upgrade["retriggered"]:
        room_spins = max(0, candidate.maxFreeSpins - (state.freeSpinsPlayed + state.freeSpinsRemaining))
        # remaining includes current spin not yet decremented; bound on total played+remaining after add
        # After this spin we decrement 1, then add spins.
        room = max(0, candidate.maxFreeSpins - state.spinsAwardedTotal)
        spins_added = min(int(upgrade["addSpins"]), room)
        if spins_added > 0:
            state.freeSpinsRemaining += spins_added
            state.spinsAwardedTotal += spins_added
            state.retriggerCount += 1
        if upgrade["upgraded"]:
            state.pendingTier = upgrade["newTier"]
            state.upgradeCount += 1

    coaches = features.get("coaches") or []
    synthetic = any(bool(coach.get("synthetic")) for coach in coaches)
    coach_count = int(features.get("coachCount") or 0)
    if tier == "PERFECT_V":
        state.coachGuaranteeState = {
            "required": True,
            "satisfied": coach_count >= 1,
            "synthetic": synthetic,
            "coachCount": coach_count,
        }
    else:
        state.coachGuaranteeState = {
            "required": False,
            "satisfied": True,
            "synthetic": False,
            "coachCount": coach_count,
        }

    # Consume this spin
    state.freeSpinsRemaining -= 1
    state.freeSpinsPlayed += 1

    # Activate pending tier for NEXT spin
    if state.pendingTier is not None and state.freeSpinsRemaining > 0:
        state.bonusTier = state.pendingTier
        state.pendingTier = None

    return {
        "stops": stops,
        "board": board,
        "wins": evaluated["wins"],
        "lineWinX": line_win,
        "featureWinXRaw": feature_raw,
        "spinWinXRaw": spin_raw,
        "spinWinXCapped": spin_capped,
        "scatter": scatter,
        "upgrade": upgrade,
        "spinsAdded": spins_added,
        "features": features,
        "tierAtStart": tier,
        "tokenFloorTier": state.tokenFloorTier,
        "persistentMysteryTargets": list(state.persistentMysteryTargets),
        "capHit": cap_hit,
        "mysteries": len(features.get("resolves") or []),
        "coachCount": int(features.get("coachCount") or 0),
        "judgeCount": int(features.get("judgeCount") or 0),
        "headJudgeCount": int(features.get("headJudgeCount") or 0),
        "gateCount": int(features.get("gateCount") or 0),
        "thermalCount": int(features.get("thermalCount") or 0),
    }


def simulate_bonus(
    rng,
    start_tier: str,
    candidate: BonusCandidate,
    *,
    config: dict,
    paying_candidate: dict,
    round_prior_win_x: float = 0.0,
) -> dict:
    state = new_bonus_state(start_tier, initial_spins=candidate.initialSpins)
    # Guaranteed Gate arms when the live tier is WORLD_CUP / PERFECT_V (including upgrades).
    state.guaranteedGateUsed = False

    spins_detail_light = {
        "floorAt": {},
        "persistAt": {},
        "mysteries": 0,
        "coaches": 0,
        "judges": 0,
        "headJudges": 0,
        "gates": 0,
        "thermals": 0,
        "lineSum": 0.0,
        "featureSum": 0.0,
        "hadCoach": False,
        "hadCollector": False,
        "hadUpgrade": False,
        "tiersVisited": {start_tier},
    }

    while state.freeSpinsRemaining > 0 and not state.maxWinReached:
        spin_index = state.freeSpinsPlayed + 1
        result = resolve_fs_spin(
            rng,
            state,
            candidate,
            config=config,
            paying_candidate=paying_candidate,
            round_prior_win_x=round_prior_win_x,
        )
        spins_detail_light["mysteries"] += result["mysteries"]
        spins_detail_light["coaches"] += result["coachCount"]
        spins_detail_light["judges"] += result["judgeCount"]
        spins_detail_light["headJudges"] += result["headJudgeCount"]
        spins_detail_light["gates"] += result["gateCount"]
        spins_detail_light["thermals"] += result["thermalCount"]
        spins_detail_light["lineSum"] += result["lineWinX"]
        spins_detail_light["featureSum"] += result["featureWinXRaw"]
        if result["coachCount"] > 0:
            spins_detail_light["hadCoach"] = True
        if result["judgeCount"] or result["headJudgeCount"]:
            spins_detail_light["hadCollector"] = True
        if result["upgrade"]["upgraded"] or result["upgrade"]["retriggered"]:
            if result["upgrade"]["upgraded"]:
                spins_detail_light["hadUpgrade"] = True
        spins_detail_light["tiersVisited"].add(result["tierAtStart"])
        spins_detail_light["tiersVisited"].add(state.bonusTier)
        if spin_index in (1, 5, 10) or state.freeSpinsRemaining == 0:
            key = str(spin_index if state.freeSpinsRemaining > 0 else "end")
            if spin_index in (1, 5, 10):
                spins_detail_light["floorAt"][str(spin_index)] = state.tokenFloorTier
                spins_detail_light["persistAt"][str(spin_index)] = len(state.persistentMysteryTargets)
        if state.freeSpinsPlayed > candidate.maxFreeSpins + 5:
            break  # hard safety

    spins_detail_light["floorAt"]["end"] = state.tokenFloorTier
    spins_detail_light["persistAt"]["end"] = len(state.persistentMysteryTargets)
    spins_detail_light["tiersVisited"] = sorted(spins_detail_light["tiersVisited"])

    return {
        "startTier": start_tier,
        "bonusWinXRaw": state.bonusWinXRaw,
        "bonusWinXCapped": state.bonusWinXCapped,
        "freeSpinsPlayed": state.freeSpinsPlayed,
        "upgradeCount": state.upgradeCount,
        "retriggerCount": state.retriggerCount,
        "finalTier": state.bonusTier,
        "maxWinReached": state.maxWinReached,
        "tokenFloorTierEnd": state.tokenFloorTier,
        "persistentCountEnd": len(state.persistentMysteryTargets),
        "stats": spins_detail_light,
    }


def base_trigger_mix(config: dict | None = None) -> dict:
    from skyjump_v2_exact import exact_perfect_v_prob, exact_scatter_distribution

    config = config or load_v2_config()
    strips = config["reelModel"]["strips"]
    scatter = exact_scatter_distribution(strips)
    pv = exact_perfect_v_prob(strips)
    p3 = scatter.get(3, 0.0)
    p4 = scatter.get(4, 0.0)
    p5 = sum(prob for n, prob in scatter.items() if n >= 5)
    p_wc = p5 - pv
    p_ge3 = p3 + p4 + p5
    return {
        "P_exact3": p3,
        "P_exact4": p4,
        "P_5plus": p5,
        "P_5plus_not_PV": p_wc,
        "P_directPerfectV": pv,
        "P_scatterGe3": p_ge3,
        "conditional": {
            "LARGE_HILL": p3 / p_ge3,
            "SKI_FLYING": p4 / p_ge3,
            "WORLD_CUP": p_wc / p_ge3,
            "PERFECT_V": pv / p_ge3,
        },
        "absolute": {
            "LARGE_HILL": p3,
            "SKI_FLYING": p4,
            "WORLD_CUP": p_wc,
            "PERFECT_V": pv,
        },
    }
