# Notebook review (static, Fri 23 Oct 2026)

**Scope.** `notebooks/01` to `05`, read cell by cell with the stored outputs, against `README.md`, `docs/REQUIREMENTS.md`,
`docs/WORKERS.md`, `docs/claims-corrections.md`, `results/*.md|json`. Nothing was run: no IPP data exist in this mirror.
The notebooks were not edited; the colleague (lane K) owns them. "Cell n" is the 0-based index of the cell in the
`.ipynb` (markdown cells count), not the `In [ ]` number.
Severity: **Critical** = a required deliverable is missing, **High** = a wrong or unconditional claim, or a clean run fails,
**Medium** = a number or caveat is missing or stale, **Low** = polish.

## 0. Verdict in five lines

1. The five notebooks are clean in form: question first, conclusions last, units in tables and axes, no error outputs, no
   leftover debug cells, no absolute paths (`grep` for `/Users`, `/home`, `bladed`: 0 hits), no raw rows printed.
2. **Critical: every bonus item has no notebook** (noise and drift, amount of data, time context, camera, unusual shapes, the
   shipped model). REQ-005 asks for "all detailed conclusions" in notebooks.
3. **High: three conclusions are unconditional where the claim corrections say conditional** (stability, "smoothing does not help",
   "coils carry almost all the information") and the real-time verdict omits the not-verified list.
4. **High: a clean run cannot work today** (kernel `hackathon` unregistered, no dependency file, `out/` files not in git, no `make_all`).
5. **High: notebook 05 quotes a latency run that differs from `results/ipp1-latency.md`** (only the median agrees).

## 1. Coverage of the assignment

| Required question | Where answered | Status |
|---|---|---|
| Accuracy per parameter | 02 (cells 7, 19) | Answered, but for the **baseline MLP**, not the shipped model (see N-02 and F-02); no tails (F-05) |
| Stability over time | 04 (cells 5, 7, 20) | Answered for clean inputs only and worded unconditionally (N-04-01) |
| Real-time feasibility (ms) | 05 (cell 14) | Measured, verdict not conditional enough, baseline architecture only (N-05-01 to 03) |
| Effect of fewer inputs | 03 (cells 3 to 17) | Answered; retraining rankings and controls missing (N-03-02) |
| Split by whole discharges | 01 section 8, 02 section 1 | Answered with a proof by experiment (1-NN 0.62 against 2.03 mm); blocked split caveat missing (N-02-02) |
| Uneven distribution (REQ-007) | 02 section 6 | Measured only; no per-configuration, polarity or end-of-discharge share (N-02-04) |
| Bonus: noise and drift | none (01 section 7 only measures the noisy file) | **Missing** (F-01) |
| Bonus: amount of training data | none | **Missing** (F-01) |
| Bonus: time context | none (04 section 8 smooths the output, it is not input context) | **Missing** (F-01) |
| Bonus: camera, B/W, position | none | **Missing** (F-01) |
| Bonus: unusual shapes | none | **Missing** (F-01) |

## 2. Findings that apply to the whole set

| ID | Sev | Notebook, cell | Problem | Exact fix |
|---|---|---|---|---|
| F-01 | Critical | none | No notebook holds the results of `results/ipp1-robustness-findings.md` (noise 0.38 to 10.2 mm, trained with noise 2.6 mm, drift +1 and +4.7 mm, learning curve 6 to 119 discharges, 3-row context), `ipp1-unusual-shapes.md` (1.0 to 3.0 times), `ipp1-final.md` (shipped model), `ipp1-distribution.md`, `ipp1-uncertainty.md`, `cloud-camera-*.md`. PLAN line 44 plans notebooks 06 to 08 but they do not exist | Write `06_robustness_and_data.ipynb` (noise, drift, learning curve, time context), `07_final_model_and_limits.ipynb` (shipped recipe, locked set, blocked folds, distribution, unusual shapes, uncertainty), `08_camera.ipynb`. Make them **data free**: read the committed `results/*.json|md` and show the committed `results/*.png`, so they run on a clean checkout. Each opens with the question and ends with one answer sentence taken from `docs/claims-corrections.md`. Add the table of section 1 above to the README |
| F-02 | High | 02, 04, 05 (cell 0 each) | They evaluate the baseline MLP 256-256-128 on 24 inputs. The shipped clean model is the "candidate" (46 inputs, ridge for the current, gated limiter network; `results/ipp1-final.md`: R axis 0.133 against 0.307 mm, current 0.035 against 1.20 kA on the locked set). A reader of 02 and 05 will take 0.38 mm and 0.0145 ms as the final model's | Add to cell 0 of 02, 04, 05: "These results are for the baseline network. The model we ship is evaluated in notebook 07." In 05 say that the candidate (46 inputs, extra networks) was **not timed** (consistent with commit 2b9fea6) |
| F-03 | High | all, cell 1 | Clean run fails or is unverified: (a) kernelspec `hackathon` exists only on the owner's Mac, so `nbclient`/`jupyter nbconvert --execute` raises `NoSuchKernel` elsewhere; (b) no `requirements.txt`; `scipy` (03, 04) is imported but not in the README install line, nor `ipykernel`/`nbclient`; (c) `out/ipp1-inputs.json` (03), `out/ipp1-predictions.csv` and `out/ipp1-time.json` (04), `out/ipp1-latency.json` (05) are not in git and `analysis/make_all` does not exist (PLAN lines 27 and 45); (d) `next(p for p ...)` raises a bare `StopIteration` when Jupyter is started outside the repo (Colab) | (a) run `python -m ipykernel install --user --name hackathon` in the README, or set the kernel to `python3` in the notebook metadata; (b) add `requirements.txt` with `numpy pandas scipy scikit-learn matplotlib torch ipykernel nbclient` and one line in the README; (c) in cell 1 add `def saved(name): for d in (C.OUT, repo/"results"): if (d/name).exists(): return d/name; raise SystemExit(f"{name} missing: run analysis/<script>.py")` and use it for the four json files (all four are committed in `results/`); for the predictions csv, which derives from the data and must stay out of git, write `analysis/make_all.sh` with `ipp1_oof.py` (about 3 min, 5 folds x 60 epochs, notebook 02 measured 172 s) and name it in the SystemExit text; (d) `next(..., None)` and `raise SystemExit("Run from inside the repository")` |
| F-04 | Medium | all, last two cells | Conclusions are typed text, not generated; the cell title "Key numbers (read by the conclusions below)" is therefore untrue, and `print("KEY_JSON", ...)` dumps a block of numbers into the output. WORKERS.md asked for conclusions generated from the outputs. A rerun on another machine (05 above all, but also 02 "172 s on a busy machine", "ratio 1.0000") makes text and output disagree | Either build the conclusion cell with f-strings from `KEY` and `display(Markdown(...))`, or delete the `KEY_JSON` cells, rename the heading and add under the conclusions: "Numbers in this text are from the stored run of 23 Oct 2026; a rerun differs slightly." Keep the second option for 01 to 04 (lean) and do the first for 05 |
| F-05 | Medium | 01 to 05, cell 0 | No runtime note. Stored `execution_seconds`: 01 27 s, 02 186 s, 03 42 s, 04 11 s, 05 35 s on the owner's Mac. Not counted: the offline `ipp1_inputs.py` run behind 03 (network retrained for every subset on 5 folds, plus controls), whose duration is not recorded anywhere | Add one line under the question of each notebook: "Runtime: about N min on 2 CPU threads; needs `out/...` (made by `analysis/...`)" |
| F-06 | Medium | 01 cell 14, 04 cell 11 | Figures draw real traces of single discharges (the median discharge with raw `IPR05`; true against predicted of discharge 148 and a median one) and the text names discharge ids 148, 127, 7. No raw row is printed, but SUBMISSION OQ-S2 and RP-6 leave open whether figures made from the data may leave the team | Owner decides. If strict: keep only normalised or binned versions (e.g. plot `R_mag_axis - mean`, hide ids, drop the raw `IPR05` panel). Whatever is chosen, state it in `docs/SUBMISSION.md` |
| F-07 | Low | all | The ending is a list of findings, not a one-sentence answer to the question in the opening cell | Start every "Conclusions" cell with `**Answer.**` and one sentence, e.g. 03: "The 16 IPR coils alone give 0.066 against 0.063 for all 24 inputs, the 8 flux loops alone 0.285; no single input is individually necessary." |
| F-08 | Low | results, not notebooks | `results/ipp1-inputs.md` gives "top 8" 0.094 and `ipp1-inputs-controls.md` gives "permutation top 8" 0.115 (the other rows agree); `README` says end to end numpy 0.053 ms and `ipp1-latency.md` says `cpu_end_to_end_numpy` 0.0140 ms | Lane L: explain or re-run once, then make notebooks 03 and 05 quote the same value |

## 3. Notebook 01 Data exploration

Numbers checked against its own outputs and `results/ipp1-data*.md`, `ipp1-claim-support.md`: rows 42,972, 149 discharges, 56 %,
99.92 % at 5 components, noise 0.086 to 0.167, correlation with time 0.050, 1-NN 0.62 against 2.03 mm (factor 3.3): all agree.

| ID | Sev | Cell | Problem | Exact fix |
|---|---|---|---|---|
| N-01-01 | Medium | 21 (bullet "The inputs are redundant") | "This is why fewer inputs can work" with no variance-not-information caveat (claims-corrections 5). Five components keep 99.9 % of the variance but a network on them has 2.6 mm axis error against 0.38 | Replace the last sentence with: "This is redundancy in variance, not in information: a network on the first 5 principal components has a radial axis error of about 2.6 mm against 0.38 mm (`results/ipp1-claim-support.md`); notebook 03 tests fewer sensors directly." |
| N-01-02 | Medium | 16, 21 (bullet "The noisy file") | Concludes "no drift component" from a correlation with time only, and never says the noise is white. The review's statement is "white noise, lag-1 autocorrelation about -0.005, every drift result synthetic" | In cell 16 add the mean lag-1 autocorrelation of `noise` inside each discharge (same loop as `mean_abs_corr_with_time`) and print it; in cell 21 write: "The provided noisy file is white noise (lag-1 autocorrelation X) with no measurable drift. All drift results in notebook 06 use drift we generated." |
| N-01-03 | Low | 21 | The spread table (cell 7) shows 2.4 to 13.7 mm for axis, X-point, strike points but 90 and 153 mm for the limiter point and 114 kA for the current; the conclusions do not say so (claims-corrections 7) | Add to the "Size" or "Shapes" bullet: "The spread is small only for the axis, X-point and strike points (2.4 to 13.7 mm); the limiter point has 90 and 153 mm and the current 114 kA, so errors are given in physical units and relative to the spread." |
| N-01-04 | Low | 5 | Inputs have no unit (coil and flux loop signals in the file's own units, not stated by the organizers) | Add to the cell 4 text: "Input units are those of the file (not specified by the organizers); inputs are standardised before any model." |
| N-01-05 | Low | 17 | Section 8 argues the group split but not that random group folds are still optimistic for a later campaign | One sentence pointing to N-02-02 |

## 4. Notebook 02 Baseline models

Checked: the results table equals `results/ipp1-baseline.md` row by row (0.377, 0.391, 1.49, 0.0346 kA, 99.26 %, 163 rows, 3.3).
Stored KEY: nRMSE 0.4629 and 0.0633, ratio 7.31: agree with the text.

| ID | Sev | Cell | Problem | Exact fix |
|---|---|---|---|---|
| N-02-01 | Medium | 19 (bullet 2), 14 | The headline is the mean only. "Typical errors are 1.3 % to 4.7 % of the spread" uses MAE over spread; the nRMSE of the same outputs is 3 to 14 % (R axis 0.139) because the tails are heavy; the two are different measures and the text does not say which is which. The review: axis median 0.153 mm, p95 1.21, p99 3.74, worst 64 mm | In cell 14 print `np.median`, p95, p99 and max of the radial axis error from the pooled `P_mlp` (one line per target for the five headline targets); in cell 19 write "mean 0.38 mm, median 0.15 mm, 99 % of rows under 3.7 mm, worst rows tens of millimetres, mostly at the end of a discharge", and say "MAE / spread" not "typical error of the spread" |
| N-02-02 | Medium | 0, 19 (bullet 1) | "whole discharges the model has never seen" is true but implies a new campaign. Discharge ids are chronological; on contiguous blocks the axis error is about 1.5 times larger (about 0.6 mm; `ipp1-final.md`, blocked 1.23 against 0.448 mm on the same 59 discharges) | Change to "on randomly chosen new discharges" and add the sentence of claims-corrections 8: "The discharge numbers appear to follow time; on contiguous blocks the radial axis error is about 1.5 times larger, about 0.6 mm instead of 0.38 mm." |
| N-02-03 | Low | 19 (bullet 6) | "elongation 0.0081 and 0.0037": the stored value is 0.00815, the printed table shows 0.0082 | Write 0.0082 |
| N-02-04 | Medium | 15 to 19 (REQ-007) | Section 6 measures error by elongation bin only. Missing, all from `results/ipp1-distribution.md`: limited rows are 44 % of the rows and 92 % of the squared R-axis error; the 16 discharges with the opposite current sign are 7 % of the rows and 78 % of the error; the last 2 % of a discharge is 2 % of the rows and 27 % of the error. Also no statement of what was done about it | Add a cell that prints these three shares (limited, reversed polarity, last 2 %) from `P_mlp`, and a bullet: "REQ-007: measured, not corrected; no reweighting or stratified folds were tried" (or what lane L did) |
| N-02-05 | Low | 19 (bullet 5) | "Wrong class is not the main cause" is shown for R only (10.8 right, 14.5 wrong); for Z_limiter the wrong-class MAE is lower (18.0 against 22.3 mm) | Say "for `R_limiter`; for `Z_limiter` the wrong class is not worse (18.0 against 22.3 mm)" |
| N-02-06 | Low | 19 (bullet 1), 9 | "so the training is reproducible" rests on a comparison with a file that a clean checkout does not have (cell 9 then prints "comparison skipped"); bit identity also depends on the CPU and thread count | "...equal on the owner's Mac with the same thread count; on another CPU expect small differences." |
| N-02-07 | Low | 1 | `torch.set_num_threads(2)` is hidden in the setup; training time in the conclusion is for 2 threads "on a busy machine" | Keep, but state the thread count in the runtime line (F-05) |

## 5. Notebook 03 Inputs and importance

Checked: all table values equal `results/ipp1-inputs.md` (0.0633, 0.0657, 0.2852, 4.51, 1.05, 1.23, 1.49, 2.26, 3.2); 7.3 times
(0.463 / 0.0633); per-target values 0.38 to 0.90 and 0.20 to 0.46 mm. Ranking taken inside each fold on training rows, so
there is no leak into the top-k curve.

| ID | Sev | Cell | Problem | Exact fix |
|---|---|---|---|---|
| N-03-01 | High | 17 (bullet 1), 0, 7 | "The coils carry almost all the information" breaks the wording rule (claims-corrections 4: ranking is importance for the trained network, never information content, never "the important sensors"). The opening question "which measurements matter most" and the bar chart "Permutation importance" invite the same reading | Cell 17 bullet 1: "The 16 IPR coils alone give a summary error of 0.0657 against 0.0633 for all 24 inputs, the 8 flux loops alone 0.2852 (4.3 to 4.5 times worse)." Cell 0: replace "which ... matter most" by "how few inputs are enough, and which ones the trained network relies on". Cell 7 title: "Permutation importance for the trained network (not information content)" |
| N-03-02 | High | none (after cell 14) | The current evidence for REQ-004 is missing: `results/ipp1-inputs-ranking.md` (no single input is individually necessary; seed noise 4.5 %; only FL01 +7.6 % worse in 5/5 folds; IPR13 eliminated last in 5/5 ridge folds; the three rankings agree with Spearman -0.14 to +0.40) and `results/ipp1-inputs-controls.json` (random 12 inputs 0.099, permutation top 12 0.077, QR-pivot 12 0.065; QR-pivot 8 0.072 against permutation top 8 0.115). The notebook's "smallest subset within 1.25 times has 12 inputs" is a property of the permutation procedure; a model-free subset of 8 stays within 1.14 times | Add a section "6. Controls and retraining rankings" that reads the two committed files and prints the control table and the three Spearman values; add a bullet: "Which subset of 8 or 12 inputs is chosen matters more than the permutation rank: a QR-pivot subset of 8 (0.072) beats the permutation top 8. The only single-input statement we defend is that IPR13 survives backward elimination in all 5 folds." |
| N-03-03 | Medium | 17 (bullet 2, caveat) | "1.05 times" (top 16) and "1.04 times" (IPR only) are read as differences, but the measured seed noise is 4.5 % (this repo) to 8 to 19 % (review); controls file: "differences under 10 to 15 % are noise". The caveat names only the single seed | Add to the caveat: "Seed noise of the same network is 4.5 % in `ipp1-inputs-ranking.md`; differences below about 10 % (top 16, IPR only against all 24) are not resolved." |
| N-03-04 | Medium | 17 (bullet 5) | "Ridge on 5 principal components gives 0.517" omits that the projection needs all 24 sensors and that the network on 5 components is about 7 times worse on the radial axis (2.6 against 0.38 mm; claims-corrections 5). The table row "24 principal components" (0.439) is better than "all 24" (0.463), unexplained | Add the two facts; either explain the 0.439 (ridge penalty acts on whitened components) or drop that row |
| N-03-05 | Low | 9, 12 | Cell order: cell 9 uses `names`, `ks`, `vals`, `imp` defined in the figure cell 7; running section 3 alone gives `NameError` | Move `names = saved["inputs"]`, `imp`, `ks`, `vals`, `errs` to cell 3 |
| N-03-06 | Low | 9, 11 | `scipy` import undeclared (F-03) | `requirements.txt` |

## 6. Notebook 04 Stability over time

Checked: pooled MAE equals the baseline; decile table equals `results/ipp1-time.md` (agreement printed 2e-16); jitter 0.97, 1.03, 1.07;
offset 0.10, 0.62; autocorrelations; per-discharge 0.24, 1.48, 6.80; 456 switches in 137 discharges, 99.4 %, 15.9 %, 0.0090 against 0.0050;
speed quartiles 0.28 and 0.57.

| ID | Sev | Cell | Problem | Exact fix |
|---|---|---|---|---|
| N-04-01 | High | 20 (bullet 3), 0, 6, 7 | "The output is as smooth as the truth" is the unconditional stability claim the corrections forbid (claims-corrections 2). It holds on clean inputs and for the 7 targets in `KEY_T` only; limiter points are 0.69 and 0.48; on `equil_data_noisy.csv` the clean-trained network jitters 8.4 times (R axis) and 3.3 times (Z axis) more than the truth, 1.7 and 1.65 after training with noise and drift. The ratio is amplitude weighted: it says the network is smooth when its input is smooth, not that it is robust. The notebook never shows a noisy-input stability result | Cell 20 bullet 3: "On clean inputs the output varies as the truth does: jitter ratio 0.97 (R axis), 1.03 (elongation), 1.07 (current), 0.97 to 1.07 for the 7 targets shown. This is not a statement about noisy signals: with the provided noisy inputs the network trained on clean data varies 8.4 times (R axis) and 3.3 times (Z axis) more than the truth, 1.7 times after training with noise and drift (`results/ipp1-time.md`)." Cell 7: loop over all 16 targets (`NUM`), not `KEY_T`, so the limiter targets are visible. Add a cell reading `saved_time["noisy"]` (already in the committed `ipp1-time.json`) and printing the jitter columns |
| N-04-02 | High | 20 (bullet 5) | "Smoothing in time does not help ... The network output has no jitter to remove" is again clean-input only. For noisy inputs time context helps (3 rows: R axis 2.64 to 2.33 mm, Z axis 2.01 to 1.51 mm, error step 1.84 to 1.15 mm; `ipp1-robustness-findings.md` section 3), and the same 3 rows hurt on clean input (0.38 to 0.57 mm). This cell also smooths the **output**, which is a different thing from time context in the **input** | "On clean inputs a causal trailing mean of the predictions makes the error larger (2.0 times for 3 rows, R axis) because the truth moves 2.5 mm per row and the filter adds lag. On noisy inputs the picture changes: three consecutive rows as network input lower the axis error (notebook 06)." |
| N-04-03 | Medium | 20 (bullet 2), 5 | "larger at the two ends" with one factor (2.9, 1.5, 1.3) that averages the first and the last tenth. From the stored table with the corrections' middle (30 to 70 %, tenths 4 to 7): elongation start 1.06 and end 2.4 times the middle, current 0.99 and 1.9, R axis 2.5 and 3.7, Z axis 1.5 and 2.9. The corrections: growth mainly at the end (1.6 to 3.7 times the 30 to 70 % middle), at the start only for the axis position (R 2.5, Z 1.5); X-point and strike points do not exist at the start | Replace the combined ratio by two columns, `first_over_middle` and `last_over_middle` (middle = tenths 4 to 7, i.e. `dec[t][3:7].mean()`), and the text by: "The error grows mainly at the end of a discharge (R axis 3.7, Z axis 2.9, elongation 2.4, current 1.9 times the 30 to 70 % middle); at the start only the axis position is worse (R 2.5, Z 1.5 times)." (Recompute from the cell output after changing it.) |
| N-04-04 | Low | 20 (bullet 4) | "82 %" for `R_strike_point_1`: the output is 0.8145, 81 % (double rounding through the 3-decimal KEY value 0.815); `results/ipp1-time.md` 0.81 | Write 81 % |
| N-04-05 | Medium | 20 | The question "Is the output stable?" gets no one-sentence answer, and `is_limited` flicker at the switches (15.9 % wrong within 3 rows) is the one real instability found; it is in bullet 7 but not tied to stability | Add the answer line (F-07): "Accurate to about 0.4 mm on clean inputs, smooth when the input is smooth, worse at the end of the discharge and within 3 rows of a limited/divertor switch; on noisy inputs the output of a clean-trained network is not stable." |
| N-04-06 | Low | 11, 20 (bullet 6) | The per-discharge table is not cut by current polarity (16 discharges, 78 % of the error, `ipp1-distribution.md`) | One extra groupby on the sign of `plasma_current` |
| N-04-07 | Low | 7 | `saved_time` is defined in cell 5 and used in cell 7 | Load it in cell 3 |

## 7. Notebook 05 Real-time latency

Checked against `results/ipp1-latency.md|json` and the README.

| ID | Sev | Cell | Problem | Exact fix |
|---|---|---|---|---|
| N-05-01 | High | 14 (bullet "Verdict"), 0 | The verdict is not the conditional wording. It says shape computation "is therefore not the bottleneck" and lists sensor readout only; the required statement (REQUIREMENTS wording rules, claims-corrections 1) names the processor, gives 0.015 ms idle / 0.03 to 0.07 ms loaded, budget 1 to 10 ms, and the not-verified list: acquisition and integration of the coil signals, worst case on a real-time system, **accuracy on really noisy signals** (clean-trained network fails: 10.2 mm axis on the provided noisy file; trained with noise 2.6 mm). The accuracy item is missing entirely | Replace the bullet: "Verdict: the network computation is not an obstacle: median 0.015 ms on an idle Apple M5 CPU, 0.03 to 0.07 ms on a loaded or different CPU, tails up to milliseconds on a system without real-time guarantees, budget 1 to 10 ms. Not verified: acquisition and integration of the coil signals, the worst case on a real-time system, and accuracy on really noisy signals (a network trained on clean data fails on them; one trained with noise gives 2.6 mm on the axis)." |
| N-05-02 | High | 3, 14 (bullets 1 to 3, limits), 13 | "Saved quiet run" numbers differ from the committed `results/ipp1-latency.md|json`: p99 0.0288 (md 0.0209), p99.9 0.0699 (0.0812), max 0.0899 (0.148), numpy median 0.0129 (0.0125), GPU single 0.2405 (0.2681), CPU batch 4096 1.68 (2.42), GPU batch 4096 0.68 (0.70). Only the median 0.0145 agrees. The notebook's `out/ipp1-latency.json` is an older run; the claims file quotes max 0.090 as if it were in `results/` | Use one source: after F-03 the notebook reads `results/ipp1-latency.json`; re-execute 05 and regenerate cell 14 from it; or re-run `ipp1_latency.py` once on an idle machine, commit the new md/json and re-execute. Then the text in the corrections file, README and notebook quote the same max |
| N-05-03 | Medium | 5, 7 | Timed network is a random-weight `C.Net(24, 16)`, i.e. the baseline architecture. Cell 0 says "trained architecture" without saying which. The shipped candidate (46 inputs, ridge, gated limiter networks) was not timed | Cell 0 and the verdict: "Timed: the baseline network (24 inputs, 107,152 parameters). The shipped candidate model adds 22 difference inputs, a ridge and a gated limiter network and has not been timed." |
| N-05-04 | Medium | 11, 14 | The headroom table shows 0.1 against the **1 ms** budget at p99.9 (fails on the loaded machine) and 1.3 against 10 ms; the verdict argues only with the median against 10 ms ("195 times") | Add: "Against 1 ms, the loaded-machine p99.9 of 7.9 ms is not inside the budget; the idle median is." Quote 1 and 10 ms together |
| N-05-05 | Medium | stored outputs | The stored run is from a machine with load average 21.5 on 10 cores, so the first thing a reader sees is median 0.051 ms and max 57.7 ms and a 25 ms single call. It is explained, but it is the weakest possible picture of an otherwise good result | Re-execute 05 once on an idle machine (load under 2) before the freeze, or keep and label the loaded run as "stress case" in the cell 5 markdown |
| N-05-06 | Low | 3, 5 | The CPU of the fresh run is not recorded (only `os.cpu_count()`); the saved json has `"cpu": "Apple M5"` and cell 3 does not print it | `import platform; print(lat.get("cpu"), platform.processor() or platform.machine(), torch.__version__)` |
| N-05-07 | Low | 11, 14 | "4,137,933 times" and "1,167,883 times faster than one minute" is false precision on an assumed lower bound ("minutes") | Write "more than a million times faster than a classical reconstruction of one minute or more (`median 0.0145 ms` against 60 s)" |
| N-05-08 | Low | 14 (bullet 4) | `predict()` median 0.0355 ms is quoted as the realistic call; README and corrections use 0.053 ms numpy in and out and the md has 0.0140 (F-08) | Quote the measured `predict()` value with its own label and drop any cross reference to 0.053 until F-08 is settled |

## 8. Passed checks (so nobody repeats them)

- Absolute or personal paths in any notebook: none. Setup cell finds the repo from any working directory inside it and sets
  `HACKATHON_HOME` only if unset.
- Error outputs: none; `execution_count` runs 1 to n without gaps in all five, so they were executed top to bottom in order
  (except the order dependencies in N-03-05, N-04-07).
- Debug leftovers (`TODO`, `DOPLNIT`, `.head(`, scratch cells): none.
- Raw IPP rows in outputs: none; only `describe()` summaries, histograms, 2-D density plots and per-discharge traces (F-06).
- Seeds: 01 `KFold(random_state=0)`; 02 seed `k` per fold; 03 `default_rng(0)`; 05 `torch.manual_seed(0)`; GroupKFold is deterministic.
- Imports: all present in each notebook's setup or at first use; only `scipy` is undeclared.
- Units: every table has a unit column or unit in the header; every axis label with a physical quantity carries `[mm]`, `[kA]`
  or "abs"; unitless indices (nRMSE, ratios) are defined in the text.
- Claim wording already right: plasma current "use the linear model" (02), ranking "a property of the trained model, not a
  physical truth" (03 bullet 4), no real-time guarantee claimed (05 limits), drift "would have to be simulated" (01).

## 9. Suggested order of work for lane K (about 2 hours without the new notebooks)

1. F-03 (kernel, `requirements.txt`, `saved()` fallback, `make_all.sh` for the predictions): until this works nothing else can be checked by a run.
2. N-04-01, N-04-02, N-03-01, N-05-01, N-05-02 (the High text and number fixes; ten minutes each).
3. N-03-02, N-02-01, N-02-04, N-04-03 (small new cells that print numbers already in `results/`).
4. F-01: notebooks 06 to 08 from `results/` (data free), then F-02, F-04, F-05, F-07.
5. Re-execute all with `nbclient` from a clean clone and record which cell failed in the IMPL-8 row.
