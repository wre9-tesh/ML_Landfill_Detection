# Landfill detection in Gujarat from free satellite data

ES 678 course project (graduate track). Can a model trained on Indian landfills outside Gujarat find Gujarat's landfills from Sentinel-2, Landsat and SRTM data? Three models were trained, each frozen under a Git tag before Gujarat was scored. All three flag almost all of the 17 known sites, and all three flag 2 to 5% of the land, so the project is written up as a diagnostic study of why such a detector is hard to build.

| | Version 1 | Version 2 | Version 3 |
| --- | --- | --- | --- |
| What changed | Original plan: 12 features | More background points near training sites | Winter season and surroundings: 26 features |
| Model selected | Logistic regression | Random forest | Gradient boosting |
| Held-out-region F1 | 0.848 | 0.739 | 0.762 |
| Gujarat sites found, of 17 | 16 | 15 | 16 |
| Scored land flagged | 5.5% | 1.8% | 5.3% |
| Known sites in the top 100 alarm patches | not recorded | 4 | 8 |
| Hand check of the top alarms | 0 of 50 are dumps | failed by eye | 5 of 99 are dumps |
| Tag | `freeze-v1` | `freeze-v2` | `freeze-v3` |

Validation F1 is not comparable between version 1 and the others: versions 2 and 3 are tested against far more background points. Only version 1 is a first-time test of Gujarat; versions 2 and 3 were designed after earlier results were seen.

## Website

The project is presented at <https://wre9-tesh.github.io/ML_Landfill_Detection/> (served from `docs/`). The page text is in `site_src/`; `python scripts/build_site_data.py` fills every number from the result files and writes the pages, and `--check` fails if a page is out of date. To view it locally: `python -m http.server 8000 --directory docs`.

## Reproducing version 3

Step-by-step manuals:

- [docs/project_guide_grader.pdf](docs/project_guide_grader.pdf): short. A quick check that needs no accounts, then the full path.
- [docs/project_guide_technical.pdf](docs/project_guide_technical.pdf): detailed. Setup from scratch on Windows, every command with its expected output, and what each script does inside.
- [docs/project_guide_plain.pdf](docs/project_guide_plain.pdf): the project explained without jargon.

Setup (Windows PowerShell, Python 3.13):

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run order. Steps marked EE need a Google Earth Engine project; every other step runs from the files in this repository.

| # | Command | Writes |
| --- | --- | --- |
| 1 | `python scripts/build_samples.py` | `data/samples/points.csv` |
| 2 | `python scripts/build_background_v2.py` | `data/samples/points_v2_background.csv` |
| 3 (EE) | `python scripts/gee_features.py --project ID`, and again with `--points data/samples/points_v2_background.csv --out data/features_v2` | The twelve base features |
| 4 (EE) | The same two fetches with `--stack extra` and `--out data/features_v3/main` or `data/features_v3/background` | The ten extra features |
| 5 | `python scripts/run_models.py --features data/features/features.csv data/features_v2/features.csv --extra data/features_v3/main/features.csv data/features_v3/background/features.csv --rule best --out data/results_v3` | Validation results |
| 6 | `python scripts/freeze_model.py --results data/results_v3` | The frozen model |
| 7 (EE) | `python scripts/gee_export_gujarat.py --project ID --boxes labels/gujarat_boxes.json`, and again with `--stack extra` | Rasters for `data/gujarat/` and `data/gujarat_x/` |
| 8 | `python scripts/score_gujarat.py --version 3` | `data/gujarat_results_v3/` |
| 9 | `python scripts/diagnostics.py`, `python scripts/alarm_diagnostics.py` | `data/analysis/` |
| 10 | `python scripts/make_chips.py` (needs the rasters), then `python scripts/build_site_data.py` | The website in `docs/` |

## Data access

- In the repository: labels and outlines, sample points, all feature tables, all results, and the model score of every scored Gujarat pixel (`data/gujarat_results_v3/scores/`).
- Not in the repository: the Gujarat feature rasters (several gigabytes). Step 7 rebuilds them from public data with a free Google Earth Engine account.
- Steps 1, 2, 5, 6, the first command of step 9 and `build_site_data.py` need no account.
- Sources and licences: Sentinel-2 (Copernicus), Landsat 8 and 9 and SRTM (USGS, NASA), JRC Global Surface Water, OpenStreetMap (ODbL), geoBoundaries (CC BY). Details in [data/README.md](data/README.md).
- The repository holds no credentials. The Earth Engine project ID is passed on the command line and is not stored.

## What the freeze tags mean

Each `freeze-vN` tag marks the commit in which a model, its threshold and its scoring rules were fixed. The tag was pushed before Gujarat was scored with that model, and `score_gujarat.py` runs only if the model file is the tagged one. The rules are in [docs/freeze.md](docs/freeze.md), [docs/freeze_v2.md](docs/freeze_v2.md) and [docs/freeze_v3.md](docs/freeze_v3.md). The Gujarat test list was sealed in commit `8711855`, before any model was run on it.

## Where things are

- `labels/`: screening decisions, hand-drawn outlines, the sealed Gujarat list, the scored boxes.
- `scripts/`: every program.
- `data/`: points, feature tables, results, analysis. Sources and licences are in [data/README.md](data/README.md).
- `docs/`: the original plan ([checklist.md](docs/checklist.md)), labelling and feature notes ([phase1_labels.md](docs/phase1_labels.md), [phase2_features.md](docs/phase2_features.md)), freeze notes, hand-off notes ([context.md](docs/context.md)) and the guides.
- `figures/`: charts for the paper.

## AI-use disclosure

An AI assistant, Claude (Anthropic), was used throughout through Claude Code.

- The assistant wrote the Python scripts to the author's requirements, ran model training, the diagnostics and the reproducibility checks, searched for and summarised related papers, drafted the documentation, the guides and the website, and proposed parts of the study design, which the author accepted, changed or rejected.
- The author chose the question, screened every OpenStreetMap candidate, drew every training outline, compiled and outlined the Gujarat test list, ran every Earth Engine fetch and the Gujarat scoring, judged all 100 alarms in the hand check, and made every decision about labels, features, versions and what to report.
- No label or verdict was produced by AI.
- Results were reproduced from a clean clone, and every number on the website is filled from the result files by script.

## References

1. Bhajantri and Mandpe (2026). *Applied Geomatics* 18, article 88. The study that prompted the project and the source of the published threshold rule.
2. Kruse, C., and others (2023). Satellite monitoring of terrestrial plastic waste. *PLOS ONE* 18(1): e0278997.
3. Gibellini and others (2025). *Waste Management Bulletin*. arXiv:2502.06607.
4. Pedregosa, F., and others (2011). Scikit-learn: machine learning in Python. *JMLR* 12: 2825–2830.
5. Lundberg, S. M., and Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS* 30.
6. Gorelick, N., and others (2017). Google Earth Engine: planetary-scale geospatial analysis for everyone. *Remote Sensing of Environment* 202: 18–27.
7. Pekel, J.-F., and others (2016). High-resolution mapping of global surface water and its long-term changes. *Nature* 540: 418–422.
8. Farr, T. G., and others (2007). The Shuttle Radar Topography Mission. *Reviews of Geophysics* 45: RG2004.
9. Runfola, D., and others (2020). geoBoundaries: a global database of political administrative boundaries. *PLOS ONE* 15(4): e0231866.
