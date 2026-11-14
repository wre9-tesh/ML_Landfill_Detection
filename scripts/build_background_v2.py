"""Version 2 background: random points around the training landfills, like the land Gujarat is scored on.

    python scripts/build_background_v2.py

Version 1 drew its background anywhere in the training states, so it held almost no towns,
industrial roofs, coast or water, and the model was never told those are not landfills.
Gujarat is scored in boxes 15 km beyond the test sites, which are full of them. This script
draws background the same way for training: for every landfill place in data/samples/points.csv,
random points in the box 15 km beyond it. No Gujarat data is used.

Rules: a point stays at least 500 m from every mapped landfill, extra site and look-alike, so
its label "not a landfill" is very likely right; it must fall in or within 20 km of a state
that is not held out; it carries the state of the landfill it surrounds, so that in validation
a held-out region takes its surroundings with it; each place has its own seeded stream. Writes
data/samples/points_v2_background.csv with the same columns as points.csv
(kind "near_site", label 0), ready for gee_features.py.
"""
import argparse
import csv
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from build_samples import POINT_COLUMNS, KnownSites, load_kml_geojson
from geoutil import REPO, StateIndex, polygons
from osm_to_screening import osm_identity


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-place", type=int, default=300)
    ap.add_argument("--buffer-km", type=float, default=15)
    ap.add_argument("--exclude-m", type=float, default=500)
    ap.add_argument("--holdout", default="IN-GJ,IN-DH")
    ap.add_argument("--seed", default="es678-v2")
    args = ap.parse_args()
    banned = set(args.holdout.split(","))

    with open(REPO / "data" / "samples" / "points.csv", newline="", encoding="utf-8") as f:
        pts = [r for r in csv.DictReader(f) if r["kind"] == "site"]
    places, place_state = defaultdict(list), {}
    for r in pts:
        places[r["group_id"]].append((float(r["lon"]), float(r["lat"])))
        place_state[r["group_id"]] = r["state_iso"]

    shapes = []
    for feat in json.load(open(REPO / "data" / "raw" / "osm_landfill_india.geojson", encoding="utf-8"))["features"]:
        g = feat.get("geometry") or {}
        shapes.append((polygons(g), [tuple(g["coordinates"][:2])] if g.get("type") == "Point" else []))
    for name in ("extra_sites", "lookalikes"):
        shapes += [(polys, pins) for _, polys, pins in load_kml_geojson(REPO / "labels" / f"{name}.geojson")]
    known = KnownSites(shapes, args.exclude_m)
    states = StateIndex()

    out, skipped = [], Counter()
    for gid, xy in sorted(places.items()):
        lon0, lat0 = sum(p[0] for p in xy) / len(xy), sum(p[1] for p in xy) / len(xy)
        dy = args.buffer_km / 111.32
        dx = args.buffer_km / (111.32 * math.cos(math.radians(lat0)))
        box = (min(p[0] for p in xy) - dx, min(p[1] for p in xy) - dy,
               max(p[0] for p in xy) + dx, max(p[1] for p in xy) + dy)
        rng = random.Random(f"{args.seed}|{gid}")
        n = 0
        for _ in range(args.per_place * 50):
            if n >= args.per_place:
                break
            lon, lat = rng.uniform(box[0], box[2]), rng.uniform(box[1], box[3])
            if known.near(lon, lat):
                skipped["near a mapped site"] += 1
                continue
            iso, _, _ = states.lookup(lon, lat)
            if not iso or iso in banned:
                skipped["held-out state or open sea"] += 1
                continue
            pid = f"N_{gid}_{n:03d}"
            out.append({"point_id": pid, "lon": round(lon, 6), "lat": round(lat, 6), "label": 0, "kind": "near_site",
                        "class": "near_site", "source": "v2", "site_id": gid, "group_id": pid, "state_iso": place_state[gid]})
            n += 1
    path = REPO / "data" / "samples" / "points_v2_background.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=POINT_COLUMNS)
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} points around {len(places)} landfill places written to {path}")
    print("  per state: " + ", ".join(f"{k} {v}" for k, v in Counter(r["state_iso"] for r in out).most_common()))
    print("  draws rejected: " + ", ".join(f"{k} {v}" for k, v in skipped.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
