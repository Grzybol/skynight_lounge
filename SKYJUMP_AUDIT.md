# SkyJump full implementation audit

Branch reviewed: `feat/skyjump-game` @ `281b11d` plus uncommitted audit fixes listed below.

This is a PR-style review of the existing implementation. It is not a new feature pass.

# Executive summary

The SkyJump loop **does run** on `/dev-preview`: weather → sequential slots 1–6 → overlay card → next round. Canonical JSON is the real source for tables. The math-sdk writer **does emit SkyJump events**, not Garden 5×3 boards, for the configured modes. Production play (when `localDemo` is false) **does not re-roll** on the client; it animates book payloads.

The foundation is usable as an engine prototype. It is **not** production-ready for Stake real-money:

- local git `main` / `origin/main` objects are missing; this checkout is not a healthy clone of the farmer baseline
- Stake published `frontend/apps/poc/src/game/config.ts` still contains Garden paylines/symbols
- Python `GameConfig` still describes a 5×3 lines game
- buy costs / max-win exist in four places
- TS book amounts use `Math.round` (half-up); Python/SDK uses banker's `round`
- resume cannot stop between slot 2 and slot 5 because `skyjumpSlots` is one event
- `/dev-preview` is prerendered into the production static build (client RNG was possible on a public host; gated to localhost during this audit)

**P0: 0 · P1: 9 · P2: 16 · P3: 11**

# P0 blockers

None found that would silently corrupt a **server-generated** SkyJump book settlement **if** RGS serves those books and `localDemo` is off.

The closest production-risk items are listed as P1 (git integrity, published Garden config, rounding split, `/dev-preview` in the static build).

# P1 high priority

1. **Local git is damaged outside `feat/skyjump-game`.** No local `main`. `origin/main` points at missing SHA `6e2c43b0…`. `git remote -v` is empty. `git fsck` reports invalid SHA1 pointers on several local/remote refs and stash. `git diff main...feat/skyjump-game` cannot run. The feature branch objects themselves are valid.

2. **Stake frontend config is still a Garden paytable with SkyJump modes bolted on.** `frontend/apps/poc/src/game/config.ts` still has 20 paylines, fruit/garden symbols, `rtp: 0.97`, and `numReels: 6` while Python `GameConfig.num_reels = 5`. This is what ACP/config publishing will see.

3. **Python math-sdk `GameConfig` is still a 5×3 lines game.** `win_type = "lines"`, farmer `paytable` / `paylines`, leftover wild multiplier assignment. `run_spin` no longer draws that board, but format checks / lookup tables / RGS metadata still describe Garden.

4. **Book amount rounding is not the same in TS vs Python/SDK.** localDemo: `Math.round(finalWinX * 100)` (half-up, `112.5 → 113`). Production writer: SDK `int(round(x * 100))` (banker's, `112.5 → 112`). Overlay cash in localDemo can disagree with a Python-generated book for half-cent multipliers.

5. **Buy-mode numbers are duplicated in four stores.** `skyjump_config.json` `buyModes`, `Game.svelte` `stateMeta`, `frontend/.../config.ts` `betModes`, `game_config.py` `BetMode`. Values currently match (1 / 3 / 8 / 4 / 10 and hill caps 500 / 1500 / 5000) but nothing enforces that.

6. **`/dev-preview` is in the production static build** (`adapter-static` prerenders `200 /dev-preview`). That route sets `localDemo = true` and used to resolve rounds in the browser. Audit fix: localDemo bet/end-round now no-ops unless hostname is `localhost` / `127.0.0.1`.

7. **Resume grain is too coarse.** Interrupt after slot 1 / 3 / 5 cannot be represented in the book: `skyjumpSlots` is a single event. Resume either has not started slots (replay 1→6) or has the full payload (catch-up apply). No re-roll, but not the requested per-slot resume points.

8. **Volatility / clamp constants are duplicated outside JSON.** TS `applyVolatilityBias` and Python `apply_volatility_bias` hardcode `2.4 / 1.8 / 1.2 / 0.35 / 0.05` and bias clamp `1.8`. Tables are canonical; this math is not.

9. **`math/tests/test_config_parity_poc.py` still expects Garden Bounty** (`bonus` mode, 5 reels). It will fail or silently miss SkyJump modes. Leftover CI landmine.

# P2 medium priority

- Vite `apps/poc/vite.config.js` aliases every `frontend/packages/*` directory (and `pixi-svelte` → `index.ts`) plus `cacheDir` in OS temp. Needed because OneDrive/pnpm left empty workspace folders. After a healthy `pnpm install`, `pixi-svelte/dist` exists; aliases still override package `main`. Tech debt, not a local-only binary.
- Relative imports of `config-vite` / `config-svelte` bypass `workspace:*` links. Robust against empty `node_modules/<pkg>`, unusual for CI.
- Overlay / weather / reel `waitForTimeout` chains had no generation guard; a second `playBet` (dev-preview Action spam) could stamp the previous round onto the next. Guards added this audit.
- Turbo: event order is slot6 complete → overlay, but Pixi can paint one frame late. Added `max(32, reelGapMs)` after slot 6.
- Overlay showed `MAX WIN CAPPED` as soon as the card opened. Now payout-phase only.
- Autoplay is XState-serial (`await playBet`) so it should not overlap rounds if the actor is used. `/dev-preview` Action can overlap. Not re-driven for many autoplay rounds in this audit.
- HUD **MENU** opens Stake `stateUi.menuOpen` drawer, not `SkyJumpMainMenu`. `/dev-preview` forces `screen = 'play'`, so the SkyJump menu is unused on the QA route. Menu exists and works when `localDemo` is false (loader → menu).
- `createBonusSnapshot` will replay `skyjumpResult` catch-up if that event is already in “before”, flashing the overlay on resume-after-overlay.
- `wincap` is not in `BOOK_EVENT_TYPES_TO_RESERVE_FOR_SNAPSHOT`.
- Farmer `reveal` handler + `enhancedBoard` still live in `stateGame` / `bookEventHandlerMap`. Unmounted, but a stray `reveal` event would try to spin a Garden board.
- `typesEmitterEvent.ts` still imports `Board.svelte` / `Win.svelte` types.
- Combined hill + multiplier is possible in `getTablesForBetMode` / `tables_for_mode` overrides. RGS `mode` is a single string (`stateBet.activeBetModeKey`). Production cannot send two profiles without a new composite mode.
- Simulator percentile is nearest-rank (`floor((n-1)*p)`), not interpolated. Counts/hit rates are otherwise consistent with the resolver.
- Overlay count-up brake uses `Math.random()` (presentation only).
- `dump-config.ts` hardcodes `bookAmountMultiplier: 100` while reading tables back from the JSON import (circular, safe if unused).
- Architecture / skill docs still say production books are farmer 5×3.

# P3 cleanup

- Unused `SkyJumpRoleIcons.svelte` after icons moved into Pixi cells
- Garden nudge maps in `stateGame.svelte.ts` (theme-gated, inactive)
- Farmer source components kept in-tree (intentional)
- Placeholder RTP `0.97` in configs vs ~117% simulator
- Vite missing `loader.gif` warnings (pre-existing SDK)
- `stateMeta.maxWin` default `8888` unused by SkyJump
- Audio is demo sprite names; keys exist in `sound.ts`
- ComfyUI offline
- `RoleIcons` CSS leftover
- `check_repeat` still knows `force_freegame`
- `SKYJUMP_IMPLEMENTATION_STATUS.md` / `AGENTS.md` skill paragraph about farmer books is stale

# Git / workspace findings

- Current branch: `feat/skyjump-game` (HEAD valid: `281b11d` before this audit’s uncommitted fixes).
- **There is no local `main` branch.** `git rev-parse main` fails.
- **`origin/main` is a dangling pointer** (`6e2c43b0ae8fcb88c8e0acb0904ee800f24b2831` — object missing).
- **No remotes configured** (`git remote -v` empty). This is not a complete clone; it is a surviving feature-branch worktree.
- `git fsck` also reports broken refs: `claude/*`, `docs/stake-com-readiness`, `feat/garden-reskin`, `feat/hand-drawn-assets`, stash.
- `feat/skyjump-game` history is linear and logical (audit → math → assets → UI → config JSON → book writer → UX → status).
- `frontend/pnpm-lock.yaml` is tracked and was not deleted.
- `node_modules`, `build/`, `.svelte-kit` are not in `git ls-files`.
- **Do not checkout / reset `main` here.** It does not exist as a valid object. Repair belongs in a dedicated git-recovery task (re-clone from a known-good remote, or fetch objects). This audit did not rewrite history.

# Build reproducibility

- This machine: `pnpm@10.5.0` frozen lockfile previously restored workspace packages; `pixi-svelte/dist` is now present.
- `npm run build` in `frontend/apps/poc` **passes** (prerender `/` and `/dev-preview`).
- Vite aliases + relative `config-vite` / `config-svelte` imports mean the app can start even if `node_modules/<workspace pkg>` is an empty OneDrive folder.
- **Clean checkout on a healthy OS would work with standard `pnpm install` from `frontend/`**, because packages have `main`/`exports` and `dist` (or source) after install.
- The aliases are **not proven required** on a clean Linux CI agent. They are a defensive overlay. Treat as **tech debt**, not as the intended Stake package graph.
- `cacheDir: tmpdir()/slot-game-poc-vite-cache` avoids OneDrive locking; fine locally, slightly non-standard for CI.

# Stake / RGS findings

- Authenticate / play / end-round still go through `rgs-requests` when `requestLocalDemoBet()` returns `null`.
- `gameID` remains `0_0_poc` in JSON, Python `GameConfig`, and `frontend/.../config.ts`.
- Changing `gameID` later requires: math folder rename, `GameConfig.game_id`, frontend `config.ts`, ACP credentials, published books path `math/games/<id>/library`. Do not invent an ID now.
- `checkIsBonusGame` is still “multiple `reveal` events”. SkyJump books have none, so rounds settle as single-round / no-win. Buy bonus is a **mode**, not a free-spin feature. That matches the architecture note and is correct **if** Stake accepts buy modes without `reveal`.
- Production must never set `stateUi.config.localDemo` on a public host.

# Book writer findings

`math/games/0_0_poc/gamestate.py` `run_spin`:

- Does **not** call farmer `draw_board`.
- Loads tables via `tables_for_mode(betmode)`.
- Emits custom `skyjumpWeather` / `skyjumpSlots` / `skyjumpResult`.
- Skips custom `setWin` / `wincap` / `setTotalWin` / `finalWin` and uses SDK `wincap_event` / `set_win_event` / `set_total_event` / `evaluate_finalwin`.
- Seeds via `random.seed(sim+1)` in `reset_seed`; `reset_book()` sets `repeat = False`, so the while-loop is **not** infinite.
- Zero win: no `setWin`, still `setTotalWin` + `finalWin` (amount 0).
- Cap: `round_result.capped` → `wincap_event`; hill cap and mode `max_win` currently align.
- Modes `base`, `large_hill`, `ski_flying`, `mult_10_100`, `mult_20_200` exist.
- Smoke (seed 7): same weather draw, different hill/mult and payouts (`base` 0, `large_hill` 30, `ski_flying` 80). Buy profile changes math.

Foundation: **yes**, with the P1 metadata/rounding caveats. Not a certified book library.

# Math findings

Formula matches the architecture:

`distance = hill.base + weather.distanceDelta + sum(slots)`  
`baseWinX = band lookup [min, max)`  
`local = product(slots 1–5)`  
`finalWinX = min(base * local * slot6, hill.maxWin)`

Edge checks added: 147.9 miss, 148 hit 0.2x, 156 → 0.5x. Cap fixtures still 500.

TS `roundTo` uses `Math.round`; Python `js_round` uses `floor(x+0.5)` for non-negative — aligned for settle. Book **integer amounts** are a separate split (P1).

Weather temperature / wind / visibility are rolled from ranges and **do not** enter distance; only `weather.id` → `distanceDelta` + `volatilityBias` does. Presentation fields are still in the book (good for replay).

# Canonical config findings

**Canonical for tables:** `math/games/0_0_poc/skyjump_config.json`

TS: `import rawConfig from '.../skyjump_config.json'`.  
Python: `CONFIG = load_config()`.

Still **not** canonical:

| Data | Extra copies |
| --- | --- |
| Volatility bias math | `resolveRound.ts`, `skyjump_resolve.py` |
| Buy cost / max win | `config.ts`, `Game.svelte`, `game_config.py` |
| `bookAmountMultiplier` | JSON + dump-config literal `100` + `constants-shared/bet.ts` `BOOK_AMOUNT_MULTIPLIER = 100` |
| Timings | `config.ts` `TIMING_PROFILES` (OK — not math) |
| Garden paytable | `config.ts`, `game_config.py` |

`dump-config.ts` reads back through the TS JSON import; it is not a second table source unless someone edits it to embed tables again.

# Money / rounding findings

Stake convention in this repo:

- API: `API_AMOUNT_MULTIPLIER = 1_000_000`
- Books: `BOOK_AMOUNT_MULTIPLIER = 100` (100 = 1× bet)
- HUD: `bookEventAmountToNormalisedAmount` = `wageredBetAmount * (amount / 100)`

SkyJump settle uses IEEE floats then `roundTo(4)` for `finalWinX` and `roundTo(2)` for `moneyWin`. Overlay **does not** display `moneyWin`; it displays `amount` via the Stake helper. That is the correct wallet model.

`localDemo` always resolves `bet: 1` then credits `stateBet.betAmount * payoutMultiplier`. Consistent with 1-credit books.

P1 remains: JS half-up vs Python bankers on `* 100` for amounts like `112.5`.

# Event contract findings

Order (localDemo TS books):

1. `skyjumpWeather` (weatherId + weather object + winnerId)
2. `skyjumpSlots` (slots 1–5, slot6 finalMultiplier, hillProfile, multiplierProfile)
3. `skyjumpResult` (distance, baseWinX, localFactors, finalWinX, moneyWin, amount, isCapped, slots)
4. `wincap` **or** `setWin` (if win)
5. `setTotalWin`
6. `finalWin`

Production Python books skip 4–6 from `round_to_book_events` and let the SDK append them. Overlay must not assume `setWin` is present (zero wins). `isCapped` / `hillProfile` / `multiplierProfile` are on the custom events.

No event schema version field. Replay is deterministic **if** the book is the source (payload-complete). Frontend does not re-resolve.

# Resume / replay findings

`convertTorResumableBet` splits by **event index**, snapshots weather/slots/result/setTotalWin, then plays remaining events.

| Interrupt | Book reality | Resume |
| --- | --- | --- |
| After weather | index ≥ 1 | snapshot weather catch-up; play slots→end |
| After slot 2 / 3 / 5 | still inside event index 1 | cannot represent; full slots replay or full catch-up |
| After slot 6 | index ≥ 2 | snapshot includes slots; overlay next |
| During overlay | index 2 in progress | replay overlay from book |
| After setTotalWin | snapshot includes setTotalWin | display win again; RGS should not re-pay if already settled |

No client RNG on resume. Double payout from replaying `setTotalWin` is display-only if RGS already closed the round. `resumeCatchUp` is cleared on `finalWin`.

# XState / timing findings

XState actor is still the round owner (`onPlayGame` → `playBet` → sequential `playBookEvents`). SkyJump animation is **not** in the machine: it is Promise/`waitForTimeout`/`requestAnimationFrame` in Svelte handlers.

That is implicit sequencing. Turbo flips `stateBet.isTurbo` and is read at handler start (`activeTimings()`). Changing turbo mid-round only affects later waits.

Generation guards added so reset/new round cancels in-flight overlay/weather/reel writes.

# Turbo findings

Same handlers, shorter `TIMING_PROFILES.turbo`. Verified earlier: overlay ~570 ms vs ~3680 ms normal.

Race: overlay HTML can appear before Pixi flushes slot 6. Event await order is correct; paint is not. Mitigation: ≥32 ms after slot 6 reveal.

# Autoplay findings

Actor path: `onNewGameStart` resets board + `lastWeather`, then `playBet` (awaited). Next autoplay spin should not start until overlay + `finalWin` complete.

Not re-tested as a long autoplay session in this audit. Dev-preview **Action** is not autoplay and can be clicked while a round is running (Story harness “your game will get stuck”).

# UI / responsive findings

From the previous implementation pass (re-checked against code, not a new pixel pass):

- Desktop landscape: 6 labeled cells, gold slot 6, HUD clear, overlay as a card over the in-run.
- Portrait HUD (~480): strip stays one row; HUD stacks. Overlay is `position: fixed` to the **browser viewport**, so it is correct on a real 480×900 device and wrong if the game is letterboxed inside a larger desktop window.
- Role vs rolled value: role icon + `SPEED`…`MULT` on the cell; distance / `xN` is the roll.

# Legacy Farmer dependencies

**SAFE DEAD CODE** (in tree, not mounted on SkyJump play): `Board.svelte`, `Win.svelte`, `GardenPayTable.svelte`, `GardenGameRules.svelte`, most garden symbol/free-spin components.

**ACTIVE LEGACY DEPENDENCY** (runtime, intended): `rgs-requests`, `utils-xstate`, HUD `components-ui-pixi`, HTML modals, demo `sounds.json`, `Authenticate`, amount helpers, autoplay/turbo flags.

**DANGEROUS LEGACY DEPENDENCY** (wired, should not receive SkyJump books): `bookEventHandlerMap.reveal` → `enhancedBoard.spin`; `stateGame.board` 5×3 farmer reels; `frontend/apps/poc/src/game/config.ts` garden paytable; Python `GameConfig` lines engine; `test_config_parity_poc.py`.

# Security / trust boundary

| Surface | Client can change? | Production safe? |
| --- | --- | --- |
| Bet amount / mode | Yes, sent to RGS | Server must validate mode + cost |
| Hill / multiplier | Only via mode key | Server books from mode |
| Round result | localDemo only | Must be book-only |
| `localDemo` | `/dev-preview` sets it | Now hostname-gated |

Client cannot make production RGS accept a homemade `finalMultiplier` unless RGS is misconfigured to use the localDemo override.

# Tests executed

| Command | Result |
| --- | --- |
| `node --experimental-strip-types tools/skyjump/test-math.ts` | pass (fixtures match Python) |
| `python math/games/0_0_poc/test_skyjump_resolve.py` | 7 tests OK |
| `npm run build` in `frontend/apps/poc` | pass |
| `math/tests/test_config_parity_poc.py` | **not a valid SkyJump test** (Garden) |
| ComfyUI `127.0.0.1:8188` | timeout / offline |
| Long autoplay in browser | not re-run this audit |
| `git diff main...HEAD` | **impossible** (no `main`) |

# Fixes applied during audit

Small, in-place only (uncommitted unless committed later):

- Overlay / weather / reel **generation tokens** so a reset cannot finish the previous round’s timers
- Overlay **cap banner** only in payout phase
- **≥32 ms** after slot 6 before overlay (turbo paint race)
- `localDemo` request overrides **refuse non-localhost** hosts
- Tests for payout band edges and documented JS vs Python `round` behavior

# Recommended next implementation pass

1. Git recovery: obtain a known-good remote, restore `main` objects, do **not** rewrite `feat/skyjump-game`.
2. Strip or replace Garden `config.ts` / `GameConfig` metadata for Stake publish; one source for buy cost + maxWin.
3. Align book integer rounding (pick banker's SDK **or** half-up, both runtimes).
4. Exclude or auth-gate `/dev-preview` from production adapter.
5. Optional: split `skyjumpSlots` into per-slot events **or** document catch-up-only resume as the contract.
6. Remove `reveal` handler from SkyJump runtime map (keep file in tree).
7. Update skill / architecture docs (books are SkyJump now).
8. Then — and only then — RTP tuning and Comfy plates.
