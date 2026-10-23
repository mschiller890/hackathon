# IPP 1: does the activation function matter? SiLU against ReLU and GELU, protocol written before the run

**Why.** The owner asked "did you try ReLU?" The honest answer was no: the shipped networks use SiLU and no other activation was compared. This is a small paired check, on development discharges only. The locked test set (`results/ipp1-locked-test-ids.txt`) is not read and nothing here changes the shipped model.

## Fixed in advance (this text was committed before the first run of `analysis/ipp1_activation.py`)

**What is compared.** The general network of the shipped recipe `cand` (`analysis/ipp1_final.py`, `fit_net`): inputs and differences of neighbouring coils (46 columns), layers 256-256-128, Huber loss (delta 0.5), AdamW (learning rate 2e-3, weight decay 1e-4), one-cycle schedule (maximum 3e-3), batch 512, 150 epochs. Only the activation after each hidden layer changes: **SiLU** (as shipped, the control), **ReLU**, **GELU**. The plasma current ridge and the limiter network of `cand` are not part of this test (the networks alone are compared, so the plasma current and the limiter point come from the general network in all three arms). The script imports `ipp1_final.py` and swaps its `MLP` class; `ipp1_final.py` is not changed.

**Data and folds.** The 119 development discharges (the 30 locked ones are excluded by the same `split` as the shipped recipe). 5 folds by whole discharge, the same `group_folds` assignment as the cross-validation of `ipp1_final.py`.

**Seeds and pairing.** 3 seeds (0, 1, 2); the seed of fold k is k + 10 x seed, so seed 0 is the seed of the shipped recipe. For one seed and fold all three activations have the same training rows, batch order and (because the layers are built in the same order) the same initial weights: the comparison is paired. 45 networks in all.

**Metrics.** From the out-of-fold predictions pooled over the 5 folds (all development rows), per seed, then mean and SD over the 3 seeds:
- MAE in mm for `R_mag_axis`, `Z_mag_axis`, `R_x_point`, `R_strike_point_1`, and the MAE of `elongation` (dimensionless);
- `axis` = the mean of the MAE of `R_mag_axis` and `Z_mag_axis` (the "pooled axis");
- `nrmse16` = the mean over all 16 targets of RMSE / SD of the target (the project's ranking number, `ipp1_final.all16`); it is the "16-target mean";
- the axis MAE per polarity group: reversed (discharges with a positive median reference plasma current, 14 in the development set) against usual (the rest), as `analysis/ipp1_confidence.py`;
- the paired difference to SiLU (activation minus SiLU, same seed) with its SD over the seeds.

**Verdict rule.** **SiLU stays** unless ReLU or GELU is better than SiLU (lower) by MORE than the SD over the 3 seeds of SiLU itself, on BOTH `axis` and `nrmse16` (comparing the means over the seeds). The verdict is written plainly whichever way it falls.

**Sanity check.** The SiLU control of seed 0 must reproduce the cached out-of-fold predictions of the shipped recipe (`cv_cand_*` of `ipp1_final.py`) on the 13 columns that the plasma current ridge and the limiter gate do not change (small differences from thread non-determinism are expected, large ones would mean the swap is wrong).

## What this cannot show

Three seeds are a rough estimate of the seed SD; only the general network is tested, not the whole shipped pair; the width, learning rate and epochs were tuned for SiLU and not re-tuned for ReLU or GELU, so a small advantage of SiLU is partly an advantage of its tuning; the targets are the institute's reference reconstruction; nothing here is a statement about the locked test set.

<!-- RESULTS BELOW -->

## Results

Out-of-fold predictions of the general network on the 119 development discharges, pooled over the 5 folds; mean over the 3 seeds, and the SD over the 3 seeds in brackets. MAE in mm; `nrmse16` = mean over the 16 targets of RMSE / SD of the target (dimensionless). `axis` = mean of the MAE of R_mag_axis and Z_mag_axis. Reversed polarity = 14 development discharges, usual = 105.

| quantity | SiLU (shipped) | ReLU | GELU |
|---|---:|---:|---:|
| axis | 0.2748 (0.01) | 0.3478 (0.0075) | 0.2831 (0.016) |
| R_mag_axis | 0.2472 (0.015) | 0.3341 (0.02) | 0.2482 (0.0071) |
| Z_mag_axis | 0.3025 (0.034) | 0.3615 (0.013) | 0.318 (0.028) |
| R_x_point | 0.2212 (0.016) | 0.28 (0.039) | 0.2262 (0.033) |
| R_strike_point_1 | 0.2157 (0.012) | 0.3071 (0.024) | 0.1882 (0.022) |
| elongation | 0.003954 (0.00017) | 0.005308 (0.00014) | 0.003734 (6.5e-05) |
| axis, reversed | 1.428 (0.063) | 1.5 (0.11) | 1.472 (0.14) |
| axis, usual | 0.1801 (0.0076) | 0.2532 (0.0029) | 0.1855 (0.016) |
| nrmse16 | 0.09617 (0.0034) | 0.1103 (0.0087) | 0.09289 (0.0013) |

Paired difference to SiLU (activation minus SiLU, same seed, folds and initial weights), mean over the 3 seeds and its SD; negative = better than SiLU.

| quantity | ReLU minus SiLU | GELU minus SiLU |
|---|---:|---:|
| axis | +0.07293 (0.0095) | +0.008267 (0.026) |
| R_mag_axis | +0.08693 (0.034) | +0.001069 (0.018) |
| Z_mag_axis | +0.05893 (0.045) | +0.01547 (0.059) |
| R_x_point | +0.05882 (0.047) | +0.004985 (0.042) |
| R_strike_point_1 | +0.09136 (0.019) | -0.02751 (0.023) |
| elongation | +0.001354 (0.00031) | -0.00022 (0.00022) |
| axis, reversed | +0.07149 (0.078) | +0.04346 (0.21) |
| axis, usual | +0.07305 (0.0048) | +0.005377 (0.021) |
| nrmse16 | +0.0141 (0.012) | -0.003279 (0.0044) |

**Verdict: SiLU stays.**

Rule (fixed in advance): SiLU stays unless another activation beats SiLU by more than the SD over the 3 seeds of SiLU itself, on BOTH `axis` and `nrmse16`.

Check: the SiLU control of seed 0 against the cached out-of-fold predictions of the shipped recipe (`cv_cand_*`), on the 13 columns that the plasma current ridge and the limiter gate do not change: largest absolute difference 0 (raw units).

## Reading

SiLU stays. ReLU is worse on almost everything: the axis MAE is 0.348 mm against 0.275 mm for SiLU (+0.073 mm, paired, in all 3 seeds more than the seed SD of 0.010 mm), and the 16-target mean nRMSE is 0.110 against 0.096. GELU is indistinguishable from SiLU on the axis (0.283 against 0.275 mm, the paired difference +0.008 mm is smaller than its own seed SD of 0.026 mm); on the 16-target mean it is slightly lower (0.0929 against 0.0962, paired difference -0.0033 with SD 0.0044) and on R_strike_point_1 and elongation it is lower by about one paired SD, so GELU does not win on both asked quantities and the rule keeps SiLU. For the reversed-polarity group (14 discharges) the axis MAE is about 1.4 to 1.5 mm for all three and the seed spread (0.06 to 0.14 mm) is larger than the differences. The SiLU control of seed 0 reproduces the cached out-of-fold predictions of the shipped recipe exactly (largest difference 0 on the 13 unchanged columns), so the swap of the class is correct.

Wording for the pitch answer: "We compared SiLU with ReLU and GELU in the same network on the development discharges, 3 seeds, paired: ReLU was clearly worse (axis error 0.35 against 0.27 mm), GELU was within the seed spread, so we kept SiLU."
