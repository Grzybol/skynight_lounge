"""SkyJump V2 Phase 3: Coach, Mystery, Flight Tokens, reducer replay."""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
MATH = HERE.parents[1]
REPO = HERE.parents[2]
GAME_DIR = MATH / "games" / "0_0_poc"

for path in (str(GAME_DIR), str(MATH)):
    if path not in sys.path:
        sys.path.insert(0, path)

from copy import deepcopy

from skyjump_v2_events import round_to_v2_events
from skyjump_v2_exact import exact_line_rtp, exact_perfect_v_prob, exact_scatter_distribution, exact_symbol_window_distribution
from skyjump_v2_features import eligible_regular_types, resolve_features
from skyjump_v2_lines import evaluate_paylines, load_v2_config
from skyjump_v2_reels import COACH_ID, MYSTERY_ID, REGULAR_IDS, SCATTER_ID
from skyjump_v2_reducer import board_symbol_grid, reduce_events
from skyjump_v2_resolve import resolve_v2_base
from skyjump_v2_tokens import DEFAULT_VALUES, TIER_NAMES, assert_token_tables, exact_token_value_distribution, token_tables


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


class ScriptedRng:
    def __init__(self, picks: list[str], tokens: list[tuple[int, int]]):
        self.picks = list(picks)
        self.tokens = list(tokens)
        self._tier_pending: int | None = None

    def choice(self, population):
        if not self.picks:
            return population[0]
        pick = self.picks.pop(0)
        if pick not in population:
            raise AssertionError(f"{pick} not eligible among {population}")
        return pick

    def choices(self, population, weights, k=1):
        if self._tier_pending is not None:
            _tier, value = self.tokens.pop(0)
            self._tier_pending = None
            return [value]
        if self.tokens:
            tier, _value = self.tokens[0]
            self._tier_pending = tier
            return [tier]
        return [population[0]]


def test_phase2_paylines_still_pass():
    config = _config()
    assert len(config["paylines"]) == 28
    assert config["paylines"]["1"] == [0, 0, 0, 0, 0]
    assert config["paylines"]["6"] == [0, 1, 2, 1, 0]
    assert config["paylines"]["28"] == [0, 2, 4, 2, 0]


def test_coach_is_math_owned_reel_content():
    config = _config()
    strips = config["reelModel"]["strips"]
    assert config["coachModel"]["id"] == COACH_ID
    assert config["coachModel"]["paysOnLines"] is False
    assert config["coachModel"]["reels"] == [2, 4]
    assert [strip.count(COACH_ID) for strip in strips] == [0, 1, 0, 1, 0]
    assert all(MYSTERY_ID not in strip for strip in strips)
    assert all(not any(cell.startswith("T") for cell in strip) for strip in strips)


def test_coach_never_pays_paylines():
    config = _config()
    board = _fill(COACH_ID)
    evaluated = evaluate_paylines(board, paytable=config["paytable"]["awards"])
    assert evaluated["wins"] == []
    assert evaluated["lineWinX"] == 0
    mixed = _paint(_fill("L3"), [(0, 0, COACH_ID), (1, 0, COACH_ID), (2, 0, COACH_ID)])
    mixed_eval = evaluate_paylines(mixed, paytable=config["paytable"]["awards"])
    assert all(win["symbolId"] != COACH_ID for win in mixed_eval["wins"])


def test_only_regulars_are_eligible():
    board = _paint(
        _fill("S"),
        [(0, 0, "L2"), (1, 0, COACH_ID), (2, 0, MYSTERY_ID), (3, 0, "T3"), (4, 0, "P1")],
    )
    eligible = eligible_regular_types(board, set(REGULAR_IDS))
    assert eligible == ["P1", "L2"]
    assert "S" not in eligible
    assert COACH_ID not in eligible
    assert MYSTERY_ID not in eligible
    assert "T3" not in eligible


def test_coach_selects_visible_type_and_transforms_all():
    config = _latent_config()
    board = _paint(
        _fill("M1"),
        [(1, 1, COACH_ID), (2, 2, "L2"), (3, 3, "L2"), (4, 0, "L2")],
    )
    rng = ScriptedRng(["L2"], [(1, 1), (1, 2), (1, 3)])
    features = resolve_features(board, rng, config)
    assert features["selectedSymbolIds"] == ["L2"]
    selected = features["coaches"][0]["selectedPositions"]
    assert {(pos["reel"], pos["row"]) for pos in selected} == {(2, 2), (3, 3), (4, 0)}
    assert features["mysteriesPerCoach"] == [3]
    assert features["totalFeatureWinX"] == 0
    for pos in selected:
        assert features["workingBoard"][pos["reel"]][pos["row"]].startswith("T")


def test_multiple_coaches_left_to_right_and_second_skips_transformed_type():
    config = _latent_config()
    board = _paint(
        _fill("L3"),
        [(1, 0, COACH_ID), (3, 4, COACH_ID), (0, 1, "P2"), (2, 1, "P2"), (4, 2, "M3")],
    )
    rng = ScriptedRng(["L3", "P2"], [(1, 1)] * 30)
    features = resolve_features(board, rng, config)
    assert [coach["coachPosition"] for coach in features["coaches"]] == [
        {"reel": 1, "row": 0},
        {"reel": 3, "row": 4},
    ]
    assert features["selectedSymbolIds"] == ["L3", "P2"]
    assert "L3" not in features["coaches"][1]["eligibleSymbolIds"]
    assert features["coaches"][1]["selectedSymbolId"] == "P2"


def test_zero_eligible_coach_is_explicit_noop():
    config = _latent_config()
    board = _paint(_fill("S"), [(2, 2, COACH_ID)])
    features = resolve_features(board, random.Random(1), config)
    assert features["coaches"][0]["noOp"] is True
    assert features["coaches"][0]["selectedSymbolId"] is None
    assert features["coaches"][0]["reason"] == "noEligibleRegularType"
    assert features["transforms"] == []
    assert features["resolves"] == []


def test_mystery_count_parity_and_every_mystery_resolves_once():
    config = _latent_config()
    rng = random.Random(20260921)
    for _ in range(80):
        result = resolve_v2_base(rng, config=config)
        events = round_to_v2_events(result)
        transforms = [event for event in events if event["type"] == "skyjumpMysteryTransform"]
        resolves = [event for event in events if event["type"] == "skyjumpMysteryResolve"]
        created = sum(len(event["positions"]) for event in transforms)
        assert created == len(resolves)
        assert created == len(result["features"]["resolves"])
        for event in resolves:
            assert event["resultType"] == "FLIGHT_TOKEN"
            assert event["tokenName"] != "SPECIAL_WORLD_RECORD"
            if event["tokenTier"] == 6:
                assert event["tokenName"] == "TOKEN_WORLD_RECORD"
                assert event["tokenId"] == "T6"


def test_valid_token_tier_value_combinations():
    config = _config()
    tables = token_tables(config)
    assert_token_tables(tables)
    assert tables["names"][6] == "TOKEN_WORLD_RECORD"
    assert tables["t6Id"] == "TOKEN_WORLD_RECORD"
    assert tables["specialWorldRecordId"] == "SPECIAL_WORLD_RECORD"
    assert tables["t6Id"] != tables["specialWorldRecordId"]
    for tier, values in DEFAULT_VALUES.items():
        assert tuple(tables["values"][tier]) == values
    dist = exact_token_value_distribution(tables)
    assert dist["expected"] > 0
    assert math.isclose(sum(dist["byValue"].values()), 1.0, rel_tol=0, abs_tol=1e-12)
    assert dist["byTier"]["6"]["p"] == 8 / 1_000_000


def test_tokens_do_not_automatically_award():
    config = _latent_config()
    rng = random.Random(7)
    for _ in range(40):
        result = resolve_v2_base(rng, config=config)
        assert result["totalFeatureWinX"] == 0
        assert result["totalWinX"] == result["lineWinX"]
        events = round_to_v2_events(result)
        result_event = next(event for event in events if event["type"] == "skyjumpResult")
        assert result_event["totalFeatureWinX"] == 0
        assert result_event["totalWinX"] == result["lineWinX"]
        if result["features"]["latentTokenValueX"] > 0:
            assert result_event["latentTokenValueX"] == result["features"]["latentTokenValueX"]


def test_same_seed_same_feature_results():
    a = resolve_v2_base(random.Random(20260921), config=_latent_config())
    b = resolve_v2_base(random.Random(20260921), config=_latent_config())
    assert a["board"] == b["board"]
    assert a["features"]["selectedSymbolIds"] == b["features"]["selectedSymbolIds"]
    assert a["features"]["tokenValues"] == b["features"]["tokenValues"]
    assert a["finalBoard"] == b["finalBoard"]
    c = resolve_v2_base(random.Random(8), config=_latent_config())
    assert a["finalBoard"] != c["finalBoard"] or a["board"] != c["board"]


def test_reducer_replay_matches_final_board():
    rng = random.Random(20260921)
    config = _latent_config()
    for _ in range(25):
        result = resolve_v2_base(rng, config=config)
        events = round_to_v2_events(result)
        state = reduce_events(events)
        assert board_symbol_grid(state) == result["finalBoard"]
        assert state["featureWinX"] == 0
        assert state["totalWinX"] == result["lineWinX"]
        assert state["mysteriesOpen"] == 0
        assert state["lineWinX"] == result["lineWinX"]
        assert all(math.isfinite(float(event.get("tokenValueX", 0) or 0)) for event in events)
        assert all((event.get("tokenValueX") or 0) >= 0 for event in events)


def test_scatter_from_initial_reveal_only():
    config = _latent_config()
    board = _paint(_fill("L2"), [(0, 0, "S"), (1, 1, "S"), (2, 2, "S"), (1, 0, COACH_ID)])
    result_scatter = resolve_v2_base(random.Random(1), stops=None, config=config)
    assert result_scatter["scatter"]["fromBoard"] == "initialReveal"
    features = resolve_features(board, ScriptedRng(["L2"], [(1, 1)] * 30), config)
    events = round_to_v2_events(
        {
            "stops": [0, 0, 0, 0, 0],
            "board": board,
            "wins": [],
            "lineWinX": 0,
            "totalFeatureWinX": 0,
            "totalWinX": 0,
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
    scatter_event = events[3]
    assert scatter_event["type"] == "skyjumpScatterResult"
    assert scatter_event["count"] == 3
    assert scatter_event["fromBoard"] == "initialReveal"
    assert not any(event.get("resultType") == "S" for event in events)
    for event in events:
        if event["type"] == "skyjumpCoachSignal":
            assert event["selectedSymbolId"] != "S"


def test_perfect_v_pattern_unchanged():
    config = _config()
    assert config["scatterModel"]["perfectVRows"] == [0, 1, 2, 1, 0]
    strips = config["reelModel"]["strips"]
    perfect = exact_perfect_v_prob(strips)
    assert perfect == pytest.approx(1.9755474637131444e-09, rel=0, abs=1e-18)
    assert 1 / perfect > 300_000_000


def test_coach_frequency_research_band():
    config = _config()
    dist = exact_symbol_window_distribution(config["reelModel"]["strips"], COACH_ID)
    p_any = 1.0 - dist.get(0, 0.0)
    p_ge2 = sum(prob for count, prob in dist.items() if count >= 2)
    # Phase 4B Coach E feel target (~8.16% / ~0.174%).
    assert 0.07 <= p_any <= 0.10
    assert 0.001 <= p_ge2 <= 0.003


def test_post_coach_line_rtp_band():
    config = _config()
    exact = exact_line_rtp(
        config["reelModel"]["strips"],
        config["paylines"],
        config["paytable"]["awards"],
    )
    assert 0.57 <= exact["lineRtp"] <= 0.61
    scatter = exact_scatter_distribution(config["reelModel"]["strips"])
    ge3 = sum(prob for count, prob in scatter.items() if count >= 3)
    assert 0.006 < ge3 < 0.007


def test_event_order_and_no_negative_nan():
    result = resolve_v2_base(random.Random(99), config=_latent_config())
    events = round_to_v2_events(result)
    types = [event["type"] for event in events]
    assert types[:4] == ["skyjumpSpinStart", "skyjumpBoardReveal", "skyjumpLineWins", "skyjumpScatterResult"]
    assert types[-3:] == ["skyjumpResult", "setTotalWin", "finalWin"]
    mid = types[4:-3]
    allowed = {"skyjumpCoachSignal", "skyjumpMysteryTransform", "skyjumpMysteryResolve"}
    assert set(mid) <= allowed
    for event in events:
        for key, value in event.items():
            if isinstance(value, float):
                assert math.isfinite(value)
                assert value >= 0 or key in {"distanceDelta"}


def test_feature_samples_cover_required_cases():
    data = json.loads((GAME_DIR / "skyjump_v2_feature_samples.json").read_text(encoding="utf-8"))
    assert data["nonProduction"] is True
    samples = {row["id"]: row for row in data["samples"]}
    # Phase 4B expands the DEV feature-sample set; Phase 3 cases remain a subset.
    assert {"01", "02", "03", "04", "05", "06", "07"}.issubset(set(samples))
    assert len(samples) >= 7
    for sample_id in ("01", "02", "03", "04", "05", "06", "07"):
        sample = samples[sample_id]
        events = sample["events"]
        state = reduce_events(events)
        assert board_symbol_grid(state) == sample["finalBoard"]


def test_phase3_sim_report():
    report = json.loads((GAME_DIR / "skyjump_v2_phase3_sim_report.json").read_text(encoding="utf-8"))
    assert report["nonProduction"] is True
    assert report["spins"] >= 5_000_000
    assert abs(report["simulatedLineRtp"] - report["theoreticalLineRtp"]) < 0.002
    assert 0.57 <= report["theoreticalLineRtp"] <= 0.61
    assert report["latent"]["perMysteryExpected"] > 0
    assert report["tailPerSpin"]["50000"] < 1e-5
    # Historical Phase 3 report used denser Coach; keep archived metric check loose.
    assert report["coach"]["exactAny"] > 0.08


def test_no_v2_production_books():
    """After 7C.4, Stake package is stake-upload-final; game dir root must stay clean."""
    for name in ("books_BASE.jsonl.zst", "lookUpTable_BASE_0.csv"):
        assert not (GAME_DIR / name).exists()
    final = REPO / "stake-upload-final" / "math"
    assert final.exists()
    assert (final / "books_BASE.jsonl.zst").exists()
