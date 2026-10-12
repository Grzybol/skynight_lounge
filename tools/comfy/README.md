# Local ComfyUI workflow

This folder is the durable recipe for the Miner's Fortune raster pipeline. It replaces
the temporary Codex-chat work directory as the source of truth.

## Rules

- Use only local ComfyUI at `http://127.0.0.1:8188`.
- Do not call cloud image-generation APIs.
- Always start from the corresponding demo asset placed in the Comfy shared input
  directory.
- Keep the prompts, seeds, sampler settings, and final selection notes in version
  control.
- Never overwrite approved production assets before comparing the candidate and
  running the game.

## Installed local model stack

- `qwen_image_edit_fp8_e4m3fn.safetensors`
- `qwen_2.5_vl_7b_fp8_scaled.safetensors`
- `qwen_image_vae.safetensors`
- `Qwen-Image-Lightning-4steps-V1.0.safetensors`
- BiRefNet background-removal model/custom nodes for alpha extraction

The known Comfy Desktop install used during this project is under:

`C:\Users\grzyb\AppData\Local\Comfy-Desktop`

Do not hard-code that location into new project code; scripts accept paths as
parameters or operate on Comfy's API.

## Recreate API workflows

From the repository root:

```powershell
node tools/comfy/build_workflows.js
```

This writes reproducible API payloads into `tools/comfy/generated/`:

- `qwen_symbol_batch_api.json`
- `qwen_background_api.json`
- `background_removal_batch_api.json`

The builders contain the exact prompts, seeds, model names, node types, sampler, CFG,
step count, denoise, and output prefixes used for the approved direction.

Queue a workflow:

```powershell
powershell -ExecutionPolicy Bypass -File tools/comfy/run_prompt.ps1 `
  -PromptPath tools/comfy/generated/qwen_symbol_batch_api.json
```

## Source preparation

Symbol inputs must be named:

`H1_original.png`, `H2_original.png`, `H3_original.png`, `H4_original.png`,
`H5_original.png`, `L1_original.png`, `L2_original.png`, `L3_original.png`,
`L4_original.png`, `W_original.png`, `S_original.png`, `M2_original.png`,
`M4_original.png`, `M5_original.png`, `M7_original.png`, `M10_original.png`.

Copy them into the Comfy shared input folder before queueing. The source extraction
used the demo atlases; do not substitute unrelated imagery.

## Approved outputs

- Symbol atlas:
  `frontend/apps/poc/static/assets/sprites/symbolsStatic/`
- Background:
  `frontend/apps/poc/static/assets/backgrounds/mine_base_drawn.webp`

The current symbol atlas is 800×1000 with 200×200 cells and four columns. Its JSON
frame names are part of the runtime contract and must be preserved.

## Garden Bounty variant

The dependent `feat/garden-reskin` branch keeps this miner workflow intact and adds:

- `tools/assets/prepare_garden_inputs.ps1`
- `tools/comfy/build_garden_workflows.js`
- generated `garden_*_api.json` payloads

Prepare source images from the approved miner atlas:

```powershell
.\tools\assets\prepare_garden_inputs.ps1 `
  -ComfyInputDirectory 'C:\path\to\ComfyUI-Shared\input'
node .\tools\comfy\build_garden_workflows.js
```

H4 (shovel) and H5 (pickaxe/garden pick) are intentionally reused and omitted from
the generated batch. See `docs/GARDEN_RESKIN_PLAN.md` for the complete map.

H1 hat lamp removal (2026-09-15):

1. Start from `slot_garden/static_drafts/H1_drawn_00001_.png`.
2. Cover the lamp on a working copy saved as `garden_H1_hatfix_source.png` in
   Comfy input (plain straw + hat band, no circular badge).
3. Queue `garden_h1_hat_fix_api.json` (Qwen Image Edit, seed `9302105`,
   denoise `0.7`, 4 Lightning steps).
4. Copy the chosen `H1_hatfix_00002_.png` into Comfy input and queue
   `garden_h1_hat_fix_alpha_api.json` (BiRefNet).
5. Fit `H1_alpha_00002_.png` into the `h1.webp` cell of
   `symbolsGardenCandidate` without rebuilding the rest of the atlas.

```powershell
node .\tools\comfy\build_garden_workflows.js
powershell -ExecutionPolicy Bypass -File tools/comfy/run_prompt.ps1 `
  -PromptPath tools/comfy/generated/garden_h1_hat_fix_api.json
```

Before queueing `garden_background_removal_batch_api.json`, copy the Qwen drafts
from Comfy's output tree into its input tree because `LoadImage` is input-scoped:

```powershell
.\tools\comfy\sync_garden_drafts_to_input.ps1 `
  -ComfyOutputDirectory 'C:\path\to\ComfyUI-Shared\output' `
  -ComfyInputDirectory 'C:\path\to\ComfyUI-Shared\input'
```
