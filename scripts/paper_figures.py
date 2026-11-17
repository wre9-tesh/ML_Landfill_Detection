"""Figures and numbers for the paper (version 3, the frozen gradient-boosting model).

    python scripts/paper_figures.py

Reads data/results_v3/, data/gujarat_results_v3/ and data/gujarat_results_v3_new/, and writes
in docs/Paper/figures/:
  fig_results.pdf  a: share of each Gujarat test site's outline flagged, both sealed lists (Q1);
                   b: what the 100 top alarms were, from the hand check
  fig_depth.pdf    a: F1 of each method under three validation designs, plus Gujarat (Q2);
                   b: pixel precision against landfill prevalence, with measured points (Q3)
  fig_*_a.pdf, fig_*_b.pdf   each panel on its own
  numbers.txt      the derived numbers quoted in the paper

Style follows the Nature figure guidelines: vector PDF with embedded TrueType fonts (editable
text), a sans-serif font (Arial or Helvetica, else the metric-compatible Liberation Sans),
text 5-7 pt, 8 pt bold lowercase panel letters, axis lines and ticks, units in parentheses,
the Okabe-Ito colour-blind-safe palette, black text with keys instead of coloured text, and
no gridlines. Nothing here selects or changes a model.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/results_v3"
GUJ = ROOT / "data/gujarat_results_v3"
NEW = ROOT / "data/gujarat_results_v3_new"
OUT = ROOT / "docs/Paper/figures"
MODEL = "gradient_boosting"
THRESH = 0.5

# Okabe-Ito palette (Wong, Nature Methods 8, 441, 2011).
BLUE, VERMILION, GREEN, ORANGE, SKY = "#0072B2", "#D55E00", "#009E73", "#E69F00", "#56B4E9"
BLACK, GREY, LIGHTGREY = "#000000", "#999999", "#D0D0D0"

MM = 1 / 25.4
FULL_W = 140 * MM          # the paper's text width (5.5 in)
PANEL_H = 50 * MM

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
HIGHLIGHT = {  # model: (colour, line style, line width)
    "gradient_boosting": (BLUE, "-", 1.5),
    "random_forest": (VERMILION, "-", 1.1),
    "logistic_regression": (GREEN, "-", 1.1),
    "published_rule": (BLACK, "--", 1.0),
}

# What the hand check saw, grouped as in the paper.
SEEN = {"bare_soil": "Bare soil", "field_or_grass": "Fields, grass", "building": "Buildings",
        "blue_roof": "Buildings", "industrial_plant": "Industrial", "riverbed": "Other",
        "other": "Other"}


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
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 6.5, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
        "legend.fontsize": 6, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def panel_letter(ax, letter):
    """8 pt bold lowercase letter at the top left of the panel, outside its tick labels."""
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    x0 = ax.get_tightbbox(renderer).transformed(fig.transFigure.inverted()).x0
    y1 = ax.get_position().y1
    fig.text(max(x0, 0.0), y1 + 0.02, letter, fontsize=8, fontweight="bold", va="bottom", ha="left")


def pct_formatter(v, _):
    v = v * 100
    return f"{v:g}"


# ---------------------------------------------------------------- panels

def draw_sites(ax):
    """Q1: share of each sealed outline flagged, both lists."""
    lists = [("First list", GUJ), ("New cities\n(unseen)", NEW)]
    rng = np.random.default_rng(0)
    for i, (_, folder) in enumerate(lists):
        s = pd.read_csv(folder / "site_recall.csv").dropna(subset=["share_flagged"])
        x = i + rng.uniform(-0.13, 0.13, len(s))
        found = (s.status == "found").to_numpy()
        y = s.share_flagged.to_numpy() * 100
        ax.scatter(x[found], y[found], s=11, color=BLUE, lw=0, zorder=3)
        ax.scatter(x[~found], y[~found], s=13, facecolor="white", edgecolor=VERMILION, lw=1, zorder=3)
        for xi, yi, city in zip(x[~found], y[~found], s.city[~found]):
            ax.annotate(city, (xi, yi), xytext=(7, -4 if yi > 40 else 0), textcoords="offset points",
                        fontsize=6, va="center")
        n_found, n = int(found.sum()), len(s)
        ax.text(i, 104, f"{n_found} of {n} found", ha="center", va="bottom", fontsize=6)
    ax.axhline(50, color=GREY, ls="--", lw=0.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([n for n, _ in lists])
    ax.set_xlim(-0.55, 1.55)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Outline flagged (%)")
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=BLUE, ms=3.5, label="Found"),
        Line2D([], [], marker="o", ls="", mfc="white", mec=VERMILION, ms=3.5, label="Missed"),
        Line2D([], [], color=GREY, ls="--", lw=0.6, label="Found threshold"),
    ], loc="lower left", bbox_to_anchor=(0.0, 0.08), handletextpad=0.3)


def draw_hand_check(ax):
    """What the 100 highest-scoring alarms were."""
    bc = pd.read_csv(GUJ / "blind_check.csv")
    groups = bc.seen.str.strip().map(SEEN)
    groups[bc.verdict == "Dump"] = "Dumpsite"
    groups[bc.verdict == "Unsure"] = "Unsure"
    order = ["Dumpsite", "Unsure", "Bare soil", "Fields, grass", "Buildings", "Industrial", "Other"]
    counts = groups.value_counts().reindex(order).fillna(0).astype(int)
    colors = [BLUE, SKY] + [GREY] * 5
    y = np.arange(len(order))[::-1]
    ax.barh(y, counts.values, color=colors, height=0.68, lw=0)
    for yi, c in zip(y, counts.values):
        ax.text(c + 0.8, yi, str(c), va="center", fontsize=6)
    ax.set_yticks(y)
    ax.set_yticklabels(order)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Alarms among the top 100 (count)")
    ax.set_xlim(0, 52)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.legend(handles=[
        plt.Rectangle((0, 0), 1, 1, color=BLUE, label="Dumpsite"),
        plt.Rectangle((0, 0), 1, 1, color=SKY, label="Unsure"),
        plt.Rectangle((0, 0), 1, 1, color=GREY, label="Look-alike"),
    ], loc="lower right", handlelength=1, handleheight=0.8, handletextpad=0.4)
    return counts


def draw_validation_design(ax, val, guj):
    """Q2: F1 under three validation designs, then Gujarat for the frozen model."""
    summary = pd.read_csv(RES / "summary.csv")
    splits = ["random_pixel", "held_out_site", "held_out_region"]
    xs = np.arange(3)
    handles = []
    for model, name in LABELS.items():
        f1 = [summary[(summary.split == s) & (summary.model == model)].f1_mean.iloc[0] for s in splits]
        col, ls, lw = HIGHLIGHT.get(model, (LIGHTGREY, "-", 0.7))
        ax.plot(xs, f1, color=col, ls=ls, lw=lw, marker="o", ms=2.2,
                zorder=3 if model in HIGHLIGHT else 2)
        if model in HIGHLIGHT:
            handles.append(Line2D([], [], color=col, ls=ls, lw=lw, marker="o", ms=2.2, label=name))
    handles.append(Line2D([], [], color=LIGHTGREY, lw=0.7, marker="o", ms=2.2, label="Other methods"))
    # Gujarat pixels at the validation class mix (frozen model only).
    p_mix = precision(guj["tpr"], guj["fpr"], val["prev"])
    f1_guj = 2 * p_mix * guj["tpr"] / (p_mix + guj["tpr"])
    gb_region = summary[(summary.split == "held_out_region") & (summary.model == MODEL)].f1_mean.iloc[0]
    ax.plot([2, 3], [gb_region, f1_guj], color=BLUE, lw=1.2, ls=":")
    ax.scatter([3], [f1_guj], marker="D", s=14, color=BLUE, zorder=4)
    handles.append(Line2D([], [], marker="D", ls="", color=BLUE, ms=3.2,
                          label="Gradient boosting,\nGujarat pixels"))
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["Random\npixel", "Held-out\nsite", "Held-out\nregion", "Gujarat"])
    ax.set_xlim(-0.25, 3.25)
    ax.set_ylim(0.3, 1.0)
    ax.set_yticks([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylabel("Mean F1")
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0, 1.0), handlelength=1.6,
              handletextpad=0.4, labelspacing=0.5)
    return f1_guj


def draw_prevalence(ax, val, guj, new):
    """Q3: expected precision against landfill prevalence, with the measured points."""
    p = np.logspace(-5, np.log10(0.6), 200)
    ax.plot(p, precision(val["tpr"], val["fpr"], p), color=BLACK, lw=1.0,
            label="Expected")
    pts = [("Validation", val, BLUE, "o"), ("First list", guj, VERMILION, "s"),
           ("New cities", new, ORANGE, "^")]
    for name, r, col, m in pts:
        ax.scatter([r["prev"]], [r["precision"]], color=col, marker=m, s=16, lw=0, zorder=3,
                   label=f"{name}, {r['precision'] * 100:.2g}%")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-5, 1)
    ax.set_ylim(1e-4, 1.5)
    for axis, ticks in ((ax.xaxis, [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1]),
                        (ax.yaxis, [1e-4, 1e-3, 1e-2, 1e-1, 1])):
        axis.set_major_locator(FixedLocator(ticks))
        axis.set_major_formatter(FuncFormatter(pct_formatter))
        axis.set_minor_locator(NullLocator())
    ax.set_xlabel("Landfill pixels (% of land)")
    ax.set_ylabel("Pixel precision (%)")
    ax.legend(loc="lower right", handletextpad=0.3, labelspacing=0.35, borderaxespad=0.1)


# ---------------------------------------------------------------- figures

def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=450)
    plt.close(fig)


def build(name, drawers, widths):
    """Whole figure with lettered panels, plus each panel as its own file."""
    fig, axes = plt.subplots(1, len(drawers), figsize=(FULL_W, PANEL_H),
                             gridspec_kw={"width_ratios": widths})
    results = []
    for ax, draw in zip(axes, drawers):
        results.append(draw(ax))
    fig.tight_layout(pad=0.4, w_pad=2.2, rect=(0, 0, 1, 0.94))
    for ax, letter in zip(axes, "ab"):
        panel_letter(ax, letter)
    save(fig, name)
    for letter, draw, w in zip("ab", drawers, widths):
        f, ax = plt.subplots(figsize=(FULL_W * w / sum(widths) + 8 * MM, PANEL_H))
        draw(ax)
        f.tight_layout(pad=0.4)
        save(f, f"{name}_{letter}")
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in ("fig_main.pdf", "fig_main.png"):
        (OUT / old).unlink(missing_ok=True)
    style()
    val, guj, new = validation_rates(), pixel_rates(GUJ), pixel_rates(NEW)

    _, counts = build("fig_results", [draw_sites, draw_hand_check], [1, 1.1])
    f1_guj, _ = build("fig_depth", [lambda ax: draw_validation_design(ax, val, guj),
                                    lambda ax: draw_prevalence(ax, val, guj, new)], [1.35, 1])

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
