# Landfill detection in Gujarat from free satellite data

ES 678 course project (graduate track), Amitesh Kumar, IIT Gandhinagar.

**Paper:** *Balanced Scores, Rare Targets: How Validation Design and Prevalence Change Satellite Dumpsite Detection*, [Amitesh_Kumar_24210011_ML_project_Report.pdf](Amitesh_Kumar_24210011_ML_project_Report.pdf). The LaTeX source is in [docs/Paper/](docs/Paper/).

This repository holds everything needed to rerun the study: the hand-made labels, every script, every intermediate table, the three frozen models, the per-pixel Gujarat score maps and the hand-check sheet.

## Questions and answers

The unit of prediction is one 10 m pixel. The target is 1 if the pixel lies on visible, active waste in March–May 2024, and 0 otherwise. Predictions use only imagery up to May 2024 and no Gujarat labels.

| | Question | Answer (version 3, gradient boosting) |
| --- | --- | --- |
| Q1 | Does a model trained only outside Gujarat find Gujarat's known dumpsites? | **Yes.** 5 of 6 sites in new cities (the clean test) and 16 of 17 on the first list. However, it also flags about 5% of all scored land. |
| Q2 | How much does the validation design change the score? | **A lot for some models.** Random forest F1 drops from 0.91 (random pixels) to 0.74 (regions held out); gradient boosting only from 0.81 to 0.76. Region-held-out validation matched Gujarat (F1 ≈ 0.70). |
| Q3 | What precision should a user expect when dumpsites are rare? | **Very low.** Precision is 67% in validation but 0.35% and 0.064% in the two Gujarat lists, where dumps are 0.024% and 0.003% of the land. Only 5 of the 100 strongest alarms were dumps. |

**Why it fails.** The false alarms are bare soil, fields, buildings and industrial yards that share the dumps' main cue, a surface warmer than its surroundings (`LST_anom`). They are not unusual pixels: none lies beyond the 99th percentile of distances to the training data. Adding features (12 to 26) did not remove the confusion; whole-patch context would be needed.

## Main results

| | |
| --- | --- |
| Training data | 34,345 pixels from 86 landfill places in 26 states (3,853 landfill, 24,989 near-site background, 3,764 random background, 1,739 look-alike) |
| Model | Gradient boosting, scikit-learn defaults, class-balanced, threshold 0.5; selected by a rule fixed in advance (best mean F1 with whole regions held out) |
| Validation, held-out region | F1 0.762 ± 0.044 (precision 0.694, recall 0.865); the published threshold rule scores 0.415 |
| Gujarat, new cities (clean test) | 5 of 6 found; Porbandar missed (18.5% of outline flagged); 4.0% of 5,244 km² flagged |
| Gujarat, first list | 16 of 17 found; Rajkot missed (48.6% flagged); 5.2% of 12,854 km² flagged, 7,801 alarm patches |
| Hand check of the top 100 alarms | 5 dumps (3 previously unknown) and 95 hard negatives: bare soil 46, fields or grass 19, buildings 17, industrial 5, other 8 |

## Three versions and why

Each version was frozen under a Git tag before Gujarat was scored with it.

| | `freeze-v1` | `freeze-v2` | `freeze-v3` (final) |
| --- | --- | --- | --- |
| Change | Original plan, 12 features | + 25,800 near-site background points | + 14 winter and neighbourhood features (26) |
| Model | Logistic regression | Random forest | Gradient boosting |
| First-list sites found | 16 of 17 | 15 of 17 | 16 of 17 |
| Top alarms | 0 dumps in 50 checked (mostly blue roofs) | Large bare fields | 5 dumps in 100 checked |

Version 3 was designed after seeing how versions 1 and 2 failed on the first 17-site list, so that list is no longer an unseen test. A second list of six sites in new cities was sealed afterwards and scored once: **that list is the clean test**. No Gujarat data entered any version's training.

## Safeguards against test leakage

- **Sealed lists:** the Gujarat lists were committed before any model was run on them (commits `8711855` and `fc81cd5`).
- **Freeze tags:** `score_gujarat.py` refuses to run unless the model file matches a `freeze-vN` tag. The rules fixed at each freeze are in [docs/freeze.md](docs/freeze.md), [freeze_v2.md](docs/freeze_v2.md) and [freeze_v3.md](docs/freeze_v3.md).
- **No Gujarat data in training,** and Gujarat false alarms were not added as negatives.
- **No tuning:** scikit-learn defaults and a fixed threshold; the only learned preprocessing is fit inside each training fold.
- **Blind hand check:** alarm pins carried shuffled IDs, hiding rank and score.

## Setup

Python 3.13 (3.11+ should work).

```bash
git clone https://github.com/wre9-tesh/ML_Landfill_Detection.git
```

```bash
cd ML_Landfill_Detection
```

```bash
python -m venv .venv
```

Activate it (`.\.venv\Scripts\Activate.ps1` on Windows, `source .venv/bin/activate` elsewhere), then:

```bash
python -m pip install -r requirements.txt
```

scikit-learn is pinned exactly, because a saved model must be opened with the version that wrote it. Steps marked **EE** need a free [Google Earth Engine](https://earthengine.google.com) account linked to a Cloud project (`earthengine authenticate`); the project ID is passed on the command line and never stored.

## Replication

Every intermediate file except the Gujarat feature rasters is stored in the repository, so each step can be rebuilt and compared, or skipped. **Without an Earth Engine account you can run steps 1, 2, 5, 6 and 10 and reproduce every validation number.** Write Earth Engine outputs to `rep/` (ignored by Git) and compare them with `scripts/compare_tables.py`. For steps that rewrite stored files, `git status --short data` printing nothing means your output is byte-for-byte identical.

| # | Command | Output | Time |
| --- | --- | --- | --- |
| 1 | `python scripts/build_samples.py` | `data/samples/points.csv` (9,530 points) | 2 s |
| 2 | `python scripts/build_background_v2.py` | `points_v2_background.csv` (25,800) | 15 s |
| 3 EE | `python scripts/gee_features.py --project ID --out rep/features`, and again with `--points data/samples/points_v2_background.csv --out rep/features_v2` | The 12 base features | ~15 min |
| 4 EE | The same two runs with `--stack extra` and `--out rep/features_v3/main` or `rep/features_v3/background` | The extra features | ~15 min |
| 5 | `python scripts/run_models.py --features data/features/features.csv data/features_v2/features.csv --extra data/features_v3/main/features.csv data/features_v3/background/features.csv --rule best --out data/results_v3` | Validation of nine methods, `results.md` | ~20 min |
| 6 | `python scripts/freeze_model.py --results data/results_v3` | `model.joblib` (the tagged model) | 20 s |
| 7 EE | `python scripts/gee_export_gujarat.py --project ID --boxes labels/gujarat_boxes.json`, and again with `--stack extra` | 28 GeoTIFFs on Google Drive → `data/gujarat/`, `data/gujarat_x/` | 1–3 h |
| 8 | `python scripts/score_gujarat.py --version 3 --out rep/gujarat_results_v3` | First-list results | ~15 min |
| 9 | `python scripts/score_gujarat.py --version 3 --sites labels/gujarat_new_sites.geojson --tifs data/gujarat_new --extra-tifs data/gujarat_new_x --out rep/gujarat_results_v3_new` | New-cities results (export their boxes in step 7 with `--sites labels/gujarat_new_sites.csv`) | ~5 min |
| 10 | `python scripts/diagnostics.py`, `python scripts/alarm_diagnostics.py --no-extract`, `python scripts/paper_figures.py` | `data/analysis/`, `figures/`, `docs/Paper/figures/` | a few min |

The hand check of the top 100 alarms (`alarms_blind.kml` in Google Earth Pro, recorded in `data/gujarat_results_v3/blind_check.csv`) is a human judgement and cannot be rerun exactly. Labelling rules, sampling and feature definitions are in [docs/methods.md](docs/methods.md).

**Numbers to match:** 34,345 points with all features; gradient boosting selected with held-out-region F1 0.762; 16 of 17 sites found, 6,662,452 of 128,541,406 pixels flagged, 7,801 alarms; 5 of 6 new-city sites, 2,791 alarms. Earth Engine refetches can differ slightly when Google reprocesses its archives; train on the stored tables to reproduce the reported numbers exactly.

## Repository layout

| Path | Contents |
| --- | --- |
| `docs/Paper/` | Paper LaTeX source, figures and `numbers.txt` |
| `docs/methods.md`, `docs/freeze*.md` | Methods detail and the three freeze records |
| `labels/` | OSM screening sheet, hand-drawn outlines, the two sealed Gujarat lists, the scored boxes |
| `scripts/` | Every program |
| `data/samples/`, `data/features*/` | Sample points and feature tables |
| `data/results*/` | Validation results and frozen models (`results/` v1, `results_v2/`, `results_v3/`) |
| `data/gujarat_results*/` | Gujarat scoring per version: site recall, alarms, hand-check sheets, score rasters (`_v3_new/` is the clean test) |
| `data/analysis/`, `figures/` | Diagnostics and their figures |

## Data sources and licences

Sentinel-2 (Copernicus); Landsat 8/9 and SRTM (USGS/NASA); JRC Global Surface Water; OpenStreetMap (© contributors, ODbL 1.0); geoBoundaries (CC BY). Details and checksums are in [data/README.md](data/README.md). No credentials are stored in the repository.

## AI-use disclosure

Claude (Anthropic), through Claude Code, wrote the Python scripts to the author's specification, ran training, diagnostics and reproducibility checks, searched for related work, drafted documentation and figures, and edited the paper text. The author chose the question, screened every OSM candidate, drew every outline, compiled both Gujarat test lists, ran the Earth Engine fetches and Gujarat scoring, judged all 100 alarms, made every decision about what to report and checked the reported numbers. No label or verdict was produced by AI.

## References

1. Bhajantri and Mandpe (2026). Ground truthing of dumpsites using remote sensing and machine learning approaches in peri-urban settings. *Applied Geomatics* 18, article 88.
2. Kruse, C., and others (2023). Satellite monitoring of terrestrial plastic waste. *PLOS ONE* 18(1): e0278997. arXiv:2204.01485.
3. Pedregosa, F., and others (2011). Scikit-learn: machine learning in Python. *JMLR* 12: 2825–2830.
4. Lundberg, S. M., and Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS* 30.
5. Gorelick, N., and others (2017). Google Earth Engine: planetary-scale geospatial analysis for everyone. *Remote Sensing of Environment* 202: 18–27.
6. Pekel, J.-F., and others (2016). High-resolution mapping of global surface water and its long-term changes. *Nature* 540: 418–422.
7. Farr, T. G., and others (2007). The Shuttle Radar Topography Mission. *Reviews of Geophysics* 45: RG2004.
8. Runfola, D., and others (2020). geoBoundaries: a global database of political administrative boundaries. *PLOS ONE* 15(4): e0231866.

## Licence

See [LICENSE](LICENSE).
