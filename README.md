# Landfill detection in Gujarat from free satellite data

ES 678 course project (graduate track), Amitesh Kumar, IIT Gandhinagar.

**Question.** Can a pixel classifier trained only on Indian dumpsites outside Gujarat find Gujarat's dumpsites from free 10 m satellite data (Sentinel-2, Landsat 8/9 thermal, SRTM)? When it is wrong, why?

**Paper:** [docs/Paper/main.pdf](docs/Paper/main.pdf). The LaTeX source is in the same folder.

## Main result (version 3, tag `freeze-v3`)

| | |
| --- | --- |
| Training data | 34,345 labelled pixels (3,853 landfill) from 86 landfill places in 26 states, plus look-alike and background points; 26 features |
| Model | Gradient boosting (scikit-learn defaults, class-balanced, threshold 0.5), selected by the best mean F1 with whole regions held out |
| Validation, held-out region | F1 0.762 ± 0.044 (precision 0.694, recall 0.865); the published threshold rule scores 0.415 |
| Gujarat, sealed list | 16 of 17 sites found; Rajkot missed (48.6% of its outline flagged) |
| Gujarat, six new cities | 5 of 6 found; Porbandar missed |
| Land flagged | 5.2% of 12,854 km² scored, in 7,801 alarm patches |
| Hand check of the top 100 alarms | 5 dumps (3 previously unknown), 94 look-alikes, 1 unsure |

The model finds the known sites, but it also flags bare soil, fields, buildings and industrial land that share the dumps' thermal signature. At realistic prevalence, pixel precision is below 2%. The paper's depth analysis covers the split ablation, precision against prevalence, and a failure audit of the alarms.

**Three versions.** Each model was frozen under a Git tag before Gujarat was scored. Version 1 (`freeze-v1`, logistic regression, 12 features) and version 2 (`freeze-v2`, random forest, with near-site background) are kept for transparency. Version 3 was designed after their results were seen, so the 17-site list is not an unseen test for it. The six-city list is. No Gujarat data was used in training any version.

## Repository layout

| Path | Contents |
| --- | --- |
| `docs/Paper/` | Paper source (`main.tex`, `refs.bib`, `figures/`, course style file) and compiled PDF |
| `docs/methods.md` | Labelling rules, sampling design and feature definitions in detail |
| `docs/freeze.md`, `freeze_v2.md`, `freeze_v3.md` | What each freeze fixed, written before the corresponding Gujarat scoring |
| `labels/` | Screening decisions, hand-drawn outlines, the sealed Gujarat lists and the scored boxes |
| `scripts/` | Every program (see run order below) |
| `data/samples/` | Sample points |
| `data/features*/` | Feature tables fetched from Earth Engine |
| `data/results*/` | Cross-validation results and frozen models (`model.joblib`), one folder per version |
| `data/gujarat_results*/` | Gujarat scoring: per-site recall, alarms, the hand-check sheet and per-pixel score rasters |
| `data/analysis/` | Depth analysis and diagnostics tables |
| `figures/` | Diagnostic figures (version 1 split ablation, feature AUC, PCA, SHAP groups) |

## Setup

Python 3.13. On Windows PowerShell:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate with `source .venv/bin/activate`. scikit-learn is pinned exactly, because a saved model must be opened with the version that wrote it.

Steps marked **EE** need a free [Google Earth Engine](https://earthengine.google.com) account and a Cloud project ID:

```
python -c "import ee; ee.Authenticate()"
```

## Run order (version 3)

| # | Command | Writes | Account |
| --- | --- | --- | --- |
| 1 | `python scripts/build_samples.py` | `data/samples/points.csv` | none |
| 2 | `python scripts/build_background_v2.py` | `data/samples/points_v2_background.csv` | none |
| 3 | `python scripts/gee_features.py --project ID`, and again with `--points data/samples/points_v2_background.csv --out data/features_v2` | The 12 base features | EE |
| 4 | The same two fetches with `--stack extra` and `--out data/features_v3/main` or `data/features_v3/background` | The 14 version 3 features | EE |
| 5 | `python scripts/run_models.py --features data/features/features.csv data/features_v2/features.csv --extra data/features_v3/main/features.csv data/features_v3/background/features.csv --rule best --out data/results_v3` | Cross-validation of the nine methods (about 20 min on 4 cores) | none |
| 6 | `python scripts/freeze_model.py --results data/results_v3` | The frozen model | none |
| 7 | `python scripts/gee_export_gujarat.py --project ID --boxes labels/gujarat_boxes.json`, and again with `--stack extra` | Feature rasters, exported to Google Drive; download them into `data/gujarat/` and `data/gujarat_x/` | EE |
| 8 | `python scripts/score_gujarat.py --version 3` | `data/gujarat_results_v3/` | none |
| 9 | `python scripts/diagnostics.py`, then `python scripts/alarm_diagnostics.py` (needs the rasters) | `data/analysis/` | none |
| 10 | `python scripts/paper_figures.py` | `docs/Paper/figures/` | none |

Steps 1, 2, 5, 6, the first command of step 9, and step 10 run from the files in this repository, with no account. Steps 1, 2, 5, 6 and 9 were checked to reproduce the committed files byte for byte, apart from figure PDFs.

The six-city test reuses the frozen model. Export boxes for `labels/gujarat_new_sites.csv` into `data/gujarat_new/` and `data/gujarat_new_x/`, then run `score_gujarat.py --version 3` with `--sites labels/gujarat_new_sites.geojson`, the matching `--tifs` and `--extra-tifs`, and `--out data/gujarat_results_v3_new`.

**Compile the paper:** in `docs/Paper/`, run `pdflatex main`, `bibtex main`, then `pdflatex main` twice. Or upload the folder to Overleaf with `main.tex` as the main file.

## Safeguards against test leakage

- **Sealed test lists.** The Gujarat lists were committed before any model was run on them: commit `8711855` for the 17 sites, `fc81cd5` for the six new cities.
- **Freeze tags.** Each `freeze-vN` tag marks the commit that fixed a model, its threshold and its scoring rules. `score_gujarat.py` refuses to run unless the model file matches a freeze tag.
- **No Gujarat data in training.** No Gujarat pixel, label or hand-check verdict was ever used for training or model selection.
- **No tuning.** All models use scikit-learn defaults and a fixed threshold of 0.5. The selection rule was written before any result.

## Data access and licences

- **In the repository:** labels, sample points, all feature tables, all results, frozen models, and the model score of every scored Gujarat pixel.
- **Not in the repository:** the Gujarat feature rasters (several GB). Step 7 rebuilds them from public data.
- **Sources:**
  - Sentinel-2 (Copernicus)
  - Landsat 8/9 and SRTM (USGS/NASA)
  - JRC Global Surface Water
  - OpenStreetMap (ODbL)
  - geoBoundaries (CC BY)

  Details are in [data/README.md](data/README.md).
- **No credentials:** the repository holds none. The Earth Engine project ID is passed on the command line.

## AI-use disclosure

Claude (Anthropic), used through Claude Code, did the following:
- wrote the Python scripts to the author's specification;
- ran model training, the diagnostics and the reproducibility checks;
- searched for and summarised related work;
- drafted the documentation and the paper text.

The author did the following:
- chose the question;
- screened every OpenStreetMap candidate and drew every training outline;
- compiled and outlined the Gujarat test lists;
- ran every Earth Engine fetch and the Gujarat scoring;
- judged all 100 alarms in the hand check;
- made every decision about labels, features, versions and what to report;
- checked the reported numbers against the result files.

No label or verdict was produced by AI.

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
