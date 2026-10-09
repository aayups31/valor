"""Observed continuation outcomes for the first non-robotic learned threat head."""

import json
import time
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.benchmarks.service import DOMAIN, ServiceForecaster, ServiceState, ServiceWorkflow
from aace.learning.resources import digest
from aace.learning.threat_data import SPLITS, load_threat
from aace.telemetry import source_provenance

CODEC = "service-candidate-features-v1"
FEATURES = ["integrity", "public_load", "remaining_work_fraction", "quota_fraction",
            "remaining_time_fraction", "continuation_duration_fraction", "fast", "checked", "restore", "defer"]


def encode(environment, candidate):
    state = environment.state
    return np.asarray([state.integrity, environment.load, (environment.goal-state.progress)/8,
        state.quota/30, max(0, environment.deadline_s-state.elapsed_s)/30, candidate.time_hint_s/30,
        *(float(candidate.identifier == name) for name in ("fast", "checked", "restore", "defer"))], dtype=np.float32)


def collect_threat(split, episodes, output: Path, *, max_seconds=60):
    if split not in SPLITS or type(episodes) is not int or not 1 <= episodes <= SPLITS[split][1]-SPLITS[split][0]:
        raise ValueError("Invalid threat-data split/count; final-test seeds remain reserved")
    if not np.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError("Invalid threat collection budget")
    started, provenance = time.perf_counter(), source_provenance()
    rows, labels, seeds, statuses, oracle = [], [], [], [], []
    censored = 0
    for index in range(episodes):
        if time.perf_counter()-started >= max_seconds:
            break
        seed = SPLITS[split][0]+index
        # Configuration and event draws have independent streams. A public
        # load must not accidentally be the same RNG draw as the next outage.
        rng = np.random.default_rng(np.random.SeedSequence([seed, 722]))
        event_seed = int(np.random.default_rng(np.random.SeedSequence([seed, 721])).integers(0, 2**31))
        environment = ServiceWorkflow("benign", seed=event_seed)
        environment.load = float(rng.uniform(0, 1))
        environment.deadline_s = float(rng.uniform(1, 30))
        environment.state = ServiceState(float(rng.uniform(1, 30)), float(rng.uniform(.15, 1)), int(rng.integers(0, 8)))
        candidate = environment.candidates()[index % 4]
        features = encode(environment, candidate)
        probability = ServiceForecaster(environment).forecast(environment.context(0), candidate, deadline=float("inf")).failure_probability
        first = True
        for _ in range(20):
            if environment.state.status != "running" or time.perf_counter()-started >= max_seconds:
                break
            action = candidate.action if first or candidate.identifier != "restore" else next(item.action for item in environment.candidates() if item.identifier == "checked")
            environment.apply(action)
            first = False
        if environment.state.status == "running":
            censored += 1
            continue
        rows.append(features); labels.append(environment.state.status == "irreversible_outage")
        seeds.append(seed); statuses.append(environment.state.status); oracle.append(probability)
    if not rows:
        raise ValueError("No complete observed threat outcomes within budget")
    directory = output/f"threat-{split}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    data = directory/"outcomes.npz"
    categories = {"completed":"success", "abandoned":"abandoned", "irreversible_outage":"irreversible_failure",
                  "deadline_missed":"task_failure", "quota_depleted":"task_failure"}
    np.savez_compressed(data, features=np.asarray(rows, dtype=np.float32), labels=np.asarray(labels, dtype=np.bool_),
                        episode_seeds=np.asarray(seeds, dtype=np.int64), statuses=np.asarray(statuses),
                        outcomes=np.asarray([categories[status] for status in statuses]),
                        oracle_probability=np.asarray(oracle, dtype=np.float32))
    manifest = {"schema": "candidate-threat-data-v1", "domain": DOMAIN, "codec": CODEC, "feature_names": FEATURES,
                "split": split, "seed_intervals": SPLITS, "episodes": len(rows), "positive_events": int(sum(labels)),
                "censored_excluded": censored, "label": "irreversible outage under the specified continuation before competing task endings",
                "horizon": "whole finite continuation until completion, outage, deadline, depletion or abandonment",
                "metadata_not_features": ["episode_seeds", "statuses", "outcomes", "oracle_probability"],
                "oracle_notice": "Known benchmark probability is a scoring reference only, never a learned input/target",
                "dataset_sha256": digest(data), "elapsed_s": time.perf_counter()-started, **provenance,
                "claim": "synthetic observed development outcomes; not final research evidence"}
    (directory/"manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    return {"directory": str(directory.resolve()), "episodes": len(rows), "positive_events": int(sum(labels)), "elapsed_s": manifest["elapsed_s"]}

