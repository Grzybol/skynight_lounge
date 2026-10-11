# SKYJUMP V2 — Phase 7A.1 Full-Round Economy Certification

**Status:** CERTIFICATION complete — PT2 class-hierarchy FAIL was the Phase 7B blocker. **Resolved in Phase 7A.2** (`25_PHASE7A2_PAYTABLE_REPAIR_AND_FINAL_ECONOMY.md`, paytable `PT2H_LADDER`, economy **H2**).
**Branch:** `feat/skyjump-v2-5x5`
**Live config:** **UNMODIFIED** (also unmodified in 7A.2)
**Artifacts:** `math/games/0_0_poc/phase7a1_research/`
**Art authority:** `23_SYMBOL_ASSET_MANIFEST.md` (APPROVED; WAIT = NONE)

Phase 7A candidate **C8 is superseded** for promotion by this measurement. Historical Phase 7A C8 research is retained. Do **not** promote historical PT2 — use **PT2H_LADDER** from 7A.2.

---

## 1. Live freeze

| Field | Value |
| --- | --- |
| Config SHA-256 | `1a737f24ff3b75ceebb80b276e4fa23dde076699d2cfc7ac8e9a6f7fbcc7b8fe` |
| BASE | 71.212% |
| Phase 5B | +17.92705 pp |
| Phase 6 PURE W2 | +4.689 pp (SE 0.078) |
| **Current game RTP** | **93.828%** |
| Phase 6 | FROZEN (`W2_PURE` + `W-CHARGE`, R-BATCH) |
| Paytable / tokens | Live provisional (PT0 / BODY0) |

No live values mutated.

---

## 2. Art lock

**PASS.** Symbol roster frozen per doc 23. Economy results do not rename any production symbol. `SPECIAL_WORLD_RECORD` identity remains valid. Art production may proceed independently.

**WAIT:** NONE

---

## 3. Artifact validation (from `phase7a_research/`)

| Check | Result |
| --- | --- |
| PT2 monotonic 3≤4≤5 | **PASS** |
| PT2 0.10× grain | **PASS** |
| PT2 class hierarchy P1≥…≥L3 at same match | **FAIL** |
| BODY1 T5/T6 unchanged | **PASS** (only T1/T2 face + T1→T2 weight −40/+40) |
| WR-C ratio LH:SF:WC:PV | **PASS** 1:3:6:12 |

### Hierarchy breaks (STOP — do not silently repair in 7A.1)

| Match | Violation |
| --- | --- |
| 4OAK | **M1 3.3 < M2 6.1** |
| 4OAK | **M1 3.3 < M3 5.8** |

Cause: Phase 7A mid-4/5 RTP recovery raised M2/M3 4oak while M1 4oak stayed at live 3.3.

---

## 4. PT2 full-game decomposition

Exact BASE (Coach E strips):

| | Line RTP |
| --- | ---: |
| PT0 | 59.6961766439716% |
| PT2 | 60.28839016193175% |
| **BASE Δ** | **+0.592213517960154 pp** |

Paired 1,000,000 triggered bonuses (Phase 6C.1, BODY0, common RNG; seed `7701000000`):

| Component | Δ pp | SE pp |
| --- | ---: | ---: |
| FS initial-board lines | **+0.05561** | (in bonus SE) |
| Rejump lines | **−0.00064** | ≈0 |
| Bonus non-line residual | ~0 | — |
| **Bonus total PT2 Δ** | **+0.05498** | **0.00177** |
| **TOTAL full-game PT2 Δ** | **+0.64719** | — |

**Do not use Phase 7A’s +0.592 as the full-game PT2 delta.** Full-game ≈ BASE +0.592 + bonus lines ≈ **+0.647 pp**.

---

## 5. BODY1 live interaction (1M paired)

| Contrast | Δ pp | SE pp |
| --- | ---: | ---: |
| BODY1 standalone (PT0) | **+1.36801** | 0.01164 |
| PT2 standalone (BODY0) | **+0.05498** | 0.00177 |
| PT2+BODY1 combo vs PT0+BODY0 | **+1.42298** | 0.01178 |
| Interaction (combo − BODY1 − PT2) | **≈ −0.000008** | — |

Phase 7A BODY1 reference +1.359 reconciled at **+1.368** (different seed / instrumented path; ~0.009 pp).

**Additivity:** PASS (interaction negligible).

### Feel (PT0 BODY0 → PT0 BODY1)

| Metric | BODY0 | BODY1 |
| --- | ---: | ---: |
| Median | 9.5 | **9.7** |
| P25 | 5.5 | 5.5 |
| P75 | 19.2 | **20.1** |
| P90 | 45.1 | 48.8 |
| P95 | 105.6 | 115.3 |
| P99 | 431.5 | 470.5 |
| P99.9 | 2180 | 2257 |
| P(&lt;5×) | 0.213 | 0.212 |
| P(&lt;10×) | 0.518 | 0.511 |
| Cap p | 1.1e-5 | 1.1e-5 |
| Mean cap drag × | 1.672 | 1.672 |

### Phase 6 visibility

| | BODY0 | BODY1 |
| --- | ---: | ---: |
| P(Rejump) | 0.166628 | 0.166629 |
| P(Wind) | 0.076475 | 0.076476 |
| P(any Phase6) | 0.197528 | 0.197529 |

**Visibility preserved: PASS**

---

## 6. World Record — exact incremental fill

Opportunity = every Free Spin **start** (board generated; before line eval). Accrued = bonus win so far (BASE prior ≈ **0.43×** on scatter≥3 — negligible vs 50k).

| Quantity | Value |
| --- | ---: |
| E[accrued bonus \| WR-weighted opp] | 36.379× |
| E[incremental fill] (bonus only) | **49963.621×** |
| E[fill] with BASE prior approx | **49963.192×** |
| Fill mass / bonus (Σ rel·fill) | 666425.22 |
| Mean FS ops / bonus | 10.433 |

Tier intensity ratio frozen: **1 : 3 : 6 : 12**.

### Canonical WR timing (freeze for 7B)

1. Math generates the Free Spin **initial board** (stops → symbols).
2. **Independent WR-C Bernoulli** runs using current bonus tier intensity (`c × rel[tier]`).
3. **Non-trigger:** board unchanged → line / Scatter / Coach probabilities identical to today.
4. **Trigger:** place `SPECIAL_WORLD_RECORD` at math-owned display position → emit `skyjumpWorldRecord` → fill economic round to 50,000× → terminate FS / Rejump / feature chain → **one** settlement.

**Chosen interpretation:** WR trial occurs **after initial board generation and before line evaluation** (phase 1b). Not a Mystery outcome; does not mutate reel strips.

### Display position (math-owned)

When WR triggers:

1. Prefer cell **(reel=2, row=2)** (0-based center) if it is **not** Scatter.
2. Else first cell in reel-major order `(reel 0..4, row 0..4)` that is not Scatter.
3. Overlay/replace that cell with `SPECIAL_WORLD_RECORD` in the book; record `position: {reel, row}` on `skyjumpWorldRecord`.
4. No frontend RNG. Scatter count remains the **pre-overlay** initial reveal.

---

## 7. Core RTP without WR

```
93.828
+ 0.59221   (exact BASE PT2)
+ 1.42298   (paired PT2+BODY1 bonus combo)
= 95.84319%
```

Simulated-overlay SE ≈ hypot(0.078 Phase6, 0.0118 combo) ≈ **0.0789 pp**.

---

## 8. Candidates (full PT2 + BODY1 + exact WR fill)

| ID | WR pp | Projected | Point reserve | Safe reserve | Band 96.25–96.35 |
| --- | ---: | ---: | ---: | ---: | --- |
| **C2** | 0.45 | **96.293%** | 0.207 | **0.052** | YES |
| C3 | 0.50 | 96.343% | 0.157 | 0.002 | YES |
| C8 | 0.55 | 96.393% | 0.107 | **−0.048** | NO |
| **CFINAL_SOLVED** | **0.457** | **96.300%** | 0.200 | 0.045 | YES |

Phase 7A additive C8 overstated headroom by omitting ~+0.055 pp bonus-line PT2. Full-round C8 safe reserve is **negative**.

### CFINAL_SOLVED WR scale (target 96.30%)

| | |
| --- | ---: |
| WR RTP contribution | **0.45681 pp** |
| Paid-round p | **9.14e-8** |
| 1 in N paid | **~10.94M** |
| P(WR \| bonus) | **~1.40e-5** |
| 1 in bonuses | **~71.4k** |

P(WR \| bonus starts …) approx:

| Start | CFINAL 1-in |
| --- | ---: |
| Large Hill | ~77.5k |
| Ski Flying | ~28.2k |
| World Cup | ~13.5k |
| Perfect V (forced 5k) | ~7.6k |

---

## 9. Cap / tail

| Path | Value |
| --- | ---: |
| Natural feature cap p | **1.1e-5** |
| Mean cap drag (excl. WR) | **1.672×** / bonus |
| World Record | = WR paid-round frequency |
| Combined | natural ∪ WR (no double settle) |
| WR fill loss vs 50k | E[accrued] ≈ 36.8× |

---

## 10. Recommendation

Math preference after full-round cert: **C2** (safe reserve ≥ 0.05 in preferred band).

**CFINAL_SOLVED** is the calibrated 96.30% WR scale if human accepts safe **0.045**.

**Phase 7B blocked** until PT2 class hierarchy is repaired in a follow-up research pass (do not silently edit awards in 7A.1). Art lock stays valid.

**C8:** superseded — do not promote.

---

## 11. READY FOR PHASE 7B?

**NO** at time of 7A.1 — hierarchy FAIL.

**Update (7A.2):** hierarchy repaired; see doc **25**. Phase 7B may proceed on **PT2H_LADDER** + **H2**.

Historical blockers at 7A.1 close:

1. **PAYTABLE CLASS HIERARCHY FAIL** (M1 4oak &lt; M2/M3 4oak).
2. Optional: hierarchy-fixed PT2′ then re-solve CFINAL / confirm C2.

Not blockers then or now: BODY1 visibility, WR architecture, art lock, live config freeze.
