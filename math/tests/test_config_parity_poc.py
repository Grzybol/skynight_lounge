"""Frontend / Python / canonical JSON parity for SkyJump (`0_0_poc`)."""

import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
MATH = HERE.parents[1]
REPO = HERE.parents[2]
CONFIG_TS = REPO / "frontend" / "apps" / "poc" / "src" / "game" / "config.ts"
CANONICAL = MATH / "games" / "0_0_poc" / "skyjump_config.json"
GAME_DIR = MATH / "games" / "0_0_poc"

for path in (str(GAME_DIR), str(MATH)):
    if path not in sys.path:
        sys.path.insert(0, path)


def _canonical() -> dict:
    return json.loads(CANONICAL.read_text(encoding="utf-8"))


def _frontend_game_id() -> str:
    text = CONFIG_TS.read_text(encoding="utf-8")
    match = re.search(r"gameID:\s*rawConfig\.meta\.gameID", text)
    assert match, "frontend config.ts must derive gameID from canonical JSON"
    return _canonical()["meta"]["gameID"]


@pytest.fixture(scope="module")
def canonical():
    return _canonical()


@pytest.fixture(scope="module")
def py():
    from game_config import GameConfig

    return GameConfig()


def test_game_id_parity(canonical, py):
    assert canonical["meta"]["gameID"] == "0_0_poc"
    assert py.game_id == canonical["meta"]["gameID"]
    assert _frontend_game_id() == canonical["meta"]["gameID"]


def test_book_amount_multiplier(canonical):
    assert canonical["bookAmountMultiplier"] == 100


def test_mode_ids_costs_and_maxwin(canonical, py):
    from skyjump_resolve import CONFIG

    enabled = {
        mode_id: mode
        for mode_id, mode in canonical["buyModes"].items()
        if mode.get("enabled", True)
    }
    # Stake-published IDs are rgsKey; canonical JSON keys/ids stay snake_case.
    published = {mode["rgsKey"]: mode for mode in enabled.values()}
    py_modes = {bm.get_name(): bm for bm in py.bet_modes}
    assert set(published) == set(py_modes)
    assert {mode["id"] for mode in enabled.values()} == set(enabled)

    fe_text = CONFIG_TS.read_text(encoding="utf-8")
    assert "paylines: {}" in fe_text
    assert "symbols: {}" in fe_text or "symbols: {} as" in fe_text
    assert "mode.rgsKey" in fe_text

    for rgs_key, mode in published.items():
        bm = py_modes[rgs_key]
        assert bm.get_cost() == pytest.approx(mode["costMultiplier"]), rgs_key
        assert bm.get_wincap() == pytest.approx(mode["maxWin"]), rgs_key
        hill = CONFIG["hills"][mode["hillProfile"]]
        assert mode["maxWin"] > 0, rgs_key
        assert mode["hillProfile"] == hill["id"]
        assert mode["multiplierProfile"] in CONFIG["finalMultipliers"]


def test_no_garden_lines_metadata(py):
    assert py.paytable == {}
    assert py.paylines == {}
    assert py.num_reels == 6
    assert list(py.num_rows) == [1, 1, 1, 1, 1, 1]
    assert py.win_type == "custom"
    assert py.special_symbols["wild"] == []
    assert py.special_symbols["scatter"] == []


def test_published_maxwin_is_gameplay_cap(canonical):
    from skyjump_resolve import tables_for_mode

    for mode in canonical["buyModes"].values():
        if not mode.get("enabled", True):
            continue
        tables = tables_for_mode(mode["rgsKey"])
        assert tables["maxWin"] == mode["maxWin"]


def _sha256_newline_stable(data: bytes) -> str:
    import hashlib

    text = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(text).hexdigest()


def test_canonical_sha256_is_frozen(canonical):
    digest = _sha256_newline_stable(CANONICAL.read_bytes())
    assert digest == "321dedd2d88259b37b7d779d000ddfe5a154bc1a9512a1dceb67830f91eefd33"
    assert canonical["meta"]["mathVersion"] == 3
    assert canonical["eventSchemaVersion"] == 1


def test_mult_mode_caps_are_not_normal_hill():
    from skyjump_resolve import tables_for_mode

    assert tables_for_mode("MULT_10_100")["maxWin"] == 6000
    assert tables_for_mode("MULT_20_200")["maxWin"] == 12000
    assert tables_for_mode("BASE")["maxWin"] == 500


def test_frontend_hud_derives_enabled_modes():
    game_svelte = (REPO / "frontend" / "apps" / "poc" / "src" / "components" / "Game.svelte").read_text(
        encoding="utf-8"
    )
    skyjump_config = (
        REPO / "frontend" / "apps" / "poc" / "src" / "game" / "skyjump" / "config.ts"
    ).read_text(encoding="utf-8")
    assert "ENABLED_MODES" in game_svelte
    assert "new Set(['LARGE_HILL'" not in game_svelte
    assert "ENABLED_BUY_MODES" in skyjump_config
    assert "mode.enabled !== false" in skyjump_config


def test_zstandard_is_available():
    import zstandard

    payload = zstandard.ZstdCompressor().compress(b"skyjump-writer-smoke")
    assert zstandard.ZstdDecompressor().decompress(payload) == b"skyjump-writer-smoke"


def test_writer_run_py_uses_rgs_keys():
    from game_config import published_sim_counts

    counts = published_sim_counts(False, 9, 1)
    assert list(counts) == ["BASE", "LARGE_HILL", "SKI_FLYING", "MULT_10_100", "MULT_20_200"]
    assert set(counts.values()) == {9}
    debug_counts = published_sim_counts(True, 9, 4)
    assert debug_counts["BASE"] == 4
    assert debug_counts["SKI_FLYING"] == 0
