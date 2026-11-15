"""Diagnostic analysis of the training data and the three frozen models.

    pip install shap matplotlib
    python scripts/diagnostics.py

Reads the feature tables, data/results*/ (frozen models and held-out scores) and writes
data/analysis/diagnostics.md, data/analysis/diag_*.csv and figures/diag_*.pdf/png.

Questions answered here (the Gujarat side is in depth_analysis.py and alarm_diagnostics.py):
  1. Separability: can landfill pixels be told from each kind of background at all?
     - one feature at a time: AUC of every feature for landfill against each background class;
     - all features together, without a model: among a point's 15 nearest neighbours from
       other places (standardised features), how many are landfill;
     - a picture: the first two principal components.
  2. What each version still confuses in validation: share of each background class flagged
     when its region is held out.
  3. What each frozen model relies on: SHAP values, reported by feature group because
     correlated features (NDVI in two seasons, for example) share credit arbitrarily.
"""
import json
import sys

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from geoutil import REPO
from run_models import DERIVED, EXTRA, FEATURES, load_tables

SEED = 678
GROUPS = {"thermal": ["LST", "LST_anom"], "terrain": ["elev", "slope"],
          "pre-monsoon spectral": ["B2", "B3", "B4", "B8", "B11", "NDVI", "NDBI", "BSI"],
          "winter spectral": EXTRA[:5], "surroundings": EXTRA[5:] + ["NDVI_rel", "NDBI_rel"],
          "seasonal change": ["dNDVI", "dBSI"]}
GROUP_OF = {f: g for g, fs in GROUPS.items() for f in fs}
CLASSES = ["near_site", "random", "bare_soil", "quarry", "ash_pond"]
LABEL = {"near_site": "Near-site background", "random": "Random background", "bare_soil": "Bare soil",
         "quarry": "Quarry", "ash_pond": "Ash pond", "landfill": "Landfill"}
VERSIONS = {"v1": ("results", "12 features"), "v2": ("results_v2", "12 features"), "v3": ("results_v3", "26 features")}
INK, MUTED = "#1c2430", "#8a94a3"
COLOURS = {"landfill": "#b5541c", "near_site": "#c9d1dc", "random": "#8a94a3", "bare_soil": "#c9a227",
           "quarry": "#6b4c9a", "ash_pond": "#1f5f8b"}


def auc(pos, neg):
    """Probability that a landfill value is higher than a background value (0.5 means no information)."""
    r = rankdata(np.concatenate([pos, neg]))
    return (r[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def neighbour_share(Z, y, groups, k=15, pool=200):
    """For every point: the share of landfill among its k nearest neighbours from other places."""
    nn = NearestNeighbors(n_neighbors=pool + 1).fit(Z)
    out = np.full(len(Z), np.nan)
    for start in range(0, len(Z), 4000):
        idx = nn.kneighbors(Z[start:start + 4000], return_distance=False)
        for i, row in enumerate(idx):
            other = row[groups[row] != groups[start + i]][:k]
            if len(other) == k:
                out[start + i] = y[other].mean()
    return out


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=7, length=2.5)


def save(fig, name):
    out = REPO / "figures"
    out.mkdir(exist_ok=True)
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def table(frame, digits=3):
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in frame.iterrows():
        lines.append("| " + " | ".join(f"{r[c]:.{digits}f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")
    return lines


def main():
    try:
        import shap
    except ImportError:
        sys.exit("shap is needed. Run: python -m pip install shap")
    rng = np.random.default_rng(SEED)
    out = REPO / "data" / "analysis"
    sel = json.loads((REPO / "data" / "results_v3" / "selection.json").read_text(encoding="utf-8"))
    df, feats = load_tables(sel["feature_tables"], sel["extra_tables"])
    df = df.dropna(subset=feats).reset_index(drop=True)
    y = df["label"].to_numpy(int)
    cls = np.where(y == 1, "landfill", df["class"].to_numpy())
    md = ["# Diagnostics on the training data and the frozen models", "",
          f"{len(df)} points with all {len(feats)} features: {int(y.sum())} landfill, "
          + ", ".join(f"{int((cls == c).sum())} {LABEL[c].lower()}" for c in CLASSES) + ".", ""]

    # 1a. One feature at a time.
    rows = []
    for f in feats:
        v = df[f].to_numpy(float)
        rows.append({"feature": f, "group": GROUP_OF[f], **{c: auc(v[y == 1], v[cls == c]) for c in CLASSES}})
    auc_df = pd.DataFrame(rows)
    auc_df.round(3).to_csv(out / "diag_feature_auc.csv", index=False)
    strength = auc_df[CLASSES].sub(0.5).abs()
    best = pd.DataFrame({"background": [LABEL[c] for c in CLASSES],
                         "best single feature": [auc_df.loc[strength[c].idxmax(), "feature"] for c in CLASSES],
                         "its AUC": [float(auc_df.loc[strength[c].idxmax(), c]) for c in CLASSES],
                         "features with AUC outside 0.3-0.7": [int((strength[c] > 0.2).sum()) for c in CLASSES]})
    md += ["## 1. Separability", "", "### One feature at a time", "",
           "AUC of a single feature for landfill against each background class: 0.5 means the feature "
           "carries no information, 1 means landfill is always higher, 0 always lower.", ""] + table(best) + [""]
    fig, ax = plt.subplots(figsize=(3.4, 5.2))
    im = ax.imshow(auc_df[CLASSES].to_numpy(), cmap="RdBu_r", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(CLASSES)), [LABEL[c] for c in CLASSES], rotation=35, ha="right", fontsize=7)
    ax.set_yticks(range(len(feats)), feats, fontsize=6.5)
    for i in range(len(feats)):
        for j, c in enumerate(CLASSES):
            v = auc_df.loc[i, c]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=5.5, color="white" if abs(v - 0.5) > 0.3 else INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.03)
    cb.ax.tick_params(labelsize=6)
    cb.set_label("AUC, landfill against the class", fontsize=7)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    save(fig, "diag_feature_auc")

    # 1b. All features together, no model.
    rows, shares = [], {}
    for label, cols in (("12 features", FEATURES), ("26 features", feats)):
        Z = StandardScaler().fit_transform(df[cols].to_numpy(float))
        share = neighbour_share(Z, y, df["group_id"].to_numpy())
        shares[label] = share
        for c in ["landfill"] + CLASSES:
            m = (cls == c) & np.isfinite(share)
            rows.append({"class": LABEL[c], "features": label, "points": int(m.sum()),
                         "mean landfill share among neighbours": float(share[m].mean()),
                         "points with a landfill majority": float((share[m] > 0.5).mean())})
    nb = pd.DataFrame(rows)
    nb.round(4).to_csv(out / "diag_neighbours.csv", index=False)
    md += ["### All features together, without a model", "",
           "For each point, the 15 nearest points from other places in standardised feature space. "
           "Landfill is 11% of the table, so a share near 0.11 means the neighbourhood is no more "
           "landfill-like than chance.", ""] + table(nb) + [""]

    # 1c. Principal components.
    Z = StandardScaler().fit_transform(df[feats].to_numpy(float))
    pca = PCA(n_components=5, random_state=SEED).fit(Z)
    pc = pca.transform(Z)
    load = pd.DataFrame(pca.components_[:2].T, index=feats, columns=["PC1", "PC2"])
    top = {k: ", ".join(f"{f} ({load.loc[f, k]:+.2f})" for f in load[k].abs().sort_values(ascending=False).index[:5])
           for k in ("PC1", "PC2")}
    md += ["### Principal components", "",
           f"The first two components hold {pca.explained_variance_ratio_[:2].sum():.0%} of the variance of the "
           f"26 standardised features ({pca.explained_variance_ratio_[0]:.0%} and "
           f"{pca.explained_variance_ratio_[1]:.0%}); five hold {pca.explained_variance_ratio_.sum():.0%}.", "",
           f"- PC1 is mostly {top['PC1']}.", f"- PC2 is mostly {top['PC2']}.", ""]
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    for c in ["near_site", "random", "bare_soil", "quarry", "ash_pond", "landfill"]:
        idx = np.flatnonzero(cls == c)
        idx = rng.choice(idx, min(len(idx), 1500), replace=False)
        ax.scatter(pc[idx, 0], pc[idx, 1], s=2.5, color=COLOURS[c], alpha=0.55, linewidths=0, label=LABEL[c])
    lo, hi = np.percentile(pc[:, :2], [0.5, 99.5], axis=0)
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.0%} of variance)", fontsize=7, color=INK)
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.0%})", fontsize=7, color=INK)
    ax.legend(fontsize=6, frameon=False, markerscale=3, loc="best", handletextpad=0.2)
    style(ax)
    save(fig, "diag_pca")

    # 2. What each version still flags in validation.
    rows = []
    for v, (folder, _) in VERSIONS.items():
        res = REPO / "data" / folder
        model = json.loads((res / "model.json").read_text(encoding="utf-8"))["model"]
        oof = pd.read_csv(res / "oof_predictions.csv")
        flag = oof[model].to_numpy() >= 0.5
        c_oof = np.where(oof["label"] == 1, "landfill", oof["class"])
        rows.append({"version": f"{v} ({model.replace('_', ' ')})",
                     **{LABEL[c]: float(flag[c_oof == c].mean()) if (c_oof == c).any() else float("nan")
                        for c in ["landfill"] + CLASSES}})
    conf = pd.DataFrame(rows)
    conf.round(4).to_csv(out / "diag_flagged_by_class.csv", index=False)
    md += ["## 2. Share of each class flagged when its region is held out", "",
           "The landfill column is recall; every other column is a false-alarm rate. Version 1 was "
           "trained without the near-site background points, so it has no value there.", ""] + table(conf) + [""]

    # 3. SHAP by feature group.
    sample = np.concatenate([rng.choice(np.flatnonzero(cls == c), min(int((cls == c).sum()), n), replace=False)
                             for c, n in (("landfill", 1500), ("near_site", 1500), ("random", 800),
                                          ("bare_soil", 480), ("quarry", 360), ("ash_pond", 960))])
    group_rows, per_feature = [], {}
    for v, (folder, _) in VERSIONS.items():
        res = REPO / "data" / folder
        meta = json.loads((res / "model.json").read_text(encoding="utf-8"))
        model, cols = joblib.load(res / "model.joblib"), meta["features"]
        X = df.loc[sample, cols].to_numpy(float)
        if meta["model"] == "logistic_regression":  # exact for a linear model: coefficient times distance from the mean
            scaler, lr = model.steps[0][1], model.steps[1][1]
            sv = (scaler.transform(X) - scaler.transform(df[cols].to_numpy(float)).mean(axis=0)) * lr.coef_[0]
        else:
            sub = sample if meta["model"] == "gradient_boosting" else rng.choice(sample, 500, replace=False)
            X = df.loc[sub, cols].to_numpy(float)
            sv = shap.TreeExplainer(model).shap_values(X, check_additivity=False)
            sv = np.asarray(sv)
            if sv.ndim == 3:  # forests return one slice per class
                sv = sv[..., 1] if sv.shape[-1] == 2 else sv[1]
        mean_abs = np.abs(sv).mean(axis=0)
        per_feature[v] = dict(zip(cols, mean_abs / mean_abs.sum()))
        by_group = {g: float(sum(per_feature[v].get(f, 0) for f in fs)) for g, fs in GROUPS.items()}
        group_rows.append({"version": f"{v} ({meta['model'].replace('_', ' ')})", **by_group})
        print(f"  SHAP done for {v}")
    shap_groups = pd.DataFrame(group_rows)
    shap_groups.round(4).to_csv(out / "diag_shap_groups.csv", index=False)
    feat_df = pd.DataFrame(per_feature).reindex(feats).fillna(0).round(4)
    feat_df.insert(0, "group", [GROUP_OF[f] for f in feats])
    feat_df.to_csv(out / "diag_shap_features.csv", index_label="feature")
    md += ["## 3. What each frozen model relies on", "",
           "Share of the mean absolute SHAP value by feature group, on a sample of training points "
           "weighted towards landfill and look-alikes. Units differ between models (log-odds for "
           "logistic regression and gradient boosting, probability for the forest), so only the shares "
           "are comparable. Versions 1 and 2 have no winter, surroundings or change features.", ""]
    md += table(shap_groups) + ["", "Five largest single features per version:", ""]
    for v in VERSIONS:
        top5 = sorted(per_feature[v].items(), key=lambda kv: -kv[1])[:5]
        md.append(f"- {v}: " + ", ".join(f"{f} {s:.0%}" for f, s in top5))
    md.append("")
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    left = np.zeros(len(shap_groups))
    palette = ["#b5541c", "#8a94a3", "#1f5f8b", "#6b4c9a", "#c9a227", "#3a7d44"]
    for g, colour in zip(GROUPS, palette):
        ax.barh(range(len(shap_groups)), shap_groups[g], left=left, color=colour, label=g, height=0.6)
        left += shap_groups[g].to_numpy()
    ax.set_yticks(range(len(shap_groups)), shap_groups["version"], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of mean |SHAP|", fontsize=7, color=INK)
    ax.legend(fontsize=6, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.4, -0.28))
    style(ax)
    save(fig, "diag_shap_groups")

    (out / "diagnostics.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out / 'diagnostics.md'} and figures/diag_*.pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
