"""VALOR's domain-independent decision contract; no environment imports."""

from dataclasses import asdict, dataclass
from math import isfinite

CORE_VERSION = "valor-decision-v1"


def finite(value, *, minimum=None, maximum=None):
    if not isfinite(value) or (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ValueError("Value outside the finite decision contract")


def named_values(values):
    if type(values) is not tuple or len(values) > 32 or len({name for name, _ in values}) != len(values):
        raise ValueError("Named values require a bounded unique immutable tuple")
    for name, value in values:
        if not isinstance(name, str) or not name or len(name) > 80:
            raise ValueError("Invalid quantity name")
        finite(value, minimum=0)


@dataclass(frozen=True)
class ActionIntent:
    name: str
    values: tuple[float, ...] = ()

    def __post_init__(self):
        if not self.name or len(self.name) > 80 or type(self.values) is not tuple or len(self.values) > 32:
            raise ValueError("Invalid action intent")
        for value in self.values:
            finite(value)


@dataclass(frozen=True)
class DecisionContext:
    domain: str
    observation_id: str
    generation: int
    resources: tuple[tuple[str, float], ...]
    capability: float
    remaining_time_s: float
    minimum_task_time_s: float

    def __post_init__(self):
        if not self.domain or not self.observation_id or type(self.generation) is not int or self.generation < 0:
            raise ValueError("Invalid context identity")
        named_values(self.resources)
        finite(self.capability, minimum=0, maximum=1)
        finite(self.remaining_time_s, minimum=0)
        finite(self.minimum_task_time_s, minimum=0)


@dataclass(frozen=True)
class Candidate:
    identifier: str
    action: ActionIntent
    continuation: str
    horizon_s: float
    role: str = "task"
    time_hint_s: float = 0

    def __post_init__(self):
        if not self.identifier or not self.continuation or self.role not in ("task", "recovery", "preserve") or not isinstance(self.action, ActionIntent):
            raise ValueError("Invalid candidate")
        finite(self.horizon_s, minimum=1e-9)
        finite(self.time_hint_s, minimum=0)


@dataclass(frozen=True)
class ForecastEvidence:
    kind: str
    model_version: str
    domain: str
    reference: str

    def __post_init__(self):
        if self.kind not in ("analytic", "validated", "experimental", "unknown") or not all((self.model_version, self.domain, self.reference)):
            raise ValueError("Forecast evidence must declare kind, scope and reference")


@dataclass(frozen=True)
class ConsequenceForecast:
    observation_id: str
    generation: int
    candidate_id: str
    continuation: str
    horizon_s: float
    success_probability: float | None
    failure_probability: float | None
    failure_upper_bound: float | None
    recoverable_damage: float | None
    resource_costs: tuple[tuple[str, float], ...]
    recovery_costs: tuple[tuple[str, float], ...]
    duration_s: float
    final_capability: float
    evidence: ForecastEvidence

    def __post_init__(self):
        if type(self.generation) is not int or self.generation < 0 or not all((self.observation_id, self.candidate_id, self.continuation)) or not isinstance(self.evidence, ForecastEvidence):
            raise ValueError("Invalid forecast identity")
        finite(self.horizon_s, minimum=1e-9)
        finite(self.duration_s, minimum=0)
        finite(self.final_capability, minimum=0, maximum=1)
        for value in (self.success_probability, self.failure_probability, self.failure_upper_bound, self.recoverable_damage):
            if value is not None:
                finite(value, minimum=0, maximum=1)
        if self.failure_probability is not None and self.failure_upper_bound is not None and self.failure_upper_bound < self.failure_probability:
            raise ValueError("Risk upper bound is below its point estimate")
        if self.success_probability is not None and self.failure_probability is not None and self.success_probability+self.failure_probability > 1.000001:
            raise ValueError("Success and irreversible failure are competing outcomes")
        named_values(self.resource_costs)
        named_values(self.recovery_costs)


@dataclass(frozen=True)
class DecisionPolicy:
    task_value: float = 30
    recoverable_damage_cost: float = 12
    failure_cost: float = 40
    time_cost: float = 0.1
    max_failure_probability: float = 0.1
    resource_reserves: tuple[tuple[str, float], ...] = ()
    minimum_capability: float = 0.15
    urgency_slack_s: float = 2

    def __post_init__(self):
        for value in (self.task_value, self.recoverable_damage_cost, self.failure_cost, self.time_cost, self.urgency_slack_s):
            finite(value, minimum=0)
        finite(self.max_failure_probability, minimum=0, maximum=1)
        finite(self.minimum_capability, minimum=0, maximum=1)
        named_values(self.resource_reserves)


@dataclass(frozen=True)
class ComputeBudget:
    max_forecasts: int = 8
    action_seconds: float = 0.1

    def __post_init__(self):
        if type(self.max_forecasts) is not int or not 1 <= self.max_forecasts <= 32:
            raise ValueError("Forecast count must be in [1, 32]")
        finite(self.action_seconds, minimum=1e-9, maximum=60)


def record(value):
    return asdict(value)
