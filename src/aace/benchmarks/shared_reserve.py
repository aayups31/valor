"""Two simulated releases with public future stakes and a shared resource reserve."""

from dataclasses import asdict, replace
from functools import lru_cache

import numpy as np

from aace.benchmarks.cascade import HIGH, LOW, RESOURCES, STAKES, ReleaseState, available, terminal_outcomes, transition
from aace.benchmarks.repeated import BOUNDARY, CLEAR, SHOCK, Fixed, Markov, apply_observed, carry

ACTORS = ("myopic_markov", "horizon_fixed", "horizon_markov", "horizon_trained", "horizon_reset")
GUARDED = "guarded_markov"
SHIFTS = {
    "nominal": (.20, LOW, HIGH, False),
    "volatile": (.45, LOW, HIGH, False),
    "harsher": (.20, .15, .52, False),
    "damaged": (.20, LOW, HIGH, True),
}


def subject(seed, scenario):
    switch, low, high, damaged = SHIFTS[scenario]
    public, regimes, precursor, actual = (
        np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(4)
    )
    state = ReleaseState(resources=int(public.integers(7, 9)), integrity=2 if damaged else 3,
                         faults=int(damaged))
    stakes = tuple(int(v) for v in public.choice(STAKES, 2))
    first = int(regimes.integers(2))
    second = 1-first if regimes.random() < switch else first
    danger = ((low, high)[first], (low, high)[second])
    evidence = tuple(SHOCK if p < danger[0] else CLEAR for p in precursor.random(3))
    return state, stakes, evidence, danger, actual.random((2, 3))


def next_task(state):
    continued = carry(state)
    return None if continued is None else replace(continued, resources=state.resources)


def task_score(state, stakes, initial_reserve):
    return terminal_outcomes(state, stakes).score + .5*(RESOURCES-initial_reserve)


class PairPlanner:
    def __init__(self, actor, stakes, trained=None):
        if actor not in ACTORS or len(stakes) != 2 or any(v not in STAKES for v in stakes):
            raise ValueError("Invalid planning scope")
        if actor in ("horizon_trained", "horizon_reset") and trained is None:
            raise ValueError("Frozen recurrent model required")
        self.actor, self.stakes = actor, stakes
        self.predictor = (Fixed() if actor == "horizon_fixed" else trained
                          if actor in ("horizon_trained", "horizon_reset") else Markov(.20))
        self.solve = lru_cache(maxsize=32768)(self._solve)
        self.evaluate_pair = lru_cache(maxsize=32768)(self._evaluate_pair)

    def boundary(self, memory):
        p = self.predictor
        return p.update(p.initial if self.actor == "horizon_reset" else memory, BOUNDARY)

    def initial(self, evidence):
        memory = self.boundary(self.predictor.initial)
        if self.actor != "horizon_reset":
            for token in evidence:
                memory = self.predictor.update(memory, token)
        return memory

    def forecast(self, state, memory, task, initial_reserve, action):
        normal = transition(state, action)
        if action != "fast":
            return self.solve(normal, memory, task, initial_reserve)[1:]
        p = self.predictor.probability(memory)
        clear = self.solve(normal, self.predictor.update(memory, CLEAR), task, initial_reserve)
        shock = self.solve(transition(state, action, shock=True), self.predictor.update(memory, SHOCK),
                           task, initial_reserve)
        return tuple(a*(1-p)+b*p for a, b in zip(clear[1:], shock[1:]))

    def alternatives(self, state, memory, task, initial_reserve):
        return {a: self.forecast(state, memory, task, initial_reserve, a) for a in available(state)}

    def _solve(self, state, memory, task, initial_reserve):
        if state.status == "running":
            alternatives = self.alternatives(state, memory, task, initial_reserve)
            action = max(alternatives, key=lambda a: alternatives[a][0])
            return action, *alternatives[action]
        score = task_score(state, self.stakes[task], initial_reserve)
        failures = int(state.status in ("outage", "release_failure"))
        if task == 0 and self.actor != "myopic_markov" and state.status != "outage":
            future = next_task(state)
            _, future_score, future_failures, future_completed = self.solve(
                future, self.boundary(memory), 1, future.resources)
            score += future_score
            failures += future_failures
        else:
            future_completed = 0
        return None, score, failures, int(state.status == "completed")+future_completed

    def _evaluate_pair(self, state, memory, task, initial_reserve):
        """Integrate the fixed myopic policy across both tasks, without changing its decisions."""
        if state.status != "running":
            _, score, failures, completed = self.solve(state, memory, task, initial_reserve)
            if task == 0 and state.status != "outage":
                future = next_task(state)
                return tuple(a+b for a, b in zip((score, failures, completed), self.evaluate_pair(
                    future, self.boundary(memory), 1, future.resources)))
            return score, failures, completed
        action = self.solve(state, memory, task, initial_reserve)[0]
        clear = self.evaluate_pair(transition(state, action),
            self.predictor.update(memory, CLEAR) if action == "fast" else memory, task, initial_reserve)
        if action != "fast":
            return clear
        shock = self.evaluate_pair(transition(state, action, shock=True),
                                   self.predictor.update(memory, SHOCK), task, initial_reserve)
        p = self.predictor.probability(memory)
        return tuple(a*(1-p)+b*p for a, b in zip(clear, shock))


def screen_checks(horizon, myopic):
    score, failures, completed = horizon
    base_score, base_failures, base_completed = myopic
    return {
        "higher_score": score > base_score + 1e-10,
        "completion_within_limit": completed >= base_completed - .04 - 1e-10,
        "failures_within_limit": failures <= base_failures + .02 + 1e-10,
    }


def choose_policy(horizon, myopic):
    return all(screen_checks(horizon, myopic).values())


def play_pair(seed, scenario, actor, planners, *, trained=None, trace=False):
    state, stakes, evidence, danger, draws = subject(seed, scenario)

    def get(name):
        key = name, stakes
        if key not in planners:
            planners[key] = PairPlanner(name, stakes, trained)
        return planners[key]

    planner = get("horizon_markov" if actor == GUARDED else actor)
    memory = planner.initial(evidence)
    def work():
        return sum(p.solve.cache_info().misses+p.evaluate_pair.cache_info().misses for p in planners.values())

    work_before = work()
    prediction = planner.solve(state, memory, 0, state.resources)[1:]
    screen = None
    if actor == GUARDED:
        baseline = get("myopic_markov")
        comparison = baseline.evaluate_pair(state, memory, 0, state.resources)
        accepted = choose_policy(prediction, comparison)
        screen = {"lookahead": prediction, "myopic": comparison, "accepted": accepted}
        if not accepted:
            planner, prediction = baseline, comparison
    totals = dict.fromkeys(("score", "completed", "stopped", "outage", "release_failure",
                            "shocks", "incidents", "repairs", "fast_attempts"), 0.)
    records = []
    for task in range(2):
        if state is None:
            break
        initial_reserve = state.resources
        while state.status == "running":
            action = planner.solve(state, memory, task, initial_reserve)[0]
            # Read the cache only; these alternatives were visited by the selected search.
            choices = planner.alternatives(state, memory, task, initial_reserve) if trace else None
            after, updated, shock = apply_observed(planner.predictor, state, memory, action, danger[task], draws[task])
            if trace:
                records.append({"task": task, "stakes": stakes[task], "before": asdict(state), "after": asdict(after),
                                "predictor_state": memory, "shock_probability": planner.predictor.probability(memory),
                                "observed_shock": shock if action == "fast" else None, "selected": action,
                                "alternatives": {a: {"expected_score": s, "expected_failure_count": f,
                                                     "expected_completed_count": c}
                                                 for a, (s, f, c) in choices.items()}})
            state, memory = after, updated
        outcome = terminal_outcomes(state, stakes[task])
        totals["score"] += task_score(state, stakes[task], initial_reserve)
        for key in totals.keys()-{"score"}:
            totals[key] += getattr(outcome, key)
        state = next_task(state)
        memory = planner.boundary(memory)
    full = actor != "myopic_markov"
    return {"seed": seed, **totals, "completion_rate": totals["completed"]/2,
            "failure_rate": (totals["outage"]+totals["release_failure"])/2,
            "initial_expected_pair_score": prediction[0] if full else None,
            "initial_expected_pair_failures": prediction[1] if full else None,
            "initial_expected_pair_completed": prediction[2] if full else None,
            "executed_policy": planner.actor,
            "new_search_nodes": work()-work_before,
            **({"public_precursor": evidence, "forecast_screen": screen, "decisions": records} if trace else {})}
