"""Run the frozen local cascade comparison and export decision evidence."""

import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.benchmarks.cascade import (
    ACTORS, HIGH, LOW, STAKES, ReleasePlanner, ReleaseState, available, terminal_outcomes, transition,
)
from aace.telemetry import source_provenance

PROTOCOL = "persistent-damage-paired-stakes-v1"
SEEDS = range(90000, 90256)
SMOKE_SEEDS = range(91000, 91008)


def subject(seed):
    regime, history, live = (np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(3))
    actual = HIGH if regime.integers(2) else LOW
    return actual, tuple(bool(x) for x in history.random(8) < actual), live.random(3)


def outcome_record(outcomes):
    return {**asdict(outcomes), "score": outcomes.score}


def decision_record(planner, state):
    choices = planner.alternatives(state)
    selected, _ = planner.decide(state)
    return {
        "before": asdict(state),
        "stakes": planner.stakes,
        "history_shocks": planner.historical_shocks if planner.actor in ("history", "adaptive") else None,
        "live_evidence_used": planner.actor == "adaptive",
        "next_fast_shock_probability": planner.danger(state),
        "excluded_legal_actions": {a: "excluded by careful-only control" for a in available(state) if a not in choices},
        "selected": selected,
        "selection_rule": "highest expected total score; ties use declared action order",
        "alternatives": {
            action: {
                "expected": outcome_record(outcomes),
                "immediate_branches": [
                    {"probability": p, "shock": shock, "state": asdict(after),
                     "next_action_if_observed": planner.decide(after)[0] if after.status == "running" else None}
                    for p, shock, after in planner.branches(state, action)
                ],
            }
            for action, outcomes in choices.items()
        },
        "authority": "simulation only",
    }


def play(planner, actual, draws, *, trace=False):
    state = ReleaseState()
    decisions = []
    first_action, forecast = planner.decide(state)
    while state.status == "running":
        action, _ = planner.decide(state)
        evidence = decision_record(planner, state) if trace else None
        shock = action == "fast" and bool(draws[state.attempts] < actual)
        state = transition(state, action, shock=shock)
        if evidence is not None:
            decisions.append({**evidence, "observed_shock": shock if action == "fast" else None,
                              "observed_after": asdict(state)})
    return {
        "actor": planner.actor, "stakes": planner.stakes, "first_action": first_action,
        "predicted_from_start": outcome_record(forecast), "terminal_state": asdict(state),
        "realized": outcome_record(terminal_outcomes(state, planner.stakes)),
        **({"decisions": decisions} if trace else {}),
    }


def witnesses():
    start = ReleaseState()
    late = start
    for _ in range(2):
        late = transition(transition(late, "fast", shock=True), "repair")
    return {
        "scope": "deterministic engineering examples, not held-out research results",
        "paired_start": [
            decision_record(ReleasePlanner("adaptive", stakes, 2), start) for stakes in STAKES
        ],
        "paired_last_tick": [
            decision_record(ReleasePlanner("adaptive", stakes, 2), late) for stakes in STAKES
        ],
        "last_tick_provenance": "fast with shock, repair, fast with shock, repair; forced reachable state",
    }


def paired_interval(deltas):
    values = np.asarray(deltas, dtype=float)
    rng = np.random.default_rng(28113)
    means = values[rng.integers(0, len(values), size=(2000, len(values)))].mean(axis=1)
    return {"mean_delta": float(values.mean()), "bootstrap_95_percent": np.quantile(means, [.025, .975]).tolist(),
            "subjects": len(values), "notice": "Paired subject bootstrap, descriptive development check"}


def metrics(row):
    actual = row["realized"]
    return {**actual, "failure": actual["outage"]+actual["release_failure"]}


def summarize(episodes, seeds):
    by_key = {(r["seed"], r["stakes"], r["actor"]): r for r in episodes}
    if len(episodes) != len(seeds)*len(STAKES)*len(ACTORS) or len(by_key) != len(episodes):
        raise ValueError("Incomplete or duplicate paired episodes")
    summary, comparisons, switches = [], [], []
    for stakes in STAKES:
        for actor in ACTORS:
            rows = [metrics(by_key[seed, stakes, actor]) for seed in seeds]
            summary.append({"stakes": stakes, "actor": actor,
                            "means": {key: sum(r[key] for r in rows)/len(rows) for key in rows[0]}})
        for control in ("fixed", "history"):
            comparisons.append({"stakes": stakes, "control": control, "adaptive_minus_control": {
                key: paired_interval([
                    metrics(by_key[seed, stakes, "adaptive"])[key]-metrics(by_key[seed, stakes, control])[key]
                    for seed in seeds
                ]) for key in ("score", "completed", "failure", "shocks", "incidents")
            }})
    for actor in ACTORS:
        counts = {}
        for seed in seeds:
            pair = f"{by_key[seed, STAKES[0], actor]['first_action']} -> {by_key[seed, STAKES[1], actor]['first_action']}"
            counts[pair] = counts.get(pair, 0)+1
        switches.append({"actor": actor, "low_to_high_stakes_first_action": counts})
    return summary, comparisons, switches


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cascade(output: Path, *, smoke=False):
    started = time.perf_counter()
    provenance = source_provenance()
    seeds = SMOKE_SEEDS if smoke else SEEDS
    planners = {}
    episodes = []
    for seed in seeds:
        actual, history, draws = subject(seed)
        for stakes in STAKES:
            for actor in ACTORS:
                observed = sum(history) if actor in ("history", "adaptive") else 0
                privileged = actual if actor == "oracle" else None
                key = actor, stakes, observed, privileged
                if key not in planners:
                    planners[key] = ReleasePlanner(actor, stakes, observed, oracle_danger=privileged)
                row = play(planners[key], actual, draws, trace=seed == seeds.start)
                episodes.append({**row, "seed": seed, "history_observations": history,
                                 "audit_actual_danger": actual})
    summary, comparisons, switches = summarize(episodes, seeds)
    directory = output/f"{'smoke' if smoke else 'pilot'}-cascade-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    episode_hash = write_json(directory/"episodes.json", episodes)
    witness_hash = write_json(directory/"witnesses.json", witnesses())
    report = {
        "protocol": PROTOCOL, "engineering": smoke, "subjects": len(seeds),
        "seed_range_inclusive": [seeds.start, seeds.stop-1], "episodes": len(episodes),
        "stakes": STAKES, "actors": ACTORS, "summary": summary, "paired_comparisons": comparisons,
        "stake_switches": switches,
        "search_work": [{"actor": k[0], "stakes": k[1], "history_shocks": k[2], "oracle_danger": k[3],
                         "unique_states_solved": p.work()} for k, p in planners.items()],
        "work_notice": "Caches shared only within a fixed actor/objective/history/danger scope; counts are unique states, not matched compute",
        "episode_sha256": episode_hash, "witness_sha256": witness_hash,
        "elapsed_s": time.perf_counter()-started, "external_spend_usd": 0,
        "decision_ready": False, "scope": "Simulated fixture, no learned weights, no external action authority",
        **provenance,
    }
    write_json(directory/"report.json", report)
    return {**report, "directory": str(directory.resolve())}
