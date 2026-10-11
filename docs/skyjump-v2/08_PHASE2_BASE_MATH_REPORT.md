# SKYJUMP V2 — Phase 2 BASE math report

**Status:** PHASE 2 PROVISIONAL BASE MATH. Not production RTP. Not a Stake LUT.  
**Lineage:** `skyjump-v2` · **mathVersion:** 1 · **eventSchemaVersion:** 2  
**Seed:** `20260921`  
**Do not start Phase 3 from this file.** Advanced features are out of scope.

This report freezes the Phase 2 research chassis: 5 virtual reel strips, 28 unchanged paylines, a 0.10×-grain provisional regular paytable, Scatter counting without payout, exact line RTP, and a 5,000,000-spin deterministic Monte Carlo.

---

## 1. Reel model

Independent wraparound virtual strips. Math owns the five stop positions. The visible window on reel `i` is:

```
board[i][row] = strips[i][(stop[i] + row) % length]
```

- 5 reels × 5 visible rows
- Strip length 52
- Frontend never rolls stops and does not use `Math.random()`
- Phase 1 DEV fixtures remain explicit fixture books; they are not this reel model

Because the strips wrap, each cell on a reel has the same symbol probability regardless of row. Exact line RTP therefore does not depend on which of the 28 paylines is evaluated, only on the per-reel symbol probabilities and the paytable.

---

## 2. Chosen provisional strips / frequencies

Template counts per 52-stop strip (jittered per reel, max run length 2):

| Symbol | Template /52 | Global share |
| --- | ---: | ---: |
| P1 FLYING_JUMPER | 1 | 1.92% |
| P2 CRYSTAL_TROPHY | 2 | 3.85% |
| P3 GOLDEN_HELMET | 3 | 6.15% |
| M1 JUMPING_SKIS | 4 | 8.08% |
| M2 FLIGHT_GOGGLES | 5 | 9.62% |
| M3 SKI_BOOTS | 6 | 11.15% |
| L1 WIND_SOCK | 8 | 16.15% |
| L2 SNOW_BADGE | 10 | 19.23% |
| L3 START_FLAG | 12 | 21.92% |
| S COMPETITION_BIB | 1 | 1.92% |

Hierarchy is strict: P1 rarest regular, then P2, P3, mids, then lows. Scatter is independently 1/52 per reel cell. Strips are mixed; they are not identical uniform copies and do not use huge repeated blocks.

Per-reel cell frequencies are in `skyjump_v2_sim_report.json` → `frequencies.perReel`.

---

## 3. Provisional regular paytable

3 / 4 / 5 of a kind only, left-to-right. Every award satisfies `payoutX * 10` integer. Scatter has no Phase 2 payout.

| Symbol | 3× | 4× | 5× |
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

The Phase 1 DEV paytable (`skyjump_v2_dev_paytable.json`) remains **FIXTURE/TEST ONLY**. It is not this table.

---

## 4. Analytical line RTP

Exact contribution:

```
lineRTP = 28 × Σ_symbol Σ_{k=3,4,5} P(exact k-kind on one line) × pay[symbol][k]
```

With wraparound strips, `P(cell = symbol)` on reel `i` is `count_i(symbol) / 52`.

| | |
| --- | ---: |
| Theoretical line RTP | **60.1408%** |
| Research target | 58–62% |
| Total game target (later) | ~96.50% |

By-symbol theoretical line RTP (share of the 60.14%):

| Symbol | Line RTP |
| --- | ---: |
| P1 | 0.08% |
| P2 | 0.53% |
| P3 | 1.87% |
| M1 | 2.79% |
| M2 | 3.65% |
| M3 | 4.19% |
| L1 | 11.34% |
| L2 | 15.66% |
| L3 | 20.01% |

Lows dominate because they are common. That is intentional for a line chassis that leaves ~35–40 RTP points for later features.

---

## 5. Simulated line RTP

| | |
| --- | ---: |
| Spins | 5,000,000 |
| Seed | 20260921 |
| Simulated line RTP | **60.0894%** |
| Delta vs theory | −0.0514 pp |
| Hit rate | 42.778% |
| Zero-win rate | 57.222% |
| Multi-line hit rate | 16.643% |
| Average win given win | 1.405× |
| Median winning payout | 1.1× |
| Average winning paylines | 1.609 |
| Std / volatility proxy | 0.9998 |
| Max observed line-only payout | 29.4× |

`P(win ≥ x)`:

| Threshold | Probability |
| --- | ---: |
| 5× | 0.66068% |
| 10× | 0.01742% |
| 25× | 0.00016% |
| 50× | 0 |
| 100× | 0 |

Theory and simulation agree to about 0.05 percentage points on 5M spins. That is enough to treat the analytical line RTP as confirmed for Phase 2.

---

## 6. Payout distribution (line-only)

| Bucket | Share of spins |
| --- | ---: |
| 0× | 57.222% |
| >0–1× | 21.202% |
| 1–2× | 12.900% |
| 2–5× | 8.057% |
| 5–10× | 0.604% |
| 10–25× | 0.017% |
| 25–50× | 0.00016% |
| 50–100× | 0 |
| 100×+ | 0 |

This is **not** final game volatility. There are no Flight Tokens, collectors, or Free Spins yet. The line game is a frequent small-to-medium hit chassis. The missing tail is reserved for later buckets.

---

## 7. Scatter foundation

Scatter occupies one stop per reel, is ignored by paylines, and pays 0 in Phase 2. Counts are taken from the initial 5×5 reveal.

Exact window convolution vs 5M simulation:

| Count | Exact | Simulated |
| --- | ---: | ---: |
| 0 | 60.322% | 60.258% |
| 1 | 32.086% | 32.152% |
| 2 | 6.827% | 6.820% |
| 3 | 0.726% | 0.730% |
| 4 | 0.0386% | 0.0390% |
| 5+ | 0.00082% | 0.00076% |

| | Exact | One in N |
| --- | ---: | ---: |
| 3+ scatter | 0.7657% | **130.6** |
| Perfect V `[0,1,2,1,0]` | 2.630×10⁻⁹ | **380,204,032** |

No Perfect V appeared in 5M spins, which matches the exact rate.

**Planning note for Phase 5, not a Phase 2 retune:** 3+ scatter at 1 in 131 is on the frequent side for a future Free Spin trigger. Perfect V on BASE strips is effectively a lore/tail event, not a usable bonus cadence. Bonus-mode strips, not this BASE chassis, should carry any Perfect V frequency that gameplay actually needs.

---

## 8. Candidate comparison

Deterministic search jointly varied strip templates, strip length, and 0.10×-legal paytable scales. Objective: line RTP near 60% without collapsing hierarchy, without huge symbol runs, and without a scatter trigger that is either ~every 50 spins or impossibly rare.

| Rank | Line RTP | 3+ scatter | Length | Notes |
| ---: | ---: | ---: | ---: | --- |
| **1 (chosen)** | 60.14% | 1 in 130.6 | 52 | Best score; hierarchy intact; max run 2 |
| 2 | 60.20% | 1 in 196.5 | 60 | Similar paytable, slightly rarer scatter, same hit feel |
| 3 | 59.05% | 1 in 196.5 | 60 | Lower 3-kind scale; RTP still in band |
| 4 | 60.97% | 1 in 196.5 | 60 | Higher hit (~49% in 150k smoke); median win 0.8× — too chimey |
| 5 | 58.92% | 1 in 130.6 | 52 | Bottom of the research band |

Rank 1 is preferred because it sits in the middle of the 58–62% band, keeps P1 clearly rarer than lows, avoids rank 4’s tiny-win spam, and leaves a measured scatter rate for later FS pricing. Rank 2 is the backup if Phase 5 needs a rarer 3-scatter trigger without touching the paytable family.

58–62% line RTP is **playable** as a base chassis. It is not “bad gameplay” by itself; it is simply incomplete. The current hit rate (~43%) with median 1.1× will feel busy until features add the missing tail. If a later playtest rejects the chatter, lower the 3-kind scale (rank 3 direction) rather than raising 5-kind pays to fake volatility.

---

## 9. RTP budget

| Bucket | Phase 2 | Later |
| --- | ---: | --- |
| Normal paylines | **60.14% measured** | retune if features need room |
| Base-game features | RESERVED | Flight Token / Mystery / collectors / modifiers |
| Free Spins | RESERVED | scatter-triggered bonus |
| Other / rounding / cap drag | RESERVED | grain, wincap, presentation leftovers |
| **TOTAL** | not targeted in Phase 2 | **~96.50%** |

Do not aim this BASE model at 96.50%. That number is the future full-game target.

---

## 10. Events and DEV replay

A real BASE math round emits, in order:

1. `skyjumpSpinStart` (includes math-owned `stops`)
2. `skyjumpBoardReveal`
3. `skyjumpLineWins`
4. `skyjumpScatterResult` (count / Perfect V / `trigger: null`)
5. `skyjumpResult` (`totalFeatureWinX = 0`)
6. `setTotalWin`
7. `finalWin`

DEV `/dev-preview` can replay:

- **FIXTURES** — Phase 1 boards (unchanged)
- **MATH SAMPLE** — `skyjump_v2_math_samples.json` (Python-generated, `nonProduction: true`)

Frontend displays supplied events. It does not generate the board.

No production `books_*.jsonl.zst`, LUT, or `stake-upload/math` was written.

---

## 11. Files

| File | Role |
| --- | --- |
| `math/games/0_0_poc/skyjump_v2_config.json` | Canonical strips, paytable, 28 paylines |
| `math/games/0_0_poc/skyjump_v2_reels.py` | Windows / mixing / hierarchy / grain |
| `math/games/0_0_poc/skyjump_v2_exact.py` | Exact line RTP + scatter convolution |
| `math/games/0_0_poc/skyjump_v2_search.py` | Deterministic BASE search |
| `math/games/0_0_poc/skyjump_v2_resolve.py` | Stop → board → lines → scatter |
| `math/games/0_0_poc/skyjump_v2_events.py` | Schema-v2 writer |
| `math/games/0_0_poc/skyjump_v2_simulate.py` | Monte Carlo |
| `math/games/0_0_poc/skyjump_v2_sim_report.json` | 5M-spin report |
| `math/games/0_0_poc/skyjump_v2_math_samples.json` | DEV replay books |
| `math/games/0_0_poc/skyjump_v2_dev_paytable.json` | Phase 1 fixture paytable only |

---

## 12. Not in Phase 2

Flight Tokens, Coach Signal, Mystery, Thermal Lift, Gate Upgrade, Rejump, Judge / Head Judge, Wind Key, Flight Multiplier, World Record, Free Spins execution, feature buys, production books.
