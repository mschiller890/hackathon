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
