# IPP 1: can the limiter point be improved by changing only the limiter network?

**Protocol and decision rule, written before any run of this experiment** (committed before `analysis/ipp1_limiter_swap.py` was first executed; the script header carries the same text).
Motivation: `results/ipp1-search-dev.md` found that the residual network of the best search trial cut the limiter error of the `cand` pipeline by 39 % (`R_limiter` 4.85 to 2.97 mm,
`Z_limiter` 12.2 to 7.44 mm) but was worse on other targets. The limiter targets are the weakest of the shipped model (locked 30 discharges: 4.55 mm and 8.35 mm). Here only the limiter
network is changed.

## Arms (119 development discharges, 5 group folds, 3 seeds, paired: same folds, same seed = fold + 10 x s for every arm)

- **arm 0, `cand` as is.** Predictions of `cand` (the cached cross-validation of `final_evaluation.py` for seed 0 and of `ipp1_search_dev.py` for seeds 1 and 2).
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
happened on the post hoc pass. If its locked result is worse than `cand` on either limiter target, it is not shipped. Shipping, if any, is a separate decision (a new recipe, not a change of `final_evaluation.py` here).

*Times.* The Lead's message gave the time of the decision as about 20:25; the clock of the machine shows this paragraph committed at 20:16:38 (`git log`), before the five latency runs (about 20:17) and before the locked scoring (20:17, logged below). The order is right, the quoted time is only the Lead's estimate.

<!-- RESULTS BELOW -->

## Results (119 development discharges, 5 folds x 3 seeds, pooled out-of-fold MAE in mm, mean (SD over seeds))

| arm | R_limiter | Z_limiter | gain R | gain Z | axis in limited rows R / Z | median latency, limited path (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| arm 0, `cand` | 4.85 (0.25) | 12.2 (0.45) | | | 0.331 / 0.404 | 0.0399 | 0.436 |
| arm 1, residual limiter network | 2.98 (0.14) | 7.44 (0.38) | 39 % | 39 % | 0.331 / 0.404 | 0.1077 | 1.490 |
| arm 2, control: own network, weight 1.5, 100 epochs | 5.11 (0.26) | 12.4 (0.33) | -5 % | -1 % | 0.331 / 0.404 | 0.0312 | 0.669 |

Check of criterion 3: the largest absolute difference of any column other than `R_limiter` and `Z_limiter` to arm 0 is 0 (arm 1) and 0 (arm 2).
Latency: random weights of the trained shapes, numpy path from 24 raw inputs (differences, standardisation, general network, ridge, gate, limiter network, de-standardisation), one core, load average [7.4, 8.9, 8.8] (`nice` job on a shared laptop, so the tails are pessimistic).

| arm | gain >= 15 % on both | gain above seed SD | nothing else changes | latency < 0.1 ms | **passes** |
|---|---|---|---|---|---|
| arm 1, residual limiter network | yes | yes | yes | no | **no** |
| arm 2, control: own network, weight 1.5, 100 epochs | no | no | yes | yes | **no** |

Arm 2 gets -14 % of the gain of arm 1 on R_limiter, -3 % of the gain of arm 1 on Z_limiter.

**Winner by the rule: nobody, `cand` stays.**

## Post hoc latency under the amended criterion 4 (5 runs at normal priority, each run measures the three arms one after the other)

| run | load average (1, 5, 15 min) | cand (ms) | arm 1 (ms) | arm 2 (ms) | arm 1 p99 (ms) |
|---:|---|---:|---:|---:|---:|
| 1 | [8.3, 9.4, 9.0] | 0.0301 | 0.0929 | 0.0298 | 0.326 |
| 2 | [8.3, 9.4, 9.0] | 0.0290 | 0.0872 | 0.0293 | 0.292 |
| 3 | [8.3, 9.4, 9.0] | 0.0290 | 0.0871 | 0.0283 | 0.304 |
| 4 | [8.4, 9.4, 9.0] | 0.0290 | 0.0862 | 0.0299 | 0.351 |
| 5 | [8.4, 9.4, 9.0] | 0.0304 | 0.0982 | 0.0296 | 0.316 |
| **median of the 5 runs** | | **0.0290** | **0.0872** | **0.0296** | |

Amended criterion 4: median latency of arm 1 over the runs 0.0872 ms against the limit 0.1 ms: **passes**; arm 1 costs 3.0 times as much as `cand` (0.0872 against 0.0290 ms). Criteria 1 to 3 hold as before, so arm 1 passes the amended rule (**post hoc**); the formal verdict of the original rule above is unchanged.

## Reading

- **Two verdicts, both kept.** By the original rule as written: nobody wins (arm 1 failed criterion 4 in the two `nice` runs, 0.117 and 0.108 ms). By the post hoc amended criterion 4 (5 runs at normal priority, median 0.087 ms): arm 1 passes all four criteria. The amendment was made after the first result was known and is marked as such above; it was written and pushed before the new measurements and the locked scoring.
- **Development (119 discharges, 5 folds x 3 seeds):** `R_limiter` 4.85 to 2.98 mm and `Z_limiter` 12.2 to 7.44 mm (39 % both), gain 1.9 and 4.8 mm against seed SDs of 0.14 to 0.45 mm. **Locked 30 discharges, scored once, seed 0:** `R_limiter` 4.55 to 3.26 mm (-28 %) and `Z_limiter` 8.35 to 5.55 mm (-34 %). Not worse on either target, so the post hoc condition for shipping is met. The locked gain is smaller than in development (28 and 34 % against 39 %); it is one seed, and the seed SD of `cand` itself on the locked set is about 0.3 and 0.5 mm (`results/ipp1-final-seeds.md`), smaller than the gains of 1.3 and 2.8 mm.
- **What it does NOT change:** every other column is identical to `cand` (difference 0 on development and on the locked set): axis, X point, strike points, plasma current, `is_limited`, and the axis error in the limited rows (0.331 and 0.404 mm in development). The gate that decides when the limiter network answers is that of `cand`.
- **What it costs:** the limiter network is the residual network of the best search trial (width 192, depth 4 against 256-256-128), about three times the cost of `cand`'s in the limited path: median 0.087 ms against 0.029 ms (5 runs at normal priority, load average 7 to 9, Apple M5, one core, random weights), still far below the budget of 1 to 10 ms; the diverted path is unchanged (general network only, 0.015 ms). Shipping it changes the limiter network, not a hyperparameter, and would be a new recipe next to `cand`.
- **The control (arm 2) found no gain** from the loss weight 1.5 and the 100 epochs (+5 % and +1 % worse), so those two settings are not the reason; which other part of the residual network's configuration carries the gain (residual blocks, GELU, cosine schedule, Huber delta 0.36, learning rate 0.0028, weight decay 2e-6, dropout 0.05) was not isolated.
- **Limits.** The hyperparameters of the residual network come from a search that saw all 149 discharges, including the locked 30, and the design of `cand` was likewise made on all 149 (`docs/internal/review-findings-2.md`, H2); so the locked number is not clean evidence for either model, only a check that the development gain did not vanish. One configuration, one locked seed, latency of random weights.

## Locked 30 discharges, scored once (2026-10-23 20:17, winner arm1 by the POST HOC amended criterion 4, not by the original rule, trained on the 119 development discharges, seed 0)

| target | `cand` (cached) | winner | change |
|---|---:|---:|---:|
| R_limiter (mm) | 4.55 | 3.26 | -28 % |
| Z_limiter (mm) | 8.35 | 5.55 | -34 % |

All other columns identical to `cand`: True. Pooled over the 8,761 rows of the 30 locked discharges (the limited rows have the target), one seed, clean inputs.
