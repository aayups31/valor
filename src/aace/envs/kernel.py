"""Pure numerical transition kernel; no random calls or implicit mutable state."""

from dataclasses import dataclass
from math import hypot, isfinite

from aace.envs.scenarios import Scenario
from aace.schemas import Action, RoverState, StepResult


@dataclass(frozen=True)
class RoverConfig:
    dt: float = 0.1
    width: float = 10.0
    height: float = 10.0
    max_acceleration: float = 2.0
    max_speed: float = 2.0
    drag: float = 0.35
    idle_energy_per_s: float = 0.18
    motion_energy_per_s: float = 0.28
    action_energy_per_s: float = 0.12
    arrival_radius: float = 0.45
    arrival_speed: float = 0.5
    max_steps: int = 500
    noise_std: float = 0.015
    version: str = "rover-kernel-v1"

    def __post_init__(self) -> None:
        positive = (self.dt, self.width, self.height, self.max_acceleration,
                    self.max_speed, self.arrival_radius, self.arrival_speed)
        nonnegative = (self.drag, self.idle_energy_per_s, self.motion_energy_per_s,
                       self.action_energy_per_s, self.noise_std)
        if any(not isfinite(v) or v <= 0 for v in positive):
            raise ValueError("Physical scales must be finite and positive")
        if any(not isfinite(v) or v < 0 for v in nonnegative) or self.max_steps <= 0:
            raise ValueError("Invalid resource, noise or step limits")


def transition(state: RoverState, action: Action, scenario: Scenario,
               config: RoverConfig, disturbance: Action = (0.0, 0.0)) -> StepResult:
    if state.status != "running":
        raise RuntimeError("An ended episode must be reset before stepping")
    if len(action) != 2 or any(not isfinite(v) or abs(v) > 1 for v in action):
        raise ValueError("Applied actions must be two finite values in [-1, 1]")
    if any(not isfinite(v) for v in disturbance):
        raise ValueError("Disturbances must be finite")
    dt = config.dt
    grip = min((p.grip for p in scenario.patches if p.contains(state.x, state.y)), default=1.0)
    ax = config.max_acceleration * state.health * grip * action[0]
    ay = config.max_acceleration * state.health * grip * action[1]
    vx = state.vx + dt * (ax - config.drag * state.vx + disturbance[0])
    vy = state.vy + dt * (ay - config.drag * state.vy + disturbance[1])
    speed = hypot(vx, vy)
    if speed > config.max_speed:
        vx *= config.max_speed / speed
        vy *= config.max_speed / speed
        speed = config.max_speed
    x, y = state.x + dt * vx, state.y + dt * vy
    damage = 0.0
    events: list[str] = []
    if not 0 <= x <= config.width or not 0 <= y <= config.height:
        damage += min(0.3, 0.06 * speed * speed)
        x, y = min(config.width, max(0.0, x)), min(config.height, max(0.0, y))
        vx, vy = 0.0, 0.0
        events.append("boundary_impact")
    for patch in scenario.patches:
        if patch.contains(x, y) and speed > patch.safe_speed:
            damage += dt * patch.damage_rate * (speed - patch.safe_speed)
    health = max(0.0, state.health - damage)
    damage = state.health - health
    if damage > 0:
        events.append("damage")
    energy = dt * (config.idle_energy_per_s + config.motion_energy_per_s * speed**2
                   + config.action_energy_per_s * hypot(*action)) * (1 + 2 * (1 - health))
    battery = max(0.0, state.battery - energy)
    inspected = state.inspected
    reward = -0.02 - 0.02 * energy - scenario.mission.damage_cost * damage
    old_target = scenario.depot if state.inspected else scenario.waypoint
    reward += 0.5 * (hypot(state.x - old_target[0], state.y - old_target[1])
                    - hypot(x - old_target[0], y - old_target[1]))
    if not inspected and hypot(x - scenario.waypoint[0], y - scenario.waypoint[1]) <= config.arrival_radius:
        inspected = True
        reward += 10.0
        events.append("waypoint_inspected")
    step = state.step + 1
    status = "running"
    if health <= 0.05:
        status = "actuator_loss"
    elif battery <= 0:
        status = "battery_depleted"
    elif inspected and hypot(x - scenario.depot[0], y - scenario.depot[1]) <= config.arrival_radius and hypot(vx, vy) <= config.arrival_speed:
        status = "completed"
        reward += scenario.mission.task_value
    elif step * dt >= scenario.mission.deadline_s:
        status = "deadline_missed"
        reward -= scenario.mission.task_value / 3
    elif step >= config.max_steps:
        status = "time_limit"
    if status in ("actuator_loss", "battery_depleted"):
        reward -= scenario.mission.catastrophe_cost
    if status != "running":
        events.append(status)
    new_state = RoverState(x, y, vx, vy, battery, health, step, inspected, status)
    return StepResult(new_state, reward, status not in ("running", "time_limit"),
                      status == "time_limit", tuple(events), energy, damage)

