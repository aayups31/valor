"""Simulator-backed upper-bound controller; no learned-model claim."""

from dataclasses import dataclass, replace
from math import hypot, sqrt

import numpy as np

from aace.controllers import PLAN_NAMES, Proposal, action_for_plan
from aace.envs.kernel import RoverConfig, transition
from aace.envs.scenarios import Scenario
from aace.schemas import Observation


@dataclass(frozen=True)
class PlanningBudget:
    horizon_steps: int = 80
    particles: int = 3
    max_branch_transitions: int = 1440

    def __post_init__(self):
        if min(self.horizon_steps, self.particles, self.max_branch_transitions) <= 0:
            raise ValueError("Planning limits must be positive")
        required = len(PLAN_NAMES)*self.horizon_steps*self.particles
        if required > self.max_branch_transitions:
            raise ValueError("Candidate support exceeds declared branch budget")


def wilson_interval(count: int, total: int) -> tuple[float, float]:
    """Sampling interval only; does not cover model error or unseen mechanisms."""
    z = 1.959963984540054
    p = count/total
    denominator = 1+z*z/total
    center = (p+z*z/(2*total))/denominator
    half = z*sqrt(p*(1-p)/total+z*z/(4*total*total))/denominator
    return max(0.0, center-half), min(1.0, center+half)


class OraclePlanner:
    name = "oracle_planner"

    def __init__(self, config: RoverConfig, seed: int = 0, budget: PlanningBudget | None = None):
        self.config = config
        self.seed = seed
        self.budget = budget or PlanningBudget()

    def decide(self, observation: Observation) -> Proposal:
        # Independently sampled future noise, shared across candidates. This is
        # not the environment's actual future disturbance sequence.
        rng = np.random.default_rng(np.random.SeedSequence([self.seed, observation.state.step, 901]))
        noise = rng.normal(0, self.config.noise_std,
                           (self.budget.particles, self.budget.horizon_steps, 2))
        records = []
        branch_transitions = 0
        for plan in PLAN_NAMES:
            forecast = self.forecast(observation, plan, noise)
            branch_transitions += forecast["branch_transitions"]
            admissible = forecast["failure_frequency"] <= observation.mission.max_failure_probability
            records.append({"plan": plan, "action": action_for_plan(observation, plan),
                            "status": "lower_score" if admissible else "constraint_rejected",
                            "reason_codes": ["lower_score" if admissible else "failure_limit"],
                            "forecast": forecast})
        admissible = [record for record in records if record["status"] != "constraint_rejected"]
        best = max(admissible, key=lambda item: item["forecast"]["score"]) if admissible else next(
            item for item in records if item["plan"] == "brake")
        best["status"] = "selected" if admissible else "selected_fallback"
        best["reason_codes"] = ["best_admissible_score" if admissible else "no_admissible_plan"]
        return Proposal(best["plan"], best["action"], tuple(records), "oracle_dynamics", branch_transitions)

    def forecast(self, observation: Observation, plan: str, noise: np.ndarray) -> dict:
        scenario = Scenario("forecast_from_public_packet", observation.depot, observation.waypoint,
                            observation.patches, mission=observation.mission)
        scores, healths, batteries, completions = [], [], [], []
        failures, work = 0, 0
        sample_path = [[observation.state.x, observation.state.y]]
        for particle in range(self.budget.particles):
            state = observation.state
            reward = 0.0
            for step in range(self.budget.horizon_steps):
                action = action_for_plan(replace(observation, state=state), plan)
                outcome = transition(state, action, scenario, self.config, tuple(noise[particle, step]))
                state = outcome.state
                reward += outcome.reward
                work += 1
                if particle == 0 and (step % 8 == 0 or outcome.terminated or outcome.truncated):
                    sample_path.append([state.x, state.y])
                if outcome.terminated or outcome.truncated:
                    break
            if particle == 0 and sample_path[-1] != [state.x, state.y]:
                sample_path.append([state.x, state.y])
            target = observation.depot if state.inspected else observation.waypoint
            # Declared terminal approximation; not a probability or certified reserve.
            distance = hypot(state.x-target[0], state.y-target[1])
            return_distance = hypot(state.x-observation.depot[0], state.y-observation.depot[1])
            reserve_estimate = return_distance*0.8/max(state.health, 0.15)
            terminal = 0.0 if state.status != "running" else (
                5.0*state.inspected-0.8*distance-2.0*max(0.0, reserve_estimate-state.battery))
            scores.append(reward+terminal)
            healths.append(state.health)
            batteries.append(state.battery)
            completions.append(state.status == "completed")
            failures += state.status in ("actuator_loss", "battery_depleted")
        interval = wilson_interval(failures, self.budget.particles)
        return {"source": "oracle_dynamics", "horizon_steps": self.budget.horizon_steps,
                "horizon_s": self.budget.horizon_steps*self.config.dt,
                "continuation": plan, "particles": self.budget.particles,
                "branch_transitions": work, "score": float(np.mean(scores)),
                "score_std": float(np.std(scores)), "failure_frequency": failures/self.budget.particles,
                "failure_count": failures, "sampling_interval_95": interval,
                "risk_estimate_kind": "uncalibrated_sample_frequency",
                "mean_health": float(np.mean(healths)), "mean_battery": float(np.mean(batteries)),
                "completion_frequency": float(np.mean(completions)), "sample_path": sample_path,
                "terminal_approximation": "distance_and_return_reserve_v1",
                "model_version": self.config.version,
                "warning": "Oracle dynamics; finite horizon/samples; uncertainty interval excludes model error"}

