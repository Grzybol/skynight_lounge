"""Phase 6C freeze snapshot — measurement only; does not mutate live config."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from skyjump_v2_lines import load_v2_config

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase6c_research"
BASELINE_MEAN = 27.45472
BASE_RTP = 71.212
PHASE5_FS_PP = 17.92705
TARGET = 96.50


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    OUT.mkdir(exist_ok=True)
    cfg_path = HERE / "skyjump_v2_config.json"
    raw = cfg_path.read_bytes()
    cfg = json.loads(raw.decode("utf-8"))
    phase6 = cfg["freeSpins"]["phase6"]
    archive = cfg["freeSpins"]["economy"]["phase5bMysteryResultWeightsArchive"]
    tiers = {
        tier: dict(cfg["freeSpins"]["tiers"][tier]["mysteryResultWeights"])
        for tier in ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
    }
    payload = {
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "branch": "feat/skyjump-v2-5x5",
        "purpose": "Phase 6C certification freeze — do not mutate",
        "liveConfigSha256": sha256_bytes(raw),
        "baseMystery": dict(cfg["featureEconomy"]["mysteryResultWeights"]),
        "phase5bArchive": dict(archive),
        "phase5bOrigin": cfg["freeSpins"]["economy"].get("phase5bCandidateOrigin"),
        "phase6": {
            "enabled": phase6.get("enabled"),
            "candidateOrigin": phase6.get("candidateOrigin"),
            "rejumpArch": phase6.get("rejumpArch"),
            "windArch": phase6.get("windArch"),
            "ladder": phase6.get("ladder"),
            "stageRule": phase6.get("stageRule"),
            "saturation": phase6.get("saturation"),
            "perfectV": phase6.get("perfectV"),
            "maxRejumpsPerSpin": phase6.get("maxRejumpsPerSpin"),
            "maxFeatureChainDepth": phase6.get("maxFeatureChainDepth"),
            "packs": phase6.get("packs"),
        },
        "e1TablesByTier": tiers,
        "tableSums": {t: sum(w.values()) for t, w in tiers.items()},
        "reducerEventSchemaVersion": 2,
        "references": {
            "phase5bWeightedCoreMeanX": BASELINE_MEAN,
            "baseRtp": BASE_RTP,
            "phase5bFsPp": PHASE5_FS_PP,
            "gameBeforePhase6": BASE_RTP + BASELINE_MEAN * 0.00652967825443787 * 100.0,
            "targetRtp": TARGET,
            "researchE1IncrementalPp": 5.194785765879253,
            "researchE1MeanX": 35.4103735,
            "live6b1MIncrementalPp": 5.854260089219676,
            "live6bPairedIncrementalPp": 5.856720145502035,
        },
        "phase6bPySha256": sha256_bytes((HERE / "skyjump_v2_phase6b.py").read_bytes()),
        "phase5aEnginePySha256": sha256_bytes((HERE / "skyjump_v2_phase5a_engine.py").read_bytes()),
    }
    # Sanity: must match promoted E1
    assert phase6["candidateOrigin"] == "P6A1_E_E1"
    assert phase6["stageRule"] == "W2_CHARGE_PRIORITY"
    assert all(s == 1000 for s in payload["tableSums"].values())
    assert "REJUMP" not in payload["baseMystery"]
    path = OUT / "freeze.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(path), "liveConfigSha256": payload["liveConfigSha256"]}, indent=2))


if __name__ == "__main__":
    main()
