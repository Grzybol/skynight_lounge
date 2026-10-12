#!/usr/bin/env python3
"""Convert SkyJump Comfy stills to runtime WebP and chroma-key jumper plates."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

RAW = Path(r"C:\Users\grzyb\OneDrive\Dokumenty\skifly casino\docs\dev-report\skyjump-comfy-raw")
FE = Path(r"C:\Users\grzyb\OneDrive\Dokumenty\skifly casino\frontend\apps\poc\src\assets\skyjump")
REPO = Path(r"C:\Users\grzyb\OneDrive\Dokumenty\skifly casino\assets\skyjump")


def chroma(path: Path, extra_snow: bool = False) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    green = (g.astype(np.int16) > 90) & (g.astype(np.int16) > r.astype(np.int16) + 18) & (
        g.astype(np.int16) > b.astype(np.int16) + 8
    )
    teal = (b.astype(np.int16) > 70) & (g.astype(np.int16) > 90) & (r.astype(np.int16) < 90)
    mask = green | teal
    if extra_snow:
        snow = (r > 210) & (g > 220) & (b > 230)
        mask = mask | snow
    a = a.copy()
    a[mask] = 0
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")


def save_webp(im: Image.Image, *dests: Path, quality: int = 82) -> None:
    for dest in dests:
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, "WEBP", quality=quality, method=6)
        print(f"{dest} {dest.stat().st_size}")


def main() -> None:
    menu = Image.open(RAW / "menu_bg_00001_.png").convert("RGB")
    play = Image.open(RAW / "gameplay_bg_v2_00001_.png").convert("RGB")
    save_webp(menu, FE / "backgrounds/menu.webp", REPO / "backgrounds/menu.webp", quality=80)
    save_webp(play, FE / "backgrounds/gameplay.webp", REPO / "backgrounds/gameplay.webp", quality=80)

    flight = chroma(RAW / "jumper_flight_win_00001_.png")
    save_webp(flight, FE / "jumper/flight.webp", FE / "jumper/flight-win.webp", REPO / "jumper/flight.webp", REPO / "jumper/flight-win.webp", quality=86)

    menu_j = chroma(RAW / "jumper_menu_00001_.png")
    save_webp(menu_j, FE / "jumper/menu-foreground.webp", REPO / "jumper/menu-foreground.webp", quality=86)

    inrun = chroma(RAW / "jumper_inrun_00001_.png")
    save_webp(inrun, FE / "jumper/inrun.webp", REPO / "jumper/inrun.webp", quality=86)


if __name__ == "__main__":
    main()
