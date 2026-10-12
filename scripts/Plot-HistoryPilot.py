"""Plot saved pilot measurements; dots show fitted-seed variability, not CI."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True,help="Output stem, without extension")
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding="utf-8"))
    if index["status"] != "complete":
        raise ValueError("A completed pilot is required")
    names = ["stateless","history_linear","history_mlp","gru","cue_counts","public_history_bayes","hidden_state_reference"]
    labels = ["Current-state MLP","Full-history linear","Full-history MLP","Recurrent GRU","Simple cue counts","Known-law Bayes","Hidden-state reference"]
    colors = ["#b9bec4","#b9bec4","#b9bec4","#35597b","#577b61","#999999","#cccccc"]
    fig,axes = plt.subplots(1,3,figsize=(12,4.8),sharey=True)
    for ax,condition,title in zip(axes,("stable","extinction","reversal"),("Stable danger","Danger disappears","Danger reverses")):
        values = [index["aggregate"][condition][name]["brier"]["mean"] for name in names]
        ax.barh(np.arange(len(names)),values,color=colors,height=.58,zorder=2)
        for row,name in enumerate(names[:4]):
            seeds = index["aggregate"][condition][name]["brier"]["training_seed_values"]
            ax.scatter(seeds,np.full(len(seeds),row),s=15,color="#222222",zorder=3)
        ax.set_xlim(0,.5);ax.set_title(title,fontsize=12,pad=17)
        ax.set_xlabel("Brier score (lower is better)",fontsize=10)
        ax.set_axisbelow(True);ax.grid(axis="x",alpha=.18)
        ax.spines[["top","right","left"]].set_visible(False)
        ax.tick_params(axis="y",length=0,labelsize=10)
        for row,value in enumerate(values):
            largest = max(index["aggregate"][condition][names[row]]["brier"]["training_seed_values"])
            ax.text(max(value,largest)+.012,row,f"{value:.3f}",va="center",fontsize=8,color="#444444")
    axes[0].set_yticks(np.arange(len(names)),labels)
    axes[0].invert_yaxis()
    fig.suptitle("VALOR repaired-body history probe · development pilot",fontsize=15,x=.06,ha="left")
    fig.text(.06,.03,"3 fitted seeds · 500 paired episodes per condition · dots show fitted-seed scores\nBayes knows the stable generation law; the hidden-state reference has privileged information. No action-policy or felt-fear result.",fontsize=9,color="#555555")
    fig.tight_layout(rect=(0,.13,1,.94))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for extension in ("png","svg"):
        fig.savefig(args.output.with_suffix("."+extension),dpi=180,facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
