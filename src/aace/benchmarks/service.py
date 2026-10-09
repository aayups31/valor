"""A non-robotic service-workflow sandbox. No actual services are controlled."""

from dataclasses import asdict, dataclass, replace
from math import ceil

import numpy as np

from aace.decision import (ActionIntent, Candidate, ConsequenceForecast, DecisionContext,
                           DecisionPolicy, ForecastEvidence)

DOMAIN = "service-workflow-v1"


@dataclass(frozen=True)
class ServiceState:
    quota: float = 20
    integrity: float = 1
    progress: int = 0
    elapsed_s: float = 0
    status: str = "running"


SCENARIOS = {
    "benign": {"load": .1},
    "hazard": {"load": .9},
    "low_reserve": {"load": .9, "quota": 9},
    "deadline": {"load": .9, "deadline_s": 5},
    "degraded": {"load": .9, "integrity": .2},
}


def operation(integrity, load, name):
    if name == "process_fast":
        return 3, 1.0, 2.0, .004+.12*load**2+.06*(1-integrity), .012*load
    if name == "process_checked":
        return 1, 2.0, 1.0, .001+.008*load**2+.005*(1-integrity), .002*load
    if name == "restore":
        return 0, 3.0, 2.0, 0.0, 0.0
    if name == "defer":
        return 0, 0.0, 0.0, 0.0, 0.0
    raise ValueError("Unknown simulated service operation")


class ServiceWorkflow:
    """Finite task, limited processing quota and persistent service integrity.

    Stochastic irreversible outage and deterministic wear are intentionally
    simple known dynamics. The analytic forecaster is benchmark-specific.
    """

    def __init__(self, scenario="hazard", *, seed=42):
        if scenario not in SCENARIOS or type(seed) is not int or not 0 <= seed < 2**31:
            raise ValueError("Invalid service benchmark scenario/seed")
        settings = SCENARIOS[scenario]
        self.scenario = scenario
        self.state = ServiceState(quota=settings.get("quota", 20), integrity=settings.get("integrity", 1))
        self.load = settings["load"]
        self.deadline_s = settings.get("deadline_s", 30)
        self.goal = 8
        self._rng = np.random.default_rng(seed)

    def context(self, generation):
        left = max(0, self.goal-self.state.progress)
        return DecisionContext(DOMAIN, f"service-{generation}", generation,
            (("processing_quota", self.state.quota),), self.state.integrity,
            max(0, self.deadline_s-self.state.elapsed_s), float(ceil(left/3)))

    def candidates(self):
        left = max(0, self.goal-self.state.progress)
        checked, fast = max(1, left*2), max(1, ceil(left/3))
        return (Candidate("checked", ActionIntent("process_checked"), "checked_until_done", checked, time_hint_s=checked),
                Candidate("fast", ActionIntent("process_fast"), "fast_until_done", fast, time_hint_s=fast),
                Candidate("restore", ActionIntent("restore"), "restore_then_checked", checked+3, role="recovery", time_hint_s=checked+3),
                Candidate("defer", ActionIntent("defer"), "stop_this_task", 1, role="preserve"))

    def policy(self):
        return DecisionPolicy(resource_reserves=(("processing_quota", 3),))

    def apply(self, action):
        if self.state.status != "running" or action.values:
            raise ValueError("Service task ended or unsupported action parameters")
        state = self.state
        progress, duration, cost, probability, damage = operation(state.integrity, self.load, action.name)
        if action.name == "defer":
            self.state = replace(state, status="abandoned")
            return
        quota = max(0, state.quota-cost)
        elapsed = state.elapsed_s+duration
        if elapsed > self.deadline_s or cost > state.quota:
            self.state = replace(state, quota=quota, elapsed_s=elapsed,
                                 status="deadline_missed" if elapsed > self.deadline_s else "quota_depleted")
            return
        if self._rng.random() < probability:
            self.state = replace(state, quota=quota, integrity=0, elapsed_s=elapsed, status="irreversible_outage")
            return
        integrity = min(1, state.integrity+.3) if action.name == "restore" else max(0, state.integrity-damage)
        progress = min(self.goal, state.progress+progress)
        self.state = ServiceState(quota, integrity, progress, elapsed,
                                  "completed" if progress >= self.goal else "running")


class ServiceForecaster:
    """Full-continuation analytic benchmark oracle, never a learned-fear claim."""

    def __init__(self, environment):
        # Copy public state/config only, never RNG or hidden future draws.
        self.state = environment.state
        self.load, self.goal, self.deadline_s = environment.load, environment.goal, environment.deadline_s
        self.operation_evaluations = 0

    def forecast(self, context, candidate, *, deadline):
        if context.domain != DOMAIN:
            raise ValueError("Service forecaster received a different domain")
        names = {"checked": "process_checked", "fast": "process_fast", "restore": "process_checked", "defer": "defer"}
        state = self.state
        remaining = max(0, self.goal-state.progress)
        names_sequence = ["restore"] if candidate.identifier == "restore" else []
        name = names[candidate.identifier]
        count = ceil(remaining/3) if name == "process_fast" else remaining
        names_sequence += [name]*(count if name != "defer" else 1)
        survival, duration, quota, integrity, damage = 1.0, 0.0, state.quota, state.integrity, 0.0
        cost_total, progress, feasible = 0.0, state.progress, True
        for name in names_sequence:
            self.operation_evaluations += 1
            amount, seconds, cost, probability, wear = operation(integrity, self.load, name)
            duration += seconds
            cost_total += cost
            quota -= cost
            if state.elapsed_s+duration > self.deadline_s or quota < 0:
                feasible = False
                break
            survival *= 1-probability
            integrity = min(1, integrity+.3) if name == "restore" else max(0, integrity-wear)
            damage += wear
            progress = min(self.goal, progress+amount)
        success = survival if feasible and progress >= self.goal else 0.0
        # Recoverable wear is scored only on non-outage paths. Outage is its own
        # consequence; it is not subtracted again as a second damage penalty.
        return ConsequenceForecast(context.observation_id, context.generation, candidate.identifier,
            candidate.continuation, candidate.horizon_s, success, 1-survival, 1-survival,
            min(1, damage)*survival, (("processing_quota", cost_total),), (("processing_quota", 0),),
            duration, integrity, ForecastEvidence("analytic", DOMAIN, DOMAIN, "declared service transition equations"))


def state_record(environment):
    return asdict(environment.state)
