"""Learn unknown mixture weights; coherent consequences use declared fixture physics."""

import copy
import hashlib
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch
from torch import nn

from aace.benchmarks.continuation import (CELLS, SCHEMA, exact_consequences, load_continuations,
                                         public_contexts, validate_public_sequences)
from aace.learning.continuation import ContinuationSettings, structural_diagnostics, validate_predictions
from aace.learning.history import summary_features
from aace.learning.resources import digest, memory_mb
from aace.telemetry import source_provenance

VERSION = "structured-consequence-mixture-v2"
KINDS = ("constant", "summary_linear", "summary_mlp", "gru")
HAZARDS = (.05, .65)


def canonical_decoder():
    return np.array([[exact_consequences(scene, action, probability) for scene, action in CELLS]
                     for probability in HAZARDS], dtype=np.float32)


def decoder_digest():
    return hashlib.sha256(canonical_decoder().astype("<f4").tobytes()).hexdigest()


class StructuredHead(nn.Module):
    def __init__(self, kind):
        super().__init__()
        if kind not in KINDS:
            raise ValueError("Unknown structured consequence head")
        self.kind = kind
        self.register_buffer("decoder", torch.from_numpy(canonical_decoder()))
        if kind == "constant":
            self.logit = nn.Parameter(torch.zeros(1))
        elif kind == "gru":
            self.recurrent = nn.GRU(6, 16, batch_first=True)
            self.head = nn.Linear(16, 1)
        elif kind == "summary_linear":
            self.head = nn.Linear(10, 1)
        else:
            self.head = nn.Sequential(nn.Linear(10, 14), nn.SiLU(), nn.Linear(14, 1))
        if kind != "constant":
            final = self.head[-1] if isinstance(self.head, nn.Sequential) else self.head
            nn.init.zeros_(final.weight); nn.init.zeros_(final.bias)

    def mixture_weight(self, sequences):
        if self.kind == "constant":
            logits = self.logit.expand(len(sequences), 1)
        else:
            history = self.recurrent(sequences)[0][:, -1] if self.kind == "gru" else summary_features(sequences)
            logits = self.head(history)
        return torch.sigmoid(logits)

    def forward(self, sequences):
        weight = self.mixture_weight(sequences)[:, :, None]
        return self.decoder[0][None]*(1-weight)+self.decoder[1][None]*weight


def mixture_predictions(weights):
    if weights.ndim != 1 or not len(weights) or not np.isfinite(weights).all() or np.any((weights < 0) | (weights > 1)):
        raise ValueError("Invalid consequence hypothesis mixture weights")
    decoder = canonical_decoder()
    result = decoder[0][None]*(1-weights[:, None, None])+decoder[1][None]*weights[:, None, None]
    validate_predictions(result)
    return result


def cue_likelihood_weights(sequences, *, recent=False):
    validate_public_sequences(sequences)
    history = sequences[:, :-1]
    if recent:
        history = history[:, -4:]
    match = (history[:, :, :2]*sequences[:, None, -1, :2]).sum(axis=2)
    events = (match*history[:, :, 2]/.25).sum(axis=1)
    exposures = match.sum(axis=1)
    log_ratio = events*math.log(.65/.05)+(exposures-events)*math.log(.35/.95)
    return 1/(1+np.exp(-log_ratio))


def structured_loss(prediction, targets):
    terminal = -(targets[:, :, :4]*torch.log(prediction[:, :, :4].clamp(min=1e-7))).sum(dim=2).mean()
    harm = nn.functional.binary_cross_entropy(prediction[:, :, 4].clamp(1e-7, 1-1e-7), targets[:, :, 4])
    quantity = nn.functional.mse_loss(prediction[:, :, 5:], targets[:, :, 5:])
    return terminal+harm+quantity


def train_structured(settings, training: Path, selection: Path, output: Path):
    began = time.perf_counter(); provenance = source_provenance()
    data, manifest = load_continuations(training, "train")
    validation, selection_manifest = load_continuations(selection, "selection")
    if manifest["engineering"] != selection_manifest["engineering"]:
        raise ValueError("Measured and engineering structured fitting cannot mix")
    torch.set_num_threads(settings.threads); torch.manual_seed(settings.seed)
    models = {kind: StructuredHead(kind) for kind in KINDS}
    optimizers = {kind: torch.optim.Adam(model.parameters(), lr=.001) for kind, model in models.items()}
    x, y, vx, vy = (torch.from_numpy(a) for a in (data["sequences"], data["targets"], validation["sequences"], validation["targets"]))
    best, weights, best_epochs = {}, {}, {}
    with torch.no_grad():
        for kind, model in models.items():
            best[kind] = float(structured_loss(model(vx), vy)); weights[kind] = copy.deepcopy(model.state_dict()); best_epochs[kind] = 0
    directory = output/f"structured-model-{settings.seed}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(settings.seed)
    updates = 0; peak = memory_mb(); logs = []
    for epoch in range(1, settings.epochs+1):
        order = rng.permutation(len(x))
        for begin in range(0, len(x), settings.batch_size):
            peak = max(peak, memory_mb())
            if time.perf_counter()-began >= settings.max_seconds or peak >= settings.max_memory_mb:
                torch.save(weights, directory/"partial-selected-weights.pt")
                (directory/"partial.json").write_text(json.dumps({"status": "budget_expired", "completed_epochs": len(logs),
                    "updates_per_model": updates, "settings": asdict(settings), "elapsed_s": time.perf_counter()-began,
                    "peak_sampled_memory_mb": peak, "logs": logs, "decision_ready": False, **provenance}, indent=2), encoding="utf-8")
                raise ValueError("Structured fit budget expired; incomplete recipe retained")
            batch = order[begin:begin+settings.batch_size]
            for kind, model in models.items():
                loss = structured_loss(model(x[batch]), y[batch])
                if not torch.isfinite(loss):
                    raise ValueError("Nonfinite structured consequence loss")
                optimizers[kind].zero_grad(); loss.backward(); optimizers[kind].step()
            updates += 1
        with torch.no_grad():
            losses = {kind: float(structured_loss(model(vx), vy)) for kind, model in models.items()}
        for kind, score in losses.items():
            if not math.isfinite(score):
                raise ValueError("Nonfinite structured selection loss")
            if score < best[kind]:
                best[kind], weights[kind], best_epochs[kind] = score, copy.deepcopy(models[kind].state_dict()), epoch
        logs.append({"epoch": epoch, "updates_per_model": updates, "selection_loss": losses})
        if epoch%5 == 0:
            print(json.dumps({"event": "structured_training", "seed": settings.seed, "epoch": epoch,
                              "updates_per_model": updates, "elapsed_s": time.perf_counter()-began}), flush=True)
    torch.save(weights, directory/"weights.pt")
    metadata = {"model_version": VERSION, "dataset_schema": SCHEMA, "engineering": manifest["engineering"],
        "settings": asdict(settings), "model_kinds": KINDS, "parameter_counts": {k: sum(p.numel() for p in m.parameters()) for k, m in models.items()},
        "decoder_sha256": decoder_digest(), "decoder_shape": [2, 6, 11], "hazard_hypotheses": HAZARDS,
        "decoder_notice": "Supplied fixture laws and two danger levels; learned weight is not a calibrated latent posterior",
        "training_sha256": manifest["dataset_sha256"], "selection_sha256": selection_manifest["dataset_sha256"],
        "training_subjects": len(x), "selection_subjects": len(vx), "updates_per_model": updates,
        "best_epochs": best_epochs, "selection_losses": best, "logs": logs, "weights_sha256": digest(directory/"weights.pt"),
        "elapsed_s": time.perf_counter()-began, "peak_sampled_memory_mb": max(peak, memory_mb()),
        "decision_ready": False, "external_spend_usd": 0, **provenance}
    (directory/"model.json").write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    return dict(metadata, directory=str(directory.resolve()))


def load_structured_model(directory: Path):
    metadata = json.loads((directory/"model.json").read_text(encoding="utf-8"))
    expected = {"model_version": VERSION, "dataset_schema": SCHEMA, "model_kinds": list(KINDS),
        "decoder_sha256": decoder_digest(), "decoder_shape": [2, 6, 11], "hazard_hypotheses": list(HAZARDS), "decision_ready": False}
    if any(metadata.get(key) != value for key, value in expected.items()) or type(metadata.get("engineering")) is not bool:
        raise ValueError("Structured model contract mismatch")
    settings = ContinuationSettings(**metadata["settings"])
    if metadata["updates_per_model"] != settings.epochs*math.ceil(metadata["training_subjects"]/settings.batch_size) or any(type(epoch) is not int or not 0 <= epoch <= settings.epochs for epoch in metadata["best_epochs"].values()):
        raise ValueError("Structured update/checkpoint contract mismatch")
    if digest(directory/"weights.pt") != metadata["weights_sha256"]:
        raise ValueError("Structured weights hash mismatch")
    weights = torch.load(directory/"weights.pt", map_location="cpu", weights_only=True)
    if set(weights) != set(KINDS):
        raise ValueError("Structured head set mismatch")
    models = {}
    for kind in KINDS:
        model = StructuredHead(kind); model.load_state_dict(weights[kind], strict=True); model.eval()
        if not torch.equal(model.decoder, torch.from_numpy(canonical_decoder())) or metadata["parameter_counts"][kind] != sum(p.numel() for p in model.parameters()) or any(not torch.isfinite(p).all() for p in model.parameters()):
            raise ValueError("Structured decoder/capacity/weights mismatch")
        models[kind] = model
    return models, metadata


def predict_structured(model, sequences, contexts):
    validate_public_sequences(sequences)
    if not np.array_equal(contexts, public_contexts()) or not torch.equal(model.decoder, torch.from_numpy(canonical_decoder())):
        raise ValueError("Structured prediction outside canonical public task scope")
    with torch.no_grad():
        output = model(torch.from_numpy(sequences.astype(np.float32))).numpy()
    validate_predictions(output)
    if any(row["subjects_with_any_contradiction"] for row in structural_diagnostics(output).values()):
        raise ValueError("Structured consequence consistency gate failed")
    return output


def structured_forecast(prediction, context, candidate):
    from dataclasses import replace
    from aace.decision import ForecastEvidence
    from aace.learning.continuation import experimental_forecast
    if any(row["subjects_with_any_contradiction"] for row in structural_diagnostics(prediction[None]).values()):
        raise ValueError("Inconsistent structured forecast cannot enter the core probe")
    forecast = experimental_forecast(prediction, context, candidate)
    return replace(forecast, evidence=ForecastEvidence("experimental", VERSION, context.domain,
        "Coherent declared-law mixture; learned public-history weight; unknown per-query risk bounds"))
