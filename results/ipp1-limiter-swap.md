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

<!-- RESULTS BELOW -->
