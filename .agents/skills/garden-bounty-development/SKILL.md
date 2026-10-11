---
name: garden-bounty-development
description: Continue, test, or release the Garden Bounty Stake Engine slot in this repository. Use for garden/vegetable/fruit visual work, local ComfyUI asset generation, Pixi/Svelte animations, production math and RTP preparation, RGS integration, QA, handoff, or Stake Engine publication tasks for frontend/apps/poc.
---

# Garden Bounty Development

Continue the active Garden Bounty product without reconstructing earlier miner work.
Treat repository documentation and runtime contracts as the source of truth.

## Start every task

1. Run `git status -sb` and confirm the active branch.
2. Read `../../../AGENTS.md`.
3. Read `../../../docs/GARDEN_PRODUCTION_TODO.md`.
4. Read `../../../docs/GARDEN_RESKIN_PLAN.md`.
5. Continue from the first unchecked item relevant to the user request.
6. Preserve unrelated user changes.

## Route the work

- For raster art, read `../../../tools/comfy/README.md`; use only local ComfyUI at
  `http://127.0.0.1:8188` and persist workflow builders, prompts, seeds, and output
  assembly steps.
- For deterministic atlases, read `../../../tools/assets/README.md` and preserve
  logical Pixi animation keys.
- For frontend or animation work, preserve symbol/book/emitter contracts and add a
  focused `/dev-preview` scenario when needed.
- For math or Stake publication, treat the local demo adapter as QA-only. Synchronize
  frontend and Python configuration before generating books.
- For asset cleanup, read `../../../docs/DEMO_ASSET_AUDIT.md`; do not assume demo
  audio or reused art has commercial clearance.

## Preserve the Garden Bounty identity

- Use a warm garden/orchard world with vegetables, fruit, trellis wood, leaves,
  sunlight, and sunflower-gold accents.
- Render in hand-drawn 2D cartoon style with bold dark ink, matte gouache texture,
  controlled cel shading, and strong silhouettes at slot size.
- Avoid photorealism, glossy 3D casino art, neon bloom, watermarks, logos, noisy
  backgrounds, or UI baked into raster assets.
- Keep `stateUi.config.theme = 'garden'` isolated from the recoverable `miner` and
  shared default themes.

## Validate proportionally

For frontend batches:

1. Exercise the relevant `/dev-preview` mode and return to base game.
2. Inspect desktop and 480x900 when layout is affected.
3. Run `git diff --check`.
4. Run the POC production build.

For production math:

1. Run a small uncompressed debug batch.
2. Validate every emitted event against frontend handlers.
3. Run production-scale compressed simulations for every mode.
4. Optimize RTP, generate analysis/PAR outputs, run RGS format checks, and inspect
   `library/publish_files/`.

Record decisions, validations, blockers, and the next unchecked action in
`../../../docs/GARDEN_PRODUCTION_TODO.md` before handing off.
