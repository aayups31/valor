"""External stop/state authority and a final simulation action commit check."""

from dataclasses import dataclass
from threading import RLock
from typing import Callable

from aace.decision.contracts import ActionIntent


@dataclass(frozen=True)
class CommitResult:
    status: str
    applied_action: ActionIntent | None
    generation: int


class ActionAuthority:
    """A small local handoff gate, not an OS/robot actuation safety certificate.

    Application callbacks must be short. Checks cannot preempt a blocking
    forecaster or application callback. The decision core cannot clear stop.
    """

    def __init__(self):
        self._lock = RLock()
        self._generation = 0
        self._stopped = False

    def snapshot(self):
        with self._lock:
            return self._generation, self._stopped

    def stop(self):
        with self._lock:
            self._stopped = True

    def supersede(self):
        with self._lock:
            self._generation += 1

    def check(self, generation, deadline, clock):
        with self._lock:
            return self._check(generation, deadline, clock)

    def _check(self, generation, deadline, clock):
        if self._stopped:
            return "external_stop"
        if generation != self._generation:
            return "stale_state"
        if clock() >= deadline:
            return "action_deadline"
        return None

    def commit(self, decision, apply: Callable[[ActionIntent], None], *, clock):
        with self._lock:
            reason = self._check(decision.generation, decision.deadline, clock)
            if reason:
                return CommitResult(reason, None, self._generation)
            if decision.action is None or decision.status != "selected":
                return CommitResult("abstained", None, self._generation)
            try:
                apply(decision.action)
            finally:
                # Also invalidate a decision after a partially failed callback.
                self._generation += 1
            return CommitResult("applied", decision.action, self._generation)
