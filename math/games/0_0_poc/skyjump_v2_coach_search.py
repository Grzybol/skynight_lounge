"""Search Coach placements on existing Phase 2 strips without remeshing."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_exact import exact_line_rtp, exact_symbol_window_distribution
from skyjump_v2_lines import load_v2_config
from skyjump_v2_reels import COACH_ID


def replace_isolated_low(strip: list[str], count: int = 1) -> list[str]:
    next_strip = list(strip)
    placed = 0
    length = len(next_strip)
    for index, symbol in enumerate(next_strip):
        if symbol != "L3" or placed >= count:
            continue
        prev_s = next_strip[(index - 1) % length]
        next_s = next_strip[(index + 1) % length]
        if prev_s == COACH_ID or next_s == COACH_ID:
            continue
        if prev_s == "L3" and next_s == "L3":
            continue
        next_strip[index] = COACH_ID
        placed += 1
    if placed < count:
        raise ValueError("could not place isolated Coach")
    return next_strip


def summarize(strips, paylines, paytable) -> dict:
    dist = exact_symbol_window_distribution(strips, COACH_ID)
    any_c = 1.0 - dist.get(0, 0.0)
    ge2 = sum(prob for count, prob in dist.items() if count >= 2)
    rtp = exact_line_rtp(strips, paylines, paytable)["lineRtp"]
    return {
        "pAny": any_c,
        "pGe2": ge2,
        "oneInAny": None if any_c <= 0 else 1 / any_c,
        "oneInGe2": None if ge2 <= 0 else 1 / ge2,
        "lineRtp": rtp,
        "dist": {str(key): value for key, value in sorted(dist.items()) if value},
    }


def search() -> list[dict]:
    config = load_v2_config()
    base = [list(strip) for strip in config["reelModel"]["strips"]]
    # If Coach already present, strip it back to L3 for comparison search.
    cleaned = [[("L3" if cell == COACH_ID else cell) for cell in strip] for strip in base]
    paylines = config["paylines"]
    paytable = config["paytable"]["awards"]
    candidates = []
    for reels in ([1, 3], [1, 2], [2, 3], [1, 2, 3], [2], [1, 3, 4]):
        strips = deepcopy(cleaned)
        ok = True
        try:
            for reel in reels:
                strips[reel] = replace_isolated_low(strips[reel], 1)
        except ValueError:
            ok = False
        if not ok:
            continue
        row = summarize(strips, paylines, paytable)
        row["reels"] = [reel + 1 for reel in reels]
        row["coachStops"] = 1
        candidates.append(row)
    candidates.sort(key=lambda row: abs(row["pAny"] - 0.14) + abs(row["pGe2"] - 0.008))
    return candidates


if __name__ == "__main__":
    rows = search()
    print(json.dumps(rows[:6], indent=2))
