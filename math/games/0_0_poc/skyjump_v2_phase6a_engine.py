"""Phase 6A research engine for Rejump and Wind Key / Flight Multiplier.

Math-only. Does not read or write live Free Spin config and does not change
BASE F01. Mystery weights are research tables passed in by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from skyjump_v2_features import eligible_regular_types
from skyjump_v2_lines import evaluate_paylines
from skyjump_v2_phase4a_economy import (
    build_token_tables,
    empty_cell,
    neighbours,
    sample_token_at_floor,
)
from skyjump_v2_phase5a_engine import FreeSpinState, apply_upgrade_rule
from skyjump_v2_reels import board_from_stops

BASE_LABELS = ("FLIGHT_TOKEN", "THERMAL_LIFT", "GATE_UPGRADE", "JUDGE", "HEAD_JUDGE")
ALL_LABELS = BASE_LABELS + ("REJUMP", "WIND_KEY")
LADDERS = {
    "K1": (1, 2, 3),
    "K2": (1, 2, 3, 4),
    "K3": (1, 2, 3, 5),
}
KIND_TOKEN = "token"
KIND_THERMAL = "thermal"
KIND_GATE = "gate"
KIND_JUDGE = "judge"
KIND_HEAD = "head_judge"
KIND_WIND = "wind"
KIND_REJUMP = "rejump"


@dataclass
class Phase6Spec:
    id: str
    weights_by_tier: dict[str, dict[str, int]]
    ladder: str = "K1"
    stage_rule: str = "W2"
    saturation: str = "B"
    availability: str = "C"
    perfect_v: str = "PV1"
    max_rejumps_per_spin: int = 2
    max_chain_depth: int = 8


@dataclass
class Phase6State(FreeSpinState):
    run_up: int = 1
    takeoff: int = 1
    flight: int = 1
    wind_keys: int = 0
    rejumps_bonus: int = 0
    max_chain: int = 0
    truncated_rejumps: int = 0
    pv_key_used: bool = False
    hit_chain_bound: bool = False


@dataclass
class SpinTally:
    line_initial: float = 0.0
    line_rejump: float = 0.0
    collector_raw: float = 0.0
    collector_paid: float = 0.0
    rejumps: int = 0
    wind_keys: int = 0
    events: int = 0
    max_locked_frac: float = 0.0
    chain: int = 0
    truncated: int = 0
    gates: int = 0
    thermals: int = 0
    tokens: int = 0
    judges: int = 0
    heads: int = 0
    mysteries: int = 0


def new_phase6_state(tier: str, *, initial_spins: int = 10) -> Phase6State:
    return Phase6State(
        bonusTier=tier,
        freeSpinsRemaining=initial_spins,
        spinsAwardedTotal=initial_spins,
    )


def global_multiplier(state: Phase6State) -> int:
    return int(state.run_up) * int(state.takeoff) * int(state.flight)


def _next_stage_value(current: int, ladder: str) -> int | None:
    order = LADDERS[ladder]
    if current not in order:
        return None
    index = order.index(current)
    if index + 1 >= len(order):
        return None
    return order[index + 1]


def _stage_values(state: Phase6State) -> dict[str, int]:
    return {"RUN_UP": state.run_up, "TAKEOFF": state.takeoff, "FLIGHT": state.flight}


def _set_stage(state: Phase6State, stage: str, value: int) -> None:
    if stage == "RUN_UP":
        state.run_up = value
    elif stage == "TAKEOFF":
        state.takeoff = value
    else:
        state.flight = value


def choose_stage(rng, state: Phase6State, spec: Phase6Spec) -> str | None:
    values = _stage_values(state)
    eligible = [name for name, value in values.items() if _next_stage_value(value, spec.ladder) is not None]
    if not eligible:
        return None
    if spec.stage_rule == "W1":
        return rng.choice(eligible)
    lowest = min(values[name] for name in eligible)
    pool = [name for name in eligible if values[name] == lowest]
    return rng.choice(pool)


def stages_maxed(state: Phase6State, spec: Phase6Spec) -> bool:
    return all(_next_stage_value(value, spec.ladder) is None for value in _stage_values(state).values())


def draw_mystery(rng, weights: dict[str, int], *, allow_wind: bool) -> str:
    labels = []
    vals = []
    for label in ALL_LABELS:
        weight = int(weights.get(label, 0))
        if label == "WIND_KEY" and not allow_wind:
            continue
        if weight <= 0:
            continue
        labels.append(label)
        vals.append(weight)
    total = sum(vals)
    roll = rng.randrange(total)
    cursor = 0
    for label, weight in zip(labels, vals, strict=True):
        cursor += weight
        if roll < cursor:
            return label
    return labels[-1]


def _token_result(rng, tables: dict, scale: float) -> dict:
    from skyjump_v2_tokens import sample_token

    token = sample_token(rng, tables)
    face = float(token["tokenValueX"]) * scale
    cell = empty_cell()
    cell.update(
        {
            "kind": KIND_TOKEN,
            "resultType": "FLIGHT_TOKEN",
            "tokenTier": token["tokenTier"],
            "tokenId": token["tokenId"],
            "faceValueX": face,
            "effectiveValueX": face,
            "tokenValueX": face,
        }
    )
    return cell


def _materialise(rng, label: str, tables: dict, scale: float, thermal_weights: dict[str, int]) -> dict:
    if label == "FLIGHT_TOKEN":
        return _token_result(rng, tables, scale)
    cell = empty_cell()
    if label == "THERMAL_LIFT":
        mults = [int(key) for key in thermal_weights]
        weights = [int(thermal_weights[str(mult)]) for mult in mults]
        total = sum(weights)
        roll = rng.randrange(total)
        cursor = 0
        chosen = mults[-1]
        for mult, weight in zip(mults, weights, strict=True):
            cursor += weight
            if roll < cursor:
                chosen = mult
                break
        cell.update({"kind": KIND_THERMAL, "resultType": "THERMAL_LIFT", "thermalMult": chosen})
        return cell
    if label == "GATE_UPGRADE":
        cell.update({"kind": KIND_GATE, "resultType": "GATE_UPGRADE"})
        return cell
    if label == "JUDGE":
        cell.update({"kind": KIND_JUDGE, "resultType": "JUDGE"})
        return cell
    if label == "HEAD_JUDGE":
        cell.update({"kind": KIND_HEAD, "resultType": "HEAD_JUDGE"})
        return cell
    if label == "WIND_KEY":
        cell.update({"kind": KIND_WIND, "resultType": "WIND_KEY", "processed": False})
        return cell
    cell.update({"kind": KIND_REJUMP, "resultType": "REJUMP"})
    return cell


def _symbol_for(cell: dict) -> str:
    kind = cell["kind"]
    if kind == KIND_TOKEN:
        return cell["tokenId"]
    if kind == KIND_THERMAL:
        return "THERMAL"
    if kind == KIND_GATE:
        return "GATE"
    if kind == KIND_JUDGE:
        return "JUDGE"
    if kind == KIND_HEAD:
        return "HEAD_JUDGE"
    if kind == KIND_WIND:
        return "WIND"
    return "L1"


def refill_catalogs(strips: list[list[str]]) -> list[tuple[str, ...]]:
    catalogs = []
    for strip in strips:
        cleaned = tuple(symbol for symbol in strip if symbol != "S")
        if not cleaned:
            raise RuntimeError("rejump refill strip has no non-scatter symbol")
        catalogs.append(cleaned)
    return catalogs


def _locked_positions(board, specials, scatter_cells, resolved_coaches) -> set[tuple[int, int]]:
    locked = set(specials)
    locked.update(scatter_cells)
    locked.update(resolved_coaches)
    return locked


def _redrop(board, locked, strips, catalogs, rng) -> tuple[list[dict], list[dict]]:
    preserved = [{"reel": reel, "row": row} for reel, row in sorted(locked)]
    redropped = []
    for reel in range(5):
        strip = strips[reel]
        stop = rng.randrange(len(strip))
        catalog = catalogs[reel]
        for row in range(5):
            if (reel, row) in locked:
                continue
            symbol = strip[(stop + row) % len(strip)]
            if symbol == "S":
                symbol = catalog[rng.randrange(len(catalog))]
            if symbol == "S":
                raise RuntimeError("rejump refill produced a scatter")
            board[reel][row] = symbol
            redropped.append({"reel": reel, "row": row})
    return preserved, redropped


def _apply_persist(board, targets, mystery_id) -> int:
    if not targets:
        return 0
    wanted = set(targets)
    count = 0
    for reel in range(5):
        for row in range(5):
            if board[reel][row] in wanted:
                board[reel][row] = mystery_id
                count += 1
    return count


def _run_coaches(board, rng, *, regular_ids, coach_id, mystery_id, exclude, prefer_b, force_if_none, only_positions=None):
    coaches = []
    for reel in range(5):
        for row in range(5):
            if board[reel][row] != coach_id:
                continue
            if only_positions is not None and (reel, row) not in only_positions:
                continue
            coaches.append((reel, row))
    synthetic = False
    if force_if_none and not coaches:
        coaches.append((-1, -1))
        synthetic = True
    selected = []
    resolved = []
    for index, (reel, row) in enumerate(coaches):
        eligible = eligible_regular_types(board, regular_ids)
        if not eligible:
            continue
        pool = eligible
        if prefer_b and exclude:
            preferred = [symbol for symbol in eligible if symbol not in exclude]
            if preferred:
                pool = preferred
        choice = rng.choice(pool)
        for pos_reel in range(5):
            for pos_row in range(5):
                if board[pos_reel][pos_row] == choice:
                    board[pos_reel][pos_row] = mystery_id
        selected.append(choice)
        if reel >= 0:
            resolved.append((reel, row))
        del index
    return selected, resolved, synthetic or (force_if_none and not resolved and coaches)


def _mystery_positions(board, mystery_id, restrict: set[tuple[int, int]] | None):
    found = []
    for reel in range(5):
        for row in range(5):
            if board[reel][row] != mystery_id:
                continue
            if restrict is not None and (reel, row) not in restrict:
                continue
            found.append((reel, row))
    return found


def _resolve_mysteries(board, positions, rng, weights, tables, scale, thermal_weights, *, allow_wind):
    specials_added = []
    for reel, row in positions:
        label = draw_mystery(rng, weights, allow_wind=allow_wind)
        cell = _materialise(rng, label, tables, scale, thermal_weights)
        board[reel][row] = _symbol_for(cell) if cell["kind"] != KIND_REJUMP else "L3"
        # Rejump markers are not pay symbols. Park them as a non-regular sentinel
        # until the chain consumes or drops them.
        if cell["kind"] == KIND_REJUMP:
            board[reel][row] = "REJUMP"
        specials_added.append(((reel, row), cell))
    return specials_added


def apply_new_gates(specials, floor: int, rng, tables, scale: float, max_floor: int, tally: SpinTally) -> int:
    gates = sorted(
        pos for pos, cell in specials.items() if cell["kind"] == KIND_GATE and not cell.get("processed")
    )
    for pos in gates:
        before = floor
        if floor < max_floor:
            floor = min(max_floor, floor + 1)
        if floor > before:
            for token_pos, token in list(specials.items()):
                if token["kind"] != KIND_TOKEN:
                    continue
                if int(token["tokenTier"]) >= floor:
                    continue
                replacement = sample_token_at_floor(rng, tables, floor, scale=scale)
                token.clear()
                token.update(replacement)
                token["processed"] = False
        specials[pos]["processed"] = True
        specials[pos]["floorAfter"] = floor
        tally.gates += 1
    return floor


def apply_new_winds(specials, state: Phase6State, rng, spec: Phase6Spec, tally: SpinTally) -> None:
    winds = sorted(
        pos for pos, cell in specials.items() if cell["kind"] == KIND_WIND and not cell.get("processed")
    )
    for pos in winds:
        cell = specials[pos]
        stage = choose_stage(rng, state, spec)
        old_global = global_multiplier(state)
        if stage is None:
            cell["processed"] = True
            cell["noOp"] = True
            continue
        old_value = _stage_values(state)[stage]
        new_value = _next_stage_value(old_value, spec.ladder)
        _set_stage(state, stage, int(new_value))
        cell["processed"] = True
        cell["stage"] = stage
        cell["oldValue"] = old_value
        cell["newValue"] = new_value
        cell["oldGlobal"] = old_global
        cell["newGlobal"] = global_multiplier(state)
        state.wind_keys += 1
        tally.wind_keys += 1


def _take_rejumps(specials) -> int:
    positions = [pos for pos, cell in specials.items() if cell["kind"] == KIND_REJUMP]
    for pos in positions:
        del specials[pos]
    return len(positions)


def _paint_specials(board, specials) -> None:
    for (reel, row), cell in specials.items():
        if cell["kind"] == KIND_REJUMP:
            board[reel][row] = "REJUMP"
        else:
            board[reel][row] = _symbol_for(cell)


def _locked_fraction(specials, scatter_cells, resolved_coaches) -> float:
    return len(_locked_positions(None, specials, scatter_cells, resolved_coaches)) / 25.0


def _settle_collectors(specials, multiplier: int, tally: SpinTally) -> tuple[float, float, int, int]:
    thermals = [(pos, int(cell["thermalMult"])) for pos, cell in specials.items() if cell["kind"] == KIND_THERMAL]
    tally.thermals += len(thermals)
    for (reel, row), mult in thermals:
        for nr, nc in neighbours(reel, row):
            token = specials.get((nr, nc))
            if not token or token["kind"] != KIND_TOKEN:
                continue
            token["appliedThermals"].append(mult)
    raw_sum = 0.0
    token_count = 0
    for cell in specials.values():
        if cell["kind"] != KIND_TOKEN:
            continue
        token_count += 1
        product = 1.0
        for mult in cell["appliedThermals"]:
            product *= float(mult)
        effective = float(cell["faceValueX"]) * product
        cell["effectiveValueX"] = effective
        raw_sum += effective
    tally.tokens += token_count
    judges = sorted(pos for pos, cell in specials.items() if cell["kind"] == KIND_JUDGE)
    heads = sorted(pos for pos, cell in specials.items() if cell["kind"] == KIND_HEAD)
    raw_paid = 0.0
    for _pos in judges:
        raw_paid += raw_sum
        tally.judges += 1
    for _pos in heads:
        raw_paid += raw_sum * 2.0
        tally.heads += 1
    paid = raw_paid * float(multiplier)
    tally.collector_raw += raw_paid
    tally.collector_paid += paid
    return raw_paid, paid, len(judges), len(heads)


def _maybe_force_wind(board, specials, rng, tables, scale, thermal_weights, weights) -> bool:
    """PV3: one Wind Key on the first Perfect V spin if the batch has none."""
    if any(cell["kind"] == KIND_WIND for cell in specials.values()):
        return False
    candidates = []
    for pos, cell in specials.items():
        if cell["kind"] == KIND_THERMAL:
            candidates.append((0, pos))
        elif cell["kind"] == KIND_TOKEN and int(cell.get("tokenTier") or 9) <= 4:
            candidates.append((1, pos))
    if not candidates:
        return False
    candidates.sort()
    pos = candidates[0][1]
    cell = _materialise(rng, "WIND_KEY", tables, scale, thermal_weights)
    specials[pos] = cell
    board[pos[0]][pos[1]] = "WIND"
    del weights
    return True


def resolve_phase6_spin(
    rng,
    state: Phase6State,
    spec: Phase6Spec,
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
) -> tuple[SpinTally, float]:
    from skyjump_v2_exact import scatter_on_board

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
    tally = SpinTally(line_initial=line_win)
    scatter_cells = {
        (reel, row)
        for reel in range(5)
        for row in range(5)
        if board[reel][row] == scatter_id
    }
    _apply_persist(board, state.persistentMysteryTargets, mystery_id)
    prefer_b = True
    force_coach = tier == "PERFECT_V"
    selected, resolved_coaches, _synthetic = _run_coaches(
        board,
        rng,
        regular_ids=regular_ids,
        coach_id=coach_id,
        mystery_id=mystery_id,
        exclude=set(state.persistentMysteryTargets),
        prefer_b=prefer_b,
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
    allow_wind = not (spec.saturation == "B" and stages_maxed(state, spec))
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

    if (
        spec.perfect_v == "PV2"
        and tier == "PERFECT_V"
        and not state.pv_key_used
        and not stages_maxed(state, spec)
    ):
        stage = choose_stage(rng, state, spec)
        if stage is not None:
            _set_stage(state, stage, int(_next_stage_value(_stage_values(state)[stage], spec.ladder)))
            state.wind_keys += 1
            state.pv_key_used = True
            tally.wind_keys += 1
    if spec.perfect_v == "PV3" and tier == "PERFECT_V" and not state.pv_key_used:
        if _maybe_force_wind(board, specials, rng, token_tables, scale, thermal_weights, weights):
            state.pv_key_used = True

    def consume_batch() -> int:
        state.tokenFloorTier = apply_new_gates(
            specials, state.tokenFloorTier, rng, token_tables, scale, max_floor, tally
        )
        _paint_specials(board, specials)
        apply_new_winds(specials, state, rng, spec, tally)
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
        queue -= 1
        chain += 1
        tally.rejumps += 1
        state.rejumps_bonus += 1
        locked = _locked_positions(board, specials, scatter_cells, resolved_coaches)
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
        new_positions = {(reel, row) for reel, row in fresh if board[reel][row] == mystery_id}
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
        spawned = _mystery_positions(board, mystery_id, None)
        # Only mysteries that were not already resolved into specials.
        spawned = [pos for pos in spawned if pos not in specials]
        allow_wind = not (spec.saturation == "B" and stages_maxed(state, spec))
        for pos, cell in _resolve_mysteries(
            board, spawned, rng, weights, token_tables, scale, thermal_weights, allow_wind=allow_wind
        ):
            specials[pos] = cell
            tally.mysteries += 1
        new_positions.update(spawned)
        del new_positions
        _paint_specials(board, specials)
        queue += consume_batch()
        tally.max_locked_frac = max(
            tally.max_locked_frac,
            _locked_fraction(specials, scatter_cells, resolved_coaches),
        )

    state.max_chain = max(state.max_chain, chain)
    tally.chain = chain
    multiplier = global_multiplier(state)
    _raw, paid, _judges, _heads = _settle_collectors(specials, multiplier, tally)
    spin_raw = tally.line_initial + tally.line_rejump + paid
    room = max(0.0, max_win_x - round_prior_win_x - state.bonusWinXCapped)
    spin_capped = min(spin_raw, room)
    state.bonusWinXRaw += spin_raw
    state.bonusWinXCapped += spin_capped
    if state.bonusWinXCapped + round_prior_win_x >= max_win_x - 1e-9:
        state.maxWinReached = True

    upgrade = apply_upgrade_rule(upgrade_rule, int(scatter["count"]), bool(scatter["perfectV"]), state.bonusTier)
    if upgrade["retriggered"]:
        room_spins = max(0, max_spins - state.spinsAwardedTotal)
        spins_added = min(int(upgrade["addSpins"]), room_spins)
        if spins_added > 0:
            state.freeSpinsRemaining += spins_added
            state.spinsAwardedTotal += spins_added
            state.retriggerCount += 1
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
    )
    state.freeSpinsRemaining -= 1
    state.freeSpinsPlayed += 1
    if state.pendingTier is not None and state.freeSpinsRemaining > 0:
        state.bonusTier = state.pendingTier
        state.pendingTier = None
    del initial_spins
    return tally, spin_capped


def simulate_phase6_bonus(
    rng,
    start_tier: str,
    spec: Phase6Spec,
    **kwargs,
) -> dict:
    state = new_phase6_state(start_tier, initial_spins=kwargs["initial_spins"])
    total_events = 6
    tally_sum = SpinTally()
    max_locked = 0.0
    safety = 0
    while state.freeSpinsRemaining > 0 and not state.maxWinReached:
        tally, _capped = resolve_phase6_spin(rng, state, spec, round_prior_win_x=kwargs["round_prior_win_x"], **{k: v for k, v in kwargs.items() if k not in ("round_prior_win_x",)})
        total_events += tally.events
        tally_sum.line_initial += tally.line_initial
        tally_sum.line_rejump += tally.line_rejump
        tally_sum.collector_raw += tally.collector_raw
        tally_sum.collector_paid += tally.collector_paid
        tally_sum.rejumps += tally.rejumps
        tally_sum.wind_keys += tally.wind_keys
        tally_sum.truncated += tally.truncated
        tally_sum.gates += tally.gates
        tally_sum.tokens += tally.tokens
        tally_sum.judges += tally.judges
        tally_sum.heads += tally.heads
        max_locked = max(max_locked, tally.max_locked_frac)
        safety += 1
        if safety > kwargs["max_spins"] + 2:
            break
    product = global_multiplier(state)
    return {
        "capped": state.bonusWinXCapped,
        "raw": state.bonusWinXRaw,
        "spins": state.freeSpinsPlayed,
        "events": total_events,
        "lineInitial": tally_sum.line_initial,
        "lineRejump": tally_sum.line_rejump,
        "collectorRaw": tally_sum.collector_raw,
        "collectorPaid": tally_sum.collector_paid,
        "rejumps": tally_sum.rejumps,
        "windKeys": state.wind_keys,
        "multiplier": product,
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
    }
