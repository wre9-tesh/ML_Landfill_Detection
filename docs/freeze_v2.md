# Freeze, version 2

Version 1 (`docs/freeze.md`, tag `freeze-v1`) is the frozen test and stays the reported first result: 16 of 17 Gujarat sites found, and none of the 50 checked top alarms a dumpsite.

Version 2 is a second attempt, designed after seeing that result. Its Gujarat numbers are therefore not a first-time test, and every write-up must say so. No Gujarat pixel is used in training. Everything below is fixed by the commit that carries the tag `freeze-v2`, pushed before version 2 is scored.

## What changed, and why

| Change | Reason |
| --- | --- |
| 25,800 more background points, drawn in the boxes 15 km around the 86 training landfills (`scripts/build_background_v2.py`); 25,223 have all features | Version 1's background was mostly farmland and forest. Gujarat is scored around cities, and the top alarms were blue roofs and water |
| Model chosen by the best mean held-out-region F1, with no "simplest within one SD" tie-break | The tie-break chose logistic regression, which gives extreme scores to pixels unlike any it was trained on |
| Alarms ranked by area times mean score | Mean score alone puts single roofs on top; dumps are large patches |

The second and third changes were decided on Nov 14 before any version 2 result existed.

## What is frozen

| Item | Value |
| --- | --- |
| Training data | Version 1's 9,470 points plus the 25,223 new background points: 3,865 landfill, 30,828 other |
| Folds | The same six Zonal Council regions; each background point belongs to the region of the landfill it surrounds |
| **Model** | **Random forest**, 500 trees, class-balanced, scikit-learn defaults. Held-out-region F1 0.739 (SD 0.115), precision 0.827, recall 0.692. Gradient boosting is next at 0.737 |
| Features, threshold | All twelve; 0.5 |
| Found, alarm size, Surat LF-3, scoring area | As in version 1: half the outline's scored pixels flagged; patches of 1 ha or more; left out; the same 13 boxes |
| Alarm order | Area times mean score |

Held out, the random forest flags 1.9% of the new near-landfill background, 1.1% of random background and 6.5% of look-alike points, against 8.5%, 5.5% and 33% for logistic regression on the same data. It pays for that in recall: 72% of landfill points, against 91%.

Validation F1 is lower than in version 1 (0.739 against 0.848) because the test is harder: there are now eight non-landfill points for every landfill point, where version 1 had one and a half.

## Steps

```bash
python scripts/freeze_model.py --results data/results_v2
```

Commit `data/results_v2/model.joblib` and `model.json`, then:

```bash
git tag -a freeze-v2 -m "Freeze of version 2 before its Gujarat scoring"
```

```bash
git push origin main freeze-v2
```

```bash
python scripts/score_gujarat.py --version 2
```

Results go to `data/gujarat_results_v2/`; version 1's results are not touched.
