"""Score the exported Gujarat boxes with the frozen model. Run once, after the freeze tag.

    pip install rasterio scipy
    python scripts/score_gujarat.py

Reads the GeoTIFFs from gee_export_gujarat.py in data/gujarat/, the frozen model in
data/results/model.joblib and the sealed list in labels/gujarat_test_sites.geojson.
Writes, in data/gujarat_results/:
  scores/<city>.tif   the model score per 10 m pixel, 0 to 100, 255 where a feature is missing
  site_recall.csv     per sealed site: pixels, share flagged, highest score, found or missed
  areas.csv           per city: pixels scored and the share flagged
  alarms.csv          flagged patches of at least 1 ha outside the sealed outlines, highest mean
                      score first, with centre coordinates and size
  alarms_blind.kml    the top alarms as pins named only by a shuffled number, for checking in
                      Google Earth without seeing the score
  summary.json        recall, flagged share, counts and the settings used

Rules applied, all fixed in the freeze: a pixel is flagged at or above the frozen threshold;
a site is found when at least --min-found-pixels of its outline's pixels are flagged and they
make up at least --min-found-share of the scored pixels in the outline; a
pixel in two overlapping boxes is counted once, in the first city alphabetically; an alarm
is a patch of touching flagged pixels (edges, not corners) of at least --min-alarm-ha.

The script refuses to run unless the current commit carries a tag starting with "freeze",
so that Gujarat cannot be scored by accident before the freeze.
"""
import argparse
import csv
import json
import random
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np

from geoutil import REPO


def freeze_tags():
    out = subprocess.run(["git", "tag", "--points-at", "HEAD"], capture_output=True, text=True, cwd=REPO)
    return [t for t in out.stdout.split() if t.lower().startswith("freeze")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tifs", default=str(REPO / "data" / "gujarat"))
    ap.add_argument("--model", default=str(REPO / "data" / "results" / "model.joblib"))
    ap.add_argument("--sites", default=str(REPO / "labels" / "gujarat_test_sites.geojson"))
    ap.add_argument("--out", default=str(REPO / "data" / "gujarat_results"))
    ap.add_argument("--min-found-pixels", type=int, default=1)
    ap.add_argument("--min-found-share", type=float, default=0.0)
    ap.add_argument("--min-alarm-ha", type=float, default=1.0)
    ap.add_argument("--top-alarms", type=int, default=100)
    ap.add_argument("--allow-unfrozen", action="store_true", help="for testing on made-up data only")
    args = ap.parse_args()

    tags = freeze_tags()
    if not tags and not args.allow_unfrozen:
        sys.exit("This commit has no freeze tag. Tag and push the freeze first (docs/freeze_draft.md).")
    try:
        import rasterio
        from rasterio.features import geometry_mask
        from rasterio.warp import transform as warp_xy, transform_geom
        from scipy import ndimage
    except ImportError:
        sys.exit("rasterio and scipy are needed. Run: python -m pip install rasterio scipy")

    meta = json.loads(Path(args.model).with_suffix(".json").read_text(encoding="utf-8"))
    model, bands, thr = joblib.load(args.model), meta["features"], meta["threshold"]
    sites = json.load(open(args.sites, encoding="utf-8"))["features"]
    tifs = sorted(Path(args.tifs).glob("gujarat_*.tif"))
    if not tifs:
        sys.exit(f"no gujarat_*.tif files in {args.tifs}")
    out = Path(args.out)
    (out / "scores").mkdir(parents=True, exist_ok=True)

    done_bounds, areas, alarms, site_rows = [], [], [], {}
    for tif in tifs:
        city = tif.stem.replace("gujarat_", "").split("-")[0]
        with rasterio.open(tif) as src:
            names = list(src.descriptions)
            if set(bands) - set(names):
                sys.exit(f"{tif.name}: bands {names} do not include {sorted(set(bands) - set(names))}")
            order = [names.index(b) + 1 for b in bands]
            h, w, tr, crs = src.height, src.width, src.transform, src.crs
            score = np.full((h, w), np.nan, np.float32)
            for r0 in range(0, h, 512):  # strips keep memory low
                win = rasterio.windows.Window(0, r0, w, min(512, h - r0))
                x = src.read(order, window=win).astype(np.float64)
                flat = x.reshape(len(bands), -1).T
                ok = np.isfinite(flat).all(axis=1)
                if src.nodata is not None:
                    ok &= (flat != src.nodata).all(axis=1)
                s = np.full(len(flat), np.nan, np.float32)
                if ok.any():
                    s[ok] = model.predict_proba(flat[ok])[:, 1]
                score[r0:r0 + win.height] = s.reshape(int(win.height), w)
            profile = dict(src.profile, count=1, dtype="uint8", nodata=255, compress="deflate")
        with rasterio.open(out / "scores" / f"{tif.stem}.tif", "w", **profile) as dst:
            dst.write(np.where(np.isfinite(score), np.round(score * 100), 255).astype(np.uint8), 1)

        # Pixels already covered by an earlier box are not counted again.
        xs = tr.c + tr.a * (np.arange(w) + 0.5)
        ys = tr.f + tr.e * (np.arange(h) + 0.5)
        fresh = np.ones((h, w), bool)
        for l, b, r, t in done_bounds:
            fresh[np.ix_((ys > b) & (ys < t), (xs > l) & (xs < r))] = False
        done_bounds.append((tr.c, tr.f + tr.e * h, tr.c + tr.a * w, tr.f))
        valid = np.isfinite(score)
        flagged = valid & (score >= thr)

        in_site = np.zeros((h, w), bool)
        for f in sites:
            pr = f["properties"]
            if f["geometry"]["type"] == "Point":
                site_rows.setdefault(pr["test_id"], {**pr, "pixels": 0, "status": "no_outline"})
                continue
            m = geometry_mask([transform_geom("EPSG:4326", crs, f["geometry"])], (h, w), tr, invert=True)
            if not m.any():
                continue
            in_site |= m
            n, nv, nf = int(m.sum()), int((m & valid).sum()), int((m & flagged).sum())
            row = site_rows.get(pr["test_id"])
            if row and row.get("pixels", 0) >= n:
                continue  # the same site seen whole in an earlier box
            site_rows[pr["test_id"]] = {
                **pr, "box": city, "pixels": n, "pixels_scored": nv, "pixels_flagged": nf,
                "share_flagged": round(nf / nv, 4) if nv else "",
                "max_score": round(float(np.nanmax(score[m])), 4) if nv else "",
                "status": "not_scored" if not nv else "found" if (
                    nf >= args.min_found_pixels and nf / nv >= args.min_found_share) else "missed"}

        count = fresh & valid
        areas.append({"city": city, "pixels": int(fresh.sum()), "pixels_scored": int(count.sum()),
                      "pixels_flagged": int((fresh & flagged).sum()),
                      "share_flagged": round(float((fresh & flagged).sum() / max(count.sum(), 1)), 5),
                      "pixels_in_test_sites": int((fresh & in_site).sum())})

        px_ha = abs(tr.a * tr.e) / 1e4
        lab, n_lab = ndimage.label(flagged & fresh & ~in_site)
        if n_lab:
            idx = np.arange(1, n_lab + 1)
            size = ndimage.sum_labels(np.ones_like(lab), lab, idx)
            keep = idx[size * px_ha >= args.min_alarm_ha]
            if len(keep):
                mean = ndimage.mean(score, lab, keep)
                cen = ndimage.center_of_mass(np.ones_like(lab), lab, keep)
                cx = [tr.c + tr.a * (c[1] + 0.5) for c in cen]
                cy = [tr.f + tr.e * (c[0] + 0.5) for c in cen]
                lon, lat = warp_xy(crs, "EPSG:4326", cx, cy)
                for k, lb in enumerate(keep):
                    alarms.append({"city": city, "lat": round(lat[k], 6), "lon": round(lon[k], 6),
                                   "area_ha": round(float(size[lb - 1] * px_ha), 2),
                                   "mean_score": round(float(mean[k]), 4)})
        print(f"  {city:12} {areas[-1]['share_flagged']:.2%} of scored pixels flagged")

    alarms.sort(key=lambda a: (-a["mean_score"], -a["area_ha"]))
    for k, a in enumerate(alarms, 1):
        a["rank"] = k
    top = alarms[: args.top_alarms]
    blind = list(range(1, len(top) + 1))
    random.Random("es678-blind").shuffle(blind)
    for a, b in zip(top, blind):
        a["blind_id"] = f"A{b:03d}"

    def write(name, rows, cols):
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    for f in sites:  # sealed sites that no box covered
        site_rows.setdefault(f["properties"]["test_id"], {**f["properties"], "pixels": 0, "status": "not_scored"})
    srows = list(site_rows.values())
    write("site_recall.csv", srows, ["test_id", "city", "site_name", "area_ha", "in_recall", "box", "pixels",
                                    "pixels_scored", "pixels_flagged", "share_flagged", "max_score", "status"])
    write("areas.csv", areas, ["city", "pixels", "pixels_scored", "pixels_flagged", "share_flagged",
                               "pixels_in_test_sites"])
    write("alarms.csv", alarms, ["rank", "blind_id", "city", "lat", "lon", "area_ha", "mean_score"])
    kml = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
           "<name>alarms_blind</name>"]
    for a in sorted(top, key=lambda a: a["blind_id"]):
        kml.append(f"<Placemark><name>{a['blind_id']}</name><Point><coordinates>{a['lon']},{a['lat']},0"
                   f"</coordinates></Point></Placemark>")
    (out / "alarms_blind.kml").write_text("\n".join(kml + ["</Document></kml>"]) + "\n", encoding="utf-8")

    counted = [r for r in srows if r.get("in_recall", "yes") == "yes" and r["status"] in ("found", "missed")]
    found = sum(r["status"] == "found" for r in counted)
    scored, flag = sum(a["pixels_scored"] for a in areas), sum(a["pixels_flagged"] for a in areas)
    summary = {"freeze_tags": tags, "model": meta["model"], "threshold": thr,
               "min_found_pixels": args.min_found_pixels, "min_found_share": args.min_found_share,
               "min_alarm_ha": args.min_alarm_ha,
               "sites_counted": len(counted), "sites_found": found,
               "site_recall": round(found / len(counted), 4) if counted else None,
               "sites_not_counted": {r["test_id"]: r["status"] if r["status"] in ("no_outline", "not_scored")
                                     else r.get("in_recall") for r in srows if r not in counted},
               "pixels_scored": scored, "pixels_flagged": flag,
               "share_flagged": round(flag / max(scored, 1), 5),
               "area_scored_km2": round(scored * px_ha / 100, 1), "alarms": len(alarms)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
