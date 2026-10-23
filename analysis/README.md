# analysis/

All scripts need `HACKATHON_HOME` (the folder that holds `data/raw/`), see the setup in the top README. Scripts write to
`$HACKATHON_HOME/out/`; the files that matter are copied by hand into `results/`. Run them with `python -I`.

| Script | Kind | What it does, and the `results/` file it backs |
|---|---|---|
| `ipp1_eda.py` | pipeline 1 | exploratory analysis; `ipp1-data.md` |
| `ipp1_baseline.py` | pipeline 2 | ridge and masked MLP baseline, 5 folds by discharge; `ipp1-baseline.md` |
| `ipp1_oof.py` | pipeline 3 | out-of-fold predictions of the baseline; read by `ipp1_time.py` and the notebooks |
| `ipp1_oof_noise.py` | pipeline 4 | the same on the provided noisy inputs |
| `ipp1_time.py` | pipeline 5 | stability over the time of a discharge; `ipp1-time.md` |
| `ipp1_inputs.py` | pipeline 6 | which inputs matter and how few suffice (about 1 h, `--quick` copies `results/`); `ipp1-inputs.md`, `ipp1-inputs-controls.md` |
| `ipp1_latency.py` | pipeline 7 | latency of the network, real-time verdict; `ipp1-latency.md` |
| `ipp1_final.py` | pipeline 8 | locked-test evaluation of the recipes; run as `--job` per recipe and fold by `make_all.py`, `--report` rewrites `ipp1-final.md` |
| `export_model.py` | pipeline 9 | exports the shipped model (`cand`) to `out/model/ipp1-selected.npz` |
| `ipp1_oof_full.py` | pipeline, `--viewer` | out-of-fold predictions of all 31 targets for the viewer |
| `export_viewer_data.py` | pipeline, `--viewer` | writes `viewer/data.js` (git-ignored, holds IPP data) |
| `make_all.py` | driver | runs the pipeline rows above in this order, `--notebooks` executes `notebooks/`, `--viewer` builds the viewer |
| `ipp1_common.py`, `cloud_search_lib.py`, `synth_equilibrium.py` | library | shared code: data, masked network, scoring; model search; synthetic equilibria |
| `ipp1_improve.py`, `ipp1_robustness.py`, `ipp1_temporal.py` | experiment | try to beat the baseline, noise and drift, causal three-row input; `ipp1-improve.md`, `ipp1-robustness-findings.md`, `ipp1-temporal.png` |
| `ipp1_distribution.py`, `ipp1_signcanon.py`, `ipp1_unusual_shapes.py`, `ipp1_unusual_heldout.py` | experiment | error against the uneven data, polarity fix, unseen shape family; `ipp1-distribution.md`, `ipp1-signcanon.md`, `ipp1-unusual-shapes.md`, `ipp1-unusual-heldout.md` |
| `ipp1_final_seeds.py`, `ipp1_traintest_gap.py`, `ipp1_uncertainty.py`, `ipp1_confidence.py` | experiment | seed noise, overfitting check, ensemble disagreement, per-target confidence; `ipp1-final-seeds.md`, `ipp1-traintest-gap.md`, `ipp1-uncertainty.md`, `ipp1-confidence.md` |
| `ipp1_inputs_ranking.py`, `ipp1_learning_curve.py`, `ipp1_limiter_swap.py` | experiment | input ranking by retraining, learning curves, limiter network swap; `ipp1-inputs-ranking.md`, `ipp1-learning_curve.png`, `ipp1-limiter-swap.md` |
| `ipp1_latency_cache.py` | experiment | latency of one estimate with hot and evicted cache; `ipp1-latency-shipped.md` |
| `ipp1_data_checks.py`, `ipp1_demo_facts.py`, `ipp1_claim_support.py` | experiment | numbers quoted on slides and in the demo; `ipp1-data-checks.md`, `ipp1-demo-facts.md`, `ipp1-claim-support.md` |
| `synth_validation.py` | experiment | closed test on simulated equilibria; `synthetic-validation.md` |
| `cloud_search.py`, `cloud_search_report.py`, `ipp1_search_dev.py` | experiment | large model search and its scoring; `cloud-search.md`, `ipp1-search-dev.md` |
| `cloud_camera_prepare.py`, `cloud_camera_model.py`, `cloud_camera_fusion.py`, `cloud_camera_explain.py` | experiment | camera model, fusion with magnetics, occlusion; `cloud-camera-*.md` |
| `ipp1_camera_prepare.py`, `ipp1_camera_model.py`, `ipp1_camera_v2_prepare.py`, `ipp1_camera_v2.py` | experiment | local camera cross check and the bigger camera network; `ipp1-camera-local-findings.md`, `ipp1-camera-v2.md` |
| `predict.py`, `check_predict.py` | tool | numpy-only prediction with the shipped model; check that it reproduces `ipp1_final.py` |
| `check_notebooks.py`, `check_claims.py`, `check_links.py` | tool | notebook checks (needs `nbformat`), numbers on the slides against `results/`, dangling path references |
| `make_submission.py`, `make_pdf.py` | tool | builds the submission package (`out/`), markdown to PDF |
| `make_chatgpt_brief.py`, `make_read_aloud.py`, `build_drill_cards.py`, `failure_gallery.py` | tool | speaker material in `presentation/` from the pitch script and the cheat sheet |
| `profile_data.py`, `fetch_wall.py` | tool | profile a data folder, download the public COMPASS wall outline |
