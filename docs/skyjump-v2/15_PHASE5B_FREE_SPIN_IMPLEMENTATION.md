# SKYJUMP V2 — Phase 5B Free Spin Implementation

**Status:** Core Free Spins implemented on `feat/skyjump-v2-5x5`.  
**Promoted candidate:** `FS5A_U1_P2_M40_mid_E15j2`  
**Upgrade model:** U1  
**Not in this phase:** Rejump, Wind Key, Flight Multiplier, `SPECIAL_WORLD_RECORD`, feature buys, production Stake books, production LUT.

The research artifact and Phase 5A scripts stay in the tree. Promotion copied the candidate strips and weights into `skyjump_v2_config.json`. It did not rebuild probabilities from the markdown summary.

---

## 1. Preflight weighted-EV reconciliation — PASS

The Phase 5A summary shows conditional trigger shares and fresh-start tier means whose rounded product is about **27.97×**. The same summary’s mix result is **27.46×**. Both numbers come from the artifact `phase5a_research/finalist_FS5A_U1_P2_M40_mid_E15j2_mix1000000_tier100000.json`. Neither is a weighting bug.

Exact direct trigger probabilities (Coach E strips, `base_trigger_mix`):

| Start | Absolute P | Conditional given Scatter ≥ 3 |
| --- | ---: | ---: |
| Exactly 3 → LARGE_HILL | 0.006213590660243767 | 0.9515921639815444 |
| Exactly 4 → SKI_FLYING | 0.0003099140083699995 | 0.047462370471220025 |
| 5, not Perfect V → WORLD_CUP | 6.171610276639861e-06 | 0.0009451629982603432 |
| Direct Perfect V | 1.9755474637131444e-09 | 3.0254897511534684e-07 |
| Scatter ≥ 3 | 0.00652967825443787 | 1 |

Direct Perfect V is a subset of exactly five Scatters. `classify_base_trigger` returns `PERFECT_V` when `perfectV` is true and does not also classify that board as World Cup.

Two different estimators:

1. **Reported 27.46×.** `run_mix_weighted`, seed `20260921`, `n = 1,000,000`, award = `bonusWinXCapped`, `round_prior_win_x = 0`. Each start tier is drawn from the exact conditional mix. The mean is `sum(awards) / n`. Reconstructing it as `sum(startCount_tier / n * perStartMeans_tier)` equals **27.45472×**. Contributions from that same run: Large Hill 21.50709240, Ski Flying 5.76912420, World Cup 0.17850340, Perfect V 0 (sampled 0 times; expected count ≈ 0.30).
2. **≈27.97×.** Dedicated 100,000-start means (Large Hill 23.309466, Ski Flying 117.61787, World Cup 214.714913, Perfect V 577.054385) multiplied by the exact conditionals. That product is about **27.9666×**. It is a different Monte Carlo from the 1,000,000 mix. The displayed 27.97× is that product rounded, not a second formula inside the mixer.

Full-round cap interaction with a large BASE trigger win is **not** inside 27.46×. The mixer passes `round_prior_win_x = 0`. The live resolver does accept the trigger win as prior when a real round is built. Cap hits in the mix are the standalone incremental cap (`pCap = 6e-6`).

Formula used for the reported weighted bonus EV and for FS RTP:

```
weightedBonusEv = mean(bonusWinXCapped) over mix-sampled starts
coreFsRtp       = weightedBonusEv * P(Scatter >= 3)
```

The candidate was not altered.

---

## 2. Certified BASE

Certified BASE SHA-256 remains:

`d932065b36a626c7cd9a818bd8c401559e6270c434622d32d1fb640e3d8d7803`

That digest is the config bytes before the appended `freeSpins` key, closed again with `}\r\n`. Every pre-existing JSON value is unchanged: Coach E strips, Mystery weights, token weights, Thermal weights, Gate rules, Judge rules, paytable, paylines, and Scatter distribution. The full file hash changed because the bonus section was added. `phase5b_promote.py` rebuilds the splice from the certified blob and refuses any other candidate id.

---

## 3. Promoted config

`freeSpins` in `skyjump_v2_config.json`:

- `version` 1, `candidateOrigin` `FS5A_U1_P2_M40_mid_E15j2`
- `initialSpins` 10, `maxSpins` 40, `upgradeModel` U1, `upgradeActivation` NEXT_SPIN
- `maxPersistentTargets` 2, duplicate behaviour B
- fallback: if no eligible non-persistent regular remains, Coach may select an already persistent type
- economy `E_s15_j2`: token value scale 1.5; Mystery weights Flight Token 752, Thermal 42, Gate 6, Judge 170, Head Judge 30
- those weights do not replace BASE `featureEconomy`
- tiers `LH_C2_Smid`, `SF_C3_Smid`, `WC_C4_Smid`, `PV_C5_Smid` with the research strips, coach plans, and scatter plan `{0:1, 1:3, 2:1, 3:2, 4:1}`
- `wagerCostMultiplier` 0
- reserved inactive: flight multipliers, rejump, Wind Key, Flight Multiplier, World Record

---

## 4. Trigger and one economic round

On a paid BASE spin, Scatter is counted on the initial board only:

| Pattern | Start tier |
| --- | --- |
| Exactly 3 Scatter | LARGE_HILL |
| Exactly 4 Scatter | SKI_FLYING |
| 5+ Scatter, not Perfect V | WORLD_CUP |
| Perfect V pattern | PERFECT_V |

The trigger spin’s line and BASE feature wins stay on that spin. They are not added again as Free Spin award. `roundWinX = triggerSpinWinX + bonusWinX`, then capped at 50,000×.

One `POST /wallet/play` returns one book: the trigger spin plus the complete Free Spin sequence. One `POST /wallet/end-round` settles it. `POST /bet/event` stores the resume index inside that bet. Free Spins do not call `play()` and do not debit the balance. Local demo still uses one play and one end-round; `checkIsBonusGame` keeps the round open until the Free Spin sequence has been played.

---

## 5. checkIsBonusGame

`frontend/apps/poc/src/game/skyjump_v2/checkIsBonusGame.ts` is wired from `actor.ts`.

It returns true only when the book contains `skyjumpFreeSpinsStart` and either the bet is still active, the end event is missing, or the resume cursor is at or before `skyjumpFreeSpinsEnd`. A BASE-only book stays false, so XState can end that round immediately. A bonus book uses the bonus path: no second play, no debit per Free Spin, and autoplay does not start the next paid round while the cursor is still inside the bonus.

---

## 6. State, events, and spin order

Serializable state is carried by `skyjumpFreeSpinState` and rebuilt by the Python and TypeScript reducers:

`bonusActive`, `bonusTier`, `freeSpinsInitial`, `freeSpinsRemaining`, `freeSpinsPlayed`, `totalFreeSpinsAwarded`, `upgradeCount`, `retriggerCount`, `tokenFloorTier`, `persistentMysteryTargets`, `guaranteedGateUsed`, `coachGuaranteeState`, `bonusWinXRaw`, `bonusWinXCapped`, `roundWinXRaw`, `roundWinXCapped`, `maxWinReached`, `pendingTierUpgrade`.

Reserved and inactive: `flightMultiplierRunUp`, `flightMultiplierTakeoff`, `flightMultiplierFlight`, `rejumpState`.

Lifecycle events: `skyjumpFreeSpinsStart`, `skyjumpFreeSpinStart`, `skyjumpFreeSpinState`, `skyjumpBonusUpgrade`, `skyjumpFreeSpinEnd`, `skyjumpFreeSpinsEnd`. Existing BASE feature events stay. `setTotalWin` during the bonus is the running round total (same pattern as the local Ways books). One `finalWin` closes the book.

Each Free Spin follows the approved order. Lines and Scatter are evaluated on the initial board before persistent Mystery transforms. An upgrade does not change the current spin’s feature rules.

U1: 3+ Scatter adds 5 spins and one tier, except Perfect V which adds 5 spins and stays Perfect V. `spinsRequested` and `spinsAdded` are both on the upgrade event. Example: awarded 38, requested +5, added +2, total 40. No further spins are added at 40. The Phase 5A research room formula was off by one against that example and never bound the 1,000,000-trigger sample (max observed 35). The live room is `max(0, maxFreeSpins - spinsAwardedTotal)`.

---

## 7. Tier rules and persistence

**Large Hill.** Research Coach rate about 13.68%. No persistent Mystery targets. Floor persists. Ordinary Coach and feature engine stay active.

**Ski Flying.** Research Coach rate about 19.79%. Up to 2 persistent Mystery targets. Behaviour B prefers a non-persistent eligible regular. A selected target stays for the rest of the bonus, including later upgrades. On later spins, after lines and Scatter, visible regulars of those types become Mystery.

**World Cup.** Research Coach rate about 23.61%. Includes Ski Flying persistence. Guaranteed Gate: the first Free Spin that has at least one Mystery and no natural Gate replaces one eligible result with `GATE_UPGRADE`. Preference is Thermal Lift, otherwise the first eligible T1–T4 Flight Token. Never T5, T6, Judge, or Head Judge. No extra Mystery is created. `guaranteedGateUsed` then stays true through later tiers.

**Perfect V.** Includes prior persistence. Every spin resolves at least one Coach. If the board has none, math emits a `skyjumpCoachSignal` with `synthetic` and `guaranteed`. Natural extra Coaches stay. `coachGuaranteeState` records `required`, `satisfied`, `synthetic`, and `coachCount`. This is bookkeeping after the spin resolves; it does not spend RNG. Wind Key, Flight Multiplier, and Rejump are not awarded. Perfect V is the core version and keeps future EV headroom.

At the end of each Free Spin the reducer clears the board, token cells, Thermals, Judges, Mysteries, and Coach positions. Tier, spin counters, token floor, persistent targets, guaranteed Gate, accumulated win, and max-win state remain. Tokens are not banked.

---

## 8. Max win and resume

The round cap is 50,000× of trigger win plus bonus win. Once `maxWinReached` is set, the resolver emits `skyjumpCapReached` with `terminated: true` and does not play the remaining Free Spins. It does not emit a string of zero-value spins. Further monetary award is not created.

Resume uses the event index. Replaying the prefix through the reducer restores the Free Spin number, tier, remaining and awarded spins, pending upgrade, persistent targets, token floor, guaranteed Gate, Coach guarantee, accumulated win, and max-win flag. `skyjumpFreeSpinState` is authoritative and clears the board so token cells cannot leak. Tests cover: before the first Free Spin, mid Large Hill, immediately after an upgrade event, Ski Flying with 2 targets, World Cup after the guaranteed Gate, Perfect V, immediately before the last Free Spin, and max-win termination.

---

## 9. Placeholder frontend

During a bonus the board shows FREE SPINS, the tier name, spins remaining, bonus win, token floor, persistent target ids, Gate locked, and Coach guaranteed. An upgrade shows `LARGE HILL → SKI FLYING` (and the later steps) plus a short unlock line for the new mechanic. There is no final art. The HUD is a mirror of book events. `skyjump_v2` does not call `Math.random`.

---

## 10. Live implementation simulation

`skyjump_v2_phase5b_validate.py` reran the promoted config through the same mixer as Phase 5A. Seed `20260921`. 1,000,000 mix-weighted triggered bonuses and 100,000 direct starts per tier. Output: `phase5b_research/live_mix1000000_tier100000.json`.

Weighted core bonus EV **27.45472×**. Core FS RTP **17.92705 pp**. Mean spins **10.432886**. Max observed **35** (bound 40). Large Hill progression: Ski Flying **8.102%**, World Cup **0.666%**, Perfect V **0.060%**.

The post-simulation `coachGuaranteeState` field does not change awards or RNG, so this run still measures the promoted candidate.

### Weighted bonus

| Metric | Value |
| --- | ---: |
| Mean | 27.45472× |
| Median | 9.6× |
| P(<5×) | 0.212998 |
| P(<10×) | 0.516924 |
| P(≥25×) | 0.188489 |
| P(≥50×) | 0.087503 |
| P(≥100×) | 0.044796 |
| P(≥250×) | 0.013385 |
| P(≥500×) | 0.004423 |
| P(≥1000×) | 0.001545 |
| Mean spins | 10.432886 |
| P(>15) | 0.006105 |
| P(>20) | 0.000462 |
| P(>30) | 0.000004 |
| Max spins | 35 |
| P(no Coach) | 0.212343 |
| P(no collector) | 0.437425 |
| P(upgrade ≥ 1) | 0.079973 |
| Cap frequency | 0.000006 |

Cap drag is not a separate accumulator. The reported mean is already `bonusWinXCapped`. Six bonuses in 1,000,000 hit the standalone cap.

### Direct-start means (100,000 each)

| Start | Mean | Median | P(<5×) | P(<10×) | P(no Coach) | P(no collector) | Mean spins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Large Hill | 23.309466× | 9.2× | 0.21843 | 0.53413 | 0.21672 | 0.45128 | 10.44176 |
| Ski Flying | 117.61787× | 55.1× | 0.07129 | 0.18231 | 0.10517 | 0.14370 | 10.43065 |
| World Cup | 214.714913× | 87.0× | 0.05182 | 0.12685 | 0.06310 | 0.09304 | 10.43498 |
| Perfect V | 577.054385× | 324.0× | 0 | 0.00002 | 0 | 0.00001 | 10.42911 |

Given a Large Hill start, P(reach Ski Flying) = 0.08102, P(reach World Cup) = 0.00666, P(reach Perfect V) = 0.00060.

---

## 11. RTP budget

| Piece | Value |
| --- | ---: |
| Certified BASE line | 59.6962% |
| Certified BASE feature, capped | 11.516% |
| BASE before Free Spins | 71.212% |
| Core FS RTP | 17.92705 pp |
| BASE + core FS | 89.13925% |
| Future reserve to 96.50% | 7.36075 pp |

The reserve is not spent. It remains for Rejump, Wind Key, Flight Multiplier, and final tuning.

---

## 12. Tests

Phase 5B unit tests cover trigger classification, Perfect V override, no trigger-spin double count, zero extra wager, initial 10 spins, U1 +5, next-spin activation, the 40-spin award cap, behaviour B, guaranteed Gate once and never on Judge or T5+, Perfect V Coach, floor and target persistence, board reset, the 50,000× cap, max-win stop, resume checkpoints, and deterministic replay.

Phase 5A tests still pass against the certified BASE prefix. Phase 1–4C pytest: **85 passed**. Python and TypeScript reducers matched on a Large Hill book (round 7.0×). `checkIsBonusGame` accepts an active or in-progress bonus book and rejects a BASE book and a cursor past `skyjumpFreeSpinsEnd`.
