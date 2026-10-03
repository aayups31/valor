"""Immutable public observations and versioned numerical records."""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

SCHEMA_VERSION = "1.0"
Action = tuple[float, float]


@dataclass(frozen=True)
class MissionPolicy:
    deadline_s: float = 45.0
    task_value: float = 30.0
    damage_cost: float = 12.0
    catastrophe_cost: float = 40.0
    max_failure_probability: float = 0.1

    def __post_init__(self) -> None:
        values = (self.deadline_s, self.task_value, self.damage_cost,
                  self.catastrophe_cost, self.max_failure_probability)
        if not all(isfinite(v) for v in values):
            raise ValueError("Mission values must be finite")
        if self.deadline_s <= 0 or min(values[1:4]) < 0:
            raise ValueError("Invalid mission deadline or loss weights")
        if not 0 <= self.max_failure_probability <= 1:
            raise ValueError("Invalid failure-probability limit")


@dataclass(frozen=True)
class RoverState:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    battery: float = 100.0
    health: float = 1.0
    step: int = 0
    inspected: bool = False
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TerrainPatch:
    x0: float
    y0: float
    x1: float
    y1: float
    grip: float
    safe_speed: float
    damage_rate: float

    def contains(self, x: float, y: float) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1


@dataclass(frozen=True)
class Observation:
    """Only this public packet is passed to ordinary controllers.

    v1 is fully observed. No disturbance seeds, snapshots or future noise enter it.
    Partial-observation experiments require a new version and matching baselines.
    """

    state: RoverState
    waypoint: tuple[float, float]
    depot: tuple[float, float]
    bounds: tuple[float, float]
    patches: tuple[TerrainPatch, ...]
    mission: MissionPolicy
    dt: float
    max_acceleration: float
    max_speed: float

    @property
    def target(self) -> tuple[float, float]:
        return self.depot if self.state.inspected else self.waypoint

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["target"] = self.target
        result["visibility"] = "fully_observed_v1"
        result["schema_version"] = SCHEMA_VERSION
        return result


@dataclass(frozen=True)
class StepResult:
    state: RoverState
    reward: float
    terminated: bool
    truncated: bool
    events: tuple[str, ...]
    energy_used: float
    damage: float

