"""Repeated simulated releases, public predictors and matched continuation search."""

from dataclasses import asdict
from functools import lru_cache

import numpy as np

from aace.benchmarks.cascade import (
    HIGH, LOW, STAKES, ReleaseState, available, mixture, terminal_outcomes, transition,
)

TASKS = 8
SWITCH = .20
BOUNDARY, SHOCK, CLEAR = range(3)


def campaign(seed):
    world, stakes, shocks, explore = (
        np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(4)
    )
    regime = int(world.integers(2))
    danger = []
    for task in range(TASKS):
        if task and world.random() < SWITCH:
            regime = 1-regime
        danger.append((LOW, HIGH)[regime])
    return danger, stakes.choice(STAKES, TASKS), shocks.random((TASKS, 3)), explore


def training_tokens(seeds):
    tokens = np.full((len(seeds), TASKS*4), -1, dtype=np.int8)
    for row, seed in enumerate(seeds):
        danger, _, draws, rng = campaign(seed)
        sequence = []
        for task, p in enumerate(danger):
            sequence.append(BOUNDARY)
            sequence.extend(SHOCK if draw < p else CLEAR for draw in draws[task, :rng.integers(1, 4)])
        tokens[row, :len(sequence)] = sequence
    return tokens


def carry(state):
    if state.status == "running":
        raise ValueError("Cannot reset unfinished work")
    if state.status == "outage":
        return None
    return ReleaseState(integrity=state.integrity, faults=state.faults)


class Markov:
    initial = .5

    def __init__(self, switch):
        if not 0 <= switch <= .5:
            raise ValueError("Invalid switching probability")
        self.switch = switch

    def probability(self, state):
        return LOW+(HIGH-LOW)*state

    def update(self, state, token):
        if token == BOUNDARY:
            return self.switch+(1-2*self.switch)*state
        if token not in (SHOCK, CLEAR):
            raise ValueError("Invalid observation")
        a, b = (LOW, HIGH) if token == SHOCK else (1-LOW, 1-HIGH)
        return b*state/(b*state+a*(1-state))


class Window:
    initial = ()

    def probability(self, state):
        return min(HIGH, max(LOW, (sum(state)+.46)/(len(state)+2)))

    def update(self, state, token):
        return state if token == BOUNDARY else (*state, int(token == SHOCK))[-4:]


class Fixed:
    initial = None

    def probability(self, state):
        return (LOW+HIGH)/2

    def update(self, state, token):
        return None


def heuristic(state, stakes):
    processing = ("fast", "careful") if stakes == 140 else ("careful", "fast")
    order = ("repair", *processing) if state.faults else (*processing, "repair")
    return tuple(action for action in order if action in available(state))


class Search:
    """Exactly integrate the public predictor's branches within one task."""

    def __init__(self, predictor, stakes):
        self.predictor, self.stakes = predictor, stakes
        self.best = lru_cache(maxsize=None)(self._best)
        self.evaluations = 0

    def branches(self, state, memory, action):
        normal = transition(state, action)
        if action != "fast":
            return ((1., normal, memory),)
        p = self.predictor.probability(memory)
        return ((1-p, normal, self.predictor.update(memory, CLEAR)),
                (p, transition(state, action, shock=True), self.predictor.update(memory, SHOCK)))

    def forecast(self, state, memory, action):
        self.evaluations += 1
        branches = self.branches(state, memory, action)
        normal = self.best(*branches[0][1:])[1]
        return normal if len(branches) == 1 else mixture(
            normal, self.best(*branches[1][1:])[1], branches[1][0])

    def choose(self, state, memory, candidates=None):
        legal = available(state)
        if not legal:
            raise ValueError("Cannot choose after terminal outcome")
        if candidates is not None and not set(candidates) <= set(legal):
            raise ValueError("Illegal candidate")
        scores = {a: self.forecast(state, memory, a) for a in legal if candidates is None or a in candidates}
        return max(scores, key=lambda a: scores[a].score), scores

    def _best(self, state, memory):
        if state.status != "running":
            return None, terminal_outcomes(state, self.stakes)
        action, choices = self.choose(state, memory)
        return action, choices[action]


def apply_observed(predictor, state, memory, action, danger, draws):
    shock = action == "fast" and bool(draws[state.attempts] < danger)
    if action == "fast":
        memory = predictor.update(memory, SHOCK if shock else CLEAR)
    return transition(state, action, shock=shock), memory, shock


def play(seed, predictor, *, reset=False, bank=None, retrieval="full", trace=False):
    danger, stakes, draws, _ = campaign(seed)
    state, memory = ReleaseState(), predictor.initial
    totals = dict.fromkeys(("score", "completed", "stopped", "outage", "release_failure", "shocks", "incidents",
                            "repairs", "fast_attempts", "brier_sum", "root_candidates", "forecast_calls", "recall_hits"), 0.)
    records = []
    for task in range(TASKS):
        if state is None:
            break
        value = int(stakes[task])
        memory = predictor.update(predictor.initial if reset else memory, BOUNDARY)
        search = Search(predictor, value)
        while state.status == "running":
            candidates, recall = None, None
            if retrieval != "full":
                order = heuristic(state, value)
                if retrieval != "heuristic":
                    recall = bank.recall(state, value, retrieval, model_switch=predictor.switch)
                if recall is not None:
                    totals["recall_hits"] += 1
                    order = (recall, *(a for a in order if a != recall))
                candidates = ("stop", *order[:2])
            action, forecasts = search.choose(state, memory, candidates)
            p = predictor.probability(memory)
            prior = memory
            after, memory, shock = apply_observed(predictor, state, memory, action, danger[task], draws[task])
            totals["root_candidates"] += len(forecasts)
            if action == "fast":
                totals["brier_sum"] += (p-shock)**2
            if trace:
                records.append({"task": task, "stakes": value, "before": asdict(state), "after": asdict(after),
                                "shock_probability": p, "observed_shock": shock if action == "fast" else None,
                                "public_predictor_state_before": prior, "public_predictor_state_after": memory,
                                "selected": action, "recalled_candidate": recall,
                                "recall_evidence": bank.evidence(state, value, model_switch=predictor.switch)
                                if recall is not None else None,
                                "evaluated": {a: {**asdict(f), "score": f.score} for a, f in forecasts.items()},
                                "legal_not_evaluated": [a for a in available(state) if a not in forecasts]})
            state = after
        totals["forecast_calls"] += search.evaluations
        search.best.cache_clear()
        result = terminal_outcomes(state, value)
        for key in ("score", "completed", "stopped", "outage", "release_failure", "shocks", "incidents", "repairs", "fast_attempts"):
            totals[key] += getattr(result, key)
        state = carry(state)
    return {"seed": seed, **totals, **({"decisions": records} if trace else {})}
