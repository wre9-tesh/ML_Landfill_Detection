"""Why were the Gujarat alarms flagged? Feature values, novelty and SHAP for the top alarms.

    python scripts/alarm_diagnostics.py            (on the machine holding the Gujarat GeoTIFFs)
    python scripts/alarm_diagnostics.py --no-extract     (anywhere, once alarm_features.csv exists)

Step 1 (needs data/gujarat/ and data/gujarat_x/): reads the 26 features at the centre of the top
100 alarms of each version and at the centre of each sealed site (median of the 3 x 3 pixels
around it) and writes data/analysis/alarm_features.csv.

Step 2 (needs only that table): joins the blind-check verdicts where they exist and writes
data/analysis/alarm_diagnostics.md and diag_alarm_*.csv:
  - novelty: how far each centre is from the training points, as the percentile of its mean
    distance to the 15 nearest training points among the training points' own such distances.
    Above the 99th percentile the model is extrapolating.
  - nearest training class: what the 15 nearest training points are.
  - SHAP by feature group for the version 3 model: what pushed each kind of alarm over 0.5.
"""
import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from diagnostics import GROUPS, table
from geoutil import REPO
from run_models import DERIVED, EXTRA, FEATURES, load_tables

RESULTS = {"v1": "gujarat_results", "v2": "gujarat_results_v2", "v3": "gujarat_results_v3"}
FETCHED = FEATURES + EXTRA


def centres(top):
    rows = []
    for v, folder in RESULTS.items():
        path = REPO / "data" / folder / "alarms.csv"
        if not path.exists():
            continue
        a = pd.read_csv(path).head(top)
        rows += [{"kind": "alarm", "version": v, "id": r.blind_id, "rank": int(r["rank"]), "city": r.city,
                  "lat": r.lat, "lon": r.lon, "area_ha": r.area_ha, "mean_score": r.mean_score}
                 for _, r in a.iterrows()]
    for f in json.load(open(REPO / "labels" / "gujarat_test_sites.geojson", encoding="utf-8"))["features"]:
        g = f["geometry"]
        if g["type"] == "Point":
            continue
        ring = np.array(g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0], float)
        rows.append({"kind": "sealed_site", "version": "all", "id": f["properties"]["test_id"], "rank": 0,
                     "city": f["properties"]["city"], "lat": ring[:, 1].mean(), "lon": ring[:, 0].mean()})
    return pd.DataFrame(rows)


def extract(pts, tifs, xtifs):
    import rasterio
    from rasterio.warp import transform as warp_xy

    vals = np.full((len(pts), len(FETCHED)), np.nan)
    for tif in sorted(Path(tifs).glob("gujarat_*.tif")):
        xtif = Path(xtifs) / tif.name.replace("gujarat_", "gujaratx_", 1)
        if not xtif.exists():
            print(f"  {tif.name}: no extra file, skipped")
            continue
        with rasterio.open(tif) as a, rasterio.open(xtif) as b:
            if a.shape != b.shape:
                print(f"  {tif.name}: extra file is on another grid, skipped")
                continue
            xs, ys = warp_xy("EPSG:4326", a.crs, pts["lon"].tolist(), pts["lat"].tolist())
            names = [(a, list(a.descriptions).index(n) + 1) if n in a.descriptions
                     else (b, list(b.descriptions).index(n) + 1) for n in FETCHED]
            n_here = 0
            for i, (x, y) in enumerate(zip(xs, ys)):
                r, c = a.index(x, y)
                if not (1 <= r < a.height - 1 and 1 <= c < a.width - 1) or np.isfinite(vals[i]).all():
                    continue
                win = rasterio.windows.Window(c - 1, r - 1, 3, 3)
                vals[i] = [np.nanmedian(src.read(band, window=win).astype(float)) for src, band in names]
                n_here += 1
            print(f"  {tif.name}: {n_here} centres")
    out = pd.concat([pts.reset_index(drop=True), pd.DataFrame(vals, columns=FETCHED)], axis=1)
    for name, (p, q) in DERIVED.items():
        out[name] = out[p] - out[q]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tifs", default=str(REPO / "data" / "gujarat"))
    ap.add_argument("--extra-tifs", default=str(REPO / "data" / "gujarat_x"))
    ap.add_argument("--top", type=int, default=100)
    ap.add_argument("--no-extract", action="store_true", help="reuse data/analysis/alarm_features.csv")
    args = ap.parse_args()
    out = REPO / "data" / "analysis"
    table_path = out / "alarm_features.csv"
    if not args.no_extract:
        pts = extract(centres(args.top), args.tifs, args.extra_tifs)
        pts.round(5).to_csv(table_path, index=False)
        print(f"wrote {table_path}: {int(pts[FETCHED].notna().all(axis=1).sum())} of {len(pts)} centres read")
    if not table_path.exists():
        sys.exit(f"{table_path} is missing; run without --no-extract where the GeoTIFFs are")
    pts = pd.read_csv(table_path, keep_default_na=False, na_values=[""])

    sel = json.loads((REPO / "data" / "results_v3" / "selection.json").read_text(encoding="utf-8"))
    train, feats = load_tables(sel["feature_tables"], sel["extra_tables"])
    train = train.dropna(subset=feats).reset_index(drop=True)
    pts = pts.dropna(subset=feats).reset_index(drop=True)
    pts["verdict"], pts["seen"] = "", ""
    for v, folder in RESULTS.items():
        path = REPO / "data" / folder / "blind_check.csv"
        if path.exists():
            b = pd.read_csv(path, keep_default_na=False).set_index("blind_id")
            m = (pts["version"] == v) & pts["id"].isin(b.index)
            pts.loc[m, "verdict"] = b.loc[pts.loc[m, "id"], "verdict"].to_numpy()
            pts.loc[m, "seen"] = b.loc[pts.loc[m, "id"], "seen"].to_numpy()
    pts["what"] = np.where(pts["kind"] == "sealed_site", "sealed site",
                           np.where(pts["verdict"] == "", "alarm, unchecked", "alarm, " + pts["verdict"]))

    # Novelty and nearest training class, in the standardised 26-feature space.
    scaler = StandardScaler().fit(train[feats].to_numpy(float))
    Zt, Zp = scaler.transform(train[feats].to_numpy(float)), scaler.transform(pts[feats].to_numpy(float))
    nn = NearestNeighbors(n_neighbors=16).fit(Zt)
    own = np.sort(nn.kneighbors(Zt)[0][:, 1:].mean(axis=1))  # each training point's own neighbours, itself left out
    dist, idx = nn.kneighbors(Zp, n_neighbors=15)
    pts["novelty_pct"] = np.searchsorted(own, dist.mean(axis=1)) / len(own) * 100
    tcls = np.where(train["label"] == 1, "landfill", train["class"]).astype(object)
    pts["neighbours_landfill"] = (tcls[idx] == "landfill").mean(axis=1)
    pts["nearest_class"] = [pd.Series(tcls[row]).mode()[0] for row in idx]

    # SHAP by group, version 3 model, for every centre.
    import shap
    model = joblib.load(REPO / "data" / "results_v3" / "model.joblib")
    sv = np.asarray(shap.TreeExplainer(model).shap_values(pts[feats].to_numpy(float), check_additivity=False))
    for g, fs in GROUPS.items():
        pts["shap_" + g] = sv[:, [feats.index(f) for f in fs]].sum(axis=1)
    pts["v3_score"] = model.predict_proba(pts[feats].to_numpy(float))[:, 1]
    pts.round(4).to_csv(out / "diag_alarm_points.csv", index=False)

    md = ["# Diagnostics on the Gujarat alarms", "",
          f"{len(pts)} centres with all 26 features: the top {args.top} alarms of each version and the "
          "sealed sites. Values are the median of the 3 x 3 pixels at the centre of the patch.", ""]
    g = pts.groupby(["version", "what"], sort=False)
    nov = g.agg(centres=("id", "size"), median_novelty_pct=("novelty_pct", "median"),
                beyond_99th=("novelty_pct", lambda s: float((s > 99).mean())),
                neighbours_landfill=("neighbours_landfill", "mean"), v3_score=("v3_score", "median")).reset_index()
    nov.round(4).to_csv(out / "diag_alarm_novelty.csv", index=False)
    md += ["## Novelty: are the alarms unlike the training data?", "",
           "Percentile of each centre's distance to its 15 nearest training points, among the training "
           "points' own distances. `beyond_99th` is the share of centres farther out than 99% of "
           "training points; `neighbours_landfill` is the share of those neighbours that are landfill.", ""]
    md += table(nov) + [""]
    near = pts.groupby(["version", "what"])["nearest_class"].value_counts().unstack(fill_value=0).reset_index()
    md += ["## What the nearest training points are", ""] + table(near) + [""]
    sh = g[["shap_" + k for k in GROUPS]].mean().reset_index()
    sh.columns = [c.replace("shap_", "") for c in sh.columns]
    sh.round(4).to_csv(out / "diag_alarm_shap.csv", index=False)
    md += ["## What pushed the score up (version 3 model, mean SHAP in log-odds)", "",
           "Positive values push towards landfill. Computed for every centre with the version 3 model, "
           "including the alarms of versions 1 and 2, to show what it now makes of them.", ""] + table(sh) + [""]
    checked = pts[(pts["kind"] == "alarm") & (pts["seen"] != "")]
    if len(checked):
        by_seen = checked.groupby(["version", "seen"]).agg(
            centres=("id", "size"), median_novelty_pct=("novelty_pct", "median"),
            v3_score=("v3_score", "median"), v3_still_flags=("v3_score", lambda s: float((s >= 0.5).mean()))).reset_index()
        by_seen.round(4).to_csv(out / "diag_alarm_by_seen.csv", index=False)
        md += ["## Checked alarms by what was seen", ""] + table(by_seen) + [""]
    (out / "alarm_diagnostics.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out / 'alarm_diagnostics.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
