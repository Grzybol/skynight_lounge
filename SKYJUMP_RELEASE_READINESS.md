# SkyJump release readiness

Current source for Stake Engine production-book / ACP work.
Historical math audits (`SKYJUMP_MATH_AUDIT.md`, `SKYJUMP_MATH_V2_REPORT.md`,
`SKYJUMP_AUDIT.md`) are evidence snapshots — do not rewrite them to hide old names.

## Frozen math

| Field | Value |
| --- | --- |
| mathVersion | 3 |
| eventSchemaVersion | 1 |
| canonical file | `math/games/0_0_poc/skyjump_config.json` |
| SHA-256 | `321dedd2d88259b37b7d779d000ddfe5a154bc1a9512a1dceb67830f91eefd33` |

Exact enumerator RTP (`E[finalWinX] / costMultiplier`):

| Mode | RTP |
| --- | ---: |
| BASE | 96.934449945% |
| LARGE_HILL | 97.086611908% |
| SKI_FLYING | 97.179578549% |
| MULT_10_100 | 96.808086909% |
| MULT_20_200 | 96.927221614% |

Do not retune tables, weights, curves, caps, costs, rounding, or settlement.

## Production architecture

- App: `frontend/apps/poc` (Stake RGS / XState / HUD reused).
- Books: `skyjumpWeather` → `skyjumpSlot` ×6 → `skyjumpResult` → `setWin` / `wincap` / `setTotalWin` / `finalWin`.
- Writer: `math/games/0_0_poc/gamestate.py` → `resolve_round` (not farmer 5×3).
- Mode keys published to Stake are canonical `rgsKey` values: `BASE`, `LARGE_HILL`, `SKI_FLYING`, `MULT_10_100`, `MULT_20_200`.
- HUD buy list is derived from enabled canonical buy modes. BASE is the default/normal mode.
- Production frontend consumes book events. `resolveRound()` is only for `/dev-preview` localDemo (DEV + localhost).
- `/dev-preview` is not prerendered into the production static site.

## Public identity vs frozen metadata

Player-facing title is **SkyJump** (`PUBLIC_GAME_TITLE`).

Frozen canonical `meta.altTitle` is still `SkiFly Jackpot`. That string is **not**
read at runtime. Changing it requires a separate metadata-only canonical JSON
migration (hash would change). Do not treat it as a live jackpot mechanic — the
game has none.

## ACP placeholders — do not invent values

Replace only after Stake ACP issues them:

- `gameID` = `0_0_poc`
- provider name = `poc_studio`
- provider number = `0`
- frontend version string = `0.1.0-skyjump`

`node --experimental-strip-types tools/skyjump/check-placeholders.ts` warns.
`--strict` fails and is for release packaging, not local development.

## What is ready

- mathVersion 3 freeze + exact RTP regression guards
- five published modes consistent from JSON → Python GameConfig → RGS keys → HUD
- player rules/paytable: Final Jump Multiplier, mode max win, buy-mode cost
- Twist/Garden/Superante default copy removed from SkyJump `state-shared` defaults
- production build strips farmer spines/sprites/fonts and archived BGM
- root GitHub Actions: `.github/workflows/skyjump.yml`
- math-sdk env: `pip install -r requirements.txt` includes `zstandard`
- writer tests for mode cost / maxWin / hill / multiplier profile

## What remains blocked

### P0 — production books / Stake pipeline

- No production-scale `.jsonl.zst` books yet (next dedicated task).
- ACP identifiers are still placeholders.

### P1 — Stake review

- Licensed commercial BGM evidence is not documented in-repo (`frostbet-*`: license status not documented).
- Farmer Howler sprite atlas (`sounds.mp3` / `sounds.json`) still ships because SkyJump button/reel SFX live on that atlas. Playback of farmer win BGM is blocked in code.
- Real RGS / Stake developer-session testing has not been run.

### P2 — later

- `meta.altTitle` metadata-only JSON migration (would change the frozen hash).
- Removing dormant farmer template files that are no longer copied into `build/`.
- GitHub repository name still contains “Jackpot”; out of scope.

## Next step

Generate and independently validate production Stake books from
`math/games/0_0_poc/run.py` after installing the math-sdk environment.
Do not invent ACP IDs during that task.
