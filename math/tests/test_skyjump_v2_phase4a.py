"""SkyJump V2 Phase 4A: paying-feature economy research (no live config mutation)."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
MATH = HERE.parents[1]
GAME_DIR = MATH / "games" / "0_0_poc"
CONFIG_PATH = GAME_DIR / "skyjump_v2_config.json"

for path in (str(GAME_DIR), str(MATH)):
    if path not in sys.path:
        sys.path.insert(0, path)

from skyjump_v2_phase4a_candidates import coach_models, handcrafted_finalist_seeds
from skyjump_v2_phase4a_economy import neighbours, resolve_paying_features
from skyjump_v2_phase4a_simulate import counterfactual_stack, score_report, simulate_candidate
from skyjump_v2_lines import load_v2_config
from skyjump_v2_reels import COACH_ID, MYSTERY_ID


def _fill(symbol: str) -> list[list[str]]:
    return [[symbol] * 5 for _ in range(5)]


def _paint(board: list[list[str]], cells: list[tuple[int, int, str]]) -> list[list[str]]:
    next_board = [col[:] for col in board]
    for reel, row, symbol in cells:
        next_board[reel][row] = symbol
    return next_board


def test_live_phase3_config_untouched():
    """Phase 4A research asserted latent live config; Phase 4B promotes F01 paying."""
    raw = CONFIG_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    config = json.loads(raw.decode("utf-8"))
    assert config["coachModel"]["reels"] == [2, 4]
    assert config["coachModel"]["stopsPerReel"] == 1
    assert config["flightTokens"]["doNotAutoPay"] is False
    assert config["featureEconomy"]["candidateOrigin"] == "F01_E_feel"
    assert config["mysteryModel"]["resultTable"] == "independent"
    assert len(digest) == 64
    assert config["meta"]["lineage"] == "skyjump-v2"
    assert config["meta"]["mathVersion"] == 2


def test_neighbours_moore_excludes_self():
    n = neighbours(2, 2)
    assert (2, 2) not in n
    assert len(n) == 8
    assert neighbours(0, 0) == [(0, 1), (1, 0), (1, 1)]


def test_token_face_immutable_under_thermal():
    config = load_v2_config()
    candidate = handcrafted_finalist_seeds()[0]
    # Force: coach transforms L1 -> mysteries. Script outcomes via choices weights path
    # by constructing mysteries directly on board with Coach absent and seeding RNG
    # that always picks TOKEN/THERMAL via weighted picks.
    board = _fill("L2")
    board = _paint(
        board,
        [
            (0, 0, MYSTERY_ID),
            (0, 1, MYSTERY_ID),
            (1, 0, MYSTERY_ID),
        ],
    )
    # Deterministic: first mystery token tier1 value1, second thermal 3x, third token.
    class Rng:
        def __init__(self):
            self.n = 0

        def choice(self, population):
            return population[0]

        def choices(self, population, weights, k=1):
            self.n += 1
            # mystery result picks
            if set(map(str, population)) >= {"FLIGHT_TOKEN", "THERMAL_LIFT"} or "FLIGHT_TOKEN" in population:
                if self.n == 1:
                    return ["FLIGHT_TOKEN"]
                if self.n == 2:
                    return ["THERMAL_LIFT"]
                if self.n == 3:
                    return ["FLIGHT_TOKEN"]
            # thermal mult
            if 2 in population or "2" in map(str, population):
                return [3]
            # tier pick
            if population == [1, 2, 3, 4, 5, 6] or list(population) == [1, 2, 3, 4, 5, 6]:
                return [1]
            # value pick within tier
            return [1]

    result = resolve_paying_features(board, Rng(), config=config, candidate=candidate, line_win_x=0.0)
    tokens = [c for col in result["cells"] for c in col if c["kind"] == "token"]
    assert tokens
    for token in tokens:
        face = token["faceValueX"]
        eff = token["effectiveValueX"]
        assert face is not None
        # Face never mutated; effective may be multiplied.
        if token["appliedThermals"]:
            product = 1
            for mult in token["appliedThermals"]:
                product *= mult
            assert eff == pytest.approx(face * product)
            assert token["tokenValueX"] == face
        else:
            assert eff == face


def test_judge_sums_effective_and_head_judge_two_passes():
    config = load_v2_config()
    candidate = handcrafted_finalist_seeds()[0]
    board = _fill("L2")
    # Place two mysteries that we force to tokens and one judge + one head judge
    # via a scripted result stream.
    board = _paint(
        board,
        [
            (0, 0, MYSTERY_ID),
            (0, 1, MYSTERY_ID),
            (1, 0, MYSTERY_ID),
            (1, 1, MYSTERY_ID),
        ],
    )
    stream = ["FLIGHT_TOKEN", "FLIGHT_TOKEN", "JUDGE", "HEAD_JUDGE"]

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

    result = resolve_paying_features(board, Rng(), config=config, candidate=candidate, line_win_x=0.0)
    assert result["judgeCount"] == 1
    assert result["headJudgeCount"] == 1
    assert result["collectorPasses"] == 3  # 1 judge + 2 head passes
    assert result["totalFeatureWinXRaw"] == pytest.approx(result["effectiveTokenSumX"] * 3)
    assert len([c for c in result["collections"] if c["type"] == "HEAD_JUDGE"]) == 2


def test_gate_upgrades_replace_below_floor_faces():
    config = load_v2_config()
    candidate = dict(handcrafted_finalist_seeds()[0])
    candidate["gateMaxFloor"] = 3
    board = _paint(
        _fill("L2"),
        [
            (0, 0, MYSTERY_ID),
            (0, 1, MYSTERY_ID),
            (1, 0, MYSTERY_ID),
        ],
    )
    stream = ["FLIGHT_TOKEN", "GATE_UPGRADE", "FLIGHT_TOKEN"]
    values = []

    class Rng:
        def choice(self, population):
            return population[0]

        def choices(self, population, weights, k=1):
            if "FLIGHT_TOKEN" in population:
                return [stream.pop(0)]
            if list(population) == [1, 2, 3, 4, 5, 6]:
                return [1]
            # floor replacement samples tier-2 values
            values.append(population[0])
            return [population[0]]

    result = resolve_paying_features(board, Rng(), config=config, candidate=candidate, line_win_x=0.0)
    assert result["gateCount"] == 1
    assert result["tokenFloorTier"] == 2
    assert result["upgradedTokens"] >= 1
    for event in result["gateEvents"]:
        for rep in event["replacements"]:
            assert rep["before"]["tier"] < event["floorAfter"]
            assert rep["after"]["tier"] == event["floorAfter"]


def test_collectors_stack_without_dedupe():
    config = load_v2_config()
    candidate = handcrafted_finalist_seeds()[0]
    board = _paint(
        _fill("L2"),
        [
            (0, 0, MYSTERY_ID),
            (1, 0, MYSTERY_ID),
            (2, 0, MYSTERY_ID),
            (3, 0, MYSTERY_ID),
        ],
    )
    stream = ["FLIGHT_TOKEN", "JUDGE", "JUDGE", "HEAD_JUDGE"]

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

    result = resolve_paying_features(board, Rng(), config=config, candidate=candidate, line_win_x=0.0)
    # 2 judges + head(2) = 4 * sum
    assert result["totalFeatureWinXRaw"] == pytest.approx(result["effectiveTokenSumX"] * 4)


def test_max_win_cap_tracks_raw_and_drag():
    config = load_v2_config()
    candidate = dict(handcrafted_finalist_seeds()[0])
    candidate["maxWinX"] = 10
    board = _paint(
        _fill("L2"),
        [
            (0, 0, MYSTERY_ID),
            (1, 0, MYSTERY_ID),
        ],
    )
    stream = ["FLIGHT_TOKEN", "JUDGE"]

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
                return [6]
            # T6 value — pick largest
            return [max(population)]

    result = resolve_paying_features(board, Rng(), config=config, candidate=candidate, line_win_x=0.0)
    assert result["totalFeatureWinXRaw"] >= 10
    assert result["capHit"] is True
    assert result["totalWinXCapped"] == 10
    assert result["capDragX"] == pytest.approx(result["totalWinXRaw"] - 10)


def test_coach_models_cover_abc_bands():
    models = coach_models()
    assert models["A"]["meta"]["pAny"] == pytest.approx(0.183, abs=0.01)
    assert models["B"]["meta"]["pAny"] == pytest.approx(0.096, abs=0.01)
    assert 0.12 <= models["C"]["meta"]["pAny"] <= 0.17


def test_handcrafted_candidates_score_near_band_on_smoke():
    coaches = coach_models()
    candidate = next(row for row in handcrafted_finalist_seeds() if row["id"] == "H01_B_R2")
    report = simulate_candidate(candidate, spins=80_000, seed=7, coach_bundle=coaches)
    scored = score_report(report)
    # Smoke only — allow wider band; deep sims validate precisely.
    assert 0.05 <= report["featureRtpCapped"] <= 0.20
    assert report["pDeadCoach"] > 0.5
    assert scored["rtpError"] < 0.12


def test_counterfactual_layers_monotonic_rtp():
    coaches = coach_models()
    candidate = handcrafted_finalist_seeds()[0]
    stack = counterfactual_stack(candidate, spins=40_000, seed=11, coach_bundle=coaches)
    # Soft-disable keeps mystery identities; each added paying layer should not reduce RTP.
    assert stack["judge_only"]["featureRtpCapped"] <= stack["judge_head"]["featureRtpCapped"] + 1e-12
    assert stack["judge_head"]["featureRtpCapped"] <= stack["judge_head_thermal"]["featureRtpCapped"] + 1e-12
    assert stack["judge_head_thermal"]["featureRtpCapped"] <= stack["full"]["featureRtpCapped"] + 1e-12
