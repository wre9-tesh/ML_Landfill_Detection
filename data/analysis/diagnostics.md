# Diagnostics on the training data and the frozen models

34345 points with all 26 features: 3853 landfill, 24989 near-site background, 3764 random background, 479 bare soil, 360 quarry, 900 ash pond.

## 1. Separability

### One feature at a time

AUC of a single feature for landfill against each background class: 0.5 means the feature carries no information, 1 means landfill is always higher, 0 always lower.

| background | best single feature | its AUC | features with AUC outside 0.3-0.7 |
| --- | --- | --- | --- |
| Near-site background | LST_anom | 0.940 | 16 |
| Random background | LST_anom | 0.942 | 13 |
| Bare soil | LST_anom | 0.759 | 2 |
| Quarry | LST_anom | 0.847 | 3 |
| Ash pond | NDBI | 0.891 | 9 |

### All features together, without a model

For each point, the 15 nearest points from other places in standardised feature space. Landfill is 11% of the table, so a share near 0.11 means the neighbourhood is no more landfill-like than chance.

| class | features | points | mean landfill share among neighbours | points with a landfill majority |
| --- | --- | --- | --- | --- |
| Landfill | 12 features | 3853 | 0.686 | 0.736 |
| Near-site background | 12 features | 24989 | 0.030 | 0.018 |
| Random background | 12 features | 3764 | 0.022 | 0.011 |
| Bare soil | 12 features | 479 | 0.102 | 0.092 |
| Quarry | 12 features | 360 | 0.121 | 0.081 |
| Ash pond | 12 features | 900 | 0.077 | 0.063 |
| Landfill | 26 features | 3853 | 0.704 | 0.734 |
| Near-site background | 26 features | 24989 | 0.027 | 0.012 |
| Random background | 26 features | 3764 | 0.019 | 0.009 |
| Bare soil | 26 features | 479 | 0.093 | 0.079 |
| Quarry | 26 features | 360 | 0.120 | 0.075 |
| Ash pond | 26 features | 900 | 0.066 | 0.048 |

### Principal components

The first two components hold 50% of the variance of the 26 standardised features (36% and 14%); five hold 75%.

- PC1 is mostly BSI (+0.28), B4 (+0.27), NDBI (+0.27), BSI_ctx (+0.26), NDVI (-0.26).
- PC2 is mostly dBSI (+0.45), dNDVI (-0.44), B2_w (+0.30), NDVI_w (-0.26), B8 (+0.24).

## 2. Share of each class flagged when its region is held out

The landfill column is recall; every other column is a false-alarm rate. Version 1 was trained without the near-site background points, so it has no value there.

| version | Landfill | Near-site background | Random background | Bare soil | Quarry | Ash pond |
| --- | --- | --- | --- | --- | --- | --- |
| v1 (logistic regression) | 0.890 | nan | 0.051 | 0.390 | 0.425 | 0.198 |
| v2 (random forest) | 0.718 | 0.018 | 0.011 | 0.065 | 0.058 | 0.068 |
| v3 (gradient boosting) | 0.864 | 0.050 | 0.032 | 0.163 | 0.200 | 0.122 |

## 3. What each frozen model relies on

Share of the mean absolute SHAP value by feature group, on a sample of training points weighted towards landfill and look-alikes. Units differ between models (log-odds for logistic regression and gradient boosting, probability for the forest), so only the shares are comparable. Versions 1 and 2 have no winter, surroundings or change features.

| version | thermal | terrain | pre-monsoon spectral | winter spectral | surroundings | seasonal change |
| --- | --- | --- | --- | --- | --- | --- |
| v1 (logistic regression) | 0.078 | 0.022 | 0.899 | 0.000 | 0.000 | 0.000 |
| v2 (random forest) | 0.355 | 0.066 | 0.579 | 0.000 | 0.000 | 0.000 |
| v3 (gradient boosting) | 0.344 | 0.044 | 0.277 | 0.167 | 0.162 | 0.006 |

Five largest single features per version:

- v1: B3 26%, B2 17%, BSI 15%, NDBI 14%, LST_anom 8%
- v2: LST_anom 31%, B2 14%, NDVI 13%, NDBI 10%, BSI 6%
- v3: LST_anom 33%, B2 8%, B2_w 8%, NDBI 7%, NDVI_w 5%

