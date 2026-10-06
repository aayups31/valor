"""Training-only reset distribution. Evaluation always uses the original mission."""

import gymnasium as gym

from aace.schemas import RoverState


class ReturnCurriculum(gym.Wrapper):
    """Half complete missions, half inspected return journeys on open ground.

    Physics, rewards, observations and action limits are unchanged. The reset
    assistance and its seed are recorded, and must be shared in fair comparisons.
    """

    def __init__(self, env):
        if env.unwrapped.scenario.name != "benign":
            raise ValueError("Return curriculum currently supports only benign terrain")
        super().__init__(env)

    def reset(self, *, seed=None, options=None):
        observation, info = self.env.reset(seed=seed, options=options)
        base = self.env.unwrapped
        phase = "full_mission"
        if base.np_random.random() < 0.5:
            phase = "return_start"
            base.state = RoverState(
                x=float(base.np_random.uniform(2.0, 8.5)),
                y=float(base.np_random.uniform(3.5, 6.5)),
                vx=float(base.np_random.uniform(-0.3, 0.3)),
                vy=float(base.np_random.uniform(-0.3, 0.3)),
                battery=base.scenario.initial_battery,
                health=base.scenario.initial_health, inspected=True,
            )
            observation = base.vector_observation()
        return observation, dict(info, training_reset_phase=phase,
                                 training_reset_distribution="mixed-return-v1")
