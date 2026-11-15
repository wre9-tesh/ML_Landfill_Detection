# Validation results

34345 points (3853 landfill, 30492 other); 985 left out for missing features. Threshold 0.5.

Headline split: `held_out_region`, folds Central (6621 points), Eastern (5852 points), North-Eastern (1846 points), Northern (9192 points), Southern (4755 points), Western (6079 points).

Rule: best mean F1. Selected: **`gradient_boosting`**.
Random forest out-of-bag accuracy on all points: 0.975.

## Mean and SD across folds

### held_out_region

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.388 | 0.078 | 0.546 | 0.232 | 0.415 | 0.139 |
| recalibrated_rule | 0.381 | 0.184 | 0.582 | 0.296 | 0.434 | 0.223 |
| logistic_regression | 0.585 | 0.123 | 0.903 | 0.099 | 0.697 | 0.071 |
| decision_tree | 0.749 | 0.055 | 0.554 | 0.156 | 0.625 | 0.109 |
| bagged_trees | 0.874 | 0.060 | 0.584 | 0.176 | 0.684 | 0.123 |
| random_forest | 0.848 | 0.078 | 0.673 | 0.174 | 0.736 | 0.106 |
| adaboost | 0.602 | 0.071 | 0.884 | 0.097 | 0.710 | 0.041 |
| gradient_boosting | 0.694 | 0.088 | 0.865 | 0.096 | 0.762 | 0.044 |

### held_out_site

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.347 | 0.037 | 0.626 | 0.090 | 0.446 | 0.052 |
| recalibrated_rule | 0.377 | 0.026 | 0.641 | 0.218 | 0.466 | 0.076 |
| logistic_regression | 0.580 | 0.012 | 0.914 | 0.087 | 0.708 | 0.022 |
| decision_tree | 0.776 | 0.043 | 0.562 | 0.092 | 0.650 | 0.073 |
| bagged_trees | 0.880 | 0.032 | 0.618 | 0.108 | 0.722 | 0.080 |
| random_forest | 0.868 | 0.033 | 0.705 | 0.108 | 0.775 | 0.072 |
| adaboost | 0.604 | 0.021 | 0.897 | 0.048 | 0.721 | 0.016 |
| gradient_boosting | 0.702 | 0.026 | 0.891 | 0.061 | 0.784 | 0.024 |

### random_pixel

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.348 | 0.006 | 0.626 | 0.007 | 0.448 | 0.005 |
| recalibrated_rule | 0.398 | 0.015 | 0.660 | 0.045 | 0.496 | 0.010 |
| logistic_regression | 0.584 | 0.013 | 0.936 | 0.010 | 0.719 | 0.008 |
| decision_tree | 0.821 | 0.005 | 0.809 | 0.006 | 0.815 | 0.004 |
| bagged_trees | 0.912 | 0.009 | 0.855 | 0.009 | 0.882 | 0.007 |
| random_forest | 0.894 | 0.011 | 0.921 | 0.015 | 0.907 | 0.011 |
| adaboost | 0.603 | 0.009 | 0.915 | 0.013 | 0.727 | 0.007 |
| gradient_boosting | 0.708 | 0.006 | 0.960 | 0.011 | 0.815 | 0.007 |

## Per fold, held_out_region

| model | fold | n_landfill | n_other | precision | recall | f1 | lookalike_flagged | random_flagged | near_site_flagged |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | Central | 697 | 5924 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Eastern | 616 | 5236 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | North-Eastern | 176 | 1670 | 0.000 | 0.000 | 0.000 | nan | 0.000 | 0.000 |
| flag_nothing | Northern | 1148 | 8044 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Southern | 495 | 4260 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Western | 721 | 5358 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | Central | 697 | 5924 | 0.357 | 0.600 | 0.447 | 0.338 | 0.079 | 0.114 |
| published_rule | Eastern | 616 | 5236 | 0.509 | 0.614 | 0.557 | 0.295 | 0.024 | 0.054 |
| published_rule | North-Eastern | 176 | 1670 | 0.421 | 0.091 | 0.150 | nan | 0.023 | 0.012 |
| published_rule | Northern | 1148 | 8044 | 0.299 | 0.713 | 0.421 | 0.889 | 0.248 | 0.229 |
| published_rule | Southern | 495 | 4260 | 0.419 | 0.556 | 0.477 | 0.303 | 0.067 | 0.062 |
| published_rule | Western | 721 | 5358 | 0.321 | 0.706 | 0.441 | 0.463 | 0.162 | 0.190 |
| recalibrated_rule | Central | 697 | 5924 | 0.404 | 0.793 | 0.536 | 0.187 | 0.122 | 0.135 |
| recalibrated_rule | Eastern | 616 | 5236 | 0.690 | 0.620 | 0.653 | 0.098 | 0.016 | 0.029 |
| recalibrated_rule | North-Eastern | 176 | 1670 | 0.125 | 0.006 | 0.011 | nan | 0.011 | 0.003 |
| recalibrated_rule | Northern | 1148 | 8044 | 0.300 | 0.582 | 0.396 | 0.478 | 0.224 | 0.185 |
| recalibrated_rule | Southern | 495 | 4260 | 0.418 | 0.689 | 0.521 | 0.188 | 0.135 | 0.097 |
| recalibrated_rule | Western | 721 | 5358 | 0.348 | 0.799 | 0.485 | 0.410 | 0.169 | 0.192 |
| logistic_regression | Central | 697 | 5924 | 0.615 | 0.954 | 0.748 | 0.247 | 0.028 | 0.060 |
| logistic_regression | Eastern | 616 | 5236 | 0.578 | 0.979 | 0.727 | 0.333 | 0.041 | 0.065 |
| logistic_regression | North-Eastern | 176 | 1670 | 0.672 | 0.756 | 0.711 | nan | 0.057 | 0.037 |
| logistic_regression | Northern | 1148 | 8044 | 0.754 | 0.800 | 0.776 | 0.322 | 0.029 | 0.035 |
| logistic_regression | Southern | 495 | 4260 | 0.438 | 0.984 | 0.606 | 0.177 | 0.095 | 0.150 |
| logistic_regression | Western | 721 | 5358 | 0.455 | 0.945 | 0.614 | 0.520 | 0.054 | 0.143 |
| decision_tree | Central | 697 | 5924 | 0.786 | 0.654 | 0.714 | 0.027 | 0.007 | 0.022 |
| decision_tree | Eastern | 616 | 5236 | 0.788 | 0.744 | 0.765 | 0.076 | 0.013 | 0.020 |
| decision_tree | North-Eastern | 176 | 1670 | 0.811 | 0.341 | 0.480 | nan | 0.006 | 0.009 |
| decision_tree | Northern | 1148 | 8044 | 0.729 | 0.451 | 0.557 | 0.189 | 0.028 | 0.021 |
| decision_tree | Southern | 495 | 4260 | 0.707 | 0.469 | 0.564 | 0.044 | 0.017 | 0.020 |
| decision_tree | Western | 721 | 5358 | 0.670 | 0.669 | 0.669 | 0.090 | 0.014 | 0.046 |
| bagged_trees | Central | 697 | 5924 | 0.917 | 0.667 | 0.772 | 0.024 | 0.000 | 0.006 |
| bagged_trees | Eastern | 616 | 5236 | 0.902 | 0.774 | 0.833 | 0.036 | 0.008 | 0.008 |
| bagged_trees | North-Eastern | 176 | 1670 | 0.913 | 0.358 | 0.514 | nan | 0.011 | 0.003 |
| bagged_trees | Northern | 1148 | 8044 | 0.886 | 0.494 | 0.634 | 0.222 | 0.009 | 0.006 |
| bagged_trees | Southern | 495 | 4260 | 0.870 | 0.446 | 0.590 | 0.031 | 0.006 | 0.005 |
| bagged_trees | Western | 721 | 5358 | 0.756 | 0.766 | 0.761 | 0.033 | 0.010 | 0.037 |
| random_forest | Central | 697 | 5924 | 0.896 | 0.803 | 0.847 | 0.029 | 0.000 | 0.011 |
| random_forest | Eastern | 616 | 5236 | 0.882 | 0.859 | 0.870 | 0.043 | 0.008 | 0.011 |
| random_forest | North-Eastern | 176 | 1670 | 0.874 | 0.472 | 0.613 | nan | 0.017 | 0.006 |
| random_forest | Northern | 1148 | 8044 | 0.892 | 0.558 | 0.687 | 0.233 | 0.009 | 0.007 |
| random_forest | Southern | 495 | 4260 | 0.854 | 0.521 | 0.647 | 0.027 | 0.002 | 0.009 |
| random_forest | Western | 721 | 5358 | 0.692 | 0.825 | 0.753 | 0.050 | 0.017 | 0.055 |
| adaboost | Central | 697 | 5924 | 0.597 | 0.934 | 0.729 | 0.222 | 0.031 | 0.066 |
| adaboost | Eastern | 616 | 5236 | 0.580 | 0.945 | 0.719 | 0.212 | 0.057 | 0.071 |
| adaboost | North-Eastern | 176 | 1670 | 0.670 | 0.705 | 0.687 | nan | 0.034 | 0.037 |
| adaboost | Northern | 1148 | 8044 | 0.679 | 0.839 | 0.751 | 0.444 | 0.057 | 0.051 |
| adaboost | Southern | 495 | 4260 | 0.602 | 0.945 | 0.736 | 0.117 | 0.041 | 0.071 |
| adaboost | Western | 721 | 5358 | 0.484 | 0.935 | 0.638 | 0.240 | 0.069 | 0.138 |
| gradient_boosting | Central | 697 | 5924 | 0.702 | 0.924 | 0.798 | 0.102 | 0.016 | 0.045 |
| gradient_boosting | Eastern | 616 | 5236 | 0.666 | 0.963 | 0.787 | 0.200 | 0.036 | 0.046 |
| gradient_boosting | North-Eastern | 176 | 1670 | 0.772 | 0.750 | 0.761 | nan | 0.034 | 0.022 |
| gradient_boosting | Northern | 1148 | 8044 | 0.765 | 0.742 | 0.754 | 0.389 | 0.041 | 0.026 |
| gradient_boosting | Southern | 495 | 4260 | 0.724 | 0.873 | 0.791 | 0.071 | 0.017 | 0.037 |
| gradient_boosting | Western | 721 | 5358 | 0.533 | 0.936 | 0.679 | 0.200 | 0.040 | 0.116 |
