"""Convert placemarks saved from Google Earth Pro into a label CSV.

    python scripts/kml_to_csv.py gujarat_test.kml --kind gujarat
    python scripts/kml_to_csv.py lookalikes.kml --kind lookalike
    python scripts/kml_to_csv.py extra_sites.kml --kind extra

Accepts .kml or .kmz, points or drawn polygons (a polygon gives its centroid
and area). Writes the CSV and, next to it, a GeoJSON with the same rows and
their outlines, which scripts/build_samples.py samples from. Naming rules, set
in docs/phase1_labels.md:
  gujarat    "City | site name", source in the description
  lookalike  name starts with the class: quarry, kiln, bare_soil, construction, riverbed, ash_pond, industrial, other
  extra      active landfills found while screening that are not in the OSM list; any name

Every row is checked against the state boundaries. A Gujarat site outside
Gujarat is reported. A look-alike or extra site inside the held-out region is
left out, because training labels must come from outside it.
"""
import argparse
import csv
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from geoutil import REPO, StateIndex, area_centroid

LOOKALIKE_CLASSES = {
    "quarry": "quarry", "mine": "quarry", "ore": "quarry", "spoil": "quarry",
    "brick_kiln": "kiln", "kiln": "kiln",
    "bare_soil": "bare_soil", "baresoil": "bare_soil", "soil": "bare_soil",
    "construction": "construction",
    "ash_pond": "ash_pond", "ashpond": "ash_pond", "fly_ash": "ash_pond", "coal_ash": "ash_pond", "ash": "ash_pond",
    "industrial": "industrial", "slag": "industrial", "coal": "industrial", "stockpile": "industrial",
    "stockyard": "industrial", "red_mud": "industrial", "phosphogypsum": "industrial", "gypsum": "industrial",
    "dry_riverbed": "riverbed", "riverbed": "riverbed", "river": "riverbed",
    "other": "other",
}


def local(tag):
    return tag.rsplit("}", 1)[-1]


def parse_coords(text):
    pts = []
    for tok in (text or "").split():
        parts = tok.split(",")
        if len(parts) >= 2:
            pts.append((float(parts[0]), float(parts[1])))
    return pts


def read_kml(path):
    if path.suffix.lower() == ".kmz":
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".kml"))
            data = z.read(name)
    else:
        data = path.read_bytes()
    return ElementTree.fromstring(data)


def placemarks(root):
    """Yield one dict per placemark: folder, name, desc, lon, lat, area_ha, geometry and polys."""

    def walk(el, folders):
        for child in el:
            t = local(child.tag)
            if t in ("Folder", "Document"):
                name = next((c.text for c in child if local(c.tag) == "name"), "") or ""
                yield from walk(child, folders + [name] if t == "Folder" else folders)
            elif t == "Placemark":
                yield from one(child, folders)

    def one(pm, folders):
        name = desc = ""
        polys, point = [], None
        for el in pm.iter():
            t = local(el.tag)
            if t == "name" and not name:
                name = (el.text or "").strip()
            elif t == "description" and not desc:
                desc = re.sub(r"<[^>]+>", " ", el.text or "").strip()
            elif t == "Point":
                c = next((x for x in el.iter() if local(x.tag) == "coordinates"), None)
                pts = parse_coords(c.text if c is not None else "")
                if pts:
                    point = pts[0]
            elif t == "Polygon":
                rings = []
                for b in el:
                    if local(b.tag) in ("outerBoundaryIs", "innerBoundaryIs"):
                        c = next((x for x in b.iter() if local(x.tag) == "coordinates"), None)
                        ring = parse_coords(c.text if c is not None else "")
                        if len(ring) < 3:
                            continue
                        if local(b.tag) == "outerBoundaryIs":
                            rings.insert(0, ring)
                        else:
                            rings.append(ring)
                if rings:
                    polys.append(rings)
        base = {"folder": " / ".join(folders), "name": name, "desc": desc}
        if polys:
            area, (lon, lat) = area_centroid(polys)
            yield {**base, "lon": lon, "lat": lat, "area_ha": round(area, 3), "geometry": "polygon", "polys": polys}
        elif point:
            yield {**base, "lon": point[0], "lat": point[1], "area_ha": "", "geometry": "point", "polys": []}

    yield from walk(root, [])


def write_geojson(path, rows, geoms):
    feats = []
    for r, (polys, lon, lat) in zip(rows, geoms):
        if polys:
            g = {"type": "MultiPolygon", "coordinates": [[[list(p) for p in ring] for ring in poly] for poly in polys]}
        else:
            g = {"type": "Point", "coordinates": [lon, lat]}
        feats.append({"type": "Feature", "properties": r, "geometry": g})
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False)


def lookalike_class(name):
    key = re.sub(r"[\s\-]+", "_", name.strip().lower())
    for alias in sorted(LOOKALIKE_CLASSES, key=len, reverse=True):
        if key == alias or key.startswith(alias + "_") or re.match(re.escape(alias) + r"\d", key):
            return LOOKALIKE_CLASSES[alias]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kml")
    ap.add_argument("--kind", choices=["gujarat", "lookalike", "extra"], required=True)
    ap.add_argument("--out", help="CSV path (default labels/gujarat_test_sites.csv, lookalikes.csv or extra_sites.csv)")
    ap.add_argument("--holdout", default="IN-GJ")
    args = ap.parse_args()

    states = StateIndex()
    rows, geoms, problems = [], [], []
    for pm in placemarks(read_kml(Path(args.kml))):
        name, lon, lat = pm["name"], pm["lon"], pm["lat"]
        iso, sname, method = states.lookup(lon, lat)
        base = {"lat": round(lat, 6), "lon": round(lon, 6), "area_ha": pm["area_ha"], "geometry": pm["geometry"],
                "state_iso": iso or "", "state_method": method, "folder": pm["folder"], "notes": pm["desc"]}
        n_before = len(rows)
        if args.kind == "gujarat":
            city, sep, site = (p.strip() for p in name.partition("|"))
            if not sep:
                problems.append(f"name has no 'City | site' separator, kept as site name: {name!r}")
                city, site = "", name
            if iso != args.holdout:
                problems.append(f"outside {args.holdout} ({iso or 'no state'}): {name!r}")
            rows.append({"test_id": f"GJ{len(rows) + 1:02d}", "city": city, "site_name": site, **base})
        elif args.kind == "extra":
            if iso == args.holdout:
                problems.append(f"inside the held-out region, row left out (add it to gujarat_test instead): {name!r}")
                continue
            rows.append({"site_id": f"ex{len(rows) + 1:04d}", "name": name, **base})
        else:
            cls = lookalike_class(name)
            if cls is None:
                problems.append(f"unknown class, row left out: {name!r}")
                continue
            if iso == args.holdout:
                problems.append(f"inside the held-out region, row left out: {name!r}")
                continue
            rows.append({"lookalike_id": f"la{len(rows) + 1:04d}", "class": cls, "name": name, **base})
        if len(rows) > n_before:
            geoms.append((pm["polys"], lon, lat))

    if args.kind == "gujarat":
        cols = ["test_id", "city", "site_name", "lat", "lon", "area_ha", "geometry", "state_iso", "state_method",
                "folder", "notes"]
        out = Path(args.out or REPO / "labels" / "gujarat_test_sites.csv")
    elif args.kind == "extra":
        cols = ["site_id", "name", "state_iso", "lat", "lon", "area_ha", "geometry", "state_method", "folder", "notes"]
        out = Path(args.out or REPO / "labels" / "extra_sites.csv")
    else:
        cols = ["lookalike_id", "class", "name", "state_iso", "lat", "lon", "area_ha", "geometry", "state_method",
                "folder", "notes"]
        out = Path(args.out or REPO / "labels" / "lookalikes.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    write_geojson(out.with_suffix(".geojson"), rows, geoms)

    print(f"{len(rows)} rows written to {out} and {out.with_suffix('.geojson').name}")
    if args.kind == "lookalike":
        counts = {}
        for r in rows:
            counts[r["class"]] = counts.get(r["class"], 0) + 1
        print("  " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    for p in problems:
        print("  check:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
