"""Phase 7B World Record (WR-C H2) — Free Spins board special."""

from __future__ import annotations

from copy import deepcopy


def world_record_config(config: dict) -> dict | None:
    wr = config.get("worldRecord")
    if not wr or not wr.get("enabled"):
        return None
    return wr


def wr_probability(config: dict, bonus_tier: str) -> float:
    wr = world_record_config(config)
    if wr is None:
        return 0.0
    by = wr.get("byTierPSpin") or {}
    if bonus_tier in by:
        return float(by[bonus_tier])
    c = float(wr.get("c") or 0.0)
    rel = (wr.get("tierRelativeIntensity") or {}).get(bonus_tier)
    if rel is None:
        return 0.0
    return c * float(rel)


def choose_wr_position(board: list[list[str]], scatter_id: str) -> dict:
    """Deterministic: prefer (2,2); else first non-Scatter reel-major."""
    if board[2][2] != scatter_id:
        return {"reel": 2, "row": 2}
    for reel in range(5):
        for row in range(5):
            if board[reel][row] != scatter_id:
                return {"reel": reel, "row": row}
    # All scatters — still place on center (display only; scatter count from pre-overlay)
    return {"reel": 2, "row": 2}


def try_world_record(
    rng,
    *,
    board: list[list[str]],
    config: dict,
    bonus_tier: str,
    free_spin_index: int,
    accrued_round_win_x: float,
    free_spins_remaining_before_consume: int,
) -> dict | None:
    """Bernoulli WR trial. Returns None if not triggered."""
    wr = world_record_config(config)
    if wr is None:
        return None
    p = wr_probability(config, bonus_tier)
    if p <= 0.0 or rng.random() >= p:
        return None

    scatter_id = config["symbols"]["scatter"]["id"]
    symbol_id = str(wr.get("symbolId") or "SPECIAL_WORLD_RECORD")
    max_win = float(wr.get("maxWinX") or config.get("featureEconomy", {}).get("maxWinX") or 50_000)
    position = choose_wr_position(board, scatter_id)
    display = deepcopy(board)
    display[position["reel"]][position["row"]] = symbol_id

    increment = max(0.0, max_win - float(accrued_round_win_x))
    final = float(accrued_round_win_x) + increment
    if final > max_win:
        final = max_win
        increment = max(0.0, max_win - float(accrued_round_win_x))

    return {
        "triggered": True,
        "symbolId": symbol_id,
        "position": position,
        "boardDisplay": display,
        "boardPreOverlay": board,
        "bonusTier": bonus_tier,
        "freeSpinIndex": free_spin_index,
        "accruedRoundWinXBefore": float(accrued_round_win_x),
        "worldRecordIncrementX": increment,
        "maxWinX": max_win,
        "finalRoundWinX": final,
        "terminated": True,
        "remainingFreeSpinsCancelled": max(0, int(free_spins_remaining_before_consume) - 1),
        "pendingRejumpsCancelled": True,
        "tierIntensity": float((wr.get("tierRelativeIntensity") or {}).get(bonus_tier) or 0.0),
        "probability": p,
        "candidateOrigin": wr.get("candidateOrigin"),
    }
