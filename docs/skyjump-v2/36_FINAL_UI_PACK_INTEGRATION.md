# SKYJUMP V2 — Final UI pack integration (Phase 8C)

**Branch:** `feat/skyjump-v2-5x5`  
**Date:** 2026-09-26  
**Scope:** Frontend presentation only. Math frozen.

---

## Attachment inventory

| Metric | Result |
| --- | --- |
| Expected | 29 |
| Found | **29/29** |
| Missing | none |
| Duplicate filenames | none |
| Byte-identical among 29 | **none** |

**Phase 8C.1 (current):** all 29 runtime + source masters are **`.png` RGBA**. Registry maps every Phase 8C key → `.png` only. Do **not** treat the pack as “mostly `.jpg`” — that described the broken Phase 8C import before repair.

### Phase 8C.1 — why assets looked black / “mostly JPG”

| Symptom | Root cause |
| --- | --- |
| **BLACK BACKGROUND** | Cursor chat attachment cache + the Phase 8C copy preserved JPEG RGB with a black studio matte. Some files named `.png` were still JPEG magic bytes. Five true PNG RGBA masters existed in Cursor `workspaceStorage` (`ui_divider_ice`, `ui_corner_ornament`, `ui_panel_topper`, `fx_payline_spark_head`, `fx_coin_sparkle`) but were overwritten by degraded JPEG copies during the Phase 8C import. Paytable / Info “black rectangles” were **opaque black JPEG matte in the image bytes**, not a CSS background bug. |
| **MOSTLY JPG** | Phase 8C importer copied Cursor attachment filenames/bytes as-is, without the Phase 7D PNG+alpha knockout pipeline. The integration report trusted file extensions instead of magic / alpha. |

### Repair

- Tool: `tools/skyjump/ingest_ui_pack_8c1.py`
- Prefer true PNG from Cursor `workspaceStorage` when available
- For JPEG-only masters: near-black knockout (`t=18`) → PNG RGBA (same idea as Phase 7D symbol ingest)
- Purge stale `.jpg` runtime/source copies; registry all `.png`

Visibility / consumer wiring: see `36A_UI_ASSET_VISIBILITY_MATRIX.md`.

---

## Runtime paths

| Category | Path under `frontend/apps/poc/static/assets/skyjump_v2/` |
| --- | --- |
| Win titles | `ui/wins/` |
| Bonus / mode titles | `ui/bonus/` |
| Menu headers | `ui/headers/` |
| Decor | `ui/decor/` |
| FX sprites | `fx/` |
| Masters copy | `assets/skyjump_v2/source/ui_pack_8c/` |

---

## Registry

`frontend/apps/poc/src/game/skyjump_v2/uiAssetRegistry.ts`

- `v2UiAssetUrl` / `v2FxAssetUrl` / `v2ModeTitleUrl` / `V2_WIN_TITLE_URLS`
- All consumers resolve through this module (board, paytable, rules, celebration, decor)
- Phase 8C.1: every Phase 8C pack path ends in `.png` (no JPEG runtime UI pack)

**UI REGISTRY: PASS**

---

## Typography

| Role | Family | Source |
| --- | --- | --- |
| Display | Oxanium → `SkyjumpDisplay` | local woff2 |
| UI / numbers | Inter → `SkyjumpUI` | local woff2 |

Local only: **YES**  
External font requests: **ZERO** (no Typekit / Google Fonts in `app.html` or font CSS)

---

## Win tier authority

| Title | Authority |
| --- | --- |
| WORLD RECORD | Explicit `skyjumpWorldRecord` / `worldRecordActive` |
| MAX WIN | Cap / max-win semantics (`capHit` / `skyjumpV2CapReached`) |
| SUPER / MEGA / BIG | **Presentation-only** stake multiples in `winPresentation.ts` |

Thresholds (visual only, never alter payout/RTP):

- BIG ≥ **10×**
- MEGA ≥ **50×**
- SUPER ≥ **200×**

Count-up displays authoritative book/event amount; animation is cosmetic.

**WORLD RECORD / MAX WIN conflict:** WR title wins when `worldRecord` is set; MAX title only when cap without WR. Both may log economically; WR is the dominant celebration title.

---

## Implemented FX / UI

| Item | Status |
| --- | --- |
| Win celebration overlay | `SkyJumpV2WinCelebration.svelte` |
| Glow ring / snow / sparkles / flash / coin | code-driven layers |
| Payline spark head + end glint | SVG `<image>` on progressive path |
| Status plate | `SkyJumpV2StatusPlate.svelte` |
| Mode badge | `SkyJumpV2ModeBadge.svelte` |
| Bonus / mode title banners | `SkyJumpV2TitleBanner` + `skyjumpV2BonusTitles` |
| Paytable / Info headers + panel decor | wired |

---

## Remaining art debt

| Item | Status |
| --- | --- |
| `ui_tier_large_hill.png` ≡ `ui_tier_ski_flying.png` | **STILL PRESENT** (HUD emblems — not replaced by mode title banners) |

---

## DEV

- Asset gallery: DEV inspector → **Assets** toggle (`SkyJumpV2AssetGallery`) — not in `Game.svelte`
- Scenarios include UI PACK SHOWCASE, BIG/MEGA/SUPER/MAX/WR showcase, FS / Retrigger / Tier Upgrade / mode titles, Paytable/Info modals, plus book fixtures (`bonus-01` / `bonus-05` / `bonus-06`, `wr-01`, `feature-17`)
- Checkerboard / White / Navy backgrounds in Assets inspector for alpha QA after 8C.1

---

## Manual / responsive

Spot-check still required by Filip at 1920 / 1280 / 960 / 640 and mobile landscape for celebration framing and long amounts.

---

## Math

**Unchanged.** No edits to books, LUTs, RTP, buy costs, or `mathVersion`.
