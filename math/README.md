# Stake Engine Math SDK

Welcome to [Stake Engine Math SDK](https://engine.stake.com/)!

The Math SDK is a Python-based engine for defining game rules, simulating outcomes, and optimizing win distributions. It generates all necessary backend and configuration files, lookup tables, and simulation results.
   

For technical details [view the docs](https://stakeengine.github.io/math-sdk/)


# Installation
 
This repository requires Python3 (version >= 3.12), along with the PIP package installer.
If the included optimization algorithm is being used, Rust/Cargo will also need to be installed.

It is recommended to use [Make](https://www.gnu.org/software/make/) and setup the engine by running:
```sh
make setup
```

Alternatively, visit our [Setup and Installation page](https://stakeengine.github.io/math-sdk/math_docs/general_overview/) for more details.

## SkyJump writer environment

A clean environment must include `zstandard` (listed in `requirements.txt`) or
`gamestate.py` / math-sdk compression will fail with `ModuleNotFoundError`.

From the repository root:

```sh
python -m pip install -r requirements.txt
```

From `math/`:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Then:

```sh
python games/0_0_poc/test_skyjump_resolve.py
python games/0_0_poc/write_skyjump_smoke.py
```

`write_skyjump_smoke.py` writes a tiny temporary library under
`math/games/0_0_poc/library/` (gitignored). It is **not** a production book set.

Do not run full-scale `games/0_0_poc/run.py` until the dedicated production-book
task. That writer now emits SkyJump events keyed by Stake `rgsKey`
(`BASE`, `LARGE_HILL`, …), not farmer 5×3 books.


