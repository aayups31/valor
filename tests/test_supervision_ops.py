import sqlite3
from contextlib import closing

import pytest

from aace.supervision import ArchiveSupervisor
from aace.supervision_ops import backup, inspect


@pytest.fixture
def supervisor(tmp_path):
    return ArchiveSupervisor.create(tmp_path / "source.sqlite3", [(1, "pending", 0), (10, "protected", 0)])


def test_verified_backup_keeps_receipts_and_can_resume_independently(supervisor, tmp_path):
    held = supervisor.propose("one", "archive_all")
    head = held["receipt_sha256"]
    copy = tmp_path / "copy.sqlite3"
    assert backup(supervisor.path, copy, head) == inspect(supervisor.path, head)
    with pytest.raises(FileExistsError):
        backup(supervisor.path, copy)
    restored = ArchiveSupervisor(copy)
    restored.resolve("one", head, approve=False)
    assert inspect(copy)["event_counts"] == {"proposal:held": 1, "resolution:denied": 1}
    assert inspect(supervisor.path, head)["audit_events"] == 1


def test_monitor_detects_unlogged_write_and_refuses_to_copy(supervisor, tmp_path):
    supervisor.propose("one", "archive_pending")
    with closing(sqlite3.connect(supervisor.path)) as db, db:
        db.execute("UPDATE items SET archived = 1 WHERE id = 10")
    with pytest.raises(ValueError, match="Current rows"):
        inspect(supervisor.path)
    copy = tmp_path / "copy.sqlite3"
    with pytest.raises(ValueError, match="Current rows"):
        backup(supervisor.path, copy)
    assert not copy.exists()


def test_external_head_detects_truncated_noop_tail(supervisor):
    supervisor.propose("one", "archive_pending")
    noop = supervisor.propose("two", "archive_pending")
    with closing(sqlite3.connect(supervisor.path)) as db, db:
        db.execute("DELETE FROM audit WHERE request = 'two'")
    assert inspect(supervisor.path)["audit_events"] == 1
    with pytest.raises(ValueError, match="operator checkpoint"):
        inspect(supervisor.path, noop["receipt_sha256"])


def test_monitor_detects_audit_corruption(supervisor):
    supervisor.propose("one", "archive_pending")
    with closing(sqlite3.connect(supervisor.path)) as db, db:
        db.execute("UPDATE audit SET record = replace(record, 'applied', 'altered')")
    with pytest.raises(ValueError, match="Audit mismatch"):
        inspect(supervisor.path)
