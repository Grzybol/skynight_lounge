# SKYJUMP V2 — V1 → V2 Reuse Audit

**Scope:** Repository as inspected on the current worktree. V1 product is the 6-slot SkyJump on Stake Engine. V2 is a 5×5 payline slot. **Do not rewrite working RGS / auth / HUD just because gameplay changes.**

Classifications: **KEEP** / **ADAPT** / **REMOVE** (runtime unplug, files stay) / **REPLACE** (new V2 module; V1 file remains until cutover).

---

## 1. Stake platform — KEEP

| System | Path | Notes |
| --- | --- | --- |
| Authenticate / session | `frontend/packages/components-shared/.../Authenticate.svelte` | `POST /wallet/authenticate`; URL `sessionID` + `rgsUrl` |
| RGS play / end-round / event ack / replay | `frontend/packages/rgs-requests` | Book in `round.state` |
| Amounts | `API_AMOUNT_MULTIPLIER`, `BOOK_AMOUNT_MULTIPLIER` (100 = 1×) | Keep rounding helpers |
| XState primary + autoplay | `frontend/packages/utils-xstate` | boot / idle / betting / turbo / errors |
| Game actor wiring | `frontend/apps/poc/src/game/actor.ts` | **ADAPT** internals; do not replace with a parallel wallet |
| Book player | `frontend/packages/utils-book` | Sequential `playBookEvents` |
| Shared bet state | `frontend/packages/state-shared` `stateBet` | balance, bet, turbo, autoplay, mode |
| i18n / hotkeys / space-hold | `components-shared` | Keep; add V2 copy keys later |
| Modals shell | `components-ui-html` (settings, autoplay, buy confirm, errors) | Swap paytable/rules snippets |
| Theme hook | `stateUi.config.theme = 'skyjump'`, `body.theme-skyjump` | Keep miner/garden available |
| `gameID` | `0_0_poc` until ACP | Do not invent |

**Do not rewrite** these because the board becomes 5×5.

---

## 2. Actor / bonus / resume — ADAPT

| Item | V1 | V2 |
| --- | --- | --- |
| `checkIsBonusGame` | **Always `false`** (single round; `noWin` / `singleRoundWin`) | **Must become true** when the book contains FS (`bonusWin` path). Detect `skyjumpFreeSpinsStart` or scatter trigger |
| `onResumeGameInactive` | Replays weather + six `skyjumpSlot` | Replay V2 snapshot (board, meters, FS) |
| `convertTorResumableBet` | Reserves weather/slot/result/wincap/setTotalWin | Extend reserved types to schema 2 (see event protocol) |
| `createBonusSnapshot` handler | Rebuilds V1 presentation | Rebuild V2 board + feature state |
| `onNewGameStart` | `skyjumpResetBoard` | Reset 5×5 + V1 strip if still mounted |

Risk: leaving `checkIsBonusGame: false` will mis-settle Free Spins.

---

## 3. HUD / bet / turbo / autoplay — KEEP, light ADAPT

| System | Path | V2 |
| --- | --- | --- |
| Pixi HUD | `components-ui-pixi` `SkyJumpHud.svelte`, layouts | KEEP dock |
| CSS dock glass | `SkyJumpHudFrame.svelte` + `skyjumpHud.ts` | KEEP; safe-area |
| Balance / win / bet labels | `LabelBalance`, `LabelWin`, `LabelBet` | KEEP |
| Turbo | `stateBet.isTurbo` → `TIMING_PROFILES` | KEEP contract; new V2 timings table |
| Autoplay | XState + modal | KEEP; must wait for FS books |
| Buy bonus | `ButtonBuyBonus` + `stateMeta.betModeMeta` | ADAPT **mode list**: drop `MULT_10_100` / `MULT_20_200`; add V2 FS buys when costs exist |
| Free spin counter | `LabelFreeSpinCounter` (already in SkyJump HUD, unused by V1 math) | **ADAPT** — finally used |
| Menu flyout | paytable / rules / settings / sound / language | KEEP; new V2 paytable/rules components |

---

## 4. Layout / Pixi stage — KEEP engine, ADAPT sizes

| System | Path | V2 |
| --- | --- | --- |
| Resize / letterbox | `utils-layout` `createLayout` | **KEEP** — do not replace with hardcoded 1280×720 |
| POC sizes | `stateLayout.ts` 1422×800 desktop | **ADAPT** toward 1280×720 desktop logical |
| Pixi `App` | `Game.svelte` | KEEP |
| HTML V1 overlays vs Pixi scale | Reel strip in CSS `vw` | **REPLACE** board placement; HUD dock pattern is the model |

See `04_UI_LAYOUT_AND_RESPONSIVE.md`.

---

## 5. Audio — KEEP direction, ADAPT cues

| System | Path | V2 |
| --- | --- | --- |
| BGM playlist | `static/assets/audio/skyjump/bgm/` + `skyjumpAudio.ts` | KEEP winter identity |
| HTMLAudio vs Howler mute | Documented V1 workaround | KEEP until Stake audio contract changes |
| SFX | skiing/wind/win/lose + farmer sprite for button/reel-stop | ADAPT: new stop/land/feature stings; still no farmer win BGM |
| `Sound.svelte` / `EnableSound` | poc | KEEP |

Legal: BGM license evidence still undocumented (V1 release-readiness). Not a V2 design blocker; still a publish blocker.

---

## 6. Current SkyJump gameplay — REPLACE (keep files)

| System | Path | Classification |
| --- | --- | --- |
| Weather draw UI + engine | `SkyJumpWeatherDraw.svelte`, weather tables | **REMOVE** from V2 round loop. Art may remain as atmosphere |
| Sequential slots 1–6 | `SkyJumpReelStrip.svelte`, `skyjumpSlot` | **REPLACE** with 5×5 board |
| Distance / payout curve | `resolveRound.ts`, overlay formula | **REPLACE** |
| Result overlay card | `SkyJumpResultOverlay.svelte` | **ADAPT or REPLACE** — overlay/toast, not fullscreen `Win.svelte` |
| Hill badge / takeoff FX | `SkyJumpHillBadge`, `SkyJumpTakeoff` | REMOVE from scoring; optional FX |
| V1 event types | `typesBookEvent.ts` weather/slot/result | Keep for V1; V2 uses schema 2 |
| `bookEventHandlerMap` V1 handlers | poc `bookEventHandlerMap.ts` | ADAPT: add schema 2 handlers or split maps |
| `localDemo.ts` | V1 resolver | ADAPT: V2 fixtures/resolver behind flag |
| `numReels: 6`, `numRows: [1×6]` | `config.ts`, `game_config.py` | **REPLACE** with 5 and `[5,5,5,5,5]` in **V2 config only** |
| Empty V1 `paylines: {}` | intentional | V2 fills canonical 28 lines in v2 JSON |

Garden `Board.svelte` is **not mounted**. Farmer 5×3 `stateGame.board` / `utils-slots` still **constructed**. Classification: leftover **REMOVE from V2 runtime**; do not delete farmer files. Do not treat that board as a 5×5 starter (it is 5×3 padded).

---

## 7. Math / books / tests

| System | Path | V2 |
| --- | --- | --- |
| V1 canonical JSON | `math/games/0_0_poc/skyjump_config.json` mathVersion 3 | **KEEP frozen.** Do not mutate |
| V1 resolver | `skyjump_resolve.py`, `frontend/.../resolveRound.ts` | KEEP for V1 / localDemo V1 |
| V1 book writer | `gamestate.py`, `run.py` | KEEP for V1; V2 gets a **new** path |
| LUT / optimization | `game_optimization.py`, `math/src/write_data` | ADAPT copies for V2. The Stake LUT **0.10×** grain (`payoutMultiplier % 10 == 0`) is a **production constraint for V2**, not a V1-only curiosity. See `02_MATH_SPEC.md` §9. |
| Exact enumerator | `tools/skyjump/exactEv.ts` | **REMOVE from V2 method** (infeasible). Keep file for V1 |
| Simulator | `tools/skyjump/simulate.ts` | REPLACE with V2 sim |
| Tests | `test_skyjump_resolve.py`, `tools/skyjump/test-math.ts` | KEEP V1 freeze tests green on CI |
| Parity | `math/tests/test_config_parity_poc.py` | KEEP V1; add `test_config_parity_v2.py` |
| Smoke writer | `write_skyjump_smoke.py` | KEEP V1; add V2 smoke later |
| Farmer lines SDK | `math/src/calculations/lines.py` | Reference only; **do not** enable wilds |
| Sample 5×5 apps | `frontend/apps/price`, `math/games/0_0_lines_feature_match` | Historical farmer samples — **do not copy** as SkyJump |

Production books / `stake-upload/` / `math/library/`: **do not touch** in the V2 design phase. Uncommitted copies exist on the dirty branch (see §12).

---

## 8. Config parity pattern — KEEP as the model

V1 already solved dual-language constants:

- Canonical JSON in `math/games/0_0_poc/`
- TS: `import rawConfig from '...json' with { type: 'json' }`
- Python: load the same file
- Pytest asserts FE/Python/JSON

**V2 canonical source:** `skyjump_v2_config.json` (new). Same import pattern. Paylines live there once. No duplicated 28-line arrays in Svelte.

---

## 9. Frontend identity — KEEP / ADAPT

| System | V2 |
| --- | --- |
| `SkyJumpBackground`, atmosphere | KEEP as environment |
| `SkyJumpBrand` logo | KEEP |
| `SkyJumpMainMenu` | ADAPT copy; still hide HUD via `uiHide` |
| `SkyJumpPayTable` / `SkyJumpGameRules` | REPLACE content for 5×5 / tokens / FS (new components OK; V1 files stay) |
| `assets.ts` | ADAPT: register V2 placeholders then art |
| i18n `en.ts` / `pl.ts` | ADAPT strings |
| `/dev-preview` | KEEP QA-only; add V2 fixtures; never production RTP |
| Loader / loading screen | KEEP with SkyJump branding |

---

## 10. Build / CI / upload

| System | Path | V2 |
| --- | --- | --- |
| Vite poc | `frontend/apps/poc` `npm run build` | KEEP |
| Dev server | port 3010 / 4010 | KEEP |
| GitHub Actions | `.github/workflows/skyjump.yml` | ADAPT: add V2 tests **without** dropping V1 freeze tests |
| `check-placeholders.ts` | ACP ids | KEEP |
| `audit-production-bundle.ts` | strips farmer / old music | KEEP; extend allowlists for V2 assets |
| Prettier | `frontend/node_modules/.bin/prettier.cmd` | KEEP |
| Comfy pipeline | `tools/comfy` | KEEP for later Phase 8; local API only |

---

## 11. Summary tables

### KEEP (safe to reuse as-is)

Stake authenticate, RGS requests, XState machines, book player, HUD controls, turbo flag, autoplay machine, settings/error modals, theme-skyjump, audio architecture, `createLayout` scaling, `/dev-preview` gating, V1 math JSON + V1 tests, production build pipeline, `gameID` placeholder policy.

### ADAPT

`actor.ts` bonus detection and resume, snapshot type list, `bookEventHandlerMap`, `config.ts` reels/rows/modes (via **v2 JSON**), buy-bonus meta, layout logical sizes, FS counter, paytable/rules copy, CI extra steps, localDemo flag.

### REMOVE from V2 runtime (files stay)

Weather-as-math, 6-slot strip as the game, V1 distance curve, V1 overlay-as-sole-result, `MULT_10_100` / `MULT_20_200`, garden 5×3 board instance, farmer wild paylines, V1 exact enumerator as V2 RTP method.

### REPLACE (new V2 modules)

5×5 board, line evaluator (no wilds), feature-chain reducer, schema 2 events, V2 config/resolver/writer/sim, placeholder symbol set, FS state machine, bet mode set BASE + four FS buys.

---

## 12. Git / worktree note (audit time)

Inspected branch: `chore/skyjump-production-books` (not `main`).  
`main` tip: `c0585f7` (PR #9 SkyJump V1).  
HEAD: `3691a62` plus **dirty** math/writer/HUD/docs files and untracked `stake-upload/`, `math/library/`.

V1 must be tagged from a **clean** canonical commit, not this dirty tree. Uncommitted V1 production-book work is out of scope for V2 and must not be mixed into `feat/skyjump-v2-5x5`.
