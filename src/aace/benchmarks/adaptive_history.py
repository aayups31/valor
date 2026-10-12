"""V2 history task: hidden variable changes, public observations, no authority."""

import json
import math
import time
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.benchmarks.history import ENCOUNTERS, FEATURES, HIGH, LOW, load_history
from aace.learning.resources import digest
from aace.telemetry import source_provenance

SCHEMA = "adaptive-repaired-body-history-v2"
CONDITIONS = ("stable","extinction","reversal","recurrence")
SPLITS = {"train":(3000,9000),"selection":(11000,12000),"check":(14000,15000)}


def episode(seed, condition="mixed"):
    if type(seed) is not int or not 0 <= seed < 2**31 or condition not in (*CONDITIONS,"mixed"):
        raise ValueError("Invalid adaptive episode seed/condition")
    rng = np.random.default_rng(seed)
    danger = int(rng.integers(2))
    change = int(rng.integers(4,10))
    return_at = int(rng.integers(9,12))
    recurrence_change = int(rng.integers(4,7))
    chosen = CONDITIONS[int(rng.integers(3))]
    mode = chosen if condition == "mixed" else condition
    if mode == "recurrence":
        change = recurrence_change
    sequence = np.zeros((ENCOUNTERS+1,len(FEATURES)),dtype=np.float32)
    recovery = 0
    for index in range(ENCOUNTERS+1):
        cue = int(rng.integers(2))
        effective = 1-danger if mode == "reversal" and index >= change else danger
        probability = HIGH if cue == effective else LOW
        if mode == "extinction" and index >= change or mode == "recurrence" and change <= index < return_at:
            probability = LOW
        damage = int(rng.random() < probability)
        sequence[index,cue] = 1
        if index < ENCOUNTERS:
            harm = .25*damage
            sequence[index,2:] = (harm,1,1-harm,.95)
            recovery += 2*damage
        else:
            sequence[index,2:] = (0,0,1,1)
    audit = {"condition":mode,"change_at":change,"return_at":return_at if mode == "recurrence" else ENCOUNTERS}
    return sequence,damage,probability,recovery,audit


def collect_adaptive(split, episodes, output: Path, *, condition="mixed", max_seconds=60):
    if split not in SPLITS or type(episodes) is not int or not 1 <= episodes <= SPLITS[split][1]-SPLITS[split][0]:
        raise ValueError("Invalid adaptive data split/capacity")
    allowed = CONDITIONS if split == "check" else ("mixed",)
    if condition not in allowed:
        raise ValueError("Adaptive fit data must be mixed; checks use explicit conditions")
    if type(max_seconds) not in (int,float) or not math.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError("Invalid adaptive collection budget")
    started = time.perf_counter();provenance = source_provenance()
    seeds = np.arange(SPLITS[split][0],SPLITS[split][0]+episodes,dtype=np.int64)
    rows = []
    for seed in seeds:
        if time.perf_counter()-started >= max_seconds:
            raise ValueError("Adaptive collection budget expired; no dataset published")
        rows.append(episode(int(seed),condition))
    directory = output/f"adaptive-{split}-{condition}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(directory/"episodes.npz", sequences=np.stack([r[0] for r in rows]),
        labels=np.array([r[1] for r in rows],dtype=np.int8),episode_seeds=seeds,
        reference_probability=np.array([r[2] for r in rows],dtype=np.float64),
        recovery_units=np.array([r[3] for r in rows],dtype=np.int16))
    np.savez_compressed(directory/"schedules.npz",conditions=np.array([r[4]["condition"] for r in rows]),
        change_at=np.array([r[4]["change_at"] for r in rows],dtype=np.int8),
        return_at=np.array([r[4]["return_at"] for r in rows],dtype=np.int8))
    manifest = {"schema":SCHEMA,"split":split,"condition":condition,"episodes":episodes,
        "encounters":ENCOUNTERS,"feature_names":FEATURES,"probabilities":[LOW,HIGH],
        "seed_intervals":{k:list(v) for k,v in SPLITS.items()},
        "label":"observed damage from the subsequent query encounter",
        "metadata_not_features":["labels","episode_seeds","reference_probability","recovery_units","schedules.npz"],
        "schedule_notice":"Hidden regimes/change times are audit-only and excluded from loader model inputs",
        "regime_counts":{mode:sum(r[4]["condition"] == mode for r in rows) for mode in CONDITIONS},
        "repair_intervention":"full repair and external replenishment; observed repair costs recorded",
        "dataset_sha256":digest(directory/"episodes.npz"),"schedule_sha256":digest(directory/"schedules.npz"),
        "elapsed_s":time.perf_counter()-started,"external_spend_usd":0,**provenance}
    (directory/"manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False),encoding="utf-8")
    return dict(manifest,directory=str(directory.resolve()))


def load_adaptive(directory: Path, expected_split):
    data, manifest = load_history(directory,expected_split,adaptive=True)
    if digest(directory/"schedules.npz") != manifest["schedule_sha256"]:
        raise ValueError("Adaptive schedule hash mismatch")
    with np.load(directory/"schedules.npz",allow_pickle=False) as archive:
        schedule = {name:archive[name].copy() for name in archive.files}
    count = manifest["episodes"]
    if set(schedule) != {"conditions","change_at","return_at"} or any(x.shape != (count,) for x in schedule.values()):
        raise ValueError("Invalid adaptive schedule dimensions")
    modes, change, returns = (schedule[name] for name in ("conditions","change_at","return_at"))
    allowed = CONDITIONS if expected_split == "check" else CONDITIONS[:3]
    if not np.isin(modes,allowed).all() or change.dtype.kind not in "iu" or returns.dtype.kind not in "iu":
        raise ValueError("Invalid adaptive schedule types/conditions")
    recurrent = modes == "recurrence"
    if np.any((change < 4) | (change > 9)) or np.any(change[recurrent] > 6) or np.any((returns[recurrent] < 9) | (returns[recurrent] > 11)) or np.any(returns[~recurrent] != ENCOUNTERS):
        raise ValueError("Adaptive schedule outside protocol")
    if expected_split == "check" and not np.all(modes == manifest["condition"]):
        raise ValueError("Adaptive schedule does not match check condition")
    if manifest["regime_counts"] != {mode:int((modes == mode).sum()) for mode in CONDITIONS}:
        raise ValueError("Adaptive regime count mismatch")
    # Never return schedules, modes or change times to a prediction model.
    return data,manifest
