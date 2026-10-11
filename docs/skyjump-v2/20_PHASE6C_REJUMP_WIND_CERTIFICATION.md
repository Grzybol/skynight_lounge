# SKYJUMP V2 — Phase 6C Rejump / Wind RTP Certification

**Status:** Historical measurement + reconciliation (no weight retune).
**Superseded for live stage selection by Phase 6C.1** — see `21_PHASE6C1_PURE_W2_ALIGNMENT_CERTIFICATION.md`.
**Branch:** `feat/skyjump-v2-5x5`
**Live candidate at time of 6C:** `P6A1_E_E1` with `stageRule=W2_CHARGE_PRIORITY`
**Freeze:** `math/games/0_0_poc/phase6c_research/freeze.json`
**Artifacts:** `quick_cert.json`, `multiseed.json`, `semantic_diff.json`

---

## 1. Why 6C

| Source | Incremental | Game RTP | Reserve to 96.50% |
| --- | ---: | ---: | ---: |
| Phase 6A.1 E1 research (1M hist.) | +5.195 pp | ~94.334% | ~2.166 pp |
| Live 6B 1M unpaired | +5.854 pp | ~94.993% | ~1.507 pp |
| Live 6B paired feature-off | +5.857 pp | — | — |

Paired ≈ unpaired on the same seed family → the ~+0.66 pp gap is **not** ordinary unpaired noise.

---

## 2. Freeze

Live config SHA-256 recorded at start; re-checked at end — **unchanged**.
BASE mystery, Phase 5B archive, E1 tier tables, `stageRule=W2_CHARGE_PRIORITY` frozen.

---

## 3. Research vs live semantic diff

| Field | Verdict |
| --- | --- |
| E1 mystery weights by tier | Equivalent |
| R-BATCH order | Equivalent |
| Spent collectors / preservation / no-Scatter refill | Equivalent |
| Max 2 / depth 8 / K1 / saturation B | Equivalent |
| Collector-only Flight Multiplier / Head Judge ×2 | Equivalent |
| Shared 50,000× round cap | Equivalent |
| **Wind stage selection** | **DIFFERENT (critical)** |
| Mid-spin persistent targets after Coach-on-Rejump | Secondary |

### Critical difference

**Research E1 (`choose_stage_a1`):** pure **W2** — pick among lowest-value eligible stages; charge applied after pick.

**Live 6B (`choose_stage_charge_priority`):** **W2 + charged-stage priority** — if any eligible stage has `charge=1`, finish that stage before opening a new charge.

Exact Wind-key-only MC (N=2 keys): priority always reaches global ×2; pure W2 reaches ×2 only ~33% of the time.

---

## 4. Charged-stage priority counterfactual (live resolver, n=200k, seed 20260926)

| Mode | Mean bonus X | Paired pp vs feature-off |
| --- | ---: | ---: |
| C OFF (Phase 5B archive) | 27.728 | — |
| B PURE_W2 | 34.489 | +4.415 |
| A FULL (live priority) | 36.697 | +5.857 |
| RJ only | 32.470 | +3.097 |
| WIND only | 29.851 | +1.387 |

**Charged-stage priority cost (A − B): +1.442 pp**

RJ + WIND + interaction = 3.097 + 1.387 + 1.373 = **5.857** (= FULL). Decomposition closes.

---

## 5. Research E1 reproduction

| Run | n | Incremental |
| --- | ---: | ---: |
| Historical `large_final.jsonl` P6A1_E_E1 | 1,000,000 | **+5.195 pp** |
| 6C re-run research engine (same seed family 20260923) | 200,000 | +5.655 pp |
| Research engine + charged-priority monkeypatch | 100,000 | +6.767 pp |

Historical 1M E1 artifact is preserved. Smaller-n re-run is noisier but same direction. Injecting charged priority into the research engine **raises** EV — consistent with live A−B.

---

## 6. Feature-off ≡ Phase 5B

200k paired OFF mean **27.728×** vs certified **27.455×** (Δ ≈ +0.18 pp).
Within ordinary Phase 5B MC fluctuation for this sample size. Archive tables + `phase6.enabled=false` path used. **PASS.**

---

## 7. Multi-seed (spaced streams)

Unpaired: 1×1M + 4×200k with non-overlapping `seed+i` families.
Paired: 1×200k (20260925) + 4×100k spaced seeds.

| | Mean pp | Std | SE | 95% CI |
| --- | ---: | ---: | ---: | --- |
| Unpaired vs certified 27.455 | 6.595 | 0.555 | 0.248 | [6.11, 7.08] |
| **Paired ON−OFF** | **5.645** | 0.532 | **0.238** | **[5.18, 6.11]** |

Paired SE **>±0.20** → cannot claim STABLE ±0.10/±0.20 RTP certification from this seed budget alone.

**Preferred central estimate (paired):** **+5.65 pp** (±0.24 SE; 95% CI half-width ~0.47).
Primary single-stream anchor (200k paired seed 20260925): **+5.857 pp**.

---

## 8. Wind / Rejump visibility (live instrument, n=80k)

| Metric | Value |
| --- | ---: |
| P(any Wind) | 7.58% |
| P(stage complete / global≥2) | 2.01% |
| P(global≥4) | 0.30% |
| P(global≥8) | 0.045% |
| Charge-only bonuses | 4458 / 80k |
| Upgrade bonuses | 1607 / 80k |

Rejump paired incremental ~**3.10 pp**; Wind alone ~**1.39 pp**; positive interaction ~**1.37 pp**.

---

## 9. Cap / tail

| | Value |
| --- | ---: |
| Natural p(cap) (1M) | ~1.3e-5 (~1 in 77k bonuses) |
| Mean cap drag X (1M) | ~1.55 |
| Cap drag RTP | ~0.010 pp |
| Forced analytic raw max | 810,000× |
| Forced capped max | 50,000× |

---

## 10. Certified RTP budget (engineering)

Using paired multi-seed mean **5.645 pp**:

| | Value |
| --- | ---: |
| BASE | 71.212% |
| Phase 5B FS | 17.927 pp |
| Phase 6 paired mean | 5.645 pp |
| **Game RTP** | **~94.78%** |
| Point reserve to 96.50% | ~1.72 pp |
| Safe planning reserve (point − 95% half-width) | ~1.25 pp |

Using 200k paired anchor **5.857 pp** → game ~**94.99%**, reserve ~**1.51 pp**, safe ~**1.27 pp** after SE.

---

## 11. Classification

**IMPLEMENTATION DIVERGED FROM RESEARCH**

Primary cause of the research→live gap: live **charged-stage priority** vs research **pure W2** (~+1.44 pp on matched live streams). Secondary: mid-spin persist timing; MC seed families.

Not retuned. Do not auto-switch stage rule without a human design decision.

Also: paired SE > ±0.20 prevents calling the RTP **STABLE** at the preferred precision until more spaced seeds / larger paired n.

---

## 12. Synthetic DEV samples

Added protocol-correct synthetics:

- `16_coach_after_rejump`
- `24_cap` (Judge ×27 → `skyjumpCapReached` terminated)

Manual `/dev-preview`: coach/rejump banner OK; cap sample credits 50,000× balance path.

---

## 13. Next

Human decision required before World Record / premium design:

1. Keep live charged-stage priority (accept hotter live EV + tighter reserve), or
2. Align live stage selection to research pure W2 (would lower live ~1.4 pp toward research), or
3. Expand paired seed budget to shrink SE below ±0.20 before locking a certified Phase 6 number.

Do **not** retune Mystery weights here. Do **not** implement World Record here.
