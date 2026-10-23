# IPP 1: a bigger camera network (96x128), protocol written before the run

**Wording: "this 96x128 camera network", never "the camera".** What is measured is one small convolutional network on downscaled grey frames; it says nothing about what a camera can do. The labels are the institute's reference reconstruction.

**Why.** The first camera networks of this project were small (`results/cloud-camera-main.md`: 48x64 pixels, width 16, 12 epochs, every 8th frame, one seed, no augmentation) and no occlusion test existed (REQ-B07). This run enlarges the network and tests it harder. The locked test set (`results/ipp1-locked-test-ids.txt`) is not used: only 78 of the 149 discharges have frames, and no camera number is a claim about the shipped magnetic model.

## Fixed in advance (this text was committed before the first run of `analysis/ipp1_camera_v2.py`)

**Data and folds.** The 115,872 frames of the 78 discharges that have frames and labels (matching as in `analysis/ipp1_camera_prepare.py`: linear interpolation of the reference values inside the discharge). Grey, the full 640x500 frame scaled to **96x128** (height x width). 5 folds by whole discharge, `GroupKFold` on the group sizes of every 8th frame, which reproduces the fold assignment of the cloud run (14,520 frames, 78 discharges, 16/16/15/16/15 test discharges per fold, checked). **Test frames: every 8th frame of each held-out discharge** (the same frames as the old network). **Training frames: every 4th frame** of each training discharge (about 23,000 per fold).

**Network and training** (as `analysis/cloud_camera_model.py`): `CamNet` with two coordinate channels, six 3x3 convolution blocks (batch norm, SiLU), average pooling to 4x4, a head of 256 units, 16 outputs (the targets of `ipp1_common.TARGETS`); input standardized with the mean and SD of 2,000 random training frames; masked mean squared error on standardized targets; AdamW (learning rate 2e-3, weight decay 1e-4), one-cycle schedule (maximum 3e-3), batch 128. Seed of fold k = k. Apple GPU (MPS) for the networks, CPU for the magnetic MLP.

**Arms.**
- **A: bigger.** Width 32, 20 epochs, no augmentation.
- **B: A plus training augmentation.** Per training sample a random shift of up to 2 pixels (each axis, uniform) and a random rotation of up to 2 degrees about the centre, border padding. Otherwise as A.
- **C: robustness (REQ-B05).** The networks of A and B tested on the test frames moved by 1 pixel (right, left, down, up) and rotated by 1 degree (both directions), unmoved test as the reference. Reported: MAE moved / MAE unmoved per target (mean over the six moves), for B (the asked case) and A (for contrast).
- **D: occlusion map (REQ-B07).** With the B network: a patch of 16x16 pixels filled with the mean grey level of the training frames is slid over the test frame on a grid of 6 x 8 positions (steps of 16 pixels); for each position the rise of the mean absolute error (mean over the test frames that have the target, in the unit of the target) against the unoccluded frame, for `R_mag_axis`, `Z_mag_axis`, `elongation` and `R_strike_point_1`, mean over the 5 folds. Saved as `results/ipp1-camera-v2-occlusion.png`: aggregate heat maps only, no frame is shown.

**Reported.** Per target the MAE (mm, kA, dimensionless) and the nRMSE (RMSE divided by the SD of the target), mean over the folds, for A and B next to (1) the old small network (grey, `results/cloud-camera-main.md`: 48x64, width 16, 12 epochs, stride 8, seed 0) and (2) the magnetic baseline on the same frames and folds: the masked MLP of `ipp1_common.fit_mlp` (60 epochs) on the 24 magnetic inputs interpolated to the frame times, trained on the same training frames and scored on the same test frames; the cloud's own magnetic number (`results/cloud-camera-multimodal.md`, trained on every 8th frame) is quoted next to it. Seed spread: a second seed (fold seed + 10) for A only, if time allows.

**Stop rule.** The experiment is stopped at 00:30 (results freeze 01:00). What has finished is reported, what has not is named as not run. Arms run one after the other (A, B with C and D, then the second seed of A), one job at a time.

## What this run cannot show

One seed per arm (the spread comes only from a second seed of A); the network settings were fixed by the Lead and not tuned; the frames of one discharge are near copies, so the test frames are few independent samples (78 discharges); the labels are the reference reconstruction, not a measurement of the plasma; nothing here concerns the locked test set or the shipped magnetic model; shifts and rotations of 1 pixel and 1 degree at 96x128 are about 1 % of the image and are no substitute for a real camera that moved.

<!-- RESULTS BELOW -->

## Results

Status: magnetic MLP finished, arm A finished, arm B (with C and D) finished, second seed of A NOT RUN or not finished.

MAE in mm (plasma current in kA, shape numbers dimensionless) and nRMSE (RMSE / SD of the target), mean over the 5 folds, test frames = every 8th frame of the held-out discharges. Old small network = grey, 48x64, width 16, 12 epochs (`results/cloud-camera-main.md`, seed 0).

| target | unit | magnetic MLP (same frames) MAE | nRMSE | old small network MAE | nRMSE | this 96x128 network, A MAE | nRMSE | this 96x128 network, B (augmented) MAE | nRMSE |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.36 | 0.0346 | 14 | 0.356 | 20.4 | 0.514 | 11 | 0.271 |
| R_mag_axis | mm | 0.407 | 0.134 | 1.7 | 0.447 | 2.28 | 0.554 | 1.59 | 0.393 |
| Z_mag_axis | mm | 0.419 | 0.147 | 2.4 | 0.489 | 3.33 | 0.588 | 1.99 | 0.397 |
| elongation | - | 0.0061 | 0.0442 | 0.0162 | 0.122 | 0.0278 | 0.177 | 0.0126 | 0.0887 |
| triangularity | - | 0.00322 | 0.0551 | 0.00855 | 0.147 | 0.0138 | 0.202 | 0.00702 | 0.118 |
| triangularity_upper | - | 0.00308 | 0.089 | 0.00891 | 0.25 | 0.0128 | 0.321 | 0.00757 | 0.215 |
| triangularity_lower | - | 0.00426 | 0.0519 | 0.0125 | 0.143 | 0.0209 | 0.2 | 0.0102 | 0.113 |
| R_x_point | mm | 0.335 | 0.124 | 1.5 | 0.31 | 2.19 | 0.416 | 1.36 | 0.28 |
| Z_x_point | mm | 0.24 | 0.0645 | 2.18 | 0.395 | 3.11 | 0.573 | 1.62 | 0.291 |
| R_strike_point_1 | mm | 0.25 | 0.0546 | 2.25 | 0.336 | 3.24 | 0.449 | 1.86 | 0.274 |
| Z_strike_point_1 | mm | 0.117 | 0.0652 | 0.787 | 0.304 | 1.3 | 0.465 | 0.688 | 0.268 |
| R_strike_point_2 | mm | 0.376 | 0.133 | 2.18 | 0.406 | 3.12 | 0.568 | 1.71 | 0.308 |
| Z_strike_point_2 | mm | 0.0844 | 0.147 | 0.416 | 0.386 | 0.628 | 0.59 | 0.336 | 0.293 |
| R_limiter | mm | 12.7 | 0.386 | 13.1 | 0.409 | 18 | 0.487 | 11.6 | 0.354 |
| Z_limiter | mm | 24.3 | 0.282 | 28.7 | 0.349 | 42 | 0.439 | 25 | 0.304 |

`is_limited` agreement: magnetic MLP 0.992, old small network 0.975, A 0.962, B 0.980.

Training time per fold on the Apple GPU: A 606 s, B 611 s; parameters: A 2,179,888, B 2,179,888.

## C. Robustness: the test frame moved by 1 pixel or rotated by 1 degree (REQ-B05)

Ratio = MAE with the moved test frame / MAE with the unmoved test frame, mean over the six moves (right, left, down, up by 1 pixel at 96x128; +1 and -1 degree) and the 5 folds; 1.00 = no change.

| target | A, unmoved MAE | A ratio | B, unmoved MAE | B ratio |
|---|---:|---:|---:|---:|
| plasma_current | 20.4 | 1.33 (worst move 1.74) | 11 | 0.99 (worst move 1.02) |
| R_mag_axis | 2.28 | 1.33 (worst move 1.59) | 1.59 | 0.99 (worst move 1.00) |
| Z_mag_axis | 3.33 | 1.33 (worst move 1.50) | 1.99 | 1.00 (worst move 1.01) |
| elongation | 0.0278 | 1.40 (worst move 1.67) | 0.0126 | 0.99 (worst move 1.01) |
| R_x_point | 2.19 | 1.68 (worst move 2.30) | 1.36 | 0.99 (worst move 1.01) |
| R_strike_point_1 | 3.24 | 1.43 (worst move 1.66) | 1.86 | 0.99 (worst move 1.02) |
| R_limiter | 18 | 1.24 (worst move 1.46) | 11.6 | 1.01 (worst move 1.01) |
| Z_limiter | 42 | 1.27 (worst move 1.52) | 25 | 1.01 (worst move 1.01) |

## D. Occlusion map (REQ-B07)

`results/ipp1-camera-v2-occlusion.png`: for every position of a 16x16 px grey patch (grid of 6 x 8, steps of 16 px) the rise of the mean absolute error of the B network over the unoccluded frame, aggregate over the test frames and the 5 folds; no frame is shown.

| target | unit | error unoccluded | largest rise | at patch (row, column in px) | median rise over the grid | patches with a rise above half of the largest |
|---|---|---:|---:|---|---:|---:|
| R_mag_axis | mm | 1.59 | 1.26 | (48, 64) | 0.183 | 8 of 48 |
| Z_mag_axis | mm | 1.99 | 1.09 | (48, 48) | 0.169 | 9 of 48 |
| elongation | - | 0.0126 | 0.0291 | (48, 48) | 0.00275 | 3 of 48 |
| R_strike_point_1 | mm | 1.86 | 2.77 | (48, 80) | 0.252 | 2 of 48 |


## Reading

**Wording: "this 96x128 camera network"; the labels are the institute's reference reconstruction.**

1. **Size alone did not help.** Arm A (width 32, 96x128, 20 epochs, no augmentation) is worse than the old small network on every target (R_mag_axis 2.28 mm against 1.7 mm, R_strike_point_1 3.24 mm against 2.25 mm, nRMSE of R_mag_axis 0.554 against 0.447). One seed only, and this run differs from the old one in several ways at once (resolution, width, epochs, training on every 4th frame, and the Apple GPU), so it does not say which of them hurts.
2. **With random shifts of up to 2 px and rotations of up to 2 degrees in training (arm B) the same network is better than the old small one** on most targets: R_mag_axis 1.59 mm (old 1.7), Z_mag_axis 1.99 mm (old 2.4), R_x_point 1.36 mm (old 1.5), R_strike_point_1 1.86 mm (old 2.25), elongation 0.0126 (old 0.0162), `is_limited` agreement 0.980 (old 0.975). It stays 4 to 8 times worse than the magnetic MLP on the same frames and folds (R_mag_axis 0.407 mm, R_strike_point_1 0.250 mm): the 24 magnetic signals carry the shape more directly than this camera network extracts it.
3. **Robustness (C).** The B network's error does not move when the test frame is shifted by 1 pixel or rotated by 1 degree (ratio 0.99 to 1.01, worst single move 1.02), while arm A's error grows by a factor 1.2 to 1.7 (R_x_point 1.68, R_mag_axis 1.33). Caveat: the moves are INSIDE the range of the training augmentation of B (up to 2 px and 2 degrees), so this shows that the augmentation does what it is meant to do, not that this 96x128 camera network would survive a larger or a different camera movement.
4. **Where the network looks (D, REQ-B07).** Hiding a 16x16 px patch raises the error mainly in the middle of the frame (patch rows about 32 to 64 px, columns about 32 to 96 px) for all four targets, and not at the edges or corners (median rise over the grid is 10 to 15 % of the largest rise). The largest rises: R_mag_axis +1.26 mm and Z_mag_axis +1.09 mm at the centre (patch at row 48, column 64 and 48), elongation +0.029 at (48, 48), R_strike_point_1 +2.77 mm at (48, 80), which is one of only 2 of 48 patches above half of the maximum, a narrower region than for the axis (8 and 9 patches). A rise means that the network depends on the information in that region (or that the grey patch itself disturbs it, which this test cannot separate); it is not a proof of which physical structure is used.
5. **Limits.** One seed per arm (a second seed of arm A is reported below if it finished); the network settings were fixed by the Lead and not tuned; 78 discharges, the frames of one discharge are near copies; no locked test set; not a statement about what a real camera can do.
