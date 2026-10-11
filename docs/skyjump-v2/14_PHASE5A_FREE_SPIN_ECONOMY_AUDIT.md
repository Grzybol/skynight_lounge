# SKYJUMP V2 — Phase 5A Free Spin Economy & Progression

**Status:** RESEARCH RECORD. Phase 5B later promoted this candidate. The tables below are the Phase 5A record and were not retuned. Implementation is `15_PHASE5B_FREE_SPIN_IMPLEMENTATION.md`.  
**Branch:** `feat/skyjump-v2-5x5`  
**Live BASE config at research time:** unchanged  
**Certified BASE SHA-256:** `d932065b36a626c7cd9a818bd8c401559e6270c434622d32d1fb640e3d8d7803`  
**Candidate later approved and promoted:** `FS5A_U1_P2_M40_mid_E15j2`

Do not generate production books or Stake LUTs from this document.

---

## 1. Accounting

The paid BASE spin that lands the triggering Scatters is already inside certified BASE RTP (line 59.6962% + capped feature 11.516% ≈ **71.212%**).

**BONUS AWARD** is only the incremental award **after** that spin:

free spins + retriggered spins + bonus upgrades + bonus-only mechanics.

Reports below are incremental bonus ×. They do **not** add the trigger-spin line, Coach, or collector win again.

Full-game target remains **96.50%**. Remaining budget before Free Spins ≈ **25.29 pp**. The full-stack implied bonus if Free Spins consumed all of it is ≈ **38.73×**. Phase 5A deliberately does **not** spend that whole budget. Rejump, Wind Key, Flight Multiplier, and Perfect-V extensions stay unsampled. Their event/state fields are schema placeholders only.

---

## 2. Exact BASE trigger mix (Coach E, frozen strips)

| Event | Absolute P | 1 in | Share of Scatter ≥ 3 |
| --- | ---: | ---: | ---: |
| Exactly 3 Scatter → **LARGE_HILL** | 0.006213590660243767 | 160.94 | **95.1592%** |
| Exactly 4 Scatter → **SKI_FLYING** | 0.000309914008370000 | 3,226.7 | **4.7462%** |
| 5 Scatter, not Perfect V → **WORLD_CUP** | 0.000006171610276640 | 162,033 | **0.09452%** |
| Direct Perfect V pattern → **PERFECT_V** | 1.9755474637131444e-09 | 506,188,800 | **0.00003025%** |
| Scatter ≥ 3 (any bonus) | 0.00652967825443787 | **153.147** | 100% |

There is no 6+ Scatter on these strips. Perfect V is a subset of exactly 5 Scatters and **overrides** the World Cup classification.

**Design implication:** ~95% of natural bonuses start on Large Hill. Large Hill has to be the game. Higher tiers cannot be the only place the bonus feels different.

Weighted FS RTP uses absolute probabilities separately. It is **not** `P(≥3) × Large Hill EV`.

---

## 3. RGS / SDK bonus-round model (local code)

Inspected, not guessed:

| Piece | What the repo actually does |
| --- | --- |
| `requestBet` | One `POST /wallet/play` debits and returns `round` (`rgs-requests.ts`). |
| Round object | `active`, `payoutMultiplier`, `state` (book / `GameState` array). Schema: `frontend/packages/rgs-fetcher/src/schema.ts`. |
| `requestEndRound` | One `POST /wallet/end-round` settles the round. No second debit. |
| `requestEndEvent` | `POST /bet/event` stores a resume index inside the **same** bet. |
| XState | `bonusWin` delays `end-round` until the book finishes; `singleRoundWin` ends immediately. `checkIsBonusGame` chooses that path. |
| Current actor | `frontend/apps/poc/src/game/actor.ts` still has `checkIsBonusGame: (_bet) => false`. |
| Ways example books | One book contains `freeSpinTrigger`, `gameType: 'freegame'` reveals, then `freeSpinEnd`. Not extra `play()` calls. |
| V2 event protocol | `03_EVENT_PROTOCOL.md` already specifies one paid book containing the base spin and the whole Free Spin sequence. |

**Supported architecture for Phase 5A math:** one economic round, cap **50,000×** shared by the trigger spin and every Free Spin, one `play()` and one `end-round`.

`/wallet/action` exists in the schema for games that need extra actions. Nothing in this repo’s SkyJump play/end-round flow requires a new `play()` per Free Spin. If ACP later forces per-spin `play()`, that is a **Phase 5B implementation blocker**, not a reason to change the 5A EV model.

---

## 4. Free Spin state (math-owned)

Serializable fields:

`bonusTier`, `freeSpinsRemaining`, `freeSpinsPlayed`, `bonusWinXRaw`, `bonusWinXCapped`, `tokenFloorTier`, `persistentMysteryTargets[]`, `coachGuaranteeState`, `guaranteedGateUsed`, `upgradeCount`, `retriggerCount`, `maxWinReached`.

Reserved, not sampled: `flightMultiplierRunUp`, `flightMultiplierTakeoff`, `flightMultiplierFlight`, `rejumpState`.

No frontend flag decides payout.

**Removed at the end of each Free Spin:** Flight Token cells, Thermal cells, Judge / Head Judge cells, current Mystery cells, current token face/effective values.

**Persists:** tier, remaining spins, `tokenFloorTier`, `persistentMysteryTargets`, `guaranteedGateUsed`, reserved future fields.

BASE tokens are not banked across spins. That stays true in the bonus. Gate persistence is the **floor tier**, not the money.

---

## 5. Tiers

All tiers start with **10** Free Spins. Count was not used as an RTP knob.

| Tier | Direct trigger | Identity in 5A |
| --- | --- | --- |
| LARGE_HILL | exactly 3 Scatter | Higher Coach than BASE. Persistent floor. No persistent Mystery types. Same Token / Thermal / Gate / Judge / Head Judge engine. |
| SKI_FLYING | exactly 4 | Large Hill + persistent Mystery targets. |
| WORLD_CUP | 5+ and not V | Ski Flying + persistent floor + one guaranteed Gate. |
| PERFECT_V | exact V pattern | World Cup + **guaranteed ≥1 Coach every Free Spin**. Natural extra Coaches still allowed. **Future EV reserve:** Wind Key / Flight Multiplier are not awarded. |

Direct Perfect V overrides scatter-count tier selection.

Duplicate persistent target behaviour compared:

- **A** — Coach may re-pick a type already persistent; that activation adds no new target (current symbols still transform).
- **B** — Coach prefers an eligible type that is not already persistent.

**B is the research default.** On the screened economies A and B produced the same weighted EV at 25k (persistence rarely fills on Large Hill, where most triggers live). B is still preferred because it does not waste a Coach once targets exist.

`maxPersistentTargets` compared at 1, 2, and 3. **2 is the recommendation.** 1 cuts Ski Flying / World Cup EV roughly in half. 3 on the hotter collector table pushed weighted EV to ~54× and wiped the future reserve.

---

## 6. Spin order (locked)

1. Math-owned board  
2. Reveal  
3. Normal paylines on the **initial** board  
4. Scatter count / Perfect V on the **initial** board  
5. Apply existing `persistentMysteryTargets` to visible regulars  
6. Resolve natural Coaches (Perfect V may synthesize one if the board has none)  
7. New persistent types may be appended (Ski Flying and above, behaviour B)  
8. Selected regulars become Mystery  
9. Resolve Mystery identities  
10. Guaranteed Gate replacement if armed and no natural Gate  
11. Gate floor upgrades from the **persisted** floor  
12. Thermal effective values  
13. Judge / Head Judge  
14. Add this spin’s incremental win to the bonus total  
15. Scatter retrigger / upgrade, stored as **next-spin** tier  
16. Decrement remaining spins, then apply pending tier if spins remain  
17. Shared 50,000× cap check  
18. Next Free Spin or settle  

No mid-spin rule change. Persistent transforms cannot delete the line win already evaluated.

**Qualifying spin for guaranteed Gate:** the first Free Spin, while the live tier is World Cup or Perfect V (including a tier that **upgraded into** those tiers), that produces at least one Mystery **and** has no natural `GATE_UPGRADE`.

Replacement rule (deterministic, safest tested):

1. Prefer a Thermal cell.  
2. Else the first Flight Token with tier ≤ 4.  
3. Never replace T5/T6.  
4. Never replace Judge / Head Judge (the judge-inclusive policy was coded and not selected).  
5. Do not add a hidden Mystery.  
6. Set `guaranteedGateUsed`. Do not guarantee again.

---

## 7. Bonus reels (research strips, not live config)

Built in memory from frozen BASE strips. Coach stops replace isolated `L3`. Scatter counts are explicit per reel. Live `skyjump_v2_config.json` is not rewritten.

| Tier | Family | P(any Coach) | P(Scatter ≥ 3) | Exact line RTP / spin |
| --- | --- | ---: | ---: | ---: |
| LARGE_HILL | `LH_C2_Smid` (2+2 Coach on reels 2 and 4) | **13.68%** | 0.8305% | **58.101%** |
| SKI_FLYING | `SF_C3_Smid` | **19.79%** | 0.8305% | **57.232%** |
| WORLD_CUP | `WC_C4_Smid` | **23.61%** | 0.8305% | **56.536%** |
| PERFECT_V | `PV_C5_Smid` plus guaranteed activation | **30.00%** natural, **100%** ≥1 activation | 0.8305% | **55.687%** |

BASE line RTP is 59.696%. Bonus line RTP is lower because Coach/Scatter replace low symbols, not because persistent Mystery deletes wins (those transforms happen after line eval).

`P(Scatter ≥ 3) ≈ 0.8305%` ⇒ about **8.0%** of a 10-spin bonus sees at least one 3+ Scatter. That is the bottom of the 8–20% visibility band. Hotter scatter (`LH_C2_Shot`, ~2.58% per spin) pushed a normal Large Hill into constant upgrades and ~45×+ weighted EV. It was rejected.

Perfect V still has a **future EV reserve**. Its direct hit rate does not justify pricing Wind Key into this core.

---

## 8. Bonus-only economy (research, not live F01)

Reusing BASE Mystery weights (Judge 85 / Head Judge 15 / 1000) at 1× token faces produced ~9× Large Hill — far under 31–34×. Core EV required a **bonus-only** table. Live BASE weights were not edited.

| Profile | Token face scale | Judge | Head Judge | Gate | Token weight |
| --- | ---: | ---: | ---: | ---: | ---: |
| `E_s3_j3` | 3.0 | 255 | 45 | 9 | 649 |
| `E_s3_j2` | 3.0 | 170 | 30 | 6 | 752 |
| `E_s25_j3` | 2.5 | 255 | 45 | 6 | 652 |
| `E_s15_j2` | **1.5** | **170** | **30** | **6** | **752** |
| `E_s25_j15` | 2.5 | 128 | 22 | 6 | 802 |

Thermal weights stay at the live F01 table.

---

## 9. Upgrade models

Next-spin activation in every model. At Perfect V, extra 3+ Scatters add spins and do not change tier.

| | 3 Scatter | 4 Scatter | 5+ / Perfect V |
| --- | --- | --- | --- |
| **U1** | +5 spins, **+1 tier** | +5, +1 tier | +5, +1 tier (5+ does not jump) |
| **U2** | +3 spins, +1 tier | +5, +1 tier | +5, **jump to Perfect V** |
| **U3** | +5 spins, **same tier** | +5, +1 tier | +5, jump to Perfect V |

On the mid scatter strips, 3 Scatter is almost the entire upgrade event. U3 therefore retriggers ~8% of bonuses but **changes tier only ~0.46%** of the time (needs 4+). U1 and U2 both upgrade ~8% of Large Hills, which is the only rate that makes Ski Flying visible from the common start.

U2’s +3 spins (instead of +5) shortens the bonus and undershoots EV. U1 is the understandable rule: **3+ Scatters = +5 spins and one tier, until Perfect V.**

Length stays tight under all three: mean spins ≈ 10.3–10.4, `P(>15) ≈ 0.6%`, `P(>30) ≈ 0` at 1,000,000 triggers. Runaway did not appear. **Production bound: 40 Free Spins.** If the bound is hit, no more spins are added; the bonus still settles. On the recommended candidate the deepest observed bonus in 1,000,000 triggers was **35**, so measured RTP lost to the bound is **~0**.

---

## 10. Finalists

Deep run: **1,000,000 mix-weighted triggered bonuses** (sampled from the exact conditional trigger mix, not from hundreds of millions of BASE spins) plus **100,000** fresh starts per tier. Seed `20260921`.

| ID | Rule | Persist | Weighted × | FS RTP | Reserve | P(tier upgrade) | LH → Ski Flying | Median | P(<5×) | Mean/median |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `FS5A_U3_P2_M40_mid_E32` | U3 | 2 | **33.00** | 21.55 pp | 3.74 pp | 0.46% | 0.46% | 11.0 | 20.7% | 3.00 |
| `FS5A_U3_P2_M40_mid_E253` | U3 | 2 | 34.73 | 22.68 pp | 2.61 pp | 0.46% | 0.42% | 12.6 | 17.7% | 2.76 |
| `FS5A_U1_P2_M40_mid_E25j15` | U1 | 2 | 34.37 | 22.44 pp | 2.85 pp | **8.02%** | **7.96%** | 9.5 | 23.0% | 3.62 |
| **`FS5A_U1_P2_M40_mid_E15j2`** | **U1** | **2** | **27.46** | **17.93 pp** | **7.36 pp** | **8.00%** | **8.10%** | **9.6** | **21.3%** | **2.86** |
| `FS5A_U3_P1_M40_mid_E32` | U3 | 1 | 27.13 | 17.72 pp | 7.57 pp | 0.46% | 0.46% | 11.0 | 20.7% | 2.47 |
| `FS5A_U2_P2_M40_mid_E15j2` | U2 | 2 | 24.53 | 16.02 pp | 9.27 pp | 8.00% | 8.05% | 9.5 | 21.6% | 2.58 |

`FS5A_U3_P2_M40_mid_E32` is the closest pure RTP fit (33×, ~4 pp reserve) and is **not** recommended. Almost every natural bonus stays Large Hill. That hides Ski Flying, World Cup, and Perfect V behind a 4-Scatter coin flip (~4.7% of triggers).

---

## 11. Recommended candidate

**`FS5A_U1_P2_M40_mid_E15j2`**

- Upgrade model **U1**
- 10 initial spins, **max 40**
- `maxPersistentTargets = 2`, duplicate behaviour **B**
- Economy `E_s15_j2` (1.5× faces, 2× Judge / Head Judge / Gate vs BASE weights)
- Mid reel family above

It misses the 31–34× band on the low side (**27.46×**, **17.93 pp**, reserve **7.36 pp**). That miss is accepted. Hitting 32–33× with U3 required a Large Hill that almost never upgrades. U1 at the hotter `E_s25_j15` profile does land at 34.4×, but the reserve falls to 2.8 pp and the mean/median ratio worsens to 3.62. The cooler U1 keeps a real upgrade (~1 in 12 Large Hills reaches Ski Flying), a cleaner tail, and room for Rejump / Wind Key / Flight Multiplier.

Feel is not a 90% dead bonus. About 21% of triggered bonuses pay under 5× and about 52% under 10×. Median is 9.6× against a 27.5× mean (ratio 2.86). Phase 5B may lift the median without switching back to U3; it should not do that by spending the whole reserve.

### Start-tier EV (100k each, incremental, cap on)

| Start | Mean × | Median | Mean spins | P(upgrade) |
| --- | ---: | ---: | ---: | ---: |
| LARGE_HILL | **23.31** | 9.20 | 10.44 | 8.10% |
| SKI_FLYING | **117.62** | 55.10 | 10.43 | 7.97% |
| WORLD_CUP | **214.71** | 87.00 | 10.43 | 8.01% |
| PERFECT_V | **577.05** | 324.00 | 10.43 | n/a (already top) |

Large Hill line contribution ≈ 0.579× per spin; feature contribution ≈ 1.66× per spin; ≈ 0.76 Mysteries per spin. Floor stays near 1 (end average **1.05**). Persistent target count at Large Hill end averages **0.12** because targets only exist after an upgrade into Ski Flying.

From a Large Hill start (100k):

- P(reach Ski Flying) **8.10%**
- P(reach World Cup) **0.666%**
- P(reach Perfect V) **0.060%**

Mix-weighted (1,000,000), which is what players actually see:

- P(upgrade at least once) **8.00%**
- P(reach Ski Flying) **12.37%** (includes the 4.75% who start there)
- P(reach World Cup) **1.05%**
- P(reach Perfect V) **0.080%**

Direct Perfect V is economically irrelevant (`P × 577× ≈ 0.000001×` of a paid spin). Upgraded Perfect V is uncommon but already inside the Large Hill / Ski Flying / World Cup means above. Do not price Perfect V as if only the 1-in-506M direct hit can reach it, and do not make it so expensive that an 8% upgrade path blows the reserve. 577× from a fresh Perfect V start is acceptable **because that path is rare even after upgrades**.

### Mix distribution (incremental bonus)

| | |
| --- | ---: |
| Mean | 27.455× |
| Median | 9.60× |
| P75 / P90 / P95 | 19.4 / 44.0 / 89.7 |
| P99 / P99.9 | 300.4 / 1,238.7 |
| P(≥10 / 25 / 50 / 100) | 48.3% / 18.8% / 8.75% / 4.48% |
| P(≥250 / 500 / 1000 / 5000) | 1.34% / 0.44% / 0.15% / 0.006% |
| P(<5×) / P(<10×) | 21.3% / 51.7% |
| P(no Coach) / P(no collector) | 21.2% / 43.7% |
| Mean spins | 10.433 |
| P(>15 / >20 / >30) | 0.61% / 0.05% / ~0 |
| Max observed / bound | 35 / **40** |
| Cap hit rate | **0.0006%** of bonuses |

Cap drag on the standalone incremental award is negligible at this rate (a handful of 50,000× hits inside 1,000,000 bonuses). Joint cap with a large **BASE trigger-spin** win was not re-simulated spin-by-spin; the engine accepts `round_prior_win_x` so Phase 5B can. Phase 4C already showed BASE cap hits are themselves rare, so the missing joint term is second order. Trigger-spin wins are not inside the 17.93 pp.

### RTP budget

| Bucket | Value |
| --- | ---: |
| BASE line | 59.6962% |
| BASE feature, capped | 11.516% |
| BASE before Free Spins | 71.212% |
| Core FS RTP (`P(trigger) × EV`) | **17.927 pp** |
| BASE + core FS | **89.14%** |
| Future mechanic reserve vs 96.50% | **7.36 pp** |

Reserve is above the 4–6 pp sketch. That is intentional headroom, not unused accident.

---

## 12. What is not done

- No production Free Spin frontend
- No live config promotion
- No books, no LUTs
- No Rejump, Wind Key, Flight Multiplier, or `SPECIAL_WORLD_RECORD` awards
- Phase 4C BASE certification hash is unchanged

Research files live under `math/games/0_0_poc/phase5a_research/`. Engine: `skyjump_v2_phase5a_engine.py`, reels: `skyjump_v2_phase5a_reels.py`, search: `skyjump_v2_phase5a_search.py`, deep run: `skyjump_v2_phase5a_finalists.py`.

**Ready for human approval of this candidate before Phase 5B. Do not start Phase 5B from this audit alone.**
