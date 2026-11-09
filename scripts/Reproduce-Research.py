"""Recreate the frozen checkpoint 8/9 rows from a disposable local Git clone."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

REVISION = "64fdca033f23cfff5141229becbaa7f8d9655a50"
ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(destination):
    destination = destination.resolve()
    if destination.exists():
        raise ValueError("Choose a new destination; existing directories are not reused")
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout",
                    str(ROOT), str(destination)], check=True)
    subprocess.run(["git", "-C", str(destination), "checkout", "--quiet", "--detach", REVISION], check=True)
    env = dict(os.environ, PYTHONPATH=str(destination/"src"))
    results = destination/"artifacts/reproduced"
    command = [sys.executable, "scripts/Run-SharedReserveReplication.py", "--output", str(results)]
    subprocess.run(command, cwd=destination, env=env, check=True)
    local_selection, = results.glob("replication-*/report.json")
    replica = read(local_selection)
    frozen = read(ROOT/"reports/2026-11-09-build-15-frozen-selection.json")
    if any(replica[k] != frozen[k] for k in ("rows_sha256", "comparison", "selected")):
        raise ValueError("Replication rows or selection did not reproduce")
    # The new report binds the same selection to this checkout's file bytes.
    # A Git checkout can normalize line endings in the historical input report.
    subprocess.run([*command, "--selection", str(local_selection)], cwd=destination, env=env, check=True)
    shift, = results.glob("shift-*/report.json")
    result = read(shift)
    expected = read(ROOT/"reports/2026-11-09-build-15-shifts.json")
    if any(result[k] != expected[k] for k in ("rows_sha256", "passes_scoped_shift_gate")) or {
        k: v["comparison"] for k, v in result["scenarios"].items()
    } != {k: v["comparison"] for k, v in expected["scenarios"].items()}:
        raise ValueError("Shift rows or intervals did not reproduce")
    return {"source_revision": REVISION, "replication_rows_sha256": replica["rows_sha256"],
            "shift_rows_sha256": result["rows_sha256"], "paired_intervals_reproduced": True,
            "passed_scoped_shift_gate": result["passes_scoped_shift_gate"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path,
                        default=ROOT/"artifacts"/f"research-repro-{uuid4().hex[:8]}")
    args = parser.parse_args()
    print(json.dumps(run(args.directory), indent=2))
