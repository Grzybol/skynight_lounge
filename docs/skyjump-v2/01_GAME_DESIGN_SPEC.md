# SKYJUMP V2 — Game Design Specification

**Status:** Canonical design spec. Phases 1–4C BASE, Phase 5B/5C Free Spins, **Phase 6 Rejump + Wind Key / Flight Multiplier (P6A1_E_E1, PURE W2 + W-CHARGE)**, and **Phase 7B promoted economy (PT2H_LADDER + BODY1 + WR-C H2)** are live on `feat/skyjump-v2-5x5`. Projected pre-book RTP **~96.290%** (not production-certified). Symbol art lock: `22` / `23`. Feature buys not priced; production books not started.
**Lineage:** SkyJump V2 (`feat/skyjump-v2-5x5` when git snapshot is possible).
**V1:** Frozen. Do not patch V1 gameplay. Do not mutate V1 math.
**Originality:** Ski-jumping terminology and mechanics only. Do not use Odin names, assets, copy, tables, or source.

If implementation disagrees with this document, the discrepancy must be resolved in writing here (or in a dated amendment) before code ships. Silent invention of mechanics is not allowed.

---

## 1. Product intent

SkyJump V1 is a sequential 6-slot ski-jump mini-game. Stake review scored gameplay as too shallow. V2 is a **proper 5×5 video slot** with:

- 28 fixed paylines
- Flight Tokens instead of generic coins
- chained specials with deterministic resolution
- persistent Free Spin progression across four hill-tier bonuses

V2 must still **feel like SkyJump**: night stadium, floodlights, ski jumper, snow, ice-blue / navy / gold palette. It is not a fruit slot and not a reskin of another studio’s feature set.

Player-facing title remains **SkyJump**. Frozen V1 `meta.altTitle = SkiFly Jackpot` is metadata debt and is not a jackpot mechanic.

---

## 2. Non-negotiable authority

| Layer | Owns | Must never own |
| --- | --- | --- |
| Math / RGS / books | Symbols, token values, Mystery results, special activation, Free Spin results, multipliers, collectors, upgrades, max win, scatter counts, feature-chain depth | Presentation timing |
| Frontend | Rendering, animation, audio, layout, turbo **timing only** | Any random outcome |
| Stake platform | Authenticate, play, end-round, balance, jurisdiction, replay index | Game rules |

Frontend never rolls:

- board symbols
- token values
- Mystery results
- special activation
- Free Spin results
- multipliers
- collectors
- upgrades
- max win
- scatter trigger / Perfect V detection

Visual reel padding for spin animation may use a **deterministic** strip derived from the book (or a hash of book id). It must never be treated as an outcome.

---

## 3. Core game

| Rule | Value |
| --- | --- |
| Reels | 5 |
| Rows | 5 |
| Evaluation | Fixed paylines, left-to-right |
| Paylines | 28 (canonical list in §4) |
| Regular win | 3, 4, or 5 matching regular symbols |
| Start | Winning sequence must begin on reel 1 (leftmost) |
| Adjacency | Symbols must continue on adjacent reels; gaps break the line |
| Scatter | Exempt from paylines |
| Simultaneous lines | Multiple paylines may pay at once |
| Overlap | Overlapping paylines are allowed |
| Aggregation | Line wins are summed |
| Wilds | **None in V2.0.** Do not enable SDK wild evaluation by accident |
| Ways / clusters | Not used |

Row indexes:

```
0 = top
1
2
3
4 = bottom
```

Board addressing is `(reel, row)` with reel `0..4` left to right.

---

## 4. Canonical 28 paylines

Store **once** in canonical V2 JSON (`paylines`). Math and frontend must read the same definitions. Do not maintain independent copies.

| ID | Rows `[reel0, reel1, reel2, reel3, reel4]` | Shape note |
| ---: | --- | --- |
| 01 | `[0,0,0,0,0]` | Top straight |
| 02 | `[1,1,1,1,1]` | |
| 03 | `[2,2,2,2,2]` | Centre straight |
| 04 | `[3,3,3,3,3]` | |
| 05 | `[4,4,4,4,4]` | Bottom straight |
| 06 | `[0,1,2,1,0]` | Peak V (also the Perfect V scatter pattern) |
| 07 | `[4,3,2,3,4]` | Inverted V |
| 08 | `[0,0,1,0,0]` | |
| 09 | `[4,4,3,4,4]` | |
| 10 | `[1,0,0,0,1]` | |
| 11 | `[3,4,4,4,3]` | |
| 12 | `[1,2,3,2,1]` | |
| 13 | `[3,2,1,2,3]` | |
| 14 | `[0,1,1,1,0]` | |
| 15 | `[4,3,3,3,4]` | |
| 16 | `[2,1,0,1,2]` | |
| 17 | `[2,3,4,3,2]` | |
| 18 | `[0,1,2,3,4]` | Diagonal down |
| 19 | `[4,3,2,1,0]` | Diagonal up |
| 20 | `[0,1,0,1,0]` | |
| 21 | `[4,3,4,3,4]` | |
| 22 | `[1,2,1,2,1]` | |
| 23 | `[3,2,3,2,3]` | |
| 24 | `[1,1,2,1,1]` | |
| 25 | `[3,3,2,3,3]` | |
| 26 | `[2,1,2,1,2]` | |
| 27 | `[2,3,2,3,2]` | |
| 28 | `[0,2,4,2,0]` | Wide V |

These are the **initial canonical V2 paylines**. Changing them later must be a JSON-only change plus parity tests. IDs stay 1–28 unless a versioned migration is written.

---

## 5. Regular pay symbols

Nine regulars. Phase 1 uses low-fidelity placeholder tiles (text ID + shape + colour). No production art in this design package.

| ID | Name | Class |
| --- | --- | --- |
| `P1` | `FLYING_JUMPER` | Highest premium |
| `P2` | `CRYSTAL_TROPHY` | Premium |
| `P3` | `GOLDEN_HELMET` | Premium |
| `M1` | `JUMPING_SKIS` | Mid |
| `M2` | `FLIGHT_GOGGLES` | Mid |
| `M3` | `SKI_BOOTS` | Mid |
| `L1` | `WIND_SOCK` | Low |
| `L2` | `SNOW_BADGE` | Low |
| `L3` | `START_FLAG` | Low |

**Phase 7A art lock:** these nine regular IDs (and the feature/token/special roster in §6–7 and doc `23`) are frozen for production symbol art. Paytable **numbers** promoted in Phase 7B as **PT2H_LADDER** (doc `27`) — identity and awards both locked for economy; reel strips unchanged.

Paytable is **configurable**, not frozen:

```
symbol → { 3: TBD, 4: TBD, 5: TBD }
```

Final payouts and reel/symbol weights are solved together for production RTP. See `02_MATH_SPEC.md`. Do not treat any example numbers in math docs as shippable.

Only regulars pay on paylines. Tokens, specials, Mystery, and Scatter do not substitute for regulars on a line.

---

## 6. Flight Tokens

Replace generic casino coins with **Flight Tokens**. Six tiers. Displayed value is a multiplier of the **nominal bet** (1× stake), included in the book. Frontend never rolls the value.

| Tier | Name | Possible displayed values |
| ---: | --- | --- |
| 1 | `ROOKIE_TOKEN` | 1× / 2× / 3× / 4× |
| 2 | `K_POINT_TOKEN` | 5× / 10× / 15× |
| 3 | `LARGE_HILL_TOKEN` | 25× / 50× / 100× |
| 4 | `SKI_FLYING_TOKEN` | 150× / 200× / 250× / 500× |
| 5 | `WORLD_CUP_TOKEN` | 750× / 1000× / 2500× / 5000× |
| 6 | `TOKEN_WORLD_RECORD` | 10000× / 25000× / 50000× |

- Token frequency and value weights are configurable and **not** production-final.
- Phase 4B (BASE): Flight Tokens **do not automatically pay**. Face value sits on the board until a **Judge** or **Head Judge** in the same spin collects effective values into `totalFeatureWinX`. Tokens without a collector remain visible but **uncollected** — there is no cross-spin token banking or wallet carry-over.
- Display id is `T1`–`T6`. Tier 6 **name** is `TOKEN_WORLD_RECORD`. The future instant-max-win board special is a different id: `SPECIAL_WORLD_RECORD`. Do not collapse those names.
- `tokenFloorTier` (see Gate Upgrade) removes lower tiers from the generation pool.
- **Effective token value** = displayed value × product of applicable Thermal Lift multipliers (V2.0 stacking rule; Math may later veto this — see contradictions).
- Tokens are **not** payline symbols.

**Provisional design ceiling:** global max win **50,000×** nominal bet. Subject to Math review before production. Every award path is capped by the configured max win.

---

## 7. Special symbols

### 7.A Coach Signal — `COACH_SIGNAL`

Coach is a **real math-owned reel symbol** (`C`) in V2.0 BASE. It is not an overlay RNG event after the spin. Occurrence comes from reel stops.

Selects **one** regular pay-symbol **type** that currently exists on the board, uniformly among distinct eligible types. Frontend never chooses the type.

Example: `FLIGHT_GOGGLES` (`M2`) selected → every currently visible `M2` becomes `SNOWBURST_MYSTERY`.

Cannot select: Scatter, Coach, Mystery, Flight Tokens, future specials.

Coach does **not** participate in paylines.

Multiple Coach Signals may activate in one round. **Math owns selection and order** (left-to-right by reel, then top-to-bottom by row). After the first Coach, later Coaches may only choose types that still exist as regulars. If none remain, Math emits an explicit no-op Coach event.

In Ski Flying+ Free Spins, Coach-selected types are also appended to `persistentMysteryTargets[]` (see §9).

### 7.B Snowburst Mystery — `SNOWBURST_MYSTERY`

Mystery is **not** an initial reel-strip symbol in V2.0. Phase 3 creates it only by Coach transformations.

Resolves into a Math-selected result. The resolved type **must** be explicit in the book event.

Phase 4B BASE legal results (independent weight table; see `12_PHASE4B_BASE_FEATURE_IMPLEMENTATION.md`):

- `FLIGHT_TOKEN` — `tokenTier` / `tokenId` / `tokenName` / `tokenValueX`
- `THERMAL_LIFT` — `thermalMult`
- `GATE_UPGRADE`
- `JUDGE`
- `HEAD_JUDGE`

Free Spins Phase 6 Mystery outcomes **additionally** include (FS tables only; not on BASE):

- `REJUMP`
- `WIND_KEY`

Still reserved / not Mystery outcomes: Coach, Scatter, `SPECIAL_WORLD_RECORD` (board special, distinct from `TOKEN_WORLD_RECORD`).

After resolve, the cell shows the resulting symbol. Collectors sum **effective** token values; uncollected tokens do not add to the wallet on that spin.

### 7.C Thermal Lift — `THERMAL_LIFT`

Local token multiplier. Math supplies one of: **2× / 3× / 4× / 5× / 10× / 20×**.

Affects Flight Tokens in the 8 neighbouring cells (`row ±1`, `column ±1`). The Thermal Lift cell itself is excluded. Off-board neighbours are ignored.

Example: 25× token adjacent to Thermal Lift 3× → effective 75×.

**V2.0 stacking:** if multiple Thermals affect one token, multipliers are **multiplicative**. This is a dangerous tail assumption and is a Math kill-test item (`02_MATH_SPEC.md`). Cap interaction is mandatory.

Thermals do not multiply line wins.

### 7.D Gate Upgrade — `GATE_UPGRADE`

Persistent feature state: `tokenFloorTier`.

- Default: `1`
- On activate: `tokenFloorTier += 1`, clamped to configurable `gateMaxFloor` (live: **3**)
- Future token generation cannot produce a tier below the floor (Rookie pool removed at floor 2, and so on)
- Currently visible tokens below the new floor: **Math supplies the upgraded replacement tier and value**. Frontend never chooses the upgrade.

Persistence during Free Spins follows bonus-tier rules in §9.

If the floor is already at max, Gate Upgrade is a documented no-op event (still present in the book).

### 7.E Rejump — `REJUMP`

Controlled redrop, not a tumble of everything.

Preserve:

- Flight Tokens
- Scatter cells (see §7.J / scatter-during-Rejump rule)
- specials that the Math event marks `persist: true` (default: tokens, scatters, unresolved specials listed in the event)
- persistent feature state (`tokenFloorTier`, Flight Multiplier stages, bonus flags)

Remove:

- eligible **regular pay symbols**
- other cells the event lists as `clearedPositions`

Refill cleared cells from **Math-provided** replacement symbols. The refilled board is evaluated again. New specials may start another feature-chain cycle.

**Loop safety:** configurable `maxFeatureChainDepth`. Design default **8** resolution cycles per paid spin (and per Free Spin). If the cap is reached, the book already contains a valid terminal board and settlement. Frontend must not invent extra cycles.

### 7.F Judge — `JUDGE`

Collector. Sums **current effective values** of all visible Flight Tokens (Thermals already applied). Award that sum to the current feature win.

**V2.0 consumption:** tokens **remain** after collection. Later collectors in the same chain may collect them again.

Math may later mark tokens `consumed: true` per event. Frontend only hides/consumes when the event says so.

### 7.G Head Judge — `HEAD_JUDGE`

Enhanced collector: **two collection passes**, each a separate book event.

**V2.0 default:** the two passes are consecutive. No other mechanic runs between them unless Math emits an explicit intervening event. With tokens remaining, that makes Head Judge **exactly 2× Judge** on the same effective token sum (before global Flight Multiplier). Do not let animation delay imply a different board.

Math owns order. If a future math version inserts upgrades between passes, both events and the intervening events must appear in the book.

### 7.H Wind Key — `WIND_KEY`

Unlocks / boosts the global **Flight Multiplier**, three stages:

| Stage | Default |
| --- | ---: |
| `RUN_UP` | ×1 |
| `TAKEOFF` | ×1 |
| `FLIGHT` | ×1 |

Displayed global multiplier = `RUN_UP × TAKEOFF × FLIGHT`.

Example: ×2 × ×2 × ×3 = **×12**.

**Phase 6 live architecture (canonical as of Phase 6C.1):**

- **W-CHARGE:** each stage stores `{value: 1|2|3, charge: 0|1}`. Two Keys on the **same** selected stage are required for one K1 step (`charge0→charge1` then `value+1, charge→0`). Charge alone has **zero** payout effect.
- **PURE W2 stage selection:** eligible stages have `value < 3`. Every Key selects uniformly among stages that share the **lowest current value**. Charge is **ignored** when choosing. Multiple partial charges may coexist. There is **no** “finish a charged stage first” rule.
- **Saturation B:** when all three stages are value 3, `WIND_KEY` is removed from the Mystery pool (no no-op Keys).

When Wind Key activates, Math supplies `selectedStage`, `action` (`CHARGE`|`UPGRADE`|`NO_OP`), old/new stage value, old/new charge, and old/new global multiplier.

**V2.0 scope:** applies to **feature / token collection awards**, not to normal line wins. Whether line wins should also be multiplied is a Math audit item and is **not** assumed.

During Free Spins with Phase 6 enabled, Flight Multiplier stages (values + charges) **persist between spins** for the whole bonus. Historical V2.0 Perfect-V-only wording is superseded by Phase 6.

### 7.I World Record — `SPECIAL_WORLD_RECORD`

Very rare max-win event. Immediately settles the round at configured `maxWin` (50,000×). No later feature can increase the award above max win. The book must terminate cleanly after this event (no further scoring features / Rejumps / Free Spins).

`SPECIAL_WORLD_RECORD` is a **board special**, not a Mystery outcome. It is **not** the same object as Tier-6 `TOKEN_WORLD_RECORD` (the token can still be collected and then capped). **Live (Phase 7B):** architecture **WR-C** — Free Spins only, tier-weighted (1 : 3 : 6 : 12), trial after initial board / before lines, fill-to-50,000×, emit `skyjumpWorldRecord`, terminate chain. See `27`.

### 7.J Competition Bib — `COMPETITION_BIB` (Scatter)

- Not evaluated on paylines
- Count = visible scatters **anywhere** on the 5×5 board
- Triggers Free Spins (§9)

#### Scatter during Rejump (required explicit rule)

This was left open in the brief. V2.0 design rule until Math amends it:

1. Scatter cells are **not** removed by Rejump.
2. Rejump refill **must not** place new Scatter symbols.
3. Bonus trigger / Perfect V detection uses the scatter layout from the **spin’s initial reveal** (PHASE 1), recorded in `skyjumpScatterResult`. Rejump cannot add a late trigger.
4. During Free Spins, retrigger / upgrade scatter counts also use that spin’s **initial reveal**, not post-Rejump boards.

Rationale: Rejump loops must not farm scatters. This is mathematically controllable.

---

## 8. Special resolution order

Complex interactions must **never** depend on frontend timing. Math emits events in phase order. UI may animate slower or faster (turbo) but cannot reorder scoring.

### V2.0 phase model (design starting point)

| Phase | Name | What happens |
| ---: | --- | --- |
| 1 | Base board reveal | 5×5 symbols from the book |
| 1b | World Record interrupt | If `SPECIAL_WORLD_RECORD` is visible, emit `skyjumpWorldRecord`, skip to phases 11–12 |
| 2 | Evaluate normal paylines | Regulars only; sum line wins |
| 3 | Coach Signal transformations | Regulars → Mystery. Persistent Mystery targets apply here too |
| 4 | Resolve Snowburst Mystery | Each Mystery becomes an explicit result |
| 5 | Apply Gate Upgrades | Floor++, visible below-floor tokens replaced by Math values |
| 6 | Apply Wind Key / Flight Multiplier | W-CHARGE + PURE W2 stage updates |
| 7 | Apply Thermal Lift | Compute effective token values |
| 8 | Judge / Head Judge collections | Settle **this Mystery batch** once (`payoutSpent`); spent collectors never re-fire |
| 9 | Process Rejump (optional) | Redrop → new batch (return to Coach/Mystery as needed) within `maxFeatureChainDepth` |
| 10 | Cap check | `min(total, maxWin)`; emit `skyjumpCapReached` if clamped |
| 11 | Round settlement | `setTotalWin` / `finalWin` / optional `wincap` |

### Documented corrections to the original brief

1. **World Record was missing from the phase list.** Inserted as 1b so later features cannot inflate past max win.
2. **R-BATCH (Phase 6 live):** within each Mystery batch the order is Gate → Wind → Thermal → collectors settle once → optional Rejump → **new** batch. Collectors do **not** wait for Rejump; spent collectors never re-fire. Post-redrop collectors are new identities in a later batch.
3. **Coach after line wins** is kept: a type can pay on lines, then transform to Mystery. Persistent Mystery targets use the same timing so Free Spins do not delete line potential of those symbols before pay.
4. **Head Judge is not allowed to invent interleaving** via animation. Only book events between the two collect events can change state.
5. **UI animation order is not mathematics.** A turbo skip still applies the same event sequence.

---

## 9. Free Spin progression

Four bonus tiers. Each awards **10 Free Spins** on trigger. Costs of buy-bonus modes are **not** assigned in this document.

| Tier | Name | Trigger | Award |
| ---: | --- | --- | ---: |
| 1 | `LARGE_HILL` | 3 Competition Bibs | 10 FS |
| 2 | `SKI_FLYING` | 4 Competition Bibs | 10 FS |
| 3 | `WORLD_CUP` | 5 Competition Bibs | 10 FS |
| 4 | `PERFECT_V` | 5 Bibs in V pattern | 10 FS |

Perfect V pattern (reel, row):

```
(0,0) (1,1) (2,2) (3,1) (4,0)
```

That is payline 06 occupied by Scatter. Math must make this extremely rare (independent of “any 5 scatters”). Five scatters that are **not** in this pattern award World Cup, not Perfect V.

**Phase 3 clarification:** direct Perfect V from BASE (`[0,1,2,1,0]` on the initial reveal) is an ultra-rare shortcut / easter-egg (about 1 in 380 million). Do not raise that BASE rate. The intended practical route later is bonus-tier upgrade:

`LARGE_HILL → SKI_FLYING → WORLD_CUP → PERFECT_V`

### Tier properties

**Large Hill FS**

- Increased chance of Coach Signal (weight TBD)
- Standard feature behaviour
- `tokenFloorTier` **may persist** for the bonus duration (V2.0: yes, persist)

**Ski Flying FS** = Large Hill plus:

- Coach-selected regular **types** become persistent Mystery targets
- Newly appearing instances of those types auto-transform in PHASE 3
- State: `persistentMysteryTargets[]`
- Configurable max unique types. Live: **`maxPersistentTargets = 2`** (historical early recommendation of 3 is superseded).
- If the list is full, V2.0 rule: Coach still transforms **current-board** instances of the Math-selected type (one-shot) but **does not** change the persistent list (no-op on persistence). Math must still emit the event.

**World Cup FS** = Ski Flying plus:

- First qualifying Flight Token feature contains a **guaranteed Gate Upgrade**
- Persistent Mystery targets remain
- `tokenFloorTier` persists

**Qualifying Flight Token feature (explicit):** the first time, in this bonus, a Flight Token is present after PHASE 4 (including tokens that just resolved from Mystery) while `tokenFloorTier` is still at the bonus-entry value, Math injects `GATE_UPGRADE` if one has not already been guaranteed-injected. If a natural Gate Upgrade already raised the floor, the guarantee is satisfied.

**Perfect V FS** = World Cup plus:

- Coach Signal **every** spin
- persistent Mystery targets
- persistent `tokenFloorTier`
- guaranteed first Gate Upgrade (same rule)
- Flight Multiplier **persists between Free Spins**
- highest feature intensity

### Retrigger / upgrade — historical option notes

An active bonus can upgrade:

`LARGE_HILL → SKI_FLYING → WORLD_CUP → PERFECT_V`

Early design Option B (3+ scatters) is superseded by the Phase 5B amendment below.

### Phase 5B amendment — implemented U1

Human-approved candidate `FS5A_U1_P2_M40_mid_E15j2` replaces the Option B spin table above for the live core bonus. Full record: `15_PHASE5B_FREE_SPIN_IMPLEMENTATION.md`.

- 10 initial Free Spins. At most 40 Free Spins awarded in one economic round.
- During a Free Spin, 3+ Scatter on that spin’s **initial** board adds +5 spins and upgrades one tier: Large Hill → Ski Flying → World Cup → Perfect V.
- At Perfect V, 3+ Scatter still adds +5 spins and the tier stays Perfect V.
- The upgrade applies on the **next** Free Spin. The triggering spin keeps the rules it started with.
- If the +5 would pass 40 awarded spins, only the remaining allowance is added.
- Ski Flying and above persist at most **2** Mystery target types. Duplicate-target behaviour is **B**: Coach prefers an eligible regular that is not already persistent. If none remain, Coach may select an already persistent type.
- World Cup and Perfect V use the approved guaranteed Gate once: on the first Mystery spin with no natural Gate, replace Thermal Lift, otherwise an eligible T1–T4 Flight Token. Never T5, T6, Judge, or Head Judge.
- Perfect V guarantees at least one Coach on every Free Spin. Natural extra Coaches remain.
- **Phase 6 (live):** Rejump + Wind Key / Flight Multiplier are active in Free Spins (`P6A1_E_E1`, R-BATCH + W-CHARGE + PURE W2). Flight Multiplier stages and charges persist for the whole bonus. See `21_PHASE6C1_PURE_W2_ALIGNMENT_CERTIFICATION.md`.
- `tokenFloorTier`, persistent targets, and `guaranteedGateUsed` persist. Boards, token faces, Thermals, Judges, Mysteries, and Coach positions do not.
- One paid play contains the trigger spin and the whole Free Spin sequence. Free Spins add no wager. The 50,000× cap covers the trigger spin plus every Free Spin. Remaining spins stop once the cap is reached.

---

## 10. Stake bet modes

V1 modes are **not** carried forward automatically.

| V2 `rgsKey` | Role |
| --- | --- |
| `BASE` | Normal 1.0× stake spin |
| `LARGE_HILL` | Candidate feature-buy of Large Hill FS |
| `SKI_FLYING` | Candidate feature-buy of Ski Flying FS |
| `WORLD_CUP` | Candidate feature-buy of World Cup FS |
| `PERFECT_V` | Candidate feature-buy of Perfect V FS |

Do **not** assign buy costs yet. Costs are `E[bonus payout] / target RTP` after bonus EV is known, then checked against Stake cross-mode spread.

### V1 mode migration

| V1 `rgsKey` | V1 meaning | V2 |
| --- | --- | --- |
| `BASE` | Normal hill + standard multipliers | Keep name; **different game** |
| `LARGE_HILL` | Buy large hill tables | Repurpose name as FS buy; **not** V1 hill math |
| `SKI_FLYING` | Buy ski-flying hill | Same: name reused, math replaced |
| `MULT_10_100` | Final multiplier table 10–100 | **Remove.** Do not silently survive |
| `MULT_20_200` | Final multiplier table 20–200 | **Remove.** Do not silently survive |

V1 weather, distance curve, slot 1–5 locals, and slot-6 final multiplier **do not exist** in V2.

---

## 11. Identity reuse (presentation)

Reuse where it still fits:

- snowy hill / stadium environment
- ski jumper motif
- SkyJump audio direction (BGM playlist + winter SFX)
- overlay / win-celebration language (NO BIG WIN / BIG WIN / MEGA WIN) only if it still matches a 5×5 slot; may become a smaller toast rather than the V1 result card
- menu structure (paytable, rules, settings, sound, language)
- Stake HUD integration
- `theme-skyjump` palette

Replace as the centre of gameplay:

- horizontal 6-slot sequential strip
- weather lottery as the round engine
- distance-to-payout curve
- slot-6 cash rail

---

## 12. Configuration surface (data-driven)

Canonical typed config (single JSON, see `02_MATH_SPEC.md` and `05_IMPLEMENTATION_PLAN.md`) must include:

- symbols (regulars, tokens, specials, scatter)
- paylines
- token tiers and legal values
- special definitions
- bonus tiers and persistence flags
- `maxWin`, `maxFeatureChainDepth`, `gateMaxFloor` (live **3**), `maxPersistentTargets` (live **2**)
- mode definitions (`id`, `rgsKey`, cost TBD, `maxWin`)
- feature-chain limits

No mechanic magnitudes in Svelte components.

---

## 13. Out of scope for this document

- Implementation
- Production weights, RTP certification, buy costs
- Final art
- Stake upload packages
- Deleting or editing V1 frozen math JSON
