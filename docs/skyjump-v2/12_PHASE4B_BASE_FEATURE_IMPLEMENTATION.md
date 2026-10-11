# SKYJUMP V2 — Phase 4B BASE Feature Implementation

**Status:** PHASE 4B PROVISIONAL PAYING FEATURE MATH. Not production RTP. Not a Stake LUT.  
**Branch:** `feat/skyjump-v2-5x5`  
**Lineage:** `skyjump-v2` · **mathVersion:** 1 (unchanged) · **featureEconomyVersion:** 1 · **eventSchemaVersion:** 2  
**Promoted candidate:** `F01_E_feel` (Phase 4A.2 feel-primary pick)  
**Seed:** `20260921`  
**Do not treat as certified RTP.** Free Spins, Rejump, Wind Key / Flight Multiplier, and production books remain out of scope.

Phase 4B promotes the first **paying** BASE feature economy onto the live V2 config and resolver. Flight Tokens can now contribute to `totalFeatureWinX` when a Judge or Head Judge collects them. Tokens without a collector remain visible but **uncollected** for that spin only — there is no cross-spin banking.

---

## 1. Promoted candidate — `F01_E_feel`

Authoritative tables live in `math/games/0_0_poc/skyjump_v2_config.json` under `featureEconomy` and `flightTokens`. Research artifact: `phase4a2_research/candidate_F01_E_feel.json`.

| Field | Value |
| --- | --- |
| `featureEconomyVersion` | **1** |
| `candidateOrigin` | **F01_E_feel** |
| `meta.lineage` | `skyjump-v2` |
| `meta.mathVersion` | **1** (no bump — no production books yet) |
| `maxWinX` / cap | **50,000×** nominal bet |
| `gateMaxFloor` | **3** (T3 is the highest persistent BASE floor) |
| `conditionalCollectors` | **false** (independent Mystery table) |

### Coach model E (live strips)

- Reels **2 and 4**, one Coach stop each, **120 / 120** frequency-preserving extended strips  
- P(any Coach) ≈ **8.16%** · P(≥2 Coach) ≈ **0.174%** · theoretical line RTP ≈ **59.70%**

### Mystery result weights (independent, sum 1000)

| Result | Weight | Share |
| --- | ---: | ---: |
| `FLIGHT_TOKEN` | 855 | 85.5% |
| `THERMAL_LIFT` | 42 | 4.2% |
| `GATE_UPGRADE` | 3 | 0.30% |
| `JUDGE` | 85 | 8.5% |
| `HEAD_JUDGE` | 15 | 1.5% |

### Token tier weights (paying economy)

| Tier | Weight /1e6 | P(tier) |
| ---: | ---: | ---: |
| T1 | 999400 | 99.94% |
| T2 | 400 | 0.04% |
| T3 | 120 | 0.012% |
| T4 | 40 | 0.004% |
| T5 | 32 | 0.0032% |
| T6 | 8 | 0.0008% |

Within-tier weights match the candidate JSON (T1 nearly always `1×`; T6 still includes `50000×`).

### Thermal weights

| Mult | Weight |
| ---: | ---: |
| 2× | 70 |
| 3× | 20 |
| 4× | 7 |
| 5× | 2 |
| 10× | 1 |
| 20× | 1 |

---

## 2. Phase 3 vs Phase 4B token table history

Phase 3 measured **latent** token exposure with research-heavy weights suited to “what if everything collected?” modelling. Phase 4B intentionally switches to **lean paying** faces so Judge/Head Judge awards stay inside the ~11.8pp provisional feature budget.

| Tier | Phase 3 weight /1e6 | Phase 4B (F01) /1e6 |
| ---: | ---: | ---: |
| T1 | 840000 | **999400** |
| T2 | 130000 | **400** |
| T3 | 25000 | **120** |
| T4 | 4500 | **40** |
| T5 | 492 | **32** |
| T6 | 8 | 8 |

Phase 3 tables are archived read-only at `flightTokens.phase3LatentResearch` in config. They must not be mixed back into live resolution.

Phase 3 also resolved every Mystery to `FLIGHT_TOKEN` only and set `totalFeatureWinX = 0`. Phase 4B resolves the full Mystery mix above and pays collectors.

---

## 3. Authoritative resolution order

Math and frontend replay must follow this sequence on a paid BASE spin. UI animation timing may differ; **event order may not.**

```
initial board reveal
→ evaluate paylines (regulars only)
→ scatter count (initial reveal only)
→ Coach selection + Mystery transform
→ resolve all Mystery identities (FLIGHT_TOKEN | THERMAL_LIFT | GATE_UPGRADE | JUDGE | HEAD_JUDGE)
→ apply Gate upgrades (sequential floor++)
→ compute Thermal effective values (Moore neighbourhood; faces immutable)
→ Judge / Head Judge collections (in Mystery resolve order; tokens not consumed)
→ accumulate feature win
→ apply max-win cap (50,000× on line + feature)
→ skyjumpResult → setTotalWin → finalWin
```

Config mirror: `featureEconomy.resolutionOrder` in `skyjump_v2_config.json`.

**Not in Phase 4B:** Rejump loops, Wind Key / Flight Multiplier, World Record board special, Free Spin execution.

---

## 4. Gate rules

- Persistent state: `tokenFloorTier`, default **1** at spin start.  
- Each `GATE_UPGRADE` Mystery raises the floor by **+1**, clamped to `gateMaxFloor = 3` (T1 → T2 → T3 max in BASE).  
- Further Gate events at max floor emit **no-op** Gate events (floor unchanged).  
- Visible tokens with tier **below** the new floor are **replaced** by Math: event carries `(tierBefore, valueBefore, tierAfter, valueAfter)` per cell. Frontend never picks replacements.  
- Replacement values are sampled from legal within-tier weights for the **new** tier (not a tier re-roll).  
- Gate runs **after** all Mystery identities are known and **before** Thermal effective-value computation.

---

## 5. Thermal Lift

- Neighbourhood: **Moore** (`row ±1`, `reel ±1`), **8 cells**, **self excluded**. Edge/corner cells have fewer neighbours.  
- **Face value is immutable.** Thermal never overwrites stored `tokenValueX` / face on the cell.  
- **Effective value** = `face × product(applicable Thermal mults)`. Multiple adjacent Thermals **multiply**.  
- Thermals affect Flight Tokens only; they do not multiply line wins.  
- Thermal events list `affectedTokens` with `faceValueX`, `effectiveValueX`, and `appliedMults[]`.

---

## 6. Collectors

### Judge

- Sums **effective** values of all visible Flight Tokens on the board at collection time.  
- Adds that sum to `totalFeatureWinX` (pre-cap).  
- **Tokens are not consumed** (`consumed: false` in V2.0). They remain on the board for later collectors in the same chain.

### Head Judge

- **Two explicit book events** (`skyjumpHeadJudgeCollect`, `pass: 1` then `pass: 2`).  
- **No other mechanics** run between the two passes in Phase 4B.  
- Each pass uses the **same** effective token sum as a Judge (unless a future math version inserts intervening events).  
- With tokens present and no intervening changes: Head Judge ≈ **2× Judge** on that sum.

### Multiple collectors

- Every Judge and each Head Judge pass is a separate collection.  
- Multiple Judges / Judge + Head Judge **stack** because tokens remain. Example: one `4×` token + Judge + Judge + Head Judge → `4 + 4 + 4 + 4 = 16×` feature raw (before cap).

Empty collectors (no tokens) pay **0×** but still emit events.

---

## 7. Cap — 50,000× semantics

- Configured `maxWinX = 50000`.  
- Settlement: `totalWinX = min(lineWinX + featureWinX, maxWinX)`.  
- **`totalFeatureWinXRaw`** / **`totalWinXRaw`** may exceed the cap; the book records both raw and capped totals.  
- When clamped, emit **`skyjumpCapReached`** with `uncappedWinX`, `cappedWinX`, `maxWin`.  
- Cap applies once at end of feature resolution for the spin (Phase 4B has no Rejump re-evaluation).  
- All awards remain on **0.10×** book grain (integer `payoutMultiplier % 10 == 0`).

---

## 8. Scatter on Coach E strips

Scatter strips were **not** edited for Coach E. Only reels 2 and 4 were lengthened (frequency-preserving Coach placement). Exact convolution on live strips:

| Count | P(count) | 1 in N |
| ---: | ---: | ---: |
| 0 | 0.6204494745833965 | |
| 1 | 0.3108247851394578 | |
| 2 | 0.06219606202270772 | |
| 3 | 0.0062135906602437665 | |
| 4 | 0.00030991400836999946 | |
| 5+ | 6.173585824103574e-06 | |
| **3+** | **0.00652967825443787** | **153.15** |
| Perfect V | 1.9755474637131444e-09 | **~506,188,800** |

| Metric | Value |
| --- | ---: |
| Theoretical line RTP (Coach E) | **0.596961766439716** (~59.70%) |
| Provisional BASE feature RTP (F01 10M research) | **~11.822%** |
| BASE before FS (line + feature) | **~71.52%** |
| FS reserve toward 96.5% target | **~24.98 pp** |
| Implied average FS bonus (reserve ÷ P(3+)) | **~38.26×** |

**Note:** the ~**38.3×** implied average bonus was **confirmed correct** on Coach E strips — it is not a documentation arithmetic error. Earlier Phase 2 scatter rates (1 in 130.6 / ~380M Perfect V) applied to Phase 3 Coach A strips and are superseded for budget math by the Coach E table above.

Free Spins are **not started** in Phase 4B. Scatter events still use `trigger: null`.

---

## 9. Placeholder frontend animation flow

Production-quality FX is Phase 7. Phase 4B ships **DEV placeholder** handlers in `SkyJumpV2Board.svelte` driven strictly by book events:

1. **Board reveal** — sequential reel stop (turbo = shorter holds).  
2. **Line wins** — highlight paths from `skyjumpLineWins`.  
3. **Scatter** — badge count toast (no FS trigger yet).  
4. **Coach** — highlight Coach cell + transformed regulars → Mystery tiles.  
5. **Mystery resolve** — per cell: token face (`T1`–`T6` + `×` label, subtext “uncollected”) or special placeholder (`THERMAL`, `GATE`, `JUDGE`, `HEAD JUDGE`).  
6. **Gate** — flash Gate cell; apply `replacements[]` to board; show floor `T{n}→T{m}`.  
7. **Thermal** — show mult on Thermal cell; update neighbour token labels to **effective** value (face unchanged in reducer state).  
8. **Judge / Head Judge** — pulse collector + contributing tokens; increment running **feature win** meter; tokens stay visible.  
9. **Cap** — brief “MAX WIN” clamp toast when `skyjumpCapReached`.  
10. **Result** — `skyjumpResult` totals; HUD `setTotalWin`.

`/dev-preview` source **FEATURE SAMPLE** cycles fixtures `01`–`17` from `skyjump_v2_feature_samples.json`. Reducer + `validateEvents.ts` parity tests must pass before trusting animation.

---

## 10. FEATURE SAMPLE fixtures (DEV 01–17)

Non-production books in `math/games/0_0_poc/skyjump_v2_feature_samples.json`. Regenerate: `python math/games/0_0_poc/write_skyjump_v2_feature_samples.py`.

| ID | Title | Intent |
| ---: | --- | --- |
| 01 | One Flight Token, no collector | Latent token; `totalFeatureWinX = 0` |
| 02 | Multiple tokens, no collector | Several faces; still 0 feature pay |
| 03 | Judge with tokens | First paying collector |
| 04 | Judge with no token | Empty collector |
| 05 | Head Judge with tokens | Two-pass collect |
| 06 | Multiple Judges | Stacking on same tokens |
| 07 | Judge + Head Judge | Mixed collectors |
| 08 | Thermal affecting one token | Single neighbour lift |
| 09 | Thermal affecting multiple tokens | Shared Thermal |
| 10 | Token affected by two Thermals | Multiplicative product |
| 11 | Gate T1 → T2 replacement | Floor + math-owned upgrade |
| 12 | Two Gates reaching T3 | Sequential floor cap at 3 |
| 13 | Gate + Thermal + Judge | Combined chain |
| 14 | Multi-Coach + collector | Second Coach after first transform |
| 15 | Rare T4/T5 token collection | High-tier face collect |
| 16 | Synthetic T6 / 50,000× tail test | Tail face (may not cap alone) |
| 17 | Cap reached | Raw total > 50,000×; clamp event |

---

## 11. Post-promotion simulation metrics

Source: `math/games/0_0_poc/skyjump_v2_phase4b_sim_report.json`  
**10,000,000** BASE spins · seed **42** · live F01 config (non-production).

| Metric | Exact / analytical | Simulated |
| --- | ---: | ---: |
| Line RTP | **59.696%** | 59.753% |
| Feature RTP raw | — | **13.911%** |
| Feature RTP capped | — | **12.410%** |
| BASE before FS (line exact + feature capped) | — | **72.107%** |
| FS reserve (vs 96.5%) | — | **24.393 pp** |
| Implied avg FS bonus | — | **37.36×** |
| P(any Coach) | **8.160%** | 8.153% |
| P(2+ Coach) | **0.174%** | 0.172% |
| P(feature win) | — | 2.043% |
| P(feature win \| Coach) | — | **25.053%** |
| P(dead Coach) | — | **74.947%** |
| Cap frequency | — | **2e-7** (2 / 10M) |
| Cap drag / spin | — | 0.0150× |
| Max raw total | — | 200,010.2× |
| Max capped total | — | **50,000×** |

Dead Coach reasons (counts among dead Coach spins):

| Reason | Count |
| --- | ---: |
| tokens_no_collector | 581,133 |
| collector_no_tokens | 21,624 |
| modifier_only | 8,285 |

Feature-win size (among spins with feature win > 0): avg **6.08×**, median **4×**, P90 **10×**, P95 **14×**, P99 **24×**, P99.9 **70×**.

**Vs Phase 4A.2 research (~11.82% feature):** feel rates match (~25% / ~75%). Capped feature RTP on this seed sits ~0.6 pp higher than the research 10M point estimate because rare T6 + collector tails (including two cap hits) pull the mean; raw vs capped gap is almost entirely those tails. Planning FS budget should use **live exact Scatter + this measured capped feature** (implied bonus **~37.4×**), not the research-only 11.82% snapshot alone. Still provisional — not certified RTP.

---

## 12. Known remaining work

| Item | Status |
| --- | --- |
| Free Spins execution | **Not started** — scatter still audit-only |
| Provisional RTP | **Not certified** — no LUT / production books |
| Production books / Stake upload | **Not generated** |
| Rejump / Wind Key / Flight Multiplier | Design present; **not wired** in Phase 4B |
| Full feature animation + resume | Placeholder only (Phase 7) |
| Buy-mode costs | TBD |

---

## 13. Files touched in Phase 4B implementation

| Path | Role |
| --- | --- |
| `skyjump_v2_config.json` | F01 promotion, Coach E strips, paying tables |
| `skyjump_v2_features.py` / `skyjump_v2_paying.py` | Paying resolution path |
| `skyjump_v2_phase4a_economy.py` | Gate / Thermal / collector engine |
| `skyjump_v2_events.py` / `skyjump_v2_reducer.py` | Schema-2 events + replay |
| `skyjump_v2_feature_samples.json` | DEV fixtures 01–17 |
| `write_skyjump_v2_feature_samples.py` | Sample writer |
| `skyjump_v2_phase4b_simulate.py` | Verification sim (report JSON when run) |
| `tests/test_skyjump_v2_phase4b.py` | Parity + cap + scatter tests |
| `frontend/.../SkyJumpV2Board.svelte` | Placeholder animation handlers |
| `frontend/.../reducer.ts`, `validateEvents.ts`, `bookEventHandlerMap.ts` | FE replay |

```bash
cd math
python -m pytest tests/test_skyjump_v2_phase4b.py -q
python games/0_0_poc/write_skyjump_v2_feature_samples.py
```
