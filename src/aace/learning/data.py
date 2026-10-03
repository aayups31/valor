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


def load_features(directory: Path, *, expected_split: str) -> tuple[np.ndarray, np.ndarray, dict]:
    manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    if manifest["split"] != expected_split or manifest["schema_version"] != "transitions-v1":
        raise ValueError("Dataset split/schema mismatch")
    source = directory/"transitions.npz"
    if file_hash(source) != manifest["dataset_sha256"]:
        raise ValueError("Dataset hash mismatch")
    with np.load(source, allow_pickle=False) as arrays:
        # Episode identifiers, seeds, scenario labels and terminal truth are not inputs.
        inputs = np.concatenate([arrays["observations"], arrays["actions"]], axis=1)
        targets = arrays["next_observations"][:, :6]-arrays["observations"][:, :6]
    if inputs.shape != (manifest["actual_transitions"], 37) or targets.shape != (len(inputs), 6):
        raise ValueError("Unexpected observation/action/target dimensions")
    if not np.isfinite(inputs).all() or not np.isfinite(targets).all():
        raise ValueError("Nonfinite dataset")
    return inputs, targets, manifest
