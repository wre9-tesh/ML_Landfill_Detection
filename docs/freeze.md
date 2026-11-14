# Freeze

Everything below is fixed by the commit that carries the tag `freeze-v1`. The tag is pushed before Gujarat is scored. After it, no site, feature, model, threshold or scoring rule changes.

## What is frozen

| Item | Value | Where it comes from |
| --- | --- | --- |
| Training data | 86 landfill places (75 hand-drawn, 11 OSM) and 60 look-alike places, none in Gujarat; 9,470 points with all features | `data/samples/samples_summary.txt` |
| Folds | The six Zonal Council regions, because only Maharashtra has 10 or more places | rule fixed Nov 4 |
| Best mean held-out-region F1 | Gradient boosting, 0.865 (SD 0.058) | `data/results/results.md` |
| **Primary model** | **Logistic regression on standardised features**, F1 0.848 (SD 0.037). It is the simplest model at or above 0.807, which is one SD below the best | selection rule fixed Nov 4 |
| Features | All twelve | fixed Nov 9 |
| Threshold | 0.5 on the model score | fixed Nov 4 |
| Scoring area | A box 15 km beyond the test sites of each of the 13 test cities, scored locally | decided Nov 11 |
| Test list | The 17 outlined sites in `labels/gujarat_test_sites.csv`, sealed in commit `8711855` | sealed Nov 11 |

The primary model's held-out-region precision is 0.832 and recall 0.883. It flags 5.1% of random background points, 20% of ash-pond points, 39% of bare-soil points and 43% of quarry points. With that recall and that background rate, precision would be about 15% if 1 pixel in 100 were landfill and about 2% at 1 in 1,000.

## Scoring rules, decided Nov 14

- **Found.** A Gujarat site is found when at least half of the scored pixels inside its outline are flagged. One flagged pixel was rejected as a rule because the model flags about 5% of background pixels, so almost any outline would contain one by chance. The share flagged is reported for every site.
- **Alarm.** A patch of touching flagged pixels (edges, not corners) of at least 1 ha, outside the sealed outlines, ranked by mean score. The top 100 go to the blind check.
- **Surat LF-3** has a pin and no outline. It is left out of recall and reported as not scoreable.
- **Failure.** The Gujarat test fails if fewer than half of the 17 sites are found (8 or fewer).

These are the defaults of `scripts/score_gujarat.py`, so it is run with no options.

## Steps

```bash
python scripts/freeze_model.py
```

Commit `data/results/model.joblib` and `model.json`, then:

```bash
git tag -a freeze-v1 -m "Freeze before Gujarat scoring"
```

```bash
git push origin main freeze-v1
```

`scripts/score_gujarat.py` refuses to run on a commit without a freeze tag.
