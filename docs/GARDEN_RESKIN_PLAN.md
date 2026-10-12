# Garden Bounty reskin plan

Last updated: 2026-09-15

## Goal

Create a second illustrated theme on top of the working Miner's Fortune frontend and
local gameplay adapter. Preserve mechanics, symbol keys, animation contracts, audio,
and the `97%` local QA payout table. Replace the mine presentation with a warm,
hand-painted garden/orchard world.

Branch: `feat/garden-reskin`

This branch is based on `feat/hand-drawn-assets` / PR #1 and should not be merged
before that dependency.

## Art direction

- Working title: **Garden Bounty**.
- Hand-drawn 2D cartoon art with dark ink outlines, matte gouache texture, controlled
  cel shading, small painted imperfections, and strong silhouettes at 200 px.
- Palette: leafy greens, tomato red, aubergine purple, blueberry blue, sunflower
  yellow, warm soil brown, and soft daylight.
- Avoid glossy 3D rendering, photorealism, neon, bloom, UI baked into backgrounds,
  and overly detailed textures.
- Raster generation uses only local ComfyUI at `http://127.0.0.1:8188`.

## Symbol map

Runtime keys and atlas frame names remain unchanged.

| Key       | Garden treatment                                      | Action                     |
| --------- | ----------------------------------------------------- | -------------------------- |
| H1        | Friendly older gardener in a straw hat                | Regenerate                 |
| H2        | Wooden wheelbarrow filled with produce                | Regenerate                 |
| H3        | Rounded metal watering can                            | Regenerate                 |
| H4        | Illustrated shovel                                    | Reuse current approved art |
| H5        | Illustrated pickaxe / garden pick                     | Reuse current approved art |
| L1        | Ripe red tomato                                       | Regenerate                 |
| L2        | Purple aubergine                                      | Regenerate                 |
| L3        | Green broccoli crown                                  | Regenerate                 |
| L4        | Blueberry cluster with leaves                         | Regenerate                 |
| W         | Crossed garden shears and sunflower with readable `W` | Regenerate                 |
| S         | Golden pumpkin with readable `SCATTER`                | Regenerate                 |
| M2/M4     | Round wooden multiplier garden badges                 | Regenerate                 |
| M5/M7/M10 | Premium produce-wreath multiplier badges              | Regenerate                 |

## Environment map

- Mine tunnel background -> sunlit garden/orchard with a pergola, fruit trees,
  raised beds, stone path, and a quiet central area for the reels.
- Timber/steel reel frame -> painted wood, trellis joints, leaves, and brass details.
- Mine dust -> pollen, drifting leaves, and small firefly-like motes.
- Miner coins -> garden tokens with a sunflower/leaf face.
- Gold/miner typography -> warm cream and sunflower-gold garden typography.
- Miner paytable/rules/loader/free-spin copy -> Garden Bounty copy.

## Execution stages

1. [x] Create the dependent local branch and persist the theme map.
2. [x] Add reproducible garden input-preparation and ComfyUI workflow builders.
3. [x] Generate and visually review the first symbol/background candidates.
4. [x] Remove backgrounds, assemble a contract-compatible atlas, and keep H4/H5.
5. [x] Register the new background/atlas and verify base spins in `/dev-preview`.
6. [x] Reskin frame, ambience, HUD, loader, win, Free Spins, and transitions.
7. [x] Replace miner-specific rules/paytable/copy and rename the presentation.
8. [x] Generate and register the garden token atlas.
9. [ ] Finish desktop/portrait functional QA.
10. [x] Push the Garden Bounty branch and open PR #2 to `main`.

## Acceptance checks

- The original Miner's Fortune branch and its approved assets remain recoverable.
- Symbol keys, frame names, and animation event contracts do not change.
- Manual BET, random wins, Auto Spin, bet controls, and Buy Bonus remain functional.
- `/dev-preview` returns to `Auto 0 · Machine idle` after every completed flow.
- Both desktop and 480x900 portrait layouts are readable.
- Production build succeeds; audio remains unchanged.

## First-batch selection notes

- Accepted background seed: `93482711`.
- Accepted symbol seeds: `9302001` through `9302014`.
- H4/H5 are copied directly from the approved Miner's Fortune atlas.
- H1 reads well at slot size. The miner headlamp and its circular outline were
  removed with local Qwen Image Edit (seed `9302105`, denoise `0.7`) plus BiRefNet,
  then fitted into `symbolsGardenCandidate`.
- M5/M7 retain crossed pickaxes as intentional cross-theme reuse.
- Contact sheet: `outputs/garden_stage1_contact_sheet.png` in the originating Codex task.

## Stage 1 QA

- Production build passed; `/` and `/dev-preview` prerendered with status 200.
- Live `/dev-preview` loaded the garden background and all contract-compatible frames.
- A manual `$1` random spin changed the board, settled `$1000 -> $999`, and returned
  to `Auto 0 · Machine idle`.
- Garden title, loader copy, transition copy, rules, paytable labels, feature tint,
  frame glow, and ambient motes have their first theme pass.

## Stage 2 UI and animation pass

- Added a dedicated `garden` UI theme without removing the recoverable `miner` theme.
- Recolored Pixi HUD controls and HTML modals to the leafy green, cream, and
  sunflower-gold palette.
- Recolored the loader, anticipation, symbol-win frame, Free Spins intro/counter/
  outro, transitions, and BIG WIN presentation.
- Renamed garden-facing component/style modules so no miner naming remains in the
  active presentation code.
- Added `tools/assets/generate_garden_token_atlas.ps1` and registered its reproducible
  12-frame sunflower token under the unchanged `coins` / `coin` runtime contracts.
- Audited active asset registration: apart from intentionally reused H4/H5 and
  unchanged audio, no mine-specific raster or Spine asset is loaded by the game.

## Stage 2 QA

- Production build passed again; `/` and `/dev-preview` prerendered with status 200.
- Live dev server and the new garden-token JSON both respond with status 200.
- `git diff --check` passed.
- Desktop interaction and 480x900 portrait checks remain open because the current
  in-app browser tab could not be reclaimed after its browser session changed.

## Continued production work

The visual-reskin checklist ends with responsive regression and PR publication.
Production math, RGS integration, asset licensing, Stake Engine ACP testing, and
release readiness continue in `docs/GARDEN_PRODUCTION_TODO.md`.
