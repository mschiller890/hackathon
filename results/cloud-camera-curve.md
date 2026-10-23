# Camera CNN: accuracy against the number of training discharges

MAE in the unit shown, mean over folds; nRMSE is the RMSE divided by the spread of the target.

| target | unit | fraction_0.05 MAE | fraction_0.05 nRMSE | fraction_0.1 MAE | fraction_0.1 nRMSE | fraction_0.25 MAE | fraction_0.25 nRMSE | fraction_0.5 MAE | fraction_0.5 nRMSE | fraction_1 MAE | fraction_1 nRMSE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 37.7 | 0.801 | 33.6 | 0.780 | 31.5 | 0.705 | 24.9 | 0.530 | 14.6 | 0.364 |
| R_mag_axis | mm | 4.89 | 1.168 | 3.89 | 0.892 | 2.74 | 0.647 | 2.35 | 0.573 | 1.79 | 0.465 |
| Z_mag_axis | mm | 5.69 | 0.878 | 5.3 | 0.896 | 4.22 | 0.736 | 3.33 | 0.626 | 2.48 | 0.521 |
| elongation |  | 0.0657 | 0.465 | 0.046 | 0.341 | 0.0346 | 0.264 | 0.0236 | 0.181 | 0.016 | 0.122 |
| triangularity |  | 0.0327 | 0.485 | 0.0229 | 0.372 | 0.0179 | 0.306 | 0.0122 | 0.209 | 0.00895 | 0.159 |
| triangularity_upper |  | 0.0266 | 0.610 | 0.0209 | 0.509 | 0.0167 | 0.431 | 0.0125 | 0.333 | 0.00947 | 0.276 |
| triangularity_lower |  | 0.0453 | 0.453 | 0.0336 | 0.354 | 0.0265 | 0.293 | 0.0189 | 0.209 | 0.013 | 0.150 |
| R_x_point | mm | 4.51 | 0.768 | 3.76 | 0.683 | 2.91 | 0.591 | 2.28 | 0.468 | 1.54 | 0.310 |
| Z_x_point | mm | 5.99 | 0.926 | 5.1 | 0.851 | 3.47 | 0.592 | 3.01 | 0.536 | 2.05 | 0.374 |
| R_strike_point_1 | mm | 6.67 | 0.824 | 5.24 | 0.697 | 3.91 | 0.516 | 3.31 | 0.472 | 2.27 | 0.343 |
| Z_strike_point_1 | mm | 2.61 | 0.856 | 2.07 | 0.731 | 1.41 | 0.526 | 1.17 | 0.439 | 0.78 | 0.302 |
| R_strike_point_2 | mm | 5.81 | 0.894 | 4.89 | 0.788 | 3.87 | 0.668 | 3.08 | 0.566 | 2.11 | 0.378 |
| Z_strike_point_2 | mm | 1.12 | 0.874 | 0.986 | 0.806 | 0.757 | 0.653 | 0.618 | 0.572 | 0.421 | 0.386 |
| R_limiter | mm | 46.4 | 0.957 | 32.3 | 0.686 | 23.4 | 0.568 | 16.8 | 0.485 | 12.8 | 0.399 |
| Z_limiter | mm | 69 | 0.635 | 60.1 | 0.593 | 44.6 | 0.471 | 38.6 | 0.437 | 28.8 | 0.360 |
| is_limited |  | 0.143 | 0.492 | 0.124 | 0.455 | 0.0912 | 0.358 | 0.0712 | 0.312 | 0.0531 | 0.265 |

is_limited accuracy: fraction_0.05 0.924, fraction_0.1 0.936, fraction_0.25 0.961, fraction_0.5 0.966, fraction_1 0.976

Channels rgb; fixed epochs (12), so small subsets get fewer updates. Training discharges (mean over folds): fraction_0.05 4, fraction_0.1 7, fraction_0.25 16, fraction_0.5 31, fraction_1 62.
