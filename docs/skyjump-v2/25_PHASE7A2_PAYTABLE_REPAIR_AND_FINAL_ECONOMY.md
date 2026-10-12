# SKYJUMP V2 — Phase 7A.2 Paytable Repair + Final Economy Freeze

**Status:** COMPLETE — hierarchy-fixed **PT2H_LADDER** + economy **H2** approved for Phase 7B implementation.
**Branch:** `feat/skyjump-v2-5x5`
**Live config:** **UNMODIFIED**
**Artifacts:** `math/games/0_0_poc/phase7a2_research/`
**Art:** LOCKED (`23`, `26`) — WAIT = NONE
**Prior:** Phase 7A.1 blocker (doc 24) resolved here; historical PT2 kept archived.

---

## 1. Inputs (frozen)

| | |
| --- | ---: |
| Current game RTP | 93.828% |
| Phase 7A.1 PT2 full-game Δ | +0.64719 pp (historical; **not** promoted) |
| BODY1 reference | ~+1.368 / ~+1.359 pp |
| WR-C ratio | 1 : 3 : 6 : 12 |
| WR fill (7A.1) | ~49963.62× |

---

## 2. Hierarchy repair → PT2H_LADDER

Historical **PT2** remains in `phase7a_research/paytables.json` (FAIL: M1 4oak 3.3 < M2 6.1 / M3 5.8).

**Minimal-distance fix:** mid 4oak ladder + tiny L3 5oak trim. Premiums unchanged vs PT2.

| Symbol | 3OAK | 4OAK | 5OAK |
| --- | ---: | ---: | ---: |
| P1 | 10.0 | 50.0 | 200.0 |
| P2 | 6.0 | 33.2 | 100.0 |
| P3 | 5.0 | 25.2 | 65.0 |
| M1 | 1.6 | **6.5** | 24.6 |
| M2 | 1.3 | **6.0** | 21.6 |
| M3 | 1.0 | **5.5** | 19.1 |
| L1 | 0.8 | 1.7 | 3.6 |
| L2 | 0.5 | 1.3 | 2.7 |
| L3 | 0.3 | 1.1 | **2.0** |

Δ vs PT2 awards: M1 4oak 3.3→6.5, M2 4oak 6.1→6.0, M3 4oak 5.8→5.5, L3 5oak 2.2→2.0.

| Check | Result |
| --- | --- |
| 3OAK hierarchy | **PASS** |
| 4OAK hierarchy | **PASS** |
| 5OAK hierarchy | **PASS** |
| Within-symbol 3≤4≤5 | **PASS** |
| 0.10× grain | **PASS** |

Exact BASE line RTP: **60.29946%** (Δ vs PT0 **+0.60328 pp**; band +0.50–+0.70).

Premium RTP unchanged vs PT2 (~5.896%). Mid feel preserved (ladder, not crushed).

**PAYTABLE ID:** `PT2H_LADDER`
**STATUS:** **APPROVED FOR PHASE 7B**

---

## 3. Full-game PT2H delta (1M paired)

| Component | Δ pp | SE |
| --- | ---: | ---: |
| BASE lines (exact) | **+0.60328** | — |
| FS initial lines | **+0.06341** | |
| Rejump lines | **−0.00036** | |
| Bonus total | **+0.06306** | 0.00180 |
| **TOTAL full-game** | **+0.66634** | |

---

## 4. BODY1 interaction

| | Δ pp | SE |
| --- | ---: | ---: |
| BODY1 standalone | **+1.33872** | 0.00771 |
| PT2H standalone | **+0.06306** | 0.00180 |
| PT2H+BODY1 combo | **+1.40177** | 0.00792 |
| Interaction | **≈ −0.000005** | — |

Additivity: PASS. Visibility unchanged (P(Rejump)/P(Wind) identical BODY0 vs BODY1).

Feel BODY0→BODY1: median 9.5→9.7, P75 19.2→20.1; cap p 1.1e-5 unchanged.

---

## 5. Core without WR

```
93.828 + 0.60328 + 1.40177 = 95.83306%
```

WR fill (PT2H+BODY1, 1M): E[incremental] **49964.08×**; fill mass/bonus 665530.

---

## 6. Final candidates

| ID | WR pp | Projected | Point res. | Safe res. | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| H1 | 0.450 | 96.283% | 0.217 | 0.063 | WR~0.45 in band |
| **H2** | **0.457** | **96.290%** | **0.210** | **0.056** | **Recommended** |
| H2_SAFE08 | 0.433 | 96.266% | 0.234 | 0.080 | safe≥0.08; under band |
| H3 | 0.427 | 96.260% | 0.240 | 0.086 | conservative |

Historical PT2-based C2 / CFINAL_SOLVED (doc 24) are comparison-only — **do not promote**.

### H2 WR scale

| | |
| --- | ---: |
| Architecture | WR-C FS-only; trial after board / before lines |
| Tier ratio | 1 : 3 : 6 : 12 |
| WR RTP pp | **0.45694** |
| Paid-round p | **9.15e-8** |
| 1 in N paid | **~10.93M** |
| P(WR \| bonus) | **~1.40e-5** (~1 in 71.4k) |

Uncertainty SE ≈ **0.0784 pp** (Phase 6 ⊕ combo).

---

## 7. Recommendation

**FINAL ECONOMY:** **H2** = PT2H_LADDER + BODY1 + WR-C @ **0.457 pp** → **96.290%**, point reserve **0.210**, safe **0.056**.

Alternate if human requires safe ≥ 0.08: **H3** (96.260%).

---

## 8. READY FOR PHASE 7B?

**YES**

Phase 7B may implement: promote PT2H_LADDER awards, BODY1 token tables, WR-C at H2 scale — still no production books/LUT in that step until separately tasked.

Art production: follow `26_PRODUCTION_ASSET_TODO.md` independently.
