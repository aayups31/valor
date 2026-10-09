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
    trainer = commands.add_parser("train", help="Bounded CPU SAC development pilot")
    trainer.add_argument("--scenario", choices=SCENARIOS, default="benign")
    trainer.add_argument("--seed", type=int, default=42)
    trainer.add_argument("--steps", type=int, default=20000)
    trainer.add_argument("--max-seconds", type=float, default=900)
    trainer.add_argument("--threads", type=int, choices=(1, 2, 4), default=2)
    trainer.add_argument("--memory-mb", type=float, default=8192)
    trainer.add_argument("--output", type=Path, default=Path("artifacts/training"))
    trainer.add_argument("--resume", type=Path)
    trainer.add_argument("--curriculum", choices=("full_mission", "mixed_return"), default="full_mission")
    trainer.add_argument("--entropy", choices=("auto", "auto_0.1"), default="auto")
    evaluator = commands.add_parser("evaluate", help="Validate a trusted local SAC checkpoint")
    evaluator.add_argument("--checkpoint", type=Path, required=True)
    evaluator.add_argument("--scenario", choices=SCENARIOS, default="benign")
    evaluator.add_argument("--seeds", type=int, nargs="+", default=[10001, 10002, 10003])
    evaluator.add_argument("--output", type=Path, default=Path("artifacts/validation"))
    collector = commands.add_parser("collect", help="Collect separated development transition datasets")
    collector.add_argument("--split", choices=("train", "validation"), required=True)
    collector.add_argument("--steps", type=int, default=10000)
    collector.add_argument("--seed-offset", type=int, default=0)
    collector.add_argument("--max-seconds", type=float, default=60)
    collector.add_argument("--output", type=Path, default=Path("artifacts/datasets"))
    world_trainer = commands.add_parser("train-world", help="Train a bounded CPU dynamics ensemble on separated development data")
    world_trainer.add_argument("--training", type=Path, required=True)
    world_trainer.add_argument("--validation", type=Path, required=True)
    world_trainer.add_argument("--seed", type=int, default=42)
    world_trainer.add_argument("--epochs", type=int, default=30)
    world_trainer.add_argument("--max-seconds", type=float, default=180)
    world_trainer.add_argument("--threads", type=int, choices=(1, 2, 4), default=2)
    world_trainer.add_argument("--memory-mb", type=float, default=4096)
    world_trainer.add_argument("--output", type=Path, default=Path("artifacts/world-models"))
    world_evaluator = commands.add_parser("evaluate-world", help="Check one-step and open-loop learned forecasts")
    world_evaluator.add_argument("--checkpoint", type=Path, required=True)
    world_evaluator.add_argument("--validation", type=Path, required=True)
    world_evaluator.add_argument("--rollout-starts", type=int, default=128)
    world_evaluator.add_argument("--output", type=Path, default=Path("artifacts/validation"))
    core_example = commands.add_parser("decision-example", help="Inspect the general fear/survival core in a simulation")
    core_example.add_argument("--domain", choices=("service", "rover"), default="service")
    core_example.add_argument("--scenario", default="hazard")
    core_example.add_argument("--seed", type=int, default=42)
    core_example.add_argument("--action-seconds", type=float, default=2)
    core_example.add_argument("--max-forecasts", type=int, default=8)
    core_example.add_argument("--output", type=Path, default=Path("artifacts/decisions"))
    core_evaluator = commands.add_parser("evaluate-core", help="Run bounded development service-workflow scenarios")
    core_evaluator.add_argument("--episodes", type=int, default=20)
    core_evaluator.add_argument("--seed-start", type=int, default=10000)
    core_evaluator.add_argument("--action-seconds", type=float, default=.1)
    core_evaluator.add_argument("--max-forecasts", type=int, default=8)
    core_evaluator.add_argument("--output", type=Path, default=Path("artifacts/validation"))
    threat_collector = commands.add_parser("collect-threat", help="Collect observed service-continuation event outcomes")
    threat_collector.add_argument("--split", choices=("train", "selection", "check"), required=True)
    threat_collector.add_argument("--episodes", type=int, default=800)
    threat_collector.add_argument("--max-seconds", type=float, default=60)
    threat_collector.add_argument("--output", type=Path, default=Path("artifacts/datasets"))
    threat_trainer = commands.add_parser("train-threat", help="Train experimental neural/linear threat heads with matched updates")
    threat_trainer.add_argument("--training", type=Path, required=True)
    threat_trainer.add_argument("--selection", type=Path, required=True)
    threat_trainer.add_argument("--epochs", type=int, default=30)
    threat_trainer.add_argument("--max-seconds", type=float, default=90)
    threat_trainer.add_argument("--output", type=Path, default=Path("artifacts/threat-models"))
    threat_evaluator = commands.add_parser("evaluate-threat", help="Score raw event probabilities on separate development episodes")
    threat_evaluator.add_argument("--checkpoint", type=Path, required=True)
    threat_evaluator.add_argument("--check", type=Path, required=True)
    threat_evaluator.add_argument("--output", type=Path, default=Path("artifacts/validation"))
    args = parser.parse_args()
    if args.command == "doctor":
        result = doctor()
    elif args.command == "smoke":
        result = smoke()
    elif args.command == "demo":
        from aace.demo.server import serve
        serve(args.port)
        return
    elif args.command == "train":
        from aace.learning.sac import TrainSettings, train
        result = train(TrainSettings(scenario=args.scenario, seed=args.seed, steps=args.steps,
                                     max_seconds=args.max_seconds, threads=args.threads,
                                     max_memory_mb=args.memory_mb, curriculum=args.curriculum,
                                     ent_coef=args.entropy), args.output, args.resume)
    elif args.command == "evaluate":
        from aace.learning.sac import evaluate
        result = evaluate(args.checkpoint, args.scenario, args.seeds, args.output)
    elif args.command == "collect":
        from aace.learning.data import collect
        result = collect(args.split, args.steps, args.output, seed_offset=args.seed_offset,
                         max_seconds=args.max_seconds)
    elif args.command == "train-world":
        from aace.learning.world import WorldTrainSettings, train_world
        result = train_world(WorldTrainSettings(seed=args.seed, epochs=args.epochs,
                                                max_seconds=args.max_seconds, threads=args.threads,
                                                max_memory_mb=args.memory_mb), args.training, args.validation, args.output)
    elif args.command == "evaluate-world":
        from aace.learning.world import evaluate_world
        result = evaluate_world(args.checkpoint, args.validation, args.output, rollout_starts=args.rollout_starts)
    elif args.command in ("decision-example", "evaluate-core"):
        from aace.benchmarks.run import evaluate_service, export_example
        from aace.decision import ComputeBudget
        budget = ComputeBudget(max_forecasts=args.max_forecasts, action_seconds=args.action_seconds)
        result = (export_example(args.domain, args.scenario, args.seed, args.output, budget=budget)
                  if args.command == "decision-example" else
                  evaluate_service(args.output, episodes=args.episodes, seed_start=args.seed_start, budget=budget))
    elif args.command == "collect-threat":
        from aace.benchmarks.threat_data import collect_threat
        result = collect_threat(args.split,args.episodes,args.output,max_seconds=args.max_seconds)
    elif args.command == "train-threat":
        from aace.learning.threat import ThreatTrainSettings, train_threat
        result = train_threat(ThreatTrainSettings(epochs=args.epochs,max_seconds=args.max_seconds),args.training,args.selection,args.output)
    elif args.command == "evaluate-threat":
        from aace.learning.threat import evaluate_threat
        result = evaluate_threat(args.checkpoint,args.check,args.output)
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
