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
    run = commands.add_parser("run", help="Run and export one bounded engineering episode")
    run.add_argument("--scenario", choices=SCENARIOS, default="shortcut")
    run.add_argument("--controller", choices=("heuristic_direct", "heuristic_detour", "oracle_planner"), default="heuristic_direct")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--output", type=Path, default=Path("artifacts/replays"))
    run.add_argument("--max-seconds", type=float, default=60)
    demo = commands.add_parser("demo", help="Serve the local decision inspector")
    demo.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.command == "doctor":
        result = doctor()
    elif args.command == "smoke":
        result = smoke()
    elif args.command == "demo":
        from aace.demo.server import serve
        serve(args.port)
        return
    else:
        from aace.runtime import Session
        if args.max_seconds <= 0:
            parser.error("--max-seconds must be positive")
        session = Session(args.scenario, args.controller, args.seed)
        started = time.perf_counter()
        while not session.ended and time.perf_counter()-started < args.max_seconds:
            session.step()
        result = session.summary()
        result["wall_clock_capped"] = not session.ended
        result["replay_file"] = str(session.export(args.output).resolve())
    print(json.dumps(result, indent=2, allow_nan=False))

