"""Phase 4C forced rare-tier conditional analysis (measurement only)."""

from __future__ import annotations

import random
from collections import defaultdict

from skyjump_v2_features import coach_positions, eligible_regular_types, mystery_positions, positions_of
from skyjump_v2_lines import evaluate_paylines, load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase4a_economy import (
    BOARD_SYMBOL_FOR_RESULT,
    MAX_WIN_X,
    RESULT_ORDER,
    THERMAL_MULTS,
    build_token_tables,
    empty_cell,
    neighbours,
    sample_mystery_result,
    sample_token_at_floor,
)
from skyjump_v2_phase4c_exact import exact_flight_token_joint
from skyjump_v2_reels import board_from_stops
from skyjump_v2_resolve import draw_stops, v2_math_tables


def _coach_transform(board, rng, config):
    working = [col[:] for col in board]
    regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    coach_id = config["coachModel"]["id"]
    mystery_id = config["mysteryModel"]["id"]
    coaches = []
    for sequence, coach in enumerate(coach_positions(board, coach_id)):
        eligible = eligible_regular_types(working, regular_ids)
        if not eligible:
            coaches.append({"noOp": True, "sequenceIndex": sequence})
            continue
        selected = rng.choice(eligible)
        selected_positions = positions_of(working, selected)
        for pos in selected_positions:
            working[pos["reel"]][pos["row"]] = mystery_id
        coaches.append(
            {
                "noOp": False,
                "sequenceIndex": sequence,
                "selectedSymbolId": selected,
                "selectedPositions": selected_positions,
            }
        )
    return working, coaches


def _settle(cells, working_symbols, rng, candidate, token_tables, line_win_x: float) -> dict:
    max_floor = int(candidate["gateMaxFloor"])
    max_win = float(candidate.get("maxWinX", MAX_WIN_X))
    floor = 1
    gate_events = []
    gates = sorted((r, c) for r in range(5) for c in range(5) if cells[r][c]["kind"] == "gate")
    for reel, row in gates:
        before = floor
        if floor < max_floor:
            floor = min(max_floor, floor + 1)
        replacements = []
        if floor > before:
            for tr in range(5):
                for tc in range(5):
                    cell = cells[tr][tc]
                    if cell["kind"] != "token" or int(cell["tokenTier"]) >= floor:
                        continue
                    replacement = sample_token_at_floor(rng, token_tables, floor)
                    cell.update(replacement)
                    working_symbols[tr][tc] = cell["tokenId"]
                    replacements.append(True)
        gate_events.append({"floorBefore": before, "floorAfter": floor, "nRep": len(replacements)})

    thermals = [
        (r, c, cells[r][c]["thermalMult"])
        for r in range(5)
        for c in range(5)
        if cells[r][c]["kind"] == "thermal"
    ]
    for reel, row, mult in thermals:
        for nr, nc in neighbours(reel, row):
            if cells[nr][nc]["kind"] == "token":
                cells[nr][nc]["appliedThermals"].append(int(mult))

    effective_sum = 0.0
    max_tier = 0
    token_count = 0
    for r in range(5):
        for c in range(5):
            cell = cells[r][c]
            if cell["kind"] != "token":
                continue
            token_count += 1
            max_tier = max(max_tier, int(cell["tokenTier"]))
            face = float(cell["faceValueX"])
            product = 1.0
            for mult in cell["appliedThermals"]:
                product *= float(mult)
            cell["effectiveValueX"] = face * product
            effective_sum += cell["effectiveValueX"]

    feature_raw = 0.0
    judge = 0
    head = 0
    collectors = []
    for r in range(5):
        for c in range(5):
            kind = cells[r][c]["kind"]
            if kind == "judge":
                collectors.append(("judge", r, c))
            elif kind == "head_judge":
                collectors.append(("head_judge", r, c))
    collectors.sort(key=lambda row: (row[1], row[2], 0 if row[0] == "judge" else 1))
    for kind, r, c in collectors:
        if kind == "judge":
            feature_raw += effective_sum
            judge += 1
        else:
            feature_raw += 2.0 * effective_sum
            head += 1
    passes = judge + 2 * head
    total_raw = float(line_win_x) + feature_raw
    total_capped = min(total_raw, max_win)
    feature_capped = max(0.0, total_capped - float(line_win_x))
    cap_hit = total_raw > max_win
    return {
        "totalFeatureWinXRaw": feature_raw,
        "totalFeatureWinXCapped": feature_capped,
        "totalWinXRaw": total_raw,
        "totalWinXCapped": total_capped,
        "capHit": cap_hit,
        "capDragX": (total_raw - total_capped) if cap_hit else 0.0,
        "maxTokenTier": max_tier,
        "tokenCount": token_count,
        "thermalCount": len(thermals),
        "gateCount": len(gates),
        "judgeCount": judge,
        "headJudgeCount": head,
        "collectorPasses": passes,
        "effectiveTokenSumX": effective_sum,
        "hasCollector": passes > 0,
    }


def force_token_on_mystery(result_tier: int, face: float, token_tables: dict) -> dict:
    return {
        "resultType": "FLIGHT_TOKEN",
        "kind": "token",
        "tokenTier": result_tier,
        "tokenId": token_tables["ids"][result_tier],
        "tokenName": token_tables["names"][result_tier],
        "tokenValueX": float(face),
        "thermalMult": None,
        "faceValueX": float(face),
        "effectiveValueX": float(face),
        "appliedThermals": [],
    }


def run_forced_tier_batch(
    *,
    spins: int,
    seed: int,
    forced_tier: int,
    forced_face: float | None = None,
    config: dict | None = None,
) -> dict:
    """Force one random Mystery to FLIGHT_TOKEN at forced_tier(/face); reweight by true p.

    Unbiased estimator of total feature RTP contribution from that forced identity
    when multiplied correctly: each spin weight = N_mysteries * p(FT∧tier∧face).
    """
    config = config or load_v2_config()
    tables = v2_math_tables(config)
    candidate = live_candidate_from_config(config)
    token_tables = build_token_tables(candidate)
    joint = exact_flight_token_joint(config)
    p_ft = joint["pFlightToken"]
    p_tier = joint["pTierGivenFlight"][forced_tier]
    face_dist = joint["pFaceGivenTier"][forced_tier]
    rng = random.Random(seed)

    w_sum = 0.0
    raw_sum = 0.0
    cap_sum = 0.0
    cap_w = 0.0
    excess = 0.0
    collector_w = 0.0
    head_w = 0.0
    multi_pass_w = 0.0
    n_used = 0
    face_stats = defaultdict(lambda: {"w": 0.0, "raw": 0.0, "cap": 0.0, "cap_w": 0.0})

    for _ in range(spins):
        stops = draw_stops(rng, tables["strips"])
        board = board_from_stops(tables["strips"], stops)
        evaluated = evaluate_paylines(
            board,
            paylines=tables["paylines"],
            paytable=tables["paytable"],
            scatter_id=tables["scatterId"],
            regular_ids=tables["regularIds"],
        )
        line_win = float(evaluated["lineWinX"])
        working, coaches = _coach_transform(board, rng, tables["config"])
        myst = mystery_positions(working, tables["config"]["mysteryModel"]["id"])
        n = len(myst)
        if n == 0:
            # No mystery → forced event impossible; contributes 0 with weight 0 for this estimator
            continue
        j = rng.randrange(n)
        if forced_face is None:
            faces = list(face_dist.keys())
            weights = [face_dist[f] for f in faces]
            face = rng.choices(faces, weights=weights, k=1)[0]
            p_face = face_dist[face]
        else:
            face = float(forced_face)
            p_face = face_dist[face]
        # Weight for "at least this forced identity on a uniformly chosen mystery index".
        weight = float(n) * p_ft * p_tier * p_face

        cells = [[empty_cell() for _ in range(5)] for _ in range(5)]
        for index, pos in enumerate(myst):
            if index == j:
                result = force_token_on_mystery(forced_tier, face, token_tables)
            else:
                result = sample_mystery_result(rng, candidate, token_tables, tokens_so_far=0)
                if result["resultType"] == "FLIGHT_TOKEN":
                    result["faceValueX"] = float(result["tokenValueX"])
                    result["effectiveValueX"] = float(result["tokenValueX"])
                    result["appliedThermals"] = []
            cell = empty_cell()
            cell.update(result)
            if cell["kind"] == "token":
                cell["faceValueX"] = float(cell.get("faceValueX") or cell["tokenValueX"])
                cell["effectiveValueX"] = float(cell["faceValueX"])
                cell["appliedThermals"] = list(cell.get("appliedThermals") or [])
                working[pos["reel"]][pos["row"]] = cell["tokenId"]
            else:
                working[pos["reel"]][pos["row"]] = BOARD_SYMBOL_FOR_RESULT[cell["resultType"]]
            cells[pos["reel"]][pos["row"]] = cell

        settled = _settle(cells, working, rng, candidate, token_tables, line_win)
        w_sum += weight
        raw_sum += weight * settled["totalFeatureWinXRaw"]
        cap_sum += weight * settled["totalFeatureWinXCapped"]
        if settled["capHit"]:
            cap_w += weight
            excess += weight * settled["capDragX"]
        if settled["hasCollector"]:
            collector_w += weight
        if settled["headJudgeCount"] > 0:
            head_w += weight
        if settled["collectorPasses"] >= 2:
            multi_pass_w += weight
        fs = face_stats[face]
        fs["w"] += weight
        fs["raw"] += weight * settled["totalFeatureWinXRaw"]
        fs["cap"] += weight * settled["totalFeatureWinXCapped"]
        if settled["capHit"]:
            fs["cap_w"] += weight
        n_used += 1

    if w_sum <= 0:
        return {"forcedTier": forced_tier, "effectiveWeight": 0.0, "samplesUsed": n_used}

    return {
        "forcedTier": forced_tier,
        "forcedFace": forced_face,
        "samplesUsed": n_used,
        "effectiveWeight": w_sum,
        # These are contributions to overall per-spin RTP (already weighted by true event rate).
        "featureRtpRawContribution": raw_sum / spins,
        "featureRtpCappedContribution": cap_sum / spins,
        "capDragRtpContribution": excess / spins,
        "pCapContribution": cap_w / spins,
        "pAnyCollectorGivenForcedApprox": collector_w / w_sum,
        "pHeadJudgeGivenForcedApprox": head_w / w_sum,
        "pMultiPassGivenForcedApprox": multi_pass_w / w_sum,
        "E_raw_given_forced_event": raw_sum / w_sum,
        "E_capped_given_forced_event": cap_sum / w_sum,
        "E_excess_given_cap": (excess / cap_w) if cap_w > 0 else 0.0,
        "byFace": {
            str(int(face)): {
                "rtpRawContribution": row["raw"] / spins,
                "rtpCappedContribution": row["cap"] / spins,
                "pCapGiven": (row["cap_w"] / row["w"]) if row["w"] > 0 else 0.0,
                "E_raw": (row["raw"] / row["w"]) if row["w"] > 0 else 0.0,
                "E_capped": (row["cap"] / row["w"]) if row["w"] > 0 else 0.0,
            }
            for face, row in face_stats.items()
        },
        "note": (
            "Contributions divide by total attempted spins (including zero-mystery). "
            "Estimator forces one mystery identity; weight = N * P(FT∧tier∧face)."
        ),
    }
