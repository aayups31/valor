"""Read-only shadow observation for a bounded SQLite archive workflow."""

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

SCHEMA = "valor-sqlite-shadow-v1"
TABLE = ("CREATE TABLE items (id INTEGER PRIMARY KEY, state TEXT NOT NULL "
         "CHECK(state IN ('pending','protected')), archived INTEGER NOT NULL CHECK(archived IN (0,1))) STRICT")
OPERATIONS = ("archive_pending", "archive_all")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def snapshot(path):
    db = Path(path).resolve(strict=True)
    if not db.is_file() or db.stat().st_size > 8*1024*1024:
        raise ValueError("Expected a bounded local SQLite file")
    with db.open("rb") as stream:
        header = stream.read(20)
    if header[:16] != b"SQLite format 3\x00" or header[18:20] != b"\x01\x01" or any(
        db.with_name(db.name+suffix).exists() for suffix in ("-journal", "-wal", "-shm")
    ):
        raise ValueError("Only quiescent rollback-journal SQLite files are supported")
    with closing(sqlite3.connect(db.as_uri()+"?mode=ro", uri=True, timeout=.2)) as connection:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA trusted_schema = OFF")
        connection.execute("BEGIN")
        objects = connection.execute("SELECT type, name, sql FROM sqlite_schema LIMIT 2").fetchall()
        if objects != [("table", "items", TABLE)]:
            raise ValueError("Unsupported schema or trigger; no forecast")
        rows = connection.execute("SELECT id, state, archived FROM items ORDER BY id LIMIT 1001").fetchall()
    if len(rows) > 1000 or any(not 0 < i < 2**31 or s not in ("pending", "protected") or a not in (0, 1)
                               for i, s, a in rows):
        raise ValueError("Unsupported data; no forecast")
    return digest(str(db)), [list(row) for row in rows]


def predict(rows, operation):
    if operation not in OPERATIONS:
        raise ValueError("Unsupported operation; no forecast")
    return [[i, state, 1 if operation == "archive_all" or state == "pending" else archived]
            for i, state, archived in rows]


def impact(before, after):
    left = {row[0]: row[1:] for row in before}
    right = {row[0]: row[1:] for row in after}
    changed = [i for i in sorted(left.keys() | right.keys()) if left.get(i) != right.get(i)]
    return {"changed_ids": changed, "protected_changed_ids": [i for i in changed if left.get(i, [None])[0] == "protected"],
            "pending_unarchived_ids": [i for i, s, a in after if s == "pending" and not a]}


def observe(path, operation):
    if operation not in OPERATIONS:
        raise ValueError("Unsupported operation; no forecast")
    target, before = snapshot(path)
    candidates = {op: impact(before, predict(before, op)) for op in OPERATIONS}
    proposed = candidates[operation]
    record = {"schema": SCHEMA, "record_id": uuid4().hex, "observed_at_utc": now(), "target": target,
              "operation": operation, "before": before, "before_sha256": digest(before),
              "expected_after_sha256": digest(predict(before, operation)), "proposed_impact": proposed,
              "alternatives": candidates, "shadow_advisory": "protected_changes" if proposed["protected_changed_ids"]
              else "no_protected_changes_predicted", "authority": "none"}
    return {**record, "record_sha256": digest(record)}


def review(path, observation):
    record = dict(observation)
    checksum = record.pop("record_sha256", None)
    if record.get("schema") != SCHEMA or checksum != digest(record):
        raise ValueError("Observation is incompatible or changed")
    target, after = snapshot(path)
    if record["target"] != target:
        raise ValueError("Observation refers to a different database")
    before = record["before"]
    expected = predict(before, record["operation"])
    if digest(before) != record["before_sha256"] or digest(expected) != record["expected_after_sha256"]:
        raise ValueError("Observation evidence mismatch")
    return {"schema": SCHEMA, "record_id": record["record_id"], "observation_sha256": checksum,
            "reviewed_at_utc": now(), "after_sha256": digest(after),
            "forecast_matches_snapshot": after == expected, "observed_impact": impact(before, after),
            "forecast_discrepancy_ids": impact(expected, after)["changed_ids"], "authority": "none",
            "scope": "A before/after snapshot comparison; discrepancies do not identify their cause."}


def save(path, record):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="phase", required=True)
    for phase in ("observe", "review"):
        cmd = sub.add_parser(phase)
        cmd.add_argument("database", type=Path)
        cmd.add_argument("--output", type=Path, required=True)
        if phase == "observe":
            cmd.add_argument("--operation", choices=OPERATIONS, required=True)
        else:
            cmd.add_argument("--observation", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.phase == "observe":
            record = observe(args.database, args.operation)
        else:
            if args.observation.stat().st_size > 256*1024:
                raise ValueError("Observation exceeds size limit")
            record = review(args.database, json.loads(args.observation.read_text(encoding="utf-8")))
        save(args.output, record)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        parser.error(str(error))
    print(json.dumps({k: v for k, v in record.items() if k != "before"}, indent=2))


if __name__ == "__main__":
    main()
