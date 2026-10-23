# Magnetic MLP, camera CNN and both, on the same frames and folds

MAE in the unit shown, mean over folds; nRMSE is the RMSE divided by the spread of the target.

| target | unit | magnetic MAE | magnetic nRMSE | camera MAE | camera nRMSE | camera+magnetic MAE | camera+magnetic nRMSE |
|---|---|---|---|---|---|---|---|
| plasma_current | kA | 1.47 | 0.035 | 14.6 | 0.364 | 2.3 | 0.056 |
| R_mag_axis | mm | 0.589 | 0.193 | 1.79 | 0.465 | 1.54 | 0.407 |
| Z_mag_axis | mm | 0.495 | 0.160 | 2.48 | 0.521 | 1.13 | 0.235 |
| elongation |  | 0.00771 | 0.063 | 0.016 | 0.122 | 0.0131 | 0.098 |
| triangularity |  | 0.00387 | 0.063 | 0.00895 | 0.159 | 0.0069 | 0.138 |
| triangularity_upper |  | 0.00345 | 0.096 | 0.00947 | 0.276 | 0.00644 | 0.191 |
| triangularity_lower |  | 0.00544 | 0.066 | 0.013 | 0.150 | 0.00975 | 0.128 |
| R_x_point | mm | 0.401 | 0.137 | 1.54 | 0.310 | 1.18 | 0.246 |
| Z_x_point | mm | 0.324 | 0.086 | 2.05 | 0.374 | 1.11 | 0.224 |
| R_strike_point_1 | mm | 0.266 | 0.052 | 2.27 | 0.343 | 0.912 | 0.173 |
| Z_strike_point_1 | mm | 0.133 | 0.063 | 0.78 | 0.302 | 0.366 | 0.164 |
| R_strike_point_2 | mm | 0.461 | 0.145 | 2.11 | 0.378 | 1.46 | 0.276 |
| Z_strike_point_2 | mm | 0.0943 | 0.155 | 0.421 | 0.386 | 0.297 | 0.285 |
| R_limiter | mm | 16.7 | 0.428 | 12.8 | 0.399 | 12.6 | 0.394 |
| Z_limiter | mm | 30.4 | 0.319 | 28.8 | 0.360 | 28 | 0.338 |
| is_limited |  | 0.0304 | 0.167 | 0.0531 | 0.265 | 0.0459 | 0.217 |

is_limited accuracy: magnetic 0.992, camera 0.976, camera+magnetic 0.987

Channels rgb; 14520 camera frames with interpolated magnetic inputs, 5 folds by discharge. The magnetic MLP is ipp1_common.fit_mlp (60 epochs) on these frames, so it is the like-for-like reference.
