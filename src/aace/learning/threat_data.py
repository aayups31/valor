"""Feature-vector event datasets shared by candidate-conditioned threat learners."""

import json
from pathlib import Path

import numpy as np

from aace.learning.resources import digest

SPLITS = {"train": (0, 10000), "selection": (10000, 11000), "check": (12000, 13000)}


def load_threat(directory: Path, expected_split):
    manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    if expected_split not in SPLITS or manifest["split"] != expected_split or manifest["schema"] != "candidate-threat-data-v1":
        raise ValueError("Threat dataset split/schema mismatch")
    names = manifest["feature_names"]
    if not manifest["domain"] or not manifest["codec"] or not 1 <= len(names) <= 128 or len(set(names)) != len(names) or manifest["seed_intervals"] != {k:list(v) for k,v in SPLITS.items()}:
        raise ValueError("Threat dataset contract mismatch")
    if digest(directory/"outcomes.npz") != manifest["dataset_sha256"]:
        raise ValueError("Threat dataset hash mismatch")
    with np.load(directory/"outcomes.npz", allow_pickle=False) as archive:
        data = {name: archive[name].copy() for name in archive.files}
    count = manifest["episodes"]
    if not 1 <= count <= SPLITS[expected_split][1]-SPLITS[expected_split][0] or data["features"].shape != (count,len(names)) or any(data[name].shape != (count,) for name in ("labels", "episode_seeds", "outcomes")):
        raise ValueError("Invalid threat dataset dimensions")
    if not np.isfinite(data["features"]).all() or np.any(data["features"] < 0) or np.any(data["features"] > 1):
        raise ValueError("Invalid public threat features")
    if "oracle_probability" in data and (data["oracle_probability"].shape != (count,) or not np.isfinite(data["oracle_probability"]).all() or np.any((data["oracle_probability"] < 0) | (data["oracle_probability"] > 1))):
        raise ValueError("Invalid scoring reference")
    seeds = data["episode_seeds"]
    if seeds.dtype.kind not in "iu" or len(np.unique(seeds)) != count or np.any(seeds < SPLITS[expected_split][0]) or np.any(seeds >= SPLITS[expected_split][1]) or data["labels"].dtype.kind != "b":
        raise ValueError("Invalid threat episode groups/labels")
    if not np.array_equal(data["labels"], data["outcomes"] == "irreversible_failure") or not set(data["outcomes"]) <= {"success", "abandoned", "task_failure", "irreversible_failure"} or int(data["labels"].sum()) != manifest["positive_events"]:
        raise ValueError("Unknown/censored threat outcomes cannot be labeled negative")
    data["features"] = data["features"].astype(np.float32)
    return data, manifest
