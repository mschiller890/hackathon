# Stability over time (REQ-003)

Out-of-fold predictions. MAE by tenth of the relative discharge time, jitter ratio (RMS of the row-to-row change of the prediction divided by the same for the truth; 1 means equally smooth) and the share of the squared error that is a whole-discharge offset.

| target | unit | 0-10 % | 10-20 % | 20-30 % | 30-40 % | 40-50 % | 50-60 % | 60-70 % | 70-80 % | 80-90 % | 90-100 % | jitter | offset share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plasma_current | kA | 1.24 | 1.33 | 1.52 | 1.2 | 1.24 | 1.24 | 1.34 | 1.5 | 1.89 | 2.36 | 1.07 | 0.30 |
| R_mag_axis | mm | 0.598 | 0.276 | 0.285 | 0.259 | 0.24 | 0.236 | 0.232 | 0.286 | 0.446 | 0.9 | 0.97 | 0.10 |
| Z_mag_axis | mm | 0.457 | 0.261 | 0.356 | 0.296 | 0.294 | 0.3 | 0.297 | 0.333 | 0.462 | 0.848 | 1.06 | 0.05 |
| elongation |  | 0.00449 | 0.00634 | 0.00727 | 0.00524 | 0.00399 | 0.00382 | 0.00397 | 0.00434 | 0.00725 | 0.0101 | 1.03 | 0.13 |
| triangularity |  | 0.00238 | 0.00302 | 0.00305 | 0.00223 | 0.00205 | 0.002 | 0.00205 | 0.00233 | 0.00383 | 0.00545 | 1.05 | 0.14 |
| R_x_point | mm | nan | 0.322 | 0.186 | 0.153 | 0.149 | 0.156 | 0.176 | 0.226 | 0.399 | 0.313 | 1.00 | 0.62 |
| R_strike_point_1 | mm | nan | 0.356 | 0.231 | 0.276 | 0.248 | 0.241 | 0.215 | 0.267 | 0.363 | 0.381 | 1.00 | 0.81 |