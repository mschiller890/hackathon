# Camera model: decisions and why (study notes for the team)

Each entry says what was chosen, what else was possible, why, and the evidence. Numbers come from the runs named in
`results/cloud-camera-findings.md`; estimates are marked as such. Updated as decisions are made (last: Fri 18:45 CEST).

## D1. Match frames to the equilibrium by interpolation inside each discharge

- **Chosen:** for each frame, interpolate the 24 inputs and 16 targets linearly in relative time between the two
  equilibrium rows of the same discharge; nearest row for `is_limited`; NaN if a neighbour is NaN; no extrapolation;
  frames in a gap wider than 5 median row spacings dropped.
- **Alternatives:** nearest row (`merge_asof`); interpolate across discharges or across NaN.
- **Why:** the organizers' notebook asks for per-discharge matching and recommends interpolation, but not for
  `is_limited` and not for targets that are NaN in part of the discharge. A value between 0 and 1 for `is_limited` would
  be meaningless, and interpolating across a NaN would invent a limiter point in a divertor phase.
- **Evidence:** a hand-computed toy check passes; 115,872 of 116,142 frames matched, none dropped for a gap.

## D2. Small images: 48x64 pixels, box filter

- **Chosen:** downscale 640x500 to 48x64 (the aspect ratio is kept; 1 cached pixel = 10 original pixels).
- **Alternatives:** 64x64 (distorts the aspect), 96x128 or a crop around the plasma (finer, 3 to 4 times the cost,
  estimate).
- **Why:** there is no GPU in the cloud session; the network must train in minutes. JPEG draft decoding plus a box
  filter makes the whole 116k-frame cache in under 3 minutes.
- **Open:** whether finer pixels help is not yet tested; the shift sweep shows that 1 cached pixel is worth several mm,
  so it might.

## D3. Every 8th frame of each discharge

- **Chosen:** `--stride 8`, 14,520 training and test frames.
- **Alternatives:** all 115,872 frames (8 times the cost), random subsets per epoch.
- **Why:** neighbouring frames are near copies (583 to 2166 frames per discharge, but only about 290 equilibrium rows
  per discharge to learn from). The fit takes about 160 s instead of about 20 min.
- **Caveat:** GroupKFold assigns discharges by row count, so the folds depend on the stride; all compared runs use the
  same stride.

## D4. A small CNN with coordinate channels, trained from scratch

- **Chosen:** six 3x3 convolution blocks (three with stride 2), two extra input channels holding the x and y position,
  4x4 pooling, an MLP head, 16 outputs, about 0.8 million parameters.
- **Alternatives:** a pretrained ResNet18 (estimated 6 to 13 times the cost, trained on everyday photos, not plasma
  emission); a linear model on pixels; hand-made features (brightness centroid).
- **Why:** the targets are positions in the image, and plain convolutions are partly blind to absolute position; the
  coordinate channels give it directly. Small enough for a CPU, big enough to learn (checked on a synthetic task:
  nRMSE 0.008).

## D5. Same targets, loss and score as the magnetic model

- **Chosen:** 16 outputs, masked MSE on standardized targets, `ipp1_common.score`.
- **Why:** the camera must be comparable with the magnetic model; targets that exist only in one configuration
  (X-point, strike points, limiter point) are simply skipped in the loss where they are NaN.

## D6. Split by whole discharges, 5 folds

- **Chosen:** GroupKFold by `discharge`, 15 or 16 test discharges per fold, mean and fold-to-fold SD reported.
- **Why:** frames of one discharge are near copies; a random split would put copies of the test frames into training
  and make the numbers look far too good (assignment rule CON-002).
- **Caveat:** the settings were fixed after one inner `--dev` split of fold 0's training discharges, with no
  alternative compared. Those validation discharges are test discharges of folds 2 to 5, so any future choice made
  there must be reported on fold 1 alone or chosen inside each fold.

## D7. Settings: 12 epochs, width 16, batch 128

- **Chosen** after one dev run (156 s per fit, validation R_mag_axis 2.0 mm), on time grounds only.
- **Open:** the model may be under-trained (about 1,100 optimizer steps). A longer run is planned on the dev split,
  not on test folds.

## D8. Colour or black and white: black and white is enough (REQ-B03)

- **Evidence:** 5 folds, every colour-grey difference is below the fold SD (R_mag_axis 1.79 vs 1.70 mm); the frames
  carry little colour (mean |R-G|+|G-B| = 8.7 of 255). Grey is also faster (1.34 vs 1.69 ms per frame).
- **Consequence:** later camera-only experiments may use grey.

## D9. How sensitive is the model to a moved camera (REQ-B05)

- **Design:** train on unmoved frames; test the same frames shifted by 1, 2 or 4 cached pixels in x or y, or rotated by
  1, 2 or 5 degrees about the centre.
- **Result:** 1 pixel (1.6 % of the width) roughly doubles the axis error; a 1 degree rotation adds about 5 %.
- **Why it happens:** the model reads absolute positions, so a moved camera looks like a moved plasma. This is the main
  practical limit of a camera model; training with random shifts (`augment`) tests a remedy.

## D10. Compare the camera with realistic magnetics, not only the ideal ones (planned, REQ-B01)

- **Chosen:** in addition to `multimodal` (clean inputs), train the magnetic MLP on the organizers'
  `equil_data_noisy.csv` interpolated to the same frames, and fuse it with the camera (a second branch in the CNN, and a
  weighted average whose weights come from the other folds).
- **Why:** with clean inputs the magnetic model is 3 to 13 times better in nRMSE, so fusion can at best tie. Real
  sensors are noisy and drift; lane R measured the noisy-trained, noisy-tested magnetic model at R/Z axis 2.64/2.01 mm,
  the same class as the camera (1.7 to 1.8 / 2.4 to 2.5 mm, other rows). The camera's errors are independent of the
  coil noise, which is when fusion can help.
- **Noisy inputs use the nearest equilibrium row**, not interpolation, so averaging two noisy rows does not hide noise.

## D11. Which parts of the image matter, and a smaller part of the image (planned, REQ-B07, REQ-004)

- **Chosen:** an occlusion map (grey out each 8x8 patch, measure how much the error grows) and models trained on fixed
  parts chosen before seeing any result: top half, bottom half, left half, right half, centre, and half resolution.
- **Why:** it answers both questions with one setup, and it checks that the network is not reading something
  non-physical (a timestamp or a frame corner). Figures show only the grid, not the camera frame (confidential data),
  unless the owner decides otherwise.

## D12. Work split between sessions

- **Chosen:** the camera stays in this cloud session. The second cloud session keeps its magnetic search; it gets no
  camera data.
- **Why:** its 4 cores are fully busy, downloading and preparing 876 MB would cost about 30 to 40 minutes, and each
  extra copy of confidential data adds risk. This session's CPU is enough for the queue (estimate: done by about 21:00).

## D13. How the work is checked

- A synthetic fixture with a known answer, run before the real data (found the label misalignment and time-unit bugs).
- A real-data alignment check (brightness against plasma current inside discharges).
- An independent review workflow: three planners, a judge, three code reviewers, each finding challenged by two
  skeptics (running; results go into D-entries).

## D14. Like-for-like result: the camera helps at the limiter point (measured, `multimodal`)

- **Design:** on the same 14,520 frames and folds, a magnetic MLP on the inputs interpolated to the frames, the camera
  CNN, and one CNN with both inputs.
- **Result:** clean coils beat the camera everywhere except the limiter point: R_limiter 16.7 mm (coils) against
  12.8 mm (camera) and 12.6 mm (both); Z_limiter 30.4 / 28.8 / 28.0 mm.
- **Why it makes sense:** the limiter point is where the plasma touches the wall. The camera sees that contact
  directly; the coils have to infer it from the field outside the plasma, which is their weakest target.
- **Why the one-network fusion is worse elsewhere:** its magnetic branch is small and trained only 12 epochs, so it adds
  noise where the coils alone are already good. That is a design limit, tested next with a weighted late fusion whose
  weights come from the other folds.
- **Reproducibility:** its camera variant gives exactly the `main` numbers (same seed and folds).

## Questions a jury may ask

- **Why is the camera worse than the coils?** It sees light from the plasma edge and the wall contact, not the magnetic
  field; the coils measure the field that defines the shape. The camera is closest at the limiter point (ratio 1.3).
- **Is the split honest?** Yes: by whole discharges; no frame of a test discharge is ever seen in training.
- **Would colour help?** No measurable difference; the camera images are almost grey.
- **Can it run in real time?** 1.3 to 1.7 ms per frame on a CPU, fine for a millisecond loop, but 100 times slower than
  the coil model.
- **What breaks it?** Moving the camera by one pixel doubles the error; it must be fixed and calibrated.
- **Does the camera add anything to the coils?** Yes, at the limiter point: on the same frames it is better than the
  coils (R_limiter 12.8 against 16.7 mm), and camera plus coils is best there.
