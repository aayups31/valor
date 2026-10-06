import numpy as np
import pytest

from aace.envs.rover import RoverEnv
from aace.learning.curriculum import ReturnCurriculum


def test_curriculum_is_reproducible_with_both_phases_and_correct_home_goal():
    first, second = ReturnCurriculum(RoverEnv()), ReturnCurriculum(RoverEnv())
    phases = set()
    for seed in range(24):
        a, info = first.reset(seed=seed)
        b, other = second.reset(seed=seed)
        np.testing.assert_array_equal(a, b)
        assert info == other
        phases.add(info["training_reset_phase"])
        if info["training_reset_phase"] == "return_start":
            o = first.unwrapped.observe()
            assert o.state.inspected and o.target == o.depot
            assert 2 <= o.state.x <= 8.5 and o.state.step == 0
    assert phases == {"full_mission", "return_start"}


def test_standard_evaluation_reset_remains_the_complete_mission():
    env = RoverEnv()
    for seed in range(24):
        env.reset(seed=seed)
        assert not env.state.inspected and (env.state.x, env.state.y) == env.scenario.depot


def test_curriculum_does_not_change_transition_or_noise():
    curriculum = ReturnCurriculum(RoverEnv())
    curriculum.reset(seed=2)
    clone = RoverEnv.from_snapshot(curriculum.unwrapped.snapshot())
    for _ in range(10):
        first, second = curriculum.step((0.2, -0.1)), clone.step((0.2, -0.1))
        np.testing.assert_array_equal(first[0], second[0])
        assert first[1:] == second[1:]


def test_dangerous_curriculum_is_not_implicitly_supported():
    with pytest.raises(ValueError, match="benign"):
        ReturnCurriculum(RoverEnv("shortcut"))
