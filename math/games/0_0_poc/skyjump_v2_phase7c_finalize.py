"""Phase 7C finalize: promote buyModes, bump mathVersion, write fingerprint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESEARCH = HERE / "phase7c_research"
LIBRARY = HERE / "library_v2" / "publish_files"
CFG_PATH = HERE / "skyjump_v2_config.json"
MODES = ("BASE", "LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
TIERS = ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((RESEARCH / "books_report.json").read_text(encoding="utf-8"))
    buy = json.loads((RESEARCH / "buy_ev.json").read_text(encoding="utf-8"))
    cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))

    # Cross-mode / ceiling gates
    rtps = {m: report["modes"][m]["lutRtp"] for m in MODES}
    spread = (max(rtps.values()) - min(rtps.values())) * 100.0
    if any(r > 0.967 + 1e-12 for r in rtps.values()):
        raise SystemExit(f"ceiling fail: {rtps}")
    if spread > 0.50 + 1e-9:
        raise SystemExit(f"spread fail: {spread}")

    costs = report["costs"]
    player_names = {
        "BASE": "Base",
        "LARGE_HILL": "Large Hill",
        "SKI_FLYING": "Ski Flying",
        "WORLD_CUP": "World Cup",
        "PERFECT_V": "Perfect V",
    }
    cfg["buyModes"] = {
        "BASE": {
            "id": "base",
            "rgsKey": "BASE",
            "label": player_names["BASE"],
            "playerName": player_names["BASE"],
            "costMultiplier": 1.0,
            "maxWin": 50000,
            "enabled": True,
            "type": "default",
            "rtp": round(rtps["BASE"] * 100, 4),
        }
    }
    for tier in TIERS:
        cfg["buyModes"][tier] = {
            "id": tier.lower(),
            "rgsKey": tier,
            "label": player_names[tier],
            "playerName": player_names[tier],
            "costMultiplier": float(costs[tier]),
            "maxWin": 50000,
            "enabled": True,
            "type": "buy",
            "startsBonusTier": tier,
            "rtp": round(rtps[tier] * 100, 4),
        }

    prev = int(cfg["meta"]["mathVersion"])
    new_ver = max(2, prev + 1) if prev < 2 else prev
    # First production freeze → mathVersion 2
    if prev == 1:
        new_ver = 2
    cfg["meta"]["mathVersion"] = new_ver
    cfg["meta"]["previousMathVersion"] = prev
    cfg["meta"]["mathStatus"] = "PHASE 7C PRODUCTION MATH FROZEN"
    cfg["meta"]["note"] = (
        f"Phase 7C production math freeze. mathVersion {new_ver}. "
        f"PT2H_LADDER + BODY1 + WR-C H2. Buy costs from LUT means. "
        f"BASE LUT RTP {rtps['BASE']*100:.4f}%."
    )
    cfg["meta"]["productionBooks"] = True

    CFG_PATH.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    fingerprint = {
        "mathVersion": new_ver,
        "previousMathVersion": prev,
        "configSha256": sha_file(CFG_PATH),
        "semanticEconomySha256PreBuyModes": None,
        "costs": costs,
        "lutRtp": {m: rtps[m] * 100 for m in MODES},
        "crossModeSpreadPp": spread,
        "books": {m: report["modes"][m]["shaBook"] for m in MODES},
        "luts": {m: report["modes"][m]["shaLut"] for m in MODES},
        "bookCounts": {m: report["modes"][m]["bookCount"] for m in MODES},
        "effectiveWrP_BASE": report["modes"]["BASE"]["effectiveWrP"],
        "staging": report.get("staging"),
        "buyEvSeed": {
            "nPerTier": buy.get("nPerTier"),
            "pricedFrom": buy.get("pricedFrom"),
        },
        "h2Unchanged": True,
        "wrScale": cfg["worldRecord"].get("globalScale") or cfg["worldRecord"].get("c"),
    }
    # Also record pre-bump economy SHA from freeze artifact
    freeze = json.loads((RESEARCH / "pre_cert_freeze.json").read_text(encoding="utf-8"))
    fingerprint["preCertEconomySha256"] = freeze["configSha256"]
    (RESEARCH / "production_fingerprint.json").write_text(json.dumps(fingerprint, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: fingerprint[k] for k in ("mathVersion", "lutRtp", "crossModeSpreadPp", "costs")}, indent=2))


if __name__ == "__main__":
    main()
