"""Candidate-conditioned learned event probabilities, kept experimental.

This learner takes encoded public features. It has no action execution or
authority and does not turn classifier outputs into certified risk bounds.
"""

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

from aace.learning.threat_data import load_threat
from aace.learning.resources import digest, memory_mb
from aace.telemetry import source_provenance


@dataclass(frozen=True)
class ThreatTrainSettings:
    seed: int = 42
    epochs: int = 30
    batch_size: int = 128
    max_seconds: float = 90
    max_memory_mb: float = 1024
    threads: int = 2

    def __post_init__(self):
        if type(self.seed) is not int or not 0 <= self.seed < 2**31 or type(self.epochs) is not int or not 1 <= self.epochs <= 200 or type(self.batch_size) is not int or not 8 <= self.batch_size <= 1024 or self.threads not in (1, 2, 4):
            raise ValueError("Invalid threat training capacity")
        if any(not math.isfinite(v) or v <= 0 for v in (self.max_seconds, self.max_memory_mb)):
            raise ValueError("Invalid threat resource limits")


def networks(dimension):
    return {"neural": nn.Sequential(nn.Linear(dimension, 32), nn.SiLU(), nn.Linear(32, 32), nn.SiLU(), nn.Linear(32, 1)),
            "linear": nn.Linear(dimension, 1)}


def train_threat(settings, training: Path, selection: Path, output: Path):
    started = time.perf_counter()
    provenance = source_provenance()
    torch.set_num_threads(settings.threads)
    torch.manual_seed(settings.seed)
    data, manifest = load_threat(training, "train")
    validation, val_manifest = load_threat(selection, "selection")
    if any(manifest[key] != val_manifest[key] for key in ("domain", "codec", "feature_names", "label", "horizon")):
        raise ValueError("Threat training/selection codec or target mismatch")
    if set(data["episode_seeds"]) & set(validation["episode_seeds"]):
        raise ValueError("Threat training/selection overlap")
    x, y = torch.from_numpy(data["features"]), torch.from_numpy(data["labels"].astype(np.float32))[:, None]
    vx, vy = torch.from_numpy(validation["features"]), torch.from_numpy(validation["labels"].astype(np.float32))[:, None]
    models = networks(x.shape[1])
    prevalence = float(data["labels"].mean())
    prior = min(1-1e-4,max(1e-4,prevalence))
    # Equal training-only prior prevents a poorly initialized linear control
    # from being presented as an informative weaker comparator.
    with torch.no_grad():
        for name,model in models.items():
            head = model[-1] if name == "neural" else model
            head.weight.zero_(); head.bias.fill_(math.log(prior/(1-prior)))
    optimizers = {name: torch.optim.Adam(model.parameters(), lr=.001) for name,model in models.items()}
    rng = np.random.default_rng(settings.seed)
    best, weights, epochs = {name: math.inf for name in models}, {}, {}
    updates, peak, stop = 0, memory_mb(), "epoch_budget"
    if peak >= settings.max_memory_mb:
        raise ValueError("Threat runtime exceeds memory budget")
    logs = []
    with torch.no_grad():
        for name,model in models.items():
            best[name] = float(nn.functional.binary_cross_entropy_with_logits(model(vx),vy))
            weights[name],epochs[name] = copy.deepcopy(model.state_dict()),0
    for epoch in range(1, settings.epochs+1):
        order = rng.permutation(len(x))
        for begin in range(0, len(x), settings.batch_size):
            peak = max(peak, memory_mb())
            if time.perf_counter()-started >= settings.max_seconds or peak >= settings.max_memory_mb:
                stop = "wall_clock_budget" if peak < settings.max_memory_mb else "memory_budget"
                break
            batch = order[begin:begin+settings.batch_size]
            for name, model in models.items():
                loss = nn.functional.binary_cross_entropy_with_logits(model(x[batch]), y[batch])
                if not torch.isfinite(loss):
                    raise ValueError("Nonfinite threat training loss")
                optimizers[name].zero_grad(); loss.backward(); optimizers[name].step()
            updates += 1
        if stop != "epoch_budget":
            break
        with torch.no_grad():
            losses = {name: float(nn.functional.binary_cross_entropy_with_logits(model(vx), vy)) for name,model in models.items()}
        for name, loss in losses.items():
            if not math.isfinite(loss):
                raise ValueError("Nonfinite threat validation loss")
            if loss < best[name]:
                best[name], weights[name], epochs[name] = loss, copy.deepcopy(models[name].state_dict()), epoch
        logs.append({"epoch":epoch,"selection_log_loss":losses,"updates_per_model":updates,"elapsed_s":time.perf_counter()-started})
    if len(weights) != len(models) or not logs:
        raise ValueError("Budget expired before a validated threat checkpoint")
    directory = output/f"threat-{settings.seed}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    torch.save(weights, directory/"weights.pt")
    metadata = {"model_version":"candidate-event-head-v1","settings":asdict(settings),"dimension":x.shape[1],
        "domain":manifest["domain"],"codec":manifest["codec"],"feature_names":manifest["feature_names"],
        "training_sha256":manifest["dataset_sha256"],"selection_sha256":val_manifest["dataset_sha256"],
        "training_prevalence":prevalence,"initialization":"shared training-prevalence prior; epoch-0 checkpoint also eligible",
        "training_seed_range":[int(data["episode_seeds"].min()),int(data["episode_seeds"].max())],
        "selection_seed_range":[int(validation["episode_seeds"].min()),int(validation["episode_seeds"].max())],
        "best_epochs":epochs,"selection_log_losses":best,"updates_per_model":updates,
        "training_episodes":len(x),"selection_episodes":len(vx),"stop_reason":stop,
        "elapsed_s":time.perf_counter()-started,"peak_sampled_memory_mb":peak,
        "parameter_counts":{name:sum(p.numel() for p in model.parameters()) for name,model in models.items()},
        "weights_sha256":digest(directory/"weights.pt"),"linear_control":"same public features, batches, updates and selection opportunities",
        "label":manifest["label"],"horizon":manifest["horizon"],
        "evidence_kind":"experimental","decision_ready":False,"external_spend_usd":0,**provenance}
    (directory/"model.json").write_text(json.dumps(metadata,indent=2,allow_nan=False),encoding="utf-8")
    (directory/"progress.json").write_text(json.dumps(logs,indent=2,allow_nan=False),encoding="utf-8")
    return dict(metadata,directory=str(directory.resolve()))


def load_threat_model(checkpoint):
    metadata = json.loads((checkpoint/"model.json").read_text(encoding="utf-8"))
    if metadata["model_version"] != "candidate-event-head-v1" or not 1 <= metadata["dimension"] <= 128 or digest(checkpoint/"weights.pt") != metadata["weights_sha256"]:
        raise ValueError("Threat checkpoint contract/hash mismatch")
    settings = ThreatTrainSettings(**metadata["settings"])
    torch.set_num_threads(settings.threads)
    models = networks(metadata["dimension"])
    weights = torch.load(checkpoint/"weights.pt",map_location="cpu",weights_only=True)
    for name, model in models.items():
        model.load_state_dict(weights[name]); model.eval()
    return models, metadata


def probability_metrics(probability, labels):
    probability = np.asarray(probability, dtype=np.float64)
    labels = labels.astype(np.float64)
    if probability.shape != labels.shape or not np.isfinite(probability).all() or np.any((probability < 0) | (probability > 1)):
        raise ValueError("Invalid threat probability")
    clipped = np.clip(probability,1e-7,1-1e-7)
    bins, ece = [], 0
    for lo, hi in zip([0,.025,.05,.1,.2,.5],[.025,.05,.1,.2,.5,1.000001]):
        mask = (probability >= lo) & (probability < hi)
        if not mask.any():
            continue
        predicted, actual = float(probability[mask].mean()), float(labels[mask].mean())
        ece += float(mask.mean())*abs(predicted-actual)
        bins.append({"range":[lo,min(hi,1)],"count":int(mask.sum()),"mean_prediction":predicted,"event_rate":actual})
    return {"count":len(labels),"positive_events":int(labels.sum()),"brier":float(np.mean((probability-labels)**2)),
            "log_loss":float(np.mean(-labels*np.log(clipped)-(1-labels)*np.log(1-clipped))),
            "fixed_bin_ece":ece,"reliability_bins":bins,
            "notice":"Raw event probabilities; bin averages are not individual risk bounds or calibrated guarantees"}


def evaluate_threat(checkpoint: Path, check: Path, output: Path):
    models, metadata = load_threat_model(checkpoint)
    data, manifest = load_threat(check, "check")
    if any(manifest[key] != metadata[key] for key in ("domain", "codec", "feature_names", "label", "horizon")):
        raise ValueError("Threat evaluation codec/scope mismatch")
    x = torch.from_numpy(data["features"])
    with torch.no_grad():
        predictions = {name:torch.sigmoid(model(x)).numpy().ravel() for name,model in models.items()}
    predictions.update(constant_prevalence=np.full(len(x),metadata["training_prevalence"]))
    if "oracle_probability" in data:
        predictions["analytic_oracle"] = data["oracle_probability"]
    report = {"protocol":"separate development episodes; not final-test or transfer evidence",
        "checkpoint":str(checkpoint.resolve()),"model_sha256":metadata["weights_sha256"],"check_sha256":manifest["dataset_sha256"],
        "domain":manifest["domain"],"codec":manifest["codec"],"metrics":{name:probability_metrics(prob,data["labels"]) for name,prob in predictions.items()},
        "check_seed_range":[int(data["episode_seeds"].min()),int(data["episode_seeds"].max())],
        "evidence_kind":"experimental","decision_ready":False,
        "remaining_gates":["independent calibration and threshold reliability intervals", "shift and candidate ranking acceptance", "approved-model applicability and risk-bound protocol"],
        "baseline_notice":"Linear head uses matched data/update opportunities; analytic oracle is a known-dynamics upper-reference, not an equally informed learned competitor",
        **source_provenance()}
    output.mkdir(parents=True,exist_ok=True)
    destination = output/f"threat-validation-{uuid4().hex[:8]}.json"
    destination.write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    return dict(report,report_file=str(destination.resolve()))
