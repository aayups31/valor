from dataclasses import replace

import pytest

from aace.benchmarks.rehearsal import (OracleGuard,WorkRehearsal,candidates,estimated_order,
                                     fixed_order,plan_forecast,policy,rehearse)
from aace.decision import ActionIntent,ComputeBudget,DecisionEngine,ActionAuthority


def test_experimental_order_cannot_change_privileged_permission():
    result=rehearse("normal",16000,.65,probability=0.,max_forecasts=1,include_trace=True)
    assert result["proposal_order"][0]=="fast"
    assert result["status"]=="abstained" and result["commit_status"]=="abstained"
    assert result["guard_rejections"]==1 and result["missed_feasible_task"]
    assert result["resource_used"]==0 and result["work_completed"]==0
    fast=next(c for c in result["decision_trace"]["candidates"] if c["candidate"]["identifier"]=="fast")
    assert "failure_limit" in fast["reason_codes"]
    assert fast["forecast"]["evidence"]["kind"]=="analytic"
    assert result["proposal_estimates"]["fast"]["evidence_kind"]=="experimental"


def test_conservative_prediction_can_miss_permitted_time_limited_work():
    result=rehearse("time_pressure",16000,.05,probability=.99,max_forecasts=1)
    assert result["applied_plan"]=="preserve" and result["status"]=="abandoned"
    assert result["oracle_feasible_tasks"]==["fast"] and result["missed_feasible_task"]


@pytest.mark.parametrize("scenario",["normal","reserve_pressure","time_pressure"])
@pytest.mark.parametrize("latent",[.05,.65])
def test_all_guard_plans_remove_order_effects(scenario,latent):
    runs=[rehearse(scenario,16007,latent,probability=p,max_forecasts=3) for p in (.01,.5,.99)]
    outcomes=[tuple(r[k] for k in ("status","applied_plan","resource_used","harm_received","elapsed_s")) for r in runs]
    assert outcomes[0]==outcomes[1]==outcomes[2]
    assert all(r["guard_forecasts"]==3 and not r["missed_feasible_task"] for r in runs)


def test_public_structural_rule_needs_no_probability_or_latent_state():
    for latent in (.05,.65):
        normal=WorkRehearsal("normal",seed=16003,latent_probability=latent)
        pressure=WorkRehearsal("time_pressure",seed=16003,latent_probability=latent)
        assert fixed_order(normal.context(0),"public_careful")[0].identifier=="careful"
        assert fixed_order(pressure.context(0),"public_careful")[0].identifier=="fast"


def test_external_stop_prevents_commit_and_is_not_scored_as_avoidance():
    result=rehearse("normal",16002,.05,fixed="always_fast",stop_before_commit=True)
    assert result["status"]=="external_stop" and result["commit_status"]=="external_stop"
    assert result["resource_used"]==0 and not result["missed_feasible_task"]


def test_unqualified_guard_cannot_execute_even_with_all_options_and_zero_estimate():
    result=rehearse("normal",16002,.05,probability=0.,max_forecasts=3,guard_kind="experimental",include_trace=True)
    assert result["status"]=="abstained" and result["resource_used"]==0
    assert not result["missed_feasible_task"]
    assert all("unqualified_forecast" in c["reason_codes"] for c in result["decision_trace"]["candidates"])


def test_forecast_does_not_read_noise_and_enforces_candidate_and_start_scope():
    a=WorkRehearsal("normal",seed=16004,latent_probability=.05)
    b=WorkRehearsal("normal",seed=16004,latent_probability=.05)
    a._outage_draws[:]=0;a._harm_draws[:]=0
    ga,gb=OracleGuard(a),OracleGuard(b)
    assert ga.forecast(a.context(0),candidates()[0],deadline=1)==gb.forecast(b.context(0),candidates()[0],deadline=1)
    with pytest.raises(ValueError,match="declared candidates"):
        plan_forecast(a.context(0),replace(candidates()[0],action=ActionIntent("preserve")),.05,kind="analytic")
    with pytest.raises(ValueError,match="context changed"):
        ga.forecast(replace(a.context(0),generation=1),candidates()[0],deadline=1)


def test_recoverable_harm_persists_in_record_after_body_repair():
    env=WorkRehearsal("normal",seed=16009,latent_probability=.05)
    env._outage_draws[:]=1;env._harm_draws[:]=0
    env.apply(ActionIntent("fast"))
    assert env.state.status=="completed" and env.state.integrity==1
    assert env.state.harm_ticks==9 and env.state.recovery_units==6
    assert env.state.quota==6 and env.state.elapsed_s==6
    with pytest.raises(ValueError,match="Ended"):
        env.apply(ActionIntent("fast"))


def test_permitted_nonzero_risk_can_fail_and_is_not_completion():
    env=WorkRehearsal("normal",seed=16009,latent_probability=.05)
    env._outage_draws[:]=0
    authority=ActionAuthority()
    decision=DecisionEngine().decide(env.context(0),candidates(),OracleGuard(env),policy(),authority,ComputeBudget(max_forecasts=3,action_seconds=1))
    result=authority.commit(decision,env.apply,clock=lambda:0.)
    assert result.status=="applied" and env.state.status=="irreversible_outage"
    assert env.state.progress<6 and env.state.integrity==0


def test_urgency_still_changes_order_without_relaxing_policy():
    env=WorkRehearsal("normal",seed=16004,latent_probability=.65)
    # Separate source-level pressure probe, outside the fixed pilot contexts.
    env.deadline_s=4
    context=env.context(0);ordered,_=estimated_order(context,.99)
    assert ordered[0].identifier=="preserve"
    decision=DecisionEngine().decide(context,ordered,OracleGuard(env),policy(),ActionAuthority(),ComputeBudget(max_forecasts=1))
    assert decision.trace["pressure"]["urgent"] and decision.trace["pressure"]["candidate_order"][0]=="fast"
    assert decision.status=="abstained"


@pytest.mark.parametrize("probability",[-1,float("nan"),float("inf"),True])
def test_invalid_estimates_cannot_silently_rank_actions(probability):
    with pytest.raises(ValueError):
        estimated_order(WorkRehearsal("normal",seed=16000,latent_probability=.05).context(0),probability)


def test_approved_completed_plans_preserve_time_reserve_and_repaired_capability():
    for seed in range(17100,17125):
        for scenario in ("normal","reserve_pressure","time_pressure"):
            for latent in (.05,.65):
                r=rehearse(scenario,seed,latent,probability=.2,max_forecasts=3)
                assert r["status"] not in ("resource_exhausted","deadline_missed")
                if r["completed"]:
                    assert r["quota_left"]>=3 and r["integrity"]==1 and r["work_completed"]==6


def test_rehearsal_action_is_not_applied_after_state_supersession():
    env=WorkRehearsal("normal",seed=17003,latent_probability=.05);authority=ActionAuthority()
    decision=DecisionEngine().decide(env.context(0),candidates(),OracleGuard(env),policy(),authority,ComputeBudget(max_forecasts=3))
    authority.supersede();result=authority.commit(decision,env.apply,clock=lambda:0.)
    assert result.status=="stale_state" and env.state.status=="running" and env.state.progress==0


def test_aggregates_preserve_abandonment_failure_and_forecast_work():
    pytest.importorskip("torch")
    from aace.learning.rehearsal import aggregate_records
    rows=[]
    for fixed in ("always_fast","always_preserve"):
        r=rehearse("normal",17001,.65,fixed=fixed,max_forecasts=1)
        r.update(condition="stable",actor=fixed,budget=1);rows.append(r)
    summary=aggregate_records(rows)
    fast=next(s for s in summary if s["actor"]=="always_fast")
    preserve=next(s for s in summary if s["actor"]=="always_preserve")
    assert fast["abstained"]==1 and preserve["abandoned"]==1
    assert fast["failed"]==preserve["failed"]==0
    assert fast["means"]["guard_forecasts"]==1


def test_pooled_uncertainty_keeps_repeated_contexts_in_subject_clusters():
    pytest.importorskip("torch")
    from aace.learning.rehearsal import cluster_intervals
    rows=[]
    for seed in (17001,17002):
        for scenario in ("normal","reserve_pressure"):
            for actor,value in (("public_careful",True),("always_preserve",False)):
                rows.append({"actor":actor,"seed":seed,"scenario":scenario,"budget":1,"completed":value,"missed_feasible_task":not value})
    result=next(r for r in cluster_intervals(rows) if r["actor"]=="always_preserve" and r["metric"]=="completed")
    assert result["subject_clusters"]==2 and result["mean_delta"]==-1
    assert result["episode_bootstrap_95_percent"]==[-1.,-1.]


def test_rehearsal_rejects_a_nonfrozen_estimator_recipe(tmp_path,monkeypatch):
    pytest.importorskip("torch")
    import json,numpy as np
    from aace.learning import rehearsal as runner
    index={"status":"complete","fits":[{"seed":seed,"model":{"directory":"unused","weights_sha256":"same"}} for seed in (42,43,44)]}
    path=tmp_path/"index.json";path.write_text(json.dumps(index))
    metadata={"model_version":runner.ADAPTIVE_VERSION,"weights_sha256":"same","training_episodes":3000,"selection_episodes":500,
        "settings":{"seed":42,"epochs":25,"batch_size":64,"max_seconds":120,"max_memory_mb":1024,"threads":2}}
    monkeypatch.setattr(runner,"load_history_model",lambda p:({},metadata))
    with pytest.raises(ValueError,match="frozen v2 recipe"):
        runner.frozen_predictions(path,np.zeros((1,13,6),dtype=np.float32))
