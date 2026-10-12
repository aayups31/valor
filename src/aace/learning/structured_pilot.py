"""Fresh structured-consequence checks with labeled historical and physics controls."""

import json
import time
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch

from aace.benchmarks.adaptive_history import CONDITIONS
from aace.benchmarks.continuation import (CELLS, QUANTITIES, SCALES, TERMINALS, audit_probabilities,
                                         collect_continuations, load_continuations)
from aace.learning.continuation import (ContinuationSettings, branch_preview, history_law_predictions,
    law_predictions, load_continuation_model, predict_continuations, reliability_bins, scores,
    structural_diagnostics, subject_losses)
from aace.learning.continuation_pilot import frozen_fit
from aace.learning.history import paired_interval
from aace.learning.resources import digest, memory_mb
from aace.learning.structured import (cue_likelihood_weights, load_structured_model, mixture_predictions,
                                    predict_structured, train_structured)
from aace.telemetry import source_provenance


def validated_source(index_path, *, engineering=False):
    source = json.loads(index_path.read_text(encoding="utf-8"))
    seeds = {fit["settings"]["seed"] for fit in source.get("fits", [])}
    if source.get("status") != "complete" or source.get("engineering") is not engineering or seeds != ({42} if engineering else {42, 43, 44}) or len(source["fits"]) != (1 if engineering else 3):
        raise ValueError("Structured pilot needs a completed frozen continuation source")
    data = {}
    for split in ("train", "selection"):
        meta = source["datasets"][split]
        data[split], manifest = load_continuations(Path(meta["directory"]), split)
        if manifest["engineering"] is not engineering or manifest["dataset_sha256"] != meta["dataset_sha256"] or not engineering and manifest["subjects"] != (3000 if split == "train" else 500):
            raise ValueError("Structured source dataset differs from frozen recipe")
    raw = []
    for fit in source["fits"]:
        models, empirical, metadata = load_continuation_model(Path(fit["directory"]))
        frozen_fit(metadata, engineering=engineering)
        if metadata["weights_sha256"] != fit["weights_sha256"] or metadata["settings"] != fit["settings"] or metadata["selection_sha256"] != source["datasets"]["selection"]["dataset_sha256"]:
            raise ValueError("Structured historical source model changed")
        if metadata["training_sha256"] != source["datasets"]["train"]["dataset_sha256"]:
            raise ValueError("Structured historical training source changed")
        expected_empirical = data["train"]["targets"].mean(axis=0, dtype=np.float64).astype(np.float32)
        if not np.array_equal(empirical, expected_empirical):
            raise ValueError("Historical empirical control differs from training-only means")
        raw.append((models, metadata))
    return source, raw, expected_empirical


def frozen_structured_fit(metadata, *, engineering=False):
    if metadata["engineering"] is not engineering or metadata["decision_ready"] is not False:
        raise ValueError("Structured fit authority/engineering boundary changed")
    settings = metadata["settings"]
    if not engineering and (settings != {"seed": settings["seed"], "epochs": 20, "batch_size": 128,
            "max_seconds": 120, "max_memory_mb": 1024, "threads": 2} or settings["seed"] not in (42, 43, 44) or
            metadata["training_subjects"] != 3000 or metadata["selection_subjects"] != 500 or metadata["updates_per_model"] != 480):
        raise ValueError("Structured fit differs from frozen recipe")


def evaluate_structured(checkpoints, raw, empirical, checks, output: Path, *, engineering=False):
    began = time.perf_counter(); provenance = source_provenance()
    directory = output/f"structured-evaluation-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    fitted = []
    for checkpoint in checkpoints:
        models, metadata = load_structured_model(checkpoint)
        frozen_structured_fit(metadata, engineering=engineering)
        if any(metadata[f"{split}_sha256"] != raw[0][1][f"{split}_sha256"] for split in ("training", "selection")):
            raise ValueError("Structured and historical fitting data differ")
        fitted.append((models, metadata))
    if {m["settings"]["seed"] for _, m in fitted} != ({42} if engineering else {42, 43, 44}) or len(fitted) != (1 if engineering else 3):
        raise ValueError("Structured fitted-seed scope changed")
    preview_metadata = next(m for _, m in fitted if m["settings"]["seed"] == 42)
    rows, work, previews, predictions = [], [], [], {}
    peak = memory_mb()
    for condition in CONDITIONS:
        data, manifest = load_continuations(checks[condition], "check", structured=True)
        if manifest["engineering"] is not engineering or manifest["condition"] != condition or not engineering and manifest["subjects"] != 500:
            raise ValueError("Structured check differs from frozen scope")
        actors, actor_kinds = {}, {}
        for models, metadata in fitted:
            for kind, model in models.items():
                actor = f"structured_{kind}_{metadata['settings']['seed']}"
                start = time.perf_counter()
                actors[actor] = predict_structured(model, data["sequences"], data["contexts"])
                actor_kinds[actor] = "learned_constant" if kind == "constant" else "structured_learned_history"
                work.append({"actor": actor, "condition": condition, "subject_predictions": len(data["sequences"]),
                             "plan_predictions": len(data["sequences"])*6, "elapsed_s": time.perf_counter()-start})
        for models, metadata in raw:
            for kind, model in models.items():
                actor = f"historical_{kind}_{metadata['settings']['seed']}"
                start = time.perf_counter()
                actors[actor] = predict_continuations(model, data["sequences"], data["contexts"])
                actor_kinds[actor] = "historical_without_structural_decoder"
                work.append({"actor": actor, "condition": condition, "subject_predictions": len(data["sequences"]),
                             "plan_predictions": len(data["sequences"])*6, "elapsed_s": time.perf_counter()-start})
        actors["context_action_empirical"] = np.broadcast_to(empirical, data["targets"].shape).copy()
        actor_kinds["context_action_empirical"] = "training_only_table"
        for recent in (False, True):
            name = "recent" if recent else "counts"
            start = time.perf_counter()
            actors[f"known_law_{name}"] = history_law_predictions(data["sequences"], recent=recent)
            actor_kinds[f"known_law_{name}"] = "public_history_plugin_with_declared_laws"
            actors[f"likelihood_mixture_{name}"] = mixture_predictions(cue_likelihood_weights(data["sequences"], recent=recent))
            actor_kinds[f"likelihood_mixture_{name}"] = "stationary_public_history_likelihood_mixture"
            work.append({"actor": f"paired_public_controls_{name}", "condition": condition,
                         "plan_predictions": len(data["sequences"])*12, "elapsed_s": time.perf_counter()-start})
        actors["latent_law_reference"] = law_predictions(audit_probabilities(checks[condition]))
        actor_kinds["latent_law_reference"] = "privileged_audit_only"
        if len(actors) != (13 if engineering else 27):
            raise ValueError("Structured actor count changed")
        reference = actors["latent_law_reference"]
        for actor, prediction in actors.items():
            peak = max(peak, memory_mb())
            if time.perf_counter()-began > 180 or peak >= 1024:
                raise ValueError("Structured evaluation budget expired; incomplete artifacts retained")
            predictions[f"{condition}__{actor}"] = prediction
            diagnostics = structural_diagnostics(prediction)
            if actor.startswith("structured_") and any(r["subjects_with_any_contradiction"] for r in diagnostics.values()):
                raise ValueError("Structured consistency gate failed")
            seed = int(actor.rsplit("_", 1)[1]) if actor.rsplit("_", 1)[-1] in ("42", "43", "44") else 42
            baseline_actor = f"structured_constant_{seed}"
            baseline = subject_losses(actors[baseline_actor], data["targets"])
            cells = []
            for index, (scene, action) in enumerate(CELLS):
                cells.append({"scenario": scene, "action": action,
                    "scores": scores(prediction[:, index:index+1], data["targets"][:, index:index+1]),
                    "outage_reliability": reliability_bins(prediction[:, index, 1], data["targets"][:, index, 1]),
                    "point_estimate_below_policy_when_latent_risk_above": int(((prediction[:, index, 1] <= .05) & (reference[:, index, 1] > .05)).sum())})
            rows.append({"condition": condition, "actor": actor, "actor_kind": actor_kinds[actor],
                "scores": scores(prediction, data["targets"]), "structural_diagnostics": diagnostics, "cells": cells,
                "paired_loss_difference_vs_constant": {"baseline_actor": baseline_actor,
                    **paired_interval(subject_losses(prediction, data["targets"]), baseline)}, "decision_ready": False})
        for scene in ("normal", "reserve_pressure", "time_pressure"):
            actor = "structured_summary_mlp_42"
            preview = branch_preview(actors[actor][0], scenario=scene,
                model_reference={"actor": actor, "model_version": preview_metadata["model_version"],
                    "weights_sha256": preview_metadata["weights_sha256"], "decoder_sha256": preview_metadata["decoder_sha256"]})
            preview["history_condition_audit_only"] = condition
            preview["supplied_knowledge"] = "Declared simulator transition laws and two possible danger levels; weight learned from public history"
            preview["observed_offline_interventions"] = [{"action": action,
                "terminal": TERMINALS[int(data["targets"][0, index, :4].argmax())],
                "quantities": dict(zip(QUANTITIES, (data["targets"][0, index, 5:]*SCALES).tolist()))}
                for index, (context, action) in enumerate(CELLS) if context == scene]
            previews.append(preview)
    np.savez_compressed(directory/"predictions.npz", **predictions)
    (directory/"previews.json").write_text(json.dumps(previews, indent=2, allow_nan=False), encoding="utf-8")
    report = {"status": "complete", "protocol": "structured consequence pilot v2", "engineering": engineering,
        "rows": rows, "prediction_work": work, "previews": len(previews), "decision_ready": False,
        "predictions_sha256": digest(directory/"predictions.npz"), "previews_sha256": digest(directory/"previews.json"),
        "elapsed_s": time.perf_counter()-began, "peak_sampled_memory_mb": max(peak, memory_mb()), "external_spend_usd": 0,
        "scope_notice": "Coherence from supplied physics, learned unknown mixture weight; no per-query upper bounds, shift certificate, felt fear or AACE",
        "grouping_notice": "500 paired IDs repeated across conditions and six plans; bootstrap groups plans within condition, excludes fitted-seed uncertainty" if not engineering else "Separate engineering smoke", **provenance}
    (directory/"report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return dict(report, directory=str(directory.resolve()))


def run_structured_pilot(index_path: Path, output: Path, *, smoke=False):
    began = time.perf_counter(); provenance = source_provenance()
    source, raw, empirical = validated_source(index_path, engineering=smoke)
    torch.set_num_threads(2)
    directory = output/f"{'smoke' if smoke else 'pilot'}-structured-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    index = {"status": "running", "protocol": "structured consequence pilot v2", "engineering": smoke,
        "source_index": str(index_path.resolve()), "source_index_sha256": digest(index_path),
        "historical_weights": [m["weights_sha256"] for _, m in raw], "checks": {}, "fits": [], **provenance}
    def save():
        (directory/"index.json").write_text(json.dumps(index, indent=2, allow_nan=False), encoding="utf-8")
    save()
    for condition in CONDITIONS:
        index["checks"][condition] = collect_continuations("check", 8 if smoke else 500, directory/"data",
                                                          condition=condition, engineering=smoke, structured=True)
        save()
    for seed in ((42,) if smoke else (42, 43, 44)):
        settings = ContinuationSettings(seed=seed, epochs=2 if smoke else 20)
        fit = train_structured(settings, Path(source["datasets"]["train"]["directory"]),
                               Path(source["datasets"]["selection"]["directory"]), directory/"models")
        frozen_structured_fit(fit, engineering=smoke)
        index["fits"].append(fit); save()
        print(json.dumps({"event": "fitted_structured", "seed": seed, "elapsed_s": fit["elapsed_s"]}), flush=True)
    result = evaluate_structured([Path(f["directory"]) for f in index["fits"]], raw, empirical,
        {c: Path(index["checks"][c]["directory"]) for c in CONDITIONS}, directory/"evaluation", engineering=smoke)
    index.update(status="complete", evaluation_directory=result["directory"],
        evaluation_report_sha256=digest(Path(result["directory"])/"report.json"), elapsed_s=time.perf_counter()-began,
        decision_ready=False, external_spend_usd=0)
    save(); print(json.dumps({"event": "complete", "index": str((directory/"index.json").resolve())}), flush=True)
    return dict(index, directory=str(directory.resolve()))
