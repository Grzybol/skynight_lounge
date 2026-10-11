"""Phase 7C.2 — conditional BASE stop sampling (true conditional distributions)."""

from __future__ import annotations

import copy
import itertools
import random
from functools import lru_cache

from skyjump_v2_exact import scatter_on_board
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import base_trigger_mix
from skyjump_v2_reels import board_from_stops, visible_window

PV_ROWS = (0, 1, 2, 1, 0)
TIERS = ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")


def wr_off_config(cfg: dict) -> dict:
    out = copy.deepcopy(cfg)
    out["worldRecord"]["byTierPSpin"] = {t: 0.0 for t in TIERS}
    return out


def wr_force_config(cfg: dict) -> dict:
    out = copy.deepcopy(cfg)
    out["worldRecord"]["byTierPSpin"] = {t: 1.0 for t in TIERS}
    return out


def scatter_rows(strip: list[str], stop: int) -> list[int]:
    window = visible_window(strip, stop)
    return [row for row, symbol in enumerate(window) if symbol == "S"]


@lru_cache(maxsize=1)
def _strip_catalog(strips_key: tuple[tuple[str, ...], ...]) -> list[dict[int, list[int]]]:
    tables: list[dict[int, list[int]]] = []
    for strip in strips_key:
        groups: dict[int, list[int]] = {}
        for stop in range(len(strip)):
            count = len(scatter_rows(list(strip), stop))
            groups.setdefault(count, []).append(stop)
        tables.append(groups)
    return tables


def strip_catalog(cfg: dict) -> list[dict[int, list[int]]]:
    strips = cfg["reelModel"]["strips"]
    key = tuple(tuple(s) for s in strips)
    return _strip_catalog(key)


def _composition_weight(catalog: list[dict[int, list[int]]], counts: tuple[int, ...]) -> int:
    w = 1
    for reel, c in enumerate(counts):
        n = len(catalog[reel].get(c, []))
        if n == 0:
            return 0
        w *= n
    return w


def compositions_for_exact_count(catalog: list[dict[int, list[int]]], total: int) -> list[tuple[tuple[int, ...], int]]:
    """All per-reel scatter-count tuples summing to total, with multiplicity weights."""
    max_c = [max(g.keys()) if g else 0 for g in catalog]
    out = []
    ranges = [range(0, max_c[r] + 1) for r in range(5)]
    for counts in itertools.product(*ranges):
        if sum(counts) != total:
            continue
        w = _composition_weight(catalog, counts)
        if w:
            out.append((counts, w))
    return out


def compositions_for_ge(catalog: list[dict[int, list[int]]], minimum: int) -> list[tuple[tuple[int, ...], int]]:
    max_c = [max(g.keys()) if g else 0 for g in catalog]
    out = []
    ranges = [range(0, max_c[r] + 1) for r in range(5)]
    for counts in itertools.product(*ranges):
        if sum(counts) < minimum:
            continue
        w = _composition_weight(catalog, counts)
        if w:
            out.append((counts, w))
    return out


def compositions_for_lt(catalog: list[dict[int, list[int]]], maximum: int) -> list[tuple[tuple[int, ...], int]]:
    max_c = [max(g.keys()) if g else 0 for g in catalog]
    out = []
    ranges = [range(0, max_c[r] + 1) for r in range(5)]
    for counts in itertools.product(*ranges):
        if sum(counts) >= maximum:
            continue
        w = _composition_weight(catalog, counts)
        if w:
            out.append((counts, w))
    return out


def sample_stops_from_composition(
    rng: random.Random, catalog: list[dict[int, list[int]]], counts: tuple[int, ...]
) -> list[int]:
    return [rng.choice(catalog[reel][counts[reel]]) for reel in range(5)]


def sample_weighted_composition(
    rng: random.Random, comps: list[tuple[tuple[int, ...], int]]
) -> tuple[int, ...]:
    total = sum(w for _, w in comps)
    pick = rng.randrange(total)
    running = 0
    for counts, w in comps:
        running += w
        if pick < running:
            return counts
    return comps[-1][0]


def perfect_v_stops_catalog(cfg: dict) -> list[list[int]]:
    """All stop tuples that place S exactly on Perfect V rows (may still need verify)."""
    strips = cfg["reelModel"]["strips"]
    per_reel: list[list[int]] = []
    for reel, strip in enumerate(strips):
        good = []
        for stop in range(len(strip)):
            rows = scatter_rows(strip, stop)
            if rows == [PV_ROWS[reel]]:
                good.append(stop)
        if not good:
            # Fall back: any stop with S on the PV row (may have extra S)
            for stop in range(len(strip)):
                window = visible_window(strip, stop)
                if window[PV_ROWS[reel]] == "S":
                    good.append(stop)
        if not good:
            raise RuntimeError(f"no Perfect V candidate stops on reel {reel}")
        per_reel.append(good)
    # Cartesian product can be large; for Coach E strips usually small.
    # Cap by sampling online rather than materializing if huge.
    sizes = [len(x) for x in per_reel]
    product = 1
    for s in sizes:
        product *= s
    if product <= 200_000:
        return [list(t) for t in itertools.product(*per_reel)]
    # Sparse reservoir of valid PV boards
    rng = random.Random(7)
    found: list[list[int]] = []
    for _ in range(2_000_000):
        stops = [rng.choice(opts) for opts in per_reel]
        board = board_from_stops(strips, stops)
        sc = scatter_on_board(board, "S", PV_ROWS)
        if sc["perfectV"]:
            found.append(stops)
            if len(found) >= 5000:
                break
    if not found:
        raise RuntimeError("failed to catalog Perfect V stops")
    return found


class ConditionalBaseSampler:
    """Sample BASE reel stops from the true conditional distribution of a class."""

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or load_v2_config()
        self.strips = self.cfg["reelModel"]["strips"]
        self.catalog = strip_catalog(self.cfg)
        self.mix = base_trigger_mix(self.cfg)
        self._comps_exact: dict[int, list[tuple[tuple[int, ...], int]]] = {}
        self._comps_lt3 = compositions_for_lt(self.catalog, 3)
        self._comps_ge5 = compositions_for_ge(self.catalog, 5)
        self._pv_stops = perfect_v_stops_catalog(self.cfg)

    def _exact_comps(self, total: int):
        if total not in self._comps_exact:
            self._comps_exact[total] = compositions_for_exact_count(self.catalog, total)
        return self._comps_exact[total]

    def sample_no_trigger(self, rng: random.Random) -> list[int]:
        for _ in range(10000):
            counts = sample_weighted_composition(rng, self._comps_lt3)
            stops = sample_stops_from_composition(rng, self.catalog, counts)
            sc = scatter_on_board(board_from_stops(self.strips, stops), "S", PV_ROWS)
            if sc["count"] < 3:
                return stops
        raise RuntimeError("no_trigger sample failed")

    def sample_large_hill(self, rng: random.Random) -> list[int]:
        comps = self._exact_comps(3)
        for _ in range(10000):
            counts = sample_weighted_composition(rng, comps)
            stops = sample_stops_from_composition(rng, self.catalog, counts)
            sc = scatter_on_board(board_from_stops(self.strips, stops), "S", PV_ROWS)
            if sc["count"] == 3 and not sc["perfectV"]:
                return stops
        raise RuntimeError("LH sample failed")

    def sample_ski_flying(self, rng: random.Random) -> list[int]:
        comps = self._exact_comps(4)
        for _ in range(10000):
            counts = sample_weighted_composition(rng, comps)
            stops = sample_stops_from_composition(rng, self.catalog, counts)
            sc = scatter_on_board(board_from_stops(self.strips, stops), "S", PV_ROWS)
            if sc["count"] == 4 and not sc["perfectV"]:
                return stops
        raise RuntimeError("SF sample failed")

    def sample_world_cup(self, rng: random.Random) -> list[int]:
        for _ in range(20000):
            counts = sample_weighted_composition(rng, self._comps_ge5)
            stops = sample_stops_from_composition(rng, self.catalog, counts)
            sc = scatter_on_board(board_from_stops(self.strips, stops), "S", PV_ROWS)
            if sc["count"] >= 5 and not sc["perfectV"]:
                return stops
        raise RuntimeError("WC sample failed")

    def sample_perfect_v(self, rng: random.Random) -> list[int]:
        for _ in range(10000):
            stops = list(rng.choice(self._pv_stops))
            sc = scatter_on_board(board_from_stops(self.strips, stops), "S", PV_ROWS)
            if sc["perfectV"]:
                return stops
        raise RuntimeError("PV sample failed")

    def sample(self, rng: random.Random, kind: str) -> list[int]:
        if kind in ("NO_TRIGGER", "BASE_NO_TRIGGER"):
            return self.sample_no_trigger(rng)
        if kind in ("LARGE_HILL", "BASE_TRIGGER_LH_WR_OFF", "LH"):
            return self.sample_large_hill(rng)
        if kind in ("SKI_FLYING", "BASE_TRIGGER_SF_WR_OFF", "SF"):
            return self.sample_ski_flying(rng)
        if kind in ("WORLD_CUP", "BASE_TRIGGER_WC_WR_OFF", "WC"):
            return self.sample_world_cup(rng)
        if kind in ("PERFECT_V", "BASE_TRIGGER_PV_WR_OFF", "PV", "WORLD_RECORD"):
            # WR books still need a legal FS path; use LH trigger preferentially for WR mass
            if kind == "WORLD_RECORD":
                return self.sample_large_hill(rng)
            return self.sample_perfect_v(rng)
        raise ValueError(kind)


def exact_start_mix(cfg: dict | None = None) -> dict:
    cfg = cfg or load_v2_config()
    mix = base_trigger_mix(cfg)
    return {
        "LARGE_HILL": float(mix["absolute"]["LARGE_HILL"]),
        "SKI_FLYING": float(mix["absolute"]["SKI_FLYING"]),
        "WORLD_CUP": float(mix["absolute"]["WORLD_CUP"]),
        "PERFECT_V": float(mix["absolute"]["PERFECT_V"]),
        "P_scatterGe3": float(mix["P_scatterGe3"]),
        "conditional": dict(mix["conditional"]),
        "P_no_trigger": 1.0 - float(mix["P_scatterGe3"]),
    }
