# SkyJump development guide

The active product is **SkyJump**, a premium winter-sports casino mini-game for
Stake Engine. Frozen canonical JSON still stores `meta.altTitle = SkiFly Jackpot`
as metadata debt; that string is not player-facing and must not be treated as a
jackpot mechanic.

`main` is the published default branch. Do not force-push `main` or delete the
farmer source tree. New work should use a fresh branch (not edit `main` directly).

The active app is still `frontend/apps/poc`. Farmer files are the technical
starter: transform that app in place. Do not add a parallel SkyJump wallet,
XState, or RGS stack.

## Read first

1. `LEGACY_REUSE_AUDIT.md` — what to reuse, modify, or replace from farmer.
2. `SKYJUMP_ARCHITECTURE.md` — states, math, books, UI split.
3. `SKYJUMP_RELEASE_READINESS.md` — frozen math, ACP placeholders, remaining blockers.
4. `SKYJUMP_IMPLEMENTATION_STATUS.md` — current checkpoint and next steps.
5. `CUSTOM_FILES.md` — frontend/math asset map (farmer-era; treat as history).
6. `docs/FUNCTIONAL_QA.md` — local tester behavior.
7. `tools/comfy/README.md` when generating raster art.
8. `tools/skyjump/README.md` for math tests and the developer simulator.

Garden/miner docs under `docs/` are historical baseline notes, not the active
product direction on this branch.

## Product and art direction

- Theme: ski jumping, snow, floodlights, mountains, night stadium.
- Look: premium winter-sports casino mini-game, not a 5x3 fruit slot.
- Palette: ice blue, night navy, floodlight gold, snow cream.
- Avoid glossy 3D casino clutter, neon bloom, baked-in UI, logos, watermarks.
- Use only the user's local ComfyUI API at `http://127.0.0.1:8188` for generated
  raster art. Do not use cloud image-generation services. If Comfy is down,
  keep SVG placeholders and record that in `assets/skyjump/generated/assets-manifest.json`.

## Runtime contracts

- Reuse Stake RGS authenticate / play / end-round, XState, HUD, autoplay, turbo
  flag, settings, and error modals.
- SkyJump books use `skyjumpWeather` → `skyjumpSlot`×6 → `skyjumpResult`, then
  existing `setTotalWin` / `finalWin` (and `wincap` when capped).
- Turbo is timing-only (`stateBet.isTurbo` → `TIMING_PROFILES`).
- Result UX is an overlay card, never a fullscreen win route.
- `/dev-preview` localDemo is QA-only and is not production RTP.
- Keep `gameID` `0_0_poc` until Stake ACP IDs exist. Do not invent credentials.
- Register runtime art in `frontend/apps/poc/src/game/assets.ts`.
- Theme: `stateUi.config.theme = 'skyjump'` / `body.theme-skyjump`. Keep `miner`
  and `garden` themes available for other branches/apps.

## Gameplay contracts

- Horizontal 6-slot strip, sequential reveal 1→6.
- Slots 1–5: run-up, takeoff, flight, wind, landing. Slot 6: final multiplier.
- Local multipliers on slots 1–5 multiply together; they do not replace slot 6.
- Weather is data-driven and affects distance delta + volatility bias.
- Hill tiers: normal / large / ski flying. Buy bonus also has independent
  multiplier tables (standard / 10–100 / 20–200).
- Distance maps through a payout curve. Do not use cash-per-metre.

## Commands

- App root: `frontend/apps/poc`
- Live tester: `http://localhost:3010/dev-preview` (use `4010` if Windows Hyper-V
  blocks 3010)
- Start from app root:
  `..\..\node_modules\.bin\vite.cmd --host 0.0.0.0 --port 3010`
- Production build from app root: `npm run build`
- Format changed frontend files with `frontend/node_modules/.bin/prettier.cmd`.
- Math tests: `node --experimental-strip-types tools/skyjump/test-math.ts`
- Simulator: `node --experimental-strip-types tools/skyjump/simulate.ts --rounds=20000 --mode=BASE --seed=7`
- Python mirror: `python math/games/0_0_poc/test_skyjump_resolve.py`
- Math SDK env: `python -m pip install -r requirements.txt` (includes `zstandard`)
- Production math-sdk entry: `math/games/0_0_poc/run.py` writes SkyJump books
  keyed by Stake `rgsKey`. Do not run a production-scale generate until that
  dedicated task. Smoke only: `python math/games/0_0_poc/write_skyjump_smoke.py`.

If `apps/poc/node_modules/<workspace pkg>` folders are empty (OneDrive/pnpm),
restore links with `pnpm install` from `frontend/` before Vite.

The Vite dev server can show a black canvas after large cross-package HMR
changes. Restart only the process listening on port `3010`, then reload
`/dev-preview`.

## Definition of done

For visual work:

1. Record Comfy prompts, seeds, and workflow notes, or mark SVG placeholders.
2. Verify `/dev-preview`: menu, weather, sequential reels, overlay, turbo, buy
   bonus. Inspect desktop plus 480x900 when layout is affected.
3. Run `git diff --check` and the production build.
4. Update `SKYJUMP_IMPLEMENTATION_STATUS.md`.

For math/release work:

1. Keep resolver tables configurable. Tune weights/curves without rewriting UI.
2. Run the developer simulator; do not treat the result as certified RTP.
3. Production books, PAR, and Stake developer-session checks come after the
   engine foundation is stable.

## Handoff rule

At the start of a new task, run `git status -sb`, confirm `feat/skyjump-game`,
read the files listed above, and continue from `SKYJUMP_IMPLEMENTATION_STATUS.md`.
Do not restart the farmer/garden reskin and do not edit `main`.
