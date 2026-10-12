"""Phase 6A.1 research engine — visibility / EV decoupling.

Research only. Does not modify live BASE, live Free Spins, or Phase 6A
artifacts. Architectures:

  R-DELAYED  collectors wait until the full Rejump chain ends (F1)
  R-BATCH    collectors from each Mystery batch settle once before redrop

  W-IMMEDIATE  Wind Key upgrades affect collectors on the same Free Spin
  W-NEXT-SPIN  Wind Key upgrades pending stages; active from next Free Spin
  W-CHARGE     two Keys required per K1 stage step (immediate, integer)

Reuse Phase 6A helpers for refill, coach, mystery materialisation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from skyjump_v2_lines import evaluate_paylines
from skyjump_v2_phase4a_economy import empty_cell, neighbours
from skyjump_v2_phase5a_engine import apply_upgrade_rule
from skyjump_v2_phase6a_engine import (
    KIND_GATE,
    KIND_HEAD,
    KIND_JUDGE,
    KIND_THERMAL,
    KIND_TOKEN,
    KIND_WIND,
    Phase6Spec,
    Phase6State,
    SpinTally,
    _apply_persist,
    _locked_fraction,
    _locked_positions,
    _maybe_force_wind,
    _materialise,
    _mystery_positions,
    _next_stage_value,
    _paint_specials,
    _redrop,
    _resolve_mysteries,
    _run_coaches,
    _set_stage,
    _stage_values,
    _take_rejumps,
    apply_new_gates,
)
from skyjump_v2_reels import board_from_stops


@dataclass
class Phase6A1Spec(Phase6Spec):
    rejump_arch: str = "R-DELAYED"  # R-DELAYED | R-BATCH
    wind_arch: str = "W-IMMEDIATE"  # W-IMMEDIATE | W-NEXT-SPIN | W-CHARGE


@dataclass
class Phase6A1State(Phase6State):
    # Active stages used by collectors this Free Spin.
    # Pending stages absorb W-NEXT-SPIN upgrades until the next spin start.
    pending_run_up: int = 1
    pending_takeoff: int = 1
    pending_flight: int = 1
    charge_run_up: int = 0
    charge_takeoff: int = 0
    charge_flight: int = 0
    pending_unused_keys: int = 0
    keys_with_future_spin: int = 0
    keys_on_final_spin: int = 0
    spins_after_first_key: int = 0
    first_key_spin: int | None = None
    active_mult_history: list[int] = field(default_factory=list)
    collector_paid_by_active_mult: dict[int, float] = field(default_factory=dict)


@dataclass
class SpinTallyA1(SpinTally):
    collector_initial_batch: float = 0.0
    collector_after_rejump: float = 0.0
    collector_recollection: float = 0.0  # paid by post-rejump collectors on pre-existing tokens
    post_rejump_tokens: int = 0
    post_rejump_judges: int = 0
    post_rejump_heads: int = 0
    pending_keys_this_spin: int = 0
    active_mult_at_settle: int = 1


def new_phase6a1_state(tier: str, *, initial_spins: int = 10) -> Phase6A1State:
    return Phase6A1State(
        bonusTier=tier,
        freeSpinsRemaining=initial_spins,
        spinsAwardedTotal=initial_spins,
    )


def _pending_values(state: Phase6A1State) -> dict[str, int]:
    return {
        "RUN_UP": state.pending_run_up,
        "TAKEOFF": state.pending_takeoff,
        "FLIGHT": state.pending_flight,
    }


def _set_pending(state: Phase6A1State, stage: str, value: int) -> None:
    if stage == "RUN_UP":
        state.pending_run_up = value
    elif stage == "TAKEOFF":
        state.pending_takeoff = value
    else:
        state.pending_flight = value


def _charge_of(state: Phase6A1State, stage: str) -> int:
    if stage == "RUN_UP":
        return state.charge_run_up
    if stage == "TAKEOFF":
        return state.charge_takeoff
    return state.charge_flight


def _set_charge(state: Phase6A1State, stage: str, value: int) -> None:
    if stage == "RUN_UP":
        state.charge_run_up = value
    elif stage == "TAKEOFF":
        state.charge_takeoff = value
    else:
        state.charge_flight = value


def active_multiplier(state: Phase6A1State) -> int:
    return int(state.run_up) * int(state.takeoff) * int(state.flight)


def pending_multiplier(state: Phase6A1State) -> int:
    return int(state.pending_run_up) * int(state.pending_takeoff) * int(state.pending_flight)


def activate_pending(state: Phase6A1State) -> None:
    """Copy pending stages into active at Free Spin start (W-NEXT-SPIN)."""
    state.run_up = state.pending_run_up
    state.takeoff = state.pending_takeoff
    state.flight = state.pending_flight


def stages_maxed_a1(state: Phase6A1State, spec: Phase6A1Spec) -> bool:
    if spec.wind_arch == "W-NEXT-SPIN":
        values = _pending_values(state)
    else:
        values = _stage_values(state)
    return all(_next_stage_value(value, spec.ladder) is None for value in values.values())


def choose_stage_a1(rng, state: Phase6A1State, spec: Phase6A1Spec) -> str | None:
    if spec.wind_arch == "W-NEXT-SPIN":
        values = _pending_values(state)
    else:
        values = _stage_values(state)
    eligible = [name for name, value in values.items() if _next_stage_value(value, spec.ladder) is not None]
    if not eligible:
        return None
    if spec.stage_rule == "W1":
        return rng.choice(eligible)
    lowest = min(values[name] for name in eligible)
    pool = [name for name in eligible if values[name] == lowest]
    return rng.choice(pool)


def apply_wind_key(state: Phase6A1State, spec: Phase6A1Spec, rng, cell: dict, tally: SpinTallyA1) -> None:
    stage = choose_stage_a1(rng, state, spec)
    if stage is None:
        cell["processed"] = True
        cell["noOp"] = True
        return
    old_active = active_multiplier(state)
    old_pending = pending_multiplier(state)
    cell["stage"] = stage
    cell["processed"] = True

    if spec.wind_arch == "W-CHARGE":
        charge = _charge_of(state, stage)
        old_value = _stage_values(state)[stage]
        if charge == 0:
            _set_charge(state, stage, 1)
            cell["chargeAfter"] = 1
            cell["newValue"] = old_value
            cell["oldValue"] = old_value
        else:
            new_value = _next_stage_value(old_value, spec.ladder)
            _set_stage(state, stage, int(new_value))
            _set_charge(state, stage, 0)
            cell["chargeAfter"] = 0
            cell["oldValue"] = old_value
            cell["newValue"] = new_value
            # Keep pending in sync for reporting when charge upgrades active.
            _set_pending(state, stage, int(new_value))
        cell["oldGlobal"] = old_active
        cell["newGlobal"] = active_multiplier(state)
    elif spec.wind_arch == "W-NEXT-SPIN":
        old_value = _pending_values(state)[stage]
        new_value = _next_stage_value(old_value, spec.ladder)
        _set_pending(state, stage, int(new_value))
        cell["oldValue"] = old_value
        cell["newValue"] = new_value
        cell["oldGlobal"] = old_pending
        cell["newGlobal"] = pending_multiplier(state)
        cell["activatesNextSpin"] = True
        tally.pending_keys_this_spin += 1
    else:
        # W-IMMEDIATE
        old_value = _stage_values(state)[stage]
        new_value = _next_stage_value(old_value, spec.ladder)
        _set_stage(state, stage, int(new_value))
        _set_pending(state, stage, int(new_value))
        cell["oldValue"] = old_value
        cell["newValue"] = new_value
        cell["oldGlobal"] = old_active
        cell["newGlobal"] = active_multiplier(state)

    state.wind_keys += 1
    tally.wind_keys += 1


def apply_new_winds_a1(specials, state: Phase6A1State, rng, spec: Phase6A1Spec, tally: SpinTallyA1) -> None:
    winds = sorted(
        pos for pos, cell in specials.items() if cell["kind"] == KIND_WIND and not cell.get("processed")
    )
    for pos in winds:
        apply_wind_key(state, spec, rng, specials[pos], tally)


def _apply_thermals(specials) -> float:
    """Reset and recompute effective token values from current thermals. Returns raw sum."""
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


def _settle_unpaid_collectors(
    specials,
    multiplier: int,
    tally: SpinTallyA1,
    *,
    after_rejump: bool,
    token_positions_before: set[tuple[int, int]] | None,
) -> float:
    raw_sum = _apply_thermals(specials)
    unpaid = []
    for pos, cell in specials.items():
        if cell["kind"] == KIND_JUDGE and not cell.get("paid"):
            unpaid.append(("judge", pos))
        elif cell["kind"] == KIND_HEAD and not cell.get("paid"):
            unpaid.append(("head", pos))
    unpaid.sort(key=lambda row: (row[1][0], row[1][1], 0 if row[0] == "judge" else 1))
    raw_paid = 0.0
    for kind, pos in unpaid:
        if kind == "judge":
            raw_paid += raw_sum
            tally.judges += 1
            if after_rejump:
                tally.post_rejump_judges += 1
        else:
            raw_paid += raw_sum * 2.0
            tally.heads += 1
            if after_rejump:
                tally.post_rejump_heads += 1
        specials[pos]["paid"] = True
        # Visual cell remains; payout authority is spent.
        specials[pos]["payoutSpent"] = True
    paid = raw_paid * float(multiplier)
    tally.collector_raw += raw_paid
    tally.collector_paid += paid
    if after_rejump:
        tally.collector_after_rejump += paid
        if token_positions_before:
            # Approximate recollection: share of raw that comes from tokens that
            # already existed before this redrop, times unpaid collector passes.
            pre_sum = 0.0
            for pos, cell in specials.items():
                if cell["kind"] != KIND_TOKEN:
                    continue
                if pos in token_positions_before:
                    pre_sum += float(cell.get("effectiveValueX") or 0.0)
            passes = sum(1 if kind == "judge" else 2 for kind, _ in unpaid)
            tally.collector_recollection += pre_sum * passes * float(multiplier)
    else:
        tally.collector_initial_batch += paid
    return paid


def resolve_phase6a1_spin(
    rng,
    state: Phase6A1State,
    spec: Phase6A1Spec,
    *,
    strips_by_tier: dict,
    catalogs_by_tier: dict,
    config: dict,
    paying: dict,
    regular_ids: set[str],
    paylines,
    paytable,
    scatter_id: str,
    mystery_id: str,
    coach_id: str,
    perfect_rows: tuple,
    max_floor: int,
    scale: float,
    thermal_weights: dict[str, int],
    token_tables: dict,
    initial_spins: int,
    max_spins: int,
    max_targets: int,
    upgrade_rule: str,
    round_prior_win_x: float,
    max_win_x: float,
) -> tuple[SpinTallyA1, float]:
    from skyjump_v2_exact import scatter_on_board

    del config, paying, initial_spins
    # Activate pending at the start of every Free Spin for W-NEXT-SPIN.
    if spec.wind_arch == "W-NEXT-SPIN":
        activate_pending(state)
    else:
        # Keep pending mirrored for reporting.
        state.pending_run_up = state.run_up
        state.pending_takeoff = state.takeoff
        state.pending_flight = state.flight

    active_at_start = active_multiplier(state)
    state.active_mult_history.append(active_at_start)

    tier = state.bonusTier
    strips = strips_by_tier[tier]
    catalogs = catalogs_by_tier[tier]
    stops = [rng.randrange(len(strip)) for strip in strips]
    board = board_from_stops(strips, stops)
    evaluated = evaluate_paylines(
        board,
        paylines=paylines,
        paytable=paytable,
        scatter_id=scatter_id,
        regular_ids=regular_ids,
    )
    line_win = float(evaluated["lineWinX"])
    scatter = scatter_on_board(board, scatter_id, perfect_rows)
    tally = SpinTallyA1(line_initial=line_win)
    scatter_cells = {
        (reel, row)
        for reel in range(5)
        for row in range(5)
        if board[reel][row] == scatter_id
    }
    _apply_persist(board, state.persistentMysteryTargets, mystery_id)
    force_coach = tier == "PERFECT_V"
    selected, resolved_coaches, _synthetic = _run_coaches(
        board,
        rng,
        regular_ids=regular_ids,
        coach_id=coach_id,
        mystery_id=mystery_id,
        exclude=set(state.persistentMysteryTargets),
        prefer_b=True,
        force_if_none=force_coach,
    )
    resolved_coaches = set(resolved_coaches)
    if tier in ("SKI_FLYING", "WORLD_CUP", "PERFECT_V"):
        for symbol in selected:
            if symbol in state.persistentMysteryTargets:
                continue
            if len(state.persistentMysteryTargets) >= max_targets:
                break
            state.persistentMysteryTargets.append(symbol)

    weights = spec.weights_by_tier[tier]
    allow_wind = not (spec.saturation == "B" and stages_maxed_a1(state, spec))
    positions = _mystery_positions(board, mystery_id, None)
    specials: dict[tuple[int, int], dict] = {}
    for pos, cell in _resolve_mysteries(
        board, positions, rng, weights, token_tables, scale, thermal_weights, allow_wind=allow_wind
    ):
        specials[pos] = cell
        tally.mysteries += 1
    _paint_specials(board, specials)

    if tier in ("WORLD_CUP", "PERFECT_V") and not state.guaranteedGateUsed:
        if not any(cell["kind"] == KIND_GATE for cell in specials.values()):
            candidates = []
            for pos, cell in specials.items():
                if cell["kind"] == KIND_THERMAL:
                    candidates.append((0, pos))
                elif cell["kind"] == KIND_TOKEN and int(cell.get("tokenTier") or 9) <= 4:
                    candidates.append((1, pos))
            if candidates:
                candidates.sort()
                pos = candidates[0][1]
                specials[pos] = _materialise(rng, "GATE_UPGRADE", token_tables, scale, thermal_weights)
                board[pos[0]][pos[1]] = "GATE"
                state.guaranteedGateUsed = True

    # PV2/PV3 kept for parity with Phase 6A research; default search uses PV1.
    if (
        spec.perfect_v == "PV2"
        and tier == "PERFECT_V"
        and not state.pv_key_used
        and not stages_maxed_a1(state, spec)
    ):
        fake = empty_cell()
        fake.update({"kind": KIND_WIND, "resultType": "WIND_KEY", "processed": False})
        apply_wind_key(state, spec, rng, fake, tally)
        state.pv_key_used = True
    if spec.perfect_v == "PV3" and tier == "PERFECT_V" and not state.pv_key_used:
        if _maybe_force_wind(board, specials, rng, token_tables, scale, thermal_weights, weights):
            state.pv_key_used = True

    batch_index = 0
    token_positions_before: set[tuple[int, int]] = set()

    def settle_multiplier() -> int:
        # Collectors always use the active (start-of-spin) product under W-NEXT-SPIN.
        # Under W-IMMEDIATE / W-CHARGE they use the live active product after keys.
        if spec.wind_arch == "W-NEXT-SPIN":
            return active_at_start
        return active_multiplier(state)

    def consume_batch() -> int:
        nonlocal batch_index, token_positions_before
        state.tokenFloorTier = apply_new_gates(
            specials, state.tokenFloorTier, rng, token_tables, scale, max_floor, tally
        )
        _paint_specials(board, specials)
        apply_new_winds_a1(specials, state, rng, spec, tally)

        if spec.rejump_arch == "R-BATCH":
            mult = settle_multiplier()
            tally.active_mult_at_settle = mult
            after = batch_index > 0
            _settle_unpaid_collectors(
                specials,
                mult,
                tally,
                after_rejump=after,
                token_positions_before=token_positions_before if after else None,
            )
            tally.thermals = sum(1 for cell in specials.values() if cell["kind"] == KIND_THERMAL)
            tally.tokens = sum(1 for cell in specials.values() if cell["kind"] == KIND_TOKEN)
            if after:
                tally.post_rejump_tokens += sum(
                    1
                    for pos, cell in specials.items()
                    if cell["kind"] == KIND_TOKEN and pos not in token_positions_before
                )

        return _take_rejumps(specials)

    queue = consume_batch()
    chain = 0
    while queue > 0:
        if chain >= spec.max_chain_depth or tally.rejumps >= spec.max_rejumps_per_spin:
            tally.truncated += queue
            state.truncated_rejumps += queue
            state.hit_chain_bound = True
            queue = 0
            break
        token_positions_before = {pos for pos, cell in specials.items() if cell["kind"] == KIND_TOKEN}
        queue -= 1
        chain += 1
        batch_index += 1
        tally.rejumps += 1
        state.rejumps_bonus += 1
        locked = _locked_positions(board, specials, scatter_cells, resolved_coaches)
        # Spent collectors remain locked for board presentation.
        tally.max_locked_frac = max(tally.max_locked_frac, len(locked) / 25.0)
        _redrop(board, locked, strips, catalogs, rng)
        rejump_eval = evaluate_paylines(
            board,
            paylines=paylines,
            paytable=paytable,
            scatter_id=scatter_id,
            regular_ids=regular_ids,
        )
        tally.line_rejump += float(rejump_eval["lineWinX"])
        fresh = {
            (reel, row)
            for reel in range(5)
            for row in range(5)
            if (reel, row) not in locked
        }
        _apply_persist(board, state.persistentMysteryTargets, mystery_id)
        coach_cells = {(reel, row) for reel, row in fresh if board[reel][row] == coach_id}
        selected_new, resolved_new, _unused = _run_coaches(
            board,
            rng,
            regular_ids=regular_ids,
            coach_id=coach_id,
            mystery_id=mystery_id,
            exclude=set(state.persistentMysteryTargets),
            prefer_b=True,
            force_if_none=False,
            only_positions=coach_cells,
        )
        resolved_coaches.update(resolved_new)
        if tier in ("SKI_FLYING", "WORLD_CUP", "PERFECT_V"):
            for symbol in selected_new:
                if symbol in state.persistentMysteryTargets:
                    continue
                if len(state.persistentMysteryTargets) >= max_targets:
                    break
                state.persistentMysteryTargets.append(symbol)
        spawned = [pos for pos in _mystery_positions(board, mystery_id, None) if pos not in specials]
        allow_wind = not (spec.saturation == "B" and stages_maxed_a1(state, spec))
        for pos, cell in _resolve_mysteries(
            board, spawned, rng, weights, token_tables, scale, thermal_weights, allow_wind=allow_wind
        ):
            specials[pos] = cell
            tally.mysteries += 1
        _paint_specials(board, specials)
        queue += consume_batch()
        tally.max_locked_frac = max(
            tally.max_locked_frac,
            _locked_fraction(specials, scatter_cells, resolved_coaches),
        )

    state.max_chain = max(state.max_chain, chain)
    tally.chain = chain

    if spec.rejump_arch == "R-DELAYED":
        mult = settle_multiplier()
        tally.active_mult_at_settle = mult
        _settle_unpaid_collectors(
            specials,
            mult,
            tally,
            after_rejump=False,
            token_positions_before=None,
        )
        # Under delayed settlement the whole payment is one pass; attribute
        # post-rejump share by whether any rejump occurred and new tokens exist.
        if tally.rejumps > 0:
            tally.collector_after_rejump = 0.0  # not separable cleanly; leave lines separate

    spin_raw = tally.line_initial + tally.line_rejump + tally.collector_paid
    room = max(0.0, max_win_x - round_prior_win_x - state.bonusWinXCapped)
    spin_capped = min(spin_raw, room)
    state.bonusWinXRaw += spin_raw
    state.bonusWinXCapped += spin_capped
    settle_mult = int(tally.active_mult_at_settle or active_at_start)
    state.collector_paid_by_active_mult[settle_mult] = (
        state.collector_paid_by_active_mult.get(settle_mult, 0.0) + tally.collector_paid
    )
    if state.bonusWinXCapped + round_prior_win_x >= max_win_x - 1e-9:
        state.maxWinReached = True

    # Wind key timing bookkeeping for W-NEXT-SPIN.
    if tally.wind_keys > 0 and state.first_key_spin is None:
        state.first_key_spin = state.freeSpinsPlayed
    if tally.pending_keys_this_spin > 0:
        remaining_after = state.freeSpinsRemaining - 1
        if remaining_after > 0:
            state.keys_with_future_spin += tally.pending_keys_this_spin
        else:
            state.keys_on_final_spin += tally.pending_keys_this_spin

    upgrade = apply_upgrade_rule(upgrade_rule, int(scatter["count"]), bool(scatter["perfectV"]), state.bonusTier)
    if upgrade["retriggered"]:
        room_spins = max(0, max_spins - state.spinsAwardedTotal)
        spins_added = min(int(upgrade["addSpins"]), room_spins)
        if spins_added > 0:
            state.freeSpinsRemaining += spins_added
            state.spinsAwardedTotal += spins_added
            state.retriggerCount += 1
            # Keys that looked final may still activate if a retrigger extends.
            if tally.pending_keys_this_spin > 0 and spins_added > 0:
                moved = tally.pending_keys_this_spin
                state.keys_on_final_spin = max(0, state.keys_on_final_spin - moved)
                state.keys_with_future_spin += moved
        if upgrade["upgraded"]:
            state.pendingTier = upgrade["newTier"]
            state.upgradeCount += 1

    passes = tally.judges + tally.heads * 2
    tally.events = (
        8
        + tally.mysteries
        + tally.gates
        + tally.wind_keys
        + tally.rejumps * 4
        + passes
        + (1 if tally.thermals else 0)
        + (1 if upgrade["retriggered"] else 0)
        + (1 if tally.pending_keys_this_spin else 0)
    )
    state.freeSpinsRemaining -= 1
    state.freeSpinsPlayed += 1
    if state.pendingTier is not None and state.freeSpinsRemaining > 0:
        state.bonusTier = state.pendingTier
        state.pendingTier = None
    return tally, spin_capped


def simulate_phase6a1_bonus(
    rng,
    start_tier: str,
    spec: Phase6A1Spec,
    **kwargs,
) -> dict:
    state = new_phase6a1_state(start_tier, initial_spins=kwargs["initial_spins"])
    total_events = 6
    tally_sum = SpinTallyA1()
    max_locked = 0.0
    safety = 0
    while state.freeSpinsRemaining > 0 and not state.maxWinReached:
        tally, _capped = resolve_phase6a1_spin(
            rng,
            state,
            spec,
            round_prior_win_x=kwargs["round_prior_win_x"],
            **{k: v for k, v in kwargs.items() if k not in ("round_prior_win_x",)},
        )
        total_events += tally.events
        for name in (
            "line_initial",
            "line_rejump",
            "collector_raw",
            "collector_paid",
            "collector_initial_batch",
            "collector_after_rejump",
            "collector_recollection",
            "rejumps",
            "wind_keys",
            "truncated",
            "gates",
            "tokens",
            "judges",
            "heads",
            "post_rejump_tokens",
            "post_rejump_judges",
            "post_rejump_heads",
        ):
            setattr(tally_sum, name, getattr(tally_sum, name) + getattr(tally, name))
        max_locked = max(max_locked, tally.max_locked_frac)
        safety += 1
        if safety > kwargs["max_spins"] + 2:
            break

    if state.first_key_spin is not None:
        state.spins_after_first_key = max(0, state.freeSpinsPlayed - 1 - state.first_key_spin)

    pending_unused = 0
    if spec.wind_arch == "W-NEXT-SPIN" and pending_multiplier(state) > active_multiplier(state):
        # Bonus ended with a pending upgrade that never became active.
        pending_unused = 1
        state.pending_unused_keys = state.keys_on_final_spin

    return {
        "capped": state.bonusWinXCapped,
        "raw": state.bonusWinXRaw,
        "spins": state.freeSpinsPlayed,
        "events": total_events,
        "lineInitial": tally_sum.line_initial,
        "lineRejump": tally_sum.line_rejump,
        "collectorRaw": tally_sum.collector_raw,
        "collectorPaid": tally_sum.collector_paid,
        "collectorInitialBatch": tally_sum.collector_initial_batch,
        "collectorAfterRejump": tally_sum.collector_after_rejump,
        "collectorRecollection": tally_sum.collector_recollection,
        "rejumps": tally_sum.rejumps,
        "windKeys": state.wind_keys,
        "multiplier": active_multiplier(state),
        "pendingMultiplier": pending_multiplier(state),
        "runUp": state.run_up,
        "takeoff": state.takeoff,
        "flight": state.flight,
        "truncated": state.truncated_rejumps,
        "hitBound": state.hit_chain_bound,
        "maxChain": state.max_chain,
        "maxLocked": max_locked,
        "cap": state.maxWinReached,
        "capDrag": max(0.0, state.bonusWinXRaw - state.bonusWinXCapped),
        "finalTier": state.bonusTier,
        "pendingUnused": pending_unused,
        "keysOnFinalSpin": state.keys_on_final_spin,
        "keysWithFutureSpin": state.keys_with_future_spin,
        "spinsAfterFirstKey": state.spins_after_first_key,
        "postRejumpTokens": tally_sum.post_rejump_tokens,
        "postRejumpJudges": tally_sum.post_rejump_judges,
        "postRejumpHeads": tally_sum.post_rejump_heads,
        "rejumpArch": spec.rejump_arch,
        "windArch": spec.wind_arch,
        "collectorByMult": dict(state.collector_paid_by_active_mult),
        "meanActiveMult": (
            sum(state.active_mult_history) / len(state.active_mult_history)
            if state.active_mult_history
            else 1.0
        ),
    }
