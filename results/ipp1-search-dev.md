# IPP 1: the architecture of the cloud search against `cand`, on the development discharges only

Script `analysis/ipp1_search_dev.py`; protocol and the **decision rule written before the first result** are in its docstring. The cloud search saw all 149 discharges, so nothing here uses the locked 30; this is 5-fold cross-validation by discharge inside the 119 development discharges, 3 seeds per fold (3 x 5 = 15 trainings per model), masked loss, the 46 inputs of `cand`. Both the search and the design of `cand` used these discharges, so the comparison is fair between them but optimistic for both.

Configurations (hyperparameters of `results/cloud-search.json`):

| name | from fold | inner objective | arch | width | depth | act | dropout | lr | wd | epochs | batch | sched | loss | delta | w_lim | w_cls |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|
| resA | 0 | 0.0814 | resmlp | 192 | 4 | gelu | 0.05 | 0.0028 | 2e-06 | 100 | 512 | cosine | huber | 0.36 | 1.5 | 1 |
| resB | 1 | 0.0923 | resmlp | 256 | 3 | mish | 0.05 | 0.0012 | 1.2e-06 | 50 | 512 | cosine | huber | 0.5 | 1.7 | 0.78 |

`cand`: general MLP 256-256-128 + ridge for plasma_current + limiter network, gated (`analysis/ipp1_final.py`); `*_pipe`: the same pipeline with the residual network in place of both networks; `*_alone`: the residual network alone for all 16 targets (what the search measured). Seed 0 of `cand` is the cached cross-validation of `ipp1_final.py`.

## all development rows (119 discharges): MAE, mean (SD over 3 seeds); unit mm, plasma current in kA

| target | unit | cand | resA_pipe | resA_alone | resB_pipe | resB_alone | resA_pipe / cand |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 0.0332 (0) | 0.0332 (0) | 0.784 (0.081) | 0.0332 (0) | 1.1 (0.086) | 1.00 |
| R_mag_axis | mm | 0.247 (0.015) | 0.298 (0.012) | 0.298 (0.012) | 0.317 (0.0097) | 0.317 (0.0097) | 1.20 |
| Z_mag_axis | mm | 0.303 (0.034) | 0.309 (0.016) | 0.309 (0.016) | 0.368 (0.0014) | 0.368 (0.0014) | 1.02 |
| R_x_point | mm | 0.221 (0.016) | 0.193 (0.02) | 0.193 (0.02) | 0.219 (0.0082) | 0.219 (0.0082) | 0.87 |
| Z_x_point | mm | 0.211 (0.014) | 0.281 (0.039) | 0.281 (0.039) | 0.299 (0.0076) | 0.299 (0.0076) | 1.33 |
| R_strike_point_1 | mm | 0.216 (0.012) | 0.26 (0.051) | 0.26 (0.051) | 0.316 (0.018) | 0.316 (0.018) | 1.20 |
| Z_strike_point_1 | mm | 0.107 (0.009) | 0.126 (0.015) | 0.126 (0.015) | 0.132 (0.0052) | 0.132 (0.0052) | 1.18 |
| R_strike_point_2 | mm | 0.258 (0.02) | 0.244 (0.022) | 0.244 (0.022) | 0.279 (0.012) | 0.279 (0.012) | 0.94 |
| Z_strike_point_2 | mm | 0.05 (0.0041) | 0.0541 (0.0025) | 0.0541 (0.0025) | 0.065 (0.0029) | 0.065 (0.0029) | 1.08 |
| R_limiter | mm | 4.85 (0.25) | 2.97 (0.14) | 3.55 (0.49) | 4.67 (0.19) | 5.68 (0.38) | 0.61 |
| Z_limiter | mm | 12.2 (0.45) | 7.44 (0.4) | 9.31 (0.72) | 11.2 (0.19) | 12.7 (0.83) | 0.61 |
| **relative score** (mean of MAE / target SD over the 11 targets) | | 0.0286 (0.00073) | 0.0252 (0.0013) | 0.0275 (0.0015) | 0.0315 (0.00032) | 0.0343 (0.00041) | 0.88 |

## negative plasma current (105 discharges): MAE, mean (SD over 3 seeds); unit mm, plasma current in kA

| target | unit | cand | resA_pipe | resA_alone | resB_pipe | resB_alone | resA_pipe / cand |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 0.0324 (0) | 0.0324 (0) | 0.618 (0.043) | 0.0324 (0) | 0.965 (0.036) | 1.00 |
| R_mag_axis | mm | 0.154 (0.008) | 0.211 (0.02) | 0.211 (0.02) | 0.213 (0.0085) | 0.213 (0.0085) | 1.37 |
| Z_mag_axis | mm | 0.206 (0.023) | 0.204 (0.012) | 0.204 (0.012) | 0.23 (0.002) | 0.23 (0.002) | 0.99 |
| R_x_point | mm | 0.11 (0.0023) | 0.0949 (0.00089) | 0.0949 (0.00089) | 0.13 (0.0072) | 0.13 (0.0072) | 0.86 |
| Z_x_point | mm | 0.116 (0.0073) | 0.124 (0.0054) | 0.124 (0.0054) | 0.157 (0.01) | 0.157 (0.01) | 1.07 |
| R_strike_point_1 | mm | 0.136 (0.0082) | 0.131 (0.0041) | 0.131 (0.0041) | 0.168 (0.0099) | 0.168 (0.0099) | 0.96 |
| Z_strike_point_1 | mm | 0.0713 (0.0076) | 0.0724 (0.003) | 0.0724 (0.003) | 0.0804 (0.00036) | 0.0804 (0.00036) | 1.02 |
| R_strike_point_2 | mm | 0.112 (0.006) | 0.102 (0.0019) | 0.102 (0.0019) | 0.161 (0.011) | 0.161 (0.011) | 0.91 |
| Z_strike_point_2 | mm | 0.0253 (0.00069) | 0.0237 (0.00039) | 0.0237 (0.00039) | 0.0419 (0.0023) | 0.0419 (0.0023) | 0.94 |
| R_limiter | mm | 4.15 (0.2) | 2.49 (0.19) | 3.04 (0.52) | 4.01 (0.2) | 5.05 (0.44) | 0.60 |
| Z_limiter | mm | 10.9 (0.45) | 5.83 (0.46) | 7.67 (0.76) | 9.6 (0.12) | 11.3 (0.81) | 0.53 |
| **relative score** (mean of MAE / target SD over the 11 targets) | | 0.0201 (0.00067) | 0.0157 (0.00013) | 0.0178 (0.001) | 0.0219 (0.00031) | 0.0248 (0.00028) | 0.78 |

## positive plasma current (14 discharges): MAE, mean (SD over 3 seeds); unit mm, plasma current in kA

| target | unit | cand | resA_pipe | resA_alone | resB_pipe | resB_alone | resA_pipe / cand |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 0.0439 (0) | 0.0439 (0) | 2.81 (0.55) | 0.0439 (0) | 2.81 (0.7) | 1.00 |
| R_mag_axis | mm | 1.38 (0.17) | 1.36 (0.094) | 1.36 (0.094) | 1.59 (0.075) | 1.59 (0.075) | 0.98 |
| Z_mag_axis | mm | 1.48 (0.29) | 1.59 (0.16) | 1.59 (0.16) | 2.05 (0.034) | 2.05 (0.034) | 1.08 |
| R_x_point | mm | 1.75 (0.21) | 1.54 (0.29) | 1.54 (0.29) | 1.45 (0.043) | 1.45 (0.043) | 0.88 |
| Z_x_point | mm | 1.52 (0.11) | 2.45 (0.53) | 2.45 (0.53) | 2.25 (0.081) | 2.25 (0.081) | 1.61 |
| R_strike_point_1 | mm | 1.31 (0.19) | 2.04 (0.74) | 2.04 (0.74) | 2.37 (0.27) | 2.37 (0.27) | 1.55 |
| Z_strike_point_1 | mm | 0.601 (0.23) | 0.864 (0.2) | 0.864 (0.2) | 0.849 (0.08) | 0.849 (0.08) | 1.44 |
| R_strike_point_2 | mm | 2.29 (0.36) | 2.21 (0.3) | 2.21 (0.3) | 1.91 (0.17) | 1.91 (0.17) | 0.96 |
| Z_strike_point_2 | mm | 0.391 (0.062) | 0.474 (0.037) | 0.474 (0.037) | 0.385 (0.03) | 0.385 (0.03) | 1.21 |
| R_limiter | mm | 12.3 (0.86) | 8 (0.44) | 8.98 (0.34) | 11.7 (0.1) | 12.3 (0.45) | 0.65 |
| Z_limiter | mm | 26.4 (2.5) | 24.5 (0.71) | 26.7 (0.44) | 28.4 (0.96) | 27.4 (1.1) | 0.93 |
| **relative score** (mean of MAE / target SD over the 11 targets) | | 0.138 (0.0083) | 0.15 (0.019) | 0.154 (0.017) | 0.155 (0.0027) | 0.157 (0.0037) | 1.08 |

## Decision rule and verdict

1. resA_pipe score at least 5 % below `cand`, negative-current group: 0.0157 against 0.0201 (ratio 0.78): **yes**; positive-current group: 0.1495 against 0.1379 (ratio 1.08): **no**.
2. MAE at least 5 % below `cand` on the limiter point: R_limiter ratio 0.61 (**yes**), Z_limiter ratio 0.61 (**yes**).
3. Score below `cand` in every seed (all development rows): per seed resA_pipe 0.0267, 0.0244, 0.0246 against `cand` 0.0278, 0.0288, 0.0292: **yes**.

**Verdict: DO NOT SHIP** (`resA_pipe` against `cand`). The locked 30 discharges were not used.

## Reading

- **Do not ship, by the rule written before the run.** `resA_pipe` fails criterion 1: in the 14 positive-current development discharges its score is 8 % worse than `cand` (0.150 against 0.138; the SD over its three seeds is 0.019, so that group is also noisy), although it is 22 % better in the 105 negative-current discharges. The locked 30 discharges were not used.
- **What is real in the result: the limiter point.** The residual network in the `cand` pipeline cuts the limiter error from 4.85 to 2.97 mm (`R_limiter`) and from 12.2 to 7.44 mm (`Z_limiter`), 39 % in both, with seed SD of 0.14 and 0.25 mm against a gap of 1.9 mm (`R_limiter`); the residual network alone, as the search measured it, is also better there (3.55 and 9.31 mm) but needs the ridge for the plasma current (0.784 kA alone against 0.033 kA).
- **What is not:** on the axis, X point and strike points `resA_pipe` is mostly worse than `cand` (R axis 0.298 against 0.247 mm, `Z_x_point` 0.281 against 0.211 mm; better only on `R_x_point` and `R_strike_point_2`, by 6 to 13 %). The second configuration `resB`, the trial closest to the winning choices of the choice table, is worse than `cand` on 8 of 11 targets (score 0.0315 against 0.0286), so the architecture alone does not carry the gain; the single trial `resA` does, and it had a limiter weight of 1.5 in its loss (`w_lim`) and 100 epochs.
- **Limits.** The search and the design of `cand` both used these development discharges, so the comparison is fair but optimistic for both. 3 seeds, 5 folds, one configuration per model; the positive-current group has only 14 discharges. The choice-table winners alone do not define a configuration (act, width and depth differ between the best trials of the folds), which is why two trials were run.
- **Not tested, not claimed:** swapping only the limiter network for the residual network with the hyperparameters of `resA` (the gain looks separable, but that is a new hypothesis and would need its own rule and its own run before the locked set is touched).
