# Phase 1: labels, step by step

Three label files come out of this phase: screened India training sites, a sealed Gujarat test list, and look-alike negatives. The scripts need only Python 3 with no extra packages. You can also upload the files to the Claude session and have them run there.

## 1. Export OSM landfills for India

Run this at [overpass-turbo.eu](https://overpass-turbo.eu), then use Export > GeoJSON > download. It adds a `node` line to the query in the checklist, so sites mapped only as a point are included too.

```
[out:json][timeout:900];
area["ISO3166-1"="IN"][admin_level=2]->.in;
(
  node["landuse"="landfill"](area.in);
  way["landuse"="landfill"](area.in);
  relation["landuse"="landfill"](area.in);
);
out geom;
```

Save it as `data/raw/osm_landfill_india.geojson`, then run:

```
python scripts/osm_to_screening.py data/raw/osm_landfill_india.geojson
```

| Output in `labels/` | What it is |
| --- | --- |
| `india_screening.csv`, `.kml` | Training candidates outside Gujarat, in screening order |
| `gujarat_osm_candidates.csv`, `.kml` | Gujarat OSM sites, used only to help build the sealed test list |
| `osm_excluded.csv` | Dropped before screening (disused, abandoned, end_date, quarry in name, outside India, Dadra and Nagar Haveli and Daman and Diu) |
| `osm_summary.txt` | Counts at each step, for the data-flow figure |

Sites of 1 ha or more come first in the order (1 ha is about one native Landsat thermal pixel). They're taken in turn across states, so stopping partway still leaves several states covered.

## 2. Screen the India candidates

1. Open `india_screening.kml` in Google Earth Pro (File > Open) and `india_screening.csv` in Excel.
2. Go down the list in `screen_order`. Double-clicking a placemark flies to it, and the yellow outline is what OSM mapped.
3. Turn on View > Historical Imagery and judge the site on the image closest to March–May 2024, which is the window the features come from.
4. Fill `decision`, `reason`, `imagery_date` (for example `2024-04`) and `notes`, if needed.
5. Stop at the end of the time box. Don't start the list again from the top.

The CSV is the record, so keep it as CSV when you save (Excel will ask; choose Keep Current Format). Don't sort or delete rows. Format the `imagery_date` column as Text before typing, or Excel turns `2024-04` into a date.

**Landfills that aren't on the list.** If you see one while screening, pin it in a Google Earth Pro folder named `extra_sites`; draw an outline where you can. The same 2024 rule applies, and the name can be anything. Don't go looking for them, and skip anything that's just part of a site already on the list (note it in that row instead). One found inside Gujarat goes in `gujarat_test`, not here. Save as `labels/extra_sites.kml`, then run `python scripts/kml_to_csv.py labels/extra_sites.kml --kind extra`.

| decision | When |
| --- | --- |
| `keep` | Active dumping visible in the 2024 image |
| `drop` | Anything else; give a `reason` |
| `unsure` | Can't tell. These are left out of both positives and negatives |

Mines count as `quarry`; fly-ash ponds next to coal power plants are `ash_pond`.

Drop reasons: `not_visible`, `inactive` (capped, vegetated or built over), `mislocated`, `too_small`, `quarry`, `kiln`, `bare_soil`, `construction`, `riverbed`, `ash_pond`, `other`. A site dropped as `quarry`, `kiln`, `bare_soil`, `construction`, `riverbed` or `ash_pond` is also a hand-checked look-alike, so it counts towards step 4.

## 3. Build and seal the Gujarat test list

1. In Google Earth Pro, use Add > Folder and name it `gujarat_test`.
2. Add one placemark per site, named `City | site name`, with the source in the description (for example `GPCB annual report 2023, p. 12` or `own knowledge`). Drawing the outline (Add > Polygon) is better than a pin: recall can then mean "any flagged pixel inside the outline", rather than within a radius you'd have to choose and justify.
3. Use `gujarat_osm_candidates.kml` and the GPCB, NGT and SBM-U / DRAP lists to get past your 14 sites to 20 or more. Confirm each one by eye.
4. Right-click the folder > Save Place As > `labels/gujarat_test.kml`, then run:

```
python scripts/kml_to_csv.py labels/gujarat_test.kml --kind gujarat
```

5. Commit `labels/gujarat_test.kml` and `labels/gujarat_test_sites.csv` and push. The pushed commit is the seal: don't change either file after it.

## 4. Pin look-alikes outside Gujarat

1. Make a folder named `lookalikes`. Each placemark's name starts with its class: `quarry`, `kiln`, `bare_soil`, `construction`, `riverbed`, `ash_pond` or `other` (for example `kiln 12`).
2. Pin them as you come across them while screening, in training states only. Any pin inside Gujarat is left out.
3. Save as `labels/lookalikes.kml`, then run:

```
python scripts/kml_to_csv.py labels/lookalikes.kml --kind lookalike
```

Random background negatives are drawn later in Earth Engine and need no hand work.
