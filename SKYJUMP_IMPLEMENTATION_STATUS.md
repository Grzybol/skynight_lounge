# SkyJump implementation status

Current release source: `SKYJUMP_RELEASE_READINESS.md`.

## BRANCH

`chore/skyjump-release-readiness` (from updated `main` + playtest HUD PR #9).

mathVersion 3 is frozen. Do not edit `skyjump_config.json` tables.

## POST-AUDIT IMPLEMENTATION PASS

### P1 fixed

- Garden paylines/paytable/wilds removed from active frontend `config.ts` and Python `GameConfig`
- Buy modes, costs, maxWin, hill/multiplier mapping live in canonical JSON; adapters derive FE/Python
- Volatility constants moved into canonical `volatilityModel`
- Book amounts use Python 3 / Stake SDK half-to-even rounding in both TS and Python
- `/dev-preview` is not prerendered into the production static site; localDemo is a DEV-only dynamic import plus localhost gated
- Garden `reveal` handler removed from the SkyJump book map
- `skyjumpSlots` replaced with six `skyjumpSlot` events (`schemaVersion: 1`)
- Resume can stop after weather and after each slot; result catch-up no longer replays overlay suspense
- `wincap` is reserved in the resume snapshot
- Vite blanket `frontend/packages/*` aliases removed; standard workspace resolution builds

### P1 remaining

- Stake ACP `gameID` is still `0_0_poc` (documented rename TODO in canonical JSON)
- Production-scale books are not generated yet — see `SKYJUMP_RELEASE_READINESS.md`

### P2 fixed

- Overlay/weather/menu are positioned against the game viewport container, not `position: fixed` on the browser window
- `/dev-preview?screen=menu` QA for the SkyJump main menu
- Config parity test rewritten for SkyJump
- Canonical JSON validation on Python load
- Autoplay stress harness: 100 normal + 100 turbo books
- Slot 6 → overlay uses `requestAnimationFrame` paint sync instead of a magic 32ms timeout

### Event contract version

`schemaVersion: 1`

Flow: `skyjumpWeather` → `skyjumpSlot`×6 → `skyjumpResult` → `setWin`/`wincap` → `setTotalWin` → `finalWin`

### Canonical config status

`math/games/0_0_poc/skyjump_config.json` is the source for tables, volatility, buy profiles, costs, mapping, and gameplay `maxWin`. Mode cap may exceed the hill default (premium multiplier buys). Canonical mode ids are `base` / `large_hill` / …; Stake-published play keys are `rgsKey` (`BASE` / …).

### Resume status

Interrupt after weather / slots 1–6 / result / wincap reconstructs the same authoritative distance, multipliers, finalWinX, and book amount. No reroll.

### Build status

From `frontend/apps/poc`: `npm run dev` (port 3010) and `npm run build`. Production static output prerenders `/` only.

### Autoplay stress status

`node --experimental-strip-types tools/skyjump/autoplay-stress.ts` — 100 normal + 100 turbo passed.

## MATH / RTP PASS (`mathVersion: 1`)

Frozen. Exact enumerator + 1M Monte Carlo (seed 7). See
`SKYJUMP_MATH_REPORT.md` and `math/games/0_0_poc/skyjump_config.mathVersion1.json`.

## MATH / ECONOMICS AUDIT (`mathVersion: 1`)

Read-only. Tables were not changed. Full write-up: `SKYJUMP_MATH_AUDIT.md`.

- RTP semantics confirmed: book `100` = 1× nominal bet, not 1× mode wager.
- Enumerator mass = 1.000000 on every published mode. No P0 math bug.
- mathVersion 1 stays the audited snapshot.

## MATH VERSION 2 + ECONOMIC UX

Active canonical JSON is `mathVersion: 3`
(`321dedd2d88259b37b7d779d000ddfe5a154bc1a9512a1dceb67830f91eefd33`).
`eventSchemaVersion` stays 1. Frozen v2:
`math/games/0_0_poc/skyjump_config.mathVersion2.json`.

Exact report: `SKYJUMP_MATH_V2_REFINEMENT.md`. Design: `SKYJUMP_MATH_DESIGN.md`.

- RTP 0.9681–0.9718 vs actual wager on all published modes
- Weather BASE 0.804–1.122 (spread 1.40, hit spread 8.4 pp)
- BASE distance-only EV 0.456; Shapley distance 72%
- Any-local 17.5%
- Hill CV BASE < LARGE < FLYING; Flying P(>50x) and p99.9 above Large

## UX / GAME-FEEL PASS (post manual review)

Math v3 tables, weights, and RTP were not retuned. eventSchema 1 is unchanged.

- All six reels start together, then lock 1→6. Stop travel is capped to about 2–3 ticks: if the result is already in that window it eases onto it, otherwise that tick is written just below the fold so the number rolls into view. The tape stays parked after stop (no swap to a number that was never on the wheel).
- Distance miss (below the hill payline, 116 m on Normal) presents slot 6 as **x0**.
  Cash is still `baseWinX * locals * slot6`; below payline that product is 0.
- Overlay shows `PAYLINE 116 m · BELOW PAYLINE` plus a pulsing **BELOW PAYLINE** banner.
  The result card opens at its final size; weather + slot + payout labels are already there and values fill in sequentially.
- Live meter above the strip: current metres, BASE start (hill + weather), payline, and QUALIFIED / GOOD JUMP / GREAT JUMP.

## UI / REFERENCE PASS

Visual source of truth: `docs/reference/skyjump-ui-reference.png`.
Gameplay background: user-supplied in-run art as `gameplay.webp`.

- Reel strip sits near 18vh, `min(86vw, 1450px)`, cards ~32vh — no longer parked on the HUD.
- Overlay holds after the result until NEXT JUMP (turbo included; autoplay still auto-dismisses). Verdict labels (NO BIG WIN / BIG WIN / MEGA WIN) are large. Big/mega payout uses a slower glow, not a snap punch. Space during overlay tally is ignored (does not BET or toggle turbo).
- Result card counts weather Δm plus rolled conditions (temp / wind / visibility) and slots 1–5 before distance/payout.
- Reels keep one repeating tape and ease 2–3 ticks onto the landed value; the strip stays on screen after lock.
- Slot 1–5 colors/pulse from each role’s distanceValue range (negatives included). Hot results throw colored electrical/firework sparks around the landed number, not a single pixel spec.
- Payout tile is larger and counts longer when the return beats the actual wager.
- Slot 6 stays gold; local x2/x3 is a gold accent on the ice card, not a second gold reel.
- Weather compact chip is top-center after the draw; the slots 1–5 tile is the weather lottery first (slower, two passes, green/red Δm), then morphs into the flight board. Overlay remains over gameplay.
- Weather lottery on the chip is ~2.5s (then the winner holds). Overlay labels weather metres separately from wind m/s. Paytable/info explain that weather type moves distance + volatility; temp/wind/vis describe that type.
- Space / BET cannot start the next round until the result overlay is dismissed. TURBO pulses with gold sparks while on. Local xN on a slot is a large pulsing gold pill.
- Slots 1–5 live in one flight board; a cyan/gold jumper point + Catmull-Rom ribbon draws L→R at constant reveal pace after slot 1. A gold **base multiplier** tile sits between the flight board and slot 6: locked until payline, then reveals the human-language formula `Hill start + weather + slots 1–5 → payout table` (those metres pick one table row; not cash per metre). Overlay shows that `baseWinX` immediately. Slot 6 is a locked **Final Jump Multiplier** cash rail with a **horizontal** lottery tape at 80% of the tile and no extra landed-x label under the wheel; it only unlocks after that tally. The landed value is locals × slot-6 (no x0 on the tape). Below-payline overlay skips flight rows. Sparks only on green/gold; negatives show a red sad face. Weather chip is compact so it no longer covers the live metre meter.

## HUD / UTILITY BAR VISUAL MATCH

Layout/styling only. mathVersion 3 and eventSchemaVersion 1 unchanged.

- Bottom HUD is one glass dock: BALANCE | WIN | TOTAL BET plus MENU / BUY / AUTO / − / BET / + / TURBO.
- Stats are stacked labels inside the dock, not tiled floating cards.
- BET/SPIN is the circular primary control; −/+ sit beside it; TURBO is last on the right.
- BUY BONUS has a warm gold fill, gold border, gift mark, and a soft gold glow. TURBO uses a green border when on and a red border when off. MENU / AUTO / − / + stay ice-cyan, including when autoplay is on.
- Buy bonus lists every enabled canonical buy mode (Large Hill, Ski Flying, Multiplier 10–100, Multiplier 20–200). Max win is shown as cash plus a multiple of that round’s total bet (canonical `maxWin` vs nominal bet, divided by cost).
- MENU opens a horizontal flyout above the dock (paytable, rules, settings, sound, language). Default copy is English; PL is available from the flag button.
- Desktop stays one row. Portrait may use two compact rows.
- Top-left is a cyan glass utility pill (`Back to game` + compact diagnostics).
- `/dev-preview` Test selector is a collapsible DEV chip, not yellow runtime UI.

## AUDIO

Presentation only. mathVersion 3 and eventSchemaVersion 1 unchanged.

- BGM lives in `frontend/apps/poc/static/assets/audio/skyjump/bgm/` (`frostbet-1` / `frostbet-2` / `frostbet-3`). Playlist is `tracks.json` plus those fallback names, shuffled on each track end.
- Earlier two BGM files without documented commercial rights sit in `frontend/apps/poc/static/assets/audio/skyjump/old music/` and are not played. Production `build/` strips that folder.
- BGM is a native `HTMLAudioElement` playlist (not Howler), so Stake `Howler.mute` on a suspended WebAudio context cannot kill it. It starts on game load / Press to Continue, unlocks on the first real pointer/key gesture, and a watchdog resumes it if the element stalls. Big/mega win is a one-shot HTMLAudio sting on the music slider (`loop: false`, hard stop at 7s). Farmer `bgm_winlevel_*` / coin-loop sprites are blocked. MENU settings sit above the result overlay so the music slider still works during a celebration.
- SFX live in `.../audio/skyjump/sfx/`: skiing + wind loop during weather and slots; anticipation during overlay count-up; `win` on a pay hit; `win` + `big-win` together from 5x profit; `lose` on a miss.
- Farmer sprite BGM is no longer used in the SkyJump poc. Reel-stop and button ticks stay on the existing sprite.

## PARTIALLY DONE

- True V-style transparent jumper (current flight plate still has graphic fill)
- Distinct LARGE / FLYING background plates (same art, camera scale for now)
- Production-scale published `.jsonl.zst` books / Stake PAR review
- Combining hill + multiplier in the buy-bonus UI (layout prepared, no new math)

## NOT STARTED

- Stake ACP upload / real-money session
- Stake math-review / production book generation
- Git recovery of `main` / remotes

## HOW TO RUN

Double-click `START.bat` (see `JAK-URUCHOMIC.txt`). The launcher
downloads a local pnpm (not npm/npx), installs workspace deps, builds
`pixi-svelte` when `dist/` is missing, then opens
`http://localhost:3010/dev-preview` (4010 if 3010 is blocked).

From `frontend/apps/poc` by hand:

```
npm run dev
```

Math:

```
node --experimental-strip-types tools/skyjump/test-math.ts
python math/games/0_0_poc/test_skyjump_resolve.py
python -m pytest math/tests/test_config_parity_poc.py
node --experimental-strip-types tools/skyjump/autoplay-stress.ts
node --experimental-strip-types tools/skyjump/mathAudit.ts --exact-only
node --experimental-strip-types tools/skyjump/designGuards.ts
node --experimental-strip-types tools/skyjump/simulate.ts --all-modes --rounds=1000000 --seed=7
python math/games/0_0_poc/write_skyjump_smoke.py
```

## MIDNIGHT LOUNGE CHARACTER ANIMATION V2

- Bartender (left) and woman (right) now play 30 fps spritesheet clips (14 packages, 2100 frames) through `frontend/apps/poc/src/game/loungeCharacters/`; the old webp/GIF figure code was removed.
- Win hooks reuse the board's existing celebration tiers; no math, thresholds or event ids changed.
- Architecture, memory strategy, placement and QA commands: `docs/midnight-lounge-character-animation.md`.
