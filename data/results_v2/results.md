# Validation results

34693 points (3865 landfill, 30828 other); 637 left out for missing features. Threshold 0.5.

Headline split: `held_out_region`, folds Central (6621 points), Eastern (5852 points), North-Eastern (1846 points), Northern (9192 points), Southern (5103 points), Western (6079 points).

Rule: best mean F1. Selected: **`random_forest`**.
Random forest out-of-bag accuracy on all points: 0.969.

## Mean and SD across folds

### held_out_region

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.383 | 0.076 | 0.548 | 0.232 | 0.413 | 0.138 |
| recalibrated_rule | 0.363 | 0.225 | 0.569 | 0.290 | 0.430 | 0.226 |
| logistic_regression | 0.552 | 0.109 | 0.900 | 0.099 | 0.675 | 0.081 |
| decision_tree | 0.737 | 0.058 | 0.555 | 0.150 | 0.621 | 0.109 |
| bagged_trees | 0.848 | 0.059 | 0.588 | 0.183 | 0.679 | 0.145 |
| random_forest | 0.827 | 0.074 | 0.692 | 0.180 | 0.739 | 0.115 |
| adaboost | 0.573 | 0.082 | 0.876 | 0.087 | 0.686 | 0.057 |
| gradient_boosting | 0.646 | 0.095 | 0.876 | 0.096 | 0.737 | 0.069 |

### held_out_site

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.345 | 0.023 | 0.628 | 0.082 | 0.445 | 0.039 |
| recalibrated_rule | 0.374 | 0.038 | 0.630 | 0.209 | 0.463 | 0.076 |
| logistic_regression | 0.548 | 0.021 | 0.914 | 0.068 | 0.685 | 0.032 |
| decision_tree | 0.760 | 0.018 | 0.585 | 0.074 | 0.659 | 0.052 |
| bagged_trees | 0.863 | 0.018 | 0.626 | 0.072 | 0.724 | 0.051 |
| random_forest | 0.835 | 0.020 | 0.725 | 0.097 | 0.773 | 0.060 |
| adaboost | 0.555 | 0.019 | 0.889 | 0.046 | 0.683 | 0.023 |
| gradient_boosting | 0.663 | 0.027 | 0.886 | 0.076 | 0.758 | 0.036 |

### random_pixel

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.346 | 0.011 | 0.628 | 0.006 | 0.446 | 0.010 |
| recalibrated_rule | 0.399 | 0.010 | 0.659 | 0.051 | 0.497 | 0.015 |
| logistic_regression | 0.550 | 0.012 | 0.926 | 0.013 | 0.690 | 0.010 |
| decision_tree | 0.806 | 0.012 | 0.805 | 0.014 | 0.805 | 0.012 |
| bagged_trees | 0.895 | 0.018 | 0.842 | 0.010 | 0.868 | 0.009 |
| random_forest | 0.863 | 0.026 | 0.908 | 0.011 | 0.885 | 0.016 |
| adaboost | 0.563 | 0.011 | 0.918 | 0.017 | 0.698 | 0.008 |
| gradient_boosting | 0.667 | 0.016 | 0.948 | 0.013 | 0.783 | 0.013 |

## Per fold, held_out_region

| model | fold | n_landfill | n_other | precision | recall | f1 | lookalike_flagged | random_flagged | near_site_flagged |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | Central | 697 | 5924 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Eastern | 616 | 5236 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | North-Eastern | 176 | 1670 | 0.000 | 0.000 | 0.000 | nan | 0.000 | 0.000 |
| flag_nothing | Northern | 1148 | 8044 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Southern | 507 | 4596 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Western | 721 | 5358 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | Central | 697 | 5924 | 0.357 | 0.600 | 0.447 | 0.338 | 0.079 | 0.114 |
| published_rule | Eastern | 616 | 5236 | 0.509 | 0.614 | 0.557 | 0.295 | 0.024 | 0.054 |
| published_rule | North-Eastern | 176 | 1670 | 0.421 | 0.091 | 0.150 | nan | 0.023 | 0.012 |
| published_rule | Northern | 1148 | 8044 | 0.299 | 0.713 | 0.421 | 0.889 | 0.248 | 0.229 |
| published_rule | Southern | 507 | 4596 | 0.393 | 0.566 | 0.464 | 0.337 | 0.061 | 0.065 |
| published_rule | Western | 721 | 5358 | 0.321 | 0.706 | 0.441 | 0.463 | 0.162 | 0.190 |
| recalibrated_rule | Central | 697 | 5924 | 0.429 | 0.736 | 0.542 | 0.142 | 0.108 | 0.114 |
| recalibrated_rule | Eastern | 616 | 5236 | 0.695 | 0.601 | 0.645 | 0.095 | 0.015 | 0.027 |
| recalibrated_rule | North-Eastern | 176 | 1670 | 0.000 | 0.000 | 0.000 | nan | 0.011 | 0.003 |
| recalibrated_rule | Northern | 1148 | 8044 | 0.301 | 0.583 | 0.397 | 0.478 | 0.224 | 0.185 |
| recalibrated_rule | Southern | 507 | 4596 | 0.408 | 0.696 | 0.514 | 0.207 | 0.125 | 0.095 |
| recalibrated_rule | Western | 721 | 5358 | 0.348 | 0.798 | 0.485 | 0.410 | 0.169 | 0.192 |
| logistic_regression | Central | 697 | 5924 | 0.595 | 0.950 | 0.731 | 0.238 | 0.036 | 0.067 |
| logistic_regression | Eastern | 616 | 5236 | 0.602 | 0.981 | 0.746 | 0.329 | 0.031 | 0.058 |
| logistic_regression | North-Eastern | 176 | 1670 | 0.571 | 0.727 | 0.640 | nan | 0.063 | 0.057 |
| logistic_regression | Northern | 1148 | 8044 | 0.697 | 0.835 | 0.760 | 0.322 | 0.053 | 0.048 |
| logistic_regression | Southern | 507 | 4596 | 0.412 | 0.961 | 0.576 | 0.291 | 0.087 | 0.139 |
| logistic_regression | Western | 721 | 5358 | 0.434 | 0.946 | 0.595 | 0.543 | 0.071 | 0.155 |
| decision_tree | Central | 697 | 5924 | 0.777 | 0.631 | 0.697 | 0.042 | 0.007 | 0.021 |
| decision_tree | Eastern | 616 | 5236 | 0.762 | 0.724 | 0.743 | 0.067 | 0.028 | 0.022 |
| decision_tree | North-Eastern | 176 | 1670 | 0.757 | 0.301 | 0.431 | nan | 0.011 | 0.010 |
| decision_tree | Northern | 1148 | 8044 | 0.790 | 0.539 | 0.641 | 0.233 | 0.031 | 0.016 |
| decision_tree | Southern | 507 | 4596 | 0.704 | 0.487 | 0.576 | 0.050 | 0.006 | 0.021 |
| decision_tree | Western | 721 | 5358 | 0.635 | 0.648 | 0.641 | 0.090 | 0.036 | 0.050 |
| bagged_trees | Central | 697 | 5924 | 0.879 | 0.699 | 0.779 | 0.040 | 0.000 | 0.010 |
| bagged_trees | Eastern | 616 | 5236 | 0.909 | 0.747 | 0.820 | 0.036 | 0.006 | 0.006 |
| bagged_trees | North-Eastern | 176 | 1670 | 0.817 | 0.278 | 0.415 | nan | 0.017 | 0.005 |
| bagged_trees | Northern | 1148 | 8044 | 0.886 | 0.522 | 0.657 | 0.200 | 0.013 | 0.007 |
| bagged_trees | Southern | 507 | 4596 | 0.849 | 0.533 | 0.655 | 0.043 | 0.002 | 0.007 |
| bagged_trees | Western | 721 | 5358 | 0.745 | 0.750 | 0.748 | 0.043 | 0.015 | 0.037 |
| random_forest | Central | 697 | 5924 | 0.878 | 0.828 | 0.852 | 0.044 | 0.000 | 0.013 |
| random_forest | Eastern | 616 | 5236 | 0.877 | 0.836 | 0.856 | 0.064 | 0.006 | 0.010 |
| random_forest | North-Eastern | 176 | 1670 | 0.828 | 0.409 | 0.548 | nan | 0.017 | 0.008 |
| random_forest | Northern | 1148 | 8044 | 0.864 | 0.587 | 0.699 | 0.300 | 0.017 | 0.009 |
| random_forest | Southern | 507 | 4596 | 0.833 | 0.631 | 0.718 | 0.050 | 0.004 | 0.010 |
| random_forest | Western | 721 | 5358 | 0.682 | 0.859 | 0.760 | 0.053 | 0.021 | 0.059 |
| adaboost | Central | 697 | 5924 | 0.577 | 0.938 | 0.714 | 0.218 | 0.052 | 0.072 |
| adaboost | Eastern | 616 | 5236 | 0.633 | 0.938 | 0.756 | 0.174 | 0.047 | 0.055 |
| adaboost | North-Eastern | 176 | 1670 | 0.642 | 0.733 | 0.684 | nan | 0.034 | 0.044 |
| adaboost | Northern | 1148 | 8044 | 0.622 | 0.804 | 0.701 | 0.433 | 0.066 | 0.066 |
| adaboost | Southern | 507 | 4596 | 0.538 | 0.909 | 0.676 | 0.180 | 0.053 | 0.077 |
| adaboost | Western | 721 | 5358 | 0.426 | 0.931 | 0.584 | 0.453 | 0.111 | 0.159 |
| gradient_boosting | Central | 697 | 5924 | 0.680 | 0.944 | 0.790 | 0.091 | 0.016 | 0.054 |
| gradient_boosting | Eastern | 616 | 5236 | 0.705 | 0.964 | 0.815 | 0.148 | 0.034 | 0.039 |
| gradient_boosting | North-Eastern | 176 | 1670 | 0.626 | 0.733 | 0.675 | nan | 0.046 | 0.046 |
| gradient_boosting | Northern | 1148 | 8044 | 0.758 | 0.781 | 0.770 | 0.344 | 0.041 | 0.031 |
| gradient_boosting | Southern | 507 | 4596 | 0.621 | 0.895 | 0.733 | 0.124 | 0.034 | 0.054 |
| gradient_boosting | Western | 721 | 5358 | 0.483 | 0.939 | 0.638 | 0.260 | 0.058 | 0.139 |
