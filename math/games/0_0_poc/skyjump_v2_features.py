"""Coach Signal, Snowburst Mystery, and Phase 4B paying feature resolution."""

from __future__ import annotations

from skyjump_v2_paying import has_paying_economy, live_candidate_from_config
from skyjump_v2_reels import COACH_ID, MYSTERY_ID, REGULAR_IDS
from skyjump_v2_tokens import sample_token, token_tables


def coach_positions(board: list[list[str]], coach_id: str = COACH_ID) -> list[dict]:
    found = []
    for reel, col in enumerate(board):
        for row, symbol in enumerate(col):
            if symbol == coach_id:
                found.append({"reel": reel, "row": row})
    return found


def eligible_regular_types(board: list[list[str]], regular_ids: set[str]) -> list[str]:
    found = set()
    for col in board:
        for symbol in col:
            if symbol in regular_ids:
                found.add(symbol)
    return [symbol for symbol in REGULAR_IDS if symbol in found]


def positions_of(board: list[list[str]], symbol_id: str) -> list[dict]:
    found = []
    for reel, col in enumerate(board):
        for row, symbol in enumerate(col):
            if symbol == symbol_id:
                found.append({"reel": reel, "row": row})
    return found


def mystery_positions(board: list[list[str]], mystery_id: str = MYSTERY_ID) -> list[dict]:
    return positions_of(board, mystery_id)


def resolve_features_phase3_latent(board: list[list[str]], rng, config: dict) -> dict:
    """Legacy Phase 3 path: every Mystery → Flight Token, no feature pay."""
    working = [col[:] for col in board]
    regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    coach_id = config["coachModel"]["id"]
    mystery_id = config["mysteryModel"]["id"]
    tables = token_tables(config)
    coaches = []
    transforms = []
    resolves = []
    selected_hist: list[str] = []
    mystery_counts: list[int] = []

    for sequence, coach in enumerate(coach_positions(board, coach_id)):
        eligible = eligible_regular_types(working, regular_ids)
        payload = {
            "coachPosition": coach,
            "sequenceIndex": sequence,
            "eligibleSymbolIds": eligible,
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
        selected = rng.choice(eligible)
        selected_positions = positions_of(working, selected)
        for pos in selected_positions:
            working[pos["reel"]][pos["row"]] = mystery_id
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

    latent = 0.0
    tiers: list[int] = []
    values: list[float] = []
    for pos in mystery_positions(working, mystery_id):
        token = sample_token(rng, tables)
        working[pos["reel"]][pos["row"]] = token["tokenId"]
        token["position"] = pos
        resolves.append(token)
        latent += token["tokenValueX"]
        tiers.append(token["tokenTier"])
        values.append(token["tokenValueX"])

    return {
        "workingBoard": working,
        "coaches": coaches,
        "transforms": transforms,
        "resolves": resolves,
        "selectedSymbolIds": selected_hist,
        "mysteriesPerCoach": mystery_counts,
        "latentTokenValueX": latent,
        "tokenTiers": tiers,
        "tokenValues": values,
        "totalFeatureWinX": 0.0,
        "totalFeatureWinXRaw": 0.0,
        "totalFeatureWinXCapped": 0.0,
        "paying": False,
    }


def _symbol_board_from_paying(paying: dict, initial_board: list[list[str]]) -> list[list[str]]:
    """Map paying cells back to a string symbol board for finalBoard."""
    working = [col[:] for col in initial_board]
    # Mysteries already replaced in paying["workingBoard"] with token ids / result types.
    return paying["workingBoard"]


def resolve_features(board: list[list[str]], rng, config: dict, *, line_win_x: float = 0.0) -> dict:
    """Mutates a copy of the post-line board. Phase 4B pays collectors; Phase 3 path stays latent."""
    if not has_paying_economy(config):
        return resolve_features_phase3_latent(board, rng, config)

    # Lazy import avoids circular dependency with research economy helpers.
    from skyjump_v2_phase4a_economy import resolve_paying_features

    candidate = live_candidate_from_config(config)
    paying = resolve_paying_features(
        board,
        rng,
        config=config,
        candidate=candidate,
        line_win_x=line_win_x,
    )
    resolves = []
    for row in paying["resolves"]:
        payload = {
            "position": row["position"],
            "resultType": row["resultType"],
            "kind": row.get("kind"),
            "tokenTier": row.get("tokenTier"),
            "tokenId": row.get("tokenId"),
            "tokenName": row.get("tokenName"),
            "tokenValueX": row.get("tokenValueX"),
            "faceValueX": row.get("faceValueX"),
            "effectiveValueX": row.get("effectiveValueX"),
            "thermalMult": row.get("thermalMult"),
            "appliedThermals": list(row.get("appliedThermals") or []),
        }
        resolves.append(payload)

    return {
        "workingBoard": _symbol_board_from_paying(paying, board),
        "coaches": paying["coaches"],
        "transforms": paying["transforms"],
        "resolves": resolves,
        "selectedSymbolIds": paying["selectedSymbolIds"],
        "mysteriesPerCoach": paying["mysteriesPerCoach"],
        "latentTokenValueX": paying["rawFaceSumX"],
        "tokenTiers": [
            int(row["tokenTier"])
            for row in resolves
            if row.get("resultType") == "FLIGHT_TOKEN" and row.get("tokenTier") is not None
        ],
        "tokenValues": [
            float(row["faceValueX"])
            for row in resolves
            if row.get("resultType") == "FLIGHT_TOKEN" and row.get("faceValueX") is not None
        ],
        "totalFeatureWinX": paying["totalFeatureWinXCapped"],
        "totalFeatureWinXRaw": paying["totalFeatureWinXRaw"],
        "totalFeatureWinXCapped": paying["totalFeatureWinXCapped"],
        "totalWinXRaw": paying["totalWinXRaw"],
        "totalWinXCapped": paying["totalWinXCapped"],
        "capHit": paying["capHit"],
        "capDragX": paying["capDragX"],
        "gateEvents": paying["gateEvents"],
        "collections": paying["collections"],
        "tokenFloorTier": paying["tokenFloorTier"],
        "cells": paying["cells"],
        "rawFaceSumX": paying["rawFaceSumX"],
        "effectiveTokenSumX": paying["effectiveTokenSumX"],
        "thermalCount": paying["thermalCount"],
        "gateCount": paying["gateCount"],
        "judgeCount": paying["judgeCount"],
        "headJudgeCount": paying["headJudgeCount"],
        "paying": True,
        "deadCoach": paying.get("deadCoach"),
        "deadReason": paying.get("deadReason"),
        "hasFeatureWin": paying.get("hasFeatureWin"),
    }
