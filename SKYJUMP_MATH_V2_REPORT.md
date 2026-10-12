# SkyJump mathVersion 2 report

Pre-certification developer math. Not a published PAR and not a Stake
certification claim.

mathVersion 1 remains the audited baseline. Do not treat this file as a
replacement of `SKYJUMP_MATH_AUDIT.md`.

| Field | Value |
| --- | --- |
| mathVersion | 2 |
| previousMathVersion | 1 |
| eventSchemaVersion | 1 (unchanged) |
| canonical config | `math/games/0_0_poc/skyjump_config.json` |
| config SHA-256 | `e56cf6e2469f81b3212b6f2fce46003ed52373cde5a59f6f663966d47ae3e3d1` |
| frozen v1 config | `math/games/0_0_poc/skyjump_config.mathVersion1.json` |
| frozen v1 SHA-256 | `709378e7f8790b03eb5354193a6800fd5ee2b8a4f140a4788612195cc6002042` |
| enumerator | exact, weather × 5^5 slots × finals; volatility bias applied |
| Monte Carlo | skipped for this retune report (`--exact-only`) |
| target RTP | 0.97 vs actual wager = nominal bet × costMultiplier |
| preferred window | 0.968 – 0.972 |

Reproduce:

```
node --experimental-strip-types tools/skyjump/mathAudit.ts --exact-only
node --experimental-strip-types tools/skyjump/test-math.ts
node --experimental-strip-types tools/skyjump/designGuards.ts
```

RTP, hit, cap, weather, locals, Shapley, and percentiles below are **exact**.

## Design choices

- Weather kept as a static modifier (audit deltas), not a round-quality oracle.
- BASE payout starts at 116 m with a small first band so the miss/pay cliff is
  softer than v1 (128 m / 0.3692).
- Hills use different curves, volatility bias, and caps. Costs were set after
  the distributions, not by scaling distance/curve/cost together.
- Local frequency cut first on LANDING and WIND. Slot roles stay distinct.
- Standard slot 6 uses **option B**: a static miss table with no x20/x50 on
  zero. Plus/max floors stay independent. This is config, not session RTP
  correction.
- Premium modes keep literal 10–100 / 20–200 floors. Caps were raised so cap
  drag is a safety rail. Costs moved to 11.3 / 22.6 after raw EV.
- `schemaVersion` stays 1. Book `amount` / wallet settlement still use
  `finalWinX`. Economic fields on `skyjumpResult` are presentation only.

## Mode summary

HIT = pay-hit (`finalWinX > 0`). BREAKEVEN = `finalWinX ≥ cost`. PROFIT =
`finalWinX > cost`. For these tables, integer costs make breakeven = profit.

Percentiles and tails are **payout / actual wager**.

| MODE | COST | MAX WIN | MAX vs WAGER | EXACT RTP | RAW EV | CAPPED EV | PAY HIT | BREAKEVEN | PROFIT | CV | P90 | P95 | P99 | P99.9 | P99.99 | P(>10x) | P(>50x) | P(>100x) | CAP FREQ | CAP DRAG |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BASE | 1 | 500 | 500x | 0.9705 | 0.9723 | 0.9705 | 49.72% | 23.69% | 23.69% | 4.298 | 2.42 | 4.83 | 10.08 | 48.3 | 131.0 | 1.006% | 0.057% | 0.015% | 0.00033% | 0.183% |
| LARGE_HILL | 3 | 4000 | 1333x | 0.9706 | 2.9136 | 2.9119 | 51.58% | 20.20% | 20.20% | 4.944 | 1.72 | 3.43 | 11.40 | 50.7 | 181.3 | 1.184% | 0.100% | 0.024% | 0.000057% | 0.058% |
| SKI_FLYING | 6 | 25000 | 4167x | 0.9686 | 5.8115 | 5.8114 | 39.44% | 21.78% | 21.78% | 5.464 | 2.42 | 3.63 | 13.53 | 48.3 | 149.3 | 1.547% | 0.098% | 0.028% | 0.00000090% | 0.002% |
| MULT_10_100 | 11.3 | 6000 | 531x | 0.9693 | 10.9551 | 10.9528 | 49.72% | 24.73% | 24.73% | 3.563 | 2.16 | 4.27 | 10.78 | 42.7 | 87.3 | 1.445% | 0.045% | 0.007% | 0.000069% | 0.020% |
| MULT_20_200 | 22.6 | 12000 | 531x | 0.9705 | 21.9375 | 21.9326 | 49.72% | 25.03% | 25.03% | 3.639 | 2.16 | 4.27 | 10.78 | 42.7 | 87.3 | 1.566% | 0.042% | 0.007% | 0.000076% | 0.022% |

Probability mass = 1.000000 on every mode (float noise < 2e-14).

FLYING 0.96856 sits 0.04 pp inside the preferred 0.968 floor.

## Hill differentiation

Normalized vs actual wager:

| | BASE | LARGE | FLYING | Order |
| --- | ---: | ---: | ---: | --- |
| CV | 4.298 | 4.944 | 5.464 | BASE < LARGE < FLYING |
| P(>10x) | 1.006% | 1.184% | 1.547% | BASE < LARGE < FLYING |
| P(>50x) | 0.057% | 0.100% | 0.098% | FLYING slightly under LARGE |
| P(>100x) | 0.015% | 0.024% | 0.028% | BASE < LARGE < FLYING |
| p99.9 | 48.3 | 50.7 | 48.3 | FLYING ≈ BASE, under LARGE |
| p99.99 | 131.0 | 181.3 | 149.3 | FLYING under LARGE, above BASE |
| maxWin vs wager | 500x | 1333x | 4167x | BASE < LARGE < FLYING |
| pay-hit | 49.7% | 51.6% | 39.4% | Flying trades hit rate for tail |

`tools/skyjump/designGuards.ts` **warns** that FLYING p99.9 is slightly below
LARGE. It does not fail: the 8% tolerance holds, CV order holds, and P(>100x)
is monotonic. Remaining risk: mid-extreme flying tail is still close to large.

## Weather (BASE)

| Weather | P | Conditional RTP | Hit | Breakeven | Avg distance | RTP contribution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sunny | 22% | 0.968 | 50.8% | 23.6% | 115.0 m | 0.213 |
| lightFavorableWind | 24% | 1.105 | 53.4% | 26.9% | 116.3 m | 0.265 |
| snow | 18% | 0.786 | 44.9% | 19.9% | 112.4 m | 0.142 |
| headwindLift | 16% | 1.244 | 56.5% | 28.8% | 117.6 m | 0.199 |
| crosswind | 14% | 0.764 | 43.2% | 19.4% | 112.3 m | 0.107 |
| storm | 6% | 0.744 | 42.8% | 19.0% | 111.2 m | 0.045 |

BASE weather RTP spread = 1.244 / 0.744 = **1.67**. Hit spread = **13.7 pp**.

v1 was ~0.435–1.592 (spread ~3.66) and ~16–43% hit. Weather is still a
noticeable metre/RTP modifier. It is no longer a round-quality oracle.

### Weather × hill

| Mode | Min RTP | Max RTP | Spread | Hit spread |
| --- | ---: | ---: | ---: | ---: |
| BASE | 0.744 | 1.244 | 1.67 | 13.7 pp |
| LARGE | 0.721 | 1.257 | 1.74 | 13.5 pp |
| FLYING | 0.713 | 1.278 | 1.79 | 13.6 pp |
| MULT_10_100 | 0.743 | 1.243 | 1.67 | 13.7 pp |
| MULT_20_200 | 0.744 | 1.245 | 1.67 | 13.7 pp |

Hill volatility bias does **not** restore v1 weather dominance. Flying is the
widest, still under the 1.85 warn / 2.4 fail guards.

## Locals (BASE)

| Metric | v1 | v2 | Target |
| --- | ---: | ---: | --- |
| P(any local) | 35.56% | **17.74%** | 15–20% |
| P(local \| pay) | 54.57% | **25.98%** | 25–30% |
| P(local \| zero) | 27.1% | 9.58% | — |
| P(product ≥ 4) | 5.94% | **1.34%** | rare stacks |
| P(product ≥ 6) | 1.08% | **0.128%** | rare |
| P(product ≥ 10) | 0.095% | **0.0057%** | very rare |

| Locals on the board | Share |
| --- | ---: |
| none | 82.26% |
| one | 16.40% |
| two | 1.29% |
| three+ | 0.051% |

Per-slot local frequency (BASE): SPEED 3.90% · TAKEOFF 4.23% · FLIGHT 5.21% ·
WIND 2.64% · LANDING 3.16%.

x2/x3 remain the visible local events. x4–x6 stacks are rare. x10+ is
essentially a showcase outcome. Cap is not used to regulate locals.

LARGE / FLYING any-local is 19.3% / 20.3% because hill volatility bias lifts
rare symbols. Still inside the 22% warn / 28% fail guards. FLYING
P(local \| pay) is 32.0%, a bit above the 30% BASE target because flying
misses more often.

## Distance and Shapley (BASE)

| Component | Exact |
| --- | ---: |
| distance-only EV `vD` | **0.454** (v1 0.300) |
| Shapley distance | 0.696 / 71.8% |
| Shapley locals | 0.147 / 15.2% |
| Shapley final | 0.127 / 13.1% |
| full EV | 0.9705 |

Distance is the payout foundation. Locals and slot 6 are spice / suspense.
Premium modes invert that on purpose: MULT_20 Shapley final share is 43.0%
because the advertised floor **is** the feature.

Typical BASE distance is now near the first paying bands (avg ~114 m, first
pay 116 m), so small weather deltas no longer flip most rounds across a 10 m
cliff.

## Slot 6

### Standard (BASE / LARGE / FLYING)

Option B: static miss table. No x20/x50 on a zero-distance payout.

| | BASE |
| --- | ---: |
| P(x10+) | 0.587% |
| P(x10+ AND pay) | 0.547% |
| P(x10+ AND zero) | **0.040%** |
| P(x20+ AND zero) | 0 |
| P(x50 AND zero) | 0 |

Whiff rate among x10+ outcomes: 0.040 / 0.587 ≈ **6.9%** (v1 ~69% because
independent x50 could land on a miss). Independent slot 6 (option A) was
rejected: with a ~50% hit rate it would still put about half of x50s on zero.

Mixture weights (pay + miss): x1 86.5% · x2 8.5% · x3 3.2% · x5 1.2% ·
x10 0.44% · x20 0.12% · x50 0.03%. Pay-table x1 is still 82% when the jump
pays. Slot 6 remains suspense, not the BASE RTP engine.

### Premium floors

Plus/max stay independent of pay state, so high multipliers on miss are the
advertised feature, not a bug:

| Mode | P(floor AND zero) | Notes |
| --- | ---: | --- |
| MULT_10_100 | 50.28% of rounds are x10+ and zero | every round is x10+ |
| MULT_20_200 | 50.28% of rounds are x20+ and zero | every round is x20+ |

Presentation now labels those as PAYOUT / RETURN VS BET, not YOU WON.

## Premium economics

| | MULT_10_100 | MULT_20_200 |
| --- | ---: | ---: |
| cost | 11.3 | 22.6 |
| RTP | 0.9693 | 0.9705 |
| pay-hit | 49.72% | 49.72% |
| breakeven / profit | **24.73%** | **25.03%** |
| return < wager | 75.27% | 74.97% |
| pay-hit but below cost | 25.00% | 24.69% |
| cap drag | 0.020% | 0.022% |
| max vs wager | 531x | 531x |

v1 breakeven/profit was 18.15% / 17.40%. The lift comes from the earlier
distance curve, not from targeting profit rate. v1 premium cap drag was
2.5–2.7%; v2 is ~0.02% after raising caps to 6000 / 12000.

A paying 10x on MULT_20 still returns 10/22.6 ≈ 0.44× wager. That is a
feature-cost outcome, not a BIG WIN. Overlay/SFX follow `isProfit` and
`returnMultiplier`.

## Cap

Cap remains a safety rail.

| Mode | Frequency | Raw EV | Capped EV | Drag / raw |
| --- | ---: | ---: | ---: | ---: |
| BASE | 3.3e-6 | 0.9723 | 0.9705 | 0.183% |
| LARGE | 5.7e-7 | 2.9136 | 2.9119 | 0.058% |
| FLYING | 9.0e-9 | 5.8115 | 5.8114 | 0.002% |
| MULT_10_100 | 6.9e-7 | 10.9551 | 10.9528 | 0.020% |
| MULT_20_200 | 7.6e-7 | 21.9375 | 21.9326 | 0.022% |

No mode exceeds the 1% warn / 2% fail drag guards.

## RNG / contract

All probabilities are static canonical JSON. No session, user, or
win/loss-history weighting. `eventSchemaVersion` is 1. `mathVersion` is 2.

## Tests and smoke

- `tools/skyjump/test-math.ts` — pass, including exact RTP window and design guards
- `python math/games/0_0_poc/test_skyjump_resolve.py` — pass
- `python -m pytest math/tests/test_config_parity_poc.py` — pass
- `tools/skyjump/autoplay-stress.ts` — 100 normal + 100 turbo pass
- exact enumerator — mass 1.000000, RTP as above
- smoke books regenerated by `python math/games/0_0_poc/write_skyjump_smoke.py`
  (gitignored under `math/games/*/library/`)

Fixtures now include zero, small payout, profitable BASE, local product,
high final, LARGE tail, FLYING tail, premium economic-loss, premium profit,
and cap.

## Remaining risks

1. Weather conditional RTP still spans ~0.74–1.24, not the 0.80–1.15 band.
   Hit spread is ~14 pp, not 8–10. Further compression flattened RTP too much
   in earlier iterations.
2. FLYING p99.9 and P(>50x) are not strictly above LARGE. CV and P(>100x) are.
3. BASE pay-hit is ~50% (v1 ~31%) as the cost of smoothing the cliff.
4. Premium Shapley is still final-multiplier heavy because of literal floors.
5. Premium 531x normalized ceiling is below FLYING 4167x. That is intentional:
   the feature is a floor, not the fattest hill tail.
