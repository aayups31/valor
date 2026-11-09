"""Train frozen predictors and measure matched repeated-stakes development gates."""

import argparse
import hashlib
import json
import time
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.benchmarks.cascade_pilot import paired_interval, write_json
from aace.benchmarks.incident_memory import build_bank
from aace.benchmarks.repeated import Fixed, Markov, TASKS, Window, play, training_tokens
from aace.learning.repeated import fit, fit_markov, load
from aace.telemetry import source_provenance

FIT_SEEDS = (42, 43, 44)


def compare(a, b):
    if [r["seed"] for r in a] != [r["seed"] for r in b]:
        raise ValueError("Unpaired campaign comparison")
    values = {}
    for metric in ("score", "completion_rate", "failure_rate"):
        values[metric] = paired_interval([x[metric]-y[metric] for x, y in zip(a, b)])
    values["passes_predeclared_gate"] = (
        values["score"]["bootstrap_95_percent"][0] > 0
        and values["completion_rate"]["bootstrap_95_percent"][0] >= -.02
        and values["failure_rate"]["bootstrap_95_percent"][1] <= .01
    )
    return values


def average_fits(groups):
    return [
        {k: rows[0][k] if k == "seed" else sum(r[k] for r in rows)/len(rows)
         for k in rows[0] if k != "decisions"}
        for rows in zip(*groups, strict=True)
    ]


def run(output, *, smoke=False):
    started = time.perf_counter()
    provenance = source_provenance()
    training, bank_seeds, checks = ((range(120000, 120032), range(120100, 120104), range(120200, 120204))
                                    if smoke else (range(100000, 101024), range(102000, 102256), range(110000, 110256)))
    directory = output/f"{'smoke' if smoke else 'pilot'}-repeated-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    tokens = training_tokens(training)
    q, losses = fit_markov(tokens)
    markov = Markov(q)
    checkpoints, predictors = [], []
    for seed in FIT_SEEDS:
        checkpoint = fit(tokens, seed, epochs=2 if smoke else 30)
        path = directory/f"fit-{seed}.json"
        checksum = write_json(path, checkpoint)
        checkpoints.append({"file": path.name, "sha256": checksum, **{k: v for k, v in checkpoint.items() if k != "parameters"}})
        predictors.append(load(path))
        print(f"Frozen fit {seed}: {checkpoint['updates']} updates", flush=True)
    bank, bank_work = build_bank(bank_seeds, markov)
    records = bank.records()
    bank_hash = write_json(directory/"memory.json", records)
    actors = {"fixed": (Fixed(), {}), "window": (Window(), {}), "markov": (markov, {}),
              **{mode: (markov, {"retrieval": mode, "bank": bank}) for mode in ("heuristic", "factual", "verified")}}
    for seed, predictor in zip(FIT_SEEDS, predictors):
        actors[f"trained_{seed}"] = predictor, {}
        actors[f"reset_{seed}"] = predictor, {"reset": True}
    results, summary, elapsed = {}, {}, {}
    for actor, (predictor, options) in actors.items():
        phase = time.perf_counter()
        rows = []
        for seed in checks:
            row = play(seed, predictor, trace=seed == checks.start, **options)
            row["completion_rate"] = row["completed"]/TASKS
            row["failure_rate"] = (row["outage"]+row["release_failure"])/TASKS
            rows.append(row)
        results[actor] = rows
        summary[actor] = {k: sum(r[k] for r in rows)/len(rows) for k in rows[0] if k not in ("seed", "decisions")}
        attempts = sum(r["fast_attempts"] for r in rows)
        summary[actor]["observed_attempt_brier"] = sum(r["brier_sum"] for r in rows)/attempts if attempts else None
        elapsed[actor] = time.perf_counter()-phase
        print(f"{actor}: score {summary[actor]['score']:.3f}; {elapsed[actor]:.2f}s", flush=True)
    trained = average_fits([results[f"trained_{seed}"] for seed in FIT_SEEDS])
    resets = average_fits([results[f"reset_{seed}"] for seed in FIT_SEEDS])
    report = {
        "protocol": "repeated-stakes-v1", "engineering": smoke, "scheduled_tasks_per_campaign": TASKS,
        "campaigns": len(checks), "actor_campaigns": len(checks)*len(actors),
        "seed_ranges_inclusive": {k: [r.start, r.stop-1] for k, r in (("training", training), ("bank", bank_seeds), ("check", checks))},
        "public_training_sha256": hashlib.sha256(tokens.tobytes()).hexdigest(),
        "markov_switch": q, "markov_train_nll": losses, "fits": checkpoints,
        "bank_work": bank_work, "bank_records": len(records),
        "qualified_records": sum(r["recourse"] is not None for r in records),
        "bank_sha256": bank_hash, "rows_sha256": write_json(directory/"campaigns.json", results),
        "summary": summary, "actor_wall_seconds": elapsed,
        "comparisons": {"trained_minus_markov": compare(trained, results["markov"]),
                        "trained_minus_reset": compare(trained, resets),
                        "verified_minus_factual": compare(results["verified"], results["factual"])},
        "failure_notice": "Outage is absorbing. Scheduled tasks after outage count as uncompleted, not additional failures.",
        "forecast_notice": "Observed-attempt scores are conditional on each policy's attempts, not a matched forecasting set.",
        "scope": "Local development simulator. No felt fear, authority, deployment or final holdout validation.",
        "decision_ready": False, "external_spend_usd": 0, "elapsed_s": time.perf_counter()-started, **provenance,
    }
    write_json(directory/"report.json", report)
    print(json.dumps({"directory": str(directory.resolve()), "comparisons": report["comparisons"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/repeated-stakes"))
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    run(args.output, smoke=args.smoke)
