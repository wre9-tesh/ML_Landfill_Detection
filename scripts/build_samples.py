"""Turn screening decisions into sample points for feature extraction.

    python scripts/build_samples.py

Reads labels/india_screening.csv (your decisions), the OSM outlines in
data/raw/osm_landfill_india.geojson and, when they exist, labels/extra_sites.geojson
and labels/lookalikes.geojson (written by kml_to_csv.py). Writes
data/samples/points.csv and data/samples/samples_summary.txt.

One row per point, of three kinds:
  site       label 1: inside the outline of a kept landfill or an extra site
  lookalike  label 0: inside a site dropped as quarry, kiln, bare_soil, construction,
             riverbed, ash_pond or industrial, or a pinned look-alike
  random     label 0: background anywhere in the states that supply sites

Sampling design (each is a flag):
  - At most 50 points per place for sites and 30 for look-alikes, where a place is a
    group_id (outlines within 500 m), so one 300 ha landfill cannot outweigh thirty
    3 ha ones.
  - Points sit at least 15 m inside the outline, to avoid mixed edge pixels, and at least
    15 m apart, so no 10 m pixel is sampled twice.
  - A pin with no outline stands for a disc of 20 m radius.
  - Random points: as many as site points, split across states in proportion to their
    site points, never within 500 m of any mapped landfill, extra site or look-alike.
  - Extra outlines within 500 m of each other are one place; a place under 1 ha gives no
    points; where an extra outline and a kept OSM site are the same landfill, the extra
    outline is the one sampled.
  - Each place and each state has its own seeded random stream, so adding decisions
    later leaves the points already drawn unchanged.
Blank and unsure rows, and drops for other reasons (not_visible, inactive, mislocated,
too_small, other), give no points.
"""
import argparse
import csv
import io
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from geoutil import (REPO, ZONAL_COUNCILS, PolygonIndex, StateIndex, area_centroid, point_in_polygon, polygons,
                     shape_distance_m)
from kml_to_csv import lookalike_class
from osm_to_screening import osm_identity

LOOKALIKE = {"quarry", "kiln", "bare_soil", "construction", "riverbed", "ash_pond", "industrial"}
NO_POINTS = {"not_visible", "inactive", "mislocated", "too_small", "other"}
M_PER_DEG = 111_320
POINT_COLUMNS = ["point_id", "lon", "lat", "label", "kind", "class", "source", "site_id", "group_id", "state_iso"]


def read_table(path):
    """Read a CSV that may have been re-saved by Excel (BOM or cp1252, comma or semicolon)."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    header = text.split("\n", 1)[0]
    delim = max([",", ";", "\t"], key=header.count)
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


def norm(s):
    return re.sub(r"[\s\-/]+", "_", (s or "").strip().lower())


def drop_class(reason):
    """Look-alike class for a drop reason, 'none' for reasons that give no points, None if unknown."""
    r = norm(reason)
    if r in LOOKALIKE:
        return r
    if r in NO_POINTS:
        return "none"
    cls = lookalike_class(r) if r else None
    if cls in LOOKALIKE:
        return cls
    return "none" if cls == "other" else None


def local_xy(lon0, lat0):
    kx = M_PER_DEG * math.cos(math.radians(lat0))
    return (lambda lon, lat: ((lon - lon0) * kx, (lat - lat0) * M_PER_DEG),
            lambda x, y: (lon0 + x / kx, lat0 + y / M_PER_DEG))


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def sample_place(polys, pins, n, rng, edge_m, spacing_m, pin_radius_m):
    """Up to n points inside the outlines (edge_m from any edge) or the pin discs."""
    if not polys and not pins:
        return []
    lons = [p[0] for poly in polys for p in poly[0]] + [p[0] for p in pins]
    lats = [p[1] for poly in polys for p in poly[0]] + [p[1] for p in pins]
    to_xy, to_ll = local_xy(sum(lons) / len(lons), sum(lats) / len(lats))
    shapes = [[[to_xy(*p[:2]) for p in ring] for ring in poly] for poly in polys]
    segs = [(a[0], a[1], b[0], b[1]) for poly in shapes for ring in poly for a, b in zip(ring, ring[1:] + ring[:1])]
    discs = [to_xy(*p) for p in pins]
    xs = [p[0] for s in shapes for p in s[0]] + [d[0] + s for d in discs for s in (-pin_radius_m, pin_radius_m)]
    ys = [p[1] for s in shapes for p in s[0]] + [d[1] + s for d in discs for s in (-pin_radius_m, pin_radius_m)]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    taken = []
    for _ in range(n * 200):
        if len(taken) >= n:
            break
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        in_disc = any(math.hypot(x - dx, y - dy) <= pin_radius_m for dx, dy in discs)
        if not in_disc:
            if not any(point_in_polygon(x, y, s) for s in shapes):
                continue
            if min(seg_dist(x, y, *s) for s in segs) < edge_m:
                continue
        if all(math.hypot(x - tx, y - ty) >= spacing_m for tx, ty in taken):
            taken.append((x, y))
    return [to_ll(x, y) for x, y in taken]


class KnownSites:
    """Bounding boxes of every mapped site, padded by pad_m, bucketed by 1 degree cell."""

    def __init__(self, shapes, pad_m):
        self.cells = defaultdict(list)
        for polys, pins in shapes:
            pts = [p for poly in polys for p in poly[0]] + list(pins)
            if not pts:
                continue
            lat_mid = sum(p[1] for p in pts) / len(pts)
            dx = pad_m / (M_PER_DEG * math.cos(math.radians(lat_mid)))
            dy = pad_m / M_PER_DEG
            box = (min(p[0] for p in pts) - dx, min(p[1] for p in pts) - dy,
                   max(p[0] for p in pts) + dx, max(p[1] for p in pts) + dy)
            for cx in range(math.floor(box[0]), math.floor(box[2]) + 1):
                for cy in range(math.floor(box[1]), math.floor(box[3]) + 1):
                    self.cells[(cx, cy)].append(box)

    def near(self, lon, lat):
        return any(b[0] <= lon <= b[2] and b[1] <= lat <= b[3]
                   for b in self.cells.get((math.floor(lon), math.floor(lat)), ()))


def random_points(state, n, rng, known):
    idx = PolygonIndex(state["polys"])
    x0, y0, x1, y1 = idx.bbox
    cmax = math.cos(math.radians(min(abs(y0), abs(y1)) if y0 * y1 > 0 else 0))
    out = []
    for _ in range(max(n, 1) * 10_000):
        if len(out) >= n:
            break
        lon, lat = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if rng.random() > math.cos(math.radians(lat)) / cmax:
            continue  # keeps the draw uniform in area, not in degrees
        if idx.contains(lon, lat) and not known.near(lon, lat):
            out.append((lon, lat))
    return out


def split_by_share(total, weights):
    """Integers proportional to weights that add up to total (largest remainder)."""
    s = sum(weights.values())
    raw = {k: total * w / s for k, w in weights.items()}
    out = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[: total - sum(out.values())]:
        out[k] += 1
    return out


def load_kml_geojson(path):
    if not path.exists():
        return []
    feats = json.load(open(path, encoding="utf-8"))["features"]
    out = []
    for f in feats:
        g = f["geometry"]
        out.append((f["properties"], polygons(g), [tuple(g["coordinates"][:2])] if g["type"] == "Point" else []))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--screening", default=str(REPO / "labels" / "india_screening.csv"))
    ap.add_argument("--osm", default=str(REPO / "data" / "raw" / "osm_landfill_india.geojson"))
    ap.add_argument("--extra", default=str(REPO / "labels" / "extra_sites.geojson"))
    ap.add_argument("--lookalikes", default=str(REPO / "labels" / "lookalikes.geojson"))
    ap.add_argument("--out", default=str(REPO / "data" / "samples"))
    ap.add_argument("--n-site", type=int, default=50, help="max points per landfill place")
    ap.add_argument("--n-lookalike", type=int, default=30, help="max points per look-alike place")
    ap.add_argument("--edge-m", type=float, default=15, help="min distance inside an outline")
    ap.add_argument("--spacing-m", type=float, default=15, help="min distance between points of one place")
    ap.add_argument("--pin-radius-m", type=float, default=20, help="disc radius for pins without an outline")
    ap.add_argument("--random-ratio", type=float, default=1.0, help="random points per site point")
    ap.add_argument("--exclude-m", type=float, default=500, help="random points stay this far from known sites")
    ap.add_argument("--merge-m", type=float, default=500, help="extra outlines this close are one place")
    ap.add_argument("--min-ha", type=float, default=1.0, help="extra places smaller than this give no points")
    ap.add_argument("--min-fold-places", type=int, default=10, help="kept places a state needs for its own fold")
    ap.add_argument("--holdout", default="IN-GJ")
    ap.add_argument("--buffer-states", default="IN-DH")
    ap.add_argument("--seed", default="es678")
    args = ap.parse_args()
    banned = {args.holdout, *filter(None, args.buffer_states.split(","))}
    log = []

    # Every mapped outline, for the exclusion zone around random points.
    osm = {}
    for feat in json.load(open(args.osm, encoding="utf-8"))["features"]:
        tags, otype, oid = osm_identity(feat)
        g = feat.get("geometry") or {}
        pins = [tuple(g["coordinates"][:2])] if g.get("type") == "Point" else []
        osm.setdefault(f"osm_{otype[:1]}{oid}", (polygons(g), pins))

    # Screening decisions -> places, keyed by (kind, group_id, class).
    rows = read_table(args.screening)
    decisions, bad_decision, bad_reason, missing_geom = Counter(), [], [], []
    by_order = {r.get("screen_order", "").strip(): r for r in rows}
    places = {}
    for r in rows:
        d = norm(r.get("decision"))
        decisions[d or "(blank)"] += 1
        if d not in ("keep", "drop"):
            if d not in ("", "unsure"):
                bad_decision.append(r.get("screen_order"))
            continue
        if d == "keep":
            kind, cls = "site", ""
        else:
            cls = drop_class(r.get("reason"))
            if cls is None:
                bad_reason.append(f"{r.get('screen_order')}:{r.get('reason')!r}")
            if cls in (None, "none"):
                continue
            kind = "lookalike"
        if r["site_id"] not in osm:
            missing_geom.append(r["site_id"])
            continue
        key = (kind, r["group_id"], cls)
        p = places.setdefault(key, {"kind": kind, "class": cls, "source": "osm", "group_id": r["group_id"],
                                    "site_ids": [], "states": Counter(), "polys": [], "pins": []})
        polys, pins = osm[r["site_id"]]
        p["site_ids"].append(r["site_id"])
        p["states"][r["state_iso"]] += 1
        p["polys"] += polys
        p["pins"] += pins

    # Extra sites from Google Earth Pro. Outlines within merge_m of each other are one place.
    # A place under min_ha gives no points. A place within merge_m of a kept OSM site is the
    # same landfill drawn twice: the hand-drawn outline is used and the OSM one set aside.
    extras = load_kml_geojson(Path(args.extra))
    parent = list(range(len(extras)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def close(a, b):
        (ax, ay), (bx, by) = a[0], b[0]
        return abs(ax - bx) < 0.5 and abs(ay - by) < 0.5 and shape_distance_m(a[1], b[1]) <= args.merge_m

    def located(polys, pins):
        pts = [q for poly in polys for q in poly[0]] + list(pins)
        return (pts[0][0], pts[0][1]), (polys, pins)

    ex_shapes = [located(polys, pins) for _, polys, pins in extras]
    for i in range(len(extras)):
        for j in range(i):
            if close(ex_shapes[i], ex_shapes[j]):
                parent[find(i)] = find(j)
    members = defaultdict(list)
    for i in range(len(extras)):
        members[find(i)].append(i)
    set_aside = []  # shapes that give no points but still keep random points away
    for idx in members.values():
        props = [extras[i][0] for i in idx]
        polys = [poly for i in idx for poly in extras[i][1]]
        pins = [pin for i in idx for pin in extras[i][2]]
        ids = [pr["site_id"] for pr in props]
        names = " + ".join(pr.get("name", "") for pr in props)
        if len(idx) > 1:
            log.append(f"merged into one place: {names}")
        area = area_centroid(polys)[0] if polys else 0.0
        if polys and area < args.min_ha:
            log.append(f"too_small, no points: {names} ({area:.2f} ha)")
            set_aside.append((polys, pins))
            continue
        group = ids[0]
        m = re.match(r"\s*fix\s*#?\s*(\d+)", props[0].get("name", ""), re.I)
        if m and str(int(m.group(1))) in by_order:
            group = by_order[str(int(m.group(1)))]["group_id"]
        shape = located(polys, pins)
        for key in [k for k, pl in places.items() if k[0] == "site" and pl["source"] == "osm"]:
            if close(shape, located(places[key]["polys"], places[key]["pins"])):
                gone = places.pop(key)
                group = gone["group_id"]
                set_aside.append((gone["polys"], gone["pins"]))
                log.append(f"check: {names} is also kept OSM site {', '.join(gone['site_ids'])}; "
                           f"used the hand-drawn outline, not the OSM one")
        places[("site", ids[0], "")] = {
            "kind": "site", "class": "", "source": "extra", "group_id": group, "site_ids": ids,
            "states": Counter(pr.get("state_iso", "") for pr in props), "polys": polys, "pins": pins}
    for props, polys, pins in load_kml_geojson(Path(args.lookalikes)):
        places[("lookalike", props["lookalike_id"], props["class"])] = {
            "kind": "lookalike", "class": props["class"], "source": "lookalikes", "group_id": props["lookalike_id"],
            "site_ids": [props["lookalike_id"]], "states": Counter([props.get("state_iso", "")]),
            "polys": polys, "pins": pins}

    # Sample every place.
    points, empty = [], []
    for (kind, _, cls), p in sorted(places.items()):
        state = p["states"].most_common(1)[0][0]
        if state in banned or not state:
            log.append(f"skipped {p['site_ids'][0]}: state {state or 'unknown'} is held out or unknown")
            continue
        n = args.n_site if kind == "site" else args.n_lookalike
        tag = f"{p['source']}_{p['site_ids'][0]}" if p["source"] != "osm" else f"{p['group_id']}{'_' + cls if cls else ''}"
        rng = random.Random(f"{args.seed}|{kind}|{tag}")
        pts = sample_place(p["polys"], p["pins"], n, rng, args.edge_m, args.spacing_m, args.pin_radius_m)
        if not pts:
            empty.append(tag)
        prefix = "S" if kind == "site" else "L"
        for k, (lon, lat) in enumerate(pts):
            points.append({"point_id": f"{prefix}_{tag}_{k:02d}", "lon": round(lon, 6), "lat": round(lat, 6),
                           "label": 1 if kind == "site" else 0, "kind": kind, "class": cls, "source": p["source"],
                           "site_id": "|".join(p["site_ids"]), "group_id": p["group_id"], "state_iso": state})

    # Random background points, in proportion to site points per state.
    site_pts = Counter(pt["state_iso"] for pt in points if pt["kind"] == "site")
    shapes = list(osm.values()) + [(p["polys"], p["pins"]) for p in places.values()] + set_aside
    known = KnownSites(shapes, args.exclude_m)
    states = {s["iso"]: s for s in StateIndex().states}
    alloc = split_by_share(round(args.random_ratio * sum(site_pts.values())), site_pts) if site_pts else {}
    for iso, n in sorted(alloc.items()):
        rng = random.Random(f"{args.seed}|random|{iso}")
        for k, (lon, lat) in enumerate(random_points(states[iso], n, rng, known)):
            points.append({"point_id": f"R_{iso}_{k:05d}", "lon": round(lon, 6), "lat": round(lat, 6), "label": 0,
                           "kind": "random", "class": "random", "source": "random", "site_id": "",
                           "group_id": f"R_{iso}_{k:05d}", "state_iso": iso})

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "points.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=POINT_COLUMNS)
        w.writeheader()
        w.writerows(points)

    # Summary, including which states are big enough for their own validation fold.
    kept = defaultdict(set)
    for pt in points:
        if pt["kind"] == "site":
            kept[pt["state_iso"]].add(pt["group_id"])
    folds = sorted((s for s in kept if len(kept[s]) >= args.min_fold_places), key=lambda s: -len(kept[s]))
    kinds = Counter(pt["kind"] for pt in points)
    lines = [
        f"Screening rows: {len(rows)}; decisions: " + ", ".join(f"{k} {v}" for k, v in decisions.most_common()),
        f"Points: {len(points)} (site {kinds['site']}, lookalike {kinds['lookalike']}, random {kinds['random']})",
        f"Site places: {sum(1 for k in places if k[0] == 'site')} "
        f"(OSM {sum(1 for k, p in places.items() if k[0] == 'site' and p['source'] == 'osm')}, "
        f"extra {sum(1 for k, p in places.items() if k[0] == 'site' and p['source'] == 'extra')})",
        "Look-alike places by class: " + ", ".join(
            f"{c} {n}" for c, n in sorted(Counter(k[2] for k in places if k[0] == "lookalike").items())),
        "Look-alike points by class: " + ", ".join(
            f"{c} {n}" for c, n in sorted(Counter(pt["class"] for pt in points if pt["kind"] == "lookalike").items())),
        "",
        f"Kept places per state (own validation fold needs >= {args.min_fold_places}):",
        *[f"  {s:6} {len(kept[s]):4d}  {'fold' if s in folds else 'training only'}"
          for s in sorted(kept, key=lambda s: -len(kept[s]))],
        f"States with their own fold: {len(folds)}"
        + ("" if len(folds) >= 5 else " -> fewer than 5, so folds become Zonal Council regions: " + ", ".join(
            f"{z} {sum(len(kept[s]) for s in kept if ZONAL_COUNCILS.get(s) == z)}"
            for z in sorted({ZONAL_COUNCILS.get(s, '?') for s in kept}))),
    ]
    if bad_decision:
        lines.append(f"check: unrecognised decision in screen_order {', '.join(bad_decision)}")
    if bad_reason:
        lines.append(f"check: unrecognised drop reason, no points taken: {', '.join(bad_reason)}")
    if missing_geom:
        lines.append(f"check: no outline found for {', '.join(missing_geom)}")
    if empty:
        lines.append(f"note: {len(empty)} places too small for any point {args.edge_m:g} m inside the edge: "
                     + ", ".join(empty[:15]) + (" ..." if len(empty) > 15 else ""))
    lines += log
    (out / "samples_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
