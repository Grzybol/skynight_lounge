"""Phase 6C.1 PURE W2 alignment tests."""

from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import new_bonus_state
from skyjump_v2_phase6a1_engine import Phase6A1State, choose_stage_a1
from skyjump_v2_phase6a1_search import PACKS, make_spec
from skyjump_v2_phase6b import (
    apply_wind_key,
    choose_stage,
    choose_stage_charge_priority,
    choose_stage_pure_w2,
    ensure_phase6_state,
    set_stage_selection_mode,
)
from skyjump_v2_phase6c_certify import BASELINE_MEAN, cfg_off, feature_off_equivalence

HERE = Path(__file__).resolve().parent
SAMPLES = HERE / "skyjump_v2_phase6_samples.json"
STAGES = ("RUN_UP", "TAKEOFF", "FLIGHT")


def _live_from_values_charges(values: dict[str, int], charges: dict[str, int]):
    state = new_bonus_state("LARGE_HILL")
    ensure_phase6_state(state)
    key = {"RUN_UP": "runUp", "TAKEOFF": "takeoff", "FLIGHT": "flight"}
    for name in STAGES:
        state.flightMultiplier[key[name]]["value"] = int(values[name])
        state.flightMultiplier[key[name]]["charge"] = int(charges[name])
    state.flightMultiplierRunUp = int(values["RUN_UP"])
    state.flightMultiplierTakeoff = int(values["TAKEOFF"])
    state.flightMultiplierFlight = int(values["FLIGHT"])
    state.runUpCharge = int(charges["RUN_UP"])
    state.takeoffCharge = int(charges["TAKEOFF"])
    state.flightCharge = int(charges["FLIGHT"])
    return state


def _research_from_values_charges(values: dict[str, int], charges: dict[str, int]):
    state = Phase6A1State()
    state.run_up = int(values["RUN_UP"])
    state.takeoff = int(values["TAKEOFF"])
    state.flight = int(values["FLIGHT"])
    state.charge_run_up = int(charges["RUN_UP"])
    state.charge_takeoff = int(charges["TAKEOFF"])
    state.charge_flight = int(charges["FLIGHT"])
    return state


class Phase6C1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_v2_config()
        cls.cand = bonus_candidate_from_config(cls.cfg)
        cls.pay = live_candidate_from_config(cls.cfg)
        cls.spec = make_spec(
            "P6A1_E_E1",
            PACKS["E1"],
            rejump_arch="R-BATCH",
            wind_arch="W-CHARGE",
            stage_rule="W2",
        )

    def test_live_default_is_pure_w2(self):
        self.assertEqual(self.cfg["freeSpins"]["phase6"]["stageRule"], "W2_PURE")
        state = _live_from_values_charges(
            {"RUN_UP": 1, "TAKEOFF": 1, "FLIGHT": 1},
            {"RUN_UP": 1, "TAKEOFF": 0, "FLIGHT": 0},
        )
        live = choose_stage(random.Random(0), state)
        pure = choose_stage_pure_w2(random.Random(0), state)
        prio = choose_stage_charge_priority(random.Random(0), state)
        self.assertEqual(live, pure)
        self.assertNotEqual(live, prio)
        self.assertEqual(prio, ("RUN_UP", "UPGRADE"))

    def test_research_live_picker_parity_many_states(self):
        mismatches = 0
        trials = 0
        for seed in range(400):
            rng = random.Random(seed)
            values = {name: rng.choice([1, 2, 3]) for name in STAGES}
            charges = {name: rng.choice([0, 1]) for name in STAGES}
            for name in STAGES:
                if values[name] == 3:
                    charges[name] = 0
            live_state = _live_from_values_charges(values, charges)
            research_state = _research_from_values_charges(values, charges)
            for draw in range(5):
                trials += 1
                live_stage, live_action = choose_stage_pure_w2(random.Random(seed * 17 + draw), live_state)
                research_stage = choose_stage_a1(
                    random.Random(seed * 17 + draw), research_state, self.spec
                )
                if research_stage is None:
                    if live_stage is not None:
                        mismatches += 1
                    continue
                expected_action = "UPGRADE" if charges[research_stage] == 1 else "CHARGE"
                if live_stage != research_stage or live_action != expected_action:
                    mismatches += 1
        self.assertEqual(mismatches, 0)
        self.assertGreater(trials, 1000)

    def test_saturated_stage_excluded(self):
        state = _live_from_values_charges(
            {"RUN_UP": 3, "TAKEOFF": 1, "FLIGHT": 1},
            {"RUN_UP": 0, "TAKEOFF": 0, "FLIGHT": 0},
        )
        for seed in range(40):
            stage, _action = choose_stage_pure_w2(random.Random(seed), state)
            self.assertNotEqual(stage, "RUN_UP")
            self.assertIn(stage, ("TAKEOFF", "FLIGHT"))

    def test_all_x3_noop(self):
        state = _live_from_values_charges(
            {"RUN_UP": 3, "TAKEOFF": 3, "FLIGHT": 3},
            {"RUN_UP": 0, "TAKEOFF": 0, "FLIGHT": 0},
        )
        detail = apply_wind_key(state, random.Random(0), {"kind": "wind"})
        self.assertEqual(detail["action"], "NO_OP")

    def test_pure_w2_samples_catalog(self):
        data = json.loads(SAMPLES.read_text(encoding="utf-8"))
        ids = {s["id"] for s in data["samples"]}
        for required in (
            "c1_a_first_key_charges_run_up",
            "c1_b_second_key_charges_takeoff",
            "c1_c_third_key_charges_flight",
            "c1_d_complete_one_to_x2",
            "c1_e_three_partial_charges",
            "c1_h_saturated_excluded",
            "c1_i_all_x3_saturation_b",
        ):
            self.assertIn(required, ids)
        self.assertTrue(data.get("pureW2"))

    def test_feature_off_near_phase5b(self):
        res = feature_off_equivalence(self.cfg, self.cand, self.pay, n=2_000, seed=11)
        self.assertLess(abs(res["featureOffMeanX"] - BASELINE_MEAN), 2.5)
        off = cfg_off(self.cfg)
        self.assertFalse(off["freeSpins"]["phase6"]["enabled"])

    def test_stage_override_still_available_for_audit(self):
        prev = set_stage_selection_mode("W2_CHARGE_PRIORITY")
        try:
            state = _live_from_values_charges(
                {"RUN_UP": 1, "TAKEOFF": 1, "FLIGHT": 1},
                {"RUN_UP": 1, "TAKEOFF": 0, "FLIGHT": 0},
            )
            self.assertEqual(choose_stage(random.Random(0), state), ("RUN_UP", "UPGRADE"))
        finally:
            set_stage_selection_mode(prev)


if __name__ == "__main__":
    unittest.main()
