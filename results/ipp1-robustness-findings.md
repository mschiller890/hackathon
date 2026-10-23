# IPP 1: robustness, amount of data, time context (lane R)

Evidence for REQ-B02, REQ-B04, REQ-B06. Same masked MLP and 5 folds split by whole discharge as the baseline
(`analysis/ipp1_common.py`). Mean absolute error (MAE) on held-out discharges, mean over 5 folds. Full tables:
`out/ipp1-{robustness,learning_curve,temporal}.{json,md}` (not in git); figures next to this file. Each script is run with
`HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/<name>.py`, about 1 to 2.5 minutes each. Checks of the
helper logic: `python -I results/ipp1-robustness-checks.py` (4 tests, OK).

Sanity: the noise-free full-data case reproduces the baseline (R axis 0.377 mm, limiter 10.7 and 22.2 mm,
`is_limited` 99.26 %).

## 1. Noise and drift (`ipp1-robustness.png`)

Synthetic noise is Gaussian, per row, with SD as a fraction of each input's training SD. The provided noisy file differs
from the clean one by 0.155 of an input SD (median), and the synthetic level 0.15 gives the same errors (R axis 10.4 mm
synthetic against 10.2 mm provided), so the synthetic noise is a fair stand in. Drift is `c * t`, an independent
Gaussian slope per discharge and coil, `t` the relative time; drift runs add noise 0.15.

| Trained on, tested on | R axis (mm) | Z axis (mm) | elongation | limiter Z (mm) | `is_limited` |
|---|---:|---:|---:|---:|---:|
| clean, clean | 0.38 | 0.39 | 0.0057 | 22.2 | 99.3 % |
| clean, provided noisy | 10.15 | 4.12 | 0.032 | 62.6 | 98.6 % |
| clean, noise 0.30 | 20.8 | 8.5 | 0.069 | 110 | 95.7 % |
| clean, noise 0.15 + drift 0.30 | 15.1 | 6.3 | 0.053 | 83.6 | 96.7 % |
| provided noisy, clean | 2.22 | 1.40 | 0.013 | 30.9 | 98.9 % |
| provided noisy, provided noisy | 2.64 | 2.01 | 0.019 | 37.6 | 98.7 % |
| provided noisy, noise 0.15 + drift 0.30 | 3.77 | 3.13 | 0.031 | 50.4 | 97.7 % |
| augmented, provided noisy | 2.74 | 2.13 | 0.020 | 38.5 | 98.5 % |
| augmented, noise 0.15 + drift 0.30 | 3.48 | 3.06 | 0.029 | 48.5 | 97.7 % |

- A model trained on clean data is very accurate and very fragile: the dataset's own noise makes the axis error 27 times
  larger (0.38 to 10.2 mm). Plasma current and the limiter point suffer too.
- Training on noisy rows (or on clean rows plus one corrupted copy) brings the noisy error to 2.6 to 2.7 mm. The price is
  accuracy on clean input: 2.2 mm against 0.38 mm. There is a clear trade-off between precision and robustness.
- Our augmentation (original plus one noise 0.15 and drift 0.15 copy) is no better than training on the provided noisy file:
  on the provided noisy test the R axis error is 2.74 against 2.64 mm, worse in 4 of 5 folds; under strong drift it is
  slightly better (3.48 against 3.77 mm, limiter Z 48.5 against 50.4 mm). Its use is that it does not need a noisy file.
- Drift hurts less than noise of the same size: slope SD 0.3 adds about 1 mm to the noisy-trained axis error.

## 2. Amount of training data (`ipp1-learning_curve.png`)

Nested subsets of the training discharges (mean 6, 12, 30, 60, 119 discharges; 1.7 k to 34 k rows), the same test folds.
Fixed 60 epochs, so smaller sets also get fewer optimizer updates.

| Training discharges | R axis (mm) | Z axis (mm) | X point R (mm) | elongation | limiter Z (mm) | `is_limited` |
|---:|---:|---:|---:|---:|---:|---:|
| 6 | 7.3 | 4.7 | 3.9 | 0.145 | 73.7 | 94.9 % |
| 12 | 6.9 | 2.8 | 1.5 | 0.075 | 55.6 | 96.8 % |
| 30 | 1.47 | 0.95 | 0.75 | 0.0116 | 34.3 | 98.9 % |
| 60 | 0.83 | 0.60 | 0.38 | 0.0086 | 28.8 | 99.1 % |
| 119 | 0.38 | 0.39 | 0.20 | 0.0057 | 22.2 | 99.3 % |

From 30 discharges up, the axis error roughly halves with every doubling and has not flattened at the full set (1.47,
0.83, 0.38 mm), so more discharges would still help; the limiter point improves slowest (34, 29, 22 mm). About 30 discharges already give about 1 mm on the axis.

## 3. Time context (`ipp1-temporal.png`)

Inputs from rows t-2, t-1, t of the same discharge (causal, the first row repeats at the start), 72 instead of 24 inputs.
"Error step" is the mean absolute change of the prediction error between consecutive samples (catches jitter and lag; a
constant prediction cannot win by being smooth).

| Input | Window | R axis (mm) | Z axis (mm) | limiter Z (mm) | error step R axis (mm) |
|---|---:|---:|---:|---:|---:|
| clean | 1 row | 0.377 | 0.392 | 22.2 | 0.102 |
| clean | 3 rows | 0.575 | 0.493 | 19.5 | 0.265 |
| provided noisy | 1 row | 2.64 | 2.01 | 37.6 | 1.84 |
| provided noisy | 3 rows | 2.33 | 1.51 | 30.4 | 1.15 |

- With noisy inputs three rows are better in all 5 folds for R axis, Z axis, elongation, limiter Z and the error step:
  Z axis 2.01 to 1.51 mm, jitter 1.84 to 1.15 mm. The history averages the noise out.
- With clean inputs three rows are worse for the axis (0.38 to 0.57 mm, worse in 5 of 5 folds for R) and better only for
  the limiter Z (22.2 to 19.5 mm, 5 of 5 folds). The larger input layer overfits where there is no noise to remove.
- Real time: the window needs the last two samples only, no future row, so the latency verdict does not change.

## Limits (state these in the talk)

- One initialization and one noise realization per fold; the fold to fold SD is descriptive, not a confidence interval.
  Differences of a few percent (for example augmented against noisy training) are not established.
- Drift is a model of ours (linear per coil), not a measured drift of the real diagnostics. Amplitudes were fixed before the
  run and were not tuned on test data.
- Dropped inputs, a bigger network or tuned epochs were not tried here; numbers are for the baseline architecture.
- Epochs are fixed (60, augmented 30 on twice the rows), so the learning curve mixes less information with fewer updates.
