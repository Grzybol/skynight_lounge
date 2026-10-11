"""Phase 4C stratified / importance-weighted BASE feature RTP measurement.

Does not mutate live config. Oversamples rare tiers and reweights by true probability.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field

from skyjump_v2_features import coach_positions, eligible_regular_types, mystery_positions, positions_of
from skyjump_v2_lines import evaluate_paylines, load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase4a_economy import (
    BOARD_SYMBOL_FOR_RESULT,
    MAX_WIN_X,
    RESULT_ORDER,
    THERMAL_MULTS,
    build_token_tables,
    empty_cell,
    neighbours,
    sample_token_at_floor,
)
from skyjump_v2_phase4c_exact import exact_flight_token_joint, exact_mystery_result_probs, exact_token_tier_probs
from skyjump_v2_reels import COACH_ID, MYSTERY_ID, board_from_stops
from skyjump_v2_resolve import draw_stops, v2_math_tables
from skyjump_v2_tokens import DEFAULT_VALUES


def _weighted_choice(rng: random.Random, items: list, weights: list[float]):
    total = float(sum(weights))
    if total <= 0:
        raise ValueError("empty weights")
    pick = rng.random() * total
    running = 0.0
    for item, weight in zip(items, weights, strict=True):
        running += float(weight)
        if pick <= running:
            return item, float(weight) / total
    return items[-1], float(weights[-1]) / total


@dataclass
class DrawLog:
    """Likelihood ratio contributions for importance sampling."""

    log_lr: float = 0.0  # sum log(p_true / p_biased)

    def observe(self, p_true: float, p_biased: float) -> None:
        if p_true <= 0 or p_biased <= 0:
            raise ValueError("non-positive probability in LR")
        self.log_lr += math.log(p_true) - math.log(p_biased)

    @property
    def weight(self) -> float:
        return math.exp(self.log_lr)


def biased_mystery_policy(mode: str) -> dict:
    """Return biased mystery + tier weight maps for a sampling mode."""
    # Natural F01 mystery weights (copied structurally; not mutated from config).
    mystery_true = {
        "FLIGHT_TOKEN": 855.0,
        "THERMAL_LIFT": 42.0,
        "GATE_UPGRADE": 3.0,
        "JUDGE": 85.0,
        "HEAD_JUDGE": 15.0,
    }
    tier_true = {1: 999400.0, 2: 400.0, 3: 120.0, 4: 40.0, 5: 32.0, 6: 8.0}

    if mode == "natural":
        return {"mystery": mystery_true, "tier": tier_true, "forceMinTier": None, "forceResult": None}

    mystery = dict(mystery_true)
    tier = dict(tier_true)
    force_min = None
    force_result = None

    if mode == "boost_t4plus":
        # Oversample high tokens + collectors for tail mass.
        mystery["FLIGHT_TOKEN"] = 700.0
        mystery["JUDGE"] = 150.0
        mystery["HEAD_JUDGE"] = 80.0
        mystery["THERMAL_LIFT"] = 60.0
        mystery["GATE_UPGRADE"] = 10.0
        tier = {1: 800000.0, 2: 50000.0, 3: 50000.0, 4: 40000.0, 5: 40000.0, 6: 20000.0}
    elif mode == "boost_t5plus":
        mystery["FLIGHT_TOKEN"] = 650.0
        mystery["JUDGE"] = 160.0
        mystery["HEAD_JUDGE"] = 100.0
        mystery["THERMAL_LIFT"] = 70.0
        mystery["GATE_UPGRADE"] = 20.0
        tier = {1: 500000.0, 2: 50000.0, 3: 50000.0, 4: 100000.0, 5: 200000.0, 6: 100000.0}
    elif mode == "boost_t6":
        mystery["FLIGHT_TOKEN"] = 600.0
        mystery["JUDGE"] = 150.0
        mystery["HEAD_JUDGE"] = 150.0
        mystery["THERMAL_LIFT"] = 80.0
        mystery["GATE_UPGRADE"] = 20.0
        tier = {1: 100000.0, 2: 50000.0, 3: 50000.0, 4: 100000.0, 5: 200000.0, 6: 500000.0}
    elif mode == "force_t6_collector":
        # Still samples freely but with extreme T6 + collector bias.
        mystery["FLIGHT_TOKEN"] = 500.0
        mystery["JUDGE"] = 200.0
        mystery["HEAD_JUDGE"] = 220.0
        mystery["THERMAL_LIFT"] = 60.0
        mystery["GATE_UPGRADE"] = 20.0
        tier = {1: 50000.0, 2: 50000.0, 3: 50000.0, 4: 50000.0, 5: 100000.0, 6: 700000.0}
    else:
        raise ValueError(f"unknown mode {mode}")

    return {"mystery": mystery, "tier": tier, "forceMinTier": force_min, "forceResult": force_result}


def sample_mystery_biased(
    rng: random.Random,
    *,
    candidate: dict,
    token_tables: dict,
    policy: dict,
    true_mystery: dict[str, float],
    true_tier: dict[int, float],
    draw: DrawLog,
    tokens_so_far: int = 0,
) -> dict:
    labels = list(RESULT_ORDER)
    true_w = [true_mystery[label] for label in labels]
    bias_w = [policy["mystery"][label] for label in labels]
    true_sum = sum(true_w)
    bias_sum = sum(bias_w)
    kind, p_b = _weighted_choice(rng, labels, bias_w)
    p_t = true_mystery[kind]
    # _weighted_choice returns biased prob; use normalized true.
    draw.observe(p_t, p_b)

    if kind == "FLIGHT_TOKEN":
        tiers = list(range(1, 7))
        true_tw = [true_tier[t] for t in tiers]
        bias_tw = [policy["tier"][t] for t in tiers]
        tier, p_tb = _weighted_choice(rng, tiers, bias_tw)
        p_tt = true_tier[tier] / sum(true_tw) if False else true_tier[tier]
        # true_tier already normalized? We store raw weights - normalize observe.
        draw.observe(true_tier[tier] / sum(true_tw), p_tb)

        values = list(token_tables["values"][tier])
        vweights = [float(w) for w in token_tables["valueWeights"][tier]]
        value, _p = _weighted_choice(rng, values, vweights)
        # Face sampling is identical under true and bias → LR = 1 (no observe).
        return {
            "resultType": "FLIGHT_TOKEN",
            "kind": "token",
            "tokenTier": tier,
            "tokenId": token_tables["ids"][tier],
            "tokenName": token_tables["names"][tier],
            "tokenValueX": float(value),
            "thermalMult": None,
        }
    if kind == "THERMAL_LIFT":
        mults = list(THERMAL_MULTS)
        weights_t = [float(candidate["thermalWeights"][str(m)]) for m in mults]
        mult, _p = _weighted_choice(rng, mults, weights_t)
        return {
            "resultType": "THERMAL_LIFT",
            "kind": "thermal",
            "thermalMult": int(mult),
            "tokenTier": None,
            "tokenValueX": None,
        }
    if kind == "GATE_UPGRADE":
        return {"resultType": "GATE_UPGRADE", "kind": "gate", "thermalMult": None, "tokenTier": None, "tokenValueX": None}
    if kind == "JUDGE":
        return {"resultType": "JUDGE", "kind": "judge", "thermalMult": None, "tokenTier": None, "tokenValueX": None}
    return {"resultType": "HEAD_JUDGE", "kind": "head_judge", "thermalMult": None, "tokenTier": None, "tokenValueX": None}


def resolve_paying_biased(
    board: list[list[str]],
    rng: random.Random,
    *,
    config: dict,
    candidate: dict,
    policy: dict,
    true_mystery: dict[str, float],
    true_tier: dict[int, float],
    line_win_x: float = 0.0,
) -> dict:
    """Same settlement as Phase 4B, but mystery/token draws use biased policy + LR."""
    working_symbols = [col[:] for col in board]
    regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    coach_id = config["coachModel"]["id"]
    mystery_id = config["mysteryModel"]["id"]
    token_tables = build_token_tables(candidate)
    max_floor = int(candidate["gateMaxFloor"])
    max_win = float(candidate.get("maxWinX", MAX_WIN_X))
    draw = DrawLog()

    coaches = []
    transforms = []
    selected_hist: list[str] = []
    mystery_counts: list[int] = []

    for sequence, coach in enumerate(coach_positions(board, coach_id)):
        eligible = eligible_regular_types(working_symbols, regular_ids)
        payload = {
            "coachPosition": coach,
            "sequenceIndex": sequence,
            "eligibleSymbolIds": eligible,
        }
        if not eligible:
            payload.update(
                {
                    "selectedSymbolId": None,
                    "selectedPositions": [],
                    "noOp": True,
                    "reason": "noEligibleRegularType",
                }
            )
            coaches.append(payload)
            continue
        selected = rng.choice(eligible)
        selected_positions = positions_of(working_symbols, selected)
        for pos in selected_positions:
            working_symbols[pos["reel"]][pos["row"]] = mystery_id
        payload.update(
            {
                "selectedSymbolId": selected,
                "selectedPositions": selected_positions,
                "noOp": False,
            }
        )
        coaches.append(payload)
        selected_hist.append(selected)
        mystery_counts.append(len(selected_positions))
        transforms.append(
            {
                "sourceSymbolId": selected,
                "positions": selected_positions,
                "sequenceIndex": sequence,
            }
        )

    cells = [[empty_cell() for _ in range(5)] for _ in range(5)]
    resolves = []
    tokens_so_far = 0
    for pos in mystery_positions(working_symbols, mystery_id):
        result = sample_mystery_biased(
            rng,
            candidate=candidate,
            token_tables=token_tables,
            policy=policy,
            true_mystery=true_mystery,
            true_tier=true_tier,
            draw=draw,
            tokens_so_far=tokens_so_far,
        )
        cell = empty_cell()
        cell.update(result)
        if cell["kind"] == "token":
            cell["faceValueX"] = float(cell["tokenValueX"])
            cell["effectiveValueX"] = float(cell["tokenValueX"])
            cell["appliedThermals"] = []
            working_symbols[pos["reel"]][pos["row"]] = cell["tokenId"]
            tokens_so_far += 1
        else:
            working_symbols[pos["reel"]][pos["row"]] = BOARD_SYMBOL_FOR_RESULT[cell["resultType"]]
        cell["position"] = pos
        cells[pos["reel"]][pos["row"]] = cell
        resolves.append({"position": pos, **{k: v for k, v in cell.items() if k != "position"}})

    # Gate
    floor = 1
    gate_events = []
    for reel, row in sorted(
        (r, c) for r in range(5) for c in range(5) if cells[r][c]["kind"] == "gate"
    ):
        before = floor
        if floor < max_floor:
            floor = min(max_floor, floor + 1)
        replacements = []
        if floor > before:
            for tr in range(5):
                for tc in range(5):
                    cell = cells[tr][tc]
                    if cell["kind"] != "token" or int(cell["tokenTier"]) >= floor:
                        continue
                    replacement = sample_token_at_floor(rng, token_tables, floor)
                    old = {"tier": cell["tokenTier"], "face": cell["faceValueX"]}
                    cell.update(replacement)
                    working_symbols[tr][tc] = cell["tokenId"]
                    replacements.append(
                        {
                            "reel": tr,
                            "row": tc,
                            "before": old,
                            "after": {"tier": cell["tokenTier"], "face": cell["faceValueX"]},
                        }
                    )
        gate_events.append(
            {
                "position": {"reel": reel, "row": row},
                "floorBefore": before,
                "floorAfter": floor,
                "replacements": replacements,
            }
        )

    # Thermal
    thermals = [
        (reel, row, cells[reel][row]["thermalMult"])
        for reel in range(5)
        for row in range(5)
        if cells[reel][row]["kind"] == "thermal"
    ]
    for reel, row, mult in thermals:
        for nr, nc in neighbours(reel, row):
            cell = cells[nr][nc]
            if cell["kind"] == "token":
                cell["appliedThermals"].append(int(mult))

    raw_face_sum = 0.0
    effective_sum = 0.0
    token_count = 0
    max_tier = 0
    for reel in range(5):
        for row in range(5):
            cell = cells[reel][row]
            if cell["kind"] != "token":
                continue
            token_count += 1
            max_tier = max(max_tier, int(cell["tokenTier"]))
            face = float(cell["faceValueX"])
            raw_face_sum += face
            product = 1.0
            for mult in cell["appliedThermals"]:
                product *= float(mult)
            cell["effectiveValueX"] = face * product
            effective_sum += cell["effectiveValueX"]

    # Collectors
    collections = []
    feature_raw = 0.0
    judge_count = 0
    head_judge_count = 0
    collectors = []
    for reel in range(5):
        for row in range(5):
            kind = cells[reel][row]["kind"]
            if kind == "judge":
                collectors.append(("judge", reel, row))
            elif kind == "head_judge":
                collectors.append(("head_judge", reel, row))
    collectors.sort(key=lambda row: (row[1], row[2], 0 if row[0] == "judge" else 1))
    for kind, reel, row in collectors:
        if kind == "judge":
            collections.append({"type": "JUDGE", "pass": 1, "collectedX": effective_sum})
            feature_raw += effective_sum
            judge_count += 1
        else:
            for pass_index in (1, 2):
                collections.append(
                    {"type": "HEAD_JUDGE", "pass": pass_index, "collectedX": effective_sum}
                )
                feature_raw += effective_sum
            head_judge_count += 1

    total_raw = float(line_win_x) + feature_raw
    total_capped = min(total_raw, max_win)
    feature_capped = max(0.0, total_capped - float(line_win_x))
    cap_hit = total_raw > max_win
    cap_drag = total_raw - total_capped if cap_hit else 0.0

    return {
        "coaches": coaches,
        "transforms": transforms,
        "resolves": resolves,
        "cells": cells,
        "workingBoard": working_symbols,
        "gateEvents": gate_events,
        "tokenFloorTier": floor,
        "collections": collections,
        "tokenCount": token_count,
        "maxTokenTier": max_tier,
        "rawFaceSumX": raw_face_sum,
        "effectiveTokenSumX": effective_sum,
        "thermalCount": len(thermals),
        "gateCount": len(gate_events),
        "judgeCount": judge_count,
        "headJudgeCount": head_judge_count,
        "collectorPasses": len(collections),
        "totalFeatureWinXRaw": feature_raw,
        "totalFeatureWinXCapped": feature_capped,
        "totalWinXRaw": total_raw,
        "totalWinXCapped": total_capped,
        "capHit": cap_hit,
        "capDragX": cap_drag,
        "importanceWeight": draw.weight,
        "logImportanceWeight": draw.log_lr,
        "coachCount": len(coaches),
        "mysteryCount": sum(mystery_counts),
        "selectedSymbolIds": selected_hist,
        "mysteriesPerCoach": mystery_counts,
    }


def classify_tier_stratum(max_tier: int) -> str:
    if max_tier <= 3:
        return "NO_T4PLUS"
    if max_tier == 4:
        return "T4_NO_T5PLUS"
    if max_tier == 5:
        return "T5_NO_T6"
    return "T6_PRESENT"


@dataclass
class WeightedAccumulator:
    weight_sum: float = 0.0
    feature_raw: float = 0.0
    feature_capped: float = 0.0
    line: float = 0.0
    cap_weight: float = 0.0
    cap_excess: float = 0.0
    max_raw: float = 0.0
    n: int = 0
    # strata
    by_tier_stratum: dict = field(default_factory=lambda: defaultdict(lambda: {"w": 0.0, "raw": 0.0, "cap": 0.0, "cap_w": 0.0}))
    by_max_tier: dict = field(default_factory=lambda: defaultdict(lambda: {"w": 0.0, "raw": 0.0, "cap": 0.0}))
    by_collector_passes: dict = field(default_factory=lambda: defaultdict(lambda: {"w": 0.0, "raw": 0.0, "cap": 0.0}))
    by_route: dict = field(default_factory=lambda: defaultdict(lambda: {"w": 0.0, "raw": 0.0, "cap": 0.0, "cap_w": 0.0}))
    thresholds: dict = field(
        default_factory=lambda: {
            1000: 0.0,
            5000: 0.0,
            10000: 0.0,
            25000: 0.0,
            50000: 0.0,
            100000: 0.0,
            200000: 0.0,
        }
    )
    t6_faces: dict = field(
        default_factory=lambda: {
            10000.0: {"w": 0.0, "raw": 0.0, "cap": 0.0, "cap_w": 0.0, "spins": 0.0},
            25000.0: {"w": 0.0, "raw": 0.0, "cap": 0.0, "cap_w": 0.0, "spins": 0.0},
            50000.0: {"w": 0.0, "raw": 0.0, "cap": 0.0, "cap_w": 0.0, "spins": 0.0},
        }
    )

    def add(self, weight: float, line: float, feat: dict) -> None:
        if weight <= 0 or not math.isfinite(weight):
            return
        self.n += 1
        self.weight_sum += weight
        raw = float(feat["totalFeatureWinXRaw"])
        capped = float(feat["totalFeatureWinXCapped"])
        self.feature_raw += weight * raw
        self.feature_capped += weight * capped
        self.line += weight * line
        total_raw = float(feat["totalWinXRaw"])
        self.max_raw = max(self.max_raw, total_raw)
        if feat["capHit"]:
            self.cap_weight += weight
            self.cap_excess += weight * float(feat["capDragX"])

        for thr in self.thresholds:
            if total_raw >= thr:
                self.thresholds[thr] += weight

        max_tier = int(feat.get("maxTokenTier") or 0)
        stratum = classify_tier_stratum(max_tier)
        row = self.by_tier_stratum[stratum]
        row["w"] += weight
        row["raw"] += weight * raw
        row["cap"] += weight * capped
        if feat["capHit"]:
            row["cap_w"] += weight

        # Attribution by highest tier present (mutually exclusive strata already cover)
        for tier in range(1, 7):
            key = f"T{tier}"
            # Contribution proxy: if max tier equals this tier, assign all feature to it.
            if max_tier == tier:
                cell = self.by_max_tier[key]
                cell["w"] += weight
                cell["raw"] += weight * raw
                cell["cap"] += weight * capped

        passes = int(feat.get("collectorPasses") or 0)
        pass_key = "5+" if passes >= 5 else str(passes)
        prow = self.by_collector_passes[pass_key]
        prow["w"] += weight
        prow["raw"] += weight * raw
        prow["cap"] += weight * capped

        high = max_tier >= 5
        has_thermal = int(feat.get("thermalCount") or 0) > 0
        thermal_ge2 = int(feat.get("thermalCount") or 0) >= 2
        has_gate = int(feat.get("gateCount") or 0) > 0
        has_collector = passes > 0
        multi_collector = passes >= 3 or (int(feat.get("judgeCount") or 0) + int(feat.get("headJudgeCount") or 0) >= 2)
        route = "other"
        if high and has_gate and has_thermal and multi_collector:
            route = "high+gate+thermal+multi_collector"
        elif high and has_gate and has_collector:
            route = "high+gate+collector"
        elif high and has_thermal and has_collector:
            route = "high+thermal+collector"
        elif high and thermal_ge2:
            route = "high+2thermal"
        elif high and has_thermal:
            route = "high+thermal"
        elif high and has_gate:
            route = "high+gate"
        elif high:
            route = "high_token_only"
        rrow = self.by_route[route]
        rrow["w"] += weight
        rrow["raw"] += weight * raw
        rrow["cap"] += weight * capped
        if feat["capHit"]:
            rrow["cap_w"] += weight

        # T6 face tracking
        for cell_col in feat.get("cells") or []:
            for cell in cell_col:
                if cell.get("kind") == "token" and int(cell.get("tokenTier") or 0) == 6:
                    face = float(cell.get("faceValueX") or 0)
                    bucket = self.t6_faces.get(face)
                    if bucket is not None:
                        bucket["w"] += weight
                        bucket["raw"] += weight * raw
                        bucket["cap"] += weight * capped
                        bucket["spins"] += weight
                        if feat["capHit"]:
                            bucket["cap_w"] += weight

    def finalize(self) -> dict:
        w = self.weight_sum
        if w <= 0:
            raise ValueError("zero weight mass")

        def fin_map(src: dict, fields=("raw", "cap")) -> dict:
            out = {}
            for key, row in src.items():
                ww = row["w"]
                entry = {
                    "weightShare": ww / w,
                    "rawRtp": row["raw"] / w,
                    "cappedRtp": row["cap"] / w,
                    "E_raw_given": (row["raw"] / ww) if ww > 0 else 0.0,
                    "E_capped_given": (row["cap"] / ww) if ww > 0 else 0.0,
                }
                if "cap_w" in row:
                    entry["pCapGiven"] = (row["cap_w"] / ww) if ww > 0 else 0.0
                    entry["capDragRtp"] = (row.get("cap_drag", 0.0) / w) if False else None
                out[key] = entry
            return out

        # Attach cap drag per route/stratum manually where we tracked cap_w only.
        tier_out = {}
        for key, row in self.by_tier_stratum.items():
            ww = row["w"]
            tier_out[key] = {
                "weightShare": ww / w,
                "rawRtp": row["raw"] / w,
                "cappedRtp": row["cap"] / w,
                "E_raw_given": (row["raw"] / ww) if ww > 0 else 0.0,
                "E_capped_given": (row["cap"] / ww) if ww > 0 else 0.0,
                "pCapGiven": (row["cap_w"] / ww) if ww > 0 else 0.0,
            }

        route_out = {}
        for key, row in self.by_route.items():
            ww = row["w"]
            route_out[key] = {
                "weightShare": ww / w,
                "rawRtp": row["raw"] / w,
                "cappedRtp": row["cap"] / w,
                "E_raw_given": (row["raw"] / ww) if ww > 0 else 0.0,
                "E_capped_given": (row["cap"] / ww) if ww > 0 else 0.0,
                "pCapGiven": (row["cap_w"] / ww) if ww > 0 else 0.0,
            }

        return {
            "effectiveSpins": w,
            "samples": self.n,
            "lineRtp": self.line / w,
            "featureRtpRaw": self.feature_raw / w,
            "featureRtpCapped": self.feature_capped / w,
            "pCap": self.cap_weight / w,
            "capDragRtp": self.cap_excess / w,
            "E_excess_given_cap": (self.cap_excess / self.cap_weight) if self.cap_weight > 0 else 0.0,
            "maxRawTotalWinX": self.max_raw,
            "rawThresholds": {str(k): v / w for k, v in self.thresholds.items()},
            "byTierStratum": tier_out,
            "byMaxTierExclusive": fin_map(self.by_max_tier),
            "byCollectorPasses": fin_map(self.by_collector_passes),
            "byRoute": route_out,
            "t6Faces": {
                str(int(face)): {
                    "weightShare": row["w"] / w,
                    "rawRtp": row["raw"] / w,
                    "cappedRtp": row["cap"] / w,
                    "pCapGiven": (row["cap_w"] / row["w"]) if row["w"] > 0 else 0.0,
                }
                for face, row in self.t6_faces.items()
            },
        }


def run_stratified_batch(
    *,
    spins: int,
    seed: int,
    mode: str,
    config: dict | None = None,
) -> WeightedAccumulator:
    config = config or load_v2_config()
    tables = v2_math_tables(config)
    candidate = live_candidate_from_config(config)
    joint = exact_flight_token_joint(config)
    true_mystery = joint["pMysteryResults"]
    # Use raw-normalized tier probs
    true_tier_probs = joint["pTierGivenFlight"]
    # Convert to raw-like weights for observe (already probs summing to 1)
    true_tier = {t: true_tier_probs[t] for t in range(1, 7)}
    # sample_mystery_biased expects weights - we pass probs and normalize in observe via sum
    # Fix: pass probs as weights (sum=1) so sum(true_tw)=1
    policy = biased_mystery_policy(mode)
    # Convert policy tier to weights; true_tier as probs
    true_mystery_w = {k: v for k, v in true_mystery.items()}
    rng = random.Random(seed)
    acc = WeightedAccumulator()
    strips = tables["strips"]

    for _ in range(spins):
        stops = draw_stops(rng, strips)
        board = board_from_stops(strips, stops)
        evaluated = evaluate_paylines(
            board,
            paylines=tables["paylines"],
            paytable=tables["paytable"],
            scatter_id=tables["scatterId"],
            regular_ids=tables["regularIds"],
        )
        line_win = float(evaluated["lineWinX"])
        if not tables["config"].get("coachModel"):
            continue
        # Coach path: always run biased resolve (handles zero-coach as empty features)
        # Use same coach transform RNG as natural (rng.choice) — LR only on mystery/token.
        from skyjump_v2_features import resolve_features

        if mode == "natural":
            features = resolve_features(board, rng, tables["config"], line_win_x=line_win)
            weight = 1.0
            # Adapt feature dict shape
            feat = {
                "totalFeatureWinXRaw": features.get("totalFeatureWinXRaw", 0),
                "totalFeatureWinXCapped": features.get("totalFeatureWinXCapped", features.get("totalFeatureWinX", 0)),
                "totalWinXRaw": features.get("totalWinXRaw", line_win + float(features.get("totalFeatureWinXRaw", 0) or 0)),
                "totalWinXCapped": features.get("totalWinXCapped", line_win + float(features.get("totalFeatureWinX", 0) or 0)),
                "capHit": features.get("capHit", False),
                "capDragX": features.get("capDragX", 0),
                "maxTokenTier": max(features.get("tokenTiers") or [0], default=0),
                "thermalCount": features.get("thermalCount", 0),
                "gateCount": features.get("gateCount", 0),
                "judgeCount": features.get("judgeCount", 0),
                "headJudgeCount": features.get("headJudgeCount", 0),
                "collectorPasses": features.get("collectorPasses", len(features.get("collections") or [])),
                "cells": features.get("cells"),
            }
        else:
            # true_tier must be raw weights for observe division - use probs * 1e6 style
            true_tier_w = {t: true_tier[t] for t in range(1, 7)}
            paying = resolve_paying_biased(
                board,
                rng,
                config=tables["config"],
                candidate=candidate,
                policy=policy,
                true_mystery=true_mystery_w,
                true_tier=true_tier_w,
                line_win_x=line_win,
            )
            weight = float(paying["importanceWeight"])
            feat = paying
        acc.add(weight, line_win, feat)
    return acc


def combine_modes(mode_results: dict[str, dict], mode_mass: dict[str, float] | None = None) -> dict:
    """Combine independent stratified mode estimates with equal prior mass on natural,
    and importance-weighted modes already self-normalized via LR.

    Each mode's finalize() already returns an unbiased estimator (for natural, and for
    IS modes via LR). We combine by inverse-variance-ish equal weight on IS modes plus
    natural, reporting a mixture estimate.
    """
    if not mode_results:
        raise ValueError("no modes")
    # Default: weight natural higher; IS modes corroborate tails.
    if mode_mass is None:
        mode_mass = {name: (4.0 if name == "natural" else 1.0) for name in mode_results}
    total_mass = sum(mode_mass[name] for name in mode_results)
    raw = 0.0
    capped = 0.0
    line = 0.0
    p_cap = 0.0
    drag = 0.0
    for name, result in mode_results.items():
        m = mode_mass[name] / total_mass
        raw += m * result["featureRtpRaw"]
        capped += m * result["featureRtpCapped"]
        line += m * result["lineRtp"]
        p_cap += m * result["pCap"]
        drag += m * result["capDragRtp"]
    # Spread across modes as uncertainty proxy
    capped_vals = [r["featureRtpCapped"] for r in mode_results.values()]
    raw_vals = [r["featureRtpRaw"] for r in mode_results.values()]
    return {
        "featureRtpRaw": raw,
        "featureRtpCapped": capped,
        "lineRtp": line,
        "pCap": p_cap,
        "capDragRtp": drag,
        "rawSpread": max(raw_vals) - min(raw_vals),
        "cappedSpread": max(capped_vals) - min(capped_vals),
        "modes": mode_results,
    }
