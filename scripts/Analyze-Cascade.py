"""Post-pilot diagnostic: integrate fixed policies under the declared generator."""

import argparse
import json
import math
from pathlib import Path

from aace.benchmarks.cascade import (
    ACTORS, HIGH, LOW, STAKES, ReleasePlanner, ReleaseState, belief, mixture,
    terminal_outcomes, transition,
)
from aace.benchmarks.cascade_pilot import outcome_record, write_json


def evaluate(planner, state, actual_danger):
    """Evaluate the chosen policy without supplying true danger to its decisions."""
    if state.status != "running":
        return terminal_outcomes(state, planner.stakes)
    action, _ = planner.decide(state)
    normal = evaluate(planner, transition(state, action), actual_danger)
    if action != "fast":
        return normal
    harmed = evaluate(planner, transition(state, action, shock=True), actual_danger)
    return mixture(normal, harmed, actual_danger)


def integrate():
    rows = []
    for stakes in STAKES:
        score_by_cell = {}
        for actor in ACTORS:
            total = {}
            for observed in range(9):
                conditional = {}
                for danger in (LOW, HIGH):
                    weight = .5*math.comb(8, observed)*danger**observed*(1-danger)**(8-observed)
                    planner = ReleasePlanner(actor, stakes, observed, oracle_danger=danger if actor == "oracle" else None)
                    actual = evaluate(planner, ReleaseState(), danger)
                    conditional[danger] = actual.score
                    score_by_cell[actor, observed, danger] = actual.score
                    for key, value in outcome_record(actual).items():
                        total[key] = total.get(key, 0.)+weight*value
                if actor == "adaptive":
                    posterior = belief(observed, 8)
                    expected = (1-posterior)*conditional[LOW]+posterior*conditional[HIGH]
                    if not math.isclose(expected, planner.decide(ReleaseState())[1].score, abs_tol=1e-10):
                        raise ValueError("Forecast differs from independent fixed-regime integration")
                    frozen_score = sum(p*score_by_cell["history", observed, d]
                                       for p, d in ((1-posterior, LOW), (posterior, HIGH)))
                    if expected < frozen_score-1e-10:
                        raise ValueError("Exact belief planner loses to a feasible frozen policy")
            rows.append({"stakes": stakes, "actor": actor, "exact_expected": total})
        for (_, observed, danger), score in score_by_cell.items():
            if score > score_by_cell["oracle", observed, danger]+1e-10:
                raise ValueError("A policy exceeded the exact known-danger optimum")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"scope": "Post-pilot analytic diagnostic; assumes the same known two-regime simulator. No new empirical data.",
              "rows": integrate()}
    write_json(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
