"""Train and validate the nine models on the sampled features.

    pip install scikit-learn pandas
    python scripts/run_models.py

Reads data/features/features.csv (written by gee_features.py) and writes, in data/results/:
  fold_metrics.csv     precision, recall and F1 for every model, split and fold
  summary.csv          mean and SD of those across folds
  oof_predictions.csv  each point's score from the round in which it was held out (headline split)
  selection.json       the folds used, the model the selection rule picks, and the settings
  results.md           the tables, ready to read

Everything here was fixed in docs/checklist.md before any model was run:
  - twelve features, scikit-learn defaults, class-balanced weights, threshold 0.5, no tuning;
  - headline split is leave-one-state-out over states with at least 10 kept places, or the
    Zonal Council regions when fewer than five states qualify; site-grouped and random-pixel
    five-fold splits are computed as contrast only;
  - the primary model has the best mean headline F1, unless a simpler model is within one
    standard deviation (across folds, of the best model) of it, in which case the simplest
    such model is taken.
Two details the checklist leaves open are settled here, also before any results: the
recalibrated rule keeps the published form (NDBI > a, NDVI < b, LST > c) and takes the
cut-offs with the best F1 on the training rows, searched over each feature's 5th to 95th
percentiles in steps of 5; and the SD is the sample SD (n - 1).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import AdaBoostClassifier, BaggingClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight

from geoutil import REPO, ZONAL_COUNCILS

FEATURES = ["B2", "B3", "B4", "B8", "B11", "NDVI", "NDBI", "BSI", "LST", "LST_anom", "elev", "slope"]
PUBLISHED = {"NDBI": 0.028, "NDVI": 0.15, "LST": 37.0}
SEED = 678
# Simplest first; the selection rule walks this order. The reference is never selected.
ORDER = ["published_rule", "recalibrated_rule", "logistic_regression", "decision_tree", "bagged_trees",
         "random_forest", "adaboost", "gradient_boosting"]
REFERENCE = "flag_nothing"
NEEDS_SAMPLE_WEIGHT = {"adaboost", "gradient_boosting"}  # no class_weight argument in scikit-learn


class FlagNothing(ClassifierMixin, BaseEstimator):
    def fit(self, X, y):
        return self

    def predict_proba(self, X):
        return np.column_stack([np.ones(len(X)), np.zeros(len(X))])


class ThresholdRule(ClassifierMixin, BaseEstimator):
    """Flags a pixel when NDBI > a, NDVI < b and LST > c. With refit, the cut-offs are refitted."""

    def __init__(self, refit=False):
        self.refit = refit

    def fit(self, X, y):
        self.cuts_ = dict(PUBLISHED)
        if self.refit:
            y = np.asarray(y) == 1
            grid = np.arange(5, 100, 5)
            a = np.percentile(X[:, FEATURES.index("NDBI")], grid)
            b = np.percentile(X[:, FEATURES.index("NDVI")], grid)
            c = np.percentile(X[:, FEATURES.index("LST")], grid)
            m_a = X[:, [FEATURES.index("NDBI")]] > a  # rows x cut-offs
            m_b = X[:, [FEATURES.index("NDVI")]] < b
            m_c = X[:, [FEATURES.index("LST")]] > c
            best = (-1.0, None)
            for i in range(len(grid)):
                for j in range(len(grid)):
                    both = m_a[:, i] & m_b[:, j]
                    flagged = both[:, None] & m_c
                    tp = (flagged & y[:, None]).sum(axis=0)
                    f1 = 2 * tp / np.maximum(flagged.sum(axis=0) + y.sum(), 1)
                    k = int(f1.argmax())
                    if f1[k] > best[0]:
                        best = (float(f1[k]), (a[i], b[j], c[k]))
            self.cuts_ = dict(zip(["NDBI", "NDVI", "LST"], map(float, best[1])))
        return self

    def predict_proba(self, X):
        flag = ((X[:, FEATURES.index("NDBI")] > self.cuts_["NDBI"])
                & (X[:, FEATURES.index("NDVI")] < self.cuts_["NDVI"])
                & (X[:, FEATURES.index("LST")] > self.cuts_["LST"])).astype(float)
        return np.column_stack([1 - flag, flag])


def make_models():
    return {
        REFERENCE: FlagNothing(),
        "published_rule": ThresholdRule(),
        "recalibrated_rule": ThresholdRule(refit=True),
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=1000)),
        "decision_tree": DecisionTreeClassifier(class_weight="balanced", random_state=SEED),
        "bagged_trees": BaggingClassifier(DecisionTreeClassifier(class_weight="balanced"), n_estimators=200,
                                          n_jobs=-1, random_state=SEED),
        "random_forest": RandomForestClassifier(n_estimators=500, class_weight="balanced", oob_score=True,
                                                n_jobs=-1, random_state=SEED),
        "adaboost": AdaBoostClassifier(DecisionTreeClassifier(max_depth=1), n_estimators=200, random_state=SEED),
        "gradient_boosting": GradientBoostingClassifier(random_state=SEED),
    }


def fit(name, model, X, y):
    if name in NEEDS_SAMPLE_WEIGHT:
        return model.fit(X, y, sample_weight=compute_sample_weight("balanced", y))
    return model.fit(X, y)


def headline_folds(df, min_places, min_states):
    """(unit name, {fold: row mask}) for leave-one-state-out, or leave-one-region-out as the fallback."""
    places = df[df["kind"] == "site"].groupby("state_iso")["group_id"].nunique()
    big = sorted(places[places >= min_places].index)
    if len(big) >= min_states:
        return "state", {s: (df["state_iso"] == s).to_numpy() for s in big}, places
    region = df["state_iso"].map(ZONAL_COUNCILS)
    if region.isna().any():
        raise SystemExit(f"no Zonal Council for {sorted(df.loc[region.isna(), 'state_iso'].unique())}")
    return "region", {r: (region == r).to_numpy() for r in sorted(region.unique())}, places


def kfold_masks(splitter, X, y, groups=None):
    masks = {}
    for k, (_, test) in enumerate(splitter.split(X, y, groups), 1):
        m = np.zeros(len(y), bool)
        m[test] = True
        masks[f"fold{k}"] = m
    return masks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--features", nargs="+", default=[str(REPO / "data" / "features" / "features.csv")],
                    help="one or more feature tables; version 2 adds data/features_v2/features.csv")
    ap.add_argument("--rule", choices=["simplest_within_sd", "best"], default="simplest_within_sd",
                    help="version 1 takes the simplest model within one SD of the best; version 2 takes the best")
    ap.add_argument("--out", default=str(REPO / "data" / "results"))
    ap.add_argument("--min-fold-places", type=int, default=10)
    ap.add_argument("--min-states", type=int, default=5)
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()

    df = pd.concat([pd.read_csv(f) for f in args.features], ignore_index=True)
    n_all = len(df)
    df = df.dropna(subset=FEATURES).reset_index(drop=True)
    X, y = df[FEATURES].to_numpy(float), df["label"].to_numpy(int)
    print(f"{len(df)} points with all twelve features ({n_all - len(df)} left out for missing values); "
          f"{y.sum()} landfill, {len(y) - y.sum()} other")

    unit, headline, places = headline_folds(df, args.min_fold_places, args.min_states)
    splits = {
        f"held_out_{unit}": headline,
        "held_out_site": kfold_masks(GroupKFold(n_splits=5), X, y, df["group_id"]),
        "random_pixel": kfold_masks(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED), X, y),
    }
    head = f"held_out_{unit}"

    rows, oof, cuts = [], {}, {}
    for split, folds in splits.items():
        for name in make_models():
            scores = np.full(len(y), np.nan)
            for fold, test in folds.items():
                model = fit(name, make_models()[name], X[~test], y[~test])
                scores[test] = model.predict_proba(X[test])[:, 1]
                pred = scores[test] >= args.threshold
                p, r, f1, _ = precision_recall_fscore_support(y[test], pred, average="binary", zero_division=0)
                look = (df["kind"].to_numpy()[test] == "lookalike")
                rows.append({"split": split, "model": name, "fold": fold, "n_landfill": int(y[test].sum()),
                             "n_other": int((1 - y[test]).sum()), "precision": p, "recall": r, "f1": f1,
                             "lookalike_flagged": float(pred[look].mean()) if look.any() else np.nan,
                             **{f"{k}_flagged": float(pred[df["kind"].to_numpy()[test] == k].mean())
                                for k in ("random", "near_site") if (df["kind"].to_numpy()[test] == k).any()}})
                if split == head and name == "recalibrated_rule":
                    cuts[fold] = model.cuts_
            if split == head:
                oof[name] = scores
            print(f"  {split:18} {name:20} mean F1 {np.mean([r['f1'] for r in rows if r['split'] == split and r['model'] == name]):.3f}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    folds_df = pd.DataFrame(rows)
    folds_df.to_csv(out / "fold_metrics.csv", index=False, float_format="%.4f")
    summary = (folds_df.groupby(["split", "model"], sort=False)[["precision", "recall", "f1"]]
               .agg(["mean", "std"]).round(4))
    summary.columns = [f"{m}_{s}" for m, s in summary.columns]
    summary = summary.reset_index()
    summary.to_csv(out / "summary.csv", index=False)
    keep = ["point_id", "label", "kind", "class", "group_id", "state_iso"]
    pd.concat([df[keep], pd.DataFrame(oof).round(4)], axis=1).to_csv(out / "oof_predictions.csv", index=False)

    # Selection rule, on the headline split only.
    h = summary[summary["split"] == head].set_index("model")
    best = h.loc[ORDER, "f1_mean"].idxmax()
    floor = h.loc[best, "f1_mean"] - h.loc[best, "f1_std"]
    chosen = best if args.rule == "best" else next(m for m in ORDER if h.loc[m, "f1_mean"] >= floor)
    forest = fit("random_forest", make_models()["random_forest"], X, y)
    selection = {
        "headline_split": head, "folds": {k: int(v.sum()) for k, v in headline.items()},
        "kept_places_per_state": {k: int(v) for k, v in places.sort_values(ascending=False).items()},
        "rule": args.rule, "feature_tables": [str(Path(f).resolve().relative_to(REPO)) if Path(f).resolve().is_relative_to(REPO) else Path(f).name for f in args.features],
        "best_mean_f1": best, "one_sd_floor": round(float(floor), 4), "selected": chosen,
        "random_forest_oob_accuracy": round(float(forest.oob_score_), 4),
        "recalibrated_cutoffs_per_fold": cuts, "published_cutoffs": PUBLISHED,
        "features": FEATURES, "threshold": args.threshold, "seed": SEED,
        "points_used": len(df), "points_missing_features": n_all - len(df),
    }
    (out / "selection.json").write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")

    def table(frame, cols):
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
        for _, r in frame.iterrows():
            lines.append("| " + " | ".join(f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")
        return lines

    md = [f"# Validation results", "",
          f"{len(df)} points ({int(y.sum())} landfill, {int(len(y) - y.sum())} other); "
          f"{n_all - len(df)} left out for missing features. Threshold {args.threshold}.", "",
          f"Headline split: `{head}`, folds " + ", ".join(f"{k} ({int(v.sum())} points)" for k, v in headline.items()) + ".",
          "", (f"Best mean F1: `{best}`. Simplest model within one SD of it (F1 of {floor:.3f} or more): **`{chosen}`**."
           if args.rule == "simplest_within_sd" else f"Rule: best mean F1. Selected: **`{chosen}`**."),
          f"Random forest out-of-bag accuracy on all points: {forest.oob_score_:.3f}.", "", "## Mean and SD across folds", ""]
    for split in splits:
        md += [f"### {split}", ""] + table(summary[summary["split"] == split],
                                           ["model", "precision_mean", "precision_std", "recall_mean", "recall_std",
                                            "f1_mean", "f1_std"]) + [""]
    md += [f"## Per fold, {head}", ""] + table(folds_df[folds_df["split"] == head],
                                                [c for c in ["model", "fold", "n_landfill", "n_other", "precision",
                                                             "recall", "f1", "lookalike_flagged", "random_flagged",
                                                             "near_site_flagged"] if c in folds_df.columns])
    (out / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nheadline {head}: best mean F1 {best}; selected {chosen}\nwrote {out}")


if __name__ == "__main__":
    sys.exit(main())
