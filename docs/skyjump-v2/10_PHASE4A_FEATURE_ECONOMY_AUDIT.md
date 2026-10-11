# SkyJump V2 — Phase 4A Feature Economy Audit

**Status:** research complete — **not** promoted to live config  
**Branch:** `feat/skyjump-v2-5x5`  
**Phase 3:** approved / frozen for live play  
**Phase 4B:** not started  

This phase mathematically designs the first **paying** BASE feature economy before committing probabilities into production events, reducers, or frontend.

---

## 1. Goal

Find a configurable Mystery-result economy:

`FLIGHT_TOKEN` · `THERMAL_LIFT` · `GATE_UPGRADE` · `JUDGE` · `HEAD_JUDGE`

that delivers approximately **9–11pp** BASE feature RTP (preferred center ~10pp), leaves a realistic Free Spins reserve toward a **~96.5%** full-game target, and does not turn every Coach activation into a dead “tokens then nothing pays” beat.

**Explicitly out of scope for 4A**

- frontend animations / production event wiring  
- production books / Stake LUTs  
- Free Spins, Rejump, Wind Key, Flight Multiplier, `SPECIAL_WORLD_RECORD`  
- feature buys  
- payline / premium-symbol retunes  
- Phase 4B promotion  

---

## 2. Locked chassis (Phase 3)

| Metric | Value |
|---|---|
| Line RTP (Coach A strips) | ~58.0486% |
| P(any Coach) A | 18.3062% |
| P(2+ Coach) A | 0.9246% |
| Mysteries / Coach | mean 3.192 · median 3 · P95 7 · P99 8 · max 12 |
| E[token face / Mystery] (Phase 3) | 6.0253x |
| E[latent token / Coach] | 19.253x |
| E[latent token / BASE spin] | 3.704x |
| Tokens pay? | **No** (Phase 3) |

Naive collection of Phase 3 latent EV would blow the RTP budget. Phase 3 token weights are therefore **not sacred** for a paying economy.

---

## 3. Methodology

### 3.1 Resolution order (deterministic, UI-independent)

1. Resolve all Mystery identities  
2. Apply all `GATE_UPGRADE` events (sequential floor++)  
3. Compute **effective** Flight Token values from adjacent `THERMAL_LIFT` (faces immutable)  
4. Process `JUDGE` / `HEAD_JUDGE` collections (no dedupe; Head Judge = two passes)  
5. Apply provisional max-win **50,000x**  
6. Settle  

### 3.2 Token face immutability

Stored face never mutates under Thermal. Example: face `50x` + adjacent `2x` and `3x` → effective `300x`, face remains `50x`.

Multiple adjacent Thermals **multiply**. Research kept this rule; 10x/20x Thermal weights were kept rare rather than removed.

### 3.3 Soft-disable counterfactuals

Layer diagnostics mute mechanics without resampling them as tokens (hard resample biased RTP upward when Thermal/Gate were “off”).

### 3.4 Search space

Research-only variables:

- Coach model A / B / C  
- Mystery result integer weights (`FLIGHT_TOKEN` dominant; `HEAD_JUDGE` ≪ `JUDGE`)  
- Token tier + within-tier weights (crushed vs Phase 3)  
- Thermal ladder weights `2,3,4,5,10,20`  
- Gate max floor **T3 vs T4** (never T5/T6 as persistent BASE floor)  

Frozen: paylines, regular paytable, Scatter frequency on live strips, board size, 50,000x ceiling.

### 3.5 Simulation

- Screen: 120,000 spins × 48 candidates (handcrafted + deterministic search stride)  
- Finalists: **5,000,000** BASE spins each (seed `20260921`)  
- Counterfactual for recommended: 1,000,000 spins  
- Conditional buckets: T5+, T6, 2+ Thermal, multi-collector  

Artifacts: `math/games/0_0_poc/phase4a_research/`

---

## 4. Coach-frequency research models

Live Phase 3 config was **not** modified. Research strips only:

| Model | Placement | P(any) | P(≥2) | Line RTP |
|---|---|---:|---:|---:|
| **A** | reels 2+4 (Phase 3 live) | 18.31% | 0.92% | 58.05% |
| **B** | reel 2 only | 9.62% | 0% | 58.47% |
| **C** | reel 2 + extended reel 4 (len 80) | 15.26% | 0.60% | 61.09%* |

\*Coach C pads the extended strip with L2/L3; line RTP drifts upward (~+3pp). Treat C as exploratory mid-band Coach frequency, not a drop-in strip for production without a dedicated line rebalance.

**Finding:** Phase 3 Coach rate (~18%) forces collectors to be extremely rare to stay near 10pp feature RTP, which drives **dead-Coach ≈ 91%**. Lowering Coach to model **B (~9.6%)** roughly doubles `P(feature win | Coach)` for the same RTP budget.

---

## 5. Why Phase 3 token EV cannot pay

Collectors pay the **sum of effective token faces**, optionally doubled by Head Judge, and stacked across multiple collectors. Gate upgrades replace below-floor faces with higher-tier faces before collection.

With Phase 3-like faces, early smokes produced **tens to hundreds of feature RTP points**. Gate uplift was the primary bomb; collector stacking amplified it.

Paying tables therefore crush T1 toward `1x` and starve T2–T6 relative to Phase 3 while **preserving the 50,000x T6 tail entry**.

---

## 6. Finalists (5,000,000 spins)

| ID | Coach | Feature RTP (capped) | P(win\|Coach) | P(dead Coach) | BASE before FS | FS remain | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| **H02_B_R1** | B | **10.71%** | **18.0%** | **82.0%** | 69.19% | 27.31% | **Recommended** |
| H04_B_gate4 | B | 10.25% | 17.0% | 83.0% | 68.73% | 27.77% | Gate max **T4** |
| H01_B_R2 | B | 11.23% | 19.1% | 80.9% | 69.71% | 26.79% | Soft-band; better feel, slightly over hard 11% |
| H05_C_mid | C | 11.38% | 12.1% | 87.9% | 72.47% | 24.03% | Mid Coach; line drift |
| H06_A_phase3_coach | A | 10.65% | 9.1% | 90.9% | 68.70% | 27.80% | Keeps Phase 3 Coach rate |

Hard feature band for scoring: **9–11pp**. Soft band used for near-misses: **8.5–12.5pp**. Exact 10.000% was not forced.

---

## 7. Recommended candidate — `H02_B_R1`

### 7.1 Coach

- Model **B**: reel 2 only  
- P(any Coach) = **9.6154%**  
- P(≥2) = 0  
- Line RTP = **58.4730%**

### 7.2 Mystery result weights

| Result | Weight | Mix (observed) |
|---|---:|---:|
| FLIGHT_TOKEN | 885 | 87.66% |
| THERMAL_LIFT | 50 | 4.94% |
| GATE_UPGRADE | 5 | 0.50% |
| JUDGE | 60 | 5.91% |
| HEAD_JUDGE | 10 | 0.99% |

### 7.3 Token tier weights (paying research)

| Tier | Weight |
|---|---:|
| T1 | 997200 |
| T2 | 2200 |
| T3 | 450 |
| T4 | 100 |
| T5 | 42 |
| T6 | 8 |

Within-tier faces heavily weight the lowest value in each tier (T1≈90% at `1x`). T6 still includes `10000 / 25000 / 50000`.

### 7.4 Thermal weights

| Mult | Weight |
|---|---:|
| 2x | 70 |
| 3x | 20 |
| 4x | 7 |
| 5x | 2 |
| 10x | 1 |
| 20x | 1 |

### 7.5 Gate

- Max floor: **T3**  
- Observed P(any Gate) ≈ **0.153%**  
- Gate face uplift RTP proxy ≈ **2.22pp** (faces only; payout impact appears through collectors)

### 7.6 Headline RTP / feel (5M)

| Metric | Value |
|---|---:|
| Line RTP | 58.4730% |
| Feature RTP raw | 10.7134% |
| Feature RTP capped | 10.7133% |
| BASE before Free Spins | **69.1863%** |
| P(any feature win) | 1.7250% |
| P(feature win \| Coach) | **17.96%** |
| P(dead Coach) | **82.04%** |
| Avg feature win \| win | 6.21x |
| Median \| win | 4x |
| P90 / P95 / P99 / P99.9 | 10 / 14 / 29 / 100 |
| P(any Judge) | 1.659% |
| P(any Head Judge) | 0.301% |
| P(any Thermal) | 1.406% |
| Avg collector passes / spin | 0.0244 |
| Avg raw face sum / spin | 0.391x |
| Avg effective token sum / spin | 0.413x |
| Judge contribution RTP | 8.39pp |
| Head Judge contribution RTP | 2.32pp |
| Thermal uplift RTP proxy | 2.17pp |

### 7.7 Cap / tail

| Metric | Value |
|---|---:|
| Cap frequency | 2e-7 (1 in 5M) |
| Cap drag RTP | ~6e-7 |
| P(feature ≥10x) | 0.1953% |
| ≥50x | 0.00612% |
| ≥100x | 0.00190% |
| ≥500x | 0.00040% |
| ≥1000x | 0.00016% |
| ≥5000x | 0.00006% |
| ≥10000x | 0.00002% |
| raw ≥50000x | 0.00002% |

Jackpot tail is present but extremely rare under crushed paying weights — as required to keep BASE features near 10pp.

### 7.8 Free Spins planning reserve

| Metric | Value |
|---|---:|
| Full target | 96.50% |
| Remaining for FS + final adj. | **27.31pp** |
| Scatter ≥3 (Coach B strips) | 0.7657% (~1/130.6) |
| Implied avg bonus / trigger | **~35.67x** |

This is a planning number only (no Free Spin math implemented). ~36x average bonus at the current Scatter rate is realistic versus an absurd multi-hundred-x requirement.

---

## 8. Counterfactual decomposition (`H02_B_R1`, 1M spins)

Soft-disable layers (same Mystery identities):

| Layer | Feature RTP | P(feature win) | Avg win\|win | P99\|win |
|---|---:|---:|---:|---:|
| A. Judge only | 6.16% | 1.52% | 4.07x | 14x |
| B. + Head Judge | 8.60% | 1.73% | 4.97x | 18x |
| C. + Thermal | 9.16% | 1.73% | 5.29x | 20x |
| D. + Gate (full) | 9.81% | 1.73% | 5.66x | 29x |

Interpretation:

- Judges carry the majority of feature RTP.  
- Head Judge adds ~+2.4pp via the mandatory double pass.  
- Thermal adds ~+0.6pp mean with more P99 stretch.  
- Rare Gate adds ~+0.7pp but fattened the P99 tail (floor replacements into higher faces before collection).  

Cap frequency stayed ~0 in the 1M counterfactual sample; the 5M full run saw a single cap hit.

---

## 9. Player-feel / dead-feature analysis

Coach currently appears ~once per 5.5 spins on Phase 3 strips. Under paying collectors constrained to ~10pp:

| Coach model | P(win\|Coach) | Dead Coach | Verdict |
|---|---:|---:|---|
| A (18.3%) | ~9% | ~91% | Unplayable feel if every Coach shows Mysteries/tokens |
| C (15.3%) | ~12% | ~88% | Still too dead |
| **B (9.6%)** | **~18%** | **~82%** | Best researched compromise |

**Even on Coach B, ~4 of 5 Coach activations still pay 0 feature win.** Tokens without a collector remain the dominant visible pattern. This is structural while:

- Mysteries mostly resolve to non-paying tokens/thermals/gates  
- Collectors must stay rare for RTP  

Options for later phases (not implemented here):

1. Accept ~80% dead Coach with clearer “banked tokens / no Judge” UX  
2. Lower Coach further (<9%) and raise collector density  
3. Introduce a small auto-pay / consolations path (new mechanic — out of 4A)  
4. Move more RTP into Free Spins and keep BASE features leaner / rarer  

Phase 4A does **not** hardcode an acceptance threshold; it ranks candidates on RTP **and** dead-Coach rate. Recommended `H02_B_R1` is the best joint score found.

---

## 10. Gate max floor T3 vs T4

Under rare Gate (~weight 5–6):

- **T3 (H02):** feature 10.71%, gate face uplift ~2.22pp  
- **T4 (H04):** feature 10.25%, gate face uplift ~2.60pp, slightly worse feel  

Recommendation: keep **max floor T3** for BASE Phase 4B. T4 is viable but not necessary; higher floors amplify collector tails when Gate + Judge collide.

---

## 11. Implementation recommendation for Phase 4B

**Do not start Phase 4B until this candidate (or an explicit alternate) is approved.**

When approved, Phase 4B should:

1. Promote research weights into a **new** config section / candidate file — **do not silently overwrite Phase 3 latent token tables** without a migration note.  
2. Implement book/events for Mystery results + Gate replacements + Thermal effective values + Judge / Head Judge double-pass collections.  
3. Keep reducer order identical to §3.1.  
4. Ship placeholder frontend only after math events exist.  
5. Plan Coach strip change **A→B** (or a production-cleaned mid-band) as part of the same promotion if dead-Coach feel is accepted as a blocker on A.  
6. Revisit premium payline feel only after the full feature stack exists (per Phase 4A scope).  

**Ready to promote into Phase 4B: NO**

Concrete blockers:

1. Human approval of `H02_B_R1` (weights + Coach B).  
2. Explicit accept/reject of ~82% dead-Coach feel (or request another search pass).  
3. Decision that paying token EV may diverge sharply from Phase 3 latent EV.  

---

## 12. Files

| Path | Role |
|---|---|
| `math/games/0_0_poc/skyjump_v2_phase4a_economy.py` | Paying resolver |
| `math/games/0_0_poc/skyjump_v2_phase4a_candidates.py` | Coach A/B/C + search space |
| `math/games/0_0_poc/skyjump_v2_phase4a_simulate.py` | MC + scoring + counterfactual |
| `math/games/0_0_poc/skyjump_v2_phase4a_search.py` | Deterministic search driver |
| `math/games/0_0_poc/phase4a_research/` | Screen/finalist/summary JSON |
| `math/tests/test_skyjump_v2_phase4a.py` | Unit / invariant tests |

**Phase 3 live config modified:** NO  

**Phase 4 complete:** NO (4A research only)

---

## 13. Reproduction

```bash
cd math
python games/0_0_poc/skyjump_v2_phase4a_search.py --screen-spins 120000 --finalist-spins 5000000 --top 5
python -m pytest tests/test_skyjump_v2_phase4a.py -q
```
