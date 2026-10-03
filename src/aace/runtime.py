"""One engine shared by CLI experiments and local demo sessions."""

import json
from math import isfinite
import subprocess
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from aace.controllers import HeuristicController, Proposal, brake
from aace.envs.rover import RoverEnv
from aace.planning import guard_action
from aace.schemas import SCHEMA_VERSION
from aace.telemetry import explain, source_provenance


def trace_action(action):
    """Keep invalid commands inspectable in strict JSON without NaN literals."""
    try:
        return tuple(float(v) if isfinite(float(v)) else None for v in action)
    except (TypeError, ValueError, OverflowError):
        return None


def make_controller(name: str, env: RoverEnv, seed: int):
    if name in ("heuristic_direct", "heuristic_detour"):
        return HeuristicController(detour=name == "heuristic_detour")
    if name == "oracle_planner":
        from aace.forecasting import OraclePlanner
        return OraclePlanner(env.config, seed=seed)
    raise ValueError(f"Unknown controller {name!r}")


class Session:
    def __init__(self, scenario: str = "shortcut", controller: str = "heuristic_direct", seed: int = 0):
        self.env = RoverEnv(scenario)
        self.env.reset(seed=seed)
        self.controller = make_controller(controller, self.env, seed)
        self.seed = seed
        self.run_id = uuid4().hex[:12]
        self.records: list[dict] = []
        self.path = [[self.env.state.x, self.env.state.y]]
        self.total_reward = 0.0
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.provenance = source_provenance()

    @property
    def ended(self) -> bool:
        return self.env.state.status != "running"

    def step(self, *, external_stop: bool = False) -> dict:
        if self.ended:
            raise RuntimeError("Session ended; create a new session")
        observation = self.env.observe()
        started = time.perf_counter()
        if external_stop:
            command = brake(observation)
            proposal = Proposal("brake", command, ({"plan": "brake", "action": command,
                                "status": "selected", "reason_codes": ["external_stop"],
                                "forecast": None},))
        else:
            proposal = self.controller.decide(observation)
        guard = guard_action(proposal.action, observation, external_stop=external_stop)
        elapsed_ms = 1000*(time.perf_counter()-started)
        _, reward, terminated, truncated, info = self.env.step(guard.action)
        self.total_reward += reward
        self.path.append([self.env.state.x, self.env.state.y])
        candidates = [dict(item, action=trace_action(item["action"]),
                           explanations=explain(item["reason_codes"])) for item in proposal.candidates]
        if guard.reason and not external_stop:
            for candidate in candidates:
                if candidate["plan"] == proposal.plan:
                    candidate["status_before_guard"] = candidate["status"]
                    candidate["status"] = "guard_overridden"
        record = {"schema_version": SCHEMA_VERSION, "run_id": self.run_id,
                  "step": observation.state.step, "observation": observation.to_dict(),
                  "controller": self.controller.name, "forecast_source": proposal.forecast_source,
                  "candidates": candidates, "selected_plan": proposal.plan,
                  "proposed_action": None if external_stop else trace_action(proposal.action),
                  "proposed_action_valid": not external_stop and guard.reason != "invalid_action",
                  "raw_invalid_action": repr(proposal.action) if guard.reason == "invalid_action" else None,
                  "controller_bypassed": external_stop, "applied_action": guard.action,
                  "guard_reason": guard.reason,
                  "guard_explanation": explain([guard.reason]) if guard.reason else [],
                  "decision_ms": elapsed_ms, "branch_transitions": proposal.branch_transitions,
                  "actual_outcome": {"state": self.env.state.to_dict(), "reward": reward,
                                     "terminated": terminated, "truncated": truncated,
                                     "events": info["events"]}}
        json.dumps(record, allow_nan=False)  # Reject unexportable traces at the source.
        self.records.append(record)
        return record

    def view(self) -> dict:
        return {"run_id": self.run_id, "seed": self.seed, "controller": self.controller.name,
                "scenario": self.env.scenario.name, "observation": self.env.observe().to_dict(),
                "path": list(self.path), "ended": self.ended, "total_reward": self.total_reward,
                "latest_decision": self.records[-1] if self.records else None}

    def summary(self) -> dict:
        import numpy as np
        latencies = [r["decision_ms"] for r in self.records]
        state = self.env.state
        return {"run_id": self.run_id, "scenario": self.env.scenario.name,
                "controller": self.controller.name, "seed": self.seed,
                "status": state.status, "steps": state.step, "health": state.health,
                "battery": state.battery, "inspected": state.inspected,
                "completed": state.status == "completed",
                "catastrophe": state.status in ("actuator_loss", "battery_depleted"),
                "total_reward": self.total_reward,
                "branch_transitions": sum(r["branch_transitions"] for r in self.records),
                "latency_ms": dict(zip(("p50", "p95", "p99"),
                                       np.percentile(latencies, [50, 95, 99]).tolist())) if latencies else {}}

    def export(self, directory: str | Path) -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory/f"{self.run_id}.json"
        header = {"schema_version": SCHEMA_VERSION, "created_at_utc": self.started_at,
                  **self.provenance,
                  "config": asdict(self.env.config), "scenario": asdict(self.env.scenario),
                  "observation_permission": "fully_observed_v1",
                  "claim": "engineering replay; no validated AACE advantage"}
        with destination.open("x", encoding="utf-8") as stream:
            json.dump({"header": header, "summary": self.summary(), "decisions": self.records},
                      stream, indent=2, allow_nan=False)
        return destination
