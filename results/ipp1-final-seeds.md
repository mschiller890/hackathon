# IPP 1: seed noise of the final comparison (locked test set)

Baseline MLP against the plain candidate (differences, Huber, 150 epochs, ridge for plasma current, gated limiter network), clean inputs, 5 seeds each (0, 1, 2, 3, 4; seed 0 is the model of `results/ipp1-final.md`). Recipes, split and metrics are those of `analysis/final_evaluation.py` unchanged; every model is trained on the 119 development discharges and scored on the 30 locked discharges, nothing was tuned after seeing them. Pooled MAE over the locked rows (mm, plasma current in kA); mean and standard deviation (n-1) over seeds. Aggregate numbers only.

| target | baseline mean (SD) | candidate mean (SD) | ratio of means | paired ratio per seed, min to max | candidate better in | worst candidate seed against best baseline seed |
|---|---:|---:|---:|---:|---:|---:|
| R_mag_axis (mm) | 0.289 (0.011) | 0.133 (0.006) | 0.46 | 0.43 to 0.50 | 5 of 5 | 0.50 |
| Z_mag_axis (mm) | 0.33 (0.021) | 0.192 (0.016) | 0.58 | 0.54 to 0.67 | 5 of 5 | 0.67 |
| R_x_point (mm) | 0.141 (0.015) | 0.111 (0.0066) | 0.79 | 0.71 to 0.96 | 5 of 5 | 0.97 |
| R_strike_point_2 (mm) | 0.206 (0.013) | 0.116 (0.015) | 0.56 | 0.49 to 0.68 | 5 of 5 | 0.72 |
| R_limiter (mm) | 10.8 (0.35) | 4.68 (0.32) | 0.43 | 0.41 to 0.48 | 5 of 5 | 0.48 |
| Z_limiter (mm) | 21.3 (0.93) | 8.61 (0.47) | 0.40 | 0.37 to 0.46 | 5 of 5 | 0.46 |
| plasma_current (kA) | 1.12 (0.057) | 0.0347 (0) | 0.03 | 0.03 to 0.03 | 5 of 5 | 0.03 |

The last column is the maximum candidate MAE over the minimum baseline MAE: below 1 the two seed ranges do not overlap, so the ordering holds for any pair of seeds, not only for equal seeds. Paired ratio = candidate over baseline with the same seed.

Per seed pooled MAE (baseline / candidate):

| target | seed 0 | seed 1 | seed 2 | seed 3 | seed 4 |
|---|---:|---:|---:|---:|---:|
| R_mag_axis (mm) | 0.307 / 0.133 | 0.281 / 0.124 | 0.282 / 0.14 | 0.29 / 0.134 | 0.283 / 0.135 |
| Z_mag_axis (mm) | 0.321 / 0.172 | 0.313 / 0.208 | 0.348 / 0.203 | 0.357 / 0.198 | 0.313 / 0.18 |
| R_x_point (mm) | 0.161 / 0.115 | 0.119 / 0.114 | 0.142 / 0.108 | 0.141 / 0.116 | 0.141 / 0.1 |
| R_strike_point_2 (mm) | 0.212 / 0.136 | 0.189 / 0.128 | 0.21 / 0.104 | 0.199 / 0.103 | 0.222 / 0.108 |
| R_limiter (mm) | 10.6 / 4.55 | 10.6 / 4.39 | 11.4 / 4.98 | 10.7 / 4.42 | 10.6 / 5.07 |
| Z_limiter (mm) | 22.5 / 8.35 | 21.8 / 8.91 | 21.1 / 8.11 | 20 / 9.27 | 21.3 / 8.43 |
| plasma_current (kA) | 1.2 / 0.0347 | 1.11 / 0.0347 | 1.11 / 0.0347 | 1.13 / 0.0347 | 1.04 / 0.0347 |

## Reading

- **The ordering holds in every seed for all seven targets**, both for the same seed (paired, 5 of 5) and for any pair of seeds (worst candidate seed against
  best baseline seed is below 1 everywhere). Seed 0 reproduces the numbers of `results/ipp1-final.md` exactly.
- Seed noise (SD over mean) is 3 to 11 % for the baseline and 5 to 13 % for the candidate; the gains for the axis, the strike point and the limiter point
  are 42 to 60 % (ratio of means 0.40 to 0.58), several times the seed noise, and far larger for the plasma current.
- **R_x_point is the weak one**: mean gain 21 % (0.141 to 0.111 mm), the paired ratio reaches 0.96 in the closest seed, and the worst candidate seed is only 3 %
  below the best baseline seed (0.97). Say "somewhat better", not "clearly better", for the X point R.
- The candidate's plasma current error is 0.0347 kA in every seed with SD 0 because that column comes from a ridge regression, which has no seed. It is not a
  sign of a very stable network; the ridge is a linear fit on the 24 inputs and is about 30 times better than the network for this target.
- Not covered: five seeds give a rough SD only; seed noise does not include the choice of the 30 locked discharges (see the bootstrap intervals in
  `results/ipp1-final.md`); noisy inputs and the augmented recipes were not rerun.
