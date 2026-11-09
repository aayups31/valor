import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import pytest

from aace.supervision import ArchiveSupervisor


@pytest.fixture
def supervisor(tmp_path):
    return ArchiveSupervisor.create(tmp_path / "fixture.sqlite3", [(1, "pending", 0), (10, "protected", 0)])


def state(supervisor):
    with closing(sqlite3.connect(supervisor.path)) as db:
        return db.execute("SELECT archived FROM items ORDER BY id").fetchall(), db.execute("SELECT count(*) FROM audit").fetchone()[0]


def test_operator_approval_and_recovery_survive_reopen(supervisor):
    held = supervisor.propose("req", "archive_all")
    assert held["status"] == "held" and held["forecast"]["protected_changed_ids"] == [10]
    assert state(supervisor) == ([(0,), (0,)], 1)
    supervisor = ArchiveSupervisor(supervisor.path)
    with pytest.raises(ValueError, match="does not match"):
        supervisor.resolve("req", "bad-sha", approve=True)
    approved = supervisor.resolve("req", held["receipt_sha256"], approve=True)
    assert state(supervisor) == ([(1,), (1,)], 2)
    assert supervisor.resolve("req", held["receipt_sha256"], approve=True) == approved
    restored = supervisor.recover("req", approved["receipt_sha256"])
    assert restored["status"] == "restored" and state(supervisor) == ([(0,), (0,)], 3)
    assert supervisor.recover("req", approved["receipt_sha256"]) == restored


def test_denial_is_final_and_does_not_write(supervisor):
    held = supervisor.propose("req", "archive_all")
    assert supervisor.resolve("req", held["receipt_sha256"], approve=False)["status"] == "denied"
    with pytest.raises(ValueError, match="already resolved"):
        supervisor.resolve("req", held["receipt_sha256"], approve=True)
    assert state(supervisor) == ([(0,), (0,)], 2)


def test_stale_approval_and_stale_recovery_are_rejected(supervisor):
    held = supervisor.propose("req", "archive_all")
    applied = supervisor.propose("next", "archive_pending")
    with pytest.raises(ValueError, match="stale"):
        supervisor.resolve("req", held["receipt_sha256"], approve=True)
    supervisor.propose("newer", "archive_pending")
    with pytest.raises(ValueError, match="newer work"):
        supervisor.recover("next", applied["receipt_sha256"])
    assert state(supervisor) == ([(1,), (0,)], 3)


def test_concurrent_retries_return_one_receipt(supervisor):
    with ThreadPoolExecutor(2) as pool:
        first, second = pool.map(lambda _: supervisor.propose("req", "archive_pending"), range(2))
    assert first == second and first["status"] == "applied"
    with pytest.raises(ValueError, match="different operation"):
        supervisor.propose("req", "archive_all")
    assert state(supervisor) == ([(1,), (0,)], 1)


def test_audit_failure_rolls_back_the_write(supervisor, monkeypatch):
    def fail(*_):
        raise sqlite3.OperationalError("audit unavailable")

    monkeypatch.setattr(supervisor, "_record", fail)
    with pytest.raises(sqlite3.OperationalError, match="audit unavailable"):
        supervisor.propose("req", "archive_pending")
    assert state(supervisor) == ([(0,), (0,)], 0)


def test_rejects_foreign_schema_and_invalid_operations(supervisor):
    with pytest.raises(ValueError, match="Unsupported request"):
        supervisor.propose("req", "delete")
    with closing(sqlite3.connect(supervisor.path)) as db, db:
        db.execute("CREATE TRIGGER unsafe AFTER UPDATE ON items BEGIN DELETE FROM items; END")
    with pytest.raises(ValueError, match="Unsupported supervised database"):
        supervisor.propose("req", "archive_pending")
    assert state(supervisor) == ([(0,), (0,)], 0)
