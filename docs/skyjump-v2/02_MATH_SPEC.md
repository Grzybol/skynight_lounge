# SKYJUMP V2 — Math Specification

**Status:** Canonical math design. **Phase 7C.4 production math frozen** (`mathVersion: 2`). Live economy: **PT2H_LADDER + BODY1 + WR-C H2** + Phase 6 PURE W2 (`featureEconomyVersion: 2`). **BASE actual LUT RTP 96.3907%**. Buy costs promoted (PRICE_A). Do not mutate V1 math.
**Companion:** `01_GAME_DESIGN_SPEC.md` is the mechanic source of truth. This file owns evaluation, RTP method, caps, and unresolved math choices.

No final production math is invented here. Example splits and paytable **shapes** are non-binding.

---

## 1. Lineage — do not touch frozen V1

V1 canonical file `math/games/0_0_poc/skyjump_config.json` is **mathVersion 3**, frozen (weather, hills, multiplier tables, buy costs 1 / 3 / 6 / 11.3 / 22.6, eventSchemaVersion 1).

V2 starts a **new lineage**:

| Field | V2 start |
| --- | --- |
| File | `math/games/0_0_poc/skyjump_v2_config.json` (new; V1 file untouched) |
| `lineage` | `skyjump-v2` |
| `mathVersion` | `2` (Phase 7C.4 production freeze) |
| `eventSchemaVersion` | `2` |
| `gameID` | Keep `0_0_poc` until Stake ACP issues a new id. Do not invent credentials |

Python resolver: `skyjump_v2_resolve.py` (new).
Reel strips / exact RTP / events: `skyjump_v2_reels.py`, `skyjump_v2_exact.py`, `skyjump_v2_events.py`.
Do not edit `skyjump_resolve.py` tables to “add paylines”.

Stake play keys for V2 (when published) are the V2 `rgsKey` set. Publishing V2 as the same ACP game as V1 is an external product decision; math must be able to live beside V1 in this repo forever.

---

## 2. Evaluation contract

### 2.1 Board

- 5 reels × 5 rows.
- Cell is one of: regular `P1–P3, M1–M3, L1–L3`, Flight Token (`T1–T6` + value), special, Mystery, Scatter.
- No wilds in V2.0. Do not call `math/src/calculations/lines.py` wild path unless wilds are later added in a written amendment.

### 2.2 Paylines

28 lines, left-to-right, 3/4/5 of a kind, must start on reel 0, adjacent, no gaps. Scatter ignored. Multiple overlapping lines sum.

Shared JSON:

```json
"paylines": {
  "1": [0, 0, 0, 0, 0],
  "28": [0, 2, 4, 2, 0]
}
```

Frontend imports the same object. A TS helper may highlight lines for fixtures; **money is never computed from a second FE paytable**.

### 2.3 Configurable paytable

**LIVE production table (Phase 7C.4 freeze):** `candidateOrigin: PT2H_LADDER` · `status: PHASE 7B LIVE PT2H_LADDER` · `nonFinal: false` in `skyjump_v2_config.json`.

```
paytable[symbol][3 | 4 | 5] = multiplier of nominal bet
```

| Symbol | 3-of-kind | 4-of-kind | 5-of-kind |
| --- | ---: | ---: | ---: |
| P1 `FLYING_JUMPER` | 10.0 | 50.0 | 200.0 |
| P2 `CRYSTAL_TROPHY` | 6.0 | 33.2 | 100.0 |
| P3 `GOLDEN_HELMET` | 5.0 | 25.2 | 65.0 |
| M1 `JUMPING_SKIS` | 1.6 | 6.5 | 24.6 |
| M2 `FLIGHT_GOGGLES` | 1.3 | 6.0 | 21.6 |
| M3 `SKI_BOOTS` | 1.0 | 5.5 | 19.1 |
| L1 `WIND_SOCK` | 0.8 | 1.7 | 3.6 |
| L2 `SNOW_BADGE` | 0.5 | 1.3 | 2.7 |
| L3 `START_FLAG` | 0.3 | 1.1 | 2.0 |

All awards are 0.10×-grain. Do **not** use the historical Phase 2 provisional table below for production RTP or code.

<details>
<summary>Historical — Phase 2 provisional table (superseded; do not use)</summary>

Phase 2 once labelled `PHASE 2 PROVISIONAL BASE MATH` / `nonFinal: true`. Kept for audit trail only (`08_PHASE2_BASE_MATH_REPORT.md`).

| Symbol | 3 | 4 | 5 |
| --- | ---: | ---: | ---: |
| P1 | 4.0 | 11.0 | 36.0 |
| P2 | 3.2 | 6.6 | 18.0 |
| P3 | 2.4 | 5.5 | 13.5 |
| M1 | 1.6 | 3.3 | 7.2 |
| M2 | 1.3 | 2.8 | 5.4 |
| M3 | 1.0 | 2.2 | 4.5 |
| L1 | 0.8 | 1.7 | 3.6 |
| L2 | 0.6 | 1.3 | 2.7 |
| L3 | 0.5 | 1.1 | 2.2 |

</details>

The Phase 1 file `skyjump_v2_dev_paytable.json` stays **FIXTURE/TEST ONLY**.

### 2.4 Scatter

Count visible `COMPETITION_BIB` on the **initial** 5×5 reveal of that spin. Perfect V is the exact five-cell pattern `[0,1,2,1,0]`. Scatter does **not** participate in paylines and has **no Phase 2 payout**. Rejump does not add scatters (game spec §7.J). Phase 2 measures frequency only; it does not start Free Spins.

Phase 2 (Coach A strips): 3+ scatter ≈ 1 in 130.6; Perfect V ≈ 1 in 380 million (`08_PHASE2_BASE_MATH_REPORT.md`). Phase 4B Coach **E** strips (120/120 on reels 2+4): 3+ scatter ≈ **1 in 153.15**; Perfect V ≈ **1 in 506 million**. Scatter strips themselves were not edited; rates shift with strip composition. See `12_PHASE4B_BASE_FEATURE_IMPLEMENTATION.md` §8.

### 2.5 Phase 4B Coach / Mystery / paying features (provisional)

**Promoted economy (Phase 7B → 7C.4 freeze):** `PT2H_LADDER` + `BODY1` + `WR-C H2` · `featureEconomyVersion: 2` · **`mathVersion: 2`**.

**Phase 7C.4 production books/LUT:** `stake-upload-final/math/`. Buy costs: LH **30.2** / SF **196.9** / WC **412.8** / PV **1369.1**. **BASE actual LUT RTP 96.3907%**. Cross-mode spread **0.1556 pp**. See `32_PHASE7C4_PRODUCTION_MATH_FREEZE.md`. (Historical 7C research under `library_v2/` / `phase7c*_research/` is non-production.)

Locked evaluation order on a paid BASE spin:

```
initial board → line wins → scatter (initial reveal) → Coach → Mystery transform
→ Mystery resolve (BASE: token | thermal | gate | judge | head judge;
  Free Spins Phase 6 also: REJUMP | WIND_KEY)
→ Gate upgrades → Wind Key (FS) → Thermal effective values → Judge / Head Judge collections (R-BATCH)
→ optional Rejump → new batch → accumulate feature win → max-win cap → result
```

- Coach **model E** on reels **2 and 4** (120/120 strips). P(any) ≈ 8.16%; P(≥2) ≈ 0.174%. Theoretical line RTP ≈ **59.70%** on Coach E strips.
- Mystery is not a strip symbol. Phase 4B uses an **independent** result table (not conditional collectors). Free Spins Phase 6 adds `REJUMP` / `WIND_KEY` to FS tables only; BASE F01 weights unchanged.
- Tokens do not auto-pay. **Judge / Head Judge** collect effective values into `totalFeatureWinX`. Uncollected tokens do not pay and do not persist to the next spin.
- Lean paying token tiers /1e6: T1 999400, T2 400, T3 120, T4 40, T5 32, T6 8. Phase 3 research-heavy tables archived under `flightTokens.phase3LatentResearch`.
- Provisional BASE feature RTP ≈ **11.82%** (Phase 4A.2 research historical). Pre-promotion certified stack: BASE **71.212%** + Phase 5B **17.92705 pp** + Phase 6 **+4.689 pp** → **93.828%**. Phase 7B adds PT2H_LADDER + BODY1 + WR-C H2 → projected **~96.290%** (doc `27`; not LUT-certified).
- Cap: **`maxWinX = 50000`**. Live Gate clamp: **`gateMaxFloor = 3`**. Live persistent targets: **`maxPersistentTargets = 2`**.
- Full implementation report: `12_PHASE4B_BASE_FEATURE_IMPLEMENTATION.md`. Phase 3 latent report: `09_PHASE3_COACH_MYSTERY_TOKEN_REPORT.md`.

---

## 3. Feature mathematics (symbolic)

All magnitudes below are **legal sets**, not weights.

### 3.1 Flight Tokens

Legal values by tier as in the game spec. Generation is a weighted table `tokenTierWeights[mode][bonusTier][tokenFloorTier]` plus `tokenValueWeights[tier]`.

Effective value:

```
effective(token) = token.value * product(thermal.mult for thermal neighbouring token)
```

V2.0 product stacking is a **hypothesis**. Kill-test in §8.

### 3.2 Thermal Lift

Legal: `{2,3,4,5,10,20}`. Neighbourhood: Moore neighbourhood, self excluded.

### 3.3 Gate Upgrade

`tokenFloorTier ∈ [1, gateMaxFloor]`, live **gateMaxFloor = 3**. Visible below-floor tokens: replacement pair `(tier, value)` **in the event**. The replacement must be a legal value for a tier `≥ newFloor`.

### 3.4 Collectors

```
judgeWin = sum(effective(token) for visible tokens)
headJudgeWin = judgeWin_pass1 + judgeWin_pass2
```

V2.0: tokens remain; passes consecutive ⇒ `headJudgeWin = 2 * judgeWin` unless intervening events exist.

### 3.5 Flight Multiplier

```
G = RUN_UP * TAKEOFF * FLIGHT
featureAward' = featureAward * G
```

**V2.0: G does not multiply line wins.** Revisit only after a written RTP/variance audit. If G also hit lines, BASE line RTP would couple to a persistent (Perfect V) or intra-spin multiplier and the 55–65% line bucket would become un-isolatable.

Stage upgrade distributions: K1 ladder `{1,2,3}` with **W-CHARGE** (two Keys per step) and **PURE W2** selection (lowest-value eligible; charge ignored when choosing). Wind Key events include `selectedStage`, `action` (`CHARGE`|`UPGRADE`), old/new value, old/new charge, and old/new global multiplier. Global = product of stage values only.

### 3.6 World Record special — `SPECIAL_WORLD_RECORD`

Payout settles the economic round to configured `maxWinX` (50,000×). Terminate remaining feature chain. Frequency must be small enough that incremental fill `E[50000 − accrued]` × `P(WR)` fits the cap/remainder RTP budget (see §6.3). Distinct from `TOKEN_WORLD_RECORD` (T6).

**Live (Phase 7B):** architecture **WR-C** (FS-only, tier-weighted 1 : 3 : 6 : 12, after board / before lines). Candidate **H2** @ **+0.457 pp** WR contribution; projected full-game **~96.290%**. Distinct from T6 `TOKEN_WORLD_RECORD`. See `27`.

### 3.7 Feature-chain depth

`maxFeatureChainDepth = 8` (configurable). Each Coach→Mystery→…→Rejump loop that returns to evaluation counts as a cycle. Books that hit the cap already contain settlement. Simulator must assert no generated round exceeds the cap without a terminal flag.

### 3.8 Rejump refill

Math emits `clearedPositions[]` and `replacements[]` of equal length. New specials are legal. New scatters are **illegal** in V2.0.

---

## 4. Free Spins and buy modes

Bonus EV is a function of:

- remaining spins
- `tokenFloorTier`
- `persistentMysteryTargets`
- Flight Multiplier persistence (Perfect V)
- Coach intensity
- guaranteed Gate Upgrade flags

State space is large. Do not enumerate full bonus trees exactly (see §7).

Buy modes `LARGE_HILL` / `SKI_FLYING` / `WORLD_CUP` / `PERFECT_V` are **feature buys of those bonuses**, not V1 hill-table buys.

```
cost_mode ≈ E[bonus payout in ×] / targetRtp
```

Then snap to Stake-legal cost granularity and re-check:

- per-mode RTP in 96.40%–96.60% preferred band
- cross-mode spread ≤ 0.50 percentage points
- never aim at 96.70% ceiling

`BASE` cost is 1.0×. **Promoted buy costs (Phase 7C.4):** LH **30.2** / SF **196.9** / WC **412.8** / PV **1369.1**. Actual LUT RTP: BASE **96.3907%**, LH **96.3802%**, SF **96.5029%**, WC **96.5358%**, PV **96.5347%** (cross-mode spread **0.1556 pp**). Publication package: `stake-upload-final/math/`. See `32_PHASE7C4_PRODUCTION_MATH_FREEZE.md`.

V1 `MULT_10_100` and `MULT_20_200` are removed from V2 publications.

---

## 5. Retrigger / upgrade — two options, one recommendation

### Option A — any Scatter during bonus upgrades one tier

- Simple to explain
- Scatter hit rate on a 5×5 with 10 spins and elevated Coach/Mystery density is hard to keep tiny
- Expected upgrades per bonus ≈ `10 * P(≥1 scatter)` which is often ≫ 1 if 3-scatter base triggers exist
- Almost every Large Hill buy would become Perfect V unless scatters are nearly absent in bonus (bad gameplay)

**Verdict:** mathematically awkward. Not recommended.

### Option B — 3+ scatters on a Free Spin initial reveal retrigger and/or upgrade

Proposed V2.0 rules (still not production-weighted):

| Scatters on FS spin (initial reveal) | Effect |
| ---: | --- |
| 0–2 | No change |
| 3 | +10 spins, **same** tier |
| 4 | +10 spins, upgrade one tier (cap Perfect V) |
| 5, not V pattern | +10 spins, upgrade to at least World Cup |
| Perfect V pattern | +10 spins, upgrade to Perfect V |

Why this is more controllable:

- Uses the same 3-scatter language as the base trigger
- `P(3+ scatters | bonus strips)` can be tuned independently of “any scatter”
- Retrigger spin-count inflation is a standard EV term: `E[spins] = 10 / (1 - p_retrigger)` if upgrade is ignored; upgrades are a separate rare term
- Perfect V remains a distinct ultra-rare pattern

**Historical recommendation: Option B.** Phase 5A measured that table and did not promote it.

**Phase 5B implemented rule: U1** on candidate `FS5A_U1_P2_M40_mid_E15j2`. The +10 / scatter-count table above is not live.

| Scatters on a Free Spin initial reveal | Effect |
| ---: | --- |
| 0–2 | No change |
| 3+ at Large Hill, Ski Flying, or World Cup | +5 spins, upgrade one tier, active next spin |
| 3+ at Perfect V | +5 spins, tier stays Perfect V |

Awarded spins stop at 40. Direct Perfect V on the paid spin overrides the ordinary 5-Scatter → World Cup classification. Trigger-spin line and BASE feature wins stay in BASE RTP and are not added again as Free Spin award. Weighted core bonus EV and the RTP reserve are in `15_PHASE5B_FREE_SPIN_IMPLEMENTATION.md`.

---

## 6. RTP / Stake constraints

From ACP / V1 experience:

| Constraint | Value |
| --- | --- |
| Allowed RTP | 90.00% – 96.70% |
| Cross-mode spread | ≤ 0.50 pp |
| V2 production target | **≈ 96.50%** |
| Preferred band per mode | **96.40% – 96.60%** |
| Do not aim at | 96.70% ceiling |
| BASE cost | 1.0× |

Production RTP is computed from **actual LUT / book weights**, not from config comments.

### 6.1 Are the suggested BASE buckets sensible?

Brief suggested:

| Bucket | Suggested |
| --- | --- |
| Normal paylines | ~55–65% |
| Base-game specials / tokens | ~8–15% |
| Free Spins | ~20–30% |
| Cap / rounding | small |

**Analysis (non-binding):**

- A 5×5 28-line game with **meaningful** bonus play typically cannot put 80%+ RTP on lines without making FS feel like a side show. 20–30% FS is the right **intent**.
- 55–65% lines + 8–15% base features + 20–30% FS = 83–110% before overlap. The bands overlap on purpose; a consistent centre is **~60% / ~12% / ~24% / ~0.5% remainder = 96.5%**.
- If base tokens include 10,000×–50,000×, the 8–15% feature bucket is dominated by the tail unless those values are almost FS-only. **Recommendation:** T5–T6 extremely rare in BASE; most T4+ live in bonus. Otherwise BASE variance will either blow the feature budget or starve FS.
- 50,000× cap: `P(hit cap) * 50000` must sit in the remainder + tail of features. If `P(cap) = 1e-6`, that is 5% RTP from cap alone — **too much**. Ballpark for a 50,000× at 96.5% with a small tail budget (~0.3–1.0% RTP) is `P(cap) ~ 6e-8 to 2e-7` (one in ~5–15 million base spins), unless cap is mostly reached by scaled-down paths (e.g. 1,000× * G) rather than World Record.
- **World Record special** at 50,000× is a Dirac. Treat it as a named cap event with frequency in that same order, or make it bonus-only.
- Multiplicative Thermals (20×) on T6 (50,000×) **always cap**. That is acceptable only if P(T6 ∧ thermal neighbour) is inside the cap budget; otherwise T6 should not spawn next to Thermal, or T6 should be FS-only, or stacking should change.

**Conclusion:** the buckets are a reasonable **design split** if high token tiers and World Record are tail-controlled. They are not a substitute for a solver.

### 6.2 Free Spins must matter

FS should be a large, desirable RTP slice (target centre ~25% of total RTP). Buy-bonus pricing then has something real to sell. Do not dump leftover RTP into lines to make BASE “feel safe”.

### 6.3 Cap

Provisional `maxWin = 50000` (× nominal bet). All paths:

```
settled = min(lineWin + featureWinAfterG, maxWin)
```

Book emits `skyjumpCapReached` when clamped, then `wincap` if that is still the Stake settlement signal (keep V1’s `wincap` + `setTotalWin` + `finalWin` pattern).

---

## 7. Computation strategy — exact enumeration is not the V2 backbone

V1 enumerated weather × slots × multiplier tables. A 5×5 board with 15+ cell types is `N^25` and **not enumerable**. Persistent bonus state makes full-round enumeration worse.

| Method | Use for | Do not use for |
| --- | --- | --- |
| Exact enumeration | Tiny isolated tables: token-value given tier; Thermal legal set; 28-line win **given a frozen board** | Full BASE generator; FS trees |
| Analytical EV | Line hit rates from independent reel strips (if strips are independent); scatter trigger P if strips independent | Feature chains with Rejump |
| Deterministic simulation | Feature chains, FS, collectors, G, cap | Replacing LUT weights with “we simulated once on a laptop” |
| Weighted production books / LUT | What Stake actually plays | Config-estimate RTP |
| Reproducible seeds | Every sim, book writer, audit | `Math.random` / unseeded Python |
| Stratification / importance sampling | Rare Perfect V, World Record, cap hits | Everyday line hits |
| ≥ 100,000 outcomes **per mode** | Minimum published / test LUT size | Claim of certified RTP by itself |
| Separate large Monte Carlo | Verification vs LUT (millions of spins, seed recorded) | Shipping as the game |
| Max-win / cap frequency verification | Mandatory before ACP | Guessing from one WR event |
| Replay determinism | Same book + reducer ⇒ same totals | Frontend clocks |

### 7.1 Recommended pipeline

1. Design **reel strips** (or cell-weight models) per mode / bonus tier / `tokenFloorTier`.
2. **Line engine** (no wilds) + scatter counter on the initial board.
3. **Feature-chain simulator** (pure functions, seeded) emitting the event protocol.
4. Draw ≥ 100,000 **complete paid rounds** per mode (BASE includes natural FS when triggered; buy modes start already in bonus).
5. Compress to Stake books + LUT weights. RTP := weighted mean of `payoutMultiplier / cost`.
6. Independent MC (different seed family) must match LUT RTP inside a stated error bar.
7. Force / stratify tails: Perfect V, WR, cap, Head Judge + high G.

### 7.2 SDK lines helper

`math/src/calculations/lines.py` is a farmer **wild-aware** engine. V2 may:

- write a SkyJump-specific `evaluate_paylines()` with **no wilds**, reading canonical JSON, or
- use the SDK class only after proving wild keys are empty and scatter is skipped

Recommendation: **SkyJump-specific evaluator** so farmer wild/global-mult behaviour cannot leak. Keep SDK as a reference for event shape (`winInfo` analogue → `skyjumpLineWins`).

### 7.3 Books vs live resolve

Production frontend plays books. `/dev-preview` may call the V2 resolver locally (DEV + localhost), never as published RTP.

---

## 8. Dangerous assumptions and required tests

| ID | Assumption | Risk | Required test / correction |
| --- | --- | --- | --- |
| M1 | Multiplicative Thermals | 20×^n on a token → instant cap, fat tail | Measure P(cap), feature RTP; fallback: max-one-thermal (highest), or additive, or cap per-token before G |
| M2 | Tokens remain after Judge | Head Judge = 2× Judge; two Judges in one chain double-dip | Include in EV; if too rich, mark consumed |
| M3 | Flight Multiplier on features only | If later applied to lines, all line RTP moves | Keep V2.0 default; separate study |
| M4 | Chain depth 8 | Rare loops of Rejump + Coach can explode presentation and EV | Hard cap in generator; assert terminal state |
| M5 | Persistent Mystery max 2 + Coach every Perfect V spin | Board can become Mystery-dense | Simulate Perfect V RTP isolation |
| M6 | 50,000× ceiling | WR + T6 + G + Head Judge all hit the same cap | One cap at the end; no stacking past maxWin |
| M7 | Exact enum leftover from V1 | Engineers may try to enumerate 5×5 | Do not; sim + LUT |
| M8 | Buy costs copied from V1 (3 / 6 / 11.3 / 22.6) | V1 costs are hill/mult tables, wrong game | Recalculate after bonus EV |
| M9 | Scatter-on-Rejump farming | Unbounded FS | V2.0 forbids new scatters on refill |
| M10 | Cross-mode 0.50 pp | Perfect V buy EV vs BASE natural FS | Price buys from EV; maybe disable Perfect V buy if unpriceable |

---

## 9. Amount / rounding

Keep V1 book amount convention unless Stake changes it:

- `bookAmountMultiplier = 100` ⇒ book `100` = 1× nominal bet
- Python 3 / Stake half-to-even rounding in both TS and Python (`roundBookAmount` parity)
- Wallet uses `API_AMOUNT_MULTIPLIER` separately

V2 tests must copy the V1 rounding parity tests, not re-derive a third convention.

### STAKE/RGS PRODUCTION CONSTRAINT — payout grain 0.10×

Observed from V1 production-book work (`verify_lookup_format` in the Stake math-sdk):

- LUT / book `payoutMultiplier` is an integer with `100` = 1.0× nominal bet
- Non-zero payouts must be `>= 10` and **`payoutMultiplier % 10 == 0`**
- That is a **0.10×** settlement grain, not 0.01×

V1 mathVersion 3 tables emit 0.01× outcomes (`0.252 → 25`, and `25 % 10 != 0`). That is why V1 LUTs fail the local RGS upload-guard without retuning economics.

**V2 must not repeat that design.**

- Design paytable rows, token values, Thermal products, collectors, Flight Multiplier, and max-win so that **every settleable award already lands on 0.10×** (integer `payoutMultiplier` divisible by 10).
- Do **not** design on arbitrary 0.01× precision and quantize only at book-write time. End-of-pipe rounding is an economic change and will desync RTP vs the solver.
- Phase 2 regular awards already obey this grain. Future feature awards must as well.

If ACP later documents a different grain, amend this section in writing before changing the solver.

### Known risks for later phases (do not silently drop)

1. Stake/RGS payout grain **0.10×** (this section).
2. Rejump returning to payline evaluation awards **another** line-win pass; RTP must budget it.
3. Thermal multipliers must **not mutate stored token face values**; recompute effective value from face × Thermals.
4. ~~Free Spin settlement requires replacing V1 `checkIsBonusGame: (_bet) => false`.~~ **RESOLVED (Phase 5B+ / 7C.4).** V2 uses `skyjump_v2/checkIsBonusGame.ts` over one-book full-round Free Spin events. Do **not** flip `checkIsBonusGame` back to a V1 false stub.
5. ~~One-book-per-paid-round vs per-Free-Spin RGS `play()` still needs ACP confirmation.~~ **INTERNAL ARCHITECTURE FROZEN (Phase 7C.4).** Contract: one paid play → one complete economic-round book (BASE trigger + entire FS when applicable, or direct buy bonus) → one settlement / end-round. External Stake ACP session validation remains a Phase 9 checklist item; it does **not** reopen the internal book shape.

---

## 10. What “done” means for math (later phases)

- Configurable tables only; no hardcoded UI numbers
- LUT RTP in band, spread legal, cap frequency documented
- Replay of any published book through the reducer matches `finalWin`
- V1 JSON hash unchanged
