# SKYJUMP V2 — UI asset visibility matrix (Phase 8C / 8C.1)

**Branch:** `feat/skyjump-v2-5x5`  
**Scope:** Presentation only. Math frozen. All 29 Phase 8C assets are `.png` (RGBA) after 8C.1 repair.

Use this matrix to answer: *is it registered, is it in the gallery, is a production consumer wired, and can a normal play path reach it?*

---

## Readiness levels (do not conflate)

| Level | Meaning |
| --- | --- |
| **REGISTRY READY** | Canonical key → `.png` path in `uiAssetRegistry.ts`; runtime file under `static/assets/skyjump_v2/`. |
| **DEV GALLERY READY** | Visible in DEV inspector → **Assets** (`SkyJumpV2AssetGallery`) and/or Scenario → **UI PACK SHOWCASE**. |
| **PRODUCTION CONSUMER WIRED** | A non-DEV component imports the registry URL and renders it when its trigger fires. |
| **PRODUCTION EVENT REACHABLE** | A real book/event/gameplay path (not showcase-only) can fire that trigger. |
| **MANUALLY VISUALLY VERIFIED** | Filip hands-on check on `/dev-preview` (leave unchecked until confirmed). |

Current pack status after 8C.1:

- [x] REGISTRY READY — all 29 keys → `.png`
- [x] DEV GALLERY READY — gallery + Scenario showcase shortcuts
- [x] PRODUCTION CONSUMER WIRED — see matrix column
- [x] PRODUCTION EVENT REACHABLE — see matrix column (mode badge is FS-only by design)
- [ ] MANUALLY VISUALLY VERIFIED — **Filip** (see `34_FRONTEND_MANUAL_QA_CHECKLIST.md` Phase 8C.1)

---

## Win title authority (presentation-only)

`SkyJumpV2WinCelebration` ← board `openCelebration` ← `classifyV2WinCelebration`:

| Tier | Authority |
| --- | --- |
| BIG | Stake multiple ≥ **10×** (presentation-only) |
| MEGA | Stake multiple ≥ **50×** (presentation-only) |
| SUPER | Stake multiple ≥ **200×** (presentation-only) |
| MAX | `capHit` / max-win / cap-reached semantics |
| WORLD RECORD | Explicit `worldRecord` / WR flag (beats MAX) |

Thresholds never alter RTP, settlement, or books.

---

## Visibility matrix (29 assets)

| ASSET | COMPONENT | WHERE IT SHOULD APPEAR | TRIGGER | PRODUCTION CONSUMER WIRED | DEV SCENARIO | PRODUCTION-REACHABLE |
| --- | --- | --- | --- | --- | --- | --- |
| `ui_win_big` | `SkyJumpV2WinCelebration` | Celebration overlay title | `openCelebration` → `classifyV2WinCelebration` → BIG (≥10×, no WR/cap) | Yes | Scenario → **BIG WIN (showcase)** (`ui:big`) | Yes — settle with ≥10× and &lt;50× |
| `ui_win_mega` | `SkyJumpV2WinCelebration` | Celebration overlay title | MEGA (≥50×, no WR/cap) | Yes | Scenario → **MEGA WIN (showcase)** (`ui:mega`) | Yes — settle with ≥50× and &lt;200× |
| `ui_win_super` | `SkyJumpV2WinCelebration` | Celebration overlay title | SUPER (≥200×, no WR/cap) | Yes | Scenario → **SUPER WIN (showcase)** (`ui:super`) | Yes — settle with ≥200× without WR/cap |
| `ui_win_max` | `SkyJumpV2WinCelebration` | Celebration overlay title | `capHit` (no WR) | Yes | Scenario → **MAX WIN (showcase)** (`ui:max`) or book **feature-17** | Yes — cap / max-win path |
| `ui_win_world_record` | `SkyJumpV2WinCelebration` | Celebration overlay title | `worldRecord` flag | Yes | Scenario → **WORLD RECORD (showcase)** (`ui:worldRecord`) or book **wr-01** | Yes — WR event / flag |
| `ui_bonus_free_spins` | `SkyJumpV2TitleBanner` via `skyjumpV2BonusTitles` | Full-board title banner | `kind === 'fsStart'` | Yes | Showcase **FREE SPINS title** (`ui:fs`) + book **bonus-01** | Yes — FS entry |
| `ui_bonus_retrigger` | `SkyJumpV2TitleBanner` via `skyjumpV2BonusTitles` | Full-board title banner | `kind === 'retrigger'` | Yes | Showcase **RETRIGGER title** (`ui:retrigger`) + book **bonus-05** | Yes — FS retrigger |
| `ui_bonus_tier_upgrade` | `SkyJumpV2TitleBanner` via `skyjumpV2BonusTitles` | Full-board title banner | tier-upgrade kind (then mode title) | Yes | Showcase **TIER UPGRADE title** (`ui:tierUpgrade`) + book **bonus-06** | Yes — tier upgrade path |
| `ui_mode_large_hill` | `SkyJumpV2TitleBanner` via `skyjumpV2BonusTitles` | Full-board mode title after FS start / upgrade | `v2ModeTitleUrl('LARGE_HILL')` | Yes | Showcase **MODE Large Hill** (`ui:modeLH`) + **bonus-01** / **bonus-06** | Yes — when tier is LARGE_HILL |
| `ui_mode_ski_flying` | `SkyJumpV2TitleBanner` via `skyjumpV2BonusTitles` | Full-board mode title | `v2ModeTitleUrl('SKI_FLYING')` | Yes | Showcase **MODE Ski Flying** (`ui:modeSF`) + bonus books | Yes — when tier is SKI_FLYING |
| `ui_mode_world_cup` | `SkyJumpV2TitleBanner` via `skyjumpV2BonusTitles` | Full-board mode title | `v2ModeTitleUrl('WORLD_CUP')` | Yes | Showcase **MODE World Cup** (`ui:modeWC`) + bonus books | Yes — when tier is WORLD_CUP |
| `ui_mode_perfect_v` | `SkyJumpV2TitleBanner` via `skyjumpV2BonusTitles` | Full-board mode title | `v2ModeTitleUrl('PERFECT_V')` | Yes | Showcase **MODE Perfect V** (`ui:modePV`) + bonus books | Yes — when tier is PERFECT_V |
| `ui_header_paytable` | `SkyJumpV2PayTable` | Paytable modal section header | Open Paytable modal | Yes | Scenario → **Paytable (decorated)** (`modal:paytable`) | Yes — player opens Paytable |
| `ui_header_info` | `SkyJumpV2GameRules` | Info / rules modal header(s) | Open Game Rules; also Max Win section | Yes | Scenario → **Info / Rules (decorated)** (`modal:rules`) | Yes — player opens Info |
| `ui_header_features` | `SkyJumpV2GameRules` | Info section header (Free Spins / features) | Game Rules section title match | Yes | `modal:rules` | Yes — Info modal |
| `ui_header_how_to_play` | `SkyJumpV2GameRules` | Info “How to Play” section header | Game Rules section title match | Yes | `modal:rules` | Yes — Info modal |
| `ui_divider_ice` | `SkyJumpV2PanelDecor` | Paytable / Info panel chrome | Modal open (`PayTable` / `GameRules`) | Yes | `modal:paytable` / `modal:rules` + showcase | Yes — modals |
| `ui_corner_ornament` | `SkyJumpV2PanelDecor` | Paytable / Info panel chrome | Modal open | Yes | `modal:paytable` / `modal:rules` + showcase | Yes — modals |
| `ui_panel_topper` | `SkyJumpV2PanelDecor` | Paytable / Info panel chrome | Modal open | Yes | `modal:paytable` / `modal:rules` + showcase | Yes — modals |
| `ui_status_plate` | `SkyJumpV2StatusPlate` | Board win bar plate | `showWin` after settle | Yes | Any spin with win bar, or **UI PACK SHOWCASE** | Yes — BASE (and bonus) after settle when win bar shows |
| `ui_mode_badge_plate` | `SkyJumpV2ModeBadge` | Inside Free Spins banner only | `bonusHud.tier` set while FS banner mounted — **not** always-on in BASE | Yes | Showcase mode badge / FS books (**bonus-01**+) | Yes — **Free Spins only** (by design) |
| `fx_payline_spark_head` | Board SVG progressive path | Travelling spark at line-draw tip | Line-win progressive draw | Yes | Any line-win fixture / normal spin with lines | Yes — line wins |
| `fx_payline_end_glint` | Board SVG progressive path | End glint when line draw completes | Line-win progressive draw end | Yes | Any line-win fixture | Yes — line wins |
| `fx_win_glow_ring` | `SkyJumpV2WinCelebration` | Behind title during celebration | `v2WinFxIntensity` glow for big+ | Yes | BIG/MEGA/SUPER/MAX/WR showcase | Yes — with celebration tier big+ |
| `fx_snow_burst` | `SkyJumpV2WinCelebration` | Celebration snow layer | snowBurst for big+ | Yes | BIG+ showcase | Yes — celebration big+ |
| `fx_ice_glint` | `SkyJumpV2WinCelebration` | Celebration ice glint | `iceGlint` wired for **big+** | Yes | BIG+ showcase | Yes — celebration big+ |
| `fx_small_sparkle` | `SkyJumpV2WinCelebration` | Particle sparkles | sparkles for big+ | Yes | BIG+ showcase | Yes — celebration big+ |
| `fx_coin_sparkle` | `SkyJumpV2WinCelebration` | Coin particle layer | coinSparkle for **mega+** (not BIG) | Yes | MEGA/SUPER/MAX/WR showcase | Yes — celebration mega+ |
| `fx_screen_flash_accent` | `SkyJumpV2WinCelebration` | Screen flash accent | screenFlash for **max** / **worldRecord** only | Yes | MAX / WORLD RECORD showcase | Yes — cap/WR celebration |

---

## Quick consumer map

| Family | Primary consumer | Board / modal entry |
| --- | --- | --- |
| Win titles + celebration FX | `SkyJumpV2WinCelebration` | `SkyJumpV2Board.openCelebration` |
| Bonus / mode titles | `SkyJumpV2TitleBanner` | `skyjumpV2BonusTitles` handler |
| Headers + panel decor | `SkyJumpV2PayTable` / `SkyJumpV2GameRules` + `SkyJumpV2PanelDecor` | Modals |
| Status plate | `SkyJumpV2StatusPlate` | Board win bar (`showWin`) |
| Mode badge plate | `SkyJumpV2ModeBadge` | Free Spins banner when `bonusHud.tier` set |
| Payline spark / end glint | Board SVG | Progressive line path |

---

## Related docs

- `36_FINAL_UI_PACK_INTEGRATION.md` — inventory, 8C.1 black-matte / JPEG root causes, repair
- `34_FRONTEND_MANUAL_QA_CHECKLIST.md` — Phase 8C.1 Filip checklist (unchecked)
