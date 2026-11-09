"""Sample the Earth Engine feature stack at the points from build_samples.py.

    pip install earthengine-api
    earthengine authenticate                      (once; opens a browser)
    python scripts/gee_features.py --project YOUR-CLOUD-PROJECT --limit 50   (quick test)
    python scripts/gee_features.py --project YOUR-CLOUD-PROJECT

Reads data/samples/points.csv and writes data/features/features.csv (the points plus
the twelve feature columns) and data/features/features_meta.json (every setting used).
Fetched points are kept in data/features/cache.csv, so a run that stops can simply be
started again, and later runs fetch only points that are new.

Features, all from the 2024 pre-monsoon window (1 March to 31 May 2024):
  B2 B3 B4 B8 B11  Sentinel-2 surface reflectance: median of scenes under 10% cloud, with
                cloud, shadow, cirrus, snow and defective pixels masked (scene classification)
  NDVI NDBI BSI from the median bands: (B8 - B4) / (B8 + B4), (B11 - B8) / (B11 + B8) and
                ((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2)), the bare soil index
  LST           Landsat 8/9 surface temperature in deg C: median of scenes under 30% cloud,
                with cloud and shadow pixels masked, bilinear to 10 m
  LST_anom      LST minus the mean LST of land within 2 km, computed at 100 m (about the
                native thermal resolution); permanent water is left out of that mean so
                coastal sites are not made to look hotter than they are
  elev slope    SRTM elevation (m) and slope (degrees), computed at its native 30 m
feature_image() is reused in Phase 3 to score Gujarat with exactly the same stack.
"""
import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from geoutil import REPO

BANDS = ["B2", "B3", "B4", "B8", "B11", "NDVI", "NDBI", "BSI", "LST", "LST_anom", "elev", "slope"]
PARAMS = {
    "start": "2024-03-01",
    "end": "2024-06-01",  # exclusive
    "s2_collection": "COPERNICUS/S2_SR_HARMONIZED",
    "s2_max_scene_cloud_pct": 10,
    "s2_masked_scl_classes": [1, 3, 8, 9, 10, 11],  # defective, shadow, cloud medium/high, cirrus, snow
    "landsat_collections": ["LANDSAT/LC08/C02/T1_L2", "LANDSAT/LC09/C02/T1_L2"],
    "landsat_max_scene_cloud_pct": 30,
    "lst_background_radius_m": 2000,
    "lst_background_scale_m": 100,
    "water": "JRC/GSW1_4/GlobalSurfaceWater",
    "water_min_occurrence_pct": 50,
    "dem": "USGS/SRTMGL1_003",
    "scale_m": 10,
}
TRANSIENT = ("Too many concurrent", "rate limit", "Rate Limit", "Quota exceeded", "429", "503", "temporarily")


def feature_image(ee, region, p=PARAMS):
    """The twelve-band feature stack over region (any geometry the scenes must touch)."""

    def s2_prep(img):
        masked = p["s2_masked_scl_classes"]
        clear = img.select("SCL").remap(masked, [0] * len(masked), 1)
        return img.select(["B2", "B3", "B4", "B8", "B11"]).divide(10000).updateMask(clear)

    def landsat_prep(img):
        clear = img.select("QA_PIXEL").bitwiseAnd(0b11110).eq(0)  # bits 1-4: dilated cloud, cirrus, cloud, shadow
        lst = img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15)
        return lst.rename("LST").updateMask(clear).resample("bilinear")

    s2 = (ee.ImageCollection(p["s2_collection"]).filterDate(p["start"], p["end"]).filterBounds(region)
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", p["s2_max_scene_cloud_pct"])).map(s2_prep).median())
    s2 = s2.addBands(s2.normalizedDifference(["B8", "B4"]).rename("NDVI"))
    s2 = s2.addBands(s2.normalizedDifference(["B11", "B8"]).rename("NDBI"))
    s2 = s2.addBands(s2.select("B11").add(s2.select("B4")).rename("soil")
                     .addBands(s2.select("B8").add(s2.select("B2")).rename("veg"))
                     .normalizedDifference(["soil", "veg"]).rename("BSI"))

    l8, l9 = (ee.ImageCollection(c) for c in p["landsat_collections"])
    lst = (l8.merge(l9).filterDate(p["start"], p["end"]).filterBounds(region)
           .filter(ee.Filter.lt("CLOUD_COVER", p["landsat_max_scene_cloud_pct"])).map(landsat_prep).median())
    land = ee.Image(p["water"]).select("occurrence").unmask(0).lt(p["water_min_occurrence_pct"])
    background = (lst.updateMask(land)
                  .focalMean(radius=p["lst_background_radius_m"], kernelType="circle", units="meters")
                  .reproject(ee.Projection("EPSG:4326").atScale(p["lst_background_scale_m"])))
    anomaly = lst.subtract(background).rename("LST_anom")

    dem = ee.Image(p["dem"]).select("elevation")
    slope = ee.Terrain.slope(dem).reproject(dem.projection())
    return ee.Image.cat([s2, lst, anomaly, dem.rename("elev"), slope.rename("slope")]).select(BANDS).toFloat()


def fetch(ee, rows, p):
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([float(r["lon"]), float(r["lat"])]),
                                          {"point_id": r["point_id"]}) for r in rows])
    img = feature_image(ee, fc.geometry(), p)
    out = img.reduceRegions(collection=fc, reducer=ee.Reducer.first(), scale=p["scale_m"], tileScale=4)
    return {f["properties"]["point_id"]: f["properties"] for f in out.getInfo()["features"]}


def fetch_robust(ee, rows, p, log, min_rows=20):
    """fetch(), waiting out rate limits and halving the batch when Earth Engine gives up on it."""
    for attempt in range(4):
        try:
            return fetch(ee, rows, p)
        except (ee.EEException, OSError) as e:
            msg = str(e)
            if isinstance(e, OSError) or any(s in msg for s in TRANSIENT):
                log(f"    waiting after: {msg[:100]}")
                time.sleep(20 * (attempt + 1))
                continue
            if len(rows) > min_rows:
                mid = len(rows) // 2
                log(f"    splitting {len(rows)} points after: {msg[:100]}")
                return {**fetch_robust(ee, rows[:mid], p, log, min_rows),
                        **fetch_robust(ee, rows[mid:], p, log, min_rows)}
            log(f"    skipped {len(rows)} points (they will be retried next run): {msg[:150]}")
            return {}
    log(f"    skipped {len(rows)} points after repeated waits (they will be retried next run)")
    return {}


def key(r):
    return r["point_id"], f"{float(r['lon']):.6f}", f"{float(r['lat']):.6f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, help="Google Cloud project registered for Earth Engine")
    ap.add_argument("--points", default=str(REPO / "data" / "samples" / "points.csv"))
    ap.add_argument("--out", default=str(REPO / "data" / "features"))
    ap.add_argument("--batch", type=int, default=300, help="points per request; halved automatically on failure")
    ap.add_argument("--limit", type=int, help="fetch only this many new points (for a first test)")
    ap.add_argument("--lst-radius-m", type=float, default=PARAMS["lst_background_radius_m"],
                    help="LST background radius; the fallback in the plan is 1000")
    args = ap.parse_args()

    try:
        import ee
    except ImportError:
        sys.exit("earthengine-api is not installed. Run: pip install earthengine-api")
    try:
        ee.Initialize(project=args.project)
    except Exception as e:  # noqa: BLE001 - any start-up failure gets the same advice
        sys.exit(f"Earth Engine did not start: {e}\nRun `earthengine authenticate` once, and check that "
                 f"'{args.project}' is the Cloud project registered for Earth Engine.")

    p = dict(PARAMS, lst_background_radius_m=args.lst_radius_m)
    # The band list is part of the hash, so adding a feature refetches every point.
    phash = hashlib.sha1(json.dumps(dict(p, bands=BANDS), sort_keys=True).encode()).hexdigest()[:10]
    with open(args.points, newline="", encoding="utf-8") as f:
        points = list(csv.DictReader(f))
    point_cols = list(points[0].keys()) if points else []
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cache_path = out / "cache.csv"
    cache_cols = ["point_id", "lon", "lat", "params"] + BANDS
    cache = {}
    if cache_path.exists():
        with open(cache_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["params"] == phash:
                    cache[key(r)] = r

    # Nearby points share scenes, so batches are made of neighbours.
    todo = sorted((r for r in points if key(r) not in cache),
                  key=lambda r: (r["state_iso"], round(float(r["lat"]) * 2), float(r["lon"])))
    n_cached = len(points) - len(todo)
    if args.limit:
        todo = todo[: args.limit]
    nb = -(-len(todo) // args.batch)
    print(f"{len(points)} points: {n_cached} already fetched, {len(todo)} to fetch now "
          f"in {nb} batches of up to {args.batch}")
    new_file = not cache_path.exists()
    t_start = time.time()
    with open(cache_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cache_cols)
        if new_file:
            w.writeheader()
        for i in range(nb):
            batch = todo[i * args.batch:(i + 1) * args.batch]
            t = time.time()
            got = fetch_robust(ee, batch, p, print)
            for r in batch:
                if r["point_id"] in got:
                    row = {"point_id": r["point_id"], "lon": r["lon"], "lat": r["lat"], "params": phash,
                           **{b: got[r["point_id"]].get(b) for b in BANDS}}
                    w.writerow(row)
                    cache[key(r)] = row
            f.flush()
            print(f"  batch {i + 1}/{nb}: {len(got)}/{len(batch)} points in {time.time() - t:.0f} s")

    rows, missing = [], {b: 0 for b in BANDS}
    for r in points:
        c = cache.get(key(r))
        vals = {b: (c[b] if c and c[b] not in (None, "") else "") for b in BANDS}
        for b in BANDS:
            missing[b] += bool(c) and vals[b] == ""
        rows.append({**r, "fetched": int(c is not None), **vals})
    with open(out / "features.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=point_cols + ["fetched"] + BANDS)
        w.writeheader()
        w.writerows(rows)

    fetched = sum(r["fetched"] for r in rows)
    meta = {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "earthengine_api": getattr(ee, "__version__", "unknown"),
        "params": p,
        "params_hash": phash,
        "points_file": str(Path(args.points).name),
        "points_sha256": hashlib.sha256(Path(args.points).read_bytes()).hexdigest(),
        "n_points": len(rows),
        "n_fetched": fetched,
        "n_missing_by_band": missing,
    }
    (out / "features_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"done in {time.time() - t_start:.0f} s: {fetched}/{len(rows)} points fetched")
    if any(missing.values()):
        print("fetched points with no value (masked pixel, e.g. no cloud-free scene): "
              + ", ".join(f"{b} {n}" for b, n in missing.items() if n))
    print(f"wrote {out / 'features.csv'}")


if __name__ == "__main__":
    sys.exit(main())
