"""Plot fresh structured predictions and equally informed controls."""
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
if report["status"] != "complete" or report["engineering"] or report["protocol"] != "structured consequence pilot v2":
    raise ValueError("Completed frozen structured research pilot required")
groups = [("Context/action table", ["context_action_empirical"]),
    ("Plug-in all counts", ["known_law_counts"]), ("Plug-in recent counts", ["known_law_recent"]),
    ("Likelihood all counts", ["likelihood_mixture_counts"]), ("Likelihood recent counts", ["likelihood_mixture_recent"]),
    ("Structured constant", [f"structured_constant_{s}" for s in (42, 43, 44)]),
    ("Structured linear", [f"structured_summary_linear_{s}" for s in (42, 43, 44)]),
    ("Structured summary MLP", [f"structured_summary_mlp_{s}" for s in (42, 43, 44)]),
    ("Structured recurrent GRU", [f"structured_gru_{s}" for s in (42, 43, 44)]),
    ("Historical raw MLP", [f"historical_summary_mlp_{s}" for s in (42, 43, 44)]),
    ("Latent-law audit", ["latent_law_reference"])]
metrics = [("Terminal log loss", lambda s: s["terminal_log_loss"]),
           ("Irreversible outage Brier", lambda s: s["outage"]["brier"]),
           ("Experienced harm Brier", lambda s: s["any_harm"]["brier"])]
colors = ["#577b61"]+["#b7beb7"]*4+["#577b61", "#a87744", "#a87744", "#35597b", "#bbbbbb", "#dddddd"]
fig, axes = plt.subplots(1, 3, figsize=(13, 7), sharey=True)
for ax, (title, metric) in zip(axes, metrics):
    samples = [[float(np.mean([metric(row["scores"]) for row in report["rows"] if row["actor"] == actor]))
                for actor in actors] for _, actors in groups]
    maximum = max(max(values) for values in samples); ax.set_xlim(0, maximum*1.3)
    for index, (values, color) in enumerate(zip(samples, colors)):
        ax.barh(index, np.mean(values), height=.62, color=color, zorder=2)
        if len(values) > 1:
            ax.scatter(values, np.full(len(values), index), s=16, color="#222222", zorder=3)
        ax.text(max(values)+maximum*.035, index, f"{np.mean(values):.4f}", va="center", fontsize=9)
    ax.set_title(title, fontsize=12, pad=18); ax.set_xlabel("Lower is better", fontsize=10)
    ax.set_axisbelow(True); ax.grid(axis="x", alpha=.17)
    ax.spines[["top", "right", "left"]].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10)
axes[0].set_yticks(range(len(groups)), [label for label, _ in groups]); axes[0].invert_yaxis()
fig.suptitle("VALOR · coherent consequences from declared physics", fontsize=16, x=.05, ha="left")
fig.text(.05, .035, "Fresh 500 paired IDs × four history conditions × six context/action interventions · dots show three fitted seeds\nStructured and likelihood models share supplied physics; historical raw heads lack that decoder.\nCoherence is a scoped construction property, not risk calibration, subjective fear or action permission.", fontsize=9, color="#555555")
fig.tight_layout(rect=(0, .13, 1, .93)); args.output.parent.mkdir(parents=True, exist_ok=True)
for extension in ("png", "svg"):
    fig.savefig(args.output.with_suffix("."+extension), dpi=180, facecolor="white")
print(json.dumps({"figures": [str(args.output.with_suffix("."+e).resolve()) for e in ("png", "svg")]}))
