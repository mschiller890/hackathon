# IPP 1: causal time window of the inputs against the provided noisy inputs

Script: `analysis/ipp1_noise_window.py` (imports `ipp1_common.py` and `ipp1_final.py` of the shipped analysis, read only). Development set = the 119 non-locked discharges, 5-fold GroupKFold by discharge (the folds of `ipp1_final.py`); the 30 locked discharges are scored once, by models trained on all 119. Selection = lowest mean pooled nRMSE over the 16 targets on the provided noisy inputs, out of fold. **One seed per model**: read differences below about 20 % as unresolved unless a bootstrap interval excludes 1.

Window k = rows t-k+1 .. t of the same discharge in `time` order, the first rows of a discharge repeat the first row, no future row. `stack` = the k rows side by side (24 k inputs); `mean` = x(t) plus the mean of the k rows (48 inputs). k is a count of samples, not a time in milliseconds. Augmented training: clean rows plus one copy with noise 0.15 and drift 0.15 of each input's SD applied per row before windowing (a consistent noisy history). `ema a` = causal exponential moving average of the k = 1 model's outputs within each discharge, y(t) = a p(t) + (1 - a) y(t-1), no training. Error step = RMS of the row-to-row change of the prediction error between neighbouring rows (as `ipp1_time.py`), a jitter measure.

Check of the k = 1 code path against the cached predictions of `ipp1_final.py` (same seeds), mean nRMSE (16) noisy: base_aug: ipp1_final 0.3129, this script 0.3129.

## Development cross-validation (pooled out of fold, 34,211 rows of 119 discharges)

MAE in mm (plasma_current in kA). `folds < k=1` = in how many of the 5 folds the config's mean nRMSE (16) on noisy inputs is lower than that of the k = 1 model of the same recipe.

| config | recipe | form | k | nRMSE16 noisy | folds < k=1 | plasma_current noisy | R_mag_axis noisy | Z_mag_axis noisy | R_x_point noisy | Z_x_point noisy | R_limiter noisy | Z_limiter noisy | err step R / Z noisy | nRMSE16 clean | R / Z axis clean | train s (5 folds) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base_aug_stack1 | base_aug | stack | 1 | 0.3129 |  | 4.77 | 2.99 | 2.27 | 2.43 | 2.38 | 22.7 | 39.3 | 4.82 / 3.75 | 0.2385 | 2.21 / 1.34 | 49 |
| base_aug_stack1_ema0.3 | base_aug | ema0.3 | 1 | 0.2967 | 5 | 4.23 | 2.77 | 1.83 | 2.02 | 2.11 | 25.7 | 38.2 | 2.32 / 1.87 | 0.2764 | 2.5 / 1.59 | 0 |
| base_aug_stack1_ema0.5 | base_aug | ema0.5 | 1 | 0.2828 | 5 | 3.6 | 2.71 | 1.84 | 2.06 | 1.96 | 22.8 | 36 | 2.64 / 2.02 | 0.2498 | 2.31 / 1.43 | 0 |
| cand_aug_stack1 | cand_aug | stack | 1 | 0.3321 |  | 4.03 | 3.09 | 2.36 | 2.57 | 2.59 | 22.2 | 41.8 | 4.94 / 3.82 | 0.1705 | 1.09 / 0.857 | 85 |
| cand_aug_stack1_ema0.3 | cand_aug | ema0.3 | 1 | 0.3048 | 5 | 3.6 | 2.79 | 1.9 | 2.14 | 2.25 | 24.1 | 38.5 | 2.41 / 1.9 | 0.2249 | 1.63 / 1.2 | 0 |
| cand_aug_stack1_ema0.5 | cand_aug | ema0.5 | 1 | 0.2941 | 5 | 2.84 | 2.76 | 1.93 | 2.19 | 2.13 | 21.5 | 36.8 | 2.76 / 2.06 | 0.1878 | 1.33 / 0.981 | 0 |
| base_aug_stack3 | base_aug | stack | 3 | 0.2637 | 5 | 4.12 | 2.64 | 1.78 | 1.94 | 1.71 | 18.7 | 32.5 | 3.27 / 2.01 | 0.2121 | 1.96 / 1.17 | 46 |
| cand_aug_stack3 | cand_aug | stack | 3 | 0.2748 | 5 | 2.67 | 2.86 | 1.86 | 1.98 | 1.96 | 18 | 33.1 | 3.99 / 2.34 | 0.1597 | 1.18 / 0.842 | 94 |
| base_aug_stack5 | base_aug | stack | 5 | 0.2511 | 5 | 3.89 | 2.47 | 1.59 | 1.8 | 1.61 | 17.7 | 32.2 | 2.8 / 1.6 | 0.2098 | 1.85 / 1.14 | 48 |
| cand_aug_stack5 | cand_aug | stack | 5 | 0.2685 | 5 | 2.5 | 2.86 | 1.75 | 1.83 | 1.9 | 17.2 | 31.7 | 3.86 / 1.9 | 0.1641 | 1.17 / 0.855 | 107 |
| base_aug_stack9 | base_aug | stack | 9 | 0.2548 | 5 | 3.96 | 2.38 | 1.55 | 1.67 | 1.64 | 17.4 | 30.9 | 2.45 / 1.46 | 0.2224 | 1.88 / 1.18 | 61 |
| cand_aug_stack9 | cand_aug | stack | 9 | 0.2620 | 5 | 2.46 | 2.74 | 1.69 | 1.71 | 1.86 | 17.9 | 30 | 3.56 / 1.79 | 0.1728 | 1.29 / 0.911 | 133 |
| base_aug_mean3 | base_aug | mean | 3 | 0.2690 | 5 | 4.05 | 2.71 | 1.8 | 1.88 | 1.84 | 19.4 | 33.8 | 3.66 / 2.29 | 0.2199 | 2.05 / 1.19 | 44 |
| cand_aug_mean3 | cand_aug | mean | 3 | 0.2783 | 5 | 2.69 | 2.88 | 1.88 | 2.03 | 1.92 | 18.5 | 33.4 | 4.29 / 2.53 | 0.1706 | 1.19 / 0.859 | 96 |
| base_aug_mean5 | base_aug | mean | 5 | 0.2520 | 5 | 3.72 | 2.58 | 1.62 | 1.75 | 1.64 | 18.5 | 32.1 | 3.43 / 1.98 | 0.2111 | 1.99 / 1.14 | 52 |
| cand_aug_mean5 | cand_aug | mean | 5 | 0.2654 | 5 | 2.67 | 2.9 | 1.71 | 1.82 | 1.81 | 18.1 | 30.3 | 4.78 / 2.27 | 0.1689 | 1.21 / 0.865 | 98 |
| base_aug_mean9 | base_aug | mean | 9 | 0.2531 | 5 | 3.67 | 2.48 | 1.52 | 1.77 | 1.67 | 18.9 | 32.8 | 3.34 / 1.95 | 0.2194 | 1.97 / 1.13 | 55 |
| cand_aug_mean9 | cand_aug | mean | 9 | 0.2674 | 5 | 2.96 | 2.92 | 1.61 | 1.81 | 1.9 | 18.6 | 31 | 5.45 / 2.33 | 0.1723 | 1.31 / 0.833 | 91 |

Selected (lowest nRMSE16 noisy among trained configs): **base_aug_stack5**.

## Locked test (30 discharges, 8,761 rows): base_aug_stack5 against the control base_aug_stack1

Scored once. The two EMA rows (outputs of the control smoothed, no training) were fixed as extras before the locked set was scored. MAE / p99 / max of the absolute error, mm (plasma_current kA).

### noisy inputs

| model | nRMSE16 | plasma_current MAE / p99 / max | R_mag_axis MAE / p99 / max | Z_mag_axis MAE / p99 / max | R_x_point MAE / p99 / max | Z_x_point MAE / p99 / max | R_limiter MAE / p99 / max | Z_limiter MAE / p99 / max | err step R / Z |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base_aug_stack1 | 0.2891 | 4.65 / 16.9 / 79.7 | 2.38 / 16.3 / 90.9 | 1.86 / 10.5 / 35.3 | 2.47 / 11.8 / 35.9 | 2.22 / 10.2 / 19.4 | 25.8 / 334 / 432 | 38.9 / 312 / 523 | 4.47 / 3.39 |
| base_aug_stack5 | 0.2187 | 3.56 / 18.9 / 40.9 | 1.85 / 14.7 / 83 | 1.25 / 7.77 / 47.1 | 1.64 / 9.06 / 21.9 | 1.58 / 7.83 / 13.1 | 18.4 / 303 / 482 | 29.1 / 249 / 527 | 2.7 / 1.56 |
| base_aug_stack1_ema0.3 | 0.2798 | 4.11 / 20.2 / 35 | 2.21 / 16.1 / 94.5 | 1.51 / 9.63 / 138 | 2.03 / 10.9 / 33.6 | 1.95 / 10.4 / 14.7 | 29.7 / 299 / 401 | 37.5 / 283 / 472 | 2.51 / 2.39 |
| base_aug_stack1_ema0.5 | 0.2606 | 3.45 / 13.6 / 39.2 | 2.13 / 14.9 / 87.5 | 1.49 / 9.45 / 98.6 | 2.06 / 11.3 / 34.9 | 1.8 / 9.75 / 16.9 | 25.9 / 296 / 405 | 35.1 / 276 / 479 | 2.72 / 2.14 |

Cluster bootstrap by discharge (1000 resamples): MAE ratio model / base_aug_stack1 with 95 % interval (below 1 = better).

| target | unit | base_aug_stack5 | base_aug_stack1_ema0.3 | base_aug_stack1_ema0.5 |
|---|---|---:|---:|---:|
| plasma_current | kA | 0.764 [0.704, 0.838] | 0.884 [0.840, 0.935] | 0.741 [0.722, 0.763] |
| R_mag_axis | mm | 0.777 [0.737, 0.814] | 0.929 [0.896, 0.964] | 0.896 [0.869, 0.923] |
| Z_mag_axis | mm | 0.673 [0.633, 0.714] | 0.812 [0.762, 0.867] | 0.802 [0.771, 0.839] |
| R_x_point | mm | 0.665 [0.616, 0.717] | 0.821 [0.763, 0.873] | 0.835 [0.783, 0.881] |
| Z_x_point | mm | 0.711 [0.679, 0.740] | 0.880 [0.832, 0.930] | 0.812 [0.780, 0.844] |
| R_limiter | mm | 0.714 [0.631, 0.791] | 1.153 [1.096, 1.216] | 1.004 [0.973, 1.036] |
| Z_limiter | mm | 0.749 [0.683, 0.826] | 0.964 [0.917, 1.016] | 0.902 [0.864, 0.942] |

### clean inputs

| model | nRMSE16 | plasma_current MAE / p99 / max | R_mag_axis MAE / p99 / max | Z_mag_axis MAE / p99 / max | R_x_point MAE / p99 / max | Z_x_point MAE / p99 / max | R_limiter MAE / p99 / max | Z_limiter MAE / p99 / max | err step R / Z |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base_aug_stack1 | 0.1998 | 1.91 / 9.17 / 72 | 1.56 / 10.6 / 62.6 | 0.837 / 6.84 / 26.6 | 1.56 / 10.9 / 31.5 | 1.11 / 8.57 / 17.1 | 18.6 / 236 / 420 | 25.7 / 235 / 442 | 1.37 / 0.635 |
| base_aug_stack5 | 0.1681 | 2.11 / 17.6 / 57.1 | 1.32 / 9.21 / 60.9 | 0.76 / 6.14 / 50.8 | 1.1 / 8.51 / 19.1 | 0.952 / 6.96 / 9.76 | 13.8 / 214 / 430 | 22.4 / 216 / 489 | 1.45 / 1.08 |
| base_aug_stack1_ema0.3 | 0.2564 | 3.56 / 21.1 / 35 | 1.93 / 14.6 / 80 | 1.18 / 7.85 / 142 | 1.68 / 10.1 / 31.6 | 1.67 / 9.56 / 13.5 | 26.3 / 298 / 397 | 31.5 / 301 / 459 | 2.11 / 2.26 |
| base_aug_stack1_ema0.5 | 0.2199 | 2.35 / 12.4 / 30.8 | 1.7 / 11.3 / 69.2 | 0.976 / 7.11 / 103 | 1.57 / 10.5 / 31.6 | 1.29 / 8.74 / 15.6 | 21.5 / 265 / 388 | 27.3 / 264 / 439 | 1.78 / 1.63 |

Cluster bootstrap by discharge (1000 resamples): MAE ratio model / base_aug_stack1 with 95 % interval (below 1 = better).

| target | unit | base_aug_stack5 | base_aug_stack1_ema0.3 | base_aug_stack1_ema0.5 |
|---|---|---:|---:|---:|
| plasma_current | kA | 1.107 [0.917, 1.317] | 1.865 [1.622, 2.196] | 1.232 [1.141, 1.358] |
| R_mag_axis | mm | 0.844 [0.788, 0.901] | 1.235 [1.177, 1.301] | 1.089 [1.063, 1.120] |
| Z_mag_axis | mm | 0.908 [0.810, 1.017] | 1.404 [1.260, 1.585] | 1.166 [1.100, 1.250] |
| R_x_point | mm | 0.706 [0.614, 0.787] | 1.082 [1.028, 1.158] | 1.011 [0.993, 1.035] |
| Z_x_point | mm | 0.854 [0.794, 0.928] | 1.494 [1.323, 1.722] | 1.156 [1.093, 1.237] |
| R_limiter | mm | 0.738 [0.641, 0.827] | 1.413 [1.329, 1.526] | 1.153 [1.119, 1.198] |
| Z_limiter | mm | 0.870 [0.764, 0.982] | 1.226 [1.173, 1.288] | 1.060 [1.039, 1.085] |

## Single-sample latency (numpy, one thread)

numpy only, one thread (OMP/OPENBLAS/VECLIB=1), single row per call incl. ring-buffer update of the last k rows; rows are the locked noisy inputs in time order. 5000 calls after 300 warm-up.

| model | median us | p99 us | mean us | max us |
|---|---:|---:|---:|---:|
| base_aug_stack1 | 17.8 | 30.5 | 18.2 | 90 |
| base_aug_stack5 | 18.2 | 43.4 | 19.1 | 119 |

## Verdict

Worth shipping for the noisy-input model, with one integration cost. In the development cross-validation every window beat k = 1 of the same recipe in 5 of 5 folds; base_aug with 5 stacked rows was selected (mean nRMSE16 noisy 0.2511 against 0.3129). The differences among k = 5, k = 9 and the mean form at k = 5 (0.2511 to 0.2548) are a few percent from one seed and are unresolved: the claim is 'a short causal window helps', not 'k = 5 is optimal'. On the locked set (scored once) the window lowers the noisy MAE on all seven headline targets with bootstrap intervals that exclude 1: R axis 2.38 to 1.85 mm (ratio 0.78 [0.74, 0.81]), Z axis 1.86 to 1.25 mm (0.67 [0.63, 0.71]), X point 0.67 to 0.71, limiter 0.71 to 0.75, plasma current 0.76; the error step (jitter) of R axis falls from 4.47 to 2.70 mm. It also beats the augmented candidate's earlier locked numbers (2.60 / 1.95 mm). Not everything improves: the worst single row is larger for Z axis (47 against 35 mm) and R limiter (482 against 432 mm), and the p99 of the plasma current is higher (18.9 against 16.9 kA). On clean inputs the windowed model is also better than its control (R axis 1.32 against 1.56 mm) but stays far behind the plain candidate shipped for clean inputs (0.133 mm), so the clean model does not change. Output smoothing without retraining (EMA alpha 0.5) gets part of the gain on noisy inputs (R 0.90, Z 0.80) but makes clean inputs worse, so the window is the better tool. Latency is unchanged in practice: 18.2 against 17.8 us median, p99 43 against 31 us (numpy, one thread, machine load about 6). Caveats: one seed; k counts samples, so the deployed stream must have the same sampling interval as the data; the gain relies on the provided noise being largely independent from row to row, so a noise that is correlated in time would shrink it, and it does nothing for slow drift; the first 4 rows of a discharge see a shorter history. Integration: predict.py currently promises that rows are independent and order does not matter; the windowed model needs rows grouped by discharge and ordered by time (or a streaming call that keeps the last 5 rows).

## Reproduce

```
export HACKATHON_HOME="/Users/bladed/Documents/AIprogramy/Hackathon ship"
PY="$HACKATHON_HOME/.venv/bin/python"
$PY -I analysis/ipp1_noise_window.py --stage cv
$PY -I analysis/ipp1_noise_window.py --stage cv_mean
$PY -I analysis/ipp1_noise_window.py --stage locked
$PY -I analysis/ipp1_noise_window.py --stage latency
```

