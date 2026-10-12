# SKYJUMP V2 — Symbol / Asset Manifest (Phase 7A art contract)

**Status:** Art-ready contract. **ART AUTHORITY for production symbol/UI art** (Phase 7A APPROVED). No final raster art generated in Phase 7A.  
**Branch:** `feat/skyjump-v2-5x5`  
**Companion:** `22_PHASE7A_FINAL_ECONOMY_AND_SYMBOL_LOCK.md`, `24_PHASE7A1_FULL_ROUND_ECONOMY_CERTIFICATION.md`

Economy certification must not rename locked IDs. WAIT = NONE.

---

## 1. Art-lock direction

Stake review criticized generic AI/template visuals. Production symbols must prioritize:

- strong unique silhouette at small cell size
- cohesive ski-jumping identity (night stadium, ice, metal, snow)
- no emoji / icon-pack look
- no generic glossy casino gems
- premium P1/P2/P3 clearly richer than M/L
- shared perspective, lighting, and material language
- no real-world federation / team / logo trademarks
- transparent backgrounds
- numeric / multiplier text as overlays where practical (not baked into every variant)

Suggested source format for all reel tiles: **PNG RGBA** (or lossless WebP RGBA), master ~512–1024 px, downscaled for cells.

---

## 2. Regular symbols (initial reels)

| ID | Player name | Category | Initial reels | Mystery-only | FS-only | Value overlay | Mult overlay | Animation states | Required visual states | Suggested filename | Multi-outcome shared art |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | Flying Jumper | premium | yes | no | no | no | no | idle / win pulse | default, win | `sym_p1_flying_jumper.png` | no |
| P2 | Crystal Trophy | premium | yes | no | no | no | no | idle / win pulse | default, win | `sym_p2_crystal_trophy.png` | no |
| P3 | Golden Helmet | premium | yes | no | no | no | no | idle / win pulse | default, win | `sym_p3_golden_helmet.png` | no |
| M1 | Jumping Skis | mid | yes | no | no | no | no | idle / win pulse | default, win | `sym_m1_jumping_skis.png` | no |
| M2 | Flight Goggles | mid | yes | no | no | no | no | idle / win pulse | default, win | `sym_m2_flight_goggles.png` | no |
| M3 | Ski Boots | mid | yes | no | no | no | no | idle / win pulse | default, win | `sym_m3_ski_boots.png` | no |
| L1 | Wind Sock | low | yes | no | no | no | no | idle / win pulse | default, win | `sym_l1_wind_sock.png` | no |
| L2 | Snow Badge | low | yes | no | no | no | no | idle / win pulse | default, win | `sym_l2_snow_badge.png` | no |
| L3 | Start Flag | low | yes | no | no | no | no | idle / win pulse | default, win | `sym_l3_start_flag.png` | no |

One primary transparent asset each. Win state may be tint/FX rather than a second painting.

---

## 3. Scatter / Coach / Mystery

| ID | Player name | Category | Initial reels | Mystery-only | FS-only | Value overlay | Mult overlay | Animation states | Required visual states | Suggested filename | Shared art |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S | Competition Bib | scatter | yes | no | no | no | no | idle / land / trigger | default, celebrate | `sym_s_competition_bib.png` | no |
| C | Coach Signal | feature | yes (Coach E strips) | no | no | no | no | idle / select / transform | default, active | `sym_c_coach_signal.png` | no |
| Y | Snowburst Mystery | feature | no (`initialReelSymbol: false`) | yes (from Coach) | no | no | no | unrevealed / reveal | closed, open | `sym_y_snowburst_mystery.png` (+ optional reveal frames) | one closed + FX |

---

## 4. Feature symbols (post-Mystery / board specials)

| ID | Player name | Category | Initial reels | Mystery-only | FS-only | Value overlay | Mult overlay | Animation states | Required visual states | Suggested filename | Shared art |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THERMAL_LIFT | Thermal Lift | feature | no | yes | no | no | **yes** (×2…×20) | land / apply | default | `sym_feat_thermal_lift.png` | one art; mult is text |
| GATE_UPGRADE | Gate Upgrade | feature | no | yes | no | no | no | land / floor bump | default | `sym_feat_gate_upgrade.png` | no |
| JUDGE | Judge | feature | no | yes | no | no | no | land / collect | default, collect | `sym_feat_judge.png` | no |
| HEAD_JUDGE | Head Judge | feature | no | yes | no | no | no | land / collect×2 | default, collect | `sym_feat_head_judge.png` | distinct from Judge |
| REJUMP | Rejump | feature | no | yes (FS Phase 6) | FS Mystery | no | no | land / redrop | default | `sym_feat_rejump.png` | no |
| WIND_KEY | Wind Key | feature | no | yes (FS Phase 6) | FS Mystery | no | no | land / charge cue | default | `sym_feat_wind_key.png` | one tile; charge lives in HUD |
| SPECIAL_WORLD_RECORD | World Record | board special | no (injected) | no | FS recommended | no | no | appear / settle | default, win | `sym_feat_special_world_record.png` | **≠** T6 token art |

---

## 5. Flight Tokens (one family, six tiers)

Prefer **one visual family** with six tier treatments (metal grade / frost / glow). Face values are **frontend text overlays**.

| Tier | ID | Player name | Initial reels | Mystery-only | FS-only | Value overlay | Mult overlay | Animation | States | Suggested filename | Shared |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | T1 | Rookie Token | no | yes | no | **yes** | no | land | default | `sym_token_t1_rookie.png` | family |
| 2 | T2 | K-Point Token | no | yes | no | **yes** | no | land | default | `sym_token_t2_k_point.png` | family |
| 3 | T3 | Large Hill Token | no | yes | no | **yes** | no | land | default | `sym_token_t3_large_hill.png` | family |
| 4 | T4 | Ski Flying Token | no | yes | no | **yes** | no | land | default | `sym_token_t4_ski_flying.png` | family |
| 5 | T5 | World Cup Token | no | yes | no | **yes** | no | land | default | `sym_token_t5_world_cup.png` | family |
| 6 | T6 | Token World Record | no | yes | no | **yes** | no | land | default | `sym_token_t6_token_world_record.png` | family; **not** SPECIAL_WORLD_RECORD |

Do **not** paint separate art for every face value (1× / 2× / 5× / …).

---

## 6. Non-symbol UI assets (not reel tiles)

| ID | Player name | Role | Overlay | Animation | Suggested filename |
| --- | --- | --- | --- | --- | --- |
| UI_STAGE_RUN_UP | Run-Up | Flight Multiplier stage icon | charge boxes in HUD | charge/upgrade | `ui_stage_run_up.png` |
| UI_STAGE_TAKEOFF | Takeoff | Flight Multiplier stage icon | charge boxes | charge/upgrade | `ui_stage_takeoff.png` |
| UI_STAGE_FLIGHT | Flight | Flight Multiplier stage icon | charge boxes | charge/upgrade | `ui_stage_flight.png` |
| UI_TIER_LARGE_HILL | Large Hill | bonus tier emblem | no | tier up | `ui_tier_large_hill.png` |
| UI_TIER_SKI_FLYING | Ski Flying | bonus tier emblem | no | tier up | `ui_tier_ski_flying.png` |
| UI_TIER_WORLD_CUP | World Cup | bonus tier emblem | no | tier up | `ui_tier_world_cup.png` |
| UI_TIER_PERFECT_V | Perfect V | bonus tier emblem | no | tier up | `ui_tier_perfect_v.png` |

Keep clearly separated from reel-symbol production.

---

## 7. Art lock roster summary

**ART LOCKED NOW:** P1–P3, M1–M3, L1–L3, S, C, Y, Thermal, Gate, Judge, Head Judge, Rejump, Wind Key, T1–T6, SPECIAL_WORLD_RECORD (design identity), UI stage + tier emblems.

**WAIT:** none for identity. Production raster delivery is a later art task; Phase 7B implements WR math after human approval of economy candidate.
