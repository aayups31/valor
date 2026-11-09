"""Read-only health checks and verified copies for the supervised archive workflow."""

import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing, contextmanager
from pathlib import Path
from time import monotonic

from aace.shadow import digest
from aace.supervision import ArchiveSupervisor


@contextmanager
def _reader(path):
    source = Path(path).resolve(strict=True).as_uri()
    with closing(sqlite3.connect(source + "?mode=ro", uri=True, timeout=1)) as db:
        db.execute("PRAGMA trusted_schema = OFF")
        db.execute("BEGIN")
        ArchiveSupervisor._validate(db)
        yield db


def _inspect(db, expected_head):
    if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise ValueError("SQLite integrity check failed")
    latest = None
    head = None
    counts = Counter()
    for index, (seq, kind, request, value) in enumerate(
        db.execute("SELECT seq, kind, request, record FROM audit ORDER BY seq"), 1
    ):
        receipt = json.loads(value)
        checksum = receipt.pop("receipt_sha256")
        if (seq != index or receipt["kind"] != kind or receipt["request"] != request
                or checksum != digest(receipt) or (latest is not None and receipt["before"] != latest)):
            raise ValueError(f"Audit mismatch at event {index}")
        latest = receipt["after"]
        head = checksum
        counts[f'{kind}:{receipt["status"]}'] += 1
    current = ArchiveSupervisor._rows(db)
    if latest is not None and current != latest:
        raise ValueError("Current rows do not match the latest audit receipt")
    if expected_head is not None and expected_head != head:
        raise ValueError("Latest receipt does not match the operator checkpoint")
    return {"status": "ok", "audit_events": sum(counts.values()), "audit_head_sha256": head,
            "event_counts": dict(counts), "rows_sha256": digest(current)}


def inspect(path, expected_head=None):
    with _reader(path) as db:
        return _inspect(db, expected_head)


def backup(source, destination, expected_head=None):
    """Copy a verified snapshot into a new file. Never replace an existing database."""
    destination = Path(destination).absolute()
    deadline = monotonic() + 10

    def check_deadline(*_):
        if monotonic() >= deadline:
            raise TimeoutError("SQLite backup deadline exceeded")

    with _reader(source) as db:
        verified = _inspect(db, expected_head)
        with destination.open("xb"):
            pass
        with closing(sqlite3.connect(destination, timeout=1)) as copy:
            db.backup(copy, pages=128, progress=check_deadline, sleep=.05)
    result = inspect(destination, expected_head)
    if result != verified:
        raise ValueError("Backup does not match the verified source snapshot")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("--expect-head", help="Latest receipt digest recorded separately by the operator")
    parser.add_argument("--copy-to", type=Path, help="Write a verified snapshot to a new file")
    args = parser.parse_args()
    try:
        if args.copy_to:
            report = backup(args.database, args.copy_to, args.expect_head)
        else:
            report = inspect(args.database, args.expect_head)
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.exit(1, json.dumps({"status": "failed", "error": str(error)}) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
