"""Write non-production Phase 4B FEATURE SAMPLE books (DEV fixtures)."""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_events import round_to_v2_events
from skyjump_v2_features import resolve_features
from skyjump_v2_lines import evaluate_paylines, load_v2_config
from skyjump_v2_phase4a_economy import resolve_paying_features
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_reels import COACH_ID, MYSTERY_ID
from skyjump_v2_resolve import resolve_v2_base

OUT = HERE / "skyjump_v2_feature_samples.json"
SEED = 20260921


class ScriptedFeatureRng:
    """Force Coach picks then Mystery result stream, then token/thermal draws."""

    def __init__(
        self,
        picks: list[str],
        results: list[str],
        *,
        token_draws: list[tuple[int, float]] | None = None,
        thermal_mults: list[int] | None = None,
        floor_values: list[float] | None = None,
    ):
        self.picks = list(picks)
        self.results = list(results)
        self.token_draws = list(token_draws or [])
        self.thermal_mults = list(thermal_mults or [])
        self.floor_values = list(floor_values or [])
        self._tier_pending: int | None = None
        self._awaiting_thermal = False

    def choice(self, population):
        if self.picks:
            pick = self.picks.pop(0)
            if pick not in population:
                raise AssertionError(f"{pick} not in {population}")
            return pick
        return population[0]

    def choices(self, population, weights, k=1):
        pop = list(population)
        labels = set(map(str, pop))
        if labels >= {"FLIGHT_TOKEN", "THERMAL_LIFT", "GATE_UPGRADE", "JUDGE", "HEAD_JUDGE"}:
            if not self.results:
                return ["FLIGHT_TOKEN"]
            return [self.results.pop(0)]
        if self._awaiting_thermal or (set(pop) <= {2, 3, 4, 5, 10, 20} and self.thermal_mults):
            self._awaiting_thermal = False
            if self.thermal_mults:
                return [self.thermal_mults.pop(0)]
            return [pop[0]]
        if self._tier_pending is not None:
            _tier, value = self.token_draws.pop(0)
            self._tier_pending = None
            return [value]
        # Floor replacement samples values only (same tier).
        if self.floor_values and len(pop) <= 4 and all(isinstance(x, (int, float)) for x in pop):
            value = self.floor_values.pop(0)
            if value not in pop:
                # snap to nearest legal
                value = min(pop, key=lambda x: abs(float(x) - float(value)))
            return [value]
        if self.token_draws:
            tier, _value = self.token_draws[0]
            self._tier_pending = tier
            return [tier]
        if set(pop) <= {2, 3, 4, 5, 10, 20}:
            self._awaiting_thermal = True
            if self.thermal_mults:
                return [self.thermal_mults.pop(0)]
        return [pop[0]]

    def randrange(self, stop):
        return 0


def _fill(symbol: str) -> list[list[str]]:
    return [[symbol] * 5 for _ in range(5)]


def _paint(board: list[list[str]], cells: list[tuple[int, int, str]]) -> list[list[str]]:
    next_board = [col[:] for col in board]
    for reel, row, symbol in cells:
        next_board[reel][row] = symbol
    return next_board


def _pack(sample_id: str, title: str, result: dict) -> dict:
    events = round_to_v2_events(result, source="math")
    features = result["features"]
    return {
        "id": sample_id,
        "title": title,
        "stops": result.get("stops") or [0, 0, 0, 0, 0],
        "board": result["board"],
        "finalBoard": result["finalBoard"],
        "lineWinX": result["lineWinX"],
        "totalFeatureWinX": float(result["totalFeatureWinX"]),
        "totalFeatureWinXRaw": float(result.get("totalFeatureWinXRaw", result["totalFeatureWinX"])),
        "totalWinX": float(result["totalWinX"]),
        "latentTokenValueX": float(features.get("latentTokenValueX") or features.get("rawFaceSumX") or 0),
        "coachCount": len(features.get("coaches") or []),
        "selectedSymbolIds": list(features.get("selectedSymbolIds") or []),
        "tokenTiers": list(features.get("tokenTiers") or []),
        "capHit": bool(features.get("capHit")),
        "events": events,
    }


def _from_board(
    board: list[list[str]],
    rng,
    *,
    config: dict,
    title: str,
    sample_id: str,
    line_win_override: float | None = None,
) -> dict:
    evaluated = evaluate_paylines(
        board,
        paylines=config["paylines"],
        paytable=config["paytable"]["awards"],
    )
    line_win = float(evaluated["lineWinX"] if line_win_override is None else line_win_override)
    features = resolve_features(board, rng, config, line_win_x=line_win)
    feature_win = float(features.get("totalFeatureWinXCapped", features.get("totalFeatureWinX", 0)) or 0)
    total_raw = float(features.get("totalWinXRaw", line_win + float(features.get("totalFeatureWinXRaw", feature_win) or 0)))
    total_capped = float(features.get("totalWinXCapped", line_win + feature_win))
    result = {
        "stops": [0, 0, 0, 0, 0],
        "board": board,
        "finalBoard": features["workingBoard"],
        "wins": evaluated["wins"] if line_win_override is None else [],
        "lineWinX": line_win,
        "totalFeatureWinX": feature_win,
        "totalFeatureWinXRaw": float(features.get("totalFeatureWinXRaw", feature_win) or 0),
        "totalWinX": total_capped,
        "totalWinXRaw": total_raw,
        "scatter": {
            "positions": [],
            "count": 0,
            "perfectV": False,
            "trigger": None,
            "fromBoard": "initialReveal",
        },
        "features": features,
        "mode": "BASE",
        "isFreeSpin": False,
    }
    return _pack(sample_id, title, result)


def _force_cells_via_mysteries(
    config: dict,
    *,
    sample_id: str,
    title: str,
    results: list[str],
    token_draws: list[tuple[int, float]],
    thermal_mults: list[int] | None = None,
    floor_values: list[float] | None = None,
    coaches: int = 1,
    extras: list[tuple[int, int, str]] | None = None,
) -> dict:
    """Paint Coach + enough L2 cells so one Coach produces len(results) Mysteries."""
    board = _fill("M1")
    paint: list[tuple[int, int, str]] = []
    paint.append((1, 2, COACH_ID))
    if coaches >= 2:
        paint.append((3, 2, COACH_ID))
    # Place N distinct L2 cells for first coach (and more if multi).
    l2_cells = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (4, 0), (4, 1)]
    needed = len(results) if coaches == 1 else max(len(results), 2)
    for cell in l2_cells[:needed]:
        paint.append((*cell, "L2"))
    if extras:
        paint.extend(extras)
    board = _paint(board, paint)
    picks = ["L2"] if coaches == 1 else ["L2", "M1"]
    # For multi-coach, second coach picks M1 (remaining regulars after L2→Mystery).
    rng = ScriptedFeatureRng(
        picks,
        results,
        token_draws=token_draws,
        thermal_mults=thermal_mults,
        floor_values=floor_values,
    )
    return _from_board(board, rng, config=config, title=title, sample_id=sample_id)


def build_samples(config: dict) -> list[dict]:
    samples: list[dict] = []

    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="01",
            title="One Flight Token, no collector",
            results=["FLIGHT_TOKEN"],
            token_draws=[(1, 1)],
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="02",
            title="Multiple tokens, no collector",
            results=["FLIGHT_TOKEN", "FLIGHT_TOKEN", "FLIGHT_TOKEN"],
            token_draws=[(1, 1), (1, 2), (2, 5)],
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="03",
            title="Judge with tokens",
            results=["FLIGHT_TOKEN", "FLIGHT_TOKEN", "JUDGE"],
            token_draws=[(1, 1), (1, 2)],
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="04",
            title="Judge with no token",
            results=["JUDGE"],
            token_draws=[],
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="05",
            title="Head Judge with tokens",
            results=["FLIGHT_TOKEN", "HEAD_JUDGE"],
            token_draws=[(2, 5)],
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="06",
            title="Multiple Judges",
            results=["FLIGHT_TOKEN", "JUDGE", "JUDGE"],
            token_draws=[(1, 4)],
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="07",
            title="Judge + Head Judge",
            results=["FLIGHT_TOKEN", "JUDGE", "HEAD_JUDGE"],
            token_draws=[(1, 2)],
        )
    )
    # Thermal beside tokens: place mysteries such that thermal at (0,1) neighbours tokens.
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="08",
            title="Thermal affecting one token",
            results=["FLIGHT_TOKEN", "THERMAL_LIFT"],
            token_draws=[(1, 1)],
            thermal_mults=[3],
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="09",
            title="Thermal affecting multiple tokens",
            results=["FLIGHT_TOKEN", "FLIGHT_TOKEN", "FLIGHT_TOKEN", "THERMAL_LIFT"],
            token_draws=[(1, 1), (1, 1), (1, 1)],
            thermal_mults=[2],
        )
    )
    # Token at (2,2) with Thermals on both sides (Moore neighbours).
    samples.append(
        _from_board(
            _paint(
                _fill("M1"),
                [(1, 2, COACH_ID), (2, 1, "L2"), (2, 2, "L2"), (2, 3, "L2")],
            ),
            ScriptedFeatureRng(
                ["L2"],
                ["THERMAL_LIFT", "FLIGHT_TOKEN", "THERMAL_LIFT"],
                token_draws=[(1, 2)],
                thermal_mults=[2, 3],
            ),
            config=config,
            title="Token affected by two Thermals",
            sample_id="10",
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="11",
            title="Gate T1 -> T2 replacement",
            results=["FLIGHT_TOKEN", "GATE_UPGRADE"],
            token_draws=[(1, 1)],
            floor_values=[5],
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="12",
            title="Two Gates reaching T3",
            results=["FLIGHT_TOKEN", "GATE_UPGRADE", "GATE_UPGRADE"],
            token_draws=[(1, 1)],
            floor_values=[5, 25],
        )
    )
    # Token + adjacent Thermal + Gate + Judge (Gate after Thermal still upgrades face).
    samples.append(
        _from_board(
            _paint(
                _fill("M1"),
                [
                    (1, 2, COACH_ID),
                    (0, 0, "L2"),
                    (0, 1, "L2"),
                    (0, 2, "L2"),
                    (1, 0, "L2"),
                ],
            ),
            ScriptedFeatureRng(
                ["L2"],
                ["FLIGHT_TOKEN", "THERMAL_LIFT", "GATE_UPGRADE", "JUDGE"],
                token_draws=[(1, 1)],
                thermal_mults=[2],
                floor_values=[5],
            ),
            config=config,
            title="Gate + Thermal + Judge",
            sample_id="13",
        )
    )
    # Multi-Coach: first Coach → one token; second Coach → Judge.
    samples.append(
        _from_board(
            _paint(
                _fill("M1"),
                [(1, 0, COACH_ID), (3, 4, COACH_ID), (0, 0, "L2"), (2, 0, "P2")],
            ),
            ScriptedFeatureRng(
                ["L2", "P2"],
                ["FLIGHT_TOKEN", "JUDGE"],
                token_draws=[(1, 4)],
            ),
            config=config,
            title="Multi-Coach + collector",
            sample_id="14",
        )
    )
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="15",
            title="Rare T4/T5 token collection",
            results=["FLIGHT_TOKEN", "JUDGE"],
            token_draws=[(5, 1000)],
        )
    )
    # Synthetic T6 + Head Judge can hit huge raw; also cap sample.
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="16",
            title="Synthetic T6 / 50,000x tail test",
            results=["FLIGHT_TOKEN", "HEAD_JUDGE"],
            token_draws=[(6, 50_000)],
        )
    )
    # Cap: Head Judge twice on 50k face with line win forces raw > cap.
    samples.append(
        _force_cells_via_mysteries(
            config,
            sample_id="17",
            title="Cap reached",
            results=["FLIGHT_TOKEN", "FLIGHT_TOKEN", "HEAD_JUDGE"],
            token_draws=[(6, 50_000), (6, 25_000)],
        )
    )

    # Verify sample 17 actually caps; if not, force line_win and rebuild.
    if not samples[-1]["capHit"] and samples[-1]["totalFeatureWinXRaw"] <= 50_000:
        # Rebuild 17 with explicit line win so total raw exceeds cap.
        board = _fill("M1")
        board = _paint(
            board,
            [
                (1, 2, COACH_ID),
                (0, 0, "L2"),
                (0, 1, "L2"),
                (0, 2, "L2"),
            ],
        )
        rng = ScriptedFeatureRng(
            ["L2"],
            ["FLIGHT_TOKEN", "FLIGHT_TOKEN", "HEAD_JUDGE"],
            token_draws=[(6, 50_000), (6, 25_000)],
        )
        packed = _from_board(
            board,
            rng,
            config=config,
            title="Cap reached",
            sample_id="17",
            line_win_override=100.0,
        )
        samples[-1] = packed

    return samples


def main() -> None:
    config = load_v2_config()
    samples = build_samples(config)
    # Sanity: 01 feature win 0; 03 > 0; 17 capped.
    assert samples[0]["totalFeatureWinX"] == 0
    assert samples[2]["totalFeatureWinX"] > 0
    assert samples[4]["totalFeatureWinX"] > 0
    payload = {
        "nonProduction": True,
        "usage": "DEV/TEST feature-sample replay only. Not production books or LUT.",
        "mathStatus": "PHASE 4B PROVISIONAL PAYING FEATURE MATH",
        "candidateOrigin": "F01_E_feel",
        "seed": SEED,
        "samples": samples,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} n={len(samples)}")
    for sample in samples:
        print(
            sample["id"],
            sample["title"],
            "feat",
            sample["totalFeatureWinX"],
            "raw",
            sample["totalFeatureWinXRaw"],
            "cap",
            sample["capHit"],
            "tiers",
            sample["tokenTiers"],
        )


if __name__ == "__main__":
    main()
