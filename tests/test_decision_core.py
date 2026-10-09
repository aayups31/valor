import json
from dataclasses import replace

import pytest

from aace.decision import (ActionAuthority, ActionIntent, Candidate, ComputeBudget,
                           ConsequenceForecast, DecisionContext, DecisionEngine,
                           DecisionPolicy, ForecastEvidence)


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now


def context():
    return DecisionContext("generic-test-v1", "observation-0", 0, (("tokens", 10),), 1, 20, 5)


def candidate(name="continue", **kwargs):
    return Candidate(name, ActionIntent(name, (1, 2, 3)), name, 10, **kwargs)


def forecast(ctx, item, **kwargs):
    result = ConsequenceForecast(ctx.observation_id, ctx.generation, item.identifier, item.continuation,
        10, .99, .01, .02, .03, (("tokens", 4),), (("tokens", 2),), 8, .9,
        ForecastEvidence("analytic", "test-equations-v1", ctx.domain, "declared test equations"))
    return replace(result, **kwargs)


class Provider:
    def __init__(self, changes=None):
        self.changes = changes or {}
        self.calls = []

    def forecast(self, ctx, item, *, deadline):
        self.calls.append(item.identifier)
        return forecast(ctx, item, **self.changes.get(item.identifier, {}))


def decide(items, provider=None, **kwargs):
    return DecisionEngine().decide(context(), items, provider or Provider(),
        kwargs.pop("policy", DecisionPolicy(resource_reserves=(("tokens", 1),))),
        kwargs.pop("authority", ActionAuthority()), **kwargs)


def test_general_action_and_one_objective_with_explicit_recovery_margin():
    result = decide((candidate(),))
    row = result.trace["candidates"][0]
    assert result.action.values == (1, 2, 3)  # No 2-D rover action assumption.
    assert row["survival"]["resource_margins"] == {"tokens": 3}
    assert row["score"] == pytest.approx(30*.99-12*.03-40*.01-.1*8)
    assert row["fear"]["qualified"]
    json.dumps(result.trace, allow_nan=False)


@pytest.mark.parametrize("changes,reason", [
    ({"success_probability": .8, "failure_probability": .2, "failure_upper_bound": .25}, "failure_limit"),
    ({"resource_costs": (("tokens", 8),)}, "insufficient_recovery_reserve"),
    ({"recovery_costs": ()}, "unknown_resource_requirements"),
    ({"duration_s": 21, "horizon_s": 25}, "mission_deadline"),
    ({"final_capability": .1}, "capability_floor"),
    ({"horizon_s": 5}, "insufficient_forecast_horizon"),
    ({"continuation": "different"}, "forecast_identity_mismatch"),
    ({"failure_probability": None, "failure_upper_bound": None}, "unknown_consequences"),
    ({"evidence": ForecastEvidence("experimental", "network-v1", "generic-test-v1", "unvalidated")}, "unqualified_forecast"),
    ({"evidence": ForecastEvidence("analytic", "equations-v1", "another-domain", "out of scope")}, "forecast_scope_mismatch"),
])
def test_forecast_cannot_silently_bypass_contract_or_policy(changes, reason):
    result = decide((candidate(),), Provider({"continue": changes}))
    assert result.action is None and result.status == "abstained"
    assert reason in result.trace["candidates"][0]["reason_codes"]


def test_human_authorized_risk_is_not_vetoed_by_an_extra_survival_objective():
    result = decide((candidate(),), Provider({"continue": {"success_probability": .8, "failure_probability": .2, "failure_upper_bound": .25}}),
                    policy=DecisionPolicy(max_failure_probability=.3))
    assert result.status == "selected"
    assert result.trace["policy"]["max_failure_probability"] == .3


def test_pressure_changes_bounded_candidate_order_without_changing_risk_limit():
    ctx = replace(context(), remaining_time_s=6, minimum_task_time_s=5)
    slow, fast = candidate("slow", time_hint_s=9), candidate("fast", time_hint_s=3)
    provider = Provider({"fast": {"duration_s": 3}, "slow": {"duration_s": 9}})
    policy = DecisionPolicy()
    result = DecisionEngine().decide(ctx, (slow, fast), provider, policy, ActionAuthority(), ComputeBudget(max_forecasts=1))
    assert provider.calls == ["fast"] and result.candidate_id == "fast"
    assert result.trace["candidates"][0]["status"] == "unexplored"
    assert result.trace["policy"]["max_failure_probability"] == policy.max_failure_probability


def test_external_stop_during_forecast_discards_proposal_before_commit():
    authority, clock = ActionAuthority(), Clock()
    class StopProvider(Provider):
        def forecast(self, ctx, item, *, deadline):
            authority.stop()
            return forecast(ctx, item)
    result = decide((candidate(),), StopProvider(), authority=authority, clock=clock)
    assert result.status == "external_stop" and result.action is None
    applied = []
    committed = authority.commit(result, applied.append, clock=clock)
    assert committed.status == "external_stop" and not applied


@pytest.mark.parametrize("change,expected", [("late", "action_deadline"), ("new_state", "stale_state")])
def test_late_or_superseded_forecast_is_discarded(change, expected):
    authority, clock = ActionAuthority(), Clock()
    class InterruptedProvider(Provider):
        def forecast(self, ctx, item, *, deadline):
            if change == "late":
                clock.now = deadline+.01
            else:
                authority.supersede()
            return forecast(ctx, item)
    result = decide((candidate(),), InterruptedProvider(), authority=authority, clock=clock)
    assert result.status == expected and result.action is None
    assert result.trace["candidates"][0]["status"] == "discarded"


@pytest.mark.parametrize("change,expected", [("stop", "external_stop"), ("late", "action_deadline"), ("new_state", "stale_state")])
def test_authority_rechecks_after_planning_before_application(change, expected):
    authority, clock = ActionAuthority(), Clock()
    result = decide((candidate(),), authority=authority, clock=clock)
    if change == "stop":
        authority.stop()
    elif change == "late":
        clock.now = result.deadline
    else:
        authority.supersede()
    applied = []
    assert authority.commit(result, applied.append, clock=clock).status == expected
    assert not applied


def test_one_proposal_cannot_be_applied_twice():
    authority, clock = ActionAuthority(), Clock()
    result = decide((candidate(),), authority=authority, clock=clock)
    applied = []
    assert authority.commit(result, applied.append, clock=clock).status == "applied"
    assert authority.commit(result, applied.append, clock=clock).status == "stale_state"
    assert len(applied) == 1


def test_stopped_controller_is_bypassed_and_forecasts_are_not_called():
    authority, provider = ActionAuthority(), Provider()
    authority.stop()
    result = decide((candidate(),), provider, authority=authority)
    assert result.status == "external_stop" and not provider.calls


def test_partial_application_error_invalidates_original_proposal():
    authority, clock = ActionAuthority(), Clock()
    result = decide((candidate(),), authority=authority, clock=clock)
    def failed_apply(action):
        raise RuntimeError("simulated application fault")
    with pytest.raises(RuntimeError):
        authority.commit(result, failed_apply, clock=clock)
    assert authority.snapshot()[0] == 1


def test_invalid_forecasts_are_recorded_and_do_not_hide_other_candidates():
    class BadProvider(Provider):
        def forecast(self, ctx, item, *, deadline):
            return forecast(ctx, item, failure_probability=float("nan")) if item.identifier == "bad" else forecast(ctx, item)
    result = decide((candidate("bad"), candidate("good")), BadProvider())
    assert result.candidate_id == "good"
    assert result.trace["candidates"][0]["status"] == "forecast_invalid"


def test_conflicting_terminal_probabilities_and_mutable_action_are_rejected():
    with pytest.raises(ValueError, match="competing"):
        forecast(context(), candidate(), success_probability=.9, failure_probability=.2, failure_upper_bound=.2)
    with pytest.raises(ValueError):
        ActionIntent("mutate", [1, 2])


def test_provider_runtime_fault_is_recorded_without_applying_an_action():
    class FaultProvider(Provider):
        def forecast(self, ctx, item, *, deadline):
            raise RuntimeError("prediction runtime fault")
    result = decide((candidate(),), FaultProvider())
    assert result.action is None and result.trace["candidates"][0]["error_type"] == "RuntimeError"


def test_forecast_scope_mismatch_never_claims_qualified_threat():
    result = decide((candidate(),), Provider({"continue":{"evidence":ForecastEvidence("analytic","model","other-domain","reference")}}))
    assert not result.trace["candidates"][0]["fear"]["qualified"]


def test_stop_received_from_another_thread_during_forecast_prevents_commit():
    from threading import Event, Thread
    authority, started, release = ActionAuthority(), Event(), Event()
    outputs = []
    class BlockingProvider(Provider):
        def forecast(self, ctx, item, *, deadline):
            started.set()
            assert release.wait(2)
            return forecast(ctx,item)
    thread = Thread(target=lambda:outputs.append(decide((candidate(),),BlockingProvider(),authority=authority,budget=ComputeBudget(action_seconds=3))))
    thread.start()
    assert started.wait(2)
    authority.stop(); release.set(); thread.join(2)
    assert not thread.is_alive() and outputs[0].status == "external_stop"
    applied = []
    assert authority.commit(outputs[0],applied.append,clock=__import__('time').perf_counter).status == "external_stop"
    assert not applied


def test_nested_mutable_policy_and_action_names_are_rejected():
    with pytest.raises(ValueError,match="immutable"):
        DecisionPolicy(resource_reserves=(["tokens",1],))
    with pytest.raises(ValueError,match="immutable"):
        ActionIntent({"name":"continue"})
