# Website plan

Build specification for the project website. Written 16 November 2026, before the site is built. It is meant to be complete enough that someone who has not followed the project can build the site from this file and the repository.

**As built (16 November):** the site follows this plan with four changes. (1) Page text lives in `site_src/*.html` with placeholders such as `{{k:guj.sites_found}}`; `scripts/build_site_data.py` fills them and writes `docs/*.html`, so there is no separate `--fill` step and `--check` compares everything it would write with what is on disk. (2) Maps and the flagged-pixel box maps are written into the pages at build time, not fetched by script. (3) Figure X5 is two ranked bar charts, not a segmented bar, to keep to three colours. (4) Margin notes fall back into the text column where they would overlap a full-width figure. Fixed text (page list, feature descriptions, glossary) is in `scripts/site_text.py`.

Site address once published: `https://wre9-tesh.github.io/ML_Landfill_Detection/`

Contents: [1 Purpose and constraints](#1-purpose-and-constraints) · [2 Decisions](#2-decisions-already-made) · [3 Course requirements](#3-course-requirements-and-where-each-is-met) · [4 Architecture](#4-architecture) · [5 Data pipeline](#5-data-pipeline) · [6 Design system](#6-design-system) · [7 Pages](#7-page-specifications) · [8 Interactions](#8-interaction-specifications) · [9 Charts](#9-chart-catalogue) · [10 Wording rules](#10-wording-rules) · [11 Glossary](#11-glossary-and-margin-notes) · [12 Pending inputs](#12-pending-inputs) · [13 Build order](#13-build-order-and-cuts) · [14 Acceptance checks](#14-acceptance-checks) · [15 Publishing](#15-publishing) · [16 Open items](#16-open-items-for-the-author)

---

## 1. Purpose and constraints

The course grades the project from what is submitted, and states that a grader "should be able to understand and assess your project from the website alone". The site therefore carries the full reasoning from question to conclusion. The repository is where a grader verifies it.

- **Reader:** a course grader who knows machine learning (F1, cross-validation, gradient boosting) but not remote sensing. Remote-sensing terms get a short definition beside the text. ML terms get a one-line reminder where the project uses them in a specific way (for example, what "held-out region" means here).
- **Main path:** version 3 only (the gradient-boosting model with 26 features). Versions 1 and 2 appear in two places: a short disclosure, and the section "How we got here" (one paragraph and one table).
- **Framing:** a diagnostic study. The model finds 16 of 17 known sites and also flags 5.2% of the land. The site explains what it finds, what it wrongly flags, and why.
- **Deadline:** Tuesday 17 November 2026. Section 13 gives the build order and what to cut first.
- **No private data:** no email address, no Earth Engine project ID, no keys, no absolute local paths anywhere in `docs/`.

## 2. Decisions already made

| Topic | Decision |
| --- | --- |
| Layout | Multi-page site, six pages |
| Pages | Overview · Data · Method · Results · Diagnosis · Reproduce |
| Reader level | Knows ML; short definitions as memory aids and for context |
| Definitions | Margin notes beside the text, plus a glossary |
| Interactions | Feature explorer and threshold slider. No alarm map, no rarity slider |
| Imagery | Sentinel-2 true-colour chips of example sites and alarms |
| Look | Plain academic, with a light and a dark mode |
| Versions | Version 3 is the main path; short disclosure; "How we got here" as one paragraph and a table |
| New-cities blind test | Specified as an optional section that can be dropped without other changes |
| Notebooks | Not required, not built |

## 3. Course requirements and where each is met

The same table appears on the Overview page (section 7.1) so a grader can jump to each item.

| Required on the website | Page and section |
| --- | --- |
| The question and what one row represents | Overview §1; Data §1 |
| The data: source, size, key variables, quality issues | Data §2 to §6 |
| Preprocessing choices and why | Method §1 |
| Baseline and models compared | Method §2 |
| Evaluation: split and metrics | Method §3 to §6 |
| Results with error analysis | Results (all); Diagnosis §1 to §7 |
| Limitations | Diagnosis §9 |
| At least one interaction | Data §5 (feature explorer); Results §2 (threshold slider) |
| Setup and run steps, data access | Reproduce §1 to §4 |
| AI-use disclosure and citations | Reproduce §6 and §7 |
| ES 678: depth component | Diagnosis (all); paper linked from every page footer |

## 4. Architecture

### 4.1 Principles

- **Static files only.** Hand-written HTML, one CSS file, a few plain JavaScript files. No framework, no bundler, no Node step.
- **Nothing loaded from other servers.** Libraries are copied into the repository. Fonts are system fonts. The site works offline from a clone (through a local web server, see 15.3).
- **Readable without JavaScript.** All text, tables and numbers are in the HTML. JavaScript adds the charts, the two interactions and the theme switch. Every chart has a table of its values in a collapsed `<details>` block, which is also the no-script fallback.
- **Every number is traceable.** Numbers in the prose are tagged and filled from one generated file (5.3). A check command fails if a page and the result files disagree.

### 4.2 Hosting

GitHub Pages, "Deploy from a branch", branch `main`, folder `/docs`. An empty file `docs/.nojekyll` turns off Jekyll so files are served as they are. The existing Markdown notes and guide PDFs in `docs/` stay where they are and become reachable by direct link, which is intended.

### 4.3 File tree

```
docs/
  .nojekyll
  index.html            Overview
  data.html             Data
  method.html           Method
  results.html          Results
  diagnosis.html        Diagnosis
  reproduce.html        Reproduce (also holds the glossary)
  paper.pdf             copy of the four-page paper (added when written)
  site/
    css/site.css
    js/theme.js         theme switch; loaded in <head>, not deferred
    js/common.js        navigation state, number formatting, table-view toggles
    js/charts.js        chart helpers and all static charts
    js/explorer.js      feature explorer
    js/threshold.js     threshold slider
    js/gallery.js       chip gallery and score overlay
    vendor/d3.min.js    D3 7.9.0, unmodified
    vendor/plot.min.js  Observable Plot 0.6.17, unmodified
    vendor/LICENSES.txt ISC licence texts for both
    data/site.json          every number used in prose (5.3)
    data/tables.json        data behind static charts and tables (5.4)
    data/features_hist.json feature explorer (5.5)
    data/threshold.json     threshold slider (5.6)
    data/maps.json          outlines and box frames in image coordinates (5.7)
    data/chips.json         chip index (5.8)
    img/india.svg  img/gujarat.svg      locator maps (5.7)
    img/boxes/<city>.png                flagged-pixel layer per scored box (5.7)
    img/chips/<id>.jpg                  true-colour chips (5.8)
    img/chips/<id>_score.png            flagged-pixel overlay per chip (5.8)
scripts/
  build_site_data.py    writes docs/site/data/* and docs/site/img/{india,gujarat}.svg, boxes/
  make_chips.py         writes docs/site/img/chips/* and chips.json (needs the Gujarat rasters)
```

### 4.4 Libraries

| Library | Version | Use | Why |
| --- | --- | --- | --- |
| D3 | 7.9.0 | Required by Plot; scales in the two interactions | Standard, ISC licence |
| Observable Plot | 0.6.17 | All charts | Short declarative code, SVG output, built-in hover tips |

Both are the minified UMD builds, committed under `docs/site/vendor/`. If either version is not available when building, use the latest 7.x and 0.6.x and record the version in `LICENSES.txt`.

### 4.5 Browser support and size budget

- Current Chrome, Edge, Firefox and Safari, desktop and phone. No Internet Explorer.
- Each page under 1.5 MB transferred on first load, images included. Chips are lazy-loaded (`loading="lazy"`).
- Layout works from 360 px to 1600 px wide with no horizontal page scroll. Wide tables scroll inside their own container.

### 4.6 Accessibility

- One `<h1>` per page, headings in order, landmarks (`header`, `nav`, `main`, `footer`).
- Colour is never the only carrier of meaning: found and missed carry a word and a symbol; chart series are labelled directly.
- All controls work by keyboard. The slider exposes `aria-valuetext` ("threshold 0.50").
- Every image has `alt` text saying what it shows. Every chart has a text caption stating its finding and a table view.
- Text contrast at least 4.5:1 in both themes.
- `prefers-reduced-motion`: no transitions.

## 5. Data pipeline

`python scripts/build_site_data.py` runs from the repository root on any machine with `requirements.txt` installed. It needs no Earth Engine account and no Gujarat feature rasters: the per-pixel model scores are already in the repository (`data/gujarat_results_v3/scores/*.tif`, values 0 to 100, 255 where a feature was missing). `scripts/make_chips.py` is the one script that must run on the machine holding `data/gujarat/*.tif`.

The script imports from existing modules instead of re-implementing them: `run_models.load_tables` (merged 26-feature table), `diagnostics.GROUPS` and `diagnostics.LABEL` (feature groups and class names), `geoutil` (paths, geometry helpers).

### 5.1 Inputs

| File | Used for |
| --- | --- |
| `data/results_v3/summary.csv`, `fold_metrics.csv`, `selection.json`, `model.json` | Validation tables and charts |
| `data/results_v3/oof_predictions.csv` | Threshold slider; class and region counts. One row per point, with the score from the round in which its region was held out. Columns used: `label`, `class`, `kind`, `state_iso`, `gradient_boosting` |
| `data/features/features.csv`, `data/features_v2/features.csv`, `data/features_v3/main/features.csv`, `data/features_v3/background/features.csv` | Feature explorer; example row; missing-value counts |
| `data/features*/features_meta.json` | Dataset names, dates and cloud limits shown on the Data page |
| `data/samples/samples_summary.txt`, `labels/osm_summary.txt`, `labels/india_screening.csv`, `labels/extra_sites.csv` | Label funnel and counts |
| `labels/gujarat_test_sites.csv`, `.geojson`, `labels/gujarat_boxes.json` | Test list, maps |
| `data/gujarat_results_v3/summary.json`, `site_recall.csv`, `site_ranks.csv`, `areas.csv`, `alarms.csv` | Gujarat results |
| `data/gujarat_results_v3/scores/*.tif` | Threshold curves for Gujarat; flagged-pixel map layers |
| `data/gujarat_results_v3/blind_check.csv` | Hand check (pending, section 12) |
| `data/analysis/diag_*.csv`, `diagnostics.md` | Diagnosis page |
| `data/analysis/alarm_diagnostics.md`, `diag_alarm_*.csv` | Alarm diagnostics (pending) |
| `data/results/`, `data/results_v2/`, `data/gujarat_results/`, `data/gujarat_results_v2/` | "How we got here" table only |
| `data/boundaries/geoBoundaries-IND-ADM1_simplified.geojson` | Locator maps |

### 5.2 Rules for the script

- Deterministic: the same inputs give byte-identical outputs (sorted keys, fixed float rounding, no timestamps except `build.date` and `build.commit` in `site.json`).
- It never recomputes a published number when the published value exists in a result file. It copies it. Where it derives a new number (a threshold curve, a histogram), it first reproduces the matching published number and stops with an error if the two differ by more than the tolerance given below.
- Region of a point: map `state_iso` to its Zonal Council region with `geoutil.ZONAL_COUNCILS`, as `run_models.py` does (import it; do not copy the table).
- Class of a point: `landfill` where `label == 1`, otherwise the `class` column (`near_site`, `random`, `bare_soil`, `quarry`, `ash_pond`).

### 5.3 `site.json`: numbers in the prose

A flat object. Each key holds the raw value, the display string and where it came from:

```json
{
  "guj.sites_found":   {"v": 16,      "s": "16",     "src": "data/gujarat_results_v3/summary.json#sites_found"},
  "guj.share_flagged": {"v": 0.05183, "s": "5.2%",   "src": "data/gujarat_results_v3/summary.json#share_flagged"},
  "check.dumps":       {"v": null,    "s": "pending", "src": "data/gujarat_results_v3/blind_check.csv"}
}
```

In the HTML a number is written as `<span data-k="guj.sites_found">16</span>`. Two commands use these tags:

- `python scripts/build_site_data.py --fill` rewrites the text of every tagged span in `docs/*.html` from `site.json`. A span whose value is `null` gets the text "pending" and the class `pending` (styled with a dotted underline).
- `python scripts/build_site_data.py --check` exits with status 1 and lists every span whose text differs from `site.json`, every key used in HTML but missing from `site.json`, and every key still pending.

Display rules: percentages to one decimal below 10% and whole numbers above; F1, precision and recall to three decimals in tables and two in prose; counts with a thin comma separator (7,801); areas in km² as whole numbers, in hectares to one decimal.

Minimum key set (the builder adds more as pages need them, following the same prefixes):

| Prefix | Keys | Expected value now |
| --- | --- | --- |
| `train.` | `points`, `points_dropped`, `landfill`, `near_site`, `random`, `bare_soil`, `quarry`, `ash_pond`, `places`, `places_osm`, `places_drawn`, `states`, `lookalike_places` | 34,345; 985; 3,853; 24,989; 3,764; 479; 360; 900; 86; 11; 75; 26; 60 |
| `screen.` | `osm_candidates`, `screened`, `kept`, `dropped`, `unsure`, `not_screened` | 843; 107; 13; 93; 1; 736 |
| `val.` | `model`, `f1`, `f1_sd`, `precision`, `recall`, `f1_site`, `f1_pixel`, `rule_f1`, `lr_f1`, `rf_f1` | gradient boosting; 0.762; 0.044; 0.694; 0.865; 0.784; 0.815; 0.415; 0.697; 0.736 |
| `guj.` | `sites`, `sites_found`, `cities`, `boxes`, `km2`, `pixels_scored`, `pixels_flagged`, `share_flagged`, `alarms`, `top50`, `top100`, `top200`, `share_of_state`, `site_px_share_of_flagged` | 17; 16; 13; 14; 12,854; 128,541,406; 6,662,452; 5.2%; 7,801; 5; 8; 9; about 6.6%; computed |
| `guj.rajkot.` | `share`, `max_score`, `rank` | 48.6%; 0.94; 4,388 of 7,796 |
| `guj.snagar.` | `rank`, `score`, `area_ha`, `dist_m` | 4; 0.90; 3.3; 31 |
| `diag.` | `nn_landfill`, `nn_random`, `nn_bare`, `nn_quarry`, `nn_ash`, `auc_lstanom_random`, `auc_lstanom_quarry`, `auc_lstanom_bare`, `fa_bare`, `fa_quarry`, `fa_ash`, `fa_random`, `fa_near`, `shap_thermal`, `shap_premonsoon`, `shap_winter`, `shap_surround` | 73%; 0.9%; 7.9%; 7.5%; 4.8%; 0.942; 0.847; 0.759; 16%; 20%; 12%; 3.2%; 5.0%; 34%; 28%; 17%; 16% |
| `check.` | `checked`, `dumps`, `dump_share`, `ci_low`, `ci_high`, one key per class seen | pending |
| `build.` | `date`, `commit` | set at build time |

`guj.share_of_state` divides `guj.km2` by 196,024 km² (area of Gujarat, cited on the page). `guj.site_px_share_of_flagged` is flagged pixels inside the 17 outlines (sum of `pixels_flagged` in `site_recall.csv`) divided by `guj.pixels_flagged`.

### 5.4 `tables.json`: data behind static charts and tables

One object per chart or table, keyed by the chart ID used in section 9 (`F-R1`, `T-R2`, and so on). Each is an array of row objects with plain column names, taken from the files in 5.1. Three items are computed here because no result file holds them:

- **`F-X3` PCA sample.** Standardise the 26 features over all 34,345 points, fit PCA with two components, and write the coordinates of a stratified sample: every look-alike point (1,739), 1,500 landfill, 1,500 near-site, 1,000 random, drawn with `numpy.random.default_rng(678)`. Check that the explained variance is 36% and 14%, as in `diagnostics.md`.
- **`F-X6` precision against rarity.** For landfill shares p from 1 in 2 to 1 in 100,000 (20 points, log-spaced): precision = p·R / (p·R + (1 − p)·F), with recall R = 0.864 and two false-alarm rates F: 0.032 (random background, validation) and the Gujarat rate (flagged pixels outside the 17 outlines divided by scored pixels outside them). Two curves.
- **`F-R6` site ranks.** From `site_ranks.csv`. Note that Nadiad-01 appears twice (its outline falls in two boxes); keep the better rank and say so in the caption.

### 5.5 `features_hist.json`: feature explorer

Built from the merged table returned by `load_tables` (rows with any missing feature dropped, 34,345 rows).

```json
{
  "classes": ["landfill", "near_site", "random", "bare_soil", "quarry", "ash_pond"],
  "class_labels": {"landfill": "Landfill", "near_site": "Near-site background", "...": "..."},
  "n": {"landfill": 3853, "near_site": 24989, "random": 3764, "bare_soil": 479, "quarry": 360, "ash_pond": 900},
  "groups": ["thermal", "terrain", "pre-monsoon spectral", "winter spectral", "surroundings", "seasonal change"],
  "features": [
    {
      "name": "LST_anom",
      "label": "Surface temperature above surroundings",
      "group": "thermal",
      "unit": "°C",
      "definition": "Landsat surface temperature minus the mean of land within 2 km.",
      "edges": [41 numbers],
      "counts": {"landfill": [40 integers], "near_site": [40], "...": "..."},
      "median": {"landfill": 3.1, "...": "..."},
      "q25": {"...": "..."}, "q75": {"...": "..."},
      "auc": {"near_site": 0.940, "random": 0.942, "bare_soil": 0.759, "quarry": 0.847, "ash_pond": 0.61}
    }
  ]
}
```

- **Bins:** 40 equal-width bins between the 1st and 99th percentile of the feature over all points. Values outside go into the first or last bin, and the caption says so.
- **AUC:** copied from `data/analysis/diag_feature_auc.csv`, not recomputed. The values shown in the JSON example above are illustrative; the file is the source.
- **Label, unit, definition:** from the feature table in section 7.2 (T-D4). The order of `features` is the order of `model.json`.

### 5.6 `threshold.json`: threshold slider

Thresholds t = 0.00, 0.01, …, 1.00 (101 values).

**Validation part**, from `oof_predictions.csv`, column `gradient_boosting`:

```json
"val": {
  "regions": ["Central", "Eastern", "North-Eastern", "Northern", "Southern", "Western"],
  "classes": ["landfill", "near_site", "random", "bare_soil", "quarry", "ash_pond"],
  "n":       {"Central": {"landfill": 697, "...": 0}, "...": {}},
  "flagged": {"Central": {"landfill": [101 integers], "...": []}, "...": {}}
}
```

`flagged[r][c][i]` is the number of points of class c in region r with score ≥ t_i. A point is flagged when its score is greater than or equal to the threshold, as in `run_models.py`.

Check before writing: at t = 0.50 the mean over the six regions of per-region precision, recall and F1 (precision taken as 0 where a region has nothing flagged, as `zero_division=0` does in `run_models.py`) must equal 0.694, 0.865 and 0.762 to three decimals, and the pooled share flagged per class must equal the version 3 row of `diag_flagged_by_class.csv` to three decimals.

**Gujarat part**, from the score rasters:

```json
"guj": {
  "pixels_scored": 128541406,
  "flagged": [101 integers],
  "sites": [{"id": "AHM-01", "city": "Ahmedabad", "pixels": 4735, "flagged": [101 integers]}, "..."],
  "published": {"t": 0.5, "pixels_flagged": 6662452, "sites_found": 16}
}
```

- A raster pixel with stored value s (0 to 100) is flagged at threshold t when s ≥ round(100·t).
- **Overlap between boxes.** Some boxes overlap, and `score_gujarat.py` counts a pixel only in the first box that covers it. Reuse its masking step (the block that begins "Pixels already covered by an earlier box are not counted again") so that the scored total equals 128,541,406. Without it the rasters hold 131,870,793 valid pixels.
- **Site pixels:** rasterise each outline in `labels/gujarat_test_sites.geojson` the same way `score_gujarat.py` does, and check the pixel counts against `site_recall.csv`.
- **Rounding.** Scores were stored rounded to two decimals, so a score of 0.496 is stored as 50 and counts as flagged at t = 0.50 here but not in the published result. The script reports the difference at t = 0.50 between its count and the published 6,662,452. The page shows the published values at exactly 0.50 and states the size of the rounding difference in the caption.
- A site is found at t when at least half of its scored pixels are flagged (the frozen rule).

### 5.7 Maps

No web map is used. Three static products:

1. **`img/india.svg`.** State outlines from the boundary file, simplified to keep the file under 150 KB (Douglas-Peucker in degrees, tolerance about 0.02). States grouped by region with class names `region-northern` and so on, Gujarat with class `gujarat`. One circle per training place (86), at the mean coordinate of its site points. Plate carrée projection with x scaled by cos(22°). No colours in the file: all fills and strokes come from CSS classes, so the map follows the theme. `charts.js` fetches the file and inserts it inline.
2. **`img/gujarat.svg`.** The Gujarat outline, the 14 box frames from `gujarat_boxes.json` with city labels, and one marker per sealed site (class `found` or `missed`), plus Surendranagar with class `unseen`.
3. **`img/boxes/<city>.png`**, one per box. The score raster reduced by a factor of 5 (50 m cells). Each cell's alpha is the share of its 25 pixels that are flagged at 0.50; the colour is fixed at `#eb6834`; unflagged cells are transparent; cells with no data are 12% grey. About 600 px wide. `maps.json` gives, for each box, the image size, the box corners, and the outlines of the sealed sites inside it in image pixel coordinates. The page draws the frame, outlines and labels as an SVG layer over the PNG, so they follow the theme.

### 5.8 Chips (`make_chips.py`, run where the rasters are)

A chip is a small true-colour picture cut from the same Sentinel-2 composite the model reads, so it shows what the model sees at 10 m.

- **Targets:** the 17 sealed sites, Surendranagar, and the top 100 alarms of `data/gujarat_results_v3/alarms.csv`. 118 chips.
- **Window:** 1.5 km square (150 × 150 pixels) centred on the site centroid or alarm centre. For a site wider than 1.2 km (Khajod, Pirana), 3 km square reduced by 2.
- **Rendering:** bands B4, B3, B2 from `data/gujarat/gujarat_<city>.tif`; reflectance clipped to 0.02 to 0.30, scaled to 0 to 1, gamma 0.8; enlarged 3 times with nearest-neighbour so pixels stay visible; saved as 450 px JPEG, quality 85, to `img/chips/<id>.jpg`.
- **Score overlay:** the same window from the score raster, flagged pixels `#eb6834` at 55% alpha, others transparent, saved as `img/chips/<id>_score.png`.
- **`chips.json`:** for each chip: `id`, `kind` (`site`, `unseen`, `alarm`), `city`, `lat`, `lon`, `rank`, `mean_score`, `area_ha`, window size in metres, and for sites the outline in chip pixel coordinates.
- **Blindness:** chip IDs for alarms are the blind IDs (A001 to A100). The script must not be run, and chips must not be looked at, before the hand check of those alarms is finished and committed.
- **Optional, needs Earth Engine:** `--training` fetches chips for six training examples outside Gujarat (two landfills, a quarry, an ash pond, a bare-soil patch, an ordinary town block) with `ee.Image.getThumbURL`, using the same composite settings. Used on the Data page. Drop if time is short.

Sentinel-2 imagery must carry the credit "Contains modified Copernicus Sentinel data 2023 to 2024" under each gallery.

## 6. Design system

### 6.1 Layout

- **Header** (sticky, 56 px): project short title at left ("Landfill detection, Gujarat"); the six page links; theme button at right. The current page link is marked with `aria-current="page"` and an underline. Below 760 px the links collapse into a menu button.
- **Page grid:** main text column 680 px; margin column 260 px to its right with a 40 px gap; both centred as a block. Figures and tables may span both columns (class `wide`, 980 px).
- **"On this page":** a short list of the page's sections under the page title, as plain links. Not sticky.
- **Footer:** previous and next page links; then one row of links: repository, paper (PDF), grader's manual (PDF), glossary; then "Built from commit `<build.commit>` on `<build.date>`".
- **Below 1100 px** the margin column disappears and each margin note becomes a boxed block directly after its paragraph.

### 6.2 Type

- Body and headings: `Charter, "Bitstream Charter", "Sitka Text", Cambria, Georgia, serif`. Body 18 px, line height 1.6.
- Navigation, tables, captions, margin notes, charts, controls: `system-ui, -apple-system, "Segoe UI", sans-serif`. Margin notes 14 px, captions 15 px.
- Code and file names: `ui-monospace, Consolas, monospace`, 0.9 em.
- Numbers in tables use `font-variant-numeric: tabular-nums`.

### 6.3 Colour tokens

Defined as CSS custom properties on `:root`. Dark values are set twice: under `@media (prefers-color-scheme: dark)` for `:root:not([data-theme="light"])`, and under `:root[data-theme="dark"]`.

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--page` | `#f9f9f7` | `#0d0d0d` | Page background |
| `--surface` | `#fcfcfb` | `#1a1a19` | Cards, charts, tables |
| `--ink` | `#0b0b0b` | `#f0efec` | Text |
| `--ink-2` | `#52514e` | `#c3c2b7` | Captions, notes |
| `--muted` | `#898781` | `#898781` | Axis labels |
| `--grid` | `#e1e0d9` | `#2c2c2a` | Gridlines, table rules |
| `--axis` | `#c3c2b7` | `#383835` | Axis lines, borders |
| `--series-1` | `#2a78d6` | `#3987e5` | Landfill; first series; links |
| `--series-2` | `#eb6834` | `#d95926` | Comparison class; flagged pixels |
| `--series-3` | `#1baf7a` | `#199e70` | Third series |
| `--neutral` | `#898781` | `#898781` | De-emphasised series |
| `--good` | `#0ca30c` | `#0ca30c` | "Found" (always with a tick and the word) |
| `--critical` | `#d03b3b` | `#d03b3b` | "Missed" (always with a cross and the word) |
| `--seq-lo`, `--seq-hi` | `#cde2fb`, `#0d366b` | `#184f95`, `#cde2fb` | Ends of the one-hue scale in the AUC table |

Colour rules for charts:

- Landfill is always `--series-1`. A background class shown against it is always `--series-2`. Precision, recall and F1 are series 1, 2 and 3 in that order, labelled on the lines.
- No chart uses more than three colours. Where six classes must be compared, they are six labelled rows or panels, not six colours.
- Text never takes a series colour.

### 6.4 Theme switch

- `theme.js` runs in `<head>` before first paint: read `localStorage.theme`; if it is `light` or `dark`, set `data-theme` on `<html>`. Otherwise leave it unset so the operating-system setting applies.
- The header button toggles between light and dark, writes `localStorage.theme`, and dispatches a `themechange` event on `document`.
- Charts read their colours from the CSS tokens with `getComputedStyle` when they draw, and redraw on `themechange`. (Do not write `var(--x)` into SVG attributes.)
- Satellite chips are not altered in dark mode. They get a 1 px `--axis` border.

### 6.5 Components

| Component | Markup | Behaviour |
| --- | --- | --- |
| Margin note | `<aside class="note"><b>NDVI.</b> …</aside>` placed directly after the paragraph that first uses the term | Floats into the margin column; one to two sentences; at most three per screen of text |
| Term | `<a class="term" href="reproduce.html#g-ndvi">NDVI</a>` on first use per page | Dotted underline; goes to the glossary |
| Stat tile | `<div class="stat"><span class="v" data-k="…">16 of 17</span><span class="l">known sites found</span></div>` | Row of up to four; value 40 px sans |
| Figure | `<figure id="F-R1"><div class="chart"></div><figcaption><b>Figure R1.</b> finding. How to read it.</figcaption><details class="tableview"><summary>Show the numbers</summary><table>…</table></details></figure>` | Caption states the finding first |
| Table | `<figure id="T-R1" class="table">` with `<caption>` above | Sticky first column on narrow screens |
| Callout | `<div class="callout">` | For the disclosure and for "what this does not show" |
| Why box | `<div class="why"><b>Why:</b> …</div>` | Attached to each preprocessing and evaluation choice |
| Chip card | `<figure class="chip"><img …><svg class="outline">…</svg><figcaption>` | Outline drawn in SVG over the image; optional score overlay |
| Pending | `.pending` | Dotted underline and a title attribute "result not yet in" |

## 7. Page specifications

For each page: its purpose, then each section with the content it must hold, its numbers (as `site.json` keys), its figures and tables (IDs from section 9), and its margin notes. Wording is the builder's, within the rules of section 10. Target lengths are for running text and exclude tables and captions.

### 7.1 Overview (`index.html`), about 500 words

Purpose: a grader who reads only this page knows the question, the method in outline, the result and its weakness, and where everything else is.

**§1 The question.**
- One paragraph: municipal dumps in India are large, poorly mapped and visible from space. Question: can a model trained on Indian dumpsites outside Gujarat find Gujarat's dumpsites from free satellite data, and when it is wrong, why?
- One sentence on what one row is: one 10 m pixel described by 26 numbers from Sentinel-2, Landsat and SRTM, labelled landfill or not.
- Margin notes: *Sentinel-2*; *why Gujarat is held out* (a model is only useful in places it was not trained on, so the whole state is kept out of training).

**§2 The answer in four numbers.** Stat tiles:
1. `guj.sites_found` of `guj.sites` known sites found.
2. `guj.share_flagged` of the scored land flagged, as `guj.alarms` separate alarm patches.
3. `check.dumps` of the top 100 alarms are dumps (pending).
4. Held-out-region F1 `val.f1`.

Then two sentences giving the reading: the model recognises landfills it is shown, but it flags far more land than can be landfill, so as a search tool its alarms are mostly wrong. The rest of the site shows what it confuses with landfill and why.

**§3 How the study was run**, as a five-step numbered list, each step linking to its page: label sites outside Gujarat by hand → read 26 features per pixel → compare nine models with whole regions held out → freeze the chosen model under a Git tag → score Gujarat and check the top alarms by eye without seeing scores.
- Figure F-O1: Gujarat locator map with the 14 boxes and the sites.

**§4 What to know before reading** (callout, the agreed disclosure; text in section 10.3).

**§5 Where each required item is.** Table T-O1 (the table in section 3 of this plan, with links).

**§6 Project facts.** Course, track, author line (section 16), links to repository, paper and manuals.

### 7.2 Data (`data.html`), about 900 words

**§1 What one row is.**
- A training row is one 10 m pixel at a sampled point: an ID, a label (1 landfill, 0 not), a class (landfill, near-site background, random background, bare soil, quarry, ash pond), the place and state it belongs to, and 26 feature values.
- A Gujarat row is one 10 m pixel of a scored box, with the same 26 features and no label. Results for Gujarat are reported per site and per alarm patch, not per pixel, and the page says why (a site is what a field officer visits).
- Table T-D1: one real landfill row shown vertically (feature, value, unit). Use the first landfill point in the merged table by `point_id`.

**§2 Sources.** Table T-D2:

| Source | Earth Engine ID | Native resolution | Dates | What is taken |
| --- | --- | --- | --- | --- |
| Sentinel-2 surface reflectance | `COPERNICUS/S2_SR_HARMONIZED` | 10 m (B2, B3, B4, B8), 20 m (B11) | 1 Mar to 31 May 2024; 15 Nov 2023 to 14 Feb 2024 | Median of scenes under 10% cloud |
| Landsat 8 and 9 surface temperature | `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2` | about 100 m | 1 Mar to 31 May 2024 | Median of scenes under 30% cloud |
| SRTM elevation | `USGS/SRTMGL1_003` | 30 m | 2000 | Elevation, slope |
| JRC Global Surface Water | `JRC/GSW1_4/GlobalSurfaceWater` | 30 m | 1984 to 2021 | Water mask for the temperature background |
| OpenStreetMap `landuse=landfill` | Overpass export, 3 Nov 2026 | outlines | | Candidate sites |
| Google Earth imagery | viewed by hand | under 1 m | nearest to Mar to May 2024 | Labelling and the hand check only; never a model input |
| geoBoundaries India ADM1 | file in `data/boundaries/` | | | Assigning sites to states |

All values in this table are read from `features_meta.json` at build time where they exist there.
- Margin notes: *surface reflectance*; *median composite* (the middle value of all cloud-free observations in a period, which removes clouds and one-off events).

**§3 How the labels were made.**
- OpenStreetMap candidates were screened by eye in Google Earth: `screen.osm_candidates` candidates, `screen.screened` screened in the time available, `screen.kept` kept, `screen.dropped` dropped. Of the dropped, `train.lookalike_places` were kept as look-alike examples (32 ash ponds, 16 bare-soil sites, 12 quarries).
- 82 further outlines were drawn by hand; after merging neighbours and removing sites under 1 ha, `train.places` places remain in `train.states` states and territories.
- The rule for a site: active dumping visible in imagery closest to March to May 2024, at least 1 ha of visible waste.
- Figure F-D1: label funnel. Figure F-D2: India map of the 86 places by region, Gujarat marked as held out.
- Why box: why OSM alone was not used (12% of screened OSM outlines were usable).
- Margin note: *look-alike* (a place that is not a dump but resembles one from above; used as a hard negative example).

**§4 Size.**
- Table T-D3: points by class and region (6 × 6, with totals), from `threshold.json` `val.n`.
- Sentence on how points are drawn: up to 50 per landfill place, up to 30 per look-alike place, as many random points as landfill points, and 25,800 background points in the 15 km boxes around the training landfills.
- Table T-D4: the Gujarat test list (17 rows: ID, city, name, area in ha), with the note that the list was committed (`8711855`) before any model was run, and that nothing from Gujarat is in training.

**§5 The 26 variables.** Table T-D5, grouped by the six groups, columns: name, what it measures, source, formula or processing:

| Group | Features |
| --- | --- |
| Pre-monsoon spectral (8) | `B2` blue, `B3` green, `B4` red, `B8` near infrared, `B11` short-wave infrared, `NDVI` = (B8 − B4)/(B8 + B4), `NDBI` = (B11 − B8)/(B11 + B8), `BSI` = ((B11 + B4) − (B8 + B2))/((B11 + B4) + (B8 + B2)) |
| Thermal (2) | `LST` surface temperature in °C; `LST_anom` = LST minus the mean LST of land within 2 km |
| Terrain (2) | `elev` in m; `slope` in degrees |
| Winter spectral (5) | `B2_w`, `B11_w`, `NDVI_w`, `NDBI_w`, `BSI_w`: the same quantities from the winter composite |
| Surroundings (7) | `NDVI_ctx`, `NDBI_ctx`, `BSI_ctx`: mean within 150 m; `NDVI_sd`, `B11_sd`: standard deviation within 50 m; `NDVI_rel`, `NDBI_rel`: pixel minus its 150 m mean |
| Seasonal change (2) | `dNDVI`, `dBSI`: winter minus pre-monsoon |

Then the **feature explorer** (interaction I1, section 8.1), introduced by one paragraph: "Pick a variable and compare landfill pixels with each kind of non-landfill pixel. If two shapes overlap, that variable cannot tell them apart."
- Margin notes: *NDVI* (greenness; high on crops and trees, near zero on waste and bare ground); *NDBI*; *BSI*; *LST*; *AUC as used here* (the chance that a random landfill pixel has a higher value than a random pixel of the other class; 0.5 means no information).

**§6 Quality problems.** A numbered list, each with its number and its consequence:
1. Labels come from one person reading imagery; no site was visited. Imagery dates do not always match the feature dates.
2. Few places: 86, unevenly spread (15 in Maharashtra; 13 states and territories have two or fewer). This is why validation folds are regions, not states.
3. OpenStreetMap outlines are unreliable (`screen.kept` kept of `screen.screened` screened).
4. Look-alike examples cover three classes only. Blue metal roofs, salt pans and construction sites, which turned out to matter in Gujarat, have no examples.
5. The thermal band is about 100 m, resampled to 10 m, so small sites are blurred with their surroundings; sites under 1 ha were excluded for this reason.
6. Missing values: `train.points_dropped` of 35,330 points dropped (snow in Himalayan states for spectral bands; winter composite gaps). State counts per feature from the `n_missing_by_band` entries of the four `features_meta.json` files.
7. The test list is small (`guj.sites` sites in `guj.cities` cities), was compiled from the author's own knowledge and public lists, and favours large municipal sites.
8. Only about `guj.share_of_state` of Gujarat was scored: boxes reaching 15 km beyond the known sites.

**§7 What these places look like** (only if the optional training chips exist): six chips with one-line captions.

### 7.3 Method (`method.html`), about 1,000 words

**§1 Preprocessing choices.** Table T-M1, three columns (choice, what was done, why), followed by short paragraphs only where a row needs more than a line:

| Choice | What was done | Why |
| --- | --- | --- |
| Season | Pre-monsoon, March to May 2024 | Dry, least cloud, vegetation at its minimum so bare and waste surfaces are exposed |
| Second season | Winter, mid-November 2023 to mid-February 2024 | Fields are green in winter and bare before the monsoon; a dump is the same in both |
| Compositing | Per-pixel median of cloud-masked scenes | Removes cloud, shadow and one-day events |
| Cloud handling | Scenes under 10% cloud (Sentinel-2) or 30% (Landsat); scene-classification classes 1, 3, 8, 9, 10, 11 masked | Fewer thermal scenes exist, so the Landsat limit is looser |
| Temperature anomaly | LST minus the mean of land within 2 km, permanent water excluded | Removes regional climate, so 40 °C in Rajasthan and in Kerala are comparable; excluding water stops coastal sites looking hot |
| Surroundings | 150 m means and 50 m standard deviations | A pixel alone cannot tell a dump from a roof; its neighbourhood can help |
| Resolution | Everything sampled at 10 m | The finest input; coarser inputs are resampled, not sharpened |
| Points per place | A cap of 50 per landfill, 30 per look-alike | One 300 ha site must not outweigh thirty small ones |
| Edge inset | Points at least 15 m inside the outline and 15 m apart | Edge pixels mix waste with surroundings; no pixel is sampled twice |
| Background | Random points at least 500 m from any mapped site; near-site points in the 15 km boxes | Random points teach "ordinary India"; near-site points teach "the kind of land around a city dump", which is what Gujarat boxes contain |
| Missing values | Rows with any missing feature dropped | 2.8% of points; no imputation to explain |
| Scaling | Standardised inside the logistic-regression pipeline only | Trees do not need it |
| Class weights | Balanced | Landfill is 11% of points |

**§2 Baselines and models.** Table T-M2: nine rows (name, kind, settings):
flag nothing (reference); published threshold rule (NDBI > 0.028, NDVI < 0.15, LST > 37.0 °C); the same rule with thresholds refitted on training data; logistic regression; decision tree; bagged trees (200); random forest (500); AdaBoost (200 stumps); gradient boosting (100 trees, depth 3, learning rate 0.1).
- State plainly: scikit-learn defaults, no tuning, threshold 0.5, random seed 678. Why box: with 86 places, tuning would fit the validation folds; fixed defaults keep the comparison honest.
- Margin notes: *gradient boosting* (one line reminder); *why a threshold rule is a baseline* (it is the method of the paper that motivated the project).

**§3 Three ways to split the data.** Figure F-M1 (schematic) and one paragraph each:
- Random pixel: pixels from the same landfill fall on both sides. Optimistic.
- Held-out site: whole places are held out, but neighbours in the same state remain.
- Held-out region (headline): all places in one of six Zonal Council regions are held out in turn. Closest to the real task of scoring a state never seen.
- Why regions and not states: the plan was leave-one-state-out with at least 10 places per state; only Maharashtra qualified, so the pre-set fallback to regions applied.
- Margin note: *leakage* (when test rows are near-copies of training rows, the score measures memory, not skill).

**§4 Metrics and the selection rule.** Precision, recall and F1 for the landfill class, per fold, reported as mean and standard deviation over the six regions. Selection: the highest mean F1 on the held-out-region split. Also reported: the share of each background class flagged.
- Margin note: *precision and recall in this project* (recall: of real landfill pixels, the share flagged; precision: of flagged pixels, the share that are landfill).

**§5 The freeze.** Figure F-M2 (timeline). Text: the test list was committed first; the model, threshold and scoring rules were committed and tagged `freeze-v3` before Gujarat was scored; `score_gujarat.py` refuses to run unless the model file matches a freeze tag. Link to `docs/freeze_v3.md`.
- Callout repeating the disclosure in one sentence, with a link to "How we got here".

**§6 Scoring Gujarat.** The rules, as a definition list:
- *Scored area:* 14 boxes reaching 15 km beyond the known sites; `guj.km2` km².
- *Flagged pixel:* score ≥ 0.5.
- *Site found:* at least half of the outline's pixels are flagged.
- *Alarm patch:* touching flagged pixels totalling at least 1 ha.
- *Ranking:* by the mean score of the patch.
- *Margin note:* "score" is the model's output between 0 and 1. It is not a probability that the place is a dump (section 10).

**§7 The hand check.** The top 100 alarm patches were given random IDs, shown without scores or ranks, and judged one by one in Google Earth as dump or not, with a note of what was seen. Why 100: enough to estimate a proportion to within about ±10 points. State who did it (the author) and that this is the weakest link in the evaluation.

### 7.4 Results (`results.html`), about 900 words

**§1 Validation outside Gujarat.**
- Table T-R1: nine models, precision, recall and F1 as mean ± SD on the held-out-region split, selected model in bold.
- Figure F-R1: F1 of every model under the three splits.
- Figure F-R2: gradient boosting per region (precision and recall).
- Text: gradient boosting is best at F1 `val.f1` (precision `val.precision`, recall `val.recall`). The published rule reaches `val.rule_f1`. The random-pixel split would have reported `val.f1_pixel` for the same model, and 0.907 for the random forest that scores 0.736 when regions are held out: the split changes the ranking of models, not only the level. Weakest region: Western (F1 0.679), which is the region Gujarat itself belongs to.

**§2 The threshold slider** (interaction I2, section 8.2), introduced by: "The threshold was fixed at 0.5 before Gujarat was scored. Move it to see what any other choice would have traded."

**§3 Gujarat: the known sites.**
- Stat sentence: `guj.sites_found` of `guj.sites` found.
- Table T-R2: 17 rows (site, city, area, share of outline flagged, found or missed, rank of its patch among all patches).
- Figure F-R3: share of each outline flagged, with the 50% rule marked.
- The miss: Rajkot, `guj.rajkot.share` flagged, just under the rule. Link to Diagnosis §7.
- Callout "One site the model had never been told about": Surendranagar, in neither the training data nor the test list, is alarm rank `guj.snagar.rank` of `guj.alarms`. One example, not a rate. Chip with outline.

**§4 Gujarat: everything else that was flagged.**
- `guj.share_flagged` of `guj.km2` km² flagged; `guj.alarms` patches of 1 ha or more. The 17 known sites cover `guj.site_px_share_of_flagged` of the flagged land.
- Figure F-R4: share flagged per box (14 bars, 0.6% Dwarka to 16% Bhavnagar).
- Figure F-R5: small multiples of the 14 boxes, flagged pixels in orange, site outlines drawn on.
- Ranking: with the known sites left in the list, `guj.top50` stand in the top 50 patches, `guj.top100` in the top 100, `guj.top200` in the top 200. Figure F-R6: rank of each known site's patch.
- Margin note: *why rank matters* (nobody can visit 7,801 places; the question is whether real dumps come first).

**§5 The hand check of the top 100 alarms** (pending).
- Stat: `check.dumps` of `check.checked` are dumps, with a 95% interval (Wilson; `check.ci_low` to `check.ci_high`).
- Table T-R3 and Figure F-R7: what the alarms were, by class seen.
- One sentence comparing with the only field-verified 10 m study (Kruse et al. 2023: 53% of candidates confirmed, with a much larger system), after the reference is checked.

**§6 New cities** (optional; include only if the test was run). Sites outlined and committed before scoring in cities outside the original boxes: how many found, their ranks. Same table layout as T-R2. If absent, the section, its nav entry and its keys are removed and nothing else changes.

**§7 Bottom line.** Three sentences: high recall on known sites; flagged area far larger than any plausible landfill area; what the hand check says about the top of the list. Link to Diagnosis.

### 7.5 Diagnosis (`diagnosis.html`), about 1,300 words

Organised as questions. Each section opens with the question, gives the evidence, and ends with a one-sentence answer in bold.

**§1 What did the model flag that is not a dump?** Chip gallery (section 8.3) grouped by the class recorded in the hand check, largest class first, up to six chips per class, each with its rank and score, with the "show flagged pixels" switch. Pending the hand check. Until then the gallery shows the 17 known sites and Surendranagar only.

**§2 Can landfill pixels be told apart at all?**
- Figure F-X1: single-feature AUC, 26 features by 5 background classes. Finding: `LST_anom` is the best single feature against ordinary land (`diag.auc_lstanom_random`) and weaker against quarries (`diag.auc_lstanom_quarry`) and bare soil (`diag.auc_lstanom_bare`). Each cell links to the feature explorer for that feature.
- Figure F-X2: share of points whose 15 nearest neighbours are mostly landfill, by class. `diag.nn_landfill` of landfill points, about 1% of ordinary land, 5 to 8% of look-alikes.
- Figure F-X3: the first two principal components (50% of variance).
- **Answer:** mostly yes against ordinary land; a quarter of landfill pixels sit among non-landfill pixels, and 5 to 8% of look-alike pixels sit among landfill pixels.

**§3 Which look-alikes fool the model?** Figure F-X4: share of each class flagged when its region is held out. Landfill 86% (recall), quarry `diag.fa_quarry`, bare soil `diag.fa_bare`, ash pond `diag.fa_ash`, near-site `diag.fa_near`, random `diag.fa_random`. **Answer:** look-alikes are flagged four to six times as often as ordinary land.

**§4 What does the model rely on?** Figure F-X5: share of mean absolute SHAP value by feature group (thermal `diag.shap_thermal`, pre-monsoon spectral `diag.shap_premonsoon`, winter `diag.shap_winter`, surroundings `diag.shap_surround`); the five largest single features listed (`LST_anom` 33%, `B2` 8%, `B2_w` 8%, `NDBI` 7%, `NDVI_w` 5%). **Answer:** one third of the decision is "hotter than its surroundings", and anything hot and bare shares that property.
- Margin note: *SHAP* (a way of dividing one prediction among the features that produced it).

**§5 Why were the Gujarat alarms flagged?** (pending `alarm_diagnostics.py`). Table T-X1: for known sites and for alarms by verdict: median novelty percentile, share beyond the 99th percentile of training, what their nearest training points are, and mean SHAP by group. The question it settles: are false alarms unlike anything in training (extrapolation), or like training landfills (true overlap)?

**§6 Why does a good F1 give thousands of alarms?** Figure F-X6: precision against how rare landfill is. Text with one worked example: at the validation mix (11% landfill) precision is 0.69; if 1 pixel in 1,000 is landfill and the model keeps the same recall and false-alarm rate, precision falls to about 3%. The 17 known sites are 0.02% of the scored pixels.

**§7 The missed site.** Rajkot: chip, flagged-pixel overlay, and two sentences on what part of the outline was not flagged. Any causal claim (for example, a capped or vegetated section) is made only if the chip shows it.

**§8 How this compares with published work.** One paragraph, after references are checked: the study that motivated the project reports sites meeting thresholds but did not verify them; the one field-verified Sentinel-2 system confirmed about half of its candidates using two networks, two dates and retraining on its own false alarms; work at 20 to 30 cm resolution reports F1 near 0.9 that falls when moved to a new area.

**§9 Limitations.** List:
1. This is the third model scored on the same 17 sites (see §10).
2. Labels and the hand check are one person's reading of imagery, with no field visit.
3. The test list favours large, known municipal sites; small informal dumps are untested.
4. About `guj.share_of_state` of the state was scored; unscored land is not "clean".
5. One year of imagery (2024); sites change.
6. 86 training places and three look-alike classes.
7. No tuning and no deep model: a patch-based network might do better; this project cannot say.
8. Features describe pixels and their near surroundings, not the shape or setting of a whole site.

**§10 How we got here.** One paragraph: the first model (logistic regression, 12 features) found 16 of 17 sites, and none of 50 checked alarms was a dump (33 were blue roofs); the second added background points from around training landfills, flagged less land but ranked large bare patches first; the third added a winter composite and surroundings. Each was frozen under its own tag before scoring. Then Table T-X2:

| | Version 1 | Version 2 | Version 3 |
| --- | --- | --- | --- |
| What changed | 12 features | More background near training sites | Winter season and surroundings: 26 features |
| Model selected | Logistic regression | Random forest | Gradient boosting |
| Held-out-region F1 | 0.848 | 0.739 | 0.762 |
| Gujarat sites found, of 17 | 16 | 15 | 16 |
| Scored land flagged | 5.5% | 1.8% | 5.3% |
| Known sites in the top 100 patches | not recorded | 4 | 8 |
| Hand check of top alarms | 0 of 50 dumps | failed by eye | `check.dumps` of `check.checked` |
| Tag | `freeze-v1` | `freeze-v2` | `freeze-v3` |

Note under the table: F1 is not comparable between version 1 and the others (versions 2 and 3 are tested against many more background points). The 5.3% for version 3 is over the same 13 city boxes as the other versions; 5.2% elsewhere on the site includes the Surendranagar box.

### 7.6 Reproduce (`reproduce.html`), about 600 words plus the glossary

**§1 What is in the repository.** Table: folder, what it holds (`labels/`, `scripts/`, `data/`, `docs/`, `figures/`, `paper/`).

**§2 Setup.** The three PowerShell commands from the README; Python 3.13; `requirements.txt`.

**§3 Run order.** The nine-row table from the README, plus a column for time taken, plus the two site commands (`build_site_data.py`, `make_chips.py`). Mark which steps need an Earth Engine account.

**§4 Data access.**
- In the repository: labels, points, all feature tables, all results, per-pixel Gujarat scores.
- Not in the repository: the Gujarat feature rasters (several gigabytes). They are rebuilt with step 7 from free public data; a free Earth Engine account is needed. State the licence of each source.
- A quick check that needs no account: steps 1, 2, 5, 6 and 9 reproduce the committed files; link to the grader's manual.

**§5 Verifying the freeze.** How to see that the tag precedes the scoring: `git log freeze-v3 -1`, the commit that added `data/gujarat_results_v3/`, and the test-list commit `8711855`.

**§6 AI-use disclosure.** Section 10.4 gives what it must cover. The same text goes in the README and the paper.

**§7 References.** Numbered list; every reference cited on any page. Each entry checked against the publisher's page before publishing (section 16).

**§8 Licences and credits.** Sentinel-2 (Copernicus), Landsat (USGS), SRTM (NASA/USGS), JRC Global Surface Water, OpenStreetMap contributors (ODbL), geoBoundaries (CC BY), D3 and Observable Plot (ISC).

**§9 Glossary** (`#glossary`). Section 11.

## 8. Interaction specifications

### 8.1 I1: feature explorer (Data §5)

**Purpose.** Let the reader see, for any of the 26 variables, how landfill pixels are distributed against each kind of non-landfill pixel, and so understand directly why some classes are confused.

**Data.** `features_hist.json` (5.5).

**Layout** (class `wide`):

```
[ Variable: ▼ LST_anom ]  [◀ previous] [next ▶]         group: thermal
Surface temperature above surroundings (°C). Landsat surface temperature minus
the mean of land within 2 km.

  Landfill vs near-site background      AUC 0.94   ▂▃▅▇▅▃▂   (panel)
  Landfill vs random background         AUC 0.94             (panel)
  Landfill vs bare soil                 AUC 0.76             (panel)
  Landfill vs quarry                    AUC 0.85             (panel)
  Landfill vs ash pond                  AUC …                (panel)

  Reading: "A landfill pixel is higher than a quarry pixel 85 times in 100."
  ▸ Show the numbers
```

**Controls.**
- A `<select>` of the 26 features, grouped with `<optgroup>` by feature group, each option showing name and plain label ("LST_anom: temperature above surroundings").
- Previous and next buttons step through the list. Left and right arrow keys do the same when the control has focus.
- The chosen feature is written to the URL as `#f=LST_anom`, and read from it on load, so the AUC table on the Diagnosis page can link to a feature.
- Default: `LST_anom`.

**Panels.** Five small charts stacked vertically, one per background class, each 120 px high, sharing the x axis (drawn once, under the last panel) and sharing the y scale.
- y: share of the class's points in each bin (count divided by class total), so classes of different size are comparable.
- Background class: filled columns in `--series-2`, 70% opacity, 1 px gap.
- Landfill: a 2 px step line in `--series-1`, drawn on top, identical in all five panels.
- Medians: a small tick under the axis for each of the two classes.
- Panel title at left: "Landfill vs quarry"; at right: "AUC 0.85" in `--ink`.
- A legend above the first panel: line swatch "Landfill", column swatch "The other class".
- Panel order is fixed (near-site, random, bare soil, quarry, ash pond) and does not change with the feature.

**Hover and focus.** Moving over any panel shows a vertical guide across all five and a tooltip: the bin range with unit, then "Landfill 12.3% of points", "Quarry 4.1% of points". On touch, tap sets the guide.

**Reading line.** Generated from the AUC of the panel last hovered, or of the panel with the AUC closest to 0.5 if none: for AUC a ≥ 0.5, "A landfill pixel is higher than a {class} pixel {round(100a)} times in 100"; below 0.5, "lower … {round(100(1 − a))} times in 100". When |a − 0.5| < 0.1 append "This variable hardly separates them."

**Table view.** Per class: number of points, 25th percentile, median, 75th percentile, AUC against landfill.

**Caption.** Says that values beyond the 1st and 99th percentile are collected in the end columns, and gives the number of points per class.

**States.** Loading (grey placeholder of final height, so the page does not jump); load failure (message and the table view remains); no JavaScript (a static sentence and a link to `diag_feature_auc.csv` on GitHub).

**Checks.** With `LST_anom` selected the five AUC values equal those in `diag_feature_auc.csv`; the landfill line is identical across panels; column shares in each panel sum to 1; the URL hash round-trips.

### 8.2 I2: threshold slider (Results §2)

**Purpose.** Show what the fixed threshold of 0.5 trades: recall on real landfills against false alarms, both in validation and in Gujarat. It also shows that no threshold removes the problem.

**Data.** `threshold.json` (5.6).

**Layout** (class `wide`):

```
Threshold  0.05 ────────●──────── 0.95     0.50   [Reset to 0.50]

Validation, regions held out            Gujarat, 12,854 km² scored
 Precision  Recall   F1                  Sites found   Land flagged
   0.69      0.87    0.76                  16 of 17     5.2%  (666 km²)

[ line chart: precision, recall, F1      [ meter list: share of each class
  against threshold; marker at the         flagged at this threshold:
  chosen value; dashed line at 0.50 ]      Landfill (recall) ████████ 86%
                                           Quarry            ██       20%
                                           Bare soil         ██       16%
                                           Ash pond          █        12%
                                           Near-site         ▌         5%
                                           Random            ▌         3% ]

At 0.50: of every 100 validation points flagged, 69 are landfill.
In Gujarat the 17 known sites make up 0.4% of the flagged land.
```

**Control.** `<input type="range" min="0.05" max="0.95" step="0.01" value="0.50">` with a visible label, a numeric readout, and a reset button. Arrow keys move by 0.01, Page Up and Page Down by 0.05. All outputs update on `input`, with no animation.

**Computed on each change**, with i the index of the threshold:
- Per region r: TP = flagged[r][landfill][i]; FP = sum of flagged[r][c][i] over the five background classes; FN = n[r][landfill] − TP. Precision = TP/(TP + FP), or 0 if nothing is flagged; recall = TP/(TP + FN); F1 = 2PR/(P + R), or 0.
- Tiles show the **mean over the six regions**, to match Table T-R1.
- Meter list: for each class, the sum over regions of flagged divided by the sum of n.
- Gujarat: sites found = number of sites with flagged/pixels ≥ 0.5; land flagged = guj.flagged[i]/pixels_scored, and the same in km² (pixels × 100 m² / 10⁶).
- At exactly 0.50 the Gujarat tiles show the published values.
- Sentence 1: round(100 × pooled precision). Sentence 2: flagged pixels inside the 17 outlines divided by all flagged pixels.

**Line chart.** x: threshold 0 to 1; y: 0 to 1; three lines (precision, recall, F1) in series 1, 2, 3, labelled at their right ends; a vertical rule at the chosen threshold with three dots on the lines; a dashed vertical rule at 0.50 labelled "frozen". The curves are the region means, precomputed once on load for all 101 thresholds.

**Meter list.** Six rows with fixed order and one hue (`--series-2`), except the landfill row in `--series-1` labelled "Landfill (recall)". Values printed at the right of each bar.

**Caveat under the widget** (always visible): "The threshold was fixed at 0.5 before Gujarat was scored. Other values are shown to explain the trade-off. They are not results the project claims." Plus the rounding note from 5.6.

**Checks.** At 0.50: tiles show 0.69, 0.87, 0.76 (0.694, 0.865, 0.762 in the table view), 16 of 17, 5.2%; meter list shows 86, 20, 16, 12, 5, 3. Recall and land flagged never increase as the threshold rises. At 0.30 all 17 sites are found.

### 8.3 Chip gallery and score overlay (supporting; not counted as a required interaction)

- A grid of chip cards, three per row on desktop, one on a phone.
- Each card: the chip, the site outline (known sites) drawn in SVG, and a caption: name or blind ID, city, rank, mean score, area, and for alarms the verdict and what was seen.
- One checkbox above each gallery: "Show the pixels the model flagged". It toggles the `_score.png` layer on all chips of that gallery.
- Clicking a chip opens it at 900 px in a `<dialog>` with a link "Open this place in Google Maps" (`https://www.google.com/maps/@<lat>,<lon>,600m/data=!3m1!1e3`). No Google imagery is copied into the site.

## 9. Chart catalogue

All charts are drawn by `charts.js` with Observable Plot into the `.chart` element of the figure with the given ID, from `tables.json`. Common rules: gridlines in `--grid`, axis text in `--muted`, 2 px lines, bar ends rounded 3 px at the value end, a hover tip on every mark, no chart title inside the SVG (the caption carries it), width from the container, redraw on resize and on `themechange`.

| ID | Page | Form | Encoding | Source |
| --- | --- | --- | --- | --- |
| F-O1 | Overview | Inline SVG map | Gujarat outline; 14 box frames with labels; site markers: found (tick), missed (cross), unseen (ring) | `img/gujarat.svg` |
| F-D1 | Data | Horizontal bars, one hue | Rows: OSM candidates 843 → screened 107 → kept 13 → used 11; hand-drawn 82 → places 75; total 86. Counts printed | `samples_summary.txt`, `osm_summary.txt` |
| F-D2 | Data | Inline SVG map | States tinted by region (six tints of the sequential hue with the region name printed on the map), Gujarat hatched and labelled "held out", 86 dots | `img/india.svg` |
| F-M1 | Method | Hand-made inline SVG | Three rows of 12 blocks. Row 1: blocks randomly marked train or test. Row 2: blocks grouped in places, whole places marked. Row 3: places grouped in regions, one region marked | none |
| F-M2 | Method | Hand-made inline SVG timeline | Test list sealed (11 Nov, `8711855`) → features → nine models compared → `freeze-v3` (15 Nov) → Gujarat scored → hand check | `git log` dates |
| F-R1 | Results | Dot plot | y: nine models, ordered by held-out-region F1; x: F1 0 to 1; three dots per model (random pixel hollow, held-out site half tone, held-out region solid, with ±1 SD bar); selected model row emphasised | `summary.csv` |
| F-R2 | Results | Dumbbell | y: six regions; x: 0 to 1; precision and recall joined by a line; F1 printed at right | `fold_metrics.csv` |
| F-R3 | Results | Horizontal bars | y: 17 sites ordered by share; x: share of outline flagged; rule at 50%; missed site in `--critical` with the word "missed" | `site_recall.csv` |
| F-R4 | Results | Horizontal bars, one hue | y: 14 boxes ordered; x: share flagged; values printed | `areas.csv` |
| F-R5 | Results | Small multiples of images | 14 box PNGs with SVG outlines, 4 per row, city name and share flagged under each | `img/boxes/`, `maps.json` |
| F-R6 | Results | Strip on a log axis | x: rank 1 to 7,796 (log); one tick per known site, labelled for the best five and for Rajkot; shaded band for the top 100 | `site_ranks.csv` |
| F-R7 | Results | Ranked horizontal bars, one hue | y: what the alarm was; x: count of 100; "dump" bar in `--series-1` | `blind_check.csv` |
| F-X1 | Diagnosis | HTML table as heat table | 26 rows grouped by feature group, 5 columns; cell shade by distance of AUC from 0.5 on the one-hue scale; value printed; each cell links to the explorer | `diag_feature_auc.csv` |
| F-X2 | Diagnosis | Horizontal bars | y: six classes; x: share of points with a landfill-majority neighbourhood (26 features) | `diag_neighbours.csv` |
| F-X3 | Diagnosis | Three small scatter panels | PC1 against PC2; each panel shows landfill (`--series-1`) over one group in `--series-2`: ordinary land, bare soil and quarry, ash pond; dots 2.5 px at 50% opacity | computed (5.4) |
| F-X4 | Diagnosis | Horizontal bars | y: six classes; x: share flagged; landfill row labelled "recall" | `diag_flagged_by_class.csv`, version 3 row |
| F-X5 | Diagnosis | One segmented bar plus a ranked list | Six feature groups as shares of total SHAP, share printed on each segment; below, the five largest features | `diag_shap_groups.csv`, `diag_shap_features.csv` |
| F-X6 | Diagnosis | Line chart, log x | x: landfill share of pixels from 1 in 2 to 1 in 100,000; y: precision; two lines (validation rates, Gujarat rates), labelled; markers at the validation mix and at the share of known-site pixels in Gujarat | computed (5.4) |

Tables T-O1, T-D1 to T-D5, T-M1, T-M2, T-R1 to T-R3, T-X1 and T-X2 are plain HTML tables written into the pages; numeric cells are tagged with `data-k` where a `site.json` key exists, and otherwise generated into the page by `--fill` from `tables.json` (a `<tbody data-table="T-R1">` is replaced whole).

## 10. Wording rules

### 10.1 Terms

| Use | Not |
| --- | --- |
| model score | confidence, probability |
| flagged | detected, predicted landfill (for pixels) |
| found (a known site, by the half-outline rule) | detected |
| alarm patch | detection |
| hand check | validation (reserved for the held-out splits) |
| known sites, sealed list | ground truth |
| not scored | clean, no landfill |
| look-alike | false positive class |
| landfill or dumpsite, used as the labels use them | sanitary landfill (none of these are) |

### 10.2 Style

- Plain declarative sentences. Finding first, then the number, then how it was measured.
- Every figure caption opens with what the figure shows as a finding ("Look-alikes are flagged four to six times as often as ordinary land."), then how to read it.
- No claim without a number or a figure next to it. No adjectives doing the work of a number.
- "The model" always means the frozen version 3 model unless a version is named.
- British spelling, as in the rest of the repository.

### 10.3 Disclosure text

Overview §4, as a callout, verbatim unless the author edits it:

> **This is the third model built in this project.** Two earlier versions were trained, frozen and scored on the same 17 Gujarat sites, and what they got wrong shaped this one. The Gujarat results here are therefore not a first-time test. No Gujarat data was used to train any version. The earlier versions are summarised under [How we got here](diagnosis.html#how-we-got-here).

Method §5 repeats the first two sentences. Diagnosis §9 lists it as the first limitation.

### 10.4 AI-use disclosure: what it must cover

To be written with the author and signed off by them. It states, specifically:
- Which assistant was used and for what: writing the scripts, the analysis code, the guides, the website and drafts of documentation; literature search.
- What the author did personally: chose the question; screened and outlined every training site and every Gujarat test site; made every labelling and design decision; ran every Earth Engine fetch and the Gujarat scoring; did the hand check; wrote the paper.
- How AI output was checked: results reproduced from a clean clone; numbers on the site checked against result files by script.
- That no labels or verdicts were produced by AI.

## 11. Glossary and margin notes

Each term has one entry of one to three sentences. The glossary on the Reproduce page lists all of them alphabetically with anchors `g-<slug>`. A margin note is the same text, placed where the term first matters on a page. A term may have a margin note on more than one page.

| Term | Pages with a margin note |
| --- | --- |
| Sentinel-2; Landsat; SRTM | Overview, Data |
| Band; surface reflectance | Data |
| Median composite | Data, Method |
| NDVI; NDBI; BSI | Data |
| Land surface temperature (LST); temperature anomaly | Data |
| Pre-monsoon; winter (rabi) season | Method |
| Look-alike; near-site background; random background | Data |
| Place (outlines within 500 m treated as one) | Data |
| Zonal Council region | Method |
| Leakage | Method |
| Held-out region; held-out site; random pixel split | Method, Results |
| Precision; recall; F1 (as used here) | Method |
| Threshold; model score | Method, Results |
| Freeze; tag | Method |
| Sealed test list | Data, Method |
| Site found (half-outline rule) | Method, Results |
| Alarm patch; rank | Method, Results |
| Hand check; blind ID | Method, Results |
| AUC (single feature) | Data, Diagnosis |
| Nearest-neighbour purity | Diagnosis |
| Principal components | Diagnosis |
| SHAP | Diagnosis |
| Novelty percentile; extrapolation | Diagnosis |
| Prevalence (how rare landfill is) | Diagnosis |
| Gradient boosting; random forest; logistic regression | Method |

The plain-language guide (`docs/guide/project_guide_plain.html`) already has definitions for most of these; reuse its wording.

## 12. Pending inputs

| Input | Who | Unlocks | Until then |
| --- | --- | --- | --- |
| `data/gujarat_results_v3/blind_check.csv` filled for A001 to A100 | Author | Overview tile 3; Results §5 (T-R3, F-R7); Diagnosis §1 gallery classes; T-X2 last cell; all `check.*` keys | Spans read "pending"; sections show a one-line notice |
| `data/analysis/alarm_diagnostics.md` and `diag_alarm_*.csv` | Author runs `alarm_diagnostics.py` | Diagnosis §5 (T-X1) | Section shows the question and "analysis not yet run" |
| Chips (`make_chips.py`) | Author, after the hand check is committed | Results §3 callout image; Diagnosis §1 and §7 | Galleries hidden |
| `docs/paper.pdf` | Author | Footer and Overview links | Link omitted |
| Checked references | Author and builder | Results §5 sentence; Diagnosis §8; Reproduce §7 | Unchecked claims left out |
| New-cities test | Author (optional) | Results §6 | Section absent |
| Author line | Author | Overview §6, footer | "ES 678 course project" only |

Vocabulary expected in `blind_check.csv`, from the version 1 sheet: `verdict` is `dump`, `lookalike` or `unsure`; `class` is one of the look-alike classes; `seen` is a short free label (`blue_roof`, `water`, `salt_pan`, `building`, …). The build script groups by `seen`, folds any label with fewer than three alarms into "other", and treats A065 (Surendranagar, known to the checker) as a dump with a footnote. The Wilson interval is computed on dumps over checked alarms excluding `unsure`.

## 13. Build order and cuts

Estimated at about 13 hours of work for one builder.

| Step | Work | Hours | Priority |
| --- | --- | --- | --- |
| 1 | `build_site_data.py`: `site.json`, `tables.json`, `--fill`, `--check` | 2 | Must |
| 2 | `site.css`, page shell, header, footer, theme switch, margin notes | 1.5 | Must |
| 3 | Text and tables of the six pages | 3.5 | Must |
| 4 | `threshold.json` and the threshold slider | 1.5 | Must (one interaction is required) |
| 5 | `features_hist.json` and the feature explorer | 1.5 | Must |
| 6 | Static charts F-R1 to F-R4, F-R6, F-X1, F-X2, F-X4 to F-X6, F-D1 | 1.5 | Must |
| 7 | Maps F-O1, F-D2, box images F-R5 | 1 | Should |
| 8 | Chips and gallery | 1 | Should |
| 9 | F-X3 (PCA), F-M1, F-M2 | 0.5 | Could |
| 10 | Checks in section 14, both themes, phone width | 1 | Must |

Cut in this order if time runs short: training chips (5.8 optional); F-X3; F-R5; score overlay on chips; F-D2; F-M1 and F-M2 (replace with a sentence each); chip gallery beyond the 18 known sites. Never cut: the two interactions, the disclosure, the limitations, the number check.

## 14. Acceptance checks

1. `python scripts/build_site_data.py --check` passes; the only keys reported pending are those listed in section 12.
2. The internal checks of 5.4, 5.5 and 5.6 pass (published values reproduced).
3. Every row of the table in section 3 links to a section that exists and holds that content.
4. Every page: one `<h1>`; no broken internal link or missing file (check with a link checker or a short script over `href` and `src`).
5. Both interactions pass the checks in 8.1 and 8.2.
6. Both themes: every chart readable, no dark text on a dark surface, chips bordered.
7. At 360 px, 768 px and 1440 px: no horizontal scroll; margin notes fall under their paragraphs on the two narrower widths.
8. With JavaScript disabled: all text, tables and numbers are present; each chart area shows its table view.
9. `grep -rniE "@gmail|elemental-day|api[_-]?key|D:\\\\" docs/` returns nothing.
10. No request leaves the site's own origin (browser network panel shows only same-origin requests).
11. Every statement about versions 1 and 2 is inside the disclosure, the limitations list, or "How we got here".
12. Every number on the site read aloud against its result file once, by a person, after the final `--fill`.

## 15. Publishing

1. Merge the working branch into `main`.
2. On GitHub: Settings → Pages → Source "Deploy from a branch" → Branch `main`, folder `/docs` → Save. The repository must be public (or the plan must allow Pages on private repositories).
3. To preview locally before publishing: `python -m http.server 8000 --directory docs`, then open `http://localhost:8000/`. Opening the files directly from disk will not work, because the pages fetch JSON.
4. After the first deployment, load all six pages at the public address, in both themes, and repeat checks 4 and 10.
5. Put the site address in the README and in the paper.

## 16. Open items for the author

1. **Author line:** name, and whether to show roll number and institute.
2. **Hand check:** finish and commit `blind_check.csv` before running `make_chips.py`.
3. **References:** confirm Agrawal et al. and the Campania paper; confirm the figures quoted from Kruse et al. 2023 and Gibellini et al. 2025 against the papers.
4. **AI-use disclosure:** read and edit the draft; it must be true as the author would state it.
5. **Repository visibility:** public, or access given to the graders, and Pages enabled.
6. **New-cities test:** go or no-go by Monday night.
