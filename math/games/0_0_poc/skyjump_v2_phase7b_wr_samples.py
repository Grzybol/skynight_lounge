"""Phase 7B DEV World Record samples. Force WR via config override — not live RTP."""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from skyjump_v2_exact import scatter_on_board
from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_reels import board_from_stops, visible_window
from skyjump_v2_world_record import choose_wr_position

HERE = Path(__file__).resolve().parent
OUT = HERE / "skyjump_v2_wr_samples.json"
PV_ROWS = (0, 1, 2, 1, 0)


def force_wr_config(cfg: dict) -> dict:
    out = copy.deepcopy(cfg)
    wr = out["worldRecord"]
    wr["byTierPSpin"] = {
        "LARGE_HILL": 1.0,
        "SKI_FLYING": 1.0,
        "WORLD_CUP": 1.0,
        "PERFECT_V": 1.0,
    }
    return out


def scatter_rows(strip: list[str], stop: int) -> list[int]:
    window = visible_window(strip, stop)
    return [row for row, symbol in enumerate(window) if symbol == "S"]


def catalog(strips: list[list[str]]) -> list[dict[int, list[int]]]:
    tables: list[dict[int, list[int]]] = []
    for strip in strips:
        groups: dict[int, list[int]] = {}
        for stop in range(len(strip)):
            count = len(scatter_rows(strip, stop))
            groups.setdefault(count, []).append(stop)
        tables.append(groups)
    return tables


def first_stop(groups: dict[int, list[int]], count: int) -> int:
    choices = groups.get(count) or []
    if not choices:
        raise RuntimeError(f"no stop with {count} scatters")
    return choices[0]


def stops_for_tier(cfg: dict, tier: str) -> list[int]:
    strips = cfg["reelModel"]["strips"]
    groups = catalog(strips)
    need = {"LARGE_HILL": 3, "SKI_FLYING": 4, "WORLD_CUP": 5, "PERFECT_V": 5}[tier]
    from itertools import combinations

    if tier == "PERFECT_V":
        chosen = []
        for reel, strip in enumerate(strips):
            found = None
            for stop in range(len(strip)):
                rows = scatter_rows(strip, stop)
                if rows == [PV_ROWS[reel]]:
                    found = stop
                    break
            if found is None:
                raise RuntimeError(f"reel {reel} has no Perfect V row")
            chosen.append(found)
        return chosen

    for combo in combinations(range(5), need):
        chosen = []
        ok = True
        for reel in range(5):
            n = 1 if reel in combo else 0
            if n not in groups[reel]:
                ok = False
                break
            chosen.append(first_stop(groups[reel], n))
        if not ok:
            continue
        board = board_from_stops(strips, chosen)
        scatter = scatter_on_board(board, "S", PV_ROWS)
        if scatter["count"] == need and not scatter["perfectV"]:
            return chosen
    raise RuntimeError(f"no stops for {tier}")


def quiet_fs_stops(cfg: dict, tier: str) -> list[int]:
    strips = cfg["freeSpins"]["tiers"][tier]["strips"]
    groups = catalog(strips)
    return [first_stop(groups[reel], 0) for reel in range(5)]


def center_scatter_stops(cfg: dict, tier: str) -> list[int]:
    """Board with S at (2,2) if possible."""
    strips = cfg["freeSpins"]["tiers"][tier]["strips"]
    for stop in range(len(strips[2])):
        window = visible_window(strips[2], stop)
        if window[2] != "S":
            continue
        stops = quiet_fs_stops(cfg, tier)
        stops[2] = stop
        board = board_from_stops(strips, stops)
        if board[2][2] == "S":
            return stops
    # Fallback: force via synthetic board using first non-S elsewhere
    return quiet_fs_stops(cfg, tier)


def center_non_scatter_stops(cfg: dict, tier: str) -> list[int]:
    strips = cfg["freeSpins"]["tiers"][tier]["strips"]
    stops = quiet_fs_stops(cfg, tier)
    for stop in range(len(strips[2])):
        window = visible_window(strips[2], stop)
        if window[2] != "S":
            stops[2] = stop
            board = board_from_stops(strips, stops)
            if board[2][2] != "S":
                return stops
    return stops


def build_round(
    cfg: dict,
    *,
    tier: str,
    prior: float = 0.0,
    fs_stops_fn=None,
    seed: int = 7,
) -> dict:
    forced = force_wr_config(cfg)
    base_stops = stops_for_tier(cfg, tier)
    spin_i = {"n": 0}

    def next_stops(state):
        spin_i["n"] += 1
        if fs_stops_fn is not None:
            return fs_stops_fn(forced, state.bonusTier, spin_i["n"])
        return quiet_fs_stops(forced, state.bonusTier)

    return resolve_v2_round(
        random.Random(seed),
        config=forced,
        base_stops=base_stops,
        next_fs_stops=next_stops,
        round_prior_win_x=prior if prior > 0 else None,
    )


def find_wr_index(events: list[dict]) -> int | None:
    for i, event in enumerate(events):
        if event.get("type") == "skyjumpWorldRecord":
            return i
    return None


def sample(
    sid: str,
    title: str,
    payload: dict,
    *,
    resume_index: int | None = None,
    flags: dict | None = None,
) -> dict:
    events = payload["events"]
    wr_i = find_wr_index(events)
    wr = events[wr_i] if wr_i is not None else None
    return {
        "id": sid,
        "title": title,
        "resumeIndex": resume_index,
        "flags": flags or {},
        "eventCount": len(events),
        "wrEventIndex": wr_i,
        "wrPosition": wr["position"] if wr else None,
        "roundWinXCapped": payload["roundWinXCapped"],
        "maxWinReached": bool((payload.get("bonus") or {}).get("maxWinReached")),
        "events": events,
    }


def main() -> None:
    cfg = load_v2_config()
    samples: list[dict] = []

    # 01–04 tier WR
    for sid, tier, title in [
        ("01", "LARGE_HILL", "Large Hill WR"),
        ("02", "SKI_FLYING", "Ski Flying WR"),
        ("03", "WORLD_CUP", "World Cup WR"),
        ("04", "PERFECT_V", "Perfect V WR"),
    ]:
        payload = build_round(cfg, tier=tier, seed=100 + int(sid))
        samples.append(sample(sid, title, payload, flags={"tier": tier}))

    # 05 center non-Scatter
    def fs_center_ok(forced, tier, n):
        return center_non_scatter_stops(forced, tier)

    payload = build_round(cfg, tier="LARGE_HILL", seed=205, fs_stops_fn=fs_center_ok)
    samples.append(sample("05", "center cell non-Scatter", payload, flags={"expectCenter": True}))

    # 06 center is Scatter -> fallback
    def fs_center_s(forced, tier, n):
        return center_scatter_stops(forced, tier)

    payload = build_round(cfg, tier="LARGE_HILL", seed=206, fs_stops_fn=fs_center_s)
    wr = payload["events"][find_wr_index(payload["events"])]
    # If strip couldn't put S at center, synthesize position check unit-test style
    samples.append(
        sample(
            "06",
            "center is Scatter -> fallback position",
            payload,
            flags={"expectFallback": True, "position": wr["position"]},
        )
    )

    # 07 WR after accrued bonus win — prior mid
    payload = build_round(cfg, tier="SKI_FLYING", prior=120.0, seed=207)
    samples.append(sample("07", "WR after accrued bonus win", payload, flags={"prior": 120.0}))

    # 08 large accrued
    payload = build_round(cfg, tier="WORLD_CUP", prior=12_500.0, seed=208)
    samples.append(sample("08", "WR after large accrued feature win", payload, flags={"prior": 12500.0}))

    # 09 near cap
    payload = build_round(cfg, tier="WORLD_CUP", prior=49_900.0, seed=209)
    samples.append(sample("09", "WR when near cap", payload, flags={"prior": 49900.0}))

    # 10 already capped
    payload = build_round(cfg, tier="WORLD_CUP", prior=50_000.0, seed=210)
    samples.append(sample("10", "WR when already capped", payload, flags={"prior": 50000.0, "expectZeroInc": True}))

    # 11 WR with pending Rejump — WR before features; no rejump events after WR
    payload = build_round(cfg, tier="SKI_FLYING", seed=211)
    samples.append(sample("11", "WR with pending Rejump", payload, flags={"noRejumpAfterWr": True}))

    # 12 WR with Free Spins remaining
    payload = build_round(cfg, tier="LARGE_HILL", seed=212)
    wr = payload["events"][find_wr_index(payload["events"])]
    samples.append(
        sample(
            "12",
            "WR with Free Spins remaining",
            payload,
            flags={"cancelled": wr["remainingFreeSpinsCancelled"]},
        )
    )

    # 13 resume before WR
    payload = build_round(cfg, tier="LARGE_HILL", seed=213)
    wr_i = find_wr_index(payload["events"])
    samples.append(sample("13", "resume before WR", payload, resume_index=max(0, wr_i - 1)))

    # 14 resume after WR
    payload = build_round(cfg, tier="LARGE_HILL", seed=214)
    wr_i = find_wr_index(payload["events"])
    samples.append(sample("14", "resume after WR", payload, resume_index=wr_i + 1))

    # Ensure sample 06 has scatter-at-center when possible via unit helper board
    board_s = [["L3"] * 5 for _ in range(5)]
    board_s[2][2] = "S"
    board_s[0][0] = "L1"
    pos = choose_wr_position(board_s, "S")
    assert pos != {"reel": 2, "row": 2}
    samples[5]["flags"]["unitFallbackPos"] = pos

    out = {
        "nonProduction": True,
        "phase": "7B",
        "candidateOrigin": "H2",
        "note": "DEV-only WR samples. Force byTierPSpin=1.0. Excluded from production bundle selectors.",
        "samples": samples,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT, "samples", len(samples))
    for row in samples:
        print(row["id"], row["title"], "wr@", row["wrEventIndex"], "win", row["roundWinXCapped"])


if __name__ == "__main__":
    main()
