# SKYJUMP V2 — True PNG master ingest (Phase 8C.2)

**Branch:** `feat/skyjump-v2-5x5`  
**Date:** 2026-09-26  
**Scope:** Source archive → extracted PNG masters → runtime. Math frozen. Layout unchanged.

---

## Raw source archive (immutable)

| Field | Value |
| --- | --- |
| **RAW SOURCE ARCHIVE** | `assets/skyjump_v2/source/archives/skyjump_ui_pack_final_png.zip` |
| **ARCHIVE SIZE** | 46 200 641 bytes (**44.06 MiB**) |
| **ARCHIVE SHA256** | `8E985A7A604805B90B4D38E2AC203F6CDCAE53FA1BEAF41438EF286E24CD0AB9` |
| **ARCHIVE SHA VERIFIED BEFORE EXTRACT** | **YES** |
| **PRODUCTION BUNDLE CONTAINS ZIP** | **NO** |

---

## Phase 8C.2 ingest result

| Metric | Result |
| --- | --- |
| Files found | **29/29** |
| Magic PNG | **29/29** |
| JPEG | **0/29** |
| RGBA with α min=0 | **29/29** |
| Ingest | **PASS** |
| Source ↔ runtime SHA256 match | **29/29** |
| Black-knockout versions active | **NONE** (replaced) |
| Registry changed | **NO** |
| Layout / live-preview harness | **unchanged** (1280×720 preserved) |

Extraction was from the committed ZIP only (no Cursor chat attachments, no workspaceStorage, no knockout reconstruction).

---

## Extracted masters

`assets/skyjump_v2/source/ui_pack_8c/*.png` — filenames preserved exactly.

## Runtime paths

Under `frontend/apps/poc/static/assets/skyjump_v2/`:

| Category | Path |
| --- | --- |
| Wins | `ui/wins/` |
| Bonus / mode | `ui/bonus/` |
| Headers | `ui/headers/` |
| Decor | `ui/decor/` |
| FX | `fx/` |

---

## 29-file audit (ZIP members → runtime)

| File | Magic | Size | Mode | α min–max | SHA256 (prefix) |
| --- | --- | --- | --- | --- | --- |
| fx_coin_sparkle.png | PNG | 1254×1254 | RGBA | 0–255 | `499d97eb39ece710…` |
| fx_ice_glint.png | PNG | 1254×1254 | RGBA | 0–255 | `e163cb1e2f80a4d8…` |
| fx_payline_end_glint.png | PNG | 1254×1254 | RGBA | 0–254 | `3f3aaf63805745c7…` |
| fx_payline_spark_head.png | PNG | 1254×1254 | RGBA | 0–254 | `96fd9fe5df845d4a…` |
| fx_screen_flash_accent.png | PNG | 1672×941 | RGBA | 0–255 | `be210ce019b0a9f5…` |
| fx_small_sparkle.png | PNG | 1254×1254 | RGBA | 0–255 | `a84475442464060c…` |
| fx_snow_burst.png | PNG | 1254×1254 | RGBA | 0–255 | `42d85fc9cd098937…` |
| fx_win_glow_ring.png | PNG | 1254×1254 | RGBA | 0–253 | `33b7dea5ebd64992…` |
| ui_bonus_free_spins.png | PNG | 1774×887 | RGBA | 0–255 | `088952102a21abb6…` |
| ui_bonus_retrigger.png | PNG | 1774×887 | RGBA | 0–255 | `064148af2821dc7d…` |
| ui_bonus_tier_upgrade.png | PNG | 1774×887 | RGBA | 0–255 | `2df71665f05c5a4b…` |
| ui_corner_ornament.png | PNG | 1254×1254 | RGBA | 0–255 | `6881054e21aa5ea7…` |
| ui_divider_ice.png | PNG | 2172×724 | RGBA | 0–255 | `bfcd6d5ba5df3f0e…` |
| ui_header_features.png | PNG | 1774×887 | RGBA | 0–255 | `3f1ddf46db6681a0…` |
| ui_header_how_to_play.png | PNG | 1774×887 | RGBA | 0–255 | `7fd971923ccc7f3c…` |
| ui_header_info.png | PNG | 1774×887 | RGBA | 0–255 | `a652afaff4ac0714…` |
| ui_header_paytable.png | PNG | 1774×887 | RGBA | 0–255 | `341ee4db5eeae412…` |
| ui_mode_badge_plate.png | PNG | 2172×724 | RGBA | 0–255 | `8c59ea32d5c8fd8c…` |
| ui_mode_large_hill.png | PNG | 1774×887 | RGBA | 0–255 | `ea0498626249221b…` |
| ui_mode_perfect_v.png | PNG | 1774×887 | RGBA | 0–255 | `d2be4577605e7e2f…` |
| ui_mode_ski_flying.png | PNG | 1774×887 | RGBA | 0–255 | `a7283184d4c8e8e3…` |
| ui_mode_world_cup.png | PNG | 1774×887 | RGBA | 0–255 | `ad572bd1e6f560c9…` |
| ui_panel_topper.png | PNG | 2172×724 | RGBA | 0–255 | `593fedbb87deb225…` |
| ui_status_plate.png | PNG | 2172×724 | RGBA | 0–255 | `dca71e7800f7d2a1…` |
| ui_win_big.png | PNG | 1774×887 | RGBA | 0–255 | `ffd67e9dc9873c06…` |
| ui_win_max.png | PNG | 1774×887 | RGBA | 0–255 | `23f7671d4c63a676…` |
| ui_win_mega.png | PNG | 1774×887 | RGBA | 0–255 | `06cfb64dbccb34dd…` |
| ui_win_super.png | PNG | 1774×887 | RGBA | 0–255 | `9bf60cc60f1c0e15…` |
| ui_win_world_record.png | PNG | 1774×887 | RGBA | 0–255 | `4ad4e2b2c7f2894e…` |

Corner-sample check on headers/wins/decor/FX: **no opaque black-matte corners** (α=0 outside content). Soft glow fringes are true partial alpha — Filip confirms visually via DEV Assets → Checkerboard / White / Navy.

---

## Historical note

Phase 8C.1 black-knockout / Cursor-JPEG derivatives are **no longer active** for these 29 assets. Prior docs remain as history.

---

## Build

Production `npm run build` after ingest: **PASS** (commit `0dd767a`).
Vite left running: `/live-preview` and `/dev-preview` on port 3011.
