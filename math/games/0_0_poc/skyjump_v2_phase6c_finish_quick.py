"""Finish remaining Phase 6C quick sections without re-running paired modes."""

from __future__ import annotations

import json
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase6c_certify import (
    exact_wind_transitions,
    feature_off_equivalence,
    research_e1_repro,
    stratified_tails,
    wind_instrument_pass,
)

OUT = Path(__file__).resolve().parent / "phase6c_research"
PATH = OUT / "quick_cert.json"


def main() -> None:
    cfg = load_v2_config()
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    seed = 20260926
    n = 80_000
    if "wind" not in payload:
        print("wind…", flush=True)
        payload["wind"] = wind_instrument_pass(cfg, cand, pay, n, seed + 3)
        PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if "exactWind" not in payload:
        print("exact…", flush=True)
        payload["exactWind"] = exact_wind_transitions()
        PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if "featureOffEquivalence" not in payload:
        print("feature-off…", flush=True)
        payload["featureOffEquivalence"] = feature_off_equivalence(cfg, cand, pay, n=n, seed=seed + 9)
        PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if "researchE1" not in payload:
        print("e1…", flush=True)
        payload["researchE1"] = research_e1_repro(n=200_000, seed=20260923)
        PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if "stratified" not in payload:
        print("strata…", flush=True)
        payload["stratified"] = stratified_tails(cfg, cand, pay)
        PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", PATH, flush=True)


if __name__ == "__main__":
    main()
