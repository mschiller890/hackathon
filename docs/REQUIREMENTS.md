# Requirements and Traceability

**Authoritative requirements record for this repository.** Process rules live in
[`../AGENTS.md`](../AGENTS.md) (§2, §6).

## Status: IMPLEMENTATION (updated Fri 23 Oct 2026 after the independent review and the audit)

Status cells were set by the auditor (`docs/internal/audit.md`, section 2) by reading the evidence file and the script that writes it;
the IPP data are not on the auditor's machine, so nothing was re-run: `DONE` means the committed files agree with each
other and with the acceptance criterion, with the caveat written in the row. Rows stay `IN PROGRESS` where the audit names
wording or a deliverable that is still open (listed in the row). Missing notebooks are the main delivery risk before the
Sat 02:30 checkpoint.

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
| REQ-001 | A model that determines plasma shape and position from magnetic measurements (the easier route) or from camera images (harder) | Cíle, 1 | Per-parameter errors on discharges unseen in training | IN PROGRESS, `DONE` once the T-3 wording is applied (slide 7 caption and `ipp1-final.md` say the 30 discharges were "never seen"; they were set aside before the final models were trained, but the recipe was chosen by cross validation over all 149). Evidence: `results/ipp1-baseline.md` and `.json` (baseline network, 5 folds by discharge, 16 targets; agrees with notebook 02), `results/ipp1-final.md` (shipped model on 30 discharges listed in `results/ipp1-locked-test-ids.txt`: radial axis 0.133 mm against 0.307 mm for the baseline, pooled MAE). Say "randomly chosen new discharges"; on contiguous blocks of ids the baseline error is 1.5 to 2.9 times larger |
| REQ-002 | Assess whether the model could run in real time (reaction in units to tens of milliseconds); GPU may be assumed | Cíle, 2 | Measured latency per sample and a written verdict | IN PROGRESS: `results/ipp1-latency.md` and `.json` (baseline network), `results/ipp1-latency-shipped.md` (shipped model); the verdict is conditional (wording rule below). Open before `DONE`: notebook 05 still shows an older latency run (audit T-6), slide 14 pairs the baseline latency with the shipped model's accuracy (T-5, `docs/deck-fixes.md` 14.1) |
| REQ-003 | Evaluate accuracy for each shape parameter and the stability of the outputs during the time evolution of the plasma | Cíle, 3 | Table per parameter and a plot over a discharge | DONE: `results/ipp1-time.md`, `.json`, `.png`, notebook 04 (all 16 targets, clean and noisy inputs; pooled MAE of the radial axis 0.377 mm equals the baseline). Keep: the jitter ratio is near 1 only for clean inputs; on noisy inputs the plain network's ratio is 1.1 to 17.8. The notebook cell text "7 of 16 targets, noisy not yet in table" is stale (audit REQ-003) |
| REQ-004 | Show how success changes with fewer inputs (fewer magnetic measurements or a smaller part of the image) and whether some inputs matter more | Cíle, 4 | Accuracy against the set of removed inputs; importance ranking | DONE: `results/ipp1-inputs.md` (how many inputs), `results/ipp1-inputs-controls.md` (random, QR-pivot and backward-ridge controls for the subsets) and `results/ipp1-inputs-ranking.md`, which replaces the rejected permutation ranking with two retraining rankings on the 119 development discharges only (locked set removed first): a paired drop-column refit per input and a deterministic greedy ridge elimination path. The finding is a negative one and must be worded as such: measured seed noise is 4.5 %. Removing any single input changes the error by less than the seed noise in at least one fold, except FL01 (+7.6 %, worse in 5 of 5 folds); IPR12, IPR13 and IPR14 rise most (+36, +15 and +13 %) but not in every fold. IPR13 is eliminated last in all 5 ridge folds and is the only stable single-input claim. The three rankings barely agree (Spearman -0.14 to +0.40). Say 'ranked by importance for the trained network', never 'the important sensors'. Notebook 03 still ranks by permutation importance only (audit T-7) |
| REQ-005 | Jupyter notebooks (Colab allowed) with the models and graphs, holding all detailed conclusions | Poznámky | Notebooks run top to bottom on a clean checkout | IN PROGRESS: `notebooks/01` to `05` exist with stored outputs (47 code cells, no error output); a clean top to bottom run after the notebook 04 fix `b7f5011` is not recorded. The notebooks hold no result for the shipped model, locked set, robustness, camera, learning curve, unusual shapes or time context: those conclusions live in `results/*.md` (audit T-7, `PLAN.md` IMPL-8) |
| REQ-006 | A presentation summarising the results | Poznámky | Delivered; the owner states 7 minutes plus a video | IN PROGRESS: `presentation/` (outline, pitch script, `deck/slides.pptx` with 14 slides and no placeholder; numbers on slides 5, 7, 11 and 12 equal `results/`); wording fixes in `docs/claims-corrections.md` and `docs/deck-fixes.md`; the PDF and the video do not exist yet |
| REQ-007 | Account for the uneven distribution of parameter values in training and evaluation | Poznámky | Documented handling and its effect on the metrics | IN PROGRESS: the table is delivered in `results/ipp1-distribution.md` (`analysis/ipp1_distribution.py`): pooled out-of-fold MAE, median, RMSE, p95, p99 and max per target, cut by configuration, by current polarity, by value quintile of each target and by the first 2 %, middle and last 2 % of the discharge, each with the group's share of the rows next to its share of the squared error. The review's numbers reproduce exactly (R axis 0.553 mm limited against 0.237 mm diverted, median 0.153 mm, p99 3.74 mm, worst row 64.3 mm). Still to do: the response to the finding (stratified folds or reweighting), not just its measurement; the shipped model is not a response to it |

**Wording rules from the review.** REQ-002: the verdict is "the network computation is not an obstacle: baseline network
median 0.0145 ms and p99 0.0209 ms for one sample, 0.0140 ms median and 0.0503 ms p99 end to end with numpy in and out
(`results/ipp1-latency.md`); shipped model 0.0154 ms (diverted) and 0.0274 ms (limited) median, p99 0.057 and 0.093 ms end
to end (`results/ipp1-latency-shipped.md`); all on one core of an Apple M5 on a shared machine (load average 5.7 and 7.0),
not an idle one; tails up to milliseconds on a system without real-time guarantees (an earlier loaded run: p99 0.65 ms,
max 21 ms); budget 1 to 10 ms". Name the processor and the model next to every latency number. Not verified: acquisition
and integration of the coil signals, the worst case on a real-time system, accuracy on really noisy signals (a network
trained on clean data fails on them: 9.16 mm on the axis for the plain baseline; the baseline network trained with noise
and drift gives 2.38 mm on the 30 set-aside discharges, `results/ipp1-final.md`). REQ-001: the 30 discharges were set aside
before the final models were trained and scored once; the recipe was chosen earlier by cross validation over all 149
discharges. REQ-003: the jitter ratio is about 1 only for clean inputs. REQ-004: say "ranked by importance for the trained
network", never "the important sensors".

## Optional bonus items (stated in the assignment)

| ID | Item | Status |
|---|---|---|
| REQ-B01 | A model for the second data source, or a multimodal one, and a comparison | DONE: `results/cloud-camera-multimodal.md`, `.json`, `.png` (same 14,520 frames and folds, magnetic network like for like). Camera plus magnetic beats camera alone on every target and loses to magnetics alone except R and Z limiter (12.6 and 28.0 against 16.7 and 30.4 mm). Caveat: 78 of 149 discharges, 48x64 pixels, every 8th frame, 12 epochs |
| REQ-B02 | Dependence of success on the number of training data | DONE: `results/ipp1-robustness-findings.md` section 2 and `results/ipp1-learning_curve.png` (the table reproduces the baseline at 119 discharges, 0.38 mm). Caveat stated in the file: fixed 60 epochs, so small sets also get fewer updates |
| REQ-B03 | Effect of a black and white camera | DONE: `results/cloud-camera-main.md` (5 folds: radial axis 1.79 mm colour, 1.70 mm grey; grey is not worse); the local 2-fold run in `results/ipp1-camera-local-findings.md` agrees (1.54 against 1.53 mm) |
| REQ-B04 | Whether several consecutive times (time context) improve the output | DONE: `results/ipp1-robustness-findings.md` section 3 and `results/ipp1-temporal.png` (helps on noisy input, hurts on clean; the reason is labelled a hypothesis) |
| REQ-B05 | Sensitivity of the camera model to camera position and rotation | DONE for the sensitivity: `results/cloud-camera-findings.md` ("Shifted and rotated camera"), `results/cloud-camera-main-sensitivity.png`: a shift of 1 px of the cached image (1.6 % of the width) roughly doubles the error, a rotation of 5 degrees multiplies it by 1.5 to 2.3. Training with random shifts (`augment`) is still `DOPLNIT` in the findings file; the only augmented result is the 2-fold local figure `results/ipp1-camera-local.png` |
| REQ-B06 | Robustness to measurement noise and linear drift (`equil_data_noisy.csv`, or drift generated as signal + noise + random coefficient per discharge times t) | DONE: `results/ipp1-robustness-findings.md` section 1, `results/ipp1-robustness.png` ("27 times larger" = 10.15 / 0.38 in section 1, checked). The provided noisy file has white noise and no measurable drift; every drift result is synthetic |
| REQ-B07 | Which image parts or magnetic measurements the model relies on | DONE with the REQ-004 wording: top-k, IPR only and flux loops only in `results/ipp1-inputs.md`; no per sensor ranking is claimed |
| REQ-B08 | Behaviour for a new, unusual shape that breaks the correlation between parameters | IN PROGRESS: `results/ipp1-unusual-shapes.md` (error 1.0 to 3.0 times larger on held-out groups that contain the 18 unusual shapes; the 18 were never held out alone, and the file itself says the extreme was not tested). Say "tested on groups containing the 18 unusual shapes" |

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
