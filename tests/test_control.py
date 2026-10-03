from dataclasses import replace

import pytest

from aace.controllers import action_for_plan
from aace.envs.rover import RoverEnv
from aace.planning import guard_action
from aace.runtime import Session


def moving_observation():
    env = RoverEnv()
    env.reset(seed=0)
    return replace(env.observe(), state=replace(env.state, vx=1))


def test_brake_and_coast_have_different_commands():
    observation = moving_observation()
    assert action_for_plan(observation, "coast") == (0, 0)
    assert action_for_plan(observation, "brake")[0] < 0


def test_external_stop_precedes_invalid_output():
    result = guard_action((float("nan"), 99), moving_observation(), external_stop=True)
    assert result.reason == "external_stop" and result.action[0] < 0


@pytest.mark.parametrize("invalid", [(float("nan"), 0), None, (1,), ("bad", 0)])
def test_guard_replaces_invalid_commands(invalid):
    result = guard_action(invalid, moving_observation())
    assert result.reason == "invalid_action" and result.action[0] < 0


def test_guard_clips_and_reports_change():
    result = guard_action((3, -2), moving_observation())
    assert result.action == (1, -1) and result.reason == "action_clipped"


def test_trace_records_selected_and_actual_action():
    session = Session("benign")
    session.step()
    record = session.step(external_stop=True)
    assert record["guard_reason"] == "external_stop"
    assert record["applied_action"] != record["proposed_action"]
    assert record["observation"]["state"]["step"] == 1
    assert record["actual_outcome"]["state"]["step"] == 2
    assert [c["plan"] for c in record["candidates"] if c["status"] == "selected"] == [record["selected_plan"]]
    assert all(c["forecast"] is None for c in record["candidates"])


def test_same_seed_sessions_match_actions_and_outcomes():
    a, b = Session("shortcut", seed=71), Session("shortcut", seed=71)
    for _ in range(20):
        first, second = a.step(), b.step()
        assert first["applied_action"] == second["applied_action"]
        assert first["actual_outcome"] == second["actual_outcome"]


def test_stop_does_not_wait_for_controller():
    class BrokenController:
        name = "broken"

        def decide(self, observation):
            raise AssertionError("External stop must bypass controller execution")

    session = Session("benign")
    session.controller = BrokenController()
    record = session.step(external_stop=True)
    assert record["controller_bypassed"] and record["proposed_action"] is None


def test_invalid_controller_action_is_guarded_and_exportable(tmp_path):
    import json
    from aace.controllers import Proposal

    class InvalidController:
        name = "invalid"

        def decide(self, observation):
            action = (float("nan"), 0)
            return Proposal("invalid", action, ({"plan": "invalid", "action": action,
                            "status": "selected", "reason_codes": [], "forecast": None},))

    session = Session("benign")
    session.controller = InvalidController()
    record = session.step()
    assert record["guard_reason"] == "invalid_action"
    assert not record["proposed_action_valid"]
    assert record["proposed_action"] == (None, 0)
    assert record["candidates"][0]["status"] == "guard_overridden"
    assert record["actual_outcome"]["state"]["step"] == 1
    artifact = json.loads(session.export(tmp_path).read_text())
    assert artifact["decisions"][0]["actual_outcome"] == record["actual_outcome"]
    assert artifact["header"]["python_source_sha256"]
