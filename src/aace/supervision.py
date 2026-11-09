"""Transactional supervision for the disposable SQLite archive workflow."""

import argparse
import json
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from uuid import uuid4

from aace.shadow import OPERATIONS, TABLE, digest, impact, now, predict

AUDIT = ("CREATE TABLE audit (seq INTEGER PRIMARY KEY, kind TEXT NOT NULL, request TEXT NOT NULL, "
         "record TEXT NOT NULL, UNIQUE(kind, request)) STRICT")
APP_ID = 0x56414C52


class ArchiveSupervisor:
    """The host owns this object. The model may only propose an operation."""

    def __init__(self, path):
        self.path = Path(path).resolve(strict=True)

    @classmethod
    def create(cls, path, rows):
        path = Path(path).absolute()
        with path.open("xb"):
            pass
        supervisor = cls(path)
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(f"PRAGMA application_id = {APP_ID}")
            db.execute(TABLE)
            db.execute(AUDIT)
            db.executemany("INSERT INTO items VALUES (?, ?, ?)", rows)
            supervisor._rows(db)
        return supervisor

    @contextmanager
    def _transaction(self):
        with closing(sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=1)) as db, db:
            db.execute("PRAGMA trusted_schema = OFF")
            db.execute("BEGIN IMMEDIATE")
            schema = db.execute("SELECT sql FROM sqlite_schema WHERE sql IS NOT NULL ORDER BY name LIMIT 3").fetchall()
            if schema != [(AUDIT,), (TABLE,)] or db.execute("PRAGMA application_id").fetchone()[0] != APP_ID:
                raise ValueError("Unsupported supervised database")
            yield db

    @staticmethod
    def _rows(db):
        rows = [list(row) for row in db.execute("SELECT id, state, archived FROM items ORDER BY id LIMIT 1001")]
        if len(rows) > 1000 or any(not 0 < row[0] < 2**31 for row in rows):
            raise ValueError("Unsupported archive rows")
        return rows

    @staticmethod
    def _prior(db, kind, request):
        row = db.execute("SELECT seq, record FROM audit WHERE kind = ? AND request = ?", (kind, request)).fetchone()
        return (row[0], json.loads(row[1])) if row else (None, None)

    @staticmethod
    def _head(db):
        return db.execute("SELECT max(seq) FROM audit").fetchone()[0]

    @staticmethod
    def _record(db, kind, request, record):
        receipt = {"kind": kind, "request": request, "event_id": uuid4().hex, "at_utc": now(), **record}
        receipt["receipt_sha256"] = digest(receipt)
        db.execute("INSERT INTO audit (kind, request, record) VALUES (?, ?, ?)",
                   (kind, request, json.dumps(receipt, allow_nan=False)))
        return receipt

    @staticmethod
    def _apply(db, before, after):
        updates = [(new[2], old[0]) for old, new in zip(before, after) if old[2] != new[2]]
        db.executemany("UPDATE items SET archived = ? WHERE id = ?", updates)
        if ArchiveSupervisor._rows(db) != after:
            raise ValueError("The write did not match the planned state")

    def propose(self, request, operation):
        if not isinstance(request, str) or not 1 <= len(request) <= 80 or operation not in OPERATIONS:
            raise ValueError("Unsupported request or operation")
        with self._transaction() as db:
            _, previous = self._prior(db, "proposal", request)
            if previous is not None:
                if previous["operation"] != operation:
                    raise ValueError("Request ID already used for a different operation")
                return previous
            before = self._rows(db)
            predicted = predict(before, operation)
            proposed = impact(before, predicted)
            status = "held" if proposed["protected_changed_ids"] else "applied"
            if status == "applied":
                self._apply(db, before, predicted)
            return self._record(db, "proposal", request, {
                "operation": operation, "status": status, "before": before, "predicted": predicted,
                "after": before if status == "held" else predicted, "forecast": proposed,
                "alternative": impact(before, predict(before, "archive_pending")),
            })

    def resolve(self, request, proposal_sha, *, approve):
        """Trusted operator only. An approval expires after any intervening audit event or state change."""
        if type(approve) is not bool:
            raise ValueError("An explicit operator decision is required")
        with self._transaction() as db:
            seq, proposal = self._prior(db, "proposal", request)
            if not proposal or proposal["status"] != "held" or proposal["receipt_sha256"] != proposal_sha:
                raise ValueError("Approval does not match a held proposal")
            _, prior = self._prior(db, "resolution", request)
            if prior:
                if prior["approve"] != approve:
                    raise ValueError("Proposal already resolved")
                return prior
            before = self._rows(db)
            if approve and (seq != self._head(db) or before != proposal["before"]):
                raise ValueError("Proposal is stale. Submit a new proposal for review")
            after = proposal["predicted"] if approve else before
            if approve:
                self._apply(db, before, after)
            return self._record(db, "resolution", request, {
                "status": "applied" if approve else "denied", "approve": approve,
                "proposal_sha256": proposal_sha, "before": before, "after": after,
            })

    def recover(self, request, applied_sha):
        """Trusted operator only. Restore the exact prior state of the latest applied event."""
        with self._transaction() as db:
            _, prior = self._prior(db, "recovery", request)
            if prior:
                if prior["applied_sha256"] != applied_sha:
                    raise ValueError("Request already recovered using a different receipt")
                return prior
            for kind in ("resolution", "proposal"):
                seq, applied = self._prior(db, kind, request)
                if applied and applied["receipt_sha256"] == applied_sha and applied["status"] == "applied":
                    break
            else:
                raise ValueError("Recovery requires an applied receipt")
            before = self._rows(db)
            if seq != self._head(db) or before != applied["after"]:
                raise ValueError("Recovery would overwrite newer work")
            after = applied["before"]
            self._apply(db, before, after)
            return self._record(db, "recovery", request, {
                "status": "restored", "applied_sha256": applied_sha, "before": before, "after": after,
            })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create a new synthetic fixture")
    propose = commands.add_parser("propose")
    propose.add_argument("request")
    propose.add_argument("operation", choices=OPERATIONS)
    for name in ("approve", "deny", "recover"):
        command = commands.add_parser(name)
        command.add_argument("request")
        command.add_argument("receipt_sha256")
    args = parser.parse_args()
    try:
        if args.command == "init":
            ArchiveSupervisor.create(args.database, [(1, "pending", 0), (10, "protected", 0)])
            record = {"status": "initialized"}
        else:
            supervisor = ArchiveSupervisor(args.database)
            if args.command == "propose":
                record = supervisor.propose(args.request, args.operation)
            elif args.command == "recover":
                record = supervisor.recover(args.request, args.receipt_sha256)
            else:
                record = supervisor.resolve(args.request, args.receipt_sha256, approve=args.command == "approve")
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
