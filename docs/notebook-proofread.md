# Notebook proofread and patch list (Fri 23 Oct 2026, evening)

Reviewer: a cloud session that read every notebook cell by cell (markdown, code comments, stored outputs, figure titles and
axis labels, read with `nbformat`) against `docs/claims-corrections.md`, `docs/review-physics.md`, `docs/review-findings-2.md`,
`docs/review-findings-3.md`, `docs/notebook-review.md` and the aggregates in `results/`. There are no IPP data in this
mirror, so **nothing was executed**; every number below was read from a stored notebook output or a file in `results/`, and
every replacement sentence uses only numbers I saw there. I did not edit any notebook, script, result file or other
document (only this file and one row of `docs/PLAN.md`). The notebooks belong to lane K (`01` to `05`, `07`, `08`) and
bladed-85 (`09`); they apply the patches.

**Notebooks present:** `01`, `02`, `03`, `04`, `05`, `07`, `08`, `09`. `06` (camera) does not exist yet (PLAN IMPL-19 waits for gate
G1), so there is nothing to proofread there and no notebook may point to it.

**Cell numbers** are the 0-based index in the `.ipynb` (markdown cells count), not the `In [ ]` number. `c21` = cell 21.
**Severity:** High = a wrong or unconditional claim, or a number that contradicts the code output next to it or `results/`;
Medium = a missing caveat or a wording that a physicist or ML reviewer will attack; Low = polish.
**Size:** `1-line` = one sentence or one string literal in one cell; `cell` = rewrite one cell; `new cell` = add a cell; `multi` = the
same change in several places (listed).

## 0. Verdict

**Count.** 92 patches: 12 High, 35 Medium, 45 Low (G-1 to G-7 for the whole set, then `01-1` ... `09-13`). 64 are one-line edits (section 13).

1. **`07`, `08`, `09` are in good shape** (question first, protocol above every table, units, conditional wording, `08` already
   says white noise, no drift, conditional real time). They are data free (`07`, `08`) or build on the `make_all.py` cache (`09`).
   What remains there: the word "locked" and "nobody trained on" as design claims in `09`, "later campaigns" resting on
   unconfirmed chronological ids, "reversed polarity" without a sign convention in `07`, "fair stand-in" for the noise in `08`,
   "true" in `07` figure labels.
2. **`01` to `05` still carry every item of `docs/notebook-review.md`** (I checked each one against the current files: none was
   applied) **and none of the wording of `docs/review-physics.md`.** The main High items are: `03` c17 "The coils carry almost all
   the information", `04` c20 "The output is as smooth as the truth" and "Smoothing in time does not help", `05` c14 verdict and
   its "saved quiet run" numbers, and `02`/`04` calling the labels "truth" and the agreement "accuracy".
3. **Wording rule for all notebooks** (physics H1, M2, claims-corrections 4): the targets are the institute's reference
   reconstruction, not a measurement of the plasma. Say "reference reconstruction" for what is called "true", "truth", "real"
   or "correct answers", say "agreement" or "difference from the reference reconstruction" for "accuracy", and say "estimate" for
   "prediction" in prose (variable and column names stay). Section 1 lists every place.
4. **Every number in a markdown cell was compared with the output next to it.** Mismatches found: `03` c17 "1.23 times" (output
   1.2246, so 1.22), `01` c21 "99.92 %" (`results/ipp1-claim-support.md` says 99.93 %), `02` c19 "10.8 mm" and "22.3 mm" against the
   table in c7 (10.73 and 22.19, the text uses the pooled values of c14), `04` c20 "82 %" (0.8145, so 81 %), `02` c19 "0.0081"
   (printed 0.0082), `05` c14 and c3 (the stored run is not the run in `results/ipp1-latency.md`), `09` c24 "1.2 to 2.4 times"
   (the file says 1.0 to 3.0, typically 1.2 to 2.4). Everything else agrees.
5. **Files not in git:** `01` to `05` and `09` need the raw data and `out/` files; section 2 lists the `make_all.py` step that creates each.

## 1. Cross-cutting patches (apply in every listed notebook)

**G-1 (High, multi). Reference reconstruction wording.** The places:

| Nb, cell | Exact text now | Replace with |
|---|---|---|
| 01 c15 | "has the same rows and the same correct answers" | "has the same rows and the same reference values (labels)" |
| 02 c10 | "## 4. Figures: relative error per target, and predicted against true" | "## 4. Figures: relative error per target, and estimate against reference" |
| 02 c12 | `a.set_xlabel(f"true [{unit or 'abs'}]"); a.set_ylabel("predicted")` | `a.set_xlabel(f"reference reconstruction [{unit or '-'}]"); a.set_ylabel(f"network estimate [{unit or '-'}]")` |
| 02 c12 | `fig.suptitle("Out-of-fold prediction against truth (density of rows, log count; orange = perfect)")` | `fig.suptitle("Out-of-fold estimate against the reference reconstruction (density of rows, log count; orange line = exact agreement)")` |
| 04 c0 | "The truth is read back from the data." | "The reference values (the institute's reconstruction) are read back from the data." |
| 04 c6 | "divided by the same for the truth (1 means equally smooth;" | "divided by the same for the reference values (1 means equally smooth;" |
| 04 c11 | `label="truth"` (two bar and line plots of one discharge) | `label="reference reconstruction"` |
| 04 c14 | "Speed of change = \|change of the true value between two neighbouring rows\| / change of relative time." | "Speed of change = \|change of the reference value between two neighbouring rows\| / change of relative time (unit: the target's unit per unit of relative time; the real time between rows is not in the file)." |
| 07 c7 | `"; limited = true `is_limited`; rows and sq err in %"` | `"; limited = `is_limited` of the reference reconstruction; rows and sq err in %"` |
| 07 c12 | "cut into five equal groups by the true value of each target" | "cut into five equal groups by the reference value of each target" |
| 07 c13 | `ax.set_xlabel("quintile of the true value")` and `plt.suptitle("MAE by quintile of the true value (P1)")` and the print label "R_mag_axis quintile edges" | replace "true value" by "reference value" in these three display strings only. **Do not** change the column name `"range of the true value"` in `numeric(... text=(...))`: it is the header of `results/ipp1-distribution.md` and the parser needs it. (Lane L may rename the header in the results file and the notebook together later.) |
| 08 c6, c17, c20 | "A network trained on clean data is accurate and fragile", "the same network is accurate on clean signals and fails on noisy ones", "**The network is accurate on clean signals and not robust to noise unless it is trained with noise, and this has a price.**" | "A network trained on clean data agrees closely with the reference reconstruction and is fragile", "the same network agrees closely with the reference reconstruction on clean signals and fails on noisy ones", "**The baseline network agrees closely with the reference reconstruction on clean signals and is not robust to noise unless it is trained with noise, and this has a price.**" |
| 09 c0 | "How accurate is the shipped model on whole discharges that none of its networks was trained on" | see 09-2 |

Also write "estimate" instead of "predict" in prose when no future is meant: `02` c0 "predict the plasma shape" (see 02-1), `01` c17
"predicts `R_mag_axis`" (fine for a regressor, leave), `04` c0 title "does the prediction stay accurate and smooth" (see 04-1).

**G-2 (Low, 1-line in 6 notebooks). `next(p for ...)` raises a bare `StopIteration` outside the repository** (`01` c1, `02` c1, `03` c1, `04` c1,
`05` c1, `09` c1). Replace
`repo = next(p for p in [here, *here.parents] if (p / "analysis" / "ipp1_common.py").exists())` by
`repo = next((p for p in [here, *here.parents] if (p / "analysis" / "ipp1_common.py").exists()), None)` and add the line
`if repo is None: raise SystemExit("Run from inside the repository")`. (`07` and `08` already do this.)

**G-3 (Medium, 2 cells in 6 notebooks). "Key numbers (read by the conclusions below)" is untrue and prints a block of numbers.** The
conclusions are typed text, not generated. Cells: `01` c19+c20, `02` c17+c18, `03` c15+c16, `04` c18+c19, `05` c12+c13, `09` the heading
inside c22 plus c23. Delete the `print("KEY_JSON", ...)` cell (it is a debug dump of 40 to 60 numbers) and change the heading to
"## Key numbers" only if the cell is kept; if it is deleted also delete its heading. If lane K prefers to keep the dump, the
heading must read: "## Key numbers (stored for the record; the conclusions below were typed from the outputs of the stored run
and differ slightly after a rerun)". Add that last sentence under the conclusions of `01` to `05` in any case (F-04).

**G-4 (Medium, `new cell` per notebook). Each notebook ends with a plain answer to the question in its first cell** (F-07). The
exact sentences are in sections 3 to 10 ("Answer"). Only `07` and `08` have one today.

**G-5 (Low, multi). Units.** (a) `unit or 'abs'` in a figure title or axis label should read `unit or '-'`: `01` c8, `01` c14, `02` c12 (see G-1), `04` c11;
"abs" reads like "absolute value". (b) `01` c14 `C.UNIT.get(c, (1, 'raw input'))[1]` should read `'file units'` (the organizers do not state the unit of the
inputs). (c) the time axes `ax.set_xlabel("relative time")` in `01` c14 and `04` c11 should read
`"relative time within the discharge [0 to 1]"`. (d) `07` tables print an empty unit for elongation, triangularity and `is_limited`
(the results files leave the cell empty): in `numeric()` (`07` c1 and `08` c1) add as the second line after `df = df.copy()`:
`if "unit" in df.columns: df["unit"] = df["unit"].replace("", "-")`. (e) the dimensionless summary error is never given a
unit: add "[-]" in `03` c7 and c12 `set_ylabel("summary error (nRMSE) [-]")`.

**G-6 (Low). Spelling.** The notebooks mix British ("standardised", "neighbouring", "initialisation", "canonicalised", "standardise") with American
("organizers", `08` c11 "optimizer updates"). The README and the results use American. Pick American: `01` c9, c17, c21; `04` c14, c20;
`05` c0, c6, c14; `07` c20, c21, c26; `08` c20; `09` c0, c12, c18, c22, c24. Nothing else was misspelled (a dictionary check of all markdown cells found no typo).

**G-7 (Medium). Runtime lines** (F-05, still missing in `01` to `05`): add one line under the question of each notebook, "Runtime: about N min (2 CPU threads); needs ...", using
section 2. Use the make_all timings of `analysis/make_all.py` (Ryzen 5 7535HS): `01` and `02` need only the data (02: 172 s of training on the
owner's Mac), `03` needs `out/ipp1-inputs.json` (about 1 h, or `--quick`), `04` 45 s + 3 s, `05` 10 s.

## 2. Files the notebooks need that are not in git, and the step that creates them

CON-001: the raw data are never in git. A clean checkout of this private mirror runs only `07` and `08`.

| Nb | Needs (not in git) | Created by (`analysis/make_all.py`, time on the Ryzen laptop) | If missing |
|---|---|---|---|
| 01 | `data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv`, `equil_data_noisy.csv` (organizers' zip, `HACKATHON_HOME`) | none: manual download (README, "Setup and run") | `C.load()` fails in c3 (c1 prints `False`) |
| 02 | the same raw files; optional `out/ipp1-baseline.json` | `ipp1_baseline.py` (1 min) | without the json c9 prints "comparison skipped", yet the conclusions still say "ratio ... 1.0000 to 1.0000, so the training is reproducible" (02-9) |
| 03 | raw files; `out/ipp1-inputs.json`; `scipy` (c9, undeclared in the README install line if it is not in the venv) | `ipp1_inputs.py` (about 1 h; `--quick` copies `results/ipp1-inputs.json`) | `FileNotFoundError` in c3 |
| 04 | raw files; `out/ipp1-predictions.csv`; `out/ipp1-time.json` | `ipp1_oof.py` (45 s), `ipp1_time.py` (3 s); the committed `results/ipp1-time.json` is the same numbers | `FileNotFoundError` in c3 and c5 |
| 05 | raw files (c7 trains one epoch); `out/ipp1-latency.json`; the GPU rows only exist on an Apple machine | `ipp1_latency.py` (10 s); **a rerun gives new tail numbers** (02-9 and 05-3) | `FileNotFoundError` in c3 |
| 07 | none beyond git: `results/ipp1-data-checks.md`, `ipp1-distribution.md`, `ipp1-final.md`, `ipp1-signcanon.md`, `ipp1-unusual-shapes.md` and `.png` | none | the notebook asserts that every file it read is tracked |
| 08 | none beyond git: `results/ipp1-data-checks.md`, `ipp1-robustness-findings.md`, `ipp1-final.md`, `ipp1-time.json`, `ipp1-latency.json` | none | same assertion |
| 09 | raw files (`F.aligned_data()`); the 21 files `out/ipp1-final-cache/{locked,blocked}_{base,cand,base_aug}.npz` and `cv_{base,cand,base_aug}_{0..4}.npz`; reads the committed `results/ipp1-final.md`, `ipp1-final-seeds.md`, `ipp1-latency-shipped.md`, `ipp1-latency.md`, `ipp1-locked-test-ids.txt` | `ipp1_final.py --job locked:base` and the other 20 jobs (295 s in total on an Apple M5); c1 asserts with the message "run analysis/make_all.py first" | assertion in c1 |

Kernels: `01` to `05` and `09` ask for the kernel `hackathon` (README: `python -m ipykernel install --user --name hackathon`); `07` and `08` carry `python3` and
Python 3.13 metadata, the others Python 3.12. Harmless, but set the same name in `07` and `08` (Low, metadata only).

## 3. Notebook 01 Data exploration

Opens with the question (c0). Ends with a list, no answer sentence (01-14). Numbers checked against the outputs and `results/`: rows 42,972,
149 discharges, 17/293/439, 92.6 %, 44.2 %, 11 rows, 0.976, 56 %, 15 %, 8.6 to 16.7 %, 0.050/0.052, 0.62/2.03 mm, factor 3.3, median correlation 0.57: all agree.

**01-1 (Medium, c21 bullet 3, 1-line).** Variance, not information (claims-corrections 5).
Now: "- **The inputs are redundant.** The first 5 principal components of the 24 inputs hold 99.92 % of the variance (5 components reach 99.9 %), and the median absolute correlation between two inputs is 0.57. This is why fewer inputs can work (notebook 03)."
Replace: "- **The inputs are redundant in variance.** The first 5 principal components of the 24 inputs hold 99.93 % of the variance (5 components reach 99.9 %), and the median absolute correlation between two inputs is 0.57. This is not the same as redundant information: a network that sees only those 5 components has a radial axis error of 2.63 mm against 0.41 mm with all 24 inputs (same folds and seed, `results/ipp1-data-checks.md`). Notebook 03 tests fewer sensors directly."
The 99.93 replaces 99.92 because `results/ipp1-claim-support.md` gives 99.93 % and the c10 output rounds to 0.99925.

**01-2 (Medium, c21 bullet 5, 1-line).** The noisy file is white noise without drift, and the noise is probably synthetic (claims-corrections 6, physics H5).
Now: "- **The noisy file** has the same rows and identical targets; the added noise is 8.6 % to 16.7 % of each input's spread (median 15.5 %). Its mean absolute correlation with time inside a discharge is 0.050, the same as for the shuffled control (0.052), so this check finds no drift component in the provided noisy file; drift would have to be simulated separately."
Replace: "- **The noisy file** has the same rows and identical reference values. The standard deviation of the added noise is 8.6 % to 16.7 % of the standard deviation of each input (median 15.5 %; about 9 % for the flux loops and 16 % for the coils). The noise is white (lag-1 autocorrelation -0.004, `results/ipp1-data-checks.md`) and shows no measurable drift: its mean absolute correlation with time inside a discharge is 0.050, the same as for the shuffled control (0.052). The narrow range of the ratio suggests that the noise was added in proportion to each input (our inference, not confirmed) and its size may be larger than the noise of real probes (to be checked with the institute), so errors on this file are a stress test, not an expected operating accuracy. Every drift result in notebook 08 uses a drift we generated."
Optional, to compute the lag-1 value here instead of quoting the file (untested sketch for c16, expected about -0.004): loop over `df.groupby("discharge").indices.values()`, order each by `t_all[idx]`, take the Pearson correlation of `noise[o][:-1]` and `noise[o][1:]` per input and average. Quoting the file is enough.

**01-3 (Low, c21 bullet 2 and c7 output, 1-line).** The X point is always the lower one (physics table, section 0): the c7 table shows `Z_x_point` from -357.9 to -280.2 mm.
Append to bullet 2: "`Z_x_point` lies between -358 and -280 mm in every divertor row, so the X point is always the lower one (lower single null); the data hold no upper X point and no double null, so nothing is known about them."

**01-4 (Low, c21 bullet 4, 1-line).** Spread caveat (claims-corrections 7) and elongation below 1 (physics M8).
Now: "- **Shapes are uneven and strongly correlated.** Elongation runs from 0.89 to 1.89, its correlation with triangularity is 0.976,"
Replace: "- **Shapes are uneven and strongly correlated.** Elongation runs from 0.89 to 1.89 (values below 1 are unusual for a tokamak plasma and the organizers' formula is not recorded here, so we do not interpret those rows; to be checked with the institute), its correlation with triangularity is 0.976,"
And add a bullet after it: "- **The spread is small only for the axis, the X point and the strike points** (standard deviation 2.4 to 13.7 mm); the limiter point has 90 mm (R) and 153 mm (Z) and the plasma current 114 kA, so errors are given in physical units and next to the spread of each target."

**01-5 (Low, c21 bullet 1, 1-line).** Add: "The real time between two rows is not in the file (`time` is relative), so nothing in this repository is a statement in milliseconds per row (open question for the organizers)."

**01-6 (Medium, c21 bullet 6, 1-line).** "every model" and the optimism of random group folds.
Now: "A row split would make every model look far better than it is."
Replace: "A row split would make this model look about 3 times better than it is, and other models are likely flattered too. Random group folds are still optimistic for a later campaign: the discharge numbers appear to follow time (not confirmed with the organizers) and on higher-numbered discharges the error is larger (notebooks 08 and 09)."

**01-7 (Low, c9, 1-line).** Now: "Principal components of the 24 standardised inputs show how many independent directions the sensors really carry." Replace: "Principal components of the 24 standardised inputs show how much of the variance lies in a few directions."

**01-8 (Low, c4, 1-line).** Add the unit of the inputs (N-01-04): append to c4 "Input units are those of the file (the organizers do not state them); every model standardises the inputs first."

**01-9 (Low, c3, 1-line).** The printed "median step 0.0030" has no unit: `print(f"relative time runs from ... median step {KEY['median_time_step']:.4f}")` -> append " (fraction of the discharge)".

**01-10 (Low, c8, 2 lines).** The histograms have no y label: after the loop `for a in ax[:, 0]: a.set_ylabel("number of rows")`. Titles use `unit or 'abs'` (G-5).

**01-11 (Low, c12 text and c11).** "Elongation and triangularity lie on a narrow curve, so the data contain few unusual shapes." is right; add "(the 18 discharges with low elongation are examined in notebook 07)".

**01-12 (Low, c14).** The figure draws the raw `IPR05` input and a real discharge trace; RP-6 (owner, 23 Oct 19:35) allows one real discharge in the talk. Whether the notebooks may ship these figures in the submission is not stated; the owner decides and writes it into `docs/SUBMISSION.md` (F-06).

**01-13 (Low, c5).** The table of inputs: the unit is missing in the output (01-8 covers it).

**01-14 (Medium, new cell, G-4). Answer.** "**Answer.** Split by whole discharges (a row split flatters a nearest-neighbour model about 3.3 times), mask the targets that do not exist (they are missing exactly in the other configuration), give errors in mm and kA next to the spread of each target, and treat the redundancy of the inputs as redundancy in variance only: 5 components hold 99.93 % of the variance, yet a network on them has 2.63 mm radial axis error against 0.41 mm. The provided noisy file is white noise with no measurable drift."

## 4. Notebook 02 Baseline models

Opens with the question. Numbers checked against the table in c7, `results/ipp1-baseline.md` and the c14 output: ridge and network columns, 99.26 %, 163 rows, 3.3, 7.3, 43: agree except where listed.

**02-1 (High, c0, 1-line).** The question says "predict the plasma shape" and "accurately"; the model estimates 16 numbers of a reference reconstruction (physics H1, H2) and this is the baseline network (F-02).
Now: "**Question.** How accurately can the 24 magnetic measurements predict the plasma shape on whole discharges the model has never seen, and how much does a neural network gain over a linear model?"
Replace: "**Question.** How closely can the 24 magnetic measurements reproduce the 16 shape parameters of the institute's reference reconstruction (position of the magnetic axis, the lower X point, two strike points and the limiter point, elongation, three triangularities, the plasma current and the limited flag) on randomly chosen whole discharges that the model did not train on, and how much does a neural network gain over a linear model? The plasma outline is not estimated. These results are for the baseline network; the model we ship is evaluated in notebook 09."

**02-2 (Low, c0).** Now: "Both are trained for real in this notebook." Replace: "Both are trained in this notebook." Also in the Protocol sentence: "errors in physical units (mm, kA) and relative to the spread of the target (nRMSE = RMSE / std)" is fine.

**02-3 (Medium, c19 bullet 2, 1-line).** "accurate", "typical error", and the tail (N-02-01, N-02-02).
Now: "- **The network is accurate on unseen discharges.** Mean absolute error: `R_mag_axis` 0.38 mm, `Z_mag_axis` 0.39 mm, `R_x_point` 0.20 mm, `R_strike_point_1` 0.26 mm, `R_strike_point_2` 0.23 mm, elongation 0.0057, plasma current 1.49 kA. `is_limited` accuracy is 99.26 %. Typical errors are 1.3 % to 4.7 % of the spread of the target (limiter point excluded)."
Replace: "- **The network agrees closely with the reference reconstruction on discharges it did not train on** (random group folds; the labels are the institute's reconstruction, not an independent measurement of the plasma). Mean absolute difference: `R_mag_axis` 0.38 mm, `Z_mag_axis` 0.39 mm, `R_x_point` 0.20 mm, `R_strike_point_1` 0.26 mm, `R_strike_point_2` 0.23 mm, elongation 0.0057, plasma current 1.49 kA. `is_limited` agrees in 99.26 % of the rows. The mean absolute error is 1.3 % to 4.7 % of the standard deviation of each target (limiter point excluded); the nRMSE, which weights large errors more, is 2.7 % to 13.9 %. The mean hides a tail: for `R_mag_axis` the median is 0.15 mm, 99 % of the rows are below 3.7 mm and the worst row is 64 mm (`results/ipp1-distribution.md`), mostly at the two ends of a discharge. The discharge numbers appear to follow time (not confirmed with the organizers); trained on the 60 lowest and tested on the 59 highest development discharges the radial axis error is 1.23 mm instead of 0.45 mm on the same discharges (`results/ipp1-final.md`; part of this is the smaller training set; see notebook 09)."
Optional code for c14 (one line, prints the tail the sentence quotes): `print({t: [round(float(np.nanmedian(np.abs(P_mlp[:, J[t]] - Y[:, J[t]]) * C.UNIT[t][0])), 3), round(float(np.nanpercentile(np.abs(P_mlp[:, J[t]] - Y[:, J[t]]) * C.UNIT[t][0], 99)), 2)] for t in ("R_mag_axis", "Z_mag_axis")})`. (Untested; the 0.15 and 3.7 are from `results/ipp1-distribution.md`.)

**02-4 (Low, c19 bullet 5, 1-line).** The limiter bullet quotes pooled values (10.8 and 22.3 mm) while the table in c7 right above shows the fold means 10.73 and 22.19. Replace "`R_limiter` has an MAE of 10.8 mm ... and `Z_limiter` 22.3 mm" by "`R_limiter` has an MAE of 10.7 mm (12 % of its spread of 90 mm) and `Z_limiter` 22.2 mm (14 % of 153 mm)" and keep the pooled 10.8 mm only where the sentence says "when the class is right and 14.5 mm when it is wrong" (those come from the pooled c14 table: write "pooled over all out-of-fold rows, `R_limiter` MAE is 10.8 mm ...").

**02-5 (Low, c19 bullet 5, 1-line).** N-02-05: "Wrong `is_limited` classification ... is not the main cause: the `R_limiter` MAE is 10.8 mm when the class is right and 14.5 mm when it is wrong." Add: "For `Z_limiter` a wrong class is not worse (18.0 against 22.3 mm)."

**02-6 (Low, c19 bullet 6, 1-line).** N-02-03: "for elongation 0.0081 and 0.0037" -> "for elongation 0.0082 and 0.0037" (the c14 table prints 0.0082).

**02-7 (Medium, c19 bullet 7, 1-line).** REQ-007 (N-02-04). Append: "Limited plasma carries 91.9 % of the squared `R_mag_axis` error with 44.2 % of the rows, the 16 discharges with positive current sign 77.8 % with 7.4 % of the rows, and the last 2 % of a discharge 26.9 % with 2.2 % of the rows (notebook 07). This was measured, not corrected: no reweighting and no stratified folds were tried." Also append to the same bullet: "The sparsest elongation bin holds values below 1 (0.89 to 0.99), which are unusual for a tokamak plasma; the organizers' definition is not recorded here."

**02-8 (Medium, c19 bullet 4, 1-line).** Plasma current: why it is linear (physics M1). Append: "This is expected from Ampere's law: the 16 IPR coils integrate the magnetic field around the vessel. The agreement of 0.035 kA on a spread of 114 kA (0.03 %) suggests that the reference current was derived from the same signals and was not measured independently (our inference, not confirmed)."

**02-9 (Low, c19 bullet 1, 1-line).** N-02-06. Now: "... (ratio of the MAE values from 1.0000 to 1.0000), so the training is reproducible." Replace: "... (ratio of the MAE values from 1.0000 to 1.0000 on the owner's machine with the same number of threads; another CPU gives small differences, and without `out/ipp1-baseline.json` this comparison is skipped)." Also "172 s on a busy machine with 2 threads" is a machine fact: keep, it matches the c5 output.

**02-10 (Low, c14 xlabel, 1-line).** `a.set_xlabel(f"log10 |error| [{unit}]")` -> `a.set_xlabel(f"log10 of |error| in {unit}")`.

**02-11 (Low, c11, 1-line).** The title "Relative error on unseen discharges" -> "Relative error on discharges not used for training"; the second title "Typical error as a share of the spread (limiter targets in orange)" -> "Mean absolute error as a share of the standard deviation (limiter targets in orange)".

**02-12 (Medium, new cell, G-4). Answer.** "**Answer.** On randomly chosen discharges that the model did not train on, the network differs from the institute's reference reconstruction by a mean of 0.38 mm (radial) and 0.39 mm (vertical) on the axis position (median 0.15 mm, 99 % of the rows below 3.7 mm), and it is 7.3 times better than ridge on the summary error; only the plasma current is better with the linear model (0.035 against 1.49 kA). The weak spot is the limiter point (10.7 mm and 22.2 mm), and the error is concentrated in limited plasma, in the discharges with positive current sign and at the ends of a discharge."

## 5. Notebook 03 Inputs and importance

Opens with the question. Numbers checked: 0.0633, 0.0657, 0.2852, 4.51, 1.05, 1.49, 2.26, 3.2, 0.38 to 0.90 mm, 0.46, 0.86/0.79, 0.463, 7.3, 0.495, 0.517, 0.028: agree; one mismatch (03-5).

**03-1 (High, c0, 1-line).** "matter most" invites the importance reading that claims-corrections 4 forbids.
Now (title): "# 03 Inputs and importance: which measurements matter and how few are enough"
Replace: "# 03 Inputs and importance: how few measurements are enough, and which ones the trained network relies on"
Now: "**Question (REQ-004).** Which of the 24 magnetic measurements (16 coils `IPR01-16`, 8 flux loops `FL01-08`) matter most, and how does the accuracy fall when fewer inputs are used?"
Replace: "**Question (REQ-004).** How does the agreement with the reference reconstruction fall when fewer of the 24 magnetic measurements (16 coils `IPR01-16`, 8 flux loops `FL01-08`) are used, and which inputs does the trained network rely on? The ranking describes the trained network, not the information content of a sensor."

**03-2 (High, c17 bullet 1, 1-line).** (claims-corrections 4, N-03-01)
Now: "- **The coils carry almost all the information.** The network trained on the 16 `IPR` coils alone has a summary error of 0.0657 against 0.0633 with all 24 inputs (1.04 times), while the 8 flux loops `FL` alone give 0.2852 (4.5 times worse)."
Replace: "- **The 16 coils alone are almost as good as all 24 inputs.** The network trained on the 16 `IPR` coils alone has a summary error of 0.0657 against 0.0633 with all 24 inputs (1.04 times, within the seed noise), while the 8 flux loops `FL` alone give 0.2852 (4.3 times worse than the coils alone, 4.5 times worse than all 24). We do not say which sensor is the most important."

**03-3 (Medium, c7 and c12 titles, 1-line each).** c7: `ax[1].set_title("Permutation importance (blue IPR coils, orange FL loops)")` -> `ax[1].set_title("Permutation importance for the trained network, not information content (blue IPR coils, orange FL loops)")` (shorten the font or wrap if too long). c12: `ax[2].set_title(f"Importance, two models (Spearman {sp.statistic:.2f})")` is fine.

**03-4 (Medium, c8, 1-line).** Now: "(this still needs all 24 sensors, it only shows how much information the sensors carry in total)". Replace: "(this still needs all 24 sensors; it only shows how the error behaves when the inputs are reduced to their first k variance directions)".

**03-5 (Low, c17 bullet 2, 1-line).** The text "0.0775 for 12 (1.23 times)" -> "0.0775 for 12 (1.22 times)"; the table in c3 prints 1.2246.

**03-6 (Medium, c17 bullet 2 caveat, 1-line).** (N-03-03) Append to the "Caveats" bullet: "Seed noise of the same network is 4.5 % (`results/ipp1-inputs-ranking.md`; earlier measurements 8 to 19 %), so differences below about 10 % (16 inputs, the coils alone and all 24) are not resolved."

**03-7 (Medium, c17 bullet 4, 1-line).** Now: "... so the ranking should be reported as a property of the trained model and not as a physical truth." Replace: "... so the ranking is reported as a property of the trained model, not of the sensors. Three rankings that we computed (permutation, ridge, backward elimination) hardly agree (Spearman -0.14 to 0.40, `results/ipp1-inputs-ranking.md`), and no single input is individually necessary."

**03-8 (Medium, c17 bullet 5, 1-line).** (N-03-04) Now: "... Ridge on 5 principal components gives 0.517." Append: "A projection on principal components needs all 24 sensors, and a network on the first 5 components has a radial axis error of 2.63 mm against 0.41 mm (`results/ipp1-data-checks.md`). The table row '24 principal components' (0.439) is lower than 'all 24' (0.463) although both use all 24 sensors; the reason was not checked, so that row is not used as evidence." (Alternatively drop the row from the table.)

**03-9 (High, new cell after c14).** The REQ-004 evidence of `results/ipp1-inputs-controls.md` and `ipp1-inputs-ranking.md` is missing (N-03-02): add a section "6. Controls and retraining rankings" that reads `results/ipp1-inputs-controls.json` and prints the control table (random 12: 0.099, permutation top 12: 0.077, QR pivot 12: 0.065, QR pivot 8: 0.072 against permutation top 8: 0.115) and the Spearman values, with the bullet: "Which subset of 8 or 12 inputs is chosen matters more than the permutation rank: a QR-pivot subset of 8 (0.072) beats the permutation top 8. The only single-input statement we defend is that IPR13 survives backward elimination in all 5 folds." Note `results/ipp1-inputs.md` gives "top 8" 0.094 while `ipp1-inputs-controls.md` gives "permutation top 8" 0.115 (F-08, still open): state which one is quoted.

**03-10 (Low, c7/c9).** N-03-05: `names`, `imp`, `ks`, `vals`, `errs` are defined in c7 and used in c9 and c12; move `names = saved["inputs"]` and the four definitions to c3 so section 3 runs alone.

**03-11 (Medium, new cell, G-4). Answer.** "**Answer.** The 16 IPR coils alone give a summary error of 0.066 against 0.063 for all 24 inputs; the 8 flux loops alone give 0.285 (4.3 times worse than the coils). Twelve inputs kept by permutation importance are within 1.22 times of all 24 and eight within 1.49 times, but which subset is chosen matters more than the rank, and the ranking is a property of the trained network, not a statement about which sensor is important."

## 6. Notebook 04 Stability over time

Opens with the question. Numbers checked against the outputs: 0.97/1.03/1.07, offsets 0.10/0.62/0.82 (see 04-6), 456 and 137, 99.4 %, 15.9 %, 0.0090/0.0050, 0.28/0.57, 0.24/1.48/6.80, -0.29: agree.

**04-1 (High, c20 bullet 3, 1-line).** The unconditional stability claim (claims-corrections 2, N-04-01).
Now: "- **The output is as smooth as the truth.** The jitter ratio (1 means the same row-to-row change as the truth) is 0.97 for `R_mag_axis`, 1.03 for elongation and 1.07 for the plasma current. The saved table in `out/ipp1-time.json` is reproduced exactly (largest relative difference 2e-16)."
Replace: "- **On clean inputs the output varies as the reference values do.** The jitter ratio (1 means the same row-to-row change as the reference reconstruction) is 0.97 for `R_mag_axis`, 1.03 for elongation and 1.07 for the plasma current, 0.97 to 1.07 for the 7 targets shown; the limiter points are lower (0.69 and 0.48, `results/ipp1-time.md`). This is not a statement about noisy signals: with the provided noisy inputs the network trained on clean data varies 8.4 times (radial axis) and 3.3 times (vertical axis) more than the reference values, and 1.7 times after training with noise and drift (notebook 08, section 3). The ratio is amplitude weighted: it says the network is smooth when its input is smooth, not that it is robust. The saved table in `out/ipp1-time.json` is reproduced exactly (largest relative difference 2e-16)."
Also change c0 title and question: Now "# 04 Stability over time: does the prediction stay accurate and smooth during a discharge?" -> "# 04 Stability over time: does the estimate keep agreeing with the reference reconstruction and stay smooth during a discharge?". And c0 first sentence "Is the output stable from one instant to the next, or does it jump around? Where does the model fail?" -> add after it: "These results are for the baseline network and for clean inputs; the noisy-input counterpart is in notebook 08."

**04-2 (High, c20 bullet 5, 1-line).** Smoothing claim (N-04-02).
Now: "- **Smoothing in time does not help.** A causal trailing mean of the last 3 predictions raises the error to 2.0 times (`R_mag_axis`), 1.5 times (elongation) and 1.4 times (plasma current); with 20 rows it is 6.1, 7.5 and 6.6 times. The network output has no jitter to remove and the filter mostly adds lag."
Replace: "- **On clean inputs, smoothing the output in time does not help.** A causal trailing mean of the last 3 estimates raises the error to 2.0 times (`R_mag_axis`), 1.5 times (elongation) and 1.4 times (plasma current); with 20 rows it is 6.1, 7.5 and 6.6 times, because the network output has little jitter to remove and the filter adds lag. On the provided noisy inputs the picture changes: giving the network three consecutive rows as input lowers the radial axis error from 2.64 to 2.33 mm (notebook 08, section 5). This cell smooths the output; that is a different thing from time context in the input."

**04-3 (Medium, c5 and c20 bullet 2).** One factor for both ends hides that the growth is mainly at the end (N-04-03, claims-corrections 2).
In c5 replace the line `ends_vs_middle = {t: float(np.nanmean([dec[t][0], dec[t][9]]) / dec[t][2:8].mean()) for t in KEY_T}` by
`mid = {t: float(dec[t][3:7].mean()) for t in KEY_T}  # 30 to 70 % of the discharge` and
`first_over_middle = {t: float(dec[t][0] / mid[t]) for t in KEY_T}` and `last_over_middle = {t: float(dec[t][9] / mid[t]) for t in KEY_T}`; print both (the first is NaN for the X point and the strike point, which do not exist in the first tenth). With the stored c5 output I get last over middle: `R_mag_axis` 3.7, `Z_mag_axis` 2.9, elongation 2.4, plasma current 1.9; first over middle: `R_mag_axis` 2.5, `Z_mag_axis` 1.5, elongation 1.06, plasma current 0.99 (recompute after the change).
Now (c20 bullet 2): "- **The error is larger at the two ends of a discharge.** For `R_mag_axis` the MAE is 0.60 mm in the first tenth and 0.90 mm in the last tenth against 0.26 mm in the middle (tenths 3 to 8), a factor of 2.9; for elongation the factor is 1.5 and for the plasma current 1.3."
Replace: "- **The error grows mainly at the end of a discharge.** For `R_mag_axis` the MAE is 0.90 mm in the last tenth against 0.24 mm in the middle (30 to 70 % of the discharge), 3.7 times; for `Z_mag_axis` 2.9, elongation 2.4 and plasma current 1.9 times. At the start only the axis position is worse (`R_mag_axis` 0.60 mm, 2.5 times, `Z_mag_axis` 1.5 times); the X point and the strike points do not exist in the first tenth. We do not know the reason; the plasma current is small and changes fast there, so the reference reconstruction itself may be least reliable (hypothesis, not tested)."

**04-4 (Low, c20 bullet 4, 1-line).** N-04-04: "for `R_strike_point_1` 82 %" -> "81 %" (output 0.8145).

**04-5 (Medium, c7, a few lines).** The jitter table loops over `KEY_T` (7 targets), so the limiter points (0.69 and 0.48) and the other triangularities are never shown: `for t in KEY_T:` -> `for t in NUM:` in the jitter/offset loop and build `cmp_tab` with `saved_time["jitter_ratio"].get(t)` and `saved_time["bias_share"].get(t)` (check that `ipp1-time.json` holds all targets; PLAN IMPL-8 says it now writes all 16). Also the noisy-input rows: add a cell that prints `saved_time["noisy"]` jitter columns (the committed `results/ipp1-time.json` has them) or point to notebook 08.

**04-6 (Medium, new cell, G-4). Answer** (N-04-05). "**Answer.** On clean inputs the estimate differs from the reference reconstruction by about 0.4 mm on the axis position, varies as the reference values do (jitter ratio 0.97 to 1.07 for the 7 targets shown), is worse at the end of the discharge (`R_mag_axis` 3.7 times the middle) and within 3 rows of a switch between limited and divertor plasma (`is_limited` wrong in 15.9 % of those rows, 99.4 % of all its errors). On the provided noisy inputs the output of a network trained on clean data is not stable: it varies 8.4 times more than the reference values on the radial axis (notebook 08)."

**04-7 (Low, c20 bullet 7 and c13).** N-04-06: cut the per-discharge table by the sign of the plasma current (16 discharges, 78 % of the error): one extra `groupby`. Optional.

**04-8 (Low, c5 and c7).** N-04-07: `saved_time` is defined in c5 and used in c7: load it in c3.

**04-9 (Low, c11).** The figure draws predicted and reference traces of discharge 148 and a median discharge; RP-6 allows one real discharge in the talk; same decision as 01-12.

## 7. Notebook 05 Real-time latency

Opens with the question. **The stored run is not the run in `results/ipp1-latency.md`** (N-05-02, still true): the notebook reads `out/ipp1-latency.json`, a run that is not committed.

| Quantity (single CPU thread) | Notebook c3 output / c14 text | `results/ipp1-latency.md` |
|---|---|---|
| median | 0.0145 ms | 0.0145 ms |
| p99 | 0.0288 ms | 0.0209 ms |
| p99.9 | 0.0699 ms | 0.0812 ms |
| max | 0.0899 ms | 0.148 ms |
| numpy median | 0.0129 ms | 0.0125 ms |
| GPU single sample median | 0.2405 ms | 0.2681 ms |
| CPU batch 4096 median | 1.68 ms | 2.42 ms |

Worse, `results/ipp1-latency.md` says the committed run was on a shared, busy machine (load average 5.67, 14.52, 29.34 on 10 cores), so
**"saved quiet run" (c14, bullet 1) and "the saved run on a quieter machine" (c14, bullet 7) are not supported.**

**05-1 (High, c14 bullet 6, 1-line).** The verdict is unconditional and quotes false precision (claims-corrections 1, N-05-01, N-05-07).
Now: "- **Verdict.** The assignment asks for a reaction in units to tens of milliseconds. The typical forward pass (0.051 ms median here, one CPU thread) is about 195 times below 10 ms and about 4,137,933 times (saved run) or 1,167,883 times (this run) faster than a classical computation of one minute. Computing the shape is therefore not the bottleneck; a controller would be limited by sensor readout, data transport and the control algorithm."
Replace: "- **Verdict (conditional).** The assignment asks for a reaction in units to tens of milliseconds; we use a budget of 1 to 10 ms. The forward pass of the baseline network takes a median of 0.0145 ms on one thread of an idle Apple M5 CPU (`results/ipp1-latency.md`) and 0.03 to 0.07 ms on a loaded or different CPU (0.051 ms in this run), more than a million times faster than a classical reconstruction of one minute or more. On a system without real-time guarantees, rare slow calls reach milliseconds (this run: p99.9 7.9 ms, slowest 25.7 ms), so against the 1 ms budget the idle median is inside and the loaded tail is not. **Not verified:** acquisition and integration of the coil signals, the worst case on a real-time system, and accuracy on really noisy signals (a network trained on clean data fails on them: 10.2 mm on the radial axis on the provided noisy file; trained with noise it gives 2.6 mm, notebook 08)."
(Check: 60,000 ms / 0.0145 ms is 4.1 million and 60,000 / 0.0514 is 1.17 million, so "more than a million times" holds for both runs; "0.03 to 0.07 ms" is the wording of `docs/claims-corrections.md` and this run's median of 0.051 ms is inside it.)

**05-2 (High, c14 bullet 1, c3, cell).** Replace the typed numbers of the saved run. Now: "- **Speed of one prediction.** The 107,152-parameter network needs a median of 0.0145 ms on one CPU thread in the saved quiet run (99.9th percentile 0.070 ms, slowest 0.090 ms). In this notebook the machine was shared with many other jobs (load average 21.5 on 10 cores) and the same call gave a median of 0.0514 ms, a 99.9th percentile of 7.88 ms and a slowest call of 25.74 ms."
Replace with: "- **Speed of one estimate.** The 107,152-parameter baseline network needs a median of 0.0145 ms on one CPU thread of an Apple M5 in the saved run (99.9th percentile 0.081 ms, slowest of 5,000 calls 0.148 ms; the machine was shared, load average 5.7 / 14.5 / 29.3, so this is not a clean benchmark). In this notebook the machine was shared with many other jobs (load average 21.5 on 10 cores, a stress case) and the same call gave a median of 0.0514 ms, a 99.9th percentile of 7.88 ms and a slowest call of 25.74 ms."
Since a rerun of `ipp1_latency.py` changes the saved numbers, either commit the new md and json together and re-type the bullet, or (better, F-04) generate bullets 1 to 3 with `display(Markdown(f"...{lat['cpu_1_thread_single_sample']['median_ms']:.4f}..."))` from `lat` and `fresh`. Same for bullets 2 and 3 (numpy 0.0125 / 0.0259 ms, GPU 0.2681 / 0.3746 ms, batch 4096 GPU 0.70 against CPU 2.42 ms in the committed file, not 0.68 and 1.68).

**05-3 (High, c14 bullet 7, 1-line).** Now: "... so the average is far inside the budget but a worst case inside it is not guaranteed; the saved run on a quieter machine had a slowest call of 0.09 ms." Replace: "... so the typical call is far inside the budget but a worst case inside it is not guaranteed; the saved run, also on a shared machine, had a slowest call of 0.148 ms. We do not claim a worst-case bound." Also delete "and, less strongly, the medians" duplication if lane K likes; not required.

**05-4 (Medium, c0, 1-line).** (N-05-03, F-02) Now: "How long does one prediction of the trained architecture take, how large are the rare slow outliers, ..." Replace: "How long does one estimate of the baseline network (24 inputs, 107,152 parameters) take, how large are the rare slow outliers, ...". Add after the Scope paragraph: "The shipped model (46 inputs, a ridge for the plasma current, a gated limiter network) is timed in notebook 09 (section 8), the 72-input time-context network was not timed."

**05-5 (Medium, c11 text, 1-line).** (N-05-04) After the headroom table add: "Against 1 ms, the loaded-machine p99.9 of 7.9 ms is not inside the budget; the idle median is. Against 10 ms the p99.9 is inside by a factor 1.3."

**05-6 (Low, c3, 1-line).** (N-05-06) Add `print(lat.get("cpu"), torch.__version__)` after the load average print so a reader sees the processor.

**05-7 (Low, c14 bullet 4).** The `predict()` call: median 0.0355 ms is quoted as the realistic call; README and `results/ipp1-latency.md` have `cpu_end_to_end_numpy` 0.0140 ms and the README quotes 0.053 ms (F-08, open). Say "median 0.0355 ms in this run" only and do not cross-reference 0.053.

**05-8 (Medium, new cell, G-4). Answer.** "**Answer.** The computation of the 107,152-parameter baseline network takes a median of 0.0145 ms on one core of an idle Apple M5 (0.03 to 0.07 ms on a loaded machine or another CPU), inside the 1 to 10 ms budget; on a machine without real-time guarantees rare calls take milliseconds. This says nothing about acquiring and integrating the coil signals, the worst case on a real-time system or accuracy on really noisy signals."

## 8. Notebook 07 Distribution and unusual shapes

Opens with the question, ends with an `## Answer`. Data free. Numbers are generated from the files; the one explicit number check: the c5 and c17 outputs agree with `results/ipp1-distribution.md` (the notebook asserts it).

**07-1 (Medium, c8, 1-line).** "reversed polarity" without a sign convention (physics M2).
Now: "16 of the 149 discharges have the opposite sign of the plasma current from all the others (`positive current` below; the usual sign is negative)."
Replace: "16 of the 149 discharges have a positive plasma current in the file, all others a negative one (`positive current` below; 92.6 % of the rows are negative). The sign convention and its relation to the toroidal field are not recorded in this repository, so we do not know whether these are discharges of opposite machine polarity; 'reversed' below only means 'positive sign'."

**07-2 (Low, display strings, multi).** "true" for the reference values: see G-1 (c7, c12, c13).

**07-3 (Medium, c31, 1-line).** Chronological ids are not confirmed. Now: "the random split is itself optimistic (discharge numbers follow time)". Replace: "the random split is itself optimistic (the discharge numbers appear to follow time; not confirmed with the organizers)". Also in c31 first paragraph: "the mean error is" -> "the mean absolute difference from the reference reconstruction is".

**07-4 (Low, c27, 1-line).** The hard-coded figure title is unconditional: `ax.set_title("A family never seen costs 1.0 to 3.0 times the error, no collapse")`. Replace: `ax.set_title("Leaving a family out costs 1.0 to 3.0 times the error in these 6 tests")`. (The words "no collapse" are also in `results/ipp1-unusual-shapes.md`; with 18 truly unusual discharges and no single one held out they are not a general claim.)

**07-5 (Low, c26, 1-line).** Elongation below 1 (physics M8). Append to the c26 text: "The 18 unusual discharges are those with a low median elongation; elongation values below 1 are unusual for a tokamak plasma and the organizers' formula is not recorded here, so we do not interpret them physically (to be checked with the institute)."

**07-6 (Low, c7 plot, 1-line).** `axes[1].set_ylabel("limited rows [%]")` for two bars (share of the rows, share of the squared error) -> `axes[1].set_ylabel("share of all rows or of the squared error [%]")`. Title "44 % of the rows, most of the error" is hard-coded: fine, it is checked by the c15 assertion.

**07-7 (Low, c24, 1-line).** Remove the internal reference "(docs/review-findings-2.md, H2)": a reader of the notebook has no use for it; say "(see section 4.1, development against kept-aside nRMSE below)".

**07-8 (Low, c1 `numeric`).** Empty unit cells: G-5(d).

**07-9 (Low, c0).** The two protocols table is good; add the word "reference reconstruction" once: "Errors are mean absolute errors (MAE) in the unit of the target" -> "Errors are mean absolute differences (MAE) from the reference reconstruction in the unit of the target".

## 9. Notebook 08 Robustness and amount of data

Opens with the question, ends with `## Answer` (the first sentence is the answer). Data free. Reading checked: noise 0.158/0.09, range 0.086 to 0.167, lag-1 -0.004, 10.2 against 0.38 mm (27 times), 2.64/2.22, drift +1.1 and +4.7 mm, learning curve 1.47/0.83/0.38, 3 rows 2.64 to 2.33 mm: all agree with `results/ipp1-robustness-findings.md` and `ipp1-final.md`.

**08-1 (Medium, c3 reading, 1-line).** "fair stand-in" for the noise (physics H5.1).
Now: "Synthetic noise of level 0.15 gives the same errors as the provided file (radial axis {syn} mm against {prov} mm), so it is a fair stand-in. "
Replace: "Synthetic noise of level 0.15 gives the same errors as the provided file (radial axis {syn} mm against {prov} mm), so it stands in for the provided file. It says nothing about the noise of real probes: the provided noise looks like noise added in proportion to each input's standard deviation (the ratio stays between 0.086 and 0.167; our inference, not confirmed) and may be larger than real probe noise (to be checked with the institute), so these errors are a stress test, not an expected operating accuracy. "

**08-2 (Medium, c4, 1-line).** What the drift is and is not (physics H5.3, H5.4). Append to the c4 text: "Every discharge reaches the same total drift at its end whatever its length; a real integrator offset grows with absolute time. Calibration errors, a failed or saturated probe, pickup from the coil currents and thermal drift were not tested."

**08-3 (Low, c0, 1-line).** Meta wording in a deliverable. Now: "**Wording fixed by the review:** everything here is for the *baseline network*; the noise is white noise provided by the organizers (the drift is our own synthetic model); stability statements are conditional on the kind of input." Replace "**Wording fixed by the review:**" by "**Scope:**".

**08-4 (Medium, c13, 1-line).** Now: "(the numbers follow time)" -> "(the numbers appear to follow time; not confirmed with the organizers)".

**08-5 (Low, c17, 1-line).** Now: "was measured on clean-trained architecture only." Replace: "was measured for the baseline network only (24 inputs; the weights do not change the timing)."

**08-6 (Low, c18, 1-line).** Add the loaded and other-CPU numbers so the cell matches the conditional wording of claims-corrections 1: after "The budget is 1 to 10 ms." insert "On a loaded machine or another CPU the median is 0.03 to 0.07 ms (notebook 05)."

**08-7 (Low, c5, optional, 1 line before `show`).** The row labels "clean, noise 0.15 + drift 0.30" and "provided noisy, noise 0.15 + drift 0.30" can be misread as drift in the provided file. Print a renamed copy: `show(nd.rename(index=lambda s: s.replace("noise 0.", "synthetic noise 0.").replace("drift 0.", "synthetic drift 0.")), P_R)` (keep `nd` unchanged: c6 and c20 look up the original labels).

**08-8 (Low, c20).** Answer: add "(the baseline network; all of this is for noise we or the organizers added, not for real probe failures)". The last paragraph already says baseline network and conditional real-time; good.

**08-9 (Low, c9).** The sentence "stays near 1 whenever the output is smooth because its input is smooth, so it is a statement about clean inputs and **not** a noise measure" is right; keep.

## 10. Notebook 09 The shipped model on the 30 set-aside discharges

Opens with the question. Ends with conclusions (no one-sentence answer, 09-12). Numbers checked against the outputs and `results/ipp1-final.md`, `ipp1-final-seeds.md`, `ipp1-latency-shipped.md`: 0.133 (0.099 to 0.177), 0.307, 35 %, 42 % and 36 %, 0.397/0.216, 0.230/0.479, seed gains 40 to 60 % and 21 %, noisy 190 mm and 2.38 mm, 0.0154/0.0274 ms: agree; one mismatch (09-9).

**09-1 (High, c0 title, 1-line).** "nobody trained on" is the design claim the notebook itself refutes in its last section ("Nobody saw them is too strong").
Now: "# 09 The shipped model on discharges nobody trained on: final evaluation"
Replace: "# 09 The shipped model on 30 discharges set aside before the final choice: final evaluation"

**09-2 (High, c0 question, 1-line).** Now: "**Question.** How accurate is the shipped model on whole discharges that none of its networks was trained on, per parameter, in mm and kA, and how far can that number be trusted?" Replace: "**Question.** How closely does the shipped model reproduce the institute's reference reconstruction on 30 whole discharges that none of its final networks was trained on, per parameter, in mm and kA, and how far can that number be trusted?"

**09-3 (Medium, c0, 1-line).** "scored once" is not literally true: `results/ipp1-final.md` says the report step was run three times (a one-epoch plumbing test, the full run, and a fix of the polarity grouping). Now: "Every model here is trained on the other 119 discharges (the development set) and scored once on the 30, pooled over their rows." Replace: "Every model here is trained on the other 119 discharges (the development set) and scored on the 30, pooled over their rows; the report step ran three times (a one-epoch plumbing test, the full run and a fix of the polarity grouping) and no recipe was changed after the first full run." Make the same change in the `proto(...)` string in c5 ("scored once on the 30 locked discharges") and the same words in `07` (c0 table, c20 text, c25 `P2` string) and in `08` (c0 table, c8 `P_L` string): "scored once" -> "scored" or "scored once per final model".

**09-4 (Low, c0, 1-line).** "The reference is the plain baseline network of notebook 02." collides with "reference reconstruction": replace "The reference is" by "The comparison model is".

**09-5 (Medium, multi, display strings).** "locked" as a design word. Replace by "set aside" or "kept aside" in strings that a reader sees (not in variable or file names): c3 `index=["development (training)", "locked test"]` -> `"set aside (30)"`; c3 and c5 `proto(...)` text "locked"; c9 proto "on the 30 locked discharges" -> "on the 30 set-aside discharges"; c10 heading "## 3. Is the locked set easier than the rest? ..." -> "## 3. Are the 30 set-aside discharges easier than the rest? ..."; c11 column names `f"{r}_locked"` and `f"{r}_locked/dev"` and the printed word "locked" (`locked {n16[r]['locked']:.4f}`) -> "set_aside"; c12 "Quote the cross-validation next to the locked number" -> "next to the set-aside number"; c15 legend "locked 30 discharges" -> "30 set aside"; c17 and c19 proto strings; c24 bullets "the locked 30 scored once" -> "the 30 scored", "locked numbers" (b3) -> "numbers on the 30". The file name `09_final_model_locked_test.ipynb`, the id file `results/ipp1-locked-test-ids.txt` and the cache names `locked_*.npz` are referenced by the README, the deck, `make_all.py` and `ipp1_final.py`; do not rename them this late (the first heading and the question already state what the set is).

**09-6 (Medium, c12 and c15 and c24 bullet 4, 1-line each).** Chronological ids are an assumption.
c12 Now: "Discharge numbers are chronological, so random folds always leave neighbouring discharges of the same campaign in the training set." Replace: "Discharge numbers appear to be chronological (not confirmed with the organizers), so random folds probably leave neighbouring discharges of the same campaign in the training set."
c12 heading: "## 4. Discharges from later campaigns: the blocked split" -> "## 4. Higher-numbered discharges: the blocked split".
c15 legend: "blocked: later 59 discharges" -> "blocked: 59 highest numbers".
c24 bullet 4: "- **Later campaigns are harder.** Trained on the lower half ..." -> "- **Higher-numbered discharges are harder.** Trained on the lower half ..." and "this is an upper bound on drift between campaigns" stays (it is already conditional).

**09-7 (Medium, c24 last bullet, 1-line).** Number mismatch with `results/ipp1-unusual-shapes.md` and notebook 07. Now: "(see `results/ipp1-unusual-shapes.md`: 1.2 to 2.4 times larger error when a whole family of shapes is left out)". Replace: "(see `results/ipp1-unusual-shapes.md`: 1.0 to 3.0 times larger error when a whole family of shapes is left out, typically 1.2 to 2.4)".

**09-8 (Medium, c24 bullet 8, 1-line).** The latency bullet needs the conditional wording (claims-corrections 1). Now it ends "Collecting and integrating the coil signals is not included." Replace by: "Collecting and integrating the coil signals is not included. The timing used random weights of the trained shapes and a numpy path that was not compared with the outputs of the trained models. We did not verify the worst case on a real-time system, and the shipped candidate fails on noisy inputs (section 7), so these times are for clean inputs only; the budget we compare with is 1 to 10 ms."

**09-9 (Low, c18 and c24 bullet 5, 1-line).** "Seed noise is 3 to 13 % of the value" (five-seed check on the 30) against "(seed noise of earlier runs: 8 to 19 %)" in `results/ipp1-final.md`. Both are right for their test; add "(earlier runs on other tests showed 8 to 19 %)" so a reader does not think they contradict.

**09-13 (Medium, c24 bullet 2, 1-line).** The limiter point is quoted by its mean only (physics M5, review-findings-3 section 6). Append to the bullet: "The limiter point has a heavy tail: the median error is 0.73 mm (`R_limiter`) and 2.96 mm (`Z_limiter`), but 99 % of the rows are below 77 mm and 92 mm (c5 table); it is a wall contact, not a smooth shape feature, and the distance of the plasma from the wall, which control needs, was not measured."

**09-10 (Low, c24 bullet 2, 1-line).** Now: "A headline of about 0.2 mm on the radial axis is more honest than 0.13 mm." Replace: "A headline of about 0.2 mm on the radial axis (agreement with the reference reconstruction, cross-validation 0.23 mm) is more representative than 0.13 mm."

**09-11 (Low, c4, 1-line).** "reversed (positive) plasma current": add "(positive sign; the sign convention is not recorded)".

**09-12 (Medium, new cell, G-4). Answer.** "**Answer.** On 30 discharges set aside before the final choice, the shipped model differs from the institute's reference reconstruction by a mean of 0.133 mm on the radial axis position (95 % interval 0.099 to 0.177 mm; 0.23 mm in cross-validation on the other 119 discharges, 0.40 mm when it trains on the lower-numbered half and is tested on the upper half), 0.035 kA on the plasma current and 4.5 mm on the limiter point, about 2.3 times closer than the baseline network on the axis (ratio 0.43). These 30 discharges are easier than the average, the ideas behind the recipe were tried on all 149 discharges, and on the provided noisy inputs the shipped model fails (190 mm), where the noise-trained baseline gives 2.4 mm."

## 11. Status of the items of `docs/notebook-review.md` on current main

All items for `01` to `05` are still open; the Critical item F-01 (missing notebooks) is done for `07`, `08`, `09` and waits for gate G1 for `06`.

| Item | Status on current main |
|---|---|
| F-01 | done for 07, 08, 09; 06 not yet |
| F-02 | open (02, 04, 05 do not say they are for the baseline network): 02-1, 04-1, 05-4 |
| F-03 | (a) kernel and (c) `out/` files handled by README and `make_all.py`; (b) `requirements.txt` not checked here; (d) bare `StopIteration` open: G-2 |
| F-04, F-05, F-07 | open: G-3, G-7, G-4 |
| F-06 | decided for the talk by RP-6; not for the submission files: 01-12, 04-9 |
| F-08 | open (results files: 0.094 against 0.115, README 0.053 ms against 0.0140 ms) |
| N-01-01 to N-01-05 | open: 01-1, 01-2, 01-4, 01-8, 01-6 |
| N-02-01 to N-02-07 | open: 02-3, 02-9, 02-6, 02-7, 02-5; N-02-07 (thread count in the runtime line): G-7 |
| N-03-01 to N-03-06 | open: 03-2, 03-9, 03-6, 03-8, 03-10, scipy in Section 2 |
| N-04-01 to N-04-07 | open: 04-1, 04-2, 04-3, 04-4, 04-6, 04-7, 04-8 |
| N-05-01 to N-05-08 | open: 05-1, 05-2, 05-4, 05-5, 05-6, 05-7; N-05-05 (stress case label): 05-2 |

## 12. Inconsistencies in other documents found on the way (not notebook edits)

1. `docs/notebook-review.md` N-02-02 contradicts itself: it asks for "on contiguous blocks the radial axis error is about 1.5 times larger, about 0.6 mm" and cites "blocked 1.23 against 0.448 mm", which is 2.7 times. The 0.6 mm figure is a reviewer's own block-wise 5-fold run (in `docs/claims-corrections.md` 8; its log is in a scratchpad, not in the repository). The committed measurement is `results/ipp1-final.md` (train on the 60 lowest, 1.23 against 0.448 mm, with a smaller training set). Quote only the committed one (02-3 does).
2. `docs/claims-corrections.md` 1 says the 0.090 ms maximum was measured "na nezatíženém počítači" (idle). `results/ipp1-latency.md` now says its run was on a busy machine (load 5.67, 14.52, 29.34) with a maximum of 0.148 ms; the 0.090 ms is from an older run that is not committed. Deck and outline owners: say "největší hodnota z 5 000 měření byla 0,148 milisekundy na vytíženém počítači" or drop the maximum.
3. `docs/claims-corrections.md` 5 says the five-component network is "asi 7krát" worse (2.6 against 0.38 mm); `results/ipp1-data-checks.md` has 2.631 against 0.4065 mm, 6.47 times (same seed and folds). Use 6.5 times or "2,63 proti 0,41 milimetru".
4. `results/ipp1-data-checks.md` quotes the correlation of the noise with time as 0.049; notebook 01 prints 0.050 (0.0497 in `docs/claims-corrections.md`). Use 0.050 in both.
5. `results/ipp1-robustness-findings.md` says the synthetic noise "is a fair stand in"; the physics review (H5) and 08-1 qualify this. Lane L may adjust the sentence together with the notebook.
6. `results/ipp1-final.md` is titled "final evaluation on a locked test set" and uses "locked" throughout; `results/ipp1-signcanon.md` has a "Locked test set" heading that `07` c22 parses by name (`table(F_SC, "Locked test set", ...)`). Do not rename without changing that parser line in `07`.
7. `README.md` still says "five notebooks" (lines 85, 114, 120, 132 and the make_all timing "2 min"); there are now eight files (`01` to `05`, `07` to `09`), and `make_all.py --notebooks` executes all of them.
8. `results/ipp1-distribution.md` (column header "range of the true value") and the other results files use "true" for the reference values; the notebooks only parse that header (G-1, c13).

## 13. Which edits are one-line, and the rest

**One-line (a sentence or a string in one cell):** G-1 (all rows), G-2, G-5(a to c, e), 01-1, 01-2, 01-3, 01-4, 01-5, 01-6, 01-7, 01-8, 01-9, 02-1, 02-2, 02-3, 02-4, 02-5, 02-6, 02-8, 02-9, 02-10, 02-11,
03-1, 03-2, 03-3, 03-4, 03-5, 03-6, 03-7, 03-8, 04-1, 04-2, 04-4, 05-1, 05-3, 05-4, 05-5, 05-6, 05-7, 07-1, 07-3, 07-4, 07-5, 07-6, 07-7, 07-9, 08-1, 08-2, 08-3, 08-4, 08-5, 08-6, 08-8, 09-1, 09-2, 09-3, 09-4, 09-6,
09-7, 09-8, 09-9, 09-10, 09-11, 09-13.
**A few lines or one cell:** 01-10, 02-7 (one bullet, three sentences), 04-3 (code and one bullet), 04-5, 05-2 (generate the bullets from `lat`), 08-7, 09-5 (display strings, 8 cells).
**New cells:** G-4 (one Answer cell in each of `01` to `05` and `09`), 03-9 (controls and Spearman values).
**Delete:** the `KEY_JSON` cells (G-3).
**Optional:** 01-11, 01-12, 04-7, 04-8, 04-9, 03-10, 02-3 code line, the kernel name of `07`/`08`.
