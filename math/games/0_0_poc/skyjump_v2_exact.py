"""Exact BASE line RTP and scatter-window analytics for independent V2 strips."""

from __future__ import annotations

from collections import Counter

from skyjump_v2_reels import COACH_ID, REGULAR_IDS, SCATTER_ID, board_from_stops, visible_window


def cell_prob(strip: list[str], symbol: str) -> float:
    return strip.count(symbol) / len(strip)


def exact_match_prob(probs: list[float], match_count: int) -> float:
    product = 1.0
    for reel in range(match_count):
        product *= probs[reel]
    if match_count < 5:
        product *= 1.0 - probs[match_count]
    return product


def exact_line_rtp(strips: list[list[str]], paylines: dict, paytable: dict) -> dict:
    reel_probs = {
        symbol: [cell_prob(strip, symbol) for strip in strips] for symbol in REGULAR_IDS
    }
    by_symbol = {symbol: {"3": 0.0, "4": 0.0, "5": 0.0, "rtp": 0.0} for symbol in REGULAR_IDS}
    total = 0.0
    for rows in paylines.values():
        if len(rows) != 5:
            raise ValueError("payline must have 5 rows")
        for symbol in REGULAR_IDS:
            awards = paytable.get(symbol, {})
            probs = reel_probs[symbol]
            for match in (3, 4, 5):
                payout = float(awards.get(str(match), 0) or 0)
                if payout <= 0:
                    continue
                contrib = exact_match_prob(probs, match) * payout
                by_symbol[symbol][str(match)] += contrib
                by_symbol[symbol]["rtp"] += contrib
                total += contrib
    return {"lineRtp": total, "bySymbol": by_symbol}


def window_scatter_distribution(strip: list[str], scatter_id: str = SCATTER_ID, rows: int = 5) -> dict[int, float]:
    length = len(strip)
    counts: Counter[int] = Counter()
    for stop in range(length):
        window = visible_window(strip, stop, rows)
        counts[window.count(scatter_id)] += 1
    return {key: counts[key] / length for key in range(rows + 1)}


def convolve(left: dict[int, float], right: dict[int, float]) -> dict[int, float]:
    out: dict[int, float] = {}
    for a, pa in left.items():
        for b, pb in right.items():
            out[a + b] = out.get(a + b, 0.0) + pa * pb
    return out


def exact_scatter_distribution(strips: list[list[str]], scatter_id: str = SCATTER_ID) -> dict[int, float]:
    dist = {0: 1.0}
    for strip in strips:
        dist = convolve(dist, window_scatter_distribution(strip, scatter_id))
    return dist


def exact_perfect_v_prob(strips: list[list[str]], rows=(0, 1, 2, 1, 0), scatter_id: str = SCATTER_ID) -> float:
    product = 1.0
    for strip, _row in zip(strips, rows, strict=True):
        product *= cell_prob(strip, scatter_id)
    return product


def exact_symbol_window_distribution(strips: list[list[str]], symbol_id: str) -> dict[int, float]:
    dist = {0: 1.0}
    for strip in strips:
        dist = convolve(dist, window_scatter_distribution(strip, symbol_id))
    return dist


def scatter_on_board(board: list[list[str]], scatter_id: str = SCATTER_ID, pattern=(0, 1, 2, 1, 0)) -> dict:
    positions = []
    for reel, col in enumerate(board):
        for row, symbol in enumerate(col):
            if symbol == scatter_id:
                positions.append({"reel": reel, "row": row})
    perfect = all(board[reel][pattern[reel]] == scatter_id for reel in range(5))
    return {
        "positions": positions,
        "count": len(positions),
        "perfectV": perfect,
        "trigger": None,
        "fromBoard": "initialReveal",
    }
