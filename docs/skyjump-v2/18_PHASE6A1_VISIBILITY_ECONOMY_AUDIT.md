# SKYJUMP V2 — Phase 6A.1 Feature Visibility / EV Decoupling

**Status:** RESEARCH / DESIGN ONLY. Not implemented in the live resolver.  
**Branch:** `feat/skyjump-v2-5x5`  
**Phase 6A:** mathematically valid. F1 stays the frozen **BENCHMARK**, not promoted.  
**Live BASE / Phase 5B Free Spins / Phase 6A research artifacts:** unchanged.  
**Recommended candidate:** `P6A1_E_E1` (R-BATCH + W-CHARGE, pack E1)  
**Ready for a human Phase 6B decision:** yes, with the architecture note in section 12.

This pass does not add Rejump or Wind Key to paid BASE spins, does not retune BASE F01, does not change live Free Spin models, does not generate production books or LUTs, and does not implement Phase 6B.

---

## 1. Why 6A.1

Phase 6A candidate F1 is economically healthy (+5.307 pp, new game ~94.446%, reserve ~2.054 pp, acceptable cap and book size) but player-visible Phase 6 events are rare on the common bonus:

| Large Hill (F1) | Rate |
| --- | ---: |
| P(any Rejump) | ~7.9% |
| P(any Wind Key) | ~1.4% |
| Median bonus | 9.6× (same as Phase 5B) |

Phase 6 mostly enriches the right tail (P90 43.8→46.0, P99 294→448). Rejump / Wind Key were meant for gameplay depth. 6A.1 tests whether architecture changes can raise visibility while keeping roughly the same 4.5–5.5 pp budget.

---

## 2. Documentation correction (Phase 6A)

In `17_PHASE6A_REJUMP_WIND_ECONOMY_AUDIT.md`:

- **Rejump is the larger standalone incremental contributor** at F1 (Rejump-only ~3.023 pp vs Wind-only ~1.998 pp). Underlying counterfactual numbers are unchanged.
- The **2× ending bin ~3.82 pp** is **total collector RTP inside that selected bin**, not the incremental RTP caused solely by Wind Key.

---

## 3. Architectures

### 3.1 Rejump

| Id | Behaviour |
| --- | --- |
| **R-DELAYED** (F1) | All collectors wait until the full Rejump chain ends. Early Judges collect tokens created by later redrops. |
| **R-BATCH** | Per Mystery batch: Gate → Wind → Thermal → **collectors settle once** → optional redrop. Flight Tokens stay. Spent collectors keep the visual cell but `payoutSpent` / `paid` blocks re-fire. Later collectors may recollect preserved tokens. |

Hard limits unchanged: max 2 Rejumps / Free Spin, chain depth 8. Rejump remains a real redrop with new lines, persist, Coach, and Mysteries.

### 3.2 Wind

| Id | Behaviour |
| --- | --- |
| **W-IMMEDIATE** (F1) | Key upgrades active stages; collectors on the same Free Spin use the new product. |
| **W-NEXT-SPIN** | Key upgrades `pending*`; collectors use start-of-spin **active** product. Pending activates at next Free Spin start. Keys found during Rejump still wait for the next Free Spin. |
| **W-CHARGE** | Two Keys required per K1 stage step (charge 0→1, then stage 1→2). Integer multipliers only. W2 lowest-stage selection. |

Default ladder / rules unless noted: **K1**, **W2**, saturation **B**, **PV1**.

### 3.3 Correlation diagnoses (unchanged from brief)

1. **R-DELAYED:** early collectors wait for the whole chain → large amplification when Rejump is rare.
2. **W-IMMEDIATE:** Keys arise on Mystery-heavy boards already rich in tokens/collectors; same-spin multiply is expensive.

---

## 4. Method

Research-only engine: `skyjump_v2_phase6a1_engine.py`.  
Screens: `skyjump_v2_phase6a1_search.py` + micro packs.  
Large runs: seed `20260923` unless noted. Trigger mix = exact BASE `P(Scatter ≥ 3)`. Incremental vs certified Phase 5B mean **27.45472×**.

Architecture controls at **F1 Mystery weights** (screen n=10k, seed 702; direction confirmed by 500k reserve run):

| Control | Inc (screen) | Notes |
| --- | ---: | --- |
| A F1 R-DELAYED + W-IMM | ~5.22 | matches large 5.307 on seed 20260923 |
| R-BATCH + W-IMM | ~3.79 | ~1.4 pp savings |
| R-DELAYED + W-NEXT | ~4.54 | ~0.7 pp savings |
| R-BATCH + W-NEXT | ~3.21 | ~2.0 pp savings |
| R-BATCH + W-CHARGE | ~1.48 | charge halves effective key power |

Headroom is real. Spending it on higher Mystery weights is the search.

---

## 5. Finalists

At least six meaningful finalists. Top two at ≥1,000,000 mix bonuses.

| Id | Arch | Pack (LH RJ,WK) | n | Inc pp | Reserve | Mix P(RJ) | Mix P(WK) | Mix any P6 | LH RJ / WK / any | Med | P90 | P99 | Cap freq |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| **A F1** | R-DELAYED + W-IMM | (10,1) | 1M | **5.307** | 2.054 | 0.096 | 0.019 | 0.105 | 0.079 / 0.015 / 0.087 | 9.6 | 46.0 | 448 | 1.5e-5 |
| **B B1** | R-BATCH + W-IMM | (18,1) | 1M | **5.302** | 2.059 | 0.145 | 0.020 | 0.152 | 0.124 / 0.015 / 0.130 | 9.6 | 46.2 | 447 | 1.9e-5 |
| **C C_LH2** | R-DELAYED + W-NEXT | (10,2)* | 500k | **4.754** | 2.607 | 0.097 | 0.024 | 0.110 | 0.080 / 0.019 / 0.091 | 9.6 | 45.6 | 434 | 1.6e-5 |
| **D D_B1_WNEXT** | R-BATCH + W-NEXT | (18,1) | 500k | **4.959** | 2.402 | 0.145 | 0.020 | 0.152 | 0.125 / 0.015 / 0.131 | 9.5 | 45.7 | 435 | 2.4e-5 |
| **E E1** | R-BATCH + W-CHARGE | (22,6) | 1M | **5.195** | 2.166 | 0.166 | 0.077 | 0.197 | **0.145 / 0.060 / 0.173** | 9.5 | 45.5 | 441 | 1.6e-5 |
| **R reserve** | R-BATCH + W-NEXT | F1 (10,1) | 500k | **3.376** | **3.985** | 0.096 | 0.019 | 0.106 | (≈F1 rates) | 9.5 | 45.0 | 389 | 1.6e-5 |

\*C_LH2 only bumps Large Hill Wind to 2; SF/WC/PV stay at F1 wind weights.

Also measured (over band or under-visible): B23 (+6.54), D17_3 (+7.87), E25_9 (+7.71), E05 (+4.73, strong visibility alternate), D_RJ14 (+4.16, under preferred band).

---

## 6. Recommended

**`P6A1_E_E1`** — R-BATCH + W-CHARGE, pack E1:

| Tier | REJUMP | WIND_KEY |
| --- | ---: | ---: |
| LARGE_HILL | 22 | 6 |
| SKI_FLYING | 36 | 14 |
| WORLD_CUP | 48 | 22 |
| PERFECT_V | 60 | 30 |

| Metric | E1 | F1 benchmark |
| --- | ---: | ---: |
| Incremental RTP | 5.195 pp | 5.307 pp |
| New game RTP | 94.334% | 94.446% |
| Future reserve | 2.166 pp | 2.054 pp |
| LH P(Rejump) | **14.5%** | 7.9% |
| LH P(Wind) | **6.0%** | 1.5% |
| LH P(any Phase 6) | **17.3%** | 8.7% |
| LH P(both) | 3.1% | ~0.7% |
| Mix P(Rejump) | 16.6% | 9.6% |
| Mix P(Wind) | 7.7% | 1.9% |
| Mix P(any Phase 6) | 19.7% | 10.5% |
| Mix P(both) | 4.6% | 1.0% |

### Why W-CHARGE (and when not to)

W-NEXT-SPIN alone does **not** buy Large Hill Wind into the 5–10% band inside 4.5–5.5 pp. Raising Wind weights under R-DELAYED + W-NEXT (C family) or R-BATCH + W-NEXT with Wind ≥2 (D0+) overshoots RTP at large N. Charge lets Keys appear often while each Key is only half a stage step — visibility without full same-spin EV blow-up.

If the team rejects charge as too many UI states, fall back to **B1** (R-BATCH + W-IMMEDIATE): same RTP band, LH Rejump ~12.4%, Wind still ~1.5%. That is cleaner math/UI but fails the Wind visibility preference.

---

## 7. Bonus distribution (mix)

| Candidate | P25 | Med | P75 | P90 | P95 | P99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Phase 5B certified | — | 9.6 | — | 43.8 | — | 294.5 |
| F1 | 5.5 | 9.6 | 19.4 | 46.0 | 107.8 | 448 |
| B1 | 5.5 | 9.6 | 19.4 | 46.2 | 110.3 | 447 |
| C_LH2 | 5.5 | 9.6 | 19.3 | 45.6 | 106.0 | 434 |
| D_B1_WNEXT | 5.5 | 9.5 | 19.3 | 45.7 | 108.2 | 435 |
| E1 | 5.5 | 9.5 | 19.2 | 45.5 | 108.8 | 441 |

Median barely moves. Visibility gains are event rates, not a thicker body.

### Material change vs Phase 5B blank (paired same seed)

Definition: `P(candidate − blank ≥ 5×)` on the same RNG stream (blank = research Phase 5B proxy, Mystery (0,0) Rejump/Wind).

| Candidate | n paired | P(Δ ≥ 5×) | Mean Δ |
| --- | ---: | ---: | ---: |
| F1 | 50k | 0.111 | 9.15× |
| B1 | 50k | 0.137 | 7.28× |
| E1 | 100k | **0.154** | 8.84× |

E1 materially changes ~15% of bonuses by ≥5× versus blank; F1 ~11%.

---

## 8. Rejump value decomposition (R-BATCH)

Under R-BATCH, Rejump EV is separable into lines + post-redrop collectors + recollection of preserved tokens.

| Piece (E1, 1M) | Mean × / bonus | pp |
| --- | ---: | ---: |
| Rejump line wins | 0.064 | 0.042 |
| Collectors after Rejump | 6.27 | 4.09 |
| of which recollection of pre-redrop tokens | 4.31 | 2.82 |
| Initial-batch collectors (pre-redrop settle) | 24.40 | — |

Compare F1: almost all Rejump EV was delayed feature amplification (counterfactual Rejump-only ~3.02 pp) with lines ~0.02 pp. R-BATCH moves amplification into **later-batch collectors** and **recollection**, with clearer causality: an early Judge cannot collect tokens that did not exist when it settled.

B1 (1M): line Rejump 0.035 pp; collector-after-RJ 3.53 pp; recollection 2.41 pp.

---

## 9. Wind value decomposition

### W-NEXT-SPIN (C_LH2 / D_B1_WNEXT)

| Metric | C_LH2 | D_B1_WNEXT |
| --- | ---: | ---: |
| P(bonus ends with pending unused) | 0.0032 | 0.0030 |
| Mean Keys with future Free Spin | 0.024 | (similar order) |
| Mean Keys on final FS | 0.003 | 0.003 |
| Mean spins after first Key | 0.107 | 0.087 |
| P(ending mult ≥ 2) | 0.021 | 0.018 |
| P(≥ 4) | 0.0017 | 0.0018 |
| P(≥ 8) | — | 0.0003 |
| Mean active mult (spin-start history) | 1.010 | 1.008 |

Pending-unused rate is **~0.3%** of bonuses — small. No automatic “final-spin activate pending” exception is recommended.

Collector RTP by **active** multiplier (E1 uses charge so P(≥2) is lower than Key rate):

| Active product | E1 collector RTP | F1 collector RTP |
| --- | ---: | ---: |
| 1× | 16.42 pp | 15.57 pp |
| 2× | 2.20 | 3.26 |
| 4× | 0.62 | 0.85 |
| 8× | 0.54 | 0.22 |
| 12× | 0.10 | 0.06 |
| 18× | 0.06 | 0.03 |
| 27× | 0.07 | 0.05 |

Charge shifts mass: more Keys, fewer completed stage steps, softer 2× selection pile than F1’s immediate first Key.

---

## 10. Cap and forced tails

| Candidate | Cap frequency | Mean cap drag (×) |
| --- | ---: | ---: |
| F1 | 15 / 1M | 1.18 |
| B1 | 19 / 1M | 1.38 |
| E1 | 16 / 1M | 1.37 |
| D_B1_WNEXT | 12 / 500k | 2.36 |

No new cap regime versus F1. Hot Perfect V / World Cup tier slices (80k each) raise absolute means as expected; E1 Perfect V cap rate ~0.0007 vs F1 ~0.0008 on that slice.

Forced analytic cases (scale 1.5, round cap 50,000×) match Phase 6A: T6 + Head Judge + high flight still drags hard; R-BATCH does not remove that pathology — it only prevents an **early** Judge from also collecting post-redrop tokens in the same settle.

---

## 11. Book size

| Candidate | Mean events | P99 events | P99 est. bytes |
| --- | ---: | ---: | ---: |
| F1 | 102.0 | 249 | ~73k |
| B1 | 103.2 | 264 | ~80k |
| E1 | 103.7 | 272 | ~83k |
| D_B1_WNEXT | 103.2 | 264 | ~80k |

Modest growth from more Rejumps / collector timing events. Acceptable.

---

## 12. Player-feel scoring and decision

Priority this pass: **visibility**.

| Score | E1 | B1 | D_B1 | C_LH2 | F1 |
| --- | :---: | :---: | :---: | :---: | :---: |
| RTP 4.5–5.5 | ✓ | ✓ | ✓ | ✓ | ✓ |
| Reserve ≥1.8 | ✓ | ✓ | ✓ | ✓ | ✓ |
| LH Rejump ≥15% | ~14.5 (near) | 12.4 | 12.5 | 8.0 | 7.9 |
| LH Wind ≥5% | ✓ 6.0 | ✗ | ✗ | ✗ | ✗ |
| Weighted any Phase 6 | best | good | good | weak | weak |
| Median / P90 body move | weak | weak | weak | weak | weak |
| Cap / book | ✓ | ✓ | ✓ | ✓ | ✓ |
| Cause/effect clarity | R-BATCH yes; charge adds UI | R-BATCH yes | R-BATCH + pending | pending only | delayed collectors |

**Recommendation:** approve **E1** for Phase 6B implementation planning, accepting W-CHARGE as the visibility tool that fits the budget. Fallback **B1** if charge is rejected.

**Do not** expect the typical bonus median to leave 9.5–9.6×; Phase 6 remains a feature-rate and right-tail layer unless a later phase spends budget on the body.

---

## 13. Live game

**LIVE CONFIG MODIFIED: NO**

No frontend handlers. No production books. No LUT. Phase 6A F1 research files untouched except the wording correction in doc 17.

---

## 14. Artifacts

| Path | Role |
| --- | --- |
| `math/games/0_0_poc/skyjump_v2_phase6a1_engine.py` | R-BATCH / W-NEXT / W-CHARGE research engine |
| `math/games/0_0_poc/skyjump_v2_phase6a1_search.py` | Screen + packs |
| `math/games/0_0_poc/skyjump_v2_phase6a1_large.py` | Large finalist runner |
| `math/games/0_0_poc/skyjump_v2_phase6a1_final.py` | Certified-seed final confirm |
| `math/games/0_0_poc/skyjump_v2_phase6a1_forced_tails.py` | Analytic forced tails |
| `math/games/0_0_poc/test_skyjump_v2_phase6a1.py` | Structural tests |
| `math/games/0_0_poc/phase6a1_research/` | Screens, large JSONL, forced tails |

---

## 15. Next step (human)

Phase 6B candidate freeze for E1 (or B1 fallback): implement Rejump + Wind in the live Free Spin resolver, events, and UI — only after explicit human approval. Do not generate production books until that freeze.
