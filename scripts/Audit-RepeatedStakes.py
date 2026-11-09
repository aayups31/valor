"""Verify saved repeated-stakes artifacts and derive labeled secondary comparisons."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from aace.benchmarks.cascade import ReleaseState, available, transition
from aace.benchmarks.cascade_pilot import paired_interval, write_json
from aace.benchmarks.incident_memory import Bank, Record
from aace.benchmarks.repeated import BOUNDARY, SHOCK, TASKS, Markov, campaign, carry, training_tokens
from aace.learning.repeated import Predictor


def require(condition, message):
    if not condition:
        raise ValueError(message)


def common_probes(predictor, tokens, *, reset=False):
    count, brier, nll = 0, 0., 0.
    for sequence in tokens:
        state = predictor.initial
        for token in sequence:
            if token < 0:
                break
            if token == BOUNDARY:
                if reset:
                    state = predictor.initial
            else:
                p, outcome = predictor.probability(state), int(token == SHOCK)
                brier += (p-outcome)**2
                nll -= math.log(p if outcome else 1-p)
                count += 1
            state = predictor.update(state, token)
    return {"observations": count, "brier": brier/count, "log_loss": nll/count}


def audit(directory):
    report = json.loads((directory/"report.json").read_text(encoding="utf-8"))

    def read(filename, expected):
        data = (directory/filename).read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected, f"Hash mismatch: {filename}")
        return json.loads(data)

    splits = {name: range(lo, hi+1) for name, (lo, hi) in report["seed_ranges_inclusive"].items()}
    require(len(set().union(*splits.values())) == sum(map(len, splits.values())), "Overlapping splits")
    require(hashlib.sha256(training_tokens(splits["training"]).tobytes()).hexdigest()
            == report["public_training_sha256"], "Training stream does not reproduce")
    predictors = {}
    for fit in report["fits"]:
        require(fit["file"] == f"fit-{fit['seed']}.json", "Unexpected checkpoint filename")
        predictors[fit["seed"]] = Predictor(read(fit["file"], fit["sha256"]))
    records = read("memory.json", report["bank_sha256"])
    bank = Bank()
    for record in records:
        require(record["seed"] in splits["bank"], "Memory originated outside bank split")
        bank.put(Record(**{**record, "state": ReleaseState(**record["state"]),
                          "observed_after": ReleaseState(**record["observed_after"])}))
    require(len(bank.records()) == len(records), "Duplicate record contexts")
    actors = read("campaigns.json", report["rows_sha256"])
    checked_transitions = 0
    for actor, rows in actors.items():
        require([r["seed"] for r in rows] == list(splits["check"]), "Campaign pairing mismatch")
        for key, mean in report["summary"][actor].items():
            if key != "observed_attempt_brier":
                require(math.isclose(mean, sum(r[key] for r in rows)/len(rows)), "Aggregate mismatch")
        for row in rows:
            ended = sum(row[k] for k in ("completed", "stopped", "outage", "release_failure"))
            require(ended <= TASKS and (row["outage"] == 1 or ended == TASKS), "Invalid campaign terminals")
            require(row["forecast_calls"] >= row["root_candidates"], "Invalid search accounting")
            if "decisions" not in row:
                continue
            dangers, stakes, draws, _ = campaign(row["seed"])
            previous, task = None, -1
            for step in row["decisions"]:
                state = ReleaseState(**step["before"])
                if step["task"] != task:
                    require(step["task"] == task+1, "Skipped task in trace")
                    require(state == (ReleaseState() if previous is None else carry(previous)), "Broken carryover")
                    task = step["task"]
                else:
                    require(state == previous, "Broken within-task trace")
                require(step["stakes"] == stakes[task], "Unexpected objective")
                action, scored = step["selected"], step["evaluated"]
                require(set(scored) <= set(available(state)), "Illegal candidate")
                require(action == max(scored, key=lambda a: scored[a]["score"]), "Action disagrees with scores")
                if actor in ("heuristic", "factual", "verified"):
                    require("stop" in scored and len(scored) <= 3, "Root cap violated")
                shock = action == "fast" and bool(draws[task, state.attempts] < dangers[task])
                require(step["observed_shock"] is (shock if action == "fast" else None), "Wrong observed shock")
                previous = transition(state, action, shock=shock)
                require(previous == ReleaseState(**step["after"]), "Transition disagrees with trace")
                checked_transitions += 1
    secondary = {
        "verified_minus_heuristic": {key: paired_interval([a[key]-b[key]
            for a, b in zip(actors["verified"], actors["heuristic"], strict=True)])
            for key in ("score", "completion_rate", "failure_rate", "root_candidates", "forecast_calls")},
        "verified_score_differs_from_factual_campaigns": sum(a["score"] != b["score"]
            for a, b in zip(actors["verified"], actors["factual"], strict=True)),
    }
    if not report["engineering"]:
        seeds = range(111000, 111256)
        require(not any(set(seeds).intersection(r) for r in splits.values()), "Overlapping probe split")
        tokens = training_tokens(seeds)
        secondary["common_public_probes"] = {
            "scope": "Post-pilot forecasting diagnostic on identical exogenous observations, not a policy test",
            "seed_range_inclusive": [seeds.start, seeds.stop-1],
            "markov": common_probes(Markov(report["markov_switch"]), tokens),
            **{f"{mode}_{seed}": common_probes(predictor, tokens, reset=mode == "reset")
               for seed, predictor in predictors.items() for mode in ("trained", "reset")},
        }
    return {**report, "pilot_artifact": str(directory), "verification": {
        "artifact_hashes": "verified", "split_and_training_stream": "verified",
        "paired_aggregates": "verified", "replayed_decisions": checked_transitions},
        "exploratory_secondary": secondary}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, audit(args.directory))
