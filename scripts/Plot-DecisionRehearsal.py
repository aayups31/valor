"""Plot descriptive guarded behavior; fitted-seed dots are not confidence intervals."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--report",type=Path,required=True)
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args();report=json.loads(args.report.read_text(encoding="utf-8"))
if report["status"]!="complete" or report["smoke"]:
    raise ValueError("Completed frozen behavior pilot required")
groups=[("Public careful rule",["public_careful"]),("Constant prior",["constant_prior"]),
    ("Cue counts",["cue_counts"]),("Forgetting counts",["forgetting_counts"]),("Recent window",["window_counts"]),
    ("Change detector",["change_detector"]),("Markov/Bayes ref.",["markov_bayes_reference"]),
    ("Recurrent GRU",[f"gru_{s}" for s in (42,43,44)]),("Summary MLP",[f"summary_mlp_{s}" for s in (42,43,44)])]
def total(actor,budget,field):
    return sum(row[field] for row in report["aggregate"] if row["actor"]==actor and row["budget"]==budget)
fig,axes=plt.subplots(1,2,figsize=(11,5.8),sharey=True)
colors=["#577b61"]+["#b7beb7"]*6+["#35597b","#a87744"]
for i,(label,actors) in enumerate(groups):
    completion=[100*total(a,1,"completed")/total(a,1,"episodes") for a in actors]
    missed=[100*total(a,1,"missed_feasible_tasks")/total(a,1,"oracle_feasible_episodes") for a in actors]
    for ax,values in zip(axes,(completion,missed)):
        ax.barh(i,float(np.mean(values)),height=.62,color=colors[i],zorder=2)
        if len(actors)>1:ax.scatter(values,np.full(len(values),i),s=15,color="#222222",zorder=3)
        ax.text(99 if ax is axes[0] else max(values)+.15,i,f"{np.mean(values):.1f}%",va="center",ha="right" if ax is axes[0] else "left",fontsize=9)
axes[0].set_xlim(0,100);axes[1].set_xlim(0,6)
axes[0].set_title("Completion · one guard forecast",fontsize=12,pad=18)
axes[1].set_title("Missed feasible tasks · one guard forecast",fontsize=12,pad=18)
full=100*total("public_careful",3,"completed")/total("public_careful",3,"episodes")
axes[0].axvline(full,color="#555555",linestyle="--",linewidth=1,label=f"All three guard forecasts: {full:.1f}%")
axes[0].set_yticks(range(len(groups)),[label for label,_ in groups]);axes[0].invert_yaxis()
for ax in axes:
    ax.set_axisbelow(True);ax.grid(axis="x",alpha=.17)
    ax.spines[["top","right","left"]].set_visible(False);ax.tick_params(axis="y",length=0,labelsize=10)
    ax.set_xlabel("Percent",fontsize=10)
fig.suptitle("VALOR decision rehearsal · privileged analytic guard",fontsize=15,x=.06,ha="left")
fig.text(.06,.035,"Dashed line: all three guard forecasts, 85.1% completion for every actor.\n1,200 paired task contexts per actor/budget from 100 episode IDs · predictions frozen · dots show three fitted seeds\nNo learned advantage over the public rule; this is not deployment or subjective-feeling evidence.",fontsize=9,color="#555555")
fig.tight_layout(rect=(0,.13,1,.93));args.output.parent.mkdir(parents=True,exist_ok=True)
for extension in ("png","svg"):
    fig.savefig(args.output.with_suffix("."+extension),dpi=180,facecolor="white")
plt.close(fig)
