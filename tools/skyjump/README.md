# SkyJump math tools

Pre-certification developer math. Not a published PAR.

## Local live gameplay (natural RTP feel)

`/dev-preview` cycles curated fixtures (biased wins). For manual play against
frozen mathVersion 2 natural resolve:

```powershell
# Terminal 1 — math (repo root)
python tools/skyjump/live_math_server.py

# Terminal 2 — Vite (frontend/apps/poc)
..\..\node_modules\.bin\vite.cmd --host 0.0.0.0 --port 3011
```

Open: http://localhost:3011/live-preview

- No fixture DEV picker
- Each spin calls `resolve_v2_round` / `resolve_v2_buy_round`
- Top badge shows empirical session RTP vs LUT BASE claim (~96.39%)
- Short sessions will swing; this is not a certified PAR

Alternate: http://localhost:3011/dev-preview?source=live (still has DEV chrome)

```powershell
node --experimental-strip-types tools/skyjump/test-math.ts
node --experimental-strip-types tools/skyjump/test-v2-phase1.ts
node --experimental-strip-types tools/skyjump/test-v2-phase2.ts
node --experimental-strip-types tools/skyjump/test-v2-phase3.ts
python math/games/0_0_poc/test_skyjump_resolve.py
python math/games/0_0_poc/skyjump_v2_simulate.py --spins 1000000 --seed 20260921
python math/games/0_0_poc/skyjump_v2_simulate_features.py --spins 200000 --seed 20260921
python math/games/0_0_poc/write_skyjump_v2_samples.py
python math/games/0_0_poc/write_skyjump_v2_feature_samples.py
python math/games/0_0_poc/skyjump_v2_simulate.py --spins 1000000 --seed 20260921
python math/games/0_0_poc/write_skyjump_v2_samples.py
node --experimental-strip-types tools/skyjump/designGuards.ts
node --experimental-strip-types tools/skyjump/mathAudit.ts --rounds=1000000 --seed=7
node --experimental-strip-types tools/skyjump/simulate.ts --all-modes --exact-only
node --experimental-strip-types tools/skyjump/simulate.ts --all-modes --rounds=1000000 --seed=7
node --experimental-strip-types tools/skyjump/simulate.ts --mode=BASE --rounds=200000 --seed=7
python math/games/0_0_poc/write_skyjump_smoke.py
node --experimental-strip-types tools/skyjump/check-placeholders.ts
```

Install the math-sdk writer environment from the repo root:

```powershell
python -m pip install -r requirements.txt
```

RTP is always `E[finalWinX] / costMultiplier` (actual RGS wager), never
nominal-bet-only.

Active tables are `mathVersion: 3`. Frozen snapshots:
`math/games/0_0_poc/skyjump_config.mathVersion2.json` and
`math/games/0_0_poc/skyjump_config.mathVersion1.json`.

`mathAudit.ts` writes exact mass / Shapley / weather / hit-breakeven / cap
stats to `tools/skyjump/math-audit.json` (gitignored). Reports:

- `SKYJUMP_MATH_V2_REFINEMENT.md` — current
- `SKYJUMP_MATH_V2_REPORT.md` — mathVersion 2
- `SKYJUMP_MATH_AUDIT.md` — mathVersion 1 economics audit
- `SKYJUMP_MATH_REPORT.md` — frozen mathVersion 1 numbers

`designGuards.ts` is a developer diagnostic, not runtime production logic.
