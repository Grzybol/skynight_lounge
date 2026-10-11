"""SkyJump math-sdk book writer. Does not emit farmer 5x3 books."""

import os
import shutil
import time

from gamestate import GameState
from game_config import GameConfig, published_sim_counts
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

FARMER_LEFTOVER_TOKENS = ("books_base", "books_bonus", "lookuptable_base", "lookuptable_bonus")
KEEP_LIBRARY_NAMES = {"smoke"}


def remove_path(path: str, attempts: int = 6) -> None:
    """Delete a file or directory, retrying Windows/OneDrive locks."""
    for attempt in range(attempts):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            return
        except OSError:
            time.sleep(0.25 * (attempt + 1))
    shutil.rmtree(path, ignore_errors=True)
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
    except OSError:
        pass


def reset_generated_library(library_path: str) -> None:
    """Drop stale generated books so farmer files cannot collide with BASE on Windows."""
    if not os.path.isdir(library_path):
        return
    leftover = []
    for name in os.listdir(library_path):
        lowered = name.lower()
        if any(token in lowered for token in FARMER_LEFTOVER_TOKENS):
            leftover.append(name)
    if leftover:
        print("Removing leftover generated library names that collide on case-insensitive disks:", leftover)
    for name in os.listdir(library_path):
        if name in KEEP_LIBRARY_NAMES:
            continue
        remove_path(os.path.join(library_path, name))


if __name__ == "__main__":

    debug_batch = os.environ.get("POC_DEBUG_BATCH") == "1"

    num_threads = 2 if debug_batch else 10
    rust_threads = 20
    batching_size = 50 if debug_batch else 5000
    compression = not debug_batch
    profiling = False

    production_sims = int(os.environ.get("POC_NUM_SIMS", "5000"))
    debug_sims = int(os.environ.get("POC_DEBUG_SIMS", "40"))
    num_sim_args = published_sim_counts(debug_batch, production_sims, debug_sims)

    run_conditions = {
        "run_sims": True,
        "run_optimization": False,
        "run_analysis": False,
        "run_format_checks": not debug_batch,
    }
    target_modes = list(num_sim_args.keys())

    config = GameConfig()
    reset_generated_library(config.library_path)
    config.construct_paths()
    gamestate = GameState(config)
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
