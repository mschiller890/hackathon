# IPP 1: plasma position and shape from magnetic measurements (COMPASS)

**Task.** From 24 magnetic measurements (16 coils, 8 flux loops) estimate 16 quantities of the plasma (axis, X point, strike points, limiter point, current, elongation, triangularity), fast enough for control. The classical reconstruction takes minutes.

**What we built.** A *basic network* (24 inputs, 16 outputs). The *selected model* adds 22 differences of neighbouring coils, a linear model for the plasma current and a separate network for the limiter point. For the provided noisy inputs we ship another network, trained with noise and drift.

**Result.** The labels are the institute's reference reconstruction, so every number is *agreement with that reconstruction*, not physical accuracy. Mean absolute error, clean inputs. *Set aside*: 30 discharges kept out of training, scored once. *5-fold*: 119 development discharges, whole discharges per fold. Latency: one core of an Apple M5, shared machine, from the 24 raw inputs.

| Quantity | Selected, 30 set aside [95 % bootstrap by discharge] | Basic network, same 30 | Selected, 5-fold |
|---|---|---|---|
| Axis R (mm) | 0.133 [0.099, 0.177] | 0.307 | 0.23 |
| X point R (mm) | 0.115 [0.076, 0.168] | 0.161 | 0.211 |
| Strike points R, 1 and 2 (mm) | 0.108 [0.077, 0.144], 0.136 [0.084, 0.205] | 0.212, 0.212 | 0.206, 0.254 |
| Limiter point R, Z (mm) | 4.55 [3.30, 6.16], 8.35 [6.81, 10.2] | 10.6, 22.5 | 4.62, 11.8 |
| Plasma current (kA) | 0.0347 [0.0311, 0.0382] | 1.20 | 0.0332 |
| Latency per sample (ms) | median 0.015 (diverted), 0.027 (limited); p99 0.057, 0.093 | basic network 0.0145 | n/a |

Sources: `results/ipp1-final.md`, `ipp1-latency-shipped.md`, `ipp1-latency.md`. The order holds in 5 of 5 seeds; the X point is only somewhat better (`ipp1-final-seeds.md`).

**Other splits.** Blocked split (train on the 60 lowest discharge ids, test on the 59 highest; ids look chronological, not confirmed): axis R 0.397 mm against 0.216 mm on random folds of the same 59 discharges (basic network 1.23 against 0.448 mm), with fewer training discharges (`ipp1-final.md`). Training against held-out error, axis R of the selected model: 0.095 against 0.230 mm in 5-fold (2.4 times), 0.087 against 0.133 mm on the 30 (1.5 times); basic network 1.7 and 1.2 times; the largest 5-fold ratio is 3.8 times (strike point 2 R), so it fits its training discharges better than new ones (`ipp1-traintest-gap.md`). Errors are means: the basic network's median axis R error is 0.15 mm against a mean of 0.38 mm, and limited plasmas carry 92 % of its squared axis error (`ipp1-distribution.md`).

**What we did NOT show.**

- Physical accuracy beyond agreement with the reference; no independent measurement was used.
- Shapes outside the data: held-out groups with the 18 unusual discharges were 1.0 to 3.0 times worse, the extreme was never held out alone (`ipp1-unusual-shapes.md`). The model gives 16 numbers, not the boundary.
- Noisy inputs for the clean model: it fails, axis R 10.15 mm against 0.38 mm (basic network, 5-fold; `ipp1-robustness-findings.md`). The noise-trained network gives 2.38 mm on the 30 (`ipp1-final.md`). The provided noisy file has white noise only; drift results are synthetic.
- Signal acquisition and a real-time system: only the network computation was timed; tails are not bounds.

**Bonus analyses (one line each).**

- Amount of data: 30 training discharges give axis R 1.47 mm, 119 give 0.38 mm, fixed 60 epochs; time context: three samples help on noisy inputs, hurt on clean (`ipp1-robustness-findings.md`).
- Fewer inputs: 16 coils alone 0.066, all 24 inputs 0.063, 8 flux loops alone 0.285 (summary error; `ipp1-inputs.md`).
- Stability: errors grow mostly in the last tenth of a discharge (`ipp1-time.md`).
- Disagreement of five networks follows the error, Spearman 0.46 for axis R (`ipp1-uncertainty.md`).
- Camera network: axis R 1.79 mm in colour, 1.70 mm in grey, against 0.38 mm from magnetics (`cloud-camera-main.md`).

**Where everything is.** Notebooks `notebooks/01` to `09`; aggregate numbers and figures in `results/`; wording rules in `docs/claims-corrections.md`. Raw data are confidential and not in the repository.
