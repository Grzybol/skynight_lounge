"""Python reducer multi-charge Wind Key parity smoke for Phase 6C.1."""

from __future__ import annotations

import unittest

from skyjump_v2_reducer import initial_state, reduce_event


class PureW2ReducerTests(unittest.TestCase):
    def test_multiple_partial_charges(self):
        state = initial_state()
        events = [
            {
                "type": "skyjumpWindKey",
                "selectedStage": "RUN_UP",
                "action": "CHARGE",
                "oldStageValue": 1,
                "newStageValue": 1,
                "oldCharge": 0,
                "newCharge": 1,
                "oldGlobalMultiplier": 1,
                "newGlobalMultiplier": 1,
            },
            {
                "type": "skyjumpWindKey",
                "selectedStage": "TAKEOFF",
                "action": "CHARGE",
                "oldStageValue": 1,
                "newStageValue": 1,
                "oldCharge": 0,
                "newCharge": 1,
                "oldGlobalMultiplier": 1,
                "newGlobalMultiplier": 1,
            },
            {
                "type": "skyjumpWindKey",
                "selectedStage": "FLIGHT",
                "action": "CHARGE",
                "oldStageValue": 1,
                "newStageValue": 1,
                "oldCharge": 0,
                "newCharge": 1,
                "oldGlobalMultiplier": 1,
                "newGlobalMultiplier": 1,
            },
        ]
        for event in events:
            state = reduce_event(state, event)
        stages = state["flightMultiplier"]
        self.assertEqual(stages["runUp"]["charge"], 1)
        self.assertEqual(stages["takeoff"]["charge"], 1)
        self.assertEqual(stages["flight"]["charge"], 1)
        self.assertEqual(stages["runUp"]["value"], 1)
        self.assertEqual(state["globalFlightMultiplier"], 1)

    def test_upgrade_clears_only_selected_charge(self):
        state = initial_state()
        for stage in ("RUN_UP", "TAKEOFF", "FLIGHT"):
            state = reduce_event(
                state,
                {
                    "type": "skyjumpWindKey",
                    "selectedStage": stage,
                    "action": "CHARGE",
                    "oldStageValue": 1,
                    "newStageValue": 1,
                    "oldCharge": 0,
                    "newCharge": 1,
                    "oldGlobalMultiplier": 1,
                    "newGlobalMultiplier": 1,
                },
            )
        state = reduce_event(
            state,
            {
                "type": "skyjumpWindKey",
                "selectedStage": "TAKEOFF",
                "action": "UPGRADE",
                "oldStageValue": 1,
                "newStageValue": 2,
                "oldCharge": 1,
                "newCharge": 0,
                "oldGlobalMultiplier": 1,
                "newGlobalMultiplier": 2,
            },
        )
        stages = state["flightMultiplier"]
        self.assertEqual(stages["takeoff"], {"value": 2, "charge": 0})
        self.assertEqual(stages["runUp"]["charge"], 1)
        self.assertEqual(stages["flight"]["charge"], 1)
        self.assertEqual(state["globalFlightMultiplier"], 2)


if __name__ == "__main__":
    unittest.main()
