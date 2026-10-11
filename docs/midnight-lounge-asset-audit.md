# Midnight Lounge asset and branding audit

> **Superseded:** the single-figure webp/GIF system described here was replaced by the two-character spritesheet system. See `docs/midnight-lounge-character-animation.md`.


Phase 0–3 record for the SkyJump chassis. Gameplay, math, RTP, event names, and Stake IDs stay SkyJump.

Generated from the working tree on branch `feat/lounge-backdrop`. Counts: 262 files. KEEP 8, REPLACE 61, RENAME 0, REMOVE 0, REVIEW 193.

## Phase 0 — repository

- Branch: `feat/lounge-backdrop` (tracks `origin/feat/lounge-backdrop`, PR #2).
- `origin/main` is the merged SkyJump import (`4f550e3`).
- Frontend app: `frontend/apps/poc` (SvelteKit + Vite + Pixi). Entry: `src/routes/+page.svelte` → `Game.svelte`.
- Dev/preview: `src/routes/live-preview/+page.svelte`, `src/routes/dev-preview/+page.svelte`. Local launcher: `start-skyjump.ps1` (port 3010).
- Game config (do not retune): `src/game/config.ts` (`gameName: 'skyjump'`, `gameID` from math JSON), `src/game/skyjump/config.ts`, `src/game/skyjump_v2/config.ts`, `math/games/0_0_poc/skyjump_config.json`.
- Asset roots:
  - `frontend/apps/poc/src/assets/skyjump/` — bundled via `new URL(..., import.meta.url)` (`skyjumpArt.ts`, `src/game/assets.ts`).
  - `frontend/apps/poc/static/assets/skyjump_v2/` — runtime URLs `/assets/skyjump_v2/...` (`symbolAssetRegistry.ts`, `uiAssetRegistry.ts`).
  - `frontend/apps/poc/static/assets/spines|sprites|fonts|audio/` — Pixi spines/sprites, CSS fonts, BGM/SFX.
  - `asset-backup/lounge-gifs/` — zip backup only. Not loaded by the game.
- Loaders: direct `new URL` imports, absolute static URLs, Pixi `Assets` manifest keys in `src/game/assets.ts`, SVG icons, animated `<img>` (webp/gif). No character `AnimatedSprite` and no `<video>` for the lounge figure.
- Do not hand-edit: `math/games/*/library/`, `stake-upload/`, `.svelte-kit/`, `dist/`, `src/assets/skyjump/generated/assets-manifest.json` (generator output).

## How animation plays today

The lounge character is HTML `<img>` inside `SkyJumpBackground.svelte`, not Pixi video.

| Clip | File | How it plays |
|---|---|---|
| Idle (forward + reverse) | `lounge-figure.webp` | Animated webp loops on its own. Duration constant `BASE_LOOP_MS` = 8580. The element is not remounted between idle loops. |
| Leg / shoe (`character_leg_extend`) | `stopa_plus.gif` | One shot. Scheduler swaps `<img>` and removes it after `STOPA_MS - STOPA_TAIL_MS`. |
| Delighted (`character_delighted`) | `smile_plus.gif` | Shown while the big-win celebration is up. |
| Wow (`character_wow`) | `wow_plus.gif` | Shown for mega and above. |

Playback start/stop is `setTimeout` from those constants, not an `ended` event. GIF/webp speed cannot be changed at runtime. Turbo (`getSkyJumpTimings` in `src/game/skyjump/timings.ts`) shortens reel and count-up timings only. It does not scale the character clips. A faster lounge performance needs new files or a different player (`playbackRate` on video). Do not point Turbo at these `<img>` tags without that player.

Crossfade: the incoming clip fades in on top; the outgoing clip fades out after `FADE_OUT_DELAY_MS`. Constants live in `loungeFigureTune.ts`.

## Phase 2 — name classes

### A. User-facing, safe to rebrand

| Where | Current text | Action |
|---|---|---|
| `src/game/skyjump/config.ts` `PUBLIC_GAME_TITLE` | SkyJump | Change the string only. It is the `<title>` in `Game.svelte`. |
| `LoaderArtwork.svelte` | SKYJUMP, THE HILL IS READY, PREPARING THE IN-RUN | Cosmetic loader copy. |
| `SkyJumpBrand.svelte`, `SkyJumpMainMenu.svelte` | alt / visually-hidden SkyJump | Accessible name. Logo pixels stay until a lounge logo exists. |
| Paytable, rules, buy-bonus kickers | SkyJump / SKYJUMP | Visible label. |
| `i18n` en/pl values for key `SKYJUMP RULES` | SKYJUMP RULES / ZASADY SKYJUMP | Change values only. The key stays, because `t('SKYJUMP RULES')` looks it up. |

### B. Internal, safe later, not in this pass

Component filenames (`SkyJumpV2Board.svelte`), CSS variables `--skyjump-font-ui`, font-family `SkyjumpDisplay` / `SkyjumpUI`, asset folder `src/assets/skyjump/`. Renaming compiles only if every import moves together. Leave them so the chassis stays recognizable.

### C. Do not rename

- `gameName: 'skyjump'`, `gameID`, `providerName` in `src/game/config.ts`.
- `math/games/0_0_poc/skyjump_config.json` modes, RTP, hills, weather tables, book events.
- TypeScript event names (`BookEventSkyJump*`), XState, RGS keys (`BASE`, buy-mode `rgsKey`).
- SFX map keys in `SKYJUMP_SFX` (they are sound IDs, not labels).
- Mode labels that mirror math modes (`LARGE HILL`, ski-flying, world cup) in the v2 UI pack. Those are presentation of mode IDs until a product pass says otherwise.
- `src/assets/skyjump/generated/assets-manifest.json` prompts.

## Phase 3 — target structure (do not move files yet)

Future drop-in folder, when art exists. Nothing is copied there in this phase.

```
frontend/apps/poc/src/assets/midnight-lounge/
  background/          midnight-lounge.jpg (today: src/assets/skyjump/backgrounds/)
  character/idle/      lounge-figure.webp
  character/reactions/ stopa_plus.gif, smile_plus.gif, wow_plus.gif
  symbols/             replaces static/assets/skyjump_v2/symbols
  ui/                  replaces static/assets/skyjump_v2/ui
  fx/                  replaces static/assets/skyjump_v2/fx
  win/                 replaces ui win titles
  audio/               replaces static/assets/audio/skyjump when tracks exist
```

The live code keeps reading the current paths. `src/game/midnightLoungeTheme.ts` is only an index of those paths plus slots marked `WAITING_FOR_REPLACEMENT`.

| Old | New (when art exists) | Now |
|---|---|---|
| `src/assets/skyjump/backgrounds/midnight-lounge.jpg` | `midnight-lounge/background/plate.jpg` | KEEP in place |
| `src/assets/skyjump/backgrounds/lounge-figure.webp` | `midnight-lounge/character/idle/character_idle.webp` | KEEP in place |
| `src/assets/skyjump/backgrounds/stopa_plus.gif` | `midnight-lounge/character/reactions/character_leg_extend.gif` | KEEP in place |
| `src/assets/skyjump/backgrounds/smile_plus.gif` | `midnight-lounge/character/reactions/character_delighted.gif` | KEEP in place |
| `src/assets/skyjump/backgrounds/wow_plus.gif` | `midnight-lounge/character/reactions/character_wow.gif` | KEEP in place |
| `static/assets/skyjump_v2/ui/ui_logo_skyjump.png` | lounge logo | WAITING_FOR_REPLACEMENT |
| `static/assets/skyjump_v2/symbols/sym_*.png` | lounge symbols | WAITING_FOR_REPLACEMENT |
| `src/assets/skyjump/jumper/*`, `weather/*`, `reel-icons/*` | lounge set | WAITING_FOR_REPLACEMENT |
| `src/assets/skyjump/backgrounds/menu.webp` | lounge menu plate | WAITING_FOR_REPLACEMENT |
| fonts `SkyjumpDisplay` / `SkyjumpUI` | lounge fonts | WAITING_FOR_REPLACEMENT |

## Phase 5 — still waiting

Do not delete SkyJump art that has no lounge file yet. Runtime must keep booting.

## Inventory

| Current asset | Type | Resolution / format | Used by | Runtime purpose | SkyJump-specific? | Midnight Lounge action |
|---|---|---|---|---|---|---|

| `asset-backup/lounge-gifs/smile_plus.gif.zip` | zip | 48.6 MB | backup only, not loaded at runtime | Midnight Lounge plate / character already in use, or its zip backup. | partial | KEEP |
| `asset-backup/lounge-gifs/stopa_plus.gif.zip` | zip | 88.8 MB | backup only, not loaded at runtime | Midnight Lounge plate / character already in use, or its zip backup. | partial | KEEP |
| `asset-backup/lounge-gifs/wow_plus.gif.zip` | zip | 58.6 MB | backup only, not loaded at runtime | Midnight Lounge plate / character already in use, or its zip backup. | partial | KEEP |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/gameplay.svg` | svg | 1 KB | skyjumpArt.ts menuBgSrc; play plate is midnight-lounge.jpg | Old ski menu/play art. Runtime play background is already the lounge JPG. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/gameplay.webp` | webp | 114 KB | skyjumpArt.ts menuBgSrc; play plate is midnight-lounge.jpg | Old ski menu/play art. Runtime play background is already the lounge JPG. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/lounge-figure.webp` | webp | 15.5 MB | skyjumpArt.ts + SkyJumpBackground.svelte | Midnight Lounge plate / character already in use, or its zip backup. | yes | KEEP |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/menu.svg` | svg | 2 KB | skyjumpArt.ts menuBgSrc; play plate is midnight-lounge.jpg | Old ski menu/play art. Runtime play background is already the lounge JPG. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/menu.webp` | webp | 50 KB | skyjumpArt.ts menuBgSrc; play plate is midnight-lounge.jpg | Old ski menu/play art. Runtime play background is already the lounge JPG. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/midnight-lounge.jpg` | jpg | 175 KB | skyjumpArt.ts + SkyJumpBackground.svelte | Midnight Lounge plate / character already in use, or its zip backup. | yes | KEEP |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/smile_plus.gif` | gif | 48.6 MB | skyjumpArt.ts + SkyJumpBackground.svelte | Midnight Lounge plate / character already in use, or its zip backup. | yes | KEEP |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/stopa_plus.gif` | gif | 88.9 MB | skyjumpArt.ts + SkyJumpBackground.svelte | Midnight Lounge plate / character already in use, or its zip backup. | yes | KEEP |
| `frontend/apps/poc/src/assets/skyjump/backgrounds/wow_plus.gif` | gif | 58.5 MB | skyjumpArt.ts + SkyJumpBackground.svelte | Midnight Lounge plate / character already in use, or its zip backup. | yes | KEEP |
| `frontend/apps/poc/src/assets/skyjump/jumper/flight-win.png` | png | 407 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/jumper/flight-win.webp` | webp | 50 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/jumper/flight.png` | png | 407 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/jumper/flight.svg` | svg | 1 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/jumper/flight.webp` | webp | 50 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/jumper/inrun.webp` | webp | 30 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/jumper/menu-foreground.svg` | svg | 1 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/jumper/menu-foreground.webp` | webp | 24 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/reel-icons/cash.svg` | svg | 1 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/reel-icons/flight.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/reel-icons/landing.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/reel-icons/multiplier.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/reel-icons/speed.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/reel-icons/takeoff.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/reel-icons/wind.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/result/big-win.webp` | webp | 132 KB | skyjumpArt.ts resultArtSrc | Legacy result cards. Live v2 wins use ui_win_* plus lounge GIFs. | yes | REVIEW |
| `frontend/apps/poc/src/assets/skyjump/result/mega-win.webp` | webp | 123 KB | skyjumpArt.ts resultArtSrc | Legacy result cards. Live v2 wins use ui_win_* plus lounge GIFs. | yes | REVIEW |
| `frontend/apps/poc/src/assets/skyjump/result/normal-win.webp` | webp | 95 KB | skyjumpArt.ts resultArtSrc | Legacy result cards. Live v2 wins use ui_win_* plus lounge GIFs. | yes | REVIEW |
| `frontend/apps/poc/src/assets/skyjump/result/too-short.webp` | webp | 75 KB | skyjumpArt.ts resultArtSrc | Legacy result cards. Live v2 wins use ui_win_* plus lounge GIFs. | yes | REVIEW |
| `frontend/apps/poc/src/assets/skyjump/weather/crosswind.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/weather/headwindLift.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/weather/lightFavorableWind.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/weather/snow.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/weather/storm.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/src/assets/skyjump/weather/sunny.svg` | svg | 0 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/audio/skyjump/bgm/frostbet-1.mp3` | mp3 | 2.7 MB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/bgm/frostbet-2.mp3` | mp3 | 2.9 MB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/bgm/frostbet-3.mp3` | mp3 | 2.9 MB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/old music/frostbet-1.mp3` | mp3 | 4.3 MB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/old music/frostbet-2.mp3` | mp3 | 3.9 MB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/anticipation.mp3` | mp3 | 250 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/big-win.mp3` | mp3 | 119 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_trimmed/bet_button_sound.wav` | wav | 17 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_trimmed/generic_panel_open_close.wav` | wav | 69 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_trimmed/ui_click.wav` | wav | 27 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/bet_button_sound.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/bet_decrease_sound.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/bet_increase_sound.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/button_hover_sound.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/generic_panel_open_close.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/landing_bad.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/landing_big.mp3` | mp3 | 12 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/landing_good.mp3` | mp3 | 12 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/landing_small.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/slot1-5reveal_sound.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/slot1-5start_sound.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/slot6_big_multiplier_sound.mp3` | mp3 | 71 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/slot6_good_multiplier_sound.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/slot6_normal_multiplier_sound.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/ui_click.mp3` | mp3 | 71 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/weather_reveal_sound.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1/weather_roll_sound.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/lose.mp3` | mp3 | 250 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/skiing.mp3` | mp3 | 704 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_bad_miss.mp3` | mp3 | 17 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_bonus_end.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_free_spins_retrigger.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_free_spins_start.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_gate_upgrade.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_head_judge_collect.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_judge_collect.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_max_win.mp3` | mp3 | 66 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_mystery_open.mp3` | mp3 | 12 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_payline_complete.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_payline_draw.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_rejump.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_scatter_land.mp3` | mp3 | 12 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_scatter_trigger.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_thermal_lift.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_tier_upgrade.mp3` | mp3 | 25 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_token_reveal.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_wind_charge.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_wind_transition.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_wind_upgrade.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/sfx_world_record.mp3` | mp3 | 48 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2_trimmed/sfx_token_reveal.wav` | wav | 76 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/win.mp3` | mp3 | 704 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/skyjump/sfx/wind.mp3` | mp3 | 119 KB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | yes | REVIEW |
| `frontend/apps/poc/static/assets/audio/sounds.m4a` | m4a | 4.0 MB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | partial | REVIEW |
| `frontend/apps/poc/static/assets/audio/sounds.mp3` | mp3 | 4.6 MB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | partial | REVIEW |
| `frontend/apps/poc/static/assets/audio/sounds.ogg` | ogg | 3.6 MB | skyjumpAudio.ts / static audio manifest | Keep playback. Replace ski stingers later; do not retune math-side sound IDs. | partial | REVIEW |
| `frontend/apps/poc/static/assets/backgrounds/garden_base_drawn.png` | png | 2.3 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | partial | REVIEW |
| `frontend/apps/poc/static/assets/backgrounds/garden_base_drawn.webp` | webp | 234 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | partial | REVIEW |
| `frontend/apps/poc/static/assets/backgrounds/mine_base_drawn.png` | png | 1.6 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | partial | REVIEW |
| `frontend/apps/poc/static/assets/backgrounds/mine_base_drawn.webp` | webp | 78 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | partial | REVIEW |
| `frontend/apps/poc/static/assets/fonts/goldBlur/miningfont_gold_blur.png` | png | 376 KB | app.html + skyjump-fonts.css | Font family is still named Skyjump. Leave the files; a rename would break CSS. | partial | REVIEW |
| `frontend/apps/poc/static/assets/fonts/goldBlur/miningfont_gold_blur.webp` | webp | 79 KB | app.html + skyjump-fonts.css | Font family is still named Skyjump. Leave the files; a rename would break CSS. | partial | REVIEW |
| `frontend/apps/poc/static/assets/fonts/goldFont/mm_gold.png` | png | 317 KB | app.html + skyjump-fonts.css | Font family is still named Skyjump. Leave the files; a rename would break CSS. | partial | REVIEW |
| `frontend/apps/poc/static/assets/fonts/goldFont/mm_gold.webp` | webp | 255 KB | app.html + skyjump-fonts.css | Font family is still named Skyjump. Leave the files; a rename would break CSS. | partial | REVIEW |
| `frontend/apps/poc/static/assets/fonts/purpleFont/mm_purple.png` | png | 47 KB | app.html + skyjump-fonts.css | Font family is still named Skyjump. Leave the files; a rename would break CSS. | partial | REVIEW |
| `frontend/apps/poc/static/assets/fonts/silverFont/mm_silver.png` | png | 790 KB | app.html + skyjump-fonts.css | Font family is still named Skyjump. Leave the files; a rename would break CSS. | partial | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/fx/fx_coin_sparkle.png` | png | 750 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/fx/fx_ice_glint.png` | png | 1.1 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/fx/fx_payline_end_glint.png` | png | 1.2 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/fx/fx_payline_spark_head.png` | png | 780 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/fx/fx_screen_flash_accent.png` | png | 2.1 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/fx/fx_small_sparkle.png` | png | 1.0 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/fx/fx_snow_burst.png` | png | 1.8 MB | v2 UI/symbol registry or skyjumpArt.ts | Ski-theme image. Waiting for replacement. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/fx/fx_win_glow_ring.png` | png | 1.9 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/overlays/ui_overlay_world_record.png` | png | 1011 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_c_coach_signal.png` | png | 1.2 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_feat_gate_upgrade.png` | png | 1.2 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_feat_head_judge.png` | png | 1.3 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_feat_judge.png` | png | 1.1 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_feat_rejump.png` | png | 1.4 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_feat_special_world_record.png` | png | 1.8 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_feat_thermal_lift.png` | png | 1.2 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_feat_wind_key.png` | png | 1.3 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_l1_wind_sock.png` | png | 604 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_l2_snow_badge.png` | png | 1.1 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_l3_start_flag.png` | png | 754 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_m1_jumping_skis.png` | png | 590 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_m2_flight_goggles.png` | png | 822 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_m3_ski_boots.png` | png | 1.2 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_p1_flying_jumper.png` | png | 923 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_p2_crystal_trophy.png` | png | 1.1 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_p3_golden_helmet.png` | png | 1.0 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_s_competition_bib.png` | png | 1.3 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_token_t1_rookie.png` | png | 1.1 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_token_t2_k_point.png` | png | 1.6 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_token_t3_large_hill.png` | png | 1.5 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_token_t4_ski_flying.png` | png | 1.7 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_token_t5_world_cup.png` | png | 1.9 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_token_t6_token_world_record.png` | png | 2.0 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/symbols/sym_y_snowburst_mystery.png` | png | 1.3 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_auto_button.png` | png | 547 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_background_tile.png` | png | 251 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_btn_minus.png` | png | 893 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_btn_plus.png` | png | 912 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_buy_bonus_button.png` | png | 418 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_info_button.png` | png | 1.1 MB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_language_button.png` | png | 612 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_menu_button.png` | png | 701 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_menu_exit_button.png` | png | 567 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_paytable_button.png` | png | 1.1 MB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_settings_button.png` | png | 1.2 MB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_sound_off_button.png` | png | 1.2 MB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_sound_on_button.png` | png | 1.2 MB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_spin_button.png` | png | 1.5 MB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_stop_button.png` | png | 1.5 MB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/betui/betui_turbo_button.png` | png | 755 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/bonus/ui_bonus_free_spins.png` | png | 1.6 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/bonus/ui_bonus_retrigger.png` | png | 1.6 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/bonus/ui_bonus_tier_upgrade.png` | png | 761 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/bonus/ui_mode_large_hill.png` | png | 760 KB | v2 UI/symbol registry or skyjumpArt.ts | Ski-theme image. Waiting for replacement. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/bonus/ui_mode_perfect_v.png` | png | 706 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/bonus/ui_mode_ski_flying.png` | png | 2.0 MB | v2 UI/symbol registry or skyjumpArt.ts | Ski-theme image. Waiting for replacement. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/bonus/ui_mode_world_cup.png` | png | 870 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/decor/ui_bet_hud_frame.png` | png | 232 KB | uiAssetRegistry.ts | HUD control. Keep if the face is not ski-branded. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/decor/ui_corner_ornament.png` | png | 810 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/decor/ui_divider_ice.png` | png | 410 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/decor/ui_mode_badge_plate.png` | png | 1.3 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/decor/ui_panel_topper.png` | png | 799 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/decor/ui_slot_board_frame.png` | png | 469 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/decor/ui_status_plate.png` | png | 1.7 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/headers/ui_header_features.png` | png | 1.3 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/headers/ui_header_how_to_play.png` | png | 1.4 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/headers/ui_header_info.png` | png | 1.4 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/headers/ui_header_paytable.png` | png | 1.4 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_logo_skyjump.png` | png | 765 KB | uiAssetRegistry.ts or assets.ts | SkyJump-branded image. Waiting for a lounge mark. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_stage_flight.png` | png | 969 KB | v2 UI/symbol registry or skyjumpArt.ts | Ski-theme image. Waiting for replacement. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_stage_run_up.png` | png | 1.6 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_stage_takeoff.png` | png | 1.0 MB | v2 UI/symbol registry or skyjumpArt.ts | Ski-theme image. Waiting for replacement. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_tier_large_hill.png` | png | 1.3 MB | v2 UI/symbol registry or skyjumpArt.ts | Ski-theme image. Waiting for replacement. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_tier_perfect_v.png` | png | 1.5 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_tier_ski_flying.png` | png | 1.3 MB | v2 UI/symbol registry or skyjumpArt.ts | Ski-theme image. Waiting for replacement. | yes | REPLACE |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/ui_tier_world_cup.png` | png | 1.5 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/wins/ui_win_big.png` | png | 1.6 MB | uiAssetRegistry.ts V2_WIN_TITLE_FILENAMES | Win title plate. Copy may be generic; styling is still the ski pack. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/wins/ui_win_max.png` | png | 2.1 MB | uiAssetRegistry.ts V2_WIN_TITLE_FILENAMES | Win title plate. Copy may be generic; styling is still the ski pack. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/wins/ui_win_mega.png` | png | 1.9 MB | uiAssetRegistry.ts V2_WIN_TITLE_FILENAMES | Win title plate. Copy may be generic; styling is still the ski pack. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/wins/ui_win_super.png` | png | 2.0 MB | uiAssetRegistry.ts V2_WIN_TITLE_FILENAMES | Win title plate. Copy may be generic; styling is still the ski pack. | yes | REVIEW |
| `frontend/apps/poc/static/assets/skyjump_v2/ui/wins/ui_win_world_record.png` | png | 2.4 MB | uiAssetRegistry.ts V2_WIN_TITLE_FILENAMES | Win title plate. Copy may be generic; styling is still the ski pack. | yes | REVIEW |
| `frontend/apps/poc/static/assets/spines/anticipation/anticipation.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/anticipation/anticipation.png` | png | 774 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/anticipation/anticipation.webp` | webp | 194 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bigwin/big_wins.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bigwin/big_wins.png` | png | 643 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bigwin/big_wins.webp` | webp | 249 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bonusButton/2.0/buy_button.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bonusButton/2.0/buy_button.png` | png | 141 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bonusButton/2.0/buy_button.webp` | webp | 33 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bonusButton/buy_button.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bonusButton/buy_button.png` | png | 659 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/bonusButton/buy_button.webp` | webp | 103 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/clusterWin/clusterpay.atlas` | atlas | 0 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/clusterWin/clusterpay.png` | png | 9 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/clusterWin/clusterpay.webp` | webp | 3 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/foregroundAnimation/mm_bg.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/foregroundAnimation/mm_bg.png` | png | 2.3 MB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/foregroundAnimation/mm_bg.webp` | webp | 388 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/foregroundFeatureAnimation/mm_bg_feature.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/foregroundFeatureAnimation/mm_bg_feature.png` | png | 1.9 MB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/foregroundFeatureAnimation/mm_bg_feature.webp` | webp | 309 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/fsIntro/fs_screen.atlas` | atlas | 0 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/fsIntro/fs_screen.png` | png | 646 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/fsIntro/fs_screen.webp` | webp | 196 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/globalMultiplier/multiframe.atlas` | atlas | 0 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/globalMultiplier/multiframe.png` | png | 60 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/globalMultiplier/multiframe.webp` | webp | 17 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/loader/loader.atlas` | atlas | 3 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/loader/loader.png` | png | 2.1 MB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/loader/loader.webp` | webp | 507 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/reelhouse/reelhouse_glow.atlas` | atlas | 0 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/reelhouse/reelhouse_glow.png` | png | 180 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/reelhouse/reelhouse_glow.webp` | webp | 57 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/symbols2/symbols2.atlas` | atlas | 12 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/symbols2/symbols2.png` | png | 2.8 MB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/symbols2/symbols2.webp` | webp | 710 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/symbols3/symbols3.atlas` | atlas | 2 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/symbols3/symbols3.png` | png | 2.4 MB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/symbols3/symbols3.webp` | webp | 647 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/symbols/symbols.atlas` | atlas | 3 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/spines/symbols/symbols.png` | png | 1.0 MB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/spines/symbols/symbols.webp` | webp | 719 KB | symbolAssetRegistry.ts or skyjumpArt.ts | Ski, snow, weather, or jumper art. Waiting for a lounge replacement. Do not delete. | yes | REPLACE |
| `frontend/apps/poc/static/assets/spines/transition/transition.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/transition/transition.png` | png | 1.4 MB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/transition/transition.webp` | webp | 360 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/tumbleWin/tumble_win.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/tumbleWin/tumble_win.png` | png | 1019 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/tumbleWin/tumble_win.webp` | webp | 306 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/winMeterExplosion/ui_explosion.atlas` | atlas | 1 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/spines/winMeterExplosion/ui_explosion.png` | png | 616 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/coin/SD2_Coin.png` | png | 2.4 MB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/freeSpins/freeSpins.png` | png | 1.1 MB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/freeSpins/freeSpins.webp` | webp | 316 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/gardenToken/gardenToken.png` | png | 92 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/minerCoin/minerCoin.png` | png | 78 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/payFrame/payFrame.png` | png | 386 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/pressToContinueText/MM_pressanywhere.png` | png | 109 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/pressToContinueText/MM_pressanywhere.webp` | webp | 46 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/progressBar/progressBar.png` | png | 43 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/progressBar/progressBar.webp` | webp | 12 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/reelsFrame/reels_frame.png` | png | 715 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/symbolsGardenCandidate/symbolsGarden.png` | png | 831 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/symbolsGardenCandidate/symbolsGarden.webp` | webp | 610 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/symbolsStatic/symbolsStatic.png` | png | 900 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/symbolsStatic/symbolsStatic.webp` | webp | 587 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/uiSlotsAssetsBespoke/autospin_active.png` | png | 6 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/uiSlotsAssetsBespoke/autospin_active.webp` | webp | 28 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/uiSlotsAssetsBespoke/autospin_active_hover.png` | png | 5 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/uiSlotsAssetsBespoke/autospin_active_hover.webp` | webp | 28 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/uiSlotsAssetsBespoke/turbo_active.png` | png | 5 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/uiSlotsAssetsBespoke/turbo_active.webp` | webp | 28 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/uiSlotsAssetsBespoke/turbo_active_hover.png` | png | 4 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/uiSlotsAssetsBespoke/turbo_active_hover.webp` | webp | 28 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/winSmall/MM_Localisation_winsmall.png` | png | 396 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/assets/sprites/winSmall/MM_Localisation_winsmall.webp` | webp | 116 KB | Pixi asset manifest / SDK sample | Sample or SDK pack. Not the live lounge plate. Do not delete without a reference check. | partial | REVIEW |
| `frontend/apps/poc/static/favicon.svg` | svg | 2 KB | app.html | Browser icon. Swap only when a lounge mark exists. | partial | REVIEW |
| `frontend/apps/poc/static/loader.gif` | gif | 77 KB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | partial | REVIEW |
| `frontend/apps/poc/static/stake-engine-loader.gif` | gif | 1.2 MB | see filename; confirm before swap | Not classified as purely generic. Leave in place. | partial | REVIEW |
