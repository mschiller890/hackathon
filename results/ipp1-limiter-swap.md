# IPP 1: can the limiter point be improved by changing only the limiter network?

**Protocol and decision rule, written before any run of this experiment** (committed before `analysis/ipp1_limiter_swap.py` was first executed; the script header carries the same text).
Motivation: `results/ipp1-search-dev.md` found that the residual network of the best search trial cut the limiter error of the `cand` pipeline by 39 % (`R_limiter` 4.85 to 2.97 mm,
`Z_limiter` 12.2 to 7.44 mm) but was worse on other targets. The limiter targets are the weakest of the shipped model (locked 30 discharges: 4.55 mm and 8.35 mm). Here only the limiter
network is changed.

## Arms (119 development discharges, 5 group folds, 3 seeds, paired: same folds, same seed = fold + 10 x s for every arm)

- **arm 0, `cand` as is.** Predictions of `cand` (the cached cross-validation of `ipp1_final.py` for seed 0 and of `ipp1_search_dev.py` for seeds 1 and 2).
- **arm 1, residual limiter network.** `cand` with ONLY the limiter network replaced by the residual network of the best search trial (`resA` of `results/ipp1-search-dev.md`: residual MLP,
  width 192, depth 4, GELU, 100 epochs, loss weight 1.5 on the limiter targets), trained on the limited rows of the training discharges.
- **arm 2, control.** `cand` with its own limiter network (MLP 256-256-128, 46 inputs) trained with the same loss weight 1.5 on the limiter targets and the same 100 epochs instead of 150.
  It tells whether the gain comes from the weight and the epochs and not from the architecture.
- The general network, the ridge for the plasma current and the gate (`is_limited` predicted above 0.5 by the general network) are those of `cand` in all arms, so every column except
  `R_limiter` and `Z_limiter` is the same in all arms by construction; this is verified by comparing the arrays.

## Measure

Pooled out-of-fold MAE per target in mm over the development rows that have the target (the limited rows), mean and SD over the 3 seeds. Relative gain = 1 - (MAE of the arm) / (MAE of arm 0),
from the means.

## Ship rule

An arm *passes* only if all of these hold:
1. **Gain:** the relative gain is at least 15 % for `R_limiter` AND for `Z_limiter`.
2. **Gain above noise:** for each of the two targets the absolute gain (mm) is larger than the seed SD of the arm and larger than the seed SD of arm 0.
3. **Nothing else changes:** all columns other than `R_limiter` and `Z_limiter` are identical to arm 0 (checked), and therefore the axis error in the limited rows (`R_mag_axis`, `Z_mag_axis` MAE
   on the rows with `is_limited` true) does not get worse (it is printed).
4. **Latency:** the median latency of the limited path (numpy path of `results/ipp1-latency-shipped.md`: 24 raw inputs to 16 outputs, both networks run) stays below 0.1 ms, measured here with the
   same protocol (5,000 timed calls after warm-up, one core) in the same run for all three arms.

**Winner.** If arm 2 passes and (its gain is at least half of the gain of arm 1 for both targets, or arm 1 does not pass), the winner is **arm 2**: it changes only a hyperparameter. Otherwise, if arm 1 passes,
the winner is arm 1. Otherwise nothing changes and `cand` stays.

**Locked set.** Only the winner is scored on the 30 locked discharges, once (trained on the 119 development discharges, seed 0), and the run is logged below; the script refuses a second run.
Results freeze at 01:00.

## Status

Not run yet when this text was committed.

## POST HOC AMENDMENT of criterion 4 (Lead decision, 23 Oct about 20:25; written before the new measurements)

**This is a change of the rule made after the result of the first run was known.** In the first run arm 1 passed criteria 1 to 3 and failed criterion 4 only (median latency of the limited path 0.117 and
0.108 ms in the two `nice 10` runs of the report, against the limit of 0.1 ms; arm 0 measured 0.042 and 0.040 ms). The Lead decided that the limit of 0.1 ms was a conservative guard (the real budget is 1 to 10 ms)
and that the measurement under `nice` and load was unfair to the arm with the bigger network. The original rule text above and the two failed runs stay in this file; the formal verdict of the original rule
(nobody wins) stays as it was.

**Amended criterion 4:** the latency is judged on the median of at least 5 repeated runs of the same measurement at NORMAL priority (no `nice`), for arm 1 and for `cand` in the same state of the machine (each run
measures all three arms one after the other); arm 1 passes if the median over the runs of its median latency in the limited path is below 0.1 ms. Everything else of the rule is unchanged (gain, noise,
nothing else changes, winner choice, the locked set once and only for the winner). If arm 1 passes under the amended criterion it is scored once on the locked 30 discharges, and the script logs that this
happened on the post hoc pass. If its locked result is worse than `cand` on either limiter target, it is not shipped. Shipping, if any, is a separate decision (a new recipe, not a change of `ipp1_final.py` here).

<!-- RESULTS BELOW -->

## Results (119 development discharges, 5 folds x 3 seeds, pooled out-of-fold MAE in mm, mean (SD over seeds))

| arm | R_limiter | Z_limiter | gain R | gain Z | axis in limited rows R / Z | median latency, limited path (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| arm 0, `cand` | 4.85 (0.25) | 12.2 (0.45) | | | 0.331 / 0.404 | 0.0399 | 0.436 |
| arm 1, residual limiter network | 2.98 (0.14) | 7.44 (0.38) | 39 % | 39 % | 0.331 / 0.404 | 0.1077 | 1.490 |
| arm 2, control: own network, weight 1.5, 100 epochs | 5.11 (0.26) | 12.4 (0.33) | -5 % | -1 % | 0.331 / 0.404 | 0.0312 | 0.669 |

Check of criterion 3: the largest absolute difference of any column other than `R_limiter` and `Z_limiter` to arm 0 is 0 (arm 1) and 0 (arm 2).
Latency: random weights of the trained shapes, numpy path from 24 raw inputs (differences, standardisation, general network, ridge, gate, limiter network, de-standardisation), one core, load average [10.6, 10.2, 9.2] (`nice` job on a shared laptop, so the tails are pessimistic).

| arm | gain >= 15 % on both | gain above seed SD | nothing else changes | latency < 0.1 ms | **passes** |
|---|---|---|---|---|---|
| arm 1, residual limiter network | yes | yes | yes | no | **no** |
| arm 2, control: own network, weight 1.5, 100 epochs | no | no | yes | yes | **no** |

Arm 2 gets -14 % of the gain of arm 1 on R_limiter, -3 % of the gain of arm 1 on Z_limiter.

**Winner by the rule: nobody, `cand` stays.**

## Reading

- **By the rule as written: nobody wins, `cand` stays.** The locked 30 discharges were not used. Arm 1 fails only criterion 4 (latency), arm 2 fails criteria 1 and 2.
- **The control answers the question it was built for: the loss weight 1.5 and the 100 epochs do not give the gain.** Arm 2 (own network, same weight and epochs) is 5 % and 1 % *worse* than `cand` (5.11 and 12.4 mm against 4.85 and 12.2 mm; the SD over seeds is 0.26 and 0.33 mm). Arm 1 differs from arm 2 in the whole network and its training (residual blocks, GELU, cosine schedule, Huber delta 0.36, learning rate 0.0028, weight decay 2e-6, dropout 0.05), so this does not say which of these carries the gain, only that it is not the weight and the epochs.
- **Arm 1 is a real gain on the limiter point and nothing else moves.** `R_limiter` 4.85 to 2.98 mm and `Z_limiter` 12.2 to 7.44 mm, 39 % in both, with a gain of 1.9 and 4.8 mm against seed SDs of 0.14 to 0.45 mm; all other columns are identical to `cand` (difference 0) and the axis error in the limited rows is unchanged (0.331 and 0.404 mm). It is also the same 39 % that the full residual pipeline gave in `results/ipp1-search-dev.md`, so the gain comes from the limiter network.
- **Latency is on the limit and depends on how the measurement is run, so the verdict hangs on it.** Five measurements of arm 1 (median, limited path, ms): 0.117 and 0.108 in the two runs of the report (the table shows the second one), both as `nice` jobs at load average 7 to 9, and 0.094, 0.089, 0.093 in three further runs of the same function at normal priority and load 13, made afterwards and not part of the rule. `cand` measured 0.042 and 0.040 in the report runs, 0.030, 0.038, 0.029 afterwards (0.027 ms in the quiet measurement of `results/ipp1-latency-shipped.md`). Arm 1 costs about three times as much as `cand` (a bigger limiter network). The runs at normal priority are below 0.1 ms and the `nice` runs above it, which fits an effect of priority and load, but it was not tested separately; on a quiet machine arm 1 would probably be near 0.08 ms, an extrapolation, not a measurement.
- **What a change of the rule would mean.** If the latency criterion were applied to the median of repeated runs, arm 1 would pass all four criteria. That is a change made after seeing the result and has to be decided and logged as such (by the Lead, with the owner); this file does not make it. The control rules out the cheap explanation, so shipping arm 1 would change the limiter network, not a hyperparameter.
- **Limits.** The residual network's hyperparameters came from a search that saw all 149 discharges, and the cross-validation here is inside the 119 development discharges; both arms are optimistic in the same way, but the gain over `cand` is an in-sample-selected configuration against a recipe designed on the same discharges. One configuration, 3 seeds, 5 folds.
