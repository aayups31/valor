"""Offline proposal/guard rehearsal. No real services, devices or model authority."""

import math
import time
from dataclasses import asdict,dataclass,replace

import numpy as np

from aace.decision import (ActionAuthority,ActionIntent,Candidate,ComputeBudget,ConsequenceForecast,
                          DecisionContext,DecisionEngine,DecisionPolicy,ForecastEvidence)
from aace.decision.engine import assess

DOMAIN="guarded-work-rehearsal-v1"
SCENARIOS={"normal":(18,16),"reserve_pressure":(14,16),"time_pressure":(18,6)}
FIXED_ORDERS={"always_fast":("fast","careful","preserve"),
              "always_careful":("careful","fast","preserve"),
              "always_preserve":("preserve","careful","fast")}


@dataclass(frozen=True)
class WorkState:
    quota: float
    integrity: float=1
    progress: int=0
    elapsed_s: float=0
    status: str="running"
    harm_ticks: int=0
    recovery_units: int=0
    processing_operations: int=0


def policy():
    return DecisionPolicy(max_failure_probability=.05,resource_reserves=(("work_quota",3),))


def candidates():
    return (Candidate("fast",ActionIntent("fast"),"fast_process_then_repair",6,time_hint_s=6),
            Candidate("careful",ActionIntent("careful"),"careful_process_then_repair",14,time_hint_s=14),
            Candidate("preserve",ActionIntent("preserve"),"abandon_this_task",1,role="preserve"))


def operation(name, probability):
    if name=="fast":
        return 3,2,1,2,.05*probability,probability,3
    if name=="careful":
        return 6,1,2,1,.005*probability,.1*probability,1
    raise ValueError("Unknown rehearsal task operation")


def plan_forecast(context,candidate,probability,*,kind="experimental"):
    if context.domain!=DOMAIN or type(probability) not in (int,float) or not math.isfinite(probability) or not 0<=probability<=1:
        raise ValueError("Invalid rehearsal forecast scope/probability")
    if candidate not in candidates() or context.capability!=1:
        raise ValueError("Rehearsal forecast requires declared candidates and a repaired starting body")
    if candidate.identifier=="preserve":
        success,failure,harm,processing,recovery,duration=0.,0.,0.,0.,0.,0.
    else:
        count,_,seconds,cost,outage,damage,ticks=operation(candidate.identifier,probability)
        stages=(count*ticks+2)//3
        duration=count*seconds+stages
        processing=count*cost;recovery=stages*2
        survival=(1-outage)**count
        success,failure=survival,1-survival
        harm=min(1,count*damage*ticks*.05)*survival
    return ConsequenceForecast(context.observation_id,context.generation,candidate.identifier,candidate.continuation,
        candidate.horizon_s,success,failure,failure,harm,(("work_quota",processing),),(("work_quota",recovery),),
        duration,1.,ForecastEvidence(kind,DOMAIN,DOMAIN,
            "privileged latent cue probability and declared equations; no future draws" if kind=="analytic"
            else "experimental cue estimate for proposal ordering only"))


class WorkRehearsal:
    def __init__(self,scenario,*,seed,latent_probability):
        if scenario not in SCENARIOS or type(seed) is not int or not 0<=seed<2**31 or latent_probability not in (.05,.65):
            raise ValueError("Invalid rehearsal scenario/seed/latent probability")
        quota,self.deadline_s=SCENARIOS[scenario]
        self.state=WorkState(quota=quota)
        self._latent_probability=float(latent_probability)
        rng=np.random.default_rng(np.random.SeedSequence([seed,731113]))
        # Same indexed independent outage/harm streams for each actor and scene.
        self._outage_draws=rng.random(6);self._harm_draws=rng.random(6)

    def context(self,generation):
        return DecisionContext(DOMAIN,f"rehearsal-{generation}",generation,(("work_quota",self.state.quota),),
            self.state.integrity,max(0,self.deadline_s-self.state.elapsed_s),3.)

    def apply(self,action):
        if self.state.status!="running" or action.values or action.name not in ("fast","careful","preserve"):
            raise ValueError("Ended rehearsal or unsupported action")
        if action.name=="preserve":
            self.state=replace(self.state,status="abandoned");return
        state=self.state
        count,amount,seconds,cost,outage,damage,ticks=operation(action.name,self._latent_probability)
        for index in range(count):
            state=replace(state,quota=state.quota-cost,elapsed_s=state.elapsed_s+seconds,
                          processing_operations=state.processing_operations+1)
            if state.quota<0 or state.elapsed_s>self.deadline_s:
                self.state=replace(state,status="resource_exhausted" if state.quota<0 else "deadline_missed");return
            if self._outage_draws[index]<outage:
                self.state=replace(state,integrity=0,status="irreversible_outage");return
            new_ticks=state.harm_ticks+(ticks if self._harm_draws[index]<damage else 0)
            state=replace(state,harm_ticks=new_ticks,integrity=1-new_ticks*.05,progress=state.progress+amount)
        stages=(state.harm_ticks+2)//3
        state=replace(state,quota=state.quota-stages*2,elapsed_s=state.elapsed_s+stages,recovery_units=stages*2)
        if state.quota<0 or state.elapsed_s>self.deadline_s:
            self.state=replace(state,status="resource_exhausted" if state.quota<0 else "deadline_missed");return
        self.state=replace(state,integrity=1,status="completed")


class OracleGuard:
    """Labeled simulator oracle: actual latent p, never an actual future draw."""
    def __init__(self,environment,kind="analytic"):
        if environment.state.status!="running" or environment.state.progress!=0:
            raise ValueError("Rehearsal guard requires an untouched task")
        self._probability=environment._latent_probability
        self._context=environment.context(0)
        self.kind=kind;self.calls=0

    def forecast(self,context,candidate,*,deadline):
        if context!=self._context:
            raise ValueError("Rehearsal guard context changed")
        self.calls+=1
        return plan_forecast(context,candidate,self._probability,kind=self.kind)


def estimated_order(context,probability):
    """Pure public-context/prediction interface. Experimental evidence cannot act."""
    proposals=candidates();rows={}
    for candidate in proposals:
        forecast=plan_forecast(context,candidate,probability)
        # Calculate estimated constraints/objective without mislabeling evidence
        # as qualified. These calculations never enter DecisionEngine permission.
        costs=dict(forecast.resource_costs);recovery=dict(forecast.recovery_costs)
        reasons=[]
        if forecast.failure_upper_bound>policy().max_failure_probability:reasons.append("estimated_failure_limit")
        if dict(context.resources)["work_quota"]-costs["work_quota"]-recovery["work_quota"]<3:reasons.append("estimated_reserve")
        if forecast.duration_s>context.remaining_time_s:reasons.append("estimated_time")
        p=policy()
        score=p.task_value*forecast.success_probability-p.failure_cost*forecast.failure_probability-p.recoverable_damage_cost*forecast.recoverable_damage-p.time_cost*forecast.duration_s
        rows[candidate.identifier]={"score":score,"estimated_rejections":reasons,"evidence_kind":"experimental"}
    ordered=tuple(sorted(proposals,key=lambda c:(bool(rows[c.identifier]["estimated_rejections"]),-rows[c.identifier]["score"])))
    return ordered,rows


def fixed_order(context,name):
    by_id={c.identifier:c for c in candidates()}
    if name=="public_careful":
        good,bad=[],[]
        for identifier in ("careful","fast","preserve"):
            candidate=by_id[identifier]
            f=plan_forecast(context,candidate,0.)
            structural=(f.duration_s<=context.remaining_time_s and dict(context.resources)["work_quota"]-dict(f.resource_costs)["work_quota"]-dict(f.recovery_costs)["work_quota"]>=3)
            (good if structural else bad).append(candidate)
        return tuple(good+bad)
    if name not in FIXED_ORDERS:
        raise ValueError("Unknown fixed rehearsal order")
    return tuple(by_id[x] for x in FIXED_ORDERS[name])


def rehearse(scenario,seed,latent_probability,*,probability=None,fixed=None,max_forecasts=1,
             stop_before_commit=False,guard_kind="analytic",include_trace=False):
    if (probability is None)==(fixed is None):
        raise ValueError("Choose one probability estimator or fixed rule")
    environment=WorkRehearsal(scenario,seed=seed,latent_probability=latent_probability)
    authority=ActionAuthority();context=environment.context(authority.snapshot()[0])
    began=time.perf_counter()
    if fixed is None:
        ordered,proposal_rows=estimated_order(context,probability)
        proposal_transforms=3
    else:
        ordered=fixed_order(context,fixed);proposal_rows={};proposal_transforms=3 if fixed=="public_careful" else 0
    proposal_ms=1000*(time.perf_counter()-began)
    guard=OracleGuard(environment,guard_kind)
    decision=DecisionEngine().decide(context,ordered,guard,policy(),authority,ComputeBudget(max_forecasts=max_forecasts,action_seconds=.5))
    if stop_before_commit:authority.stop()
    commit=authority.commit(decision,environment.apply,clock=time.perf_counter)
    if commit.status!="applied":
        environment.state=replace(environment.state,status="abstained" if commit.status=="abstained" else commit.status)
    # Retrospective oracle assessment is diagnostic, separate from actor/guard work.
    audit={c.identifier:assess(context,c,plan_forecast(context,c,latent_probability,kind="analytic"),policy()) for c in candidates()}
    feasible=[name for name in ("fast","careful") if not audit[name]["reason_codes"]]
    state=environment.state
    missed=bool(feasible) and state.status in ("abandoned","abstained") and guard_kind=="analytic"
    result={"scenario":scenario,"seed":seed,"status":state.status,"completed":state.status=="completed",
        "failed":state.status in ("irreversible_outage","resource_exhausted","deadline_missed"),"harm_received":state.harm_ticks*.05,
        "recovery_units":state.recovery_units,"resource_used":SCENARIOS[scenario][0]-state.quota,
        "elapsed_s":state.elapsed_s,"work_completed":state.progress,"integrity":state.integrity,
        "quota_left":state.quota,"missed_feasible_task":missed,"oracle_feasible_tasks":feasible,
        "applied_plan":decision.candidate_id if commit.status=="applied" else None,"commit_status":commit.status,
        "estimated_probability":probability,"proposal_order":[c.identifier for c in ordered],
        "guard_order":decision.trace["pressure"]["candidate_order"],"urgent":decision.trace["pressure"]["urgent"],
        "urgency_overrode_order":[c.identifier for c in ordered]!=decision.trace["pressure"]["candidate_order"],
        "guard_forecasts":guard.calls,"proposal_transforms":proposal_transforms,"retrospective_forecasts":3,
        "guard_rejections":sum(r["status"]=="constraint_rejected" for r in decision.trace["candidates"]),
        "decision_ms":decision.trace["decision_ms"],"proposal_ms":proposal_ms,
        "guard_notice":"Privileged latent-state analytic simulator guard; no future draws; not a deployment certificate",
        "prediction_notice":"Frozen experimental cue estimates rank proposals only; not used as qualified guard evidence"}
    if include_trace:
        result.update(decision_trace=decision.trace,proposal_estimates=proposal_rows,
                      retrospective_audit=audit,actual_state=asdict(state))
    return result
