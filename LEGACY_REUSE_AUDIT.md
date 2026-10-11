# Legacy reuse audit — Farmer / Garden Bounty → SkyJump

Baseline: Stake Engine `frontend/apps/poc` (Garden Bounty / farmer theme) on the
working tree copied into this repository. Git objects for the previous remote
history were not present locally; `feat/skyjump-game` is the implementation
branch. `main` is left without new commits.

This is **not** a second game beside FarmerGame. SkyJump replaces the themed
presentation and round math inside the existing POC app, and keeps the Stake
platform stack.

## Platform findings (do not rewrite)

Stake RGS is already wired:

| Step | Path | Protocol |
| --- | --- | --- |
| Authenticate | `frontend/packages/components-shared/.../Authenticate.svelte` | `POST /wallet/authenticate` |
| Play | `frontend/packages/rgs-requests/src/rgs-requests.ts` | `POST /wallet/play` |
| End round | same | `POST /wallet/end-round` |
| Event ack | same | `POST /bet/event` |
| Replay | same | replay endpoint |
| Session | `state-shared` URL-derived `sessionID` + `rgsUrl` | query params |
| Local QA | `frontend/apps/poc/src/game/localDemo.ts` + `actor.ts` overrides | `/dev-preview` only |

The frontend is presentation-only: RGS returns a **book** (`round.state` events).
`playBet` runs `playBookEvents`. Balance uses `API_AMOUNT_MULTIPLIER`. Book cash
uses `BOOK_AMOUNT_MULTIPLIER` (100 = 1× bet).

XState (`utils-xstate` + `actor.ts`) owns:

- boot / idle / betting / autoplay
- turbo (`stateBet.isTurbo`, `timeScale`)
- buy-bonus mode key
- resume of an active round
- error modal
- end-round settlement (`noWin` / `singleRoundWin` / `bonusWin`)

SkyJump **must not** replace this actor with a parallel wallet or spin loop.

## Game loop today

1. `Authenticate` hydrates balance, bet levels, jurisdiction, optional active round.
2. Pixi `App` loads `src/game/assets.ts`.
3. Loading screen → `gameActor.start()` + `RENDERED`.
4. Idle: HUD (`components-ui-pixi`) Spin / Auto / Turbo / Bet / Buy Bonus.
5. `BET` → `onNewGameStart` (5×3 prespin) → `requestBet` (or local demo) → `playBet`.
6. Book handlers animate `reveal` → optional `winInfo` / `setWin` (fullscreen win) → `setTotalWin` → `finalWin`.
7. Next spin or `end-round` depending on bet type.

Local `/dev-preview` sets `stateUi.config.localDemo = true` and **must never** be
treated as production RTP.

## Module catalogue

### REUSE AS-IS

| Path | Responsibility | Farmer usage | SkyJump usage | Risk |
| --- | --- | --- | --- | --- |
| `frontend/packages/rgs-requests` | Wallet authenticate / play / end-round / replay | Live RGS | Same | Low — do not change |
| `frontend/packages/utils-xstate` | Primary + autoplay machines | Spin lifecycle | Same; SkyJump is still one book per round | Low |
| `frontend/packages/state-shared` `stateBet` | Balance, bet, turbo, autoplay, mode | HUD + actor | Same | Low |
| `frontend/packages/components-ui-pixi` | HUD: spin, bet +/-, auto, turbo, buy bonus, settings | Garden HUD | Keep; hide on main menu via `uiHide` | Low |
| `frontend/packages/components-ui-html` modals | Settings, autoplay, buy bonus, errors | HTML overlays | Keep; swap paytable/rules snippets | Low |
| `frontend/packages/components-shared` Authenticate / i18n / hotkeys | Bootstrap | Same | Same | Low |
| `frontend/packages/utils-book` | Sequential book playback | `playBet` | Same, new event types | Low |
| `frontend/apps/poc/src/game/actor.ts` | Wires machines to this game | Prespin + localDemo override | Keep override; drop 5×3 prespin | Medium if prespin left on |
| `frontend/apps/poc/src/routes/+layout.svelte` | RGS vs `/dev-preview` | Auth wrapper | Same | Low |
| Demo audio `static/assets/audio` | Howler sprite map | Garden/miner SFX | Reuse as placeholder SFX | Legal: commercial rights unresolved |

### REUSE WITH MODIFICATION

| Path | Responsibility | Farmer usage | SkyJump usage | Risk |
| --- | --- | --- | --- | --- |
| `src/game/bookEventHandlerMap.ts` | Book → animation | 5×3 reveal, FS, fullscreen win | Weather, sequential 6 slots, result overlay; `setWin` no longer fullscreen | Medium — keep `setTotalWin` / `finalWin` / `wincap` |
| `src/game/typesBookEvent.ts` | Book typings | Lines events | Add `skyjumpWeather`, `skyjumpSlots`, `skyjumpResult` | Low |
| `src/game/localDemo.ts` | QA book generator | Fake 5×3 + FS | Call SkyJump resolver, emit SkyJump books | Medium — still demo-only |
| `src/game/config.ts` | FE gameID / bet modes / RTP label | 5×3 lines + bonus 100× | Rename + hill/mult buy modes; keep `gameID: 0_0_poc` | Medium vs future math-sdk sync |
| `src/components/Game.svelte` | Scene composition | Garden board + FS + Win | Menu + ski in-run + reel strip + overlay | Medium |
| `src/game/assets.ts` | Asset registry | Garden bg / atlas | SkyJump sprites + keep audio | Low |
| `src/game/stateGame.svelte.ts` | Board + layout | 5 spinning reels | Keep unused board object; add `screen` + skyjump UI state | Low |
| `packages/state-shared` theme union | `garden` / `miner` | Garden CSS | Add `skyjump`, do not delete others | Low |
| `packages/components-ui-html/global.scss` | Modal / button theme | Garden greens | Additive `theme-skyjump` winter palette | Low |
| Buy-bonus `stateMeta.betModeMeta` | BONUS 100× FS | Modal cards | Hill tier + multiplier-table buys | Low |

### REWRITE (themed presentation only)

| Path | Responsibility | Farmer usage | SkyJump usage | Risk |
| --- | --- | --- | --- | --- |
| `src/components/Board.svelte` + reel stack | 5×3 slot board | Core view | Replaced by horizontal 6-slot strip | High if left mounted |
| `src/components/Win.svelte` | Fullscreen win + big-win spines | `setWin` | Result overlay card on gameplay | High if still triggered |
| `src/components/Background.svelte` + GardenAmbience | Garden backdrop | Visual | Menu / in-run ski jump backgrounds | Low |
| `GardenPayTable.svelte` / `GardenGameRules.svelte` | Info | Garden paytable | SkyJump rules / slots / weather | Low |
| `LoaderArtwork.svelte` | Loader copy | Garden bounty | SkyJump branding | Low |
| `/dev-preview` scenarios | QA books | FS / big win / garden tokens | Weather, sequential reveal, overlay, turbo, buys | Low |

### REMOVE / DEPRECATE (do not delete files yet unless unused at runtime)

Garden-only runtime mounts (FS intro/outro, cluster board, garden tokens, 5×3
board) are **unmounted** on this branch. Source stays in-tree so the farmer
baseline remains recoverable. Do not delete `math/games/0_0_poc` lines engine
until a production SkyJump book pipeline exists.

### NEW SYSTEM REQUIRED

| System | Why |
| --- | --- |
| Data-driven round resolver | Farmer math is 5×3 lines + free spins. SkyJump is weather + 5 role slots + final multiplier + payout curve. |
| Weather draw UI + config | No farmer equivalent. Must be data-driven, not hardcoded in components. |
| Sequential 6-slot reveal | Not `utils-slots` simultaneous stop. |
| Result overlay count-up | Replaces fullscreen `Win.svelte`. |
| Hill + multiplier buy tables | Replaces 100× free-spin buy. |
| Production math-sdk books | `gamestate.py` still generates lines books. A future 0_0_poc SkyJump book writer is required before real-money RGS. |
| Certified RTP | Local resolver + simulator are **engine foundation only**. |

## Math / fairness

Farmer production math lives in `math/games/0_0_poc` (Python math-sdk). It is
server-authoritative **once books are published to RGS**. The local demo adapter
is a client sampler and is explicitly QA-only.

SkyJump stage-1 math is a **pure, testable resolver** used by localDemo to build
books. It does not talk to the wallet. Settlement still goes through existing
`requestBet` / `requestEndRound` (or their demo overrides).

Do not invent a second RNG/wallet. When production books exist, the same book
event contract is what RGS will send; the client already plays books.

## Critical non-blockers vs blockers

Non-blockers (placeholders OK): final title, ComfyUI art, certified RTP, audio
reskin, 5×5 board (not requested).

Blockers we will not cross: rewriting `rgs-requests`, replacing XState, claiming
`/dev-preview` RTP, deleting farmer math-sdk, force-pushing `main`.
