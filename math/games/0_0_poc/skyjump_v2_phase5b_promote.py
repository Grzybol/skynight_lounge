"""Promote FS5A_U1_P2_M40_mid_E15j2 into canonical JSON without rewriting BASE bytes."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "skyjump_v2_config.json"
EXPECTED = "d932065b36a626c7cd9a818bd8c401559e6270c434622d32d1fb640e3d8d7803"

sys.path.insert(0, str(HERE))

from skyjump_v2_phase5a_reels import REEL_FAMILIES, materialize_family
from skyjump_v2_phase5a_search import ECONOMY_PROFILES

FAMILIES = {
    "LARGE_HILL": "LH_C2_Smid",
    "SKI_FLYING": "SF_C3_Smid",
    "WORLD_CUP": "WC_C4_Smid",
    "PERFECT_V": "PV_C5_Smid",
}
RULES = {
    "LARGE_HILL": {
        "persistentMysteryTargets": False,
        "guaranteedGate": False,
        "guaranteedCoach": False,
    },
    "SKI_FLYING": {
        "persistentMysteryTargets": True,
        "guaranteedGate": False,
        "guaranteedCoach": False,
    },
    "WORLD_CUP": {
        "persistentMysteryTargets": True,
        "guaranteedGate": True,
        "guaranteedCoach": False,
    },
    "PERFECT_V": {
        "persistentMysteryTargets": True,
        "guaranteedGate": True,
        "guaranteedCoach": True,
    },
}


def build_section(base_strips: list[list[str]]) -> dict:
    economy = ECONOMY_PROFILES["E_s15_j2"]
    tiers = {}
    for tier, family in FAMILIES.items():
        spec = REEL_FAMILIES[family]
        tiers[tier] = {
            "familyId": family,
            "coachPlan": {str(reel): count for reel, count in spec["coach_plan"].items()},
            "scatterPlan": {str(reel): count for reel, count in spec["scatter_plan"].items()},
            "strips": materialize_family(base_strips, family),
            "mysteryResultWeights": dict(economy["mysteryResultWeights"]),
            "tokenValueScale": economy["tokenValueScale"],
            **RULES[tier],
        }
    return {
        "version": 1,
        "candidateOrigin": "FS5A_U1_P2_M40_mid_E15j2",
        "researchOnly": False,
        "promotedFrom": "math/games/0_0_poc/phase5a_research/finalist_FS5A_U1_P2_M40_mid_E15j2_mix1000000_tier100000.json",
        "initialSpins": 10,
        "maxSpins": 40,
        "upgradeModel": "U1",
        "upgradeActivation": "NEXT_SPIN",
        "maxPersistentTargets": 2,
        "duplicateTargetBehaviour": "B",
        "duplicateTargetFallback": "if no eligible non-persistent regular remains, Coach may select an already persistent type",
        "guaranteedGatePolicy": "token_or_thermal",
        "guaranteedGatePreference": ["THERMAL_LIFT", "FLIGHT_TOKEN_T1_T4"],
        "guaranteedGateNeverReplace": ["T5", "T6", "JUDGE", "HEAD_JUDGE"],
        "maxWinX": 50000,
        "wagerCostMultiplier": 0,
        "economyId": "E_s15_j2",
        "economy": {
            "tokenValueScale": economy["tokenValueScale"],
            "mysteryResultWeights": dict(economy["mysteryResultWeights"]),
            "note": "Bonus-only. Does not replace BASE featureEconomy weights.",
        },
        "tiers": tiers,
        "reservedInactive": [
            "flightMultiplierRunUp",
            "flightMultiplierTakeoff",
            "flightMultiplierFlight",
            "rejumpState",
            "WIND_KEY",
            "FLIGHT_MULTIPLIER",
            "SPECIAL_WORLD_RECORD",
        ],
    }


def restore_certified_base() -> None:
    import subprocess

    blob_id = subprocess.check_output(
        ["git", "rev-parse", "HEAD:math/games/0_0_poc/skyjump_v2_config.json"],
        text=True,
    ).strip()
    blob = subprocess.check_output(["git", "cat-file", "blob", blob_id])
    print("blob", hashlib.sha256(blob).hexdigest(), "len", len(blob), "cr", blob.count(b"\r\n"))
    if hashlib.sha256(blob).hexdigest() != EXPECTED:
        crlf = blob.replace(b"\n", b"\r\n")
        if hashlib.sha256(crlf).hexdigest() == EXPECTED:
            blob = crlf
        else:
            raise SystemExit("HEAD config is not the certified BASE blob")
    CONFIG.write_bytes(blob)


def main() -> None:
    raw = CONFIG.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        restore_certified_base()
        raw = CONFIG.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED:
        raise SystemExit(f"BASE hash mismatch before promote: {digest}")
    if b"\r\n" not in raw:
        raise SystemExit("expected CRLF canonical config")
    text = raw.decode("utf-8")
    parsed = json.loads(text)
    if "freeSpins" in parsed:
        raise SystemExit("freeSpins already present")
    section = build_section(parsed["reelModel"]["strips"])
    payload = json.dumps(section, indent=2).replace("\n", "\r\n")
    payload = payload.replace("\r\n", "\r\n  ")
    stripped = raw.rstrip(b"\r\n")
    if not stripped.endswith(b"}"):
        raise SystemExit("unexpected ending")
    prefix = stripped[:-1].rstrip()
    updated = prefix + b",\r\n  \"freeSpins\": " + payload.encode("utf-8") + b"\r\n}\r\n"
    CONFIG.write_bytes(updated)
    after = json.loads(CONFIG.read_text(encoding="utf-8"))
    for key, value in parsed.items():
        if after[key] != value:
            raise SystemExit(f"BASE key changed: {key}")
    # Every original byte except the final closing brace remains a prefix.
    original_prefix = raw[: raw.rfind(b"}")]
    if not updated.startswith(original_prefix.rstrip()):
        raise SystemExit("BASE byte prefix was not preserved")
    print("promoted", after["freeSpins"]["candidateOrigin"])
    print("file sha", hashlib.sha256(CONFIG.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
