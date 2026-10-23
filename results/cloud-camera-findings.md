# Camera model for IPP task 1 (cloud session, independent second attempt)

Branch `cloud/camera`, draft PR https://github.com/BLADED-K/hackathon-cloud/pull/1. Scripts
`analysis/cloud_camera_prepare.py` and `analysis/cloud_camera_model.py`. Every number here comes from a run whose command
is given; tables with the full precision are in `results/cloud-camera-*.md` and `.json`. Status Fri 18:40 CEST:
`main` and `multimodal` done; `curve`, `augment`, then the noisy-magnetics fusion, occlusion and image parts
running or queued (rows marked `DOPLNIT`).

## Data (measured)

- Camera archive: 116,142 JPEG frames of 640x500 pixels from 78 of the 149 discharges (583 to 2166 frames per discharge),
  mapping file `camera_data.csv` (`filename`, `time`, `discharge`, `mode`).
- Matched to `equil_data.csv` (command `cloud_camera_prepare.py --time-scale 1 --size 48 64`): 115,872 frames; 270 frames
  lie outside the time range of their discharge, none in a wide gap. Divertor targets exist on 67,839 frames, limiter
  targets on 46,977.
- The frames carry little colour: mean |R-G|+|G-B| = 8.7 of 255 per pixel.
- Alignment check on the real cache: frame brightness against plasma current inside each discharge, mean Pearson 0.078
  over 78 discharges, 0.001 with labels shuffled inside each discharge. Weak but not zero; the real check is that the
  network learns on unseen discharges (below).

## Method

- Every frame gets the 24 magnetic inputs and 16 targets interpolated linearly in relative time between the two bracketing
  rows of its discharge (organizers' notebook: match per discharge, interpolate, not for `is_limited` and not across NaN):
  no extrapolation, NaN when a neighbour is NaN (masked loss), nearest row for `is_limited`, frames between rows more than
  5 median spacings apart dropped.
- Frames downscaled with a box filter to 48x64 (1 cached pixel = 10 original pixels = 1/64 of the width), cached as uint8
  outside git. Every 8th frame of each discharge is used (14,520 frames): neighbouring frames are near copies and this
  keeps a CPU fit at about 160 s.
- Small CNN: two coordinate channels, six 3x3 conv blocks (three with stride 2), 4x4 pooling, MLP head, 16 outputs, masked
  MSE on standardized targets as `ipp1_common.fit_mlp`, AdamW with OneCycle, 12 epochs, width 16, batch 128.
- 5-fold GroupKFold by whole discharge (15 or 16 test discharges per fold), MAE in mm and kA, nRMSE = RMSE over the
  spread of the target, `ipp1_common.score`.
- The settings were fixed before the 5-fold run after one `--dev` run (inner split of fold 0's training discharges); no
  alternative setting was compared there. Note: those validation discharges are test discharges of folds 2 to 5, so any
  future selection on `--dev` must be reported on fold 1 alone or nested per fold.
- Checked first on a synthetic fixture outside the repository (extraction safety, interpolation against hand-computed
  values, the gap rule, time-unit detection, learning). This found a label/image misalignment bug in the cache step
  (labels indexed by the position among decoded frames instead of the original row); it is fixed and guarded by an
  assertion.

## Results: camera CNN, 5 folds by discharge (`results/cloud-camera-main.md`)

Command: `cloud_camera_model.py main --size 48x64 --stride 8 --epochs 12 --width 16 --folds 5 --sweep-step 4`.
The magnetic columns come from `results/ipp1-baseline.md` (all 149 discharges, other folds): orientation only, not a
like-for-like comparison; the like-for-like one is `multimodal` below.

| target | unit | colour MAE ± fold SD | grey MAE ± fold SD | camera nRMSE (grey) | magnetic MLP MAE | magnetic nRMSE | nRMSE camera / magnetic |
|---|---|---|---|---|---|---|---|
| plasma_current | kA | 14.6 ± 6.5 | 14.0 ± 6.0 | 0.356 | 1.49 | 0.027 | 13.2 |
| R_mag_axis | mm | 1.79 ± 0.42 | 1.70 ± 0.40 | 0.447 | 0.377 | 0.139 | 3.2 |
| Z_mag_axis | mm | 2.48 ± 0.61 | 2.40 ± 0.73 | 0.489 | 0.391 | 0.107 | 4.6 |
| elongation |  | 0.0160 ± 0.0031 | 0.0162 ± 0.0031 | 0.122 | 0.00569 | 0.041 | 3.0 |
| triangularity |  | 0.0090 ± 0.0014 | 0.0086 ± 0.0013 | 0.147 | 0.00284 | 0.048 | 3.0 |
| triangularity_upper |  | 0.0095 ± 0.0017 | 0.0089 ± 0.0020 | 0.250 | 0.00297 | 0.080 | 3.1 |
| triangularity_lower |  | 0.0130 ± 0.0027 | 0.0125 ± 0.0022 | 0.143 | 0.00368 | 0.044 | 3.3 |
| R_x_point | mm | 1.54 ± 0.31 | 1.50 ± 0.41 | 0.310 | 0.202 | 0.067 | 4.6 |
| Z_x_point | mm | 2.05 ± 0.90 | 2.18 ± 0.91 | 0.395 | 0.195 | 0.039 | 10.2 |
| R_strike_point_1 | mm | 2.27 ± 0.83 | 2.25 ± 0.73 | 0.336 | 0.265 | 0.051 | 6.6 |
| Z_strike_point_1 | mm | 0.78 ± 0.36 | 0.79 ± 0.34 | 0.304 | 0.131 | 0.067 | 4.6 |
| R_strike_point_2 | mm | 2.11 ± 0.76 | 2.18 ± 0.95 | 0.406 | 0.228 | 0.045 | 9.1 |
| Z_strike_point_2 | mm | 0.42 ± 0.15 | 0.42 ± 0.17 | 0.386 | 0.055 | 0.068 | 5.7 |
| R_limiter | mm | 12.8 ± 1.7 | 13.1 ± 2.4 | 0.409 | 10.7 | 0.317 | 1.3 |
| Z_limiter | mm | 28.8 ± 1.3 | 28.7 ± 3.1 | 0.349 | 22.2 | 0.270 | 1.3 |

`is_limited` accuracy: colour 0.976, grey 0.975 (magnetic 0.993). Training about 160 s per fit on 4 CPU cores.

Reading: the camera learns the shape on discharges it never saw (nRMSE 0.12 to 0.49), but it is 3 to 13 times worse than
the magnetic model in nRMSE. It comes closest at the limiter point (ratio 1.3), where the plasma touches the wall that the
camera sees, and is farthest on what it cannot see: the plasma current (13x) and the vertical X-point position (10x).
The ratio uses different rows and folds; the like-for-like check is pending.

## Colour against black and white (REQ-B03)

No difference: every colour-grey gap in the table is smaller than the fold-to-fold SD, and the frames carry almost no
colour. Grey is cheaper: 1.34 ms against 1.69 ms per frame (median, CPU, model only). A black and white camera is enough.

## Shifted and rotated camera (REQ-B05)

Trained on the unmoved images, tested on every 4th test frame shifted or rotated (`results/cloud-camera-main-sensitivity.png`),
error relative to the unmoved image, colour model:

| change of the test image | R_mag_axis | Z_mag_axis | elongation | R_x_point | is_limited accuracy |
|---|---|---|---|---|---|
| none | 1.78 mm | 2.49 mm | 0.016 | 1.53 mm | 0.975 |
| shift 1 px (10 original px, 1.6 % of the width) | x1.9 to x2.4 | x2.0 to x2.3 | x2.2 to x5.1 | x3.0 to x3.8 | 0.94 to 0.97 |
| shift 4 px | x3.4 to x4.0 | x3.5 to x5.2 | x13 to x23 | x6.1 to x7.0 | 0.45 to 0.87 |
| rotate 1 degree | x1.04 to x1.06 | x1.05 to x1.07 | x1.05 to x1.07 | x1.12 | 0.975 |
| rotate 2 degrees | x1.14 to x1.18 | x1.19 to x1.22 | x1.17 to x1.23 | x1.41 | 0.97 |
| rotate 5 degrees | x1.5 to x1.6 | x1.7 to x1.9 | x2.0 to x2.3 | x2.3 to x2.7 | 0.97 |

The grey model behaves the same. Reading: the network estimates absolute positions in the image, so a camera that moves
looks exactly like a plasma that moves. A shift of 1/64 of the frame already doubles the error; a small rotation about the
image centre matters much less. The camera must stay fixed and calibrated. Training with random shifts and rotations:
`DOPLNIT` (experiment `augment`).

## Camera against magnetics on the same frames and folds (REQ-B01, `results/cloud-camera-multimodal.md`)

Command: `cloud_camera_model.py multimodal --size 48x64 --stride 8 --epochs 12 --width 16 --folds 5` (colour). The magnetic
MLP is `ipp1_common.fit_mlp` (60 epochs) trained on the inputs interpolated to the same 14,520 frames, so it is weaker than
the baseline on all rows (R_mag_axis 0.59 against 0.38 mm), but it is the fair reference.

| target | unit | magnetic MAE ± SD | camera MAE ± SD | camera + magnetic (one network) MAE ± SD |
|---|---|---|---|---|
| R_mag_axis | mm | 0.59 ± 0.25 | 1.79 ± 0.42 | 1.54 ± 0.26 |
| Z_mag_axis | mm | 0.50 ± 0.18 | 2.48 ± 0.61 | 1.13 ± 0.29 |
| elongation |  | 0.0077 ± 0.0029 | 0.0160 ± 0.0031 | 0.0131 ± 0.0036 |
| R_x_point | mm | 0.40 | 1.54 | 1.18 |
| Z_x_point | mm | 0.32 | 2.05 | 1.11 |
| R_limiter | mm | 16.7 ± 1.8 | **12.8 ± 1.7** | **12.6 ± 2.0** |
| Z_limiter | mm | 30.4 ± 2.9 | 28.8 ± 1.3 | 28.0 ± 2.3 |
| plasma_current | kA | 1.47 ± 0.17 | 14.6 ± 6.5 | 2.30 ± 0.37 |

`is_limited` accuracy: magnetic 0.992, camera 0.976, both 0.987.

Reading: with ideal (clean) coil signals the coils win on everything except the limiter point, where the camera is better
(R_limiter 12.8 against 16.7 mm) and the combination is best. The single network that takes both inputs is worse than the
coils alone elsewhere: its magnetic branch is small and trained for 12 epochs, so this is a limit of that fusion design,
not proof that the camera carries no information; the weighted late fusion and the comparison with realistic (noisy)
coil signals are the next run. The camera variant reproduces `main` exactly (same seed and folds: R_mag_axis 1.7879 mm
in both), so runs are deterministic.

## Pending (running or queued in this session)

| Question | Result |
|---|---|
| Camera accuracy against the number of training discharges | `DOPLNIT` (`curve`) |
| Training with random shifts and rotations (REQ-B05) | `DOPLNIT` (`augment`) |
| Which image parts matter (REQ-B07), smaller part of the image (REQ-004) | planned: occlusion map and crops |
| Camera against realistic (noisy) magnetics | planned: `equil_data_noisy.csv` inputs on the same frames |

## Real time

1.69 ms (colour) and 1.34 ms (grey) per frame, median, p99 about 3 ms, CPU, 811k parameters, model only (JPEG readout and
decoding not measured). That is fast enough for the units-to-tens-of-milliseconds requirement, but about 100 times slower
than the magnetic MLP (0.015 ms).

## Honest limits

- Only 78 discharges have camera frames; 15 or 16 test discharges per fold, so fold-to-fold SD is 20 to 45 % of the MAE.
- 48x64 frames: one cached pixel is 10 original pixels; finer resolution is untested.
- One network seed per fold so far; colour and grey use the same seed.
- The camera sees emission, not the magnetic flux surfaces or the plasma current.
- The model needs the camera position of the training data; a shift of one cached pixel doubles the error.
