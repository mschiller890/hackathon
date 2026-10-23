# Fewer inputs: controls for the permutation-ranked subsets (REQ-004)

Folds run: 0, 1, 2, 3, 4 of 5. One seed per cell, fold SD is about 40 % of the mean, so read differences under 10 to 15 % as noise. Every subset was chosen on the training discharges of its fold only; all rows of one fold use the same seed and the same test discharges, so the rows are paired. Epochs 60. Summary error = mean relative error (RMSE / fold spread) over 13 targets, without the limiter point; lower is better. Columns after it are the mean absolute error in report units.

| inputs | summary error | plasma_current (kA) | R_mag_axis (mm) | Z_mag_axis (mm) | elongation (abs) | R_x_point (mm) | R_strike_point_1 (mm) | R_limiter (mm) |
|---|---|---|---|---|---|---|---|---|
| all 24 | 0.063 ± 0.028 | 1.49 | 0.377 | 0.391 | 0.00569 | 0.202 | 0.265 | 10.7 |
| permutation top 12 | 0.077 ± 0.024 | 1.51 | 0.629 | 0.662 | 0.00634 | 0.267 | 0.221 | 11.7 |
| random (mean of 3 draws) 12 | 0.099 ± 0.026 | 1.62 | 0.617 | 0.663 | 0.0078 | 0.534 | 0.487 | 14.8 |
| QR-pivot 12 | 0.065 ± 0.030 | 1.44 | 0.437 | 0.389 | 0.00587 | 0.203 | 0.251 | 11 |
| backward ridge 12 | 0.073 ± 0.029 | 1.4 | 0.447 | 0.422 | 0.00599 | 0.283 | 0.361 | 12.6 |
| permutation top 8 | 0.115 ± 0.051 | 1.58 | 1.17 | 1.07 | 0.00752 | 0.712 | 0.653 | 15.6 |
| random (mean of 3 draws) 8 | 0.151 ± 0.063 | 1.72 | 0.929 | 0.914 | 0.0109 | 0.998 | 0.789 | 18.9 |
| QR-pivot 8 | 0.072 ± 0.031 | 1.49 | 0.63 | 0.43 | 0.00549 | 0.265 | 0.289 | 12.3 |
| backward ridge 8 | 0.087 ± 0.028 | 1.58 | 0.644 | 0.812 | 0.00663 | 0.457 | 0.496 | 15.6 |
| permutation top 6 | 0.143 ± 0.053 | 2.08 | 1.62 | 1.58 | 0.00879 | 0.981 | 0.814 | 17 |
| random (mean of 3 draws) 6 | 0.214 ± 0.047 | 1.96 | 1.63 | 1.41 | 0.0133 | 1.51 | 1.52 | 21.3 |
| QR-pivot 6 | 0.126 ± 0.023 | 2.19 | 2.43 | 0.547 | 0.00914 | 0.697 | 0.498 | 15.6 |
| backward ridge 6 | 0.116 ± 0.020 | 1.94 | 1.21 | 0.985 | 0.00833 | 0.715 | 0.625 | 15.5 |

Summary error per fold (same order as the folds above):

| inputs | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 |
|---|---|---|---|---|---|
| all 24 | 0.067 | 0.057 | 0.041 | 0.037 | 0.115 |
| permutation top 12 | 0.074 | 0.089 | 0.052 | 0.056 | 0.116 |
| random (mean of 3 draws) 12 | 0.088 | 0.133 | 0.076 | 0.072 | 0.129 |
| QR-pivot 12 | 0.068 | 0.055 | 0.044 | 0.036 | 0.120 |
| backward ridge 12 | 0.070 | 0.092 | 0.044 | 0.041 | 0.117 |
| permutation top 8 | 0.099 | 0.112 | 0.074 | 0.076 | 0.214 |
| random (mean of 3 draws) 8 | 0.161 | 0.175 | 0.083 | 0.086 | 0.253 |
| QR-pivot 8 | 0.071 | 0.076 | 0.040 | 0.046 | 0.126 |
| backward ridge 8 | 0.088 | 0.088 | 0.056 | 0.066 | 0.137 |
| permutation top 6 | 0.122 | 0.119 | 0.117 | 0.107 | 0.249 |
| random (mean of 3 draws) 6 | 0.166 | 0.239 | 0.206 | 0.168 | 0.290 |
| QR-pivot 6 | 0.124 | 0.117 | 0.119 | 0.101 | 0.170 |
| backward ridge 6 | 0.109 | 0.099 | 0.112 | 0.105 | 0.156 |

Reading: the permutation ranking is the importance of an input for the trained network, not information content. A random subset of the same size and a model-free QR-pivot or ridge-selected subset show how much of the top-k curve comes from the ranking method and how much from the number of inputs.
