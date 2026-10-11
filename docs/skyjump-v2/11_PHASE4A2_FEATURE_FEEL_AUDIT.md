# SkyJump V2 — Phase 4A.2 Feature Feel Audit

**Status:** research complete — **promoted to live config as Phase 4B** (`F01_E_feel`)  
**Branch:** `feat/skyjump-v2-5x5`  
**Benchmark:** Phase 4A `H02_B_R1` (preserved in research; not promoted)  
**Phase 4B:** **complete** — see `12_PHASE4B_BASE_FEATURE_IMPLEMENTATION.md`  

---

## 1. Why another pass

`H02_B_R1` has healthy economy (~10.7pp feature RTP in Phase 4A; ~9.7pp re-sim at seed `20260922` / 10M) but weak feel:

| Metric | H02 (10M) |
|---|---:|
| P(feature win \| Coach) | 18.05% |
| P(dead Coach) | 81.95% |
| P(2+ Coach) | **0** (single-reel B) |

Phase 4A.2 targets more frequent successful Coach activations with smaller typical awards, while restoring rare multi-Coach.

---

## 2. Coach frequency redesign

Research-only two-reel sparse models on reels **2+4**, lengthened by **frequency-preserving cycling** (not L3/L2 pad):

| Model | Strip lengths (r2/r4) | P(any) | P(≥2) | Line RTP |
|---|---|---:|---:|---:|
| A (Phase 3) | 52/52 | 18.31% | 0.925% | 58.05% |
| B (benchmark) | 52 / — | 9.62% | 0% | 58.47% |
| **D** | 100/100 | 9.75% | 0.250% | 59.66% |
| **E** | 120/120 | 8.16% | 0.174% | 59.70% |
| **F** | 90/90 | 10.80% | 0.309% | 59.56% |

Line RTP stays in **~59.5–59.7%** (within 57–60%). Multi-Coach is rare but non-zero on D/E/F.

**Structural finding:** at fixed Mystery mix, higher Coach frequency raises feature RTP roughly in proportion. To hold ~10pp RTP, denser Coaches force leaner collectors → worse feel. **Lower two-reel Coach E** is the best joint belt for feel + RTP.

---

## 3. Collector-density tradeoff

Feel direction: raise JUDGE share (~8–10% of Mystery mix) and crush token faces further (T1 ≈ 99.94% of tiers, within-tier nearly always `1x`).

Dominant dead reason remains:

**tokens present + no collector (~71–75% of Coach spins)**

Collector-without-token is small (~2–3% independent; ~0.8% conditioned).

So collector density is the correct lever; conditioned tables help the minority failure mode.

---

## 4. Independent vs conditional result tables

**Independent (recommended path):** one Mystery weight table.

**Conditional (research only):** after ≥1 token already resolved in the current Mystery chain, raise JUDGE/HEAD_JUDGE weights; before any token, suppress collectors.

| Candidate | Feature RTP | Feel | Dead | collector/no-token | Notes |
|---|---:|---:|---:|---:|---|
| F01 independent | 11.82% | 25.0% | 75.0% | 2.65% | Feel primary |
| F06 conditioned | 13.18% | 24.4% | 75.6% | **0.82%** | Cuts empty Judges; RTP overshoots |

Conditional **does** reduce Judge-with-no-token without obvious guaranteed wins, but it fattens average wins / RTP. **Do not promote** conditional automatically.

---

## 5. Finalists (deep sims)

| Role | ID | Coach | Spins | Feat RTP | Feel | Dead | P(≥2) | Cond |
|---|---|---|---:|---:|---:|---:|---:|---|
| Benchmark | H02_B_R1 | B | 10M | 9.67% | 18.0% | 82.0% | 0 | No |
| Best two-reel independent | **F01_E_feel** | E | 10M | 11.82% | **25.0%** | **75.0%** | 0.174% | No |
| Best lower-Coach / hard-band | F07_E_safe | E | 5M | **10.70%** | 22.4% | 77.6% | 0.174% | No |
| Best higher-collector | F02_E_collect | E | 5M | 13.23% | 26.9% | 73.1% | 0.174% | No |
| Best conditioned | F06_E_cond | E | 5M | 13.18% | 24.4% | 75.6% | 0.174% | Yes |

---

## 6. Recommended: `F01_E_feel`

Feel-primary pick for Phase 4A.2 goals. Soft-band feature RTP (~11.8pp) is accepted over forcing the hard 11.00% wall.

**Alternate hard-band:** `F07_E_safe` (~10.7pp, feel ~22.4%).

### Coach E

- Reels 2+4, strip lengths **120 / 120**, one Coach stop each  
- P(any) **8.16%** · P(≥2) **0.174%** · Line RTP **59.70%**

### Mystery weights (independent)

| Result | Weight | Observed mix |
|---|---:|---:|
| FLIGHT_TOKEN | 855 | 85.5% |
| THERMAL_LIFT | 42 | 4.2% |
| GATE_UPGRADE | 3 | 0.30% |
| JUDGE | 85 | 8.5% |
| HEAD_JUDGE | 15 | 1.5% |

### Token tiers

| Tier | Weight |
|---|---:|
| T1 | 999400 |
| T2 | 400 |
| T3 | 120 |
| T4 | 40 |
| T5 | 32 |
| T6 | 8 |

Within-tier: T1 nearly always `1x`; T6 still includes `50000x`.

### Headline metrics (10M)

| Metric | Value |
|---|---:|
| Feature RTP capped | 11.8216% |
| BASE before FS | 71.52% |
| P(win \| Coach) | 25.03% |
| Dead Coach | 74.97% |
| Avg win \| win | 5.79x |
| Median \| win | 4x |
| P90 / P95 / P99 / P99.9 | 10 / 14 / 24 / 70 |
| Cap frequency | 1e-7 |
| Cap drag RTP | ~1.8e-6 |
| FS reserve | 24.98pp |
| Implied bonus / Scatter≥3 | ~38.3x (confirmed on Coach E strips — not a doc arithmetic error) |

### Dead Coach reasons (given Coach)

| Reason | Share |
|---|---:|
| tokens / no collector | 71.29% |
| collector / no tokens | 2.65% |
| modifier-only | 1.02% |
| other | 0% |

### Feature win distribution (given Coach)

| Bucket | Share |
|---|---:|
| 0x | 74.97% |
| (0,1] | 3.15% |
| (1,2] | 4.27% |
| (2,5] | 9.43% |
| (5,10] | 6.09% |
| (10,25] | 1.89% |
| (25,50] | 0.16% |
| (50,100] | 0.030% |
| (100,500] | 0.0085% |
| (500,1000] | 0.0023% |
| (1000,5000] | 0.0020% |
| 5000+ | 0.00049% |

### Multi-Coach tail

On multi-Coach spins (rate ~0.172%): average raw feature ~4.93x; cap rate 0. No evidence of pathological multi-Coach jackpot stacking under ultra-lean tokens. Second Coach still cannot re-select an already transformed type.

---

## 7. H02 delta (`F01` − `H02`)

| Metric | H02 | F01 | Δ |
|---|---:|---:|---:|
| P(any Coach) | 9.62% | 8.16% | −1.46pp |
| P(≥2 Coach) | 0 | 0.174% | +0.174pp |
| Feature RTP | 9.67% | 11.82% | +2.15pp |
| P(win \| Coach) | 18.05% | 25.03% | +6.98pp |
| Dead Coach | 81.95% | 74.97% | −6.98pp |
| Avg win \| win | 5.58x | 5.79x | +0.21x |
| Median | 4x | 4x | 0 |
| P99 | 28x | 24x | −4x |
| Cap freq | 0 | 1e-7 | ~0 |
| FS reserve | 28.35pp | 24.98pp | −3.37pp |

---

## 8. Phase 4B outcome

**Promoted (feel-primary):** `F01_E_feel` weights + Coach E strips (120/120 freq-preserving).

1. Independent Mystery table (not conditional).  
2. Soft-band ~11.8pp BASE feature RTP accepted for feel.  
3. Lean paying token faces; Phase 3 research tables archived.  
4. UX shows uncollected token faces when no Judge/Head Judge — **no cross-spin banking**.

Alternate not promoted: `F07_E_safe` (~10.7pp, feel ~22.4%) remains in `phase4a2_research/`.

**Phase 4B implementation:** YES — `12_PHASE4B_BASE_FEATURE_IMPLEMENTATION.md`  
**Phase 3 tables in live config:** archived under `phase3LatentResearch`  
**Phase 4A H02 research preserved:** YES  

---

## 9. Files

| Path | Role |
|---|---|
| `skyjump_v2_phase4a2_candidates.py` | Coach D/E/F + feel seeds |
| `skyjump_v2_phase4a2_simulate.py` | Feel scoring + H02 deltas |
| `skyjump_v2_phase4a2_search.py` | Search driver |
| `skyjump_v2_phase4a_economy.py` | Conditional sampling + dead reasons |
| `phase4a2_research/` | Screen / finalists / summary |
| `tests/test_skyjump_v2_phase4a2.py` | Invariants |

```bash
cd math
python games/0_0_poc/skyjump_v2_phase4a2_search.py --screen-spins 120000 --finalist-spins 5000000 --top-spins 10000000
python -m pytest tests/test_skyjump_v2_phase4a2.py -q
```
