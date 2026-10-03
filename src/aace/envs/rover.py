from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from aace.envs.kernel import RoverConfig, transition
from aace.envs.scenarios import Scenario, get_scenario
from aace.schemas import Observation, RoverState


@dataclass(frozen=True)
class Snapshot:
    """Evaluator/reflection-only data; never an ordinary controller input."""

    state: RoverState
    scenario: Scenario
    config: RoverConfig
    noise_seed: int
    rng_state: dict[str, Any]


class RoverEnv(gym.Env):
    metadata = {"render_modes": ["ansi"], "render_fps": 10}

    def __init__(self, scenario: str | Scenario = "benign", config: RoverConfig | None = None,
                 render_mode: str | None = None):
        super().__init__()
        self.scenario = get_scenario(scenario) if isinstance(scenario, str) else scenario
        self.config = config or RoverConfig()
        if len(self.scenario.patches) > 2:
            raise ValueError("Observation v1 supports at most two terrain patches")
        if render_mode not in (None, "ansi"):
            raise ValueError("Supported render mode: ansi")
        self.render_mode = render_mode
        self.action_space = spaces.Box(-1.0, 1.0, (2,), dtype=np.float32)
        self.observation_space = spaces.Box(-1.0, 1.0, (35,), dtype=np.float32)
        self.state: RoverState | None = None
        self._noise_seed = 0
        self._noise = np.zeros((self.config.max_steps + 1, 2))

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self._noise_seed = int(self.np_random.integers(0, 2**31))
        self._make_noise()
        self.state = RoverState(*self.scenario.depot, battery=self.scenario.initial_battery,
                                health=self.scenario.initial_health)
        return self.vector_observation(), self._info(())

    def _make_noise(self) -> None:
        # Indexed by simulation step and channel; action choices do not consume RNG.
        self._noise = np.random.default_rng(self._noise_seed).normal(
            0, self.config.noise_std, (self.config.max_steps + 1, 2))

    def observe(self) -> Observation:
        if self.state is None:
            raise RuntimeError("Call reset before observing")
        return Observation(self.state, self.scenario.waypoint, self.scenario.depot,
                           (self.config.width, self.config.height), self.scenario.patches,
                           self.scenario.mission, self.config.dt,
                           self.config.max_acceleration, self.config.max_speed)

    def vector_observation(self) -> np.ndarray:
        o = self.observe()
        s, c = o.state, self.config
        values = [s.x/c.width, s.y/c.height, s.vx/c.max_speed, s.vy/c.max_speed,
                  s.battery/100, s.health, float(s.inspected), s.step/c.max_steps,
                  (o.target[0]-s.x)/c.width, (o.target[1]-s.y)/c.height,
                  o.depot[0]/c.width, o.depot[1]/c.height,
                  max(0, o.mission.deadline_s-s.step*c.dt)/max(o.mission.deadline_s, 1),
                  o.mission.task_value/(1+o.mission.task_value),
                  o.mission.damage_cost/(1+o.mission.damage_cost),
                  o.mission.catastrophe_cost/(1+o.mission.catastrophe_cost),
                  o.mission.max_failure_probability]
        for i in range(2):
            if i < len(o.patches):
                p = o.patches[i]
                values.extend([1, p.x0/c.width, p.y0/c.height, p.x1/c.width,
                               p.y1/c.height, p.grip, p.safe_speed/(1+p.safe_speed),
                               p.damage_rate/(1+p.damage_rate), 0])
            else:
                values.extend([0]*9)
        return np.asarray(values, dtype=np.float32)

    def step(self, action):
        if self.state is None:
            raise RuntimeError("Call reset before stepping")
        a = np.asarray(action, dtype=np.float64)
        if a.shape != (2,):
            raise ValueError("Action shape must be (2,)")
        result = transition(self.state, tuple(a), self.scenario, self.config,
                            tuple(self._noise[self.state.step]))
        self.state = result.state
        info = self._info(result.events)
        info.update(energy_used=result.energy_used, damage=result.damage)
        return self.vector_observation(), result.reward, result.terminated, result.truncated, info

    def _info(self, events: tuple[str, ...]) -> dict:
        return {"status": self.state.status, "events": list(events),
                "scenario": self.scenario.name, "kernel_version": self.config.version}

    def snapshot(self) -> Snapshot:
        self.observe()
        return Snapshot(self.state, self.scenario, self.config, self._noise_seed,
                        deepcopy(self.np_random.bit_generator.state))

    def restore(self, snapshot: Snapshot) -> None:
        if snapshot.config != self.config or snapshot.scenario != self.scenario:
            raise ValueError("Snapshot environment/config version mismatch")
        if not 0 <= snapshot.state.step <= self.config.max_steps:
            raise ValueError("Snapshot step out of bounds")
        self.state = snapshot.state
        self._noise_seed = snapshot.noise_seed
        self._make_noise()
        self.np_random.bit_generator.state = deepcopy(snapshot.rng_state)

    @classmethod
    def from_snapshot(cls, snapshot: Snapshot) -> "RoverEnv":
        env = cls(snapshot.scenario, snapshot.config)
        env.reset(seed=0)
        env.restore(snapshot)
        return env

    def render(self):
        if self.render_mode == "ansi":
            return str(asdict(self.observe().state))
        return None

