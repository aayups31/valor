"""Frozen continuation pilot and descriptive qualification audit; no action authority."""

import json
import time
from pathlib import Path
from uuid import uuid4

import numpy as np

from aace.benchmarks.adaptive_history import CONDITIONS
from aace.benchmarks.continuation import (CELLS, QUANTITIES, SCALES, TERMINALS, audit_probabilities,
                                         collect_continuations, load_continuations)
from aace.learning.continuation import (ContinuationSettings, branch_preview, history_law_predictions,
    law_predictions, load_continuation_model, predict_continuations, reliability_bins, scores,
    structural_diagnostics, subject_losses, train_continuations)
from aace.learning.history import paired_interval
from aace.learning.resources import digest, memory_mb
from aace.telemetry import source_provenance


def frozen_fit(metadata, *, engineering=False):
    settings = metadata["settings"]
    if metadata["engineering"] != engineering or metadata["decision_ready"] is not False:
        raise ValueError("Continuation authority/engineering boundary changed")
    if not engineering:
        expected = {"seed": settings["seed"], "epochs": 20, "batch_size": 128,
                    "max_seconds": 120, "max_memory_mb": 1024, "threads": 2}
        if settings != expected or settings["seed"] not in (42, 43, 44) or metadata["training_subjects"] != 3000 or metadata["selection_subjects"] != 500 or metadata["updates_per_model"] != 480:
            raise ValueError("Continuation fit differs from frozen recipe")


def evaluate_continuations(checkpoints, checks, output: Path, *, engineering=False):
    began = time.perf_counter(); provenance = source_provenance()
    directory = output/f"continuation-evaluation-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    fitted = []
    empirical = None
    for checkpoint in checkpoints:
        models, table, metadata = load_continuation_model(checkpoint)
        frozen_fit(metadata, engineering=engineering)
        if empirical is not None and (not np.array_equal(table, empirical) or metadata["training_sha256"] != fitted[0][2]["training_sha256"] or metadata["selection_sha256"] != fitted[0][2]["selection_sha256"]):
            raise ValueError("Continuation fitted models do not share frozen data")
        empirical = table
        fitted.append((checkpoint, models, metadata))
    if {m["settings"]["seed"] for _, _, m in fitted} != ({42} if engineering else {42, 43, 44}) or len(fitted) != (1 if engineering else 3):
        raise ValueError("Continuation fitted-seed scope mismatch")
    preview_metadata = next(metadata for _, _, metadata in fitted if metadata["settings"]["seed"] == 42)
    rows, previews, work = [], [], []
    predictions = {}
    peak = memory_mb()
    for condition in CONDITIONS:
        data, manifest = load_continuations(checks[condition], "check")
        if manifest["engineering"] != engineering or manifest["condition"] != condition or not engineering and manifest["subjects"] != 500:
            raise ValueError("Continuation check differs from frozen scope")
        actors = {}
        for checkpoint, models, metadata in fitted:
            for kind, model in models.items():
                name = f"{kind}_{metadata['settings']['seed']}"
                start = time.perf_counter()
                actors[name] = predict_continuations(model, data["sequences"], data["contexts"])
                work.append({"actor": name, "condition": condition, "subject_predictions": len(data["sequences"]),
                             "plan_predictions": len(data["sequences"])*6, "elapsed_s": time.perf_counter()-start})
        actors["context_action_empirical"] = np.broadcast_to(empirical, data["targets"].shape).copy()
        for name, recent in (("known_law_counts", False), ("known_law_recent", True)):
            start = time.perf_counter()
            actors[name] = history_law_predictions(data["sequences"], recent=recent)
            work.append({"actor": name, "condition": condition, "plan_predictions": len(data["sequences"])*6,
                         "elapsed_s": time.perf_counter()-start,
                         "notice": "Exact declared-law integration cached for repeated probability/context/action inputs"})
        actors["latent_law_reference"] = law_predictions(audit_probabilities(checks[condition]))
        baseline = subject_losses(actors["context_action_empirical"], data["targets"])
        reference = actors["latent_law_reference"]
        for actor, prediction in actors.items():
            peak = max(peak, memory_mb())
            if time.perf_counter()-began > 180 or peak >= 1024:
                raise ValueError("Continuation evaluation budget expired; incomplete directory retained")
            predictions[f"{condition}__{actor}"] = prediction
            cells = []
            for index, (scene, action) in enumerate(CELLS):
                cell_prediction = prediction[:, index:index+1]
                cell_targets = data["targets"][:, index:index+1]
                cells.append({"scenario": scene, "action": action, "scores": scores(cell_prediction, cell_targets),
                              "outage_reliability": reliability_bins(prediction[:, index, 1], data["targets"][:, index, 1]),
                              "point_estimate_below_policy_when_latent_risk_above": int(((prediction[:, index, 1] <= .05) & (reference[:, index, 1] > .05)).sum())})
            rows.append({"condition": condition, "actor": actor, "scores": scores(prediction, data["targets"]),
                         "structural_diagnostics": structural_diagnostics(prediction),
                         "subject_paired_loss_difference_vs_empirical": paired_interval(subject_losses(prediction, data["targets"]), baseline),
                         "cells": cells, "decision_ready": False,
                         "qualification": {"per_query_failure_upper_bound": None, "applicability_shift_evidence": False,
                                           "approved_model_registry": False,
                                           "notice": "Descriptive bins cannot authorize an individual action; privileged reference is audit-only"}})
        preview_actor = "summary_mlp_42"
        for scene in ("normal", "reserve_pressure", "time_pressure"):
            preview = branch_preview(actors[preview_actor][0], scenario=scene,
                                     model_reference={"actor": preview_actor, "weights_sha256": preview_metadata["weights_sha256"],
                                                      "training_sha256": preview_metadata["training_sha256"]})
            preview["history_condition_audit_only"] = condition
            preview["observed_offline_interventions"] = [{"action": action,
                "terminal": TERMINALS[int(data["targets"][0, index, :4].argmax())],
                "any_harm": bool(data["targets"][0, index, 4]),
                "quantities": dict(zip(QUANTITIES, (data["targets"][0, index, 5:]*SCALES).tolist()))}
                for index, (context, action) in enumerate(CELLS) if context == scene]
            preview["observation_notice"] = "Separate actual offline action interventions; not inputs to predicted branches"
            previews.append(preview)
    np.savez_compressed(directory/"predictions.npz", **predictions)
    (directory/"previews.json").write_text(json.dumps(previews, indent=2, allow_nan=False), encoding="utf-8")
    report = {"status": "complete", "protocol": "public-history continuation pilot v1", "engineering": engineering,
              "fits": [{"checkpoint": str(path.resolve()), "weights_sha256": m["weights_sha256"],
                        "settings": m["settings"], "parameter_counts": m["parameter_counts"]} for path, _, m in fitted],
              "check_datasets": {condition: {"directory": str(checks[condition].resolve()),
                       "manifest_sha256": digest(checks[condition]/"manifest.json")} for condition in CONDITIONS},
              "rows": rows, "prediction_work": work, "preview_count": len(previews),
              "predictions_sha256": digest(directory/"predictions.npz"), "previews_sha256": digest(directory/"previews.json"),
              "elapsed_s": time.perf_counter()-began, "peak_sampled_memory_mb": max(peak, memory_mb()),
              "decision_ready": False, "external_spend_usd": 0,
              "scope_notice": "Whole finite simulator continuations, not general world dynamics, calibrated authority or AACE",
              "grouping_notice": "500 paired subjects per condition; six contexts/actions stay in each bootstrap subject; fitted-seed uncertainty excluded" if not engineering else "Separate engineering smoke, not measured research pilot", **provenance}
    (directory/"report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return dict(report, directory=str(directory.resolve()))


def run_continuation_pilot(output: Path, *, smoke=False):
    began = time.perf_counter(); provenance = source_provenance()
    directory = output/f"{'smoke' if smoke else 'pilot'}-continuation-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    index = {"status": "running", "protocol": "public-history continuation pilot v1", "engineering": smoke,
             "datasets": {}, "fits": [], "external_spend_usd": 0, **provenance}
    def save():
        (directory/"index.json").write_text(json.dumps(index, indent=2, allow_nan=False), encoding="utf-8")
    save()
    for split, count in (("train", 24 if smoke else 3000), ("selection", 12 if smoke else 500)):
        index["datasets"][split] = collect_continuations(split, count, directory/"data", engineering=smoke)
        save(); print(json.dumps({"event": "collected_continuations", "split": split, "subjects": count}), flush=True)
    for condition in CONDITIONS:
        name = f"check_{condition}"
        index["datasets"][name] = collect_continuations("check", 8 if smoke else 500, directory/"data", condition=condition, engineering=smoke)
        save()
    for seed in ((42,) if smoke else (42, 43, 44)):
        settings = ContinuationSettings(seed=seed, epochs=2 if smoke else 20)
        fit = train_continuations(settings, Path(index["datasets"]["train"]["directory"]),
                                  Path(index["datasets"]["selection"]["directory"]), directory/"models")
        frozen_fit(fit, engineering=smoke)
        index["fits"].append(fit); save()
        print(json.dumps({"event": "fitted_continuations", "seed": seed, "elapsed_s": fit["elapsed_s"]}), flush=True)
    result = evaluate_continuations([Path(fit["directory"]) for fit in index["fits"]],
        {c: Path(index["datasets"][f"check_{c}"]["directory"]) for c in CONDITIONS}, directory/"evaluation", engineering=smoke)
    index.update(status="complete", evaluation_directory=result["directory"], evaluation_report_sha256=digest(Path(result["directory"])/"report.json"),
                 elapsed_s=time.perf_counter()-began, decision_ready=False)
    save(); print(json.dumps({"event": "complete", "index": str((directory/"index.json").resolve())}), flush=True)
    return dict(index, directory=str(directory.resolve()))
