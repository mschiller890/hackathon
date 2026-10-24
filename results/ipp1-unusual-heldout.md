# IPP 1: the oddest discharges left out of training alone (REQ-B08)

Script `analysis/ipp1_unusual_heldout.py`. **Wording: "osmnáct nejodlišnějších výbojů vynecháno z učení"; this does not test new shapes**: 18 discharges, one network, 3 seeds, and nothing is said about shapes outside the range of the data.

Network: the shared masked MLP of `common.fit_mlp` (the baseline network, 60 epochs). Groups by the median elongation of a discharge: **odd18** = the 18 discharges with median elongation below 1.74 (elongation 1.01 to 1.74, triangularity 0.02 to 0.33; the other 131 discharges train, 18 test) and **lowest5** = the 5 with the lowest median elongation (144 train, 5 test). Reference: the error on the same discharges in the random 5-fold split by discharge, same network and seeds (there they are held out together with other discharges and neighbours from the same campaign are in training). MAE and p99 of the absolute error pooled over the rows of the group, in mm (plasma current in kA, elongation and triangularity dimensionless); mean (SD over 3 seeds).

## odd18: 18 discharges, 3435 rows, 131 training discharges

| target | unit | MAE random folds | MAE left out | factor | p99 random folds | p99 left out |
|---|---|---:|---:|---:|---:|---:|
| plasma_current | kA | 3.18 (0.53) | 5.03 (0.9) | 1.6 | 26.2 | 34.1 |
| R_mag_axis | mm | 0.907 (0.092) | 2.26 (0.47) | 2.5 | 9.96 | 14.6 |
| Z_mag_axis | mm | 0.703 (0.064) | 1.46 (0.59) | 2.1 | 5.42 | 21.4 |
| elongation | - | 0.0122 (0.0016) | 0.0219 (0.00085) | 1.8 | 0.058 | 0.273 |
| triangularity | - | 0.00608 (0.00042) | 0.0109 (0.0012) | 1.8 | 0.0346 | 0.147 |
| R_x_point | mm | 0.219 (0.018) | 0.462 (0.062) | 2.1 | 1.13 | 2.68 |
| Z_x_point | mm | 0.182 (0.014) | 0.288 (0.097) | 1.6 | 1.2 | 1.86 |
| R_strike_point_1 | mm | 0.271 (0.018) | 0.327 (0.07) | 1.2 | 1.7 | 2.27 |
| R_strike_point_2 | mm | 0.329 (0.057) | 0.595 (0.092) | 1.8 | 1.49 | 3.51 |
| R_limiter | mm | 16 (5) | 36.5 (11) | 2.3 | 178 | 591 |
| Z_limiter | mm | 24.4 (3.2) | 28.4 (4.2) | 1.2 | 140 | 245 |

The elongation error left out, 0.0219, is 2.2 % of the range of the elongation in the data (1.01).

## lowest5: 5 discharges, 545 rows, 144 training discharges

| target | unit | MAE random folds | MAE left out | factor | p99 random folds | p99 left out |
|---|---|---:|---:|---:|---:|---:|
| plasma_current | kA | 4.25 (2.2) | 8.22 (5.7) | 1.9 | 20.5 | 62.1 |
| R_mag_axis | mm | 2.6 (0.38) | 4.89 (1.8) | 1.9 | 27.6 | 68 |
| Z_mag_axis | mm | 1.07 (0.039) | 2.82 (1.6) | 2.6 | 5.99 | 29.2 |
| elongation | - | 0.0195 (0.0083) | 0.0471 (0.013) | 2.4 | 0.0584 | 0.295 |
| triangularity | - | 0.0116 (0.0036) | 0.0265 (0.0026) | 2.3 | 0.0409 | 0.192 |
| R_x_point | mm | n/a | n/a | n/a | n/a | n/a |
| Z_x_point | mm | n/a | n/a | n/a | n/a | n/a |
| R_strike_point_1 | mm | n/a | n/a | n/a | n/a | n/a |
| R_strike_point_2 | mm | n/a | n/a | n/a | n/a | n/a |
| R_limiter | mm | 10.5 (1.4) | 60.6 (23) | 5.8 | 95.2 | 618 |
| Z_limiter | mm | 19.7 (8.3) | 24.9 (11) | 1.3 | 99.2 | 203 |

The elongation error left out, 0.0471, is 4.7 % of the range of the elongation in the data (1.01).

Ids of odd18: 2, 3, 4, 5, 6, 7, 8, 27, 28, 29, 30, 31, 33, 36, 70, 92, 127, 148; runs of consecutive numbers: 2 to 8, 27 to 31, 33, 36, 70, 92, 127, 148 (8 runs).
Ids of lowest5: 127, 6, 7, 148, 33; runs of consecutive numbers: 6 to 7, 33, 127, 148 (4 runs).

**Campaign order.** 14 of the 18 ids lie in the lowest quarter of all discharge numbers (up to 37), the start of the campaign order; so the factor mixes the shape with the early campaign, and the second group (the 5 lowest) has no rows of the X point and the strike points (those discharges are limited) which are marked n/a.

**Contiguity.** The 18 ids form 8 runs of consecutive numbers (the longest 7 numbers long), so they are not one block of the campaign order, but most of them are early (see above).

**Limits.** 18 discharges (5 in the second group) and 3 seeds; the random-fold reference has about 24 test discharges per fold and shares its training discharges with its neighbours, so it is optimistic; only the baseline network was used, not the shipped model; the least elongated discharges have conditional targets (X point, strike points, limiter) in few rows.
