"""Figures and numbers for the paper (version 3, the frozen gradient-boosting model).

    python scripts/paper_figures.py

Reads data/results_v3/ and data/gujarat_results_v3/ and writes, in docs/Paper/figures/:
  fig_main.pdf   (a) mean F1 of every model under the three validation splits;
                 (b) expected pixel precision against landfill prevalence
  numbers.txt    the derived numbers quoted in the paper
Nothing here selects or changes a model.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/results_v3"
GUJ = ROOT / "data/gujarat_results_v3"
OUT = ROOT / "docs/Paper/figures"
MODEL = "gradient_boosting"
THRESH = 0.5

LABELS = {
    "published_rule": "Published rule",
    "recalibrated_rule": "Recalibrated rule",
    "logistic_regression": "Logistic regr.",
    "decision_tree": "Decision tree",
    "bagged_trees": "Bagged trees",
    "random_forest": "Random forest",
    "adaboost": "AdaBoost",
    "gradient_boosting": "Gradient boosting",
}


def rates():
    oof = pd.read_csv(RES / "oof_predictions.csv")
    flag = oof[MODEL] >= THRESH
    val_tpr = flag[oof.label == 1].mean()
    val_fpr_random = flag[oof["kind"] == "random"].mean()

    sites = pd.read_csv(GUJ / "site_recall.csv").dropna(subset=["pixels_scored"])
    summ = json.loads((GUJ / "summary.json").read_text())
    inside, inside_f = sites.pixels_scored.sum(), sites.pixels_flagged.sum()
    outside = summ["pixels_scored"] - inside
    outside_f = summ["pixels_flagged"] - inside_f
    return dict(
        val_tpr=val_tpr,
        val_fpr=val_fpr_random,
        guj_tpr=inside_f / inside,
        guj_fpr=outside_f / outside,
        guj_prev=inside / summ["pixels_scored"],
        guj_pixel_precision=inside_f / summ["pixels_flagged"],
    )


def precision(tpr, fpr, p):
    return tpr * p / (tpr * p + fpr * (1 - p))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(RES / "summary.csv")
    r = rates()

    plt.rcParams.update({"font.size": 6.5, "axes.spines.top": False, "axes.spines.right": False})
    fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 2.05), gridspec_kw={"width_ratios": [1.35, 1]})

    splits = [("random_pixel", "Random pixel", "#9db8d9"),
              ("held_out_site", "Held-out site", "#4a7fb5"),
              ("held_out_region", "Held-out region", "#1b3f6b")]
    models = list(LABELS)
    x = np.arange(len(models))
    w = 0.27
    for i, (split, name, col) in enumerate(splits):
        s = summary[summary.split == split].set_index("model").loc[models]
        a.bar(x + (i - 1) * w, s.f1_mean, w, yerr=s.f1_std, color=col, label=name,
              error_kw=dict(lw=0.6, capsize=1.2))
    a.set_xticks(x)
    a.set_xticklabels([LABELS[m] for m in models], rotation=30, ha="right")
    a.set_ylabel("Mean F1 (± SD across folds)")
    a.set_ylim(0, 1.18)
    a.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    a.legend(frameon=False, ncol=3, loc="upper center", fontsize=6, bbox_to_anchor=(0.5, 1.03))
    a.set_title("(a) Validation design", loc="left", fontsize=7.5)

    p = np.logspace(-4.5, np.log10(0.5), 200)
    b.plot(p, precision(r["val_tpr"], r["val_fpr"], p), color="#1b3f6b", label="Validation rates")
    b.plot(p, precision(r["guj_tpr"], r["guj_fpr"], p), color="#c0392b", ls="--", label="Gujarat rates")
    b.scatter([r["guj_prev"]], [r["guj_pixel_precision"]], color="#c0392b", zorder=3, s=12)
    b.annotate("Gujarat, measured\n(sealed sites only)", (r["guj_prev"], r["guj_pixel_precision"]),
               xytext=(1.5e-3, 6e-4), fontsize=6, arrowprops=dict(arrowstyle="-", lw=0.5))
    b.set_xscale("log")
    b.set_yscale("log")
    b.set_xlabel("Share of pixels that are landfill")
    b.set_ylabel("Pixel precision")
    b.set_ylim(2e-4, 1.5)
    b.legend(frameon=False, fontsize=6, loc="upper left")
    b.set_title("(b) Precision against prevalence", loc="left", fontsize=7.5)

    fig.tight_layout(pad=0.3, w_pad=1.2)
    fig.savefig(OUT / "fig_main.pdf")
    fig.savefig(OUT / "fig_main.png", dpi=200)

    lines = [f"{k} = {v:.6g}" for k, v in r.items()]
    for prev in (0.5, 0.1, 0.01, 0.001):
        lines.append(f"precision at prevalence {prev}: validation rates {precision(r['val_tpr'], r['val_fpr'], prev):.4f}, "
                     f"Gujarat rates {precision(r['guj_tpr'], r['guj_fpr'], prev):.4f}")
    (OUT / "numbers.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
