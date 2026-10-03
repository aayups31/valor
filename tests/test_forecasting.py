import json
from dataclasses import replace

import pytest

from aace.envs.rover import RoverEnv
from aace.forecasting import OraclePlanner, PlanningBudget, wilson_interval
from aace.runtime import Session


def test_budget_rejects_oversized_search():
    with pytest.raises(ValueError):
        PlanningBudget(horizon_steps=100, particles=5, max_branch_transitions=100)


def test_zero_failures_are_not_displayed_as_zero_uncertainty():
    low, high = wilson_interval(0, 3)
    assert low == pytest.approx(0, abs=1e-15) and high > 0.5


def test_oracle_forecast_rejects_shortcut_and_accounts_for_work():
    env = RoverEnv("shortcut")
    env.reset(seed=42)
    before = env.snapshot()
    planner = OraclePlanner(env.config, seed=42)
    proposal = planner.decide(env.observe())
    assert proposal.plan in ("detour_north", "detour_south")
    direct = next(c for c in proposal.candidates if c["plan"] == "direct")
    assert direct["status"] == "constraint_rejected"
    assert direct["forecast"]["failure_frequency"] == 1
    assert proposal.branch_transitions <= planner.budget.max_branch_transitions
    assert proposal.branch_transitions == sum(c["forecast"]["branch_transitions"] for c in proposal.candidates)
    assert env.snapshot().state == before.state
    assert proposal.forecast_source == "oracle_dynamics"
    json.dumps(proposal.candidates, allow_nan=False)


def test_forecast_does_not_depend_on_actual_future_noise():
    first, second = RoverEnv("shortcut"), RoverEnv("shortcut")
    first.reset(seed=1)
    second.reset(seed=999)
    assert first.observe() == second.observe()
    planner = OraclePlanner(first.config, seed=11)
    assert planner.decide(first.observe()) == planner.decide(second.observe())


def test_records_contain_real_forecast_paths_and_selection():
    record = Session("shortcut", "oracle_planner", 42).step()
    assert record["forecast_source"] == "oracle_dynamics"
    assert record["branch_transitions"] > 0
    assert all(len(c["forecast"]["sample_path"]) > 1 for c in record["candidates"])


def test_infeasible_risk_rule_is_explicit_fallback():
    env = RoverEnv("shortcut")
    env.reset(seed=4)
    observation = replace(env.observe(), state=replace(env.state, battery=0.001))
    proposal = OraclePlanner(env.config).decide(observation)
    selected = next(c for c in proposal.candidates if c["plan"] == proposal.plan)
    assert proposal.plan == "brake" and selected["status"] == "selected_fallback"
    assert selected["reason_codes"] == ["no_admissible_plan"]
