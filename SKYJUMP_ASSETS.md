# SkyJump release assets

Runtime production art is registered in
`frontend/apps/poc/src/game/assets.ts`. Unregistered static files must not be
treated as shipped just because they sit in the farmer template tree.

## Shipped

| Asset | Path | License |
| --- | --- | --- |
| Menu / play backgrounds, jumper, result art, reel icons | `frontend/apps/poc/src/assets/skyjump/` | see `generated/assets-manifest.json` where Comfy prompts exist; otherwise **license status not documented** |
| SkyJump BGM | `frontend/apps/poc/static/assets/audio/skyjump/bgm/frostbet-1.mp3` … `frostbet-3.mp3` | **license status not documented** |
| SkyJump SFX | `frontend/apps/poc/static/assets/audio/skyjump/sfx/` | **license status not documented** |
| Howler button / reel sprite atlas | `frontend/apps/poc/static/assets/audio/sounds.{json,mp3,ogg,m4a,ac3}` | farmer template; **license status not documented** |

## Explicitly not loaded

`frontend/apps/poc/static/assets/audio/skyjump/old music/` is not referenced by
`skyjumpAudio.ts`. `tools/skyjump/strip-legacy-static.mjs` deletes it from
`build/` so it is not shipped.

Farmer Spine / Garden sprite / miner font trees remain in
`frontend/apps/poc/static/assets/{spines,sprites,fonts}` as dormant template
files. The same strip script removes them from `build/` after `vite build`.

## Checklist before Stake upload

- [ ] Confirm BGM/SFX commercial license in writing and store evidence in-repo
- [ ] Replace or isolate the farmer Howler atlas if Stake objects to unused `bgm_main` sprites
- [ ] Keep `assets.ts` as the only runtime raster registry
- [ ] Do not claim a file is commercially licensed without repository evidence
