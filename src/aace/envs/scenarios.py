from dataclasses import dataclass

from aace.schemas import MissionPolicy, TerrainPatch


@dataclass(frozen=True)
class Scenario:
    name: str
    depot: tuple[float, float] = (1.0, 5.0)
    waypoint: tuple[float, float] = (8.5, 5.0)
    patches: tuple[TerrainPatch, ...] = ()
    initial_battery: float = 100.0
    initial_health: float = 1.0
    mission: MissionPolicy = MissionPolicy()
    version: str = "rover-scenarios-v1"


SCENARIOS = {
    "benign": Scenario("benign"),
    "shortcut": Scenario("shortcut", patches=(
        TerrainPatch(4.0, 4.0, 6.0, 6.0, 0.55, 0.7, 1.3),
    )),
    "recoverable_damage": Scenario("recoverable_damage", patches=(
        TerrainPatch(4.0, 4.0, 6.0, 6.0, 0.75, 1.0, 0.12),
    )),
    "low_reserve": Scenario("low_reserve", initial_battery=9.0),
    "deadline": Scenario("deadline", mission=MissionPolicy(deadline_s=6.0)),
    "changed_dynamics": Scenario("changed_dynamics", patches=(
        TerrainPatch(4.0, 4.0, 6.0, 6.0, 0.95, 1.5, 0.03),
    )),
}


def get_scenario(name: str) -> Scenario:
    try:
        return SCENARIOS[name]
    except KeyError:
        raise ValueError(f"Unknown scenario {name!r}; choose {', '.join(SCENARIOS)}") from None

