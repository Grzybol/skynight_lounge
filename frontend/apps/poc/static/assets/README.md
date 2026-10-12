# Drop-zone: grafiki, animacje, dźwięki gry `poc`

Tu wgrywasz własne pliki assetów. Po dodaniu pliku **zarejestruj go**
w `../src/game/assets.ts` (nazwa logiczna → typ → ścieżka).

- `spines/` / `sprites/` / `fonts/` — farmer template leftovers. Stripped from production `build/` by `tools/skyjump/strip-legacy-static.mjs`.
- `audio/`   — SkyJump BGM/SFX plus the farmer Howler atlas (`sounds.json` + `sounds.{mp3,ogg,m4a,ac3}`) used for button/reel ticks.
- `audio/skyjump/old music/` — not loaded; stripped from production `build/`.

Nazwy kluczy symboli w `assets.ts` muszą zgadzać się z symbolami w
`../src/game/config.ts` oraz w matematyce (`math/games/0_0_poc/game_config.py`).

Pełna instrukcja: patrz `CUSTOM_FILES.md` w korzeniu repo.
