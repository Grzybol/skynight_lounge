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
