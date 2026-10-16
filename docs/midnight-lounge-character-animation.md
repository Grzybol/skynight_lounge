# Midnight Lounge character animation V2

Two animated characters on the 1280x720 scene: the **bartender** (left) and the
**woman** (right, replaces the old webp/GIF figure). Both play metadata-driven
30 fps clips, run independent idle schedulers and react to the board's existing
win events.

## Assets

The 16 supplied ZIPs (8 woman, 8 bartender V3) are **not** in the repo. They stay in the
operator's Downloads folder and are converted by:

```
python -I tools/midnight-lounge/build-character-anims.py [--zips DIR] [--quality 90] [--only woman|bartender]
```

The script validates every JSON and PNG (frame order, frame size, sheet size,
frame rectangle inside the sheet, 150 frames, no empty frame), cuts each frame
with the **explicit x/y/w/h from the JSON** (never from the grid), and writes to
`frontend/apps/poc/static/assets/midnight-lounge/characters/`:

| file | content |
| --- | --- |
| `<animation id>.pack` | 150 lossless-alpha WebP frames (554x740) concatenated |
| `manifest.json` | per animation: fps, frame count, per-frame byte offset/size |
| `validation.json` | frame accounting + loop-seam diffs |

Both source layouts are read (old: 5 sheets of 7x5, 554x740; V3 bartender: 30 sheets of
1x5, 562x748, `sheets` as file names). `--only bartender` rebuilds just the bartender and
merges into `manifest.json`, leaving the woman's packs untouched. Per character frame
size is `manifest.frames`.

Validation result (woman, original package): 8 packages, 1200 frames, 5 sheets each, 5 sheets each (4 x 35 + 10),
sheet size 3894x3712 (final sheet is smaller than the nominal grid, which is why
coordinates come from the JSON), 30 fps, 150 frames, 0 empty frames.

Zip -> id mapping lives in the script (`MAP`) and in
`src/game/loungeCharacters/config.ts` (`CHARACTER_ANIMATIONS`). Pack sizes: woman
~11.5 MB per clip, bartender ~5.3 MB per clip, 119 MiB total in the build.

## Why packs and not atlases or Pixi textures

- The characters are DOM `<canvas>` layers, like the old figure (`SkyJumpBackground`
  is plain HTML under the Pixi stage). No Pixi texture is involved.
- A decoded 3894x3712 RGBA sheet is ~58 MB; 70 of them are ~4 GB. One animation
  (5 sheets) is ~290 MB; 150 full frames are ~246 MB. Native sheets (even
  per-animation) are not viable, and 3894 px is close to the 4096 limit of common
  GPUs.
- Runtime keeps **compressed** bytes per pack and decodes frames on demand into
  `ImageBitmap`s, a sliding window of ~25 per character (~40 MB each).

## Runtime (`src/game/loungeCharacters/`)

| module | role |
| --- | --- |
| `config.ts` | ids, per-character tuning (idle window, cache sizes), placement |
| `timeline.ts` | pure time -> frame math, stall handling |
| `idleScheduler.ts` | pure variation pick / delay / win-priority rules |
| `framePackStore.ts` | streamed pack download, bounded per-character LRU |
| `CharacterAnimationPlayer.ts` | canvas player: play / prepare / pause / resume / cancel / destroy |
| `CharacterController.ts` | idle loop, variations, win arbitration, epoch-guarded callbacks |
| `loungeWinCue.ts` | win-reveal bus (`emitLoungeWin`, `syncLoungeFigureWin`, `announceSmallWin`) |
| `createCharacter.ts` | wiring + dev registry |

UI: `components/skyjump/LoungeCharacter.svelte` (one canvas per character),
mounted twice from `SkyJumpBackground.svelte`.

### Playback

- Frame = `floor(elapsed * fps / 1000)`: correct on 60/120/144/240 Hz displays.
- A gap above 250 ms (throttled tab) shifts the clip clock instead of skipping;
  `visibilitychange` pauses/resumes.
- Packs stream into one preallocated buffer, so a clip starts after its first
  frames are decoded plus a bandwidth check (projected download finishes before
  80% of the clip has played). If bytes run out mid-clip the clock is held, never
  skipped, and the last frame stays visible.
- `play(id)` awaits `prepare(id)`; the current clip keeps rendering until the
  replacement has its first 6 frames decoded. A newer `play()` supersedes an older
  one (request token). Completion callbacks carry the controller epoch, so a late
  "finished" from a replaced clip is ignored.
- 20 frames before a one-shot ends the controller pre-warms idle, so the cut back
  to idle is on the same animation tick as the last frame.

### Loading and memory

- Startup: only the two default idle packs (+ the small-win pack 4 s later).
- Idle variation: its pack is fetched 10 s before it plays.
- Big/mega: fetched on first use (streamed; see limitation below), then cached.
- Per-character pack LRU: woman 5 (idle, variation, mini, big, mega), bartender 4.
  The current clip, default idle and the pending variation are pinned.
- Bitmaps outside `[playhead-1, playhead+18]` (and the pending clip's start frames)
  are `close()`d every tick.

### Idle scheduler

Woman: the default idle loops 1-4 whole times (random, `idleLoopsMin/Max`), then a
random variation plays once (never the same twice in a row) and she returns to idle.
Bartender: the main idle plays 1-2 whole loops (5-10 s), then one of the secondary idle / three
interruptions (optional `variationWeights`). A time window (`idleVariationMinMs/MaxMs`) remains as the
fallback when no loop counts are set. Both are configurable in `CHARACTER_TUNING`. A spin start never restarts idle. A win cancels the
pending variation.

### Win events

The board already classifies wins (`classifyV2WinCelebration`, thresholds in
`winPresentation.ts`). Nothing in math or thresholds changed:

| existing signal | category | woman | bartender |
| --- | --- | --- | --- |
| `skyjumpV2Result` with win below the celebration threshold | mini | `woman_mini_win` | `bartender_mini_win` |
| celebration tier `big` | big | `woman_big_win` | `bartender_big_win` |
| tier `mega`, `super`, `max`, `worldRecord` | mega | `woman_mega_win` | `bartender_mega_win` |

Triggers (the win counter drives the characters; nothing in math or thresholds changed):

- A win **at or below the bet** triggers nothing; **above the bet** (x > 1) but below the celebration
  threshold gives `mini` once, when the result is revealed (`announceSmallWin` in `skyjumpV2Result`).
- A celebration (big and above) counts up for 8 s and pulses the final figure for 2 s (turbo: 3.4 s + 1.5 s).
  While it counts, `SkyJumpV2WinCelebration` asks for `mini` when the counter passes the bet, `big` at the
  big threshold and `mega` at the mega threshold; the tier's own category is always requested at the end.
- Wins **queue**, a win clip is never cut: a request above the playing clip waits (only the highest waiting
  one is kept) and starts the moment the clip ends. Big/mega clips play forward then in reverse at normal
  speed (10 s) and once in turbo (5 s); if a higher win is already waiting at the turning point the reverse is
  skipped. Idle and variations yield immediately. After the last win the character returns to idle.

During a celebration the room blur fades in and out (700 ms) with `data-win-plate`; the lounge plate is lifted
and fades with it, and the characters and bar stay in front (`data-win-focus`, which outlives the celebration
by the fade time). Mini wins do not blur.

## Placement (all configurable in `CHARACTER_PLACEMENT`)

Fractions of the play area, so the existing responsive scaling is kept.

- Woman: height 0.822 x play height, centre x 0.8406, bottom 0.962. Calibrated
  against the old figure's measured opaque footprint (x 885-1280, y 133-652 at
  1280x720).
- Bartender: height 1.1124, centre x 0.134, bottom 1.134 (final; +15% over V3, shoes at the
  same screen Y as V3/XL). A +28% step (1.236 / 1.1409) was judged too large and reduced by
  10%. That +28% step was +28% over the V3
  placement (0.965 / 1.126) with the shoes kept at the same screen Y (~772, off the bottom
  edge). +50% was tried: with the feet anchored the head leaves the screen, so 1.236 is
  the largest scale that keeps the whole head visible in every clip (mega-win bbox top
  y70). Earlier V3 values: height 0.965, bottom 1.126; before that 0.84 / 0.885.
  Values come from the actual alpha bounds (head y 77, shoes y 707 of 748). The BetUI bar
  (y >= 605) covers his lower legs; the reel board starts at x ~408 and his tray ends at
  x ~370.
- Draw order: plate (z 0) < characters (z 1) < board/HUD < win overlay; during
  big/mega the characters go to z 30, above the overlay. Canvases have
  `pointer-events: none`.

## Transitions

Every woman clip is trimmed by 3 frames (0.1 s) at the start and at the end
(`trimHeadFrames` / `trimTailFrames` in `CHARACTER_TUNING`, per character), which removes
the small hitch at clip joins. Her clips are 144 frames (4.8 s).

All 14 clips start and end on the idle pose (loop seam diff between last frame and
the idle first frame is ~1% of opaque pixels at most, same as idle's own loop
seam), so transitions are **hard cuts at frame boundaries**, not crossfades. A
crossfade between two different poses would only produce a double silhouette.

Known limitations:

- A higher-priority win interrupting another win/variation mid-clip is a pose cut
  (the previous clip is by definition not at its idle pose). It is rare and
  intentional.
- First big/mega win of a session streams its pack on demand. Locally this is
  instant; on a slow CDN the reaction can be delayed by the time to fetch the
  first few hundred KB and the bandwidth check above (idle keeps playing, never
  blank).
- 119 MiB of character packs ships with the build. `--quality 80` is ~26% smaller
  per frame if the Stake upload size needs trimming.

## QA

```
# dev server (port 3020 used for QA in this branch)
cd frontend/apps/poc && ../../node_modules/.bin/vite.cmd --host 127.0.0.1 --port 3020

# logic tests (no browser)
node --experimental-transform-types --import ./tools/midnight-lounge/register.mjs tools/midnight-lounge/test-characters.ts

# live browser QA (headless Chrome, screenshots in tools/qa/output/lounge-characters)
node tools/qa/lounge_characters_qa.mjs
```

Dev-only inspector: `/dev-preview` -> DEV PAYLINE INSPECTOR -> **CHARACTERS**
(select character, trigger any clip, idle/small/big/mega, rapid burst, live frame,
fps, pack cache). It is gated by `import.meta.env.DEV && localDemo` and is absent
from production builds.

## Scene props, start screen, win sounds

- **Looping props** (`plant_loop`, `guard_loop` packs, same pipeline: `build-character-anims.py --only plant|guard`):
  `LoopingProp.svelte` plays them with `CharacterAnimationPlayer` (shared pack cache, `propPlayer.ts`).
  Plants: two in the room in front of the thick columns (`ROOM_PLANTS`, play-area fractions), two on the start
  screen; copies start 2.1-2.3 s apart so they never sway in sync. Bodyguard: start screen only, 0.1 s trimmed from
  the start and the end of the loop. Placement is by ground point (`propLayout.ts`); the start-screen values were read
  from the previous start screen and mapped into the 4:3 stage (`y = 0.125 + 0.75 y`, `h = 0.75 h` at 16:9).
- **Start screen**: `start_screen.png` is the doorway artwork; the animated bodyguard, plants and the velvet-rope stanchion
  (`intro_stanchion.png`, over the right plant) are placed over it (`INTRO_*` in `propLayout.ts`). Leaving it: the background
  blurs for 0.45 s while the figures fade out, then 0.45 s of full-screen backdrop blur clearing over the slot.
- `woman_idle_1` (`feet2_przerywnik1_v1`) and `woman_idle_4` (`feet2_extra_przerywnik_v8`) are 1124x1496 (2x, same 3:4 aspect,
  ~101 MB each as lossless WebP). Manifest entries carry their own `w`/`h`; the player's canvas only grows and every frame is
  drawn scaled to it, so placement and on-screen size match the 562x748 clips.
- Slot frame: `ui_slot_board_frame_midnight_lounge.png` is the Art Deco frame; hole fractions live in `V2_SLOT_BOARD_FRAME`.

## Latest pass

- Woman packs come from `video_converter_batch.zip` (`*_v1` / `_v2` / `_v9`, all 562x748); `woman_big_win` keeps the earlier
  `bigwin_v1` clip (no v2 supplied), `woman_mega_win` is `bigwin_v2`. The two 1124x1496 packs are gone (the player still
  supports per-clip sizes via `w`/`h` in the manifest).
- Trims: bartender 0.1 s per end (3 frames), woman 0.2 s per end (6 frames).
- Plants sway at half speed (`PROP_RATE`, 5 s -> 10 s) on every screen; copies are offset into the loop (`offsetMs`).
- The start screen shows `start_loading.png` (a still of the finished scene) until the background, stanchion, bodyguard, both
  plants (first frame drawn) and the game are ready.
- Buy bonus button = the SKYNIGHT LOUNGE emblem (`ui_logo_midnight_lounge.png`), same 108x66 box as the old tile.
- Bartender clips come from `barman_nowe_animacje.zip` (`barman2_*_v1`, 562x748, lossless).
- The room / free-spins HUD tile left of the slot is gone. `SkyJumpBrand` stacks logo -> mode banner (special rooms only) ->
  free-spins banner with a generated `xN` count (spins remaining) in the top-right corner.
- BetUI: the WIN counter is centred on the bar (a spacer keeps the right-hand buttons in place), its label is 20 px, and the
  SPIN/STOP button is centred on the bar (its lower edge runs ~20 px past the screen bottom).
- `bet_increase_sound.mp3` (the "+" click) was cut to half its length (2.0 s -> 1.0 s, 40 ms fade); the duration meta follows.
- Plants: `background_prop_plant_v4` (same 562x748 frame and ground anchor). `woman_idle_4` plays 33 % faster (`CLIP_RATE`).
- Chimney smoke: `scene/smoke_frame_1..4.png` cross-faded at 30 fps by `game/loungeScene/chimneySmoke.ts` (one shared timer,
  per-chimney phase), 30 % opacity, drawn in the raised buildings layer; chimney tops are listed in `SkyJumpBackground.svelte`.
- Panels (`.pop-up-wrap`) use Marcellus at weight 700 (synthetic bold: the family ships one weight), except h2/h3 captions.

## Upscaled woman clips

- `woman_idle`, `woman_idle_alt`, `woman_idle_1`, `woman_idle_4`, `woman_mini_win` now come from the `*_upscaled` zips
  (1108x1480, lossless, ~128 MB each). They are stored in parts (`.pack`, `.pack.1`, `.pack.2`, <= 60 MB each, manifest `parts`)
  because GitHub rejects files above 100 MiB; the loader streams the parts back to back. `build-character-anims.py` splits
  automatically (`--split-only` re-splits an existing build).
- **OLD VERSION clips** (no upscaled source yet, still 562x748): `woman_idle_2`, `woman_idle_3`, `woman_big_win`,
  `woman_mega_win`. They are listed in `OLD_VERSION_CLIPS` (`loungeCharacters/config.ts`), flagged `[OLD]` in the dev
  CHARACTERS inspector and logged once in the dev console, and marked in the build script's `MAP`.
- Memory: a 1108x1480 frame decodes to ~6.5 MB; the player keeps ~25 per character.

## Woman clips: video_converter_batch_v2 (current)

All eight woman clips come from `video_converter_batch_v2.zip` (554x740, lossless, ~30 MB each). `feet2_bigwin_v3` is the only
big-win clip, so it serves big and mega (`woman_mega_win` is gone). This supersedes the upscaled pass above: those packs and the
`OLD_VERSION_CLIPS` list are now empty/unused (the multi-part pack support stays in the loader and build script).

## Scene update (video_converter_batch_v3 and background pack)

- Woman clips: `video_converter_batch_v3` (562x748, `bigwin_v4` serves big and mega).
- Slot scene back to front: `background_3_static.png` (= background_farthest) -> `clouds_prop.png` drifting band (top 46 % of the
  scene, 240 s per tile, CSS only) -> buildings (14-image pool, `buildingsPool.svelte.ts`: a random other image cross-fades in every
  10-20 s, identical placement) + 3 chimney smokes (left, middle, right; opacity 0.15) -> balustrade/floor -> plants.
- SPIN / STOP buttons: `spin_cartoon` / `stop_cartoon` (as `ui/betui2/spin.png`, `stop.png`).

## Headers, buy-bonus plate, modal size, BetUI

- The 15 section headers (`ui/headers/hdr_*.png`) are the byte-exact PNGs from `new_assets.zip` (2172x724). The buy-bonus screen's
  header is `ui/ui_buy_bonus_badge.png`: it was a 1024x341 leftover and is now the zip's "BUY BONUS" plate (2172x724, byte copy).
- Info / Paytable: the visible window is 57 px from every edge of the 1280x720 stage (`global.scss`).
- BetUI: panels are `border-box`, the WIN counter is centred on the bar, the turbo / auto / buy group is pushed against SPIN.
- Still low-res / lossy and not part of the lounge UI: `src/assets/skyjump/**/*.webp` (ski-era leftovers) and the skyjump_v2
  `ui_header_*` (info, how-to-play, ~950 px wide) used above the Info/Paytable cards.

## Ski-era assets removed

Deleted because nothing reachable from the app used them: `src/assets/skyjump/{jumper,reel-icons,result,weather}`, the ski menu /
gameplay / lounge-figure backgrounds, the dead components that imported them (`SkyJumpMainMenu`, `SkyJumpResultOverlay`,
`SkyJumpReelStrip`, `SkyJumpWeatherDraw`, `SkyJumpPayTable`, `SkyJumpRoleIcons`, `SkyJumpHudFrame`, `skyjumpArt.ts`), their
preload entries in `game/assets.ts`, the ski fallbacks in `static/assets/skyjump_v2` (logo, stages, tiers, modes, wins, bonus,
decor, ice/snow fx, ski symbols) and the unused garden / mine backgrounds. Still shipped from `skyjump_v2`: the info / paytable /
how-to-play / features headers, the world-record overlay, six fx sprites and the Pixi bet-UI buttons that `assets.ts` preloads.

## Big win and above (current)

- No separate big / mega clips for the bartender or the woman: `wins.mini`, `wins.big` and `wins.mega` all point to the win
  clip (`*_mini_win`, played once, never ping-pong). A request for the clip that is already playing is absorbed.
- Sound: `sfx_win_bigwin_universal.mp3` (5 s) for `WIN_BIG` and `WIN_MEGA`; `winReaction.ts` starts it once per 5 s window.
- Celebration length for big and every tier above: 4 s count + 1 s pulse = 5 s (turbo 3.4 + 1.5 s).
- No blur, no lifted plate, no characters over the BetUI: a light dimming layer (`.win-dim`, z 21, 38 % dark) fades in over the
  screen; the celebration (z 22) sits above it. Characters keep z 20.
- While a big win runs, the BetUI is `inert` (`stateGame.celebrationActive`, set by `SkyJumpV2Board`) and Space does not spin.

## Engine approval self-check fixes

Fixed after the guideline review (verified against a local mock RGS, a production build served statically, and a replay URL):
- 275 no Stake Engine loader; 223 viewport locks zoom (`maximum-scale=1, user-scalable=no`, `touch-action: manipulation`).
- 181 `rgs_url` accepted with or without scheme (`rgsBaseUrl`); 274 a failed authenticate shows a clear error screen and the game does not start.
- 242 the game opens on `defaultBetLevel`; 187 an active round's `round.amount` overrides it.
- 219 / 273 / 78 currency formatting: per-currency decimals (JPY 0), extra decimals for sub-cent amounts, XSC/XGC/XEC as `10.00 SC` / `10.00 GC`.
- 222 `/wallet/play` is never sent when balance < bet x mode cost (guard in `handleRequestBet`, spin disabled, visible note);
  228 Space only bets when idle and is ignored in menus and modals.
- 25 / 235: Info lists RTP and max win per mode (`modeStats.ts`, regenerate with `tools/skyjump/gen-mode-stats.py`) and a Controls card.
- 77 / 188 / 225 social mode: `utils-shared/social.ts` word table applied to all HTML text by `game/socialWording.ts`; baked "BUY BONUS" and
  "PAYTABLE" header art is replaced by text. Test: `node --experimental-transform-types tools/midnight-lounge/test-social.ts`.
- 171-174 replay: no wallet calls, currency / amount applied, bet and real cost shown, REPLAY restarts the event, load failure shows an error screen.

## Performance, fonts, FX (latest)

- Character / prop packs are now lossy WebP (quality 90, alpha stays lossless): 370 MB -> 93 MB in the repo, ~190 MB -> ~50 MB downloaded
  before the first spin. Rebuild: `python -I tools/midnight-lounge/build-character-anims.py --lossy-quality 90 --zips <dirs>`
  (omit `--lossy-quality` for lossless, packs above 90 MB are split automatically).
- Font: Luckiest Guy (`luckiest-guy-400.ttf`, one weight, bold by design) replaces Marcellus everywhere; the weight range is declared so the browser does not fake a bold.
- The SkyJump ice-blue FX and the world-record ice plate are removed; glints use `fx_glint_ruby_gold`, bursts `fx_luxury_burst_gold`, world record the royal overlay.
- Clouds sit higher (top part runs off the screen); bartender and woman are 15% smaller (feet anchored) and re-spaced from the slot.

## Slot frame, tier tiles, rolling blur (latest)

- `scene/slot_background_2.png` (behind symbols) and `slot_background_1.png` (frame, above symbols) are the supplied art extended from
  4 to 5 rows (a 155 px band of the middle row was duplicated, 1672x1096) because the game has 5 rows; bg2 got an alpha mask from the frame
  silhouette. The board is a flush 5x5 grid of cell pitches (`V2_SLOT_BOARD_FRAME`), so each symbol is centred on its frame window.
- Six tier tiles (`tiles/`, `tiles_blur/`, cropped to their solid bounds): low (L1-3), medium (M1-3), premium (P1-3), scatter (S),
  concierge_mystery (C, Y), feature (specials, Midnight Crown, tokens T1-T6). Mapping: `v2SymbolTier` in `symbolAssetRegistry.ts`.
- While a reel rolls the cells use `tiles_blur/` and `symbols_blur/`; they switch to the sharp art when the reel starts landing.
- Woman: `brightness(0.6)` (measured: mean luminance 87 vs the bartender's 52). Sky: `background_farthest-sky.png`; clouds: `clouds_prop_v1.png`.
- `ui_logo_midnight_lounge.png` from the new pack was NOT imported (it is the old Midnight Lounge logo; the SKYNIGHT LOUNGE emblem stays).

## Slot frame v2 (5x5 art), per-window tiles, tier sizes

- `slot_frame_layer1/2.png` (1672x941, true 5x5) replace the stretched 4-row frame. Window rectangles are in `V2_FRAME_WINDOWS`
  (the bottom row is a short window under the frame's bar): tier tiles are placed and sized per window (last row cut, not squashed).
- Settled reels are drawn above the frame (tiles z 7, symbols z 8-10 by tier); rolling reels stay under it. `.grid` has no stacking context of its own.
- Symbol size by tier (`V2_TIER_SCALE`, relative to cell height): low 0.6, medium 0.9, premium 1.35 (x1.5 per regular tier);
  scatter, concierge/mystery and feature use the premium size.
- Woman tone: `brightness(0.66) contrast(1.05)` (matched to the bartender's upper body).

## Frame v3 and tuning

- `slot_frame_layer1/2.png` (second delivery, uniform windows) are now `slot_background_1/2.png`; window rects in `V2_FRAME_WINDOWS`.
- Tier sizes: low 0.8, medium 1.04, premium 1.35 (x1.3 per regular tier). Woman: `brightness(0.85) contrast(1.05)`. SPIN/STOP image: `brightness(0.9)`.

## New BetUI and equal frame rows

- BetUI is image based, no bar behind it: `ui/betui2/{spin,stop,balance,bet_background,minus,plus,menu,autospin,turbo,bonus}.png`, placed by the
  visible bounds of each file on the 1280x720 stage (`HUD` / `L` in `MidnightLoungeBetUI.svelte`, layout from `new_betui_preview.png`).
  Texts (balance, bet, WIN, labels) are code, Luckiest Guy. The old SPIN/STOP `brightness(0.9)` was dropped with the old art.
  The bonus pill replaces the emblem as the buy-bonus button.
- Slot frame rows: the art's rows were 138 / 136 / 134 / 131 / 127 px tall. `SlotFrameLayer.svelte` redraws both frame layers as a top piece, five row
  bands stretched to one height (`V2_FRAME_BANDS`) and a bottom piece; tiles and symbols use one uniform window height (`V2_FRAME_WINDOWS.winH`).

## Frame v4 (100x100 windows) and v1 tier tiles

- `scene/slot_background_1.png` = `slot_background_100x100px_windows.png` (25 equal windows of ~98.5 art px on a 128 x 126.25 pitch, one band, no equalising needed).
  `scene/slot_window_bg.png` = `slot_frame_default_background.png`, drawn per window as the very first layer.
- Layer order of the slot: window backgrounds -> rolling symbols and their blurred tiles -> frame -> settled symbols and their tiles (over the frame).
- Tier tiles come from `slot_tile_backgrounds_tiers_v1_renamed.zip` (black corners turned transparent, cropped); the rolling versions are generated from them with a
  vertical motion blur (script was run once, see `tiles_blur/`). Tile and symbol are centred on the window (tile matches the window to the pixel; symbols sit 6 art px higher).
- Tier sizes relative to the window height: low 0.80, medium 0.84, premium 0.88 (5 % steps). BetUI elements (not SPIN/STOP) are 10 % smaller; the bet +/- circles are symmetric.

## Loading on slow connections

- Before: ~144 MB were requested while the start screen was still shown (all at once). Causes: a duplicated eager preload effect in the board, 1254 px symbol / tile / HUD PNGs
  (1.2-1.4 MB each for ~100 px on screen), variation and win packs prefetched during the intro.
- Now: symbols, rolling symbols and tier tiles are 512 / 384 px (still lossless PNG), HUD art 40 %, clouds half width (101 MB -> 20 MB in the repo); the preload of every symbol/tile
  waits for `warmGate` (opened when the player continues) and runs four at a time at low priority; character variation / win clips wait for the gate too; character packs and slot-scene images
  use low fetch priority, the start screen's own pieces (background, bodyguard, plants) high priority; the woman keeps all 6 packs in memory (no re-downloads).
- Start screen weight: ~58 MB (idle packs 14 MB + plant/guard 13.5 MB + images) instead of ~144 MB; after that ~50 MB more in the background.

## Slim frame, new +/- buttons, quality 80/60 (latest)

- Character / prop packs rebuilt at lossy WebP quality 80 (alpha lossless): `python -I tools/midnight-lounge/build-character-anims.py --lossy-quality 80 --zips ~/Downloads D:/ai_gif_upscaling/output`.
- Rolling-blur assets (`symbols_blur/`, `tiles_blur/`) are lossy WebP quality 60 (`.webp`; the sharp symbols and tiles stay PNG).
- Tier tiles come from `slot_tile_backgrounds_tiers_cartoon_named.zip` (black corners -> alpha, 384 px; blurred copies built from the same crop).
- `scene/slot_background_1.png` is `slot_background_100x100px_windows_slim.png` (1536x1024). Its 137.5x134 px windows sit on a 148.75x144.75 pitch
  (`V2_FRAME_WINDOWS`); `BOARD_GRID_W` is 440 so the windows stay about as large as before. Symbols are 5 % bigger (`V2_TIER_SCALE`) and
  centred on the window (`SYMBOL_LIFT = 0`).
- BetUI: new `betui2/minus.png` / `plus.png`; BONUS / TURBO / AUTO labels live inside their buttons so they press with the art; every
  control is 10 % smaller (each cluster shrinks towards its screen edge); switched-on buttons get a pulsing gold ring that stays under hover.
- Woman moved up (`bottomFrac` 0.955) so the BetUI no longer covers her.

## Slim frame v1, tile fixes (latest)

- `scene/slot_background_1.png` is `slot_background_100x100px_windows_slim_v1.png` (1672x941, transparent): windows ~127.5x118 on a 153.9x142.9 pitch,
  snapped to an even grid in `V2_FRAME_WINDOWS` so every cell has the same tile/symbol offset (rolling and settled used to differ by a few px = the
  small jump when a reel stopped). Tile grow on landing now starts at 94 %. `BOARD_GRID_W` 570: the slot (frame, windows, symbols) is 15 % bigger.
- Non-winning symbols are darkened (`filter`), not made transparent, so the window background no longer shows through the tiles; winners get a gold glow.
- `tiles_blur/` comes from `slot_tile_backgrounds_tiers_cartoon_named_blurred.zip` (same crop and alpha as the sharp tiles), WebP q60.

## Slot frame 5x5 slim fixed (latest)

- `scene/slot_background_1.png` is `slot_frame_5x5_100x100_slim_fixed.png` (1147x849): even 102x102 windows on a 128.4 pitch (`V2_FRAME_WINDOWS`).
  `tileGrow` 1.14: tier tiles and the default window background are drawn 14 % larger than the window so the frame lattice hides their edges.
- Symbol cells are no longer stacking contexts: the tile (z 3) stays under the frame (z 6), the symbol art (z 8-11) is above it, so a landing
  tile can never show over the frame. Dim / win glow filters moved from `.symbol` to its children for the same reason; `reel-land` removed.
- Symbols rest 3 art px above the window centre (`SYMBOL_LIFT`); `BOARD_GRID_W` 515 so the last row ends above the WIN plate.

## Gothic rose frame (latest)

- `scene/slot_background_1.png` is `Gotycka rama inwentarza z różami.png` (1448x1086). Its 25 hand-drawn windows (~133x128 art px) are snapped to an even
  167 x 162.4 grid (measured deviation <= ~3 px, hidden by `tileGrow`); `BOARD_GRID_W` 524 keeps the windows ~82 px and the last row above the WIN plate.

## Vine-stone frame, 135 px tiles (latest)

- `scene/slot_background_1.png` is `slot_frame_vine_stone_5x5_132ish_fixed.png` (1312x1199, windows 130 +-3 px). Rows snapped to an even 176.7 pitch, column
  centres as measured. Tier tiles and the default window background are rendered 135x135 art px (`tileGrow` = 135/130) under the frame lattice.
- Tier growth: step between tiers +50 % (low 0.84, medium 0.903, premium and feature symbols 0.966 of the 130 px window).
- `BOARD_GRID_W` 521 (the frame is 1199 art px tall; the last row has to end above the WIN plate).

## UI panels, gems, plants (latest)

- Window art: `ui/panels/panel.png` (from `vertical_UI_asset.png`) is a 9-slice (`border-image`, slice 64, width 26 px) behind every window: bet menu, autoplay,
  buy-bonus confirm, error, settings, paytable, info, buy bonus (`.ui-popup-standard-content-wrap`, `.decor-shell`, `.lounge-settings`) and the menu flyout.
  Game.svelte publishes `--ml-panel`, `--ml-button`, `--ml-square` on `<body>`.
- Buttons: `ui/panels/button.png` (`horizontal_rectangle_ui_asset.png`) 9-slice on every `.rectangle` (autoplay options / start, bet menu), the menu flyout
  buttons and the buy-bonus buttons. `ui/panels/square.png` (`square_UI_asset.png`) is the plate of all close (X) buttons and the settings ON/OFF buttons.
  The buy-bonus header is `ui/panels/buy_bonus_header.png` (`buy bonus new.png`); its bet +/- use the BetUI +/- art.
- Intro: the "click anywhere to continue" art is replaced by Luckiest Guy text (white, black outline) that floats up and down.
- Slot: tier tiles and the default window background fill the whole cell (+1 px), so they touch while rolling and when stopped (frame lattice hides it);
  symbols 2 px lower. 16 red gems of the frame (`frameGems.ts`, cut from the art) pulse (0.9 s, scale 1.28, brighter), 1-3 at a time every 1-3 s (`GemPulse.svelte`).
- Two more animated plants stand behind the slot, half hidden by its frame (`SCENE_PLANTS`).
- BetUI: all controls another 5 % smaller (K = 0.855), +/- 3 % smaller and further inside the BET plate, WIN centred on the slot (stage x = 640),
  smaller glow on switched-on buttons.

## Slot to the bottom edge, symbols, panel URLs (latest)

- `BOARD_GRID_W` 555: the crest stays on the top edge and the frame's visible bottom (art y 1145) lands on the bottom edge of the stage.
  The WIN plate sits on that lower edge (bottom 6 px above the stage bottom). Plants behind the slot moved out to the new frame edges (x 0.226 / 0.774).
- Settled symbols +5 %; tier growth over `low` raised by 50 % (medium x1.1125, premium and feature x1.225 of low). BET +/- circles 5 % smaller.
  Bartender and woman +5 % (bottom anchor unchanged).
- Fix: `--ml-panel`, `--ml-button`, `--ml-square` hold absolute URLs; a `url()` in a custom property resolves against the stylesheet using it
  (`/_app/immutable/assets/` in the build), which gave 404s for the panel, button and square art on Stake Engine.

## Stars, crest ruby, BetUI geometry (latest)

- `SkyStars.svelte`: the 10 sparkle stars of `background_3_static.png` (`skyStars.ts`, cut from the art) twinkle at random like the frame gems (0.9 s, 1-3 at a time).
- `GemPulse.svelte`: the crest ruby has its own controller (every 0.6-2 s, 0.5-1.8 s long, varied strength, sometimes a double flash) and, while any reel
  rolls, a quick 0.38 s flash per symbol that enters at the top (`crestKick`, at most one per 90 ms).
- Slot raised by 18 px (`BOARD_RISE`; the crest ruby stays inside the screen). WIN plate 1 px above the bottom edge.
- BetUI: BET plate and its lettering 10 % smaller, +/- another 5 % smaller; BET, TURBO and AUTO keep one 11 px gap to the curve of the SPIN disc.
- Win celebration: fixed one-column stage, so the title no longer moves when the amount gets wider. Amounts show at most 2 decimals (JPY 0).
- Intro CTA sits on the horizontal plate; settings ON/OFF plates are not clipped; plants behind the slot are ~60 % hidden.
- `exports/paytable_info_headers.zip` (not in git): all header images of the Paytable / Info / Buy Bonus screens with a README of where each is used.

## Frame wind, calmer crest ruby, new headers (latest)

- `SlotFrameWind.svelte` draws the slot frame with WebGL2; the foliage and golden thorns around the windows sway through an animated displacement
  (3 art px), limited by `scene/slot_frame_wind_mask.png` (white = leaves / thorns around the windows, black = pillars, crest, base). The plain image layer is
  the fallback (no WebGL2, reduced motion, before the first frame). The mask is made from the frame alpha (distance to the window holes); regenerate it
  when the frame art changes.
- Crest ruby: every 3-7 s, 0.7-1.6 s long, about half the growth of the small gems; the per-symbol flashing while rolling and the double flash are gone.
- 9-slice plates (panels, buttons, intro CTA) have a stretched copy of the art under the slices, so no transparent cut line shows through.
- Headers of Paytable / Info / Buy Bonus replaced by `paytable_info_headers_cartoon_renamed.zip` (the titles `ui_header_paytable/info/how_to_play` were not in the pack).

## Calmer frame wind, new headers, EN/PL plates (latest)

- Frame wind halved in amplitude (1.5 art px), speed and spatial frequency (`SlotFrameWind.svelte`).
- Headers from `skynight_lounge_headers_named.zip` (2048x682): the 15 `hdr_*` plus `hdr_paytable`, `hdr_info`, `hdr_how_to_play`, which replace
  `skyjump_v2/ui/headers/ui_header_paytable|info|how_to_play.png` (same paths, so no code change).
- The stretched-copy background under the 9-slice art stays only on the intro CTA; on the flyout buttons it showed as a second outline (EN / PL), so it is removed again there and on the panels.

## Frame piecewise, BetUI bottom line, paytable (latest)

- `scene/slot_background_1.png` is `slot_grid_130px_piecewise.png` (1286x1174, windows ~130 px): rows on an even 171 pitch, columns as measured (`COL_CENTERS`);
  `BOARD_GRID_W` 548 (frame bottom on the stage's bottom edge before the 18 px raise). Frame gems, wind mask and the wind shader's art size regenerated for it.
- BetUI: the lowest opaque pixels of balance / menu (left), spin and bet (right) and WIN all sit on stage y = 719 (`BOTTOM`); bonus, turbo and auto move with their cluster.
- Default master volume 50 (music and effects stay 75). Woman brightness 0.907 (-3 %).
- Paytable: Payline Inspector first; regular symbols show "3 / 4 / 5 symbols" in the normal colour and the multiplier in bigger gold, on the tier tile of the symbol;
  token cards T1-T6 list the prize values from the math config (valueWeights) and the Free Spins x1.5 (`freeSpins.economy.tokenValueScale`).
- Checked against `skyjump_v2_config.json` / the engines: 28 lines, awards, 10 initial / 40 max Free Spins, +5 spins and a room step on 3+ invitations in Free Spins
  (rule U1), 3/4/5 invitations -> Large Hill / Ski Flying / World Cup and the V -> Perfect V, persistence from Ski Flying, guaranteed VIP Upgrade from World Cup,
  guaranteed Concierge in Perfect V, Encore and Black Access Pass only in Free Spins, max win 50,000x.

## New frame + stone tablet, symbols, music, win coins (latest)

- Frame: `slot_background_1.png` is "Gotycka rama z różami i klejnotami (1)" (1352x1163), one opening of 823x738 art px (x 244, y 200): the 5x5 cells fill it (`presentationLayout.ts`:
  `V2_FRAME_ART`, `V2_SLOT_BOARD_FRAME`, `V2_FRAME_WINDOWS` = the cells). `BOARD_GRID_W` 553 puts the visible frame (art y 17..1089) on the stage; `BOARD_RISE` 0.
- Stone tablet `scene/slot_tablet.png` ("Kamienna tablica z różami i bluszczem") sits behind the opening (`V2_TABLET_RECT`, opening +5 %), under symbols and frame; the old window background is gone.
- Wind (`FoliageWind.svelte`, WebGL2, generic for any picture + mask): on the tablet the vines, leaves and roses sway (`slot_tablet_wind_mask.png`: green / red pixels); on the frame only the
  foliage outside the stone columns (`slot_frame_wind_mask.png`: green + rose pixels outside the column bands; gems and columns stay still). `frameGems.ts` regenerated (16 gems).
- Tier tiles: base reel strips land low 57.3 %, medium 28.5 %, premium 11.9 %, scatter 1.8 %, Concierge / Mystery 0.5 %. Low and medium have no tile any more (on the slot and in the paytable); `V2_TILE_TIERS`.
- Symbols from `Midnight_Lounge_cartoon_renamed.zip` (512 px PNG), rolling versions from `..._motion_blur.zip` (512 px WebP q60), new `fx_glint_ruby_gold` and `fx_luxury_burst_gold`.
- Music: `relaxed_background_music1/2.mp3` replace `midnight-vip-1/2.mp3` (`bgm/tracks.json`). Win screens (big and above) play `sfx_win_background_sound.mp3` (replaces `sfx_win_bigwin_universal.mp3`).
- `slot_new_row.mp3` (`ROW_SPAWN`, gain 0.3, voices stack, one per 35 ms at most) plays for every new row entering a rolling reel.
- Win coins (`CoinBurst.svelte`): 12 / 24 / 36 / 48 / 60 coins for big / mega / super / max / world record start behind the header, alternate left and right, rise a little and fall off the screen;
  one full turn per flight (atlas `fx/win_coin_atlas.png`, 20 frames 180 -> 90 degrees and back); `win_coin_spawn.mp3` on appearing, `win_coin_escape.mp3` on leaving.

## Stone wall, vine dividers, coins over the whole stage (latest)

- `scene/slot_tablet.png` is the fully opaque centre (1088x1008 of 1240x1268) of "Kamienna ściana w różanym splocie", 10 % darker, 960x877; `V2_TABLET_RECT` = the opening +3 %.
  The crop is made so that no transparent pixel can show; the wind mask (`slot_tablet_wind_mask.png`) is rebuilt from its green / red pixels.
- `slot_column_1..4.png` (482x1446) are four vine dividers between the five columns (`V2_COLUMN_DIVIDERS`, squeeze 0.58 of their 1:3 width): z 5 = above the tier tiles, under the symbols and the frame;
  each sways through `FoliageWind` (own phase, ends pinned by `slot_column_wind_mask.png`).
- Win coins: the coin layer is stretched over the whole `.skyjump-viewport`, so the coins leave through the bottom edge of the stage; `COIN_ESCAPE` (`win_coin_escape.mp3`) plays then.

## Flat wall, no dividers, BetUI trims (latest)

- `scene/slot_tablet.png` is the fully opaque centre of `slot_background.png`, 10 % darker, drawn static at 50 % opacity (`.slot-wall`); the vine dividers (`slot_column_*`), the tablet wind mask and their code are removed.
- Slot raised by 20 px and smaller (`BOARD_GRID_W` 514) so the frame ends at about y 650, above the WIN / BALANCE / BET plates.
- BetUI: BET, TURBO and AUTO keep a 3 px gap to the SPIN disc (`GAP`); BET and menu another 10 % smaller; WIN plate 10 % lower and 15 % longer with the label and the amount on one line;
  BET lettering 5 % bigger and 14 % wider (`scaleX`).

## TURBO / AUTO in the bottom strip (latest)

- The wall is 10 % transparent (opacity 0.9). TURBO sits between balance and WIN, AUTO between WIN and BET, all plates end on y 719; the menu button is centred on the balance plate's round end (`HUD.balance` end circle) and is 78x76.
- Slot grows with the top where it was (raised 20 px): `BOARD_GRID_W` 524, the frame ends just above the bottom strip. "BET" label 15.2 px (the amount keeps 16 px).
