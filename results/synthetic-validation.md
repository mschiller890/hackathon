# Synthetic validation: a known plasma, simulated probe signals

**SIMULATED, NOT COMPASS DATA.** No IPP file was read or copied; the vessel contour, the probe layout and
every parameter range below are invented and only COMPASS-sized. Produced by `analysis/synth_validation.py`
(numbers in `results/synthetic-validation.json`), generator in `analysis/synth_equilibrium.py`,
walk-through in `notebooks/10_synthetic_validation.ipynb`.

## Plain reading (read this first)

- This is the closed test that `docs/review-physics.md` (H1, section 2) asks for: the truth is known
  because we built the plasma. It shows that **the method can recover a known plasma from simulated probe
  signals**: the same masked network recipe as the main work gets the magnetic axis to
  0.728 mm (R) and 0.602 mm (Z), the elongation to 0.00586,
  the triangularity to 0.00394 and the lower X point to 0.622 mm (R) and
  1.03 mm (Z), on whole synthetic discharges it never saw (400 epochs, clean signals, mean absolute error
  against the known truth).
- With white noise of the size of the organizers' noisy file (15 % of the spread on the coils, 9 % on the flux loops)
  the same quantities degrade to 5.17 mm, 4.26 mm, 0.03,
  0.0178, 2.42 mm and 5.06 mm when the network was trained on clean
  signals: noise at that size is the dominant error source, several times the clean error.
- **It says nothing about the real COMPASS reference labels**, about how close the reference reconstruction is to the real
  plasma, or about real probe calibration. The errors here are against an analytic truth; the 0.13 mm and 0.38 mm in
  `ipp1-final.md` and `ipp1-baseline.md` are agreements with the institute's reconstruction. The two sets of numbers are
  not comparable and neither is a bound on the other: the synthetic family has about seven free parameters, so the 24
  signals overdetermine it far more than they do a real plasma (see "What is NOT simulated").
- The synthetic clean error is not zero (0.728 mm on the axis) although the family is deterministic and noise
  free: that is the approximation error of this network on 3200 training rows, a floor that any real-data
  error also contains.

## What is simulated

- **Equations.** Solov'ev solutions of the Grad-Shafranov equation (constant p' and FF'), built after
  Cerfon and Freidberg, Phys. Plasmas 17, 032502 (2010), as `Delta* psi = (1 - A) x^2 + A` in units of the plasma major
  radius, plus 7 (limited) or 12 (diverted) homogeneous solutions whose coefficients are fixed by requiring the
  boundary `psi = 0` to pass through the outer, inner and top points of a requested shape with matching curvatures,
  and, for the diverted family, through a lower X point.
- **Two configurations.** `limited`: up-down symmetric, no X point (target columns `R_x_point`, `Z_x_point` are missing, so
  the masked loss and the masked score are exercised exactly as on the real file); `diverted`: lower single null.
  `is_limited` is 1 for the first family. Share of limited rows: 0.425.
- **Size.** R0 about 0.56 m, minor radius a about 0.2 m. Each discharge draws base values: plasma major radius 0.545 to
  0.575 m, a 0.185 to 0.205 m, vertical shift +-2 cm, requested elongation 1.05 to 1.6 (limited) or 1.3 to 1.55 (diverted),
  requested triangularity 0.0 to 0.35, profile parameter A -0.25 to 0.35, peak plasma current 120 to 260 kA; then every
  parameter drifts smoothly in time (amplitudes in `make_discharge`, elongation clipped to 1.0 to 1.8, triangularity to -0.05
  to 0.45) and the current ramps up and down (lowest value 42 kA).
- **Truth is measured, not copied.** The axis is the Newton-refined minimum of psi, the X point the Newton-refined saddle,
  the boundary extremes are Newton-refined points with `psi = 0` and the right derivative zero, and
  `elongation = (Z_top - Z_bottom) / (2 a)`, `triangularity = (delta_upper + delta_lower) / 2` are computed from those
  extremes (for the diverted family the bottom is the X point, so the measured elongation is about 1.05 times the requested one).
  Plasma current is set by integrating `-Delta* psi / (mu0 R)` over the plasma.
- **Probes.** 16 tangential poloidal field probes (equal arc length) and 8 flux loops (equal angle) on an invented rounded-box
  contour (half widths 0.30 m by 0.55 m about R = 0.56 m), evaluated **exactly** from the analytic psi and its derivatives
  (`B_R = -(1/R) dpsi/dZ`, `B_Z = (1/R) dpsi/dR`, flux `2 pi psi`). The inputs are named `IPR01..16` and `FL01..08`
  only to match the recipe; they are not the COMPASS channels.
- **Discharges.** 40 synthetic discharges of 100 time slices = 4000 rows. Each discharge draws a
  base shape and lets every parameter drift smoothly (two random low-frequency sinusoids) so that rows of one discharge are near
  copies, as in the real file; splits are by whole discharge (GroupKFold, 5 folds). 0 discharges were redrawn
  because a slice failed to solve or left the vessel.
- **Generator checks (measured when this report was written).** Largest `|Delta* phi|` of the homogeneous solutions
  3.4e-13; largest `|Delta* psi - source|` 8.9e-16 (limited) and
  2.0e-14 (diverted); Ampere's law, loop integral of `B.dl` over `mu0 Ip` along the traced boundary,
  1.0000 and 1.0001; requested to measured shape for one example
  (kappa 1.5, delta 0.3): limited 1.5000 and 0.3000,
  diverted 1.5750 and 0.3150 (the diverted values include the
  X point as the bottom).

Spread of the truth over the 4000 rows:

| target | unit | min | max | std |
|---|---|---:|---:|---:|
| plasma_current | kA | 44 | 253 | 52 |
| R_mag_axis | mm | 561 | 615 | 10.7 |
| Z_mag_axis | mm | -32.1 | 47.2 | 18.2 |
| elongation | - | 1 | 1.72 | 0.157 |
| triangularity | - | -0.0525 | 0.397 | 0.121 |
| R_x_point | mm | 467 | 584 | 27.8 |
| Z_x_point | mm | -381 | -250 | 27.1 |
| is_limited | - | 0 | 1 | 0.494 |

## What is NOT simulated

- **No real vessel currents and no coil currents.** psi is a Solov'ev solution everywhere, so outside the separatrix it is the
  analytic continuation, which carries toroidal current there and has no external coils. A real tokamak has a vacuum
  outside the plasma plus coil and wall-current fields. The probe signals therefore carry a different mixture of
  information than real ones; whether that makes the task easier or harder was not tested.
- **No real calibration.** No probe position or orientation errors, gains, offsets, integrator drift, cross-talk or
  missing channels. The flux is measured relative to the separatrix flux (the gauge is fixed by `psi = 0` on the boundary).
  The probe layout is invented, not the COMPASS layout.
- **No EFIT or any reconstruction code.** The truth is an analytic solution, not the output of a reconstruction with its grid,
  constraints and regularisation. Nothing here measures the agreement between a network and such a code.
- **No disruptions, ELMs or fast dynamics, no eddy-current delays.** Every slice is an independent static equilibrium whose
  parameters drift smoothly.
- **A narrow family.** About seven free parameters (R0p, a, kappa, delta, A, vertical shift, Ip) plus the configuration, so
  24 signals overdetermine it. Real profiles are far richer. This makes the test optimistic about recovering shape from probes.
- **No consistent vacuum exterior (tried, dropped).** An attempt to replace the continuation by the field of the plasma current
  (current filaments from the Solov'ev interior) plus fitted external coil filaments was ill-posed: the fit to the boundary flux left
  0.25 % residual, needed coil currents of order 1e8 A and gave flux-loop values that were not credible. It is not used anywhere.
- **No limiter physics and no upper X point or double null.** `limited` is only the symmetric no-X-point family.
- **No second solver.** The finite-difference fixed-boundary Grad-Shafranov solve named as a second choice was not built;
  the analytic family was enough for the closed test and the time was spent on checking it.
- Noise is white and independent per row, with no drift (as measured in `ipp1-data-checks.md` for the organizers' file).

## Method

- Network: the recipe of `analysis/ipp1_common.py` (256-256-128, SiLU, AdamW lr 2e-3 weight decay 1e-4, OneCycle max lr 3e-3,
  batch 512, standardised inputs and targets, loss masked to the targets that exist), copied into `analysis/synth_validation.py`.
  Targets: plasma_current, R_mag_axis, Z_mag_axis, elongation, triangularity, R_x_point, Z_x_point, is_limited.
- Baseline: ridge regression per target on standardised inputs (the same one `ipp1_common.py` uses).
- Splits: 5-fold GroupKFold by synthetic discharge; every row is predicted once out of fold and the errors are pooled.
- Noise: each channel gets white noise of 15 % (coils) or 9 % (flux loops) of that channel's standard deviation over all
  rows, as `ipp1-data-checks.md` measured for the organizers' noisy file. Training noise and test noise are two different draws.
- Scenarios: train clean to test clean; train clean to test noisy; train noisy to test noisy.
- Epochs: 60 (the recipe's default) and 400. With about 3200 training rows, 60 epochs is only about
  420 optimiser steps and the network is under-trained, so both settings are given in full. Neither was tuned further.
  Each MLP number is the mean over 3 seeds of the pooled out-of-fold error.
- MAE is in mm for positions, kA for the current and dimensionless for kappa, delta and `is_limited` (for the last one it is the
  mean absolute difference of the network output and the 0/1 flag; the accuracy is in the JSON). nRMSE is the pooled RMSE divided by the
  standard deviation of the truth, so 1.0 is the error of always guessing the mean.

## Results: MLP, 400 epochs

| target | unit | truth std | MAE clean to clean | nRMSE clean to clean | MAE clean to noisy | nRMSE clean to noisy | MAE noisy to noisy | nRMSE noisy to noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 52 | 2.05 | 0.0639 | 9.17 | 0.233 | 16 | 0.405 |
| R_mag_axis | mm | 10.7 | 0.728 | 0.0991 | 5.17 | 0.675 | 6.54 | 0.771 |
| Z_mag_axis | mm | 18.2 | 0.602 | 0.0528 | 4.26 | 0.339 | 5.32 | 0.396 |
| elongation | - | 0.157 | 0.00586 | 0.0556 | 0.03 | 0.263 | 0.0404 | 0.352 |
| triangularity | - | 0.121 | 0.00394 | 0.0501 | 0.0178 | 0.2 | 0.0294 | 0.316 |
| R_x_point | mm | 27.8 | 0.622 | 0.0344 | 2.42 | 0.12 | 3.22 | 0.162 |
| Z_x_point | mm | 27.1 | 1.03 | 0.0546 | 5.06 | 0.257 | 7.98 | 0.392 |
| is_limited | - | 0.494 | 0.0132 | 0.042 | 0.0446 | 0.144 | 0.0339 | 0.112 |

Fold-to-fold spread of the R axis MAE for clean to clean (seed 0, mm): 0.60, 0.79, 0.59, 0.72, 1.18.

## Results: MLP, 60 epochs

| target | unit | truth std | MAE clean to clean | nRMSE clean to clean | MAE clean to noisy | nRMSE clean to noisy | MAE noisy to noisy | nRMSE noisy to noisy |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 52 | 5.39 | 0.147 | 9.7 | 0.242 | 11.3 | 0.284 |
| R_mag_axis | mm | 10.7 | 2 | 0.278 | 4.7 | 0.583 | 4.99 | 0.608 |
| Z_mag_axis | mm | 18.2 | 1.41 | 0.117 | 3.91 | 0.308 | 3.55 | 0.272 |
| elongation | - | 0.157 | 0.0148 | 0.125 | 0.0301 | 0.255 | 0.0322 | 0.27 |
| triangularity | - | 0.121 | 0.00686 | 0.0823 | 0.0178 | 0.199 | 0.0182 | 0.201 |
| R_x_point | mm | 27.8 | 1.18 | 0.0586 | 2.41 | 0.116 | 2.12 | 0.103 |
| Z_x_point | mm | 27.1 | 2.26 | 0.113 | 4.95 | 0.248 | 4.63 | 0.222 |
| is_limited | - | 0.494 | 0.0298 | 0.0828 | 0.0496 | 0.141 | 0.0388 | 0.115 |

## Results: ridge baseline (independent of the epochs)

| target | unit | MAE clean to clean | nRMSE clean to clean | MAE clean to noisy | nRMSE clean to noisy | MAE noisy to noisy | nRMSE noisy to noisy |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 2.21 | 0.059 | 13.4 | 0.324 | 9.74 | 0.235 |
| R_mag_axis | mm | 2.15 | 0.285 | 6.31 | 0.748 | 4.92 | 0.584 |
| Z_mag_axis | mm | 6.13 | 0.449 | 8.01 | 0.569 | 6.36 | 0.46 |
| elongation | - | 0.0427 | 0.378 | 0.0607 | 0.498 | 0.0499 | 0.419 |
| triangularity | - | 0.036 | 0.404 | 0.0425 | 0.457 | 0.036 | 0.391 |
| R_x_point | mm | 7.05 | 0.368 | 9.35 | 0.444 | 7.13 | 0.355 |
| Z_x_point | mm | 7.95 | 0.399 | 12.3 | 0.586 | 8.28 | 0.396 |
| is_limited | - | 0.205 | 0.509 | 0.246 | 0.622 | 0.208 | 0.503 |

## What these numbers do and do not support

- Supported: on simulated static equilibria of this family, with exact invented probes, a 107 k-parameter network trained on
  whole discharges recovers the axis, elongation, triangularity and X point of a discharge it has not seen to a small fraction of the spread of the truth
  (nRMSE 0.0991 for R axis, 0.0528 for Z axis, 0.0344 for the X point R,
  clean signals). On clean signals ridge regression is clearly worse on every position-like target (they are not linear in the
  probe signals), while the current is nearly linear in the signals (ridge nRMSE 0.059,
  network 0.0639).
- Supported: noise at the size of the organizers' noisy file moves the axis error from about a millimetre to several millimetres.
  Training on one fixed noisy copy did not reduce it on the radial axis (4.7 mm trained clean against
  4.99 mm trained noisy at 60 epochs, 5.17 against 6.54 mm at 400),
  and under noise ridge is as good as the network on the radial axis (4.92 mm). That the long run
  overfits the one noise draw is a plausible reading, not tested. All of this is about this synthetic noise and this family; the
  main work found a gain from noise training on the real noisy file, and this test neither confirms nor contradicts that.
- Not supported: any statement about COMPASS, about how close the reference reconstruction is to the real plasma, about calibration, drift
  or disruptions, or that the real-data errors would be larger or smaller than these. The honest sentence for the talk is: "On a plasma we
  simulated ourselves, so that the truth is known, the same network recovers the axis to about a millimetre from clean probe signals.
  That tests the method, not the COMPASS labels."

## Reproduce

```
pip install numpy scipy scikit-learn torch
python -I analysis/synth_equilibrium.py                       # generator self-checks, about 10 s
python -I analysis/synth_validation.py --epochs 60 400 --seeds 3 --threads 2   # about 9 min, writes the json
python -I analysis/synth_validation.py --report               # rewrites this file from the json
```
