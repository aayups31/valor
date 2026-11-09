"""Check paired artifacts and replay recorded paths without refitting or changing gates."""

import argparse
import json
import math
import runpy
from pathlib import Path

from aace.benchmarks.cascade import ReleaseState, available, transition
from aace.benchmarks.cascade_pilot import write_json
from aace.benchmarks.shared_reserve import choose_policy, next_task, subject

ROOT = Path(__file__).resolve().parent
RUNNER = runpy.run_path(str(ROOT/"Run-SharedReserve.py"))
sha, compare = RUNNER["sha"], RUNNER["compare"]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(directory):
    report = json.loads((directory/"report.json").read_text(encoding="utf-8"))
    rows = directory/"rows.json"
    require(not report["git_dirty"] and sha(rows) == report["rows_sha256"], "Dirty source or invalid artifact hash")
    return report, json.loads(rows.read_text(encoding="utf-8"))


def replay(row, scenario):
    initial, stakes, precursor, danger, draws = subject(row["seed"], scenario)
    require(list(precursor) == row["public_precursor"], "Public precursor mismatch")
    state, task, start_resources = initial, 0, initial.resources
    cumulative, completed, failures = 0., 0, 0
    screen = row["forecast_screen"]
    if screen is not None:
        require(screen["accepted"] == choose_policy(screen["lookahead"], screen["myopic"]), "Screen mismatch")
        selected = screen["lookahead"] if screen["accepted"] else screen["myopic"]
        require(selected == [row[k] for k in ("initial_expected_pair_score",
                    "initial_expected_pair_failures", "initial_expected_pair_completed")], "Wrong selected forecast")
    for decision in row["decisions"]:
        if decision["task"] != task:
            require(task == 0 and decision["task"] == 1, "Invalid task order")
            state = next_task(state)
            require(state is not None, "Task followed an outage")
            task, start_resources = 1, state.resources
        require(state == ReleaseState(**decision["before"]) and decision["stakes"] == stakes[task], "Discontinuous trace")
        actions = decision["alternatives"]
        require(tuple(actions) == available(state), "Incomplete legal alternatives")
        action = decision["selected"]
        require(action == max(actions, key=lambda a: actions[a]["expected_score"]), "Score/action mismatch")
        shock = action == "fast" and bool(draws[task, state.attempts] < danger[task])
        require(decision["observed_shock"] is (shock if action == "fast" else None), "Shock tape mismatch")
        state = transition(state, action, shock=shock)
        require(state == ReleaseState(**decision["after"]), "Invalid simulated transition")
        if state.status != "running":
            won = state.status == "completed"
            failed = state.status in ("release_failure", "outage")
            completed += won
            failures += failed
            cumulative += ((stakes[task]*(10-state.elapsed)/10 if won else 0.)
                           - 9*state.shocks-5*state.incidents-25*failed-.5*(start_resources-state.resources))
    require(math.isclose(cumulative, row["score"]) and completed/2 == row["completion_rate"]
            and failures/2 == row["failure_rate"], "Episode accounting mismatch")
    return len(row["decisions"])


def audit(replication, shift, frozen):
    report, paired = read(replication)
    heldout, scenarios = read(shift)
    require(json.loads(frozen.read_text(encoding="utf-8")) == report, "Frozen selection differs from replication")
    require(heldout["frozen_selection_sha256"] == sha(frozen), "Selection fingerprint mismatch")
    require(report["fingerprints"] == heldout["fingerprints"], "Policy source changed")
    require(set(scenarios) == set(RUNNER["HOLDOUTS"]), "Missing shift")
    count = 0
    seen = set()
    for name, runs, expected, result, validation in [
        ("nominal", paired, range(130000, 132048), report["comparison"], False),
        *((key, rows, RUNNER["HOLDOUTS"][key], heldout["scenarios"][key]["comparison"], True)
          for key, rows in scenarios.items()),
    ]:
        require(not seen.intersection(expected) and not any(20000 <= i < 30000 for i in expected), "Overlapping seeds")
        seen.update(expected)
        for rows in runs.values():
            require([row["seed"] for row in rows] == list(expected), "Wrong paired seed range")
            count += replay(rows[0], name)
        require(compare(runs["selected"], runs["baseline"], validation=validation) == result, "Comparison mismatch")
    return {"hashes": "verified", "distinct_subjects": len(seen), "replayed_decisions": count,
            "all_intervals_reproduced": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("replication", "shift", "frozen", "output"):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()
    write_json(args.output, audit(args.replication, args.shift, args.frozen))
