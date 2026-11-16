"""Cut small true-colour pictures ("chips") for the website from the Gujarat rasters.

    python scripts/make_chips.py          (on the machine holding data/gujarat/*.tif)
    python scripts/build_site_data.py     (afterwards, so the pages pick the chips up)

Run it only after the hand check of the top 100 alarms is finished and committed: the chips
show those same places.

For each of the 17 sealed sites, the Surendranagar site and the top 100 version 3 alarms it
writes, in docs/site/img/chips/:
    <id>.jpg         Sentinel-2 bands B4, B3, B2 (March to May 2024 median), 1.5 km across,
                     or 3 km for an outline wider than 1.2 km; 450 x 450 pixels
    <id>_score.png   the pixels the frozen model flagged, same window, transparent elsewhere
and docs/site/data/chips.json, the index the galleries read. Reflectance 0.02 to 0.30 is
stretched to the full range with gamma 0.8.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from geoutil import REPO

UNSEEN = {"id": "UNSEEN", "name": "Surendranagar landfill (not on the test list)", "lat": 22.7418, "lon": 71.5922}
ORANGE = (235, 104, 52, 150)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tifs", default=str(REPO / "data" / "gujarat"))
    ap.add_argument("--results", default=str(REPO / "data" / "gujarat_results_v3"))
    ap.add_argument("--out", default=str(REPO / "docs" / "site"))
    ap.add_argument("--top", type=int, default=100)
    args = ap.parse_args()
    try:
        import rasterio
        from PIL import Image
        from rasterio.warp import transform as warp_xy, transform_geom
        from rasterio.windows import Window
    except ImportError:
        sys.exit("rasterio and Pillow are needed. Run: python -m pip install rasterio pillow")
    res = Path(args.results)
    check = pd.read_csv(res / "blind_check.csv", keep_default_na=False)
    if (check.verdict.str.strip() == "").any():
        sys.exit("The hand check is not finished (blind_check.csv has empty verdicts). Finish and commit it first.")

    targets = []
    recall = pd.read_csv(res / "site_recall.csv").set_index("test_id")
    for f in json.load(open(REPO / "labels" / "gujarat_test_sites.geojson", encoding="utf-8"))["features"]:
        g = f["geometry"]
        if g["type"] == "Point":
            continue
        rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        xy = np.array([p for r in rings for p in r], float)
        tid = f["properties"]["test_id"]
        row = recall.loc[tid]
        targets.append({"id": tid, "kind": "site", "city": f["properties"]["city"], "name": f"{f['properties']['city']} ({tid})",
                        "lon": float((xy[:, 0].min() + xy[:, 0].max()) / 2), "lat": float((xy[:, 1].min() + xy[:, 1].max()) / 2),
                        "rings": rings, "area_ha": float(row.area_ha),
                        "note": f"{float(row.area_ha):.0f} ha. {round(100 * float(row.share_flagged))}% of the outline flagged: {row.status}."})
    targets.append({**UNSEEN, "kind": "unseen", "city": "Surendranagar", "rings": [], "note": "In neither the training data nor the test list."})
    alarms = pd.read_csv(res / "alarms.csv").head(args.top)
    for r in alarms.itertuples():
        targets.append({"id": r.blind_id, "kind": "alarm", "city": r.city, "lon": float(r.lon), "lat": float(r.lat), "rings": [],
                        "rank": int(r.rank), "mean_score": float(r.mean_score), "area_ha": float(r.area_ha)})

    out = Path(args.out)
    (out / "img" / "chips").mkdir(parents=True, exist_ok=True)
    index, missing = [], []
    tifs = sorted(Path(args.tifs).glob("gujarat_*.tif"))
    if not tifs:
        sys.exit(f"no gujarat_*.tif files in {args.tifs}")
    done = set()
    for tif in tifs:
        score_tif = res / "scores" / tif.name
        with rasterio.open(tif) as src, rasterio.open(score_tif) as sc:
            names = list(src.descriptions)
            bands = [names.index(b) + 1 for b in ("B4", "B3", "B2")]
            xs, ys = warp_xy("EPSG:4326", src.crs, [t["lon"] for t in targets], [t["lat"] for t in targets])
            n_here = 0
            for t, x, y in zip(targets, xs, ys):
                if t["id"] in done:
                    continue
                size = 150
                if t["rings"]:
                    rr = [transform_geom("EPSG:4326", src.crs, {"type": "Polygon", "coordinates": [r]})["coordinates"][0] for r in t["rings"]]
                    a = np.array([p for r in rr for p in r], float)
                    if max(np.ptp(a[:, 0]), np.ptp(a[:, 1])) > 1200:
                        size = 300
                row, col = src.index(x, y)
                if not (0 <= row < src.height and 0 <= col < src.width):
                    continue
                # Near a box edge the window is moved inwards, so the place is off-centre in its chip.
                r0 = int(np.clip(row - size // 2, 0, src.height - size))
                c0 = int(np.clip(col - size // 2, 0, src.width - size))
                win = Window(c0, r0, size, size)
                rgb = np.stack([src.read(b, window=win).astype(np.float32) for b in bands], axis=-1)
                s = sc.read(1, window=win)
                flagged = (s >= 50) & (s != 255)
                if size == 300:
                    rgb = np.nanmean(rgb.reshape(150, 2, 150, 2, 3), axis=(1, 3))
                    flagged = flagged.reshape(150, 2, 150, 2).mean(axis=(1, 3)) >= 0.5
                rgb = np.clip((np.nan_to_num(rgb, nan=0.02) - 0.02) / 0.28, 0, 1) ** 0.8
                img = Image.fromarray((rgb * 255).astype(np.uint8), "RGB").resize((450, 450), Image.NEAREST)
                img.save(out / "img" / "chips" / f"{t['id']}.jpg", "JPEG", quality=85)
                ov = np.zeros((150, 150, 4), np.uint8)
                ov[flagged] = ORANGE
                Image.fromarray(ov, "RGBA").resize((450, 450), Image.NEAREST).save(out / "img" / "chips" / f"{t['id']}_score.png", "PNG", optimize=True)
                tr = src.window_transform(win)
                outline = []
                if t["rings"]:
                    outline = [[[round((px - tr.c) / tr.a / size, 4), round((py - tr.f) / tr.e / size, 4)] for px, py in r] for r in rr]
                index.append({k: v for k, v in t.items() if k != "rings"} | {"size_m": size * 10, "outline": outline})
                done.add(t["id"])
                n_here += 1
        print(f"  {tif.name}: {n_here} chips")
    missing = [t["id"] for t in targets if t["id"] not in done]
    index.sort(key=lambda c: (c["kind"] != "site", c.get("rank", 0), c["id"]))
    (out / "data" / "chips.json").write_text(json.dumps(index, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(index)} chips to {out / 'img' / 'chips'}" + (f"; not cut (outside every raster): {', '.join(missing)}" if missing else ""))
    print("now run: python scripts/build_site_data.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
