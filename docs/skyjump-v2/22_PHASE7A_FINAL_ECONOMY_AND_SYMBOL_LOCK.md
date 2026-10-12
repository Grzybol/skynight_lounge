# SKYJUMP V2 — Phase 7A Final Economy Design + Symbol Lock

**Status:** RESEARCH / DESIGN complete. **Superseded for promotion** by Phase 7A.1 (full-round) and Phase 7A.2 (`PT2H_LADDER` + economy **H2** — see `24`, `25`).
**Branch:** `feat/skyjump-v2-5x5`
**Phase 6:** FROZEN (PURE W2 + W-CHARGE, doc 21).
**Artifacts:** `math/games/0_0_poc/phase7a_research/` (historical PT2)
**Asset contract:** `23_SYMBOL_ASSET_MANIFEST.md` + checklist `26_PRODUCTION_ASSET_TODO.md` (**ART LOCK APPROVED**; WAIT = NONE)

Do **not** treat this document as promoted live math. No production World Record, books, or LUT in 7A.

### Human decision / supersession

- Phase 7A **C8** (additive) → superseded by 7A.1 (bonus-line PT2 Δ).
- Phase 7A.1 **C2** / historical PT2 → superseded by 7A.2 **PT2H_LADDER** (hierarchy repair) + **H2**.
Historical C8 / PT2 rows below are retained as design history only.

---

## 1. Starting certified stack

| Component | Value |
| --- | ---: |
| BASE | 71.212% |
| Phase 5B | +17.92705 pp |
| Phase 6 PURE W2 | +4.689 pp (SE 0.078) |
| **Current game RTP** | **93.828%** |
| Point reserve to 96.50% | 2.672 pp |
| Safe reserve (point − 1.96×SE) | ~2.518 pp |

---

## 2. Canonical doc cleanup

Audited `01`, `02`, `03`, `05` against Phases 4–6C.1. Stale items corrected:

| Item | Fix |
| --- | --- |
| A. REJUMP / WIND_KEY “reserved” | Split: BASE Mystery excludes them; FS Phase 6 includes them |
| B. Rejump-before-Judge | Replaced with **R-BATCH** order |
| C. Persistent max 3 | Live **`maxPersistentTargets = 2`** |
| D. Wind | Documented **W-CHARGE + PURE W2** (already in 01 §7.H) |
| E. Wind/Rejump inactive in FS | Removed; Phase 6 live |
| F. RGS book model | One paid play → one full-round book → one end-round |
| G. Gate max floor | Live **`gateMaxFloor = 3`** (not design-6) |
| H. Provisional RTP | Distinguished from certified interim **93.828%** |
| 05 Phase 4 remainder / Phase 6 numbering | Superseded / split mechanics vs books |

Historical dated audits (12–21) were **not** rewritten.

**Cleanup: PASS**

---

## 3. Symbol roster lock

Frozen identities (no renames):

**Regulars:** P1 Flying Jumper, P2 Crystal Trophy, P3 Golden Helmet, M1 Jumping Skis, M2 Flight Goggles, M3 Ski Boots, L1 Wind Sock, L2 Snow Badge, L3 Start Flag

**Scatter / feature:** S Competition Bib, C Coach Signal, Y Snowburst Mystery, Thermal Lift, Gate Upgrade, Judge, Head Judge, Rejump, Wind Key

**Tokens:** T1–T6 including `TOKEN_WORLD_RECORD` (tier 6 token — **not** the instant max-win special)

**Board special:** `SPECIAL_WORLD_RECORD` (player label: World Record)

**ART LOCKED NOW:** all of the above + UI stage/tier emblems (see doc 23).

**WAIT:** NONE

---

## 4. SPECIAL_WORLD_RECORD design

| Field | Spec |
| --- | --- |
| Internal id | `SPECIAL_WORLD_RECORD` |
| Player label | World Record |
| Effect | Settle economic round to `maxWinX` (**50,000×**) |
| Book | Emit `skyjumpWorldRecord` → terminate remaining FS / Rejump / feature chain → one final settlement |
| Cap | Must not double-pay if round already at cap; award fills to 50,000× total |
| Distinct from | `TOKEN_WORLD_RECORD` (T6 Flight Token) |

### Architecture comparison

| Option | Idea | Verdict |
| --- | --- | --- |
| WR-A | Ultra-rare BASE+FS board special | Contaminates BASE feel; harder isolation |
| WR-B | FS-only flat rate | Simple but not progressive with tier fantasy |
| **WR-C** | **FS-only, tier-weighted** (LH rare → PV highest) | **Recommended** |
| WR-D | World Cup / Perfect V only | Too narrow; LH/SF never see it |

**Preferred generation:** independent Bernoulli (or equivalent) on Free Spin boards, **not** a Mystery result, **not** reel-frequency mutation. Math owns trigger + optional display position; frontend owns presentation only.

### RTP band (analytical)

Using incremental EV ≈ 50,000 − E[accrued] with E[accrued]≈12× (prior winnings already present when WR fires):

| Target WR pp | p(paid round) | 1 in N paid | p(bonus) | 1 in bonuses | P(WR\|PV start) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.35 | 7.00e-8 | 14.3M | 1.07e-5 | 93k | ~1.17e-4 |
| 0.40 | 8.00e-8 | 12.5M | 1.23e-5 | 82k | ~1.34e-4 |
| 0.45 | 9.00e-8 | 11.1M | 1.38e-5 | 73k | ~1.50e-4 |
| 0.50 | 1.00e-7 | ~10.0M | 1.53e-5 | ~65k | ~1.67e-4 |
| **0.55** | **1.10e-7** | **~9.1M** | **1.69e-5** | **~59k** | **~1.84e-4** |

Tier-relative intensities (WR-C): LH 1 : SF 3 : WC 6 : PV 12 (normalized to hit target bonus rate).

Natural MC cannot certify WR EV — use exact frequency × incremental fill.

DEV fixture (design only): forced `SPECIAL_WORLD_RECORD` → `skyjumpWorldRecord` → total 50,000× → terminate → one settlement.

---

## 5. Premium paytable research (paytable-only)

Exact line RTP on live Coach E strips: **59.696%**. Awards monotonic (3≤4≤5) on 0.10× grain. Reel frequencies unchanged.

| | Line RTP | Premium | Mid | Low | Δ vs PT0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| **PT0** (control) | 59.696% | 2.447% | 10.697% | 46.553% | 0 |
| **PT1** (neutral) | 59.688% | 4.583% | 12.283% | 42.822% | −0.008 pp |
| **PT2** | 60.288% | 5.896% | 13.697% | 40.695% | **+0.592 pp** |
| **PT3** | 60.688% | 6.995% | 12.997% | 40.695% | **+0.991 pp** |

PT1–PT3 raise P1/P2/P3 awards for feel (e.g. P1 5oak 36→150/200/250). Mid 4/5 recover RTP lost from light L cuts. P1 remains rare on strips — paytable-only cannot make P1 a major RTP bucket without reel edits (optional later; **not** required for art lock).

**Recommended paytable for combined economy:** **PT2**.

Premium hit metrics (PT2, analytical):

| Symbol | P(any line) | P(4oak≈) | P(5oak≈) | Avg payout \| match |
| --- | ---: | ---: | ---: | ---: |
| P1 | 1.73e-4 | 2.82e-6 | 5.53e-8 | ~10.7× |
| P2 | 1.38e-3 | 5.53e-5 | 2.21e-6 | ~7.2× |
| P3 | 7.22e-3 | 4.55e-4 | 2.79e-5 | ~6.5× |
| Premium union | ~0.876% | — | — | — |

Expected lines paying ≥5× / ≥10× / ≥25× / ≥50× (PT2): ~0.0149 / 0.00145 / 0.00054 / 3.3e-5 (vs PT0 ~0.00089 / 3.3e-5 / ~0 / 0).

Awards live in `phase7a_research/paytables.json` (research only).

---

## 6. Optional bonus-body tuning

Existing mechanics only: T1/T2 **face** redistribution + tiny T1→T2 tier-weight shift. **T5/T6 fixed.** No new symbols.

| | n | Median | P25 | P75 | P99.9 | Cap p | Δ pp vs BODY0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BODY0 | 100k | 9.5 | 5.5 | 19.2 | 1993 | 5e-5 | 0 |
| BODY1 | 100k | 9.7 | 5.5 | 20.2 | 2076 | 5e-5 | +1.337 |
| BODY2 | 100k | 9.9 | 5.5 | 22.2 | 2257 | 5e-5 | +3.820 |
| BODY0 | **1M** | 9.5 | 5.5 | 19.2 | 2069 | 1.8e-5 | 0 |
| **BODY1** | **1M** | **9.7** | 5.5 | 20.2 | 2152 | 1.8e-5 | **+1.359** |

BODY2 is too hot for this phase. **Recommend BODY1** (1M paired confirms body uplift; cap rate unchanged vs BODY0).

---

## 7. Combined candidates

Body Δ uses **1M** BODY1 (+1.359 pp). Paytable Δ analytical.

| ID | WR | PT | Body | Projected RTP | Cal. reserve | Notes |
| --- | --- | --- | ---: | ---: | ---: | --- |
| C1 | 0.40 | PT1 | BODY1 | 95.579% | 0.921 | under preferred band |
| C2 | 0.45 | PT2 | BODY1 | 96.229% | 0.271 | near band |
| C3 | 0.50 | PT2 | BODY1 | 96.279% | 0.221 | WR in preferred 0.35–0.50; just under RTP band |
| C4 | 0.40 | PT3 | BODY0 | 95.219% | 1.281 | no body uplift |
| C5 | 0.35 | PT2 | BODY0 | 94.770% | 1.730 | conservative |
| C6 | 0.40 | PT1 | BODY0 | 94.220% | 2.280 | reserve-max |
| C7 | 0.50 | PT3 | BODY1 | 96.678% | −0.178 | overshoots |
| **C8** | **0.55** | **PT2** | **BODY1** | **96.329%** | **0.171** | **Recommended — in preferred RTP band** |

**Recommended final economy candidate: C8**

- WR-C @ **+0.55 pp** (within research 0.25–0.60; slightly above preferred initial 0.35–0.50)
- Paytable **PT2** @ **+0.592 pp**
- Body **BODY1** @ **+1.359 pp** (1M paired)
- Projected **~96.329%**
- Calibration reserve **~0.17 pp** (inside 0.10–0.25 preference)

Alternate if human prefers WR ≤0.50: **C3** (~96.279%, reserve ~0.22 pp).

Player-feel: improves premium awards and ≥5×/≥10× line presence, slightly lifts bonus median (9.5→9.7), preserves Phase 6 visibility, keeps WR ultra-rare, no new symbols beyond WR special.

---

## 8. Cap interaction

| Path | Notes |
| --- | --- |
| Natural | Existing T5/T6 + Thermal + Head Judge + Flight Mult + Rejump; Phase 6C.1 cap ~1e-5, drag ~0.068 pp |
| World Record | Settles round to 50,000×; incremental = 50,000 − accrued; no second pay if already capped |
| Combined | WR frequency so low that natural + WR double-count is negligible; still enforce terminate-on-WR |

---

## 9. Feature buys

**Not priced.** Any derived buy costs would be NON-FINAL.

---

## 10. Phase 6 config

**Unmodified.**

---

## 11. Ready for Phase 7B?

**YES** — pending human approval of:

1. Economy candidate **C8** (or **C3** if WR must stay ≤0.50)
2. WR architecture **WR-C**
3. BODY1 vs BODY0 preference

Phase 7B would implement WR + promote research paytable/body — not started here.
