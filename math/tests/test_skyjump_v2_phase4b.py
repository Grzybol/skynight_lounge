"""SkyJump V2 Phase 4B: F01 paying feature economy on live config."""

from __future__ import annotations

import json
import math
import random
import sys
from copy import deepcopy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
MATH = HERE.parents[1]
REPO = HERE.parents[2]
GAME_DIR = MATH / "games" / "0_0_poc"

for path in (str(GAME_DIR), str(MATH)):
    if path not in sys.path:
        sys.path.insert(0, path)

from skyjump_v2_events import round_to_v2_events
from skyjump_v2_exact import exact_line_rtp, exact_perfect_v_prob, exact_scatter_distribution, exact_symbol_window_distribution
from skyjump_v2_features import resolve_features
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import has_paying_economy, live_candidate_from_config
from skyjump_v2_phase4a_economy import neighbours, resolve_paying_features
from skyjump_v2_reels import COACH_ID, MYSTERY_ID
from skyjump_v2_reducer import board_symbol_grid, reduce_events
from skyjump_v2_resolve import resolve_v2_base
from skyjump_v2_tokens import assert_token_tables, token_tables

CANDIDATE_PATH = GAME_DIR / "phase4a2_research" / "candidate_F01_E_feel.json"


def _config() -> dict:
    return load_v2_config()


def _latent_config() -> dict:
    config = deepcopy(_config())
    config["flightTokens"]["doNotAutoPay"] = True
    return config


def _fill(symbol: str) -> list[list[str]]:
    return [[symbol] * 5 for _ in range(5)]


def _paint(board: list[list[str]], cells: list[tuple[int, int, str]]) -> list[list[str]]:
    next_board = [col[:] for col in board]
    for reel, row, symbol in cells:
        next_board[reel][row] = symbol
    return next_board


class StreamRng:
    def __init__(
        self,
        results: list[str],
        *,
        picks: list[str] | None = None,
        token_draws: list[tuple[int, float]] | None = None,
        thermal_mults: list[int] | None = None,
        floor_values: list[float] | None = None,
    ):
        self.results = list(results)
        self.picks = list(picks or [])
        self.token_draws = list(token_draws or [])
        self.thermal_mults = list(thermal_mults or [])
        self.floor_values = list(floor_values or [])
        self._tier_pending: int | None = None

    def choice(self, population):
        if self.picks:
            pick = self.picks.pop(0)
            assert pick in population
            return pick
        return population[0]

    def choices(self, population, weights, k=1):
        pop = list(population)
        labels = set(map(str, pop))
        if labels >= {"FLIGHT_TOKEN", "THERMAL_LIFT", "GATE_UPGRADE", "JUDGE", "HEAD_JUDGE"}:
            return [self.results.pop(0)]
        if set(pop) <= {2, 3, 4, 5, 10, 20} and self.thermal_mults:
            return [self.thermal_mults.pop(0)]
        if self._tier_pending is not None:
            _tier, value = self.token_draws.pop(0)
            self._tier_pending = None
            return [value]
        # Floor replacements sample within-tier values only (never the 1..6 tier list).
        if (
            self.floor_values
            and all(isinstance(x, (int, float)) for x in pop)
            and list(pop) != [1, 2, 3, 4, 5, 6]
            and not (set(pop) <= {2, 3, 4, 5, 10, 20} and len(pop) == 6)
        ):
            value = self.floor_values.pop(0)
            if value not in pop:
                value = min(pop, key=lambda x: abs(float(x) - float(value)))
            return [value]
        if self.token_draws:
            tier, _value = self.token_draws[0]
            self._tier_pending = tier
            return [tier]
        return [pop[0]]


def test_f01_config_parity():
    config = _config()
    artifact = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    economy = config["featureEconomy"]
    assert economy["featureEconomyVersion"] == 2
    assert economy["candidateOrigin"] == "F01_E_feel"
    assert economy["gateMaxFloor"] == artifact["gateMaxFloor"] == 3
    assert economy["mysteryResultWeights"] == artifact["mysteryResultWeights"]
    assert economy["thermalWeights"] == artifact["thermalWeights"]
    assert economy["conditionalCollectors"] is False
    assert config["meta"]["lineage"] == "skyjump-v2"
    assert config["meta"]["mathVersion"] == 2
    assert config["flightTokens"]["doNotAutoPay"] is False
    assert has_paying_economy(config) is True
    tables = token_tables(config)
    assert_token_tables(tables)
    # BODY1 retuned token tier masses vs historical F01 artifact — pin live T1/T6 only.
    assert tables["tierWeights"][0] == 999360
    assert tables["tierWeights"][5] == int(artifact["tokenTierWeights"]["6"])
    for tier in range(1, 7):
        assert len(tables["values"][tier]) == len(tables["valueWeights"][tier])
        assert sum(int(w) for w in tables["valueWeights"][tier]) > 0
    live = live_candidate_from_config(config)
    assert live["mysteryResultWeights"] == artifact["mysteryResultWeights"]
    assert config["flightTokens"]["phase3LatentResearch"]["archived"] is True


def test_coach_e_reel_construction():
    config = _config()
    strips = config["reelModel"]["strips"]
    assert config["coachModel"]["modelId"] == "E"
    assert config["coachModel"]["reels"] == [2, 4]
    assert [len(strip) for strip in strips] == [52, 120, 52, 120, 52]
    assert [strip.count(COACH_ID) for strip in strips] == [0, 1, 0, 1, 0]
    dist = exact_symbol_window_distribution(strips, COACH_ID)
    p_any = 1.0 - dist.get(0, 0.0)
    p_ge2 = sum(p for n, p in dist.items() if n >= 2)
    assert p_any == pytest.approx(0.0815972222222221, rel=0, abs=1e-12)
    assert p_ge2 == pytest.approx(0.001736111111111111, rel=0, abs=1e-12)


def test_exact_mystery_and_token_weights():
    config = _config()
    artifact = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    assert config["featureEconomy"]["mysteryResultWeights"] == {
        "FLIGHT_TOKEN": 855,
        "THERMAL_LIFT": 42,
        "GATE_UPGRADE": 3,
        "JUDGE": 85,
        "HEAD_JUDGE": 15,
    }
    assert sum(config["featureEconomy"]["mysteryResultWeights"].values()) == 1000
    assert config["flightTokens"]["tiers"]["1"]["weight"] == 999360
    assert artifact["tokenTierWeights"]["6"] == 8


def test_gate_sequential_and_max_floor():
    config = _config()
    candidate = live_candidate_from_config(config)
    board = _paint(
        _fill("L2"),
        [(0, 0, MYSTERY_ID), (0, 1, MYSTERY_ID), (0, 2, MYSTERY_ID)],
    )
    result = resolve_paying_features(
        board,
        StreamRng(
            ["FLIGHT_TOKEN", "GATE_UPGRADE", "GATE_UPGRADE"],
            token_draws=[(1, 1)],
            floor_values=[5, 25],
        ),
        config=config,
        candidate=candidate,
    )
    assert result["tokenFloorTier"] == 3
    assert len(result["gateEvents"]) == 2
    assert result["gateEvents"][0]["floorBefore"] == 1
    assert result["gateEvents"][0]["floorAfter"] == 2
    assert result["gateEvents"][1]["floorAfter"] == 3
    token = next(c for col in result["cells"] for c in col if c["kind"] == "token")
    assert token["tokenTier"] == 3
    assert token["faceValueX"] == 25
    # Third gate would not raise above max.
    board2 = _paint(
        _fill("L2"),
        [(0, 0, MYSTERY_ID), (0, 1, MYSTERY_ID), (0, 2, MYSTERY_ID), (0, 3, MYSTERY_ID)],
    )
    result2 = resolve_paying_features(
        board2,
        StreamRng(
            ["FLIGHT_TOKEN", "GATE_UPGRADE", "GATE_UPGRADE", "GATE_UPGRADE"],
            token_draws=[(1, 1)],
            floor_values=[5, 25],
        ),
        config=config,
        candidate=candidate,
    )
    assert result2["tokenFloorTier"] == 3


def test_gate_replacements_are_math_owned_and_faces_immutable_under_thermal():
    config = _config()
    candidate = live_candidate_from_config(config)
    board = _paint(
        _fill("L2"),
        [(2, 1, MYSTERY_ID), (2, 2, MYSTERY_ID), (2, 3, MYSTERY_ID)],
    )
    result = resolve_paying_features(
        board,
        StreamRng(
            ["THERMAL_LIFT", "FLIGHT_TOKEN", "THERMAL_LIFT"],
            token_draws=[(1, 2)],
            thermal_mults=[2, 3],
        ),
        config=config,
        candidate=candidate,
    )
    token = result["cells"][2][2]
    assert token["faceValueX"] == 2
    assert token["effectiveValueX"] == 12
    assert token["appliedThermals"] == [2, 3]
    assert token["tokenValueX"] == 2


def test_thermal_adjacency_excludes_self():
    assert (2, 2) not in neighbours(2, 2)
    assert len(neighbours(2, 2)) == 8
    assert neighbours(0, 0) == [(0, 1), (1, 0), (1, 1)]


def test_judge_sum_no_consume_multiple_and_head_two_passes():
    config = _config()
    candidate = live_candidate_from_config(config)
    board = _paint(
        _fill("L2"),
        [
            (0, 0, MYSTERY_ID),
            (0, 1, MYSTERY_ID),
            (1, 0, MYSTERY_ID),
            (1, 1, MYSTERY_ID),
        ],
    )
    result = resolve_paying_features(
        board,
        StreamRng(
            ["FLIGHT_TOKEN", "JUDGE", "JUDGE", "HEAD_JUDGE"],
            token_draws=[(1, 4)],
        ),
        config=config,
        candidate=candidate,
    )
    assert result["effectiveTokenSumX"] == 4
    assert result["collectorPasses"] == 4
    assert result["totalFeatureWinXRaw"] == pytest.approx(16)
    assert len([c for c in result["collections"] if c["type"] == "HEAD_JUDGE"]) == 2
    assert [c["pass"] for c in result["collections"] if c["type"] == "HEAD_JUDGE"] == [1, 2]
    # Tokens remain after collection.
    assert sum(1 for col in result["cells"] for c in col if c["kind"] == "token") == 1
    empty = resolve_paying_features(
        _paint(_fill("L2"), [(0, 0, MYSTERY_ID)]),
        StreamRng(["JUDGE"]),
        config=config,
        candidate=candidate,
    )
    assert empty["totalFeatureWinXRaw"] == 0
    empty_h = resolve_paying_features(
        _paint(_fill("L2"), [(0, 0, MYSTERY_ID)]),
        StreamRng(["HEAD_JUDGE"]),
        config=config,
        candidate=candidate,
    )
    assert empty_h["collectorPasses"] == 2
    assert empty_h["totalFeatureWinXRaw"] == 0


def test_cap_enforcement_and_raw_can_exceed():
    config = _config()
    candidate = live_candidate_from_config(config)
    board = _paint(_fill("L2"), [(0, 0, MYSTERY_ID), (0, 1, MYSTERY_ID)])
    result = resolve_paying_features(
        board,
        StreamRng(["FLIGHT_TOKEN", "HEAD_JUDGE"], token_draws=[(6, 50_000)]),
        config=config,
        candidate=candidate,
        line_win_x=10.0,
    )
    assert result["totalFeatureWinXRaw"] == 100_000
    assert result["totalWinXRaw"] == 100_010
    assert result["totalWinXCapped"] == 50_000
    assert result["capHit"] is True
    assert result["capDragX"] == pytest.approx(50_010)


def test_reducer_parity_and_replay():
    config = _config()
    rng = random.Random(20260921)
    for _ in range(40):
        result = resolve_v2_base(rng, config=config)
        events = round_to_v2_events(result)
        state = reduce_events(events)
        assert board_symbol_grid(state) == result["finalBoard"]
        assert state["featureWinX"] == pytest.approx(result["totalFeatureWinX"])
        assert state["totalWinX"] == pytest.approx(result["totalWinX"])
        assert state["totalWinX"] <= 50_000 + 1e-9
        assert state["mysteriesOpen"] == 0
        types = [e["type"] for e in events]
        assert types[:4] == [
            "skyjumpSpinStart",
            "skyjumpBoardReveal",
            "skyjumpLineWins",
            "skyjumpScatterResult",
        ]
        assert types[-3:] == ["skyjumpResult", "setTotalWin", "finalWin"]
        for event in events:
            for key, value in event.items():
                if isinstance(value, float):
                    assert math.isfinite(value)
                    assert value >= 0 or key in {"distanceDelta"}


def test_line_rtp_and_scatter_on_coach_e():
    config = _config()
    strips = config["reelModel"]["strips"]
    exact = exact_line_rtp(strips, config["paylines"], config["paytable"]["awards"])
    assert exact["lineRtp"] == pytest.approx(0.6029945972727959, rel=0, abs=1e-12)
    scatter = exact_scatter_distribution(strips)
    ge3 = sum(p for n, p in scatter.items() if n >= 3)
    assert ge3 == pytest.approx(0.00652967825443787, rel=0, abs=1e-12)
    assert 1 / ge3 == pytest.approx(153.14690265486726, rel=0, abs=1e-6)
    perfect = exact_perfect_v_prob(strips)
    assert perfect == pytest.approx(1.9755474637131444e-09, rel=0, abs=1e-18)
    # FS budget practicality check.
    feature_rtp = 0.11822
    reserve = 0.965 - exact["lineRtp"] - feature_rtp
    implied = reserve / ge3
    assert 30 < implied < 50


def test_scatter_and_perfect_v_initial_board_only():
    config = _config()
    board = _paint(
        _fill("M1"),
        [(0, 0, "S"), (1, 1, "S"), (2, 2, "S"), (1, 0, COACH_ID), (0, 1, "L2")],
    )
    features = resolve_features(
        board,
        StreamRng(["FLIGHT_TOKEN"] * 5, picks=["L2"], token_draws=[(1, 1)] * 5),
        config=config,
    )
    events = round_to_v2_events(
        {
            "stops": [0, 0, 0, 0, 0],
            "board": board,
            "wins": [],
            "lineWinX": 0,
            "totalFeatureWinX": features["totalFeatureWinX"],
            "totalFeatureWinXRaw": features["totalFeatureWinXRaw"],
            "totalWinX": features["totalFeatureWinX"],
            "totalWinXRaw": features["totalFeatureWinXRaw"],
            "scatter": {
                "positions": [{"reel": 0, "row": 0}, {"reel": 1, "row": 1}, {"reel": 2, "row": 2}],
                "count": 3,
                "perfectV": False,
                "trigger": None,
                "fromBoard": "initialReveal",
            },
            "features": features,
            "mode": "BASE",
            "isFreeSpin": False,
        }
    )
    assert events[3]["fromBoard"] == "initialReveal"
    assert events[3]["count"] == 3


def test_feature_samples_phase4b():
    data = json.loads((GAME_DIR / "skyjump_v2_feature_samples.json").read_text(encoding="utf-8"))
    assert data["nonProduction"] is True
    assert data["candidateOrigin"] == "F01_E_feel"
    samples = {row["id"]: row for row in data["samples"]}
    assert set(samples) == {f"{i:02d}" for i in range(1, 18)}
    assert samples["01"]["totalFeatureWinX"] == 0
    assert samples["03"]["totalFeatureWinX"] > 0
    assert samples["05"]["totalFeatureWinX"] > 0
    assert samples["16"]["capHit"] is True
    assert samples["17"]["capHit"] is True
    for sample in data["samples"]:
        state = reduce_events(sample["events"])
        assert board_symbol_grid(state) == sample["finalBoard"]
        assert state["totalWinX"] <= 50_000 + 1e-9
        assert abs(state["featureWinX"] - sample["totalFeatureWinX"]) < 1e-6


def test_latent_path_still_available_for_research():
    config = _latent_config()
    assert has_paying_economy(config) is False
    board = _paint(_fill("M1"), [(1, 1, COACH_ID), (0, 0, "L2")])
    features = resolve_features(board, random.Random(1), config)
    assert features["paying"] is False
    assert features["totalFeatureWinX"] == 0


def test_no_nan_negative_and_no_frontend_rng_contract():
    """Math events must be complete; frontend must not need RNG to settle."""
    result = resolve_v2_base(random.Random(99))
    events = round_to_v2_events(result)
    allowed_mid = {
        "skyjumpCoachSignal",
        "skyjumpMysteryTransform",
        "skyjumpMysteryResolve",
        "skyjumpGateUpgrade",
        "skyjumpThermalLift",
        "skyjumpJudgeCollect",
        "skyjumpHeadJudgeCollect",
        "skyjumpCapReached",
    }
    mid = [e["type"] for e in events][4:-3]
    assert set(mid) <= allowed_mid
    for event in events:
        if event["type"] == "skyjumpMysteryResolve":
            assert event["resultType"] in {
                "FLIGHT_TOKEN",
                "THERMAL_LIFT",
                "GATE_UPGRADE",
                "JUDGE",
                "HEAD_JUDGE",
            }


def test_phase4b_sim_report_exists_when_present():
    path = GAME_DIR / "skyjump_v2_phase4b_sim_report.json"
    if not path.exists():
        pytest.skip("10M report not written yet")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["nonProduction"] is True
    assert report["spins"] >= 1_000_000
    assert report["candidateOrigin"] == "F01_E_feel"
    assert abs(report["exact"]["lineRtp"] - 0.596961766439716) < 1e-9
    assert abs(report["simulated"]["featureRtpCapped"] - 0.11822) < 0.02
    assert abs(report["exact"]["pCoachAny"] - 0.0815972222222221) < 1e-9
    assert 0.20 <= report["simulated"]["pFeatureWinGivenCoach"] <= 0.30
    if report["spins"] >= 10_000_000:
        assert abs(report["simulated"]["featureRtpCapped"] - 0.11822) < 0.015
        assert report["simulated"]["capFrequency"] < 1e-5
