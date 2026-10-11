# SkyJump developer math report

**Active tables are mathVersion 3.** See `SKYJUMP_MATH_V2_REFINEMENT.md`.

mathVersion 2: `SKYJUMP_MATH_V2_REPORT.md` /
`math/games/0_0_poc/skyjump_config.mathVersion2.json`.

This file is the frozen **mathVersion 1** developer report. Config snapshot:
`math/games/0_0_poc/skyjump_config.mathVersion1.json`. Economics audit:
`SKYJUMP_MATH_AUDIT.md`.

Pre-certification developer math. Not a published PAR.

| Field | Value |
| --- | --- |
| mathVersion | 1 |
| eventSchemaVersion | 1 |
| config | `math/games/0_0_poc/skyjump_config.json` (frozen: `skyjump_config.mathVersion1.json`) |
| config SHA-256 | `709378e7f8790b03eb5354193a6800fd5ee2b8a4f140a4788612195cc6002042` |
| exact enumerator | 112 500–131 250 combinations / mode |
| Monte Carlo | 1 000 000 rounds / mode, seed `7` |
| target RTP | 0.97 vs actual wager = nominal bet × costMultiplier |

Reproduce:

```
node --experimental-strip-types tools/skyjump/mathAudit.ts --rounds=1000000 --seed=7
```

RTP in the mode table is the **exact** enumerator. Prefer exact percentiles
from `tools/skyjump/mathAudit.ts`. Older 1M Monte Carlo tails (especially
p99.9) are noisier; BASE MC p99.9 was 53.2 versus exact 59.07.

Economics audit: `SKYJUMP_MATH_AUDIT.md`.

## Mode summary

HIT = pay-hit (`finalWinX > 0`), **not** breakeven vs actual wager. Exact
breakeven (`finalWinX ≥ cost`) is 15.8% BASE / 17.4% LARGE / 18.8% FLYING /
18.2% MULT_10 / 17.4% MULT_20.

| MODE | COST | TARGET | EXACT RTP | MC RTP | PAY HIT | ZERO | AVG WIN ON HIT (nominal) | MAX WIN | EXACT CAP | P50 | P90 | P99 | P99.9 | VOL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE | 1 | 0.97 | 0.9678 | 0.9647 | 30.72% | 69.28% | 3.15 | 500 | 0.0014% | 0 | 1.77 | 14.18 | 59.07 | medium-high |
| LARGE_HILL | 3 | 0.97 | 0.9665 | 0.9637 | 33.21% | 66.79% | 8.73 | 1500 | 0.0019% | 0 | 1.91 | 13.10 | 58.24 | similar vs wager |
| SKI_FLYING | 6 | 0.97 | 0.9688 | 0.9650 | 35.37% | 64.63% | 16.43 | 5000 | 0.0002% | 0 | 2.29 | 13.73 | 54.91 | similar vs wager |
| MULT_10_100 | 11 | 0.97 | 0.9717 | 0.9719 | 30.72% | 69.28% | 34.79 | 1000 | 0.038% | 0 | 2.42 | 16.11 | 59.07 | literal 10–100 |
| MULT_20_200 | 22 | 0.97 | 0.9711 | 0.9712 | 30.72% | 69.28% | 69.54 | 2000 | 0.042% | 0 | 2.01 | 16.11 | 59.07 | literal 20–200 |

Percentiles are **exact payout / actual wager**. P50 is 0 because pay-hit is
~31%.

BASE is **0.02 pp** below 0.968. LARGE is **0.15 pp** below 0.968. FLYING and
both premium modes sit inside 0.968–0.972. Left as-is in mathVersion 1.

## EV breakdown (BASE, exact)

| Component | E[nominal] |
| --- | --- |
| Distance / payout curve only (locals=1, final=1) | 0.300 |
| Distance × local product, final=1 | 0.685 |
| Distance × final, locals=1 | 0.426 |
| Full capped | 0.968 |
| Uncapped | 0.973 |
| Cap drag | 0.005 |

Distance is the pay/no-pay gate. Shapley on BASE capped EV is distance 62.8% /
locals 25.3% / final 11.9%. The curve alone is still only 0.300 of 0.968 —
multipliers attach most of the dollars above a miss. Full economics:
`SKYJUMP_MATH_AUDIT.md`. Cap removes ~0.55% of raw BASE EV.

## Weather (BASE conditional E[finalWinX])

| Weather | EV |
| --- | --- |
| headwindLift | 1.59 |
| lightFavorableWind | 1.30 |
| sunny | 0.88 |
| crosswind | 0.59 |
| snow | 0.55 |
| storm | 0.44 |

Storm is the worst package, not a forced miss. Lift is the best package, not a
forced win. The EV spread (0.44–1.59) is still too large versus the “flavor
modifier” intent; see `SKYJUMP_MATH_AUDIT.md`.

## Local multipliers (BASE exact)

| Locals on the board | Share |
| --- | --- |
| none | 64.44% |
| one | 29.62% |
| two | 5.42% |
| three+ | 0.52% |

| Product | Share |
| --- | --- |
| none (product = 1) | 64.44% |
| any local | 35.56% |
| product ≥ 4 | 5.94% |
| product ≥ 6 | 1.08% |
| product ≥ 10 | 0.095% |

Do not use the simulator label `x4–x5` (`local < 5.5`): it includes isolated
x3. P(local | pay) = 54.6%. P(local | zero) = 27.1%.

## Final multiplier (BASE exact table weights)

| Mult | Share |
| --- | --- |
| x1 | 82.0% |
| x2 | 10.5% |
| x3 | 4.4% |
| x5 | 2.0% |
| x10 | 0.78% |
| x20 | 0.24% |
| x50 | 0.06% |

`plus` (10–100) starts at x10 (~55.6%). `max` (20–200) starts at x20 (~54.3%).

## Distance (BASE)

p10 93 · p25 106 · p50 118 · p75 131 · p90 141 · p99 155 (1M Monte Carlo).
First paying band starts at 128 m.

## Slot metres (exact expected distanceValue)

SPEED 10.0 · TAKEOFF 6.9 · FLIGHT 12.5 · WIND 3.4 · LANDING 2.1

## Top payout contributors

High results need a paying distance band × a local product × a high slot-6
value. Isolated locals on a miss still pay 0. Cap is a rare clip on those
stacked tails, especially on 10–100 / 20–200.

## Smoke books

`math/games/0_0_poc/library/smoke/` — 8 random books per published mode plus
fixture books (zero, small, local product, cap, flying miss). Event sequence is
weather → six `skyjumpSlot` → result → settlement.
