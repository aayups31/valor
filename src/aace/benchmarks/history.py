"""Controlled repaired-body history probe; no real actions or future inputs."""

import json
import math
import time
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.learning.resources import digest
from aace.telemetry import source_provenance

SCHEMA = "repaired-body-history-v1"
FEATURES = ["cue_a", "cue_b", "observed_harm", "exposure_completed", "integrity", "reserve_fraction"]
CONDITIONS = ("stable", "extinction", "reversal")
SPLITS = {"train": (0, 10000), "selection": (10000, 11000), "check": (12000, 13000)}
ENCOUNTERS = 12
HIGH, LOW = .65, .05


def episode(seed, condition="stable"):
    if type(seed) is not int or not 0 <= seed < 2**31 or condition not in CONDITIONS:
        raise ValueError("Invalid history episode seed/condition")
    rng = np.random.default_rng(seed)
    danger = int(rng.integers(2))
    sequence = np.zeros((ENCOUNTERS+1, len(FEATURES)), dtype=np.float32)
    recovery = 0
    probability = LOW
    for index in range(ENCOUNTERS+1):
        cue = int(rng.integers(2))
        effective_danger = 1-danger if condition == "reversal" and index >= 8 else danger
        probability = HIGH if cue == effective_danger else LOW
        if condition == "extinction" and index >= 8:
            probability = LOW
        damage = int(rng.random() < probability)
        sequence[index, cue] = 1
        if index < ENCOUNTERS:
            harm = .25*damage
            sequence[index, 2:] = (harm, 1, 1-harm, .95)
            recovery += 2*damage
        else:
            # Public pre-action query. Its outcome is a label, never a feature.
            sequence[index, 2:] = (0, 0, 1, 1)
    return sequence, damage, probability, recovery


def collect_history(split, episodes, output: Path, *, condition="stable", max_seconds=60):
    if split not in SPLITS or condition not in CONDITIONS or type(episodes) is not int or not 1 <= episodes <= SPLITS[split][1]-SPLITS[split][0]:
        raise ValueError("Invalid history data capacity/split/condition")
    if condition != "stable" and split != "check":
        raise ValueError("Shift conditions are development checks only")
    if type(max_seconds) not in (int, float) or not math.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError("Invalid history collection budget")
    started = time.perf_counter()
    provenance = source_provenance()
    seeds = np.arange(SPLITS[split][0], SPLITS[split][0]+episodes, dtype=np.int64)
    sequences, labels, references, recovery = [], [], [], []
    for seed in seeds:
        if time.perf_counter()-started >= max_seconds:
            raise ValueError("History collection budget expired; no dataset published")
        sequence, label, reference, cost = episode(int(seed), condition)
        sequences.append(sequence); labels.append(label); references.append(reference); recovery.append(cost)
    directory = output/f"history-{split}-{condition}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(directory/"episodes.npz", sequences=np.stack(sequences),
                        labels=np.asarray(labels, dtype=np.int8), episode_seeds=seeds,
                        reference_probability=np.asarray(references, dtype=np.float64),
                        recovery_units=np.asarray(recovery, dtype=np.int16))
    manifest = {"schema":SCHEMA, "split":split, "condition":condition, "episodes":episodes,
        "encounters":ENCOUNTERS, "feature_names":FEATURES, "seed_intervals":{k:list(v) for k,v in SPLITS.items()},
        "label":"observed damage from the subsequent query encounter", "probabilities":[LOW,HIGH],
        "repair_intervention":"full repair and external replenishment before each encounter; cumulative repair cost recorded",
        "metadata_not_features":["labels", "episode_seeds", "reference_probability", "recovery_units"],
        "dataset_sha256":digest(directory/"episodes.npz"), "elapsed_s":time.perf_counter()-started,
        "external_spend_usd":0, **provenance}
    (directory/"manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False),encoding="utf-8")
    return dict(manifest,directory=str(directory.resolve()))


def load_history(directory: Path, expected_split):
    manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    if expected_split not in SPLITS or manifest.get("split") != expected_split or manifest.get("schema") != SCHEMA:
        raise ValueError("History dataset split/schema mismatch")
    condition = manifest.get("condition")
    if condition not in CONDITIONS or (expected_split != "check" and condition != "stable"):
        raise ValueError("History condition mismatch")
    if manifest.get("feature_names") != FEATURES or manifest.get("encounters") != ENCOUNTERS or manifest.get("probabilities") != [LOW,HIGH] or manifest.get("seed_intervals") != {k:list(v) for k,v in SPLITS.items()}:
        raise ValueError("History codec/protocol mismatch")
    if digest(directory/"episodes.npz") != manifest["dataset_sha256"]:
        raise ValueError("History dataset hash mismatch")
    with np.load(directory/"episodes.npz", allow_pickle=False) as archive:
        data = {name:archive[name].copy() for name in archive.files}
    count = manifest["episodes"]
    if type(count) is not int or not 1 <= count <= SPLITS[expected_split][1]-SPLITS[expected_split][0] or set(data) != {"sequences","labels","episode_seeds","reference_probability","recovery_units"}:
        raise ValueError("Invalid history dataset fields/capacity")
    x = data["sequences"]
    if x.shape != (count,ENCOUNTERS+1,len(FEATURES)) or not np.isfinite(x).all() or np.any((x < 0) | (x > 1)):
        raise ValueError("Invalid public history dimensions/values")
    if any(data[name].shape != (count,) for name in data if name != "sequences"):
        raise ValueError("Invalid history audit dimensions")
    if not np.isin(x[:,:,:2], [0,1]).all() or not np.all(x[:,:,:2].sum(axis=-1)==1):
        raise ValueError("History cues must be one-hot")
    if not np.isin(x[:,:-1,2], [0,.25]).all() or not np.all(x[:,:-1,3]==1) or not np.all(x[:,:-1,4]==1-x[:,:-1,2]) or not np.all(x[:,:-1,5]==np.float32(.95)):
        raise ValueError("Observed history/body invariant mismatch")
    if not np.all(x[:,-1,2:]==np.array([0,0,1,1])):
        raise ValueError("Query contains future outcome or unmatched body state")
    if data["labels"].dtype.kind not in "iu" or not np.isin(data["labels"],[0,1]).all() or not np.isin(data["reference_probability"],[LOW,HIGH]).all():
        raise ValueError("Invalid history label/reference")
    if not np.array_equal(data["recovery_units"], (x[:,:-1,2]/.25).sum(axis=1)*2):
        raise ValueError("Recovery cost does not match observed damage")
    seeds = data["episode_seeds"]
    if seeds.dtype.kind not in "iu" or len(np.unique(seeds)) != count or np.any(seeds < SPLITS[expected_split][0]) or np.any(seeds >= SPLITS[expected_split][1]):
        raise ValueError("History episode seed overlap/outside split")
    data["sequences"] = x.astype(np.float32)
    return data, manifest


def history_controls(sequence):
    """Counts and a stable-law Bayes reference use only observed public rows."""
    history, query = sequence[:,:-1], sequence[:,-1]
    exposure = history[:,:,:2].sum(axis=1)
    damage = (history[:,:,:2]*(history[:,:,2:3]/.25)).sum(axis=1)
    selected = np.argmax(query[:,:2],axis=1)
    laplace = ((damage+1)/(exposure+2))[np.arange(len(sequence)),selected]
    log_likelihood = []
    for danger in range(2):
        probabilities = np.array([HIGH if cue == danger else LOW for cue in range(2)])
        log_likelihood.append((damage*np.log(probabilities)+(exposure-damage)*np.log(1-probabilities)).sum(axis=1))
    logits = np.stack(log_likelihood,axis=1)
    logits -= logits.max(axis=1,keepdims=True)
    posterior = np.exp(logits); posterior /= posterior.sum(axis=1,keepdims=True)
    stable_bayes = LOW+(HIGH-LOW)*posterior[np.arange(len(sequence)),selected]
    return {"cue_counts":laplace,"public_history_bayes":stable_bayes}
