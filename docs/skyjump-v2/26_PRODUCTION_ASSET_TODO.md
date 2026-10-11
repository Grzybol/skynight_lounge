# SKYJUMP V2 — Production Asset TODO (Filip handoff)

**Status:** Official human art/audio checklist.
**Art authority:** `23_SYMBOL_ASSET_MANIFEST.md` (LOCKED — WAIT = NONE).
**Branch:** `feat/skyjump-v2-5x5`
**Code surface:** `frontend/apps/poc` V2 board (`SkyJumpV2Board.svelte`) + shared Stake HUD.

Economy / Phase 7B does **not** block starting reel-symbol art.

---

## FILIP — START NOW

Produce these first (style anchors). Square PNG RGBA masters. No numbers baked into art.

1. **P1** Flying Jumper — `sym_p1_flying_jumper.png`
2. **P2** Crystal Trophy — `sym_p2_crystal_trophy.png`
3. **P3** Golden Helmet — `sym_p3_golden_helmet.png`
4. **M1** Jumping Skis — `sym_m1_jumping_skis.png`
5. **M2** Flight Goggles — `sym_m2_flight_goggles.png`
6. **M3** Ski Boots — `sym_m3_ski_boots.png`
7. **L1** Wind Sock — `sym_l1_wind_sock.png`
8. **L2** Snow Badge — `sym_l2_snow_badge.png`
9. **L3** Start Flag — `sym_l3_start_flag.png`
10. **S** Competition Bib — `sym_s_competition_bib.png`
11. **C** Coach Signal — `sym_c_coach_signal.png`
12. **Y** Snowburst Mystery (closed) — `sym_y_snowburst_mystery.png`

Then feature / token family (same lighting language):

13. Thermal Lift · Gate · Judge · Head Judge · Rejump · Wind Key
14. T1–T6 token family (six tiers, **no** face values in art)
15. **SPECIAL_WORLD_RECORD** — must look **different** from T6 Token World Record
16. UI stage icons + tier emblems (see § Non-reel)

---

## DO NOT MAKE / CODE OWNS THIS

| Item | Why |
| --- | --- |
| Token face values (1×, 5×, 100×, …) | Frontend text overlay |
| Thermal ×2…×20 | Frontend text overlay |
| Flight Multiplier numbers / charge boxes | HUD CODE_FX (`■`/`□` or bars) |
| Payline geometry | SVG CODE_FX |
| Random reel outcomes | Math / book |
| Spin / Bet+ / Bet− / Buy / Auto / Turbo / Settings / Info / Sound button PNGs | Shared Stake Pixi HUD — **KEEP_EXISTING** |
| Win-pulse glow / dim / scale | CSS CODE_FX on cells |
| Fake spin-band animation | CODE_FX |
| Dynamic balance / bet / win numerals | HUD text (CODE_FX) |

---

## Delivery convention

| | Spec |
| --- | --- |
| Reel tile master | **768×768** PNG RGBA (acceptable 512–1024) |
| Safe content box | ~70–80% center; ~10–15% transparent margin |
| Cell on screen | ~22–96 px (often ~48–80 desktop) |
| Naming | Exact filenames below / doc 23 |
| Tokens / Thermal | One art; numbers never painted in |
| Non-square UI | Stage/tier icons **512×512** OK; backgrounds keep ~1920×1080 WebP |

No Typekit/Google Fonts runtime CDN for final offline builds (FONT_DECISION — see § Typography).

---

## WHERE FILIP DROPS FINAL ASSETS

| Category | Runtime path (Vite `static/`) | Source / master (optional) |
| --- | --- | --- |
| Reel / feature / token symbols | `frontend/apps/poc/static/assets/skyjump_v2/symbols/` | `assets/skyjump_v2/source/symbols/` |
| UI stage + tier icons | `frontend/apps/poc/static/assets/skyjump_v2/ui/` | same tree under `assets/skyjump_v2/source/ui/` if masters kept |
| Logo | `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_logo_skyjump.png` | optional master in `source/ui/` |
| Overlays (WR, etc.) | `frontend/apps/poc/static/assets/skyjump_v2/overlays/` | optional `source/overlays/` |
| Audio | `frontend/apps/poc/static/assets/audio/skyjump/` | optional masters outside repo |

**Filenames:** exact names from § Reel symbols checklist below and doc `23`. Registry: `frontend/apps/poc/src/game/skyjump_v2/symbolAssetRegistry.ts`.

**Source vs runtime:** masters **768×768 PNG RGBA** in `assets/skyjump_v2/source/`; copy **same filename** to matching path under `frontend/apps/poc/static/assets/skyjump_v2/`. Runtime copies may be optimized later; registry keys unchanged.

---

## Reel symbols — USER_ART (25 tiles)

Priority **P0** unless noted. Current: CSS color + shape + label in `placeholders.ts` / `SkyJumpV2Board.svelte` (registry falls back when PNG missing). Transparent YES. Static primary; win pulse = CODE_FX. **Status:** 25/25 reel symbols READY (Head Judge landed 2026-09-25).

| Done | Pri | ID | Name | Filename | States | Overlay | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [x] | P0 | P1 | Flying Jumper | `sym_p1_flying_jumper.png` | default | no | READY | Premium silhouette |
| [x] | P0 | P2 | Crystal Trophy | `sym_p2_crystal_trophy.png` | default | no | READY | |
| [x] | P0 | P3 | Golden Helmet | `sym_p3_golden_helmet.png` | default | no | READY | |
| [x] | P0 | M1 | Jumping Skis | `sym_m1_jumping_skis.png` | default | no | READY | |
| [x] | P0 | M2 | Flight Goggles | `sym_m2_flight_goggles.png` | default | no | READY | |
| [x] | P0 | M3 | Ski Boots | `sym_m3_ski_boots.png` | default | no | READY | |
| [x] | P0 | L1 | Wind Sock | `sym_l1_wind_sock.png` | default | no | READY | |
| [x] | P0 | L2 | Snow Badge | `sym_l2_snow_badge.png` | default | no | READY | |
| [x] | P0 | L3 | Start Flag | `sym_l3_start_flag.png` | default | no | READY | |
| [x] | P0 | S | Competition Bib | `sym_s_competition_bib.png` | default / celebrate optional | no | READY | Scatter |
| [x] | P0 | C | Coach Signal | `sym_c_coach_signal.png` | default / active optional | no | READY | |
| [x] | P0 | Y | Snowburst Mystery | `sym_y_snowburst_mystery.png` | closed; open optional frames | no | READY | Reveal can be CODE_FX |
| [x] | P0 | THERMAL_LIFT | Thermal Lift | `sym_feat_thermal_lift.png` | default | **×N text** | READY | One art |
| [x] | P0 | GATE_UPGRADE | Gate Upgrade | `sym_feat_gate_upgrade.png` | default | no | READY | |
| [x] | P0 | JUDGE | Judge | `sym_feat_judge.png` | default / collect optional | no | READY | Distinct from Head |
| [x] | P0 | HEAD_JUDGE | Head Judge | `sym_feat_head_judge.png` | default / collect optional | no | READY | Distinct from Judge |
| [x] | P0 | REJUMP | Rejump | `sym_feat_rejump.png` | default | no | READY | |
| [x] | P0 | WIND_KEY | Wind Key | `sym_feat_wind_key.png` | default | no | READY | Charge = HUD |
| [x] | P0 | SPECIAL_WORLD_RECORD | World Record | `sym_feat_special_world_record.png` | default / win | no | READY | **≠ T6** |
| [x] | P0 | T1 | Rookie Token | `sym_token_t1_rookie.png` | default | **value text** | READY | Family |
| [x] | P0 | T2 | K-Point Token | `sym_token_t2_k_point.png` | default | value text | READY | |
| [x] | P0 | T3 | Large Hill Token | `sym_token_t3_large_hill.png` | default | value text | READY | |
| [x] | P0 | T4 | Ski Flying Token | `sym_token_t4_ski_flying.png` | default | value text | READY | |
| [x] | P0 | T5 | World Cup Token | `sym_token_t5_world_cup.png` | default | value text | READY | |
| [x] | P0 | T6 | Token World Record | `sym_token_t6_token_world_record.png` | default | value text | READY | **≠ SPECIAL_WR** |

Consumer: `symbolAssetRegistry.ts`, `SkyJumpV2Board.svelte`, `SkyJumpV2PayTable.svelte`.

---

## Non-reel UI

| Done | Pri | ID | Name | Class | Filename / note | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [x] | P1 | UI_LOGO | SkyJump logo | USER_ART | `ui_logo_skyjump.png` (or SVG) | READY | Today HTML text `SkyJumpBrand.svelte` |
| [ ] | P2 | BG_GAMEPLAY | Gameplay background | KEEP_EXISTING | `assets/skyjump/backgrounds/gameplay.webp` | KEEP | Refresh optional |
| [ ] | P2 | BG_MENU | Menu background | KEEP_EXISTING | `menu.webp` | KEEP | |
| [ ] | P2 | FG_MENU_JUMPER | Menu jumper | KEEP_EXISTING | `jumper/menu-foreground.webp` | KEEP | |
| [ ] | P1 | UI_BOARD_FRAME | Board / reel frame | CODE_FX | cells/CSS today | CODE | Optional USER_ART plate later — not required |
| [ ] | P2 | UI_PAYLINE | Payline treatment | CODE_FX | SVG stroke | CODE | |
| [ ] | P2 | UI_WIN_CELL | Win cell glow | CODE_FX | CSS `.hit` | CODE | |
| [x] | P1 | UI_STAGE_RUN_UP | Run-Up icon | USER_ART | `ui_stage_run_up.png` | READY | 512; charge CODE_FX |
| [x] | P1 | UI_STAGE_TAKEOFF | Takeoff icon | USER_ART | `ui_stage_takeoff.png` | READY | |
| [x] | P1 | UI_STAGE_FLIGHT | Flight icon | USER_ART | `ui_stage_flight.png` | READY | |
| [x] | P1 | UI_TIER_LARGE_HILL | Large Hill emblem | USER_ART | `ui_tier_large_hill.png` | READY | **BYTE-IDENTICAL to Ski Flying — replace needed** |
| [x] | P1 | UI_TIER_SKI_FLYING | Ski Flying emblem | USER_ART | `ui_tier_ski_flying.png` | READY | SHA256 BB48BE826C504B44… same as Large Hill |
| [x] | P1 | UI_TIER_WORLD_CUP | World Cup emblem | USER_ART | `ui_tier_world_cup.png` | READY | |
| [x] | P1 | UI_TIER_PERFECT_V | Perfect V emblem | USER_ART | `ui_tier_perfect_v.png` | READY | |
| [ ] | P2 | UI_PERSIST_FRAME | Persistent Mystery frame | CODE_FX | CSS | CODE | |
| [ ] | P2 | UI_FLOOR | Token floor visual | CODE_FX | text/HUD | CODE | |
| [ ] | P1 | UI_FS_BANNER | Free Spins / upgrade banner | CODE_FX | board `.fs-banner` | CODE | Optional art plate P2 |
| [x] | P1 | UI_WR_OVERLAY | World Record overlay | USER_ART | `ui_overlay_world_record.png` | READY | After SPECIAL_WR art |
| [ ] | P1 | UI_MAXWIN | Max-win overlay | CODE_FX | board banner / cap overlay text | CODE | Shares WR language; no USER_ART required |
| [ ] | P2 | UI_WIN_TIERS | Good / big win art | CODE_FX | text banners today | CODE | V1 result WebPs unused in V2 |
| [ ] | P2 | UI_LOADING | Loading / studio | KEEP_EXISTING | Stake loading | KEEP | |

---

## Buttons / HUD

| Control | Class | Status | Notes |
| --- | --- | --- | --- |
| PLAY / SPIN | KEEP_EXISTING | KEEP | Stake `ButtonBet` + skyjump ice theme |
| BET + / − | KEEP_EXISTING | KEEP | |
| BUY BONUS | KEEP_EXISTING | KEEP | |
| AUTOPLAY | KEEP_EXISTING | KEEP | |
| TURBO | KEEP_EXISTING | KEEP | |
| SETTINGS / INFO / SOUND / MENU | KEEP_EXISTING | KEEP | Pixi flyouts |
| Main menu PLAY / SETTINGS | CODE_FX | CODE | HTML in `SkyJumpMainMenu.svelte` |

Do **not** paint button PNGs unless redesigning away from Stake HUD.

---

## Typography — FONT_DECISION (Phase 7D)

**RESOLVED (Phase 7D):** Remote Typekit removed from `frontend/apps/poc/src/app.html`. Runtime uses safe system stack:

`Segoe UI, system-ui, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif`

(`SKYJUMP_UI_FONT` in `gardenTextStyle.ts`). **ZERO** network font requests from the poc app. No Adobe font files redistributed.

| Role | Current | Decision | Notes |
| --- | --- | --- | --- |
| Stake HUD / Pixi labels | `SKYJUMP_UI_FONT` | SYSTEM_FALLBACK | Offline OK |
| Game logo / menu title | same | SYSTEM_FALLBACK | Phase 8 may swap licensed face |
| FS / WR titles | board CSS / system | SYSTEM_FALLBACK | |
| Token / Thermal / FM numbers | board `<small>` | SYSTEM_FALLBACK | |
| Body / paytable / rules | sans-serif | SYSTEM_FALLBACK | |
| Dynamic balance / bet / win | HUD numerals | CODE_FX | |

If Filip later supplies an approved licensed font: replace in Phase 8 only.

---

## Audio — USER_AUDIO

Base: `static/assets/audio/skyjump/`  
Semantic catalog: `frontend/apps/poc/src/game/skyjump_v2/audio.ts`  
Custom masters: `static/assets/audio/skyjump/sfx/v2/` (21 files, 2026-09-25 pack)  
Gap audit: `docs/skyjump-v2/35_AUDIO_GAP_AUDIT.md`

| Done | Pri | ID | Event | Class | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | P0 | BGM | Ambient playlist | KEEP / EXISTING | READY | `bgm/frostbet-*.mp3` unchanged |
| [x] | P0 | UI_CLICK | UI click | REUSE | READY | `legacy_v1/ui_click.mp3` |
| [x] | P1 | UI_HOVER | Hover | REUSE | READY | `legacy_v1/button_hover_sound.mp3` |
| [x] | P1 | PANEL_OPEN/CLOSE | Panels | REUSE | READY | `legacy_v1/generic_panel_open_close.mp3` |
| [x] | P0 | SPIN / BET_CONFIRM | Bet confirm | REUSE | READY | `legacy_v1/bet_button_sound.mp3` |
| [x] | P0 | BET_INCREASE/DECREASE | Bet +/- | REUSE | READY | legacy_v1 |
| [x] | P0 | REEL_START/STOP | Reel | REUSE | READY | legacy_v1 slot sounds |
| [x] | P0 | PAYLINE_DRAW/COMPLETE | Line draw FX | USER_AUDIO | READY | `sfx_payline_*.mp3` synced to draw |
| [x] | P0 | SCATTER_LAND | Scatter land | USER_AUDIO | READY | `sfx_scatter_land.mp3` |
| [x] | P0 | SCATTER_TRIGGER | Bonus trigger | USER_AUDIO | READY | `sfx_scatter_trigger.mp3` once |
| [x] | P0 | FS_START | Free Spins start | USER_AUDIO | READY | `sfx_free_spins_start.mp3` |
| [x] | P1 | FS_RETRIGGER | Retrigger | USER_AUDIO | READY | `sfx_free_spins_retrigger.mp3` |
| [x] | P1 | TIER_UPGRADE | Tier upgrade | USER_AUDIO | READY | `sfx_tier_upgrade.mp3` |
| [x] | P0 | COACH | Coach | SILENT | SILENT | No dedicated final SFX — visual only |
| [x] | P0 | MYSTERY | Mystery open/reveal | USER_AUDIO | READY | `sfx_mystery_open.mp3` |
| [x] | P0 | TOKEN | Token reveal | USER_AUDIO | READY | `sfx_token_reveal.mp3` |
| [x] | P0 | THERMAL | Thermal apply | USER_AUDIO | READY | `sfx_thermal_lift.mp3` |
| [x] | P0 | GATE | Gate upgrade | USER_AUDIO | READY | `sfx_gate_upgrade.mp3` |
| [x] | P0 | JUDGE | Judge collect | USER_AUDIO | READY | `sfx_judge_collect.mp3` |
| [x] | P0 | HEAD_JUDGE | Head Judge | USER_AUDIO | READY | `sfx_head_judge_collect.mp3` policy B |
| [x] | P0 | REJUMP | Rejump start | USER_AUDIO | READY | `sfx_rejump.mp3` |
| [x] | P0 | WIND_CHARGE | Wind Key charge | USER_AUDIO | READY | `sfx_wind_charge.mp3` |
| [x] | P0 | WIND_UPGRADE | Stage upgrade | USER_AUDIO | READY | `sfx_wind_upgrade.mp3` + transition |
| [—] | P0 | FM_UP | Flight Mult increase | — | N/A | covered by wind/stage presentation |
| [x] | P0 | WORLD_RECORD | WR trigger | USER_AUDIO | READY | `sfx_world_record.mp3` |
| [x] | P0 | MAX_WIN | Max win / cap | USER_AUDIO | READY | `sfx_max_win.mp3` after WR |
| [x] | P1 | BONUS_END | Bonus end | USER_AUDIO | READY | `sfx_bonus_end.mp3` |
| [x] | P2 | BAD_MISS | Optional miss | USER_AUDIO | OPTIONAL | Mapped; **not** wired to no-win spins |
| [x] | P2 | WIND_BED | Wind bed | KEEP | READY | V1 BGM/ambient unchanged |

---

## Animation ownership

| Effect | Owner |
| --- | --- |
| Win pulse / dim / scale | CODE_FX |
| Payline flash | CODE_FX |
| Spin band | CODE_FX |
| Charge fill | CODE_FX |
| Multiplier number tween | CODE_FX |
| Mystery open | CODE_FX (optional USER_ART frames) |
| Judge collect pose | optional USER_ART state else CODE_FX |
| World Record settle | USER_ART symbol + CODE_FX overlay |

---

## Counts

| Class | Count (approx) |
| --- | ---: |
| USER_ART (reel) | **25** |
| USER_ART (non-reel UI) | **10** (logo, 3 stage, 4 tier, WR overlay, optional frame) |
| USER_AUDIO (custom V2) | **21 READY** + UI REUSE + Coach SILENT + BAD_MISS OPTIONAL |
| FONT_DECISION | **LOCAL Oxanium/Inter (`SkyjumpDisplay` / `SkyjumpUI`)** — no Typekit/Google |
| CODE_FX | board FX, banners, paylines, overlays, menu HTML |
| KEEP_EXISTING | Stake HUD buttons, BGM, gameplay/menu WebPs |
| OPTIONAL | hover SFX, illustrated menu CTAs, V1 result plates |
| USER_ART (UI pack 8C) | **29/29 READY** — wins / bonus / headers / decor / FX under `static/assets/skyjump_v2/ui|fx/` |

### Release-blocking USER assets (P0)

All **25 reel tiles READY** (including Head Judge + SPECIAL_WORLD_RECORD ≠ T6). **Core custom SFX pack is wired READY** (Coach intentionally SILENT; BAD_MISS mapped OPTIONAL).

**Phase 8C UI pack:** 29 final assets integrated (see `36_FINAL_UI_PACK_INTEGRATION.md`). Win titles, bonus/mode banners, menu headers, panel decor, and FX sprites are registry-backed.

**Known art debt:** `ui_tier_large_hill.png` and `ui_tier_ski_flying.png` are **byte-identical** (SHA256 `BB48BE826C504B4444F589753608FF6CE72B3F0C2FD9C69907A6EB6475B5B50C`) under `frontend/apps/poc/static/assets/skyjump_v2/ui/` — Filip should replace one emblem; do not invent art. Mode title banners (`ui_title_*`) are separate from these tier emblems.
Logo + stage/tier emblems are **P1** (game playable with CODE_FX text substitutes).
