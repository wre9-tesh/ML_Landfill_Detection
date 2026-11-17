"""Figures and numbers for the paper (version 3, the frozen gradient-boosting model).

    python scripts/paper_figures.py

Reads data/results_v3/, data/gujarat_results_v3/ and data/gujarat_results_v3_new/, and writes
in docs/Paper/figures/:
  fig_results.pdf  (a) share of each Gujarat test site's outline flagged, both sealed lists (Q1);
                   (b) what the 100 top alarms were, from the hand check
  fig_depth.pdf    (a) F1 of each method under three validation designs, plus Gujarat (Q2);
                   (b) pixel precision against landfill prevalence, with measured points (Q3)
  numbers.txt      the derived numbers quoted in the paper
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
NEW = ROOT / "data/gujarat_results_v3_new"
OUT = ROOT / "docs/Paper/figures"
MODEL = "gradient_boosting"
THRESH = 0.5

DARK, MID, LIGHT, RED, GREY = "#1b3f6b", "#4a7fb5", "#9db8d9", "#c0392b", "#9a9a9a"

LABELS = {
    "published_rule": "Published rule",
    "recalibrated_rule": "Recalibrated rule",
    "logistic_regression": "Logistic regression",
    "decision_tree": "Decision tree",
    "bagged_trees": "Bagged trees",
    "random_forest": "Random forest",
    "adaboost": "AdaBoost",
    "gradient_boosting": "Gradient boosting",
}

# What the hand check saw, grouped as in the paper.
SEEN = {"bare_soil": "Bare soil", "field_or_grass": "Fields, grass", "building": "Buildings",
        "blue_roof": "Buildings", "industrial_plant": "Industrial", "riverbed": "Other",
        "other": "Other"}


def pct(x):
    return f"{x:.0%}" if x >= 0.1 else f"{x * 100:.2g}%"


def precision(tpr, fpr, p):
    return tpr * p / (tpr * p + fpr * (1 - p))


def pixel_rates(folder):
    sites = pd.read_csv(folder / "site_recall.csv").dropna(subset=["pixels_scored"])
    summ = json.loads((folder / "summary.json").read_text())
    inside, inside_f = sites.pixels_scored.sum(), sites.pixels_flagged.sum()
    outside = summ["pixels_scored"] - inside
    outside_f = summ["pixels_flagged"] - inside_f
    return dict(tpr=inside_f / inside, fpr=outside_f / outside,
                prev=inside / summ["pixels_scored"], precision=inside_f / summ["pixels_flagged"])


def validation_rates():
    oof = pd.read_csv(RES / "oof_predictions.csv")
    flag = oof[MODEL] >= THRESH
    tp = (flag & (oof.label == 1)).sum()
    fp = (flag & (oof.label == 0)).sum()
    return dict(tpr=flag[oof.label == 1].mean(), fpr=flag[oof["kind"] == "random"].mean(),
                prev=(oof.label == 1).mean(), precision=tp / (tp + fp))


def style():
    plt.rcParams.update({"font.size": 6.5, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titlesize": 7.5, "axes.titlelocation": "left", "legend.frameon": False})


def fig_results():
    fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 1.95), gridspec_kw={"width_ratios": [1, 1.15]})

    # (a) Q1: share of each sealed outline flagged.
    lists = [("First list\n(16 of 17 found)", GUJ, MID), ("New cities, unseen\n(5 of 6 found)", NEW, DARK)]
    rng = np.random.default_rng(0)
    for i, (name, folder, col) in enumerate(lists):
        s = pd.read_csv(folder / "site_recall.csv").dropna(subset=["share_flagged"])
        x = i + rng.uniform(-0.12, 0.12, len(s))
        found = s.status == "found"
        a.scatter(x[found], s.share_flagged[found], s=10, color=col, zorder=3)
        a.scatter(x[~found], s.share_flagged[~found], s=14, facecolor="white", edgecolor=RED, lw=1, zorder=3)
        for xi, (_, row) in zip(x[~found], s[~found].iterrows()):
            a.annotate(row.city, (xi, row.share_flagged), xytext=(6, -2), textcoords="offset points",
                       fontsize=6, color=RED)
    a.axhline(0.5, color=GREY, ls="--", lw=0.7)
    a.text(1.45, 0.51, "found if ≥ half\nflagged", fontsize=5.5, color=GREY, va="bottom", ha="right")
    a.set_xticks([0, 1])
    a.set_xticklabels([n for n, _, _ in lists])
    a.set_xlim(-0.5, 1.5)
    a.set_ylim(0, 1.05)
    a.set_ylabel("Share of site outline flagged")
    a.set_title("(a) Gujarat test sites")

    # (b) What the 100 top alarms were.
    bc = pd.read_csv(GUJ / "blind_check.csv")
    groups = bc.seen.str.strip().map(SEEN)
    groups[bc.verdict == "Dump"] = "Dumpsite"
    groups[bc.verdict == "Unsure"] = "Unsure"
    order = ["Dumpsite", "Unsure", "Bare soil", "Fields, grass", "Buildings", "Industrial", "Other"]
    counts = groups.value_counts().reindex(order).fillna(0).astype(int)
    colors = [DARK, LIGHT] + [GREY] * 5
    y = np.arange(len(order))[::-1]
    b.barh(y, counts.values, color=colors, height=0.7)
    for yi, c in zip(y, counts.values):
        b.text(c + 0.8, yi, str(c), va="center", fontsize=6)
    b.set_yticks(y)
    b.set_yticklabels(order)
    b.set_xlabel("Alarms among the top 100")
    b.set_xlim(0, 55)
    b.set_title("(b) Hand check of the top 100 alarms")

    fig.tight_layout(pad=0.3, w_pad=1.5)
    fig.savefig(OUT / "fig_results.pdf")
    fig.savefig(OUT / "fig_results.png", dpi=200)
    return counts


def fig_depth(val, guj, new):
    summary = pd.read_csv(RES / "summary.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 2.0), gridspec_kw={"width_ratios": [1.1, 1]})

    # (a) Q2: F1 under three validation designs, and Gujarat for the frozen model.
    splits = ["random_pixel", "held_out_site", "held_out_region"]
    xs = np.arange(4)
    highlight = {"gradient_boosting": (DARK, 1.6), "random_forest": (RED, 1.2),
                 "logistic_regression": (MID, 1.2), "published_rule": (GREY, 1.2)}
    for model, name in LABELS.items():
        f1 = [summary[(summary.split == s) & (summary.model == model)].f1_mean.iloc[0] for s in splits]
        col, lw = highlight.get(model, ("#d5d5d5", 0.7))
        a.plot(xs[:3], f1, color=col, lw=lw, marker="o", ms=2.2, zorder=3 if model in highlight else 2)
        if model in highlight:
            a.text(-0.16, f1[0], name, ha="right", va="center", fontsize=5.8, color=col)
    # Gujarat pixels at the validation class mix (frozen model only).
    p_mix = precision(guj["tpr"], guj["fpr"], val["prev"])
    f1_guj = 2 * p_mix * guj["tpr"] / (p_mix + guj["tpr"])
    gb_region = summary[(summary.split == "held_out_region") & (summary.model == MODEL)].f1_mean.iloc[0]
    a.plot([2, 3], [gb_region, f1_guj], color=DARK, lw=1.6, ls=":")
    a.scatter([3], [f1_guj], marker="*", s=40, color=DARK, zorder=4)
    a.set_xticks(xs)
    a.set_xticklabels(["Random\npixel", "Held-out\nsite", "Held-out\nregion", "Gujarat\npixels*"])
    a.set_xlim(-1.8, 3.3)
    a.set_ylim(0.3, 1.0)
    a.set_ylabel("Mean F1")
    a.set_title("(a) Validation design")

    # (b) Q3: precision against prevalence, with the three measured points.
    p = np.logspace(-5, np.log10(0.6), 200)
    b.plot(p, precision(val["tpr"], val["fpr"], p), color=DARK, lw=1.2, label="Expected, validation rates")
    pts = [("Validation", val, MID), ("Gujarat, first list", guj, RED), ("Gujarat, new cities", new, RED)]
    offs = [(-6, 5, "right"), (6, -2, "left"), (6, -2, "left")]
    for (name, r, col), (dx, dy, ha) in zip(pts, offs):
        b.scatter([r["prev"]], [r["precision"]], color=col, s=14, zorder=3)
        b.annotate(f"{name}\n{pct(r['precision'])}", (r["prev"], r["precision"]), xytext=(dx, dy),
                   textcoords="offset points", fontsize=5.5, ha=ha, va="center", color=col)
    b.set_xscale("log")
    b.set_yscale("log")
    b.set_ylim(2e-4, 1.5)
    b.set_xlabel("Share of pixels that are landfill")
    b.set_ylabel("Pixel precision")
    b.legend(fontsize=5.5, loc="lower right")
    b.set_title("(b) Precision against prevalence")

    fig.tight_layout(pad=0.3, w_pad=1.5)
    fig.savefig(OUT / "fig_depth.pdf")
    fig.savefig(OUT / "fig_depth.png", dpi=200)
    return f1_guj


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    style()
    val, guj, new = validation_rates(), pixel_rates(GUJ), pixel_rates(NEW)
    counts = fig_results()
    f1_guj = fig_depth(val, guj, new)

    lines = []
    for name, r in [("validation", val), ("gujarat_first", guj), ("gujarat_new", new)]:
        lines += [f"{name}_{k} = {v:.6g}" for k, v in r.items()]
    lines.append(f"gujarat_first F1 at the validation class mix = {f1_guj:.4f}")
    for prev in (0.5, 0.1, 0.01, 0.001):
        lines.append(f"precision at prevalence {prev}: validation rates "
                     f"{precision(val['tpr'], val['fpr'], prev):.4f}, Gujarat rates "
                     f"{precision(guj['tpr'], guj['fpr'], prev):.4f}")
    lines.append("top-100 hand check: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    (OUT / "numbers.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
