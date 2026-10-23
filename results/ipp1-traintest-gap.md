# IPP 1: error on the training rows against the held-out rows

Script `analysis/ipp1_traintest_gap.py`. MAE per target (mm, plasma current in kA, shape numbers and `is_limited` dimensionless). **gap = held-out MAE / training MAE**; a value near 1 means the model is as good on unseen discharges as on the ones it trained on, a large value means it fits its training discharges much better than new ones.

- **Development**: the 5 group folds inside the 119 development discharges (about 95 training and 24 held-out discharges per fold), one seed (seed = fold). For each fold the model is trained once and scored on its own training rows and on its held-out rows; the table is the mean over the 5 folds of the pooled MAE of a fold.
- **Locked**: the models trained on all 119 development discharges (seed 0), scored on those 119 discharges (training) and on the 30 locked discharges (held out). Clean inputs throughout.
- Check: the held-out predictions of the retrained models differ from the cached ones of `ipp1_final.py` by at most 0 (raw units) over all ten models, so these are the same models.

## shipped candidate (`cand`)

| target | unit | dev train | dev held-out | gap | locked: train | locked: held-out | gap |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 0.03322 | 0.03324 | 1.0 | 0.03221 | 0.03465 | 1.1 |
| R_mag_axis | mm | 0.09513 | 0.2302 | 2.4 | 0.08704 | 0.1331 | 1.5 |
| Z_mag_axis | mm | 0.1211 | 0.3413 | 2.8 | 0.1092 | 0.1721 | 1.6 |
| elongation | - | 0.001853 | 0.003916 | 2.1 | 0.001754 | 0.002807 | 1.6 |
| triangularity | - | 0.001002 | 0.002159 | 2.2 | 0.0009383 | 0.001353 | 1.4 |
| triangularity_upper | - | 0.001262 | 0.002099 | 1.7 | 0.001212 | 0.001526 | 1.3 |
| triangularity_lower | - | 0.001354 | 0.002995 | 2.2 | 0.001271 | 0.00183 | 1.4 |
| R_x_point | mm | 0.06467 | 0.2094 | 3.2 | 0.06131 | 0.1153 | 1.9 |
| Z_x_point | mm | 0.0605 | 0.1952 | 3.2 | 0.05601 | 0.09686 | 1.7 |
| R_strike_point_1 | mm | 0.07078 | 0.2053 | 2.9 | 0.06596 | 0.108 | 1.6 |
| Z_strike_point_1 | mm | 0.03217 | 0.1159 | 3.6 | 0.02901 | 0.04591 | 1.6 |
| R_strike_point_2 | mm | 0.06622 | 0.2519 | 3.8 | 0.0651 | 0.1356 | 2.1 |
| Z_strike_point_2 | mm | 0.01652 | 0.04478 | 2.7 | 0.01501 | 0.02636 | 1.8 |
| R_limiter | mm | 3.064 | 4.618 | 1.5 | 2.866 | 4.549 | 1.6 |
| Z_limiter | mm | 7.465 | 11.75 | 1.6 | 6.688 | 8.348 | 1.2 |
| is_limited | - | 0.01032 | 0.01456 | 1.4 | 0.009756 | 0.01359 | 1.4 |

## baseline network (`base`)

| target | unit | dev train | dev held-out | gap | locked: train | locked: held-out | gap |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.093 | 1.508 | 1.4 | 1.053 | 1.199 | 1.1 |
| R_mag_axis | mm | 0.2743 | 0.4797 | 1.7 | 0.2577 | 0.3067 | 1.2 |
| Z_mag_axis | mm | 0.2853 | 0.4686 | 1.6 | 0.267 | 0.3213 | 1.2 |
| elongation | - | 0.004634 | 0.006532 | 1.4 | 0.004223 | 0.004446 | 1.1 |
| triangularity | - | 0.002201 | 0.00333 | 1.5 | 0.00208 | 0.00223 | 1.1 |
| triangularity_upper | - | 0.002309 | 0.003444 | 1.5 | 0.002234 | 0.002602 | 1.2 |
| triangularity_lower | - | 0.002908 | 0.004505 | 1.5 | 0.002717 | 0.002974 | 1.1 |
| R_x_point | mm | 0.1087 | 0.2524 | 2.3 | 0.1084 | 0.161 | 1.5 |
| Z_x_point | mm | 0.1347 | 0.2325 | 1.7 | 0.1327 | 0.1617 | 1.2 |
| R_strike_point_1 | mm | 0.1542 | 0.313 | 2.0 | 0.1626 | 0.2121 | 1.3 |
| Z_strike_point_1 | mm | 0.07143 | 0.1423 | 2.0 | 0.06893 | 0.09864 | 1.4 |
| R_strike_point_2 | mm | 0.1589 | 0.2904 | 1.8 | 0.1605 | 0.212 | 1.3 |
| Z_strike_point_2 | mm | 0.0384 | 0.07248 | 1.9 | 0.03495 | 0.04538 | 1.3 |
| R_limiter | mm | 9.194 | 13.9 | 1.5 | 8.12 | 10.62 | 1.3 |
| Z_limiter | mm | 18.85 | 23.05 | 1.2 | 18.95 | 22.48 | 1.2 |
| is_limited | - | 0.018 | 0.0214 | 1.2 | 0.01762 | 0.02182 | 1.2 |

Reading, shipped candidate: the development gap ranges from 1.0 (plasma_current) to 3.8 (R_strike_point_2); 4 of 16 targets have a gap of 3 or more (R_x_point, Z_x_point, Z_strike_point_1, R_strike_point_2).
Reading, baseline network: the development gap ranges from 1.2 (is_limited) to 2.3 (R_x_point); no target has a gap of 3 or more.
