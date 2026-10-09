"""Bounded, replayable engineering checks across VALOR benchmark adapters."""

import json
import time
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from aace.benchmarks.service import SCENARIOS, ServiceForecaster, ServiceWorkflow, state_record
from aace.decision import ActionAuthority, ComputeBudget, DecisionEngine
from aace.telemetry import source_provenance


def service_episode(scenario="hazard", *, seed=42, budget=None):
    budget = budget or ComputeBudget()
    environment, authority, engine = ServiceWorkflow(scenario, seed=seed), ActionAuthority(), DecisionEngine()
    records = []
    reason = None
    for _ in range(32):
        if environment.state.status != "running":
            break
        generation, _ = authority.snapshot()
        context = environment.context(generation)
        forecaster = ServiceForecaster(environment)
        decision = engine.decide(context, environment.candidates(), forecaster, environment.policy(), authority, budget)
        committed = authority.commit(decision, environment.apply, clock=time.perf_counter)
        records.append({"decision": decision.trace, "proposed_action": asdict(decision.action) if decision.action else None,
                        "commit": asdict(committed), "actual_outcome": state_record(environment),
                        "analytic_operation_evaluations": forecaster.operation_evaluations})
        if committed.status != "applied":
            reason = committed.status
            break
    status = environment.state.status if environment.state.status != "running" else reason or "step_budget"
    return {"domain": "service-workflow-v1", "scenario": scenario, "seed": seed,
            "status": status, "completed": status == "completed", "irreversible_failure": status == "irreversible_outage",
            "abandoned": status == "abandoned", "state": state_record(environment),
            "forecast_calls": sum(row["decision"]["forecast_calls"] for row in records),
            "analytic_operation_evaluations": sum(row["analytic_operation_evaluations"] for row in records),
            "decisions": records}


def rover_probe(scenario="shortcut", *, seed=42, budget=None):
    from aace.benchmarks.rover import RoverDecisionAdapter
    from aace.envs.rover import RoverEnv
    environment = RoverEnv(scenario)
    environment.reset(seed=seed)
    adapter = RoverDecisionAdapter(environment, seed=seed)
    result = DecisionEngine().decide(adapter.context(0), adapter.candidates(), adapter, adapter.policy(),
                                     ActionAuthority(), budget or ComputeBudget(action_seconds=2))
    return {"domain": "rover-public-v1", "scenario": scenario, "seed": seed,
            "status": result.status, "action_applied": False, "decision": result.trace,
            "branch_transitions": adapter.branch_transitions,
            "notice": "Public adapter check only. Coarse forecast evidence is unqualified; no rover action is applied."}


def export_example(domain, scenario, seed, output: Path, *, budget=None):
    provenance = source_provenance()
    if domain == "service":
        result = service_episode(scenario, seed=seed, budget=budget)
    elif domain == "rover":
        result = rover_probe(scenario, seed=seed, budget=budget)
    else:
        raise ValueError("Unknown benchmark domain")
    output.mkdir(parents=True, exist_ok=True)
    destination = output/f"core-example-{uuid4().hex[:8]}.json"
    report = {"protocol": "engineering example; no learned transfer or AACE advantage claim",
              "forecast_source": "analytic benchmark equations" if domain == "service" else "unqualified oracle samples",
              **provenance, **result}
    destination.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return {k: value for k, value in dict(report, report_file=str(destination.resolve())).items() if k not in ("decision", "decisions")}


def evaluate_service(output: Path, *, episodes=20, seed_start=10000, budget=None):
    if type(episodes) is not int or not 1 <= episodes <= 100 or type(seed_start) is not int or not 0 <= seed_start < 20000 or seed_start+episodes > 20000:
        raise ValueError("Use 1-100 development episodes below reserved seed 20000")
    started, provenance = time.perf_counter(), source_provenance()
    scenarios = {}
    for scenario in SCENARIOS:
        runs = [service_episode(scenario, seed=seed_start+i, budget=budget) for i in range(episodes)]
        summaries = [{key: value for key, value in run.items() if key != "decisions"} for run in runs]
        status_counts = {}
        for run in runs:
            status_counts[run["status"]] = status_counts.get(run["status"], 0)+1
        # Outcomes are scored, not inferred from a selected/predicted plan.
        scenarios[scenario] = {"episodes": summaries, "status_counts": status_counts,
            "completion_rate": sum(run["completed"] for run in runs)/episodes,
            "irreversible_failure_rate": sum(run["irreversible_failure"] for run in runs)/episodes,
            "abandonment_rate": sum(run["abandoned"] for run in runs)/episodes,
            "forecast_calls": sum(run["forecast_calls"] for run in runs),
            "analytic_operation_evaluations": sum(run["analytic_operation_evaluations"] for run in runs)}
    report = {"protocol": "development engineering sweep; one fixed algorithm and analytic model, no research comparison",
              "domain": "service-workflow-v1", "seeds": list(range(seed_start, seed_start+episodes)),
              "budget": asdict(budget or ComputeBudget()), "forecast_source": "known analytic simulation equations",
              "scenarios": scenarios, "elapsed_s": time.perf_counter()-started, **provenance,
              "external_spend_usd": 0,
              "limitations": ["Synthetic service dynamics and fixed primitives; no real services controlled",
                              "No independent trained-model replications or AACE memory", "Abandonment is not completion",
                              "Shared seeds use decision-indexed random event draws; differing action sequences alter exposure"]}
    output.mkdir(parents=True, exist_ok=True)
    destination = output/f"core-evaluation-{uuid4().hex[:8]}.json"
    destination.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return {"report_file": str(destination.resolve()), "elapsed_s": report["elapsed_s"],
            "scenarios": {name: {k: v for k, v in summary.items() if k != "episodes"} for name, summary in scenarios.items()}}
