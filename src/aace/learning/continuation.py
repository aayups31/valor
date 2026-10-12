"""Experimental public-history continuation models; never qualified action evidence."""

import copy
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch
from torch import nn

from aace.benchmarks.continuation import (ACTIONS, CELLS, PUBLIC_FEATURES, QUANTITIES, SCHEMA, SCALES,
                                         TERMINALS, exact_consequences, load_continuations, public_contexts, validate_public_sequences)
from aace.learning.history import summary_features
from aace.learning.resources import digest, memory_mb
from aace.telemetry import source_provenance

VERSION = "public-continuation-head-v1"
KINDS = ("summary_linear", "summary_mlp", "gru")
BINS = np.array([0, .01, .025, .05, .1, .25, .5, .75, 1])


@dataclass(frozen=True)
class ContinuationSettings:
    seed: int = 42
    epochs: int = 20
    batch_size: int = 128
    max_seconds: float = 120
    max_memory_mb: float = 1024
    threads: int = 2

    def __post_init__(self):
        if type(self.seed) is not int or not 0 <= self.seed < 2**31 or type(self.epochs) is not int or not 1 <= self.epochs <= 100 or type(self.batch_size) is not int or not 8 <= self.batch_size <= 512 or type(self.threads) is not int or self.threads not in (1, 2, 4):
            raise ValueError("Invalid continuation learning settings")
        if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in (self.max_seconds, self.max_memory_mb)):
            raise ValueError("Invalid continuation resource budget")


class ContinuationHead(nn.Module):
    def __init__(self, kind):
        super().__init__()
        if kind not in KINDS:
            raise ValueError("Unknown continuation head")
        self.kind = kind
        if kind == "gru":
            self.recurrent = nn.GRU(6, 16, batch_first=True)
        dimension = 20 if kind == "gru" else 14
        self.head = nn.Linear(dimension, 11) if kind == "summary_linear" else nn.Sequential(nn.Linear(dimension, 24), nn.SiLU(), nn.Linear(24, 11))

    def forward(self, sequences, contexts):
        # History encoding runs once per subject; all paired plans share it.
        history = self.recurrent(sequences)[0][:, -1] if self.kind == "gru" else summary_features(sequences)
        features = torch.cat((history[:, None].expand(-1, len(contexts), -1), contexts[None].expand(len(history), -1, -1)), dim=2)
        return self.head(features)


def output_predictions(logits):
    return torch.cat((torch.softmax(logits[:, :, :4], dim=2), torch.sigmoid(logits[:, :, 4:])), dim=2)


def loss_function(logits, targets):
    terminal = nn.functional.cross_entropy(logits[:, :, :4].reshape(-1, 4), targets[:, :, :4].argmax(dim=2).flatten())
    harm = nn.functional.binary_cross_entropy_with_logits(logits[:, :, 4], targets[:, :, 4])
    quantities = nn.functional.mse_loss(torch.sigmoid(logits[:, :, 5:]), targets[:, :, 5:])
    return terminal+harm+quantities


def train_continuations(settings, training: Path, selection: Path, output: Path):
    began = time.perf_counter(); provenance = source_provenance()
    data, manifest = load_continuations(training, "train")
    val, val_manifest = load_continuations(selection, "selection")
    if manifest["engineering"] != val_manifest["engineering"]:
        raise ValueError("Engineering and measured continuation data cannot mix")
    torch.set_num_threads(settings.threads); torch.manual_seed(settings.seed)
    models = {kind: ContinuationHead(kind) for kind in KINDS}
    empirical = data["targets"].mean(axis=0, dtype=np.float64).astype(np.float32)
    prior = np.clip(data["targets"].mean(axis=(0, 1)), 1e-4, 1-1e-4)
    terminal = prior[:4]/prior[:4].sum()
    bias = np.concatenate((np.log(terminal), np.log(prior[4:]/(1-prior[4:]))))
    with torch.no_grad():
        for model in models.values():
            final = model.head if isinstance(model.head, nn.Linear) else model.head[-1]
            final.weight.zero_(); final.bias.copy_(torch.tensor(bias, dtype=torch.float32))
    optimizers = {kind: torch.optim.Adam(model.parameters(), lr=.001) for kind, model in models.items()}
    x, y, vx, vy, contexts = (torch.from_numpy(a) for a in (data["sequences"], data["targets"], val["sequences"], val["targets"], data["contexts"]))
    best, weights, best_epochs = {}, {}, {}
    with torch.no_grad():
        for kind, model in models.items():
            best[kind] = float(loss_function(model(vx, contexts), vy))
            weights[kind] = copy.deepcopy(model.state_dict()); best_epochs[kind] = 0
    updates = 0; peak = memory_mb(); logs = []
    rng = np.random.default_rng(settings.seed)
    directory = output/f"continuation-model-{settings.seed}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    for epoch in range(1, settings.epochs+1):
        for begin in range(0, len(x), settings.batch_size):
            if begin == 0:
                order = rng.permutation(len(x))
            peak = max(peak, memory_mb())
            if time.perf_counter()-began >= settings.max_seconds or peak >= settings.max_memory_mb:
                torch.save(weights, directory/"partial-selected-weights.pt")
                (directory/"partial.json").write_text(json.dumps({"status": "budget_expired", "settings": asdict(settings),
                    "completed_epochs": len(logs), "updates_per_model": updates, "elapsed_s": time.perf_counter()-began,
                    "peak_sampled_memory_mb": peak, "logs": logs, "decision_ready": False, **provenance}, indent=2), encoding="utf-8")
                raise ValueError("Continuation fit budget expired before complete frozen recipe")
            batch = order[begin:begin+settings.batch_size]
            for kind, model in models.items():
                loss = loss_function(model(x[batch], contexts), y[batch])
                if not torch.isfinite(loss):
                    raise ValueError("Nonfinite continuation loss")
                optimizers[kind].zero_grad(); loss.backward(); optimizers[kind].step()
            updates += 1
        with torch.no_grad():
            losses = {kind: float(loss_function(model(vx, contexts), vy)) for kind, model in models.items()}
        for kind, score in losses.items():
            if not math.isfinite(score):
                raise ValueError("Nonfinite continuation selection score")
            if score < best[kind]:
                best[kind], weights[kind], best_epochs[kind] = score, copy.deepcopy(models[kind].state_dict()), epoch
        logs.append({"epoch": epoch, "updates_per_model": updates, "selection_loss": losses})
        if epoch%5 == 0:
            print(json.dumps({"event": "continuation_training", "seed": settings.seed, "epoch": epoch,
                              "updates_per_model": updates, "elapsed_s": time.perf_counter()-began}), flush=True)
    torch.save(weights, directory/"weights.pt")
    np.savez_compressed(directory/"empirical.npz", prediction=empirical)
    metadata = {"model_version": VERSION, "dataset_schema": SCHEMA, "settings": asdict(settings),
                "model_kinds": KINDS, "engineering": manifest["engineering"], "terminals": TERMINALS,
                "quantities": QUANTITIES, "scales": SCALES.tolist(), "cells": CELLS, "public_features": PUBLIC_FEATURES,
                "training_sha256": manifest["dataset_sha256"], "selection_sha256": val_manifest["dataset_sha256"],
                "training_subjects": len(x), "selection_subjects": len(vx), "updates_per_model": updates,
                "parameter_counts": {k: sum(p.numel() for p in m.parameters()) for k, m in models.items()},
                "weights_sha256": digest(directory/"weights.pt"), "empirical_sha256": digest(directory/"empirical.npz"),
                "best_epochs": best_epochs, "selection_losses": best, "logs": logs,
                "elapsed_s": time.perf_counter()-began, "peak_sampled_memory_mb": max(peak, memory_mb()),
                "decision_ready": False, "qualification_notice": "Experimental whole-continuation predictions; no per-query bounds or shift qualification",
                "external_spend_usd": 0, **provenance}
    (directory/"model.json").write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    return dict(metadata, directory=str(directory.resolve()))


def load_continuation_model(directory: Path):
    metadata = json.loads((directory/"model.json").read_text(encoding="utf-8"))
    expected = {"model_version": VERSION, "dataset_schema": SCHEMA, "model_kinds": list(KINDS),
                "terminals": list(TERMINALS), "quantities": list(QUANTITIES), "scales": SCALES.tolist(),
                "cells": [list(cell) for cell in CELLS], "public_features": list(PUBLIC_FEATURES), "decision_ready": False}
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError("Continuation model contract mismatch")
    ContinuationSettings(**metadata["settings"])
    if digest(directory/"weights.pt") != metadata["weights_sha256"] or digest(directory/"empirical.npz") != metadata["empirical_sha256"]:
        raise ValueError("Continuation weights/control hash mismatch")
    weights = torch.load(directory/"weights.pt", map_location="cpu", weights_only=True)
    if set(weights) != set(KINDS):
        raise ValueError("Continuation head set mismatch")
    models = {}
    for kind in KINDS:
        model = ContinuationHead(kind); model.load_state_dict(weights[kind], strict=True); model.eval()
        if metadata["parameter_counts"][kind] != sum(p.numel() for p in model.parameters()) or any(not torch.isfinite(p).all() for p in model.parameters()):
            raise ValueError("Continuation capacity/weights mismatch")
        models[kind] = model
    with np.load(directory/"empirical.npz", allow_pickle=False) as archive:
        empirical = archive["prediction"].copy()
    validate_predictions(empirical[None])
    return models, empirical, metadata


def validate_predictions(prediction, *, cells=6):
    if cells not in (1, 6) or prediction.ndim != 3 or prediction.shape[1:] != (cells, 11) or not np.isfinite(prediction).all() or np.any((prediction < 0) | (prediction > 1)) or not np.allclose(prediction[:, :, :4].sum(axis=2), 1, atol=1e-6):
        raise ValueError("Invalid competing-outcome continuation predictions")


def predict_continuations(model, sequences, contexts):
    validate_public_sequences(sequences)
    if not np.array_equal(contexts, public_contexts()):
        raise ValueError("Continuation prediction outside declared public scope")
    with torch.no_grad():
        output = output_predictions(model(torch.from_numpy(sequences.astype(np.float32)), torch.from_numpy(contexts))).numpy()
    validate_predictions(output)
    return output


def history_law_predictions(sequences, *, recent=False):
    history = sequences[:, :-1]
    if recent:
        history = history[:, -4:]
    match = (history[:, :, :2]*sequences[:, None, -1, :2]).sum(axis=2)
    probability = ((match*history[:, :, 2]/.25).sum(axis=1)+1)/(match.sum(axis=1)+2)
    return law_predictions(probability)


def law_predictions(probability):
    return np.array([[exact_consequences(scene, action, float(p)) for scene, action in CELLS]
                     for p in probability], dtype=np.float32)


def subject_losses(prediction, targets):
    terminal = -(targets[:, :, :4]*np.log(np.clip(prediction[:, :, :4], 1e-7, 1))).sum(axis=2)
    p = np.clip(prediction[:, :, 4], 1e-7, 1-1e-7); y = targets[:, :, 4]
    harm = -(y*np.log(p)+(1-y)*np.log(1-p))
    mse = ((prediction[:, :, 5:]-targets[:, :, 5:])**2).mean(axis=2)
    return (terminal+harm+mse).mean(axis=1)


def probability_scores(probability, labels):
    p = np.clip(probability.astype(np.float64), 1e-7, 1-1e-7)
    return {"brier": float(np.mean((probability-labels)**2)),
            "log_loss": float(np.mean(-labels*np.log(p)-(1-labels)*np.log(1-p))),
            "mean_prediction": float(np.mean(probability)), "observed_rate": float(np.mean(labels))}


def scores(prediction, targets):
    validate_predictions(prediction, cells=prediction.shape[1])
    return {"subjects": len(prediction), "action_records": len(prediction)*prediction.shape[1],
            "combined_loss": float(subject_losses(prediction, targets).mean()),
            "terminal_brier": float(np.mean(((prediction[:, :, :4]-targets[:, :, :4])**2).sum(axis=2))),
            "terminal_log_loss": float(np.mean(-(targets[:, :, :4]*np.log(np.clip(prediction[:, :, :4], 1e-7, 1))).sum(axis=2))),
            "outage": probability_scores(prediction[:, :, 1], targets[:, :, 1]),
            "any_harm": probability_scores(prediction[:, :, 4], targets[:, :, 4]),
            "normalized_quantity_rmse": float(np.sqrt(np.mean((prediction[:, :, 5:]-targets[:, :, 5:])**2))),
            "quantity_rmse": dict(zip(QUANTITIES, (np.sqrt(np.mean((prediction[:, :, 5:]-targets[:, :, 5:])**2, axis=(0, 1)))*SCALES).tolist()))}


def wilson_interval(events, count):
    if type(count) is not int or count < 1 or type(events) is not int or not 0 <= events <= count:
        raise ValueError("Invalid event interval count")
    z = 1.959963984540054; p = events/count
    denominator = 1+z*z/count
    center = (p+z*z/(2*count))/denominator
    radius = z*math.sqrt(p*(1-p)/count+z*z/(4*count*count))/denominator
    return [max(0., center-radius), min(1., center+radius)]


def reliability_bins(probability, labels):
    rows = []
    for index, (lower, upper) in enumerate(zip(BINS[:-1], BINS[1:])):
        mask = (probability >= lower) & ((probability <= upper) if index == len(BINS)-2 else (probability < upper))
        count = int(mask.sum())
        if count:
            events = int(labels[mask].sum())
            rows.append({"interval": [float(lower), float(upper)], "subjects": count, "events": events,
                         "mean_prediction": float(probability[mask].mean()), "observed_rate": events/count,
                         "observed_rate_wilson_95": wilson_interval(events, count),
                         "sufficient_descriptive_support": count >= 100})
    return rows


def branch_preview(prediction, *, scenario, model_reference):
    """Structured predicted consequences; no action selection, observed label or latent p."""
    validate_predictions(prediction[None])
    if scenario not in {scene for scene, _ in CELLS}:
        raise ValueError("Unknown continuation preview context")
    branches = []
    for index, (scene, action) in enumerate(CELLS):
        if scene != scenario:
            continue
        values = prediction[index]
        branches.append({"action": action, "continuation": f"{action}_process_then_repair",
                         "terminal_probabilities": dict(zip(TERMINALS, values[:4].tolist())),
                         "any_harm_probability": float(values[4]),
                         "expected_quantities": dict(zip(QUANTITIES, (values[5:]*SCALES).tolist())),
                         "failure_upper_bound": None, "evidence_kind": "experimental",
                         "decision_ready": False})
    return {"schema": "valor-consequence-preview-v1", "scenario": scenario, "model_reference": model_reference,
            "branches": branches, "action_applied": False,
            "scope": "Repaired body, declared fast/careful plans and fixed within-task cue danger in offline simulator",
            "uncertainty": "Point estimates only; per-query risk bounds and shift qualification unavailable",
            "notice": "Predicted expected outcomes, not a future recording or stepwise trajectory; no authority to execute"}


def experimental_forecast(prediction, context, candidate):
    """Core contract probe. Missing bounds and experimental evidence must block use."""
    from aace.benchmarks.rehearsal import DOMAIN, SCENARIOS, candidates
    from aace.decision import ConsequenceForecast, ForecastEvidence
    validate_predictions(prediction[None])
    if context.domain != DOMAIN or context.capability != 1 or candidate not in candidates() or candidate.identifier not in ACTIONS:
        raise ValueError("Experimental continuation forecast outside task scope")
    scenes = [scene for scene, (quota, deadline) in SCENARIOS.items()
              if context.resources == (("work_quota", quota),) and context.remaining_time_s == deadline]
    if len(scenes) != 1:
        raise ValueError("Experimental forecast requires the untouched public task context")
    values = prediction[CELLS.index((scenes[0], candidate.identifier))]
    quantity = dict(zip(QUANTITIES, values[5:]*SCALES))
    return ConsequenceForecast(context.observation_id, context.generation, candidate.identifier, candidate.continuation,
        candidate.horizon_s, float(values[0]), float(values[1]), None, float(quantity["harm_received"]),
        (("work_quota", max(0., float(quantity["resource_used"]-quantity["recovery_units"]))),),
        (("work_quota", float(quantity["recovery_units"])),), float(quantity["elapsed_s"]), float(quantity["integrity"]),
        ForecastEvidence("experimental", VERSION, DOMAIN, "Unqualified expected continuation quantities; no conservative bounds"))
