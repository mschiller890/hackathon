# Requirements and Traceability

**Authoritative requirements record for this repository.** Process rules live in
[`../AGENTS.md`](../AGENTS.md) (§2, §6).

## Status: IMPLEMENTATION (updated Fri 23 Oct 2026 after the independent review)

Baseline and the required analyses are measured; notebooks and the camera model are in progress. No
requirement is `DONE` yet: each has evidence, and the review (`review-findings.md`) lists the caveats that must be
resolved or stated first. Missing notebooks are the main delivery risk before the Sat 02:30 checkpoint.

### Task chosen (history)

Hackathon: **CVUT ML Hackathon 2026**. Five tasks were offered (two from Ústav fyziky plazmatu
AV ČR, three from Datové centrum Ústeckého kraje). The team chose **IPP task 1, "Určení tvaru a
pozice plazmatu z magnetických měření a ze snímků z ultrarychlé kamery"** (plasma shape and
position from magnetic measurements and fast camera images, tokamak COMPASS); see
[`DECISIONS.md`](DECISIONS.md) DEC-002. Source text: `FJFI hackaton 2026 - úloha 1 (ekvilibrium) -
zadání.docx` (kept outside this repository, with the data). Every row below carries its source.

## Identifier scheme

- `REQ-NNN` a requirement, `ASM-NNN` an assumption, `OQ-NNN` an open question,
  `CON-NNN` a constraint. Identifiers are never reused or renumbered.
- Status: `TODO` · `IN PROGRESS` · `BLOCKED` · `DONE`. **A requirement is `DONE` only when its
  acceptance criteria are checked against evidence** (`AGENTS.md` §0, §15).

## Confirmed requirements (stated in the assignment)

| ID | Requirement | Source | Acceptance criteria | Status |
|---|---|---|---|---|
| REQ-001 | A model that determines plasma shape and position from magnetic measurements (the easier route) or from camera images (harder) | Cíle, 1 | Per-parameter errors on discharges unseen in training | IN PROGRESS: `results/ipp1-baseline.md` (5 folds by discharge, so "randomly chosen new discharges"; contiguous blocks of discharge numbers give errors about 1.5 times larger, measured by the review) |
| REQ-002 | Assess whether the model could run in real time (reaction in units to tens of milliseconds); GPU may be assumed | Cíle, 2 | Measured latency per sample and a written verdict | IN PROGRESS: `results/ipp1-latency.md`; the verdict is conditional (see below) |
| REQ-003 | Evaluate accuracy for each shape parameter and the stability of the outputs during the time evolution of the plasma | Cíle, 3 | Table per parameter and a plot over a discharge | IN PROGRESS: `results/ipp1-time.md` (clean inputs, 7 of 16 targets; noisy inputs and the limiter targets not yet in that table) |
| REQ-004 | Show how success changes with fewer inputs (fewer magnetic measurements or a smaller part of the image) and whether some inputs matter more | Cíle, 4 | Accuracy against the set of removed inputs; importance ranking | IN PROGRESS: `results/ipp1-inputs.md`; the ranking is permutation importance for the trained network, not information content; a drop-one or backward elimination ranking is still missing |
| REQ-005 | Jupyter notebooks (Colab allowed) with the models and graphs, holding all detailed conclusions | Poznámky | Notebooks run top to bottom on a clean checkout | IN PROGRESS: `notebooks/01` to `05` exist; a clean top to bottom run is not yet verified |
| REQ-006 | A presentation summarising the results | Poznámky | Delivered; the owner states 7 minutes plus a video | IN PROGRESS: `presentation/` (outline, pitch script, deck v1); wording fixes in `docs/claims-corrections.md` |
| REQ-007 | Account for the uneven distribution of parameter values in training and evaluation | Poznámky | Documented handling and its effect on the metrics | IN PROGRESS: the table is delivered in `results/ipp1-distribution.md` (`analysis/ipp1_distribution.py`): pooled out-of-fold MAE, median, RMSE, p95, p99 and max per target, cut by configuration, by current polarity, by value quintile of each target and by the first 2 %, middle and last 2 % of the discharge, each with the group's share of the rows next to its share of the squared error. The review's numbers reproduce exactly (R axis 0.553 mm limited against 0.237 mm diverted, median 0.153 mm, p99 3.74 mm, worst row 64.3 mm). Still to do: the response to the finding (stratified folds or reweighting), not just its measurement |

**Wording rules from the review.** REQ-002: the verdict is "the network computation is not an obstacle: median 0.015 ms on
an idle CPU (Apple M5), 0.03 to 0.07 ms on a loaded or different CPU, end to end with numpy in and out 0.053 ms, tails up to
milliseconds on a system without real-time guarantees, budget 1 to 10 ms". Not verified: acquisition and integration of
the coil signals, the worst case on a real-time system, accuracy on really noisy signals (a network trained on clean data
fails on them, one trained with noise gives 2.6 mm on the axis). REQ-003: the jitter ratio is about 1 only for clean inputs
and only for the 7 targets in the table. REQ-004: say "ranked by importance for the trained network", never "the important
sensors".

## Optional bonus items (stated in the assignment)

| ID | Item | Status |
|---|---|---|
| REQ-B01 | A model for the second data source, or a multimodal one, and a comparison | TODO |
| REQ-B02 | Dependence of success on the number of training data | IN PROGRESS: `results/ipp1-robustness-findings.md` section 2 (fixed 60 epochs, so small sets also get fewer updates; not yet redone with epochs scaled) |
| REQ-B03 | Effect of a black and white camera | IN PROGRESS: lane camera; first fold only (`out/ipp1-camera.log`), no conclusion yet |
| REQ-B04 | Whether several consecutive times (time context) improve the output | IN PROGRESS: `results/ipp1-robustness-findings.md` section 3 (helps on noisy input, hurts on clean; the reason is a hypothesis) |
| REQ-B05 | Sensitivity of the camera model to camera position and rotation | TODO |
| REQ-B06 | Robustness to measurement noise and linear drift (`equil_data_noisy.csv`, or drift generated as signal + noise + random coefficient per discharge times t) | IN PROGRESS: `results/ipp1-robustness-findings.md` section 1. The provided noisy file has white noise and no measurable drift; every drift result is synthetic |
| REQ-B07 | Which image parts or magnetic measurements the model relies on | IN PROGRESS: top-k, IPR only and flux loops only in `results/ipp1-inputs.md`; no per sensor ranking should be presented |
| REQ-B08 | Behaviour for a new, unusual shape that breaks the correlation between parameters | TODO (lane R: `analysis/ipp1_unusual_shapes.py` planned) |

## Constraints

| ID | Constraint | Source |
|---|---|---|
| CON-001 | The data were provided by ÚFP only for this hackathon. They must **not** be published or made accessible to anyone outside the participants without ÚFP's permission. Raw data never enter this repository | Dataset section |
| CON-002 | Train and test must be split by whole discharges (column `discharge`), not by rows | Poznámky |
| CON-003 | Columns `time` and `discharge` only index the rows and are not model inputs | Dataset section |
| CON-004 | No graphical user interface is required | Poznámky |

## Assumptions

| ID | Assumption | Basis |
|---|---|---|
| ASM-001 | Work on the magnetic data first; the camera model is a late bonus | The assignment calls the magnetic route the easier one |
| ASM-002 | Errors are reported in physical units (millimetres, kiloampères) and relative to each parameter's spread | Spreads (standard deviation) are 2.4 to 13.7 mm for the axis, X-point and strike points only; 90 and 153 mm for the limiter point (R, Z); 114 kA for the plasma current (measured, `docs/DECISIONS.md` DEC-003). The limiter point is a discrete wall contact (66 and 111 distinct values), so a classifier plus a regressor may fit it better |
| ASM-003 | The hackathon's judging weights favour presentation and functionality | Owner's statement; not confirmed by the organizers |

## Open questions

| ID | Question | Needs |
|---|---|---|
| OQ-001 | Judging criteria weights and the jury | Organizers |
| OQ-002 | Exact submission time and the length limit of the video | Organizers |
| OQ-003 | The task text allows the column `mode` as an input, but `equil_data.csv` has no such column | Organizers |
| OQ-004 | The example plotting code needs `COMPASS_stena.csv` (wall outline), which is not in either data zip | Organizers' repository |
