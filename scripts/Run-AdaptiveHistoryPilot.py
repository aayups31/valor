"""Run frozen v2 mixed-change development comparisons locally, without action authority."""

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch

from aace.benchmarks.adaptive_history import CONDITIONS,collect_adaptive
from aace.learning.history import HistoryTrainSettings,evaluate_history,train_history
from aace.telemetry import source_provenance


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("artifacts/adaptive-history-pilots"))
    args=parser.parse_args()
    directory=args.output/f"pilot-v2-{uuid4().hex[:8]}";directory.mkdir(parents=True,exist_ok=False)
    index={"protocol":"adaptive repaired-body history v2 frozen development pilot","status":"running",
        "runtime":{"python":sys.version.split()[0],"torch":torch.__version__,"numpy":np.__version__},
        "datasets":{},"fits":[],"external_spend_usd":0,**source_provenance()}
    def record():
        (directory/"index.json").write_text(json.dumps(index,indent=2,allow_nan=False),encoding="utf-8")
    record()
    for split,count in (("train",3000),("selection",500),("check",500)):
        conditions=CONDITIONS if split=="check" else ("mixed",)
        for condition in conditions:
            data=collect_adaptive(split,count,directory/"data",condition=condition)
            index["datasets"][split+"_"+condition]=data;record()
            print(json.dumps({"event":"collected","split":split,"condition":condition,"episodes":count}),flush=True)
    training=Path(index["datasets"]["train_mixed"]["directory"])
    selection=Path(index["datasets"]["selection_mixed"]["directory"])
    for seed in (42,43,44):
        print(json.dumps({"event":"training","seed":seed,"max_seconds":120,"epochs":25}),flush=True)
        model=train_history(HistoryTrainSettings(seed=seed),training,selection,directory/"models",adaptive=True)
        fit={"seed":seed,"model":model,"checks":{}};index["fits"].append(fit);record()
        for condition in CONDITIONS:
            result=evaluate_history(Path(model["directory"]),Path(index["datasets"]["check_"+condition]["directory"]),directory/"checks")
            fit["checks"][condition]=result;record()
            print(json.dumps({"event":"evaluated","seed":seed,"condition":condition,
                "brier":{name:metrics["brier"] for name,metrics in result["metrics"].items()}}),flush=True)
    aggregate={}
    for condition in CONDITIONS:
        aggregate[condition]={}
        for name in index["fits"][0]["checks"][condition]["metrics"]:
            scores={}
            for metric in ("brier","log_loss","reference_probability_rmse"):
                values=[fit["checks"][condition]["metrics"][name][metric] for fit in index["fits"]]
                scores[metric]={"mean":float(np.mean(values)),"training_seed_values":values,
                               "training_seed_standard_deviation":float(np.std(values,ddof=1))}
            groups={}
            for group in index["fits"][0]["checks"][condition]["metrics"][name]["conditional_reference_groups"]:
                rows=[fit["checks"][condition]["metrics"][name]["conditional_reference_groups"][group] for fit in index["fits"]]
                groups[group]={"count_per_fit":rows[0]["count"],"mean_reference":rows[0]["mean_reference"],
                    "mean_prediction":float(np.mean([r["mean_prediction"] for r in rows])),
                    "prediction_bias":float(np.mean([r["prediction_bias"] for r in rows]))}
            scores["conditional_reference_groups"]=groups;aggregate[condition][name]=scores
    index["aggregate"]=aggregate
    index["aggregate_notice"]="Three fitted seeds, same 500 paired check episodes per condition. Recurrence absent from fitting; not a final test or action-policy result."
    index["status"]="complete";record()
    print(json.dumps({"event":"complete","index":str((directory/"index.json").resolve())}),flush=True)


if __name__=="__main__":
    main()
