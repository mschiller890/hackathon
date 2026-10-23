# Stability over time (REQ-003)

Out-of-fold predictions, all 16 targets. MAE by tenth of the relative discharge time (n/a = no rows of that target in the decile, for example the X-point and strike points do not exist at the start of a discharge), jitter ratio (RMS of the row-to-row change of the prediction divided by the same for the truth; amplitude weighted, it stays near 1 whenever the truth moves, so it does not prove a quiet output), error step (RMS of the row-to-row change of the prediction error, in report units) and the share of the squared error that is a constant offset of a whole discharge. The first and last tenth are the start and end of the discharge, where the equilibrium is least well defined.

## clean inputs, network trained on clean data

| target | unit | 0-10 % | 10-20 % | 20-30 % | 30-40 % | 40-50 % | 50-60 % | 60-70 % | 70-80 % | 80-90 % | 90-100 % | jitter | error step | step / truth step | offset share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 1.24 | 1.33 | 1.52 | 1.2 | 1.24 | 1.24 | 1.34 | 1.5 | 1.89 | 2.36 | 1.07 | 0.942 | 0.39 | 0.30 |
| R_mag_axis | mm | 0.598 | 0.276 | 0.285 | 0.259 | 0.24 | 0.236 | 0.232 | 0.286 | 0.446 | 0.9 | 0.97 | 0.451 | 0.18 | 0.10 |
| Z_mag_axis | mm | 0.457 | 0.261 | 0.356 | 0.296 | 0.294 | 0.3 | 0.297 | 0.333 | 0.462 | 0.848 | 1.06 | 1.46 | 0.58 | 0.05 |
| elongation |  | 0.00449 | 0.00634 | 0.00727 | 0.00524 | 0.00399 | 0.00382 | 0.00397 | 0.00434 | 0.00725 | 0.0101 | 1.03 | 0.00477 | 0.34 | 0.13 |
| triangularity |  | 0.00238 | 0.00302 | 0.00305 | 0.00223 | 0.00205 | 0.002 | 0.00205 | 0.00233 | 0.00383 | 0.00545 | 1.05 | 0.00272 | 0.34 | 0.14 |
| triangularity_upper |  | 0.00208 | 0.00265 | 0.00296 | 0.00265 | 0.00271 | 0.00269 | 0.00279 | 0.00309 | 0.00348 | 0.00453 | 1.01 | 0.00297 | 0.42 | 0.23 |
| triangularity_lower |  | 0.00339 | 0.00403 | 0.00395 | 0.00261 | 0.00245 | 0.00239 | 0.00239 | 0.00272 | 0.00505 | 0.00773 | 1.01 | 0.00351 | 0.34 | 0.12 |
| R_x_point | mm | n/a | 0.322 | 0.186 | 0.153 | 0.149 | 0.156 | 0.176 | 0.226 | 0.399 | 0.313 | 1.00 | 0.0745 | 0.17 | 0.62 |
| Z_x_point | mm | n/a | 0.403 | 0.166 | 0.193 | 0.184 | 0.185 | 0.165 | 0.181 | 0.293 | 0.272 | 1.01 | 0.0858 | 0.08 | 0.68 |
| R_strike_point_1 | mm | n/a | 0.356 | 0.231 | 0.276 | 0.248 | 0.241 | 0.215 | 0.267 | 0.363 | 0.381 | 1.00 | 0.0956 | 0.10 | 0.81 |
| Z_strike_point_1 | mm | n/a | 0.272 | 0.113 | 0.124 | 0.109 | 0.104 | 0.102 | 0.142 | 0.238 | 0.183 | 0.99 | 0.0434 | 0.12 | 0.65 |
| R_strike_point_2 | mm | n/a | 0.708 | 0.229 | 0.176 | 0.163 | 0.202 | 0.194 | 0.235 | 0.4 | 0.414 | 0.99 | 0.121 | 0.14 | 0.48 |
| Z_strike_point_2 | mm | n/a | 0.0961 | 0.0496 | 0.0426 | 0.0377 | 0.0464 | 0.0437 | 0.0583 | 0.122 | 0.087 | 0.96 | 0.0521 | 0.30 | 0.23 |
| R_limiter | mm | 15.5 | 8.15 | 10.1 | 12.7 | 12.4 | 15.2 | 13.6 | 6.34 | 7.6 | 9.41 | 0.69 | 31 | 0.64 | 0.09 |
| Z_limiter | mm | 6.15 | 23.7 | 38.6 | 35.6 | 25.6 | 36.5 | 28.6 | 19.2 | 30.2 | 18.2 | 0.48 | 38.3 | 0.84 | 0.12 |
| is_limited |  | 0.00683 | 0.0163 | 0.0291 | 0.0232 | 0.0144 | 0.0135 | 0.0121 | 0.0262 | 0.0403 | 0.0209 | 0.40 | 0.0937 | 0.91 | 0.02 |

## Noisy inputs (equil_data_noisy.csv, out-of-fold)

Same metrics for the plain network on noisy inputs and for the network hardened with noise and drift augmentation. jitter = jitter ratio, step = error step in report units, ratio = error step / RMS change of the truth. A ratio near 0 means the error does not wobble from row to row; above 1 the wobble of the error is larger than the movement of the truth.

| target | unit | truth step | jitter clean | jitter plain | jitter hardened | step clean | step plain | step hardened | ratio clean | ratio plain | ratio hardened |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 2.39 | 1.07 | 4.47 | 3.27 | 0.942 | 10.4 | 7.45 | 0.39 | 4.37 | 3.12 |
| R_mag_axis | mm | 2.5 | 0.97 | 8.42 | 1.71 | 0.451 | 21 | 4.35 | 0.18 | 8.40 | 1.74 |
| Z_mag_axis | mm | 2.53 | 1.06 | 3.25 | 1.65 | 1.46 | 7.94 | 3.53 | 0.58 | 3.14 | 1.39 |
| elongation |  | 0.014 | 1.03 | 4.42 | 2.45 | 0.00477 | 0.0603 | 0.0324 | 0.34 | 4.32 | 2.32 |
| triangularity |  | 0.00788 | 1.05 | 4.54 | 2.12 | 0.00272 | 0.035 | 0.0154 | 0.34 | 4.44 | 1.96 |
| triangularity_upper |  | 0.00715 | 1.01 | 7.02 | 2.27 | 0.00297 | 0.0498 | 0.0152 | 0.42 | 6.97 | 2.13 |
| triangularity_lower |  | 0.0105 | 1.01 | 4.34 | 2.17 | 0.00351 | 0.0445 | 0.0213 | 0.34 | 4.25 | 2.04 |
| R_x_point | mm | 0.442 | 1.00 | 17.84 | 6.76 | 0.0745 | 7.87 | 2.98 | 0.17 | 17.81 | 6.74 |
| Z_x_point | mm | 1.02 | 1.01 | 5.60 | 3.40 | 0.0858 | 5.64 | 3.38 | 0.08 | 5.51 | 3.30 |
| R_strike_point_1 | mm | 0.965 | 1.00 | 6.15 | 3.56 | 0.0956 | 5.86 | 3.35 | 0.10 | 6.08 | 3.47 |
| Z_strike_point_1 | mm | 0.351 | 0.99 | 7.14 | 3.96 | 0.0434 | 2.48 | 1.37 | 0.12 | 7.08 | 3.91 |
| R_strike_point_2 | mm | 0.883 | 0.99 | 9.78 | 4.39 | 0.121 | 8.6 | 3.83 | 0.14 | 9.73 | 4.33 |
| Z_strike_point_2 | mm | 0.172 | 0.96 | 9.56 | 4.14 | 0.0521 | 1.64 | 0.703 | 0.30 | 9.51 | 4.09 |
| R_limiter | mm | 48.7 | 0.69 | 2.57 | 0.86 | 31 | 132 | 57.9 | 0.64 | 2.71 | 1.19 |
| Z_limiter | mm | 45.4 | 0.48 | 2.78 | 1.30 | 38.3 | 133 | 71.4 | 0.84 | 2.94 | 1.57 |
| is_limited |  | 0.103 | 0.40 | 1.08 | 0.72 | 0.0937 | 0.143 | 0.116 | 0.91 | 1.39 | 1.12 |

### MAE by tenth of the discharge, noisy inputs, network trained on clean data

| target | unit | 0-10 % | 10-20 % | 20-30 % | 30-40 % | 40-50 % | 50-60 % | 60-70 % | 70-80 % | 80-90 % | 90-100 % | offset share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 6.94 | 5.76 | 6.1 | 5.7 | 5.63 | 5.68 | 5.6 | 5.73 | 6.02 | 6.9 | 0.08 |
| R_mag_axis | mm | 18.2 | 9.94 | 8.44 | 7.72 | 7.55 | 7.48 | 7.47 | 7.77 | 9.97 | 16.7 | 0.00 |
| Z_mag_axis | mm | 5.29 | 3.5 | 3.45 | 3.55 | 3.61 | 3.59 | 3.58 | 3.84 | 4.2 | 6.52 | 0.01 |
| elongation |  | 0.0313 | 0.0475 | 0.0392 | 0.0287 | 0.0232 | 0.0231 | 0.0236 | 0.024 | 0.0351 | 0.0423 | 0.01 |
| triangularity |  | 0.017 | 0.0224 | 0.0192 | 0.0161 | 0.0146 | 0.0146 | 0.0148 | 0.0158 | 0.021 | 0.0267 | 0.02 |
| triangularity_upper |  | 0.0139 | 0.0172 | 0.024 | 0.029 | 0.031 | 0.0299 | 0.0287 | 0.0296 | 0.0279 | 0.0273 | 0.02 |
| triangularity_lower |  | 0.0221 | 0.0306 | 0.0262 | 0.0209 | 0.0191 | 0.017 | 0.0165 | 0.017 | 0.0258 | 0.0335 | 0.02 |
| R_x_point | mm | n/a | 4.3 | 4.62 | 4.6 | 4.5 | 4.38 | 4.11 | 4.28 | 4.65 | 4.16 | 0.01 |
| Z_x_point | mm | n/a | 3.66 | 3.45 | 3.3 | 3.2 | 3.16 | 2.97 | 3.07 | 3.28 | 3.05 | 0.03 |
| R_strike_point_1 | mm | n/a | 3.51 | 3.37 | 3.34 | 3.28 | 3.31 | 3.34 | 3.27 | 3.42 | 3.26 | 0.04 |
| Z_strike_point_1 | mm | n/a | 0.397 | 1.21 | 1.6 | 1.57 | 1.22 | 1.01 | 1.07 | 1.22 | 1.11 | 0.04 |
| R_strike_point_2 | mm | n/a | 6.14 | 5.17 | 4.84 | 4.65 | 4.59 | 4.36 | 4.66 | 5.19 | 4.57 | 0.02 |
| Z_strike_point_2 | mm | n/a | 0.599 | 0.956 | 0.958 | 0.965 | 0.935 | 0.838 | 0.832 | 0.869 | 0.825 | 0.01 |
| R_limiter | mm | 83.5 | 33.9 | 31 | 35.6 | 35.2 | 32.1 | 41.4 | 31 | 33.4 | 45.3 | 0.06 |
| Z_limiter | mm | 31.8 | 78.9 | 96.9 | 96.6 | 66.8 | 66.3 | 65.3 | 53.6 | 66.6 | 43.7 | 0.04 |
| is_limited |  | 0.0284 | 0.0359 | 0.0494 | 0.0405 | 0.0292 | 0.0284 | 0.0348 | 0.0548 | 0.0719 | 0.0416 | 0.02 |

### MAE by tenth of the discharge, noisy inputs, network trained with noise and drift augmentation

| target | unit | 0-10 % | 10-20 % | 20-30 % | 30-40 % | 40-50 % | 50-60 % | 60-70 % | 70-80 % | 80-90 % | 90-100 % | offset share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 4.39 | 4.44 | 4.49 | 4.35 | 4.37 | 4.47 | 4.53 | 4.74 | 4.93 | 5.47 | 0.05 |
| R_mag_axis | mm | 4.46 | 2.15 | 1.95 | 1.96 | 2.12 | 2.22 | 2.06 | 2.31 | 2.93 | 5.47 | 0.17 |
| Z_mag_axis | mm | 1.18 | 1.36 | 1.74 | 1.65 | 1.88 | 2.17 | 2.04 | 2.15 | 2.71 | 4.45 | 0.15 |
| elongation |  | 0.0207 | 0.0313 | 0.0239 | 0.0149 | 0.0126 | 0.0123 | 0.0116 | 0.0135 | 0.0273 | 0.0347 | 0.13 |
| triangularity |  | 0.00963 | 0.0116 | 0.00965 | 0.0071 | 0.00689 | 0.00715 | 0.00724 | 0.00871 | 0.0138 | 0.0194 | 0.11 |
| triangularity_upper |  | 0.00748 | 0.00855 | 0.00821 | 0.00747 | 0.00919 | 0.0101 | 0.00994 | 0.0116 | 0.0138 | 0.018 | 0.18 |
| triangularity_lower |  | 0.0125 | 0.0162 | 0.0146 | 0.0107 | 0.0104 | 0.00967 | 0.0093 | 0.011 | 0.0186 | 0.0241 | 0.10 |
| R_x_point | mm | n/a | 1.87 | 2.28 | 2.11 | 2.12 | 2.29 | 2.17 | 2.46 | 3.02 | 3.07 | 0.33 |
| Z_x_point | mm | n/a | 2.95 | 2.45 | 2.17 | 2.13 | 2.29 | 2.1 | 2.23 | 2.78 | 2.8 | 0.20 |
| R_strike_point_1 | mm | n/a | 3.12 | 2.28 | 2.13 | 2.07 | 2.25 | 2.21 | 2.28 | 2.59 | 2.72 | 0.20 |
| Z_strike_point_1 | mm | n/a | 0.443 | 0.856 | 1.04 | 0.991 | 0.827 | 0.701 | 0.832 | 1.12 | 1.01 | 0.20 |
| R_strike_point_2 | mm | n/a | 3.41 | 3.05 | 2.56 | 2.52 | 2.75 | 2.55 | 2.9 | 3.71 | 3.69 | 0.27 |
| Z_strike_point_2 | mm | n/a | 0.507 | 0.574 | 0.495 | 0.512 | 0.553 | 0.513 | 0.539 | 0.639 | 0.659 | 0.28 |
| R_limiter | mm | 40.4 | 17.5 | 17.9 | 19.8 | 15.1 | 13.2 | 12.4 | 14.9 | 17.5 | 22.7 | 0.03 |
| Z_limiter | mm | 10.3 | 45.9 | 70.3 | 66.7 | 36.7 | 39.3 | 27.3 | 33.7 | 50.1 | 28.1 | 0.06 |
| is_limited |  | 0.0132 | 0.0273 | 0.0444 | 0.0364 | 0.0248 | 0.0247 | 0.0199 | 0.0427 | 0.0677 | 0.0343 | 0.04 |


Note (independent review): the jitter ratio compares the RMS row to row step of prediction and truth; it stays near 1 whenever the output is smooth because its input is smooth, so it is not a noise measure. It holds on clean inputs only and only for the 7 targets above (the 13 non limiter targets on clean inputs span 0.96 to 1.07; the limiter points 0.69 and 0.48, because the true value jumps between wall points). On noisy inputs the output of a clean trained network jitters 8.4 times (R axis) and 3.3 times (Z axis) more than the truth, a network trained with noise 1.7 and 1.65 times (measured from out/ipp1-predictions-noise.csv, same definition and the same time gap filter as this table). Error growth: mainly at the end of a discharge (1.6 to 3.7 times the middle, taken as 30 to 70 % of the time); at the start only for the axis position (R 2.5 times, Z 1.5 times); "nan" means the target does not exist there (no X-point or strike points in the first decile). The offset share is the share of the squared error that is a whole discharge offset, not row to row noise.
