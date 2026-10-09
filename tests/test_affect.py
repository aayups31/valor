import pytest

from aace.decision.affect import AffectiveObserver, SurvivalObservation as O


def test_harm_history_persists_after_identical_body_recovery():
    experienced, fresh = AffectiveObserver(), AffectiveObserver()
    experienced.observe(O(1, 1, 0, "load"))
    hurt = experienced.observe(O(.6, 1, 1, "load"))
    recovered = experienced.observe(O(1, 1, 10, "load"))
    untouched = fresh.observe(O(1, 1, 10, "load"))
    assert hurt["observed_harm"] == pytest.approx(.4)
    assert recovered["observation"] == untouched["observation"]
    assert recovered["arousal"] > untouched["arousal"]
    assert recovered["current_cue_activation"] > 0
    assert recovered["decision_influence"].startswith("observer only")


def test_only_observed_safe_cue_extinguishes_and_novel_cue_is_not_danger():
    observer = AffectiveObserver()
    observer.observe(O(1, 1, 0, "load"))
    hurt = observer.observe(O(.8, 1, 1, "load"))
    novel = observer.observe(O(.8, 1, 2, "new"))
    assert novel["current_cue_activation"] == 0
    assert novel["cue_associations"]["load"] == hurt["cue_associations"]["load"]
    observer.observe(O(.8, 1, 3, "load", safe_exposure=True))
    safe = observer.observe(O(.8, 1, 4, "load", safe_exposure=True))
    assert 0 < safe["current_cue_activation"] < hurt["current_cue_activation"]


def test_time_validation_does_not_mutate_state_and_memory_is_bounded():
    observer = AffectiveObserver()
    observer.observe(O(1, 1, 2, "start"))
    with pytest.raises(ValueError):
        observer.observe(O(0, 0, 1, "invalid"))
    assert observer.previous.integrity == 1
    assert "invalid" not in observer.associations
    for i in range(40):
        row = observer.observe(O(1, .5, i+3, f"cue-{i}"))
    assert len(row["cue_associations"]) == 32
    assert 0 <= row["arousal"] <= 1


@pytest.mark.parametrize("values", [(float("nan"),1,0,"a"),(1,2,0,"a"),(1,1,-1,"a"),(1,1,0,"")])
def test_invalid_observations(values):
    with pytest.raises(ValueError):
        O(*values)
