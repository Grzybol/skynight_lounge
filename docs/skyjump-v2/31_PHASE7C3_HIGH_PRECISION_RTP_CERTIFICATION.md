# Phase 7C.3 — High-precision BASE / buy EV certification & cross-mode pricing

**Branch:** `feat/skyjump-v2-5x5`  
**Live economy:** UNCHANGED (PT2H_LADDER + BODY1 + WR-C H2 + Phase 6 PURE W2)  
**mathVersion:** **1** (not bumped)  
**Config SHA:** `d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0`  
**Artifacts:** `math/games/0_0_poc/phase7c3_research/` (parallel to 7C–7C.2; no overwrite)

---

## Verdict

| Gate | Result |
|------|--------|
| BASE SE ≤ 0.10 pp | **PASS** (0.080 pp) |
| BASE SE ≤ 0.07 pp (preferred) | FAIL (0.080) |
| Upper 95% CI < 96.70% | **PASS** (96.547%) |
| BASE LUT compatibility (2-SE) | **PASS** |
| Cross-mode spread ≤ 0.50 pp (PRICE_A) | **PASS** (0.156 pp) |
| Ceiling on PRICE_A buys | **PASS** |
| Live economy / mathVersion / costs promoted | **NO** |

**Classification:** **PRODUCTION ECONOMY VALID — NO RETUNE**

**Ready for human freeze decision:** **YES**  
(Do not bump `mathVersion` / promote costs / publish until a later freeze step.)

---

## Method (variance reduction)

1. **Freeze 7C.2** into `phase7c3_research/freeze_snapshot.json`.
2. Keep full-round leaf partition: `BASE_NO_TRIGGER`, `BASE_TRIGGER_*_WR_OFF`, `WORLD_RECORD`.
3. **Exact anchors:** line RTP 60.29946%; trigger mix / WR paid `p` from 7A2 H2.
4. **LH:** hierarchical MECE strata (collector × rejump/GFM heat), then **7.92M natural** conditional rounds to SE target (stratum-`p̂` uncertainty floored stratified SE; natural MC is primary for LH mean).
5. **SF:** 1.4M natural → contribution SE 0.019 pp. **WC:** stratified pilot PASS at 0.003 pp.
6. **PV:** n=64; max RTP uncertainty ≪ 0.001 pp — not oversampled.
7. **NO_TRIGGER:** 200k conditional MC for point mean; SE folded into feature certification band (lines exact).
8. **Primary auth:** `Σ p_leaf × E[X|leaf]` with exact `p` + high-precision conditional means.
9. **Buy:** same hot-tail stratification; PRICE_A/B design only (no cost promotion).

---

## Authoritative BASE

| Quantity | Value |
|----------|------:|
| RTP | **96.3907%** |
| SE | **0.0798 pp** |
| 95% CI | [96.2342%, 96.5472%] |
| Upper 95% | **96.5472%** |
| Ceiling | **PASS** |

### Components (pp)

| Component | pp |
|-----------|---:|
| Lines (exact) | 60.2995 |
| Features capped (4C stratified, diagnostic) | 12.4715 |
| Cap drag | 0.0855 |
| NO_TRIGGER leaf | 71.5327 |
| LH full-round | 18.3769 |
| SF full-round | 5.7799 |
| WC full-round | 0.2438 |
| PV full-round | 0.0002 |
| WR | 0.4573 |
| Trigger-spin mass (in lines+features) | 0.2978 |

### Conditional freegame

| Mode | mean X | SE X | RTP contrib pp | RTP SE pp |
|------|-------:|-----:|---------------:|----------:|
| LH | 29.5757 | 0.0958 | 18.3769 | **0.0595** |
| SF | 186.5015 | 0.6121 | 5.7799 | **0.0190** |
| WC | 395.0213 | 5.1451 | 0.2438 | **0.0032** |
| PV | ~1274 (n=64) | — | ~0.0002 | max unc ≪ 0.001 |

LH preferred target was ≤0.05 pp contribution SE; achieved **0.0595 pp** after 7.92M natural rounds (~61 min). Further reduction is diminishing returns vs wall-clock.

### Prior-cap CRN

Paired actual `triggerSpinWinX` vs `prior=0` (n=5000/tier): mean diffs LH +0.46, SF +0.31, WC +0.20 X — **not zero**. Freeze as small positive cap-prior effect; natural path uses actual trigger win. Bound: LH paid-round impact ≈ 0.29 pp with SE ≈ 0.016 pp.

---

## BASE LUT (`library_v2_phase7c3`)

Weighted production books under exact leaf probabilities. Book leaf means are **2-SE compatible** with authoritative conditional means → **PASS**.  
Raw book-sample RTP gap vs auth ≈ 0.35–0.60 pp (MC noise at book counts); authority-aligned reconstruction matches auth when means are compatible.

---

## Buy EV (WR-off stratified + WR mass in authMean)

| Mode | EV X (WR-off) | SE | 95% CI | median | P90 | P99 | P(cap) | P(WR)≈ | mean len |
|------|-------------:|---:|--------|-------:|----:|----:|-------:|-------:|---------:|
| LH | 28.498 | 0.298 | [27.92, 29.08] | 9.3 | 39.5 | 360.8 | 0 | 1.2e-5 | 11.6 |
| SF | 188.359 | 1.447 | [185.5, 191.2] | 73.5 | 381 | 1837 | 0 | 3.3e-5 | 10.5 |
| WC | 395.212 | 2.613 | [390.1, 400.3] | 125.9 | 894 | 4146 | 0 | 6.6e-5 | 10.5 |
| PV | 1315.246 | 5.428 | [1304.6, 1325.9] | 661 | 2779 | 10275 | 0 | 1.3e-4 | 10.4 |

Buy LUT means are compatible with auth means (PASS under compatibility gate). **Costs not promoted.**

---

## PRICE_A — no BASE retune

Target buy RTP ≈ BASE + 0.15 pp, clipped under 96.70.

| Mode | cost (design) | RTP % |
|------|-------------:|------:|
| BASE | — | 96.3907 |
| LH | **30.2** | 96.380 |
| SF | **196.9** | 96.503 |
| WC | **412.8** | 96.536 |
| PV | **1369.1** | 96.535 |

- Cross-mode spread: **0.156 pp** → **PASS** (≤ 0.50)  
- Ceiling: **PASS**  
- Historical provisional 31.4 / 197.8 / 416.4 / 1356.4 are **not** frozen.

## PRICE_B — informational only

Hypothetical family at 96.45%: required BASE uplift ≈ **+0.059 pp** (tiny). Buy costs would reprice to that target. **Not applied.**

## WR uplift (optional, not applied)

Current WR ≈ **0.457 pp**, paid `p` ≈ 9.1455e-8 (1 in ~10.9M). To 96.45% need only +0.059 pp WR — aesthetically fine but **unnecessary** (BASE already ~96.39%).

---

## What was not done

- No live config / economy / buy-cost promotion  
- No `mathVersion` bump  
- No publish / push  
- No downward TUNE_B/C  
- Docs 28–30 not rewritten  

---

## Scripts

- `skyjump_v2_phase7c3_common.py`
- `skyjump_v2_phase7c3_lh_strata.py`
- `skyjump_v2_phase7c3_natural_precision.py`
- `skyjump_v2_phase7c3_base_auth.py`
- `skyjump_v2_phase7c3_buy.py`
- `skyjump_v2_phase7c3_prior_cap.py`
- `test_skyjump_v2_phase7c3.py`
