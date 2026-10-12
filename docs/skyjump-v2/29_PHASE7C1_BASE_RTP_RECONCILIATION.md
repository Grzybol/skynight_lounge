# SKYJUMP V2 — Phase 7C.1 BASE RTP / LUT Reconciliation

**Status:** COMPLETE (diagnostic) — **acceptance gate FAIL** — **READY FOR HUMAN RETUNE DECISION: NO**  
**Branch:** `feat/skyjump-v2-5x5`  
**Live economy modified:** **NO**  
**mathVersion:** **1** (unchanged)  
**Artifacts:** `math/games/0_0_poc/phase7c1_research/` (Phase 7C files not overwritten)

---

## 0. Freeze

| Item | Value |
| --- | --- |
| Config SHA | `d6879d5c…2edbd0` **MATCH** |
| Phase 7C books/LUTs/reports | snapshotted hashes in `freeze_snapshot.json` |
| Buy costs | provisional LH 32.5 / SF 197.7 / WC 416.7 / PV 1381.2 — **unchanged** |

---

## 1. Four estimators (side-by-side)

| Estimator | RTP % | Notes |
| --- | ---: | --- |
| **A. Historical staged projection** | **96.290** | `93.828 + PT2HΔ0.666 + BODY1Δ1.339 → core 95.833 + WR 0.457` |
| **B. Direct natural full-round MC** | **98.43** | 5×40k seeds; 95% CI **[91.4, 105.4]** (unstable tails) |
| **C. Stratified (corrected hybrid)** | **97.641** | `p_none·eNone + p·E[triggerBase] + Σp_tier·buyNaturalFS + WR` |
| **D. Current production BASE LUT** | **98.120** | Weighted books |

Exclusive lines+features+FS+WR (features from non-trigger MC only): **96.928%** (slight feature undercount on trigger spins).

---

## 2. Decomposition (corrected hybrid — exclusive)

| Bucket | pp |
| --- | ---: |
| Non-bonus mass (`p_none · eNone`) | 72.169 |
| Trigger-spin BASE (lines+features on scatter triggers) | 0.276 |
| Natural bonus FS body (`Σ p_tier · buy meanNaturalX`) | 24.739 |
| World Record H2 | 0.457 |
| **TOTAL** | **97.641** |

Cap drag on BASE non-trigger features: **~0** (P(cap)=0 in 80k). Shared full-round cap is inside FS/WR means.

---

## 3. Line anchor

Exact PT2H + Coach-E: **60.29946%** — **PASS** (all estimators that use exact lines agree).

---

## 4. BASE features (live BODY1)

| Metric | Value |
| --- | ---: |
| Method | Rejection non-trigger `resolve_v2_base` (n=80k) |
| Feature RTP raw ≈ capped | **11.433%** |
| SE | **0.414 pp** |
| P(cap) | 0 |
| Non-bonus total (lines+features \| no trigger) | 70.845% |

Full NO_T4PLUS/T4/T5/T6 importance pack not re-run end-to-end; bulk estimate is the live BODY1 feature bucket for this phase. Uncertainty ~0.4 pp on features.

---

## 5. Natural start mix (exact)

| Start | Absolute p | Conditional |
| --- | ---: | ---: |
| LARGE_HILL (exact 3) | 0.00621359 | 0.95159 |
| SKI_FLYING (exact 4) | 0.00030991 | 0.04746 |
| WORLD_CUP (5+ non-PV) | 6.172e-6 | 0.000945 |
| PERFECT_V | 1.976e-9 | 3.03e-7 |
| P(scatter≥3) | 0.00652968 | — |

Matches Phase 5 `base_trigger_mix` / LUT theoretical targets (except Perfect V **weight floor** — below).

---

## 6–7. Buy vs natural bonus / shared cap prior

Buy = direct-start FS (prior 0). Natural forced-trigger rounds carry `triggerSpinWinX` into the shared cap.

| Effect | Estimate |
| --- | --- |
| Mean E[triggerBase \| trigger] (2k natural hits) | **0.423×** |
| Paid-round trigger-base contribution | **+0.276 pp** |
| Forced-stop prior/cap study | noisy (fixed boards; SF/PV priors 0) — treat as qualitative |

**Do not double-count** trigger payout into FS: it belongs in BASE line/feature / trigger-base bucket.

---

## 8. WR double-count audit

| Question | Answer |
| --- | --- |
| Independent hybrid | **B** — uses `meanNaturalX` (WR-off) + separate WR fill |
| Extra WR if `meanX`+WR again | +0.394 pp (not what 7C did) |
| H2 contribution | **0.457 pp** (not ~0.914) |

---

## 9. Phase 5/6 double-count audit

| Question | Answer |
| --- | --- |
| Hybrid mixes staged 5B+6 **and** final bonus EV? | **NO** |
| Hybrid uses final live buy FS EV only | **YES** |
| Historical 96.29 uses staged 5B+6 buckets | **YES** (different estimator) |

---

## 10–13. BASE LUT strata (actual writer categories)

| Stratum | Books | Norm p | Theory p | Mean X | RTP contrib |
| --- | ---: | ---: | ---: | ---: | ---: |
| basegame | 100,000 | 0.993470 | 0.993470 | 0.7264 | 0.7217 |
| freegame_LARGE_HILL | 40,000 | 0.006214 | 0.006214 | 31.144 | 0.1935 |
| freegame_SKI_FLYING | 25,000 | 0.000310 | 0.000310 | 190.25 | 0.0590 |
| freegame_WORLD_CUP | 20,000 | 6.18e-6 | 6.17e-6 | 394.81 | 0.0024 |
| freegame_PERFECT_V | 15,000 | **1.50e-8** | **1.98e-9** | 1316.6 | ~2e-5 |
| world_record | 20 | 9.146e-8 | 9.145e-8 | 50000 | 0.00457 |

- **Partition:** mutually exclusive criteria; Σp = 1 — **PASS**  
- **No T4/T5/T6 overlay strata** in writer (those are not BASE LUT categories)  
- **Stratum recon = LUT RTP** — **PASS**  
- **Perfect V:** `max(1, round(W·p/n))` floors → **~7.6× overweight** (~0.002 pp RTP) — writer defect, small

**Bonus source:** `freegame_*` = slices of **buy-mode books** (not random natural triggers).

---

## 14. WR LUT weight

Target 9.145e-8 vs effective 9.146e-8 — **PASS**

---

## 15–16. MC vs stratified

Natural multi-seed mean 98.43% with CI width ~14 pp — stratified **97.64%** lies inside CI. Do not demand ±0.10 pp from naive MC.

---

## 17. Buy LUT audit (provisional costs kept)

| Mode | LUT mean X | buy_ev natural | Δ X | Δ % |
| --- | ---: | ---: | ---: | ---: |
| LH | 31.362 | 30.060 | +1.30 | +4.3% |
| SF | 190.76 | 187.61 | +3.15 | +1.7% |
| WC | 402.10 | 398.61 | +3.49 | +0.9% |
| PV | 1332.83 | 1304.72 | +28.1 | +2.2% |

Buy LUTs priced to ~96.50% **from their own means** — internally consistent, but means run hot vs 200k EV. Costs remain **PROVISIONAL**.

---

## 18. LUT vs hybrid gap (~0.75 pp) — explained

| Bucket | Gap pp |
| --- | ---: |
| freegame_LARGE_HILL mean slice vs 200k EV | **+0.674** |
| freegame_SKI_FLYING | +0.082 |
| other | ~0 |
| **Sum** | **~0.753** ≈ reported 0.755 |

Plus hybrid missing trigger-base (**+0.276 pp** when restored) → corrected hybrid **97.641** vs LUT **98.120** → residual gap **0.479 pp**.

---

## 19. Acceptance gate

`|LUT − corrected stratified| = 0.479 pp` ≰ 0.10 — **FAIL**

---

## 20–21. If economy hot (report only — not applied)

After reconciliation, authoritative band **~97.6–98.1%** still **>96.70**.

Required reduction to ~96.50: **~1.14–1.62 pp**.

| Candidate | Idea | Sufficient alone? |
| --- | --- | --- |
| **TUNE_A** | WR → 0 (max −0.457 pp) | **NO** (still ~97.2) |
| **TUNE_B** | WR ~0.10pp + BODY1 partial rollback | YES (design) |
| **TUNE_C** | WR ~0.30pp + small PT2H trim + tiny BODY | YES (design) |

**Do not promote.**

---

## Root cause (concise)

**MULTIPLE CAUSES:** (1) 7C hybrid undercount (missed trigger-base); (2) BASE LUT freegame means from hot buy-book slices vs long-run EV; (3) tiny PV weight-floor bug; (4) historical 96.29 understates live absolute; (5) live economy likely still above ceiling once means are fixed.

---

## Classification

**MULTIPLE CAUSES**

## Ready for human retune decision?

**NO**

### Blockers

1. Close LUT↔stratified gap to ≤0.10 pp (regen BASE freegame strata to long-run means / fix weight floor).  
2. Re-quote authoritative BASE RTP after that regen.  
3. Only then size TUNE_B/C against the reconciled number.

Do not retune / bump mathVersion / publish / push from this phase.
