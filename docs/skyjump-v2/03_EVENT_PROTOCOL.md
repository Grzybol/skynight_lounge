# SKYJUMP V2 — Event / Replay Protocol

**Status:** Canonical event contract for `eventSchemaVersion: 2`. Phase 7B **`skyjumpWorldRecord`** live for WR-C H2 (FS-only, after board / before lines).
**Authority:** Math writes events. Frontend replays them. No RNG on resume.

V1 schema 1 flow (`skyjumpWeather` → `skyjumpSlot` ×6 → `skyjumpResult` → `setWin`/`wincap` → `setTotalWin` → `finalWin`) remains the V1 game. V2 does **not** extend those events. It adds a parallel typed set. Settlement events `setTotalWin`, `finalWin`, and `wincap` are **reused** because Stake / XState already understand them.

---

## 1. Goals

- Stake replay and reconnect without RNG
- Every state-changing mechanic reconstructable from the book
- Resume at **feature-chain boundaries** (after a complete event), not mid-animation
- One paid round’s book contains the base spin and, if triggered, the entire Free Spin sequence (V2.0). If ACP later requires per-spin `play()` calls, that is an amendment; the **event types** stay the same

`checkIsBonusGame` is `false` in V1 (single mini-game round). V2 Phase 5B sets it from the book: true when `skyjumpFreeSpinsStart` is present and the resume cursor has not passed `skyjumpFreeSpinsEnd` (or the bet is still `active`). See `15_PHASE5B_FREE_SPIN_IMPLEMENTATION.md`.

---

## 2. Persistent state (serializable)

Reconstruct from events; also the logical snapshot after any event:

| Field | Type | Notes |
| --- | --- | --- |
| `board` | 5×5 cells | Full cell objects (kind, id, token value, thermal mult, flags) |
| `accumulatedWin` | number | Running × (book units derived at settlement) |
| `lineWinX` | number | Sum of line awards this spin (pre-cap) |
| `featureWinX` | number | Feature awards this spin after G (pre-cap) |
| `bonusTier` | `null \| LARGE_HILL \| SKI_FLYING \| WORLD_CUP \| PERFECT_V` | |
| `freeSpinsRemaining` | int | |
| `freeSpinsAwarded` | int | Audit |
| `persistentMysteryTargets` | symbol id[] | Max **2** (`maxPersistentTargets`; historical “max 3” superseded) |
| `tokenFloorTier` | int | Default 1 |
| `runUpMultiplier` | number | Stage, default 1 |
| `takeoffMultiplier` | number | |
| `flightMultiplier` | number | |
| `globalFlightMultiplier` | number | Product of stages |
| `featureChainStep` | int | 0..maxFeatureChainDepth |
| `maxWin` | number | Mode cap |
| `capReached` | bool | |
| `worldRecord` | bool | Terminal max-win path |
| `scatterCount` | int | From initial reveal of current spin |
| `perfectV` | bool | |
| `guaranteedGateUpgradePending` | bool | World Cup / Perfect V |
| `mode` | rgsKey | |

Frontend may keep a mirrored UI snapshot. Authoritative values are always the last book events, not the Pixi/Svelte timers.

---

## 3. Event list (typed)

Every event has:

```
{
  index: number,
  type: string,
  schemaVersion: 2
}
```

Optional `resumeBoundary: true` marks a safe reconnect point (end of a phase or end of a Free Spin).

Amounts that affect the wallet are in **book units** (V1: 100 = 1×). Multipliers in events are × of nominal bet unless named as a pure multiplier (`mult: 3` on a Thermal).

### 3.1 `skyjumpSpinStart`

Begins a paid spin or a Free Spin.

```
mode, isFreeSpin, bonusTier,
tokenFloorTier,
persistentMysteryTargets,
runUpMultiplier, takeoffMultiplier, flightMultiplier,
globalFlightMultiplier,
freeSpinsRemaining,
featureChainStep: 0,
maxWin
```

### 3.2 `skyjumpBoardReveal`

Full 5×5 after the RNG (Math). Cells include placeholder ids for FE.

```
board: Cell[][]  // [reel][row]
spinBand?: Cell[][]  // optional deterministic padding for reel animation
```

`Cell` (logical):

```
{
  reel, row,
  kind: 'regular' | 'token' | 'special' | 'mystery' | 'scatter',
  symbolId: string,          // P1, T3, COACH, ...
  tokenTier?: 1-6,
  tokenValue?: number,       // displayed ×
  thermalMult?: number,
  persist?: boolean
}
```

### 3.3 `skyjumpLineWins`

```
wins: [{
  paylineId: 1-28,
  symbolId,
  matchCount: 3 | 4 | 5,
  positions: [{ reel, row }],
  payoutX
}],
lineWinX
```

Empty `wins` if miss. Frontend only highlights what is listed.

### 3.3b `skyjumpScatterResult` (Phase 2+)

Counted from the initial reveal. Phase 2 does not start Free Spins.

```
positions: [{ reel, row }],
count,
perfectV,
trigger: null,
fromBoard: 'initialReveal'
```

### 3.4 `skyjumpCoachSignal`

Phase 3 fields:

```
coachPosition: { reel, row },
selectedSymbolId,           // regular type or null
selectedPositions: [{ reel, row }],
sequenceIndex,
noOp,
reason?                     // 'noEligibleRegularType' when noOp
```

Math owns selection. Frontend never chooses `selectedSymbolId`.

### 3.5 `skyjumpMysteryTransform`

Phase 3: emitted immediately after a non-no-op Coach for the cells that Coach just converted.

```
sourceSymbolId,
positions: [{ reel, row }],
sequenceIndex
```

Persistent-target transforms are live from Ski Flying+ Free Spins (Phase 5B).

### 3.6 `skyjumpMysteryResolve`

One Mystery cell → explicit result. Phase 4B `resultType` values:

| `resultType` | Extra fields |
| --- | --- |
| `FLIGHT_TOKEN` | `tokenTier`, `tokenId`, `tokenName`, `tokenValueX` |
| `THERMAL_LIFT` | `thermalMult` (2 \| 3 \| 4 \| 5 \| 10 \| 20) |
| `GATE_UPGRADE` | (floor change emitted on following `skyjumpGateUpgrade`) |
| `JUDGE` | (collection emitted on following `skyjumpJudgeCollect`) |
| `HEAD_JUDGE` | (two collections on following `skyjumpHeadJudgeCollect` ×2) |
| `REJUMP` | Free Spins Phase 6 only — starts R-BATCH Rejump chain |
| `WIND_KEY` | Free Spins Phase 6 only — `skyjumpWindKey` CHARGE/UPGRADE |

`tokenValueX` on tokens is the **face** value. Wallet credit happens only on collector events (and cap/settlement). Uncollected token faces are audit/UI only.

### 3.7 `skyjumpGateUpgrade` (Phase 4B live)

Emitted after Gate Mystery resolves. Math owns all below-floor replacements.

```
position: { reel, row },
floorBefore,
floorAfter,
replacements: [{ reel, row, before: { tier, face }, after: { tier, face } }],
noOp?: boolean
```

### 3.8 `skyjumpThermalLift` (Phase 4B live)

Moore neighbourhood (self excluded). Face values immutable; effective values in `affectedTokens`.

```
position: { reel, row },
thermalMult,
affectedTokens: [{ reel, row, faceValueX, effectiveValueX, appliedMults: number[] }]
```

### 3.9 `skyjumpWindKey` (Phase 6B live)

```
position: { reel, row },
selectedStage: 'RUN_UP' | 'TAKEOFF' | 'FLIGHT' | null,
action: 'CHARGE' | 'UPGRADE' | 'NO_OP',
oldStageValue, newStageValue,
oldCharge, newCharge,
oldGlobalMultiplier, newGlobalMultiplier,
windKeysCollected
```

CHARGE fills a stage charge box without changing GLOBAL. UPGRADE completes a charged stage (value+1, charge→0). Frontend never picks the stage.

### 3.10 `skyjumpFlightMultiplier`

Optional. Ordinary Wind Keys already carry the full transition on `skyjumpWindKey`. Use this only for non-Key multiplier transitions if needed later.

### 3.11 Rejump chain (Phase 6B live)

Prefer the four-event chain over a single blob:

`skyjumpRejumpStart` — `chainIndex`, `preservedPositions`, `redroppedPositions`, `rejumpsThisSpin`
`skyjumpRejumpBoard` — `chainIndex`, `board` and/or `changedCells`
`skyjumpRejumpLineWins` — `chainIndex`, `lineWins`, `lineWinX`
`skyjumpRejumpEnd` — `chainIndex`, `applied`, `truncated`, `reason`

Refill must not create Scatter. Collectors settled before the redrop stay `payoutSpent` and must not fire again.

### 3.12 `skyjumpJudgeCollect` (Phase 4B live; Phase 6B fields)

```
position: { reel, row },
passIndex: 1,
tokenContributions: [{ reel, row, faceValueX, effectiveValueX, appliedThermals }],
collectedX,
rawTokenCollectionX,
flightMultiplierX,
paidCollectionX,
batchIndex,
payoutSpentAfter: true,
consumed: false,             // V2.0: tokens remain
accumulatedFeatureWinX
```

### 3.13 `skyjumpHeadJudgeCollect` (Phase 4B live)

Same shape as Judge with `passIndex: 1 | 2`. **Two separate events.** Both share the same R-BATCH `batchIndex`. Nothing else between them in Phase 4B.

### 3.14 `skyjumpScatterResult`

```
positions: [{ reel, row }],
count,
perfectV: boolean,
trigger: null | 'LARGE_HILL' | 'SKI_FLYING' | 'WORLD_CUP' | 'PERFECT_V',
fromBoard: 'initialReveal'
```

Always from the spin’s PHASE 1 board.

### 3.15 `skyjumpFreeSpinsStart`

```
tier,
awardedSpins,
tokenFloorTier,
persistentMysteryTargets,
guaranteedGateUpgradePending,
flightMultiplierPersists: boolean
```

### 3.16 `skyjumpFreeSpinState`

Emitted at resume boundaries (end of a FS spin, before next).

```
tier,
spinsRemaining,
tokenFloorTier,
persistentMysteryTargets,
stages, globalFlightMultiplier,
accumulatedWinX
```

### 3.17 `skyjumpBonusUpgrade`

```
fromTier, toTier,
reason: 'scatter3' | 'scatter4' | 'scatter5' | 'perfectV' | 'other',
spinsRemainingAfter,
extraSpinsAwarded
```

Retrigger-without-upgrade can be this event with `fromTier === toTier` and `extraSpinsAwarded > 0`, or a dedicated field `retrigger: true`. Pick one in implementation and test it; do not support both silently.

### 3.18 `skyjumpFreeSpinsEnd`

```
tierEnded,
totalFreeSpinWinX,
persistentStateCleared: true
```

Base-game persistent fields reset unless a future buy-bonus amendment says otherwise.

### Phase 5B live Free Spin events

These fields are the implemented book, and they supersede the sketch above where they differ. One `finalWin` closes the paid round. Intermediate `setTotalWin` events are the running round total for the HUD, matching the local Ways books; they are not extra wagers and they are not a second payout authority.

`skyjumpFreeSpinsStart`: `initialTier`, `spinsAwarded`, `directTriggerType`, `triggeringScatterPositions`, `triggerSpinWinX`, `wagerCostMultiplier: 0`.

`skyjumpFreeSpinStart`: `spinIndex`, `currentTier`, `spinsRemainingBefore`.

`skyjumpFreeSpinState`: the serializable bonus snapshot (`bonusActive`, tier, spin counters, `tokenFloorTier`, `persistentMysteryTargets`, `guaranteedGateUsed`, `coachGuaranteeState`, raw and capped bonus/round wins, `maxWinReached`, `pendingTierUpgrade`, live `flightMultiplier` stages+charges, `globalFlightMultiplier`, `windKeysCollected`, `rejumpsThisBonus`, `featureBatchIndex`, `rejumpState`). `board` is cleared.

`skyjumpBonusUpgrade`: `fromTier`, `toTier`, `triggeringScatterCount`, `spinsRequested`, `spinsAdded`, `spinsRemainingAfter`, `totalFreeSpinsAwarded`, `activatesFromSpinIndex`, `tierChanged`.

`skyjumpFreeSpinEnd`: `spinIndex`, `spinWinX`, `bonusWinRunningX`, `spinsRemainingAfter`, `currentTier`.

`skyjumpFreeSpinsEnd`: `totalSpinsPlayed`, `finalTier`, `bonusWinX`, `upgradeCount`, `retriggerCount`, round wins, persistence fields.

Also emitted when they occur: `skyjumpPersistentTargetsApply`, `skyjumpPersistentTargetsUpdate`, `skyjumpGuaranteedGate`. A Perfect V guaranteed Coach is a `skyjumpCoachSignal` with `synthetic` and `guaranteed` set. `skyjumpCapReached` with `terminated: true` stops further Free Spins.

Approved Free Spin order: start → board reveal → line wins → scatter on the initial board → apply existing persistent targets → Coach → transforms → update targets (end of spin for list growth) → Mystery resolve → R-BATCH (Gate → Wind → Thermal → collectors settle once → optional Rejump → new batch) → U1 upgrade scheduled for the next spin → cap check → free-spin end → next spin or free-spins end.

### 3.19 `skyjumpWorldRecord`

Free Spins only (WR-C). Emitted **after** `skyjumpBoardReveal` and **before** `skyjumpLineWins` when `SPECIAL_WORLD_RECORD` triggers. Terminates remaining FS, Rejump, and feature chain; fills economic round to `maxWinX` (50,000×). Distinct from T6 `TOKEN_WORLD_RECORD`.

```
position: { reel, row },           // math-owned display cell (pre-overlay scatter count unchanged)
bonusTier,
freeSpinIndex,
accruedRoundWinXBefore,
worldRecordIncrementX,             // fill to maxWinX
maxWinX: 50000,
finalRoundWinX,
terminated: true,
remainingFreeSpinsCancelled,
pendingRejumpsCancelled: true,
tierIntensity?,                    // WR-C relative weight for this tier
symbolId: "SPECIAL_WORLD_RECORD",
candidateOrigin?: "H2"
```

No `skyjumpLineWins`, Mystery, collectors, or Rejump after this event. Followed by cap/settlement only (`skyjumpCapReached?`, `skyjumpResult`, `setTotalWin`, `finalWin`).

### 3.20 `skyjumpCapReached`

```
uncappedWinX,
cappedWinX,
maxWin
```

### 3.21 `skyjumpResult`

V2 summary for UI (not a second RNG). Analogous to V1 overlay payload but for the 5×5 game:

```
totalLineWinX,
totalFeatureWinX,   // Phase 4B: Judge / Head Judge collections (capped)
totalWinX,          // line + feature after cap
amount,
latentTokenValueX?  // sum of uncollected token faces; audit/UI only
```

Do not require a fullscreen route. A compact result toast is enough; V1’s large overlay is optional presentation.

### 3.22 Stake settlement (reuse)

| Type | V1 behaviour | V2 |
| --- | --- | --- |
| `setWin` | Amount + winLevel; FE handler is a no-op (no fullscreen Win) | Keep no-op or drive a small toast via winLevel |
| `wincap` | Present when capped | Keep |
| `setTotalWin` | Sets HUD win from book amount | Keep — **wallet-facing** |
| `finalWin` | Clears resumeCatchUp | Keep |
| `createBonusSnapshot` | Rebuilds weather/slots for resume | Adapt: rebuild V2 snapshot from reserved V2 types |

---

## 4. Suggested event order (one paid spin, no FS)

```
skyjumpSpinStart
skyjumpBoardReveal
skyjumpWorldRecord?          // if present: then cap + settlement only
skyjumpLineWins
skyjumpScatterResult
  [feature chain 0..N]
    skyjumpCoachSignal*
    skyjumpMysteryTransform?
    skyjumpMysteryResolve*
    skyjumpGateUpgrade*
    skyjumpWindKey*          // Phase 6 FS; before Thermals in R-BATCH
    skyjumpThermalLift?
    skyjumpJudgeCollect*
    skyjumpHeadJudgeCollect* // pass 1, pass 2
    skyjumpRejump?           // then new batch (Coach/Mystery…); spent collectors never re-fire
skyjumpCapReached?
skyjumpResult
setWin | wincap
setTotalWin
finalWin
```

With Free Spins: after `skyjumpScatterResult` / trigger, `skyjumpFreeSpinsStart`, then N times (`skyjumpSpinStart` isFreeSpin, … spin body …, `skyjumpFreeSpinState` / `skyjumpBonusUpgrade?`), then `skyjumpFreeSpinsEnd`, then final settlement for the **paid** round.

Running total: scoring events may carry `accumulatedWinX` for reconnect HUD; **one** paid `play` produces **one** full-round book and **one** `end-round`. Intermediate `setTotalWin` is HUD/running total only — not a per-Free-Spin wager.

---

## 5. Resume / reconnect

V1: `convertTorResumableBet` slices `bet.event` index, wraps prior events in `createBonusSnapshot`, replays weather + slots with `catchUp`.

V2 must:

1. Extend `BOOK_EVENT_TYPES_TO_RESERVE_FOR_SNAPSHOT` with every V2 type in §3 (live list: `skyjump_v2/snapshotResume.ts` — includes `skyjumpWorldRecord`, `skyjumpFreeSpinsEnd`, `finalWin`).
2. Snapshot handler rebuilds board + meters from the **last** of each state-bearing event, then plays remaining events with `resumeCatchUp` (skip long animation, apply state).
3. Safe boundaries: after `skyjumpBoardReveal`, after each feature event, after `skyjumpFreeSpinState`, after settlement.
4. Never re-roll Rejump replacements.

**Phase 7D presentation modes:** `NORMAL` / `TURBO` / `CATCH_UP` via `getV2TimingsForState(turbo, catchUp)`. Turbo and catch-up never change economics. Input lock uses Stake `overlayOpen` for the V2 presentation window (`presentationLock.ts`). After `skyjumpWorldRecord`, do not present further ordinary feature FX before settlement.

Turbo remains `stateBet.isTurbo` → timing profile only.

---

## 6. Deterministic reducer

Implementation target (Phase 2+):

```
type SkyJumpV2State = { ...persistent fields... }
reduce(state, event) -> state
```

- Python writer uses the same rules as a TS reducer used in tests
- `replay(book) === book.finalWin`
- Visual layer is a function of `(state, event, timings)`

Do not put scoring in Svelte `onMount` or Pixi tweens.

---

## 7. Local demo / fixtures

Phase 1: checked-in JSON boards (`skyjump_v2_phase1_fixtures.json`) with known line wins. `/dev-preview` source **FIXTURES** cycles them.

Phase 4B paid BASE order:

```
skyjumpSpinStart
skyjumpBoardReveal
skyjumpLineWins
skyjumpScatterResult
skyjumpCoachSignal*
skyjumpMysteryTransform?
skyjumpMysteryResolve*       // FLIGHT_TOKEN | THERMAL_LIFT | GATE_UPGRADE | JUDGE | HEAD_JUDGE
skyjumpGateUpgrade*
skyjumpThermalLift*
skyjumpJudgeCollect*
skyjumpHeadJudgeCollect*     // pass 1, pass 2 when Head Judge resolved
skyjumpCapReached?           // when raw total exceeds maxWin
skyjumpResult
setTotalWin
finalWin
```

Phase 2: additional source **MATH SAMPLE** replays Python-generated `skyjump_v2_math_samples.json`. The frontend does not generate those boards.

Phase 4B: additional source **FEATURE SAMPLE** replays `skyjump_v2_feature_samples.json` (fixtures **01–17**). DEV + localhost only.

Production RGS never uses the TS resolver as authority.

---

## 8. Versioning

- V1 books: `schemaVersion: 1`, weather/slot/result
- V2 books: `schemaVersion: 2`, events in this file
- Frontend handler map must **not** feed V2 events into V1 strip components
- Mixing schemas in one book is illegal
