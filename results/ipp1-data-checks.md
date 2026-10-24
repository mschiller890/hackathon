# Data checks quoted on the slides

Measured with `analysis/data_checks.py` (aggregate numbers only).

## Spread of the targets (standard deviation, and the width of the band holding 98 percent of the values)

| target | unit | standard deviation | 98 percent band width |
|---|---|---:|---:|
| plasma_current | kA | 114.2 | 542.7 |
| R_mag_axis | mm | 8.022 | 42.3 |
| Z_mag_axis | mm | 13.74 | 56.43 |
| elongation | - | 0.2706 | 0.8363 |
| triangularity | - | 0.1194 | 0.4241 |
| triangularity_upper | - | 0.07492 | 0.2999 |
| triangularity_lower | - | 0.1724 | 0.598 |
| R_x_point | mm | 8.056 | 38.2 |
| Z_x_point | mm | 12.74 | 49.94 |
| R_strike_point_1 | mm | 12.55 | 52.29 |
| Z_strike_point_1 | mm | 5.033 | 20.34 |
| R_strike_point_2 | mm | 11.77 | 49.53 |
| Z_strike_point_2 | mm | 2.379 | 8.745 |
| R_limiter | mm | 89.6 | 424.4 |
| Z_limiter | mm | 153.3 | 497.6 |

## Structure of the noise in `equil_data_noisy.csv`

- Noise standard deviation over the standard deviation of the signal: IPR coils median 0.158, flux loops median 0.090, overall range 0.086 to 0.167.
- Mean absolute correlation of the noise with time inside a discharge (a linear drift would show here): 0.049.
- Mean lag-1 autocorrelation of the noise inside a discharge (white noise is about 0): -0.004.
- Reading: white noise, no measurable drift; every drift result of ours is synthetic.

## A network that sees only the first five principal components of the 24 inputs (5 folds by discharge, 60 epochs, seed 0)

| target | unit | all 24 inputs MAE | 5 components MAE | ratio |
|---|---|---:|---:|---:|
| R_mag_axis | mm | 0.4065 | 2.631 | 6.47 |
| Z_mag_axis | mm | 0.3961 | 0.653 | 1.65 |
| elongation | - | 0.006181 | 0.009209 | 1.49 |
| R_x_point | mm | 0.2319 | 1.007 | 4.34 |
| R_limiter | mm | 13.62 | 16.47 | 1.21 |

Reading: 99.9 percent of the variance is not 99.9 percent of the information; the low-variance directions carry what the targets need.