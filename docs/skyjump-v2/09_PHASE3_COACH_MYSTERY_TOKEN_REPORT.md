# SKYJUMP V2 — Phase 3 Coach / Mystery / Token report

**Status:** PHASE 3 PROVISIONAL FEATURE MATH. Not production RTP. Not a Stake LUT.  
**Lineage:** `skyjump-v2` · **mathVersion:** 1 · **eventSchemaVersion:** 2  
**Seed:** `20260921`  
**Simulation:** 5,000,000 BASE spins (`skyjump_v2_phase3_sim_report.json`)  
**Do not start Phase 4 from this file.** Thermal, collectors, Free Spins, and production books remain out of scope.

Phase 3 adds the first real feature layer on top of the approved Phase 2 chassis. Flight Tokens **do not pay**. Feature RTP from tokens is **0**. This report measures occurrence, Mystery flood, and **latent token-value exposure** for later RTP modelling.

---

## 1. Locked Phase 3 rules

1. Tokens are latent wager-multipliers on the board. A 25× token stores face value 25×; it does not add 25× to the player's win.
2. Coach `C` is a math-owned reel-strip symbol. It is not an overlay roll after the spin.
3. Mystery `Y` is created only by Coach transformations. It is not an initial strip symbol.
4. Flight Tokens are created only by Mystery resolution. They are not initial strip symbols.
5. Paylines evaluate on the **initial** board, then Coach, then Mystery, then tokens.
6. Scatter and Perfect V are counted from the initial reveal only.
7. Direct Perfect V pattern stays `[0,1,2,1,0]`. Do not raise the BASE rate.

Event order:

```
skyjumpSpinStart
skyjumpBoardReveal
skyjumpLineWins
skyjumpScatterResult
skyjumpCoachSignal*
skyjumpMysteryTransform?
skyjumpMysteryResolve*
skyjumpResult          // totalFeatureWinX = 0
setTotalWin
finalWin
```

---

## 2. Coach reel placement

Deterministic search over isolated `L3 → C` replacements (no remesh, no Coach on every reel).

| Candidate reels (1-based) | P(any Coach) | P(2+) | Notes |
| --- | ---: | ---: | --- |
| 2 | ~9.6% | 0 | Below the 10–18% research band |
| 2+3+4 | ~26% | too high | Above band |
| **2+4** | **18.306%** | **0.925%** | Only 2-reel layout inside both bands |

**Chosen:** reels **2 and 4**, **one isolated Coach stop each**.

Exact window convolution:

| Metric | Value | 1 in N |
| --- | ---: | ---: |
| P(any Coach) | 18.3062% | 5.46 |
| P(2+ Coach) | 0.9246% | 108.16 |
| Simulated P(any) | 18.3115% | 5.46 |
| Simulated P(2+) | 0.9261% | 108.0 |
| Simulated P(exactly 1) | 17.3855% | |
| Simulated no-op Coach | 0 | |

Coach never occupies reels 1, 3, or 5 in V2.0 BASE.

---

## 3. Post-Coach line RTP

Adding non-paying `C` cells dilutes regular-symbol probabilities. Phase 2's 60.1408% is **not** assumed.

| Metric | Phase 2 | Phase 3 |
| --- | ---: | ---: |
| Theoretical line RTP | 60.1408% | **58.0486%** |
| Simulated line RTP | 60.0894% (5M) | **58.0045%** (5M) |
| Hit rate | ~43.3% | **42.0568%** |
| Zero-win rate | | **57.9432%** |
| Max observed line win | | 29.4× |

The 58.05% result sits inside the locked 57–61% research band. **No paytable or strip remesh was applied.**

Payout distribution (5M):

| Bucket | Share |
| --- | ---: |
| 0× | 57.9432% |
| >0–1× | 21.3314% |
| 1–2× | 12.5402% |
| 2–5× | 7.6045% |
| 5–10× | 0.5641% |
| 10–25× | 0.0166% |
| 25–50× | 0.00014% |
| 50×+ | 0 |

---

## 4. Coach selection

Default model: uniform among **distinct visible regular types** at the moment that Coach resolves. Not weighted by cell count.

Simulated selection mix among activating Coaches:

| Type | Share of selections |
| --- | ---: |
| P1 | 4.11% |
| P2 | 7.04% |
| P3 | 10.88% |
| M1 | 11.99% |
| M2 | 12.87% |
| M3 | 12.43% |
| L1 | 13.57% |
| L2 | 13.51% |
| L3 | 13.61% |

Low symbols still lead because they are more often *present*, but P1 is selected far more often than its 1.92% cell frequency. Cell-count weighting would have made P1 almost invisible. Keep uniform-over-types unless a later feel pass proves otherwise.

Multiple Coaches resolve left-to-right by reel, then top-to-bottom by row. After a type is transformed, it is no longer eligible. Zero-eligible boards emit `noOp` + `reason: noEligibleRegularType`.

---

## 5. Mystery-count distribution

No cap in Phase 3. All visible instances of the selected type transform.

| Stat | Mysteries per Coach |
| --- | ---: |
| Mean | 3.192 |
| Median | 3 |
| P90 | 6 |
| P95 | 7 |
| P99 | 8 |
| Max observed (5M) | **12** |
| N | 961,880 |

**Tail note:** selecting L2/L3 can flood the board. Twelve Mysteries on one Coach is real. That is not a bug; it is exposure. Do **not** add an arbitrary cap without a written decision. Later Thermal / Judge / Flight Multiplier will multiply this tail.

---

## 6. Token model

Six canonical tiers. Display ids `T1`–`T6`. Tier 6 name is `TOKEN_WORLD_RECORD`. Future instant-max-win special is `SPECIAL_WORLD_RECORD`.

| Tier | Name | Values | Weight /1e6 | P(tier) |
| ---: | --- | --- | ---: | ---: |
| 1 | ROOKIE_TOKEN | 1 / 2 / 3 / 4 | 840000 | 84.00% |
| 2 | K_POINT_TOKEN | 5 / 10 / 15 | 130000 | 13.00% |
| 3 | LARGE_HILL_TOKEN | 25 / 50 / 100 | 25000 | 2.50% |
| 4 | SKI_FLYING_TOKEN | 150 / 200 / 250 / 500 | 4500 | 0.45% |
| 5 | WORLD_CUP_TOKEN | 750 / 1000 / 2500 / 5000 | 492 | 0.0492% |
| 6 | TOKEN_WORLD_RECORD | 10000 / 25000 / 50000 | 8 | 0.0008% |

Within-tier weights down-weight the top of each ladder (see `flightTokens.valueWeights` in `skyjump_v2_config.json`).

Exact per-Mystery face-value:

| Stat | Value |
| --- | ---: |
| E[token face] | **6.0253×** |
| Median | 2× |
| P90 | 5× |
| P95 | 15× |
| P99 | 50× |
| P99.9 | 250× |
| Max possible | 50000× |
| Simulated mean | 6.0310× |

T6 is 8 in 1,000,000 Mysteries (1 in 125,000 Mysteries). It is not remotely common.

---

## 7. Latent exposure

Tokens do not pay. These are **face-value sums** sitting on the board.

Per Coach activation (simulated):

| Stat | Latent × |
| --- | ---: |
| Mean | 19.253 |
| Median | 8 |
| P90 | 29 |
| P95 | 55 |
| P99 | 200 |
| Max observed on a spin | 50014 |

Per paid BASE spin:

| Stat | Value |
| --- | ---: |
| E[latent token value] | **3.704×** |
| P(any token) | 18.3115% |
| P(T3+ on spin) | 1.473% |
| P(T4+) | 0.275% |
| P(T5+) | 0.0300% |
| P(T6) | 0.00054% (1 in 185,185) |

Phase 3 feature RTP from this layer: **0**.

---

## 8. Tail safety

Future mechanics can multiply/collect these faces (Thermal × Flight Multiplier × repeated Judge). A 50,000× token can hit max win immediately.

Per paid BASE spin (5M):

| Event | Simulated P | 1 in N |
| --- | ---: | ---: |
| token ≥ 100× | 0.60414% | 165.5 |
| token ≥ 500× | 0.05754% | 1,738 |
| token ≥ 2500× | 0.00914% | 10,941 |
| token ≥ 10000× | 0.00054% | 185,185 |
| token = 50000× | 0.00008% | 1,250,000 |

High tiers stay in the table. They are intended jackpot/tail content. Do not delete T6 because it is rare.

---

## 9. Scatter after Coach integration

Coach replaced isolated `L3` stops, not Scatter. Exact 3+ Scatter remains **0.7657% = 1 in 130.6**. Simulated 3+ = 0.7639%. Perfect V exact remains **1 in 380,204,032**. Simulated Perfect V hits in 5M: 0, as expected.

Coach cannot select Scatter. Mystery cannot create Scatter. Tokens cannot create Scatter.

---

## 10. Direct Perfect V

Pattern unchanged: `[0,1,2,1,0]`.

This BASE route is an ultra-rare shortcut / easter-egg. The intended practical Perfect V path later is bonus-tier upgrade:

`LARGE_HILL → SKI_FLYING → WORLD_CUP → PERFECT_V`

Do not make the BASE V-pattern common.

---

## 11. Premium symbol value / player-feel risk

Phase 3 did **not** retune the paytable. Line RTP is still dominated by lows.

Theoretical contribution after Coach:

| Symbol | RTP (pp) |
| --- | ---: |
| P1 | 0.083 |
| P2 | 0.533 |
| P3 | 1.868 |
| M1–M3 | 10.64 |
| L1 | 11.34 |
| L2 | 15.66 |
| L3 | 17.92 |

P1+P2+P3 together are **2.48 pp** of 58.05% line RTP (~4.3% of the line bucket). L1+L2+L3 are **44.92 pp** (~77%).

5M observed premium line hits:

| Hit | Count | 1 in N spins |
| --- | ---: | ---: |
| P1 3-kind | 906 | 5,519 |
| P1 4-kind | 16 | 312,500 |
| P1 5-kind | 0 | >5M |
| P2 3-kind | 7,473 | 669 |
| P2 4-kind | 308 | 16,234 |
| P2 5-kind | 15 | 333,333 |
| P3 3-kind | 33,598 | 149 |
| P3 4-kind | 1,977 | 2,529 |
| P3 5-kind | 135 | 37,037 |
| Any premium line ≥5× | 0.04622% of spins | 2,164 |

**Feel risk:** premium symbols will often look like dead tiles. P1 5-kind did not appear in 5M. Candidate future direction (not implemented): move some RTP from low 3-kind chatter into premium 4/5-kind awards. Do this only with a written Phase 4+ math pass.

---

## 12. Feature reducer

Pure event replay. No RNG. No UI timing. Phase 3 state includes board cell kinds, token tier/face, Coach progress, feature-chain step, line win, feature win (forced 0), and reserved future fields (`tokenFloorTier`, `persistentMysteryTargets`, Flight Multiplier stages, Free Spin remaining).

Same events → same final board in Python and TypeScript tests.

---

## 13. FEATURE SAMPLE

Seven Python-generated DEV books in `skyjump_v2_feature_samples.json`:

| Id | Case |
| --- | --- |
| 01 | Coach selects a premium |
| 02 | Coach selects a low with multiple cells |
| 03 | Two Coaches |
| 04 | T1 token |
| 05 | T3 token |
| 06 | T4+ token |
| 07 | Mixed token tiers |

`/dev-preview` source **FEATURE SAMPLE** replays them. Production must not import that JSON.

---

## 14. What was not built

Thermal Lift, Gate Upgrade, Rejump, Judge, Head Judge, Wind Key, Flight Multiplier, `SPECIAL_WORLD_RECORD`, Free Spins execution, feature buys, production `books_*.jsonl.zst`, LUT, `stake-upload/math`.
