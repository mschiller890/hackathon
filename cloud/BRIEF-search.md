# Cloud brief: large model search for the magnetic part of IPP task 1

Hackathon: CVUT ML Hackathon 2026, ends Sat 24 Oct 2026 14:00 CEST. Task IPP 1: the plasma shape of the tokamak COMPASS from
24 magnetic measurements. Baseline MLP (256-256-128, 60 epochs, 5-fold GroupKFold by discharge): 0.06 to 0.4 mm on most
parameters; weakest are the limiter point R_limiter 10.7 mm and Z_limiter 22 mm. The Lead tries a few improvements locally;
you run a much larger search with more compute. Write only new files named `cloud_search*` on your own branch `cloud/search`.

1. Read `CLAUDE.md`, `README.md`, `docs/PLAN.md`, `docs/REQUIREMENTS.md`, `docs/WORKERS.md`, `results/*.md`. Use
   `analysis/ipp1_common.py` (load, group_folds, fit_mlp, fit_ridge, score, TARGETS, UNIT, Net). Keep the protocol: 5-fold
   GroupKFold by whole discharges, masked loss, errors in mm and kA and relative to the spread, the same score function.
2. Data (confidential, IPP, only for this hackathon): never commit it, never print raw rows, never send it anywhere. Download
   with gdown into a folder you choose and point `HACKATHON_HOME` at it (layout in `README.md`) the magnetic zip, Drive file id
   `1MBev-lb4l5Z7m33PeRJ4sjHQmeN5ELVp` (37 MB: `equil_data.csv`, `equil_data_noisy.csv`), into its own new empty folder; check zip
   entry names first. Install gdown pandas torch scikit-learn lightgbm optuna matplotlib.
3. `analysis/cloud_search.py` (use every CPU core, log wall-clock times): (a) Optuna over MLP width, depth, activation, dropout,
   weight decay, learning rate schedule, epochs, batch size, Huber against MSE, per-target loss weights; (b) residual MLP and a
   small transformer or attention model over the 24 coil values; (c) LightGBM and ExtraTrees per target; (d) a separate model for
   the limited configuration (limiter point) gated by a classifier for is_limited; (e) ensembles of 5 to 10 seeds; (f) input
   features: standardised inputs, differences of neighbouring coils, PCA components. Select hyperparameters inside the training
   folds only (nested split by discharge); never tune on the test discharges.
4. Report a Pareto table: summary relative error (mean nRMSE over the targets without the limiter point), R_limiter and Z_limiter
   MAE in mm, R_mag_axis MAE in mm, parameters and CPU inference latency per sample; the recommendation is the best model that
   stays far below 1 ms per sample. Test the best configuration on `equil_data_noisy.csv` (train clean, test noisy; train noisy).
5. Outputs: `results/cloud-search.md`, `results/cloud-search.json`, figures in `results/`. Small Conventional Commits on
   `cloud/search`, stage files explicitly (never data), push, open a pull request, do not merge. Push intermediate results at
   least every 45 minutes; the Lead integrates around 22:00 Fri and 08:00 Sat.
6. Report evidence only: the command and the number you saw. Talk to the user in Czech, write files in English.
