# Diagnostics on the Gujarat alarms

317 centres with all 26 features: the top 100 alarms of each version and the sealed sites. Values are the median of the 3 x 3 pixels at the centre of the patch.

## Novelty: are the alarms unlike the training data?

Percentile of each centre's distance to its 15 nearest training points, among the training points' own distances. `beyond_99th` is the share of centres farther out than 99% of training points; `neighbours_landfill` is the share of those neighbours that are landfill.

| version | what | centres | median_novelty_pct | beyond_99th | neighbours_landfill | v3_score |
| --- | --- | --- | --- | --- | --- | --- |
| v1 | alarm, unchecked | 50 | 95.796 | 0.200 | 0.217 | 0.086 |
| v1 | alarm, lookalike | 50 | 95.892 | 0.260 | 0.165 | 0.153 |
| v2 | alarm, unchecked | 100 | 25.108 | 0.000 | 0.614 | 0.941 |
| v3 | alarm, look_alike | 94 | 44.612 | 0.000 | 0.752 | 0.952 |
| v3 | alarm, Dump | 5 | 12.657 | 0.000 | 0.893 | 0.976 |
| v3 | alarm, Unsure | 1 | 33.449 | 0.000 | 1.000 | 0.959 |
| all | sealed site | 17 | 19.141 | 0.000 | 0.788 | 0.936 |

## What the nearest training points are

| version | what | ash_pond | bare_soil | landfill | near_site | quarry |
| --- | --- | --- | --- | --- | --- | --- |
| all | sealed site | 0 | 0 | 15 | 2 | 0 |
| v1 | alarm, lookalike | 1 | 1 | 10 | 38 | 0 |
| v1 | alarm, unchecked | 2 | 0 | 13 | 34 | 1 |
| v2 | alarm, unchecked | 0 | 0 | 69 | 31 | 0 |
| v3 | alarm, Dump | 0 | 0 | 5 | 0 | 0 |
| v3 | alarm, Unsure | 0 | 0 | 1 | 0 | 0 |
| v3 | alarm, look_alike | 1 | 0 | 80 | 13 | 0 |

## What pushed the score up (version 3 model, mean SHAP in log-odds)

Positive values push towards landfill. Computed for every centre with the version 3 model, including the alarms of versions 1 and 2, to show what it now makes of them.

| version | what | thermal | terrain | pre-monsoon spectral | winter spectral | surroundings | seasonal change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v1 | alarm, unchecked | -0.293 | -0.287 | -0.465 | -0.016 | -0.190 | 0.001 |
| v1 | alarm, lookalike | -0.294 | -0.285 | -0.532 | -0.136 | -0.077 | 0.003 |
| v2 | alarm, unchecked | 2.411 | -0.119 | 0.360 | -0.093 | -0.021 | -0.005 |
| v3 | alarm, look_alike | 2.431 | -0.108 | 0.293 | 0.186 | 0.114 | 0.007 |
| v3 | alarm, Dump | 1.996 | -0.108 | 0.859 | 0.538 | 0.399 | 0.003 |
| v3 | alarm, Unsure | 3.037 | -0.116 | 0.259 | 0.475 | -0.282 | 0.025 |
| all | sealed site | 1.834 | -0.143 | 0.683 | 0.398 | 0.223 | 0.005 |

## Checked alarms by what was seen

| version | seen | centres | median_novelty_pct | v3_score | v3_still_flags |
| --- | --- | --- | --- | --- | --- |
| v1 | ash_pond | 1 | 90.450 | 0.143 | 0.000 |
| v1 | blue_roof | 33 | 95.030 | 0.205 | 0.333 |
| v1 | building | 4 | 93.423 | 0.705 | 0.750 |
| v1 | field_or_grass | 2 | 97.717 | 0.447 | 0.500 |
| v1 | industrial_plant | 1 | 99.892 | 0.152 | 0.000 |
| v1 | other | 1 | 97.857 | 0.406 | 0.000 |
| v1 | salt_pan | 2 | 99.677 | 0.014 | 0.000 |
| v1 | salvage_yard | 1 | 93.615 | 0.011 | 0.000 |
| v1 | water | 5 | 99.828 | 0.011 | 0.000 |
| v3 | bare_soil | 46 | 37.567 | 0.941 | 0.957 |
| v3 | blue_roof | 1 | 93.763 | 0.876 | 1.000 |
| v3 | building | 16 | 47.810 | 0.961 | 1.000 |
| v3 | field_or_grass | 19 | 52.782 | 0.940 | 0.895 |
| v3 | industrial_plant | 5 | 22.329 | 0.945 | 0.800 |
| v3 | other  | 5 | 50.290 | 0.966 | 1.000 |
| v3 | riverbed | 2 | 24.200 | 0.956 | 1.000 |

