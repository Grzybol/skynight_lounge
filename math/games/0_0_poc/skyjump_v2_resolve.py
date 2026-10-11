"""Resolve a SkyJump V2 BASE spin from math-owned reel stops."""

from __future__ import annotations

from skyjump_v2_exact import scatter_on_board
from skyjump_v2_features import resolve_features
from skyjump_v2_lines import evaluate_paylines, load_v2_config
from skyjump_v2_reels import board_from_stops


def v2_math_tables(config: dict | None = None) -> dict:
    config = config or load_v2_config()
    paytable = config["paytable"]["awards"]
    strips = config["reelModel"]["strips"]
    return {
        "config": config,
        "paytable": paytable,
        "strips": strips,
        "paylines": config["paylines"],
        "scatterId": config["symbols"]["scatter"]["id"],
        "regularIds": {row["id"] for row in config["symbols"]["regular"]},
        "perfectVRows": tuple(config["scatterModel"]["perfectVRows"]),
        "coachId": config.get("coachModel", {}).get("id", "C"),
    }


def draw_stops(rng, strips: list[list[str]]) -> list[int]:
    return [rng.randrange(len(strip)) for strip in strips]


def resolve_v2_base(rng=None, *, stops: list[int] | None = None, config: dict | None = None) -> dict:
    tables = v2_math_tables(config)
    strips = tables["strips"]
    if stops is None:
        if rng is None:
            raise ValueError("rng or stops required")
        stops = draw_stops(rng, strips)
    if any(stop < 0 or stop >= len(strips[index]) for index, stop in enumerate(stops)):
        raise ValueError("stop out of range")
    board = board_from_stops(strips, stops)
    evaluated = evaluate_paylines(
        board,
        paylines=tables["paylines"],
        paytable=tables["paytable"],
        scatter_id=tables["scatterId"],
        regular_ids=tables["regularIds"],
    )
    scatter = scatter_on_board(board, tables["scatterId"], tables["perfectVRows"])
    line_win = float(evaluated["lineWinX"])
    if line_win < 0 or any(
        (not isinstance(win["payoutX"], (int, float))) or win["payoutX"] < 0 or win["payoutX"] != win["payoutX"]
        for win in evaluated["wins"]
    ):
        raise ValueError("invalid line payout")
    features = {
        "workingBoard": [col[:] for col in board],
        "coaches": [],
        "transforms": [],
        "resolves": [],
        "selectedSymbolIds": [],
        "mysteriesPerCoach": [],
        "latentTokenValueX": 0.0,
        "tokenTiers": [],
        "tokenValues": [],
        "totalFeatureWinX": 0.0,
        "totalFeatureWinXRaw": 0.0,
        "totalFeatureWinXCapped": 0.0,
        "paying": False,
    }
    if rng is not None and tables["config"].get("coachModel"):
        features = resolve_features(board, rng, tables["config"], line_win_x=line_win)
    feature_win = float(features.get("totalFeatureWinXCapped", features.get("totalFeatureWinX", 0)) or 0)
    total_raw = float(features.get("totalWinXRaw", line_win + float(features.get("totalFeatureWinXRaw", feature_win) or 0)))
    total_capped = float(features.get("totalWinXCapped", line_win + feature_win))
    return {
        "stops": stops,
        "board": board,
        "finalBoard": features["workingBoard"],
        "wins": evaluated["wins"],
        "lineWinX": line_win,
        "totalFeatureWinX": feature_win,
        "totalFeatureWinXRaw": float(features.get("totalFeatureWinXRaw", feature_win) or 0),
        "totalWinX": total_capped,
        "totalWinXRaw": total_raw,
        "scatter": scatter,
        "features": features,
        "mode": "BASE",
        "isFreeSpin": False,
    }
