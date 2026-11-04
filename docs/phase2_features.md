# Phase 2: sample points and Earth Engine features

Two scripts turn the screening decisions into the training table. `build_samples.py` picks sample points from your decisions and needs no internet; `gee_features.py` reads the ten features at those points from Earth Engine. Run both after each screening session: points already drawn and features already fetched are reused, so each run only adds what is new.

## One-time setup

```
pip install earthengine-api
earthengine authenticate
```

The second command opens a browser to sign in. You also need the ID of the Google Cloud project registered for Earth Engine (the Contributor-tier one): it is shown at the top right of [code.earthengine.google.com](https://code.earthengine.google.com) and in the project picker of the Cloud console.

## Each run

1. Save `labels/india_screening.csv` (as CSV). If you added extra sites or look-alikes, save their KML and convert it as in [phase1_labels.md](phase1_labels.md); that also writes the `.geojson` outlines the sampler reads.
2. Run `python scripts/build_samples.py`. It prints the point counts and which states have enough kept places for their own validation fold. Fix anything on a `check:` line (an unrecognised decision or reason, for example) and run it again.
3. The first time, run `python scripts/gee_features.py --project YOUR-PROJECT-ID --limit 50` as a quick test, then the same command without `--limit`.
4. Commit and push `labels/`, `data/samples/` and `data/features/`.

If `gee_features.py` stops or shows errors, run it again: it continues where it stopped. If it keeps splitting batches, add `--batch 100`.

Until screening is finished, most states will show "training only" in the fold table. That is expected; it fills in as you screen.

## The points

| Kind | Label | Taken from | How many |
| --- | --- | --- | --- |
| `site` | 1 | Kept outlines, and extra sites | Up to 50 per place |
| `lookalike` | 0 | Drops with reason `quarry`, `kiln`, `bare_soil`, `construction`, `riverbed`, `ash_pond` or `industrial`, and pinned look-alikes | Up to 30 per place |
| `random` | 0 | Anywhere in the states that supply sites | As many as site points in total, split by each state's share of them |

A place is a `group_id`: outlines within 500 m of each other. The rest of the design, and the reason for each choice:

- **A cap per place**, so one 300 ha landfill does not outweigh thirty 3 ha ones.
- **At least 15 m inside the outline**: OSM outlines are approximate, and pixels on the edge mix waste with whatever surrounds it.
- **At least 15 m between points of a place**, so no 10 m pixel is sampled twice.
- **A pin without an outline stands for a disc of 20 m radius.** Draw outlines where you can.
- **Random points split by state**, so every held-out state has a similar balance of landfill and background.
- **Random points at least 500 m from any mapped landfill, extra site or look-alike**, so an unscreened landfill cannot end up labelled as background.
- **Each place and each state has its own seeded random stream**, so adding decisions leaves the points already drawn where they were.

Blank and `unsure` rows, and drops for `not_visible`, `inactive`, `mislocated`, `too_small` or `other`, give no points.

## The features

All from the 2024 pre-monsoon window, 1 March to 31 May 2024.

| Feature | Source and processing |
| --- | --- |
| `B3`, `B4`, `B8`, `B11` | Sentinel-2 surface reflectance: median of scenes under 10% cloud, with cloud, shadow, cirrus, snow and defective pixels masked by the scene classification layer |
| `NDVI`, `NDBI` | From the median bands: (B8 − B4) / (B8 + B4) and (B11 − B8) / (B11 + B8) |
| `LST` | Landsat 8/9 surface temperature in °C: median of scenes under 30% cloud, with cloud and shadow pixels masked, bilinear to 10 m |
| `LST_anom` | LST minus the mean LST of land within 2 km, computed at 100 m, about the native thermal resolution. Permanent water (JRC Global Surface Water, at least 50% occurrence) is left out of the mean, so coastal sites are not made to look hotter than they are |
| `elev`, `slope` | SRTM elevation (m) and slope (degrees), slope computed at the native 30 m |

The Landsat scene filter is looser than the Sentinel-2 one because there are fewer thermal scenes (one every 8 days from the two satellites, against one every 5 days); cloudy pixels are masked either way. A point whose pixel is masked in every scene comes back empty: `features.csv` keeps the row, and the modelling step reports and drops it.

Every setting is written to `data/features/features_meta.json` with the run, and `gee_features.feature_image()` builds the same stack when Gujarat is scored in Phase 3.
