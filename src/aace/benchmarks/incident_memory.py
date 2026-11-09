"""Bounded simulated evidence bank; recall nominates actions, never authorizes them."""

from collections import OrderedDict
from dataclasses import asdict, dataclass

from aace.benchmarks.cascade import HIGH, LOW, ReleaseState, available, mixture, terminal_outcomes, transition
from aace.benchmarks.repeated import BOUNDARY, CLEAR, SHOCK, TASKS, Search, apply_observed, campaign, carry

VERSION = "cascade-two-regime-recourse-v1"
CAPACITY = 256


def failure(outcome):
    return outcome.outage + outcome.release_failure


def audit_action(search, state, memory, action, actual_danger):
    """Integrate the fixed public policy at one hidden-regime endpoint."""
    work = 0

    def evaluate(state, memory, action):
        nonlocal work
        work += 1
        if state.status != "running":
            return terminal_outcomes(state, search.stakes)
        if action is None:
            action = search.best(state, memory)[0]
        if action != "fast":
            return evaluate(transition(state, action), memory, None)
        normal = evaluate(transition(state, action), search.predictor.update(memory, CLEAR), None)
        hurt = evaluate(transition(state, action, shock=True), search.predictor.update(memory, SHOCK), None)
        return mixture(normal, hurt, actual_danger)

    return evaluate(state, memory, action), work


@dataclass(frozen=True)
class Record:
    seed: int
    task: int
    state: ReleaseState
    stakes: int
    observed_action: str
    observed_after: ReleaseState
    observed_task_status: str
    observed_score: float
    recourse: str | None
    endpoint_deltas: tuple
    audit_nodes: int
    model_switch: float
    public_belief: float
    version: str = VERSION


class Bank:
    def __init__(self):
        self._records = OrderedDict()

    def put(self, record):
        if record.version != VERSION or record.observed_action not in available(record.state):
            raise ValueError("Invalid record scope")
        if record.recourse is not None and (record.recourse not in available(record.state)
                or len(record.endpoint_deltas) != 2 or any(score < 1 or risk > 0 for score, risk in record.endpoint_deltas)):
            raise ValueError("Recourse does not pass both declared regime checks")
        key = record.state, record.stakes, record.model_switch
        self._records[key] = record
        self._records.move_to_end(key)
        if len(self._records) > CAPACITY:
            self._records.popitem(last=False)

    def recall(self, state, stakes, mode, *, model_switch):
        if mode not in ("verified", "factual"):
            raise ValueError("Unknown recall mode")
        record = self._records.get((state, stakes, model_switch))
        if record is None:
            return None
        if mode == "verified" and record.recourse is not None:
            return record.recourse
        return record.observed_action if record.observed_task_status == "completed" else None

    def records(self):
        return [asdict(record) for record in self._records.values()]


def build_bank(seeds, predictor):
    bank, audited, forecasts = Bank(), 0, 0
    for seed in seeds:
        danger, stakes, draws, rng = campaign(seed)
        state, memory = ReleaseState(), predictor.initial
        for task in range(TASKS):
            if state is None:
                break
            value = int(stakes[task])
            memory = predictor.update(memory, BOUNDARY)
            search = Search(predictor, value)
            pending = []
            while state.status == "running":
                legal = available(state)
                actual = str(rng.choice(legal[1:])) if len(legal) > 1 else "stop"
                observed, updated, _ = apply_observed(predictor, state, memory, actual, danger[task], draws[task])
                outcomes, work = {}, 0
                for action in legal:
                    pair = [audit_action(search, state, memory, action, p) for p in (LOW, HIGH)]
                    outcomes[action] = [result for result, _ in pair]
                    work += sum(nodes for _, nodes in pair)
                candidates = {}
                for action, pair in outcomes.items():
                    if action in ("stop", actual):
                        continue
                    deltas = tuple((a.score-b.score, failure(a)-failure(b)) for a, b in zip(pair, outcomes[actual]))
                    if all(score >= 1 and risk <= 0 for score, risk in deltas):
                        candidates[action] = deltas
                recourse = max(candidates, key=lambda a: min(d[0] for d in candidates[a]), default=None)
                pending.append((state, actual, observed, recourse, candidates.get(recourse, ()), work, memory))
                audited += work
                state, memory = observed, updated
            score = terminal_outcomes(state, value).score
            for before, action, after, recourse, deltas, work, prior in pending:
                bank.put(Record(seed, task, before, value, action, after, state.status, score, recourse,
                                deltas, work, predictor.switch, prior))
            forecasts += search.evaluations
            search.best.cache_clear()
            state = carry(state)
    return bank, {"endpoint_nodes": audited, "continuation_forecasts": forecasts}
