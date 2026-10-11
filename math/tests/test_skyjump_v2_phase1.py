"""SkyJump V2 Phase 1: 5×5 paylines, fixtures, JSON parity."""

from __future__ import annotations

import json
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

from skyjump_v2_lines import evaluate_paylines, load_dev_paytable, load_v2_config


def _fixtures() -> dict:
    data = json.loads((GAME_DIR / "skyjump_v2_phase1_fixtures.json").read_text(encoding="utf-8"))
    assert data["nonProduction"] is True
    return data


def test_v2_config_foundation():
    config = load_v2_config()
    assert config["meta"]["lineage"] == "skyjump-v2"
    assert config["meta"]["mathVersion"] == 2
    assert config["eventSchemaVersion"] == 2
    assert config["board"] == {"reels": 5, "rows": 5}
    assert config["maxFeatureChainDepth"] == 8
    assert config["layout"]["desktopLogical"] == {"width": 1280, "height": 720}
    assert len(config["symbols"]["regular"]) == 9
    assert config["symbols"]["scatter"]["id"] == "S"
    assert "weights" not in config
    assert config["paytable"]["status"] == "PHASE 7B LIVE PT2H_LADDER"
    assert config["paytable"]["nonFinal"] is False
    paylines = config["paylines"]
    assert len(paylines) == 28
    assert sorted(int(key) for key in paylines) == list(range(1, 29))
    for key, rows in paylines.items():
        assert len(rows) == 5, key
        assert all(0 <= row <= 4 for row in rows), key


def test_v1_config_untouched():
    v1 = json.loads((GAME_DIR / "skyjump_config.json").read_text(encoding="utf-8"))
    assert v1["meta"]["mathVersion"] == 3
    assert v1["eventSchemaVersion"] == 1
    assert v1["meta"].get("lineage") != "skyjump-v2"


def test_dev_paytable_is_labelled_non_production():
    data = load_dev_paytable()
    assert data["nonProduction"] is True
    assert data["usage"] == "FIXTURE/TEST ONLY"
    with pytest.raises(ValueError, match="paytable required"):
        evaluate_paylines([["L3"] * 5 for _ in range(5)])


def test_match_counts_and_rules():
    empty = [["S"] * 5 for _ in range(5)]

    def paint(cells):
        board = [col[:] for col in empty]
        for reel, row, symbol in cells:
            board[reel][row] = symbol
        return board

    three = evaluate_paylines(
        paint([(0, 2, "P1"), (1, 2, "P1"), (2, 2, "P1")]),
        allow_dev_paytable=True,
    )
    assert three["wins"][0]["matchCount"] == 3
    four = evaluate_paylines(
        paint([(0, 2, "P2"), (1, 2, "P2"), (2, 2, "P2"), (3, 2, "P2")]),
        allow_dev_paytable=True,
    )
    assert four["wins"][0]["matchCount"] == 4
    five = evaluate_paylines(
        paint([(0, 2, "P1"), (1, 2, "P1"), (2, 2, "P1"), (3, 2, "P1"), (4, 2, "P1")]),
        allow_dev_paytable=True,
    )
    assert five["wins"][0]["matchCount"] == 5
    late = [["S"] * 5] + [["P1"] * 5 for _ in range(4)]
    assert evaluate_paylines(late, allow_dev_paytable=True)["wins"] == []
    gap = paint([(0, 2, "P1"), (1, 2, "P1"), (2, 2, "L3"), (3, 2, "P1"), (4, 2, "P1")])
    assert evaluate_paylines(gap, allow_dev_paytable=True)["wins"] == []
    scatter = paint([(reel, 2, "S") for reel in range(5)])
    assert evaluate_paylines(scatter, allow_dev_paytable=True)["wins"] == []


def test_fixtures_replay():
    data = _fixtures()
    assert len(data["fixtures"]) == 10
    for row in data["fixtures"]:
        actual = evaluate_paylines(row["board"], allow_dev_paytable=True)
        if row["id"] in {"01", "07", "08", "09"}:
            assert actual["wins"] == []
        if row["id"] == "02":
            assert actual["wins"][0]["matchCount"] == 3
        if row["id"] == "03":
            assert actual["wins"][0]["matchCount"] == 4
        if row["id"] == "04":
            assert actual["wins"][0]["matchCount"] == 5
        if row["id"] in {"05", "06", "10"}:
            assert len(actual["wins"]) >= 2


def test_no_v2_production_books():
    library = MATH / "library"
    if not library.exists():
        return
    names = [path.name for path in library.iterdir()]
    assert not any("v2" in name.lower() and name.endswith((".jsonl", ".zst", ".csv")) for name in names)
