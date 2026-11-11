"""Fit the selected model on every training point and save it for Gujarat scoring.

    python scripts/freeze_model.py

Reads data/results/selection.json (written by run_models.py) and data/features/features.csv.
Writes data/results/model.joblib and data/results/model.json, which records the model, its
features and threshold, the scikit-learn version and, for logistic regression, the
coefficients on the standardised features. Run it after the last run_models.py and commit
both files in the freeze commit.
"""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import sklearn

from geoutil import REPO
from run_models import FEATURES, fit, make_models


def main():
    res = REPO / "data" / "results"
    sel = json.loads((res / "selection.json").read_text(encoding="utf-8"))
    name = sel["selected"]
    df = pd.read_csv(REPO / "data" / "features" / "features.csv").dropna(subset=FEATURES)
    model = fit(name, make_models()[name], df[FEATURES].to_numpy(float), df["label"].to_numpy(int))
    joblib.dump(model, res / "model.joblib")
    meta = {"model": name, "features": FEATURES, "threshold": sel["threshold"], "trained_on_points": len(df),
            "scikit_learn": sklearn.__version__}
    if name == "logistic_regression":
        scaler, lr = model.steps[0][1], model.steps[1][1]
        meta["standardised_coefficients"] = dict(zip(FEATURES, [round(float(c), 4) for c in lr.coef_[0]]))
        meta["intercept"] = round(float(lr.intercept_[0]), 4)
        meta["feature_means"] = dict(zip(FEATURES, [round(float(v), 5) for v in scaler.mean_]))
        meta["feature_sds"] = dict(zip(FEATURES, [round(float(v), 5) for v in scaler.scale_]))
    (res / "model.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"saved {name}, trained on {len(df)} points, to {res / 'model.joblib'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
