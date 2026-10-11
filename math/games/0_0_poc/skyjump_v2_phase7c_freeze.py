"""Phase 7C pre-certification freeze snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from skyjump_v2_lines import load_v2_config

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c_research" / "pre_cert_freeze.json"
EXPECTED = "d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0"


def main() -> None:
    cfg_path = HERE / "skyjump_v2_config.json"
    raw = cfg_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    cfg = load_v2_config()
    if sha != EXPECTED:
        raise SystemExit(f"STOP: config SHA {sha} != expected 7B {EXPECTED}")

    wr = cfg["worldRecord"]
    fs = cfg["freeSpins"]
    freeze = {
        "configSha256": sha,
        "expectedSha256": EXPECTED,
        "match": True,
        "meta": {
            "mathVersion": cfg["meta"]["mathVersion"],
            "featureEconomyVersion": cfg["meta"].get("featureEconomyVersion"),
            "economyCandidate": cfg["meta"].get("economyCandidate"),
            "paytableCandidate": cfg["meta"].get("paytableCandidate"),
            "bonusBodyCandidate": cfg["meta"].get("bonusBodyCandidate"),
            "worldRecordCandidate": cfg["meta"].get("worldRecordCandidate"),
        },
        "paytable": {
            "candidateOrigin": cfg["paytable"]["candidateOrigin"],
            "awardsP1": cfg["paytable"]["awards"]["P1"],
        },
        "body": {
            "candidateOrigin": cfg["flightTokens"].get("candidateOrigin"),
            "tierWeights": {k: v["weight"] for k, v in cfg["flightTokens"]["tiers"].items()},
            "vw1": cfg["flightTokens"]["valueWeights"]["1"],
            "vw2": cfg["flightTokens"]["valueWeights"]["2"],
            "vw5": cfg["flightTokens"]["valueWeights"]["5"],
            "vw6": cfg["flightTokens"]["valueWeights"]["6"],
        },
        "worldRecord": {
            "architecture": wr["architecture"],
            "candidateOrigin": wr["candidateOrigin"],
            "c": wr["c"],
            "byTierPSpin": wr["byTierPSpin"],
            "tierRelativeIntensity": wr["tierRelativeIntensity"],
            "targetWrPp": wr.get("targetWrPp"),
        },
        "phase6": {
            "candidateOrigin": fs["phase6"]["candidateOrigin"],
            "rejumpArch": fs["phase6"].get("rejumpArch"),
            "windArch": fs["phase6"].get("windArch"),
            "stageRule": fs["phase6"].get("stageRule"),
            "ladder": fs["phase6"].get("ladder"),
            "maxRejumpsPerSpin": fs["phase6"]["maxRejumpsPerSpin"],
            "maxFeatureChainDepth": fs["phase6"]["maxFeatureChainDepth"],
            "packs": fs["phase6"]["packs"],
        },
        "freeSpins": {
            "candidateOrigin": fs["candidateOrigin"],
            "initialSpins": fs["initialSpins"],
            "maxSpins": fs["maxSpins"],
            "maxPersistentTargets": fs["maxPersistentTargets"],
            "maxWinX": fs.get("maxWinX"),
            "upgradeModel": fs["upgradeModel"],
        },
        "featureEconomy": {
            "maxWinX": cfg["featureEconomy"]["maxWinX"],
            "gateMaxFloor": cfg["featureEconomy"]["gateMaxFloor"],
        },
        "eventSchemaVersion": cfg["eventSchemaVersion"],
        "board": cfg["board"],
        "projectedPreBookRtp": 96.290,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "sha": sha, "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
