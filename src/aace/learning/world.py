"""Small probabilistic dynamics ensemble. No privileged simulator state as input."""

import copy
import importlib.metadata
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch
from torch import nn

from aace.learning.data import load_records
from aace.learning.resources import digest, memory_mb
from aace.telemetry import source_provenance

MODEL_VERSION = "probabilistic-delta-ensemble-v1"
STATE_NAMES = ["x", "y", "vx", "vy", "battery", "health"]
STATE_SCALES = np.array([10, 10, 2, 2, 100, 1], dtype=np.float32)


@dataclass(frozen=True)
class WorldTrainSettings:
    seed: int = 42
    members: int = 3
    hidden: int = 64
    epochs: int = 30
    batch_size: int = 256
    learning_rate: float = 0.001
    threads: int = 2
    max_seconds: float = 180
    max_memory_mb: float = 4096

    def __post_init__(self):
        if not 0 <= self.seed < 2**31 or not 1 <= self.members <= 5 or self.hidden not in (32, 64, 128):
            raise ValueError("Invalid world-model seed/capacity")
        if not 1 <= self.epochs <= 500 or not 8 <= self.batch_size <= 2048 or self.threads not in (1, 2, 4):
            raise ValueError("Invalid world-model training budget")
        if any(not math.isfinite(v) or v <= 0 for v in (self.learning_rate, self.max_seconds, self.max_memory_mb)):
            raise ValueError("World-model resource/rate limits must be finite and positive")


class DynamicsNetwork(nn.Module):
    def __init__(self, hidden=64):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(37, hidden), nn.SiLU(),
                                     nn.Linear(hidden, hidden), nn.SiLU(), nn.Linear(hidden, 12))

    def forward(self, inputs):
        output = self.network(inputs)
        # Smooth bounded log variance avoids an unconstrained variance collapse.
        return output[:, :6], -3.0+5.0*torch.tanh(output[:, 6:])


def features(records):
    return np.concatenate([records["observations"], records["actions"]], axis=1).astype(np.float32)


def targets(records):
    return (records["next_observations"][:, :6]-records["observations"][:, :6]).astype(np.float32)


def constant_velocity_delta(observations):
    """Euler extrapolation from public velocity, with the declared v1 units.

    No learned parameters, acceleration response, terrain or resource dynamics.
    """
    delta = np.zeros((len(observations), 6), dtype=np.float32)
    delta[:, :2] = np.clip(observations[:, :2]+observations[:, 2:4]*0.02, 0, 1)-observations[:, :2]
    return delta


class WorldEnsemble:
    def __init__(self, networks, normalization, metadata):
        self.networks = networks
        self.normalization = normalization
        self.metadata = metadata
        for network in networks:
            network.eval()

    def predict(self, inputs):
        inputs = np.asarray(inputs, dtype=np.float32)
        if inputs.ndim != 2 or inputs.shape[1] != 37 or not len(inputs) or not np.isfinite(inputs).all():
            raise ValueError("Prediction requires finite public observation/action features")
        if np.any(np.abs(inputs) > 1.000001):
            raise ValueError("Prediction features outside the public contract")
        norm = self.normalization
        tensor = torch.from_numpy((inputs-norm["x_mean"])/norm["x_scale"])
        means, variances = [], []
        with torch.no_grad():
            for network in self.networks:
                mean, log_variance = network(tensor)
                means.append(mean.numpy()*norm["y_scale"]+norm["y_mean"])
                variances.append(np.exp(log_variance.numpy())*norm["y_scale"]**2)
        means, variances = np.stack(means), np.stack(variances)
        mean = means.mean(axis=0)
        disagreement = ((means-mean)**2).mean(axis=0)
        aleatoric = variances.mean(axis=0)
        if not np.isfinite(means).all() or not np.isfinite(variances).all():
            raise ValueError("Nonfinite model prediction")
        return {"mean": mean, "variance": aleatoric+disagreement,
                "aleatoric_variance": aleatoric, "disagreement_variance": disagreement,
                "member_means": means, "member_variances": variances}


def load_world(directory: Path) -> WorldEnsemble:
    metadata = json.loads((directory/"model.json").read_text(encoding="utf-8"))
    if metadata["model_version"] != MODEL_VERSION or metadata["environment_version"] != "rover-kernel-v1" or metadata["observation_version"] != "fully_observed_v1":
        raise ValueError("World-model version/contract mismatch")
    if digest(directory/"weights.pt") != metadata["weights_sha256"]:
        raise ValueError("World-model hash mismatch")
    settings = WorldTrainSettings(**metadata["settings"])
    torch.set_num_threads(settings.threads)
    saved = torch.load(directory/"weights.pt", map_location="cpu", weights_only=True)
    if len(saved["networks"]) != settings.members:
        raise ValueError("World-model ensemble count mismatch")
    normalization = {key: value.numpy() for key, value in saved["normalization"].items()}
    for key, value in normalization.items():
        shape = (37,) if key.startswith("x_") else (6,)
        if value.shape != shape or not np.isfinite(value).all() or (key.endswith("scale") and np.any(value <= 0)):
            raise ValueError("Invalid world-model normalization")
    if set(normalization) != {"x_mean", "x_scale", "y_mean", "y_scale"}:
        raise ValueError("Incomplete world-model normalization")
    networks = []
    for weights in saved["networks"]:
        network = DynamicsNetwork(settings.hidden)
        network.load_state_dict(weights)
        networks.append(network)
    return WorldEnsemble(networks, normalization, metadata)


def train_world(settings: WorldTrainSettings, training: Path, validation: Path, output: Path) -> dict:
    started = time.perf_counter()
    torch.set_num_threads(settings.threads)
    torch.manual_seed(settings.seed)
    rng = np.random.default_rng(settings.seed)
    for path in (training, validation):
        count = json.loads((path/"manifest.json").read_text())["actual_transitions"]
        if count*400/2**20 > settings.max_memory_mb/4:
            raise ValueError("Dataset capacity exceeds the world-model memory budget")
    train_records, train_manifest = load_records(training, expected_split="train")
    val_records, val_manifest = load_records(validation, expected_split="validation")
    if set(train_records["episode_seeds"]) & set(val_records["episode_seeds"]):
        raise ValueError("World-model training/validation episodes overlap")
    x, y = features(train_records), targets(train_records)
    vx, vy = features(val_records), targets(val_records)
    norm = {"x_mean": x.mean(axis=0), "x_scale": np.maximum(x.std(axis=0), 1e-3),
            "y_mean": y.mean(axis=0), "y_scale": np.maximum(y.std(axis=0), 1e-5)}
    tx, ty = torch.from_numpy((x-norm["x_mean"])/norm["x_scale"]), torch.from_numpy((y-norm["y_mean"])/norm["y_scale"])
    tvx, tvy = torch.from_numpy((vx-norm["x_mean"])/norm["x_scale"]), torch.from_numpy((vy-norm["y_mean"])/norm["y_scale"])
    networks = [DynamicsNetwork(settings.hidden) for _ in range(settings.members)]
    optimizers = [torch.optim.AdamW(network.parameters(), lr=settings.learning_rate, weight_decay=1e-4) for network in networks]
    unique = np.unique(train_records["episode_ids"])
    bootstraps, sampled_ids = [], []
    for _ in networks:
        chosen = rng.choice(unique, len(unique), replace=True)
        sampled_ids.append(chosen.tolist())
        bootstraps.append(np.concatenate([np.flatnonzero(train_records["episode_ids"] == episode) for episode in chosen]))
    directory = output/f"world-{settings.seed}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    metadata = {"model_version": MODEL_VERSION, "settings": asdict(settings),
                "environment_version": "rover-kernel-v1", "observation_version": "fully_observed_v1",
                "input_contract": "35 public observation values and 2 applied actions; no episode/scenario IDs",
                "targets": STATE_NAMES, "target_transform": "normalized physical-state delta",
                "training_dataset": str(training.resolve()), "validation_dataset": str(validation.resolve()),
                "training_sha256": train_manifest["dataset_sha256"], "validation_sha256": val_manifest["dataset_sha256"],
                "normalization_source": "training data only", "bootstrap_episode_ids": sampled_ids,
                "checkpoint_selection": "lowest ensemble mean standardized validation NLL; development only",
                "package_versions": {name: importlib.metadata.version(name) for name in ("torch", "numpy")},
                "device": "cpu", **source_provenance()}
    (directory/"manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    best_loss, best_weights, best_epoch = math.inf, None, 0
    updates, peak, stop_reason = 0, memory_mb(), "epoch_budget"
    if peak >= settings.max_memory_mb:
        raise ValueError("Runtime exceeds the world-model memory budget")
    for epoch in range(1, settings.epochs+1):
        for network, optimizer, bootstrap in zip(networks, optimizers, bootstraps):
            network.train()
            order = rng.permutation(bootstrap)
            for begin in range(0, len(order), settings.batch_size):
                peak = max(peak, memory_mb())
                if peak >= settings.max_memory_mb or time.perf_counter()-started >= settings.max_seconds:
                    stop_reason = "memory_budget" if peak >= settings.max_memory_mb else "wall_clock_budget"
                    break
                batch = order[begin:begin+settings.batch_size]
                mean, log_variance = network(tx[batch])
                loss = 0.5*((ty[batch]-mean)**2*torch.exp(-log_variance)+log_variance).mean()
                if not torch.isfinite(loss):
                    raise ValueError("Nonfinite training loss")
                optimizer.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(network.parameters(), 10)
                optimizer.step(); updates += 1
            if stop_reason != "epoch_budget":
                break
        if stop_reason != "epoch_budget":
            break
        losses = []
        with torch.no_grad():
            for network in networks:
                network.eval()
                total = 0.0
                for begin in range(0, len(tvx), settings.batch_size):
                    mean, log_variance = network(tvx[begin:begin+settings.batch_size])
                    total += float(0.5*((tvy[begin:begin+settings.batch_size]-mean)**2*torch.exp(-log_variance)+log_variance).sum())
                losses.append(total/(len(tvx)*6))
        validation_nll = float(np.mean(losses))
        if not math.isfinite(validation_nll):
            raise ValueError("Nonfinite validation loss")
        if validation_nll < best_loss:
            best_loss, best_epoch = validation_nll, epoch
            best_weights = [copy.deepcopy(network.state_dict()) for network in networks]
        progress = {"epoch": epoch, "validation_standardized_nll": validation_nll,
                    "gradient_updates": updates, "elapsed_s": time.perf_counter()-started,
                    "peak_sampled_memory_mb": peak}
        with (directory/"progress.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(progress, allow_nan=False)+"\n")
        if epoch == 1 or epoch % 5 == 0:
            print(json.dumps(progress), flush=True)
    if best_weights is None:
        raise ValueError("Budget expired before a validated world-model checkpoint was available")
    torch.save({"networks": best_weights, "normalization": {key: torch.from_numpy(value) for key, value in norm.items()}}, directory/"weights.pt")
    result = {"directory": str(directory.resolve()), "best_epoch": best_epoch,
              "completed_epochs": epoch if stop_reason == "epoch_budget" else epoch-1,
              "best_standardized_validation_nll": best_loss, "gradient_updates": updates,
              "stop_reason": stop_reason, "elapsed_s": time.perf_counter()-started,
              "peak_sampled_memory_mb": peak, "training_transitions": len(x), "validation_transitions": len(vx),
              "external_spend_usd": 0, "claim": "development model; planner readiness not established"}
    metadata.update(result, weights_sha256=digest(directory/"weights.pt"))
    (directory/"model.json").write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    return result


def metrics(model, inputs, actual):
    prediction = model.predict(inputs)
    mean, variance = prediction["mean"], np.maximum(prediction["variance"], 1e-12)
    error = (mean-actual)*STATE_SCALES
    member_var = np.maximum(prediction["member_variances"], 1e-12)
    log_prob = -0.5*(np.log(2*np.pi*member_var)+(actual-prediction["member_means"])**2/member_var).sum(axis=2)
    maximum = log_prob.max(axis=0)
    nll = -(maximum+np.log(np.exp(log_prob-maximum).mean(axis=0)))
    return {"count": len(actual), "physical_rmse": dict(zip(STATE_NAMES, np.sqrt(np.mean(error**2, axis=0)).tolist())),
            "mean_joint_delta_nll": float(nll.mean()),
            "moment_matched_90_interval_coverage": dict(zip(STATE_NAMES, (np.abs(mean-actual) <= 1.644854*np.sqrt(variance)).mean(axis=0).tolist())),
            "mean_physical_interval_width": dict(zip(STATE_NAMES, (2*1.644854*np.sqrt(variance)*STATE_SCALES).mean(axis=0).tolist())),
            "uncertainty_notice": "Moment-matched Gaussian bands; empirical coverage only, not calibrated failure probabilities"}


def advance_vector(observation, delta, waypoint, *, dt=0.1, max_steps=500, deadline=45.0):
    """Declared public-state decoder, not a call to exact transition dynamics.

    Clipping and task-event geometry are explicit. Velocity/resource changes come
    from the learned network; no simulator disturbance or hidden state is read.
    """
    result = observation.copy()
    state = observation[:6]+delta
    state[:2] = np.clip(state[:2], 0, 1)
    state[2:4] /= max(1, float(np.linalg.norm(state[2:4])))
    state[4:6] = np.clip(state[4:6], 0, observation[4:6])
    result[:6] = state
    result[6] = float(observation[6] > 0.5 or np.linalg.norm((state[:2]-waypoint)*10) <= 0.45)
    result[7] = observation[7]+1/max_steps
    goal = result[10:12] if result[6] else waypoint
    result[8:10] = goal-state[:2]
    result[12] = max(0, observation[12]-dt/max(deadline, 1))
    return result


def evaluate_world(checkpoint: Path, validation: Path, output: Path, *, rollout_starts=128) -> dict:
    if not 1 <= rollout_starts <= 2048:
        raise ValueError("Invalid rollout-validation budget")
    model = load_world(checkpoint)
    records, manifest = load_records(validation, expected_split="validation")
    if manifest["dataset_sha256"] == model.metadata["training_sha256"]:
        raise ValueError("Training dataset cannot be evaluation data")
    x, y = features(records), targets(records)
    start_time = time.perf_counter()
    one_step = {"all": metrics(model, x, y)}
    masks = {"damage": records["damage"] > 0, "no_damage": records["damage"] == 0,
             "return_phase": records["observations"][:, 6] > 0.5,
             "catastrophe_transition": records["catastrophes"],
             "at_boundary": np.any((records["next_observations"][:, :2] <= 1e-6) | (records["next_observations"][:, :2] >= 1-1e-6), axis=1)}
    for name, mask in masks.items():
        one_step[name] = metrics(model, x[mask], y[mask]) if mask.any() else {"count": 0, "status": "no evidence"}
    baselines = {}
    for name, delta in (("no_change", np.zeros(6)), ("training_mean_delta", model.normalization["y_mean"]),
                        ("constant_velocity", constant_velocity_delta(records["observations"]))):
        errors = (delta-y)*STATE_SCALES
        baselines[name] = {"all": dict(zip(STATE_NAMES, np.sqrt(np.mean(errors**2, axis=0)).tolist()))}
        damage_mask = masks["damage"]
        if damage_mask.any():
            baselines[name]["damage"] = dict(zip(STATE_NAMES, np.sqrt(np.mean(errors[damage_mask]**2, axis=0)).tolist()))
    rollouts = {}
    for horizon in (5, 20):
        starts = []
        for episode in np.unique(records["episode_ids"]):
            indices = np.flatnonzero(records["episode_ids"] == episode)
            starts.extend(indices[:max(0, len(indices)-horizon+1)].tolist())
        if not starts:
            rollouts[str(horizon)] = {"count": 0, "status": "no complete windows"}; continue
        selected = np.array(starts)[np.linspace(0, len(starts)-1, min(rollout_starts, len(starts)), dtype=int)]
        predictions, truths, persistence, kinematic = [], [], [], []
        for start in selected:
            initial = records["observations"][start]
            observation = initial.copy()
            simple = initial.copy()
            waypoint = initial[:2]+initial[8:10] if not initial[6] else initial[10:12]
            for offset in range(horizon):
                inputs = np.concatenate([observation, records["actions"][start+offset]])[None]
                delta = model.predict(inputs)["mean"][0]
                observation = advance_vector(observation, delta, waypoint)
                simple = advance_vector(simple, constant_velocity_delta(simple[None])[0], waypoint)
            predictions.append(observation[:6])
            truths.append(records["next_observations"][start+horizon-1, :6])
            persistence.append(initial[:6])
            kinematic.append(simple[:6])
        error = (np.array(predictions)-truths)*STATE_SCALES
        baseline_error = (np.array(persistence)-truths)*STATE_SCALES
        kinematic_error = (np.array(kinematic)-truths)*STATE_SCALES
        rollouts[str(horizon)] = {"count": len(selected), "physical_rmse": dict(zip(STATE_NAMES, np.sqrt((error**2).mean(axis=0)).tolist())),
                                  "no_change_physical_rmse": dict(zip(STATE_NAMES, np.sqrt((baseline_error**2).mean(axis=0)).tolist())),
                                  "constant_velocity_physical_rmse": dict(zip(STATE_NAMES, np.sqrt((kinematic_error**2).mean(axis=0)).tolist())),
                                  "seconds": horizon*0.1}
    report = {"protocol": "development validation; checkpoint selection used validation; no independent final-test claim",
              "checkpoint": str(checkpoint.resolve()), "model_version": MODEL_VERSION,
              "model_sha256": model.metadata["weights_sha256"], "validation_sha256": manifest["dataset_sha256"],
              "one_step": one_step, "simple_baselines": baselines, "open_loop_recorded_action_rollouts": rollouts,
              "rollout_notice": "Only initial public state and recorded applied actions are supplied; no future states/noise. Decoder clips physical ranges and updates known task geometry. Windows are correlated development samples. This is state-error validation, not a closed-loop controller or calibrated terminal-risk forecast.",
              "planner_ready": False, "remaining_gates": ["held-out candidate ranking", "threat calibration", "longer-horizon and policy-shift validation"],
              "elapsed_s": time.perf_counter()-start_time, **source_provenance()}
    output.mkdir(parents=True, exist_ok=True)
    destination = output/f"world-validation-{uuid4().hex[:8]}.json"
    destination.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return dict(report, report_file=str(destination.resolve()))
