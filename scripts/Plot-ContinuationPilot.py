"""Plot measured continuation scores; dots are fitted seeds, not confidence bounds."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--report", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
report = json.loads(args.report.read_text(encoding="utf-8"))
if report["status"] != "complete" or report["engineering"]:
    raise ValueError("Completed frozen research pilot required")
groups = [("Context/action table", ["context_action_empirical"]), ("Known-law cue counts", ["known_law_counts"]),
          ("Known-law recent counts", ["known_law_recent"]),
          ("Linear summary", [f"summary_linear_{s}" for s in (42, 43, 44)]),
          ("Summary MLP", [f"summary_mlp_{s}" for s in (42, 43, 44)]),
          ("Recurrent GRU", [f"gru_{s}" for s in (42, 43, 44)]),
          ("Latent-law audit", ["latent_law_reference"])]
metrics = [("Terminal log loss", lambda s: s["terminal_log_loss"]),
           ("Irreversible outage Brier", lambda s: s["outage"]["brier"]),
           ("Experienced harm Brier", lambda s: s["any_harm"]["brier"])]
colors = ["#577b61", "#b7beb7", "#b7beb7", "#a87744", "#a87744", "#35597b", "#dddddd"]
fig, axes = plt.subplots(1, 3, figsize=(13, 5.5), sharey=True)
for ax, (title, metric) in zip(axes, metrics):
    values = [[float(np.mean([metric(row["scores"]) for row in report["rows"] if row["actor"] == actor]))
               for actor in actors] for _, actors in groups]
    maximum = max(max(v) for v in values)
    ax.set_xlim(0, maximum*1.28)
    for index, (samples, color) in enumerate(zip(values, colors)):
        ax.barh(index, np.mean(samples), height=.6, color=color, zorder=2)
        if len(samples) > 1:
            ax.scatter(samples, np.full(len(samples), index), s=16, color="#222222", zorder=3)
        ax.text(max(samples)+maximum*.035, index, f"{np.mean(samples):.4f}", va="center", fontsize=9)
    ax.set_title(title, fontsize=12, pad=18)
    ax.set_xlabel("Lower is better", fontsize=10)
    ax.set_axisbelow(True); ax.grid(axis="x", alpha=.17)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=10)
axes[0].set_yticks(range(len(groups)), [label for label, _ in groups]); axes[0].invert_yaxis()
fig.suptitle("VALOR · predicting the consequences of proposed actions", fontsize=16, x=.05, ha="left")
fig.text(.05, .035, "Equal means over four history conditions · 500 paired subjects per condition · dots show three fitted seeds\nKnown-law controls use declared transition equations; latent-law reference has hidden risk access.\nWhole-plan simulator forecasts only · no per-query upper bounds or authority qualification", fontsize=9, color="#555555")
fig.tight_layout(rect=(0, .15, 1, .92)); args.output.parent.mkdir(parents=True, exist_ok=True)
for extension in ("png", "svg"):
    fig.savefig(args.output.with_suffix("."+extension), dpi=180, facecolor="white")
print(json.dumps({"figures": [str(args.output.with_suffix("."+e).resolve()) for e in ("png", "svg")]}))
