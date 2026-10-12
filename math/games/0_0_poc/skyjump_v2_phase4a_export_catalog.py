"""Export Phase 4A research candidate catalog (no live config writes)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_phase4a_candidates import (
    DEFAULT_THERMAL,
    PAYING_TOKEN_TIERS,
    PAYING_VALUE_WEIGHTS,
    coach_models,
    handcrafted_finalist_seeds,
)

OUT = HERE / "phase4a_research"
OUT.mkdir(exist_ok=True)

for candidate in handcrafted_finalist_seeds():
    path = OUT / f"candidate_{candidate['id']}.json"
    path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")

meta = {
    "nonProduction": True,
    "phase": "4A",
    "coachModels": {
        key: {
            "label": value["label"],
            "pAny": value["meta"]["pAny"],
            "pGe2": value["meta"]["pGe2"],
            "lineRtp": value["meta"]["lineRtp"],
            "reels0": value["reels0"],
        }
        for key, value in coach_models().items()
    },
    "payingTokenTiers": PAYING_TOKEN_TIERS,
    "payingValueWeights": PAYING_VALUE_WEIGHTS,
    "defaultThermal": DEFAULT_THERMAL,
    "handcraftedIds": [row["id"] for row in handcrafted_finalist_seeds()],
}
(OUT / "skyjump_v2_phase4a_candidate_catalog.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
print("wrote", len(handcrafted_finalist_seeds()), "candidates to", OUT)
