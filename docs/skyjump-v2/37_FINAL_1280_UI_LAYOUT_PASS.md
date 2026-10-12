# SKYJUMP V2 — Phase 8D Final 1280×720 UI Layout Pass

**Branch:** `feat/skyjump-v2-5x5`  
**Date:** 2026-09-26  
**Primary target:** `/live-preview` logical stage **1280×720**  
**Math:** frozen (unchanged) · **UI pack:** 29/29 true PNG RGBA preserved

---

## Intent

Presentation polish only. No asset reimport, no math/RTP/books/LUT/buy-cost changes.
Design and verify against the Stake-like 1280×720 stage; smaller presets CSS-scale that composition.

---

## Primary 1280×720 layout decisions

| Region | Decision |
| --- | --- |
| Top-left | Compact live status pill (`SkyJumpUtilityBar`) — `%` max-width so it fits inside the stage |
| Top-right | Secondary branding — logo capped ~152px, tag + hill pill; does not compete with board |
| Center | 5×5 board dominant; mild left optical nudge (~−16–20px), not heavy vanishing bias |
| Under board | Always-on `ui_status_plate.png` status bar (`READY` idle → win/status copy in play) |
| Bottom | Stake HUD unchanged in architecture |

### Board geometry (measured at 1280×720 after polish)

| Metric | Value |
| --- | --- |
| Position | Horizontally near-centered (optical nudge ≈ −20px); vertically balanced between top status and HUD |
| Surface / cells | ~equal 5×5 cells; grow factors soft (`BOARD_WIDTH_GROW` 1.02, height 1.0) |
| Tile gap | ~8–10px (`gap` clamp 5–10 from play width) |
| Frame pad | ~12–15px |
| Symbol safe area | **78%** content stage, centered `object-fit: contain` |
| Status slot | Reserved under board (~48px) — plate never overlaps row 5 |

### Ambient FX

Outer icy sweep, inner grid sheen, edge conic glint, and corner glints kept continuous and subtle — raised visibility slightly so they read at 1280 without casino-neon intensity.

---

## Celebrations

| Tier | Treatment |
| --- | --- |
| BIG | Restrained glow + snow; fewer particles; no coins; no screen flash |
| MEGA | Stronger glow + coins + richer sparkles |
| SUPER | Flash accent + denser FX |
| MAX | Heavy premium climax + flash |
| WORLD RECORD | Strongest / unique — WR title + underlay overlay; title wins over MAX |

- Hierarchy: **title → dynamic amount → FX field**
- Title PNG: `object-fit: contain`, max-height capped (not stretched)
- Count-up: SkyjumpDisplay, responsive scale for long values, final **pulse**
- Particles: deterministic **ring/arc** placement — keep center title + amount clear
- Stage-relative sizing (`%` / max-px) instead of raw `vw` so letterboxed stage stays correct

---

## Bonus / mode titles

- FREE SPINS → mode title sequenced (no stack)
- RETRIGGER → short banner alone
- TIER UPGRADE → upgrade banner → mode title
- Mode titles (LH / SF / WC / PV): shared banner component, `max-height` capped, consistent center seat
- Mode badge plate used in Free Spins HUD; not forced in BASE

---

## Modals

### Paytable

- Smaller header image (max-height ~56px)
- Sparing panel decor (smaller topper/corners/divider)
- Tighter section gaps for 720-tall modal chrome
- 28-line viewer unchanged functionally

### Info / How to Play

- Same header/decor discipline
- Denser feature cards; Inter/SkyjumpUI body; display headers

---

## Payline FX

- Spark head ~32px (was 28) — visible but small
- End glint ~36px (was 44) — less heavy on the tip
- Stroke geometry still SVG/code

---

## Typography

- Status / win amount: SkyjumpDisplay
- Mode badge / HUD diagnostics: SkyjumpUI
- Local Oxanium/Inter only — no remote fonts
- Idle status casing: `READY`; live labels uppercase via plate CSS

---

## Live-preview responsive model

**Fix in 8D:** presets no longer reflow layout to the display box.

- Logical canvas always **1280×720** (`data-skyjump-preview-stage`)
- Display frame sized to preset; CSS `transform: scale(display/1280)`
- Pixi / `stateLayout` continue to see 1280×720 client size

| Preset | Expected | Result |
| --- | --- | --- |
| 1280×720 | identity | PASS — board inside frame |
| 768×432 | scale 0.6 | PASS — uniform scale, no reflow |
| 640×360 | scale 0.5 | PASS |
| 480×270 | scale 0.375 | PASS |
| 400×225 | scale 0.3125 | PASS |

---

## Remaining visual debt

| Item | Status |
| --- | --- |
| `ui_tier_large_hill.png` ≡ `ui_tier_ski_flying.png` | **STILL PRESENT** — do not invent art; mode title banners are not replacements |
| Symbol placeholders on idle demo board until book symbols land | Expected for empty/local spins |
| Filip final visual QA of celebrations / Paytable / Info / FS banners | **Pending human approval** |

---

## Build / tests

- V2 frontend tests (phase8c, 8b, 8a autoplay, audio final, visual pack, 7d, live-preview stage): **PASS**
- Production build: **PASS**
- Math SHA unchanged
- 29/29 pack paths intact (phase8c)

---

## Manual QA pointers (Filip)

See also `34_FRONTEND_MANUAL_QA_CHECKLIST.md` § Phase 8D.

Primary: http://localhost:3011/live-preview @ 1280×720  
Scenarios via `/dev-preview` DEV inspector (BASE, paylines, BIG→WR, FS, retrigger, tier upgrade, LH/SF/WC/PV, Paytable, Info).
