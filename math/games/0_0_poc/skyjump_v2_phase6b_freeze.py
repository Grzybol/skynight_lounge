"""Phase 6B pre-promotion freeze snapshot. Do not edit after promotion."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase4c_exact import config_fingerprint
from skyjump_v2_phase6a_search import table_for
from skyjump_v2_phase6a1_search import PACKS

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase6b_research" / "pre_promotion_freeze.json"

E1 = PACKS["E1"]
EXPECTED = {
    "LARGE_HILL": table_for(E1["LARGE_HILL"]),
    "SKI_FLYING": table_for(E1["SKI_FLYING"]),
    "WORLD_CUP": table_for(E1["WORLD_CUP"]),
    "PERFECT_V": table_for(E1["PERFECT_V"]),
}


def main() -> None:
    cfg_path = HERE / "skyjump_v2_config.json"
    raw = cfg_path.read_bytes()
    cfg = load_v2_config()
    base = cfg["featureEconomy"]["mysteryResultWeights"]
    fs = cfg["freeSpins"]["economy"]["mysteryResultWeights"]
    assert base == {
        "FLIGHT_TOKEN": 855,
        "THERMAL_LIFT": 42,
        "GATE_UPGRADE": 3,
        "JUDGE": 85,
        "HEAD_JUDGE": 15,
    }, "BASE mystery weights unexpectedly changed — STOP"
    assert fs == {
        "FLIGHT_TOKEN": 752,
        "THERMAL_LIFT": 42,
        "GATE_UPGRADE": 6,
        "JUDGE": 170,
        "HEAD_JUDGE": 30,
    }, "Phase 5B FS mystery weights unexpectedly changed — STOP"
    assert "REJUMP" not in base and "WIND_KEY" not in base
    assert "REJUMP" not in fs and "WIND_KEY" not in fs
    assert cfg["freeSpins"]["candidateOrigin"] == "FS5A_U1_P2_M40_mid_E15j2"
    assert int(cfg["freeSpins"]["initialSpins"]) == 10
    assert int(cfg["freeSpins"]["maxSpins"]) == 40
    assert float(cfg["freeSpins"]["maxWinX"]) == 50_000.0
    assert int(cfg["maxFeatureChainDepth"]) == 8

    payload = {
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "branch": "feat/skyjump-v2-5x5",
        "configSha256": hashlib.sha256(raw).hexdigest(),
        "baseFingerprint": config_fingerprint(cfg),
        "phase5b": {
            "candidateOrigin": cfg["freeSpins"]["candidateOrigin"],
            "weightedCoreBonusMeanX": 27.45472,
            "fsRtpContributionPp": 17.92705,
            "baseRtpPct": 71.212,
            "gameBeforePhase6Pct": 89.139,
        },
        "phase6a1E1": {
            "id": "P6A1_E_E1",
            "expectedIncrementalPp": 5.195,
            "expectedGameAfterPct": 94.334,
            "expectedReservePp": 2.166,
            "packs": E1,
            "tables": EXPECTED,
        },
        "phase4cReportSha256Prefix": hashlib.sha256(
            (HERE / "skyjump_v2_phase4c_cert_report.json").read_bytes()
        ).hexdigest()[:32],
        "status": "FREEZE_OK",
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": "FREEZE_OK", "configSha256": payload["configSha256"]}, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
