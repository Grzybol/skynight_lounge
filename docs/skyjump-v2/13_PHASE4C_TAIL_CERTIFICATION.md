# SKYJUMP V2 — Phase 4C BASE Feature RTP Tail Certification

**Status:** MEASUREMENT ONLY — live F01 / Coach E config frozen.  
**Branch:** `feat/skyjump-v2-5x5`  
**Classification:** **STABLE** (ready for Free Spin *design*; do not retune in 4C)  
**Live config SHA-256:** `d932065b36a626c7cd9a818bd8c401559e6270c434622d32d1fb640e3d8d7803`

---

## 1. Why Phase 4C exists

Phase 4B’s single 10M natural Monte Carlo was structurally correct but **not sufficient to certify** BASE feature EV:

| Source | Feature RTP raw | Feature RTP capped | Cap hits |
| --- | ---: | ---: | ---: |
| Phase 4A.2 research (F01) | ~11.822% | ~11.822% | ~0 |
| Phase 4B live 10M (seed 42) | ~13.911% | ~12.410% | 2 |

Two cap hits produced ~**1.50 pp** of cap drag on that seed. Max raw ~**200,010×**.  
Rare T6 + multi-collector tails dominate variance. Free Spin design cannot start from one noisy BASE residual.

---

## 2. Frozen live config

| Field | Value |
| --- | --- |
| `candidateOrigin` | `F01_E_feel` |
| `featureEconomyVersion` | 1 |
| Coach | E (120/120) |
| Cap | 50,000× |
| Mystery / token / Thermal / Gate / Judge | **unchanged** |

Hash recorded in `math/games/0_0_poc/phase4c_research/live_config_sha256.txt`.

---

## 3. Methodology

### A. Natural Monte Carlo (cross-check)

**5 × 10,000,000** independent seeds (`42…46`).  
Reports mean / min / max / std. **Not** the sole certified result.

### B. Stratified / conditional (primary)

1. Probe \(P(N)\) mystery counts (500k).  
2. Exact mix over \(N\): `NO_T4PLUS` / `T4` / `T5` / `T6` using independent Mystery × tier probabilities.  
3. Bulk MC (5M) for \(E[X\mid\mathrm{NO\_T4PLUS}]\).  
4. Forced conditional sims (150k+) for \(E[X\mid T4]\), \(E[X\mid T5]\), \(E[X\mid T6]\).  
5. \(\mathrm{RTP}=\sum_s P(s)\,E[X\mid s]\).

### C. Exact / semi-exact

Exact Mystery / tier / face probabilities and stratum partition given \(N\).  
Cap drag via \(P(s)\,P(\mathrm{cap}\mid s)\,E[\mathrm{excess}\mid\mathrm{cap},s]\).  
Thermal / Gate geometry remains in conditional sims (not fully enumerated).

---

## 4. Results

### Natural MC (5 × 10M = 50M spins)

| Metric | Value |
| --- | ---: |
| Feature RTP capped mean | **11.736%** |
| Feature RTP capped median | 11.357% |
| min / max capped | 11.079% / 12.704% |
| std (across seeds) | **0.764 pp** |
| Feature RTP raw mean | 12.186% |
| Cap hits total | **5** |
| Cap frequency | ~1.0e-7 |

Seed 42 alone (Phase 4B) remains an upper outlier due to two huge caps.

### Stratified / semi-exact certified estimate

| Metric | Value |
| --- | ---: |
| Feature RTP raw | **11.600%** |
| Feature RTP capped | **11.516%** |
| Internal method CI | ~**±0.099 pp** |
| Engineering CI (incl. multi-seed SE / method gap) | ~**±0.34 pp** |

±**0.10 pp** is achieved by the stratified estimator’s internal error model, but **not** by naive multi-seed MC alone (seed std ≫ 0.10 pp). FS planning should use the **engineering** interval.

### Exact line / Scatter (unchanged)

| Metric | Value |
| --- | ---: |
| Line RTP | **59.6962%** |
| P(Scatter ≥ 3) | **0.65297%** (1 in 153.15) |

### Cap (stratified)

| Metric | Value |
| --- | ---: |
| P(cap) | ~**4.87e-8** (~1 in 20.5M) |
| Cap drag RTP | ~**0.085 pp** |
| Dominant route | **high token + collector** (T6 face × Judge/Head Judge) |
| Extreme route | `high+gate+thermal+multi_collector` can hit ~300,000× raw but is ultra-rare |

### RTP contribution by max-tier stratum

| Stratum | P(stratum) | Capped RTP contrib |
| --- | ---: | ---: |
| T1–T3 (bulk) | ~0.99998 | ~10.53 pp |
| T4 | 9.10e-6 | ~0.045 pp |
| T5 | 7.28e-6 | ~0.213 pp |
| T6 | 1.82e-6 | ~0.727 pp |

T6 raw contrib ~0.81 pp; ~0.085 pp lost to cap → **most T6 EV is kept**.

### T6 faces (forced / reweighted)

| Face | Approx capped RTP contrib | Cap drag contrib | P(collector\|forced) |
| ---: | ---: | ---: | ---: |
| 10,000× | ~0.54 pp | ~0.014 pp | ~29% |
| 25,000× | ~0.32 pp | ~0.036 pp | ~29% |
| 50,000× | ~0.24 pp | ~0.104 pp | ~28% |

The 50,000× face is the main cap-drag source; it is still net-positive after capping.

### Collector passes (bulk 5M, mostly low tiers)

| Passes | Capped RTP |
| ---: | ---: |
| 1 | ~5.53 pp |
| 2 | ~3.70 pp |
| 3 | ~1.15 pp |
| 4 | ~0.32 pp |
| 5+ | ~0.10 pp |

Repeated collection of the same token state (Head Judge / multi-Judge) is material but secondary to single-pass mass among low tiers.

---

## 5. Free Spin budget (planning only)

Remaining RTP ≈ **25.29 pp** toward 96.5%.

Implied average FS bonus ≈ **38.73×** (engineering band ~**38.2× – 39.3×**).

Scatter \(P(3+)=0.00652967825443787\) unchanged.

---

## 6. Decision

**STABLE**

- Stratified (~11.52%) and multi-seed mean (~11.74%) agree with research (~11.82%) within a few tenths of a pp.  
- Cap drag is understood (~0.085 pp stratified; seed-volatile in naive MC).  
- **Ready for Free Spin design.**  
- Do **not** retune F01 in this phase. If later design needs a leaner tail, that is a separate decision.

**Precision note:** ±0.10 pp is **defensible for the stratified point estimate**, but engineering planning should quote ~**±0.34 pp** given multi-seed spread.

---

## 7. Files

| Path | Role |
| --- | --- |
| `skyjump_v2_phase4c_exact.py` | Exact tables |
| `skyjump_v2_phase4c_strata.py` | Strata + conditional + bulk |
| `skyjump_v2_phase4c_forced.py` | Forced-tier estimators |
| `skyjump_v2_phase4c_stratified.py` | IS tooling (diagnostic) |
| `skyjump_v2_phase4c_certify.py` | Certification runner |
| `skyjump_v2_phase4c_multiseed.py` | Multi-seed natural MC |
| `skyjump_v2_phase4c_cert_report.json` | Authoritative JSON |
| `phase4c_research/` | Hash, seed shards, copy of report |
| `tests/test_skyjump_v2_phase4c.py` | Regressions |
