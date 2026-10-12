# Midnight Lounge implementation checklist

Progress of the SkyJump chassis presentation swap. This is not the production brief. Asset specs stay in `docs/midnight-lounge-asset-checklist.md`.

States: **GENERATED**, **INTEGRATED**, **VALIDATED**, **MISSING**, **NOT_REQUIRED**, **REVIEW**.

Math, RGS ids, event ids, and payouts are unchanged. Old SkyJump files are still on disk.

Source pack: `midnight_lounge_assets_most.zip` (left untouched). Runtime copies live under `frontend/apps/poc/static/assets/midnight-lounge/`. Squares that arrived at 1254×1254 were resampled to 1024×1024 with Lanczos, alpha kept. Same-ratio banners were resampled to the checklist target. No crop.

| ID | Asset | Generated | Integrated | Validated | Runtime target | Notes |
|---|---|---|---|---|---|---|
| A01 | Background plate | YES, before this ZIP | YES | YES | `midnight-lounge.jpg` | Not in this ZIP. Still the live plate. |
| A02 | Character idle | YES, before this ZIP | YES | YES | `lounge-figure.webp` | Not in this ZIP. Idle still on the play screen. |
| A03 | Character leg | YES, before this ZIP | YES | YES | `stopa_plus.gif` | ZIP copy is a different file. Live pixel-perfect GIF was kept. |
| A04 | Character delighted | YES, in ZIP and already live | YES | YES | `smile_plus.gif` | SHA-256 matches the live file. Controller unchanged. |
| A05 | Character wow | YES, in ZIP and already live | YES | YES | `wow_plus.gif` | SHA-256 matches the live file. Controller unchanged. |
| A06 | Logo | YES | YES | YES | `/assets/midnight-lounge/ui/ui_logo_midnight_lounge.png` | 1774×887 → 1024×512. Visible on the play screen. |
| A07 | Menu plate | NO | NO | NO | `menu.webp` | MISSING. Ski menu plate still used. |
| A08 | Menu figure | NO | NO | NO | `jumper/menu-foreground.webp` | MISSING. |
| A09 | Falling snow | n/a | YES | YES | `SkyJumpAtmosphere.svelte` | Snow render removed. Component stays mounted. Play screen has no `.snow`. |
| A10 | Browser title | YES, before this ZIP | YES | YES | `PUBLIC_GAME_TITLE` | Tab title “Midnight Lounge”. |
| A11 | Loader copy | YES, before this ZIP | YES | YES | `LoaderArtwork.svelte` | Not reopened this pass. |
| A12 | Brand tagline | YES | YES | YES | `SkyJumpBrand.svelte` | “OWN THE NIGHT”. Fits the 168px brand box. |
| A13 | Menu copy | YES | YES | YES | `SkyJumpMainMenu.svelte` | Kicker “VIP CASINO EXPERIENCE”. Subtitle “Luxury lounge · five reels · premium features”. Menu plate and figure are still the old art. |
| B01 | Slot frame | YES | YES | YES | `ui/decor/ui_slot_board_frame_midnight_lounge.png` | 1254 → 1024. Hole aligned to the five windows. Symbols sit in the cells. |
| B02 | P1 | YES | YES | YES | `symbols/sym_p1_champagne.png` | Paytable rendered Champagne at 1024. |
| B03 | P2 | YES | YES | YES | `sym_p2_crystal_cocktail.png` | Paytable rendered Crystal Cocktail. |
| B04 | P3 | YES | YES | YES | `sym_p3_masquerade_mask.png` | Paytable rendered Masquerade Mask. |
| B05 | M1 | YES | YES | YES | `sym_m1_red_stiletto.png` | Paytable rendered Red Stiletto. |
| B06 | M2 | YES | YES | YES | `sym_m2_gold_watch.png` | Paytable rendered Gold Watch. |
| B07 | M3 | YES | YES | YES | `sym_m3_luxury_perfume.png` | Paytable rendered Luxury Perfume. |
| B08 | L1 | YES | YES | YES | `sym_l1_velvet_rope.png` | Paytable rendered Velvet Rope. |
| B09 | L2 | YES | YES | YES | `sym_l2_gold_lounge_key.png` | Paytable rendered Gold Lounge Key. |
| B10 | L3 | YES | YES | YES | `sym_l3_red_rose.png` | Idle board and paytable. |
| B11 | S | YES | YES | YES | `sym_s_vip_invitation.png` | Paytable rendered VIP Invitation. |
| B12 | C | YES | YES | YES | `sym_c_concierge_bell.png` | Paytable rendered Concierge Bell. |
| B13 | Y | YES | YES | YES | `sym_y_mystery_gift.png` | Paytable rendered Mystery Gift. |
| B14 | Thermal | YES | YES | YES | `sym_feat_golden_spotlight.png` | Paytable rendered Golden Spotlight. ID unchanged. |
| B15 | Gate | YES | YES | YES | `sym_feat_vip_upgrade_card.png` | Paytable rendered VIP Upgrade. ID unchanged. |
| B16 | Judge | YES | YES | YES | `sym_feat_lounge_dealer.png` | Paytable rendered Lounge Dealer. ID unchanged. |
| B17 | Head Judge | YES | YES | YES | `sym_feat_pit_boss.png` | Paytable rendered Pit Boss. ID unchanged. |
| B18 | Rejump | YES | YES | YES | `sym_feat_encore.png` | Paytable rendered Encore. ID unchanged. |
| B19 | Wind Key | YES | YES | YES | `sym_feat_black_access_pass.png` | Paytable rendered Black Access Pass. ID unchanged. |
| B20 | Board special | YES | YES | YES | `sym_feat_midnight_crown.png` | Paytable rendered Midnight Crown. ID unchanged. |
| B21 | Token T1 | YES | YES | YES | `sym_token_t1_bronze_guest.png` | Paytable chip. Value stays code-rendered. |
| B22 | Token T2 | YES | YES | YES | `sym_token_t2_silver_member.png` | Paytable chip. |
| B23 | Token T3 | YES | YES | YES | `sym_token_t3_gold_vip.png` | Paytable chip. |
| B24 | Token T4 | YES | YES | YES | `sym_token_t4_platinum_elite.png` | Paytable chip. |
| B25 | Token T5 | YES | YES | YES | `sym_token_t5_black_diamond.png` | Paytable chip. |
| B26 | Token T6 | YES | YES | YES | `sym_token_t6_royal_ruby.png` | Paytable chip. Not the Midnight Crown. |
| B27 | Stage arrival | YES | YES | PARTIAL | `ui/ui_stage_arrival.png` | ID `RUN_UP`. Label `ARRIVAL` via `loungeShown`. Icon not on the idle HUD. |
| B28 | Stage VIP entry | YES | YES | PARTIAL | `ui/ui_stage_vip_entry.png` | ID `TAKEOFF`. Label `VIP ENTRY`. |
| B29 | Stage inner lounge | YES | YES | PARTIAL | `ui/ui_stage_inner_lounge.png` | ID `FLIGHT`. Label `INNER LOUNGE`. |
| B30 | Tier Velvet Room | YES | YES | PARTIAL | `ui/ui_tier_velvet_room.png` | ID `LARGE_HILL`. |
| B31 | Tier Gold Room | YES | YES | PARTIAL | `ui/ui_tier_gold_room.png` | ID `SKI_FLYING`. |
| B32 | Tier Diamond Lounge | YES | YES | PARTIAL | `ui/ui_tier_diamond_lounge.png` | ID `WORLD_CUP`. |
| B33 | Tier Midnight Suite | YES | YES | PARTIAL | `ui/ui_tier_midnight_suite.png` | ID `PERFECT_V`. |
| B34 | Board glass | n/a | YES | YES | CSS `.board-glass` | Burgundy to black, gold inset edge. Breathe peak is opacity 0.82. No blue tint. |
| C01 | Spin | LEGACY_REFERENCE | CODE_RENDERED | YES | `MidnightLoungeBetUI` / `BetUISpinButton` | PNG kept, not preloaded. Code ring is 132px. A physical mouse click on the visible center starts the existing `bet` path. |
| C02 | Stop | LEGACY_REFERENCE | CODE_RENDERED | YES | same spin control | Same button. Mouse click on the visible STOP face uses `stopRound` / `stopButtonClick`, including the existing no-op while the V2 presentation lock is open. |
| C03 | Auto | LEGACY_REFERENCE | CODE_RENDERED | YES | `BetUIIconButton` | Toggle opens the auto modal or clears the counter. Active state is the gold face plus a count badge. |
| C04 | Turbo | LEGACY_REFERENCE | CODE_RENDERED | YES | `BetUIIconButton` | `aria-pressed` follows `stateBet.isTurbo`. |
| C05 | Buy Bonus | NOT_REQUIRED | CODE_RENDERED | YES | `BetUITextButton` | Opens the existing buy modal. No C05 PNG. |
| C06 | Menu | NOT_REQUIRED | CODE_RENDERED | YES | `BetUIIconButton` | Opens the utility flyout. |
| C07 | Exit | NOT_REQUIRED | CODE_RENDERED | YES | same menu control | While the flyout is open the control is the close icon. |
| C08 | Info | NOT_REQUIRED | CODE_RENDERED | YES | flyout | Opens the rules modal. |
| C09 | Paytable button | NOT_REQUIRED | CODE_RENDERED | YES | flyout | Opens the paytable modal. |
| C10 | Settings | NOT_REQUIRED | CODE_RENDERED | YES | flyout | Opens settings. |
| C11 | Sound | NOT_REQUIRED | CODE_RENDERED | YES | flyout | Toggles master volume between 0 and 50. Icon swaps. |
| C12 | Bet +/− | NOT_REQUIRED | CODE_RENDERED | YES | `BetUIStepper` | Same option stepping as the Pixi buttons. |
| C13 | Language | NOT_REQUIRED | CODE_RENDERED | YES | flyout | EN / PL via `switchLanguage`. The old dock never mounted this control. |
| C14 | HUD frame | NOT_REQUIRED | CODE_RENDERED | YES | CSS wings | Ice frame is not mounted. PNG remains on disk. |
| C15 | HUD tile | NOT_REQUIRED | CODE_RENDERED | YES | `BetUIValuePanel` | Lacquer panels. Tile PNG is not preloaded. |
| D01 | Big win title | YES | YES | YES | `ui/wins/ui_win_big_midnight_lounge.png` | Already 1774×887. Showcase shows title and `12.5×`. |
| D02 | Mega win title | YES | YES | YES | `ui_win_mega_midnight_lounge.png` | Showcase `64×` on the soft plate. |
| D03 | Super win title | YES | YES | YES | `ui_win_super_midnight_lounge.png` | Showcase `220×` on the grand plate. |
| D04 | Max win title | YES | YES | YES | `ui_win_max_midnight_lounge.png` | Showcase amount on the grand plate. |
| D05 | Royal win title | YES | YES | YES | `ui_win_royal_midnight_lounge.png` | Player label `ROYAL WIN`. Event id stays world record. |
| D06 | Royal overlay | YES | YES | YES | `overlays/ui_overlay_royal_midnight_lounge.png` | 1672×941 → 1024×576. Shared, not copied per tier. |
| D06-SOFT | Soft win overlay | YES | YES | YES | `ui_overlay_win_soft_midnight_lounge.png` | BIG and MEGA. Plate opacity 0.46, mix-blend-mode soft-light. Backdrop for those tiers is rgba(28,10,16,0.1) to rgba(8,4,8,0.2). The reel stage is no longer blurred during the win, so the board stays readable. Grand and Royal plates stay at opacity 1 and blend normal. |
| D06-GRAND | Grand win overlay | YES | YES | YES | `ui_overlay_win_grand_midnight_lounge.png` | SUPER and MAX. |
| D07 | Free spins banner | YES | YES | YES | `ui/bonus/ui_bonus_free_spins_midnight_lounge.png` | Already 1774×887. Showcase loaded it. |
| D08 | Retrigger banner | YES | YES | YES | `ui_bonus_retrigger_midnight_lounge.png` | Showcase rendered the banner at 1774×887. |
| D09 | Tier upgrade banner | YES | YES | YES | `ui_bonus_tier_upgrade_midnight_lounge.png` | 1774×887 → 1024×512. Dev showcase rendered the TIER UPGRADE banner. |
| D10 | Velvet Room banner | YES | YES | YES | `ui/bonus/ui_mode_velvet_room.png` | Showcase rendered the banner at 1024×512. ID `LARGE_HILL`. |
| D11 | Gold Room banner | YES | YES | YES | `ui_mode_gold_room.png` | Showcase rendered the banner. ID `SKI_FLYING`. |
| D12 | Diamond Lounge banner | YES | YES | YES | `ui_mode_diamond_lounge.png` | Dev showcase rendered the banner at 1024×512. ID `WORLD_CUP`. |
| D13 | Midnight Suite banner | YES | YES | YES | `ui_mode_midnight_suite.png` | Dev showcase rendered the banner at 1024×512. ID `PERFECT_V`. |
| D14 | Luxury burst | YES | YES | YES | `fx/fx_luxury_burst_gold.png` | Rendered in the win celebration at 1254×1254. Timing unchanged. |
| D15 | Ruby-gold glint | YES | YES | YES | `fx/fx_glint_ruby_gold.png` | Rendered in the win celebration at 1254×1254. |
| D16 | Payline spark | NO | NO | NO | old `fx_payline_spark_head.png` | Left on SkyJump art. |
| D17 | Payline glint | NO | NO | NO | old `fx_payline_end_glint.png` | Left on SkyJump art. |
| D18 | Win ring | NO | NO | NO | old `fx_win_glow_ring.png` | Left on SkyJump art. Seen behind the big-win title. |
| D19 | Coin sparkle | NO | NO | NO | old `fx_coin_sparkle.png` | Left on SkyJump art. |
| D20 | Small sparkle | NO | NO | NO | old `fx_small_sparkle.png` | Left on SkyJump art. |
| D21 | Screen flash | NO | NO | NO | old `fx_screen_flash_accent.png` | Left on SkyJump art. |
| E01 | Paytable header | NO | NO | NO | `headers/ui_header_paytable.png` | Pending. Mounted in the 520×88 header slot. Old crest still visible. |
| E02 | How-to header | NO | NO | NO | `headers/ui_header_how_to_play.png` | Pending. Small crest on the How to Play card. |
| E03 | Features header | NO | NO | NO | `headers/ui_header_features.png` | Pending. Small crest on the Free Spins card. |
| E04 | Info header | NO | NO | NO | `headers/ui_header_info.png` | Pending. Mounted in the 520×88 Game Info header slot. |
| E05 | Divider | NO | CODE_RENDERED | YES | gold rule + diamond | Player-facing divider is code. `decor/ui_divider_ice.png` is not mounted. |
| E06 | Corner ornament | NO | CODE_RENDERED | YES | gold corner strokes | Player-facing corners are code. `decor/ui_corner_ornament.png` is not mounted. |
| E07 | Panel topper | NO | CODE_RENDERED | YES | gold top rule | Player-facing topper is code. `decor/ui_panel_topper.png` is not mounted. |
| E08 | Mode badge plate | NO | NO | NO | `decor/ui_mode_badge_plate.png` | Pending. Still the Buy Bonus header image. The left room HUD no longer uses this plate. |
| E09 | Status plate | NO | CODE_RENDERED | YES | `SkyJumpV2StatusPlate.svelte` | Burgundy/black lacquer, warm-gold edge, 64px tall, 340px wide (about 80% of the 425px reel grid). The blue SkyJump `ui_status_plate.png` is no longer mounted. |
| E10 | Paytable lede | YES | YES | YES | `SkyJumpV2PayTable.svelte` | “5×5 Midnight Lounge slot”. Symbol and feature names follow the lounge art. |
| E11 | Rules body | YES | YES | YES | `SkyJumpV2GameRules.svelte` | Opened in the rules modal. Room, stage, and feature wording is lounge copy. Mechanics and numbers are unchanged. |
| E12 | Buy sentence | YES | YES | YES | `SkyJumpV2BuyBonus.svelte` | “Choose a free-spin room.” Burgundy shell, code − / + and room buttons. Header crest is still the old plate (E08). |
| E13 | Hill chip | YES | YES | YES | `SkyJumpBrand.svelte` | `BASE` shows MAIN LOUNGE. Math ids unchanged. |
| E14 | Modal kicker | YES, before this ZIP | YES | YES | Midnight Lounge kicker | Not redone. |
| E15 | Rules title | YES, before this ZIP | YES | YES | i18n display string | Lookup key `SKYJUMP RULES` unchanged. |
| F01 | Oxanium | n/a | n/a | n/a | `SkyjumpDisplay` | NOT_REQUIRED. |
| F02 | Inter | n/a | n/a | n/a | `SkyjumpUI` | NOT_REQUIRED. |
| F03 | Optional gold face | NO | NO | NO | none | REVIEW. Not blocking. |
| G01 | BGM 1 | YES | YES | YES | `midnight-vip-1.mp3` | Background playlist. Loops with G02. |
| G02 | BGM 2 | YES | YES | YES | `midnight-vip-2.mp3` | Background playlist. Loops with G01. |
| G03 | BGM 3 | n/a | n/a | n/a | none | Playlist is two tracks. |
| G04 | UI clicks | n/a | n/a | n/a | `SKYJUMP_SFX` sprite | NOT_REQUIRED this pass. |
| G05 | Feature stingers | YES, 21 files | YES | PARTIAL | `/assets/midnight-lounge/audio/sfx_*.mp3` | Same hook names. `sfx_token_reveal.mp3` now plays the lounge file instead of the old trimmed wav. `sfx_scatter_land.mp3` returned 200. Not every hook was heard. |
| H01 | v1 weather | n/a | n/a | n/a | unmounted | NOT_REQUIRED. |
| H02 | v1 reel icons | n/a | n/a | n/a | unmounted | NOT_REQUIRED. |
| H03 | v1 jumper flight | n/a | n/a | n/a | unmounted | NOT_REQUIRED. |
| H04 | v1 result cards | n/a | n/a | n/a | unmounted | NOT_REQUIRED. |
| H05 | GIF zip backups | n/a | n/a | n/a | `asset-backup/lounge-gifs/` | NOT_REQUIRED at runtime. |
| H06 | Dev showcase | n/a | n/a | n/a | dev inspector | NOT_REQUIRED. Showcase labels use the lounge names. The fixture picker still says “World Record (book)”. |
| H07 | Math / protocol | n/a | n/a | n/a | config and event ids | NOT_REQUIRED. Not renamed. |

## Unmapped audio

Left in the ZIP only. No runtime hook.

| File | State | Possible existing hooks, not wired |
|---|---|---|
| `Quick_reverse_whoosh_#1-1790347183824.mp3` | UNMAPPED_AUDIO_SOURCE | `sfx_wind_transition`, `sfx_wind_charge`, reel start. None of those were retargeted to this file. |
| `Soft_triumphant_crys_#2-1790347362309.mp3` | UNMAPPED_AUDIO_SOURCE | `sfx_world_record`, `sfx_max_win`, `sfx_bonus_end`. The same-name lounge files already fill those hooks. |

## Code BetUI (replaces C01–C15 raster production)

C01–C15 stay code-rendered. Their PNGs remain legacy reference and are not preloaded. No new raster BetUI faces.

Spin click bug: `.ml-betui` is `pointer-events: none` so the Pixi canvas keeps clicks outside the HUD. The wings set `pointer-events: auto`, which is why +/−, Buy, Auto, Turbo, and Menu already worked. The spin button did not, so `elementFromPoint` at the visible center returned the canvas. Fix is `pointer-events: auto` on the `<button>` and `pointer-events: none` on the decorative ring and face. The button calls the existing `onSpin` → `betFromIdle` / `stopRound` path. No second spin implementation.

Sizing tokens on `.ml-betui`: `--ml-spin-size: 132px` (was 116), `--ml-utility-size: 46px` (was 40), `--ml-gap-tight: 4px` inside a group, `--ml-gap-group: 12px` between groups, `--ml-value-height: 52px`, `--ml-buy-width: 156px`, `--ml-buy-height: 46px` (was about 128×42), `--ml-balance-width: 188px`, `--ml-step-size: 48px`, `--ml-step-width: 155px`, `--ml-dock-height: 128px`, `--ml-wing-height: 104px`. Dock width `min(1200px, calc(100% - 28px))`, bottom 10px. The bet control is one joined stepper. Value numbers are 21px. Labels are 9px. The left wing is `justify-content: flex-start` with 16px outer padding and 44px before the spin cradle, so Balance sits toward the outer edge and the stepper follows it.

Measured on the 1280×720 stage inside the desktop preview: spin 132×132, utility buttons 46×46, Buy Bonus 156×46, stepper 48 + 155 + 48 (253px outer), balance panel 188×52, win panel 132×52, dock 1200×128. The left group is 453px, 82% of the 555px left wing. Status plate 96% of the slot column by 86px, centered, clear of the spin, with no `<img>`. The label and the detail share that inner field and wrap instead of leaving the lacquer. The right wing sizes are unchanged. The menu button sits inside the right wing. The character shoe stays clear of the dock.

Physical clicks on that resized wing, using screenshot coordinates: − moved the bet $1.00 → $0.50, + moved it back to $1.00, SPIN became STOP and the machine entered `bet`, and BUY BONUS opened the room modal. Each click landed on the visible control.

Earlier physical clicks on the 1280×720 stage: SPIN became STOP and the machine entered `bet`; STOP hit the same button while the round was locked by the existing presentation overlay; − moved the bet $1.00 → $0.50 and + moved it back; BUY BONUS opened the room modal; AUTO opened the count modal; TURBO toggled on; MENU opened INFO, PAYTABLE, SETTINGS, SOUND, and LANGUAGE. The status plate showed READY, then NO WIN 0.0x, with no blue image.

Physical mouse clicks (screenshot coordinates, not `element.click()`):

| Control | Result |
|---|---|
| SPIN | Hit the button. Label became STOP, machine `bet`, round ran. Repeated from idle, including with Turbo on. |
| STOP | Hit the visible STOP button during a bonus. Uses the existing `stopRound` guard: while `overlayOpen` is set by the V2 presentation lock, the click does not broadcast `stopButtonClick`. Same rule as the old Pixi control. |
| − / + | Bet stepped $2.00 → $1.00 and $1.00 → $2.00. |
| BUY BONUS | Opened the buy-bonus room modal. |
| AUTO | Opened the auto-spin count modal. Auto was off; the click did not start a counter. |
| TURBO | Toggled on (`aria-pressed`, inspector “turbo on”), then off. A later SPIN click with Turbo on still started a round. |
| MENU / EXIT | Opened the flyout, then closed it. |
| INFO | Opened Game Info. |
| PAYTABLE | Opened the paytable. |
| SETTINGS | Opened the volume settings. |
| SOUND | Toggled SOUND ON → SOUND OFF, then back ON. |
| LANGUAGE | Opened EN / PL. PL switched labels (KUP BONUS, ZAKŁAD). EN restored them. |

Space, after the source select was blurred, started a fixture round (balance $1,239.50 → $1,240.30, total win 1.8×) and returned to SPIN.

## CODE REEL PRESENTATION

Presentation only. Math, RTP, payouts, symbol ids, book events, feature resolution, and the replay contract are unchanged. B01–B33 asset statuses are unchanged. B34 stays one shared burgundy/black glass panel.

The V2 board is five clipped vertical strips in `SkyJumpV2Board.svelte`. Each `.reel` hides overflow and holds one `.reel-strip`. The strip translates as a single unit, downward: symbols enter from above. Visible rows stay 5. Logical cell bounds are invisible. Per-cell border, radius, background, inset shadow, and the old tile-glass breathe are gone. Hit, preserved, and world-record states use a drop-shadow on the art. The shared `.board-glass` remains behind every reel. The Midnight Lounge frame (`ui_slot_board_frame_midnight_lounge.png`) stays above the strips, so the vertical mullions cover the reel gaps. There is no horizontal grid.

Timing lives on `V2_TIMING` (`reelStartStaggerMs`, `reelStopStaggerMs`, `reelTravelMs`, `reelTravelSlots`, `reelSettleMs`). Reel 1 starts at 0. Each next reel adds the start stagger. Later reels shorten travel by `startStagger - stopStagger` so the land gap stays the stop stagger. Settle is a few pixels of downward overshoot, then back to 0. Travel ease is 20% acceleration, about 58% fast cruise, 22% deceleration.

| | Start stagger | Travel slots | Reel 1 travel | Stop stagger | Settle |
|---|---:|---:|---:|---:|---:|
| Normal | 300ms | 30 | 1800ms | 220ms | 160ms |
| Turbo | 90ms | 15 | 600ms | 70ms | 80ms |
| Catch-up | 0 | 0 | 0 | 0 | 0 |

Normal strip length is 35 (30 travel + 5 previous). Turbo strip length is 20 (15 travel + 5 previous). `prefers-reduced-motion` shortens to a 40ms start, 30ms stop, travel capped at 280ms, 5 slots, and no settle. Catch-up and `reelTravelMs <= 0` snap the book board with no strip.

Filler is the published strip alphabet only: P1–P3, M1–M3, L1–L3, S, and C. That is the unique set on `reelModel.strips` and on every free-spin tier strip in `skyjump_v2_config.json` (BASE, LARGE_HILL, SKI_FLYING, WORLD_CUP, PERFECT_V). Those alphabets match, so `reelFillerBand` does not invent a per-mode subset. Y, T1–T6, THERMAL, GATE, JUDGE, HEAD_JUDGE, REJUMP, WIND_KEY, and SPECIAL_WORLD_RECORD are post-stop outcomes. They can land from the book. They are not spun as filler. Filler is never written to `board`.

Travel eases in, runs fast, then eases out inside the same duration. The last part of travel adds the existing overshoot (at most 5px), and the settle eases back to 0. A moving reel gets a soft vertical blur on the way in and out, and `blur(1.25px)` only at peak speed. The blur is on the symbols, not the gold frame. Landing is a 1.01 scale and a short gold glow on that reel, for the settle duration, then it is gone. Symbol slots stay flush. The air between icons is transparent padding in the PNGs. A shared scale-up would crop the champagne art, so the art scale is unchanged.

When a reel finishes, that column is replaced with the reveal-event column. After the last reel lands, `board` is set to the full reveal board again. Paylines, highlights, tokens, and feature handlers still address `reel` / `row`. Payline Y uses the symbol pitch (`board height / 5`). Glass is under the strips. The frame (`z-index` 6) is over the grid (`z-index` 1).

Measured on `/dev-preview?fixture=01` (no-win board), 16ms samples. Nine of ten normal spins; one sample hitched on the main thread and is omitted:

| | Reel 1 start after click | Start gaps | Reel 1 land | Land gaps | Click to last reel settled | Peak nodes | After spin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Normal, 9 spins | 33–55ms | 288–310ms | 1986–2004ms | 207–231ms | 2863–2884ms | 175 | 25 |
| Turbo, 5 spins | 29–61ms | 88–101ms | 709–734ms | 60–80ms | 987–1014ms | 100 | 25 |

All ten normal spins and all five turbo spins settled on the fixture board (reel 1 P1, reels 2–5 S). No blank `data-symbol`. Strip length peaked at 35 normal and 20 turbo, then returned to 25 symbols. A live-math spin on the 1280×720 stage showed the same cascade: soft, then a long fast cruise, then land, with translateY moving from about −2490px through the strip to 0.

Every one of those spins ended with no spinning class, no blur, and `translateY` at 0. Filler ids stayed inside P/M/L/S/C. No reel-animation console errors.

Feature samples, same renderer, filler still that alphabet. Settled symbols matched the sample final boards: `feature-01` C/M1/T1, `feature-03` C/JUDGE/M1/T1, `feature-05` C/HEAD_JUDGE/M1/T2, `feature-08` C/M1/T1/THERMAL, `feature-11` C/GATE/M1/T2. Win highlights and token badges were on the landed cells.

## Modal chrome and left room HUD

Generic modal chrome is code: burgundy-to-black lacquer, warm-gold edge, inset glow, gold corner strokes, gold divider. The blue SkyJump popup shell, ice divider, ice corners, and ice topper are not mounted. Settings uses the same lacquer panel; volume sliders use a gold accent and the existing volume bindings.

Header art stays in a stable slot, `V2_MODAL_HEADER`, 520×88 (about 5.9:1). E01 and E04 fill that slot. E02 and E03 are the smaller card crests. E08 is the Buy Bonus header. Those five PNGs are still the old crests and are not done.

The free-spins HUD is the same `bonusHud` state, rendered as a 200px vertical panel on the left of the slot frame. It is no longer the horizontal ice bar translated above the board. On the 1280×720 stage during Velvet Room: x 188, y 51, 200×365, right edge 16px left of the frame (frame x 404). It does not cover the frame, the 340px result plate, the spin button, or the character. Base game hides it. While the feature is active it shows room, Arrival, VIP Entry, Inner Lounge, Global, Free Spins remaining, played count, bonus total, and token floor. Mystery targets, notices, and the dev inspector lines appear only when that state is set.

## Still on SkyJump art on purpose

Menu plate and menu figure, modal header crests E01–E04 and E08, payline and win-ring FX, BGM. The READY / win plate, modal shell, divider, corners, and left room HUD are code-rendered. BetUI faces C01–C15 are code-rendered; their PNGs stay in the repo as legacy reference and are not preloaded. Stage icons are not drawn on the left HUD. The tier emblem still sits in that panel when a room is active.

## Player-facing room names

| Internal id | On screen |
|---|---|
| `BASE` | MAIN LOUNGE |
| `LARGE_HILL` | VELVET ROOM |
| `SKI_FLYING` | GOLD ROOM |
| `WORLD_CUP` | DIAMOND LOUNGE |
| `PERFECT_V` | MIDNIGHT SUITE |
| `RUN_UP` | ARRIVAL |
| `TAKEOFF` | VIP ENTRY |
| `FLIGHT` | INNER LOUNGE |
| world-record win copy | ROYAL WIN |

## Start screen

START SCREEN: **CODE + ART IMPLEMENTED**

Assets: `assets/midnight-lounge/ui/start_screen.png`, `assets/midnight-lounge/ui/ui_click_anywhere_to_continue_midnight_lounge.png`.

The entrance covers the 1280×720 stage (`object-fit: cover`, centered). The continue plaque sits at 77% of the stage height, 600px wide, aspect kept. It fades up, then breathes (opacity 0.82–1, scale 0.99–1.015, 2.1s). Continue is the whole stage, plus Space and Enter, and only after `stateApp.loaded`. The click starts the existing BGM unlock. Transition: intro to black 300ms, hold 100ms, black to the slot 400ms.

Old blue loader: **NOT MOUNTED**. `LoaderArtwork.svelte`, `LoadingScreen.svelte`, and `TransitionAnimation.svelte` stay on disk. `PressToContinue.svelte` stays mounted for win and free-spin prompts, not for startup.
