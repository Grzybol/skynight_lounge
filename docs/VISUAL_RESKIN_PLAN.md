# Miner's Fortune — visual reskin plan and handoff

Last updated: 2026-07-27  
Branch: `feat/hand-drawn-assets`

## Objective

Convert the `poc` Stake Engine demo into an original miner-themed game while retaining
the working math, events, sound map, reel behavior, and integration surface. All new
raster generation is local through ComfyUI. UI animation is preferably code-native
Pixi/Svelte.

## Approved art direction

- Hand-drawn 2D cartoon game illustration.
- Bold, clean dark outlines and strong silhouettes.
- Matte gouache/paper texture with restrained hand-painted imperfections.
- Controlled cel shading; no glossy 3D casino finish.
- Palette: deep plum/indigo rock, rust and warm wood, ochre/gold accents, violet
  feature energy.
- Symbols must remain clear at 120–200 px.
- Generated assets preserve the broad composition and gameplay meaning of the demo
  input, but must not simply copy its rendering.

## Completed

- [x] Created branch `feat/hand-drawn-assets`.
- [x] Extracted and compared original symbol inputs.
- [x] Generated the symbol set locally with Qwen Image Edit in ComfyUI.
- [x] Removed backgrounds locally and assembled the Pixi sprite atlas.
- [x] Replaced static symbols and created code-native land/win/explosion animation.
- [x] Created a custom hand-painted mine background from the demo composition.
- [x] Replaced BIG WIN presentation.
- [x] Replaced Free Spins intro, outro, counter, transition, and anticipation.
- [x] Replaced loader and press-to-continue presentation.
- [x] Added the Miner's Fortune logo and local `miner` HUD theme.
- [x] Restyled Balance/Win/Bet and control buttons.
- [x] Restyled Buy Bonus, bet selection, settings, paytable, and game rules.
- [x] Removed unrelated sample bet modes such as Samurai Spin and Super Bonus.
- [x] Replaced demo foreground-dust Spine and Free Spins frame glow with Pixi effects.
- [x] Replaced the remaining `L5/M` Spine symbol with the local hand-drawn 2x badge
      and code-native land/win/explosion motion.
- [x] Replaced the Spine `payframe` with a shared Pixi win frame.
- [x] Replaced inherited reel-frame sprites with a responsive code-native timber,
      forged-steel, rivet, and feature-glow construction.
- [x] Added `/dev-preview` scenarios and a reliable `Back to game` reset.
- [x] Added a default `Base spin (symbols change)` tester scenario that executes the
      real reveal flow and produces a new reel layout on every `Action` click.
- [x] Replaced the inherited bitmap `gold` font with a shared code-native Pixi text
      style for wins, Free Spins, transitions, counters, and symbol multipliers.
- [x] Replaced the inherited glossy coin-particle atlas with a deterministic local
      12-frame Miner's Fortune coin atlas using the existing emitter behavior.
- [x] Removed all remaining confirmed-dead demo registrations from `assets.ts`;
      original source files remain on disk for reference and recovery.
- [x] Added a functional local demo adapter for BET, stake controls, Auto Spin, and
      Buy Bonus, with balance/bet/actor diagnostics in `/dev-preview`.
- [x] Added weighted random base-game books with `97%` theoretical RTP, varied
      matching-symbol wins, correct book/API amount conversion, and end-round balance
      settlement for both manual BET and Auto Spin.
- [x] Persisted the ComfyUI workflow recipe and agent handoff documentation.

## Next work, in priority order

- [ ] Run a final desktop/portrait regression covering base spin, win, Free Spins,
      buy bonus, modals, loader, and reset.
- [ ] Commit the completed visual-reskin batch once the user approves the direction.

## Possible 5x5 gameplay expansion

The current game is 5 reels by 3 visible rows. A true 5x5 conversion is a separate
math/mechanics project, not a visual-only resize. It requires synchronized frontend
and math dimensions, a new win model or new paylines using rows 0-4, regenerated
books/lookup tables, and RTP/volatility tuning. Do not change the board dimensions
as part of the visual reskin without an explicit mechanics decision.

## Important implementation files

- Game composition: `frontend/apps/poc/src/components/Game.svelte`
- Symbol mapping: `frontend/apps/poc/src/game/constants.ts`
- Asset registry: `frontend/apps/poc/src/game/assets.ts`
- Animated symbols: `frontend/apps/poc/src/components/SymbolSpriteAnimated.svelte`
- Background ambience: `frontend/apps/poc/src/components/MineAmbience.svelte`
- Loader: `frontend/apps/poc/src/components/LoaderArtwork.svelte`
- Custom paytable/rules: `MinerPayTable.svelte`, `MinerGameRules.svelte`
- Tester: `frontend/apps/poc/src/routes/dev-preview/+page.svelte`
- Shared scoped UI theme: `frontend/packages/components-ui-pixi` and
  `frontend/packages/components-ui-html`, gated by `stateUi.config.theme === 'miner'`
  or `body.theme-miner`.

## Validation

The production build command is:

```powershell
cd frontend/apps/poc
$env:NODE_OPTIONS='--max-old-space-size=8192'
& '..\..\node_modules\.bin\vite.CMD' build
```

Existing non-blocking warnings include optional public env variables, bundle size,
and Vite static `new URL(...)` resolution warnings.
