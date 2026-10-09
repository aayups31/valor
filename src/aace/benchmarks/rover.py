"""Rover-to-core adapter. Coarse oracle samples remain unqualified evidence."""

import numpy as np

from aace.controllers import PLAN_NAMES, action_for_plan
from aace.decision import (ActionIntent, Candidate, ConsequenceForecast, DecisionContext,
                           DecisionPolicy, ForecastEvidence)
from aace.forecasting import OraclePlanner

DOMAIN = "rover-public-v1"


class RoverDecisionAdapter:
    def __init__(self, environment, *, seed=42):
        self.observation = environment.observe()
        self.planner = OraclePlanner(environment.config, seed=seed)
        self.config = environment.config
        self.seed = seed

    def context(self, generation):
        from math import hypot
        observation, state = self.observation, self.observation.state
        distance = hypot(observation.target[0]-state.x, observation.target[1]-state.y)
        if not state.inspected:
            distance += hypot(observation.waypoint[0]-observation.depot[0], observation.waypoint[1]-observation.depot[1])
        return DecisionContext(DOMAIN, f"rover-{generation}-{state.step}", generation,
            (("energy", state.battery),), state.health,
            max(0, observation.mission.deadline_s-state.step*self.config.dt), distance/self.config.max_speed)

    def policy(self):
        policy = self.observation.mission
        return DecisionPolicy(task_value=policy.task_value, recoverable_damage_cost=policy.damage_cost,
                              failure_cost=policy.catastrophe_cost, max_failure_probability=policy.max_failure_probability)

    def candidates(self):
        horizon = self.planner.budget.horizon_steps*self.config.dt
        return tuple(Candidate(plan, ActionIntent("acceleration", action_for_plan(self.observation, plan)),
            plan, horizon, role="recovery" if plan == "return" else "preserve" if plan in ("brake", "coast") else "task") for plan in PLAN_NAMES)

    def forecast(self, context, candidate, *, deadline):
        rng = np.random.default_rng(np.random.SeedSequence([self.seed, self.observation.state.step, 901]))
        budget = self.planner.budget
        noise = rng.normal(0, self.config.noise_std, (budget.particles, budget.horizon_steps, 2))
        forecast = self.planner.forecast(self.observation, candidate.identifier, noise)
        endpoint = forecast["sample_path"][-1]
        depot = self.observation.depot
        return_estimate = float(np.linalg.norm(np.array(endpoint)-depot)*.8/max(forecast["mean_health"], .15))
        return ConsequenceForecast(context.observation_id, context.generation, candidate.identifier,
            candidate.continuation, forecast["horizon_s"], forecast["completion_frequency"],
            forecast["failure_frequency"], forecast["sampling_interval_95"][1], None,
            (("energy", max(0, self.observation.state.battery-forecast["mean_battery"])),),
            (("energy", return_estimate),), forecast["horizon_s"], forecast["mean_health"],
            ForecastEvidence("experimental", "oracle-samples-3-v1", DOMAIN,
                             "coarse sampling interval and approximate return reserve; not qualified for core decisions"))
