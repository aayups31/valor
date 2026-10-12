"""Experimental learned history predictions; no policy or action authority."""

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

from aace.benchmarks.history import ENCOUNTERS, FEATURES, SCHEMA, history_controls, load_history
from aace.learning.resources import digest, memory_mb
from aace.learning.threat import probability_metrics
from aace.telemetry import source_provenance

VERSION = "history-event-head-v1"
KINDS = ("stateless", "history_linear", "history_mlp", "gru")


@dataclass(frozen=True)
class HistoryTrainSettings:
    seed: int = 42
    epochs: int = 25
    batch_size: int = 128
    max_seconds: float = 120
    max_memory_mb: float = 1024
    threads: int = 2

    def __post_init__(self):
        if type(self.seed) is not int or not 0 <= self.seed < 2**31 or type(self.epochs) is not int or not 1 <= self.epochs <= 200 or type(self.batch_size) is not int or not 8 <= self.batch_size <= 1024 or type(self.threads) is not int or self.threads not in (1,2,4):
            raise ValueError("Invalid history learning capacity")
        if any(type(v) not in (int,float) or not math.isfinite(v) or v <= 0 for v in (self.max_seconds,self.max_memory_mb)):
            raise ValueError("Invalid history resource budget")


class HistoryHead(nn.Module):
    def __init__(self, kind):
        super().__init__()
        if kind not in KINDS:
            raise ValueError("Unknown history model")
        self.kind = kind
        dimension = len(FEATURES)*(ENCOUNTERS+1)
        if kind == "gru":
            self.recurrent = nn.GRU(len(FEATURES),16,batch_first=True)
            self.head = nn.Linear(16,1)
        elif kind == "history_linear":
            self.head = nn.Linear(dimension,1)
        else:
            self.head = nn.Sequential(nn.Linear(len(FEATURES) if kind == "stateless" else dimension,14),
                                      nn.SiLU(),nn.Linear(14,1))

    def forward(self, sequence):
        if self.kind == "gru":
            features, _ = self.recurrent(sequence)
            return self.head(features[:,-1])
        features = sequence[:,-1] if self.kind == "stateless" else sequence.flatten(start_dim=1)
        return self.head(features)

    def step(self, observation, state=None):
        """Streaming recurrent prediction. State belongs to one episode only."""
        if self.kind != "gru":
            raise ValueError("Streaming state requires the recurrent model")
        features, state = self.recurrent(observation[:,None,:],state)
        return self.head(features[:,0]), state


def train_history(settings, training: Path, selection: Path, output: Path):
    started = time.perf_counter()
    provenance = source_provenance()
    data, manifest = load_history(training,"train")
    validation, val_manifest = load_history(selection,"selection")
    if set(data["episode_seeds"]) & set(validation["episode_seeds"]):
        raise ValueError("History training/selection overlap")
    torch.set_num_threads(settings.threads)
    torch.manual_seed(settings.seed)
    models = {name:HistoryHead(name) for name in KINDS}
    prevalence = float(data["labels"].mean())
    prior = min(1-1e-4,max(1e-4,prevalence))
    with torch.no_grad():
        for model in models.values():
            head = model.head[-1] if isinstance(model.head,nn.Sequential) else model.head
            head.weight.zero_();head.bias.fill_(math.log(prior/(1-prior)))
    optimizers = {name:torch.optim.Adam(model.parameters(),lr=.001) for name,model in models.items()}
    x, vx = torch.from_numpy(data["sequences"]), torch.from_numpy(validation["sequences"])
    y = torch.from_numpy(data["labels"].astype(np.float32))[:,None]
    vy = torch.from_numpy(validation["labels"].astype(np.float32))[:,None]
    rng = np.random.default_rng(settings.seed)
    best, weights, epochs = {}, {}, {}
    with torch.no_grad():
        for name,model in models.items():
            best[name] = float(nn.functional.binary_cross_entropy_with_logits(model(vx),vy))
            weights[name],epochs[name] = copy.deepcopy(model.state_dict()),0
    updates, peak, stop, logs = 0, memory_mb(), "epoch_budget", []
    if peak >= settings.max_memory_mb:
        raise ValueError("History runtime exceeds memory budget")
    for epoch in range(1,settings.epochs+1):
        order = rng.permutation(len(x))
        for begin in range(0,len(x),settings.batch_size):
            peak = max(peak,memory_mb())
            if time.perf_counter()-started >= settings.max_seconds or peak >= settings.max_memory_mb:
                stop = "wall_clock_budget" if peak < settings.max_memory_mb else "memory_budget"
                break
            batch = order[begin:begin+settings.batch_size]
            for name,model in models.items():
                loss = nn.functional.binary_cross_entropy_with_logits(model(x[batch]),y[batch])
                if not torch.isfinite(loss):
                    raise ValueError("Nonfinite history learning loss")
                optimizers[name].zero_grad();loss.backward();optimizers[name].step()
            updates += 1
        if stop != "epoch_budget":
            break
        with torch.no_grad():
            losses = {name:float(nn.functional.binary_cross_entropy_with_logits(model(vx),vy)) for name,model in models.items()}
        for name,loss in losses.items():
            if not math.isfinite(loss):
                raise ValueError("Nonfinite history selection loss")
            if loss < best[name]:
                best[name],weights[name],epochs[name] = loss,copy.deepcopy(models[name].state_dict()),epoch
        logs.append({"epoch":epoch,"updates_per_model":updates,"selection_log_loss":losses,"elapsed_s":time.perf_counter()-started})
    if not logs:
        raise ValueError("Budget expired before a validated history checkpoint")
    directory = output/f"history-model-{settings.seed}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True,exist_ok=False)
    torch.save(weights,directory/"weights.pt")
    metadata = {"model_version":VERSION,"dataset_schema":SCHEMA,"feature_names":FEATURES,
        "encounters":ENCOUNTERS,"settings":asdict(settings),"training_sha256":manifest["dataset_sha256"],
        "selection_sha256":val_manifest["dataset_sha256"],"training_episodes":len(x),"selection_episodes":len(vx),
        "training_seed_range":[int(data["episode_seeds"].min()),int(data["episode_seeds"].max())],
        "selection_seed_range":[int(validation["episode_seeds"].min()),int(validation["episode_seeds"].max())],
        "training_prevalence":prevalence,"best_epochs":epochs,"selection_log_losses":best,
        "updates_per_model":updates,"parameter_counts":{name:sum(p.numel() for p in model.parameters()) for name,model in models.items()},
        "recurrent_state_float32_bytes":64,"initialization":"same training-event prior; epoch zero eligible",
        "comparison":"same history for history heads; same data, batches, updates and selection opportunities; computation not equalized",
        "weights_sha256":digest(directory/"weights.pt"),"elapsed_s":time.perf_counter()-started,
        "peak_sampled_memory_mb":peak,"stop_reason":stop,"evidence_kind":"experimental","decision_ready":False,
        "external_spend_usd":0, **provenance}
    (directory/"model.json").write_text(json.dumps(metadata,indent=2,allow_nan=False),encoding="utf-8")
    (directory/"progress.json").write_text(json.dumps(logs,indent=2,allow_nan=False),encoding="utf-8")
    return dict(metadata,directory=str(directory.resolve()))


def load_history_model(checkpoint: Path):
    metadata = json.loads((checkpoint/"model.json").read_text(encoding="utf-8"))
    if metadata.get("model_version") != VERSION or metadata.get("dataset_schema") != SCHEMA or metadata.get("feature_names") != FEATURES or metadata.get("encounters") != ENCOUNTERS or metadata.get("decision_ready") is not False:
        raise ValueError("History checkpoint contract mismatch")
    if digest(checkpoint/"weights.pt") != metadata["weights_sha256"]:
        raise ValueError("History checkpoint hash mismatch")
    settings = HistoryTrainSettings(**metadata["settings"])
    torch.set_num_threads(settings.threads)
    models = {name:HistoryHead(name) for name in KINDS}
    weights = torch.load(checkpoint/"weights.pt",map_location="cpu",weights_only=True)
    if set(weights) != set(KINDS) or any(not torch.isfinite(value).all() for model in weights.values() for value in model.values()):
        raise ValueError("Invalid history weights")
    for name,model in models.items():
        model.load_state_dict(weights[name]);model.eval()
    return models, metadata


def paired_interval(first, second, seed=42):
    difference = np.asarray(first)-np.asarray(second)
    rng = np.random.default_rng(seed)
    bootstrap = difference[rng.integers(len(difference),size=(1000,len(difference)))].mean(axis=1)
    return {"mean_delta":float(difference.mean()),"episode_bootstrap_95_percent":[float(v) for v in np.quantile(bootstrap,[.025,.975])],
            "notice":"Paired development episodes for one fitted model; does not include training-seed variability"}


def evaluate_history(checkpoint: Path, check: Path, output: Path):
    models, metadata = load_history_model(checkpoint)
    data, manifest = load_history(check,"check")
    seeds = data["episode_seeds"]
    for group in ("training_seed_range","selection_seed_range"):
        lo,hi = metadata[group]
        if np.any((seeds >= lo) & (seeds <= hi)):
            raise ValueError("History evaluation overlaps fit/selection episodes")
    sequence = data["sequences"]
    x = torch.from_numpy(sequence)
    predictions, timings = {}, {}
    with torch.no_grad():
        for name,model in models.items():
            model(x[:min(32,len(x))])
            started = time.perf_counter()
            predictions[name] = torch.sigmoid(model(x)).numpy().ravel()
            timings[name] = 1000*(time.perf_counter()-started)/len(x)
        shuffled = x.clone()
        # Deterministic cross-episode rotation preserves each query and destroys
        # its association with its own observed history. Not a new training set.
        shuffled[:,:-1] = x[torch.roll(torch.arange(len(x)),1),:-1]
        for name in ("gru","history_mlp"):
            predictions[name+"_shuffled_history"] = torch.sigmoid(models[name](shuffled)).numpy().ravel()
    predictions.update(history_controls(sequence))
    predictions["constant_prevalence"] = np.full(len(x),metadata["training_prevalence"])
    predictions["hidden_state_reference"] = data["reference_probability"]
    labels = data["labels"]
    scores = {name:(prob-labels)**2 for name,prob in predictions.items()}
    metrics = {name:dict(probability_metrics(prob,labels),reference_probability_rmse=float(np.sqrt(np.mean((prob-data["reference_probability"])**2)))) for name,prob in predictions.items()}
    report = {"protocol":"repaired-body history probe v1; separate development episodes, not a final-test or survival-policy result",
        "condition":manifest["condition"],"checkpoint":str(checkpoint.resolve()),"model_sha256":metadata["weights_sha256"],
        "check_sha256":manifest["dataset_sha256"],"check_seed_range":[int(seeds.min()),int(seeds.max())],
        "metrics":metrics,"gru_brier_differences":{name:paired_interval(scores["gru"],value) for name,value in scores.items() if name != "gru"},
        "batch_amortized_inference_ms_per_episode":timings,"inference_notice":"One full batch after warmup; not single-request latency or a deadline guarantee",
        "observed_history_damage_events":int((sequence[:,:-1,2]/.25).sum()),"total_recovery_units":int(data["recovery_units"].sum()),
        "evidence_kind":"experimental","decision_ready":False,"external_spend_usd":0,
        "baseline_notice":"Cue-count control uses public history; stable-law Bayes knows the generation law; hidden-state reference has privileged latent information",
        "remaining_gates":["broader replicated and final evaluation", "independent calibration and shift qualification", "causal action coupling and excessive-avoidance tests", "matched counterfactual memory comparison"],
        **source_provenance()}
    output.mkdir(parents=True,exist_ok=True)
    stem = output/f"history-check-{manifest['condition']}-{uuid4().hex[:8]}"
    np.savez_compressed(stem.with_suffix(".npz"),episode_seeds=seeds,labels=labels,**{"probability_"+name:value for name,value in predictions.items()})
    report["episode_scores_sha256"] = digest(stem.with_suffix(".npz"))
    report["episode_scores_file"] = str(stem.with_suffix(".npz").resolve())
    stem.with_suffix(".json").write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    return dict(report,report_file=str(stem.with_suffix(".json").resolve()))
