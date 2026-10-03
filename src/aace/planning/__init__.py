"""External action guard, independent of controller scoring."""

from dataclasses import dataclass
from math import isfinite

from aace.controllers import brake
from aace.schemas import Action, Observation


@dataclass(frozen=True)
class GuardResult:
    action: Action
    reason: str | None = None


def guard_action(proposed, observation: Observation, *, external_stop: bool = False) -> GuardResult:
    if external_stop:
        return GuardResult(brake(observation), "external_stop")
    try:
        if len(proposed) != 2 or not all(isfinite(float(v)) for v in proposed):
            return GuardResult(brake(observation), "invalid_action")
        action = tuple(max(-1.0, min(1.0, float(v))) for v in proposed)
        return GuardResult(action, "action_clipped" if action != tuple(proposed) else None)
    except (TypeError, ValueError, OverflowError):
        return GuardResult(brake(observation), "invalid_action")

