"""Plot actual v2 development scores; point marks are fitted-seed scores, not CI."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();index=json.loads(args.index.read_text(encoding="utf-8"))
    if index["status"]!="complete":
        raise ValueError("Completed adaptive pilot required")
    names=["stateless","gru","summary_mlp","cue_counts","forgetting_counts","window_counts","change_detector","markov_bayes_reference","hidden_state_reference"]
    labels=["Current-state MLP","Recurrent GRU","Summary MLP","Cue counts","Forgetting counts","Recent window","Change detector","Markov/Bayes ref.","Hidden-state ref."]
    colors=["#b9bec4","#35597b","#a87744","#8eae95","#577b61","#577b61","#8eae95","#999999","#cccccc"]
    fig,axes=plt.subplots(1,4,figsize=(15,5.4),sharey=True)
    for ax,condition,title in zip(axes,("stable","extinction","reversal","recurrence"),("Stable danger","Danger disappears","Danger reverses","Danger returns (unseen)")):
        values=[index["aggregate"][condition][n]["brier"]["mean"] for n in names]
        ax.barh(np.arange(len(names)),values,height=.62,color=colors,zorder=2)
        for row,name in enumerate(names[:3]):
            scores=index["aggregate"][condition][name]["brier"]["training_seed_values"]
            ax.scatter(scores,np.full(len(scores),row),s=12,color="#222222",zorder=3)
        for row,name in enumerate(names):
            largest=max(index["aggregate"][condition][name]["brier"]["training_seed_values"])
            ax.text(largest+.01,row,f"{values[row]:.3f}",fontsize=8,va="center")
        ax.set_xlim(0,.36);ax.set_title(title,fontsize=11,pad=17)
        ax.set_xticks([0,.1,.2,.3]);ax.set_xlabel("Brier score (lower is better)",fontsize=9)
        ax.set_axisbelow(True);ax.grid(axis="x",alpha=.18)
        ax.spines[["top","right","left"]].set_visible(False);ax.tick_params(axis="y",length=0,labelsize=10)
    axes[0].set_yticks(np.arange(len(names)),labels);axes[0].invert_yaxis()
    fig.suptitle("VALOR adaptive history probe · frozen v2 development pilot",fontsize=15,x=.05,ha="left")
    fig.text(.05,.03,"3 fitted seeds · 500 paired episodes per condition · settings chosen on selection episodes only\nSummary MLP: 169 parameters. GRU: 1,169. Bayes knows the likelihood law; hidden-state reference has privileged information. No survival-policy or felt-fear result.",fontsize=9,color="#555555")
    fig.tight_layout(rect=(0,.13,1,.94));args.output.parent.mkdir(parents=True,exist_ok=True)
    for extension in ("png","svg"):
        fig.savefig(args.output.with_suffix("."+extension),dpi=180,facecolor="white")
    plt.close(fig)


if __name__=="__main__":
    main()
