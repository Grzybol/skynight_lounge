# SKYJUMP V2 — Phase 6A Rejump + Wind Key / Flight Multiplier

**Status:** RESEARCH / DESIGN ONLY. Not implemented in the live resolver.  
**Branch:** `feat/skyjump-v2-5x5`  
**Phase 5C:** approved. Live BASE and live Phase 5B Free Spins stay frozen.  
**Recommended candidate:** `P6A_F1_C_K1_W2_R1_PV1_B`  
**Ready for a human Phase 6B decision:** yes, with the feel tradeoff in section 12.

This pass does not add Rejump or Wind Key to paid BASE spins, does not retune BASE F01, does not change the live Free Spin reel models, U1, the initial 10 spins, the max-40 rule, or persistent-target max 2, and does not generate production books or LUTs.

---

## 1. Budget

| Piece | Value |
| --- | ---: |
| Certified BASE | 71.212% |
| Phase 5B Free Spin contribution | 17.92705 pp |
| Game before Phase 6 | 89.139% |
| Production target | 96.50% |
| Design budget before this phase | 7.361 pp |
| Phase 6 research band | 4.5–5.5 pp, center 5.0 pp |
| Reserve to keep | prefer ≥ 1.8 pp, do not go under ~1.5 pp |

The reserve is for `SPECIAL_WORLD_RECORD`, a later premium-symbol feel pass, and final cap / rounding. This phase does not design World Record.

Trigger probability used throughout: exact BASE `P(Scatter ≥ 3) = 0.00652967825443787`.  
Incremental pp = (bonus mean × − Phase 5B mean 27.45472×) × that probability × 100.  
`round_prior_win_x = 0` on every research bonus. The 50,000× cap is the shared round cap. Phase 6 does not get its own cap. Mean BASE win on the trigger (~0.71×) is negligible next to 50,000×, so prior = 0 matches the Phase 5B comparison.

A feature-off control of this research resolver (500,000 mix bonuses, seed `20260922`) landed at **27.809×**, which is **+0.231 pp** versus the certified 27.45472×. That gap is the resolver-plus-seed noise, not a feature. The headline increment below is versus the certified mean, which is the higher of the two readings and the one that leaves less reserve. The paired control reading is about **0.23 pp lower**. Both sit inside 4.5–5.5 pp.

---

## 2. Mechanic definitions

Both features exist only inside Free Spins. Mystery weights are one normalized table per current bonus tier. Weights sum to 1000. New mass is taken from `FLIGHT_TOKEN` only. Thermal 42, Gate 6, Judge 170, and Head Judge 30 stay at the live Phase 5B values.

### 2.1 Rejump

A Mystery that resolves to `REJUMP` queues one redrop. It is not an animation. After the redrop the board is paid once on the standard 28 lines and the same regular paytable. The original spin's lines are not paid again.

Preserved cells:

- Flight Tokens
- Thermal Lift
- Gate
- Judge and Head Judge
- Wind Key cells
- Coach cells that already resolved on this spin
- Scatter cells from the initial reveal

Ordinary regular pay symbols are removed and refilled. The refill is a math-owned reel window: one stop per reel, then the unlocked rows of that window. If the window symbol is Scatter, the draw is replaced from that reel's non-scatter multiset. A Scatter placement is a hard failure. Scatter evaluation and retriggers use only the initial reveal. Rejump does not add free spins and does not change `freeSpinsRemaining` or `totalFreeSpinsAwarded`.

After the new line pass:

1. `persistentMysteryTargets` convert matching regulars on the new cells.
2. Coaches that the refill just created resolve. Already-resolved coaches do not fire again. Perfect V does not inject another synthetic coach on the redrop.
3. New Mysteries resolve, including further Rejumps and Wind Keys.

Chains are allowed. `maxFeatureChainDepth = 8` stays the hard ceiling. The recommended practical limit is **2 Rejumps per Free Spin**. A queued Rejump past that limit, or past depth 8, resolves as an explicit terminal no-op. It does not pay and it does not loop.

### 2.2 Wind Key and Flight Multiplier

`WIND_KEY` upgrades the persistent flight multiplier by one step on one stage. Stages start at 1 / 1 / 1 when the economic round starts and reset only when the round ends. They persist across the remaining Free Spins and across Large Hill → Ski Flying → World Cup → Perfect V.

Global multiplier = `runUp × takeoff × flight`.

Recommended ladder **K1**: each stage is 1 → 2 → 3. Maximum product **27×**.

Stage choice is math-owned. Recommended rule **W2**: among stages that are not at the ladder maximum, choose uniformly among those with the current lowest value. Tie-break is the math RNG. The frontend does not pick the stage.

Under K1 + W2 the product path is 1 → 2 → 4 → 8 → 12 → 18 → 27. A global 3× does not occur, because the second key finishes a second stage at 2 before any stage reaches 3.

Saturation rule **B**: when all three stages are at the ladder maximum, `WIND_KEY` is removed from the eligible Mystery pool and the remaining weights are renormalized by their original integers. No consolation pay. Rule A (draw the key, then explicit no-op) was compared on the hot screen and did not change the decision at weights that almost never max the ladder.

The multiplier applies only to Judge and Head Judge collection passes, independently per pass:

`finalCollection = rawTokenCollection × globalFlightMultiplier`

It does not multiply paylines, Rejump lines, Scatter, stored token faces, Gate replacements, or Thermal multipliers. Tokens remain after collection. Head Judge is two passes of the same effective sum, then the flight multiplier.

### 2.3 Collectors wait for the chain

Gates and Wind Keys from the current Mystery batch apply before any Rejump in that batch. Collectors do not pay until the Rejump queue for that spin is finished. An early Judge therefore collects tokens created by a later redrop, and a key found anywhere in the same chain multiplies those collections. Thermal effective values are computed once, on the final board, immediately before that settlement.

---

## 3. Resolution order to lock in Phase 6B

Initial Free Spin reveal:

1. Board
2. Line wins
3. Scatter (only evaluation in the spin)
4. Persistent targets
5. Coach, including the existing Perfect V guaranteed coach on the initial board
6. Mystery identities

Feature chain, repeating while a Rejump remains inside the limit:

A. Gate upgrades from the current batch  
B. Wind Key stage upgrades from the current batch  
C. If a Rejump is still queued and the spin is under the practical limit and under depth 8: redrop, Rejump line win, persistent targets, new coaches, new Mysteries, return to A

Then, once:

D. Thermal effective token values on the final board  
E. Every Judge pass and every Head Judge double pass  
F. Multiply each of those passes by the global flight multiplier  
G. Settle the spin total into the shared round cap

---

## 4. State to add in Phase 6B

Serializable on the bonus snapshot, replayable, not wired in this phase:

| Field | Meaning |
| --- | --- |
| `flightMultiplier.runUp` | integer stage, start 1 |
| `flightMultiplier.takeoff` | integer stage, start 1 |
| `flightMultiplier.flight` | integer stage, start 1 |
| `windKeysCollected` | count of applied keys this round |
| `rejumpChainDepth` | depth used inside the current spin |
| `rejumpsThisSpin` | applied redrops this spin |
| `rejumpsThisBonus` | applied redrops this bonus |

A truncated Rejump is recorded as a no-op count, not as another redrop. The global product is derived from the three stages. It is not a separate source of truth.

Phase 5B already reserves `flightMultiplierRunUp / Takeoff / Flight` on the client snapshot. Phase 6A does not change that reducer.

---

## 5. Events to add in Phase 6B

Design only. No production handler is added here. Names match the existing V2 protocol family. The single `skyjumpRejump` sketch in `03_EVENT_PROTOCOL.md` should be split into four playback events so the redrop, the line pass, and the chain index are separate.

`skyjumpRejumpStart`

- `chainIndex`
- `preservedPositions`
- `redroppedPositions`

`skyjumpRejumpBoard`

- `chainIndex`
- `newBoard`

`skyjumpRejumpLineWins`

- `chainIndex`
- `lineWins`
- `lineWinX`

`skyjumpRejumpEnd`

- `chainIndex`
- `rejumpsThisSpin`
- `truncated`

`skyjumpWindKey`

- `position`
- `selectedStage`
- `oldStageValue`
- `newStageValue`
- `oldGlobalMultiplier`
- `newGlobalMultiplier`

`skyjumpFlightMultiplierUpdate`

- emitted when the product changes for a reason other than a cell key (Perfect V entry grant, or the round-end reset)
- `reason`, `stages`, `global`

Do not auto-pay a key. Do not emit a Wind Key event for a saturation-B removal; that outcome is simply absent from the draw.

---

## 6. Why moderate weights are not viable

The first screen put Rejump and Wind Key on the order of 3–15% of the Mystery table (models A, B, C, C_LO, C_HI). At 8,000 mix bonuses those packs added **tens to hundreds of percentage points**, not 5 pp.

| Screen pack | Large Hill Rejump / Wind | Incremental RTP | Cap frequency | Mean cap drag |
| --- | ---: | ---: | ---: | ---: |
| C | 48 / 12 | ~185 pp | 0.00088 | ~34× |
| C_LO | 28 / 6 | ~53 pp | 0.00013 | ~1.3× |
| C_HI | 70 / 22 | ~360 pp | 0.00263 | ~387× |
| C + K2 | 48 / 12 | ~195 pp | 0.00125 | ~42× |
| C + K3 | 48 / 12 | ~214 pp | 0.00213 | ~40× |

Rejump line wins in that screen were about 0.1× per bonus. Collector raw sums were about 40–90× and, after the flight multiplier, several hundred ×. The value is feature amplification: preserved tokens and collectors survive the redrop, the refill adds more of them, and a key multiplies the whole pile. K2 (max 64×) and K3 (max 125×) make that tail worse. They are rejected.

A second 40,000-bonus screen (seed 606) cut the weights to integers near the budget:

| Pack | LH Rejump / Wind | Incremental | Reserve | P(Rejump) | P(Wind) | Median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| G1 | 10 / 1 | 5.04 pp | 2.32 pp | 0.094 | 0.019 | 9.60× |
| G2 | 12 / 1 | 7.35 pp | 0.01 pp | 0.109 | 0.024 | 9.60× |
| G3 | 14 / 1 | 7.21 pp | 0.15 pp | 0.120 | 0.024 | 9.60× |
| G4 | 16 / 1 | 7.14 pp | 0.22 pp | 0.132 | 0.025 | 9.60× |
| G5 | 12 / 2 | 8.75 pp | −1.39 pp | 0.109 | 0.035 | 9.60× |
| G6 | 8 / 2 | 5.86 pp | 1.50 pp | 0.083 | 0.031 | 9.60× |
| G7 | 18 / 0 | 11.62 pp | −4.26 pp | 0.142 | 0.027 | 9.60× |
| G8 | 10 / 0 | 7.63 pp | −0.27 pp | 0.098 | 0.026 | 9.60× |

Only G1 was inside 4.5–5.5 pp with reserve above 1.8 pp. G6 sat on the 1.5 pp floor and had even less Rejump visibility. Raising Large Hill Rejump toward the 15% feel note (G4) spent the reserve. The 40,000-sample means still move by about 1 pp when a few 10,000× hits land, which is why the finalists below are 500,000 or 1,000,000 bonuses.

The median stayed 9.60× on every pack, including the hot screen (9.5–9.7×). That is the Phase 5B median. Phase 6 at a legal RTP does not move the typical bonus. It moves the mean through the right tail.

---

## 7. Rejump limit

At the recommended weight, measured on 1,000,000 mix bonuses:

| Limit | Id | Incremental | P(hit the practical limit) | Max chain seen | Extra vs max 2 |
| --- | --- | ---: | ---: | ---: | ---: |
| Max 2 per spin (R1) | F1 | 5.307 pp | 0.001579 | 2 | — |
| Max 3 per spin (R2) | F2 | 5.396 pp | 0.00022 | 3 | +0.089 pp |
| Depth 8 only (R3) | F3 | see finalist table |  |  |  |

R1 truncates about 1.6 bonuses in 1,000. R2 truncates about 1 in 4,500 and spends 0.09 pp to do it. Neither hits depth 8 in natural play at this weight. The hot C screen did hit depth 8 when the per-spin cap was removed, and those chains were part of the tail. R1 is the recommendation: the no-op is explicit, natural play almost never sees it, and the saved 0.09 pp stays in the World Record reserve.

P(2 or more Rejumps in the bonus) at F1 is 0.0257. P(3+) is 0.0099. P(5+) is 0.0016. Mean Rejumps per bonus is 0.139. Mean free spins stays 10.43. The max-40 rule is unchanged.

---

## 8. Wind ladder, stage rule, saturation, Perfect V

K1 is the recommendation. On the hot screen, K2 and K3 raised cap drag without changing how often a key appears. At F1's wind rate the ladder rarely leaves the first step (mean global multiplier **1.025**, median **1**, max observed **27**). A taller ladder only matters on the bonuses that already have a fat collector pile. That is the state the forced table in section 11 shows can reach the cap.

W2 is the recommendation. It is deterministic given the math RNG and it keeps the three stages level, so the product reads as 2×, then 4×, then 8×. W1 (any non-max stage) can produce a 3× by upgrading the same stage twice. On the hot screen W1 did not reduce the tail. F4 in the finalist table is the same G1 weight with W1, at 500,000 bonuses.

Saturation B is the recommendation. With mean keys per bonus of 0.022, a maxed ladder is a few bonuses per hundred thousand. Removing the key from the pool and renormalizing is auditable: each remaining result keeps its integer weight, and the draw total becomes `1000 − windWeight`. No pay is added. Saturation A was within noise of B on the hot screen.

Perfect V treatments PV2 (one granted key on the first Perfect V spin, no cell) and PV3 (one forced key cell on that spin if the initial batch has none) do not move the mix. Phase 5B reached Perfect V on **0.060%** of bonuses. Direct Perfect V triggers are about 3×10⁻⁷ of bonuses. The 8,000-bonus hot screen could not tell PV1, PV2, and PV3 apart. Dedicated Perfect V batches for F1 are in section 12. The recommendation is **PV1**: higher natural weight only (32 / 1000 on Perfect V). Perfect V already has a guaranteed coach. A scripted key on every Perfect V spin was not needed to make the tier's table stronger, and it was not simulated because the brief allows it only after the other treatments fail. They do not fail the mix budget; they fail to matter.

---

## 9. Finalists

All use K1 unless noted, saturation B, PV1, and the shared 50,000× cap. Seed `20260922`. Mix draws use the exact BASE trigger weights. F1 and F2 are 1,000,000 bonuses. The others are 500,000.

Common Mystery body, live Phase 5B values, not retuned: Thermal 42, Gate 6, Judge 170, Head Judge 30.

**F1–F5 weight (model C), per 1000:**

| Tier | Flight Token | Rejump | Wind Key |
| --- | ---: | ---: | ---: |
| Large Hill | 741 | 10 | 1 |
| Ski Flying | 731 | 18 | 3 |
| World Cup | 722 | 24 | 6 |
| Perfect V | 710 | 32 | 10 |

**F6 weight (model B), same total feature mass, Large Hill wind moved up:**

| Tier | Flight Token | Rejump | Wind Key |
| --- | ---: | ---: | ---: |
| Large Hill | 741 | 11 | 0 |
| Ski Flying | 730 | 18 | 4 |
| World Cup | 721 | 24 | 7 |
| Perfect V | 709 | 32 | 11 |

| Id | What changed | n | Inc. pp | Reserve pp | New game | P(Rejump) | P(Wind) | Mean mult | P(trunc) | P(cap) | Mean events |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **F1** | C, K1, W2, max 2 | 1,000,000 | **5.307** | **2.054** | **94.446%** | 0.0963 | 0.0194 | 1.025 | 0.00158 | 1.5e-5 | 102.4 |
| F2 | max 3 | 1,000,000 | 5.396 | 1.964 | 94.535% | 0.0963 | 0.0194 | 1.025 | 0.00022 | 1.4e-5 | 102.4 |
| F3 | max 8 only | 500,000 | 5.280 | 2.081 | 94.419% | 0.0965 | 0.0195 | 1.025 | 0 | 1.6e-5 | 102.4 |
| F4 | W1 stage rule | 500,000 | 5.077 | 2.284 | 94.216% | 0.0965 | 0.0195 | 1.025 | 0.00152 | 1.6e-5 | 102.4 |
| F5 | K2 ladder | 500,000 | 5.208 | 2.153 | 94.347% | 0.0965 | 0.0195 | 1.026 | 0.00152 | 1.6e-5 | 102.4 |
| F6 | model B, no LH wind | 500,000 | 5.813 | 1.548 | 94.952% | 0.1008 | 0.0184 | 1.024 | 0.00159 | 1.6e-5 | 102.4 |

F4 keeps the most reserve inside the band and sits closest to the 5.0 pp center. It is the reserve-max runner-up. F1 is still the recommendation because W2 was the preferred stage rule and it was certified at 1,000,000 on the top candidate line. F6 spends reserve for a small mix bump and removes the Large Hill Wind Key demo. F5 does not beat F1 on reserve or tail safety at this wind rate.

F1 and F2 share the seed, so their Rejump and Wind rates match. The only difference is the third redrop.

Rank for F1, ahead of a pure RTP match:

1. 5.307 pp is inside 4.5–5.5 and is the closest large-sample reading to 5.0 pp among the in-band packs.
2. Reserve 2.05 pp stays above 1.8 pp. F2's extra 0.09 pp is legal but spends reserve on a chain that 0.16% of bonuses were going to lose anyway.
3. Large Hill does see the system, at the low end of what the budget can afford. See section 12. Forcing the 15–35% / 5–20% notes requires the G4/G5 region, which leaves under 1.5 pp or goes negative.
4. W2 + K1 is a short readable ladder (2 / 4 / 8, then 12 / 18 / 27).
5. Cap frequency stays on the same order as the feature-off control.
6. The forced tail in section 11 is real and is already capped at 50,000×. It is rare at this wind rate.
7. Chain truncation is 0.16%.
8. Book growth versus the feature-off control is about one event per bonus.
9. Median stays 9.6×. Every legal pack does this. It is not a reason to pick a hotter pack.
10. Tier weights still rise from Large Hill to Perfect V. Model B (F6) removes the Large Hill key entirely, so common bonuses never show the multiplier.

---

## 10. Counterfactual decomposition

Seed `20260922`. All F1 rows are 1,000,000 triggered mix bonuses. `:wind_key` disables Wind Key and leaves Rejump. `:rejump` disables Rejump and leaves Wind Key.

| Mode | Mean | Incremental vs 27.45472× | Median | P90 | P99 | Cap frequency | Mean spins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Phase 5B certified | 27.455× | 0 | 9.6× | 43.8× | 294.5× | 0.000006 | 10.433 |
| Feature-off research control | 27.809× | +0.231 pp | 9.60× | 43.8× | 294.5× | 0.000016 | 10.431 |
| F1 Rejump only (Wind off) | 32.084× | +3.023 pp | 9.60× | 45.5× | 386.5× | 0.000014 | 10.431 |
| F1 Wind only (Rejump off) | 30.515× | +1.998 pp | 9.60× | 44.5× | 341.3× | 0.000014 | 10.431 |
| F1 full | 35.582× | +5.307 pp | 9.60× | 46.0× | 448.0× | 0.000015 | 10.431 |

Interaction = full − Rejump-only − Wind-only = **+0.286 pp**. At this weight **Rejump is the larger standalone incremental contributor** (3.023 pp vs Wind-only 1.998 pp). Wind Key still matters because a key multiplies collector sums on Mystery-heavy bonuses that already had judges; that selection effect shows up in the multiplier bins below, but it is not a larger standalone counterfactual than Rejump. Rejump's mass is almost all feature amplification, not paylines.

Rejump value is not the extra paylines.

| Piece | RTP |
| --- | ---: |
| Rejump line wins (full F1) | 0.020 pp |
| Rejump feature amplification (Rejump-only path, lines ≈ 0) | 3.023 pp |
| Wind / multiplier with Rejump disabled | 1.998 pp |
| Rejump × Wind interaction | 0.286 pp |

Amplification is additional tokens, judges, head judges, gates, and thermals that survive on a locked board and get collected after the chain. Line wins are blocked by those same locked cells. Mean Rejump line win per bonus at F1 is **0.030×** against a mean initial line win of **6.05×**.

Board saturation at F1, share of bonuses whose fullest spin exceeded the lock fraction:

| Lock | Probability |
| --- | ---: |
| > 25% of cells | 0.0672 |
| > 50% | 0.0306 |
| > 75% | 0.0065 |

Above 75% is uncommon and is reported rather than cleaned up. Earlier specials stay on the board.

---

## 11. Flight-multiplier bins and forced tails

F1, 1,000,000 bonuses. "Mean raw" is the collector sum before the flight multiplier, averaged over bonuses that **ended** at that global product. Bonuses that reach 2× and above are a selected set: they had enough Mysteries to draw a key, so their raw collector sum is already much larger than a 1× bonus. The multiplier then scales that selected pile. This is the T6 × multiplier pathology in ordinary clothing. Most of the mass is T3–T5 plus several collector passes, not T6.

| Ending product | Share of bonuses | Mean collector raw | Mean collector paid | Collector RTP |
| --- | ---: | ---: | ---: | ---: |
| 1× | 0.980598 | 22.43× | 22.43× | 14.363 pp |
| 2× | 0.017488 | 210.26× | 334.71× | 3.822 pp |
| 3× | 0 | — | — | 0 |
| 4–5× | 0.001630 | 517.03× | 1,187.1× | 1.263 pp |
| 6–8× | 0.000227 | 633.58× | 2,354.5× | 0.349 pp |
| 9–15× | 0.000044 | 915.14× | 4,321.9× | 0.124 pp |
| 16×+ | 0.000013 | 1,211.8× | 13,607× | 0.116 pp |

The 2× ending bin carries **3.82 pp of total collector RTP** inside that selected subset of bonuses. That is **not** the incremental RTP caused solely by Wind Key (the Wind-only counterfactual was 1.998 pp). The bin includes the already-large raw collector piles that correlate with drawing a key, then multiplies them. Another point of Wind weight (the G5 pack) still broke the reserve because those selected piles are expensive to scale. Mean final multiplier is 1.025 because 98.1% of bonuses never leave 1×.

P(multiplier ≥ 2) = 0.0194.  
P(≥ 4) = 0.00191.  
P(≥ 6) = 0.000284.  
P(≥ 9) = 0.000057.  
P(≥ 12) = 0.000057.  
Max = 27.

### Forced collector cases

Token faces below are the config faces. Free Spin scale is 1.5. The cap is 50,000× on the round, so a single collection that is already over 50,000× contributes its full raw excess as drag. These rows are conditional. They are not probabilities. Gate cannot raise a T6 (max floor 3). Two thermals use 2× and 3×, the two heaviest common thermal weights aside from the rare 10× and 20×.

| Case | Raw | Capped | Drag |
| --- | ---: | ---: | ---: |
| T5 face 750, Judge, 1× | 1,125 | 1,125 | 0 |
| T5 face 750, Head Judge, 27× | 60,750 | 50,000 | 10,750 |
| T5 face 5,000, Judge, 4× | 30,000 | 30,000 | 0 |
| T5 face 5,000, Judge, 8× | 60,000 | 50,000 | 10,000 |
| T5 face 5,000, Head Judge, 4× | 60,000 | 50,000 | 10,000 |
| T5 face 5,000, Judge, thermal 2×3, 3× flight | 135,000 | 50,000 | 85,000 |
| T6 face 10,000, Judge, 1× | 15,000 | 15,000 | 0 |
| T6 face 10,000, Head Judge, 2× | 60,000 | 50,000 | 10,000 |
| T6 face 10,000, Judge, thermal 2, 3× flight | 90,000 | 50,000 | 40,000 |
| T6 face 25,000, Judge, 1× | 37,500 | 37,500 | 0 |
| T6 face 25,000, Head Judge, 1× | 75,000 | 50,000 | 25,000 |
| T6 face 50,000, Judge, 1× | 75,000 | 50,000 | 25,000 |
| T6 face 50,000, Head Judge, 27× | 4,050,000 | 50,000 | 4,000,000 |

T6 is 8 weights per 1,000,000 token draws. The ordinary Monte Carlo cap rate at F1 is **15 per 1,000,000** bonuses, mean drag **1.184×** (about 0.77 pp of the capped mean). The feature-off control was 16 per 1,000,000 with drag 1.87× on a 500,000 sample that included a worse cap cluster. Live Phase 5B, on its own seed, capped 6 per 1,000,000. Phase 6 at F1 does not open a new cap regime. The hot packs did: C_HI capped 2.6 per 1,000 bonuses and dragged hundreds of × off the mean.

Do not certify Phase 6 from one unstratified simulation. The 1,000,000-bonus mean is stable enough to choose a candidate. A later Phase 6B implementation run should repeat the mix at least at this size and should keep the forced table above as the tail spec.

---

## 12. Player feel

Exploratory notes in the brief: any Rejump in a Large Hill bonus about 15–35%, any Wind Key about 5–20%. Those notes were not forced. At weights that respect the RTP band, Large Hill sits below both bands.

F1 mix (exact BASE trigger weights, 1,000,000 bonuses):

| Event | Probability |
| --- | ---: |
| At least one Rejump | 0.0963 |
| At least one Wind Key | 0.0194 |
| Flight multiplier > 1 | 0.0194 |
| Both Rejump and Wind Key | 0.0103 |
| Two or more Rejumps | 0.0257 |
| Multiplier ≥ 4× | 0.00191 |

F1 dedicated start tier (same seed family, not mix-weighted):

| Start tier | n | P(Rejump) | P(Wind) | P(multi-Rejump) | Mean Rejumps / bonus |
| --- | ---: | ---: | ---: | ---: | ---: |
| Large Hill | 80,000 | 0.0788 | 0.0143 | 0.0175 | 0.108 |
| Ski Flying | 40,000 | 0.4316 | 0.1200 | 0.1920 | 0.750 |
| World Cup | 20,000 | 0.5631 | 0.2500 | 0.3154 | 1.197 |
| Perfect V | 20,000 | 0.9273 | 0.6226 | 0.7716 | 3.075 |

Higher tiers show the system clearly once the player reaches them. Perfect V at these weights is almost guaranteed to Rejump and often draws multiple keys. That is acceptable because Perfect V is rare in the mix and already has a high baseline EV.

PV2 and PV3 on a 20,000 Perfect V batch both reached **P(Wind Key) = 1.0** and roughly doubled the mean bonus versus PV1. They are rejected for Phase 6B. Perfect V does not need a guaranteed key on entry or on the first spin when the natural table already lands a key on 62% of Perfect V bonuses.

The median bonus on the mix is still 9.6×. P90 is 46.0× against 43.8× on the feature-off control. P99 is 448× against 294×. Players who never draw a key see a bonus that is very close to Phase 5B, plus an occasional redrop. The mean moves because the 1.9% of bonuses that draw a key are already the bonuses with large collector sums.

That is the acceptable tradeoff. A pack that puts Wind Key near 5% on Large Hill (G5, weight 2) was 8.8 pp at 40,000 bonuses and left a negative reserve.

---

## 13. Book size

Phase 5C sample books measured **281 uncompressed bytes per event** (one 211-event book, 59,374 bytes). Rejump adds four events, and the board event is heavier than the Phase 5C average. The estimate adds **1,680 bytes per applied Rejump** on top of 281 × event count. This is not a serialized production book and it is not compressed. The hot screen's stub zlib sample was about 33 bytes because the stub was a win counter, not a book. Ignore that figure.

F1, 1,000,000 bonuses:

|  | Events | Estimated bytes |
| --- | ---: | ---: |
| Mean | 102.4 | 29,009 |
| P95 | 173 | 49,725 |
| P99 | 252 | 73,903 |
| Max | 823 | 258,143 |

Feature-off control mean events were 101.3 and P99 events 234. Growth is small because mean Rejumps per bonus is 0.14. No candidate at the F1 weight is near a pathological book. The hot C screen was also only ~107 mean events; the failure there was RTP, not payload size.

---

## 14. Proposed Phase 6B rules

Implement only `P6A_F1_C_K1_W2_R1_PV1_B`.

- Keep BASE F01 and the live Phase 5B reel strips, U1, initial 10, max 40, persistent-target max 2, and the 50,000× shared cap untouched.
- Add the tier Mystery tables in section 9. Do not add a second economy on BASE.
- Rejump and Wind Key are Free Spin mysteries only.
- Practical Rejump limit 2 per spin. Hard chain depth 8. Overflow is a terminal no-op.
- Refill cannot emit Scatter. Retrigger only from the initial reveal.
- Resolution order is section 3. Collectors run after the chain. Flight multiplier hits only Judge and Head Judge passes.
- Ladder K1, stage rule W2, saturation B, Perfect V rule PV1.
- Persist the three stages across upgrades. Reset them at round end.
- Emit the events in section 5. Do not let the client choose the stage.
- Do not implement `SPECIAL_WORLD_RECORD` in Phase 6B.
- Do not generate production books in Phase 6B until a separate certification run repeats at least 1,000,000 mix bonuses on the live resolver and checks the cap rate against section 11.

---

## 15. Freeze check

Research code lives in:

- `math/games/0_0_poc/skyjump_v2_phase6a_engine.py`
- `math/games/0_0_poc/skyjump_v2_phase6a_search.py`
- `math/games/0_0_poc/skyjump_v2_phase6a_confirm.py`
- `math/games/0_0_poc/skyjump_v2_phase6a_large.py`
- `math/games/0_0_poc/test_skyjump_v2_phase6a.py`
- `math/games/0_0_poc/phase6a_research/`

Live `skyjump_v2_config.json`, the Phase 5B Free Spin candidate, `skyjump_v2_phase4a_economy.py`, and `skyjump_v2_phase5a_engine.py` are not part of this change. No frontend handler was added. No production book or LUT was written.
