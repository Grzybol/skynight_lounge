"""SkyJump V2 payline evaluator. No wilds. Scatter never pays on lines."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANONICAL_V2 = HERE / "skyjump_v2_config.json"
DEV_PAYTABLE = HERE / "skyjump_v2_dev_paytable.json"


def load_v2_config() -> dict:
    return json.loads(CANONICAL_V2.read_text(encoding="utf-8"))


def load_dev_paytable() -> dict:
    data = json.loads(DEV_PAYTABLE.read_text(encoding="utf-8"))
    if data.get("nonProduction") is not True:
        raise ValueError("skyjump_v2_dev_paytable.json must be marked nonProduction")
    return data


def evaluate_paylines(
    board: list[list[str]],
    *,
    paylines: dict | None = None,
    paytable: dict | None = None,
    scatter_id: str | None = None,
    regular_ids: set[str] | None = None,
    allow_dev_paytable: bool = False,
) -> dict:
    """board[reel][row]. Returns wins + lineWinX. Does not mutate the board.

    The DEV/TEST paytable is never used unless allow_dev_paytable=True.
    Production math must pass an explicit paytable.
    """
    config = load_v2_config() if paylines is None or scatter_id is None or regular_ids is None else None
    if paylines is None:
        paylines = config["paylines"]
    if scatter_id is None:
        scatter_id = config["symbols"]["scatter"]["id"]
    if regular_ids is None:
        regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    if paytable is None:
        if not allow_dev_paytable:
            raise ValueError("paytable required; pass allow_dev_paytable=True for fixtures/tests only")
        paytable = load_dev_paytable()["paytable"]

    reels = len(board)
    if reels != 5 or any(len(col) != 5 for col in board):
        raise ValueError("board must be 5 reels × 5 rows")

    wins = []
    total = 0.0
    for raw_id, rows in paylines.items():
        line_id = int(raw_id)
        first = board[0][rows[0]]
        if first == scatter_id or first not in regular_ids:
            continue
        match_count = 1
        positions = [{"reel": 0, "row": rows[0]}]
        for reel in range(1, reels):
            cell = board[reel][rows[reel]]
            if cell != first:
                break
            match_count += 1
            positions.append({"reel": reel, "row": rows[reel]})
        if match_count < 3:
            continue
        payout = float(paytable.get(first, {}).get(str(match_count), 0))
        if payout <= 0:
            continue
        wins.append(
            {
                "paylineId": line_id,
                "symbolId": first,
                "matchCount": match_count,
                "positions": positions,
                "payoutX": payout,
            }
        )
        total += payout

    wins.sort(key=lambda row: row["paylineId"])
    return {"wins": wins, "lineWinX": total}


def line_win_summary(
    board: list[list[str]],
    *,
    paylines: dict,
    paytable: dict,
    scatter_id: str,
    regular_ids: set[str],
) -> tuple[float, int]:
    """Fast path for simulation: total lineWinX and number of winning paylines."""
    total = 0.0
    hits = 0
    for rows in paylines.values():
        first = board[0][rows[0]]
        if first == scatter_id or first not in regular_ids:
            continue
        match_count = 1
        for reel in range(1, 5):
            if board[reel][rows[reel]] != first:
                break
            match_count += 1
        if match_count < 3:
            continue
        payout = float(paytable.get(first, {}).get(str(match_count), 0) or 0)
        if payout <= 0:
            continue
        total += payout
        hits += 1
    return total, hits
