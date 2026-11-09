"""Finite simulated release task with persistent damage and exact belief planning."""

from dataclasses import dataclass, replace
from functools import lru_cache

LOW, HIGH = .08, .38
STAKES = (24, 140)
DEADLINE, RESOURCES = 7, 10
ACTORS = ("fixed", "history", "adaptive", "careful_only", "oracle")
ACTIONS = ("stop", "careful", "repair", "fast")
COSTS = {"stop": (0, 0), "careful": (2, 1), "repair": (2, 2), "fast": (1, 1)}


@dataclass(frozen=True, slots=True)
class ReleaseState:
    stage: int = 0
    integrity: int = 3
    faults: int = 0
    elapsed: int = 0
    resources: int = RESOURCES
    attempts: int = 0
    shocks: int = 0
    incidents: int = 0
    repairs: int = 0
    status: str = "running"


def available(state):
    if state.status != "running":
        return ()
    return tuple(a for a in ACTIONS if state.elapsed + COSTS[a][0] <= DEADLINE
                 and state.resources >= COSTS[a][1]
                 and (a != "repair" or state.integrity < 3 or state.faults))


def transition(state, action, *, shock=False):
    if action not in available(state) or type(shock) is not bool or shock and action != "fast":
        raise ValueError("Illegal simulated transition")
    if action == "stop":
        return replace(state, status="stopped")
    ticks, units = COSTS[action]
    elapsed, resources = state.elapsed+ticks, state.resources-units
    if action == "repair":
        return replace(state, integrity=min(3, state.integrity+1), faults=0,
                       elapsed=elapsed, resources=resources, repairs=state.repairs+1)
    fast = action == "fast"
    integrity, faults = state.integrity-int(shock), state.faults+int(shock)
    stage = state.stage+1
    status = ("outage" if integrity == 0 else "release_failure" if stage == 3 and faults
              else "completed" if stage == 3 else "running")
    return ReleaseState(stage, integrity, faults, elapsed, resources, state.attempts+int(fast),
                        state.shocks+int(shock), state.incidents+int(fast and state.faults > 0),
                        state.repairs, status)


def belief(shocks, attempts):
    """Public two-regime posterior, with equal initial regime odds."""
    if not 0 <= shocks <= attempts:
        raise ValueError("Impossible shock history")
    # Likelihood ratios avoid forming a product of two tiny likelihoods.
    odds = (HIGH/LOW)**shocks * ((1-HIGH)/(1-LOW))**(attempts-shocks)
    return odds/(1+odds)


@dataclass(frozen=True, slots=True)
class Outcomes:
    reward: float
    cost: float
    completed: float
    stopped: float
    outage: float
    release_failure: float
    shocks: float
    incidents: float
    repairs: float
    fast_attempts: float

    @property
    def score(self):
        return self.reward-self.cost


def terminal_outcomes(state, stakes):
    if state.status not in ("completed", "stopped", "outage", "release_failure"):
        raise ValueError("Cannot score an unfinished release")
    completed, stopped = state.status == "completed", state.status == "stopped"
    outage, failure = state.status == "outage", state.status == "release_failure"
    reward = stakes*(10-state.elapsed)/10 if completed else 0.
    cost = (9*state.shocks + 5*state.incidents + 25*int(outage or failure)
            + .5*(RESOURCES-state.resources))
    return Outcomes(reward, cost, float(completed), float(stopped), float(outage), float(failure),
                    state.shocks, state.incidents, state.repairs, state.attempts)


def mixture(first, second, weight):
    return Outcomes(*(getattr(first, key)*(1-weight)+getattr(second, key)*weight
                      for key in Outcomes.__dataclass_fields__))


class ReleasePlanner:
    def __init__(self, actor, stakes, historical_shocks=0, *, oracle_danger=None):
        if actor not in ACTORS or stakes not in STAKES or type(historical_shocks) is not int or not 0 <= historical_shocks <= 8:
            raise ValueError("Unknown planner scope")
        if (actor == "oracle" and oracle_danger not in (LOW, HIGH)) or (actor != "oracle" and oracle_danger is not None):
            raise ValueError("Only the privileged oracle receives actual danger")
        self.actor, self.stakes, self.historical_shocks = actor, stakes, historical_shocks
        self.oracle_danger = oracle_danger
        # Instance-scoped cache: one model, objective and history per search.
        self._best = lru_cache(maxsize=None)(self._solve)

    def danger(self, state):
        if self.actor == "oracle":
            return self.oracle_danger
        if self.actor in ("fixed", "careful_only"):
            return (LOW+HIGH)/2
        adaptive = self.actor == "adaptive"
        weight = belief(self.historical_shocks+(state.shocks if adaptive else 0),
                        8+(state.attempts if adaptive else 0))
        return LOW+(HIGH-LOW)*weight

    def branches(self, state, action):
        if action != "fast":
            return ((1., False, transition(state, action)),)
        p = self.danger(state)
        return ((1-p, False, transition(state, action)),
                (p, True, transition(state, action, shock=True)))

    def alternatives(self, state):
        result = {}
        for action in available(state):
            if self.actor == "careful_only" and action not in ("careful", "stop"):
                continue
            branches = self.branches(state, action)
            first = self._best(branches[0][2])[1]
            result[action] = (first if len(branches) == 1
                              else mixture(first, self._best(branches[1][2])[1], branches[1][0]))
        return result

    def _solve(self, state):
        if state.status != "running":
            return None, terminal_outcomes(state, self.stakes)
        choices = self.alternatives(state)
        action = max(choices, key=lambda a: choices[a].score)
        return action, choices[action]

    def decide(self, state):
        action, outcomes = self._best(state)
        if action is None:
            raise ValueError("Task already finished")
        return action, outcomes

    def work(self):
        return self._best.cache_info().misses
