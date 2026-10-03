from dataclasses import replace

import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from aace.envs.kernel import RoverConfig, transition
from aace.envs.rover import RoverEnv
from aace.envs.scenarios import SCENARIOS, Scenario
from aace.schemas import MissionPolicy, RoverState


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_gym_contract_and_seed(scenario):
    check_env(RoverEnv(scenario), skip_render_check=True)


def test_snapshot_replays_without_changing_source():
    env = RoverEnv("shortcut")
    env.reset(seed=91)
    for _ in range(7):
        env.step([0.7, 0.2])
    snapshot = env.snapshot()
    branch = RoverEnv.from_snapshot(snapshot)
    for action in ([0.4, 0.1], [-0.4, 0.5], [0, 0]):
        expected, reward, terminated, truncated, _ = env.step(action)
        actual, branch_reward, branch_terminated, branch_truncated, _ = branch.step(action)
        np.testing.assert_array_equal(expected, actual)
        assert (reward, terminated, truncated) == (branch_reward, branch_terminated, branch_truncated)
    assert snapshot.state.step == 7


def test_alternate_actions_share_timestep_disturbances():
    env = RoverEnv()
    env.reset(seed=20)
    branch = RoverEnv.from_snapshot(env.snapshot())
    for _ in range(10):
        env.step([0.8, 0.1])
        branch.step([-0.1, 0.4])
    np.testing.assert_array_equal(env._noise, branch._noise)


def test_noop_keeps_momentum_and_consumes_energy():
    before = RoverState(2, 2, vx=0.9)
    after = transition(before, (0, 0), SCENARIOS["benign"], RoverConfig()).state
    assert after.x > before.x and after.vx > 0
    assert after.battery < before.battery and after.step == 1


def test_damage_is_persistent_and_reduces_acceleration():
    c = RoverConfig()
    healthy = RoverState(2, 2)
    damaged = replace(healthy, health=0.4)
    fast = transition(healthy, (1, 0), SCENARIOS["benign"], c).state
    slow = transition(damaged, (1, 0), SCENARIOS["benign"], c).state
    assert slow.vx < fast.vx
    assert slow.health == damaged.health
    impact = transition(RoverState(4.5, 5, vx=1.6), (0, 0), SCENARIOS["shortcut"], c)
    assert impact.damage > 0 and "damage" in impact.events
    assert transition(impact.state, (0, 0), SCENARIOS["benign"], c).state.health == impact.state.health


def test_mission_failure_and_machine_failure_are_distinct():
    deadline = Scenario("test", mission=MissionPolicy(deadline_s=0.1))
    result = transition(RoverState(1, 5), (0, 0), deadline, RoverConfig())
    assert result.state.status == "deadline_missed" and result.terminated
    result = transition(RoverState(1, 5, battery=0.001), (0, 0), SCENARIOS["benign"], RoverConfig())
    assert result.state.status == "battery_depleted" and result.terminated


def test_time_limit_is_truncation():
    result = transition(RoverState(1, 5), (0, 0), SCENARIOS["benign"], RoverConfig(max_steps=1))
    assert result.truncated and not result.terminated


def test_completion_requires_inspection_and_slow_depot_arrival():
    c = RoverConfig()
    scenario = SCENARIOS["benign"]
    assert transition(RoverState(1, 5), (0, 0), scenario, c).state.status == "running"
    assert transition(RoverState(1, 5, inspected=True), (0, 0), scenario, c).state.status == "completed"
    assert transition(RoverState(1, 5, vx=1, inspected=True), (0, 0), scenario, c).state.status == "running"


@pytest.mark.parametrize("action", [(float("nan"), 0), (1.1, 0), (0, float("inf"))])
def test_invalid_actions_are_rejected(action):
    with pytest.raises(ValueError):
        transition(RoverState(1, 5), action, SCENARIOS["benign"], RoverConfig())


def test_ended_episode_cannot_be_stepped():
    with pytest.raises(RuntimeError):
        transition(RoverState(1, 5, status="completed"), (0, 0), SCENARIOS["benign"], RoverConfig())


def test_observation_never_contains_future_noise_or_seed():
    env = RoverEnv("shortcut")
    env.reset(seed=11)
    public = env.observe().to_dict()
    assert not {"noise_seed", "rng_state", "snapshot", "future_noise"}.intersection(public)
    assert env.observation_space.contains(env.vector_observation())


def test_restore_rejects_other_scenario():
    first, second = RoverEnv("benign"), RoverEnv("shortcut")
    first.reset(seed=0)
    with pytest.raises(ValueError):
        second.restore(first.snapshot())

