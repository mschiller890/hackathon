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
