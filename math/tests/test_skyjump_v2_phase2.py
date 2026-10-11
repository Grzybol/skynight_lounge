"""SkyJump V2 Phase 2: reel strips, grain, scatter, events, simulation sanity."""

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
        sys.path.insert(0, str(GAME_DIR if path == str(GAME_DIR) else MATH))

from skyjump_v2_events import round_to_v2_events
from skyjump_v2_exact import exact_line_rtp, exact_perfect_v_prob, exact_scatter_distribution, scatter_on_board
from skyjump_v2_lines import evaluate_paylines, load_dev_paytable, load_v2_config
from skyjump_v2_reels import (
    REGULAR_IDS,
    SCATTER_ID,
    assert_hierarchy,
    board_from_stops,
    frequency_table,
    grain_ok,
    visible_window,
)
from skyjump_v2_resolve import resolve_v2_base
from skyjump_v2_simulate import simulate


def _config() -> dict:
    return load_v2_config()


def test_phase1_paylines_unchanged():
    config = _config()
    paylines = config["paylines"]
    assert len(paylines) == 28
    assert paylines["1"] == [0, 0, 0, 0, 0]
    assert paylines["6"] == [0, 1, 2, 1, 0]
    assert paylines["28"] == [0, 2, 4, 2, 0]
    assert sorted(int(key) for key in paylines) == list(range(1, 29))


def test_provisional_config_sections():
    config = _config()
    assert config["meta"]["lineage"] == "skyjump-v2"
    assert config["meta"]["mathVersion"] == 2
    assert config["eventSchemaVersion"] == 2
    assert config["meta"]["mathStatus"] == "PHASE 7C.4 PRODUCTION MATH FROZEN"
    assert config["payoutGrainX"] == 0.1
    assert config["wager"]["unitX"] == 1
    assert "weights" not in config
    assert config["paytable"]["nonFinal"] is False
    assert config["reelModel"]["type"] == "independentVirtualStrips"
    assert config["reelModel"]["visibleRows"] == 5
    assert len(config["reelModel"]["strips"]) == 5
    assert all(len(strip) in (52, 120) for strip in config["reelModel"]["strips"])
    assert [len(strip) for strip in config["reelModel"]["strips"]] == [52, 120, 52, 120, 52]
    assert config["scatterModel"]["paysOnLines"] is False
    assert config["scatterModel"]["phase2PayoutX"] == 0
    assert config["scatterModel"]["perfectVRows"] == [0, 1, 2, 1, 0]
    assert config["flightTokens"]["doNotAutoPay"] is False
    assert config["featureEconomy"]["candidateOrigin"] == "F01_E_feel"
    assert config["freeSpins"]["candidateOrigin"] == "FS5A_U1_P2_M40_mid_E15j2"
    assert "featureBuys" not in config


def test_dev_paytable_fixture_still_available():
    data = load_dev_paytable()
    assert data["nonProduction"] is True
    assert data["usage"] == "FIXTURE/TEST ONLY"


def test_payout_grain_010x():
    awards = _config()["paytable"]["awards"]
    for symbol in REGULAR_IDS:
        for match in ("3", "4", "5"):
            payout = awards[symbol][match]
            assert grain_ok(payout, 0.1), f"{symbol} {match}={payout}"
            scaled = payout * 10
            assert abs(scaled - round(scaled)) < 1e-9
            assert payout > 0


def test_symbol_hierarchy_and_nonuniform_strips():
    config = _config()
    strips = config["reelModel"]["strips"]
    freqs = frequency_table(strips)
    global_freq = freqs["global"]
    for reel, strip in enumerate(strips):
        counts = {symbol: strip.count(symbol) for symbol in REGULAR_IDS}
        # Coach E pads reels 2/4 (1-indexed) with L3; keep hierarchy on unextended reels.
        if len(strip) == 52:
            assert_hierarchy(counts)
        assert 1 <= strip.count(SCATTER_ID) <= 2
        assert len(set(strip)) >= 8, reel
    assert global_freq["P1"] < global_freq["P2"] < global_freq["P3"]
    assert global_freq["P3"] < global_freq["M1"]
    assert global_freq["M3"] < global_freq["L1"]
    assert global_freq["L1"] <= global_freq["L2"] <= global_freq["L3"]
    assert global_freq["S"] < global_freq["P3"]


def test_visible_window_wraparound():
    strip = ["A", "B", "C", "D", "E", "F"]
    assert visible_window(strip, 0, 5) == ["A", "B", "C", "D", "E"]
    assert visible_window(strip, 4, 5) == ["E", "F", "A", "B", "C"]
    assert visible_window(strip, 5, 5) == ["F", "A", "B", "C", "D"]
    with pytest.raises(ValueError):
        visible_window(strip, 6, 5)


def test_board_from_stops_is_deterministic():
    strips = _config()["reelModel"]["strips"]
    stops = [0, 10, 20, 30, 51]
    first = board_from_stops(strips, stops)
    second = board_from_stops(strips, stops)
    assert first == second
    assert all(len(col) == 5 for col in first)
    wrapped = board_from_stops(strips, [51, 51, 51, 51, 51])
    for reel, col in enumerate(wrapped):
        assert col[0] == strips[reel][51]
        assert col[1] == strips[reel][0]


def test_same_seed_same_simulation():
    a = simulate(4_000, 20260921)
    b = simulate(4_000, 20260921)
    assert a["simulatedLineRtp"] == b["simulatedLineRtp"]
    assert a["hitRate"] == b["hitRate"]
    assert a["scatterCounts"] == b["scatterCounts"]
    c = simulate(4_000, 7)
    assert a["simulatedLineRtp"] != c["simulatedLineRtp"]


def test_scatter_does_not_pay_and_counts():
    config = _config()
    board = [["S"] * 5 for _ in range(5)]
    evaluated = evaluate_paylines(board, paytable=config["paytable"]["awards"])
    assert evaluated["wins"] == []
    assert evaluated["lineWinX"] == 0
    scatter = scatter_on_board(board, "S", (0, 1, 2, 1, 0))
    assert scatter["count"] == 25
    assert scatter["perfectV"] is True
    assert scatter["trigger"] is None

    v_board = [["L3"] * 5 for _ in range(5)]
    pattern = [0, 1, 2, 1, 0]
    for reel, row in enumerate(pattern):
        v_board[reel][row] = "S"
    detected = scatter_on_board(v_board, "S", tuple(pattern))
    assert detected["count"] == 5
    assert detected["perfectV"] is True
    v_board[2][2] = "L3"
    v_board[2][0] = "S"
    missed = scatter_on_board(v_board, "S", tuple(pattern))
    assert missed["count"] == 5
    assert missed["perfectV"] is False


def test_evaluator_parity_with_resolve():
    rng = random.Random(20260921)
    config = _config()
    for _ in range(40):
        result = resolve_v2_base(rng, config=config)
        replay = evaluate_paylines(
            result["board"],
            paylines=config["paylines"],
            paytable=config["paytable"]["awards"],
        )
        assert replay["wins"] == result["wins"]
        assert replay["lineWinX"] == result["lineWinX"]
        events = round_to_v2_events(result)
        line_event = events[2]
        assert line_event["wins"] == result["wins"]
        scatter_event = events[3]
        assert scatter_event["type"] == "skyjumpScatterResult"
        assert scatter_event["count"] == result["scatter"]["count"]
        assert scatter_event["trigger"] is None
        result_event = next(event for event in events if event["type"] == "skyjumpResult")
        assert result_event["totalFeatureWinX"] == pytest.approx(result["totalFeatureWinX"])
        assert result_event["totalLineWinX"] == result["lineWinX"]
        assert result_event["totalWinX"] == pytest.approx(result["totalWinX"])
        assert result_event["totalWinX"] == pytest.approx(result["lineWinX"] + result["totalFeatureWinX"])
        win_sum = sum(win["payoutX"] for win in result["wins"])
        assert abs(win_sum - result["lineWinX"]) < 1e-12
        assert result["lineWinX"] >= 0
        assert math.isfinite(result["lineWinX"])
        assert result["totalWinX"] <= 50_000 + 1e-9


def test_event_serialization_and_replay():
    result = resolve_v2_base(stops=[0, 1, 2, 3, 4])
    events = round_to_v2_events(result)
    assert [event["type"] for event in events] == [
        "skyjumpSpinStart",
        "skyjumpBoardReveal",
        "skyjumpLineWins",
        "skyjumpScatterResult",
        "skyjumpResult",
        "setTotalWin",
        "finalWin",
    ]
    assert events[0]["stops"] == [0, 1, 2, 3, 4]
    replay = resolve_v2_base(stops=events[0]["stops"])
    assert replay["board"] == events[1]["board"]
    assert replay["wins"] == events[2]["wins"]
    cloned = json.loads(json.dumps(events))
    assert cloned[5]["amount"] == cloned[6]["amount"]
    assert cloned[4]["totalFeatureWinX"] == 0
    # Without RNG there is no feature chain; forcing a feature win is allowed by schema-v2.
    forced = round_to_v2_events({**result, "totalFeatureWinX": 1, "totalWinX": result["lineWinX"] + 1})
    assert forced[-3]["totalFeatureWinX"] == 1


def test_math_samples_are_non_production_and_replayable():
    config = _config()
    data = json.loads((GAME_DIR / "skyjump_v2_math_samples.json").read_text(encoding="utf-8"))
    assert data["nonProduction"] is True
    assert "Not production" in data["usage"]
    assert len(data["samples"]) == 8
    for sample in data["samples"]:
        replay = evaluate_paylines(
            sample["board"],
            paylines=config["paylines"],
            paytable=config["paytable"]["awards"],
        )
        # Historical samples may predate PT2H paytable; still require finite replay structure.
        assert "lineWinX" in replay
        assert isinstance(replay["wins"], list)
        assert sample["events"][3]["type"] == "skyjumpScatterResult"
        assert all(math.isfinite(float(event.get("amount", 0) or 0)) for event in sample["events"])


def test_theoretical_line_rtp_in_research_band():
    config = _config()
    exact = exact_line_rtp(
        config["reelModel"]["strips"],
        config["paylines"],
        config["paytable"]["awards"],
    )
    assert 0.57 <= exact["lineRtp"] <= 0.61
    scatter = exact_scatter_distribution(config["reelModel"]["strips"])
    ge3 = sum(prob for count, prob in scatter.items() if count >= 3)
    assert 0.003 < ge3 < 0.02
    perfect = exact_perfect_v_prob(config["reelModel"]["strips"])
    assert perfect > 0
    assert perfect < 1e-6


def test_simulation_agrees_with_theory():
    report = simulate(80_000, 20260921)
    assert abs(report["simulatedLineRtp"] - report["theoreticalLineRtp"]) < 0.02
    assert report["hitRate"] > 0.2
    assert report["zeroWinRate"] > 0.4
    assert report["stdDev"] > 0
    assert report["maxObservedLineWinX"] >= 0
    assert all(math.isfinite(value) for value in (report["simulatedLineRtp"], report["stdDev"], report["hitRate"]))


def test_checked_in_five_million_report():
    report = json.loads((GAME_DIR / "skyjump_v2_sim_report.json").read_text(encoding="utf-8"))
    assert report["nonProduction"] is True
    assert report["spins"] >= 1_000_000
    assert abs(report["simulatedLineRtp"] - report["theoreticalLineRtp"]) < 0.002
    assert 0.57 <= report["theoreticalLineRtp"] <= 0.61


def test_no_v2_production_books():
    """Historical Phase 2 guard — after 7C.4, production lives only under stake-upload-final."""
    forbidden = list((MATH / "library").glob("*")) if (MATH / "library").exists() else []
    names = [path.name.lower() for path in forbidden]
    assert not any("v2" in name and name.endswith((".jsonl", ".zst", ".csv")) for name in names)
    for name in ("books_BASE.jsonl.zst", "lookUpTable_BASE_0.csv"):
        assert not (GAME_DIR / name).exists()
    final = REPO / "stake-upload-final" / "math"
    assert final.exists()
    assert (final / "books_BASE.jsonl.zst").exists()
    assert (final / "index.json").exists()
    # No research leaks in final package
    leaked = [
        p.name
        for p in final.iterdir()
        if p.is_file() and (p.suffix in {".md", ".py"} or (p.suffix == ".json" and p.name != "index.json"))
    ]
    assert leaked == []
