from dataclasses import replace

import pytest

from aace.benchmarks.cascade import (
    HIGH, LOW, ReleasePlanner, ReleaseState, available, belief, terminal_outcomes, transition,
)


def test_damage_persists_and_spreads_in_later_work():
    hurt = transition(ReleaseState(), "fast", shock=True)
    assert (hurt.stage, hurt.integrity, hurt.faults) == (1, 2, 1)
    spread = transition(hurt, "fast")
    assert (spread.stage, spread.integrity, spread.faults, spread.incidents) == (2, 2, 1, 1)
    assert transition(spread, "careful").status == "release_failure"
    assert transition(hurt, "careful").incidents == 0


def test_recovery_restores_options_without_erasing_costs():
    hurt = transition(ReleaseState(), "fast", shock=True)
    repaired = transition(hurt, "repair")
    assert (repaired.integrity, repaired.faults, repaired.elapsed, repaired.resources) == (3, 0, 3, 7)
    finished = transition(transition(repaired, "careful"), "careful")
    assert finished.status == "completed"
    assert terminal_outcomes(finished, 24).cost == 11.5


def test_outage_takes_priority_and_terminates():
    state = ReleaseState()
    for _ in range(3):
        state = transition(state, "fast", shock=True)
    assert state.status == "outage" and state.incidents == 2
    assert not available(state)
    assert terminal_outcomes(state, 140).release_failure == 0
    with pytest.raises(ValueError):
        transition(state, "stop")


def test_action_bounds_and_stop():
    state = replace(ReleaseState(), elapsed=6, resources=1)
    assert available(state) == ("stop", "fast")
    assert available(transition(state, "fast")) == ("stop",)
    with pytest.raises(ValueError):
        transition(state, "careful")
    with pytest.raises(ValueError):
        transition(ReleaseState(), "careful", shock=True)


def test_live_evidence_changes_belief_only_for_adaptive_actor():
    after_shock = transition(ReleaseState(), "fast", shock=True)
    after_safe = transition(ReleaseState(), "fast")
    adaptive = ReleasePlanner("adaptive", 24, 2)
    history = ReleasePlanner("history", 24, 2)
    assert adaptive.danger(after_safe) < adaptive.danger(ReleaseState()) < adaptive.danger(after_shock)
    assert history.danger(after_shock) == history.danger(after_safe) == adaptive.danger(ReleaseState())
    assert belief(0, 8) < belief(2, 8)
    with pytest.raises(ValueError):
        ReleasePlanner("adaptive", 24, oracle_danger=LOW)


def test_same_hazard_and_legal_actions_different_stakes():
    state = ReleaseState()
    ordinary = ReleasePlanner("adaptive", 24, 2)
    urgent = ReleasePlanner("adaptive", 140, 2)
    assert ordinary.danger(state) == urgent.danger(state)
    assert ordinary.alternatives(state).keys() == urgent.alternatives(state).keys()
    assert ordinary.decide(state)[0] == "careful"
    assert urgent.decide(state)[0] == "fast"
    assert ordinary.decide(state)[1].shocks == 0
    assert urgent.decide(state)[1].shocks > 0


def test_exact_last_action_matches_hand_calculation():
    state = replace(ReleaseState(), stage=2, elapsed=6, resources=8)
    planner = ReleasePlanner("oracle", 140, oracle_danger=HIGH)
    forecasts = planner.alternatives(state)
    assert tuple(forecasts) == ("stop", "fast")
    risky = forecasts["fast"]
    assert risky.completed == pytest.approx(.62)
    assert risky.release_failure == pytest.approx(.38)
    assert risky.reward == pytest.approx(.62 * 42)
    assert risky.cost == pytest.approx(1.5 + .38 * 34)
    assert planner.decide(state)[0] == "fast"
    assert ReleasePlanner("oracle", 24, oracle_danger=HIGH).decide(state)[0] == "stop"
