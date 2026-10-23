# Camera CNN: colour against grey

MAE in the unit shown, mean over folds; nRMSE is the RMSE divided by the spread of the target.

| target | unit | rgb MAE | rgb nRMSE | grey MAE | grey nRMSE |
|---|---|---|---|---|---|
| plasma_current | kA | 14.6 | 0.364 | 14 | 0.356 |
| R_mag_axis | mm | 1.79 | 0.465 | 1.7 | 0.447 |
| Z_mag_axis | mm | 2.48 | 0.521 | 2.4 | 0.489 |
| elongation |  | 0.016 | 0.122 | 0.0162 | 0.122 |
| triangularity |  | 0.00895 | 0.159 | 0.00855 | 0.147 |
| triangularity_upper |  | 0.00947 | 0.276 | 0.00891 | 0.250 |
| triangularity_lower |  | 0.013 | 0.150 | 0.0125 | 0.143 |
| R_x_point | mm | 1.54 | 0.310 | 1.5 | 0.310 |
| Z_x_point | mm | 2.05 | 0.374 | 2.18 | 0.395 |
| R_strike_point_1 | mm | 2.27 | 0.343 | 2.25 | 0.336 |
| Z_strike_point_1 | mm | 0.78 | 0.302 | 0.787 | 0.304 |
| R_strike_point_2 | mm | 2.11 | 0.378 | 2.18 | 0.406 |
| Z_strike_point_2 | mm | 0.421 | 0.386 | 0.416 | 0.386 |
| R_limiter | mm | 12.8 | 0.399 | 13.1 | 0.409 |
| Z_limiter | mm | 28.8 | 0.360 | 28.7 | 0.349 |
| is_limited |  | 0.0531 | 0.265 | 0.0519 | 0.265 |

is_limited accuracy: rgb 0.976, grey 0.975

14520 frames, 78 discharges, 5 folds by discharge, 12 epochs, image 48x64, width 16.
Training seconds per fold: rgb 160, grey 164.
