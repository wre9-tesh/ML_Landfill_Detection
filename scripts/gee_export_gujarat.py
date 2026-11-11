"""Export the twelve-band feature stack around the sealed Gujarat test sites.

    python scripts/gee_export_gujarat.py --dry-run                       (list the boxes, no Earth Engine)
    python scripts/gee_export_gujarat.py --project YOUR-CLOUD-PROJECT    (start the exports)
    python scripts/gee_export_gujarat.py --project YOUR-CLOUD-PROJECT --status

One GeoTIFF per test city goes to a Google Drive folder (default landfill_gujarat). Each
covers the box around that city's test sites, widened by 15 km on every side, at 10 m in
UTM zone 43N, with the same feature_image() the training points were sampled from. Download
the files into data/gujarat/ when the tasks finish; scoring happens locally, after the freeze.

This exports features only. It reads the site list for the box positions and nothing else,
so running it before the freeze does not reveal any result. Boxes of nearby cities can
overlap; the scoring script counts each pixel once.
"""
import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone

from gee_features import BANDS, PARAMS, feature_image
from geoutil import REPO

CRS = "EPSG:32643"


def city_boxes(path, buffer_km):
    """{city: (west, south, east, north)} in degrees, the sites' bounding box plus the buffer."""
    sites = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            sites.setdefault(r["city"], []).append((float(r["lon"]), float(r["lat"])))
    boxes = {}
    for city, pts in sorted(sites.items()):
        lat_mid = sum(p[1] for p in pts) / len(pts)
        dy = buffer_km / 111.32
        dx = buffer_km / (111.32 * math.cos(math.radians(lat_mid)))
        boxes[city] = (min(p[0] for p in pts) - dx, min(p[1] for p in pts) - dy,
                       max(p[0] for p in pts) + dx, max(p[1] for p in pts) + dy)
    return boxes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", help="Google Cloud project registered for Earth Engine")
    ap.add_argument("--sites", default=str(REPO / "labels" / "gujarat_test_sites.csv"))
    ap.add_argument("--buffer-km", type=float, default=15)
    ap.add_argument("--drive-folder", default="landfill_gujarat")
    ap.add_argument("--only", help="comma-separated cities, to redo some of them")
    ap.add_argument("--dry-run", action="store_true", help="print the boxes and stop")
    ap.add_argument("--status", action="store_true", help="show the state of the export tasks and stop")
    args = ap.parse_args()

    boxes = city_boxes(args.sites, args.buffer_km)
    if args.only:
        want = {c.strip().lower() for c in args.only.split(",")}
        boxes = {c: b for c, b in boxes.items() if c.lower() in want}
    total = 0
    for city, (w, s, e, n) in boxes.items():
        km_x = (e - w) * 111.32 * math.cos(math.radians((s + n) / 2))
        km_y = (n - s) * 111.32
        mpx = km_x * km_y * 1e6 / PARAMS["scale_m"] ** 2 / 1e6
        total += mpx
        print(f"  {city:12} {w:.4f},{s:.4f} to {e:.4f},{n:.4f}  {km_x:.0f} x {km_y:.0f} km  {mpx:.1f} M pixels")
    print(f"{len(boxes)} boxes, {total:.0f} M pixels, about {total * 48 / 1000:.1f} GB before compression")
    if args.dry_run:
        return 0
    if not args.project:
        sys.exit("--project is required unless --dry-run is given")

    try:
        import ee
    except ImportError:
        sys.exit("earthengine-api is not installed. Run: python -m pip install earthengine-api")
    try:
        ee.Initialize(project=args.project)
    except Exception as e:  # noqa: BLE001 - any start-up failure gets the same advice
        sys.exit(f"Earth Engine did not start: {e}")

    if args.status:
        for t in ee.batch.Task.list():
            d = t.status()
            if d.get("description", "").startswith("gujarat_"):
                print(f"  {d['description']:24} {d['state']:10} {d.get('error_message', '')}")
        return 0

    tasks = {}
    for city, (w, s, e, n) in boxes.items():
        region = ee.Geometry.Rectangle([w, s, e, n], proj="EPSG:4326", geodesic=False)
        name = "gujarat_" + city.lower().replace(" ", "_")
        task = ee.batch.Export.image.toDrive(
            image=feature_image(ee, region), description=name, folder=args.drive_folder, fileNamePrefix=name,
            region=region, scale=PARAMS["scale_m"], crs=CRS, maxPixels=int(1e9), fileFormat="GeoTIFF")
        task.start()
        tasks[city] = task.id
        print(f"  started {name} ({task.id})")
    out = REPO / "data" / "gujarat"
    out.mkdir(parents=True, exist_ok=True)
    meta = {"created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "buffer_km": args.buffer_km,
            "crs": CRS, "bands": BANDS, "params": PARAMS, "drive_folder": args.drive_folder,
            "boxes_wsen": boxes, "tasks": tasks}
    (out / "export_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out / 'export_meta.json'}; check progress with --status")
    return 0


if __name__ == "__main__":
    sys.exit(main())
