# SkyJump architecture

Working title: **SkyJump**. Frozen canonical `meta.altTitle` still says
SkiFly Jackpot (metadata debt; not player-facing; no jackpot mechanic).
Theme: premium winter ski-jump casino mini-game for Stake Engine. Not a 5×3 slot.

## Decision

Transform `frontend/apps/poc` in place on `feat/skyjump-game`. Reuse Stake
platform (authenticate, play, end-round, XState, HUD, turbo, autoplay, modals).
Replace garden presentation and round generation.

```
GAME CONFIG     src/game/skyjump/config.ts
MATH            src/game/skyjump/resolveRound.ts   (pure, seeded)
ROUND → BOOK    src/game/skyjump/toBookEvents.ts
GAME STATE      existing XState actor + stateGame.screen / skyjump UI state
PLATFORM        rgs-requests + actor localDemo override
UI              Pixi HUD + SkyJump Pixi strip/background + HTML overlays
ANIMATIONS      bookEventHandlerMap timings (normal / turbo)
ASSETS          assets/skyjump/* registered in assets.ts
AUDIO           demo sprite map (placeholder)
WEATHER         config-driven draw + overlay
BONUS           betModeMeta buy cards → hill / multiplier tables
RESULT          HTML overlay card, never a fullscreen win route
```

## Screens

| Screen | How |
| --- | --- |
| BOOT | Existing loading screen |
| MAIN_MENU | `stateGame.screen = 'menu'`, HUD hidden (`uiHide`) |
| IDLE gameplay | `screen = 'play'`, HUD shown, 6 slots idle |
| WEATHER_DRAW | `skyjumpWeather` book event |
| REEL_1..6 | `skyjumpSlot` book events, sequential reveal in the handler |
| RESULT overlay | `skyjumpResult` then existing `setTotalWin` / `finalWin` |
| Back to IDLE | actor `endGame` |

Turbo is **not** a second state machine. `getSkyJumpTimings()` reads `stateBet.isTurbo`.

## Round formula (tunable, not certified)

```
weather = weightedRoll(weatherTable)
slots[1..5] = weightedRoll(slotTables[i], weather.volatilityBias)
finalMultiplier = weightedRoll(activeMultiplierTable)
distance = hill.baseDistance + weather.distanceDelta + sum(slot.distanceValue)
baseWinX = payoutCurve(distance)          // NOT cash-per-metre
localMultiplier = product(slot.localMultiplier)   // default 1
finalWinX = min(baseWinX * localMultiplier * finalMultiplier, hill.maxWin)
money = bet * finalWinX
```

Hit / miss is whatever the payout curve assigns (including 0). Impossible values
are clamped (distance ≥ 0, local multipliers ≥ 1, slot 6 may display x0 on a
distance miss, winX ≥ 0, max-win cap).

## Book contract (Stake-compatible)

A SkyJump book is still `Bet.state: BookEvent[]`:

1. `skyjumpWeather`
2. `skyjumpSlots` (all six outcomes; client reveals 1→6)
3. `skyjumpResult` (overlay payload)
4. `setWin` (amount + winLevel; **no fullscreen Win.svelte**)
5. `setTotalWin`
6. `finalWin`
7. optional `wincap`

`checkIsBonusGame` stays “multiple reveal events”. SkyJump uses a single round,
so settlement uses `noWin` / `singleRoundWin`. Buy-bonus only changes **tables**
for that round (hill and/or final-multiplier range), not a free-spin feature.

## Buy bonus (independent options)

| Mode key | Type | Effect | Cost × bet (placeholder) |
| --- | --- | --- | --- |
| `BASE` | default | Normal hill + standard multipliers | 1 |
| `LARGE_HILL` | buy | Large hill | 3 |
| `SKI_FLYING` | buy | Ski flying hill | 8 |
| `MULT_10_100` | buy | Final multiplier table 10–100 | 4 |
| `MULT_20_200` | buy | Final multiplier table 20–200 | 10 |

Costs and tables are **gameplay placeholders**, not certified math.

## ComfyUI

Existing pipeline: local `http://127.0.0.1:8188`, Qwen Image Edit + BiRefNet,
scripts under `tools/comfy`. SkyJump needs T2I-style plates; if the API is down,
authored SVG/PNG placeholders ship with a manifest and TODO for later generation.

## Production math-sdk

`math/games/0_0_poc` lines engine is **not** replaced in this stage. A Python
mirror of the resolver + simulator lives beside it for later book generation.
Real-money play still requires published books + ACP credentials (external).
