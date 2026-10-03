"""Controllers accept public observations, never simulator snapshots."""

from dataclasses import dataclass
from math import hypot
from typing import Any

from aace.schemas import Action, Observation

PLAN_NAMES = ("direct", "detour_north", "detour_south", "return", "brake", "coast")


def brake(observation: Observation) -> Action:
    o = observation
    grip = min((p.grip for p in o.patches if p.contains(o.state.x, o.state.y)), default=1.0)
    scale = max(0.01, o.max_acceleration * o.state.health * grip * o.dt)
    return (max(-1.0, min(1.0, -o.state.vx/scale)),
            max(-1.0, min(1.0, -o.state.vy/scale)))


def seek(observation: Observation, target: tuple[float, float]) -> Action:
    s = observation.state
    dx, dy = target[0]-s.x, target[1]-s.y
    distance = hypot(dx, dy)
    desired_speed = min(0.85*observation.max_speed, 1.3*distance)
    denominator = max(distance, 1e-9)
    desired_vx, desired_vy = desired_speed*dx/denominator, desired_speed*dy/denominator
    scale = max(0.1, observation.max_acceleration*s.health)
    return (max(-1.0, min(1.0, 2.5*(desired_vx-s.vx)/scale)),
            max(-1.0, min(1.0, 2.5*(desired_vy-s.vy)/scale)))


def action_for_plan(observation: Observation, plan: str) -> Action:
    if plan == "brake":
        return brake(observation)
    if plan == "coast":
        return (0.0, 0.0)
    target = observation.depot if plan == "return" else observation.target
    if plan in ("detour_north", "detour_south") and observation.patches:
        patch = observation.patches[0]
        lane_y = patch.y1+1.0 if plan == "detour_north" else patch.y0-1.0
        lane_y = min(observation.bounds[1]-0.6, max(0.6, lane_y))
        west, east = patch.x0-1.0, patch.x1+1.0
        s = observation.state
        if target[0] > s.x:
            if s.x < west-0.15:
                target = (west, lane_y)
            elif s.x < east-0.15:
                target = (east, lane_y)
        else:
            if s.x > east+0.15:
                target = (east, lane_y)
            elif s.x > west+0.15:
                target = (west, lane_y)
    return seek(observation, target)


@dataclass(frozen=True)
class Proposal:
    plan: str
    action: Action
    candidates: tuple[dict[str, Any], ...]
    forecast_source: str = "none"
    branch_transitions: int = 0


class HeuristicController:
    def __init__(self, detour: bool = False):
        self.detour = detour
        self.name = "heuristic_detour" if detour else "heuristic_direct"

    def decide(self, observation: Observation) -> Proposal:
        plan = "detour_north" if self.detour and observation.patches else "direct"
        records = tuple({"plan": name, "action": action_for_plan(observation, name),
                         "status": "selected" if name == plan else "unexplored",
                         "reason_codes": ["heuristic_rule" if name == plan else "no_forecast_budget"],
                         "forecast": None} for name in PLAN_NAMES)
        return Proposal(plan, action_for_plan(observation, plan), records)

