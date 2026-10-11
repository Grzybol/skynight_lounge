"""One-shot ingest of Filip's SkyJump V2 visual pack from Cursor attachment cache."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageChops

ATTACH = Path(
    r"C:\Users\grzyb\.cursor\projects\c-Users-grzyb-OneDrive-Dokumenty-skifly-casino\assets"
)
ROOT = Path(r"C:\Users\grzyb\OneDrive\Dokumenty\skifly-casino-v2")
RUNTIME_SYM = ROOT / "frontend/apps/poc/static/assets/skyjump_v2/symbols"
RUNTIME_UI = ROOT / "frontend/apps/poc/static/assets/skyjump_v2/ui"
RUNTIME_OV = ROOT / "frontend/apps/poc/static/assets/skyjump_v2/overlays"
SRC_SYM = ROOT / "assets/skyjump_v2/source/symbols"
SRC_UI = ROOT / "assets/skyjump_v2/source/ui"
SRC_OV = ROOT / "assets/skyjump_v2/source/overlays"

SYMBOLS = [
    "sym_p1_flying_jumper.png",
    "sym_p2_crystal_trophy.png",
    "sym_p3_golden_helmet.png",
    "sym_m1_jumping_skis.png",
    "sym_m2_flight_goggles.png",
    "sym_m3_ski_boots.png",
    "sym_l1_wind_sock.png",
    "sym_l2_snow_badge.png",
    "sym_l3_start_flag.png",
    "sym_s_competition_bib.png",
    "sym_c_coach_signal.png",
    "sym_y_snowburst_mystery.png",
    "sym_feat_thermal_lift.png",
    "sym_feat_gate_upgrade.png",
    "sym_feat_judge.png",
    "sym_feat_head_judge.png",
    "sym_feat_rejump.png",
    "sym_feat_wind_key.png",
    "sym_feat_special_world_record.png",
    "sym_token_t1_rookie.png",
    "sym_token_t2_k_point.png",
    "sym_token_t3_large_hill.png",
    "sym_token_t4_ski_flying.png",
    "sym_token_t5_world_cup.png",
    "sym_token_t6_token_world_record.png",
]
UI = [
    "ui_logo_skyjump.png",
    "ui_stage_run_up.png",
    "ui_stage_takeoff.png",
    "ui_stage_flight.png",
    "ui_tier_large_hill.png",
    "ui_tier_ski_flying.png",
    "ui_tier_world_cup.png",
    "ui_tier_perfect_v.png",
]
OVERLAY = ["ui_overlay_world_record.png"]
EXPECTED = SYMBOLS + UI + OVERLAY


def stem_key(name: str) -> str | None:
    for canon in EXPECTED:
        base = canon[:-4]
        markers = (
            f"images_{base}-",
            f"images_{base}.",
            f"_{base}-",
            f"_{base}.",
        )
        if any(m in name for m in markers) or name.startswith(base):
            return canon
    return None


def to_png_rgba(src: Path, dest: Path, threshold: int = 18) -> None:
    im = Image.open(src).convert("RGBA")
    # Knock out near-black studio background (Cursor JPEG exports).
    bands = im.split()
    r, g, b, a = bands
    mask = Image.eval(r, lambda v: 0 if v <= threshold else 255)
    mask_g = Image.eval(g, lambda v: 0 if v <= threshold else 255)
    mask_b = Image.eval(b, lambda v: 0 if v <= threshold else 255)
    # Keep pixel only if any channel is above threshold
    keep = ImageChops.lighter(ImageChops.lighter(mask, mask_g), mask_b)
    a = ImageChops.multiply(a, keep)
    im = Image.merge("RGBA", (r, g, b, a))
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, format="PNG", optimize=True)


def main() -> None:
    found: dict[str, Path] = {}
    unexpected: list[str] = []
    for f in ATTACH.iterdir():
        if not f.is_file():
            continue
        key = stem_key(f.name)
        if key:
            prev = found.get(key)
            if prev is None or f.stat().st_size >= prev.stat().st_size:
                found[key] = f
        elif any(x in f.name for x in ("sym_", "ui_logo", "ui_stage", "ui_tier", "ui_overlay")):
            unexpected.append(f.name)

    missing = [c for c in EXPECTED if c not in found]
    print(f"FOUND {len(found)}/34")
    print("MISSING", missing)
    print("UNEXPECTED", unexpected)

    for d in (RUNTIME_SYM, RUNTIME_UI, RUNTIME_OV, SRC_SYM, SRC_UI, SRC_OV):
        d.mkdir(parents=True, exist_ok=True)

    for canon, src in sorted(found.items()):
        if canon in SYMBOLS:
            rt, master = RUNTIME_SYM / canon, SRC_SYM / canon
        elif canon in UI:
            rt, master = RUNTIME_UI / canon, SRC_UI / canon
        else:
            rt, master = RUNTIME_OV / canon, SRC_OV / canon
        to_png_rgba(src, rt)
        shutil.copy2(rt, master)
        print(f"OK {canon} ({rt.stat().st_size} bytes)")

    print(f"COPIED {len(found)}")
    print(f"STILL_MISSING {missing}")


if __name__ == "__main__":
    main()
