# SkyJump math design

Pre-certification developer math. This is not a published PAR and is not a
Stake certification claim.

`mathVersion: 3` is the active table revision. `mathVersion: 2` is frozen in
`math/games/0_0_poc/skyjump_config.mathVersion2.json` (`SKYJUMP_MATH_V2_REPORT.md`).
`mathVersion: 1` is frozen in `skyjump_config.mathVersion1.json` /
`SKYJUMP_MATH_AUDIT.md`. `eventSchemaVersion: 1` is unchanged.

Canonical source: `math/games/0_0_poc/skyjump_config.json`.

Current exact numbers: `SKYJUMP_MATH_V2_REFINEMENT.md`.

## RTP definition

Stake play sends **nominal** `betAmount` plus `mode` to `/wallet/play`.

RGS debit uses published `BetMode.cost`:

```
actualWager = betAmount × costMultiplier
```

Book `amount` is versus the **nominal** bet, not versus the debit:

```
bookAmount 100  →  1.0 × betAmount cash
frontend cash   →  wageredBetAmount × (bookAmount / 100)
wageredBetAmount is the nominal betAmount
```

HUD `betCost()` multiplies for Stake `type === 'activate'` **and** SkyJump
`type === 'buy'`, so TOTAL BET shows the real charge. `requestBet` still
sends nominal `betAmount`. Buy-bonus UI (`BonusCards`) shows
`betAmount * costMultiplier` as TOTAL BET. `localDemo` deducts that product.

```
RTP = E[finalWinX] / costMultiplier
    = E[payout cash] / actualWager
```

Do **not** divide by the nominal bet alone.

## Exact enumerator

Weather × 5 slot symbols × final multiplier is 112k–131k combinations per
mode. Volatility bias is applied per weather/hill, then combinations are
enumerated. Flavor RNG (temperature/wind/visibility) does not affect
settlement. Standard slot 6 uses the static miss table when `baseWinX == 0`.

```
node --experimental-strip-types tools/skyjump/mathAudit.ts --exact-only
node --experimental-strip-types tools/skyjump/test-math.ts
node --experimental-strip-types tools/skyjump/designGuards.ts
```

Developer guards warn (they do not change runtime odds) if RTP leaves
0.968–0.972, locals exceed ~20%, cap drag exceeds 1%, weather RTP spread is
large, or hill CV / p99.9 order is wrong.

## Design targets (mathVersion 3)

| Goal | Choice |
| --- | --- |
| Target RTP | 0.97 vs actual wager (window 0.968–0.972) |
| Feel | BASE medium-high; LARGE thicker tail; FLYING most aggressive |
| Distance | Foundation of payout; first BASE band at 116 m |
| Locals | ~15–20% of rounds; spice, not the RTP engine |
| Slot 6 | Mostly x1 on pay; static miss table without x20/x50 on zero |
| Weather | Modifier, not a round-quality oracle |
| Cap | Rare safety rail |
| Premium 10–100 / 20–200 | Literal floors; cost set after raw EV |

There is no runtime RTP correction, session balancing, or user-based weighting.

## Profiles

Hills (`normal` / `large` / `flying`) and multiplier tables (`standard` /
`plus` / `max`) stay independent. A mode only references `hillProfile` +
`multiplierProfile` + `costMultiplier` + `maxWin`. Hill curves are **not**
scaled copies of BASE.

Gameplay cap is **mode `maxWin`**. Hill `maxWin` is the default if a caller
omits the override.

## Costs

Set from exact E[finalWinX] / 0.97 after distributions were stable:

| Mode | costMultiplier | maxWin | max vs wager |
| --- | ---: | ---: | ---: |
| BASE | 1 | 500 | 500x |
| LARGE_HILL | 3 | 4000 | 1333x |
| SKI_FLYING | 6 | 25000 | 4167x |
| MULT_10_100 | 11.3 | 6000 | 531x |
| MULT_20_200 | 22.6 | 12000 | 531x |

mathVersion 1 costs were 1 / 3 / 6 / 11 / 22. Premium costs moved after the
distance curve lifted raw EV. Caps moved so premium drag is not the RTP
regulator.

## Slot character

| Slot | Role |
| --- | --- |
| SPEED | Tight metres, rare explosive/record x2 |
| TAKEOFF | Fault vs perfect; perfect x2 is uncommon |
| FLIGHT | Largest distance contribution |
| WIND | Variance; sweet-spot local is rare |
| LANDING | Style closer; perfect/style locals are rare |

## Slot 6 miss table

Standard paying rounds keep the full x1–x50 table. Standard **miss** rounds
use `finalMultiplierMissTables.standard` (no x20/x50). Plus/max tables stay
independent because their floors are the bought feature.

## Presentation economics

Settlement is unchanged (`finalWinX` → book amount). Overlay/SFX/winLevel
use actual wager:

```
returnMultiplier = finalWinX / costMultiplier
isPayHit = finalWinX > 0
isBreakEven = finalWinX >= costMultiplier
isProfit = finalWinX > costMultiplier
```

Buy-mode payout below cost is PAYOUT, not YOU WON / BIG WIN.
