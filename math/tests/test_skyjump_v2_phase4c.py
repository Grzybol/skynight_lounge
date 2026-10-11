"""SkyJump V2 Phase 4C: BASE feature RTP tail certification (measurement only)."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
MATH = HERE.parents[1]
GAME_DIR = MATH / "games" / "0_0_poc"

for path in (str(GAME_DIR), str(MATH)):
    if path not in sys.path:
        sys.path.insert(0, path)

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase4c_exact import config_fingerprint, exact_flight_token_joint, exact_mystery_result_probs
from skyjump_v2_phase4c_strata import (
    bulk_low_tier_mc,
    certified_from_strata,
    conditional_given_forced_tier,
    exact_p_max_tier_given_n,
    mix_over_n,
    probe_mystery_count_distribution,
)
from skyjump_v2_phase4c_stratified import DrawLog, biased_mystery_policy, run_stratified_batch

CONFIG_PATH = GAME_DIR / "skyjump_v2_config.json"
HASH_PATH = GAME_DIR / "phase4c_research" / "live_config_sha256.txt"
BASE_HASH = "1a29aec272e35dd5a1d1e772c0083a04a0ad50409690071185d243a6ea6e1560"


def certified_base_bytes(raw: bytes) -> bytes:
    """Phase 5B appends freeSpins. The certified BASE file is the prefix before that key."""
    marker = b',\r\n  "freeSpins"'
    if marker not in raw:
        return raw
    return raw.split(marker)[0] + b"\r\n}\r\n"


def test_live_config_hash_recorded_and_stable():
    digest = hashlib.sha256(certified_base_bytes(CONFIG_PATH.read_bytes())).hexdigest()
    assert digest == BASE_HASH
    # Phase 4C must not alter core economy fingerprint fields.
    fp = config_fingerprint(load_v2_config())
    assert fp["candidateOrigin"] == "F01_E_feel"
    assert fp["mysteryResultWeights"]["FLIGHT_TOKEN"] == 855
    assert fp["tokenTierWeights"]["6"] == 8
    assert fp["gateMaxFloor"] == 3
    assert fp["coachModelId"] == "E"


def test_exact_mystery_and_token_probs():
    config = load_v2_config()
    myst = exact_mystery_result_probs(config)
    assert abs(sum(myst.values()) - 1.0) < 1e-12
    joint = exact_flight_token_joint(config)
    assert joint["pFlightToken"] == pytest.approx(0.855)
    assert joint["pTierGivenFlight"][6] == pytest.approx(8 / 1_000_000)
    assert joint["pFlightAndTier"][6] == pytest.approx(0.855 * 8 / 1_000_000)
    assert abs(sum(joint["pFlightAndT6Face"].values()) - joint["pFlightAndTier"][6]) < 1e-15


def test_stratum_probs_sum_for_fixed_n():
    config = load_v2_config()
    joint = exact_flight_token_joint(config)
    for n in (0, 1, 2, 5, 10):
        part = exact_p_max_tier_given_n(n, joint["pFlightAndTier"])
        s = part["NO_T4PLUS"] + part["T4_NO_T5PLUS"] + part["T5_NO_T6"] + part["T6_PRESENT"]
        assert abs(s - 1.0) < 1e-12


def test_mix_over_n_sums_to_one():
    config = load_v2_config()
    joint = exact_flight_token_joint(config)
    probe = probe_mystery_count_distribution(20_000, 11, config)
    mixed = mix_over_n(probe["pN"], joint["pFlightAndTier"])
    s = mixed["NO_T4PLUS"] + mixed["T4_NO_T5PLUS"] + mixed["T5_NO_T6"] + mixed["T6_PRESENT"]
    assert abs(s - 1.0) < 1e-9


def test_importance_drawlog_reweight_identity():
    draw = DrawLog()
    draw.observe(0.5, 0.5)
    draw.observe(0.2, 0.1)
    assert draw.weight == pytest.approx(2.0)


def test_biased_policy_does_not_mutate_true_tables():
    a = biased_mystery_policy("natural")
    b = biased_mystery_policy("boost_t6")
    assert a["tier"][6] == 8.0
    assert b["tier"][6] > a["tier"][6]
    # re-fetch natural unchanged
    c = biased_mystery_policy("natural")
    assert c["tier"][6] == 8.0


def test_raw_ge_capped_and_cap_excess_accounting():
    config = load_v2_config()
    cond = conditional_given_forced_tier(spins=2_000, seed=21, forced_tier=6, config=config)
    assert cond["n"] > 0
    assert cond["E_raw"] + 1e-9 >= cond["E_capped"]
    if cond["pCap"] > 0:
        assert cond["E_excess_given_cap"] >= 0


def test_tier_decomposition_pieces_nonnegative():
    config = load_v2_config()
    joint = exact_flight_token_joint(config)
    probe = probe_mystery_count_distribution(30_000, 5, config)
    p_stratum = mix_over_n(probe["pN"], joint["pFlightAndTier"])
    bulk = bulk_low_tier_mc(40_000, 6, config)
    cond_t4 = conditional_given_forced_tier(spins=1_500, seed=7, forced_tier=4, config=config)
    cond_t5 = conditional_given_forced_tier(spins=1_500, seed=8, forced_tier=5, config=config)
    cond_t6 = conditional_given_forced_tier(spins=1_500, seed=9, forced_tier=6, config=config)
    cert = certified_from_strata(
        p_stratum=p_stratum, bulk=bulk, cond_t4=cond_t4, cond_t5=cond_t5, cond_t6=cond_t6
    )
    assert cert["featureRtpRaw"] + 1e-9 >= cert["featureRtpCapped"]
    assert cert["featureRtpCapped"] > 0
    piece_sum = sum(p["p"] * p["E_capped"] for p in cert["pieces"].values())
    assert abs(piece_sum - cert["featureRtpCapped"]) < 1e-9


def test_collector_pass_decomposition_sums_near_bulk():
    bulk = bulk_low_tier_mc(30_000, 12, load_v2_config())
    s = sum(row["cappedRtp"] for row in bulk["byCollectorPasses"].values())
    assert abs(s - bulk["featureRtpCapped"]) < 1e-9


def test_deterministic_stratified_and_conditional():
    config = load_v2_config()
    a = run_stratified_batch(spins=3_000, seed=99, mode="natural", config=config).finalize()
    b = run_stratified_batch(spins=3_000, seed=99, mode="natural", config=config).finalize()
    assert a["featureRtpCapped"] == b["featureRtpCapped"]
    c1 = conditional_given_forced_tier(spins=800, seed=77, forced_tier=6, config=config)
    c2 = conditional_given_forced_tier(spins=800, seed=77, forced_tier=6, config=config)
    assert c1["E_capped"] == c2["E_capped"]


def test_no_live_config_mutation_during_analysis():
    before = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
    config = load_v2_config()
    _ = exact_flight_token_joint(config)
    _ = probe_mystery_count_distribution(2_000, 1, config)
    _ = conditional_given_forced_tier(spins=200, seed=2, forced_tier=6, config=config)
    after = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
    assert before == after


def test_phase4c_report_when_present():
    path = GAME_DIR / "skyjump_v2_phase4c_cert_report.json"
    if not path.exists():
        pytest.skip("cert report not written yet")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["nonProduction"] is True
    assert report["phase"] == "4C"
    # Report SHA is historical (pre-7C.4 promote); live stripped BASE hash is pinned separately.
    assert isinstance(report["liveConfigSha256"], str) and len(report["liveConfigSha256"]) == 64
    assert report["certifiedBestEstimate"]["featureRtpCapped"] > 0
    assert report["classification"] in {
        "STABLE",
        "STABLE BUT ECONOMICALLY POOR",
        "NOT STABLE",
    }
