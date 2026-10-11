"""Phase 4C stratified certification via P(stratum)×E[X|stratum] (measurement only)."""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict

from skyjump_v2_features import mystery_positions, resolve_features
from skyjump_v2_lines import evaluate_paylines, load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase4a_economy import build_token_tables, sample_mystery_result
from skyjump_v2_phase4c_exact import exact_flight_token_joint
from skyjump_v2_phase4c_forced import _coach_transform, _settle, force_token_on_mystery
from skyjump_v2_reels import board_from_stops
from skyjump_v2_resolve import draw_stops, v2_math_tables


def probe_mystery_count_distribution(spins: int, seed: int, config: dict | None = None) -> dict:
    """Estimate P(N mysteries) and coach rates under live config (cheap, low variance)."""
    config = config or load_v2_config()
    tables = v2_math_tables(config)
    rng = random.Random(seed)
    hist = Counter()
    coach_any = 0
    mystery_total = 0
    for _ in range(spins):
        stops = draw_stops(rng, tables["strips"])
        board = board_from_stops(tables["strips"], stops)
        features = resolve_features(board, rng, tables["config"], line_win_x=0.0)
        n = len(features.get("resolves") or [])
        hist[n] += 1
        if features.get("coaches"):
            coach_any += 1
        mystery_total += n
    total = float(spins)
    return {
        "spins": spins,
        "pCoachAny": coach_any / total,
        "meanMysteries": mystery_total / total,
        "pN": {str(k): hist[k] / total for k in sorted(hist)},
        "counts": {str(k): hist[k] for k in sorted(hist)},
    }


def exact_p_max_tier_given_n(n: int, p_tier_mystery: dict[int, float]) -> dict[str, float]:
    """Exact P(max token tier stratum | N independent mystery draws).

    Each mystery is independently:
      empty-of-token with prob 1 - sum p_tier_mystery
      or tier t with p_tier_mystery[t]
    where p_tier_mystery[t] = P(FT)*P(tier=t).
    """
    p_token = {t: float(p_tier_mystery[t]) for t in range(1, 7)}
    p_none = 1.0 - sum(p_token.values())
    if p_none < -1e-12:
        raise ValueError("token probs exceed 1")
    p_none = max(0.0, p_none)

    # CDF-style: P(all tiers <= k) and P(all < k)
    def p_all_le(k: int) -> float:
        mass = p_none + sum(p_token[t] for t in range(1, k + 1))
        return mass**n

    def p_all_lt(k: int) -> float:
        if k <= 1:
            return p_none**n
        mass = p_none + sum(p_token[t] for t in range(1, k))
        return mass**n

    return {
        "NO_T4PLUS": p_all_le(3),
        "T4_NO_T5PLUS": p_all_le(4) - p_all_lt(4),
        "T5_NO_T6": p_all_le(5) - p_all_lt(5),
        "T6_PRESENT": 1.0 - p_all_lt(6),
        "P_any_T4": 1.0 - p_all_lt(4),
        "P_any_T5": 1.0 - p_all_lt(5),
        "P_any_T6": 1.0 - p_all_lt(6),
    }


def mix_over_n(p_n: dict[str, float], p_tier_mystery: dict[int, float]) -> dict[str, float]:
    acc = defaultdict(float)
    for n_s, p in p_n.items():
        n = int(n_s)
        part = exact_p_max_tier_given_n(n, p_tier_mystery)
        for key, val in part.items():
            acc[key] += float(p) * float(val)
    return dict(acc)


def conditional_given_forced_tier(
    *,
    spins: int,
    seed: int,
    forced_tier: int,
    config: dict | None = None,
    require_collector: bool = False,
) -> dict:
    """Unweighted E[X | at least one forced_tier token] via rejection/forcing.

    Method: run spins with Coach/Mystery; if N=0 skip; force one random mystery to
    a random face of forced_tier; sample remaining naturally; average outcomes.
    This estimates E[X | specific forced identity present], which is a close proxy
    for E[X | max_tier >= forced_tier] when forced_tier is rare (T5/T6).
    """
    config = config or load_v2_config()
    tables = v2_math_tables(config)
    candidate = live_candidate_from_config(config)
    token_tables = build_token_tables(candidate)
    joint = exact_flight_token_joint(config)
    face_dist = joint["pFaceGivenTier"][forced_tier]
    rng = random.Random(seed)

    n_used = 0
    raw = 0.0
    capped = 0.0
    caps = 0
    excess = 0.0
    collector = 0
    head = 0
    passes_hist = Counter()
    route_raw = defaultdict(float)
    route_n = Counter()
    face_raw = defaultdict(float)
    face_cap = defaultdict(float)
    face_n = Counter()
    face_caps = Counter()
    threshold_hits = Counter()
    max_raw = 0.0

    attempts = 0
    while n_used < spins:
        attempts += 1
        if attempts > spins * 50:
            break
        stops = draw_stops(rng, tables["strips"])
        board = board_from_stops(tables["strips"], stops)
        evaluated = evaluate_paylines(
            board,
            paylines=tables["paylines"],
            paytable=tables["paytable"],
            scatter_id=tables["scatterId"],
            regular_ids=tables["regularIds"],
        )
        line_win = float(evaluated["lineWinX"])
        working, _coaches = _coach_transform(board, rng, tables["config"])
        myst = mystery_positions(working, tables["config"]["mysteryModel"]["id"])
        if not myst:
            continue
        j = rng.randrange(len(myst))
        faces = list(face_dist.keys())
        weights = [face_dist[f] for f in faces]
        face = rng.choices(faces, weights=weights, k=1)[0]

        from skyjump_v2_phase4a_economy import BOARD_SYMBOL_FOR_RESULT, empty_cell

        cells = [[empty_cell() for _ in range(5)] for _ in range(5)]
        for index, pos in enumerate(myst):
            if index == j:
                result = force_token_on_mystery(forced_tier, face, token_tables)
            else:
                result = sample_mystery_result(rng, candidate, token_tables)
                if result["resultType"] == "FLIGHT_TOKEN":
                    result["faceValueX"] = float(result["tokenValueX"])
                    result["effectiveValueX"] = float(result["tokenValueX"])
                    result["appliedThermals"] = []
            cell = empty_cell()
            cell.update(result)
            if cell["kind"] == "token":
                cell["faceValueX"] = float(cell.get("faceValueX") or cell["tokenValueX"])
                cell["effectiveValueX"] = float(cell["faceValueX"])
                cell["appliedThermals"] = list(cell.get("appliedThermals") or [])
                working[pos["reel"]][pos["row"]] = cell["tokenId"]
            else:
                working[pos["reel"]][pos["row"]] = BOARD_SYMBOL_FOR_RESULT[cell["resultType"]]
            cells[pos["reel"]][pos["row"]] = cell

        settled = _settle(cells, working, rng, candidate, token_tables, line_win)
        if require_collector and not settled["hasCollector"]:
            continue

        n_used += 1
        raw += settled["totalFeatureWinXRaw"]
        capped += settled["totalFeatureWinXCapped"]
        max_raw = max(max_raw, settled["totalWinXRaw"])
        if settled["capHit"]:
            caps += 1
            excess += settled["capDragX"]
        if settled["hasCollector"]:
            collector += 1
        if settled["headJudgeCount"] > 0:
            head += 1
        passes_hist[settled["collectorPasses"]] += 1
        face_n[face] += 1
        face_raw[face] += settled["totalFeatureWinXRaw"]
        face_cap[face] += settled["totalFeatureWinXCapped"]
        if settled["capHit"]:
            face_caps[face] += 1

        high = True
        has_th = settled["thermalCount"] > 0
        th2 = settled["thermalCount"] >= 2
        has_g = settled["gateCount"] > 0
        has_c = settled["hasCollector"]
        multi_c = settled["collectorPasses"] >= 3
        if has_g and has_th and multi_c:
            route = "high+gate+thermal+multi_collector"
        elif has_g and has_c:
            route = "high+gate+collector"
        elif has_th and has_c:
            route = "high+thermal+collector"
        elif th2:
            route = "high+2thermal"
        elif has_th:
            route = "high+thermal"
        elif has_g:
            route = "high+gate"
        elif has_c:
            route = "high+collector"
        else:
            route = "high_token_only"
        route_n[route] += 1
        route_raw[route] += settled["totalFeatureWinXRaw"]

        for thr in (1000, 5000, 10000, 25000, 50000, 100000, 200000):
            if settled["totalWinXRaw"] >= thr:
                threshold_hits[thr] += 1

    if n_used == 0:
        return {"forcedTier": forced_tier, "n": 0}

    return {
        "forcedTier": forced_tier,
        "n": n_used,
        "attempts": attempts,
        "E_raw": raw / n_used,
        "E_capped": capped / n_used,
        "pCap": caps / n_used,
        "E_excess_given_cap": (excess / caps) if caps else 0.0,
        "pCollector": collector / n_used,
        "pHeadJudge": head / n_used,
        "maxRaw": max_raw,
        "passesHist": {str(k): v / n_used for k, v in sorted(passes_hist.items())},
        "routes": {
            k: {"share": route_n[k] / n_used, "E_raw": route_raw[k] / route_n[k]}
            for k in route_n
        },
        "byFace": {
            str(int(face)): {
                "share": face_n[face] / n_used,
                "E_raw": face_raw[face] / face_n[face],
                "E_capped": face_cap[face] / face_n[face],
                "pCap": face_caps[face] / face_n[face],
            }
            for face in face_n
        },
        "rawThresholdsGiven": {str(k): threshold_hits[k] / n_used for k in sorted(threshold_hits)},
    }


def bulk_low_tier_mc(spins: int, seed: int, config: dict | None = None) -> dict:
    """Natural MC with decomposition; used for bulk (NO_T4PLUS) EV and diagnostics."""
    config = config or load_v2_config()
    tables = v2_math_tables(config)
    rng = random.Random(seed)
    totals = {
        "line": 0.0,
        "raw": 0.0,
        "capped": 0.0,
        "drag": 0.0,
        "caps": 0,
        "max_raw": 0.0,
    }
    by_stratum = defaultdict(lambda: {"n": 0, "raw": 0.0, "capped": 0.0, "caps": 0, "drag": 0.0})
    by_passes = defaultdict(lambda: {"n": 0, "raw": 0.0, "capped": 0.0})
    by_max_tier = defaultdict(lambda: {"n": 0, "raw": 0.0, "capped": 0.0})
    thresholds = Counter()

    for _ in range(spins):
        stops = draw_stops(rng, tables["strips"])
        board = board_from_stops(tables["strips"], stops)
        evaluated = evaluate_paylines(
            board,
            paylines=tables["paylines"],
            paytable=tables["paytable"],
            scatter_id=tables["scatterId"],
            regular_ids=tables["regularIds"],
        )
        line = float(evaluated["lineWinX"])
        features = resolve_features(board, rng, tables["config"], line_win_x=line)
        raw = float(features.get("totalFeatureWinXRaw") or 0)
        capped = float(features.get("totalFeatureWinXCapped") or features.get("totalFeatureWinX") or 0)
        total_raw = float(features.get("totalWinXRaw") or (line + raw))
        totals["line"] += line
        totals["raw"] += raw
        totals["capped"] += capped
        totals["max_raw"] = max(totals["max_raw"], total_raw)
        if features.get("capHit"):
            totals["caps"] += 1
            totals["drag"] += float(features.get("capDragX") or 0)
        max_tier = max(features.get("tokenTiers") or [0], default=0)
        if max_tier <= 3:
            stratum = "NO_T4PLUS"
        elif max_tier == 4:
            stratum = "T4_NO_T5PLUS"
        elif max_tier == 5:
            stratum = "T5_NO_T6"
        else:
            stratum = "T6_PRESENT"
        row = by_stratum[stratum]
        row["n"] += 1
        row["raw"] += raw
        row["capped"] += capped
        if features.get("capHit"):
            row["caps"] += 1
            row["drag"] += float(features.get("capDragX") or 0)
        passes = int(features.get("collectorPasses") or len(features.get("collections") or []))
        pk = "5+" if passes >= 5 else str(passes)
        by_passes[pk]["n"] += 1
        by_passes[pk]["raw"] += raw
        by_passes[pk]["capped"] += capped
        if max_tier >= 1:
            tk = f"T{max_tier}"
            by_max_tier[tk]["n"] += 1
            by_max_tier[tk]["raw"] += raw
            by_max_tier[tk]["capped"] += capped
        for thr in (1000, 5000, 10000, 25000, 50000, 100000, 200000):
            if total_raw >= thr:
                thresholds[thr] += 1

    def fin(src):
        out = {}
        for key, row in src.items():
            n = row["n"]
            out[key] = {
                "p": n / spins,
                "rawRtp": row["raw"] / spins,
                "cappedRtp": row["capped"] / spins,
                "E_raw_given": (row["raw"] / n) if n else 0.0,
                "E_capped_given": (row["capped"] / n) if n else 0.0,
            }
            if "caps" in row:
                out[key]["pCapGiven"] = (row["caps"] / n) if n else 0.0
                out[key]["capDragRtp"] = row["drag"] / spins
        return out

    return {
        "spins": spins,
        "seed": seed,
        "lineRtp": totals["line"] / spins,
        "featureRtpRaw": totals["raw"] / spins,
        "featureRtpCapped": totals["capped"] / spins,
        "pCap": totals["caps"] / spins,
        "capDragRtp": totals["drag"] / spins,
        "E_excess_given_cap": (totals["drag"] / totals["caps"]) if totals["caps"] else 0.0,
        "maxRawTotalWinX": totals["max_raw"],
        "byTierStratum": fin(by_stratum),
        "byCollectorPasses": fin(by_passes),
        "byMaxTierExclusive": fin(by_max_tier),
        "rawThresholds": {str(k): thresholds[k] / spins for k in sorted(thresholds)},
    }


def certified_from_strata(
    *,
    p_stratum: dict[str, float],
    bulk: dict,
    cond_t4: dict,
    cond_t5: dict,
    cond_t6: dict,
) -> dict:
    """Combine exact-ish P(stratum) with conditional expectations."""
    # Bulk MC already includes rare strata sparsely. Replace rare strata EV with conditional.
    # Contribution = P(stratum) * E[X|stratum]
    pieces = {}
    # NO_T4PLUS from bulk conditional
    bulk_s = bulk["byTierStratum"]
    pieces["NO_T4PLUS"] = {
        "p": p_stratum["NO_T4PLUS"],
        "E_raw": bulk_s.get("NO_T4PLUS", {}).get("E_raw_given", 0.0),
        "E_capped": bulk_s.get("NO_T4PLUS", {}).get("E_capped_given", 0.0),
        "pCap": bulk_s.get("NO_T4PLUS", {}).get("pCapGiven", 0.0),
        "source": "bulk_mc",
    }
    pieces["T4_NO_T5PLUS"] = {
        "p": p_stratum["T4_NO_T5PLUS"],
        "E_raw": cond_t4["E_raw"],
        "E_capped": cond_t4["E_capped"],
        "pCap": cond_t4["pCap"],
        "source": "forced_conditional",
    }
    pieces["T5_NO_T6"] = {
        "p": p_stratum["T5_NO_T6"],
        "E_raw": cond_t5["E_raw"],
        "E_capped": cond_t5["E_capped"],
        "pCap": cond_t5["pCap"],
        "source": "forced_conditional",
    }
    pieces["T6_PRESENT"] = {
        "p": p_stratum["T6_PRESENT"],
        "E_raw": cond_t6["E_raw"],
        "E_capped": cond_t6["E_capped"],
        "pCap": cond_t6["pCap"],
        "source": "forced_conditional",
    }

    raw = 0.0
    capped = 0.0
    p_cap = 0.0
    drag = 0.0
    for key, row in pieces.items():
        raw += row["p"] * row["E_raw"]
        capped += row["p"] * row["E_capped"]
        p_cap += row["p"] * row["pCap"]
        # excess approx: p(stratum)*pCap*E[excess|cap,stratum]
        if key == "T6_PRESENT":
            drag += row["p"] * row["pCap"] * cond_t6.get("E_excess_given_cap", 0.0)
        elif key == "T5_NO_T6":
            drag += row["p"] * row["pCap"] * cond_t5.get("E_excess_given_cap", 0.0)
        elif key == "T4_NO_T5PLUS":
            drag += row["p"] * row["pCap"] * cond_t4.get("E_excess_given_cap", 0.0)
        else:
            drag += bulk_s.get("NO_T4PLUS", {}).get("capDragRtp", 0.0)

    # Uncertainty: rare strata dominated by P(N) probe error + conditional SE
    def se_mean(e_sq_proxy: float, n: int) -> float:
        if n <= 1:
            return abs(e_sq_proxy)
        return abs(e_sq_proxy) / math.sqrt(n)

    # Rough: T6 contribution uncertainty
    p6 = p_stratum["T6_PRESENT"]
    se6 = p6 * se_mean(cond_t6["E_capped"], max(1, cond_t6["n"]))
    se5 = p_stratum["T5_NO_T6"] * se_mean(cond_t5["E_capped"], max(1, cond_t5["n"]))
    se4 = p_stratum["T4_NO_T5PLUS"] * se_mean(cond_t4["E_capped"], max(1, cond_t4["n"]))
    # Bulk SE from MC
    se_bulk = math.sqrt(max(1e-16, bulk["featureRtpCapped"] * 50 / bulk["spins"]))  # rough
    unc = math.sqrt(se6**2 + se5**2 + se4**2 + (0.3 * se_bulk) ** 2)
    # Also include model error for forcing proxy vs true max-tier conditioning (~10% of rare mass)
    model_err = 0.10 * (pieces["T6_PRESENT"]["p"] * pieces["T6_PRESENT"]["E_capped"]
                        + pieces["T5_NO_T6"]["p"] * pieces["T5_NO_T6"]["E_capped"]
                        + pieces["T4_NO_T5PLUS"]["p"] * pieces["T4_NO_T5PLUS"]["E_capped"])
    unc = max(unc, model_err)

    return {
        "featureRtpRaw": raw,
        "featureRtpCapped": capped,
        "pCap": p_cap,
        "capDragRtp": drag,
        "uncertaintyAbs": unc,
        "pieces": pieces,
        "pStratum": p_stratum,
    }
