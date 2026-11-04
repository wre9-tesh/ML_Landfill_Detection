"""Stdlib-only geometry helpers shared by the label scripts.

Coordinates are GeoJSON order, (lon, lat), in degrees. Areas use a local
equirectangular projection per ring, which is accurate to well under 1% at
landfill scale and needs no projection library.
"""
import json
import math
from pathlib import Path

EARTH_R = 6371008.8
REPO = Path(__file__).resolve().parent.parent
STATES_GEOJSON = REPO / "data" / "boundaries" / "geoBoundaries-IND-ADM1_simplified.geojson"

# Zonal Councils of India, the fallback regions if too few states have enough sites for
# their own validation fold. The island territories attend the Southern council.
ZONAL_COUNCILS = {
    **dict.fromkeys(["IN-HR", "IN-HP", "IN-PB", "IN-RJ", "IN-DL", "IN-CH", "IN-JK", "IN-LA"], "Northern"),
    **dict.fromkeys(["IN-CT", "IN-UT", "IN-UP", "IN-MP"], "Central"),
    **dict.fromkeys(["IN-BR", "IN-JH", "IN-OR", "IN-WB"], "Eastern"),
    **dict.fromkeys(["IN-GA", "IN-GJ", "IN-MH", "IN-DH"], "Western"),
    **dict.fromkeys(["IN-AP", "IN-KA", "IN-KL", "IN-TN", "IN-TG", "IN-PY", "IN-AN", "IN-LD"], "Southern"),
    **dict.fromkeys(["IN-AS", "IN-AR", "IN-MN", "IN-ML", "IN-MZ", "IN-NL", "IN-SK", "IN-TR"], "North-Eastern"),
}


def haversine_m(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(h))


def ring_area_centroid(ring):
    """Unsigned area in m^2 and centroid (lon, lat) of one lon/lat ring."""
    lon0, lat0 = ring[0][0], ring[0][1]
    kx = math.radians(1) * EARTH_R * math.cos(math.radians(lat0))
    ky = math.radians(1) * EARTH_R
    pts = [((p[0] - lon0) * kx, (p[1] - lat0) * ky) for p in ring]
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    if abs(a) < 1e-9:
        n = len(ring)
        return 0.0, (sum(p[0] for p in ring) / n, sum(p[1] for p in ring) / n)
    cx, cy = cx / (3 * a), cy / (3 * a)
    return abs(a) / 2, (lon0 + cx / kx, lat0 + cy / ky)


def polygons(geom):
    """Polygons in a GeoJSON geometry, each a list of rings (outer first).

    A closed LineString counts as a polygon; points and open lines give none.
    """
    if not geom:
        return []
    t, c = geom["type"], geom.get("coordinates")
    if t == "Polygon":
        return [c]
    if t == "MultiPolygon":
        return list(c)
    if t == "LineString" and len(c) >= 4 and c[0] == c[-1]:
        return [[c]]
    if t == "GeometryCollection":
        return [p for g in geom["geometries"] for p in polygons(g)]
    return []


def area_centroid(polys):
    """Area in hectares and area-weighted centroid (lon, lat) of polygons."""
    total = sx = sy = 0.0
    for poly in polys:
        for i, ring in enumerate(poly):
            a, (x, y) = ring_area_centroid(ring)
            w = a if i == 0 else -a
            total += w
            sx += w * x
            sy += w * y
    if total <= 0:
        return 0.0, None
    return total / 1e4, (sx / total, sy / total)


def point_in_ring(lon, lat, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def point_in_polygon(lon, lat, poly):
    return point_in_ring(lon, lat, poly[0]) and not any(point_in_ring(lon, lat, h) for h in poly[1:])


class StateIndex:
    """Point-in-state lookup over the geoBoundaries ADM1 file.

    A point outside every polygon (coastal sites can fall just outside the
    simplified coastline) goes to the nearest state boundary within
    `max_snap_km`, and the method column records that it was snapped.
    """

    def __init__(self, path=STATES_GEOJSON, iso_field="shapeISO", name_field="shapeName", max_snap_km=20):
        with open(path, encoding="utf-8") as f:
            feats = json.load(f)["features"]
        self.max_snap_m = max_snap_km * 1000
        self.states = []
        for ft in feats:
            polys = polygons(ft["geometry"])
            xs = [p[0] for poly in polys for p in poly[0]]
            ys = [p[1] for poly in polys for p in poly[0]]
            self.states.append({
                "iso": ft["properties"][iso_field],
                "name": ft["properties"][name_field],
                "polys": polys,
                "bbox": (min(xs), min(ys), max(xs), max(ys)),
            })

    def lookup(self, lon, lat):
        """(iso, name, method) where method is 'inside', 'snapped' or 'none'."""
        for s in self.states:
            x0, y0, x1, y1 = s["bbox"]
            if x0 <= lon <= x1 and y0 <= lat <= y1 and any(point_in_polygon(lon, lat, p) for p in s["polys"]):
                return s["iso"], s["name"], "inside"
        pad = self.max_snap_m / 111_000 * 1.5
        best = (None, None, float("inf"))
        for s in self.states:
            x0, y0, x1, y1 = s["bbox"]
            if not (x0 - pad <= lon <= x1 + pad and y0 - pad <= lat <= y1 + pad):
                continue
            for poly in s["polys"]:
                for p in poly[0]:
                    if abs(p[0] - lon) < pad and abs(p[1] - lat) < pad:
                        d = haversine_m(lon, lat, p[0], p[1])
                        if d < best[2]:
                            best = (s["iso"], s["name"], d)
        if best[2] <= self.max_snap_m:
            return best[0], best[1], "snapped"
        return None, None, "none"


class RingIndex:
    """Point-in-ring test that only checks edges in the point's latitude band.

    Same answer as point_in_ring, but fast enough to place thousands of random
    points inside state outlines with thousands of vertices.
    """

    def __init__(self, ring, nbands=512):
        ys = [p[1] for p in ring]
        self.y0, self.y1 = min(ys), max(ys)
        self.h = (self.y1 - self.y0) / nbands or 1e-12
        self.bands = [[] for _ in range(nbands)]
        for a, b in zip(ring, ring[1:] + ring[:1]):
            lo, hi = sorted((a[1], b[1]))
            for k in range(self.band(lo), self.band(hi) + 1):
                self.bands[k].append((a[0], a[1], b[0], b[1]))

    def band(self, y):
        return min(max(int((y - self.y0) / self.h), 0), len(self.bands) - 1)

    def contains(self, x, y):
        if not self.y0 <= y <= self.y1:
            return False
        inside = False
        for x1, y1, x2, y2 in self.bands[self.band(y)]:
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
        return inside


class PolygonIndex:
    """Fast containment for a list of polygons (outer ring first, then holes)."""

    def __init__(self, polys):
        self.parts = [(RingIndex(p[0]), [RingIndex(h) for h in p[1:]]) for p in polys]
        xs = [q[0] for p in polys for q in p[0]]
        ys = [q[1] for p in polys for q in p[0]]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))

    def contains(self, x, y):
        return any(o.contains(x, y) and not any(h.contains(x, y) for h in holes) for o, holes in self.parts)
