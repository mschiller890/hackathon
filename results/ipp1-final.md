# IPP 1: final evaluation on a locked test set

Locked test set: 30 discharges (8761 rows) drawn with numpy seed 20261024; ids in `results/ipp1-locked-test-ids.txt`. Development set: the other 119 discharges (34211 rows). Recipe choices use 5-fold GroupKFold inside the development set only; the locked set was scored once, with models trained on all development discharges. All metrics are pooled over the rows of the test set (not means of folds). Every model is one seed (seed noise of earlier runs: 8 to 19 %), so read differences below about 20 % between recipes as unresolved unless the bootstrap interval excludes 1.

Recipes: `baseline MLP` = common.fit_mlp, 60 epochs. `candidate` = network on 24 inputs + 22 neighbouring-coil differences (Huber 0.5, 150 epochs) + ridge for plasma_current + a limited-rows network for R_limiter and Z_limiter gated by the predicted is_limited. `augmented` = trained on the clean rows plus one copy with noise 0.15 and drift 0.15 of each input's SD (candidate: 75 epochs on twice the rows; baseline: 60 epochs on twice the rows, an extra control). `clean` = clean inputs, `noisy` = the provided noisy file (same rows).

## Which recipe to ship

- **clean inputs: candidate, plain** (`cand`): lowest mean nRMSE over the 16 targets in the development cross-validation (baseline MLP 0.1228, baseline MLP, augmented (extra) 0.2385, candidate, plain 0.0912, candidate, augmented 0.1705).
- **noisy inputs: baseline MLP, augmented (extra)** (`base_aug`): lowest mean nRMSE over the 16 targets in the development cross-validation (baseline MLP 0.5267, baseline MLP, augmented (extra) 0.3129, candidate, plain 12.4320, candidate, augmented 0.3321).
- Locked-set check of that choice: mean nRMSE over 16 targets, clean: baseline MLP 0.0803, baseline MLP, augmented (extra) 0.1998, candidate, plain 0.0590, candidate, augmented 0.1108; noisy: baseline MLP 0.4923, baseline MLP, augmented (extra) 0.2891, candidate, plain 12.0304, candidate, augmented 0.3159.

## Reading of the results (written by hand from the tables below)

**Ship, clean inputs: the candidate trained plain** (network with neighbouring-coil differences, ridge for the plasma current, gated limiter network).
It also had the lowest development cross-validation score before the locked set was looked at. On the locked set (30 discharges, 8,761 rows) against the baseline MLP,
pooled MAE: plasma_current 0.035 against 1.20 kA, R_mag_axis 0.133 against 0.307 mm, Z_mag_axis 0.172 against 0.321 mm, R_x_point 0.115 against 0.161 mm,
R_limiter 4.55 against 10.6 mm, Z_limiter 8.35 against 22.5 mm. The bootstrap interval of the MAE ratio excludes 1 for every headline target
(the weakest: R_x_point 0.72 [0.53, 0.97] and R_strike_point_2 0.64 [0.43, 0.94]). The gain is largest where the baseline was weakest (limiter point, plasma current).
**The tails do not improve everywhere.** The RMSE of R_x_point is 0.454 against 0.305 mm and of R_strike_point_2 0.638 against 0.401 mm (candidate worse), the worst row of
R_x_point is 10.1 against 2.76 mm, of R_strike_point_2 15.2 against 7.19 mm, of Z_limiter 485 against 369 mm. The median, p95 and p99 are lower for the candidate on all 11 headline targets; the RMSE is higher on two (R_x_point, R_strike_point_2) and the worst single row is larger on six (Z_mag_axis, R_x_point, Z_x_point, R_strike_point_2, R_limiter, Z_limiter). So say "better on average and in the bulk, with a few worse single rows", not "better everywhere".
The limiter point stays the weak target for both (p99 of R_limiter 77 mm for the candidate, 150 mm for the baseline).

**Ship, noisy inputs: the baseline MLP trained with noise plus drift augmentation (`base_aug`, an extra recipe added as the fair control).**
Reason: the plain candidate collapses on the provided noisy inputs (R_mag_axis MAE 190 mm against 9.2 mm for the plain baseline), because the neighbouring-coil
differences amplify the noise. With augmentation the candidate recovers, but is not better than the augmented baseline: development cross-validation mean nRMSE 0.3321
against 0.3129, locked 0.3159 against 0.2891; on the headline targets the two are within the bootstrap noise
(R_mag_axis 2.60 against 2.38 mm, R_x_point 2.71 against 2.47 mm). One exception that the data show: the plasma current. The ridge inside the augmented candidate gives
4.03 kA (p99 13.0, max 20.6) against 4.65 kA (p99 16.9, max 79.7) for the augmented baseline, with non-overlapping bootstrap intervals [3.96, 4.09] and [4.34, 5.05].
The two models predict each target independently, so taking the plasma current from the augmented candidate's ridge and everything else from `base_aug` would combine
these measured numbers; that combination itself was not run as one recipe. Against the plain baseline on noisy inputs the augmented baseline is much better
(R_mag_axis MAE 2.38 against 9.16 mm, ratio 0.26 [0.23, 0.30]).

**Price of robustness on clean inputs.** The augmented models are clearly worse on clean data than the plain ones (baseline: R_mag_axis 1.56 against 0.307 mm; candidate: 0.548
against 0.133 mm). The shipped pair therefore needs to know which kind of input it gets; there is no single model that wins in both cases.

**Random group folds are optimistic.** Blocked by id (train on the 60 lowest development ids, test on the 59 highest; ids are chronological) the clean-input MAE of the
plain baseline is 1.5 to 2.9 times that of random group folds on the same 59 discharges (R_mag_axis 1.23 against 0.448 mm, R_x_point 2.89 times, R_limiter 1.64 times);
the plain candidate is 1.07 to 2.8 times worse (R_mag_axis 0.397 against 0.216 mm, R_limiter 8.67 against 4.70 mm). Part of the gap is the smaller training set
(60 against about 95 discharges), which this experiment does not separate. On noisy inputs the blocked/random ratio is 0.87 to 1.09 for the plain baseline and 1.15 to 1.41 for the augmented baseline (the plain candidate is not meaningful on noisy inputs).
So a headline built on random group folds understates what a new campaign will see; quote the blocked numbers next to it.

**Limits of this evaluation.** One seed per model (earlier seed noise 8 to 19 %). Only 30 locked discharges, of which 2 have positive plasma current (591 rows) and 28 negative:
the polarity table says nothing reliable about reversed-polarity discharges (the review found them to carry most of the squared error); it needs a locked set with more of them.
The first and last 2 % of every discharge are 189 rows each; the end of the discharge is worse than the middle for all recipes (R_mag_axis candidate 0.578 mm against 0.114 mm in the middle).
No recipe was changed after the locked numbers were seen; the report step was run three times (a plumbing test with one-epoch networks, the full run, and a fix of the polarity grouping, which a NaN in one discharge had broken).

## Development set: pooled out-of-fold scores (5 group folds inside the 119 development discharges)

| recipe | inputs | mean nRMSE (16) | plasma_current MAE | R_mag_axis MAE | Z_mag_axis MAE | R_x_point MAE | Z_x_point MAE | R_strike_point_1 MAE | Z_strike_point_1 MAE | R_strike_point_2 MAE | Z_strike_point_2 MAE | R_limiter MAE | Z_limiter MAE |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline MLP | clean | 0.1228 | 1.51 | 0.479 | 0.469 | 0.253 | 0.234 | 0.312 | 0.142 | 0.291 | 0.0728 | 14 | 23 |
| baseline MLP | noisy | 0.5267 | 6.08 | 10.2 | 4.21 | 4.51 | 3.2 | 3.37 | 1.29 | 4.82 | 0.92 | 48.6 | 63 |
| baseline MLP, augmented (extra) | clean | 0.2385 | 2.14 | 2.21 | 1.34 | 1.69 | 1.42 | 1.31 | 0.557 | 1.98 | 0.365 | 17 | 28.9 |
| baseline MLP, augmented (extra) | noisy | 0.3129 | 4.77 | 2.99 | 2.27 | 2.43 | 2.38 | 2.38 | 0.945 | 2.94 | 0.554 | 22.7 | 39.3 |
| candidate, plain | clean | 0.0912 | 0.0332 | 0.23 | 0.341 | 0.211 | 0.195 | 0.206 | 0.116 | 0.254 | 0.0453 | 4.62 | 11.8 |
| candidate, plain | noisy | 12.4320 | 4.32 | 138 | 223 | 43.6 | 107 | 110 | 23.9 | 116 | 15.9 | 1.32e+03 | 1.18e+03 |
| candidate, augmented | clean | 0.1705 | 0.472 | 1.09 | 0.857 | 0.764 | 0.719 | 0.704 | 0.303 | 0.873 | 0.181 | 10.4 | 19.4 |
| candidate, augmented | noisy | 0.3321 | 4.03 | 3.09 | 2.36 | 2.57 | 2.59 | 2.61 | 1.02 | 3.1 | 0.596 | 22.2 | 41.8 |

Units: mm for R and Z targets, kA for plasma_current.

## Locked test, clean inputs: all metrics per target, pooled over 8761 rows

### baseline MLP, clean inputs (mean nRMSE over 16 targets 0.0803)

| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 8760 | 1.2 | 0.773 | 2.2 | 3.61 | 7.7 | 69.1 | 0.0188 | 1 |
| R_mag_axis | mm | 8761 | 0.307 | 0.156 | 0.75 | 0.932 | 2.51 | 17.9 | 0.0958 | 0.991 |
| Z_mag_axis | mm | 8761 | 0.321 | 0.193 | 0.887 | 0.797 | 2.24 | 35.3 | 0.0668 | 0.996 |
| elongation |  | 8760 | 0.00445 | 0.00261 | 0.00817 | 0.0137 | 0.0324 | 0.152 | 0.0318 | 0.999 |
| triangularity |  | 8760 | 0.00223 | 0.00147 | 0.00366 | 0.00649 | 0.0131 | 0.104 | 0.0319 | 0.999 |
| triangularity_upper |  | 8760 | 0.0026 | 0.0018 | 0.00416 | 0.00746 | 0.0166 | 0.114 | 0.0586 | 0.997 |
| triangularity_lower |  | 8760 | 0.00297 | 0.00176 | 0.0054 | 0.00949 | 0.0208 | 0.137 | 0.0324 | 0.999 |
| R_x_point | mm | 5207 | 0.161 | 0.0873 | 0.305 | 0.568 | 1.46 | 2.76 | 0.034 | 0.999 |
| Z_x_point | mm | 5207 | 0.162 | 0.101 | 0.258 | 0.49 | 0.906 | 4.42 | 0.0211 | 1 |
| R_strike_point_1 | mm | 5206 | 0.212 | 0.148 | 0.365 | 0.574 | 1.25 | 6.2 | 0.0288 | 0.999 |
| Z_strike_point_1 | mm | 5206 | 0.0986 | 0.051 | 0.211 | 0.3 | 0.982 | 4.14 | 0.0424 | 0.998 |
| R_strike_point_2 | mm | 5206 | 0.212 | 0.119 | 0.401 | 0.711 | 1.76 | 7.19 | 0.0332 | 0.999 |
| Z_strike_point_2 | mm | 5206 | 0.0454 | 0.0287 | 0.106 | 0.117 | 0.265 | 2.89 | 0.0448 | 0.998 |
| R_limiter | mm | 3554 | 10.6 | 2.26 | 29.1 | 43 | 150 | 306 | 0.314 | 0.901 |
| Z_limiter | mm | 3554 | 22.5 | 8.66 | 40.8 | 88.3 | 160 | 369 | 0.26 | 0.932 |
| is_limited |  | 8761 | 0.0218 | 0.00523 | 0.0836 | 0.0553 | 0.518 | 0.923 | 0.17 | 0.971 |

is_limited accuracy: 0.9892

### baseline MLP, augmented (extra), clean inputs (mean nRMSE over 16 targets 0.1998)

| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 8760 | 1.91 | 1.22 | 3.11 | 5.9 | 9.17 | 72 | 0.0267 | 0.999 |
| R_mag_axis | mm | 8761 | 1.56 | 0.825 | 2.86 | 5.35 | 10.6 | 62.6 | 0.366 | 0.866 |
| Z_mag_axis | mm | 8761 | 0.837 | 0.479 | 1.56 | 2.58 | 6.84 | 26.6 | 0.118 | 0.986 |
| elongation |  | 8760 | 0.0101 | 0.00525 | 0.0198 | 0.0325 | 0.0887 | 0.26 | 0.0769 | 0.994 |
| triangularity |  | 8760 | 0.00552 | 0.00308 | 0.0094 | 0.0185 | 0.0387 | 0.0847 | 0.0819 | 0.993 |
| triangularity_upper |  | 8760 | 0.00565 | 0.00322 | 0.0097 | 0.0192 | 0.0423 | 0.0827 | 0.136 | 0.981 |
| triangularity_lower |  | 8760 | 0.00712 | 0.00404 | 0.0122 | 0.023 | 0.0541 | 0.116 | 0.073 | 0.995 |
| R_x_point | mm | 5207 | 1.56 | 0.8 | 2.87 | 5.7 | 10.9 | 31.5 | 0.32 | 0.898 |
| Z_x_point | mm | 5207 | 1.11 | 0.683 | 1.84 | 3.31 | 8.57 | 17.1 | 0.15 | 0.977 |
| R_strike_point_1 | mm | 5206 | 1.14 | 0.658 | 1.97 | 3.99 | 9.24 | 17.3 | 0.156 | 0.976 |
| Z_strike_point_1 | mm | 5206 | 0.47 | 0.27 | 0.79 | 1.71 | 3.13 | 8.33 | 0.159 | 0.975 |
| R_strike_point_2 | mm | 5206 | 1.83 | 0.987 | 3.5 | 5.99 | 14.3 | 44.4 | 0.29 | 0.916 |
| Z_strike_point_2 | mm | 5206 | 0.312 | 0.188 | 0.493 | 0.952 | 1.78 | 5.39 | 0.208 | 0.957 |
| R_limiter | mm | 3554 | 18.6 | 4.54 | 47.6 | 89.7 | 236 | 420 | 0.513 | 0.737 |
| Z_limiter | mm | 3554 | 25.7 | 9.11 | 52.2 | 103 | 235 | 442 | 0.333 | 0.889 |
| is_limited |  | 8761 | 0.0253 | 0.00653 | 0.0935 | 0.069 | 0.545 | 1 | 0.19 | 0.964 |

is_limited accuracy: 0.9874

### candidate, plain, clean inputs (mean nRMSE over 16 targets 0.0590)

| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 8760 | 0.0347 | 0.0258 | 0.047 | 0.0982 | 0.143 | 0.398 | 0.000403 | 1 |
| R_mag_axis | mm | 8761 | 0.133 | 0.0614 | 0.374 | 0.403 | 1.39 | 15.1 | 0.0478 | 0.998 |
| Z_mag_axis | mm | 8761 | 0.172 | 0.0785 | 0.741 | 0.47 | 1.59 | 37.2 | 0.0558 | 0.997 |
| elongation |  | 8760 | 0.00281 | 0.00118 | 0.00699 | 0.0091 | 0.0333 | 0.132 | 0.0272 | 0.999 |
| triangularity |  | 8760 | 0.00135 | 0.000764 | 0.00344 | 0.0034 | 0.0145 | 0.0766 | 0.03 | 0.999 |
| triangularity_upper |  | 8760 | 0.00153 | 0.00116 | 0.0031 | 0.00326 | 0.0109 | 0.0886 | 0.0436 | 0.998 |
| triangularity_lower |  | 8760 | 0.00183 | 0.000824 | 0.00502 | 0.00528 | 0.0191 | 0.125 | 0.0302 | 0.999 |
| R_x_point | mm | 5207 | 0.115 | 0.0558 | 0.454 | 0.277 | 1.01 | 10.1 | 0.0506 | 0.997 |
| Z_x_point | mm | 5207 | 0.0969 | 0.0417 | 0.257 | 0.349 | 0.716 | 7.25 | 0.021 | 1 |
| R_strike_point_1 | mm | 5206 | 0.108 | 0.0546 | 0.219 | 0.39 | 1.03 | 2.77 | 0.0173 | 1 |
| Z_strike_point_1 | mm | 5206 | 0.0459 | 0.0211 | 0.11 | 0.161 | 0.461 | 2.9 | 0.0222 | 1 |
| R_strike_point_2 | mm | 5206 | 0.136 | 0.0522 | 0.638 | 0.357 | 1.2 | 15.2 | 0.0529 | 0.997 |
| Z_strike_point_2 | mm | 5206 | 0.0264 | 0.0117 | 0.1 | 0.0772 | 0.22 | 2.83 | 0.0424 | 0.998 |
| R_limiter | mm | 3554 | 4.55 | 0.733 | 19.4 | 17.2 | 77.5 | 357 | 0.209 | 0.956 |
| Z_limiter | mm | 3554 | 8.35 | 2.96 | 20.9 | 35.2 | 92.2 | 485 | 0.133 | 0.982 |
| is_limited |  | 8761 | 0.0136 | 0.00219 | 0.0784 | 0.0216 | 0.384 | 1.1 | 0.16 | 0.975 |

is_limited accuracy: 0.9916

### candidate, augmented, clean inputs (mean nRMSE over 16 targets 0.1108)

| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 8760 | 0.509 | 0.463 | 0.64 | 1.13 | 1.63 | 13.8 | 0.00548 | 1 |
| R_mag_axis | mm | 8761 | 0.548 | 0.246 | 1.25 | 2.05 | 4.64 | 33.5 | 0.16 | 0.974 |
| Z_mag_axis | mm | 8761 | 0.462 | 0.245 | 1.1 | 1.4 | 3.62 | 36.3 | 0.0832 | 0.993 |
| elongation |  | 8760 | 0.00614 | 0.00339 | 0.0112 | 0.0202 | 0.0463 | 0.157 | 0.0437 | 0.998 |
| triangularity |  | 8760 | 0.00279 | 0.00145 | 0.00555 | 0.00887 | 0.0251 | 0.108 | 0.0483 | 0.998 |
| triangularity_upper |  | 8760 | 0.00285 | 0.00183 | 0.00516 | 0.00801 | 0.0212 | 0.119 | 0.0726 | 0.995 |
| triangularity_lower |  | 8760 | 0.00392 | 0.0019 | 0.00785 | 0.0137 | 0.0351 | 0.168 | 0.0472 | 0.998 |
| R_x_point | mm | 5207 | 0.5 | 0.205 | 1.15 | 1.85 | 4.01 | 17.5 | 0.129 | 0.983 |
| Z_x_point | mm | 5207 | 0.426 | 0.214 | 0.875 | 1.59 | 3.69 | 10.2 | 0.0713 | 0.995 |
| R_strike_point_1 | mm | 5206 | 0.513 | 0.27 | 1.03 | 1.67 | 4.77 | 10.4 | 0.0817 | 0.993 |
| Z_strike_point_1 | mm | 5206 | 0.215 | 0.0974 | 0.421 | 0.822 | 1.95 | 3.73 | 0.0847 | 0.993 |
| R_strike_point_2 | mm | 5206 | 0.609 | 0.283 | 1.46 | 2.04 | 4.79 | 26.9 | 0.121 | 0.985 |
| Z_strike_point_2 | mm | 5206 | 0.116 | 0.0557 | 0.208 | 0.406 | 0.768 | 2.59 | 0.0879 | 0.992 |
| R_limiter | mm | 3554 | 9.47 | 1.97 | 29.9 | 35.9 | 165 | 348 | 0.323 | 0.896 |
| Z_limiter | mm | 3554 | 16.7 | 5.55 | 35.8 | 74.5 | 143 | 484 | 0.228 | 0.948 |
| is_limited |  | 8761 | 0.02 | 0.00458 | 0.0912 | 0.0377 | 0.57 | 1.03 | 0.186 | 0.966 |

is_limited accuracy: 0.9885

## Locked test, noisy inputs: all metrics per target, pooled over 8761 rows

### baseline MLP, noisy inputs (mean nRMSE over 16 targets 0.4923)

| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 8760 | 5.63 | 4.52 | 7.43 | 14.3 | 22.3 | 69.6 | 0.0637 | 0.996 |
| R_mag_axis | mm | 8761 | 9.16 | 6.59 | 13.6 | 25.6 | 50.5 | 131 | 1.73 | -2 |
| Z_mag_axis | mm | 8761 | 3.82 | 2.98 | 5.17 | 10 | 16.1 | 50.3 | 0.389 | 0.848 |
| elongation |  | 8760 | 0.0292 | 0.0207 | 0.0412 | 0.0869 | 0.14 | 0.303 | 0.16 | 0.974 |
| triangularity |  | 8760 | 0.0161 | 0.0115 | 0.0227 | 0.0481 | 0.0755 | 0.216 | 0.198 | 0.961 |
| triangularity_upper |  | 8760 | 0.024 | 0.0173 | 0.0339 | 0.0682 | 0.117 | 0.305 | 0.477 | 0.772 |
| triangularity_lower |  | 8760 | 0.0216 | 0.0154 | 0.0304 | 0.0635 | 0.102 | 0.252 | 0.182 | 0.967 |
| R_x_point | mm | 5207 | 4.35 | 3.46 | 5.64 | 11.5 | 16 | 35.3 | 0.628 | 0.606 |
| Z_x_point | mm | 5207 | 3.01 | 2.45 | 3.81 | 7.57 | 10.2 | 15.7 | 0.311 | 0.903 |
| R_strike_point_1 | mm | 5206 | 3.21 | 2.67 | 4.07 | 8.02 | 10.7 | 17 | 0.321 | 0.897 |
| Z_strike_point_1 | mm | 5206 | 1.22 | 0.827 | 1.74 | 3.73 | 5.64 | 9.8 | 0.349 | 0.878 |
| R_strike_point_2 | mm | 5206 | 4.63 | 3.64 | 6.09 | 12.2 | 17.7 | 42.9 | 0.504 | 0.746 |
| Z_strike_point_2 | mm | 5206 | 0.855 | 0.672 | 1.12 | 2.22 | 3.17 | 8.38 | 0.473 | 0.776 |
| R_limiter | mm | 3554 | 48.9 | 10.9 | 111 | 326 | 466 | 538 | 1.2 | -0.428 |
| Z_limiter | mm | 3554 | 62.3 | 33.5 | 105 | 220 | 463 | 672 | 0.667 | 0.555 |
| is_limited |  | 8761 | 0.0375 | 0.0139 | 0.11 | 0.102 | 0.649 | 1.07 | 0.225 | 0.95 |

is_limited accuracy: 0.9848

### baseline MLP, augmented (extra), noisy inputs (mean nRMSE over 16 targets 0.2891)

| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 8760 | 4.65 | 3.78 | 6.15 | 11.7 | 16.9 | 79.7 | 0.0527 | 0.997 |
| R_mag_axis | mm | 8761 | 2.38 | 1.35 | 4.7 | 7.16 | 16.3 | 90.9 | 0.601 | 0.639 |
| Z_mag_axis | mm | 8761 | 1.86 | 1.16 | 2.93 | 5.89 | 10.5 | 35.3 | 0.221 | 0.951 |
| elongation |  | 8760 | 0.0175 | 0.00937 | 0.0298 | 0.063 | 0.121 | 0.344 | 0.116 | 0.987 |
| triangularity |  | 8760 | 0.00944 | 0.00613 | 0.0143 | 0.0294 | 0.0507 | 0.14 | 0.124 | 0.985 |
| triangularity_upper |  | 8760 | 0.00956 | 0.00639 | 0.0152 | 0.0274 | 0.0597 | 0.153 | 0.213 | 0.955 |
| triangularity_lower |  | 8760 | 0.0128 | 0.00866 | 0.019 | 0.0393 | 0.069 | 0.189 | 0.114 | 0.987 |
| R_x_point | mm | 5207 | 2.47 | 1.72 | 3.66 | 7.16 | 11.8 | 35.9 | 0.408 | 0.833 |
| Z_x_point | mm | 5207 | 2.22 | 1.6 | 3.09 | 6.46 | 10.2 | 19.4 | 0.252 | 0.937 |
| R_strike_point_1 | mm | 5206 | 2.31 | 1.77 | 3.16 | 6.22 | 10 | 22.6 | 0.249 | 0.938 |
| Z_strike_point_1 | mm | 5206 | 0.857 | 0.602 | 1.23 | 2.55 | 4.22 | 9.9 | 0.248 | 0.939 |
| R_strike_point_2 | mm | 5206 | 2.96 | 2.04 | 4.49 | 8.89 | 16.4 | 47.2 | 0.372 | 0.861 |
| Z_strike_point_2 | mm | 5206 | 0.534 | 0.4 | 0.736 | 1.53 | 2.26 | 5.98 | 0.311 | 0.903 |
| R_limiter | mm | 3554 | 25.8 | 6.5 | 62.3 | 123 | 334 | 432 | 0.672 | 0.549 |
| Z_limiter | mm | 3554 | 38.9 | 16.2 | 72.3 | 155 | 312 | 523 | 0.461 | 0.788 |
| is_limited |  | 8761 | 0.0325 | 0.0111 | 0.103 | 0.0883 | 0.605 | 1.02 | 0.211 | 0.956 |

is_limited accuracy: 0.9858

### candidate, plain, noisy inputs (mean nRMSE over 16 targets 12.0304)

| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 8760 | 4.31 | 3.62 | 5.41 | 10.5 | 14.1 | 21.6 | 0.0463 | 0.998 |
| R_mag_axis | mm | 8761 | 190 | 155 | 242 | 479 | 656 | 1.07e+03 | 30.9 | -955 |
| Z_mag_axis | mm | 8761 | 206 | 175 | 252 | 483 | 644 | 1.04e+03 | 18.9 | -358 |
| elongation |  | 8760 | 1.3 | 1.09 | 1.62 | 3.2 | 4.13 | 6.46 | 6.31 | -38.8 |
| triangularity |  | 8760 | 0.712 | 0.388 | 1.06 | 2.4 | 3.31 | 5.61 | 9.21 | -83.8 |
| triangularity_upper |  | 8760 | 1.4 | 1.2 | 1.73 | 3.36 | 4.39 | 6.48 | 24.3 | -592 |
| triangularity_lower |  | 8760 | 1.02 | 0.86 | 1.29 | 2.54 | 3.31 | 5.16 | 7.73 | -58.7 |
| R_x_point | mm | 5207 | 47.2 | 26.3 | 71.2 | 164 | 235 | 399 | 7.94 | -62 |
| Z_x_point | mm | 5207 | 16.4 | 13.5 | 21.2 | 42.5 | 62 | 110 | 1.73 | -2 |
| R_strike_point_1 | mm | 5206 | 92.5 | 55.5 | 136 | 305 | 419 | 682 | 10.7 | -114 |
| Z_strike_point_1 | mm | 5206 | 71.7 | 52.1 | 97.5 | 212 | 298 | 512 | 19.6 | -383 |
| R_strike_point_2 | mm | 5206 | 71.1 | 58.8 | 90.8 | 182 | 238 | 329 | 7.52 | -55.6 |
| Z_strike_point_2 | mm | 5206 | 17.2 | 4.7 | 29.3 | 68.8 | 98.2 | 171 | 12.4 | -152 |
| R_limiter | mm | 3554 | 1.31e+03 | 1.09e+03 | 1.69e+03 | 3.37e+03 | 4.39e+03 | 7.61e+03 | 18.2 | -331 |
| Z_limiter | mm | 3554 | 994 | 799 | 1.29e+03 | 2.59e+03 | 3.44e+03 | 5.79e+03 | 8.22 | -66.6 |
| is_limited |  | 8761 | 3.22 | 2.51 | 4.26 | 8.8 | 12.2 | 20.7 | 8.68 | -74.3 |

is_limited accuracy: 0.4438

### candidate, augmented, noisy inputs (mean nRMSE over 16 targets 0.3159)

| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 8760 | 4.03 | 3.4 | 5.05 | 9.84 | 13 | 20.6 | 0.0433 | 0.998 |
| R_mag_axis | mm | 8761 | 2.6 | 1.47 | 5.32 | 7.61 | 17.6 | 97.1 | 0.68 | 0.538 |
| Z_mag_axis | mm | 8761 | 1.95 | 1.21 | 3.24 | 6.22 | 11.1 | 69.9 | 0.244 | 0.941 |
| elongation |  | 8760 | 0.0189 | 0.0103 | 0.0323 | 0.0678 | 0.129 | 0.322 | 0.126 | 0.984 |
| triangularity |  | 8760 | 0.0103 | 0.00652 | 0.0159 | 0.0333 | 0.0585 | 0.16 | 0.139 | 0.981 |
| triangularity_upper |  | 8760 | 0.00994 | 0.00653 | 0.0166 | 0.0277 | 0.0704 | 0.173 | 0.233 | 0.946 |
| triangularity_lower |  | 8760 | 0.0139 | 0.00906 | 0.0212 | 0.0432 | 0.0791 | 0.208 | 0.127 | 0.984 |
| R_x_point | mm | 5207 | 2.71 | 1.88 | 3.84 | 8.05 | 12.6 | 27.6 | 0.428 | 0.817 |
| Z_x_point | mm | 5207 | 2.5 | 1.76 | 3.45 | 7.49 | 11.1 | 18.8 | 0.281 | 0.921 |
| R_strike_point_1 | mm | 5206 | 2.59 | 1.95 | 3.54 | 7.26 | 11.7 | 20.5 | 0.28 | 0.922 |
| Z_strike_point_1 | mm | 5206 | 0.954 | 0.652 | 1.38 | 2.84 | 4.77 | 14.4 | 0.278 | 0.923 |
| R_strike_point_2 | mm | 5206 | 3.25 | 2.22 | 4.68 | 9.77 | 16.5 | 30.2 | 0.388 | 0.85 |
| Z_strike_point_2 | mm | 5206 | 0.59 | 0.441 | 0.803 | 1.63 | 2.43 | 5.27 | 0.339 | 0.885 |
| R_limiter | mm | 3554 | 24.7 | 4.89 | 69.8 | 101 | 405 | 568 | 0.752 | 0.434 |
| Z_limiter | mm | 3554 | 40.3 | 15.2 | 76.9 | 173 | 335 | 606 | 0.49 | 0.76 |
| is_limited |  | 8761 | 0.0323 | 0.0111 | 0.111 | 0.0776 | 0.719 | 1.16 | 0.226 | 0.949 |

is_limited accuracy: 0.9845

## Locked test, clean inputs: cluster bootstrap by discharge (1000 resamples, 95 % intervals)

MAE and RMSE with intervals; ratio = MAE of the recipe over MAE of the baseline MLP on the same resamples (below 1 means better).

| target | unit | baseline MLP MAE [95 %] | baseline MLP, augmented (extra) MAE [95 %] | candidate, plain MAE [95 %] | candidate, augmented MAE [95 %] | MAE ratio base_aug/base [95 %] | MAE ratio cand/base [95 %] | MAE ratio cand_aug/base [95 %] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.2 [0.988, 1.45] | 1.91 [1.52, 2.33] | 0.0347 [0.0311, 0.0382] | 0.509 [0.476, 0.544] | 1.59 [1.43, 1.78] | 0.03 [0.02, 0.03] | 0.42 [0.35, 0.51] |
| R_mag_axis | mm | 0.307 [0.235, 0.4] | 1.56 [1.26, 1.92] | 0.133 [0.099, 0.177] | 0.548 [0.403, 0.716] | 5.09 [4.00, 6.39] | 0.43 [0.38, 0.49] | 1.79 [1.48, 2.13] |
| Z_mag_axis | mm | 0.321 [0.262, 0.396] | 0.837 [0.68, 1.05] | 0.172 [0.128, 0.223] | 0.462 [0.373, 0.569] | 2.61 [2.28, 3.00] | 0.54 [0.47, 0.60] | 1.44 [1.31, 1.59] |
| R_x_point | mm | 0.161 [0.124, 0.203] | 1.56 [1.08, 2.15] | 0.115 [0.0756, 0.168] | 0.5 [0.338, 0.712] | 9.66 [7.60, 12.25] | 0.72 [0.53, 0.97] | 3.11 [2.49, 3.99] |
| Z_x_point | mm | 0.162 [0.128, 0.199] | 1.11 [0.882, 1.38] | 0.0969 [0.0673, 0.13] | 0.426 [0.312, 0.568] | 6.89 [5.64, 8.16] | 0.60 [0.49, 0.71] | 2.64 [2.10, 3.30] |
| R_strike_point_1 | mm | 0.212 [0.172, 0.255] | 1.14 [0.855, 1.48] | 0.108 [0.0768, 0.144] | 0.513 [0.367, 0.683] | 5.36 [4.14, 6.94] | 0.51 [0.40, 0.63] | 2.42 [1.86, 3.04] |
| Z_strike_point_1 | mm | 0.0986 [0.0749, 0.126] | 0.47 [0.359, 0.601] | 0.0459 [0.0344, 0.0606] | 0.215 [0.153, 0.285] | 4.77 [3.74, 6.17] | 0.47 [0.40, 0.54] | 2.18 [1.79, 2.62] |
| R_strike_point_2 | mm | 0.212 [0.162, 0.277] | 1.83 [1.32, 2.48] | 0.136 [0.0836, 0.205] | 0.609 [0.421, 0.846] | 8.63 [7.18, 10.39] | 0.64 [0.43, 0.94] | 2.87 [2.25, 3.63] |
| Z_strike_point_2 | mm | 0.0454 [0.0356, 0.0571] | 0.312 [0.23, 0.409] | 0.0264 [0.019, 0.0358] | 0.116 [0.0827, 0.159] | 6.87 [5.25, 8.84] | 0.58 [0.47, 0.70] | 2.55 [1.95, 3.26] |
| R_limiter | mm | 10.6 [8.05, 13.8] | 18.6 [15, 22.9] | 4.55 [3.3, 6.16] | 9.47 [7.2, 12.3] | 1.75 [1.64, 1.90] | 0.43 [0.37, 0.51] | 0.89 [0.78, 1.01] |
| Z_limiter | mm | 22.5 [20.1, 24.8] | 25.7 [21.9, 30.6] | 8.35 [6.81, 10.2] | 16.7 [13.8, 20.5] | 1.14 [1.01, 1.32] | 0.37 [0.33, 0.42] | 0.74 [0.65, 0.86] |

RMSE with intervals:

| target | unit | baseline MLP RMSE [95 %] | baseline MLP, augmented (extra) RMSE [95 %] | candidate, plain RMSE [95 %] | candidate, augmented RMSE [95 %] |
|---|---|---:|---:|---:|---:|
| plasma_current | kA | 2.2 [1.58, 2.87] | 3.11 [2.28, 3.98] | 0.047 [0.0423, 0.0517] | 0.64 [0.592, 0.69] |
| R_mag_axis | mm | 0.75 [0.517, 0.975] | 2.86 [2.38, 3.35] | 0.374 [0.26, 0.481] | 1.25 [0.918, 1.54] |
| Z_mag_axis | mm | 0.887 [0.553, 1.22] | 1.56 [1.16, 2] | 0.741 [0.376, 1.1] | 1.1 [0.78, 1.44] |
| R_x_point | mm | 0.305 [0.22, 0.384] | 2.87 [1.92, 3.94] | 0.454 [0.16, 0.738] | 1.15 [0.704, 1.61] |
| Z_x_point | mm | 0.258 [0.208, 0.31] | 1.84 [1.37, 2.31] | 0.257 [0.146, 0.378] | 0.875 [0.576, 1.18] |
| R_strike_point_1 | mm | 0.365 [0.27, 0.468] | 1.97 [1.4, 2.55] | 0.219 [0.145, 0.282] | 1.03 [0.675, 1.35] |
| Z_strike_point_1 | mm | 0.211 [0.14, 0.279] | 0.79 [0.57, 0.995] | 0.11 [0.0692, 0.153] | 0.421 [0.284, 0.547] |
| R_strike_point_2 | mm | 0.401 [0.274, 0.53] | 3.5 [2.32, 4.72] | 0.638 [0.193, 0.999] | 1.46 [0.89, 2.05] |
| Z_strike_point_2 | mm | 0.106 [0.0572, 0.154] | 0.493 [0.349, 0.656] | 0.1 [0.0479, 0.146] | 0.208 [0.151, 0.271] |
| R_limiter | mm | 29.1 [22, 36.5] | 47.6 [38, 57.8] | 19.4 [11.6, 28.7] | 29.9 [21.6, 38.8] |
| Z_limiter | mm | 40.8 [37.3, 44.6] | 52.2 [42.4, 63.1] | 20.9 [16.4, 26.3] | 35.8 [29.3, 43] |

## Locked test, noisy inputs: cluster bootstrap by discharge (1000 resamples, 95 % intervals)

MAE and RMSE with intervals; ratio = MAE of the recipe over MAE of the baseline MLP on the same resamples (below 1 means better).

| target | unit | baseline MLP MAE [95 %] | baseline MLP, augmented (extra) MAE [95 %] | candidate, plain MAE [95 %] | candidate, augmented MAE [95 %] | MAE ratio base_aug/base [95 %] | MAE ratio cand/base [95 %] | MAE ratio cand_aug/base [95 %] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 5.63 [5.37, 5.96] | 4.65 [4.34, 5.05] | 4.31 [4.24, 4.38] | 4.03 [3.96, 4.09] | 0.83 [0.80, 0.86] | 0.77 [0.73, 0.80] | 0.72 [0.68, 0.75] |
| R_mag_axis | mm | 9.16 [8.61, 9.8] | 2.38 [2.09, 2.72] | 190 [188, 192] | 2.6 [2.28, 2.99] | 0.26 [0.23, 0.30] | 20.74 [19.35, 22.05] | 0.28 [0.25, 0.33] |
| Z_mag_axis | mm | 3.82 [3.65, 4] | 1.86 [1.67, 2.11] | 206 [197, 212] | 1.95 [1.76, 2.21] | 0.49 [0.44, 0.55] | 53.87 [51.39, 56.58] | 0.51 [0.46, 0.57] |
| R_x_point | mm | 4.35 [4.1, 4.67] | 2.47 [2.04, 3.01] | 47.2 [45.9, 48.4] | 2.71 [2.25, 3.27] | 0.57 [0.48, 0.66] | 10.85 [10.00, 11.68] | 0.62 [0.52, 0.72] |
| Z_x_point | mm | 3.01 [2.89, 3.16] | 2.22 [1.97, 2.48] | 16.4 [14.3, 19.2] | 2.5 [2.17, 2.85] | 0.74 [0.66, 0.82] | 5.45 [4.66, 6.45] | 0.83 [0.72, 0.94] |
| R_strike_point_1 | mm | 3.21 [3.09, 3.34] | 2.31 [2.07, 2.59] | 92.5 [90.1, 95] | 2.59 [2.3, 2.91] | 0.72 [0.65, 0.80] | 28.79 [27.38, 30.25] | 0.81 [0.71, 0.91] |
| Z_strike_point_1 | mm | 1.22 [1.11, 1.33] | 0.857 [0.759, 0.956] | 71.7 [70.1, 73.3] | 0.954 [0.827, 1.09] | 0.70 [0.63, 0.77] | 58.60 [53.15, 65.58] | 0.78 [0.70, 0.87] |
| R_strike_point_2 | mm | 4.63 [4.36, 5.01] | 2.96 [2.49, 3.53] | 71.1 [68.7, 74.4] | 3.25 [2.71, 3.83] | 0.64 [0.56, 0.73] | 15.36 [14.05, 16.68] | 0.70 [0.60, 0.80] |
| Z_strike_point_2 | mm | 0.855 [0.798, 0.937] | 0.534 [0.462, 0.622] | 17.2 [16.5, 18] | 0.59 [0.51, 0.684] | 0.63 [0.55, 0.70] | 20.10 [18.11, 22.13] | 0.69 [0.61, 0.78] |
| R_limiter | mm | 48.9 [43.6, 55.3] | 25.8 [21.8, 30.2] | 1.31e+03 [1.28e+03, 1.35e+03] | 24.7 [21.6, 28.7] | 0.53 [0.47, 0.59] | 26.87 [23.75, 30.06] | 0.50 [0.46, 0.56] |
| Z_limiter | mm | 62.3 [58, 66.4] | 38.9 [35.5, 43.3] | 994 [958, 1.03e+03] | 40.3 [36.5, 45.2] | 0.62 [0.58, 0.68] | 15.96 [14.87, 17.30] | 0.65 [0.60, 0.70] |

RMSE with intervals:

| target | unit | baseline MLP RMSE [95 %] | baseline MLP, augmented (extra) RMSE [95 %] | candidate, plain RMSE [95 %] | candidate, augmented RMSE [95 %] |
|---|---|---:|---:|---:|---:|
| plasma_current | kA | 7.43 [6.98, 8.01] | 6.15 [5.54, 6.91] | 5.41 [5.31, 5.5] | 5.05 [4.97, 5.13] |
| R_mag_axis | mm | 13.6 [12.5, 14.8] | 4.7 [4.02, 5.38] | 242 [239, 245] | 5.32 [4.53, 6.14] |
| Z_mag_axis | mm | 5.17 [4.89, 5.46] | 2.93 [2.56, 3.42] | 252 [244, 258] | 3.24 [2.75, 3.85] |
| R_x_point | mm | 5.64 [5.27, 6.18] | 3.66 [2.9, 4.57] | 71.2 [69.6, 72.8] | 3.84 [3.15, 4.58] |
| Z_x_point | mm | 3.81 [3.66, 4.02] | 3.09 [2.71, 3.45] | 21.2 [17.9, 25.4] | 3.45 [2.99, 3.88] |
| R_strike_point_1 | mm | 4.07 [3.91, 4.23] | 3.16 [2.76, 3.59] | 136 [132, 139] | 3.54 [3.1, 4] |
| Z_strike_point_1 | mm | 1.74 [1.59, 1.88] | 1.23 [1.07, 1.39] | 97.5 [95.6, 99.7] | 1.38 [1.17, 1.61] |
| R_strike_point_2 | mm | 6.09 [5.65, 6.68] | 4.49 [3.58, 5.51] | 90.8 [88.1, 94] | 4.68 [3.83, 5.51] |
| Z_strike_point_2 | mm | 1.12 [1.03, 1.26] | 0.736 [0.617, 0.88] | 29.3 [28.3, 30.4] | 0.803 [0.688, 0.935] |
| R_limiter | mm | 111 [100, 122] | 62.3 [53.5, 71.6] | 1.69e+03 [1.64e+03, 1.73e+03] | 69.8 [61.3, 79.9] |
| Z_limiter | mm | 105 [96.2, 112] | 72.3 [64.9, 81.4] | 1.29e+03 [1.25e+03, 1.33e+03] | 76.9 [69.6, 85.6] |

## Locked test: breakdowns (MAE per headline target; p95 is in the json)

Polarity is the sign of the plasma current of the discharge: 28 negative and 2 positive locked discharges. Relative time is the row's time scaled to 0..1 within its discharge. Configuration is the true is_limited. n = rows.

### polarity: negative plasma current (8170 rows, 28 discharges)

| target | unit | baseline MLP clean | baseline MLP, augmented (extra) clean | candidate, plain clean | candidate, augmented clean | baseline MLP noisy | baseline MLP, augmented (extra) noisy | candidate, plain noisy | candidate, augmented noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.09 | 1.7 | 0.0342 | 0.513 | 5.43 | 4.45 | 4.3 | 4.02 |
| R_mag_axis | mm | 0.257 | 1.52 | 0.11 | 0.489 | 9.36 | 2.36 | 190 | 2.61 |
| Z_mag_axis | mm | 0.286 | 0.783 | 0.144 | 0.407 | 3.89 | 1.85 | 211 | 1.94 |
| R_x_point | mm | 0.15 | 1.57 | 0.0944 | 0.485 | 4.42 | 2.49 | 46.7 | 2.73 |
| Z_x_point | mm | 0.155 | 1.11 | 0.0877 | 0.409 | 3.03 | 2.25 | 14.8 | 2.54 |
| R_strike_point_1 | mm | 0.205 | 1.14 | 0.1 | 0.493 | 3.25 | 2.34 | 92.8 | 2.63 |
| Z_strike_point_1 | mm | 0.0905 | 0.476 | 0.0429 | 0.209 | 1.25 | 0.876 | 71.3 | 0.978 |
| R_strike_point_2 | mm | 0.204 | 1.83 | 0.106 | 0.581 | 4.69 | 2.98 | 70.3 | 3.27 |
| Z_strike_point_2 | mm | 0.0399 | 0.317 | 0.0226 | 0.112 | 0.868 | 0.543 | 16.8 | 0.601 |
| R_limiter | mm | 9.68 | 17.4 | 4.23 | 9.21 | 49.6 | 24.8 | 1.31e+03 | 24.7 |
| Z_limiter | mm | 21.5 | 25.8 | 7.41 | 15.5 | 62.4 | 39.2 | 1.01e+03 | 40.3 |

### polarity: positive plasma current (591 rows, 2 discharges)

| target | unit | baseline MLP clean | baseline MLP, augmented (extra) clean | candidate, plain clean | candidate, augmented clean | baseline MLP noisy | baseline MLP, augmented (extra) noisy | candidate, plain noisy | candidate, augmented noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 2.71 | 4.72 | 0.0404 | 0.448 | 8.31 | 7.51 | 4.46 | 4.13 |
| R_mag_axis | mm | 0.998 | 2.17 | 0.454 | 1.37 | 6.3 | 2.62 | 184 | 2.55 |
| Z_mag_axis | mm | 0.808 | 1.59 | 0.557 | 1.22 | 2.87 | 2.02 | 136 | 2.1 |
| R_x_point | mm | 0.36 | 1.23 | 0.487 | 0.784 | 3.07 | 2.2 | 55.4 | 2.3 |
| Z_x_point | mm | 0.28 | 1.12 | 0.26 | 0.731 | 2.57 | 1.79 | 45 | 1.8 |
| R_strike_point_1 | mm | 0.339 | 1.02 | 0.249 | 0.873 | 2.49 | 1.72 | 86.3 | 1.85 |
| Z_strike_point_1 | mm | 0.244 | 0.365 | 0.1 | 0.315 | 0.838 | 0.516 | 80 | 0.532 |
| R_strike_point_2 | mm | 0.359 | 1.72 | 0.66 | 1.1 | 3.6 | 2.74 | 86.6 | 2.81 |
| Z_strike_point_2 | mm | 0.143 | 0.214 | 0.0927 | 0.178 | 0.626 | 0.374 | 24.4 | 0.409 |
| R_limiter | mm | 20.3 | 31.6 | 7.87 | 12.2 | 41.5 | 36 | 1.31e+03 | 24 |
| Z_limiter | mm | 32.9 | 24.9 | 18 | 29.1 | 61 | 36 | 832 | 40.9 |

### relative time: first 2 % (189 rows, 30 discharges)

| target | unit | baseline MLP clean | baseline MLP, augmented (extra) clean | candidate, plain clean | candidate, augmented clean | baseline MLP noisy | baseline MLP, augmented (extra) noisy | candidate, plain noisy | candidate, augmented noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.69 | 2.12 | 0.0195 | 0.395 | 7.05 | 4.86 | 4.28 | 4.16 |
| R_mag_axis | mm | 1.65 | 5.2 | 0.538 | 2.25 | 30.8 | 11.8 | 205 | 13.4 |
| Z_mag_axis | mm | 0.935 | 1.97 | 0.435 | 1.64 | 8.43 | 2.65 | 186 | 2.96 |
| R_x_point | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z_x_point | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| R_strike_point_1 | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z_strike_point_1 | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| R_strike_point_2 | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z_strike_point_2 | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| R_limiter | mm | 48 | 83.6 | 18.5 | 39.1 | 183 | 127 | 1.17e+03 | 146 |
| Z_limiter | mm | 12.6 | 12.9 | 6.37 | 13.4 | 39.6 | 18 | 1.08e+03 | 23.5 |

### relative time: middle (8383 rows, 30 discharges)

| target | unit | baseline MLP clean | baseline MLP, augmented (extra) clean | candidate, plain clean | candidate, augmented clean | baseline MLP noisy | baseline MLP, augmented (extra) noisy | candidate, plain noisy | candidate, augmented noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.15 | 1.85 | 0.0348 | 0.507 | 5.56 | 4.59 | 4.31 | 4.02 |
| R_mag_axis | mm | 0.256 | 1.38 | 0.114 | 0.479 | 8.5 | 2.01 | 190 | 2.16 |
| Z_mag_axis | mm | 0.274 | 0.756 | 0.14 | 0.398 | 3.63 | 1.76 | 207 | 1.82 |
| R_x_point | mm | 0.16 | 1.54 | 0.115 | 0.495 | 4.35 | 2.46 | 47.1 | 2.69 |
| Z_x_point | mm | 0.16 | 1.1 | 0.0954 | 0.418 | 3.01 | 2.21 | 16.4 | 2.48 |
| R_strike_point_1 | mm | 0.21 | 1.12 | 0.108 | 0.501 | 3.21 | 2.3 | 92.4 | 2.57 |
| Z_strike_point_1 | mm | 0.0979 | 0.465 | 0.0454 | 0.212 | 1.22 | 0.852 | 71.7 | 0.942 |
| R_strike_point_2 | mm | 0.21 | 1.81 | 0.135 | 0.602 | 4.63 | 2.95 | 71.1 | 3.23 |
| Z_strike_point_2 | mm | 0.0448 | 0.309 | 0.026 | 0.114 | 0.855 | 0.531 | 17.2 | 0.586 |
| R_limiter | mm | 8.2 | 14 | 3.57 | 7.42 | 40.4 | 18.4 | 1.33e+03 | 16.3 |
| Z_limiter | mm | 23.2 | 26.7 | 8.3 | 16.9 | 64.2 | 40.4 | 988 | 41.6 |

### relative time: last 2 % (189 rows, 30 discharges)

| target | unit | baseline MLP clean | baseline MLP, augmented (extra) clean | candidate, plain clean | candidate, augmented clean | baseline MLP noisy | baseline MLP, augmented (extra) noisy | candidate, plain noisy | candidate, augmented noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 2.93 | 4.35 | 0.043 | 0.697 | 7.19 | 7.11 | 4.45 | 4.2 |
| R_mag_axis | mm | 1.21 | 5.98 | 0.578 | 1.91 | 16.7 | 9.25 | 186 | 11.5 |
| Z_mag_axis | mm | 1.8 | 3.31 | 1.33 | 2.12 | 7.92 | 5.58 | 198 | 6.85 |
| R_x_point | mm | 0.229 (n=56) | 2.81 (n=56) | 0.122 (n=56) | 0.981 (n=56) | 4.02 (n=56) | 3.83 (n=56) | 49.8 (n=56) | 4.35 (n=56) |
| Z_x_point | mm | 0.313 (n=56) | 2.29 (n=56) | 0.231 (n=56) | 1.19 (n=56) | 2.83 (n=56) | 3.43 (n=56) | 14.1 (n=56) | 4.33 (n=56) |
| R_strike_point_1 | mm | 0.381 (n=56) | 2.51 (n=56) | 0.151 (n=56) | 1.6 (n=56) | 3.1 (n=56) | 3.53 (n=56) | 97.9 (n=56) | 4.29 (n=56) |
| Z_strike_point_1 | mm | 0.165 (n=56) | 0.957 (n=56) | 0.0894 (n=56) | 0.464 (n=56) | 1.44 (n=56) | 1.3 (n=56) | 69.7 (n=56) | 2.1 (n=56) |
| R_strike_point_2 | mm | 0.394 (n=56) | 3.09 (n=56) | 0.208 (n=56) | 1.22 (n=56) | 4.34 (n=56) | 4.26 (n=56) | 71.7 (n=56) | 4.87 (n=56) |
| Z_strike_point_2 | mm | 0.0974 (n=56) | 0.585 (n=56) | 0.0561 (n=56) | 0.287 (n=56) | 0.826 (n=56) | 0.812 (n=56) | 17.6 (n=56) | 0.981 (n=56) |
| R_limiter | mm | 16.4 | 38.7 | 8.5 | 17.1 | 63.8 | 60.9 | 1.19e+03 | 55.5 |
| Z_limiter | mm | 18.4 | 20.5 | 12.3 | 18 | 47.1 | 31.8 | 1e+03 | 32.4 |

### configuration: divertor (5207 rows, 30 discharges)

| target | unit | baseline MLP clean | baseline MLP, augmented (extra) clean | candidate, plain clean | candidate, augmented clean | baseline MLP noisy | baseline MLP, augmented (extra) noisy | candidate, plain noisy | candidate, augmented noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 0.954 | 1.72 | 0.0357 | 0.469 | 5.37 | 4.44 | 4.34 | 4.03 |
| R_mag_axis | mm | 0.202 | 1.29 | 0.0929 | 0.471 | 6.84 | 1.82 | 187 | 2.02 |
| Z_mag_axis | mm | 0.24 | 0.723 | 0.109 | 0.366 | 3.55 | 1.77 | 207 | 1.82 |
| R_x_point | mm | 0.161 | 1.56 | 0.115 | 0.5 | 4.35 | 2.47 | 47.2 | 2.71 |
| Z_x_point | mm | 0.162 | 1.11 | 0.0969 | 0.426 | 3.01 | 2.22 | 16.4 | 2.5 |
| R_strike_point_1 | mm | 0.212 | 1.14 | 0.108 | 0.513 | 3.21 | 2.31 | 92.5 | 2.59 |
| Z_strike_point_1 | mm | 0.0986 | 0.47 | 0.0459 | 0.215 | 1.22 | 0.857 | 71.7 | 0.954 |
| R_strike_point_2 | mm | 0.212 | 1.83 | 0.136 | 0.609 | 4.63 | 2.96 | 71.1 | 3.25 |
| Z_strike_point_2 | mm | 0.0454 | 0.312 | 0.0264 | 0.116 | 0.855 | 0.534 | 17.2 | 0.59 |
| R_limiter | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z_limiter | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

### configuration: limited (3554 rows, 30 discharges)

| target | unit | baseline MLP clean | baseline MLP, augmented (extra) clean | candidate, plain clean | candidate, augmented clean | baseline MLP noisy | baseline MLP, augmented (extra) noisy | candidate, plain noisy | candidate, augmented noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.56 | 2.19 | 0.0331 | 0.566 | 6 | 4.97 | 4.27 | 4.02 |
| R_mag_axis | mm | 0.46 | 1.96 | 0.192 | 0.661 | 12.5 | 3.2 | 193 | 3.45 |
| Z_mag_axis | mm | 0.44 | 1 | 0.264 | 0.604 | 4.23 | 2 | 204 | 2.15 |
| R_x_point | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z_x_point | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| R_strike_point_1 | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z_strike_point_1 | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| R_strike_point_2 | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z_strike_point_2 | mm | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| R_limiter | mm | 10.6 | 18.6 | 4.55 | 9.47 | 48.9 | 25.8 | 1.31e+03 | 24.7 |
| Z_limiter | mm | 22.5 | 25.7 | 8.35 | 16.7 | 62.3 | 38.9 | 994 | 40.3 |

## Blocked-by-id split against random group folds (development set only)

Train on the lower half of the development discharge ids, test on the upper half. Discharge ids are chronological, so this is a test on later campaigns. The random-fold numbers are the pooled out-of-fold errors of the SAME recipe on the SAME upper-half discharges, and on all development discharges. Caveat: the blocked model trains on about 60 discharges, the random folds on about 95, so part of the gap is the smaller training set, not only the drift between campaigns.

### baseline MLP (60 training, 59 test discharges, 18506 test rows)

| target | unit | inputs | blocked MAE | random folds, same discharges MAE | ratio | random folds, all development MAE |
|---|---|---|---:|---:|---:|---:|
| plasma_current | kA | clean | 2.6 | 1.44 | 1.81 | 1.51 |
| plasma_current | kA | noisy | 6.37 | 5.98 | 1.07 | 6.08 |
| R_mag_axis | mm | clean | 1.23 | 0.448 | 2.75 | 0.479 |
| R_mag_axis | mm | noisy | 8.59 | 9.29 | 0.92 | 10.2 |
| Z_mag_axis | mm | clean | 0.82 | 0.405 | 2.02 | 0.469 |
| Z_mag_axis | mm | noisy | 3.41 | 3.9 | 0.87 | 4.21 |
| R_x_point | mm | clean | 0.634 | 0.219 | 2.89 | 0.253 |
| R_x_point | mm | noisy | 4.05 | 4.42 | 0.92 | 4.51 |
| Z_x_point | mm | clean | 0.516 | 0.238 | 2.17 | 0.234 |
| Z_x_point | mm | noisy | 3.02 | 3.11 | 0.97 | 3.2 |
| R_strike_point_1 | mm | clean | 0.697 | 0.247 | 2.83 | 0.312 |
| R_strike_point_1 | mm | noisy | 3.23 | 3.21 | 1.00 | 3.37 |
| Z_strike_point_1 | mm | clean | 0.311 | 0.132 | 2.36 | 0.142 |
| Z_strike_point_1 | mm | noisy | 1.36 | 1.25 | 1.09 | 1.29 |
| R_strike_point_2 | mm | clean | 0.751 | 0.295 | 2.55 | 0.291 |
| R_strike_point_2 | mm | noisy | 4.31 | 4.71 | 0.91 | 4.82 |
| Z_strike_point_2 | mm | clean | 0.134 | 0.0717 | 1.88 | 0.0728 |
| Z_strike_point_2 | mm | noisy | 0.814 | 0.875 | 0.93 | 0.92 |
| R_limiter | mm | clean | 18.6 | 11.3 | 1.64 | 14 |
| R_limiter | mm | noisy | 43.6 | 47 | 0.93 | 48.6 |
| Z_limiter | mm | clean | 34.6 | 23.3 | 1.49 | 23 |
| Z_limiter | mm | noisy | 69.7 | 64.8 | 1.08 | 63 |

### baseline MLP, augmented (extra) (60 training, 59 test discharges, 18506 test rows)

| target | unit | inputs | blocked MAE | random folds, same discharges MAE | ratio | random folds, all development MAE |
|---|---|---|---:|---:|---:|---:|
| plasma_current | kA | clean | 2.72 | 1.92 | 1.42 | 2.14 |
| plasma_current | kA | noisy | 5.3 | 4.59 | 1.15 | 4.77 |
| R_mag_axis | mm | clean | 3.35 | 2.13 | 1.57 | 2.21 |
| R_mag_axis | mm | noisy | 3.85 | 2.91 | 1.32 | 2.99 |
| Z_mag_axis | mm | clean | 1.64 | 1.06 | 1.54 | 1.34 |
| Z_mag_axis | mm | noisy | 2.73 | 1.94 | 1.41 | 2.27 |
| R_x_point | mm | clean | 2.98 | 1.85 | 1.61 | 1.69 |
| R_x_point | mm | noisy | 3.48 | 2.68 | 1.30 | 2.43 |
| Z_x_point | mm | clean | 2.04 | 1.43 | 1.43 | 1.42 |
| Z_x_point | mm | noisy | 2.95 | 2.26 | 1.31 | 2.38 |
| R_strike_point_1 | mm | clean | 1.54 | 1.23 | 1.26 | 1.31 |
| R_strike_point_1 | mm | noisy | 2.69 | 2.32 | 1.16 | 2.38 |
| Z_strike_point_1 | mm | clean | 0.861 | 0.567 | 1.52 | 0.557 |
| Z_strike_point_1 | mm | noisy | 1.23 | 0.95 | 1.29 | 0.945 |
| R_strike_point_2 | mm | clean | 3.59 | 2.12 | 1.70 | 1.98 |
| R_strike_point_2 | mm | noisy | 4.25 | 3.05 | 1.39 | 2.94 |
| Z_strike_point_2 | mm | clean | 0.647 | 0.387 | 1.67 | 0.365 |
| Z_strike_point_2 | mm | noisy | 0.778 | 0.566 | 1.38 | 0.554 |
| R_limiter | mm | clean | 26.1 | 18.7 | 1.39 | 17 |
| R_limiter | mm | noisy | 29.7 | 25.1 | 1.18 | 22.7 |
| Z_limiter | mm | clean | 42.7 | 29.2 | 1.46 | 28.9 |
| Z_limiter | mm | noisy | 51.8 | 41 | 1.26 | 39.3 |

### candidate, plain (60 training, 59 test discharges, 18506 test rows)

| target | unit | inputs | blocked MAE | random folds, same discharges MAE | ratio | random folds, all development MAE |
|---|---|---|---:|---:|---:|---:|
| plasma_current | kA | clean | 0.0387 | 0.0361 | 1.07 | 0.0332 |
| plasma_current | kA | noisy | 4.31 | 4.33 | 1.00 | 4.32 |
| R_mag_axis | mm | clean | 0.397 | 0.216 | 1.84 | 0.23 |
| R_mag_axis | mm | noisy | 121 | 138 | 0.87 | 138 |
| Z_mag_axis | mm | clean | 0.431 | 0.203 | 2.12 | 0.341 |
| Z_mag_axis | mm | noisy | 187 | 222 | 0.84 | 223 |
| R_x_point | mm | clean | 0.431 | 0.225 | 1.92 | 0.211 |
| R_x_point | mm | noisy | 60.3 | 43.6 | 1.38 | 43.6 |
| Z_x_point | mm | clean | 0.414 | 0.188 | 2.20 | 0.195 |
| Z_x_point | mm | noisy | 120 | 108 | 1.11 | 107 |
| R_strike_point_1 | mm | clean | 0.448 | 0.158 | 2.83 | 0.206 |
| R_strike_point_1 | mm | noisy | 166 | 110 | 1.52 | 110 |
| Z_strike_point_1 | mm | clean | 0.199 | 0.0865 | 2.30 | 0.116 |
| Z_strike_point_1 | mm | noisy | 63.4 | 24.3 | 2.61 | 23.9 |
| R_strike_point_2 | mm | clean | 0.598 | 0.243 | 2.46 | 0.254 |
| R_strike_point_2 | mm | noisy | 64.6 | 117 | 0.55 | 116 |
| Z_strike_point_2 | mm | clean | 0.113 | 0.0431 | 2.63 | 0.0453 |
| Z_strike_point_2 | mm | noisy | 26.3 | 16 | 1.64 | 15.9 |
| R_limiter | mm | clean | 8.67 | 4.7 | 1.85 | 4.62 |
| R_limiter | mm | noisy | 745 | 1.32e+03 | 0.56 | 1.32e+03 |
| Z_limiter | mm | clean | 23.9 | 10.7 | 2.23 | 11.8 |
| Z_limiter | mm | noisy | 1.39e+03 | 1.19e+03 | 1.16 | 1.18e+03 |

### candidate, augmented (60 training, 59 test discharges, 18506 test rows)

| target | unit | inputs | blocked MAE | random folds, same discharges MAE | ratio | random folds, all development MAE |
|---|---|---|---:|---:|---:|---:|
| plasma_current | kA | clean | 0.703 | 0.485 | 1.45 | 0.472 |
| plasma_current | kA | noisy | 4.02 | 4.03 | 1.00 | 4.03 |
| R_mag_axis | mm | clean | 2.72 | 0.958 | 2.84 | 1.09 |
| R_mag_axis | mm | noisy | 3.69 | 3.04 | 1.21 | 3.09 |
| Z_mag_axis | mm | clean | 1.57 | 0.641 | 2.46 | 0.857 |
| Z_mag_axis | mm | noisy | 2.83 | 2.02 | 1.40 | 2.36 |
| R_x_point | mm | clean | 1.86 | 0.761 | 2.44 | 0.764 |
| R_x_point | mm | noisy | 3.56 | 2.84 | 1.26 | 2.57 |
| Z_x_point | mm | clean | 1.41 | 0.678 | 2.08 | 0.719 |
| Z_x_point | mm | noisy | 3.03 | 2.45 | 1.23 | 2.59 |
| R_strike_point_1 | mm | clean | 1.48 | 0.549 | 2.69 | 0.704 |
| R_strike_point_1 | mm | noisy | 2.95 | 2.48 | 1.19 | 2.61 |
| Z_strike_point_1 | mm | clean | 0.694 | 0.273 | 2.54 | 0.303 |
| Z_strike_point_1 | mm | noisy | 1.25 | 1.02 | 1.23 | 1.02 |
| R_strike_point_2 | mm | clean | 1.94 | 0.917 | 2.12 | 0.873 |
| R_strike_point_2 | mm | noisy | 4.13 | 3.22 | 1.28 | 3.1 |
| Z_strike_point_2 | mm | clean | 0.363 | 0.184 | 1.98 | 0.181 |
| Z_strike_point_2 | mm | noisy | 0.785 | 0.61 | 1.29 | 0.596 |
| R_limiter | mm | clean | 19.7 | 12.1 | 1.63 | 10.4 |
| R_limiter | mm | noisy | 27.3 | 24.7 | 1.10 | 22.2 |
| Z_limiter | mm | clean | 32.1 | 19.9 | 1.61 | 19.4 |
| Z_limiter | mm | noisy | 51.3 | 43.7 | 1.17 | 41.8 |

