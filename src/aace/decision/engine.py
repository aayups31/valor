"""Fear, survival margins and bounded arbitration under external authority."""

import time
from dataclasses import dataclass
from typing import Protocol

from aace.decision.authority import ActionAuthority
from aace.decision.contracts import (CORE_VERSION, ActionIntent, Candidate, ComputeBudget,
                                     ConsequenceForecast, DecisionContext, DecisionPolicy, finite, record)


class Forecaster(Protocol):
    def forecast(self, context: DecisionContext, candidate: Candidate, *, deadline: float) -> ConsequenceForecast: ...


@dataclass(frozen=True)
class Decision:
    generation: int
    deadline: float
    status: str
    candidate_id: str | None
    action: ActionIntent | None
    trace: dict


def assess(context, candidate, forecast, policy):
    """One objective; fear does not subtract a second damage penalty."""
    reasons = []
    if (forecast.observation_id, forecast.generation, forecast.candidate_id, forecast.continuation) != (context.observation_id, context.generation, candidate.identifier, candidate.continuation):
        reasons.append("forecast_identity_mismatch")
    if forecast.evidence.domain != context.domain:
        reasons.append("forecast_scope_mismatch")
    if forecast.horizon_s+1e-9 < candidate.horizon_s or forecast.duration_s > forecast.horizon_s+1e-9:
        reasons.append("insufficient_forecast_horizon")
    known = all(value is not None for value in (forecast.success_probability, forecast.failure_probability,
                                               forecast.failure_upper_bound, forecast.recoverable_damage))
    qualified = forecast.evidence.kind in ("analytic", "validated")
    if not known:
        reasons.append("unknown_consequences")
    if not qualified:
        reasons.append("unqualified_forecast")
    if forecast.failure_upper_bound is not None and forecast.failure_upper_bound > policy.max_failure_probability:
        reasons.append("failure_limit")
    costs, recovery, reserves = map(dict, (forecast.resource_costs, forecast.recovery_costs, policy.resource_reserves))
    available = dict(context.resources)
    if set(costs) != set(available) or set(recovery) != set(available) or not set(reserves) <= set(available):
        reasons.append("unknown_resource_requirements")
    margins = {name: value-costs[name]-recovery[name]-reserves.get(name, 0)
               for name, value in available.items() if name in costs and name in recovery}
    if any(value < -1e-9 for value in margins.values()):
        reasons.append("insufficient_recovery_reserve")
    time_margin = context.remaining_time_s-forecast.duration_s
    if time_margin < -1e-9:
        reasons.append("mission_deadline")
    capability_margin = forecast.final_capability-policy.minimum_capability
    if capability_margin < -1e-9:
        reasons.append("capability_floor")
    score = (policy.task_value*forecast.success_probability-policy.recoverable_damage_cost*forecast.recoverable_damage
             -policy.failure_cost*forecast.failure_probability-policy.time_cost*forecast.duration_s) if known and qualified else None
    for value in (*margins.values(), time_margin, capability_margin):
        finite(value)
    if score is not None:
        finite(score)
    return {"reason_codes": reasons, "score": score,
            "fear": {"failure_probability": forecast.failure_probability,
                     "failure_upper_bound": forecast.failure_upper_bound, "qualified": qualified and known and not any(reason in reasons for reason in ("forecast_identity_mismatch", "forecast_scope_mismatch", "insufficient_forecast_horizon")),
                     "notice": "Action/continuation-specific threat forecast, not an emotion percentage"},
            "survival": {"resource_margins": margins, "time_margin_s": time_margin,
                         "capability_margin": capability_margin}, "forecast": record(forecast)}


class DecisionEngine:
    """Produces inspectable proposals. Apply only through a current authority gate."""

    def decide(self, context: DecisionContext, candidates: tuple[Candidate, ...], forecaster: Forecaster,
               policy: DecisionPolicy, authority: ActionAuthority, budget: ComputeBudget | None = None,
               *, clock=time.perf_counter) -> Decision:
        budget = budget or ComputeBudget()
        if type(candidates) is not tuple or not 1 <= len(candidates) <= 32 or any(not isinstance(item, Candidate) for item in candidates):
            raise ValueError("Provide 1-32 immutable candidates")
        if len({item.identifier for item in candidates}) != len(candidates):
            raise ValueError("Candidate IDs must be unique")
        started = clock()
        deadline = started+budget.action_seconds
        slack = context.remaining_time_s-context.minimum_task_time_s
        urgent = slack <= policy.urgency_slack_s
        # Urgency changes only order under a finite budget, never risk permission.
        ordered = sorted(candidates, key=lambda item: (item.role != "task", item.time_hint_s)) if urgent else list(candidates)
        records = {item.identifier: {"candidate": record(item), "status": "unexplored",
                                     "reason_codes": ["not_evaluated"], "forecast": None} for item in candidates}
        calls, interruption = 0, authority.check(context.generation, deadline, clock)
        for candidate in ordered:
            if interruption or calls >= budget.max_forecasts:
                break
            interruption = authority.check(context.generation, deadline, clock)
            if interruption:
                break
            calls += 1
            try:
                forecast = forecaster.forecast(context, candidate, deadline=deadline)
                if not isinstance(forecast, ConsequenceForecast):
                    raise ValueError("Provider did not return a consequence forecast")
                evaluated = assess(context, candidate, forecast, policy)
                evaluated["status"] = "constraint_rejected" if evaluated["reason_codes"] else "admissible"
                if not evaluated["reason_codes"]:
                    evaluated["reason_codes"] = ["admissible"]
                records[candidate.identifier].update(evaluated)
            except (ValueError, TypeError, ArithmeticError, RuntimeError, OSError) as error:
                records[candidate.identifier].update(status="forecast_invalid", reason_codes=["forecast_invalid"], error_type=type(error).__name__)
            interruption = authority.check(context.generation, deadline, clock)
        admissible = [item for item in candidates if records[item.identifier]["status"] == "admissible"]
        best = max(admissible, key=lambda item: records[item.identifier]["score"]) if admissible and not interruption else None
        if interruption:
            for row in records.values():
                if row["status"] == "admissible":
                    row.update(status="discarded", reason_codes=[interruption])
        elif best:
            for item in admissible:
                records[item.identifier].update(status="selected" if item == best else "lower_score",
                    reason_codes=["best_admissible_score" if item == best else "lower_score"])
        status = interruption or ("selected" if best else "abstained")
        trace = {"core_version": CORE_VERSION, "context": record(context), "policy": record(policy),
                 "budget": record(budget), "pressure": {"minimum_task_time_slack_s": slack, "urgent": urgent,
                 "candidate_order": [item.identifier for item in ordered], "rule": "shorter task hints first when slack is limited"},
                 "candidates": [records[item.identifier] for item in candidates], "forecast_calls": calls,
                 "decision_ms": (clock()-started)*1000, "status": status,
                 "selected_candidate": best.identifier if best else None,
                 "timing_notice": "Cooperative checks between forecasts and at commit; not preemptive execution",
                 "claim": "Finite declared alternatives; no inner monologue or exhaustive reasoning claim"}
        return Decision(context.generation, deadline, status, best.identifier if best else None,
                        best.action if best else None, trace)
