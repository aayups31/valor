"""Frozen estimator rehearsal runner; model outputs have proposal authority only."""

import json
import time
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch

from aace.benchmarks.adaptive_history import CONDITIONS,episode
from aace.benchmarks.rehearsal import SCENARIOS,rehearse
from aace.learning.adaptive_controls import predict_control
from aace.learning.history import ADAPTIVE_VERSION,load_history_model,paired_interval
from aace.learning.resources import digest,memory_mb
from aace.telemetry import source_provenance


def frozen_predictions(index_path,sequences):
    source=json.loads(index_path.read_text(encoding="utf-8"))
    if source.get("status")!="complete" or len(source.get("fits",[]))!=3 or {f["seed"] for f in source["fits"]}!={42,43,44}:
        raise ValueError("Rehearsal requires the completed three-seed v2 pilot")
    output,metadata,timings={},{},{}
    first=None
    x=torch.from_numpy(sequences)
    for fit in source["fits"]:
        checkpoint=Path(fit["model"]["directory"])
        models,m=load_history_model(checkpoint)
        if m["model_version"]!=ADAPTIVE_VERSION or m["weights_sha256"]!=fit["model"]["weights_sha256"] or m["settings"]["seed"]!=fit["seed"] or m["settings"]["epochs"]!=25 or m["training_episodes"]!=3000 or m["selection_episodes"]!=500:
            raise ValueError("Rehearsal estimator differs from frozen v2 recipe")
        if first is None:first=m
        elif any(m[k]!=first[k] for k in ("training_sha256","selection_sha256","training_prevalence")) or m["adaptive_controls"]["settings"]!=first["adaptive_controls"]["settings"]:
            raise ValueError("Frozen estimators have mismatched data/control settings")
        with torch.no_grad():
            for kind in ("gru","summary_mlp"):
                name=f"{kind}_{fit['seed']}"
                began=time.perf_counter()
                output[name]=torch.sigmoid(models[kind](x)).numpy().ravel()
                timings[name]={"batch_episodes":len(x),"elapsed_s":time.perf_counter()-began}
                metadata[name]={"kind":"experimental_learned_proposal","seed":fit["seed"],"checkpoint":str(checkpoint),
                    "weights_sha256":m["weights_sha256"],"parameter_count":m["parameter_counts"][kind],"decision_ready":False}
    for name,spec in first["adaptive_controls"]["settings"].items():
        began=time.perf_counter()
        output[name]=predict_control(sequences,spec,first["adaptive_controls"]["prior"])
        timings[name]={"batch_episodes":len(x),"elapsed_s":time.perf_counter()-began}
        metadata[name]={"kind":"frozen_history_control","setting":spec,"prior":first["adaptive_controls"]["prior"]}
    output["constant_prior"]=np.full(len(x),first["training_prevalence"])
    metadata["constant_prior"]={"kind":"training_prior","probability":first["training_prevalence"]}
    if any(p.shape!=(len(x),) or not np.isfinite(p).all() or np.any((p<0)|(p>1)) for p in output.values()):
        raise ValueError("Invalid frozen prediction output")
    return output,metadata,timings


def aggregate_records(records):
    groups={}
    for row in records:
        key=(row["condition"],row["scenario"],row["budget"],row["actor"])
        groups.setdefault(key,[]).append(row)
    result=[]
    numeric=("harm_received","recovery_units","resource_used","elapsed_s","guard_forecasts","guard_rejections","decision_ms","proposal_ms")
    for key,rows in sorted(groups.items()):
        result.append({"condition":key[0],"scenario":key[1],"budget":key[2],"actor":key[3],"episodes":len(rows),
            "completed":sum(r["completed"] for r in rows),"failed":sum(r["failed"] for r in rows),
            "abandoned":sum(r["status"]=="abandoned" for r in rows),"abstained":sum(r["status"]=="abstained" for r in rows),
            "missed_feasible_tasks":sum(r["missed_feasible_task"] for r in rows),
            "oracle_feasible_episodes":sum(bool(r["oracle_feasible_tasks"]) for r in rows),
            "urgency_overrides":sum(r["urgency_overrode_order"] for r in rows),
            "means":{n:float(np.mean([r[n] for r in rows])) for n in numeric}})
    return result


def run_rehearsal(index_path: Path,output: Path,*,smoke=False):
    began=time.perf_counter();provenance=source_provenance()
    count,start=(2,17000) if smoke else (100,16000)
    seeds=np.arange(start,start+count,dtype=np.int64)
    sequences,latent,ignored_labels=[],[],[]
    for condition in CONDITIONS:
        rows=[episode(int(seed),condition) for seed in seeds]
        sequences.extend(r[0] for r in rows);latent.extend(r[2] for r in rows);ignored_labels.extend(r[1] for r in rows)
    x=np.stack(sequences)
    probabilities,actors,timings=frozen_predictions(index_path,x)
    for name in ("always_fast","always_careful","always_preserve","public_careful"):
        actors[name]={"kind":"fixed_public_rule"}
    if len(actors)!=16:raise ValueError("Frozen actor count changed")
    directory=output/f"{'smoke' if smoke else 'pilot'}-rehearsal-{uuid4().hex[:8]}"
    directory.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(directory/"probes.npz",sequences=x,episode_seeds=np.tile(seeds,len(CONDITIONS)),
        latent_probability=np.asarray(latent),ignored_query_labels=np.asarray(ignored_labels))
    np.savez_compressed(directory/"predictions.npz",**probabilities)
    progress={"status":"running","protocol":"guarded decision rehearsal v1","smoke":smoke,
        "frozen_index_sha256":digest(index_path),"actors":actors,"prediction_work":timings,
        "episode_seeds":[int(seeds.min()),int(seeds.max())],"paired_subjects_per_condition":count,
        "probe_sha256":digest(directory/"probes.npz"),"predictions_sha256":digest(directory/"predictions.npz"),
        "external_spend_usd":0,**provenance}
    def save():
        (directory/"report.json").write_text(json.dumps(progress,indent=2,allow_nan=False),encoding="utf-8")
    save();print(json.dumps({"event":"loaded_frozen_estimators","actors":len(actors),"subjects":count,"smoke":smoke}),flush=True)
    records,examples=[],[];peak=memory_mb()
    with (directory/"episodes.jsonl").open("w",encoding="utf-8") as stream:
        for ci,condition in enumerate(CONDITIONS):
            for scenario in SCENARIOS:
                for budget in (1,3):
                    for actor,meta in actors.items():
                        for i,seed in enumerate(seeds):
                            if len(records)%100==0:
                                peak=max(peak,memory_mb())
                                if time.perf_counter()-began>=180 or peak>=1024:
                                    progress.update(status="budget_expired",records=len(records),elapsed_s=time.perf_counter()-began,
                                                    peak_sampled_memory_mb=peak);save()
                                    raise ValueError("Rehearsal budget expired; incomplete artifacts retained")
                            position=ci*count+i
                            kwargs={"fixed":actor} if meta["kind"]=="fixed_public_rule" else {"probability":float(probabilities[actor][position])}
                            result=rehearse(scenario,int(seed),float(latent[position]),max_forecasts=budget,include_trace=i==0,**kwargs)
                            result.update(actor=actor,condition=condition,budget=budget)
                            if i==0:
                                examples.append(result)
                                result={k:v for k,v in result.items() if k not in ("decision_trace","proposal_estimates","retrospective_audit","actual_state")}
                            records.append(result);stream.write(json.dumps(result,allow_nan=False)+"\n")
                    print(json.dumps({"event":"rehearsed","condition":condition,"scenario":scenario,"budget":budget,"records":len(records)}),flush=True)
    # Paired comparisons against the strongest fixed rule, not a weak predictor.
    paired=[]
    for condition in CONDITIONS:
        for scenario in SCENARIOS:
            for budget in (1,3):
                selected=[r for r in records if r["condition"]==condition and r["scenario"]==scenario and r["budget"]==budget]
                baseline=sorted([r for r in selected if r["actor"]=="public_careful"],key=lambda r:r["seed"])
                for actor in actors:
                    rows=sorted([r for r in selected if r["actor"]==actor],key=lambda r:r["seed"])
                    for metric in ("completed","missed_feasible_task"):
                        interval=paired_interval(np.array([r[metric] for r in rows],dtype=float),
                                                 np.array([r[metric] for r in baseline],dtype=float))
                        paired.append({"condition":condition,"scenario":scenario,"budget":budget,"actor":actor,"metric":metric,**interval})
    (directory/"examples.json").write_text(json.dumps(examples,indent=2,allow_nan=False),encoding="utf-8")
    progress.update({"status":"complete","records":len(records),"aggregate":aggregate_records(records),
        "paired_differences_against_public_careful":paired,"elapsed_s":time.perf_counter()-began,
        "peak_sampled_memory_mb":max(peak,memory_mb()),"records_sha256":digest(directory/"episodes.jsonl"),
        "examples_sha256":digest(directory/"examples.json"),"examples":len(examples),
        "total_qualified_guard_forecasts":sum(r["guard_forecasts"] for r in records),
        "total_experimental_proposal_transforms":sum(r["proposal_transforms"] for r in records),
        "total_retrospective_forecasts":sum(r["retrospective_forecasts"] for r in records),
        "notice":"Offline controlled tasks with privileged analytic guard; experimental proposals only, not deployment or felt-fear evidence",
        "work_notice":"Qualified guard budgets matched, not total computation. Prediction batches, proxy transforms and audits recorded separately."})
    save();print(json.dumps({"event":"complete","report":str((directory/"report.json").resolve()),"records":len(records)}),flush=True)
    return dict(progress,directory=str(directory.resolve()))
