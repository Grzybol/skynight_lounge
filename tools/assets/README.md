# Deterministic local asset generators

These scripts generate small code-authored raster assets without cloud services or
image-generation APIs.

## Miner's Fortune coin atlas

`generate_miner_coin_atlas.ps1` creates the 12-frame spinning coin atlas used by
`WinCoins.svelte`. The output is:

- `frontend/apps/poc/static/assets/sprites/minerCoin/minerCoin.png`
- `frontend/apps/poc/static/assets/sprites/minerCoin/minerCoin.json`

Run from the repository root:

```powershell
.\tools\assets\generate_miner_coin_atlas.ps1
```

The logical asset key remains `coins`, so the existing Pixi particle emitter,
win-level frequency settings, timing, and audio behavior remain unchanged.

## Garden Bounty token atlas

`generate_garden_token_atlas.ps1` creates the contract-compatible 12-frame
sunflower-and-leaf token used by the garden reskin:

- `frontend/apps/poc/static/assets/sprites/gardenToken/gardenToken.png`
- `frontend/apps/poc/static/assets/sprites/gardenToken/gardenToken.json`

Run it from the repository root:

```powershell
.\tools\assets\generate_garden_token_atlas.ps1
```

It intentionally keeps the `coin` animation name and logical `coins` asset key.

## Garden Bounty candidate assembly

`prepare_garden_inputs.ps1` extracts and upscales the approved miner atlas cells for
the local Qwen Image Edit workflow. H4 and H5 are intentionally not extracted because
their approved shovel/pickaxe art is reused unchanged.

After the garden batch and BiRefNet alpha workflow finish,
`assemble_garden_candidates.py` creates an isolated candidate atlas while preserving
all runtime frame keys:

```powershell
python .\tools\assets\assemble_garden_candidates.py `
  --alpha-directory 'C:\path\to\ComfyUI-Shared\output\slot_garden\alpha_final' `
  --background 'C:\path\to\ComfyUI-Shared\output\slot_garden\background_drawn_v1_00001_.png'
```

The default output is `symbolsGardenCandidate`; it does not overwrite the active
Miner's Fortune atlas.
