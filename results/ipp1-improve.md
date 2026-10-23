# IPP 1: improving the model (same protocol as the baseline)

5-fold GroupKFold by whole discharge, masked loss, `ipp1_common.score`, at least 60 epochs. Every number is the mean of the 5 held-out folds. `summary nRMSE` = mean nRMSE over the 14 targets without the limiter point (all targets except R_limiter and Z_limiter, is_limited included); the json also has the 13-target mean without is_limited. `all-16 nRMSE` adds the two limiter targets (mean over all 16); tables are sorted by it. Latency = end-to-end `predict` of one raw sample (features, standardisation, forward pass, de-standardisation), median in ms, measured on a shared, loaded machine (use it for ranking, not as a guarantee); gated rows are timed on a limited sample, i.e. both models run. Latency limit used for the recommendation: 0.2 ms.

`plain` = trained on the clean training discharges. `aug` = trained on the clean rows plus one corrupted copy (noise 0.15, drift 0.15 of the training input SD, the augmentation of `ipp1_robustness.py`), same number of epochs over twice the rows. Both are tested on the clean file and on the provided noisy file (same held-out discharges).

## Held-out clean data

| configuration | training | summary nRMSE | all-16 nRMSE | R_limiter MAE mm | Z_limiter MAE mm | R_mag_axis MAE mm | Z_mag_axis MAE mm | latency ms/sample |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| base | aug | 0.1933 | 0.2221 | 16.62 | 27.32 | 1.905 | 1.241 | 0.0626 |
| combo_diff / net + ridge Ip + limiter net | plain | 0.0671 | 0.0832 | 5.73 | 11.66 | 0.323 | 0.308 | 0.1775 |
| deep | plain | 0.0716 | 0.0906 | 6.62 | 13.41 | 0.400 | 0.386 | 0.0943 |
| gate_nn / all limited targets from specialist | plain | 0.0680 | 0.0919 | 8.83 | 16.86 | 0.412 | 0.354 | 0.1199 |
| combo_diff / net + ridge Ip | plain | 0.0671 | 0.0922 | 8.84 | 17.79 | 0.323 | 0.308 | 0.0791 |
| combo_diff / net + ridge Ip + limiter LightGBM | plain | 0.0671 | 0.0923 | 7.44 | 11.09 | 0.323 | 0.308 | 0.4338 |
| gate_nn / limiter point from specialist | plain | 0.0690 | 0.0928 | 8.83 | 16.86 | 0.377 | 0.391 | 0.1272 |
| combo_diff / net | plain | 0.0692 | 0.0940 | 8.84 | 17.79 | 0.323 | 0.308 | 0.0752 |
| diff | plain | 0.0692 | 0.0940 | 8.84 | 17.79 | 0.323 | 0.308 | 0.0512 |
| ens3 | plain | 0.0665 | 0.0956 | 10.78 | 20.40 | 0.365 | 0.325 | 0.1826 |
| huber | plain | 0.0664 | 0.0963 | 10.37 | 19.71 | 0.361 | 0.385 | 0.0598 |
| base | plain | 0.0690 | 0.0971 | 10.73 | 22.19 | 0.377 | 0.391 | 0.0238 |
| base_mine | plain | 0.0690 | 0.0971 | 10.73 | 22.19 | 0.377 | 0.391 | 0.0477 |
| gate_nn / general only | plain | 0.0690 | 0.0971 | 10.73 | 22.19 | 0.377 | 0.391 | 0.0456 |
| wd1e-2 | plain | 0.0692 | 0.0979 | 11.09 | 22.37 | 0.386 | 0.397 | 0.0586 |
| wide | plain | 0.0711 | 0.0989 | 10.44 | 19.58 | 0.364 | 0.373 | 0.0685 |
| lin | plain | 0.0708 | 0.1001 | 11.80 | 22.20 | 0.370 | 0.407 | 0.0271 |
| weights | plain | 0.0773 | 0.1030 | 10.45 | 19.49 | 0.386 | 0.368 | 0.0574 |
| resid | plain | 0.0942 | 0.1207 | 13.24 | 21.43 | 0.698 | 0.439 | 0.0615 |

## Held-out provided noisy data

| configuration | training | summary nRMSE | all-16 nRMSE | R_limiter MAE mm | Z_limiter MAE mm | R_mag_axis MAE mm | Z_mag_axis MAE mm | latency ms/sample |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| base | aug | 0.2744 | 0.3099 | 23.30 | 38.76 | 2.776 | 2.152 | 0.0626 |
| ens3 | plain | 0.4570 | 0.5145 | 45.39 | 58.59 | 10.150 | 3.992 | 0.1826 |
| deep | plain | 0.4571 | 0.5167 | 43.69 | 52.72 | 9.560 | 3.867 | 0.0943 |
| huber | plain | 0.4641 | 0.5179 | 40.98 | 59.39 | 10.038 | 4.220 | 0.0598 |
| wd1e-2 | plain | 0.4628 | 0.5211 | 46.76 | 62.05 | 10.118 | 4.113 | 0.0586 |
| wide | plain | 0.4585 | 0.5216 | 49.22 | 59.15 | 10.065 | 3.903 | 0.0685 |
| base | plain | 0.4646 | 0.5231 | 46.82 | 62.62 | 10.150 | 4.119 | 0.0238 |
| base_mine | plain | 0.4646 | 0.5231 | 46.82 | 62.62 | 10.150 | 4.119 | 0.0477 |
| gate_nn / general only | plain | 0.4646 | 0.5231 | 46.82 | 62.62 | 10.150 | 4.119 | 0.0456 |
| gate_nn / limiter point from specialist | plain | 0.4646 | 0.5286 | 47.72 | 58.72 | 10.150 | 4.119 | 0.1272 |
| weights | plain | 0.4668 | 0.5293 | 49.55 | 61.78 | 10.065 | 4.047 | 0.0574 |
| lin | plain | 0.4709 | 0.5296 | 49.99 | 62.53 | 10.139 | 4.199 | 0.0271 |
| gate_nn / all limited targets from specialist | plain | 0.4683 | 0.5318 | 47.72 | 58.72 | 10.511 | 4.037 | 0.1199 |
| resid | plain | 1.7846 | 1.8618 | 157.69 | 307.63 | 27.358 | 16.777 | 0.0615 |
| combo_diff / net + ridge Ip + limiter LightGBM | plain | 9.5623 | 9.2128 | 479.72 | 381.98 | 112.841 | 208.308 | 0.4338 |
| combo_diff / net + ridge Ip | plain | 9.5623 | 10.1396 | 1250.17 | 1018.45 | 112.841 | 208.308 | 0.0791 |
| combo_diff / net | plain | 9.8975 | 10.4329 | 1250.17 | 1018.45 | 112.841 | 208.308 | 0.0752 |
| diff | plain | 9.8975 | 10.4329 | 1250.17 | 1018.45 | 112.841 | 208.308 | 0.0512 |
| combo_diff / net + ridge Ip + limiter net | plain | 9.5623 | 10.5275 | 1542.63 | 1216.70 | 112.841 | 208.308 | 0.1775 |

## Recommendation (latency within the limit, ranked by the all-16 nRMSE)

- trained on clean data, best on clean test: **combo_diff / net + ridge Ip + limiter net** (neighbour-difference features; ridge for plasma current; limited-row specialist (network or LightGBM) for the limiter point); summary nRMSE clean 0.0671, noisy 9.5623 (all-16 clean 0.0832, noisy 10.5275), latency 0.1775 ms.
- trained on clean data, best on noisy test: **ens3** (ensemble of 3 seeds, baseline recipe); summary nRMSE clean 0.0665, noisy 0.4570 (all-16 clean 0.0956, noisy 0.5145), latency 0.1826 ms.
- trained with noise plus drift augmentation, best on clean test: **base** (baseline: ipp1_common.fit_mlp, 256-256-128, 60 epochs); summary nRMSE clean 0.1933, noisy 0.2744 (all-16 clean 0.2221, noisy 0.3099), latency 0.0626 ms.
- trained with noise plus drift augmentation, best on noisy test: **base** (baseline: ipp1_common.fit_mlp, 256-256-128, 60 epochs); summary nRMSE clean 0.1933, noisy 0.2744 (all-16 clean 0.2221, noisy 0.3099), latency 0.0626 ms.

## Per-target: combo_diff / net + ridge Ip + limiter net (plain) against the baseline recipe (plain), clean test

| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.488 | 0.03455 | -98 % | 0.0271 | 0.0004 | 5 |
| R_mag_axis | mm | 0.3772 | 0.323 | -14 % | 0.1394 | 0.1437 | 4 |
| Z_mag_axis | mm | 0.3915 | 0.3081 | -21 % | 0.1069 | 0.0950 | 5 |
| elongation |  | 0.00569 | 0.004832 | -15 % | 0.0408 | 0.0382 | 4 |
| triangularity |  | 0.002844 | 0.002401 | -16 % | 0.0483 | 0.0433 | 4 |
| triangularity_upper |  | 0.002966 | 0.002478 | -16 % | 0.0797 | 0.0692 | 5 |
| triangularity_lower |  | 0.003679 | 0.003214 | -13 % | 0.0440 | 0.0406 | 4 |
| R_x_point | mm | 0.2024 | 0.256 | +26 % | 0.0673 | 0.0825 | 1 |
| Z_x_point | mm | 0.1952 | 0.209 | +7 % | 0.0387 | 0.0408 | 2 |
| R_strike_point_1 | mm | 0.2646 | 0.2499 | -6 % | 0.0509 | 0.0487 | 5 |
| Z_strike_point_1 | mm | 0.1307 | 0.09618 | -26 % | 0.0666 | 0.0488 | 5 |
| R_strike_point_2 | mm | 0.2281 | 0.2627 | +15 % | 0.0447 | 0.0619 | 2 |
| Z_strike_point_2 | mm | 0.05517 | 0.05877 | +7 % | 0.0681 | 0.0842 | 3 |
| R_limiter | mm | 10.73 | 5.729 | -47 % | 0.3170 | 0.2131 | 5 |
| Z_limiter | mm | 22.19 | 11.66 | -47 % | 0.2702 | 0.1792 | 5 |
| is_limited |  | 0.02027 | 0.01841 | -9 % | 0.1440 | 0.1416 | 5 |

## Per-target: combo_diff / net + ridge Ip + limiter net (plain) against the baseline recipe (plain), provided noisy test

| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 6.01 | 4.399 | -27 % | 0.0740 | 0.0499 | 5 |
| R_mag_axis | mm | 10.15 | 112.8 | +1012 % | 1.9144 | 18.1825 | 0 |
| Z_mag_axis | mm | 4.119 | 208.3 | +4957 % | 0.4314 | 20.7067 | 0 |
| elongation |  | 0.03182 | 0.5359 | +1584 % | 0.1675 | 2.5977 | 0 |
| triangularity |  | 0.01824 | 0.5314 | +2813 % | 0.2178 | 5.9659 | 0 |
| triangularity_upper |  | 0.02582 | 0.8902 | +3348 % | 0.4885 | 15.2140 | 0 |
| triangularity_lower |  | 0.02289 | 0.5783 | +2426 % | 0.1911 | 4.4871 | 0 |
| R_x_point | mm | 4.401 | 22.01 | +400 % | 0.7184 | 3.8309 | 0 |
| Z_x_point | mm | 3.168 | 155.2 | +4798 % | 0.3324 | 17.9887 | 0 |
| R_strike_point_1 | mm | 3.317 | 124.1 | +3642 % | 0.3426 | 14.1854 | 0 |
| Z_strike_point_1 | mm | 1.256 | 21.93 | +1647 % | 0.3622 | 6.2705 | 0 |
| R_strike_point_2 | mm | 4.711 | 121.1 | +2470 % | 0.5353 | 14.7380 | 0 |
| Z_strike_point_2 | mm | 0.8991 | 9.727 | +982 % | 0.5098 | 5.7485 | 0 |
| R_limiter | mm | 46.82 | 1543 | +3195 % | 1.1828 | 23.6905 | 0 |
| Z_limiter | mm | 62.62 | 1217 | +1843 % | 0.6821 | 10.8763 | 0 |
| is_limited |  | 0.04148 | 1.445 | +3383 % | 0.2194 | 3.9069 | 0 |

## Per-target: base (aug) against the baseline recipe (aug), clean test

| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 2.004 | 2.004 | +0 % | 0.0321 | 0.0321 | 0 |
| R_mag_axis | mm | 1.905 | 1.905 | +0 % | 0.4754 | 0.4754 | 0 |
| Z_mag_axis | mm | 1.241 | 1.241 | +0 % | 0.2147 | 0.2147 | 0 |
| elongation |  | 0.01239 | 0.01239 | +0 % | 0.0823 | 0.0823 | 0 |
| triangularity |  | 0.00598 | 0.00598 | +0 % | 0.0925 | 0.0925 | 0 |
| triangularity_upper |  | 0.005991 | 0.005991 | +0 % | 0.1507 | 0.1507 | 0 |
| triangularity_lower |  | 0.008002 | 0.008002 | +0 % | 0.0879 | 0.0879 | 0 |
| R_x_point | mm | 1.523 | 1.523 | +0 % | 0.3451 | 0.3451 | 0 |
| Z_x_point | mm | 1.286 | 1.286 | +0 % | 0.1744 | 0.1744 | 0 |
| R_strike_point_1 | mm | 1.125 | 1.125 | +0 % | 0.1437 | 0.1437 | 0 |
| Z_strike_point_1 | mm | 0.4886 | 0.4886 | +0 % | 0.1966 | 0.1966 | 0 |
| R_strike_point_2 | mm | 1.816 | 1.816 | +0 % | 0.2876 | 0.2876 | 0 |
| Z_strike_point_2 | mm | 0.3462 | 0.3462 | +0 % | 0.2596 | 0.2596 | 0 |
| R_limiter | mm | 16.62 | 16.62 | +0 % | 0.4824 | 0.4824 | 0 |
| Z_limiter | mm | 27.32 | 27.32 | +0 % | 0.3649 | 0.3649 | 0 |
| is_limited |  | 0.02414 | 0.02414 | +0 % | 0.1642 | 0.1642 | 0 |

## Per-target: base (aug) against the baseline recipe (aug), provided noisy test

| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 4.702 | 4.702 | +0 % | 0.0574 | 0.0574 | 0 |
| R_mag_axis | mm | 2.776 | 2.776 | +0 % | 0.6857 | 0.6857 | 0 |
| Z_mag_axis | mm | 2.152 | 2.152 | +0 % | 0.2896 | 0.2896 | 0 |
| elongation |  | 0.02025 | 0.02025 | +0 % | 0.1226 | 0.1226 | 0 |
| triangularity |  | 0.01035 | 0.01035 | +0 % | 0.1365 | 0.1365 | 0 |
| triangularity_upper |  | 0.01036 | 0.01036 | +0 % | 0.2251 | 0.2251 | 0 |
| triangularity_lower |  | 0.014 | 0.014 | +0 % | 0.1278 | 0.1278 | 0 |
| R_x_point | mm | 2.44 | 2.44 | +0 % | 0.4569 | 0.4569 | 0 |
| Z_x_point | mm | 2.319 | 2.319 | +0 % | 0.2684 | 0.2684 | 0 |
| R_strike_point_1 | mm | 2.288 | 2.288 | +0 % | 0.2491 | 0.2491 | 0 |
| Z_strike_point_1 | mm | 0.9075 | 0.9075 | +0 % | 0.2887 | 0.2887 | 0 |
| R_strike_point_2 | mm | 2.933 | 2.933 | +0 % | 0.3838 | 0.3838 | 0 |
| Z_strike_point_2 | mm | 0.557 | 0.557 | +0 % | 0.3510 | 0.3510 | 0 |
| R_limiter | mm | 23.3 | 23.3 | +0 % | 0.6286 | 0.6286 | 0 |
| Z_limiter | mm | 38.76 | 38.76 | +0 % | 0.4880 | 0.4880 | 0 |
| is_limited |  | 0.03269 | 0.03269 | +0 % | 0.1985 | 0.1985 | 0 |
