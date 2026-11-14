"""Post hoc: how would the other models and feature sets have done on Gujarat?

    python scripts/posthoc_gujarat.py

Run after the freeze and the scoring. It changes no reported result and selects nothing: the
frozen model stays the result. It exists to explain that result, and it gives the split
ablation its Gujarat rung for every model.

Fits each of the nine models, and the frozen model on feature sets A1 to A5, on all training
points with the frozen settings, then scores three sets of Gujarat pixels from the exported
GeoTIFFs in data/gujarat/:
  outlines   every pixel inside the 17 sealed outlines
  land       a random sample of about 2 million pixels of all scored land, each pixel counted once
  alarms     the 3 x 3 pixels at the centre of each of the frozen model's top alarms
Writes data/analysis/posthoc_gujarat_models.csv (one row per model) and
posthoc_gujarat_alarm_scores.csv (each alarm centre's score under every model).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from depth_analysis import SETS
from geoutil import REPO
from run_models import FEATURES, fit, make_models


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tifs", default=str(REPO / "data" / "gujarat"))
    ap.add_argument("--out", default=str(REPO / "data" / "analysis"))
    ap.add_argument("--land-sample", type=int, default=2_000_000)
    ap.add_argument("--seed", type=int, default=678)
    args = ap.parse_args()
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.warp import transform as warp_xy, transform_geom

    gres = REPO / "data" / "gujarat_results"
    meta = json.loads((REPO / "data" / "results" / "model.json").read_text(encoding="utf-8"))
    frozen, thr = meta["model"], meta["threshold"]
    sites = [f for f in json.load(open(REPO / "labels" / "gujarat_test_sites.geojson", encoding="utf-8"))["features"]
             if f["geometry"]["type"] != "Point"]
    box_of = dict(zip(*[pd.read_csv(gres / "site_recall.csv")[c] for c in ("test_id", "box")]))
    alarms = pd.read_csv(gres / "alarms.csv").dropna(subset=["blind_id"])
    tifs = sorted(Path(args.tifs).glob("gujarat_*.tif"))
    if not tifs:
        sys.exit(f"no gujarat_*.tif files in {args.tifs}")
    total = pd.read_csv(gres / "areas.csv")["pixels_scored"].sum()
    p_keep = min(1.0, args.land_sample / total)
    rng = np.random.default_rng(args.seed)

    # Collect the three pixel sets.
    X_parts, tag_parts, done = [], [], []
    for tif in tifs:
        city = tif.stem.replace("gujarat_", "").split("-")[0]
        with rasterio.open(tif) as src:
            names = list(src.descriptions)
            order = [names.index(b) + 1 for b in FEATURES]
            h, w, tr, crs = src.height, src.width, src.transform, src.crs
            xs, ys = tr.c + tr.a * (np.arange(w) + 0.5), tr.f + tr.e * (np.arange(h) + 0.5)
            fresh = np.ones((h, w), bool)
            for l, b, r, t in done:
                fresh[np.ix_((ys > b) & (ys < t), (xs > l) & (xs < r))] = False
            done.append((tr.c, tr.f + tr.e * h, tr.c + tr.a * w, tr.f))
            tag = np.full((h, w), "", dtype=object)
            tag[fresh & (rng.random((h, w)) < p_keep)] = "land"
            for f in sites:
                tid = f["properties"]["test_id"]
                if box_of.get(tid) != city:
                    continue
                m = geometry_mask([transform_geom("EPSG:4326", crs, f["geometry"])], (h, w), tr, invert=True)
                tag[m & (tag == "land")] = "land+site:" + tid
                tag[m & (tag == "")] = "site:" + tid
            a = alarms[alarms["city"] == city]
            if len(a):
                ax, ay = warp_xy("EPSG:4326", crs, a["lon"].tolist(), a["lat"].tolist())
                for bid, x, y in zip(a["blind_id"], ax, ay):
                    c0, r0 = int((x - tr.c) / tr.a), int((y - tr.f) / tr.e)
                    if not (0 <= r0 < h and 0 <= c0 < w):
                        continue
                    sub = tag[max(r0 - 1, 0):r0 + 2, max(c0 - 1, 0):c0 + 2]
                    sub[sub == "land"] = "land+alarm:" + bid
                    sub[sub == ""] = "alarm:" + bid
            for r0 in range(0, h, 512):
                rows = slice(r0, min(r0 + 512, h))
                want = tag[rows] != ""
                if not want.any():
                    continue
                x = src.read(order, window=rasterio.windows.Window(0, r0, w, rows.stop - r0)).astype(np.float64)
                flat = x[:, want].T
                ok = np.isfinite(flat).all(axis=1)
                X_parts.append(flat[ok])
                tag_parts.append(tag[rows][want][ok])
        print(f"  read {city}")
    X, tags = np.vstack(X_parts), np.concatenate(tag_parts).astype(str)
    is_land = np.char.startswith(tags, "land")
    site_id = np.array([t.split("site:")[1] if "site:" in t else "" for t in tags])
    alarm_id = np.array([t.split("alarm:")[1] if "alarm:" in t else "" for t in tags])
    in_site = site_id != ""
    print(f"{len(X):,} pixels: {is_land.sum():,} sampled land, {in_site.sum():,} in outlines, "
          f"{(alarm_id != '').sum():,} at alarm centres")

    train = pd.read_csv(REPO / "data" / "features" / "features.csv").dropna(subset=FEATURES)
    y = train["label"].to_numpy(int)
    blind = gres / "blind_check.csv"
    seen = dict(zip(*[pd.read_csv(blind)[c] for c in ("blind_id", "seen")])) if blind.exists() else {}
    runs = [(n, n, FEATURES) for n in make_models()] + [
        (f"{frozen} / {label}", frozen, feats) for label, feats in SETS.items() if feats != FEATURES]
    rows, per_alarm = [], pd.DataFrame({"blind_id": sorted(set(alarm_id) - {""})})
    per_alarm["seen"] = per_alarm["blind_id"].map(seen)
    for label, name, feats in runs:
        cols = [FEATURES.index(f) for f in feats]
        model = fit(name, make_models()[name], train[feats].to_numpy(float), y)
        score = model.predict_proba(X[:, cols])[:, 1]
        flag = score >= thr
        share = pd.Series(flag[in_site]).groupby(site_id[in_site]).mean()
        centre = pd.Series(score[alarm_id != ""]).groupby(alarm_id[alarm_id != ""]).median()
        per_alarm[label] = per_alarm["blind_id"].map(centre).round(3)
        row = {"model": label, "sites_found": int((share >= 0.5).sum()), "sites": len(share),
               "outline_pixels_flagged": float(flag[in_site].mean()),
               "land_flagged": float(flag[is_land & ~in_site].mean()),
               "top_alarm_centres_flagged": float((centre >= thr).mean())}
        for kind in sorted({v for v in seen.values() if isinstance(v, str)}):
            ids = [b for b, v in seen.items() if v == kind and b in centre.index]
            if len(ids) >= 3:
                row[f"checked_{kind}_flagged"] = float((centre[ids] >= thr).mean())
        rows.append(row)
        print(f"  {label:45} sites {row['sites_found']:2d}/{row['sites']}  land flagged {row['land_flagged']:.2%}  "
              f"alarm centres flagged {row['top_alarm_centres_flagged']:.0%}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).round(4).to_csv(out / "posthoc_gujarat_models.csv", index=False)
    per_alarm.to_csv(out / "posthoc_gujarat_alarm_scores.csv", index=False)
    print(f"wrote {out / 'posthoc_gujarat_models.csv'} and posthoc_gujarat_alarm_scores.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
