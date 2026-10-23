# IPP 1: does the model know when it is wrong?

Five networks with different seeds are trained on the same data; the spread (SD) of their predictions is the uncertainty, the error is that of their
mean. Held-out rows only, the usual 5 folds by discharge. Full tables: `out/ipp1-uncertainty.{json,md}` (not in git); figure `ipp1-uncertainty.png`.

Command (`HACKATHON_HOME=<your hackathon folder>`): `~/.venvs/hackathon/bin/python -I analysis/ipp1_uncertainty.py`
(3 minutes; shared MLP, 60 epochs, 25 trainings, 2 threads).

| Target | Spearman | MAE of the 10 % most uncertain rows | MAE of the other 90 % | Ratio | Share of all error in the top 10 % | Ensemble MAE | Single net MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| plasma current (kA) | 0.52 | 3.72 | 0.55 | 6.7x | 43 % | 0.87 | 1.50 |
| R axis (mm) | 0.46 | 1.79 | 0.18 | 9.7x | 52 % | 0.345 | 0.403 |
| Z axis (mm) | 0.44 | 1.35 | 0.19 | 7.0x | 44 % | 0.308 | 0.397 |
| elongation | 0.51 | 0.0197 | 0.0036 | 5.5x | 38 % | 0.0052 | 0.0061 |
| triangularity | 0.45 | 0.0110 | 0.0017 | 6.4x | 42 % | 0.0027 | 0.0030 |
| X point R (mm) | 0.43 | 1.11 | 0.08 | 14.0x | 61 % | 0.183 | 0.217 |
| X point Z (mm) | 0.53 | 0.83 | 0.09 | 9.6x | 52 % | 0.162 | 0.211 |
| limiter R (mm) | 0.66 | 54.4 | 6.5 | 8.4x | 48 % | 11.3 | 12.2 |
| limiter Z (mm) | 0.48 | 52.5 | 17.2 | 3.1x | 25 % | 20.7 | 22.3 |

One warning per row (mean over R axis, Z axis, elongation and triangularity of spread and error, each divided by the target SD): Spearman 0.72, the
10 % most uncertain rows have 8.1 times the error of the rest and hold 47 % of the total error (random flagging would give 10 %).
Accuracy of `is_limited` from the ensemble: 99.25 %.

- **Yes, the disagreement is a usable warning signal.** Rows where the five networks disagree most carry 5 to 14 times the error and 38 to 61 % of
  all error for every target except limiter Z (3.1x, 25 %). A real-time system could flag these rows and fall back to a slower method.
- The ensemble mean is also more accurate than one network (R axis 0.345 against 0.403 mm, plasma current 0.87 against 1.50 kA), at five times the compute if the networks run one after another
  (`results/ipp1-latency.md` gives the single network time).

## Limits

- Only the seed varies, so the spread measures the variance of training, not an error all five share. We did **not** test whether the spread grows on
  unusual shapes (`ipp1-unusual-shapes.md`) or on noisy input, which is the case a warning must catch; it is untested whether it does.
- Rows of one discharge are near copies, so the Spearman values are not from independent samples. We did not check how many discharges the 10 %
  flagged rows come from; the warning may partly mark a few hard discharges.
- One realization; no thresholds were tuned, and no probability of error is claimed, only a ranking.
