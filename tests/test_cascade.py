from dataclasses import asdict, replace

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
    state = ReleaseState()
    for _ in range(2):
        state = transition(transition(state, "fast", shock=True), "repair")
    planner = ReleasePlanner("oracle", 140, oracle_danger=HIGH)
    forecasts = planner.alternatives(state)
    assert tuple(forecasts) == ("stop", "fast")
    risky = forecasts["fast"]
    assert risky.completed == pytest.approx(.62)
    assert risky.release_failure == pytest.approx(.38)
    assert risky.reward == pytest.approx(.62 * 42)
    assert risky.cost == pytest.approx(21.5 + .38 * 34)
    assert planner.decide(state)[0] == "fast"
    assert ReleasePlanner("oracle", 24, oracle_danger=HIGH).decide(state)[0] == "stop"


def test_adaptive_forecast_matches_fixed_regime_policy_enumeration():
    planner = ReleasePlanner("adaptive", 140, 2)

    def evaluate(state, actual_danger):
        if state.status != "running":
            return terminal_outcomes(state, 140).score
        action, _ = planner.decide(state)
        normal = evaluate(transition(state, action), actual_danger)
        if action != "fast":
            return normal
        harmed = evaluate(transition(state, action, shock=True), actual_danger)
        return (1-actual_danger)*normal + actual_danger*harmed

    initial = ReleaseState()
    expected = (1-belief(2, 8))*evaluate(initial, LOW) + belief(2, 8)*evaluate(initial, HIGH)
    assert planner.decide(initial)[1].score == pytest.approx(expected)


def test_trace_matches_applied_transitions_and_records_rejected_choices():
    from aace.benchmarks.cascade_pilot import play

    row = play(ReleasePlanner("adaptive", 140, 2), LOW, [0., .99, .99], trace=True)
    for decision in row["decisions"]:
        state = ReleaseState(**decision["before"])
        action = decision["selected"]
        assert set(decision["alternatives"]) == set(available(state))
        assert action == max(decision["alternatives"], key=lambda a: decision["alternatives"][a]["expected"]["score"])
        after = transition(state, action, shock=bool(decision["observed_shock"]))
        assert decision["observed_after"] == asdict(after)
    assert row["decisions"][0]["observed_shock"] is True
    assert row["realized"]["shocks"] == 1


def test_smoke_is_paired_and_reproducible(tmp_path):
    import hashlib
    import json
    from pathlib import Path
    from aace.benchmarks.cascade_pilot import run_cascade

    report = run_cascade(tmp_path, smoke=True)
    assert report["subjects"] == 8 and report["episodes"] == 80
    assert report["seed_range_inclusive"] == [91000, 91007]
    assert report["decision_ready"] is False
    episodes = (Path(report["directory"])/"episodes.json").read_bytes()
    assert hashlib.sha256(episodes).hexdigest() == report["episode_sha256"]
    rows = json.loads(episodes)
    paired = [r for r in rows if r["seed"] == 91000]
    assert len(paired) == 10
    assert len({tuple(r["history_observations"]) for r in paired}) == 1
    assert len({r["audit_actual_danger"] for r in paired}) == 1
    assert run_cascade(tmp_path, smoke=True)["episode_sha256"] == report["episode_sha256"]
