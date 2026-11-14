# Depth analysis

Frozen model: `logistic_regression`, threshold 0.5. Everything here is post hoc and selects nothing.

## 1. Split ablation

Mean F1 of every model under the three validation designs:

| model | random_pixel | held_out_site | held_out_region | drop_pixel_to_region |
| --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.650 | 0.648 | 0.571 | 0.079 |
| recalibrated_rule | 0.759 | 0.759 | 0.740 | 0.019 |
| logistic_regression | 0.878 | 0.867 | 0.848 | 0.030 |
| decision_tree | 0.906 | 0.823 | 0.797 | 0.109 |
| bagged_trees | 0.948 | 0.861 | 0.828 | 0.120 |
| random_forest | 0.948 | 0.873 | 0.840 | 0.107 |
| adaboost | 0.893 | 0.877 | 0.857 | 0.037 |
| gradient_boosting | 0.937 | 0.898 | 0.865 | 0.072 |

The frozen model across all four designs. Gujarat is scored at pixel level: 31,201 scored pixels lie inside the 17 sealed outlines and 119,113,329 outside. Recall is the share of outline pixels flagged (0.678); the false-alarm rate is the share of all other pixels flagged (0.0544), which counts any unlisted dump as a false alarm. "At the validation class mix" applies those two rates to the 40.8% landfill share of the validation points, so the row is comparable with the three above; "as they are" uses the real mix, where outline pixels are 0.0262% of the land. One difference remains: Gujarat counts every pixel of an outline, edge pixels included, while validation points sit at least 15 m inside their outlines, so part of the fall in recall is the edge.

| design | precision | recall | f1 |
| --- | --- | --- | --- |
| random pixel | 0.8432 | 0.916 | 0.8781 |
| held-out site | 0.8378 | 0.900 | 0.8672 |
| held-out region | 0.8319 | 0.883 | 0.8484 |
| Gujarat pixels, at the validation class mix | 0.8957 | 0.678 | 0.7715 |
| Gujarat pixels, as they are | 0.0033 | 0.678 | 0.0065 |

Site level, by the frozen rule: 16 of 17 sites found (94.1%).

## 2. Feature ablation

`logistic_regression` retrained with the same settings on each feature set, held out region folds:

| feature set | features | precision | recall | f1 | f1_sd | f1_min_fold | f1_change_vs_A0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A0 all twelve | 12 | 0.832 | 0.883 | 0.848 | 0.037 | 0.795 | +0.000 |
| A1 NDVI, NDBI, LST | 3 | 0.627 | 0.729 | 0.611 | 0.221 | 0.172 | -0.238 |
| A2 A1 + BSI | 4 | 0.715 | 0.787 | 0.725 | 0.067 | 0.627 | -0.124 |
| A3 original ten (no BSI, B2) | 10 | 0.804 | 0.856 | 0.819 | 0.027 | 0.785 | -0.029 |
| A4 no thermal | 10 | 0.759 | 0.835 | 0.779 | 0.041 | 0.729 | -0.069 |
| A5 no terrain | 10 | 0.824 | 0.890 | 0.848 | 0.028 | 0.815 | +0.000 |

## 3. Precision against prevalence

Validation rates: 0.890 of landfill points flagged, 0.0510 of random background points (pooled over the held-out rounds; 0.129 of all non-landfill points, look-alikes included). Gujarat rates: 0.678 and 0.0544.

| landfill share | true alarms per million px (validation rates) | false alarms per million px (validation rates) | precision (validation rates) | precision (Gujarat rates) |
| --- | --- | --- | --- | --- |
| 1 in 2 | 445019 | 25493 | 94.58% | 92.57% |
| 1 in 10 | 89004 | 45887 | 65.98% | 58.05% |
| 1 in 100 | 8900 | 50476 | 14.99% | 11.17% |
| 1 in 1,000 | 890 | 50935 | 1.72% | 1.23% |
| 1 in 10,000 | 89 | 50980 | 0.17% | 0.12% |

Measured in Gujarat: 21,139 flagged pixels inside the sealed outlines out of 6,501,765 flagged in all, a pixel precision of 0.33% against the sealed list. This is a lower bound: flagged land outside the list may include dumps that are not on it.

## 4. Threshold sensitivity on Gujarat

Post hoc. The frozen threshold is 0.5; the other rows change no reported result. The rows are counted from score maps rounded to 0.01, so each flags about 2% more land than an exact count; the exact figures at 0.5 are in sections 1 and 3.

| threshold | sites found (half the outline) | sites | median share of outline flagged | outline pixels flagged | other land flagged | km2 flagged |
| --- | --- | --- | --- | --- | --- | --- |
| 0.3 | 17 | 17 | 0.883 | 0.826 | 0.1284 | 1532 |
| 0.4 | 17 | 17 | 0.834 | 0.761 | 0.0840 | 1002 |
| 0.5 | 16 | 17 | 0.750 | 0.682 | 0.0555 | 664 |
| 0.6 | 16 | 17 | 0.700 | 0.593 | 0.0364 | 435 |
| 0.7 | 10 | 17 | 0.574 | 0.486 | 0.0230 | 276 |
| 0.8 | 7 | 17 | 0.414 | 0.366 | 0.0134 | 161 |
| 0.9 | 2 | 17 | 0.154 | 0.216 | 0.0065 | 78 |

## 5. Failure audit

Held-out false alarms of the frozen model, by class:

| class | points | flagged | rate |
| --- | --- | --- | --- |
| ash_pond | 960 | 190 | 19.8% |
| bare_soil | 480 | 187 | 39.0% |
| quarry | 360 | 153 | 42.5% |
| random | 3805 | 194 | 5.1% |

By held-out region:

| region | look-alike points flagged | random points flagged | landfill points flagged |
| --- | --- | --- | --- |
| Central | 0.216 | 0.039 | 0.954 |
| Eastern | 0.310 | 0.031 | 0.974 |
| North-Eastern |  | 0.069 | 0.705 |
| Northern | 0.278 | 0.038 | 0.780 |
| Southern | 0.248 | 0.105 | 0.951 |
| Western | 0.480 | 0.058 | 0.935 |

Random background points flagged, the five highest states:

| state_iso | points | rate |
| --- | --- | --- |
| IN-KA | 150 | 15.3% |
| IN-TG | 50 | 14.0% |
| IN-AS | 69 | 11.6% |
| IN-TN | 147 | 11.6% |
| IN-UT | 99 | 10.1% |

Training places judged by the Gujarat rule while held out: 6 of 86 have fewer than half their points flagged. The lowest:

| group_id | state_iso | points | share_flagged |
| --- | --- | --- | --- |
| g0416 | IN-LA | 50 | 0.00 |
| ex0030 | IN-HR | 50 | 0.02 |
| ex0075 | IN-UP | 21 | 0.14 |
| g0343 | IN-PY | 13 | 0.23 |
| ex0060 | IN-MH | 50 | 0.34 |
| ex0072 | IN-TR | 50 | 0.46 |
| ex0029 | IN-PB | 48 | 0.52 |
| ex0014 | IN-AS | 19 | 0.53 |

Gujarat land flagged, by city box:

| city | pixels_scored | share_flagged |
| --- | --- | --- |
| bhavnagar | 9146195 | 12.36% |
| ahmedabad | 10696170 | 8.14% |
| surat | 12020171 | 6.82% |
| vapi | 7812379 | 6.06% |
| jamnagar | 8817160 | 5.52% |
| mehsana | 9299394 | 5.40% |
| rajkot | 9492497 | 4.18% |
| vadodara | 12144928 | 4.06% |
| dwarka | 5669441 | 4.03% |
| gandhinagar | 9140362 | 3.64% |
| nadiad | 6010285 | 3.29% |
| anand | 9214188 | 3.23% |
| bhuj | 9681360 | 2.81% |

Sealed Gujarat sites, lowest flagged share first:

| test_id | city | area_ha | share_flagged | max_score | status |
| --- | --- | --- | --- | --- | --- |
| RAJ-01 | Rajkot | 30.2 | 0.46 | 0.955 | missed |
| SUR-02 | Surat | 107.5 | 0.60 | 0.999 | found |
| VAD-02 | Vadodara | 8.5 | 0.63 | 0.990 | found |
| SUR-01 | Surat | 2.3 | 0.64 | 0.944 | found |
| AHM-02 | Ahmedabad | 19.2 | 0.66 | 0.997 | found |
| AHM-01 | Ahmedabad | 47.5 | 0.66 | 0.992 | found |
| GNR-01 | Gandhinagar | 17.0 | 0.66 | 0.994 | found |
| Anand-01 | Anand | 2.5 | 0.73 | 0.976 | found |
| VAP-01 | Vapi | 2.0 | 0.75 | 0.979 | found |
| VAD-01 | Vadodara | 15.2 | 0.77 | 0.986 | found |
| AHM-03 | Ahmedabad | 8.6 | 0.84 | 0.971 | found |
| JAM-01 | Jamnagar | 3.3 | 0.84 | 0.972 | found |
| Nadiad-01 | Nadiad | 4.4 | 0.89 | 0.975 | found |
| BHJ-01 | Bhuj | 10.3 | 0.90 | 0.989 | found |
| MEH-01 | Mehsana | 5.1 | 0.92 | 0.984 | found |
| BHV-01 | Bhavnagar | 28.0 | 0.99 | 1.000 | found |
| Dwarka-01 | Dwarka | 1.1 | 0.99 | 0.974 | found |

