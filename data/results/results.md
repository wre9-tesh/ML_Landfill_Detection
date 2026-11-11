# Validation results

9470 points (3865 landfill, 5605 other); 60 left out for missing features. Threshold 0.5.

Headline split: `held_out_region`, folds Central (1821 points), Eastern (1652 points), North-Eastern (350 points), Northern (2352 points), Southern (1553 points), Western (1742 points).

Best mean F1: `gradient_boosting`. Simplest model within one SD of it (F1 of 0.807 or more): **`logistic_regression`**.
Random forest out-of-bag accuracy on all points: 0.960.

## Mean and SD across folds

### held_out_region

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.690 | 0.075 | 0.548 | 0.232 | 0.571 | 0.205 |
| recalibrated_rule | 0.706 | 0.115 | 0.825 | 0.168 | 0.740 | 0.059 |
| logistic_regression | 0.832 | 0.080 | 0.883 | 0.112 | 0.848 | 0.037 |
| decision_tree | 0.871 | 0.036 | 0.749 | 0.134 | 0.797 | 0.069 |
| bagged_trees | 0.905 | 0.038 | 0.779 | 0.158 | 0.828 | 0.086 |
| random_forest | 0.911 | 0.033 | 0.797 | 0.169 | 0.840 | 0.097 |
| adaboost | 0.847 | 0.072 | 0.881 | 0.107 | 0.857 | 0.033 |
| gradient_boosting | 0.879 | 0.059 | 0.866 | 0.128 | 0.865 | 0.058 |

### held_out_site

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.673 | 0.029 | 0.628 | 0.082 | 0.648 | 0.053 |
| recalibrated_rule | 0.671 | 0.039 | 0.874 | 0.072 | 0.759 | 0.051 |
| logistic_regression | 0.838 | 0.041 | 0.900 | 0.068 | 0.867 | 0.049 |
| decision_tree | 0.883 | 0.030 | 0.776 | 0.098 | 0.823 | 0.057 |
| bagged_trees | 0.922 | 0.027 | 0.813 | 0.098 | 0.861 | 0.057 |
| random_forest | 0.924 | 0.028 | 0.832 | 0.084 | 0.873 | 0.048 |
| adaboost | 0.864 | 0.037 | 0.892 | 0.051 | 0.877 | 0.034 |
| gradient_boosting | 0.907 | 0.032 | 0.890 | 0.060 | 0.898 | 0.036 |

### random_pixel

| model | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std |
| --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | 0.674 | 0.009 | 0.628 | 0.020 | 0.650 | 0.010 |
| recalibrated_rule | 0.668 | 0.013 | 0.879 | 0.034 | 0.759 | 0.010 |
| logistic_regression | 0.843 | 0.008 | 0.916 | 0.011 | 0.878 | 0.006 |
| decision_tree | 0.901 | 0.017 | 0.911 | 0.005 | 0.906 | 0.008 |
| bagged_trees | 0.939 | 0.013 | 0.957 | 0.008 | 0.948 | 0.009 |
| random_forest | 0.936 | 0.010 | 0.959 | 0.005 | 0.948 | 0.005 |
| adaboost | 0.868 | 0.017 | 0.921 | 0.013 | 0.893 | 0.006 |
| gradient_boosting | 0.917 | 0.010 | 0.957 | 0.006 | 0.937 | 0.005 |

## Per fold, held_out_region

| model | fold | n_landfill | n_other | precision | recall | f1 | lookalike_flagged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| flag_nothing | Central | 697 | 1124 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Eastern | 616 | 1036 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | North-Eastern | 176 | 174 | 0.000 | 0.000 | 0.000 | nan |
| flag_nothing | Northern | 1148 | 1204 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Southern | 507 | 1046 | 0.000 | 0.000 | 0.000 | 0.000 |
| flag_nothing | Western | 721 | 1021 | 0.000 | 0.000 | 0.000 | 0.000 |
| published_rule | Central | 697 | 1124 | 0.671 | 0.600 | 0.633 | 0.338 |
| published_rule | Eastern | 616 | 1036 | 0.731 | 0.614 | 0.667 | 0.295 |
| published_rule | North-Eastern | 176 | 174 | 0.800 | 0.091 | 0.163 | nan |
| published_rule | Northern | 1148 | 1204 | 0.697 | 0.713 | 0.705 | 0.889 |
| published_rule | Southern | 507 | 1046 | 0.574 | 0.566 | 0.570 | 0.337 |
| published_rule | Western | 721 | 1021 | 0.665 | 0.706 | 0.685 | 0.463 |
| recalibrated_rule | Central | 697 | 1124 | 0.693 | 0.921 | 0.791 | 0.287 |
| recalibrated_rule | Eastern | 616 | 1036 | 0.710 | 0.896 | 0.793 | 0.438 |
| recalibrated_rule | North-Eastern | 176 | 174 | 0.926 | 0.494 | 0.644 | nan |
| recalibrated_rule | Northern | 1148 | 1204 | 0.675 | 0.850 | 0.753 | 0.900 |
| recalibrated_rule | Southern | 507 | 1046 | 0.598 | 0.830 | 0.695 | 0.328 |
| recalibrated_rule | Western | 721 | 1021 | 0.634 | 0.957 | 0.762 | 0.537 |
| logistic_regression | Central | 697 | 1124 | 0.844 | 0.954 | 0.896 | 0.216 |
| logistic_regression | Eastern | 616 | 1036 | 0.801 | 0.974 | 0.879 | 0.310 |
| logistic_regression | North-Eastern | 176 | 174 | 0.912 | 0.705 | 0.795 | nan |
| logistic_regression | Northern | 1148 | 1204 | 0.930 | 0.780 | 0.848 | 0.278 |
| logistic_regression | Southern | 507 | 1046 | 0.720 | 0.951 | 0.820 | 0.248 |
| logistic_regression | Western | 721 | 1021 | 0.784 | 0.935 | 0.853 | 0.480 |
| decision_tree | Central | 697 | 1124 | 0.873 | 0.776 | 0.822 | 0.109 |
| decision_tree | Eastern | 616 | 1036 | 0.848 | 0.896 | 0.871 | 0.140 |
| decision_tree | North-Eastern | 176 | 174 | 0.925 | 0.631 | 0.750 | nan |
| decision_tree | Northern | 1148 | 1204 | 0.902 | 0.560 | 0.691 | 0.289 |
| decision_tree | Southern | 507 | 1046 | 0.832 | 0.750 | 0.788 | 0.111 |
| decision_tree | Western | 721 | 1021 | 0.846 | 0.879 | 0.863 | 0.197 |
| bagged_trees | Central | 697 | 1124 | 0.933 | 0.841 | 0.885 | 0.073 |
| bagged_trees | Eastern | 616 | 1036 | 0.872 | 0.942 | 0.906 | 0.140 |
| bagged_trees | North-Eastern | 176 | 174 | 0.962 | 0.568 | 0.714 | nan |
| bagged_trees | Northern | 1148 | 1204 | 0.917 | 0.609 | 0.732 | 0.311 |
| bagged_trees | Southern | 507 | 1046 | 0.864 | 0.789 | 0.825 | 0.089 |
| bagged_trees | Western | 721 | 1021 | 0.882 | 0.926 | 0.904 | 0.140 |
| random_forest | Central | 697 | 1124 | 0.939 | 0.928 | 0.934 | 0.080 |
| random_forest | Eastern | 616 | 1036 | 0.885 | 0.937 | 0.910 | 0.131 |
| random_forest | North-Eastern | 176 | 174 | 0.960 | 0.545 | 0.696 | nan |
| random_forest | Northern | 1148 | 1204 | 0.916 | 0.639 | 0.753 | 0.311 |
| random_forest | Southern | 507 | 1046 | 0.879 | 0.805 | 0.840 | 0.085 |
| random_forest | Western | 721 | 1021 | 0.888 | 0.931 | 0.909 | 0.160 |
| adaboost | Central | 697 | 1124 | 0.866 | 0.948 | 0.905 | 0.156 |
| adaboost | Eastern | 616 | 1036 | 0.818 | 0.969 | 0.887 | 0.210 |
| adaboost | North-Eastern | 176 | 174 | 0.949 | 0.733 | 0.827 | nan |
| adaboost | Northern | 1148 | 1204 | 0.904 | 0.754 | 0.822 | 0.333 |
| adaboost | Southern | 507 | 1046 | 0.774 | 0.937 | 0.847 | 0.191 |
| adaboost | Western | 721 | 1021 | 0.772 | 0.947 | 0.851 | 0.407 |
| gradient_boosting | Central | 697 | 1124 | 0.919 | 0.947 | 0.933 | 0.098 |
| gradient_boosting | Eastern | 616 | 1036 | 0.878 | 0.972 | 0.923 | 0.133 |
| gradient_boosting | North-Eastern | 176 | 174 | 0.931 | 0.688 | 0.791 | nan |
| gradient_boosting | Northern | 1148 | 1204 | 0.928 | 0.716 | 0.808 | 0.289 |
| gradient_boosting | Southern | 507 | 1046 | 0.836 | 0.925 | 0.878 | 0.133 |
| gradient_boosting | Western | 721 | 1021 | 0.785 | 0.946 | 0.858 | 0.463 |
