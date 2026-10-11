# Math run log

Last updated: 2026-09-14

`library/` is gitignored. Recreate with the project venv; do not commit books.

## Environment

- Python 3.12.10 venv: `math/.venv`
- `pip install -e math` plus numpy, pytest, zstandard, xlsxwriter, toml,
  matplotlib, python-dotenv, boto3
- Optimizer: `math/optimization_program/Cargo.toml` is tracked again
  (`math/.gitignore` now has `!optimization_program/Cargo.toml`).
  `cargo build --release` succeeds (Rust 1.97.1). SDK unused-variable
  warnings only.
- `run.py` defaults to **100000** compressed sims per mode. Overrides:
  - `POC_DEBUG_BATCH=1` — 2 threads, uncompressed, no optimizer
  - `POC_DEBUG_SIMS` — debug count (default 200)
  - `POC_NUM_SIMS` — production count (default 100000)
- SDK batch leak: `_payout_ints` is reset at the start of each `run_sims`
  batch (needed once `num_repeats > 1`, i.e. 100k with 10 threads × 5000).

## 2026-09-14 uncompressed debug batch

```powershell
cd math\games\0_0_poc
$env:POC_DEBUG_BATCH='1'
$env:POC_DEBUG_SIMS='100'
..\..\.venv\Scripts\python.exe run.py
```

Results:

- `books_base.json` 100 rounds, `books_bonus.json` 100 rounds
- Frontend handlers cover every emitted type. No leftovers.

| Mode | Event types seen |
| --- | --- |
| base | reveal, setTotalWin, finalWin, winInfo, setWin, freeSpinTrigger, updateFreeSpin, freeSpinEnd, **wincap** (1) |
| bonus | same plus **freeSpinRetrigger** (5) and **wincap** (2) |

Thread RTP in this tiny sample is not a production RTP measurement.

## 2026-09-14 compressed 10k smoke (optimizer + RGS checks)

```powershell
cd math\games\0_0_poc
$env:POC_NUM_SIMS='10000'
..\..\.venv\Scripts\python.exe -u run.py
```

Wall time ~79s. Exit 0.

Publish pack (gitignored):

| File | SHA-256 |
| --- | --- |
| `publish_files/books_base.jsonl.zst` | `56e4dab48ef2d8971008aa26e851178d9dc5f6be12689dd56b3ed4f5ef809ba3` |
| `publish_files/books_bonus.jsonl.zst` | `b5a1c8fd244cc2ffe71402eaacdcc4ad4eaf84a4f9ac5dcf13e9fa1857433652` |
| `publish_files/lookUpTable_base_0.csv` | `01d9fa3c2cbc58453935b4a2b1a0c41a95756d35a64ffdf11884e7197befe510` |
| `publish_files/lookUpTable_bonus_0.csv` | `5683a30f8fea65af3c812a42913bb37521f83598dc94b7cf941631c35e32c9c2` |

LUT RTP **0.97** for both modes. Book length 10000. Hashes in
`configs/config.json` match the zst files. RGS `execute_all_tests` used the
verification sidecar (FAST PATH) and passed asserts.

Warnings (SDK 3-star helper, not a hard fail):

- both modes: `rtp 0.97 > 0.967` — expected; spec is 97%, the helper still
  encodes the sample 3-star 96.7% cap
- bonus: `cvar 882 > 800`

Raw thread RTP before the optimizer is not the published RTP. Do not quote
it.

This 10k pack is a **pipeline smoke**, not the upload candidate.

## 2026-09-14 compressed 100k/mode (optimizer + RGS checks)

```powershell
cd math\games\0_0_poc
$env:POC_NUM_SIMS='100000'
..\..\.venv\Scripts\python.exe -u run.py
```

Wall time ~251s. Exit 0. Two sim batches (`Batch 1 of 2` / `2 of 2`).

Publish pack (gitignored, local only):

| File | Size | SHA-256 |
| --- | --- | --- |
| `books_base.jsonl.zst` | 17.8 MB | `2ac86a1a2f8cdc0bc285b1d9294c268a34db98bfbc91e8c27c78c63b5259e38f` |
| `books_bonus.jsonl.zst` | 100.4 MB | `8dbd3c3ff4e6dc2f5a51a569e6520982c8779ee5ce3c9565bf1edd2c64e92d6d` |
| `lookUpTable_base_0.csv` | 2.0 MB | `ab0211550f33bb9ad3e39d692af77741532ac05374c743060cc42e1fbbc32940` |
| `lookUpTable_bonus_0.csv` | 2.2 MB | `bd3ebfc31f3b1e217fc12298fdd325e55bbb3ddd27479c9b57b6673b579b9736` |

`index.json` modes: `base` cost 1.0, `bonus` cost 100.0. LUT RTP **0.97**
both modes. Book length **100000**. `config.json` book/LUT hashes match the
files. RGS `execute_all_tests` FAST PATH passed (sidecar SHA + payout hash).

PAR (`library/stats_summary.json`):

| Mode | RTP | avg win | std (raw) | hit rate | P(0) | max-win HR | CVaR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 0.97 | 0.97× | 7.29 | 1 / 3.44 | 0.709 | 1 / 5.00e6 | 118 |
| bonus | 0.97 | 97× (on 100× buy) | 126 | 1 / 1 | 0 | 1 / 5.00e4 | 1258 |

Fence targets (base): basegame RTP 0.602 HR 3.5; freegame RTP 0.367 HR 200;
wincap RTP 0.001. Bonus freegame RTP 0.969 + wincap 0.001.

Warnings (SDK 3-star helper, not a hard fail):

- both modes: `rtp 0.97 > 0.967` — locked spec, not the sample 3-star cap
- bonus: `cvar 1258 > 800` — do not retune until Stake asks for 3-star
  volatility. Changing fences means another 100k run.

`prob5k` prints as 0 because the 5000× weight is the 0.001 RTP fence
(about 1 in 5 million on base). That is the designed cap frequency, not a
missing outcome.

## Next

Phase 1 math pack is locally complete. Do not commit `library/`. Remaining
Stake.com work is ACP IDs, licensed audio, real RGS session, and
desktop/portrait `/dev-preview` regression (Phase 2 leftover).
