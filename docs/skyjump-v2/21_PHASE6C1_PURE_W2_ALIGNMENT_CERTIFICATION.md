# SKYJUMP V2 — Phase 6C.1 PURE W2 Alignment Certification

**Status:** COMPLETE — live Wind stage selection aligned to approved E1 **PURE W2**.
**Branch:** `feat/skyjump-v2-5x5`
**Candidate:** `P6A1_E_E1` (weights unchanged)
**Live rule:** `W-CHARGE` + **`W2_PURE`** (no charged-stage priority)
**Artifacts:** `math/games/0_0_poc/phase6c1_research/`
**Freeze SHA-256:** `1a737f24ff3b75ceebb80b276e4fa23dde076699d2cfc7ac8e9a6f7fbcc7b8fe`

---

## 1. Human decision

Phase 6C showed live **charged-stage priority** vs research **pure W2** as the primary research→live gap (~+1.44 pp on matched streams).

**Decision:** remove charged-stage priority from live payout authority. Align live selection to approved Phase 6A.1 E1 research semantic:

> Eligible = `value < 3`. Pick uniformly among stages with the lowest value. Ignore charge when selecting. Then apply W-CHARGE on the chosen stage.

This is **not** a weight retune.

---

## 2. Live Wind rule (canonical)

Each stage: `{value: 1|2|3, charge: 0|1}`.

For every `WIND_KEY`:

1. Eligible stages: `value < 3`
2. Among eligible, take the lowest value; RNG uniform among ties
3. Charge ignored for selection / priority
4. Apply key:
   - `charge==0` → `CHARGE` (charge→1, value unchanged)
   - `charge==1` → `UPGRADE` (charge→0, value+1)
5. Value-3 stages are saturated (ineligible)
6. Saturation B: all three at value 3 → remove `WIND_KEY` from Mystery pool

Multiple partial charges may coexist. Global = product of stage values only.

Historical `choose_stage_charge_priority` remains for audit/counterfactual only (`set_stage_selection_mode("W2_CHARGE_PRIORITY")`).

---

## 3. Research / live picker parity

Deterministic state + RNG draw parity between:

- research `choose_stage_a1` (W2 + W-CHARGE)
- live `choose_stage_pure_w2`

**16,000 trials — 0 mismatches — PASS.**

---

## 4. Persistent-target timing (secondary)

| | Semantic |
| --- | --- |
| Research | Append Coach selections to `persistentMysteryTargets` immediately (incl. after Rejump coaches) |
| Live | Append after full spin feature resolve; mid-chain Rejump uses pre-spin targets |
| Canonical | Phase 5B/6: persist after lines on a board; mid-chain list growth not required to match research |

**Action: KEEP_LIVE.**

100k paired counterfactual (mid-spin append ON vs OFF): research-style append is **~+0.42 pp hotter**. Do not change live to chase research.

---

## 5. Paired certification (main estimator)

Common random numbers. Spaced seeds (`stride ≥ 1.1M`) so `Random(seed+i)` streams do not overlap.

| Seed | n | OFF mean X | ON mean X | Incremental pp |
| ---: | ---: | ---: | ---: | ---: |
| 7026092700 | 500,000 | 27.242 | 34.720 | 4.883 |
| 7027192700 | 500,000 | 27.582 | 34.424 | 4.468 |
| 7028292700 | 500,000 | 27.744 | 34.409 | 4.352 |
| 7029392700 | 500,000 | 27.505 | 34.847 | 4.794 |
| 7030492700 | 500,000 | 27.395 | 35.017 | 4.977 |
| 7031592700 | 500,000 | 27.433 | 34.932 | 4.896 |
| 7032692700 | 500,000 | 28.193 | 34.775 | 4.298 |
| 7033792700 | 500,000 | 27.626 | 34.625 | 4.570 |
| 7034892700 | 500,000 | 27.312 | 34.812 | 4.898 |
| 7035992700 | 500,000 | 27.374 | 34.659 | 4.757 |

| Aggregate | Value |
| --- | ---: |
| Paired bonuses | **5,000,000** |
| Mean incremental | **+4.689 pp** |
| Std (across seeds) | 0.248 |
| SE | **0.078** |
| 95% CI | **[4.536, 4.843]** |

Stop rule: SE ≤ 0.10 preferred — **met**.

Mean paired OFF X ≈ **27.54** vs certified Phase 5B **27.455** — feature-off ≡ Phase 5B **PASS** (paired). Unpaired 50k OFF smoke can wander; do not use it as the gate.

---

## 6. Historical E1 reconciliation

| Source | Incremental |
| --- | ---: |
| Historical E1 research (1M) | +5.195 pp |
| Phase 6C research re-run (200k) | +5.655 pp |
| Phase 6C live PURE_W2 (200k) | +4.415 pp |
| **Phase 6C.1 live PURE_W2 (5M paired)** | **+4.689 pp** |

**Difference vs historical E1:** −0.51 pp.

Consistent with:

1. Monte Carlo / seed-family variance on the historical 1M artifact
2. Secondary research mid-spin persist (~+0.42 pp if research semantics were used live)
3. Residual engine path differences that are not charged-priority (priority removed)

Not evidence of remaining charged-priority divergence — picker parity PASS.

---

## 7. Decomposition (seed 7026092700, n=200k)

| Mode | Incremental pp |
| --- | ---: |
| Rejump only | 3.165 |
| Wind only | 1.033 |
| Interaction | 0.468 |
| Full | 4.666 |

Closure: 3.165 + 1.033 + 0.468 = 4.666 — **PASS**.

---

## 8. Visibility (n=100k) — must not regress

| | Mix | Large Hill |
| --- | ---: | ---: |
| P(Rejump) | 16.57% | 14.26% |
| P(Wind Key) | 7.45% | 5.78% |
| P(any Phase 6) | 19.61% | 17.05% |

Aligned with E1 targets (~16.6 / 7.6–7.7 / 19.7 mix; ~14.5 / 6.0 / 17.3 LH).

**Stage completion falls under PURE W2** (no forced finish of charged stages):

| Wind state | P |
| --- | ---: |
| Any Wind | 7.45% |
| Any charge (peak) | 7.39% |
| 2+ simultaneous partial charges | 1.35% |
| 3 simultaneous partial charges | 0.17% |
| Any completed stage | 1.10% |
| Global ≥2 / ≥4 / ≥8 / ≥12 | 1.10% / 0.21% / 0.06% / 0.01% |
| Global =27 | ~0 |
| Mean final GLOBAL | 1.018 |

---

## 9. Cap / tails (n=100k natural mix)

| Metric | Value |
| --- | ---: |
| Cap probability | ~1e-5 |
| Cap drag | ~0.068 pp |
| Max payout ≤ 50,000× | PASS |

Forced tail book coverage remains via DEV samples / prior Phase 6B book tails; natural mix confirms shared cap.

---

## 10. RTP budget

| Component | Value |
| --- | ---: |
| BASE | 71.212% |
| Phase 5B | 17.92705 pp |
| Certified Phase 6 PURE W2 | **+4.689 pp** |
| **Game RTP** | **93.828%** |
| Point future reserve (to 96.50%) | **2.672 pp** |
| Safe future reserve (point − 1.96×SE) | **2.518 pp** |

---

## 11. Classification

**STABLE**

- Semantic parity with approved E1 PURE W2
- Paired SE 0.078 ≤ 0.10
- Healthy future reserve before World Record

**READY FOR FINAL FEATURE / TUNING DESIGN: YES**
(World Record / premium paytable / production books still out of scope until explicitly scheduled.)

---

## 12. Code / QA

- Config `freeSpins.phase6.stageRule = W2_PURE`
- Live default `_STAGE_SELECTION_MODE = W2_PURE`
- DEV samples `c1_a`…`c1_i` prove multi-charge PURE W2 paths
- Flight Multiplier HUD renders per-stage charge boxes; charge toast does not imply next-Key lock
- Python reducer multi-charge tests; research/live picker tests

---

## 13. Historical docs

| Doc | Role |
| --- | --- |
| `19_PHASE6B_…` | Historical 6B implementation (charged-priority at ship) |
| `20_PHASE6C_…` | Historical measurement that identified the divergence |
| **`21` (this file)** | Live alignment + final PURE W2 certification |

Do not rewrite historical numeric results in 19/20.
