"""Phase 8C.1 — restore UI pack as PNG RGBA with alpha.

Prefer Cursor workspaceStorage true PNG masters when present.
When only Cursor JPEG (black-matte) exists, recover alpha via near-black
knockout (same pipeline as Phase 7D symbol ingest). Never ship JPEG for UI pack.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from PIL import Image, ImageChops

WS = Path(
	r"C:\Users\grzyb\AppData\Roaming\Cursor\User\workspaceStorage"
	r"\a9117ff639cfe973f8876bea5e2f20c7\images"
)
ATTACH = Path(
	r"C:\Users\grzyb\.cursor\projects\c-Users-grzyb-OneDrive-Dokumenty-skifly-casino\assets"
)
ROOT = Path(r"C:\Users\grzyb\OneDrive\Dokumenty\skifly-casino-v2")
RUNTIME = ROOT / "frontend/apps/poc/static/assets/skyjump_v2"
SOURCE = ROOT / "assets/skyjump_v2/source/ui_pack_8c"

# stem -> relative runtime dir under skyjump_v2
DEST = {
	"ui_win_big": "ui/wins",
	"ui_win_mega": "ui/wins",
	"ui_win_super": "ui/wins",
	"ui_win_max": "ui/wins",
	"ui_win_world_record": "ui/wins",
	"ui_bonus_free_spins": "ui/bonus",
	"ui_bonus_retrigger": "ui/bonus",
	"ui_bonus_tier_upgrade": "ui/bonus",
	"ui_mode_large_hill": "ui/bonus",
	"ui_mode_ski_flying": "ui/bonus",
	"ui_mode_world_cup": "ui/bonus",
	"ui_mode_perfect_v": "ui/bonus",
	"ui_header_paytable": "ui/headers",
	"ui_header_info": "ui/headers",
	"ui_header_features": "ui/headers",
	"ui_header_how_to_play": "ui/headers",
	"ui_divider_ice": "ui/decor",
	"ui_corner_ornament": "ui/decor",
	"ui_status_plate": "ui/decor",
	"ui_mode_badge_plate": "ui/decor",
	"ui_panel_topper": "ui/decor",
	"fx_payline_spark_head": "fx",
	"fx_payline_end_glint": "fx",
	"fx_ice_glint": "fx",
	"fx_snow_burst": "fx",
	"fx_win_glow_ring": "fx",
	"fx_screen_flash_accent": "fx",
	"fx_small_sparkle": "fx",
	"fx_coin_sparkle": "fx",
}


def find_best_source(stem: str) -> Path:
	candidates: list[tuple[int, int, Path]] = []
	# Prefer workspaceStorage (often keeps original PNG)
	if WS.exists():
		for p in WS.iterdir():
			if p.is_file() and p.name.startswith(f"{stem}-"):
				data = p.read_bytes()[:8]
				is_png = data.startswith(b"\x89PNG")
				# rank: PNG first, then larger
				candidates.append((0 if is_png else 1, -p.stat().st_size, p))
	# Fallback: project assets cache
	if ATTACH.exists():
		pat = re.compile(rf"images_{re.escape(stem)}-[0-9a-f]")
		for p in ATTACH.iterdir():
			if p.is_file() and pat.search(p.name):
				data = p.read_bytes()[:8]
				is_png = data.startswith(b"\x89PNG")
				candidates.append((0 if is_png else 1, -p.stat().st_size, p))
	if not candidates:
		raise FileNotFoundError(stem)
	candidates.sort()
	return candidates[0][2]


def to_png_rgba(src: Path, dest: Path, threshold: int = 18) -> str:
	"""Copy true PNG RGBA, or recover alpha from black-matte JPEG."""
	im = Image.open(src)
	data_head = src.read_bytes()[:8]
	method = "copy_png"
	if data_head.startswith(b"\x89PNG") and im.mode in ("RGBA", "LA"):
		rgba = im.convert("RGBA")
	elif data_head.startswith(b"\x89PNG") and im.mode == "P" and "transparency" in im.info:
		rgba = im.convert("RGBA")
	else:
		# JPEG / opaque PNG — knock out near-black studio matte (Phase 7D pipeline)
		method = f"black_knockout_t{threshold}"
		rgba = im.convert("RGBA")
		r, g, b, a = rgba.split()
		mask_r = Image.eval(r, lambda v: 0 if v <= threshold else 255)
		mask_g = Image.eval(g, lambda v: 0 if v <= threshold else 255)
		mask_b = Image.eval(b, lambda v: 0 if v <= threshold else 255)
		keep = ImageChops.lighter(ImageChops.lighter(mask_r, mask_g), mask_b)
		a = ImageChops.multiply(a, keep)
		rgba = Image.merge("RGBA", (r, g, b, a))

	dest.parent.mkdir(parents=True, exist_ok=True)
	rgba.save(dest, format="PNG", optimize=True)
	a = list(rgba.getchannel("A").getdata())
	zero = sum(1 for v in a if v == 0) / len(a)
	return f"{method} size={rgba.size} amin={min(a)} amax={max(a)} zero%={zero:.3f}"


def purge_old(stem: str, rel_dir: str) -> None:
	folder = RUNTIME / rel_dir
	if not folder.exists():
		return
	for p in folder.glob(f"{stem}.*"):
		if p.suffix.lower() != ".png":
			p.unlink()
			print(f"  removed stale {p.relative_to(ROOT)}")
	# also purge non-png in source
	for p in SOURCE.glob(f"{stem}.*"):
		if p.suffix.lower() != ".png":
			p.unlink()
			print(f"  removed stale source {p.name}")


def main() -> None:
	SOURCE.mkdir(parents=True, exist_ok=True)
	print(f"DEST assets: {len(DEST)}")
	for stem, rel in DEST.items():
		src = find_best_source(stem)
		purge_old(stem, rel)
		runtime_dest = RUNTIME / rel / f"{stem}.png"
		source_dest = SOURCE / f"{stem}.png"
		info = to_png_rgba(src, runtime_dest)
		shutil.copy2(runtime_dest, source_dest)
		print(f"OK {stem:28} from={src.name[:48]} -> {rel}/{stem}.png  [{info}]")
	print("DONE")


if __name__ == "__main__":
	main()
