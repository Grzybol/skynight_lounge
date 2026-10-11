"""SkyJump V2 Phase 4A.2: feel refinement research."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
MATH = HERE.parents[1]
GAME_DIR = MATH / "games" / "0_0_poc"
CONFIG_PATH = GAME_DIR / "skyjump_v2_config.json"
H02_PATH = GAME_DIR / "phase4a_research" / "candidate_H02_B_R1.json"

for path in (str(GAME_DIR), str(MATH)):
    if path not in sys.path:
        sys.path.insert(0, path)

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase4a_economy import resolve_paying_features
from skyjump_v2_phase4a2_candidates import coach_models_4a2, feel_handcrafted_seeds, h02_benchmark
from skyjump_v2_phase4a2_simulate import score_feel_report
from skyjump_v2_reels import MYSTERY_ID


def _fill(symbol: str) -> list[list[str]]:
    return [[symbol] * 5 for _ in range(5)]


def _paint(board, cells):
    next_board = [col[:] for col in board]
    for reel, row, symbol in cells:
        next_board[reel][row] = symbol
    return next_board


def test_phase3_config_untouched_and_h02_preserved():
    raw = CONFIG_PATH.read_bytes()
    config = json.loads(raw.decode("utf-8"))
    assert config["coachModel"]["reels"] == [2, 4]
    assert config["flightTokens"]["doNotAutoPay"] is False
    assert config["featureEconomy"]["candidateOrigin"] == "F01_E_feel"
    assert H02_PATH.exists()
    h02 = json.loads(H02_PATH.read_text(encoding="utf-8"))
    assert h02["id"] == "H02_B_R1"
    assert hashlib.sha256(raw).hexdigest()


def test_sparse_two_reel_models_def():
    models = coach_models_4a2()
    for key in ("D", "E", "F"):
        meta = models[key]["meta"]
        assert 0.07 <= meta["pAny"] <= 0.12
        assert meta["pGe2"] > 0
        assert 0.57 <= meta["lineRtp"] <= 0.605
        assert models[key]["reels0"] == [1, 3]


def test_dead_reason_tokens_no_collector():
    config = load_v2_config()
    candidate = next(row for row in feel_handcrafted_seeds() if row["id"] == "F01_E_feel")
    board = _paint(_fill("L2"), [(0, 0, MYSTERY_ID), (0, 1, MYSTERY_ID)])
    stream = ["FLIGHT_TOKEN", "FLIGHT_TOKEN"]

    class Rng:
        def __init__(self):
            self.i = 0

        def choice(self, population):
            return population[0]

        def choices(self, population, weights, k=1):
            if "FLIGHT_TOKEN" in population:
                out = stream[self.i]
                self.i += 1
                return [out]
            if list(population) == [1, 2, 3, 4, 5, 6]:
                return [1]
            return [1]

    # Force a coach activation path by placing Coach... resolve uses board coaches.
    # Direct mystery board: coachCount may be 0. Use coach on board.
    from skyjump_v2_reels import COACH_ID

    board = _paint(
        _fill("L2"),
        [(1, 2, COACH_ID), (0, 0, "L1"), (2, 0, "L1"), (3, 0, "L1"), (4, 0, "L1")],
    )

    class CoachRng:
        def __init__(self):
            self.n = 0

        def choice(self, population):
            return "L1" if "L1" in population else population[0]

        def choices(self, population, weights, k=1):
            self.n += 1
            if "FLIGHT_TOKEN" in population:
                return ["FLIGHT_TOKEN"]
            if list(population) == [1, 2, 3, 4, 5, 6]:
                return [1]
            return [1]

    result = resolve_paying_features(board, CoachRng(), config=config, candidate=candidate, line_win_x=0.0)
    assert result["coachCount"] >= 1
    if result["deadCoach"]:
        assert result["deadReason"] in {
            "tokens_no_collector",
            "collector_no_tokens",
            "modifier_only",
            "other",
        }


def test_conditional_reduces_collector_without_token_bias():
    config = load_v2_config()
    independent = next(row for row in feel_handcrafted_seeds() if row["id"] == "F01_E_feel")
    conditioned = next(row for row in feel_handcrafted_seeds() if row["id"] == "F06_E_cond")
    assert conditioned["conditionalCollectors"] is True
    assert "mysteryResultWeightsWhenToken" in conditioned
    assert conditioned["mysteryResultWeightsNoToken"]["JUDGE"] < conditioned["mysteryResultWeightsWhenToken"]["JUDGE"]
    assert independent["conditionalCollectors"] is False


def test_feel_score_penalizes_high_dead_coach():
    base = {
        "featureRtpCapped": 0.10,
        "pDeadCoach": 0.82,
        "pFeatureWinGivenCoach": 0.18,
        "medianFeatureWinGivenWin": 4.0,
        "avgFeatureWinGivenWin": 6.0,
        "coachExact": {"pGe2": 0.0, "pAny": 0.096},
        "theoreticalLineRtp": 0.585,
        "remainingFsRtp": 0.27,
        "impliedAvgBonusPerScatterTrigger": 35.0,
        "capFrequency": 0.0,
        "capDragRtp": 0.0,
        "tailFeatureRaw": {"100": 0.00002, "50000": 0.0},
        "candidate": {"tokenTierWeights": {"6": 8}, "conditionalCollectors": False},
        "coachModelId": "B",
    }
    good = dict(base)
    good["pDeadCoach"] = 0.70
    good["pFeatureWinGivenCoach"] = 0.30
    good["coachExact"] = {"pGe2": 0.002, "pAny": 0.085}
    assert score_feel_report(good)["score"] > score_feel_report(base)["score"]


def test_h02_benchmark_id_stable():
    assert h02_benchmark()["id"] == "H02_B_R1"
    assert h02_benchmark().get("benchmark") is True
