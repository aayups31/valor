from dataclasses import replace

import numpy as np
import pytest

from aace.benchmarks.cascade import HIGH, ReleaseState, transition
from aace.benchmarks.incident_memory import Bank, Record, audit_action, build_bank
from aace.benchmarks.repeated import BOUNDARY, SHOCK, Markov, Search, campaign, carry, play


def test_carry_preserves_damage_and_faults_but_resets_allowance():
    damaged = transition(ReleaseState(), "fast", shock=True)
    stopped = transition(damaged, "stop")
    assert carry(stopped) == ReleaseState(integrity=2, faults=1)
    assert carry(replace(stopped, status="outage", integrity=0)) is None
    with pytest.raises(ValueError):
        carry(damaged)


def test_public_filter_tracks_both_shock_and_time():
    model = Markov(.2)
    hurt = model.update(model.initial, SHOCK)
    assert hurt > model.initial
    assert model.initial < model.update(hurt, BOUNDARY) < hurt


def test_endpoint_audit_does_not_change_the_public_search_policy():
    search = Search(Markov(.2), 140)
    state = replace(ReleaseState(), stage=2, elapsed=6)
    outcome, nodes = audit_action(search, state, .5, "fast", HIGH)
    assert outcome.completed == pytest.approx(.62)
    assert outcome.release_failure == pytest.approx(.38)
    assert search.predictor.probability(.5) == pytest.approx(.23)
    assert nodes == 3


def test_recall_needs_exact_scope_and_robust_recourses():
    bank = Bank()
    state = ReleaseState()
    record = Record(120000, 0, state, 24, "fast", transition(state, "fast", shock=True),
                    "release_failure", -10., "careful", ((1., 0.), (2., -.1)), 20, .2, .5)
    bank.put(record)
    assert bank.recall(state, 24, "verified", model_switch=.2) == "careful"
    assert bank.recall(state, 24, "factual", model_switch=.2) is None
    assert bank.recall(state, 140, "verified", model_switch=.2) is None
    assert bank.recall(state, 24, "verified", model_switch=.1) is None
    with pytest.raises(ValueError):
        bank.put(replace(record, endpoint_deltas=((4., 0.), (3., .01))))


def test_shortlisted_recall_is_reevaluated_and_never_applied_directly():
    bank, work = build_bank(range(120010, 120014), Markov(.2))
    assert work["endpoint_nodes"] > 0 and len(bank.records()) <= 256
    row = play(120014, Markov(.2), bank=bank, retrieval="verified", trace=True)
    assert row["recall_hits"] > 0
    for decision in row["decisions"]:
        scores = decision["evaluated"]
        assert "stop" in scores and len(scores) <= 3
        assert scores[decision["selected"]]["score"] == max(s["score"] for s in scores.values())
        assert decision["recalled_candidate"] is None or decision["recalled_candidate"] in scores
    other = campaign(120014)
    np.testing.assert_array_equal(other[2], campaign(120014)[2])
