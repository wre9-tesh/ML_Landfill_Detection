# Labels, sample points and features

The rules below were fixed before any model was run. The paper summarises them; this note gives the detail needed to rebuild the training table.

## 1. Training sites (outside Gujarat)

**Source of candidates.** OpenStreetMap features tagged `landuse=landfill` in India (nodes, ways and relations), fetched with this Overpass query on 3 November 2026 (snapshot in `data/raw/export.json`):

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

`scripts/osm_to_screening.py` drops disused, abandoned or end-dated features and anything named as a quarry, splits off Gujarat (used only to help build the test list), and writes the screening list `labels/india_screening.csv` / `.kml`.

**Screening.** Each candidate was judged by eye in Google Earth Pro historical imagery closest to March–May 2024, the window the features come from:

| decision | when |
| --- | --- |
| `keep` | Active dumping visible in the 2024 imagery |
| `drop` | Anything else, with a reason |
| `unsure` | Cannot tell; left out of both positives and negatives |

- If only 2023 and 2025 imagery exist, a site is kept when active on both, and only the area that is waste on both is outlined.
- Minimum size is 1 ha of visible waste, measured on the waste, not the compound (`drop`, `too_small`). 1 ha is about one native Landsat thermal pixel.
- Biomining areas count while waste is still there; finished, levelled ground does not.
- A wrongly placed OSM outline is dropped as `mislocated`; where the real dump is nearby, it is outlined again by hand.

**Drop reasons that become look-alike negatives:** `quarry` (also mines, ore, spoil, coal overburden), `kiln`, `bare_soil`, `construction`, `riverbed`, `ash_pond`, `industrial` (slag, coal, stockyards, red mud, gypsum). Drops for `not_visible`, `inactive`, `mislocated`, `too_small` or `other` give no points.

**Own outlines.** Active landfills not in OSM, found while screening, were outlined by hand (`Extra_Sites` folder of `labels/ML landfill detection_india_screening.kml`, converted with `scripts/kml_to_csv.py --kind extra --folder Extra_Sites` to `labels/extra_sites.csv` / `.geojson`).

Result: 13 OSM sites kept and 82 own outlines. Outlines within 500 m of each other are one *place*, which gives 86 landfill places in 26 states, plus 60 look-alike places.

## 2. Gujarat test lists (never used in training)

- **First list:** `labels/gujarat_test_sites.csv` / `.geojson`, from `labels/Gujarat_landfills_ml_test.kml`. There are 17 outlined dumpsites in 13 cities, all 1 ha or more. Only confirmed dumps are listed; nothing else in Gujarat is labelled. The list was sealed in commit `8711855` before any model was run on Gujarat.
- **New-cities list:** `labels/gujarat_new_sites.csv` / `.geojson`, with 6 sites in 6 further cities. It was sealed in commit `fc81cd5` and scored once with the frozen version 3 model.
- **Scored area:** a box 15 km beyond the test sites of each city (`labels/gujarat_boxes.json`, as exported). Land outside the boxes is not scored.

## 3. Sample points (`scripts/build_samples.py`, `scripts/build_background_v2.py`)

| kind | label | taken from | how many |
| --- | --- | --- | --- |
| `site` | 1 | Kept outlines and own outlines | Up to 50 per place |
| `lookalike` | 0 | Look-alike drops | Up to 30 per place |
| `random` | 0 | Anywhere in the states that supply sites, split by each state's share of site points | As many as site points |
| `near_site` | 0 | Boxes 15 km around each training landfill, at least 500 m from any mapped site (added in version 2) | 25,800 |

- The cap per place stops one 300 ha landfill outweighing thirty 3 ha ones.
- Points lie at least 15 m inside the outline and at least 15 m apart, so no 10 m pixel is sampled twice.
- Background points lie at least 500 m from any mapped landfill or look-alike.
- Each place and state has its own seeded random stream, so the points are reproducible.

## 4. Features (`scripts/gee_features.py`)

Pre-monsoon window, 1 March – 31 May 2024 (12 features, used by all versions):

| feature | source and processing |
| --- | --- |
| `B2 B3 B4 B8 B11` | Sentinel-2 surface reflectance, median of scenes under 10% cloud, masked with the scene classification layer |
| `NDVI`, `NDBI`, `BSI` | From the median bands: (B8−B4)/(B8+B4), (B11−B8)/(B11+B8), ((B11+B4)−(B8+B2))/((B11+B4)+(B8+B2)) |
| `LST` | Landsat 8/9 surface temperature (°C), median of scenes under 30% cloud, bilinear to 10 m |
| `LST_anom` | LST minus the mean LST of land within 2 km at 100 m; permanent water (JRC, ≥50% occurrence) is excluded from the mean |
| `elev`, `slope` | SRTM elevation (m) and slope (degrees) |

Added in version 3 (`--stack extra`, 14 features):

| feature | definition |
| --- | --- |
| `B2_w B11_w NDVI_w NDBI_w BSI_w` | Sentinel-2 median, 15 November 2023 – 14 February 2024 (winter crop season) |
| `NDVI_ctx NDBI_ctx BSI_ctx` | Mean of the pre-monsoon index within 150 m |
| `NDVI_sd B11_sd` | Standard deviation of the pre-monsoon value within 50 m |
| `dNDVI dBSI` | Winter minus pre-monsoon |
| `NDVI_rel NDBI_rel` | Pixel minus its 150 m mean |

Every setting is recorded in the `features_meta.json` next to each feature table. When Gujarat is scored, `gee_features.feature_image()` builds the same stack.
