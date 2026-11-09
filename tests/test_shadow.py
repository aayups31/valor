from contextlib import closing
import sqlite3

import pytest

from aace.shadow import TABLE, observe, review, save


@pytest.fixture
def database(tmp_path):
    path = tmp_path/"fixture.sqlite3"
    with closing(sqlite3.connect(path)) as db:
        db.execute(TABLE)
        db.executemany("INSERT INTO items VALUES (?, ?, ?)", [(1, "pending", 0), (2, "protected", 0)])
        db.commit()
    return path


def execute(path, statement):
    with closing(sqlite3.connect(path)) as db:
        db.execute(statement)
        db.commit()


def test_shadow_observes_without_mutation_and_matches_separate_action(database):
    before = database.read_bytes()
    obs = observe(database, "archive_pending")
    assert database.read_bytes() == before and obs["authority"] == "none"
    assert obs["alternatives"]["archive_all"]["protected_changed_ids"] == [2]
    execute(database, "UPDATE items SET archived=1 WHERE state='pending'")
    applied = database.read_bytes()
    result = review(database, obs)
    assert result["forecast_matches_snapshot"] and result["observed_impact"]["changed_ids"] == [1]
    assert database.read_bytes() == applied


def test_warning_cannot_block_actual_overbroad_tool_action(database):
    obs = observe(database, "archive_all")
    assert obs["shadow_advisory"] == "protected_changes"
    execute(database, "UPDATE items SET archived=1")
    result = review(database, obs)
    assert result["forecast_matches_snapshot"]
    assert result["observed_impact"]["protected_changed_ids"] == [2]


def test_unexpected_delta_is_reported_and_cannot_rewrite_forecast(database, tmp_path):
    obs = observe(database, "archive_pending")
    execute(database, "UPDATE items SET archived=1")
    result = review(database, obs)
    assert not result["forecast_matches_snapshot"] and result["forecast_discrepancy_ids"] == [2]
    other = tmp_path/"other.sqlite3"
    other.write_bytes(database.read_bytes())
    with pytest.raises(ValueError, match="different database"):
        review(other, obs)
    with pytest.raises(ValueError, match="changed"):
        review(database, {**obs, "operation": "archive_all"})


def test_refuses_unknown_actions_active_sidecars_and_triggers(database):
    with pytest.raises(ValueError, match="Unsupported operation"):
        observe(database, "DELETE FROM items")
    sidecar = database.with_name(database.name+"-wal")
    sidecar.touch()
    with pytest.raises(ValueError, match="quiescent"):
        observe(database, "archive_pending")
    sidecar.unlink()
    execute(database, "CREATE TRIGGER watched AFTER UPDATE ON items BEGIN SELECT 1; END")
    with pytest.raises(ValueError, match="Unsupported schema"):
        observe(database, "archive_pending")


def test_evidence_write_is_exclusive(tmp_path):
    path = tmp_path/"record.json"
    save(path, {"example": 1})
    with pytest.raises(FileExistsError):
        save(path, {"example": 2})
