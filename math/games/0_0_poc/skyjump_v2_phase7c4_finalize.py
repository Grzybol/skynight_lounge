"""Phase 7C.4 finalize: promote buyModes, bump mathVersion, stage package, fingerprint."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from skyjump_v2_phase7c4_common import EXPECTED_SHA_PRE, OUT, sha_file

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LIBRARY = HERE / "library_v2_phase7c4" / "publish_files"
STAGING = REPO / "stake-upload-final" / "math"
CFG_PATH = HERE / "skyjump_v2_config.json"
V1_CFG = HERE / "skyjump_config.json"
MODES = ("BASE", "LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
TIERS = ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")

PLAYER_NAMES = {
    "BASE": "Base",
    "LARGE_HILL": "Large Hill",
    "SKI_FLYING": "Ski Flying",
    "WORLD_CUP": "World Cup",
    "PERFECT_V": "Perfect V",
}


def write_index(costs: dict) -> dict:
    modes = []
    for mode in MODES:
        modes.append(
            {
                "name": mode,
                "cost": float(costs[mode]),
                "events": f"books_{mode}.jsonl.zst",
                "weights": f"lookUpTable_{mode}_0.csv",
            }
        )
    index = {"modes": modes}
    LIBRARY.mkdir(parents=True, exist_ok=True)
    (LIBRARY / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def stage_upload() -> dict:
    STAGING.mkdir(parents=True, exist_ok=True)
    wanted = [
        "index.json",
        *[f"books_{m}.jsonl.zst" for m in MODES],
        *[f"lookUpTable_{m}_0.csv" for m in MODES],
    ]
    for name in wanted:
        src = LIBRARY / name
        if not src.exists():
            raise FileNotFoundError(src)
        dst = STAGING / name
        if dst.exists():
            dst.unlink()
        shutil.copy2(src, dst)
    allowed = set(wanted)
    for path in list(STAGING.iterdir()):
        if path.name not in allowed and path.is_file():
            path.unlink()
    leaked = [
        p.name
        for p in STAGING.rglob("*")
        if p.is_file()
        and (
            p.suffix in {".md", ".py", ".txt"}
            or (p.suffix == ".json" and p.name != "index.json")
        )
    ]
    return {"path": str(STAGING).replace("\\", "/"), "leaked": leaked, "files": wanted}


def artifact_row(rel: str, path: Path, **extra) -> dict:
    return {
        "relativePath": rel.replace("\\", "/"),
        "byteSize": path.stat().st_size,
        "sha256": sha_file(path),
        **extra,
    }


def main():
    base = json.loads((OUT / "base_lut_report.json").read_text(encoding="utf-8"))
    buy = json.loads((OUT / "buy_lut_report.json").read_text(encoding="utf-8"))
    val = json.loads((OUT / "validation_report.json").read_text(encoding="utf-8"))
    freeze = json.loads((OUT / "freeze_snapshot.json").read_text(encoding="utf-8"))

    if not base.get("pass_0_05"):
        raise SystemExit("BASE LUT gate fail")
    if not buy.get("allGatesPass"):
        raise SystemExit("buy LUT / cross-mode gate fail")
    if not val.get("pass"):
        raise SystemExit("validation gate fail")

    costs = {"BASE": 1.0, **buy["pricing"]["costs"]}
    rtps = buy["crossModeActual"]["rtpPct"]
    # Prefer actual BASE from base report
    rtps = dict(rtps)
    rtps["BASE"] = float(base["actualLutRtpPct"])

    pre_sha = sha_file(CFG_PATH)
    if pre_sha != EXPECTED_SHA_PRE:
        raise SystemExit(f"config SHA drift before promote: {pre_sha}")

    v1 = json.loads(V1_CFG.read_text(encoding="utf-8"))
    if int(v1["meta"]["mathVersion"]) != 3:
        raise SystemExit("V1 mathVersion must remain 3")

    cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    cfg["buyModes"] = {
        "BASE": {
            "id": "base",
            "rgsKey": "BASE",
            "label": PLAYER_NAMES["BASE"],
            "playerName": PLAYER_NAMES["BASE"],
            "costMultiplier": 1.0,
            "maxWin": 50000,
            "enabled": True,
            "type": "default",
            "rtp": round(rtps["BASE"], 4),
            "title": PLAYER_NAMES["BASE"],
            "dialog": "Base game",
            "description": "Base game",
            "button": "Base",
            "betAmountLabel": "Base bet",
            "tickerIdle": "SkyJump",
            "tickerSpin": "Jumping…",
        }
    }
    for tier in TIERS:
        name = PLAYER_NAMES[tier]
        cfg["buyModes"][tier] = {
            "id": tier.lower(),
            "rgsKey": tier,
            "label": name,
            "playerName": name,
            "costMultiplier": float(costs[tier]),
            "maxWin": 50000,
            "enabled": True,
            "type": "buy",
            "startsBonusTier": tier,
            "rtp": round(rtps[tier], 4),
            "title": name,
            "dialog": f"Buy {name}",
            "description": f"Start Free Spins at {name}",
            "button": name,
            "betAmountLabel": f"{name} buy",
            "tickerIdle": name,
            "tickerSpin": f"{name}…",
        }

    prev = int(cfg["meta"]["mathVersion"])
    if prev != 1:
        raise SystemExit(f"expected mathVersion 1 before freeze, got {prev}")
    new_ver = 2
    cfg["meta"]["mathVersion"] = new_ver
    cfg["meta"]["previousMathVersion"] = prev
    cfg["meta"]["mathStatus"] = "PHASE 7C.4 PRODUCTION MATH FROZEN"
    cfg["meta"]["note"] = (
        f"Phase 7C.4 production math freeze. mathVersion {new_ver}. "
        f"PT2H_LADDER + BODY1 + WR-C H2 + Phase 6 PURE W2. "
        f"BASE actual LUT RTP {rtps['BASE']:.4f}%. "
        f"Buy costs PRICE_A (grain-adjusted if required)."
    )
    cfg["meta"]["productionBooks"] = True
    CFG_PATH.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    final_sha = sha_file(CFG_PATH)

    index = write_index(costs)
    staging = stage_upload()
    if staging["leaked"]:
        raise SystemExit(f"staging leak: {staging['leaked']}")

    # Release manifest
    artifacts = []
    for mode in MODES:
        bp = STAGING / f"books_{mode}.jsonl.zst"
        lp = STAGING / f"lookUpTable_{mode}_0.csv"
        n_books = None
        if mode == "BASE":
            n_books = base["bookCount"]
        else:
            n_books = buy["lutReports"][mode]["bookCount"]
        artifacts.append(
            artifact_row(
                f"stake-upload-final/math/books_{mode}.jsonl.zst",
                bp,
                mode=mode,
                bookCount=n_books,
                mathVersion=new_ver,
                configSha=final_sha,
                lutRtp=rtps[mode],
                buyCost=costs[mode],
            )
        )
        artifacts.append(
            artifact_row(
                f"stake-upload-final/math/lookUpTable_{mode}_0.csv",
                lp,
                mode=mode,
                mathVersion=new_ver,
                configSha=final_sha,
                lutRtp=rtps[mode],
                buyCost=costs[mode],
            )
        )
    artifacts.append(
        artifact_row(
            "stake-upload-final/math/index.json",
            STAGING / "index.json",
            mathVersion=new_ver,
            configSha=final_sha,
        )
    )
    artifacts.append(
        artifact_row(
            "math/games/0_0_poc/skyjump_v2_config.json",
            CFG_PATH,
            mathVersion=new_ver,
            configSha=final_sha,
        )
    )

    manifest = {
        "phase": "7C.4",
        "classification": "PRODUCTION MATH FROZEN",
        "mathVersion": {"old": prev, "new": new_ver},
        "configSha": {"before": pre_sha, "final": final_sha},
        "economyShaPrePromote": EXPECTED_SHA_PRE,
        "freezeSnapshot": freeze,
        "finalRtpPct": rtps,
        "crossMode": buy["crossModeActual"],
        "finalBuyCosts": {t: costs[t] for t in TIERS},
        "lutVsAuthority": {
            "BASE": {
                "gapPp": base["gapPp"],
                "pass": base["pass_0_05"],
                "actualPct": base["actualLutRtpPct"],
                "authPct": base["authRtpPct"],
            },
            **{
                t: {
                    "gapPp": buy["gates"][t]["gapPp"],
                    "pass": buy["gates"][t]["pass_0_05"],
                    "actualPct": buy["gates"][t]["lutRtpPct"],
                    "authPct": buy["gates"][t]["authRtpPct"],
                }
                for t in TIERS
            },
        },
        "bookCounts": {
            "BASE": base["bookCount"],
            **{t: buy["lutReports"][t]["bookCount"] for t in TIERS},
        },
        "pvWeight": base.get("pv"),
        "wrWeight": base.get("wr"),
        "validation": {
            "pass": val.get("pass"),
            "replayPass": val.get("replayPass"),
            "grainPass": val.get("grainPass"),
            "capPass": val.get("capPass"),
            "maxObservedX": val.get("maxObservedX"),
        },
        "staging": staging,
        "index": index,
        "artifacts": artifacts,
        "devResearchLeak": "NONE" if not staging["leaked"] else "FOUND",
        "v1MathVersionUnchanged": 3,
    }
    manifest_path = HERE / "phase7c4_release_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT / "production_fingerprint.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "mathVersion": {"old": prev, "new": new_ver},
                "configSha": {"before": pre_sha, "final": final_sha},
                "costs": {t: costs[t] for t in TIERS},
                "rtp": rtps,
                "spreadPp": buy["crossModeActual"]["spreadPp"],
                "staging": staging["path"],
                "manifest": str(manifest_path).replace("\\", "/"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
