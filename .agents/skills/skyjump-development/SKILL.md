---
name: skyjump-development
description: Continue, test, or release the SkyJump Stake Engine ski-jump mini-game in this repository. Use for winter-sports visual work, local ComfyUI asset generation, sequential reel UX, weather/hill math, RGS integration, QA, or Stake Engine publication tasks for frontend/apps/poc on feat/skyjump-game.
---

# SkyJump Development

Continue SkyJump on `feat/skyjump-game`. Treat farmer/garden code as the Stake
Engine baseline, not the active theme. Do not edit `main`.

## Start every task

1. Run `git status -sb` and confirm `feat/skyjump-game`.
2. Read `../../../AGENTS.md`.
3. Read `../../../LEGACY_REUSE_AUDIT.md`.
4. Read `../../../SKYJUMP_ARCHITECTURE.md`.
5. Read `../../../SKYJUMP_IMPLEMENTATION_STATUS.md` and continue from NEXT STEPS.
6. Preserve Stake RGS / XState / HUD unless the task is explicitly about them.

## Route the work

- Gameplay and UI live in `frontend/apps/poc/src/components/skyjump` and
  `frontend/apps/poc/src/game/skyjump`.
- Math tables and `resolveRound` must stay UI-free and data-driven.
- Local demo books come from `localDemo.ts` → resolver → `roundToBookEvents`.
- Raster art: local ComfyUI only (`http://127.0.0.1:8188`). If it is down, keep
  placeholders and update `assets/skyjump/generated/assets-manifest.json`.
- Production math-sdk (`math/games/0_0_poc/run.py`) still emits farmer 5x3
  books. Do not present those as SkyJump RTP.

## Preserve SkyJump identity

- Horizontal 6-slot sequential reveal, weather draw, result overlay.
- Local multipliers (slots 1–5 product) plus final multiplier (slot 6).
- Overlay, not a fullscreen win screen. Turbo is timing-only.

## Validate

1. `node --experimental-strip-types tools/skyjump/test-math.ts`
2. `python math/games/0_0_poc/test_skyjump_resolve.py`
3. poc production build when workspace links are healthy
4. `/dev-preview` menu → spin → overlay, plus turbo and buy bonus
