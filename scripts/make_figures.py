"""Draw the two paper figures from data/analysis/.  Writes figures/*.pdf and *.png.

    pip install matplotlib
    python scripts/make_figures.py
"""
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from geoutil import REPO

NAMES = {"published_rule": "Published rule", "recalibrated_rule": "Recalibrated rule",
         "logistic_regression": "Logistic regression", "decision_tree": "Decision tree",
         "bagged_trees": "Bagged trees", "random_forest": "Random forest", "adaboost": "AdaBoost",
         "gradient_boosting": "Gradient boosting"}
INK, MUTED, ACCENT, SECOND = "#1c2430", "#8a94a3", "#1f5f8b", "#b5541c"


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=7, length=2.5)
    ax.grid(axis="y", color="#e3e7ec", linewidth=0.6)
    ax.set_axisbelow(True)


def main():
    plt.rcParams.update({"font.size": 7.5, "font.family": "DejaVu Sans", "pdf.fonttype": 42})
    an, out = REPO / "data" / "analysis", REPO / "figures"
    out.mkdir(exist_ok=True)
    frozen = json.loads((REPO / "data" / "results" / "model.json").read_text())["model"]

    # Figure 1: split ablation. Tree ensembles in one colour, the frozen model in another, rules in grey.
    s = pd.read_csv(an / "split_ablation.csv").set_index("model")
    cols = ["random_pixel", "held_out_site", "held_out_region", "gujarat_pixels_at_validation_mix"]
    labels = ["Random\npixel", "Held-out\nsite", "Held-out\nregion", "Gujarat\n(post hoc)"]
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    x = np.arange(len(cols))
    groups = {"rule": (MUTED, ":"), "tree": (SECOND, "-"), "boost": (SECOND, "--")}
    kind = {"published_rule": "rule", "recalibrated_rule": "rule", "decision_tree": "tree", "bagged_trees": "tree",
            "random_forest": "tree", "adaboost": "boost", "gradient_boosting": "boost"}
    for m, k in kind.items():
        c, ls = groups[k]
        ax.plot(x, s.loc[m, cols], color=c, linestyle=ls, linewidth=0.9, marker="o", markersize=2.2, alpha=0.75)
    ax.plot(x, s.loc[frozen, cols], color=ACCENT, linewidth=1.8, marker="o", markersize=3.5, zorder=5)
    ends = {"random_forest": ("Bagged trees, random forest", 0, 0.948, "bottom"),
            "published_rule": ("Published rule", 0, 0.650, "bottom"),
            "recalibrated_rule": ("Recalibrated rule", 0, 0.759, "bottom")}
    for m, (text, xi, yv, va) in ends.items():
        ax.annotate(text, (xi, yv), xytext=(4, 4 if va == "bottom" else -4), textcoords="offset points",
                    fontsize=6.3, color=INK, va=va)
    ax.set_xticks(x, labels)
    ax.set_xlim(-0.25, len(cols) - 0.75)
    ax.set_ylim(0.4, 1.0)
    ax.set_ylabel("F1", color=INK)
    handles = [plt.Line2D([], [], color=ACCENT, linewidth=1.8, marker="o", markersize=3.5,
                          label="Logistic regression (frozen model)"),
               plt.Line2D([], [], color=SECOND, linestyle="-", linewidth=0.9, label="Trees, bagging, forest"),
               plt.Line2D([], [], color=SECOND, linestyle="--", linewidth=0.9, label="Boosting"),
               plt.Line2D([], [], color=MUTED, linestyle=":", linewidth=0.9, label="Threshold rules")]
    ax.legend(handles=handles, fontsize=6, frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.0))
    style(ax)
    fig.tight_layout(pad=0.4)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"split_ablation.{ext}", dpi=300)
    plt.close(fig)

    # Figure 2: precision against prevalence, from the Gujarat hit and false-alarm rates.
    pp = pd.read_csv(an / "split_ablation_frozen_model.csv").set_index("design")
    tpr = pp.loc["Gujarat pixels, as they are", "recall"]
    p_real = pp.loc["Gujarat pixels, as they are", "precision"]
    prev_real = p_real * 1.0  # placeholder, replaced below from the rates
    md = (an / "depth_analysis.md").read_text()
    fpr = float(md.split("the share of all other pixels flagged (")[1].split(")")[0])
    prev_real = float(md.split("where outline pixels are ")[1].split("%")[0]) / 100
    prev_val = float(md.split("rates to the ")[1].split("%")[0]) / 100
    prev = np.logspace(-4.3, np.log10(0.6), 200)
    prec = tpr * prev / (tpr * prev + fpr * (1 - prev))
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    ax.plot(prev, prec, color=ACCENT, linewidth=1.6)
    for pv, text, dx, dy, ha in ((prev_val, "Validation mix\n(41% landfill)", -6, -4, "right"),
                                 (prev_real, "Gujarat as scored\n(1 pixel in 3,800)", 0, 26, "center")):
        yv = tpr * pv / (tpr * pv + fpr * (1 - pv))
        ax.plot([pv], [yv], marker="o", markersize=4.5, color=SECOND, zorder=5)
        ax.annotate(f"{text}\nprecision {yv:.1%}" if yv < 0.1 else f"{text}\nprecision {yv:.0%}", (pv, yv),
                    xytext=(dx, dy), textcoords="offset points", fontsize=6.3, color=INK, ha=ha, va="center")
    ax.set_xscale("log")
    ax.set_xticks([1e-4, 1e-3, 1e-2, 1e-1], ["1 in 10,000", "1 in 1,000", "1 in 100", "1 in 10"])
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylim(-0.03, 1.0)
    ax.set_xlabel("Share of pixels that are landfill", color=INK)
    ax.set_ylabel("Precision of an alarm", color=INK)
    style(ax)
    fig.tight_layout(pad=0.4)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"precision_prevalence.{ext}", dpi=300)
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
