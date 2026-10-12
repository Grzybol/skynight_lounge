# SkyJump math / economics audit

Pre-certification developer audit of **mathVersion 1**. Not a published PAR
and not a Stake certification claim. Tables were not changed.

| Field | Value |
| --- | --- |
| Branch | `feat/skyjump-game` |
| Canonical config (at audit) | `math/games/0_0_poc/skyjump_config.json` |
| Frozen snapshot | `math/games/0_0_poc/skyjump_config.mathVersion1.json` |
| mathVersion | 1 |
| eventSchemaVersion | 1 |
| config SHA-256 | `709378e7f8790b03eb5354193a6800fd5ee2b8a4f140a4788612195cc6002042` |
| Enumerator | exact, weather × slots 1–5 × slot 6 |
| Monte Carlo | 1 000 000 rounds / mode, seed `7` |
| Reproduce | `node --experimental-strip-types tools/skyjump/mathAudit.ts --rounds=1000000 --seed=7` |

Raw JSON: `tools/skyjump/math-audit.json` (generated, not source).

---

## Executive summary

RTP semantics are **correct**. Book amount `100` is **1× nominal bet**, not
1× actual mode wager. RTP = `E[finalWinX] / costMultiplier` matches Stake
play, BetMode.cost, book amounts, and frontend cash conversion.

The exact enumerator is **correct**. Probability mass is 1.000000 for every
published mode (IEEE remainder ≤ 1.6e-14). It includes weather, biased slots
1–5, independent slot 6, payout curve, local product, final multiplier, and
mode `maxWin`.

mathVersion 1 is internally consistent and should be **kept as the audited
snapshot**. It should not be silently retuned. It does **not** yet match the
stated gameplay intent on weather, hill differentiation, or local frequency.

Headline diagnosis:

1. Weather is a **main determinant**, not a flavor modifier. After the weather
   reveal, BASE conditional RTP spans **0.44 (storm) to 1.59 (lift)**.
2. BASE / LARGE / FLYING look different in metres and cost, but
   **wager-normalized volatility is almost the same**. Flying even has a
   slightly **lower** coefficient of variation than BASE.
3. Distance is the pay/no-pay gate. Shapley gives it ~63% of BASE EV, but the
   **curve alone is only 0.300 of 0.968**. Multipliers supply most of the
   dollars above a miss.
4. Any local multiplier lands in **35.6% of BASE rounds** and **54.6% of
   paying rounds**. That is ordinary, not rare spice.
5. Slot 6 is independent of distance, so **~69% of x10 / x20 / x50 reveals
   pay zero**. Same miss rate as the rest of the game.
6. Premium buys can show `FINAL MULTIPLIER x20` and `FINAL WIN` while returning
   less than the 11× / 22× debit. About **13 pp** of premium rounds are a
   presented win and an economic loss.

No P0 implementation bug. P1 items are design / economics.

---

## RTP semantics

Independent re-trace, not copied from the previous math report.

### What Stake actually charges

1. Frontend `requestBet` sends `amount: stateBet.betAmount` (nominal) and
   `mode: activeBetModeKey`.
2. `rgs-requests` multiplies that amount by `API_AMOUNT_MULTIPLIER` (1e6).
3. Python `BetMode.cost` is canonical `costMultiplier`.
4. Stake RGS debit is play-amount × mode cost.

```
actualWager = nominalBet × costMultiplier
```

### What the book stores

5. `roundToBookEvents` writes `amount = roundBookAmount(finalWinX)`.
6. `BOOK_AMOUNT_MULTIPLIER = 100`. Comments and conversion in
   `utils-shared/amount.ts`: on a $1 bet, book `100` is $1.
7. `setWin` / `wincap` / `setTotalWin` / `finalWin` all use that book amount.
8. After play, `stateBet.wageredBetAmount = stateBet.betAmount` (nominal,
   **not** × cost).
9. Frontend cash = `wageredBetAmount × (bookAmount / 100)`.

Therefore:

```
bookAmount 100  =  1× NOMINAL BET
                ≠  1× ACTUAL MODE WAGER
```

Example: $1 nominal, MULT_20_200 cost 22. RGS debit = $22. Book `100` credits
$1. A 20× final multiplier on a 1.00× distance band is book `2000` = $20,
which is still a $2 loss versus the $22 debit.

### RTP formula

math-sdk lookup RTP is `E[payout_multiplier] / bet_mode.get_cost()`.

SkyJump uses the same:

```
RTP = E[finalWinX] / costMultiplier
    = E[payout cash] / actualWager
```

`localDemo` matches: debit `betAmount * costMultiplier`, credit
`betAmount * payoutMultiplier`.

**Confirmed. Not a P0. Leave as-is.**

HUD `betCost()` only multiplies Stake `type === 'activate'` ante modes.
SkyJump buys are `type === 'buy'`, so the on-screen bet chip can show the
nominal amount while RGS charges the mode cost. That is a UX mismatch, not an
RTP-definition bug. See P2.

---

## Exact enumerator validation

`tools/skyjump/exactEv.ts` and `tools/skyjump/mathAudit.ts` walk the same
settlement as `resolveRound`:

| Input | Included? |
| --- | --- |
| Weather probability | yes, from table weights |
| Slot 1–5 probability | yes, 5 symbols each |
| Weather + hill volatility bias | yes, `applyVolatilityBias` then renormalise |
| Slot 6 probability | yes, independent of weather (matches runtime) |
| Payout curve | yes, `lookupPayout` |
| Local product | yes, `Π max(1, localMultiplier)` |
| Final multiplier | yes |
| Mode `maxWin` | yes, not hill default when mode overrides |
| Flavor temperature / wind / visibility | ignored; they do not settle |

Combinations with mass: 112 500 (standard table) to 131 250 (6 weather × 5⁵
× 7 finals).

| Mode | Total probability | Raw EV (nominal) | Capped EV (nominal) | Cap drag (nominal) |
| --- | ---: | ---: | ---: | ---: |
| BASE | 1.000000 | 0.9731 | 0.9678 | 0.0053 |
| LARGE_HILL | 1.000000 | 2.9128 | 2.8996 | 0.0132 |
| SKI_FLYING | 1.000000 | 5.8201 | 5.8125 | 0.0075 |
| MULT_10_100 | 1.000000 | 10.9645 | 10.6886 | 0.2759 |
| MULT_20_200 | 1.000000 | 21.9564 | 21.3633 | 0.5931 |

Mass remainder is floating-point noise, not missing outcomes.

---

## Mode economics

RTP is exact. Expected loss is versus **actual wager**.

| Mode | Cost | Exact RTP | vs 0.97 | Expected loss | E[payout] / wager | Avg wager units |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BASE | 1 | 0.9678 | −0.22 pp | 3.22% | 0.9678 | 1 |
| LARGE_HILL | 3 | 0.9665 | −0.35 pp | 3.35% | 0.9665 | 3 |
| SKI_FLYING | 6 | 0.9688 | −0.12 pp | 3.12% | 0.9688 | 6 |
| MULT_10_100 | 11 | 0.9717 | +0.17 pp | 2.83% | 0.9717 | 11 |
| MULT_20_200 | 22 | 0.9711 | +0.11 pp | 2.89% | 0.9711 | 22 |

Target 97% implies ~3% expected loss. All five modes sit in 2.83–3.35%.

### RTP precision (no retune)

Do **not** describe BASE / LARGE as 0.2–0.4 pp below the 0.968 lower bound.
That sentence in `SKYJUMP_MATH_REPORT.md` was wrong and is corrected there.

| Mode | Exact RTP | Gap to 0.968 | Gap to 0.97 |
| --- | ---: | ---: | ---: |
| BASE | 0.9678 | **−0.02 pp** | −0.22 pp |
| LARGE_HILL | 0.9665 | **−0.15 pp** | −0.35 pp |
| SKI_FLYING | 0.9688 | +0.08 pp | −0.12 pp |
| MULT_10_100 | 0.9717 | inside 0.968–0.972 | +0.17 pp |
| MULT_20_200 | 0.9711 | inside 0.968–0.972 | +0.11 pp |

They do **not** need identical RTP. ±0.2 pp across modes is a reasonable
intentional band for different volatility. LARGE is the outlier (−0.15 pp
versus 0.968, −0.35 pp versus 0.97). That is a P2 nudge, not a bug.

---

## Weather influence

BASE exact, payouts versus actual wager (cost 1).

| Weather | P | Cond. RTP / EV | Hit | Zero | p50 | p90 | p99 | Avg m | P(>10x) | P(>50x) | Share of total EV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| headwindLift | 16% | **1.592** | 43.1% | 56.9% | 0 | 3.54 | 23.63 | 123.4 | 3.22% | 0.22% | **26.3%** |
| lightFavorableWind | 24% | **1.300** | 38.8% | 61.2% | 0 | 3.54 | 17.72 | 121.7 | 2.54% | 0.17% | **32.2%** |
| sunny | 22% | 0.882 | 31.1% | 68.9% | 0 | 1.77 | 13.00 | 117.9 | 1.54% | 0.10% | 20.0% |
| crosswind | 14% | 0.588 | 21.1% | 78.9% | 0 | 1.48 | 8.86 | 112.8 | 0.99% | 0.07% | 8.5% |
| snow | 18% | 0.548 | 20.8% | 79.2% | 0 | 1.11 | 7.38 | 112.9 | 0.90% | 0.06% | 10.2% |
| storm | 6% | **0.435** | 16.2% | 83.8% | 0 | 0.74 | 7.09 | 109.8 | 0.72% | 0.05% | 2.7% |

RTP contribution = `P(weather) × E[payout | weather]`. Good weather (lift +
favorable = 40% of rounds) produces **58.6% of EV**. Bad weather (snow +
cross + storm = 38% of rounds) produces **21.4% of EV**.

Mechanism: BASE miss band starts at 128 m. Typical distance is ~118 m.
Weather deltas (−9 … +6) move the jumper across that cliff. Storm average
109.8 m is ~18 m below pay. Lift average 123.4 m is only ~4.6 m below pay.
Hit rate therefore jumps from 16% to 43%.

**Verdict:** weather is currently a **main determinant**, not a flavor
modifier. After the reveal the player can already tell good-round from
bad-round in expectation (~3.7× EV spread, ~2.7× hit-rate spread).

Proposed mathVersion 2 deltas / bias (not applied):

| Weather | Current Δ | Current bias | Proposed Δ | Proposed bias |
| --- | ---: | ---: | ---: | ---: |
| sunny | +2 | 0.00 | +1 | 0.00 |
| lightFavorableWind | +5 | 0.08 | +2 | 0.04 |
| headwindLift | +6 | 0.16 | +3 | 0.08 |
| snow | −4 | 0.10 | −2 | 0.05 |
| crosswind | −5 | 0.20 | −2.5 | 0.10 |
| storm | −9 | 0.30 | −4 | 0.15 |

Target after retune: conditional RTP inside roughly **0.80–1.15**, hit-rate
spread inside ~8–10 pp, weather still visible on the metre tape.

---

## Distance contribution

BASE exact, capped settlement unless noted.

Naive subsets (locals and/or final forced to 1):

| Counterfactual | E[nominal] | Share of full 0.968 |
| --- | ---: | ---: |
| Distance only (L=1, F=1) `vD` | 0.300 | 31.0% |
| Distance × locals, F=1 `vDL` | 0.685 | 70.8% |
| Distance × final, L=1 `vDF` | 0.426 | 44.1% |
| Full capped `vDLF` | 0.968 | 100% |
| Uncapped | 0.973 | — |

Simple subtraction is misleading because D, L, and F multiply.

Shapley on `{D, L, F}` (average over the two incremental orders, third
component dummy is 0 without distance):

| Component | Shapley EV | Share of capped EV |
| --- | ---: | ---: |
| Distance | 0.608 | **62.8%** |
| Local product | 0.245 | 25.3% |
| Final multiplier | 0.115 | 11.9% |
| 3-way interaction leftover in subsets | 0.156 | (already allocated) |

Incremental orders:

| Order | Distance | Then locals | Then final |
| --- | ---: | ---: | ---: |
| D → L → F | 0.300 | +0.385 | +0.282 |
| D → F → L | 0.300 | +0.126 (final first) | +0.541 (locals last) |

How to read this without lying:

- Distance **is** the foundation: without a paying band, multipliers pay 0.
  Shapley therefore gives it the majority.
- Distance is **also** a steep gate. The curve alone only returns 0.30×.
  About **69% of the EV dollars** appear only after multipliers attach.
- Locals added first look larger than finals; finals added first look small
  because standard table is 82% x1.

**Verdict:** not “multipliers are the whole game”, but also not “distance
carries the payout”. Intent (“distance is the payout, locals/final are
spice”) is only half-true. mathVersion 2 should raise `vD` (more EV in the
curve, slightly fewer stacked tails) if that intent is kept.

Same Shapley pattern on hills (~62 / 26 / 12). Premium modes invert it:
MULT_10_100 **43 / 19 / 38**, MULT_20_200 **42 / 19 / 40** — slot 6 becomes
a co-equal EV engine because the floor is 10× / 20×.

---

## Local multiplier influence

BASE exact.

| Count of local events | Probability |
| --- | ---: |
| none | 64.44% |
| one | 29.62% |
| two | 5.42% |
| three+ | 0.52% |
| **any local** | **35.56%** |

| Filter | Probability |
| --- | ---: |
| P(local \| paying round) | **54.57%** |
| P(local \| zero round) | 27.13% |
| P(product ≥ 4) | 5.94% |
| P(product ≥ 6) | 1.08% |
| P(product ≥ 10) | 0.095% |

Previous report bucket `x4–x5` used `local < 5.5`, which **includes isolated
x3**. Exact P(product ≥ 4) is 5.94%, not 6.5% + 0.99%.

Per slot (BASE):

| Slot | P(this slot has a local) | EV removed if that local is forced to 1 | P(slot in a product ≥ 6) |
| --- | ---: | ---: | ---: |
| SPEED | 6.72% | 0.103 | 0.40% |
| TAKEOFF | 6.67% | 0.146 | 0.40% |
| FLIGHT | 8.80% | 0.196 | 0.49% |
| WIND | 8.84% | 0.125 | 0.49% |
| LANDING | **11.00%** | 0.144 | 0.93% |

Landing is the most common local. Flight contributes the most local EV.
Shapley local share is 25% of BASE EV.

**Verdict:** locals are too common versus “noticeable event, not ordinary”.
One in three rounds, and **one in two paying rounds**, shows a local. If
intent stays “spice”, mathVersion 2 should target ~15–20% of rounds (and
~25–30% of paying rounds), mainly by cutting landing / wind local weights.

Do not change weights in this audit.

---

## Final multiplier influence

Standard table (BASE / LARGE / FLYING). Slot 6 is **independent of
distance**, so P(zero | high final) = overall miss rate.

| Mult | P | P(and pay) | P(and zero) | P(zero \| this mult) |
| --- | ---: | ---: | ---: | ---: |
| x1 | 82.00% | 25.19% | 56.81% | 69.3% |
| x2 | 10.50% | 3.23% | 7.27% | 69.3% |
| x3 | 4.40% | 1.35% | 3.05% | 69.3% |
| x5 | 2.00% | 0.61% | 1.39% | 69.3% |
| x10 | 0.80% | 0.25% | 0.55% | 69.3% |
| x20 | 0.24% | 0.074% | 0.166% | 69.3% |
| x50 | 0.06% | 0.018% | 0.042% | 69.3% |

BASE:

| Event | Probability |
| --- | ---: |
| P(x10+) | 1.10% |
| P(x10+ AND win) | 0.34% |
| P(x10+ AND zero) | **0.76%** |
| P(x20+ AND win) | 0.092% |
| P(x20+ AND zero) | 0.208% |
| P(x50 AND win) | 0.018% |
| P(x50 AND zero) | 0.042% |

E[slot 6] = **1.42**. Shapley share of BASE EV = **11.9%**.

**Verdict:** high-final-on-miss is not a rare glitch. It is **the default
outcome** of an independent slot 6 (~69% of those reveals). Suspense is
real; “wow x50 → €0” will happen about **two of every three x50s**.
mathVersion 2 can keep independence (honest math) and tone the overlay, or
add a mild anti-whiff coupling. Do not hide it by retuning RTP.

Premium tables: every round is x10+ or x20+, so 69.3% of those floors still
pay zero. See premium section.

---

## Premium multiplier UX economics

Returns are **payout / actual wager**. Exact.

### MULT_10_100 — cost 11, literal floor x10

| Outcome vs 11× debit | Probability |
| --- | ---: |
| Loss (return < 1) | **81.85%** |
| Return < 0.25× | 69.28% (≈ all zeros) |
| Return < 0.50× | 73.53% |
| Return < 1× | 81.85% |
| Return ≥ 1× | 18.15% |
| Return ≥ 2× | 10.63% |
| Return ≥ 5× | 4.33% |
| Return ≥ 10× | 1.82% |
| Return ≥ 50× | 0.13% |

First two paying distance bands × x10 are **3.69× and 8.86× nominal**, both
below the 11× debit. The overlay can show `FINAL MULTIPLIER x10` and a
positive `FINAL WIN` while the player is still down versus the buy.

### MULT_20_200 — cost 22, literal floor x20

| Outcome vs 22× debit | Probability |
| --- | ---: |
| Loss (return < 1) | **82.60%** |
| Return < 0.25× | 69.28% |
| Return < 0.50× | 74.82% |
| Return < 1× | 82.60% |
| Return ≥ 1× | 17.40% |
| Return ≥ 2× | 10.67% |
| Return ≥ 5× | 4.44% |
| Return ≥ 10× | 1.88% |
| Return ≥ 50× | 0.14% |

First two paying bands × x20 are **7.38× and 17.72× nominal**, both below
22. `FINAL MULTIPLIER x20` is therefore often a losing buy.

Mathematically this is consistent with 97% RTP on a 22× stake. UX-wise it is
easy to read as “I hit x20 and still lost most of the buy”.

Do not force-change costs or floors in this audit. Flag as P1 design.

Normalized max win on both premium modes is **90.91× actual wager**
(1000/11 and 2000/22). Tail >100× actual wager is **impossible**.

---

## Hill differentiation

Exact wager-normalized payout (finalWinX / cost).

| | BASE (cost 1) | LARGE (cost 3) | FLYING (cost 6) |
| --- | ---: | ---: | ---: |
| Variance | 28.92 | 26.77 | 24.46 |
| Std dev | 5.38 | 5.17 | 4.95 |
| CV | **5.56** | **5.35** | **5.11** |
| p90 | 1.77 | 1.91 | 2.29 |
| p95 | 3.54 | 3.28 | 3.36 |
| p99 | 14.18 | 13.10 | 13.73 |
| p99.9 | 59.07 | 58.24 | 54.91 |
| p99.99 | 194.9 | 191.1 | 164.7 |
| Max theoretical before cap | 18 904 | 45 861 | 65 887 |
| P(>10× wager) | 1.81% | 1.68% | 1.68% |
| P(>50×) | 0.120% | 0.163% | 0.117% |
| P(>100×) | 0.035% | 0.041% | 0.029% |
| P(>250×) | 0.0067% | 0.0082% | 0.0057% |
| P(>500×) | 0 (capped at 500) | 0 (capped at 500) | 0.0012% |

What actually changes: base distance (82 / 104 / 132), cost (1 / 3 / 6),
nominal maxWin (500 / 1500 / 5000), pay-hit (30.7 / 33.2 / 35.4%).

What barely changes: the distribution **after dividing by the price**.
Flying is slightly **less** volatile (lower CV, thinner p99.9) than BASE.
p90 is the only percentile that clearly climbs with hill size.

**DESIGN ISSUE.** Bigger Hill is currently a more expensive ticket to a
similar normalized game, plus bigger metre numbers. Intent (LARGE = fatter
tail, FLYING = most aggressive) is not delivered.

---

## Max-win normalization

| Mode | Nominal maxWin | Cost | maxWin / actual wager |
| --- | ---: | ---: | ---: |
| BASE | 500 | 1 | **500×** |
| LARGE_HILL | 1500 | 3 | **500×** |
| SKI_FLYING | 5000 | 6 | **833×** |
| MULT_10_100 | 1000 | 11 | **90.9×** |
| MULT_20_200 | 2000 | 22 | **90.9×** |

BASE and LARGE share the same cap versus money in. Flying’s extra headroom
almost never hits (cap frequency 0.00021%). Premium caps are much tighter
versus the buy price; they clip the stacked tail and cannot pay 100× the
debit.

Caps were not changed.

---

## Cap analysis

Cap is mode `maxWin`. Overshoot = uncapped − maxWin, conditional on a clip.

| Mode | Cap frequency | Uncapped EV | Capped EV | EV removed | Drag / raw | Avg overshoot | p99 overshoot | Max raw |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BASE | 0.00139% | 0.9731 | 0.9678 | 0.0053 | 0.55% | 382 | 2336 | 18 904 |
| LARGE_HILL | 0.00192% | 2.9128 | 2.8996 | 0.0132 | 0.45% | 686 | 6144 | 45 861 |
| SKI_FLYING | 0.00021% | 5.8201 | 5.8125 | 0.0075 | 0.13% | 3589 | 19 708 | 65 887 |
| MULT_10_100 | 0.0382% | 10.9645 | 10.6886 | 0.2759 | 2.52% | 722 | 4199 | 37 808 |
| MULT_20_200 | 0.0418% | 21.9564 | 21.3633 | 0.5931 | 2.70% | 1418 | 8397 | 75 615 |

Hills: safety rail. Rare, large clips, small RTP impact.

Premium: still not the RTP engine, but no longer negligible (~2.5–2.7% of
raw EV). Frequency ~1 in 2 400–2 600 rounds.

---

## Slot-role distributions

BASE (weather-mixture, exact). Distance EV contribution ≈ share of expected
metres (the curve is non-linear, so this is a distance-role split, not a
payout split).

| Slot | Mean m | SD | Min | Max | P(neg) | P(local) | p10 | p50 | p90 | Metre share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SPEED | 10.03 | 4.18 | 5 | 18 | 0 | 6.7% | 5 | 11 | 15 | 28.7% |
| TAKEOFF | 6.88 | 7.68 | −8 | 20 | 9.8% | 6.7% | 1 | 9 | 16 | 19.7% |
| FLIGHT | 12.49 | 10.75 | −12 | 28 | 7.8% | 8.8% | 2 | 12 | 22 | **35.7%** |
| WIND | 3.44 | 9.43 | −14 | 14 | **33.2%** | 8.8% | −14 | 6 | 14 | 9.8% |
| LANDING | 2.12 | 5.22 | −8 | 8 | 17.3% | **11.0%** | −8 | 2 | 6 | 6.1% |

Roles **do** differ mathematically, not only by name: SPEED is tight and
never negative; WIND is the fault slot; FLIGHT is the metre engine; LANDING
is a small-metre / high-local closer.

Hill bias lifts means slightly (FLYING SPEED 10.27, FLIGHT 13.2-class) and
raises local rates. The role identities stay the same.

---

## Pay-hit / breakeven / profit rates

Definitions used here:

- **Pay hit:** `finalWinX > 0` (any credit)
- **Breakeven:** `finalWinX ≥ costMultiplier` (cash ≥ actual wager)
- **Profit:** `finalWinX > costMultiplier`

Exact. `P(finalWinX === cost)` is 0 on these tables, so breakeven = profit.

| Mode | Zero | Pay hit | Breakeven | Profit |
| --- | ---: | ---: | ---: | ---: |
| BASE | 69.28% | **30.72%** | **15.82%** | 15.82% |
| LARGE_HILL | 66.79% | 33.21% | 17.39% | 17.39% |
| SKI_FLYING | 64.63% | 35.37% | 18.76% | 18.76% |
| MULT_10_100 | 69.28% | 30.72% | 18.15% | 18.15% |
| MULT_20_200 | 69.28% | 30.72% | 17.40% | 17.40% |

The previously quoted “~31% hit rate” is **pay hit**, not recovery of the
stake. About **half of paying BASE rounds still lose versus the 1× bet**
(partial bands 0.37× and 0.89×). On premium, pay hit stays 30.7% while
recovery of the 11× / 22× debit is 18% / 17%.

---

## Monte Carlo confidence

1M rounds, seed 7. SE from the Monte Carlo sample. Exact RTP is inside every
95% CI. Differences are sampling, not a simulator bug.

| Mode | Exact | MC | Diff | SE | 95% CI | Exact in CI? |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| BASE | 0.9678 | 0.9647 | +0.0031 | 0.0053 | 0.9544–0.9750 | yes |
| LARGE_HILL | 0.9665 | 0.9637 | +0.0028 | 0.0051 | 0.9538–0.9736 | yes |
| SKI_FLYING | 0.9688 | 0.9650 | +0.0037 | 0.0047 | 0.9558–0.9743 | yes |
| MULT_10_100 | 0.9717 | 0.9719 | −0.0002 | 0.0039 | 0.9642–0.9796 | yes |
| MULT_20_200 | 0.9711 | 0.9712 | −0.0001 | 0.0040 | 0.9634–0.9790 | yes |

Exact variance implies BASE SE(mean) ≈ 5.38 / √1e6 ≈ 0.0054 on wager units,
matching the MC SE. 1M is too thin to quote p99.9 from samples
(MATH_REPORT BASE MC p99.9 53.2 versus exact 59.07). Use exact percentiles.

---

## Report inconsistencies

Found in `SKYJUMP_MATH_REPORT.md` and corrected there:

1. **Wrong pp language.** “BASE / LARGE sit 0.2–0.4 pp under the 0.968–0.972
   window” — BASE is 0.02 pp below 0.968, LARGE 0.15 pp. Not 0.2–0.4 pp
   below the lower bound.
2. **Hit rate unlabeled.** The 30.7% column is pay-hit (`finalWinX > 0`),
   not breakeven.
3. **Local product buckets.** Simulator label `x4–x5` includes isolated x3
   (`local < 5.5`).
4. **Percentiles presented as if exact.** They were 1M Monte Carlo. Extreme
   tail (p99.9) is noisy. This audit uses exact percentiles.
5. **Local / final tables** were Monte Carlo; they happen to match exact
   count frequencies to ~0.1 pp, but product-bucket labels did not.

No unit mix-up of book-100 versus mode wager in the RTP column of the old
report. The formula itself was already correct.

---

## P0 math issues

None.

RTP semantics hold. Enumerator mass is 1. Settlement matches `resolveRound`.
Monte Carlo agrees with exact inside CI.

---

## P1 math/design issues

1. **Weather is too strong.** Conditional BASE RTP 0.44–1.59. After reveal
   the player largely knows if the round is good. Intent: modifier, not
   determinant.
2. **Hills are not distinct versus actual wager.** CV 5.56 / 5.35 / 5.11.
   Flying is slightly tamer, not more aggressive. Intent: LARGE fatter tail,
   FLYING most aggressive.
3. **Locals are too common.** 35.6% of rounds, 54.6% of paying rounds.
   Intent: noticeable spice.
4. **Distance curve carries only 0.30×;** multipliers attach the rest of the
   dollars. Intent: distance is the payout foundation in *magnitude*, not
   only as a gate.
5. **Independent slot 6 × miss band** → 69% of x10+ reveals pay zero.
   Acceptable as honest math, bad as unexplained UX.
6. **Premium overlay economics.** Literal x10 / x20 floors often return less
   than the 11× / 22× debit while UI still says WIN.
7. **WIN / you-won / winLevel keyed off nominal `finalWinX`**, not versus
   actual wager. See next section. Do not change UI in this task.

---

## P2 observations

1. LARGE RTP 0.9665 is 0.15 pp below 0.968. Fine to leave, or a tiny v2
   nudge if we want every mode inside 0.968–0.972.
2. Premium cap drag ~2.5–2.7% of raw EV. Still a rail, slightly more than
   hills.
3. BASE / LARGE normalized maxWin are identical (500× wager). Flying 833×
   almost never binds.
4. HUD `betCost()` ignores buy-mode cost. Chip can show 1× while RGS takes
   22×.
5. `winLevelFor` fires BIG WIN at 50× **nominal**. On MULT_20_200 that is
   ~2.3× the debit.
6. Overlay SFX `sfx_youwon_panel` when `finalWinX >= 10` nominal. On
   MULT_20_200, 10× nominal is still a loss versus 22×.
7. Exact P(payout === cost) = 0, so “breakeven” never means a push.

---

## Recommended mathVersion 2 changes

Do **not** implement in this task. Freeze mathVersion 1 as the audited
baseline.

1. **Weather:** cut deltas and volatilityBias by about half (table above).
   Re-check that lift/storm conditional RTP sit near 1.15 / 0.80, not
   1.59 / 0.44. Keep six identities.
2. **Hills:** stop scaling cost, metres, and curve together so that
   payout/wager stays the same. Give LARGE a fatter upper curve / slightly
   higher P(>50× wager). Give FLYING a genuinely heavier tail and a
   normalized cap that can actually hit. Accept that p90–p99.9 versus wager
   should *separate*, even if RTP stays ~0.97.
3. **Distance EV:** lift `vD` toward ~0.45–0.55 by paying a bit more in the
   first two bands and a bit less in stacked multiplier tails. Distance
   should remain the gate **and** a larger share of the dollars.
4. **Locals:** reduce any-local frequency to ~15–20% of rounds. Cut LANDING
   local weight first. Keep product ≥10 as a rare stack, not a common
   double-x2.
5. **Slot 6:** keep the standard table shape (mostly x1). Either keep
   independence and fix copy (“multiplier applies only if the jump pays”),
   or add a light miss-dampener so x20/x50 are rarer on zero bands.
6. **Premium:** keep literal floors and costs unless UX research says
   otherwise. If kept, overlay must not celebrate x20 as a mode win when
   cash < debit. Optional later: show payout versus buy cost.
7. **RTP window:** keep target 0.97 vs actual wager. Allow ±0.20 pp across
   modes on purpose. Only nudge LARGE if we want every mode ≥ 0.968.
8. **Caps:** keep rare. If hills are retuned for fatter tails, re-measure
   cap drag; do not use the cap as the RTP knob.

mathVersion 2 is a new JSON revision plus enumerator re-run. Event contract
stays at schemaVersion 1.
