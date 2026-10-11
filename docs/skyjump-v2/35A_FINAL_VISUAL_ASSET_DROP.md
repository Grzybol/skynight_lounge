# SkyJump V2 — Final visual asset drop-in

**Date:** 2026-09-25  
**Branch:** `feat/skyjump-v2-5x5`  
**Scope:** Visual PNG integration only. Math frozen (`mathVersion: 2`).

## Attachments inventory

| | Count |
| --- | --- |
| FOUND (canonical) | **33 / 34** |
| MISSING | `sym_feat_head_judge.png` |
| DUPLICATE CONTENT | `ui_tier_large_hill.png` ≡ `ui_tier_ski_flying.png` (identical source bytes in the supplied pack) |
| UNEXPECTED | none for this pack |
| WRONG_FILENAME | none (Cursor cache used long UUID names; mapped by canonical stem) |

Attachments arrived as JPEG RGB on black; ingest converted to PNG RGBA with near-black knocked to alpha (`tools/skyjump/ingest_v2_visual_pack.py`).

## Runtime paths

| Set | Path |
| --- | --- |
| 24 reel/feature/token symbols | `frontend/apps/poc/static/assets/skyjump_v2/symbols/` |
| 8 UI (logo/stages/tiers) | `frontend/apps/poc/static/assets/skyjump_v2/ui/` |
| WR overlay | `frontend/apps/poc/static/assets/skyjump_v2/overlays/ui_overlay_world_record.png` |
| Masters | `assets/skyjump_v2/source/{symbols,ui,overlays}/` |

## Registry

- Symbols: `symbolAssetRegistry.ts` (unchanged keys; PNGs now load)
- UI: new `uiAssetRegistry.ts`
- T6 token ≠ SPECIAL_WORLD_RECORD (distinct PNG hashes)
- Head Judge: registry still points at `sym_feat_head_judge.png` → CSS placeholder until Filip supplies art

## Wiring

- Board cells: final PNG via existing registry + CODE_FX overlays (token values, Thermal ×N)
- Flight Multiplier HUD: stage icons + dynamic values/charges
- Bonus banner: tier emblem from event `bonusHud.tier`
- WR: decorative overlay + dynamic WORLD RECORD / win × text
- Logo: `SkyJumpBrand.svelte` + menu (`SkyJumpMainMenu.svelte`) with accessible text fallback

## Presentation

Shared `object-fit: contain` on symbols (inset 4%). No per-symbol size hacks.

## Remaining visual issues

1. **Head Judge** still placeholder.
2. **Large Hill / Ski Flying** emblems are byte-identical — need a distinct Ski Flying master from Filip.
3. Source pack was JPEG; alpha is approximate (near-black threshold). If fringe halos appear, remaster as true PNG RGBA.

## Math

Unchanged. Config blob hash verified in `tools/skyjump/test-v2-visual-pack.ts`.

## Tests / build

See commit message / CI output for this drop.
