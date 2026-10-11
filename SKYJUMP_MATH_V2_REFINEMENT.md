# SkyJump mathVersion 3 refinement

Pre-certification developer math. Not a published PAR.

This is a **small** retune of mathVersion 2. It is not a redesign.

`mathVersion: 2` stays frozen in `math/games/0_0_poc/skyjump_config.mathVersion2.json`
with SHA-256 `e56cf6e2469f81b3212b6f2fce46003ed52373cde5a59f6f663966d47ae3e3d1`.
See `SKYJUMP_MATH_V2_REPORT.md`.

| Field | Value |
| --- | --- |
| mathVersion | 3 |
| previousMathVersion | 2 |
| eventSchemaVersion | 1 |
| canonical config | `math/games/0_0_poc/skyjump_config.json` |
| config SHA-256 | `321dedd2d88259b37b7d779d000ddfe5a154bc1a9512a1dceb67830f91eefd33` |
| enumerator | exact (`mathAudit.ts --exact-only`) |

What changed: weather `distanceDelta` / `volatilityBias`, flying payout curve
upper bands, flying `volatilityProfile` 0.16 → 0.20. Locals, BASE/LARGE
curves, premium floors, costs, caps, miss table, and event schema are unchanged.

## Mode summary

| MODE | COST | EXACT RTP | PAY HIT | BREAKEVEN / PROFIT | CV | P95 | P99 | P99.9 | P99.99 | P(>10x) | P(>50x) | P(>100x) | CAP DRAG |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BASE | 1 | 0.9693 | 49.96% | 23.84% | 4.270 | 4.83 | 9.87 | 48.3 | 121.8 | 0.997% | 0.0564% | 0.0146% | 0.176% |
| LARGE_HILL | 3 | 0.9709 | 51.83% | 20.27% | 4.906 | 3.43 | 11.33 | 45.3 | 181.3 | 1.177% | 0.0984% | 0.0235% | 0.056% |
| SKI_FLYING | 6 | 0.9718 | 40.54% | 21.83% | 5.479 | 4.63 | 12.93 | 51.7 | 161.7 | 1.520% | 0.1035% | 0.0291% | 0.003% |
| MULT_10_100 | 11.3 | 0.9681 | 49.96% | 24.89% | 3.533 | 4.27 | 10.78 | 42.7 | 87.3 | 1.434% | 0.0433% | 0.0068% | 0.020% |
| MULT_20_200 | 22.6 | 0.9693 | 49.96% | 25.20% | 3.609 | 4.27 | 10.78 | 42.7 | 87.3 | 1.555% | 0.0404% | 0.0067% | 0.022% |

v2 RTP was 0.9705 / 0.9706 / 0.9686 / 0.9693 / 0.9705. All five modes stay
inside 0.968–0.972.

## Weather

Compressed deltas (v2 → v3):

| Weather | Δ v2 | Δ v3 | bias v2 | bias v3 |
| --- | ---: | ---: | ---: | ---: |
| sunny | +1 | +1.5 | 0 | 0 |
| lightFavorableWind | +2 | +2.15 | 0.04 | 0.03 |
| snow | −2 | −0.8 | 0.05 | 0.04 |
| headwindLift | +3 | +2.85 | 0.08 | 0.055 |
| crosswind | −2.5 | −1.1 | 0.10 | 0.07 |
| storm | −4 | −2.05 | 0.15 | 0.08 |

Mean delta was nudged up after the first shrink so convex payout bands did
not drop RTP ~6 pp. Relative order of deltas is unchanged:
lift > favorable > sunny > snow > crosswind > storm.

### BASE

| Weather | P | Conditional RTP | Hit | Breakeven | Avg m | RTP contribution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sunny | 22% | 0.968 | 50.8% | 23.6% | 115.5 | 0.213 |
| lightFavorableWind | 24% | 1.094 | 53.2% | 26.7% | 116.4 | 0.263 |
| snow | 18% | 0.851 | 46.5% | 21.3% | 113.5 | 0.153 |
| headwindLift | 16% | 1.122 | 53.6% | 27.2% | 117.3 | 0.180 |
| crosswind | 14% | 0.804 | 45.3% | 20.3% | 113.5 | 0.112 |
| storm | 6% | 0.812 | 45.5% | 20.4% | 112.6 | 0.049 |

min/max RTP **0.804 / 1.122**, spread **1.40** (v2 1.67). Hit spread **8.36 pp**
(v2 13.7 pp).

### LARGE

min/max RTP **0.801 / 1.122**, spread **1.40**, hit spread **8.30 pp**.

### FLYING

min/max RTP **0.782 / 1.145**, spread **1.46**, hit spread **9.46 pp**.

Lift remains best, storm has the shortest average jump. Crosswind RTP is
slightly below storm on all three hills because storm keeps a bit more
volatility bias. Distance order still has storm last.

## Hill tails vs wager

| | BASE | LARGE | FLYING |
| --- | ---: | ---: | ---: |
| CV | 4.270 | 4.906 | 5.479 |
| P(>10x) | 0.997% | 1.177% | 1.520% |
| P(>50x) | 0.0564% | 0.0984% | **0.1035%** |
| P(>100x) | 0.0146% | 0.0235% | **0.0291%** |
| p99.9 | 48.3 | 45.3 | **51.7** |
| p99.99 | 121.8 | **181.3** | 161.7 |

CV, P(>10x), P(>50x), and P(>100x) are BASE < LARGE < FLYING. Flying p99.9
is above Large. Flying p99.99 is still below Large (remaining risk). Large
p99.9 sits a little under Base after weather compression; Large was not
retuned.

Flying pay-hit 40.5% (v2 39.4%), inside the 35–40% band plus a hair.

## Preserved v2 properties

| Guard | v2 | v3 |
| --- | ---: | ---: |
| BASE any-local | 17.7% | **17.5%** |
| BASE local \| pay | 26.0% | 25.7% |
| BASE distance-only EV | 0.454 | **0.456** |
| BASE Shapley D/L/F | 71.8 / 15.2 / 13.1 | **71.9 / 15.0 / 13.1** |
| Cap drag all modes | << 1% | max 0.176% BASE |

Premium modes were not redesigned. Their RTP stayed in window from the
weather nudge alone.

## Remaining risks

1. Storm conditional RTP is ~0.8 pp above crosswind, though storm distance is
   worse. Further storm-only cuts dropped global RTP out of window.
2. Flying p99.99 (161.7) is still below Large (181.3). p99.9 and P(>50x) are not.
3. Large p99.9 (45.3) is slightly below Base (48.3). Large was left alone.
4. Flying any-local 20.7% is above Base because hill volatility bias lifts
   rare symbols. Still under the 22% warn.
