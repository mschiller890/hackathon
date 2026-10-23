# Work split (who does what)

**Authoritative for who owns which task and which paths.** The task board stays in
[`PLAN.md`](PLAN.md); requirements in [`REQUIREMENTS.md`](REQUIREMENTS.md). Read `../AGENTS.md`,
`../README.md`, `PLAN.md`, `REQUIREMENTS.md` and this file before starting. Event ends Sat 24 Oct 14:00;
feature freeze Sat 10:00.

## Rules for every lane

- **Data are confidential (CON-001).** They stay in `$HACKATHON_HOME/data/raw` (`HACKATHON_HOME` is the
  `hackathon/` folder next to this repository; on the owner's Mac `/Users/bladed/Documents/AIprogramy/hackathon`).
  Never commit raw data or files that contain it (the `.gitignore` covers `data/`, `out/`, `viewer/data.js`).
  Never publish or deploy anything built from the data. Aggregate metrics and figures go to `results/`.
- Python: `~/.venvs/hackathon/bin/python -I <script>` with `HACKATHON_HOME` set. Reuse `analysis/ipp1_common.py`
  (loading, the masked network, scoring) so every lane measures the same way. Split by whole discharges only.
- Each lane writes only in its own paths. Small Conventional Commits, files staged explicitly, `git pull --rebase`
  before `git push`, no secrets, no force-push. Update your own row in `PLAN.md` (status, evidence) when you finish.
- Report what you ran and what you saw, with numbers. A task is `DONE` only when its acceptance criteria are checked.
- If you are on the owner's Mac you can also read the Obsidian notes in
  `~/Documents/Obsidian/2026/2027/Hackathon-Brain/` (start with `00-START-HERE.md`); the shared facts are the same.

## State at 17:00 on Fri 23 Oct

Baseline (`analysis/ipp1_baseline.py`, 5 folds by discharge, result in `results/ipp1-baseline.md`): the network
reaches 0.06 to 0.4 mm on axis, X-point and strike points, 1.5 kA on the plasma current, 0.0057 on elongation,
99.3 % accuracy on `is_limited`, 0.015 ms per sample on CPU. The weakest are the limiter point (R 11 mm, Z 22 mm).
Out-of-fold predictions: `$HACKATHON_HOME/out/ipp1-predictions.csv` (script `analysis/ipp1_oof.py`).
The 876 MB camera archive is downloaded to `data/raw/ipp1-photron-zip/` (not yet extracted).

## Lanes

### L, Lead (Claude main session of the owner): required analyses
IMPL-4. Stability of the output over a discharge (error and jitter against time), fewer inputs (drop one coil, drop
groups, best small subsets) and importance of each input, latency on CPU and the Mac GPU with a verdict for
real-time control, a stronger model if cheap. Paths: `analysis/ipp1_inputs.py`, `analysis/ipp1_time.py`,
`analysis/ipp1_latency.py`, `results/`. Also integrates, keeps `PLAN.md` and the notes current, assembles the notebooks.

### U, Viewer (Claude fork "Hackathonová strategie a příprava" [65894b]): plasma shape viewer
IMPL-10. A static, offline page that opens by double click (data inlined through a generated `viewer/data.js`,
which is gitignored). It shows the poloidal cross section of the COMPASS tokamak: the wall outline (file
`notebooks/COMPASS_stena.csv` of the organizers' repository `repo.tok.ipp.cas.cz/seidl/cvut-ml-hackaton-2026-compass`,
save it under `data/raw/organizers/`), the plasma boundary rebuilt from the shape parameters (follow the organizers'
`plot_equilibrium` in `notebooks/uloha-1-ekvilibrium-nacteni-dat.ipynb`: four superellipses using the squareness
columns), magnetic axis, X-point, strike points, limiter point. True and predicted shape drawn together, a time
slider with play, a discharge picker, a table of true against predicted per parameter with the error, and a chart of
the error over time. Version 0 may show the true shape only; predictions come from `out/ipp1-predictions.csv`
(columns `<target>_pred`, join with `equil_data.csv` on `discharge` and `time`). Paths: `viewer/`,
`analysis/export_viewer_data.py`. Looks matter: this is the live demo of the presentation. Check it in a browser
screenshot before calling it done.

### R, Robustness and data (GPT): required bonus experiments
IMPL-5, REQ-B02, REQ-B04, REQ-B06. Three self-contained scripts using `analysis/ipp1_common.py`, each writing
`out/ipp1-<name>.json`, `.md` and `.png`, and a short `results/ipp1-robustness-findings.md` with the numbers:
1. `analysis/ipp1_robustness.py`: train on clean and test on `equil_data_noisy.csv`; train on noisy and test on noisy;
   generated drift `x + noise + c * t` with a random coefficient `c` per discharge (`t` the relative time); report the
   MAE per target against the noise level; try noise augmentation during training as a way to harden the model.
2. `analysis/ipp1_learning_curve.py`: train on 5, 10, 25, 50, 100 % of the training discharges, test on the same
   held-out discharges; accuracy against the number of training data.
3. `analysis/ipp1_temporal.py`: inputs from the previous rows of the same discharge (for example t-2, t-1, t)
   against the single row; does time context improve accuracy and the stability of the output?
Seeds recorded, five folds by discharge where affordable. Paths: those scripts and `results/ipp1-robustness*`.

### K, Colleague and his Claude: checks and the presentation text
IMPL-11. (1) Reproducibility: clone the repository, follow `README.md` on your machine, download the IPP 1 magnetic data
yourself from the organizers' Drive (only participants may hold it), run `analysis/ipp1_eda.py` and
`analysis/ipp1_baseline.py`, and write every problem you hit into the open questions of `PLAN.md`. (2) The
presentation outline in Czech, `presentation/outline.md`: 7 minutes, slide by slide with the seconds and the one
sentence each slide must say: the problem (the plasma must be kept off the wall within milliseconds, the classical
computation takes minutes), the data, the method, the results (take numbers only from `results/`), the real-time
verdict, the limits, what the model cannot do. Use plain Czech without English words and without dashes. Numbers
that do not exist yet stay marked `DOPLNIT`. (3) Later: material for the motion reel; the owner starts it after the
results exist (not before Sat 08:00).

### K takes more work (Fri 17:00)
In this order, after the reproducibility check and the outline:
1. **The real slide deck** from `presentation/outline.md` and, when it exists, `presentation/pitch-script.md`, with the images in
   `presentation/assets/` and the figures in `results/` (png). Tool of your choice (PowerPoint, Keynote, Google Slides); if your
   Claude builds it, use python-pptx and save `presentation/deck/slides.pptx`. 16:9, one message per slide, big numbers, a dark navy
   background with orange and blue accents like the images, speaker notes with the seconds. Only aggregate numbers from `results/`;
   never raw rows of the IPP data.
2. **Rehearsal:** read the talk aloud with a stopwatch (7:00 maximum), mark where it is too long or hard to follow, and play the
   hostile jury with the ten questions of the pitch script. Write the findings into `presentation/rehearsal-notes.md`.
3. **Glossary for the audience:** `presentation/slovnicek.md`, twelve terms (tokamak, plasma, X-point, strike point, limiter, elongation,
   triangularity, discharge, flux loop, coil, latency, overfitting) each in one plain Czech sentence that matches the slides.
4. **Reel material later** (not before Sat 08:00).
The submission video is not part of lane K; the owner decides who makes it.
Report each item by its row in `docs/PLAN.md` (IMPL-11) and push small commits.

### R also takes the camera model now (decided Fri 17:00, GPT has only 25 % of its limit used)
IMPL-6, IMPL-7, REQ-B01, REQ-B03, REQ-B05. Do this right after the three experiments above, or in parallel if you can.
1. Extract `$HACKATHON_HOME/data/raw/ipp1-photron-zip/uloha_1-photron.zip` (876 MB, already downloaded and complete) into
   its own new empty folder `data/raw/ipp1-photron/` (check the entry names for absolute or parent paths first, make the
   folder read-only afterwards). Profile it: number of JPEGs, resolution, the CSV that maps images to discharge and time.
2. `analysis/ipp1_camera_prepare.py`: match every image to a row of `equil_data.csv` (interpolate in time within the
   discharge as the organizers' notebook describes), downscale to a small grayscale array, cache it as `.npy` outside git.
3. `analysis/ipp1_camera_model.py`: a small convolutional network (Apple GPU via `torch.backends.mps` if available) that
   predicts the main shape parameters from the image; split by whole discharges; per-target MAE in mm against the
   magnetic baseline `results/ipp1-baseline.md`. Then black and white against colour (REQ-B03) and the effect of a shifted
   or rotated image (REQ-B05). Outputs `out/ipp1-camera*.{json,md,png}` and a summary in `results/ipp1-camera-findings.md`.
Never commit images or arrays (the `.gitignore` covers `data/` and `out/`).

### Lane L now also runs a Claude workflow (Fri 17:00)
The Lead's side takes: a stronger model for the weak targets (`analysis/ipp1_improve.py`), an independent review of all
analysis code and claims, the executed notebooks in `notebooks/`, the presentation images (`presentation/assets/`) and a
Czech pitch script. Lane U continues to polish the viewer; lane K continues with the reproducibility check and the outline.
