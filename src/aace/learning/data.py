"""Recorded transitions with explicit episode grouping and no metadata features."""

import hashlib
import json
import math
import time
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.controllers import action_for_plan
from aace.envs.rover import RoverEnv
from aace.telemetry import source_provenance


def split_manifest() -> dict:
    result = json.loads(files("aace.learning").joinpath("dataset_splits.json").read_text())
    train, validation, test = (result[name] for name in ("train", "validation", "reserved_test"))
    intervals = [(item["seed_start"], item["seed_stop"]) for item in (train, validation, test)]
    for i, (start, stop) in enumerate(intervals):
        if not 0 <= start < stop:
            raise ValueError("Invalid split interval")
        if any(max(start, other_start) < min(stop, other_stop) for other_start, other_stop in intervals[:i]):
            raise ValueError("Dataset seed intervals overlap")
    return result


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(split: str, steps: int, output: Path, *, seed_offset=0, max_seconds=60.0) -> dict:
    manifest = split_manifest()
    if split not in ("train", "validation"):
        raise ValueError("Only development train/validation collection is allowed")
    if type(steps) is not int or not 0 < steps <= 1000000:
        raise ValueError("Collection steps must be in [1, 1000000]")
    if type(seed_offset) is not int or not 0 <= seed_offset < 10000:
        raise ValueError("Invalid seed offset")
    if not math.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError("Collection time budget must be finite and positive")
    settings = manifest[split]
    directory = output/f"{split}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(np.random.SeedSequence([settings["seed_start"], seed_offset, 2026]))
    rows = {name: [] for name in ("observations", "actions", "next_observations", "rewards",
                                 "terminated", "truncated", "catastrophes", "damage",
                                 "episode_ids", "episode_seeds", "scenario_indices")}
    episodes = []
    count = 0
    episode = 0
    started = time.perf_counter()
    provenance = source_provenance()
    while count < steps and time.perf_counter()-started < max_seconds:
        seed = settings["seed_start"]+seed_offset+episode
        if seed >= settings["seed_stop"]:
            raise ValueError("Collection exhausted its split's unique episode seeds")
        scenario_index = episode % len(settings["scenarios"])
        name = settings["scenarios"][scenario_index]
        env = RoverEnv(name)
        obs, _ = env.reset(seed=seed)
        # Cross every policy with every scenario; do not confound terrain with
        # a single policy (which would omit direct failures on dangerous terrain).
        plan = ("direct", "detour_north", "detour_south", "brake")[(episode // len(settings["scenarios"])) % 4]
        episode_count = 0
        while env.state.status == "running" and count < steps and time.perf_counter()-started < max_seconds:
            if rng.random() < 0.35:
                action = rng.uniform(-1, 1, 2).astype(np.float32)
            else:
                action = np.asarray(action_for_plan(env.observe(), plan), dtype=np.float32)
            nxt, reward, terminated, truncated, info = env.step(action)
            values = (obs, action, nxt, reward, terminated, truncated,
                      info["status"] in ("actuator_loss", "battery_depleted"), info["damage"],
                      episode, seed, scenario_index)
            for key, value in zip(rows, values):
                rows[key].append(value)
            obs = nxt
            count += 1
            episode_count += 1
        episodes.append({"episode_id": episode, "seed": seed, "scenario": name,
                         "policy": plan+"+35% random", "steps": episode_count,
                         "status": env.state.status, "complete_episode": env.state.status != "running"})
        env.close()
        episode += 1
    if not count:
        raise ValueError("Time budget expired before any transitions were collected")
    arrays = {}
    for key, values in rows.items():
        dtype = np.int64 if key in ("episode_ids", "episode_seeds", "scenario_indices") else (
            np.bool_ if key in ("terminated", "truncated", "catastrophes") else np.float32)
        arrays[key] = np.asarray(values, dtype=dtype)
    dataset = directory/"transitions.npz"
    np.savez_compressed(dataset, **arrays)
    report = {"schema_version": "transitions-v1", "split": split, "split_manifest": manifest,
              "observation_version": "fully_observed_v1", "environment_version": "rover-kernel-v1",
              "features": ["observations", "actions"], "targets": ["next_observations"],
              "model_target_transform": "delta of normalized [x,y,vx,vy,battery,health]",
              "metadata_not_features": ["episode_ids", "episode_seeds", "scenario_indices"],
              "actual_transitions": count, "requested_transitions": steps, "episodes": episodes,
              "catastrophic_transitions": int(arrays["catastrophes"].sum()),
              "damage_transitions": int((arrays["damage"] > 0).sum()),
              "elapsed_s": time.perf_counter()-started,
              "dataset_sha256": file_hash(dataset), **provenance,
              "external_spend_usd": 0, "claim": "development dataset; not a final benchmark"}
    (directory/"manifest.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return {"directory": str(directory.resolve()), "dataset_file": str(dataset.resolve()),
            "split": split, "transitions": count, "episodes": len(episodes),
            "catastrophic_transitions": report["catastrophic_transitions"],
            "damage_transitions": report["damage_transitions"], "elapsed_s": report["elapsed_s"]}


def load_records(directory: Path, *, expected_split: str) -> tuple[dict, dict]:
    """Verified labels/grouping for evaluation; metadata never becomes model input."""
    manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    declared = split_manifest()
    if expected_split not in ("train", "validation") or manifest["split"] != expected_split or manifest["schema_version"] != "transitions-v1":
        raise ValueError("Dataset split/schema mismatch")
    if manifest["split_manifest"] != declared or manifest["environment_version"] != "rover-kernel-v1" or manifest["observation_version"] != "fully_observed_v1":
        raise ValueError("Dataset contract/version mismatch")
    source = directory/"transitions.npz"
    if file_hash(source) != manifest["dataset_sha256"]:
        raise ValueError("Dataset hash mismatch")
    with np.load(source, allow_pickle=False) as arrays:
        records = {name: arrays[name].copy() for name in arrays.files}
    count = manifest["actual_transitions"]
    shapes = {"observations": (count, 35), "next_observations": (count, 35), "actions": (count, 2)}
    for name in ("rewards", "terminated", "truncated", "catastrophes", "damage",
                 "episode_ids", "episode_seeds", "scenario_indices"):
        shapes[name] = (count,)
    if not 0 < count <= 1000000 or any(name not in records or records[name].shape != shape for name, shape in shapes.items()):
        raise ValueError("Unexpected dataset dimensions")
    if any(not np.isfinite(value).all() for value in records.values()):
        raise ValueError("Nonfinite dataset")
    if np.any(np.abs(records["actions"]) > 1) or any(np.any(np.abs(records[name]) > 1.000001) for name in ("observations", "next_observations")):
        raise ValueError("Dataset action/observation outside contract")
    if any(records[name].dtype.kind != "b" for name in ("terminated", "truncated", "catastrophes")):
        raise ValueError("Outcome labels must contain booleans")
    limits = declared[expected_split]
    if np.any(records["episode_seeds"] < limits["seed_start"]) or np.any(records["episode_seeds"] >= limits["seed_stop"]):
        raise ValueError("Episode seed outside declared split")
    for name in ("episode_ids", "episode_seeds", "scenario_indices"):
        if records[name].dtype.kind not in "iu":
            raise ValueError("Episode grouping must contain integers")
    actual_ids = set(np.unique(records["episode_ids"]).tolist())
    described_ids = {episode["episode_id"] for episode in manifest["episodes"]}
    if actual_ids != described_ids or len(described_ids) != len(manifest["episodes"]):
        raise ValueError("Episode manifest/group mismatch")
    if len({episode["seed"] for episode in manifest["episodes"]}) != len(manifest["episodes"]):
        raise ValueError("Episode seeds must be unique within a dataset")
    for episode in manifest["episodes"]:
        mask = records["episode_ids"] == episode["episode_id"]
        if mask.sum() != episode["steps"] or not np.all(records["episode_seeds"][mask] == episode["seed"]):
            raise ValueError("Episode manifest/group mismatch")
        indices = records["scenario_indices"][mask]
        if not np.all(indices == limits["scenarios"].index(episode["scenario"])):
            raise ValueError("Episode scenario/group mismatch")
        positions = np.flatnonzero(mask)
        if np.any(np.diff(positions) != 1) or not np.array_equal(records["next_observations"][positions[:-1]], records["observations"][positions[1:]]):
            raise ValueError("Episode trajectory is not contiguous")
        ended = records["terminated"][positions] | records["truncated"][positions]
        if ended[:-1].any() or bool(ended[-1]) != episode["complete_episode"]:
            raise ValueError("Episode terminal labels disagree with its trajectory")
    return records, manifest


def load_features(directory: Path, *, expected_split: str) -> tuple[np.ndarray, np.ndarray, dict]:
    records, manifest = load_records(directory, expected_split=expected_split)
    # Episode identifiers, seeds, scenario labels and terminal truth are not inputs.
    inputs = np.concatenate([records["observations"], records["actions"]], axis=1)
    targets = records["next_observations"][:, :6]-records["observations"][:, :6]
    if inputs.shape != (manifest["actual_transitions"], 37) or targets.shape != (len(inputs), 6):
        raise ValueError("Unexpected observation/action/target dimensions")
    if not np.isfinite(inputs).all() or not np.isfinite(targets).all():
        raise ValueError("Nonfinite dataset")
    return inputs, targets, manifest
