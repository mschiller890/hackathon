# Bonus gaps: what a jury could still call "not answered", and the ten cheapest ways to close it

Written Fri 23 Oct 2026 about 20:15 CEST by the cloud session `cloud/gap-hunter`, from `origin/main` c66e1f0. Sources read: `README.md`,
`docs/REQUIREMENTS.md`, `docs/PLAN.md`, `docs/TIMELINE.md`, `docs/notebook-review.md`, `docs/review-findings-2.md`, `docs/review-findings-3.md`,
`docs/REHEARSAL.md` (N11 only), `docs/DECISIONS.md` (D-RP6 only) and every `results/*.md` named below. The organizers' task text is not in the
repository (REQUIREMENTS.md: it is kept outside, with the data), so the item list follows the requirement rows `REQ-001` to `REQ-007`,
`REQ-B01` to `REQ-B08` as they quote it. There is no data and no Apple M5 here: **nothing was re-run**. Every result below is quoted from a
committed file. Runtimes are **estimates** and say what they are derived from. Slide lines are drafts in plain Czech; numbers not yet measured
are `DOPLNIT`.

## 0. Verdict

1. Every required question (REQ-001 to REQ-007) and every bonus (REQ-B01 to REQ-B08) has a number in `results/`. The weak spots are not missing
   topics but missing **controls and tails**: no training error anywhere, an uncertainty estimate that is a ranking and not calibrated, 15 of 31
   targets never scored in `results/`, the only partial bonus (unusual shapes) never tested on the unusual shapes alone, and "fewer inputs"
   answered only as a family-level statement.
2. One factual error is still in the prepared answers: `docs/REHEARSAL.md` N11 says the other 15 columns "we did not predict". They are predicted
   (`analysis/ipp1_oof_full.py`, 31 outputs, per-target errors in `out/ipp1-oof-full.md` on the Mac), they are only not published in `results/`.
   Experiment A fixes this in minutes.
3. Do first: **E** (18 oddest discharges held out alone), **A** (complete per-target confidence table), **B** (train against test gap as a
   learning curve at constant updates). Together about 2 hours of work and under 15 minutes of computing (estimates).
4. Anything that changes a spoken sentence must delete another one: `docs/review-findings-3.md` section 5 puts the script at 7:25 at a normal
   pace, so new results go to a notebook or the backup slide first.
5. `TIMELINE.md`: results freeze Sat 01:00 (no new training result enters `results/` after it), feature freeze Sat 10:00. The three FIRST items
   fit before 01:00.

## 1. Coverage matrix

Status: **done** (answered with a number and a figure or table), **partial** (answered, but a named piece is missing), **missing**.
Strength: A = 5 folds or a locked set and a seed or interval check; B = 5 folds, one seed; C = synthetic, 2 folds, or a labelled hypothesis.

| # | Item (requirement) | Status | Where | Strength of the evidence | Where a jury could say "not answered" |
|---|---|---|---|---|---|
| 1 | Accuracy per parameter (REQ-001) | done for 16 of 31 targets | `results/ipp1-baseline.md`, `ipp1-final.md`, `ipp1-final-seeds.md`, `ipp1-distribution.md` | A: baseline 5 folds, shipped model on 30 set-aside discharges with bootstrap and 5 seeds, but the locked set is 35 to 40 % easier than development CV (0.133 against 0.230 mm) | The other 15 columns have no table in `results/`; the answer "we did not predict them" (REHEARSAL N11) is false; headline is a mean (median 0.15 mm, p99 3.74 mm, worst 64 mm; limiter p99 78 and 92 mm, worst 357 and 485 mm) and no interval over discharges is given |
| 2 | Stability over time (REQ-003) | done for clean inputs; partial otherwise | `results/ipp1-time.md`, `.json`, `.png`, notebook 04 | B: baseline out-of-fold only | Measured for the baseline network, **not for the shipped model**; jitter ratio is amplitude weighted and says nothing about noise (clean-trained net jitters 8.4 times on noisy input); 15.9 % of `is_limited` wrong within 3 rows of a switch; the per-time table is not cut by polarity |
| 3 | Real-time feasibility (REQ-002) | done, conditional | `results/ipp1-latency.md`, `ipp1-latency-shipped.md` | B: Apple M5, load average 6 to 7, median stable to about 5 % over 5 runs | Shipped timing uses random weights and a numpy re-implementation that no file checks against the trained network (review 3); the noise-trained model needed for noisy input is not timed; acquisition of the coil signals not included; "1 to 10 ms" is our budget, the assignment says units to tens of ms |
| 4 | Fewer inputs (REQ-004) | done, as a negative result | `results/ipp1-inputs.md`, `ipp1-inputs-controls.md`, `ipp1-inputs-ranking.md` | B: seed noise 4.5 %; QR-pivot 8 inputs 0.072 against permutation top 8 0.115 | "Smallest set" depends on the selection method; no per-target smallest set; nothing for a sensor that fails at run time (review 2 question 9, "not tested"); smaller part of the **image** has a script (`cloud_camera_explain.py parts`) but no result file |
| 5 | Importance of inputs (REQ-004, REQ-B07) | done, as a negative result | same, `ipp1-inputs-ranking.md` | B: three rankings agree with Spearman -0.14 to +0.40; only FL01 (+7.6 %, 5 of 5 folds) and IPR13 (eliminated last in 5 of 5 ridge folds) survive | "Which sensors matter?" has no answer by design; notebook 03 still ranks by permutation importance only (notebook-review N-03-01, N-03-02); which **image parts** matter (occlusion) has a script and no result |
| 6 | Noise (REQ-B06) | done | `results/ipp1-robustness-findings.md` section 1, `ipp1-final.md`, `ipp1-data-checks.md` | A: provided file, 0.155 of an input SD, white noise; synthetic noise gives the same errors (10.4 against 10.2 mm) | Needs two models (clean 0.133 mm, noisy-input 2.38 mm; limiter 25.8 and 38.9 mm, current 4.65 kA) and a switch nobody tested; clean-trained model fails (9.16 mm); the combination "ridge current from the augmented candidate, rest from `base_aug`" was never run as one recipe (`ipp1-final.md`) |
| 7 | Drift (REQ-B06) | partial | `ipp1-robustness-findings.md` section 1 | C: the provided file has **no** drift (lag-1 -0.004, correlation with time 0.049); all drift is our synthetic `c * t` | "Is it drift robust?" is answered only for the baseline architecture and our own drift model; no mitigation tried; amplitudes of drift and noise are not comparable (file says so) |
| 8 | Amount of training data (REQ-B02) | done with a caveat | `ipp1-robustness-findings.md` section 2, `ipp1-learning_curve.png` | B-C: fixed 60 epochs, so small sets also get fewer updates; "halves per doubling" is overstated by the file's own words | No training error, so "more data or a bigger model?" cannot be answered; no curve for the shipped model; slide 13 x axis is categorical (review 2 L3) |
| 9 | Time context (REQ-B04) | done | `ipp1-robustness-findings.md` section 3, `ipp1-temporal.png` | C: 3 rows help noisy input (R axis 2.64 to 2.33 mm, 5 of 5 folds), hurt clean (0.38 to 0.57 mm); the reason is a **labelled hypothesis** | Only 3 rows; the discriminating test the file proposes (x(t) and x(t) minus x(t-1)) was not run; not tried on the shipped model |
| 10 | Black and white camera (REQ-B03) | done | `results/cloud-camera-main.md`, `ipp1-camera-local-findings.md` | B: 5 folds, R axis 1.79 colour against 1.70 mm grey, below fold SD; local 2 folds agree (1.54 against 1.53) | Small network (48x64, width 16, 12 epochs, every 8th frame, 78 of 149 discharges); frames carry almost no colour (8.7 of 255) so the question is easy |
| 11 | Camera model and multimodal (REQ-B01) | done | `cloud-camera-multimodal.md`, `cloud-camera-findings.md` | B: like for like magnetic network; camera 1.3 to 13 times worse; camera plus magnetics beats magnetics only at the limiter point (R 12.6 against 16.7 mm) | Fusion with **realistic (noisy)** coils, the case where fusion could win, is "planned" only; camera accuracy against the number of training discharges (`curve`) is `DOPLNIT`; readout and JPEG decoding not timed |
| 12 | Unusual shapes (REQ-B08) | **partial** | `results/ipp1-unusual-shapes.md` | C: factor 1.0 to 3.0 on held-out groups that merely **contain** the 18 odd discharges (one seed, 23 to 43 discharges per group) | The 18 truly unusual discharges were never held out alone; the extreme (elongation near 1.0) never tested as an unseen extreme; uncertainty on unusual shapes untested (`ipp1-uncertainty.md` limits); the stated REQUIREMENTS wording is "tested on groups containing the 18" |
| 13 | Camera position and rotation (REQ-B05) | done for the sensitivity, remedy open | `cloud-camera-findings.md`, `cloud-camera-main-sensitivity.png`, `ipp1-camera-local-findings.md` | B: 1 px (1.6 % of the width) roughly doubles the error; 5 degrees multiplies it by 1.5 to 2.3 | Training with random shifts (`augment`) is `DOPLNIT` on 5 folds; the 2-fold local run fixes the shift (2.0 mm) but the curve is non monotonic, "padding suspected" |
| 14 | Uneven distribution (REQ-007) | partial | `ipp1-distribution.md`, `ipp1-signcanon.md` | A for the measurement (limited rows 44.2 % of rows, 91.9 % of squared axis error; 16 reversed-polarity discharges 7.4 % of rows, 77.8 %); the response is a **trade**, not shipped | `REQUIREMENTS.md` row still says the response is "to do" although IMPL-13 delivered one (stale); stratified folds and reweighting never tried; the locked set holds 2 reversed discharges, so the shipped model's polarity result is not reliable |
| 15 | Split by whole discharges (CON-002) | done | `ipp1-final.md` (blocked split), notebook 01 section 8 (1-NN 0.62 against 2.03 mm) | A | Blocked by id the error is 1.5 to 2.9 times larger, part of it from 60 instead of about 95 training discharges (file says so); ids "chronological" is not confirmed with the organizers |
| 16 | Uncertainty (extra, REQ-003 style) | done as a ranking | `results/ipp1-uncertainty.md` | B: Spearman 0.43 to 0.66; top 10 % rows hold 38 to 61 % of the error | Not calibrated ("no probability of error is claimed"); untested on noisy input and unusual shapes; flagged rows may come from a few discharges (file says it was not checked) |
| 17 | Training against test error | **missing** | none (`grep` for train error finds only a hypothesis sentence in `ipp1-robustness-findings.md`) | none | The first ML question after "split by discharge": is it overfit? |
| 18 | Notebooks with all conclusions (REQ-005) | partial | `notebooks/01` to `05`, `07`, `08`, `09` | B: notebook-review lists fixes for 01 to 05; applied or not is **not verified here** | `06` (camera) is missing, waits for gate G1; notebook 04 and 05 wording fixes of notebook-review N-04-01, N-05-01, N-05-02 unverified |

## 2. The ten experiments, ranked by value per hour

"Hours" are working hours of one person or agent for coding, running and writing the result file (estimates). "Laptop runtime" is for 4 threads
and is derived from recorded runs: a 5-fold baseline takes about 1 minute (README table, Ryzen), the 25-training uncertainty script 3 minutes,
`ipp1_unusual_shapes.py` 1.5 minutes for six groups, `ipp1_inputs_ranking.py` 9.1 minutes, the 21 jobs of `ipp1_final.py` 295 seconds on the
Apple M5. **Who:** every run needs the data, so a local terminal (bladed-55, bladed-85) runs it; a cloud session without data can still write and
test the script on a synthetic fixture (`ipp1_common.py` fails at import without data, audit R-1, so the fixture needs a fake
`HACKATHON_HOME`), and can write the result file once the numbers are pasted in.

### FIRST three (do these before Sat 01:00)

#### 1. E: the 18 oddest discharges held out alone (closes REQ-B08)
- **Question.** What does the network do on the shapes that break the usual correlations, when they are really absent from training?
- **Method.** (1) Take the 18 discharges with median elongation 1.0 to 1.74 and triangularity 0.02 to 0.33 that `ipp1_unusual_shapes.py` already
  finds (all in its cluster 0); (2) train on the other 131 and test on the 18, and again on the 5 lowest-elongation discharges alone;
  (3) reference is the random-fold error on the same discharges (the factor the script already computes), report MAE, p99 and the elongation error
  against its range, and check whether the 18 ids are contiguous (then it is also a campaign test).
- **Copy.** `analysis/ipp1_unusual_shapes.py` (add two groups; groups are built from medians there).
- **Laptop runtime.** About 1 to 2 minutes (the script does six groups in 1.5 minutes, about 15 seconds each; estimate).
- **Who.** Local terminal; bladed-85 wrote the original.
- **Overclaim risk.** Medium. 18 discharges, one seed; if the ids are contiguous the factor mixes shape with campaign; says nothing about shapes
  outside the data range. Wording: "tested with the 18 oddest discharges removed from training", never "new shapes".
- **Slide.** "Osmnáct nejodlišnějších výbojů jsme z učení úplně vynechali: chyba osy DOPLNIT milimetru, DOPLNITkrát větší než u ostatních. Tvary mimo rozsah dat jsme neověřili."

#### 2. A: the complete per-target confidence table (31 targets, interval over discharges)
- **Question.** How accurate, and how certain is that accuracy, for every parameter, including the 15 never scored in `results/`?
- **Method.** (1) Collect out-of-fold predictions: baseline for all 31 targets (`out/ipp1-predictions-full.csv`, already made by `ipp1_oof_full.py`;
  its report `out/ipp1-oof-full.md` is not in `results/`), the shipped model on the 119 development discharges (cache of `ipp1_final.py`, jobs
  `cv:cand:k`) and on the locked 30; (2) per target MAE, median, p95, p99, a 95 % interval of the MAE by bootstrap over **whole discharges**, and the
  share of discharges whose mean error is under a stated tolerance (as `ipp1_claim_support.py` does for the axis at 1 mm); (3) slices that the
  locked set cannot give: reversed polarity (16 of 149 discharges, 14 of them in the development set, 2 in the locked set), limited against
  diverted, last 2 % of the discharge, time deciles for the shipped model (item 2 of the matrix). Write `results/ipp1-confidence.md`.
- **Copy.** `analysis/ipp1_distribution.py` (slices, asserts against `score_extended`), `analysis/ipp1_claim_support.py`, bootstrap code in
  `analysis/ipp1_final.py`.
- **Laptop runtime.** Scoring about 2 minutes when the CSV and the cache exist (estimate); `ipp1_oof_full.py` about 3 minutes and the final cache
  295 seconds on the M5 if they must be rebuilt. Writing the file 30 to 40 minutes.
- **Who.** Local terminal (the caches live on the Macs). The cloud session can write and test the script.
- **Overclaim risk.** Low. The 31-target numbers belong to the **baseline** network (the shipped pair predicts 16 of 31): say so in the header.
  The locked set is 35 to 40 % easier than development CV, so print both side by side.
- **Slide.** "Každá z jedenatřiceti veličin s rozsahem, ve kterém jí můžeme věřit: osa DOPLNIT milimetru, interval DOPLNIT; bod u limiteru DOPLNIT." Also replaces the false answer in REHEARSAL N11.

#### 3. B: training against test error, as a learning curve at constant updates
- **Question.** Is the network overfit, and does more data (or a bigger model) still pay?
- **Method.** (1) For 5 folds train the baseline network on 6, 12, 30, 60 and 119 training discharges with the **number of optimizer updates held
  equal** (epochs scaled by 119 divided by n), which removes the confound named in `ipp1-robustness-findings.md`; (2) score the training rows
  and the held-out rows with the same `score` and report the test over train ratio per target; (3) one more point: the shipped candidate at
  full data, training rows against development-CV rows. Plot both curves against n on a log axis.
- **Copy.** `analysis/ipp1_learning_curve.py` (61 lines, nested subsets already built); `fit_mlp` returns a `predict` closure, so train rows are one extra call.
- **Laptop runtime.** At most 5 minutes (the original takes 1 to 2.5 minutes; constant updates make small sets cost as much as the largest; estimate), candidate fit 1 to 2 minutes.
- **Who.** Local terminal.
- **Overclaim risk.** Medium. Rows within a discharge are near copies, so training error is optimistic by construction and a large gap is expected;
  report the ratio, never "no overfitting". Constant updates is one control among others.
- **Slide.** "Na učení je chyba DOPLNIT milimetru, na nových výbojích DOPLNIT: odstup je DOPLNITkrát. Se všemi učícími výboji křivka DOPLNIT (ještě klesá, nebo se zplošťuje)."

### The remaining seven

#### 4. O: does the timed numpy path equal the trained network? (real-time claim)
- **Question.** Is the 0.027 ms of the closing slide the speed of the model that was scored?
- **Method.** (1) Train the shipped pair once (the cache stores predictions, not weights) and compare `predict()` of `ipp1_final.py` with the numpy path
  on 1000 rows, report the maximum absolute difference per target; (2) time the numpy path with the trained weights on a quiet machine (load below 2),
  CPU named; (3) time the noise-trained baseline too (the model needed for noisy input, not timed so far).
- **Copy.** `analysis/ipp1_latency.py --shipped`.
- **Laptop runtime.** About 10 minutes including one training (estimate).
- **Who.** Local terminal on the Apple M5 (the Lead's quiet-machine rerun in TIMELINE is the same session).
- **Overclaim risk.** Low. Weights do not change timing; this is a correctness check. Do not quote a better median from a busy machine.
- **Slide.** No new sentence: it removes the footnote "náhodné váhy" from the latency tile.

#### 5. H: failure-case gallery and tail attribution
- **Question.** Where exactly does it fail, and why? (axis p99 3.74 mm, worst 64 mm; limiter p99 78 and 92 mm, worst 357 and 485 mm)
- **Method.** (1) A table of the rows above p99 (axis and limiter): share in the last 2 % of a discharge, with reversed current, within 3 rows of a
  limited/divertor switch, limited, and how many discharges hold them; (2) pick **by rule**, not by taste: the 3 discharges with the largest mean axis
  error and the median one; figure with true and predicted boundary at the worst frame and the error trace over time; (3) one sentence of cause per
  case, only where the table supports it.
- **Copy.** `analysis/ipp1_oof_full.py` (predicted outline), `analysis/export_viewer_data.py` and `viewer/record.py` (stills chosen by rule),
  switch logic in `analysis/ipp1_time.py`, slices in `analysis/ipp1_distribution.py`.
- **Laptop runtime.** Under 5 minutes of computing with the CSV in place; 45 to 60 minutes to assemble the figure (estimate).
- **Who.** Local terminal.
- **Overclaim risk.** Low for claims, **constraint for confidentiality**: D-RP6 allows one real discharge in the talk and nothing in a public
  repository; a gallery of four needs the owner's yes, and the PNG stays out of git until OQ-S1 and OQ-S2 (private repository) are answered.
- **Slide.** "Kde to selhává: konec výboje, obrácený směr proudu a přechod mezi limiterem a divertorem. Ukazujeme tři nejhorší výboje a jeden typický, vybrané pravidlem, ne ručně."

#### 6. C: calibration of the uncertainty estimate
- **Question.** Can the spread of the five networks be turned into an expected error with honest numbers? (`ipp1-uncertainty.md`: "no probability of error is claimed")
- **Method.** (1) Rerun the 5-network ensemble per fold and keep spread, error and discharge for every row; (2) reliability table by decile of spread
  (mean error and RMS error divided by spread), a monotone map spread to expected error fitted on four folds and tested on the fifth, and the
  share of rows with |error| within 1, 2 and 3 spreads; (3) count how many discharges hold the top 10 % flagged rows (the limit the file names).
- **Copy.** `analysis/ipp1_uncertainty.py` (115 lines).
- **Laptop runtime.** About 3 to 4 minutes (the script states 3 minutes for 25 trainings on 2 threads).
- **Who.** Local terminal.
- **Overclaim risk.** Medium. Only seed variance is measured, so coverage will probably fall short of nominal (shared bias is invisible to five seeds); say
  "a risk ranking calibrated to X", never "confidence interval". Report intervals over discharges, rows are near copies.
- **Slide.** "Když se pět sítí neshodne, je chyba DOPLNITkrát větší; z rozptylu odhadneme chybu s odchylkou DOPLNIT. Je to varování, ne interval spolehlivosti."

#### 7. G: a sensor fails at run time
- **Question.** If one coil, or a whole family (16 coils, 8 flux loops), fails, can the network still be used? (review 2 question 9: "not tested")
- **Method.** (1) Train the baseline with random input dropout (each input lost with probability 0.1, mask as extra input) and the plain baseline;
  (2) at test time drop each of the 24 inputs singly, and each family, on held-out discharges; (3) table: axis and X-point MAE for both models.
- **Copy.** `analysis/ipp1_baseline.py` and `ipp1_common.fit_mlp` (about 40 new lines for the input mask); test-time masking idea from `analysis/ipp1_inputs.py`.
- **Laptop runtime.** About 4 minutes (2 trainings by 5 folds at about 10 seconds; estimate).
- **Who.** Local terminal.
- **Overclaim risk.** Medium. The dropout-trained network is a different model from the shipped one; zero-filling the plain model creates rows off the data
  manifold (the same objection that rejected permutation importance), so show it only as the weak control. The already measured related answer is
  `ipp1-inputs-ranking.md`: no single input is necessary except FL01 (+7.6 %).
- **Slide.** "Výpadek jednoho čidla zhorší osu z DOPLNIT na DOPLNIT milimetru; výpadek všech smyček na DOPLNIT. Síť učená s výpadky to zvládne lépe (DOPLNIT)."

#### 8. F: the smallest input set per target
- **Question.** How many inputs does each target need, with an answer that does not depend on one ranking method?
- **Method.** (1) **No data needed:** tabulate the per-target errors of the QR-pivot, backward-ridge and permutation sets at 6, 8 and 12 inputs from the
  committed `results/ipp1-inputs-controls.json`; (2) with data: retrain on QR-pivot sets of 3, 4, 6, 8, 12 and 16 inputs inside each fold for six headline targets
  and report the smallest k within 1.25 times the all-24 error **and** beyond the measured seed noise of 4.5 %; (3) name the coil/loop mix of the set, not "the important sensors".
- **Copy.** `analysis/ipp1_inputs.py` (controls, QR-pivot code), `analysis/ipp1_inputs_ranking.py` (seed noise, ridge path).
- **Laptop runtime.** Step 1 seconds; step 2 about 6 minutes of training (6 sizes by 5 folds at about 10 seconds), up to 15 minutes if the existing loop is reused unchanged (it needed about 13 minutes per fold in the second-machine run).
- **Who.** Step 1 any session including the cloud; step 2 a local terminal.
- **Overclaim risk.** Medium to high: it reopens the ranking argument. One seed per cell; differences below 10 to 15 % are noise (controls file); the sets are
  method specific. Wording rule from REQUIREMENTS: "ranked by importance for the trained network".
- **Slide.** "Osu určíme z DOPLNIT vstupů s chybou do 1,25násobku, bod X z DOPLNIT; které vstupy to jsou, záleží na způsobu výběru."

#### 9. D: does the uncertainty warning fire under noise and on unusual shapes?
- **Question.** Does the spread rise in the cases the warning is for, or only in ordinary tails? (`ipp1-uncertainty.md`: "untested")
- **Method.** (1) Feed the provided noisy inputs to the clean-trained and the noise-trained ensembles and compare mean spread and the spread-error
  correlation with the clean case; (2) use the 18 held-out discharges of experiment E and compare their spread with the same discharges in random folds;
  (3) report for each setting how well the spread flags rows above the p95 error.
- **Copy.** `analysis/ipp1_uncertainty.py`, `analysis/ipp1_oof_noise.py` (`load(noisy=True)`), group code of `analysis/ipp1_unusual_shapes.py`.
- **Laptop runtime.** About 6 to 8 minutes (two ensembles of 25 trainings plus one of 5; estimate).
- **Who.** Local terminal, after E.
- **Overclaim risk.** Medium. A negative result (the spread does not rise) is likely enough to plan for; both outcomes are reportable.
- **Slide.** "Varování při šumu a u neobvyklých tvarů: rozptyl vzroste DOPLNITkrát (nebo: nevzroste, DOPLNIT)."

#### 10. J: time context, the discriminating test and longer windows
- **Question.** Why do 3 rows help on noisy and hurt on clean input, and do longer windows help more?
- **Method.** (1) Compare stacked rows [x(t-2), x(t-1), x(t)] with [x(t), x(t) minus x(t-1)], the test `ipp1-robustness-findings.md` itself proposes;
  (2) windows of 1, 3, 5 and 9 rows on the provided noisy input, causal; (3) error and error step, 5 folds.
- **Copy.** `analysis/ipp1_temporal.py` (96 lines).
- **Laptop runtime.** About 5 minutes (the original takes 1 to 2.5 minutes for 4 settings; estimate).
- **Who.** Local terminal.
- **Overclaim risk.** Low to medium. A window is a count of rows, not milliseconds (the 0.6 ms spacing is in no committed `results/` file); one seed; the noise is the provided file's.
- **Slide.** "Více časových kroků pomáhá jen při šumu: tři řádky DOPLNIT, devět řádků DOPLNIT. Na čistých vstupech škodí."

### Considered, not in the top ten
- **Noisy-input recipe as one model** (ridge current from the augmented candidate, the rest from `base_aug`): changes the current from 4.65 to about 4.03 kA at most (`ipp1-final.md`); a second look at the locked set, so it must be chosen on development CV first. Small gain, some risk.
- **Camera `augment`, `curve`, `parts` and `occlusion`:** scripts exist, results do not. Each setting is a 5-fold camera fit (about 160 s per fit, 13 minutes per setting, estimate from `cloud-camera-findings.md`); the camera is cut-list item 1 of `TIMELINE.md`. Only **collect** what the camera cloud session already produced (check its branch `cloud/camera` before 22:00); do not recompute.
- **A drift mitigation and the shipped model under drift:** would need a physical drift model that the provided file does not support (no drift in it).

## 3. Stop doing

Evidence is in the files cited; "low value" means it does not change any answer in the matrix.

1. **The cloud hyperparameter search (`cloud-search.md`).** The committed file is a shell: status PARTIAL, an empty Pareto table, "not run" for the per-target, limiter and noisy sections. The rule in `TIMELINE.md` says no tested result by 21:30 means the locked recipe stands; any change after that also invalidates the review-2 numbers H1 and H2. Remove it from the story and label or hide the file so a reader does not open an empty table.
2. **Another ranking of the inputs** (permutation, drop-column, greedy). Three rankings already disagree (Spearman -0.14 to +0.40); a fourth cannot settle it. The family result (IPR 0.066 against FL 0.285) and IPR13 are what survives.
3. **Further sign-canonicalisation work** (`ipp1-signcanon.md`, "keep the raw inputs as extra features"). The verdict is a trade, not shipped, and on the locked 30 it moves the axis 0.133 to 0.126 mm.
4. **More latency variants** (GPU, batch sizes, thread counts). The run-to-run spread of the median is about 5 %, the GPU is 35 to 65 times slower for one sample, and the budget is met 30 to 100 times over. Do only the quiet-machine rerun and the equality check (item 4).
5. **More camera training runs** beyond collecting existing results (see above). It is the bonus with the largest gap to the coils (1.3 to 13 times) and the first item on the cut list.
6. **Another independent review round of the talk.** Reviews 2 and 3 already found the text mostly fixed; what remains is a short list of specific edits (`review-findings-3.md` section 1 and X1 to X6). Spend the next review once, after the last number changes (`check_claims.py` at 01:30 and 08:00 is already planned).
7. **Seed repetitions of recipe comparisons.** `ipp1-final-seeds.md` already gives 5 seeds; only the X-point (0.79, worst seed 0.97) stays unresolved, and no further seed will change the slide.
8. **Reel polish** (cut list item 2) and new slides: the script already overruns 7:00 at a normal pace.

## 4. How the results should enter the repository

- Each experiment writes one file `results/ipp1-<name>.md` with the command, the protocol and its limits, as the existing files do; no raw rows, no PNG of a real discharge before the owner answers OQ-S1/OQ-S2.
- After a result lands: update the matrix row here (status, strength), the matching row of `docs/REQUIREMENTS.md`, and run `analysis/check_claims.py` before any number reaches a slide.
- Not done here and not claimed: no experiment of section 2 has been run, no runtime was measured, and the status cells in section 1 are read from the committed files, not re-verified.
