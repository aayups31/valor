"""Run the frozen v1 development pilot locally; no paid resources or UI changes."""

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch

from aace.benchmarks.history import collect_history
from aace.learning.history import HistoryTrainSettings, evaluate_history, train_history
from aace.telemetry import source_provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("artifacts/history-pilots"))
    args = parser.parse_args()
    directory = args.output/f"pilot-v1-{uuid4().hex[:8]}"
    directory.mkdir(parents=True,exist_ok=False)
    index = {"protocol":"repaired-body history probe v1 frozen development pilot",
             "status":"running","runtime":{"python":sys.version.split()[0],"torch":torch.__version__,"numpy":np.__version__},
             "datasets":{},"fits":[],"external_spend_usd":0,**source_provenance()}

    def record():
        (directory/"index.json").write_text(json.dumps(index,indent=2,allow_nan=False),encoding="utf-8")

    record()
    for split,count in (("train",3000),("selection",500),("check",500)):
        conditions = ("stable","extinction","reversal") if split == "check" else ("stable",)
        for condition in conditions:
            data = collect_history(split,count,directory/"data",condition=condition)
            index["datasets"][split+"_"+condition] = data
            record();print(json.dumps({"event":"collected","split":split,"condition":condition,"episodes":count}),flush=True)
    training = Path(index["datasets"]["train_stable"]["directory"])
    selection = Path(index["datasets"]["selection_stable"]["directory"])
    for seed in (42,43,44):
        print(json.dumps({"event":"training","seed":seed,"epoch_limit":25,"seconds_limit":120,"threads":2}),flush=True)
        result = train_history(HistoryTrainSettings(seed=seed),training,selection,directory/"models")
        fitted = {"seed":seed,"model":result,"checks":{}}
        index["fits"].append(fitted);record()
        for condition in ("stable","extinction","reversal"):
            data = Path(index["datasets"]["check_"+condition]["directory"])
            check = evaluate_history(Path(result["directory"]),data,directory/"checks")
            fitted["checks"][condition] = check
            record();print(json.dumps({"event":"evaluated","seed":seed,"condition":condition,
                "brier":{name:value["brier"] for name,value in check["metrics"].items()}}),flush=True)
    aggregate = {}
    for condition in ("stable","extinction","reversal"):
        aggregate[condition] = {}
        names = index["fits"][0]["checks"][condition]["metrics"]
        for name in names:
            scores = {}
            for metric in ("brier","log_loss","reference_probability_rmse"):
                values = [fit["checks"][condition]["metrics"][name][metric] for fit in index["fits"]]
                scores[metric] = {"mean":float(np.mean(values)),"training_seed_values":values,
                                  "training_seed_standard_deviation":float(np.std(values,ddof=1))}
            aggregate[condition][name] = scores
    index["aggregate"] = aggregate
    index["aggregate_notice"] = "Three fitted seeds on the same 500 development episodes per condition; not a final test or a calibrated survival policy"
    index["status"] = "complete";record()
    print(json.dumps({"event":"complete","index":str((directory/"index.json").resolve())}),flush=True)


if __name__ == "__main__":
    main()
