import importlib.util
import json
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "ollama_shadow", Path(__file__).resolve().parents[1] / "scripts/Run-OllamaShadow.py"
)
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


def reply(choice):
    return {"model": trial.MODEL, "done": True, "message": {"content": json.dumps(choice)}}


def test_invalid_operation_never_reaches_sqlite(tmp_path):
    row = trial.run_case(tmp_path, 0, lambda *_: reply({"operation": "drop_table"}))
    assert row["status"] == "model_error"
    assert trial.read_rows(tmp_path / "11700.sqlite3") == {1: ("pending", 0), 10: ("protected", 0)}


def test_observer_error_is_recorded_and_does_not_veto_worker(tmp_path, monkeypatch):
    def unavailable(*_):
        raise ValueError("fixture unavailable to observer")

    monkeypatch.setattr(trial, "observe", unavailable)
    row = trial.run_case(tmp_path, 0, lambda *_: reply({"operation": "archive_all"}))
    assert row["status"] == "observe_error"
    assert row["worker_changed_count"] == 2
    assert trial.read_rows(tmp_path / "11700.sqlite3") == {1: ("pending", 1), 10: ("protected", 1)}
    assert not trial.summarize([row], True)["gate_passed"]


def test_gate_uses_all_planned_cases_and_separates_worker_accuracy(tmp_path):
    def local_stub(route, body=None):
        if route == "tags":
            return {"models": [{"name": trial.MODEL, "digest": trial.DIGEST_PREFIX + "0" * 52}]}
        assert route == "chat"
        assert len(body["messages"]) == 2
        operator = json.loads(body["messages"][1]["content"])
        assert set(operator) == {"request", "rows"}
        operation = "archive_all" if operator["request"] == trial.BULK else "archive_pending"
        if body["options"]["seed"] == 11700:
            operation = "archive_all"
        return reply({"operation": operation})

    result = trial.run(tmp_path / "trial", local_stub)
    assert result["gate_passed"]
    assert result["reviewed"] == result["exact_snapshot_and_changes"] == 24
    assert result["followed_request"] == 23
    assert result["protected_write_cases"] == 7
    assert result["no_change_cases"] == 12
    assert result["observer_byte_changes"] == 0
