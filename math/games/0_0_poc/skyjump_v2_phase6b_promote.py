"""Promote approved P6A1_E_E1 into live freeSpins config. BASE untouched."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from skyjump_v2_phase6a_search import table_for
from skyjump_v2_phase6a1_search import PACKS

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "skyjump_v2_config.json"

E1 = PACKS["E1"]
PHASE6 = {
    "enabled": True,
    "candidateOrigin": "P6A1_E_E1",
    "rejumpArch": "R-BATCH",
    "windArch": "W-CHARGE",
    "ladder": "K1",
    "stageRule": "W2_CHARGE_PRIORITY",
    "saturation": "B",
    "perfectV": "PV1",
    "maxRejumpsPerSpin": 2,
    "maxFeatureChainDepth": 8,
    "packs": {
        "LARGE_HILL": {"REJUMP": 22, "WIND_KEY": 6},
        "SKI_FLYING": {"REJUMP": 36, "WIND_KEY": 14},
        "WORLD_CUP": {"REJUMP": 48, "WIND_KEY": 22},
        "PERFECT_V": {"REJUMP": 60, "WIND_KEY": 30},
    },
}


def main() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    base = cfg["featureEconomy"]["mysteryResultWeights"]
    if "REJUMP" in base or "WIND_KEY" in base:
        raise SystemExit("BASE already has Phase 6 keys — abort")
    fs = cfg["freeSpins"]
    if fs.get("phase6", {}).get("candidateOrigin") == "P6A1_E_E1":
        print("already promoted")
        return

    # Keep Phase 5B origin for core FS meta; Phase 6 is additive under phase6.
    fs["phase6"] = deepcopy(PHASE6)
    # economy table becomes LARGE_HILL E1 (documentation + fallback)
    lh = table_for(E1["LARGE_HILL"])
    fs["economy"]["mysteryResultWeights"] = lh
    fs["economy"]["phase5bMysteryResultWeightsArchive"] = {
        "FLIGHT_TOKEN": 752,
        "THERMAL_LIFT": 42,
        "GATE_UPGRADE": 6,
        "JUDGE": 170,
        "HEAD_JUDGE": 30,
    }
    for tier, pair in E1.items():
        table = table_for(pair)
        assert sum(table.values()) == 1000
        fs["tiers"][tier]["mysteryResultWeights"] = table
        fs["tiers"][tier]["phase6Pack"] = {"REJUMP": pair[0], "WIND_KEY": pair[1]}

    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print("promoted P6A1_E_E1")
    for tier in E1:
        print(tier, fs["tiers"][tier]["mysteryResultWeights"])


if __name__ == "__main__":
    main()
