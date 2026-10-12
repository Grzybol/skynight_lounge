"""SkyJump V2 virtual reel strips. Stops are math-owned; frontend never rolls them."""

from __future__ import annotations

from collections import Counter

REGULAR_IDS = ("P1", "P2", "P3", "M1", "M2", "M3", "L1", "L2", "L3")
SCATTER_ID = "S"
COACH_ID = "C"
MYSTERY_ID = "Y"
HIERARCHY = ("P1", "P2", "P3", "M1", "M2", "M3", "L1", "L2", "L3")
TRACKED_IDS = REGULAR_IDS + (SCATTER_ID, COACH_ID)


def visible_window(strip: list[str], stop: int, rows: int = 5) -> list[str]:
    length = len(strip)
    if length < rows:
        raise ValueError("strip shorter than visible window")
    if not 0 <= stop < length:
        raise ValueError("stop must be in [0, length)")
    return [strip[(stop + row) % length] for row in range(rows)]


def board_from_stops(strips: list[list[str]], stops: list[int], rows: int = 5) -> list[list[str]]:
    if len(strips) != 5 or len(stops) != 5:
        raise ValueError("need 5 strips and 5 stops")
    return [visible_window(strips[reel], stops[reel], rows) for reel in range(5)]


def mix_strip(counts: dict[str, int], rng) -> list[str]:
    remaining = {key: int(value) for key, value in counts.items() if int(value) > 0}
    if sum(remaining.values()) <= 0:
        raise ValueError("empty strip counts")
    strip: list[str] = []
    while remaining:
        candidates = [symbol for symbol, count in remaining.items() if count > 0]
        if len(strip) >= 2 and strip[-1] == strip[-2]:
            blocked = strip[-1]
            filtered = [symbol for symbol in candidates if symbol != blocked]
            if filtered:
                candidates = filtered
        weights = [remaining[symbol] for symbol in candidates]
        pick = rng.choices(candidates, weights=weights, k=1)[0]
        strip.append(pick)
        remaining[pick] -= 1
        if remaining[pick] <= 0:
            del remaining[pick]
    return strip


def longest_run(strip: list[str]) -> int:
    best = current = 1
    for index in range(1, len(strip)):
        if strip[index] == strip[index - 1]:
            current += 1
            best = max(best, current)
        else:
            current = 1
    wrap = 0
    if strip:
        symbol = strip[0]
        left = 0
        while left < len(strip) and strip[left] == symbol:
            left += 1
        right = 0
        while right < len(strip) and strip[-1 - right] == symbol:
            right += 1
        wrap = left + right if strip[0] == strip[-1] else 0
        if wrap > len(strip):
            wrap = len(strip)
    return max(best, wrap)


def symbol_counts(strip: list[str]) -> dict[str, int]:
    return dict(Counter(strip))


def frequency_table(strips: list[list[str]]) -> dict:
    per_reel = []
    combined: Counter[str] = Counter()
    for strip in strips:
        counts = Counter(strip)
        length = len(strip)
        combined.update(counts)
        per_reel.append({symbol: counts[symbol] / length for symbol in TRACKED_IDS})
    total = sum(len(strip) for strip in strips)
    global_freq = {symbol: combined[symbol] / total for symbol in TRACKED_IDS}
    return {"perReel": per_reel, "global": global_freq, "counts": dict(combined), "totalCells": total}


def assert_hierarchy(counts: dict[str, int]) -> None:
    values = [counts.get(symbol, 0) for symbol in HIERARCHY]
    if not values[0] < values[1] < values[2]:
        raise ValueError("premium hierarchy P1 < P2 < P3 required")
    if not values[2] <= values[3] <= values[4] <= values[5]:
        raise ValueError("mid hierarchy P3 <= M1 <= M2 <= M3 required")
    if not values[5] < values[6] <= values[7] <= values[8]:
        raise ValueError("low hierarchy M3 < L1 <= L2 <= L3 required")


def grain_ok(payout_x: float, grain: float = 0.1) -> bool:
    scaled = payout_x / grain
    return abs(scaled - round(scaled)) < 1e-9
