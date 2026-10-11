"""Assemble reviewed Garden Bounty ComfyUI outputs without touching miner assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps


FRAMES = {
    "H1": ("h1.webp", (0, 0)),
    "H2": ("h2.webp", (200, 0)),
    "H3": ("h3.webp", (400, 0)),
    "H4": ("h4.webp", (600, 0)),
    "H5": ("h5.webp", (0, 200)),
    "L1": ("l1.webp", (200, 200)),
    "L2": ("l2.webp", (400, 200)),
    "L3": ("l3.webp", (600, 200)),
    "L4": ("l4.webp", (0, 400)),
    "W": ("w.png", (200, 400)),
    "EXPLODED_W": ("explodedW.png", (400, 400)),
    "S": ("s.png", (600, 400)),
    "M2": ("m1_2x.png", (0, 600)),
    "M4": ("m1_4x.png", (200, 600)),
    "M5": ("m2_5x.png", (400, 600)),
    "M7": ("m2_7x.png", (600, 600)),
    "M10": ("m3_10x.png", (0, 800)),
}

GENERATED_SYMBOLS = {
    "H1",
    "H2",
    "H3",
    "L1",
    "L2",
    "L3",
    "L4",
    "W",
    "S",
    "M2",
    "M4",
    "M5",
    "M7",
    "M10",
}


def latest_symbol(alpha_directory: Path, symbol: str) -> Path:
    matches = sorted(
        alpha_directory.glob(f"{symbol}_alpha_*.png"),
        key=lambda path: path.stat().st_mtime,
    )
    if not matches:
        raise FileNotFoundError(f"No alpha output found for {symbol} in {alpha_directory}")
    return matches[-1]


def fit_symbol(source: Image.Image) -> Image.Image:
    source = source.convert("RGBA")
    alpha_bbox = source.getchannel("A").getbbox()
    if alpha_bbox:
        source = source.crop(alpha_bbox)
    fitted = ImageOps.contain(source, (188, 188), Image.Resampling.LANCZOS)
    cell = Image.new("RGBA", (200, 200))
    cell.alpha_composite(fitted, ((200 - fitted.width) // 2, (200 - fitted.height) // 2))
    return cell


def assemble(args: argparse.Namespace) -> None:
    atlas_source = Image.open(args.miner_atlas).convert("RGBA")
    atlas = Image.new("RGBA", (800, 1000))

    for symbol, (_, position) in FRAMES.items():
        if symbol == "EXPLODED_W":
            cell = fit_symbol(Image.open(latest_symbol(args.alpha_directory, "W")))
        elif symbol in GENERATED_SYMBOLS:
            cell = fit_symbol(Image.open(latest_symbol(args.alpha_directory, symbol)))
        else:
            x, y = position
            cell = atlas_source.crop((x, y, x + 200, y + 200))
        atlas.alpha_composite(cell, position)

    args.output_directory.mkdir(parents=True, exist_ok=True)
    atlas.save(args.output_directory / "symbolsGarden.png")
    atlas.save(
        args.output_directory / "symbolsGarden.webp",
        "WEBP",
        lossless=True,
        method=6,
    )

    atlas_json = json.loads(args.miner_json.read_text(encoding="utf-8"))
    atlas_json["meta"]["app"] = "Codex local Garden Bounty ComfyUI pipeline"
    atlas_json["meta"]["image"] = "symbolsGarden.webp"
    (args.output_directory / "symbolsGarden.json").write_text(
        json.dumps(atlas_json, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.background:
        background = Image.open(args.background).convert("RGB")
        background.save(args.output_directory / "garden_base_drawn.png")
        background.save(
            args.output_directory / "garden_base_drawn.webp",
            "WEBP",
            quality=92,
            method=6,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alpha-directory", type=Path, required=True)
    parser.add_argument("--background", type=Path)
    parser.add_argument(
        "--miner-atlas",
        type=Path,
        default=Path(
            "frontend/apps/poc/static/assets/sprites/symbolsStatic/symbolsStatic.png"
        ),
    )
    parser.add_argument(
        "--miner-json",
        type=Path,
        default=Path(
            "frontend/apps/poc/static/assets/sprites/symbolsStatic/symbolsStatic.json"
        ),
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path(
            "frontend/apps/poc/static/assets/sprites/symbolsGardenCandidate"
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    assemble(parse_args())
