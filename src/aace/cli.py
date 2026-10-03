"""Small explicit commands; commands never launch paid work."""

import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from gymnasium.utils.env_checker import check_env

from aace import __version__
from aace.envs.rover import RoverEnv
from aace.envs.scenarios import SCENARIOS


def doctor() -> dict:
    packages = {}
    for name in ("numpy", "gymnasium", "pytest", "torch", "stable-baselines3"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return {"aace_version": __version__, "python": sys.version.split()[0],
            "executable": sys.executable, "platform": platform.platform(),
            "logical_cpus": os.cpu_count(), "packages": packages,
            "git_revision": revision.stdout.strip() if revision.returncode == 0 else None,
            "default_backend": "cpu", "external_spend_usd": 0}


def smoke() -> dict:
    env = RoverEnv()
    check_env(env, skip_render_check=True)
    env.reset(seed=42)
    snapshot = env.snapshot()
    branch = RoverEnv.from_snapshot(snapshot)
    started = time.perf_counter()
    steps = 0
    for _ in range(100):
        action = (0.05, 0.0)
        obs, reward, terminated, truncated, _ = env.step(action)
        other = branch.step(action)
        np.testing.assert_array_equal(obs, other[0])
        assert reward == other[1]
        steps += 1
        if terminated or truncated:
            break
    elapsed = time.perf_counter()-started
    return {"gym_contract": "passed", "snapshot_replay": "passed", "seed": 42,
            "paired_steps": steps, "elapsed_s": elapsed,
            "paired_steps_per_s": steps/max(elapsed, 1e-9),
            "note": "Engineering smoke; not an AACE experiment"}


def main() -> None:
    parser = argparse.ArgumentParser(description="VALOR / AACE local research engine")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Report runtime versions and reference backend")
    commands.add_parser("smoke", help="Check Gym contract and exact replay")
    args = parser.parse_args()
    result = doctor() if args.command == "doctor" else smoke()
    print(json.dumps(result, indent=2, allow_nan=False))

