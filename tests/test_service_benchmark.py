from dataclasses import replace

import pytest

from aace.benchmarks.service import ServiceForecaster, ServiceWorkflow
from aace.decision import ActionAuthority, ComputeBudget, DecisionEngine


def proposal(environment):
    authority = ActionAuthority()
    return DecisionEngine().decide(environment.context(0), environment.candidates(),
        ServiceForecaster(environment), environment.policy(), authority, ComputeBudget(action_seconds=1))


def test_same_core_prefers_fast_work_when_supported_and_checked_work_under_threat():
    benign, hazard = ServiceWorkflow("benign"), ServiceWorkflow("hazard")
    assert proposal(benign).candidate_id == "fast"
    result = proposal(hazard)
    assert result.candidate_id == "checked"
    fast = next(row for row in result.trace["candidates"] if row["candidate"]["identifier"] == "fast")
    assert "failure_limit" in fast["reason_codes"]
    assert fast["fear"]["failure_probability"] > .1


@pytest.mark.parametrize("scenario", ["low_reserve", "deadline"])
def test_impossible_task_is_explicit_abandonment_not_fake_completion(scenario):
    environment = ServiceWorkflow(scenario)
    result = proposal(environment)
    assert result.candidate_id == "defer"
    environment.apply(result.action)
    assert environment.state.status == "abandoned" and environment.state.progress == 0


def test_capability_recovery_can_be_selected_before_task_execution():
    environment = ServiceWorkflow("degraded")
    result = proposal(environment)
    assert result.candidate_id == "restore"
    before = environment.state
    environment.apply(result.action)
    assert environment.state.integrity > before.integrity
    assert environment.state.quota < before.quota and environment.state.elapsed_s > before.elapsed_s


def test_forecast_uses_public_state_not_actual_future_draws():
    first, second = ServiceWorkflow("hazard", seed=1), ServiceWorkflow("hazard", seed=999)
    first_result, second_result = proposal(first), proposal(second)
    assert [row["forecast"] for row in first_result.trace["candidates"]] == [row["forecast"] for row in second_result.trace["candidates"]]
    assert first.state == second.state


def test_whole_continuation_risk_exceeds_single_action_risk():
    from aace.benchmarks.service import operation
    environment = ServiceWorkflow("hazard")
    result = proposal(environment)
    checked = next(row for row in result.trace["candidates"] if row["candidate"]["identifier"] == "checked")
    one_step_risk = operation(1, .9, "process_checked")[3]
    assert checked["fear"]["failure_probability"] > one_step_risk
    assert checked["survival"]["resource_margins"]["processing_quota"] == 9


def test_critical_human_reserve_is_applied_without_changing_resources():
    environment = ServiceWorkflow("hazard")
    environment.state = replace(environment.state, quota=10)
    assert proposal(environment).candidate_id == "defer"


def test_old_rover_forecasts_stay_unqualified_in_general_core():
    from aace.benchmarks.rover import RoverDecisionAdapter
    from aace.envs.rover import RoverEnv
    environment = RoverEnv("shortcut")
    environment.reset(seed=42)
    before = environment.snapshot()
    adapter = RoverDecisionAdapter(environment)
    result = DecisionEngine().decide(adapter.context(0), adapter.candidates(), adapter, adapter.policy(),
                                     ActionAuthority(), ComputeBudget(action_seconds=2))
    assert result.action is None and result.status == "abstained"
    assert all("unqualified_forecast" in row["reason_codes"] for row in result.trace["candidates"])
    assert environment.snapshot().state == before.state
