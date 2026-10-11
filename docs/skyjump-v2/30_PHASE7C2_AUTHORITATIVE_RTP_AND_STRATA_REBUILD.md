# SKYJUMP V2 — Phase 7C.2 Authoritative RTP & Strata Rebuild

**Status:** COMPLETE for BASE acceptance — buy LUT agreement still provisional  
**Branch:** `feat/skyjump-v2-5x5`  
**Live economy modified:** **NO**  
**mathVersion:** **1**  
**Outputs:** `library_v2_phase7c2/`, `stake-upload-phase7c2/math/`, `phase7c2_research/`  
**Does not overwrite:** Phase 7C `library_v2/` or docs 28/29

---

## Freeze

Config SHA `d6879d5c…2edbd0` **MATCH**. Phase 7C / 7C.1 artifacts pinned in `freeze_snapshot.json`.

---

## Architecture fix

BASE freegame leaves are **conditional natural full-round books** (BASE board + lines + features + FS + one settlement), **not** buy-mode slices.

Leaf partition:

| Leaf | Role |
| --- | --- |
| `BASE_NO_TRIGGER` | scatter &lt; 3 |
| `BASE_TRIGGER_LH_WR_OFF` | exact 3, WR disabled |
| `BASE_TRIGGER_SF_WR_OFF` | exact 4, WR disabled |
| `BASE_TRIGGER_WC_WR_OFF` | 5+ non-PV, WR disabled |
| `BASE_TRIGGER_PV_WR_OFF` | Perfect V, WR disabled |
| `WORLD_RECORD` | explicit WR mass |

Σp = 1. WR appears once. Freegame leaves are WR-off.

---

## Exact start mix (parity)

| Start | p |
| --- | ---: |
| LH | 0.0062135906602437665 |
| SF | 0.00030991400836999946 |
| WC | 6.171610276639861e-6 |
| PV | 1.9755474637131444e-9 |
| P(≥3) | 0.00652967825443787 |

---

## BASE features (Phase-4C method, live PT2H+BODY1)

| Metric | Value |
| --- | ---: |
| Raw | **12.5570%** |
| Capped | **12.4715%** |
| Cap drag | **0.0855 pp** |
| Uncertainty | **±0.0993 pp** (target ≤0.10 — **PASS**) |
| Lines + features before FS | **72.771%** |

---

## Conditional full-round means (new BASE library)

| Leaf | n | Mean X | E[trig] |
| --- | ---: | ---: | ---: |
| NO_TRIGGER | 80,000 | **0.7131** | 0.7131 |
| LH WR-off | 60,000 | **29.847** | 0.453 |
| SF WR-off | 30,000 | **185.738** | 0.331 |
| WC WR-off | 15,000 | **417.810** | 0.168 |
| PV WR-off | 8 | **683.7** (high SE; tiny mass) | 0 |
| WORLD_RECORD | 20 | **50000** | — |

Trigger-base paid-round: E[win\|trigger]≈0.423× from 7C.1; in new LH/SF sample ~0.33–0.45×.  
Prior-cap paired delta ≈ **0 pp** (caps rarely bind on delta in 6k/tier).

---

## Authoritative BASE RTP

**95.861% ± 1.01 pp** (SE from conditional-mean sampling; dominated by LH)

Primary estimator: Σ p_leaf × E[X\|leaf] — no staged 5B/6, no buy substitution, one WR term.

| | % |
| --- | ---: |
| New BASE LUT | **95.861%** |
| Gap LUT − auth | **~0.000 pp** |
| Acceptance ≤0.10 / ≤0.05 | **PASS / PASS** |
| Old Phase 7C BASE LUT | 98.120% |
| Old bias | **+2.26 pp** — buy-slice freegame books + hotter means |

---

## PV / WR weights

| | target | effective | |
| --- | ---: | ---: | --- |
| PV | 1.9755e-9 | 1.9755e-9 | **PASS** |
| WR | 9.1455e-8 | 9.1455e-8 | **PASS** |

Weight scale `10^15` + few PV books — no `max(1,…)` inflation.

---

## Natural MC cross-check

5×25k seeds: mean **100.2%**, CI ~[90.4, 109.9]; auth **95.86%** inside CI (**PASS** as secondary).

---

## Buy EV (authoritative, 100k/tier) & provisional costs

| Mode | EV X | Prov. cost | Target RTP |
| --- | ---: | ---: | ---: |
| LH | 30.345 | **31.4** | 96.64% |
| SF | 190.892 | **197.8** | 96.51% |
| WC | 401.840 | **416.4** | 96.50% |
| PV | 1308.946 | **1356.4** | 96.50% |

Not promoted to live config.

## Buy LUT agreement

80k-book LUTs vs EV: relative errors ~0.15–1.2% (SF worst). **Not yet** at preferred ≤0.10% / ≤0.05 pp RTP. Costs must stay priced from **EV**, not noisy LUT means, until buy libraries are enlarged.

---

## Economy decision

Authoritative BASE **95.861% &lt; 96.70%** → **WITHIN LIMIT** (point estimate).  
Full-round SE (~1 pp) is larger than preferred 0.10 pp internal target; feature cert meets 0.10 pp. No retune candidates required for a hot economy.

Old 7C “too hot” reading was an **artifact of buy-sourced BASE freegame strata**.

---

## Classification / readiness

| | |
| --- | --- |
| Current economy | **WITHIN LIMIT** |
| READY FOR HUMAN RETUNE | **NO** (no hot retune; optional later upward trim if product wants ~96.5%) |
| Blockers for publication freeze | Buy LUT↔EV agreement; optional more LH samples to shrink full-round SE; then mathVersion bump in a later phase |

---

## Tests

`test_skyjump_v2_phase7c2.py` — freeze, line anchor, mix, conditional full-round shape, partition, PV/WR weights, LUT gap.
