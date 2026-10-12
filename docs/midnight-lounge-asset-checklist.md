# Midnight Lounge asset replacement checklist

Player-facing production list for the SkyJump chassis. Internal IDs, math, RTP, book events, and Stake/RGS names stay as they are.

Use this file row by row. The next asset to make is **A06**, the logo.

Runtime classes used below:

| Class | Meaning |
|---|---|
| RUNTIME_ACTIVE | On the current screen and already lounge art |
| RUNTIME_REPLACE | On the current screen and still SkyJump |
| RUNTIME_REVIEW | On the current screen; may be generic |
| GENERIC_SHARED | Shared font or click that is not ski art |
| SOURCE_ONLY | File exists; the current `Game.svelte` tree does not mount it |
| ARCHIVE | Zip backup. Not loaded |
| DEV_ONLY | Dev showcase / inspector |

Checklist status: `DONE`, `TODO`, `REVIEW`, `GENERIC_KEEP`, `NOT_PLAYER_FACING`.

`TBD_MIDNIGHT_LOUNGE_LABEL` means the lounge name is not chosen. The screen keeps the current English string.

## How the screen is built

Live tree in `Game.svelte`:

- Plate and character: `SkyJumpBackground.svelte` (HTML `<img>`, not Pixi)
- Logo and hill tag: `SkyJumpBrand.svelte`
- Snow dots: `SkyJumpAtmosphere.svelte` (CSS, no file)
- Board, symbols, bonus HUD: `SkyJumpV2Board.svelte`
- Bet chrome: Pixi HUD using `/assets/skyjump_v2/ui/betui/` and `decor/ui_bet_hud_frame.png`
- Modals: v2 paytable, rules, buy bonus
- Menu (production after load; local demo skips to play): `SkyJumpMainMenu.svelte`

v1 reel strip, weather draw, v1 paytable, and v1 result cards are not mounted. They are listed once at the end so they are not drawn again by mistake.

## Character clips

GIF and animated WebP play through `<img>`. There is no `ended` event and no `playbackRate`. Start and stop use `setTimeout` in `loungeFigureTune.ts`. Turbo (`getSkyJumpTimings`) changes reel and count-up timing only. It does not speed these clips. Do not make a second Turbo file.

| Role | File | Format | Canvas | Timing | Loop | Trigger | Final? |
|---|---|---|---|---|---|---|---|
| Idle / shoe dangling | `frontend/apps/poc/src/assets/skyjump/backgrounds/lounge-figure.webp` | animated WebP, alpha | 1167×1556 | `BASE_LOOP_MS` 8580 | native loop; the element is not remounted between loops | always, while no reaction is up | yes, in use |
| Leg extension | `.../stopa_plus.gif` | GIF, alpha | 1167×1556 | source 6050 ms; scheduler drops the last 500 ms | one-shot | random after 2–6 full idle loops | yes, in use |
| Delighted | `.../smile_plus.gif` | GIF, alpha | 1167×1556 | plays for the big-win overlay, not a file timer | one-shot | big win | yes, in use |
| Wow | `.../wow_plus.gif` | GIF, alpha | 1167×1556 | plays for the mega-and-above overlay | one-shot | mega, super, max, world record | yes, in use |

Drop-in names already exported from `src/game/midnightLoungeTheme.ts`: `characterIdleSrc`, `characterLegExtendSrc`, `characterDelightedSrc`, `characterWowSrc`.

## Presentation map

`LOUNGE_PRESENTATION` in `midnightLoungeTheme.ts`. `loungeShown()` returns `shown`. The `lounge` field is not displayed.

| Internal ID | Player sees now | Midnight Lounge label | Where |
|---|---|---|---|
| `LARGE_HILL` | LARGE HILL | TBD_MIDNIGHT_LOUNGE_LABEL | bonus HUD badge, tier emblem, `ui_mode_large_hill.png`, rules |
| `SKI_FLYING` | SKI FLYING | TBD_MIDNIGHT_LOUNGE_LABEL | same |
| `WORLD_CUP` | WORLD CUP | TBD_MIDNIGHT_LOUNGE_LABEL | same |
| `PERFECT_V` | PERFECT V | TBD_MIDNIGHT_LOUNGE_LABEL | same |
| `RUN_UP` | RUN-UP | TBD_MIDNIGHT_LOUNGE_LABEL | flight HUD and rules |
| `TAKEOFF` | TAKEOFF | TBD_MIDNIGHT_LOUNGE_LABEL | flight HUD and rules |
| `FLIGHT` | FLIGHT | TBD_MIDNIGHT_LOUNGE_LABEL | flight HUD and rules |

Buy-mode cards also read `playerName` from `skyjump_v2_config.json` (`Large Hill`, `Ski Flying`, `World Cup`, `Perfect V`, `Base`). That JSON is math. Do not edit it. When lounge names exist, map them in `LOUNGE_PRESENTATION` and point the card alt text at `lounge`.

Symbol IDs (`P1` … `T6`) stay. Paytable names are the math `name` field (`FLYING_JUMPER` → “Flying Jumper”). New art keeps the ID and the filename until a later registry pass.

## A. Core scene

| ID | Priority | Area | Current asset / source | Current visible role | Status | Replacement needed | Required format | Notes |
|---|---|---|---|---|---|---|---|---|
| A01 | P0 | Background | `src/assets/skyjump/backgrounds/midnight-lounge.jpg` | Full 1280×720 plate behind the board | DONE | no | JPG opaque | 1024×576 source, object-fit fill. RUNTIME_ACTIVE. |
| A02 | P0 | Character idle | `lounge-figure.webp` | Seated lounge figure, shoe dangling | DONE | no | animated WebP, alpha | 1167×1556, 8580 ms ping-pong. RUNTIME_ACTIVE. |
| A03 | P0 | Character leg | `stopa_plus.gif` | Shoe / leg extension | DONE | no | GIF, alpha | Same canvas. One-shot. RUNTIME_ACTIVE. |
| A04 | P0 | Character delighted | `smile_plus.gif` | Big-win reaction | DONE | no | GIF, alpha | Same canvas. RUNTIME_ACTIVE. |
| A05 | P0 | Character wow | `wow_plus.gif` | Mega and above | DONE | no | GIF, alpha | Same canvas. RUNTIME_ACTIVE. |
| A06 | P0 | Logo | `static/assets/skyjump_v2/ui/ui_logo_skyjump.png` | Top-right logo on the play screen; menu logo | TODO | yes | PNG transparent | 1024×512. Alt text already says Midnight Lounge. Pixels still say SkyJump. `loungeLogoSrc`. RUNTIME_REPLACE. |
| A07 | P1 | Menu plate | `src/assets/skyjump/backgrounds/menu.webp` | Full-screen menu background | TODO | yes | WebP or JPG opaque | 1344×768. Ski night stadium. Shown when `screen === 'menu'`. `loungeMenuPlateSrc`. RUNTIME_REPLACE. |
| A08 | P1 | Menu figure | `src/assets/skyjump/jumper/menu-foreground.webp` | Figure on the right of the menu | TODO | yes | WebP, alpha | Ski jumper. Replace with the lounge character, or drop the layer once A07 carries her. RUNTIME_REPLACE. |
| A09 | P0 | Snow | `SkyJumpAtmosphere.svelte` | Falling white dots over the play screen | TODO | yes, or remove | CSS / no file | No image. 18 flakes, z-index 10, play screen only. RUNTIME_REPLACE. |
| A10 | P0 | Browser title | `PUBLIC_GAME_TITLE` | Tab title | DONE | no | text | “Midnight Lounge”. |
| A11 | P0 | Loader | `LoaderArtwork.svelte` | Loading and ready lines | DONE | no | text | “MIDNIGHT LOUNGE”, “PREPARING THE ROOM”, “THE LOUNGE IS OPEN”. |
| A12 | P1 | Brand tagline | `SkyJumpBrand.svelte` `t('Reach higher')` | Line under the logo | TODO | copy only | text | Still ski copy. Lounge line TBD. |
| A13 | P1 | Menu copy | `SkyJumpMainMenu.svelte` | Kicker and subtitle | TODO | copy only | text | “WINTER SPORTS MINI-GAME” and “Ski jumping · night stadium · sequential reels”. |

## B. Game board

Slot frame and symbols are what the player watches during a spin. Symbol files are 1024×1024 PNG with alpha. Keep the filename. Draw a lounge object that reads at cell size. Do not bake multiplier numbers into tokens; those stay text.

| ID | Priority | Area | Current asset / source | Current visible role | Status | Replacement needed | Required format | Notes |
|---|---|---|---|---|---|---|---|---|
| B01 | P0 | Slot frame | `ui/decor/ui_slot_board_frame.png` | Ornate frame around the 5×5 | TODO | yes | PNG transparent | 1024×1024. Ice/gold ski frame. `loungeSlotFrameSrc`. RUNTIME_REPLACE. |
| B02 | P0 | Symbol P1 | `sym_p1_flying_jumper.png` | Premium reel symbol | TODO | yes | PNG transparent 1024² | Player name Flying Jumper. ID `P1`. |
| B03 | P0 | Symbol P2 | `sym_p2_crystal_trophy.png` | Premium | TODO | yes | PNG transparent 1024² | Crystal Trophy. Can become a lounge trophy. |
| B04 | P0 | Symbol P3 | `sym_p3_golden_helmet.png` | Premium | TODO | yes | PNG transparent 1024² | Golden Helmet. Ski helmet. |
| B05 | P1 | Symbol M1 | `sym_m1_jumping_skis.png` | Mid | TODO | yes | PNG transparent 1024² | Jumping Skis. |
| B06 | P1 | Symbol M2 | `sym_m2_flight_goggles.png` | Mid | TODO | yes | PNG transparent 1024² | Flight Goggles. |
| B07 | P1 | Symbol M3 | `sym_m3_ski_boots.png` | Mid | TODO | yes | PNG transparent 1024² | Ski Boots. |
| B08 | P1 | Symbol L1 | `sym_l1_wind_sock.png` | Low | TODO | yes | PNG transparent 1024² | Wind Sock. |
| B09 | P1 | Symbol L2 | `sym_l2_snow_badge.png` | Low | TODO | yes | PNG transparent 1024² | Snow Badge. |
| B10 | P1 | Symbol L3 | `sym_l3_start_flag.png` | Low | TODO | yes | PNG transparent 1024² | Start Flag. |
| B11 | P1 | Symbol S | `sym_s_competition_bib.png` | Scatter | TODO | yes | PNG transparent 1024² | Competition Bib. Triggers free spins. |
| B12 | P1 | Symbol C | `sym_c_coach_signal.png` | Feature | TODO | yes | PNG transparent 1024² | Coach Signal. |
| B13 | P1 | Symbol Y | `sym_y_snowburst_mystery.png` | Mystery | TODO | yes | PNG transparent 1024² | Snowburst Mystery. |
| B14 | P1 | Symbol Thermal | `sym_feat_thermal_lift.png` | Feature, multiplier is text | TODO | yes | PNG transparent 1024² | ID `THERMAL_LIFT`. |
| B15 | P1 | Symbol Gate | `sym_feat_gate_upgrade.png` | Feature | TODO | yes | PNG transparent 1024² | ID `GATE_UPGRADE`. |
| B16 | P1 | Symbol Judge | `sym_feat_judge.png` | Collector | TODO | yes | PNG transparent 1024² | ID `JUDGE`. |
| B17 | P1 | Symbol Head Judge | `sym_feat_head_judge.png` | Collector | TODO | yes | PNG transparent 1024² | Must stay distinct from Judge. |
| B18 | P1 | Symbol Rejump | `sym_feat_rejump.png` | Free-spin feature | TODO | yes | PNG transparent 1024² | ID `REJUMP`. |
| B19 | P1 | Symbol Wind Key | `sym_feat_wind_key.png` | Free-spin feature | TODO | yes | PNG transparent 1024² | ID `WIND_KEY`. |
| B20 | P1 | Symbol World Record | `sym_feat_special_world_record.png` | Board special | TODO | yes | PNG transparent 1024² | Not the T6 token. |
| B21 | P1 | Token T1 | `sym_token_t1_rookie.png` | Prize token | TODO | yes | PNG transparent 1024² | Rookie. Value is a text overlay. |
| B22 | P1 | Token T2 | `sym_token_t2_k_point.png` | Prize token | TODO | yes | PNG transparent 1024² | K-Point. |
| B23 | P1 | Token T3 | `sym_token_t3_large_hill.png` | Prize token | TODO | yes | PNG transparent 1024² | Large Hill tier. |
| B24 | P1 | Token T4 | `sym_token_t4_ski_flying.png` | Prize token | TODO | yes | PNG transparent 1024² | Ski Flying tier. |
| B25 | P1 | Token T5 | `sym_token_t5_world_cup.png` | Prize token | TODO | yes | PNG transparent 1024² | World Cup tier. |
| B26 | P1 | Token T6 | `sym_token_t6_token_world_record.png` | Prize token | TODO | yes | PNG transparent 1024² | Token world record. Not B20. |
| B27 | P1 | Stage icon | `ui_stage_run_up.png` | Flight HUD icon | TODO | yes | PNG transparent 1024² | Label stays `loungeShown('RUN_UP')` until the lounge name exists. |
| B28 | P1 | Stage icon | `ui_stage_takeoff.png` | Flight HUD icon | TODO | yes | PNG transparent 1024² | |
| B29 | P1 | Stage icon | `ui_stage_flight.png` | Flight HUD icon | TODO | yes | PNG transparent 1024² | |
| B30 | P1 | Tier emblem | `ui_tier_large_hill.png` | Bonus HUD emblem | TODO | yes | PNG transparent 1024² | Baked ski title. ID `LARGE_HILL`. |
| B31 | P1 | Tier emblem | `ui_tier_ski_flying.png` | Bonus HUD emblem | TODO | yes | PNG transparent 1024² | ID `SKI_FLYING`. |
| B32 | P1 | Tier emblem | `ui_tier_world_cup.png` | Bonus HUD emblem | TODO | yes | PNG transparent 1024² | ID `WORLD_CUP`. |
| B33 | P1 | Tier emblem | `ui_tier_perfect_v.png` | Bonus HUD emblem | TODO | yes | PNG transparent 1024² | ID `PERFECT_V`. |
| B34 | P2 | Board glass | CSS `.board-glass` in `SkyJumpV2Board.svelte` | Dim glass over the grid | REVIEW | maybe | CSS | No ski drawing. Recolor toward burgundy/gold when the frame lands. |

## C. Controls / UI

These faces are the ice/gold bet pack. Listen and look before redrawing: a plain metal button can stay. Paths are under `static/assets/skyjump_v2/ui/betui/` unless noted.

| ID | Priority | Area | Current asset / source | Current visible role | Status | Replacement needed | Required format | Notes |
|---|---|---|---|---|---|---|---|---|
| C01 | P2 | Spin | `betui_spin_button.png` | Spin | REVIEW | maybe | PNG transparent | 1024×1024. |
| C02 | P2 | Stop | `betui_stop_button.png` | Stop | REVIEW | maybe | PNG transparent | 1024×1024. |
| C03 | P2 | Auto | `betui_auto_button.png` | Autoplay | REVIEW | maybe | PNG transparent | 768×1024. |
| C04 | P2 | Turbo | `betui_turbo_button.png` | Turbo | REVIEW | maybe | PNG transparent | 853×1024. Turbo does not speed the character. |
| C05 | P2 | Buy | `betui_buy_bonus_button.png` | Opens buy feature | REVIEW | maybe | PNG transparent | 1024×341. |
| C06 | P2 | Menu | `betui_menu_button.png` | Menu | REVIEW | maybe | PNG transparent | 768×1024. |
| C07 | P2 | Menu exit | `betui_menu_exit_button.png` | Close menu | REVIEW | maybe | PNG transparent | 1024×682. |
| C08 | P2 | Info | `betui_info_button.png` | Info | REVIEW | maybe | PNG transparent | 1024×1024. |
| C09 | P2 | Paytable button | `betui_paytable_button.png` | Paytable | REVIEW | maybe | PNG transparent | 1024×1024. |
| C10 | P2 | Settings | `betui_settings_button.png` | Settings | REVIEW | maybe | PNG transparent | 1024×1024. |
| C11 | P2 | Sound | `betui_sound_on_button.png`, `betui_sound_off_button.png` | Sound toggle | REVIEW | maybe | PNG transparent | 1024×1024 each. |
| C12 | P2 | Bet step | `betui_btn_plus.png`, `betui_btn_minus.png` | Bet up / down, also buy modal | REVIEW | maybe | PNG transparent | 1024×1024. |
| C13 | P2 | Language | `betui_language_button.png` | Language | REVIEW | maybe | PNG transparent | 1024×512. |
| C14 | P2 | HUD frame | `ui/decor/ui_bet_hud_frame.png` | Bar behind the spin seat | REVIEW | maybe | PNG transparent | 1024×217. Ice wings. |
| C15 | P2 | HUD tile | `betui_background_tile.png` | HUD fill | REVIEW | maybe | PNG | 1024×341. |

## D. Win / result presentation

Win amounts are code-rendered. Titles are baked into the PNG, so a lounge title means a new image, not a string change.

| ID | Priority | Area | Current asset / source | Current visible role | Status | Replacement needed | Required format | Notes |
|---|---|---|---|---|---|---|---|---|
| D01 | P1 | Big win title | `ui/wins/ui_win_big.png` | Big-win plate | TODO | yes | PNG transparent | 1774×887. Pairs with A04. |
| D02 | P1 | Mega win title | `ui_win_mega.png` | Mega plate | TODO | yes | PNG transparent | 1774×887. Pairs with A05. |
| D03 | P1 | Super win title | `ui_win_super.png` | Super plate | TODO | yes | PNG transparent | 1774×887. |
| D04 | P1 | Max win title | `ui_win_max.png` | Max plate | TODO | yes | PNG transparent | 1774×887. |
| D05 | P1 | World-record title | `ui_win_world_record.png` | Top win plate | TODO | yes | PNG transparent | 1774×887. Baked “world record”. |
| D06 | P1 | World-record overlay | `overlays/ui_overlay_world_record.png` | Full-board overlay | TODO | yes | PNG transparent | 1024×576. |
| D07 | P1 | Bonus banner | `ui/bonus/ui_bonus_free_spins.png` | Free-spin entry | TODO | yes | PNG transparent | 1774×887. |
| D08 | P1 | Retrigger banner | `ui_bonus_retrigger.png` | Extra spins | TODO | yes | PNG transparent | 1774×887. |
| D09 | P1 | Tier-upgrade banner | `ui_bonus_tier_upgrade.png` | Tier step | TODO | yes | PNG transparent | 1024×512. |
| D10 | P1 | Mode banner | `ui_mode_large_hill.png` | Buy card and mode title | TODO | yes | PNG transparent | 1024×512. Baked LARGE HILL. ID stays. |
| D11 | P1 | Mode banner | `ui_mode_ski_flying.png` | Buy card and mode title | TODO | yes | PNG transparent | 1774×887. |
| D12 | P1 | Mode banner | `ui_mode_world_cup.png` | Buy card and mode title | TODO | yes | PNG transparent | 1024×512. |
| D13 | P1 | Mode banner | `ui_mode_perfect_v.png` | Buy card and mode title | TODO | yes | PNG transparent | 1024×512. |
| D14 | P2 | Snow burst | `fx/fx_snow_burst.png` | Win / feature burst | TODO | yes | PNG transparent | 1254×1254. Ski snow. |
| D15 | P2 | Ice glint | `fx/fx_ice_glint.png` | Board glint | TODO | yes | PNG transparent | 1254×1254. |
| D16 | P3 | Payline spark | `fx_payline_spark_head.png` | Payline head | REVIEW | maybe | PNG transparent | 1254×1254. |
| D17 | P3 | Payline glint | `fx_payline_end_glint.png` | Payline end | REVIEW | maybe | PNG transparent | 1254×1254. |
| D18 | P3 | Win ring | `fx_win_glow_ring.png` | Win glow | REVIEW | maybe | PNG transparent | 1254×1254. |
| D19 | P3 | Coin sparkle | `fx_coin_sparkle.png` | Sparkle | REVIEW | maybe | PNG transparent | 1254×1254. |
| D20 | P3 | Small sparkle | `fx_small_sparkle.png` | Sparkle | REVIEW | maybe | PNG transparent | 1254×1254. |
| D21 | P3 | Screen flash | `fx_screen_flash_accent.png` | Flash | REVIEW | maybe | PNG transparent | 1672×941. |

## E. Modals / info

| ID | Priority | Area | Current asset / source | Current visible role | Status | Replacement needed | Required format | Notes |
|---|---|---|---|---|---|---|---|---|
| E01 | P1 | Paytable header | `ui/headers/ui_header_paytable.png` | Modal header art | TODO | yes | PNG transparent | 1774×887. HTML heading “Paytable” is already generic. Kicker is “Midnight Lounge”. |
| E02 | P1 | How-to header | `ui_header_how_to_play.png` | Rules header | TODO | yes | PNG transparent | 1774×887. |
| E03 | P1 | Features header | `ui_header_features.png` | Rules header | TODO | yes | PNG transparent | 1774×887. |
| E04 | P1 | Info header | `ui_header_info.png` | Rules header | TODO | yes | PNG transparent | 1774×887. |
| E05 | P2 | Divider | `ui/decor/ui_divider_ice.png` | Panel divider | TODO | yes | PNG transparent | 2172×724. Ice ornament. |
| E06 | P2 | Corner | `ui_corner_ornament.png` | Panel corners | REVIEW | maybe | PNG transparent | 1254×1254. |
| E07 | P2 | Panel topper | `ui_panel_topper.png` | Panel cap | REVIEW | maybe | PNG transparent | 2172×724. |
| E08 | P2 | Mode plate | `ui_mode_badge_plate.png` | Buy-bonus header plate | REVIEW | maybe | PNG transparent | 2172×724. Title “Buy Bonus” is HTML on top. |
| E09 | P2 | Status plate | `ui_status_plate.png` | Status chip plate | REVIEW | maybe | PNG transparent | 2172×724. |
| E10 | P1 | Paytable lede | `SkyJumpV2PayTable.svelte` | First paragraph | TODO | copy only | text | “5×5 ski-jump slot”. Feature blurbs still say Rejump, Wind Key, RUN-UP, TAKEOFF, FLIGHT. |
| E11 | P1 | Rules body | `SkyJumpV2GameRules.svelte` | Help copy | TODO | copy only | text | Names Large Hill, Ski Flying, World Cup, Perfect V, Coach, Mystery, flight stages. IDs stay. |
| E12 | P1 | Buy sentence | `SkyJumpV2BuyBonus.svelte` | Intro line | TODO | copy only | text | “Choose a free-spin hill.” |
| E13 | P1 | Hill chip | `SkyJumpBrand.svelte` | Chip under the logo | TODO | copy only | text | v1 `HILL_TABLE` label via i18n: Normal Hill, Large Hill, Ski Flying Hill. Math labels stay. |
| E14 | P0 | Modal kicker | paytable, rules, buy bonus | Small “Midnight Lounge” line | DONE | no | text | |
| E15 | P0 | Rules title | i18n value for key `SKYJUMP RULES` | Rules heading | DONE | no | text | EN “MIDNIGHT LOUNGE RULES”, PL “ZASADY MIDNIGHT LOUNGE”. Lookup key stays. |

## F. Typography

| ID | Priority | Area | Current asset / source | Current visible role | Status | Replacement needed | Required format | Notes |
|---|---|---|---|---|---|---|---|---|
| F01 | P3 | Display face | `oxanium-600/700/800.woff2` as `SkyjumpDisplay` | Loader and display | GENERIC_KEEP | no | font woff2 | OFL Oxanium. Family name is internal. |
| F02 | P3 | UI face | `inter-400/500/600/700.woff2` as `SkyjumpUI` | Body UI | GENERIC_KEEP | no | font woff2 | OFL Inter. |
| F03 | P3 | Lounge display | none | Optional gold display | REVIEW | maybe | font | Only if Oxanium feels too sports-technical. Not blocking. |

## G. Audio

| ID | Priority | Area | Current asset / source | Current visible role | Status | Replacement needed | Required format | Notes |
|---|---|---|---|---|---|---|---|---|
| G01 | P2 | BGM | `bgm/frostbet-1.mp3` | Main loop | TODO | yes | MP3 or OGG | Listed in `tracks.json`. Frost/ski bed. |
| G02 | P2 | BGM | `bgm/frostbet-2.mp3` | Main loop | TODO | yes | MP3 or OGG | |
| G03 | P2 | BGM | `bgm/frostbet-3.mp3` | Main loop | TODO | yes | MP3 or OGG | |
| G04 | P3 | UI clicks | `SKYJUMP_SFX` sprite names (`sfx_btn_general`, reel stops, win levels) | Buttons, reels, count-up | GENERIC_KEEP | no | audio | Sound IDs stay. Replace the file only if the take is obviously ski. |
| G05 | P2 | Feature stingers | `sfx/v2/sfx_*.mp3` (21 files) | Scatter, wind, rejump, judge, world record | REVIEW | maybe | MP3 or OGG | Hook names describe ski features. Listen before redrawing. Do not rename hooks. |

## H. Not on the current screen

Do not generate lounge art for these until something mounts them. Confirmed: `Game.svelte` does not import the v1 reel, weather, v1 paytable, or v1 result overlay.

| ID | Priority | Area | Current asset / source | Current visible role | Status | Replacement needed | Required format | Notes |
|---|---|---|---|---|---|---|---|---|
| H01 | — | v1 weather icons | `src/assets/skyjump/weather/*.svg` | none on live tree | NOT_PLAYER_FACING | no | SVG | SOURCE_ONLY. Used by unmounted `SkyJumpWeatherDraw.svelte`. |
| H02 | — | v1 reel icons | `src/assets/skyjump/reel-icons/*.svg` | none on live tree | NOT_PLAYER_FACING | no | SVG | SOURCE_ONLY. |
| H03 | — | v1 jumper flight | `jumper/flight.png`, `flight-win.png`, `inrun.webp` | none | NOT_PLAYER_FACING | no | PNG/WebP | Exported, not referenced by a mounted component. |
| H04 | — | v1 result cards | `src/assets/skyjump/result/*.webp` | none | NOT_PLAYER_FACING | no | WebP | `SkyJumpResultOverlay.svelte` is not in `Game.svelte`. Live wins use section D plus A04/A05. |
| H05 | — | GIF zip backups | `asset-backup/lounge-gifs/*.zip` | none | NOT_PLAYER_FACING | no | zip | ARCHIVE. Not requested at runtime. |
| H06 | — | Dev showcase | `SkyJumpV2UiPackShowcase.svelte`, `SkyJumpV2DevSource.svelte` | dev only | NOT_PLAYER_FACING | no | — | DEV_ONLY. |
| H07 | — | Math / protocol | `gameName: 'skyjump'`, `gameID`, `BookEventSkyJump*`, mode `rgsKey`, `skyjump_v2_config.json` | not a graphic | NOT_PLAYER_FACING | no | — | INTERNAL. Do not rename. |

## Counts

| Status | Rows |
|---|---|
| DONE | 9 (A01–A05, A10, A11, E14, E15) |
| TODO | 66 |
| REVIEW | 28 |
| GENERIC_KEEP | 3 (F01, F02, G04) |
| NOT_PLAYER_FACING | 7 (H01–H07) |

## Next production order

1. A06 logo
2. A09 snow overlay (remove or replace; no new file required)
3. B01 slot frame
4. B02–B10 regular symbols, premiums first
5. B11–B26 scatter, features, tokens
6. D10–D13 mode banners and B30–B33 tier emblems, after lounge names exist
7. D01–D06 win plates
8. A07–A08 menu plate and menu figure
9. E10–E13 and A12–A13 copy, using `LOUNGE_PRESENTATION` once names are decided
10. G01–G03 music
