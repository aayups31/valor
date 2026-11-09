"""Execute preregistered shared-reserve development and independent shift checks."""

import argparse
import hashlib
import json
import time
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.benchmarks.cascade_pilot import write_json
from aace.benchmarks.shared_reserve import ACTORS, GUARDED, SHIFTS, play_pair
from aace.learning.repeated import Predictor
from aace.telemetry import source_provenance

MODEL_HASH = "89c6b3be7867407f04df5174ec9731f44626df70d558c0ea0f9c58bbbcb201f4"
BASE = "myopic_markov"
DEVELOPMENT = range(112000, 112512)
HOLDOUTS = {name: range(start, start+512) for name, start in zip(SHIFTS, (113000, 114000, 115000, 116000))}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(provenance):
    script = Path(__file__).resolve()
    protocol = script.parent.parent/"01_Architecture/CROSS_TASK_HOLDOUT_PROTOCOL.md"
    return {"python_source_sha256": provenance["python_source_sha256"], "runner_sha256": sha(script),
            "protocol_sha256": sha(protocol), "model_sha256": MODEL_HASH}


def interval(values, *, resamples, alpha):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(28115)
    sampled = np.concatenate([values[rng.integers(0, len(values), size=(min(512, resamples-i), len(values)))].mean(axis=1)
                              for i in range(0, resamples, 512)])
    return {"mean": float(values.mean()), "interval": np.quantile(sampled, [alpha/2, 1-alpha/2]).tolist(),
            "subjects": len(values), "resamples": resamples, "alpha": alpha}


def compare(candidate, baseline, *, validation=False):
    if [r["seed"] for r in candidate] != [r["seed"] for r in baseline]:
        raise ValueError("Unpaired campaign data")
    settings = {"resamples": 20000, "alpha": .05/16} if validation else {"resamples": 4000, "alpha": .05}
    result = {key: interval([a[key]-b[key] for a, b in zip(candidate, baseline)], **settings)
              for key in ("score", "completion_rate", "failure_rate")}
    score_bound = result["score"]["interval"][0]
    gates = {"score": score_bound >= -2 if validation else score_bound > 0,
             "completion": result["completion_rate"]["interval"][0] >= -.02,
             "failure": result["failure_rate"]["interval"][1] <= .01}
    if validation:
        result["failure_count_underprediction"] = (
            interval([2*r["failure_rate"]-r["initial_expected_pair_failures"] for r in candidate], **settings)
            if all(r["initial_expected_pair_failures"] is not None for r in candidate) else None)
        error = result["failure_count_underprediction"]
        gates["forecast"] = error is not None and error["interval"][1] <= .08
    result.update(gates=gates, passed=all(gates.values()))
    return result


def evaluate(seeds, scenario, actor, trained):
    began = time.perf_counter()
    planners = {}
    rows = [play_pair(seed, scenario, actor, planners, trained=trained, trace=seed == seeds.start) for seed in seeds]
    for planner in planners.values():
        planner.solve.cache_clear()
        planner.evaluate_pair.cache_clear()
    summary = {key: float(np.mean([r[key] for r in rows])) for key in
               ("score", "completion_rate", "failure_rate", "shocks", "incidents", "repairs", "stopped", "new_search_nodes")}
    summary["lookahead_executed_rate"] = sum(r["executed_policy"] != BASE for r in rows)/len(rows)
    summary["seconds"] = time.perf_counter()-began
    print(f"{scenario}/{actor}: score {summary['score']:.3f}; completed {summary['completion_rate']:.1%}; {summary['seconds']:.2f}s", flush=True)
    return rows, summary


def selection(comparisons):
    def passed(name):
        return comparisons[name]["passed"]

    if all(passed(n) for n in ("trained_vs_markov", "trained_vs_reset", "trained_vs_myopic")):
        return "horizon_trained"
    if passed("markov_vs_myopic"):
        return "horizon_markov"
    if passed("guarded_vs_myopic"):
        return GUARDED
    return BASE


def development(directory, trained, *, smoke, metadata):
    seeds = range(117000, 117008) if smoke else DEVELOPMENT
    rows, summary = {}, {}
    for actor in (*ACTORS, GUARDED):
        rows[actor], summary[actor] = evaluate(seeds, "nominal", actor, trained)
    pairs = {
        "markov_vs_myopic": ("horizon_markov", BASE),
        "markov_vs_fixed": ("horizon_markov", "horizon_fixed"),
        "trained_vs_markov": ("horizon_trained", "horizon_markov"),
        "trained_vs_reset": ("horizon_trained", "horizon_reset"),
        "trained_vs_myopic": ("horizon_trained", BASE),
        "guarded_vs_myopic": (GUARDED, BASE),
    }
    comparisons = {label: compare(rows[a], rows[b]) for label, (a, b) in pairs.items()}
    return {**metadata, "phase": "development", "engineering": smoke, "subjects": len(seeds),
            "seed_range_inclusive": [seeds.start, seeds.stop-1], "summary": summary, "comparisons": comparisons,
            "selected": selection(comparisons), "rows_sha256": write_json(directory/"rows.json", rows)}


def holdout(directory, trained, *, manifest, metadata):
    if (manifest["phase"] != "development" or manifest["engineering"] or manifest["git_dirty"]
            or manifest["fingerprints"] != metadata["fingerprints"]
            or manifest["seed_range_inclusive"] != [112000, 112511]
            or manifest["selected"] != selection(manifest["comparisons"])):
        raise ValueError("Selection must bind to clean frozen development source and the declared cohort")
    candidate = manifest["selected"]
    all_rows, results = {}, {}
    for scenario, seeds in HOLDOUTS.items():
        left, left_summary = evaluate(seeds, scenario, candidate, trained)
        right, right_summary = evaluate(seeds, scenario, BASE, trained)
        all_rows[scenario] = {"selected": left, "baseline": right}
        results[scenario] = {"seed_range_inclusive": [seeds.start, seeds.stop-1], "subjects": len(seeds),
                             "selected_summary": left_summary, "baseline_summary": right_summary,
                             "comparison": compare(left, right, validation=True)}
    return {**metadata, "phase": "holdout", "selected": candidate, "scenarios": results,
            "passes_scoped_shift_gate": all(r["comparison"]["passed"] for r in results.values()),
            "rows_sha256": write_json(directory/"rows.json", all_rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/shared-reserve"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--selection", type=Path, help="Frozen development report; enables shift validation")
    args = parser.parse_args()
    if args.smoke and args.selection:
        parser.error("Cannot use engineering smoke for holdout validation")
    raw = args.checkpoint.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MODEL_HASH:
        parser.error("Checkpoint is not the predeclared frozen fit 42")
    trained = Predictor(json.loads(raw))
    provenance = source_provenance()
    if not args.smoke and provenance["git_dirty"] is not False:
        parser.error("Measured runs require a clean source checkout")
    metadata = {**provenance, "fingerprints": fingerprints(provenance),
                "scope": "Local supplied-law simulation, not production or a risk certificate",
                "decision_ready": False, "external_spend_usd": 0}
    started = time.perf_counter()
    directory = args.output/f"{'shift' if args.selection else 'smoke' if args.smoke else 'dev'}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    if args.selection:
        report = holdout(directory, trained, manifest=json.loads(args.selection.read_text(encoding="utf-8")), metadata=metadata)
        report["frozen_selection_sha256"] = sha(args.selection)
    else:
        report = development(directory, trained, smoke=args.smoke, metadata=metadata)
    report["elapsed_s"] = time.perf_counter()-started
    write_json(directory/"report.json", report)
    print(json.dumps({"directory": str(directory.resolve()), "selected": report["selected"],
                      "passes_scoped_shift_gate": report.get("passes_scoped_shift_gate")}))


if __name__ == "__main__":
    main()
