# Error against the uneven distribution of the data (REQ-007)

Pooled over the 42,972 out-of-fold rows of 149 discharges (`out/ipp1-predictions.csv (analysis/out_of_fold.py, 5 folds by discharge)`); no model is trained here. 44.2% of the rows are limited, 16 of 149 discharges have positive plasma current (7.4% of the rows), 926 rows lie in the first 2 % and 925 in the last 2 % of the relative discharge time.

All errors are absolute errors in the report unit of the target. `rows` is the group's share of the rows of that target and `sq err` its share of that target's total squared error: where `sq err` is far above `rows`, a minority of the data carries the error. Metrics follow `common.score_extended` (the script asserts this on the full row set), so they are comparable with the other reports. `n/a` means the group has no row of that target, which is expected: the X-point and the strike points exist only in diverted rows, the limiter point only in limited rows.

## Overall, for reference

| target | unit | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 | n |
|---|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 1.49 | 0.747 | 3.39 | 4.38 | 15.9 | 91.4 | 0.0297 | 0.9991 | 42,971 |
| R_mag_axis | mm | 0.377 | 0.153 | 1.25 | 1.21 | 3.74 | 64.3 | 0.156 | 0.9757 | 42,972 |
| Z_mag_axis | mm | 0.391 | 0.18 | 1.71 | 1.33 | 3.55 | 284 | 0.125 | 0.9845 | 42,972 |
| elongation |  | 0.00569 | 0.00301 | 0.0116 | 0.0188 | 0.044 | 0.493 | 0.0429 | 0.9982 | 42,971 |
| triangularity |  | 0.00284 | 0.00145 | 0.00617 | 0.00935 | 0.0253 | 0.306 | 0.0517 | 0.9973 | 42,971 |
| triangularity_upper |  | 0.00297 | 0.00171 | 0.0062 | 0.009 | 0.0306 | 0.338 | 0.0828 | 0.9931 | 42,971 |
| triangularity_lower |  | 0.00368 | 0.00176 | 0.00822 | 0.0121 | 0.0293 | 0.305 | 0.0477 | 0.9977 | 42,971 |
| R_x_point | mm | 0.203 | 0.0755 | 0.624 | 0.615 | 3.15 | 20.5 | 0.0774 | 0.994 | 23,960 |
| Z_x_point | mm | 0.195 | 0.0866 | 0.519 | 0.593 | 2.81 | 7.83 | 0.0407 | 0.9983 | 23,960 |
| R_strike_point_1 | mm | 0.265 | 0.112 | 0.819 | 0.754 | 3.55 | 15.1 | 0.0653 | 0.9957 | 23,949 |
| Z_strike_point_1 | mm | 0.131 | 0.05 | 0.411 | 0.38 | 2.19 | 7.71 | 0.0816 | 0.9933 | 23,949 |
| R_strike_point_2 | mm | 0.23 | 0.106 | 0.562 | 0.755 | 2.49 | 20.6 | 0.0478 | 0.9977 | 23,949 |
| Z_strike_point_2 | mm | 0.0557 | 0.0253 | 0.168 | 0.166 | 0.551 | 6.81 | 0.0705 | 0.995 | 23,949 |
| R_limiter | mm | 10.8 | 2.64 | 28.5 | 49 | 145 | 378 | 0.318 | 0.8988 | 19,012 |
| Z_limiter | mm | 22.3 | 9.32 | 41.9 | 90.9 | 171 | 512 | 0.273 | 0.9253 | 19,012 |
| is_limited |  | 0.0203 | 0.00522 | 0.0717 | 0.0636 | 0.415 | 0.957 | 0.144 | 0.9792 | 42,972 |

## By configuration (limited against diverted)

Split by the truth of `is_limited`. The limited rows are the minority and the harder case.

| target | unit | MAE limited | p99 limited | rows limited | sq err limited | MAE diverted | p99 diverted | rows diverted | sq err diverted |
|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 2.01 | 26 | 44.2% | 77.9% | 1.07 | 9.42 | 55.8% | 22.1% |
| R_mag_axis | mm | 0.553 | 6.71 | 44.2% | 91.9% | 0.237 | 2.29 | 55.8% | 8.1% |
| Z_mag_axis | mm | 0.516 | 4.87 | 44.2% | 94.3% | 0.293 | 2.43 | 55.8% | 5.7% |
| elongation |  | 0.00815 | 0.0573 | 44.2% | 80.4% | 0.00373 | 0.0294 | 55.8% | 19.6% |
| triangularity |  | 0.00415 | 0.0331 | 44.2% | 84.1% | 0.0018 | 0.0121 | 55.8% | 15.9% |
| triangularity_upper |  | 0.0035 | 0.0352 | 44.2% | 66.4% | 0.00254 | 0.027 | 55.8% | 33.6% |
| triangularity_lower |  | 0.00567 | 0.0489 | 44.2% | 86.8% | 0.0021 | 0.0126 | 55.8% | 13.2% |
| R_x_point | mm | n/a | n/a | n/a | n/a | 0.203 | 3.15 | 100.0% | 100.0% |
| Z_x_point | mm | n/a | n/a | n/a | n/a | 0.195 | 2.81 | 100.0% | 100.0% |
| R_strike_point_1 | mm | n/a | n/a | n/a | n/a | 0.265 | 3.55 | 100.0% | 100.0% |
| Z_strike_point_1 | mm | n/a | n/a | n/a | n/a | 0.131 | 2.19 | 100.0% | 100.0% |
| R_strike_point_2 | mm | n/a | n/a | n/a | n/a | 0.23 | 2.49 | 100.0% | 100.0% |
| Z_strike_point_2 | mm | n/a | n/a | n/a | n/a | 0.0557 | 0.551 | 100.0% | 100.0% |
| R_limiter | mm | 10.8 | 145 | 100.0% | 100.0% | n/a | n/a | n/a | n/a |
| Z_limiter | mm | 22.3 | 171 | 100.0% | 100.0% | n/a | n/a | n/a | n/a |
| is_limited |  | 0.024 | 0.466 | 44.2% | 49.3% | 0.0173 | 0.346 | 55.8% | 50.7% |

## By current polarity

Split by whole discharges on the sign of the mean true plasma current: 16 of 149 discharges are positive. The folds are not stratified on polarity, so these few discharges are also unevenly spread over the folds.

| target | unit | MAE positive current | p99 positive current | rows positive current | sq err positive current | MAE negative current | p99 negative current | rows negative current | sq err negative current |
|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 3.62 | 29.8 | 7.4% | 26.0% | 1.32 | 14.4 | 92.6% | 74.0% |
| R_mag_axis | mm | 1.73 | 19.9 | 7.4% | 77.8% | 0.269 | 2.41 | 92.6% | 22.2% |
| Z_mag_axis | mm | 1.38 | 12 | 7.4% | 86.6% | 0.312 | 2.57 | 92.6% | 13.4% |
| elongation |  | 0.0174 | 0.127 | 7.4% | 51.6% | 0.00475 | 0.0341 | 92.6% | 48.4% |
| triangularity |  | 0.00865 | 0.0707 | 7.4% | 53.7% | 0.00238 | 0.0186 | 92.6% | 46.3% |
| triangularity_upper |  | 0.00906 | 0.0627 | 7.4% | 51.4% | 0.00248 | 0.0176 | 92.6% | 48.6% |
| triangularity_lower |  | 0.00996 | 0.0981 | 7.4% | 46.0% | 0.00317 | 0.0263 | 92.6% | 54.0% |
| R_x_point | mm | 1.36 | 6.96 | 6.4% | 83.8% | 0.123 | 0.977 | 93.6% | 16.2% |
| Z_x_point | mm | 0.953 | 5.87 | 6.4% | 69.5% | 0.143 | 1.01 | 93.6% | 30.5% |
| R_strike_point_1 | mm | 1.48 | 9.12 | 6.4% | 81.4% | 0.181 | 1.57 | 93.6% | 18.6% |
| Z_strike_point_1 | mm | 0.721 | 5.85 | 6.4% | 75.9% | 0.0904 | 0.79 | 93.6% | 24.1% |
| R_strike_point_2 | mm | 0.954 | 4.92 | 6.4% | 59.3% | 0.18 | 1.48 | 93.6% | 40.7% |
| Z_strike_point_2 | mm | 0.238 | 1.29 | 6.4% | 42.1% | 0.0432 | 0.266 | 93.6% | 57.9% |
| R_limiter | mm | 21.8 | 179 | 8.6% | 18.1% | 9.76 | 137 | 91.4% | 81.9% |
| Z_limiter | mm | 32.7 | 317 | 8.6% | 17.9% | 21.3 | 163 | 91.4% | 82.1% |
| is_limited |  | 0.0562 | 0.57 | 7.4% | 20.4% | 0.0174 | 0.365 | 92.6% | 79.6% |

## By position in the discharge

The first and last 2 % of the relative time, against the middle. This is where the equilibrium reconstruction itself is least well defined.

| target | unit | MAE first 2 % | p99 first 2 % | rows first 2 % | sq err first 2 % | MAE middle 96 % | p99 middle 96 % | rows middle 96 % | sq err middle 96 % | MAE last 2 % | p99 last 2 % | rows last 2 % | sq err last 2 % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 1.92 | 8.07 | 2.2% | 1.3% | 1.43 | 15.5 | 95.7% | 84.7% | 3.59 | 35.5 | 2.2% | 14.0% |
| R_mag_axis | mm | 1.54 | 16.6 | 2.2% | 23.4% | 0.321 | 2.85 | 95.7% | 49.7% | 1.7 | 26 | 2.2% | 26.9% |
| Z_mag_axis | mm | 1.38 | 11.4 | 2.2% | 7.2% | 0.335 | 2.88 | 95.7% | 14.9% | 1.91 | 19.4 | 2.2% | 77.9% |
| elongation |  | 0.00773 | 0.0411 | 2.2% | 2.1% | 0.00543 | 0.0427 | 95.7% | 78.1% | 0.0151 | 0.153 | 2.2% | 19.8% |
| triangularity |  | 0.0039 | 0.0201 | 2.2% | 2.6% | 0.00269 | 0.0244 | 95.7% | 78.1% | 0.00846 | 0.0657 | 2.2% | 19.3% |
| triangularity_upper |  | 0.00331 | 0.0164 | 2.2% | 2.1% | 0.00286 | 0.0302 | 95.7% | 80.4% | 0.00749 | 0.0657 | 2.2% | 17.5% |
| triangularity_lower |  | 0.00564 | 0.0259 | 2.2% | 2.2% | 0.00345 | 0.0279 | 95.7% | 78.2% | 0.0118 | 0.118 | 2.2% | 19.6% |
| R_x_point | mm | n/a | n/a | n/a | n/a | 0.202 | 3.15 | 99.0% | 99.1% | 0.313 | 2.23 | 1.0% | 0.9% |
| Z_x_point | mm | n/a | n/a | n/a | n/a | 0.193 | 2.62 | 99.0% | 97.0% | 0.473 | 3.72 | 1.0% | 3.0% |
| R_strike_point_1 | mm | n/a | n/a | n/a | n/a | 0.262 | 3.52 | 99.0% | 98.7% | 0.561 | 4.1 | 1.0% | 1.3% |
| Z_strike_point_1 | mm | n/a | n/a | n/a | n/a | 0.129 | 2.17 | 99.0% | 98.3% | 0.294 | 2.2 | 1.0% | 1.7% |
| R_strike_point_2 | mm | n/a | n/a | n/a | n/a | 0.227 | 2.4 | 99.0% | 97.7% | 0.501 | 3.93 | 1.0% | 2.3% |
| Z_strike_point_2 | mm | n/a | n/a | n/a | n/a | 0.0553 | 0.549 | 99.0% | 99.0% | 0.0915 | 0.557 | 1.0% | 1.0% |
| R_limiter | mm | 52.6 | 240 | 4.9% | 40.5% | 8.28 | 103 | 91.5% | 51.9% | 18.2 | 187 | 3.7% | 7.6% |
| Z_limiter | mm | 14 | 58 | 4.9% | 1.1% | 22.8 | 176 | 91.5% | 95.9% | 18.7 | 155 | 3.7% | 3.0% |
| is_limited |  | 0.0118 | 0.0642 | 2.2% | 0.1% | 0.0203 | 0.422 | 95.7% | 96.9% | 0.0278 | 0.452 | 2.2% | 3.0% |

## By value quantile of the target

Quintiles of the TRUE value of each target, over the rows where that target exists. `range` is the quintile edge in the report unit. A target whose error grows towards one edge is a target whose rare values are predicted worse, which is the point of REQ-007. Shown for the 10 main targets; all 16 are in `out/ipp1-distribution.json`.

### plasma_current (kA)

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | -318.4 to -222.9 | 8,594 | 1.4 | 0.805 | 3.91 | 15 | 65.6 | 20.0% | 13.0% |
| Q2 | -222.9 to -210.3 | 8,594 | 0.819 | 0.525 | 2.38 | 4.28 | 19.2 | 20.0% | 3.1% |
| Q3 | -210.3 to -187.7 | 8,594 | 1.24 | 0.496 | 2.95 | 25.6 | 37.1 | 20.0% | 25.1% |
| Q4 | -187.7 to -105.7 | 8,594 | 1.71 | 0.963 | 4.43 | 18.1 | 91.4 | 20.0% | 26.8% |
| Q5 | -105.7 to 318.5 | 8,595 | 2.27 | 1.28 | 6.81 | 23 | 63.4 | 20.0% | 32.0% |

### R_mag_axis (mm)

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | 462.3 to 555.1 | 8,595 | 0.455 | 0.195 | 1.25 | 5.59 | 39.8 | 20.0% | 27.9% |
| Q2 | 555.1 to 559.9 | 8,594 | 0.31 | 0.148 | 0.94 | 2.27 | 32.9 | 20.0% | 17.6% |
| Q3 | 559.9 to 563.2 | 8,594 | 0.289 | 0.145 | 0.807 | 1.91 | 34.9 | 20.0% | 14.6% |
| Q4 | 563.2 to 566 | 8,594 | 0.228 | 0.111 | 0.759 | 2.15 | 8.69 | 20.0% | 3.2% |
| Q5 | 566 to 674.1 | 8,595 | 0.604 | 0.193 | 2.45 | 6.86 | 64.3 | 20.0% | 36.6% |

### Z_mag_axis (mm)

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | -197.9 to 4.056 | 8,595 | 0.537 | 0.174 | 2.24 | 5.51 | 51.2 | 20.0% | 18.4% |
| Q2 | 4.056 to 13.1 | 8,594 | 0.31 | 0.192 | 0.879 | 2.39 | 32.2 | 20.0% | 3.7% |
| Q3 | 13.1 to 17.88 | 8,594 | 0.32 | 0.175 | 1.25 | 2.17 | 6.88 | 20.0% | 2.0% |
| Q4 | 17.88 to 27.56 | 8,594 | 0.388 | 0.173 | 1.33 | 3.11 | 31.9 | 20.0% | 7.7% |
| Q5 | 27.56 to 143.1 | 8,595 | 0.402 | 0.188 | 1.2 | 3.44 | 284 | 20.0% | 68.2% |

### elongation

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | 0.8865 to 1.336 | 8,594 | 0.00678 | 0.00342 | 0.0223 | 0.0609 | 0.493 | 20.0% | 33.4% |
| Q2 | 1.336 to 1.751 | 8,594 | 0.00954 | 0.00551 | 0.0323 | 0.0668 | 0.177 | 20.0% | 43.4% |
| Q3 | 1.751 to 1.787 | 8,594 | 0.00478 | 0.00206 | 0.0185 | 0.0409 | 0.102 | 20.0% | 13.6% |
| Q4 | 1.787 to 1.806 | 8,594 | 0.00309 | 0.00223 | 0.00885 | 0.0156 | 0.0572 | 20.0% | 3.1% |
| Q5 | 1.806 to 1.894 | 8,595 | 0.00425 | 0.00289 | 0.0127 | 0.0268 | 0.0624 | 20.0% | 6.6% |

### triangularity

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | -0.05206 to 0.1991 | 8,594 | 0.00391 | 0.0021 | 0.0137 | 0.0297 | 0.306 | 20.0% | 33.0% |
| Q2 | 0.1991 to 0.3516 | 8,594 | 0.00393 | 0.0022 | 0.0133 | 0.0274 | 0.107 | 20.0% | 28.8% |
| Q3 | 0.3516 to 0.3668 | 8,594 | 0.00163 | 0.00101 | 0.0051 | 0.00975 | 0.0924 | 20.0% | 6.0% |
| Q4 | 0.3668 to 0.3845 | 8,594 | 0.00166 | 0.00111 | 0.00466 | 0.00946 | 0.0698 | 20.0% | 5.2% |
| Q5 | 0.3845 to 0.5275 | 8,595 | 0.00307 | 0.00138 | 0.0102 | 0.0296 | 0.103 | 20.0% | 27.0% |

### R_x_point (mm)

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | 410 to 456.9 | 4,792 | 0.33 | 0.098 | 1.41 | 3.92 | 20.5 | 20.0% | 52.7% |
| Q2 | 456.9 to 463.2 | 4,791 | 0.226 | 0.0804 | 0.682 | 3.15 | 4.8 | 20.0% | 18.5% |
| Q3 | 463.2 to 466.9 | 4,793 | 0.181 | 0.0811 | 0.436 | 3.78 | 4.75 | 20.0% | 14.4% |
| Q4 | 466.9 to 469.5 | 4,792 | 0.127 | 0.0539 | 0.342 | 3.28 | 4.8 | 20.0% | 9.4% |
| Q5 | 469.5 to 482.8 | 4,792 | 0.15 | 0.0684 | 0.496 | 1.75 | 1.9 | 20.0% | 5.1% |

### Z_x_point (mm)

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | -357.9 to -338.1 | 4,792 | 0.186 | 0.0924 | 0.595 | 1.48 | 5.32 | 20.0% | 11.4% |
| Q2 | -338.1 to -331.9 | 4,792 | 0.185 | 0.125 | 0.491 | 1.15 | 7.13 | 20.0% | 10.4% |
| Q3 | -331.9 to -328 | 4,792 | 0.153 | 0.0756 | 0.374 | 1.35 | 7.79 | 20.0% | 16.5% |
| Q4 | -328 to -316.6 | 4,792 | 0.301 | 0.0877 | 1.38 | 4.38 | 7.83 | 20.0% | 48.5% |
| Q5 | -316.6 to -280.2 | 4,792 | 0.153 | 0.0644 | 0.517 | 1.14 | 6.42 | 20.0% | 13.2% |

### R_strike_point_1 (mm)

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | 393.7 to 420.4 | 4,790 | 0.227 | 0.0826 | 0.617 | 2.3 | 15.1 | 20.0% | 21.9% |
| Q2 | 420.4 to 430 | 4,790 | 0.338 | 0.112 | 0.584 | 7.57 | 9.4 | 20.0% | 40.8% |
| Q3 | 430 to 437.9 | 4,789 | 0.348 | 0.138 | 0.982 | 6.9 | 8.35 | 20.0% | 28.7% |
| Q4 | 437.9 to 444.8 | 4,790 | 0.189 | 0.111 | 0.537 | 1.21 | 6.14 | 20.0% | 3.7% |
| Q5 | 444.8 to 476.4 | 4,790 | 0.222 | 0.126 | 0.759 | 1.64 | 5.69 | 20.0% | 4.9% |

### R_limiter (mm)

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | n/a | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Q2 | n/a | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Q3 | n/a | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Q4 | 347 to 447.4 | 15,101 | 7.37 | 2.05 | 28.8 | 102 | 356 | 79.4% | 41.4% |
| Q5 | 447.4 to 771.5 | 3,911 | 24.1 | 7.47 | 109 | 210 | 378 | 20.6% | 58.6% |

### Z_limiter (mm)

| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | -358 to -312.2 | 3,379 | 24.2 | 10.2 | 100 | 176 | 313 | 17.8% | 19.3% |
| Q2 | -312.2 to -76.43 | 4,058 | 34.7 | 24 | 95.8 | 146 | 297 | 21.3% | 28.9% |
| Q3 | -76.43 to 1.886e-08 | 2,570 | 13.1 | 8.3 | 38.9 | 83.4 | 131 | 13.5% | 3.2% |
| Q4 | 1.886e-08 to 7.333 | 4,213 | 4.81 | 2.52 | 16.2 | 31.6 | 139 | 22.2% | 1.3% |
| Q5 | 7.333 to 327.9 | 4,792 | 30.6 | 13.3 | 115 | 245 | 512 | 25.2% | 47.3% |

## Limits (state these in the talk)

- The headline MAE is an average over two very different regimes. The limited rows are 44.2% of the rows and carry 91.9% of the squared error of the radial axis (0.553 against 0.237 mm diverted).
- The 16 discharges with positive plasma current are 7.4% of the rows and carry 77.8% of it (1.73 against 0.269 mm). A shape absent from training is not handled.
- The worst localised weakness is the limiter point at the START of a discharge: `R_limiter` is 52.6 mm in the first 2 % against 8.28 mm in the middle, which is 40.5% of its squared error on 4.9% of its rows.
- The end of a discharge is the other edge: `Z_mag_axis` puts 77.9% of its squared error into the last 2 % of the rows, and `R_mag_axis` 26.9%.
- Rare target values are predicted worse at BOTH edges, not just one: the outer quintiles of `R_mag_axis` are 0.455 and 0.604 mm against 0.228 mm in the best quintile.
- These are out-of-fold rows of randomly held-out discharges. This file says nothing about a new campaign or regime; the discharge ids are chronological, so GroupKFold is the optimistic protocol.
- This file MEASURES the uneven distribution. It does not respond to it: no stratified folds and no reweighting were applied here.

