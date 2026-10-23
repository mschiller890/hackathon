# IPP 1: camera model, local run (lane R, second measurement)

The camera lane is the cloud session (`docs/internal/WORKERS.md`, Fri 18:00); this is an independent local run kept as a cross check.
Evidence for REQ-B01, REQ-B03, REQ-B05. Figure: `ipp1-camera-local.png`.

Commands (with `HACKATHON_HOME=<your hackathon folder>`, `~/.venvs/hackathon/bin/python -I`):
`analysis/ipp1_camera_prepare.py`, then `analysis/ipp1_camera_model.py --epochs 8 --folds 5 --run-folds 2` (about 1 h 20 min on the Apple GPU).

## Data and setup

- 116,142 frames of 640x500 RGB from 78 of the 149 discharges; 115,872 (99.8 %) matched to labels. A frame is dropped outside the labelled
  time range or inside a label gap longer than 0.01 (relative time); labels are linear interpolations, conditional targets only where both
  neighbours have them, `is_limited` from the nearest row.
- Frames are cropped to 112x112 px (after a 1/4 downscale) and normalized per image after a square root: exposure and colour balance differ
  strongly between discharges (orange, white and pink tints were seen) and the view moves between discharges: the left edge of the vessel image lies between 115 and 198 px (median 156, quartiles 154 to 164) at full resolution, measured on mean frames of 78 discharges.
- **Only the first 2 of the 5 group folds were run** (time budget): 31 and 30 held-out discharges, 15.4 k test frames scored (every third frame).
  One initialization per fold. The magnetic reference below uses the same frames and folds; on these two folds it is 0.24 mm, easier than the
  0.38 mm of the five-fold baseline, so compare only inside this table.

## Results (mean of the 2 folds, MAE)

| Model | R axis (mm) | Z axis (mm) | elongation | limiter Z (mm) | plasma current (kA) | `is_limited` |
|---|---:|---:|---:|---:|---:|---:|
| magnetic MLP (24 inputs) | 0.24 | 0.23 | 0.0040 | 19.2 | 1.04 | 99.4 % |
| camera, colour | 1.54 | 1.95 | 0.0152 | 32.2 | 17.9 | 97.9 % |
| camera, black and white | 1.53 | 2.03 | 0.0158 | 30.4 | 18.2 | 97.5 % |
| camera + magnetic | 1.21 | 0.52 | 0.0092 | 29.6 | 1.36 | 99.0 % |
| camera, colour, shift and rotation augmentation | 2.00 | 2.22 | 0.0155 | 37.9 | 13.8 | 98.2 % |

- The camera alone is 6 to 8 times worse than magnetics on the axis and cannot measure the plasma current (18 kA), which agrees with the cloud
  session's first run (about 2 mm, `is_limited` 98 %). It stays a bonus.
- **Black and white (REQ-B03):** no visible difference. R axis 1.54 against 1.53 mm; per fold the sign flips (fold 1 colour better, fold 2 grey better).
- **Multimodal (REQ-B01): did not beat the magnetic network** (R axis 1.21 against 0.24 mm, limiter Z 29.6 against 19.2 mm). The fused model was
  trained for only 8 short epochs and the image branch dominated; with this setup the camera adds nothing to the magnetics. We did not test a
  longer training or a late fusion, so this does not prove that no fusion can help.

## Camera moved (REQ-B05), colour model, R axis MAE in mm (unperturbed 1.54)

| Test frames moved by | plain model | trained with augmentation |
|---|---:|---:|
| 4 px right / 8 px right | 4.95 / 6.28 | 2.00 / 1.97 |
| 8 px up or down | 5.6 to 6.6 | 2.07 |
| rotated 5 degrees (either way) | 3.25 | 2.0 |
| rotated 10 degrees | 3.6 to 4.0 | 2.0 to 2.1 |

- A plain model is fragile: a 4 to 8 px shift (4 to 7 % of the image; at this scale the discharges differ typically by about 3 px, in the extreme by about 20 px) triples
  the error and the elongation error rises from 0.015 to about 0.27. Augmentation removes this (2.0 mm everywhere) at the price of 0.5 mm on
  unshifted frames (2.00 against 1.54 mm).
- **Caveat, shifts of 16 px:** the plain model's error falls back to 1.8 to 2.0 mm (elongation 0.02) at 16 px, which is not monotonic. It is
  the same in both folds, so it is systematic, not training noise. A likely cause is that the shift pads with zero after the per image
  standardization, which is not the black background level, so the border looks like a different input; this is not verified. Treat the
  shift numbers as showing fragility, not as a calibrated curve. A re-run should pad before normalizing (models were not saved, so this needs
  a new training; left to the camera lane).

## Not done

Fewer images (number of images against accuracy), the remaining three folds, a stronger fusion, the cloud session's own variants.
