"""Scoped offline continuation data and known-law references; no tool execution."""

import json
import math
import time
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.benchmarks.adaptive_history import CONDITIONS, episode
from aace.benchmarks.rehearsal import SCENARIOS, WorkRehearsal, WorkState, operation
from aace.learning.resources import digest
from aace.telemetry import source_provenance
from aace.decision import ActionIntent

SCHEMA = "public-history-continuation-v1"
STRUCTURED_SCHEMA = "structured-continuation-check-v2"
ACTIONS = ("fast", "careful")
CELLS = tuple((scene, action) for scene in SCENARIOS for action in ACTIONS)
TERMINALS = ("completed", "irreversible_outage", "deadline_missed", "resource_exhausted")
QUANTITIES = ("work_completed", "harm_received", "recovery_units", "resource_used", "elapsed_s", "integrity")
SCALES = np.array([6, .45, 6, 12, 14, 1], dtype=np.float64)
SPLITS = {"train": (40000, 43000), "selection": (50000, 50500), "check": (60000, 60500)}
ENGINEERING_SPLITS = {"train": (70000, 70064), "selection": (71000, 71032), "check": (72000, 72032)}
STRUCTURED_SPLITS = {"check": (80000, 80500)}
STRUCTURED_ENGINEERING_SPLITS = {"check": (81000, 81032)}
PUBLIC_FEATURES = ("quota_fraction", "deadline_fraction", "fast", "careful")


def public_contexts():
    return np.array([[SCENARIOS[s][0]/18, SCENARIOS[s][1]/16, float(a == "fast"), float(a == "careful")]
                     for s, a in CELLS], dtype=np.float32)


def validate_public_sequences(sequence):
    if sequence.ndim != 3 or sequence.shape[1:] != (13, 6) or len(sequence) < 1 or not np.isfinite(sequence).all():
        raise ValueError("Invalid continuation sequence dimensions/values")
    if not np.isin(sequence[:, :, :2], [0, 1]).all() or not np.all(sequence[:, :, :2].sum(axis=2) == 1) or not np.all(sequence[:, -1, 2:] == [0, 0, 1, 1]):
        raise ValueError("Invalid repaired query or cue observations")
    history = sequence[:, :-1]
    if not np.isin(history[:, :, 2], [0, .25]).all() or not np.all(history[:, :, 3] == 1) or not np.all(history[:, :, 4] == 1-history[:, :, 2]) or not np.allclose(history[:, :, 5], .95, atol=1e-7):
        raise ValueError("Observed prelude outside repaired-body experiment scope")


def outcome_vector(state, starting_quota):
    if state.status not in TERMINALS:
        raise ValueError("Continuation target needs an observed terminal outcome")
    values = np.array([state.progress, state.harm_ticks*.05, state.recovery_units,
                       starting_quota-state.quota, state.elapsed_s, state.integrity])/SCALES
    return np.concatenate(([float(state.status == status) for status in TERMINALS],
                           [float(state.harm_ticks > 0)], values)).astype(np.float32)


@lru_cache(maxsize=4096)
def exact_consequences(scenario, action, probability):
    """Integrate declared equations including early endings, without future draws.

    This is a strong known-law reference, not a learned predictor or authority.
    The output is immutable so a caller cannot corrupt the cached reference.
    """
    if scenario not in SCENARIOS or action not in ACTIONS or type(probability) not in (float, int) or not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Invalid known-law continuation scope")
    quota, deadline = SCENARIOS[scenario]
    count, amount, seconds, cost, outage, harm, ticks = operation(action, probability)
    states = {0: 1.}
    output = np.zeros(11, dtype=np.float64)
    for index in range(count):
        next_states = {}
        for old_ticks, mass in states.items():
            state = WorkState(quota-index*cost-cost, 1-old_ticks*.05, index*amount,
                              (index+1)*seconds, "running", old_ticks, 0, index+1)
            if state.quota < 0 or state.elapsed_s > deadline:
                state = replace(state, status="resource_exhausted" if state.quota < 0 else "deadline_missed")
                output += mass*outcome_vector(state, quota)
                continue
            output += mass*outage*outcome_vector(replace(state, integrity=0, status="irreversible_outage"), quota)
            for new_ticks, chance in ((old_ticks, 1-harm), (old_ticks+ticks, harm)):
                weight = mass*(1-outage)*chance
                if index < count-1:
                    next_states[new_ticks] = next_states.get(new_ticks, 0.)+weight
                else:
                    stages = (new_ticks+2)//3
                    final = replace(state, quota=state.quota-stages*2, elapsed_s=state.elapsed_s+stages,
                                    progress=(index+1)*amount, harm_ticks=new_ticks, recovery_units=stages*2,
                                    integrity=1-new_ticks*.05)
                    if final.quota < 0 or final.elapsed_s > deadline:
                        final = replace(final, status="resource_exhausted" if final.quota < 0 else "deadline_missed")
                    else:
                        final = replace(final, status="completed", integrity=1)
                    output += weight*outcome_vector(final, quota)
        states = next_states
    if not np.isclose(output[:4].sum(), 1., atol=1e-6):
        raise ValueError("Known-law terminal distribution did not conserve mass")
    return tuple(float(value) for value in output)


def collect_continuations(split, subjects, output: Path, *, condition="mixed", engineering=False, max_seconds=60, structured=False):
    if type(engineering) is not bool or type(structured) is not bool:
        raise ValueError("Continuation protocol flags must be explicit booleans")
    intervals = (STRUCTURED_ENGINEERING_SPLITS if engineering else STRUCTURED_SPLITS) if structured else (ENGINEERING_SPLITS if engineering else SPLITS)
    if split not in intervals or type(subjects) is not int or not 1 <= subjects <= intervals[split][1]-intervals[split][0]:
        raise ValueError("Invalid continuation dataset split/capacity")
    if condition not in (CONDITIONS if split == "check" else ("mixed",)):
        raise ValueError("Fitting uses mixed histories; checks use explicit conditions")
    if type(max_seconds) not in (int, float) or not math.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError("Invalid continuation collection budget")
    began = time.perf_counter()
    provenance = source_provenance()
    seeds = np.arange(intervals[split][0], intervals[split][0]+subjects, dtype=np.int64)
    sequences, targets, latent, modes = [], [], [], []
    for seed in seeds:
        if time.perf_counter()-began >= max_seconds:
            raise ValueError("Collection budget expired; no dataset published")
        sequence, ignored_future_query, probability, _, schedule = episode(int(seed), condition)
        sequences.append(sequence); latent.append(probability); modes.append(schedule["condition"])
        subject = []
        for scene, action in CELLS:
            environment = WorkRehearsal(scene, seed=int(seed), latent_probability=probability)
            environment.apply(ActionIntent(action))
            subject.append(outcome_vector(environment.state, SCENARIOS[scene][0]))
        targets.append(subject)
    directory = output/f"continuation-{'structured-' if structured else ''}{split}-{condition}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(directory/"public-targets.npz", sequences=np.stack(sequences),
                        contexts=public_contexts(), targets=np.array(targets, dtype=np.float32))
    np.savez_compressed(directory/"audit.npz", episode_seeds=seeds,
                        latent_probability=np.array(latent), conditions=np.array(modes))
    manifest = {"schema": STRUCTURED_SCHEMA if structured else SCHEMA, "split": split, "condition": condition, "engineering": engineering,
                "subjects": subjects, "action_records": subjects*len(CELLS), "cells": CELLS,
                "public_features": PUBLIC_FEATURES, "terminals": TERMINALS, "quantities": QUANTITIES,
                "scales": SCALES.tolist(), "seed_interval": list(intervals[split]),
                "dataset_sha256": digest(directory/"public-targets.npz"), "audit_sha256": digest(directory/"audit.npz"),
                "input_notice": "Only sequences and contexts enter prediction; targets are labels; audit never enters model",
                "elapsed_s": time.perf_counter()-began, "external_spend_usd": 0, **provenance}
    (directory/"manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    return dict(manifest, directory=str(directory.resolve()))


def load_continuations(directory: Path, expected_split, *, structured=False):
    if type(structured) is not bool:
        raise ValueError("Continuation protocol flag must be explicit")
    manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    expected = {"schema": STRUCTURED_SCHEMA if structured else SCHEMA, "split": expected_split, "cells": [list(c) for c in CELLS],
                "public_features": list(PUBLIC_FEATURES), "terminals": list(TERMINALS),
                "quantities": list(QUANTITIES), "scales": SCALES.tolist()}
    if any(manifest.get(key) != value for key, value in expected.items()) or type(manifest.get("engineering")) is not bool:
        raise ValueError("Continuation dataset contract mismatch")
    intervals = (STRUCTURED_ENGINEERING_SPLITS if manifest["engineering"] else STRUCTURED_SPLITS) if structured else (ENGINEERING_SPLITS if manifest["engineering"] else SPLITS)
    if expected_split not in intervals or manifest.get("seed_interval") != list(intervals[expected_split]):
        raise ValueError("Continuation episode scope mismatch")
    if digest(directory/"public-targets.npz") != manifest["dataset_sha256"] or digest(directory/"audit.npz") != manifest["audit_sha256"]:
        raise ValueError("Continuation dataset/audit hash mismatch")
    with np.load(directory/"public-targets.npz", allow_pickle=False) as archive:
        data = {name: archive[name].copy() for name in archive.files}
    with np.load(directory/"audit.npz", allow_pickle=False) as archive:
        audit = {name: archive[name].copy() for name in archive.files}
    count = manifest["subjects"]
    if type(count) is not int or not 1 <= count <= intervals[expected_split][1]-intervals[expected_split][0] or manifest["action_records"] != count*6:
        raise ValueError("Invalid continuation subject count")
    if set(data) != {"sequences", "contexts", "targets"} or data["sequences"].shape != (count, 13, 6) or data["targets"].shape != (count, 6, 11) or data["contexts"].shape != (6, 4):
        raise ValueError("Invalid continuation public/target dimensions")
    if any(a.dtype != np.float32 or not np.isfinite(a).all() or np.any((a < 0) | (a > 1)) for a in data.values()) or not np.array_equal(data["contexts"], public_contexts()):
        raise ValueError("Invalid continuation inputs/targets")
    terminal = data["targets"][:, :, :4]
    if not np.isin(terminal, [0, 1]).all() or not np.all(terminal.sum(axis=2) == 1) or not np.isin(data["targets"][:, :, 4], [0, 1]).all():
        raise ValueError("Continuation labels must record competing terminal events")
    validate_public_sequences(data["sequences"])
    if set(audit) != {"episode_seeds", "latent_probability", "conditions"} or any(a.shape != (count,) for a in audit.values()):
        raise ValueError("Invalid continuation audit dimensions")
    if audit["episode_seeds"].dtype != np.int64 or not np.array_equal(audit["episode_seeds"], np.arange(intervals[expected_split][0], intervals[expected_split][0]+count)) or not np.isin(audit["latent_probability"], [.05, .65]).all():
        raise ValueError("Invalid continuation audit seeds/probabilities")
    modes = CONDITIONS if expected_split == "check" else CONDITIONS[:3]
    if not np.isin(audit["conditions"], modes).all() or manifest["condition"] not in (CONDITIONS if expected_split == "check" else ("mixed",)) or expected_split == "check" and not np.all(audit["conditions"] == manifest["condition"]):
        raise ValueError("Invalid continuation fitting/check regimes")
    # Audit is validated here but deliberately not returned in model data.
    return data, manifest


def audit_probabilities(directory: Path):
    """Scoring reference only. Callers must first validate the dataset contract."""
    with np.load(directory/"audit.npz", allow_pickle=False) as archive:
        return archive["latent_probability"].copy()
