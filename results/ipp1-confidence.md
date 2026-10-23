# IPP 1: how accurate, and how certain, for every parameter

Script `analysis/ipp1_confidence.py`; nothing is trained, the out-of-fold predictions that already exist are read. MAE, median, p95 and p99 of the absolute error pooled over rows, in mm (plasma current in kA, shape numbers and squareness dimensionless). **95 % interval = percentile interval of the MAE from 1,000 resamples of whole discharges** (rows of one discharge are near copies, so resampling rows would give intervals that are too narrow). *Share of discharges under a tolerance* = the share of discharges whose mean absolute error for that target is below the stated tolerance (tight: 1 mm, 1 kA, 0.01; loose: 5 mm, 5 kA, 0.05).

**Which model is which.** The table of 31 targets is the **basic network's** (`ipp1_oof_full.py`: 5 random group folds over all 149 discharges; a masked MLP with 31 outputs, **with the plasma current taken from a ridge regression** (linear in the 24 inputs), not from the network): the shipped model predicts 16 of the 31 targets only. The second table is the shipped model (`cand`, 16 targets, no `is_limited` row) on the 119 development discharges (cross-validation inside them) and on the 30 locked discharges, side by side with the basic network trained on the same discharges. **The locked set is easier than development:** the mean relative error over the 16 targets is 35 % lower for the shipped model and 35 % lower for the basic network (0.0590 against 0.0912 and 0.0803 against 0.1228, `notebooks/09_final_model_locked_test.ipynb`), so quote the development column next to it. Both models were designed on all 149 discharges, so the locked column is a check, not clean evidence.

## 1. The basic network, all 31 targets (149 discharges, 5 random group folds)

| target | unit | rows | MAE | 95 % interval | median | p95 | p99 | share of discharges < tight | < loose |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| R_mag_axis | mm | 42972 | 0.421 | [0.35, 0.519] | 0.185 | 1.33 | 3.9 | 93 % (1) | 99 % (5) |
| Z_mag_axis | mm | 42972 | 0.424 | [0.356, 0.512] | 0.2 | 1.46 | 4.06 | 94 % (1) | 100 % (5) |
| is_limited | accuracy | 42972 | 99.25 % | [99.15, 99.35] % | | | | | |
| R_x_point | mm | 23960 | 0.278 | [0.175, 0.428] | 0.109 | 0.809 | 4.61 | 96 % (1) | 99 % (5) |
| Z_x_point | mm | 23960 | 0.252 | [0.198, 0.329] | 0.13 | 0.87 | 2.13 | 96 % (1) | 100 % (5) |
| R_strike_point_1 | mm | 23949 | 0.311 | [0.217, 0.459] | 0.134 | 0.892 | 4.84 | 96 % (1) | 99 % (5) |
| Z_strike_point_1 | mm | 23949 | 0.165 | [0.127, 0.213] | 0.0762 | 0.53 | 1.7 | 98 % (1) | 100 % (5) |
| R_strike_point_2 | mm | 23949 | 0.322 | [0.224, 0.471] | 0.135 | 0.949 | 4.14 | 98 % (1) | 100 % (5) |
| Z_strike_point_2 | mm | 23949 | 0.0729 | [0.0541, 0.0996] | 0.0324 | 0.238 | 0.759 | 100 % (1) | 100 % (5) |
| R_limiter | mm | 19012 | 11.6 | [10.4, 13.1] | 3.45 | 50.1 | 149 | 0 % (1) | 5 % (5) |
| Z_limiter | mm | 19012 | 21.4 | [19.7, 23.3] | 8.77 | 80.7 | 180 | 0 % (1) | 0 % (5) |
| elongation | - | 42971 | 0.0056 | [0.00475, 0.00676] | 0.00291 | 0.0194 | 0.0447 | 89 % (0.01) | 100 % (0.05) |
| triangularity | - | 42971 | 0.00283 | [0.0023, 0.00358] | 0.00142 | 0.00893 | 0.0269 | 95 % (0.01) | 100 % (0.05) |
| triangularity_lower | - | 42971 | 0.00388 | [0.00319, 0.00495] | 0.00185 | 0.0128 | 0.0365 | 94 % (0.01) | 99 % (0.05) |
| triangularity_upper | - | 42971 | 0.00284 | [0.00242, 0.00335] | 0.00168 | 0.00888 | 0.0232 | 96 % (0.01) | 100 % (0.05) |
| a | mm | 42971 | 0.443 | [0.377, 0.535] | 0.199 | 1.35 | 4.5 | 92 % (1) | 99 % (5) |
| plasma_current | kA | 42971 | 0.0346 | [0.0329, 0.0361] | 0.0261 | 0.0914 | 0.139 | 100 % (1) | 100 % (5) |
| R_geom | mm | 42972 | 0.395 | [0.324, 0.486] | 0.164 | 1.35 | 4.01 | 91 % (1) | 99 % (5) |
| Z_geom | mm | 42972 | 0.711 | [0.569, 0.951] | 0.334 | 2.22 | 6.55 | 85 % (1) | 99 % (5) |
| R_top | mm | 42972 | 0.717 | [0.574, 0.906] | 0.352 | 2.23 | 8.81 | 88 % (1) | 98 % (5) |
| Z_top | mm | 42972 | 1.07 | [0.928, 1.24] | 0.572 | 3.47 | 9.22 | 64 % (1) | 99 % (5) |
| R_bottom | mm | 42972 | 0.805 | [0.641, 1.06] | 0.357 | 2.53 | 9.38 | 83 % (1) | 98 % (5) |
| Z_bottom | mm | 42972 | 1.36 | [1.09, 1.82] | 0.562 | 4.55 | 13.2 | 56 % (1) | 97 % (5) |
| Z_outer | mm | 42972 | 0.562 | [0.471, 0.688] | 0.318 | 1.69 | 5.06 | 91 % (1) | 99 % (5) |
| R_outer | mm | 42972 | 0.545 | [0.458, 0.653] | 0.233 | 1.86 | 5.18 | 87 % (1) | 99 % (5) |
| Z_inner | mm | 42972 | 6.76 | [5.75, 8.13] | 2.11 | 30.5 | 82.9 | 0 % (1) | 47 % (5) |
| R_inner | mm | 42972 | 0.637 | [0.526, 0.781] | 0.258 | 2.11 | 8.86 | 86 % (1) | 97 % (5) |
| squareness_upper_outer | - | 42972 | 0.00107 | [0.000957, 0.00122] | 0.000714 | 0.00309 | 0.00756 | 100 % (0.01) | 100 % (0.05) |
| squareness_upper_inner | - | 42972 | 0.0104 | [0.00894, 0.0123] | 0.00337 | 0.048 | 0.12 | 63 % (0.01) | 99 % (0.05) |
| squareness_lower_outer | - | 42972 | 0.00308 | [0.00251, 0.00385] | 0.00143 | 0.011 | 0.0336 | 97 % (0.01) | 100 % (0.05) |
| squareness_lower_inner | - | 42972 | 0.0123 | [0.0102, 0.0149] | 0.00418 | 0.0542 | 0.156 | 58 % (0.01) | 99 % (0.05) |

## 2. The shipped model (`cand`) and the basic network of the same protocol: development cross-validation next to the 30 locked discharges

| target | unit | shipped, development: MAE [95 %] | shipped, locked 30: MAE [95 %] | basic, development | basic, locked | shipped: share of discharges < tight (dev / locked) | < loose (dev / locked) |
|---|---|---|---|---:|---:|---|---|
| plasma_current | kA | 0.0332 [0.0314, 0.0351] | 0.0347 [0.0311, 0.0385] | 1.51 | 1.2 | 100 % / 100 % (1) | 100 % / 100 % (5) |
| R_mag_axis | mm | 0.23 [0.171, 0.305] | 0.133 [0.1, 0.176] | 0.479 | 0.307 | 94 % / 100 % (1) | 100 % / 100 % (5) |
| Z_mag_axis | mm | 0.341 [0.209, 0.541] | 0.172 [0.131, 0.224] | 0.469 | 0.321 | 93 % / 100 % (1) | 99 % / 100 % (5) |
| elongation | - | 0.00392 [0.00284, 0.00527] | 0.00281 [0.002, 0.00381] | 0.00653 | 0.00445 | 94 % / 97 % (0.01) | 100 % / 100 % (0.05) |
| triangularity | - | 0.00216 [0.00153, 0.00297] | 0.00135 [0.000978, 0.00184] | 0.00333 | 0.00223 | 97 % / 100 % (0.01) | 100 % / 100 % (0.05) |
| triangularity_upper | - | 0.0021 [0.00167, 0.00266] | 0.00153 [0.00127, 0.00188] | 0.00344 | 0.0026 | 98 % / 100 % (0.01) | 100 % / 100 % (0.05) |
| triangularity_lower | - | 0.00299 [0.00209, 0.00424] | 0.00183 [0.00134, 0.00247] | 0.00451 | 0.00297 | 96 % / 100 % (0.01) | 100 % / 100 % (0.05) |
| R_x_point | mm | 0.211 [0.126, 0.345] | 0.115 [0.0741, 0.162] | 0.253 | 0.161 | 96 % / 97 % (1) | 100 % / 100 % (5) |
| Z_x_point | mm | 0.195 [0.112, 0.314] | 0.0969 [0.0668, 0.129] | 0.234 | 0.162 | 96 % / 100 % (1) | 100 % / 100 % (5) |
| R_strike_point_1 | mm | 0.206 [0.122, 0.341] | 0.108 [0.0777, 0.144] | 0.312 | 0.212 | 97 % / 100 % (1) | 99 % / 100 % (5) |
| Z_strike_point_1 | mm | 0.116 [0.0606, 0.215] | 0.0459 [0.0337, 0.0599] | 0.142 | 0.0986 | 99 % / 100 % (1) | 100 % / 100 % (5) |
| R_strike_point_2 | mm | 0.254 [0.132, 0.434] | 0.136 [0.0813, 0.201] | 0.291 | 0.212 | 95 % / 97 % (1) | 100 % / 100 % (5) |
| Z_strike_point_2 | mm | 0.0453 [0.0281, 0.0702] | 0.0264 [0.0184, 0.0351] | 0.0728 | 0.0454 | 100 % / 100 % (1) | 100 % / 100 % (5) |
| R_limiter | mm | 4.62 [3.74, 5.74] | 4.55 [3.34, 6.18] | 14 | 10.6 | 3 % / 0 % (1) | 77 % / 77 % (5) |
| Z_limiter | mm | 11.8 [9.17, 15.3] | 8.35 [6.89, 10.2] | 23 | 22.5 | 0 % / 0 % (1) | 11 % / 17 % (5) |

Protocol: shipped and basic network trained once (seed per fold, seed 0 for the locked set), clean inputs; the locked interval is wide because it rests on 30 discharges.

## 3. Slices: where the error lives (MAE in report units)

Rows are cut by the truth: reversed polarity = discharges with positive median plasma current (16 of 149 discharges, 14 of them in the development set, 2 in the locked set, so no locked column here); limited / diverted = the true `is_limited`; the first and last 2 % of the relative time of each discharge. A slice with at most 50 rows with the target is left empty.

### basic network, 149 discharges, 31-target table above

| target | all rows | negative plasma current (normal) | positive plasma current (reversed) | diverted rows | limited rows | first 2 % of the discharge | middle | last 2 % of the discharge |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current (kA) | 0.0346 | 0.034 | 0.0414 | 0.0352 | 0.0337 | 0.0247 | 0.0342 | 0.0583 |
| R_mag_axis (mm) | 0.421 | 0.309 | 1.82 | 0.289 | 0.588 | 1.65 | 0.359 | 1.97 |
| Z_mag_axis (mm) | 0.424 | 0.345 | 1.41 | 0.301 | 0.578 | 1.33 | 0.368 | 1.97 |
| elongation (-) | 0.0056 | 0.00453 | 0.019 | 0.00395 | 0.00768 | 0.009 | 0.00536 | 0.013 |
| R_x_point (mm) | 0.278 | 0.176 | 1.76 | 0.278 |  |  | 0.276 | 0.429 |
| R_strike_point_1 (mm) | 0.311 | 0.214 | 1.71 | 0.311 |  |  | 0.307 | 0.639 |
| R_limiter (mm) | 11.6 | 10.1 | 27.9 |  | 11.6 | 56 | 8.83 | 21.9 |
| Z_limiter (mm) | 21.4 | 20.2 | 34.2 |  | 21.4 | 14.9 | 21.9 | 18 |

### shipped model `cand`, 119 development discharges (cross-validation)

| target | all rows | negative plasma current (normal) | positive plasma current (reversed) | diverted rows | limited rows | first 2 % of the discharge | middle | last 2 % of the discharge |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current (kA) | 0.0332 | 0.0324 | 0.0439 | 0.0327 | 0.0339 | 0.0247 | 0.0329 | 0.0561 |
| R_mag_axis (mm) | 0.23 | 0.148 | 1.23 | 0.176 | 0.296 | 0.663 | 0.199 | 1.18 |
| Z_mag_axis (mm) | 0.341 | 0.224 | 1.77 | 0.261 | 0.439 | 0.528 | 0.303 | 1.85 |
| elongation (-) | 0.00392 | 0.0029 | 0.0163 | 0.00273 | 0.00535 | 0.00499 | 0.00365 | 0.0145 |
| R_x_point (mm) | 0.211 | 0.109 | 1.62 | 0.211 |  |  | 0.209 | 0.417 |
| R_strike_point_1 (mm) | 0.206 | 0.129 | 1.27 | 0.206 |  |  | 0.204 | 0.402 |
| R_limiter (mm) | 4.62 | 3.95 | 11.8 |  | 4.62 | 18.9 | 3.69 | 9.22 |
| Z_limiter (mm) | 11.8 | 10.6 | 24.2 |  | 11.8 | 8.07 | 11.9 | 14.5 |

**Limits.** No row of a tolerance share is a probability of a future discharge being that accurate: it is the share among these discharges, and a discharge counts as accurate on its mean error, not on its worst frame (see p99 and the last 2 %). The intervals say how much the MAE would move with another set of discharges drawn from the same data, not with another tokamak campaign (blocked split, `results/ipp1-final.md`, is 1.1 to 2.8 times worse). One network and one seed per cell; the baseline's 31-target numbers must not be read as the shipped model's.
