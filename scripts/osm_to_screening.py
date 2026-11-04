"""Turn an overpass-turbo GeoJSON export of landuse=landfill into screening files.

    python scripts/osm_to_screening.py data/raw/osm_landfill_india.geojson

Writes into --out (default labels/):
  india_screening.csv / .kml          training candidates outside the held-out region, in screening order
  gujarat_osm_candidates.csv / .kml   held-out (Gujarat) sites, used only to build the sealed test list
  osm_excluded.csv                    sites dropped before screening, with the reason
  osm_summary.txt                     counts for the paper's data-flow figure

Screening order: sites of at least --min-ha (default 1 ha, about one native
Landsat thermal pixel) come first, taken round-robin across states so that a
partly finished screen still covers several states; smaller sites and
point-only sites follow in the same pattern.
"""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from geoutil import REPO, StateIndex, area_centroid, haversine_m, polygons

LIFECYCLE_PREFIXES = ("disused:", "abandoned:", "was:", "removed:", "demolished:", "razed:", "destroyed:")
CLOSED_STATUS = {"closed", "abandoned", "disused", "inactive", "decommissioned"}
SCREEN_COLUMNS = ["decision", "reason", "imagery_date", "notes"]


def osm_identity(feat):
    props = feat.get("properties") or {}
    if isinstance(props.get("tags"), dict):
        tags, otype, oid = props["tags"], props.get("type"), props.get("id")
    else:
        tags = {k: v for k, v in props.items() if not k.startswith("@") and not isinstance(v, (dict, list))}
        ref = str(props.get("@id") or feat.get("id") or "")
        otype, _, oid = ref.partition("/")
    return tags, str(otype), str(oid)


def exclusion_reason(tags):
    if tags.get("landuse") != "landfill":
        return "landuse_not_landfill"
    for k in ("disused", "abandoned"):
        if tags.get(k, "no").lower() not in ("no", ""):
            return k
    if tags.get("operational_status", "").lower() in CLOSED_STATUS:
        return "operational_status_" + tags["operational_status"].lower()
    if "end_date" in tags:
        return "end_date"
    for k in tags:
        if k.startswith(LIFECYCLE_PREFIXES):
            return "lifecycle_tag_" + k
    if "quarry" in (tags.get("name", "") + " " + tags.get("description", "")).lower():
        return "quarry_in_name"
    return None


def assign_groups(rows, link_m):
    """Single-linkage groups: sites within link_m of each other share a group_id."""
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if abs(a["lat"] - b["lat"]) < link_m / 111_000 and haversine_m(a["lon"], a["lat"], b["lon"], b["lat"]) <= link_m:
                parent[find(i)] = find(j)
    roots = {}
    for i, r in enumerate(rows):
        r["group_id"] = roots.setdefault(find(i), f"g{len(roots) + 1:04d}")


def screening_order(rows):
    """Large sites first, round-robin across states, largest first within each state."""
    ordered = []
    for tier in (1, 2):
        by_state = defaultdict(list)
        for r in rows:
            if r["tier"] == tier:
                by_state[r["state_iso"]].append(r)
        queues = sorted(by_state.values(), key=len, reverse=True)
        for q in queues:
            q.sort(key=lambda r: -r["area_ha"])
        while any(queues):
            for q in queues:
                if q:
                    ordered.append(q.pop(0))
    for i, r in enumerate(ordered, 1):
        r["screen_order"] = i
    return ordered


def osm_url(r):
    return f"https://www.openstreetmap.org/{r['osm_type']}/{r['osm_id']}"


def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def ring_coords(ring):
    return " ".join(f"{p[0]:.6f},{p[1]:.6f},0" for p in ring)


def write_kml(path, title, rows, label):
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
        f"<name>{escape(title)}</name>",
        '<Style id="site"><LineStyle><color>ff00ffff</color><width>2</width></LineStyle>'
        "<PolyStyle><fill>0</fill></PolyStyle>"
        "<IconStyle><scale>0.8</scale></IconStyle></Style>",
        f"<Folder><name>{escape(title)}</name>",
    ]
    for r in rows:
        desc = (
            f"{r['site_id']} &middot; {r['state_name'] or 'no state'}<br>"
            f"area {r['area_ha']:.2f} ha &middot; group {r['group_id']}<br>"
            f"{escape(r['tags'])}<br><a href=\"{osm_url(r)}\">{osm_url(r)}</a>"
        )
        geoms = [f"<Point><coordinates>{r['lon']:.6f},{r['lat']:.6f},0</coordinates></Point>"]
        for poly in r["polys"]:
            g = f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{ring_coords(poly[0])}</coordinates></LinearRing></outerBoundaryIs>"
            g += "".join(
                f"<innerBoundaryIs><LinearRing><coordinates>{ring_coords(h)}</coordinates></LinearRing></innerBoundaryIs>"
                for h in poly[1:]
            )
            geoms.append(g + "</Polygon>")
        out.append(
            f"<Placemark><name>{escape(label(r))}</name><description>{escape(desc)}</description>"
            f"<styleUrl>#site</styleUrl><MultiGeometry>{''.join(geoms)}</MultiGeometry></Placemark>"
        )
    out.append("</Folder></Document></kml>")
    Path(path).write_text("\n".join(out), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("geojson", nargs="?", default=str(REPO / "data/raw/osm_landfill_india.geojson"),
                help="overpass-turbo export (Export > GeoJSON)")
    ap.add_argument("--out", default=str(REPO / "labels"))
    ap.add_argument("--holdout", default="IN-GJ", help="state ISO code held out as the test region")
    ap.add_argument("--buffer-states", default="IN-DH",
                    help="comma-separated ISO codes kept out of training because they sit inside or against the "
                         "held-out region (default: Dadra and Nagar Haveli and Daman and Diu)")
    ap.add_argument("--min-ha", type=float, default=1.0, help="sites at least this large are screened first")
    ap.add_argument("--group-m", type=float, default=500, help="sites closer than this share a group_id")
    args = ap.parse_args()

    with open(args.geojson, encoding="utf-8") as f:
        feats = json.load(f)["features"]
    states = StateIndex()
    buffer_states = {s for s in args.buffer_states.split(",") if s}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    seen, rows, excluded = set(), [], []
    for feat in feats:
        tags, otype, oid = osm_identity(feat)
        if (otype, oid) in seen:
            continue
        seen.add((otype, oid))
        polys = polygons(feat.get("geometry"))
        area_ha, centroid = area_centroid(polys)
        if centroid is None:
            g = feat.get("geometry") or {}
            if g.get("type") != "Point":
                excluded.append({"osm_type": otype, "osm_id": oid, "reason": "no_usable_geometry",
                                 "tags": json.dumps(tags, ensure_ascii=False)})
                continue
            centroid = tuple(g["coordinates"][:2])
        lon, lat = centroid
        iso, name, method = states.lookup(lon, lat)
        r = {
            "site_id": f"osm_{otype[:1]}{oid}", "osm_type": otype, "osm_id": oid,
            "state_iso": iso or "", "state_name": name or "", "state_method": method,
            "lat": round(lat, 6), "lon": round(lon, 6), "area_ha": round(area_ha, 3),
            "geometry": "polygon" if polys else "point",
            "tier": 1 if area_ha >= args.min_ha else 2,
            "name": tags.get("name", ""),
            "tags": "; ".join(f"{k}={v}" for k, v in sorted(tags.items()) if k != "landuse"),
            "polys": polys,
        }
        reason = exclusion_reason(tags)
        if reason is None and iso is None:
            reason = "outside_india_boundaries"
        if reason is None and iso in buffer_states:
            reason = "buffer_state_" + iso
        if reason:
            excluded.append({**r, "reason": reason})
        else:
            rows.append(r)

    assign_groups(rows, args.group_m)
    holdout = [r for r in rows if r["state_iso"] == args.holdout]
    train = [r for r in rows if r["state_iso"] != args.holdout]
    train = screening_order(train)
    holdout.sort(key=lambda r: -r["area_ha"])
    for i, r in enumerate(holdout, 1):
        r["screen_order"] = i

    base = ["screen_order", "site_id", "state_iso", "state_name", "lat", "lon", "area_ha", "tier",
            "geometry", "group_id", "name", "tags", "state_method", "osm_type", "osm_id"]
    write_csv(out / "india_screening.csv", train, base + SCREEN_COLUMNS)
    write_csv(out / "gujarat_osm_candidates.csv", holdout, base + SCREEN_COLUMNS)
    write_csv(out / "osm_excluded.csv", excluded,
              ["site_id", "osm_type", "osm_id", "reason", "state_iso", "lat", "lon", "area_ha", "name", "tags"])

    def area_label(r):
        return f"{r['area_ha']:.1f} ha" if r["geometry"] == "polygon" else "point"

    write_kml(out / "india_screening.kml", "India training candidates", train,
              lambda r: f"{r['screen_order']:04d} {r['state_iso'][3:]} {area_label(r)}")
    write_kml(out / "gujarat_osm_candidates.kml", "Gujarat OSM candidates (test-list building only)", holdout,
              lambda r: f"G{r['screen_order']:03d} {area_label(r)}")

    per_state = defaultdict(Counter)
    for r in train:
        per_state[(r["state_iso"], r["state_name"])][r["tier"]] += 1
    lines = [
        f"Input: {Path(args.geojson).name}, {len(feats)} features, {len(seen)} unique OSM objects",
        f"Excluded before screening: {len(excluded)}",
        *[f"  {k}: {v}" for k, v in Counter(e["reason"] for e in excluded).most_common()],
        f"Held out ({args.holdout}), for test-list screening only: {len(holdout)}",
        f"India training candidates: {len(train)} "
        f"(>= {args.min_ha:g} ha: {sum(r['tier'] == 1 for r in train)}, smaller or point: {sum(r['tier'] == 2 for r in train)})",
        f"Site groups at {args.group_m:g} m: {len({r['group_id'] for r in train})}",
        f"State assigned by snapping to the nearest boundary: {sum(r['state_method'] == 'snapped' for r in rows)}",
        "",
        "Training candidates per state (all / >= min-ha):",
        *[f"  {iso:6} {name:45} {c[1] + c[2]:4d} {c[1]:4d}"
          for (iso, name), c in sorted(per_state.items(), key=lambda kv: -sum(kv[1].values()))],
    ]
    (out / "osm_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
