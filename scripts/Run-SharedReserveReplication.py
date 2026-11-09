"""Replicate the unchanged guarded policy, then validate only a frozen passing candidate."""

import argparse
import json
import runpy
import time
from pathlib import Path
from uuid import uuid4

from aace.benchmarks.cascade_pilot import write_json
from aace.benchmarks.shared_reserve import GUARDED
from aace.telemetry import source_provenance

REPLICATION = range(130000, 132048)
BASE = "myopic_markov"
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
RUNNER = runpy.run_path(str(SCRIPT.with_name("Run-SharedReserve.py")))
sha, evaluate, compare = (RUNNER[key] for key in ("sha", "evaluate", "compare"))
INITIAL = ROOT/"reports/2026-11-09-build-15-initial.json"


def identity():
    provenance = source_provenance()
    base = RUNNER["fingerprints"](provenance)
    original = json.loads(INITIAL.read_text(encoding="utf-8"))
    if (provenance["git_dirty"] is not False or original["git_dirty"] is not False
            or original["fingerprints"] != base or original["selected"] != BASE):
        raise ValueError("Replication requires the original unchanged clean source and inconclusive pilot")
    return {**provenance, "fingerprints": {
        **base, "initial_report_sha256": sha(INITIAL), "replication_runner_sha256": sha(SCRIPT),
        "replication_protocol_sha256": sha(ROOT/"01_Architecture/SHARED_RESERVE_REPLICATION.md"),
    }}


def validate_frozen(report, metadata):
    if (report.get("phase") != "replication" or report.get("fingerprints") != metadata["fingerprints"]
            or report.get("git_dirty") is not False or report.get("selected") != GUARDED
            or report.get("seed_range_inclusive") != [130000, 132047] or not report["comparison"]["passed"]):
        raise ValueError("Shift validation needs a passing frozen unchanged-policy replication")


def run(directory, metadata, frozen=None):
    started = time.perf_counter()
    if frozen is None:
        guarded, candidate = evaluate(REPLICATION, "nominal", GUARDED, None)
        myopic, baseline = evaluate(REPLICATION, "nominal", BASE, None)
        result = compare(guarded, myopic)
        report = {"phase": "replication", "seed_range_inclusive": [REPLICATION.start, REPLICATION.stop-1],
                  "subjects": len(REPLICATION), "selected": GUARDED if result["passed"] else BASE,
                  "comparison": result, "selected_summary": candidate, "baseline_summary": baseline}
        rows = {"selected": guarded, "baseline": myopic}
    else:
        selection = json.loads(frozen.read_text(encoding="utf-8"))
        validate_frozen(selection, metadata)
        rows, scenarios = {}, {}
        for scenario, seeds in RUNNER["HOLDOUTS"].items():
            guarded, candidate = evaluate(seeds, scenario, GUARDED, None)
            myopic, baseline = evaluate(seeds, scenario, BASE, None)
            rows[scenario] = {"selected": guarded, "baseline": myopic}
            scenarios[scenario] = {"seed_range_inclusive": [seeds.start, seeds.stop-1], "subjects": len(seeds),
                                   "selected_summary": candidate, "baseline_summary": baseline,
                                   "comparison": compare(guarded, myopic, validation=True)}
        report = {"phase": "shift", "selected": GUARDED, "scenarios": scenarios,
                  "frozen_selection_sha256": sha(frozen),
                  "passes_scoped_shift_gate": all(r["comparison"]["passed"] for r in scenarios.values())}
    report.update(metadata, scope="Local simulator only; no individual risk bounds or authority",
                  decision_ready=False, external_spend_usd=0, elapsed_s=time.perf_counter()-started,
                  rows_sha256=write_json(directory/"rows.json", rows))
    write_json(directory/"report.json", report)
    print(json.dumps({"directory": str(directory.resolve()), "selected": report["selected"],
                      "passes_scoped_shift_gate": report.get("passes_scoped_shift_gate")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/shared-reserve"))
    parser.add_argument("--selection", type=Path, help="Passing frozen replication report; enables shifts")
    args = parser.parse_args()
    metadata = identity()
    directory = args.output/f"{'shift' if args.selection else 'replication'}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    run(directory, metadata, args.selection)
