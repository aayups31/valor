from dataclasses import replace

import numpy as np
import pytest

from aace.benchmarks.cascade import ReleaseState, transition
from aace.benchmarks.repeated import CLEAR
from aace.benchmarks.shared_reserve import (
    GUARDED, PairPlanner, choose_policy, next_task, play_pair, subject, task_score,
)


def test_reserve_and_vulnerability_carry_but_cost_is_not_double_counted():
    start = ReleaseState(resources=7)
    hurt = transition(start, "fast", shock=True)
    stopped = transition(hurt, "stop")
    continued = next_task(stopped)
    assert continued == ReleaseState(resources=6, integrity=2, faults=1)
    assert task_score(stopped, 24, 7) == -9.5
    assert task_score(transition(continued, "stop"), 24, 6) == 0


def test_only_lookahead_responds_to_future_stakes():
    start = ReleaseState(resources=7)
    def action(actor, future_stakes):
        planner = PairPlanner(actor, (24, future_stakes))
        return planner.solve(start, planner.initial((CLEAR,)*3), 0, 7)[0]
    assert action("myopic_markov", 24) == action("myopic_markov", 140)
    assert action("horizon_markov", 24) == "careful"
    assert action("horizon_markov", 140) == "stop"


def test_last_tick_forecast_matches_hand_calculation():
    state = replace(ReleaseState(resources=1), stage=2, elapsed=6)
    planner = PairPlanner("horizon_fixed", (140, 140))
    _, score, failures, completed = planner.solve(state, None, 0, 1)
    assert completed == pytest.approx(.77)
    assert failures == pytest.approx(.23)
    assert score == pytest.approx(.77*42-.23*34-.5)


def test_guard_checks_completion_and_failure_independently():
    baseline = (10, .02, 2)
    assert choose_policy((11, .04, 1.96), baseline)
    assert not choose_policy((100, .041, 2), baseline)
    assert not choose_policy((100, .01, 1.95), baseline)
    assert not choose_policy((10, .02, 2), baseline)


def test_guard_fallback_runs_unchanged_policy_and_predicts_entire_pair():
    row = play_pair(117000, "nominal", GUARDED, {}, trace=True)
    base = play_pair(117000, "nominal", "myopic_markov", {}, trace=True)
    assert row["executed_policy"] == "myopic_markov"
    assert row["decisions"] == base["decisions"]
    assert row["initial_expected_pair_score"] == row["forecast_screen"]["myopic"][0]
    assert row["new_search_nodes"] > base["new_search_nodes"]


def test_shifts_preserve_public_reserve_stakes_and_random_tape():
    nominal = subject(117002, "nominal")
    for name in ("volatile", "harsher", "damaged"):
        shifted = subject(117002, name)
        assert shifted[0].resources == nominal[0].resources
        assert shifted[1] == nominal[1]
        np.testing.assert_array_equal(shifted[-1], nominal[-1])
    assert subject(117002, "damaged")[0].faults == 1
