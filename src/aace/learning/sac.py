import hashlib
import importlib.metadata
import json
import math
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

from aace.envs.rover import RoverEnv
from aace.envs.scenarios import SCENARIOS
from aace.telemetry import source_provenance


@dataclass(frozen=True)
class TrainSettings:
    scenario: str = "benign"
    seed: int = 42
    steps: int = 20000
    max_seconds: float = 900.0
    max_memory_mb: float = 8192.0
    threads: int = 2
    buffer_size: int = 50000
    batch_size: int = 64
    learning_starts: int = 500
    train_freq: int = 4
    checkpoint_freq: int = 5000

    def __post_init__(self):
        if self.scenario not in SCENARIOS or not 0 <= self.seed < 2**31:
            raise ValueError("Invalid training scenario/seed")
        if min(self.steps, self.buffer_size, self.batch_size, self.train_freq, self.checkpoint_freq) <= 0:
            raise ValueError("Training counts must be positive")
        if self.batch_size > self.buffer_size or self.learning_starts < 0 or self.threads not in (1, 2, 4):
            raise ValueError("Invalid training capacity/thread setting")
        if not math.isfinite(self.max_seconds) or not math.isfinite(self.max_memory_mb) or min(self.max_seconds, self.max_memory_mb) <= 0:
            raise ValueError("Resource limits must be finite and positive")
        replay_mb = self.buffer_size*4*(35*2+2+3)/2**20
        if replay_mb > self.max_memory_mb/2:
            raise ValueError("Replay capacity consumes too much of the memory budget")


def memory_mb() -> float:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), "Unable to measure process memory")
        return counters.WorkingSetSize/2**20
    import resource
    import sys
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak/(2**20 if sys.platform == "darwin" else 1024)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            value.update(chunk)
    return value.hexdigest()


def save_bundle(model: SAC, directory: Path, metadata: dict) -> Path:
    directory.mkdir(parents=True, exist_ok=False)
    model.save(directory/"policy.zip")
    model.save_replay_buffer(directory/"replay.pkl")
    result = {**metadata, "total_environment_steps": model.num_timesteps,
              "gradient_updates": model._n_updates, "replay_size": model.replay_buffer.size(),
              "policy_sha256": digest(directory/"policy.zip"),
              "replay_sha256": digest(directory/"replay.pkl"),
              "resume_semantics": "weights/optimizer/replay; fresh episode; not exact mid-episode RNG continuation"}
    (directory/"checkpoint.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    return directory


def verify_bundle(directory: Path) -> dict:
    metadata = json.loads((directory/"checkpoint.json").read_text(encoding="utf-8"))
    if digest(directory/"policy.zip") != metadata["policy_sha256"] or digest(directory/"replay.pkl") != metadata["replay_sha256"]:
        raise ValueError("Checkpoint bundle hash mismatch")
    if metadata["environment_version"] != "rover-kernel-v1" or metadata["observation_version"] != "fully_observed_v1":
        raise ValueError("Checkpoint environment/observation version mismatch")
    return metadata


class BudgetCallback(BaseCallback):
    def __init__(self, settings: TrainSettings, directory: Path, metadata: dict, started: float):
        super().__init__()
        self.settings, self.directory, self.metadata, self.started = settings, directory, metadata, started
        self.reason = "step_budget"
        self.initial_steps = 0
        self.peak_memory_mb = 0.0

    def _on_training_start(self):
        self.initial_steps = self.model.num_timesteps

    def _on_step(self):
        used_steps = self.num_timesteps-self.initial_steps
        elapsed = time.perf_counter()-self.started
        if used_steps == 1 or used_steps % 100 == 0:
            self.peak_memory_mb = max(self.peak_memory_mb, memory_mb())
        if self.peak_memory_mb >= self.settings.max_memory_mb:
            self.reason = "memory_budget"
        elif elapsed >= self.settings.max_seconds:
            self.reason = "wall_clock_budget"
        elif used_steps >= self.settings.steps:
            self.reason = "step_budget"
        else:
            self.reason = "running"
        if used_steps == 1 or used_steps % 1000 == 0 or self.reason != "running":
            record = {"steps_this_run": used_steps, "elapsed_s": elapsed,
                      "gradient_updates": self.model._n_updates,
                      "peak_sampled_memory_mb": self.peak_memory_mb, "status": self.reason}
            with (self.directory/"progress.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, allow_nan=False)+"\n")
            print(json.dumps(record, allow_nan=False), flush=True)
        if self.reason != "running":
            return False
        if used_steps % self.settings.checkpoint_freq == 0:
            save_bundle(self.model, self.directory/f"step-{self.num_timesteps:09d}", self.metadata)
        return True


def train(settings: TrainSettings, output: Path, resume: Path | None = None) -> dict:
    torch.set_num_threads(settings.threads)
    directory = output/f"sac-{settings.seed}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    env = Monitor(RoverEnv(settings.scenario))
    env.reset(seed=settings.seed)
    metadata = {"algorithm": "stable-baselines3.SAC", "settings": asdict(settings),
                "environment_version": "rover-kernel-v1", "observation_version": "fully_observed_v1",
                "device": "cpu", "net_arch": [64, 64], **source_provenance(),
                "package_versions": {name: importlib.metadata.version(name) for name in
                                     ("torch", "stable-baselines3", "gymnasium", "numpy")},
                "protocol": "development pilot; not final research evaluation"}
    (directory/"manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    started = time.perf_counter()
    projected_memory = memory_mb()+settings.buffer_size*4*(35*2+2+3)/2**20
    if projected_memory >= settings.max_memory_mb:
        raise ValueError("Runtime and replay exceed the configured memory budget")
    if resume:
        parent = verify_bundle(resume)
        matching = ("scenario", "buffer_size", "batch_size", "learning_starts", "train_freq")
        if any(parent["settings"][key] != asdict(settings)[key] for key in matching):
            raise ValueError("Resume training settings differ from checkpoint")
        model = SAC.load(resume/"policy.zip", env=env, device="cpu")
        model.load_replay_buffer(resume/"replay.pkl")
        metadata["resumed_from"] = str(resume.resolve())
    else:
        model = SAC("MlpPolicy", env, device="cpu", seed=settings.seed, verbose=0,
                    buffer_size=settings.buffer_size, batch_size=settings.batch_size,
                    learning_starts=settings.learning_starts, train_freq=settings.train_freq,
                    gradient_steps=1, policy_kwargs={"net_arch": [64, 64]})
    initial_steps, initial_updates = model.num_timesteps, model._n_updates
    (directory/"manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    callback = BudgetCallback(settings, directory, metadata, started)
    try:
        model.learn(total_timesteps=settings.steps, callback=callback, reset_num_timesteps=resume is None)
    except KeyboardInterrupt:
        callback.reason = "interrupted"
    checkpoint = save_bundle(model, directory/"final", metadata)
    elapsed = time.perf_counter()-started
    result = {"directory": str(directory.resolve()), "checkpoint": str(checkpoint.resolve()),
              "stop_reason": callback.reason, "environment_steps": model.num_timesteps-initial_steps,
              "gradient_updates": model._n_updates-initial_updates, "elapsed_s": elapsed,
              "steps_per_s": (model.num_timesteps-initial_steps)/max(elapsed, 1e-9),
              "peak_sampled_memory_mb": callback.peak_memory_mb,
              "device": "cpu", "threads": settings.threads,
              "external_spend_usd": 0, "claim": "runtime/training pilot only"}
    (directory/"result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    env.close()
    return result


def evaluate(checkpoint: Path, scenario: str, seeds: list[int], output: Path) -> dict:
    metadata = verify_bundle(checkpoint)
    torch.set_num_threads(2)
    model = SAC.load(checkpoint/"policy.zip", device="cpu")
    episodes = []
    for seed in seeds:
        env = RoverEnv(scenario)
        obs, _ = env.reset(seed=seed)
        total_reward = 0.0
        while env.state.status == "running":
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, _, _, _ = env.step(action)
            total_reward += reward
        episodes.append({"seed": seed, "status": env.state.status, "steps": env.state.step,
                         "health": env.state.health, "battery": env.state.battery,
                         "inspected": env.state.inspected, "reward": total_reward})
        env.close()
    result = {"protocol": "development validation pilot; no final-test claim",
              "checkpoint": str(checkpoint.resolve()), "checkpoint_source": metadata,
              "evaluator_source": source_provenance(), "scenario": scenario, "episodes": episodes,
              "completion_rate": float(np.mean([e["status"] == "completed" for e in episodes])),
              "catastrophe_rate": float(np.mean([e["status"] in ("actuator_loss", "battery_depleted") for e in episodes]))}
    output.mkdir(parents=True, exist_ok=True)
    destination = output/f"validation-{uuid4().hex[:8]}.json"
    destination.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    result["report_file"] = str(destination.resolve())
    return result
