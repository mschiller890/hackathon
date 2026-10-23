# IPP 1: improving the model (same protocol as the baseline)

## Summary of what was found (all numbers below are in the tables further down; 5 held-out folds)

Baseline = `ipp1_common.fit_mlp`, 256-256-128, 60 epochs (summary nRMSE 0.0690, R_limiter 10.73 mm, Z_limiter 22.19 mm,
R_mag_axis 0.377 mm, Z_mag_axis 0.391 mm). The re-implementation in this script (`base_mine`) gives identical numbers.

**Best configuration on clean data: `combo_long`** = general network (inputs plus differences of neighbouring coils, 46 features;
Huber loss, delta 0.5 SD; 256-256-128; **150 epochs**) + ridge regression for the plasma current + a second network of the same
kind trained **only on the limited rows** (150 epochs), used for R_limiter and Z_limiter when the general network predicts
is_limited > 0.5. Summary nRMSE 0.0575 (baseline 0.0690, -17 %); R_limiter 4.71 mm (-56 %); Z_limiter 9.70 mm (-56 %);
R_mag_axis 0.197 mm (-48 %); Z_mag_axis 0.245 mm (-37 %); plasma current 0.0346 kA (baseline 1.488 kA); better than the baseline
in 5 of 5 folds on R/Z_limiter, R/Z_mag_axis, plasma current, elongation and all three triangularities. Latency 0.14 to 0.17 ms per
sample end to end with both networks running (baseline 0.024 to 0.035 ms measured the same way); far below 1 ms.

**Caveat, important: this clean-trained model is fragile.** The neighbour differences amplify measurement noise: on the provided
noisy file the clean-trained difference models give R_mag_axis 110 mm (the baseline gives 10.2 mm). Do not use a clean-trained
difference model on real, noisy data. With noise plus drift augmentation the same recipe (`combo_diff_huber`, 60 epochs, aug) is
stable: on the clean test it beats the augmented baseline by 54 % on R_limiter, 57 % on R_mag_axis (1.905 to 0.817 mm), 43 % on
Z_mag_axis, but on the provided noisy test it is 3 to 7 % worse than the augmented baseline on most targets (better in 0 of 5 folds on most targets;
R_mag_axis 2.846 against 2.776 mm). The error on the noisy file is then set by the noise, not by the model: lane R trained on the
provided noisy file itself and got R_mag_axis 2.64 mm. So under noise no model change tested here gains anything on the
magnetic axis; the gain is on clean data and on the plasma current (4.03 against 4.70 kA on the noisy file, ridge).
The most noise-robust variants are `combo_raw` (raw inputs, aug) and `huber` (aug): about 1 % and 0 % better than the augmented
baseline on the noisy summary nRMSE, and Huber with aug takes R_limiter on the noisy file from 23.3 to 19.4 mm.
`combo_long` with aug (150 epochs on twice the rows) was NOT run: one such run would take well over the 5 minute limit on this loaded machine.
Command for later: `python -I analysis/ipp1_improve.py --run combo_long --aug --device mps`, then `--report`.

What each requested experiment did (clean data, plain training):
1. Width and depth, length, weight decay. Wider 512-512-256: summary 0.0711 (worse), Z_limiter 19.58 mm. Deeper 256x4-128: R_limiter 6.62
   mm and Z_limiter 13.41 mm (-38 % and -40 %) but R_mag_axis 0.400 mm (+6 %), summary 0.0716. Longer training (150 epochs, same net):
   the biggest single gain, summary 0.0637, R_limiter 7.75, Z_limiter 16.37, R_mag_axis 0.307. Weight decay 1e-2: no effect (0.0692).
   Weight decay 1e-1 and a 512-wide 120-epoch run are defined in the script but were not run (time).
2. Huber loss (delta 0.5): summary 0.0664, R_mag_axis 0.361, Z_limiter 19.71 mm: a small gain, and it stacks with the other changes.
   Per-target weights 3 on the limiter and magnetic-axis targets: worse (summary 0.0773, plasma current 1.90 kA).
3. Limited-only specialist, gated by the predicted is_limited (a true limited row the gate calls divertor falls back to the general
   net). Network on raw inputs: R_limiter 8.83 and Z_limiter 16.86 mm (-18 %, -24 %). LightGBM (300 trees, 63 leaves, neighbour
   differences): R_limiter 7.44, Z_limiter 11.09 mm on top of the difference network, but 0.24 to 0.54 ms per sample (called through
   Booster.predict; the scikit-learn wrapper cost about 0.5 ms more per call), and with the stronger networks the specialist network
   beats it (combo_long: 4.71 and 9.70 against 7.41 and 11.07 mm), so LightGBM is not recommended. Letting the specialist also answer
   the other limited targets helped Z_mag_axis (0.354) and hurt R_mag_axis (0.412), so only the limiter point is taken from it.
4. Ensemble of 3 seeds (ens3): summary 0.0665, R_limiter 10.78, Z_limiter 20.40, R_mag_axis 0.365, latency 3 networks (0.18 ms): a small
   gain for three times the cost; ens5 was not run. Ensembling was not combined with the best recipe (time).
5. Inputs: neighbour differences cut R_mag_axis to 0.323 mm and Z_mag_axis to 0.308 mm (-14 %, -21 %) and R_limiter to 8.84 mm, but
   worsen R_x_point (0.256 against 0.202 mm) and are the reason for the noise fragility above. A linear skip connection did nothing
   (summary 0.0708). Fitting the ridge first and training the network on the residual (frozen linear part) was clearly worse (0.0942).
   Using the ridge alone for the plasma current is the one free win: 0.0346 kA against 1.488 kA (the current is linear in the 24
   measurements), a 43 times smaller error; on the noisy file it gives 4.0 against 4.7 kA with aug.

Latency note: all latencies are end-to-end `predict` of one raw sample on a machine running about 15 jobs, so absolute values are
inflated and noisy; the re-measurement with one torch thread (`--latency`, out/ipp1-improve-latency.json) gave 0.035 ms for the
baseline, 0.14 ms for the difference network + ridge + limiter network, 0.24 ms with LightGBM.

5-fold GroupKFold by whole discharge, masked loss, `ipp1_common.score`, at least 60 epochs. Every number is the mean of the 5 held-out folds. `summary nRMSE` = mean nRMSE over the 14 targets without the limiter point (all targets except R_limiter and Z_limiter, is_limited included); the json also has the 13-target mean without is_limited. `all-16 nRMSE` adds the two limiter targets (mean over all 16); tables are sorted by it. Latency = end-to-end `predict` of one raw sample (features, standardisation, forward pass, de-standardisation), median in ms, measured on a shared, loaded machine (use it for ranking, not as a guarantee); gated rows are timed on a limited sample, i.e. both models run. Latency limit used for the recommendation: 0.2 ms.

`plain` = trained on the clean training discharges. `aug` = trained on the clean rows plus one corrupted copy (noise 0.15, drift 0.15 of the training input SD, the augmentation of `ipp1_robustness.py`), same number of epochs over twice the rows. Both are tested on the clean file and on the provided noisy file (same held-out discharges).

## Held-out clean data

| configuration | training | summary nRMSE | all-16 nRMSE | R_limiter MAE mm | Z_limiter MAE mm | R_mag_axis MAE mm | Z_mag_axis MAE mm | latency ms/sample |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| combo_diff_huber / net + ridge Ip + limiter net | aug | 0.1205 | 0.1389 | 7.68 | 15.94 | 0.817 | 0.713 | 0.1264 |
| combo_diff / net + ridge Ip + limiter net | aug | 0.1278 | 0.1451 | 8.34 | 17.49 | 0.984 | 0.812 | 0.1751 |
| combo_diff_huber / net + ridge Ip + limiter LightGBM | aug | 0.1205 | 0.1458 | 9.52 | 17.07 | 0.817 | 0.713 | 0.3675 |
| combo_diff_huber / net + ridge Ip | aug | 0.1205 | 0.1479 | 11.42 | 20.62 | 0.817 | 0.713 | 0.0620 |
| combo_diff_huber / net | aug | 0.1216 | 0.1489 | 11.42 | 20.62 | 0.817 | 0.713 | 0.0367 |
| combo_diff / net + ridge Ip | aug | 0.1278 | 0.1513 | 11.19 | 21.76 | 0.984 | 0.812 | 0.0755 |
| combo_diff / net + ridge Ip + limiter LightGBM | aug | 0.1278 | 0.1520 | 9.58 | 16.93 | 0.984 | 0.812 | 0.3250 |
| combo_diff / net | aug | 0.1293 | 0.1526 | 11.19 | 21.76 | 0.984 | 0.812 | 0.0539 |
| combo_raw / net + ridge Ip + limiter net | aug | 0.1901 | 0.2159 | 14.35 | 25.01 | 1.911 | 1.185 | 0.0684 |
| combo_raw / net + ridge Ip + limiter LightGBM | aug | 0.1901 | 0.2172 | 13.30 | 23.22 | 1.911 | 1.185 | 0.0917 |
| combo_raw / net + ridge Ip | aug | 0.1901 | 0.2195 | 16.65 | 28.41 | 1.911 | 1.185 | 0.0288 |
| combo_raw / net | aug | 0.1918 | 0.2210 | 16.65 | 28.41 | 1.911 | 1.185 | 0.0269 |
| base | aug | 0.1933 | 0.2221 | 16.62 | 27.32 | 1.905 | 1.241 | 0.0626 |
| huber | aug | 0.2018 | 0.2310 | 14.22 | 24.41 | 1.941 | 1.231 | 0.0642 |
| combo_long / net + ridge Ip + limiter net | plain | 0.0575 | 0.0730 | 4.71 | 9.70 | 0.197 | 0.245 | 0.1730 |
| combo_long / net + ridge Ip | plain | 0.0575 | 0.0741 | 4.72 | 11.55 | 0.197 | 0.245 | 0.0816 |
| combo_long / net | plain | 0.0592 | 0.0756 | 4.72 | 11.55 | 0.197 | 0.245 | 0.0746 |
| combo_deep_huber / net + ridge Ip + limiter net | plain | 0.0665 | 0.0798 | 3.42 | 7.53 | 0.258 | 0.297 | 0.1015 |
| combo_diff_huber / net + ridge Ip + limiter net | plain | 0.0644 | 0.0800 | 5.06 | 10.43 | 0.250 | 0.306 | 0.1965 |
| combo_deep_huber / net + ridge Ip | plain | 0.0665 | 0.0829 | 4.90 | 10.78 | 0.258 | 0.297 | 0.0458 |
| combo_diff / net + ridge Ip + limiter net | plain | 0.0671 | 0.0832 | 5.73 | 11.66 | 0.323 | 0.308 | 0.1775 |
| combo_long / net + ridge Ip + limiter LightGBM | plain | 0.0575 | 0.0838 | 7.41 | 11.07 | 0.197 | 0.245 | 0.3292 |
| combo_deep_huber / net | plain | 0.0688 | 0.0849 | 4.90 | 10.78 | 0.258 | 0.297 | 0.0805 |
| long150 | plain | 0.0637 | 0.0859 | 7.75 | 16.37 | 0.307 | 0.331 | 0.0317 |
| combo_diff_huber / net + ridge Ip | plain | 0.0644 | 0.0880 | 7.79 | 15.89 | 0.250 | 0.306 | 0.0863 |
| combo_diff_huber / net | plain | 0.0659 | 0.0893 | 7.79 | 15.89 | 0.250 | 0.306 | 0.0760 |
| combo_diff_huber / net + ridge Ip + limiter LightGBM | plain | 0.0644 | 0.0901 | 7.44 | 11.12 | 0.250 | 0.306 | 0.5387 |
| deep | plain | 0.0716 | 0.0906 | 6.62 | 13.41 | 0.400 | 0.386 | 0.0943 |
| gate_nn / all limited targets from specialist | plain | 0.0680 | 0.0919 | 8.83 | 16.86 | 0.412 | 0.354 | 0.1199 |
| combo_deep_huber / net + ridge Ip + limiter LightGBM | plain | 0.0665 | 0.0919 | 7.44 | 11.11 | 0.258 | 0.297 | 0.3660 |
| combo_diff / net + ridge Ip | plain | 0.0671 | 0.0922 | 8.84 | 17.79 | 0.323 | 0.308 | 0.0791 |
| combo_diff / net + ridge Ip + limiter LightGBM | plain | 0.0671 | 0.0923 | 7.44 | 11.09 | 0.323 | 0.308 | 0.4338 |
| gate_nn / limiter point from specialist | plain | 0.0690 | 0.0928 | 8.83 | 16.86 | 0.377 | 0.391 | 0.1272 |
| combo_diff / net | plain | 0.0692 | 0.0940 | 8.84 | 17.79 | 0.323 | 0.308 | 0.0752 |
| diff | plain | 0.0692 | 0.0940 | 8.84 | 17.79 | 0.323 | 0.308 | 0.0512 |
| ens3 | plain | 0.0665 | 0.0956 | 10.78 | 20.40 | 0.365 | 0.325 | 0.1826 |
| huber | plain | 0.0664 | 0.0963 | 10.37 | 19.71 | 0.361 | 0.385 | 0.0598 |
| base | plain | 0.0690 | 0.0971 | 10.73 | 22.19 | 0.377 | 0.391 | 0.0238 |
| base_mine | plain | 0.0690 | 0.0971 | 10.73 | 22.19 | 0.377 | 0.391 | 0.0477 |
| gate_nn / general only | plain | 0.0690 | 0.0971 | 10.73 | 22.19 | 0.377 | 0.391 | 0.0456 |
| wd1e-2 | plain | 0.0692 | 0.0979 | 11.09 | 22.37 | 0.386 | 0.397 | 0.0586 |
| wide | plain | 0.0711 | 0.0989 | 10.44 | 19.58 | 0.364 | 0.373 | 0.0685 |
| lin | plain | 0.0708 | 0.1001 | 11.80 | 22.20 | 0.370 | 0.407 | 0.0271 |
| weights | plain | 0.0773 | 0.1030 | 10.45 | 19.49 | 0.386 | 0.368 | 0.0574 |
| resid | plain | 0.0942 | 0.1207 | 13.24 | 21.43 | 0.698 | 0.439 | 0.0615 |

## Held-out provided noisy data

| configuration | training | summary nRMSE | all-16 nRMSE | R_limiter MAE mm | Z_limiter MAE mm | R_mag_axis MAE mm | Z_mag_axis MAE mm | latency ms/sample |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| combo_raw / net + ridge Ip | aug | 0.2715 | 0.3072 | 23.23 | 39.80 | 2.761 | 2.106 | 0.0288 |
| combo_raw / net | aug | 0.2723 | 0.3079 | 23.23 | 39.80 | 2.761 | 2.106 | 0.0269 |
| combo_raw / net + ridge Ip + limiter LightGBM | aug | 0.2715 | 0.3083 | 23.96 | 40.83 | 2.761 | 2.106 | 0.0917 |
| base | aug | 0.2744 | 0.3099 | 23.30 | 38.76 | 2.776 | 2.152 | 0.0626 |
| huber | aug | 0.2744 | 0.3101 | 19.37 | 36.78 | 2.634 | 2.110 | 0.0642 |
| combo_raw / net + ridge Ip + limiter net | aug | 0.2715 | 0.3108 | 24.15 | 40.57 | 2.761 | 2.106 | 0.0684 |
| combo_diff_huber / net + ridge Ip + limiter LightGBM | aug | 0.2828 | 0.3187 | 24.43 | 41.79 | 2.846 | 2.245 | 0.3675 |
| combo_diff_huber / net + ridge Ip | aug | 0.2828 | 0.3212 | 21.20 | 40.19 | 2.846 | 2.245 | 0.0620 |
| combo_diff_huber / net | aug | 0.2834 | 0.3217 | 21.20 | 40.19 | 2.846 | 2.245 | 0.0367 |
| combo_diff / net + ridge Ip + limiter LightGBM | aug | 0.2871 | 0.3224 | 24.44 | 41.73 | 3.019 | 2.299 | 0.3250 |
| combo_diff / net + ridge Ip | aug | 0.2871 | 0.3253 | 24.99 | 42.34 | 3.019 | 2.299 | 0.0755 |
| combo_diff / net | aug | 0.2882 | 0.3262 | 24.99 | 42.34 | 3.019 | 2.299 | 0.0539 |
| combo_diff_huber / net + ridge Ip + limiter net | aug | 0.2828 | 0.3278 | 24.16 | 45.67 | 2.846 | 2.245 | 0.1264 |
| combo_diff / net + ridge Ip + limiter net | aug | 0.2871 | 0.3340 | 26.66 | 48.71 | 3.019 | 2.299 | 0.1751 |
| ens3 | plain | 0.4570 | 0.5145 | 45.39 | 58.59 | 10.150 | 3.992 | 0.1826 |
| deep | plain | 0.4571 | 0.5167 | 43.69 | 52.72 | 9.560 | 3.867 | 0.0943 |
| huber | plain | 0.4641 | 0.5179 | 40.98 | 59.39 | 10.038 | 4.220 | 0.0598 |
| wd1e-2 | plain | 0.4628 | 0.5211 | 46.76 | 62.05 | 10.118 | 4.113 | 0.0586 |
| wide | plain | 0.4585 | 0.5216 | 49.22 | 59.15 | 10.065 | 3.903 | 0.0685 |
| base | plain | 0.4646 | 0.5231 | 46.82 | 62.62 | 10.150 | 4.119 | 0.0238 |
| base_mine | plain | 0.4646 | 0.5231 | 46.82 | 62.62 | 10.150 | 4.119 | 0.0477 |
| gate_nn / general only | plain | 0.4646 | 0.5231 | 46.82 | 62.62 | 10.150 | 4.119 | 0.0456 |
| long150 | plain | 0.4620 | 0.5250 | 48.17 | 59.68 | 10.043 | 3.962 | 0.0317 |
| gate_nn / limiter point from specialist | plain | 0.4646 | 0.5286 | 47.72 | 58.72 | 10.150 | 4.119 | 0.1272 |
| weights | plain | 0.4668 | 0.5293 | 49.55 | 61.78 | 10.065 | 4.047 | 0.0574 |
| lin | plain | 0.4709 | 0.5296 | 49.99 | 62.53 | 10.139 | 4.199 | 0.0271 |
| gate_nn / all limited targets from specialist | plain | 0.4683 | 0.5318 | 47.72 | 58.72 | 10.511 | 4.037 | 0.1199 |
| resid | plain | 1.7846 | 1.8618 | 157.69 | 307.63 | 27.358 | 16.777 | 0.0615 |
| combo_deep_huber / net + ridge Ip + limiter LightGBM | plain | 9.1158 | 8.2370 | 177.05 | 143.31 | 81.615 | 254.454 | 0.3660 |
| combo_diff / net + ridge Ip + limiter LightGBM | plain | 9.5623 | 9.2128 | 479.72 | 381.98 | 112.841 | 208.308 | 0.4338 |
| combo_deep_huber / net + ridge Ip | plain | 9.1158 | 9.3302 | 1007.94 | 804.37 | 81.615 | 254.454 | 0.0458 |
| combo_long / net + ridge Ip + limiter LightGBM | plain | 10.4981 | 9.3764 | 129.80 | 135.97 | 110.330 | 204.181 | 0.3292 |
| combo_deep_huber / net + ridge Ip + limiter net | plain | 9.1158 | 9.8816 | 1141.28 | 1498.24 | 81.615 | 254.454 | 0.1015 |
| combo_diff_huber / net + ridge Ip + limiter LightGBM | plain | 10.8869 | 10.0515 | 285.43 | 345.54 | 128.024 | 246.679 | 0.5387 |
| combo_deep_huber / net | plain | 9.9446 | 10.0554 | 1007.94 | 804.37 | 81.615 | 254.454 | 0.0805 |
| combo_diff / net + ridge Ip | plain | 9.5623 | 10.1396 | 1250.17 | 1018.45 | 112.841 | 208.308 | 0.0791 |
| combo_diff / net | plain | 9.8975 | 10.4329 | 1250.17 | 1018.45 | 112.841 | 208.308 | 0.0752 |
| diff | plain | 9.8975 | 10.4329 | 1250.17 | 1018.45 | 112.841 | 208.308 | 0.0512 |
| combo_diff / net + ridge Ip + limiter net | plain | 9.5623 | 10.5275 | 1542.63 | 1216.70 | 112.841 | 208.308 | 0.1775 |
| combo_long / net + ridge Ip | plain | 10.4981 | 10.5970 | 982.10 | 915.68 | 110.330 | 204.181 | 0.0816 |
| combo_diff_huber / net + ridge Ip | plain | 10.8869 | 10.7031 | 609.80 | 986.37 | 128.024 | 246.679 | 0.0863 |
| combo_diff_huber / net + ridge Ip + limiter net | plain | 10.8869 | 10.8070 | 866.59 | 786.16 | 128.024 | 246.679 | 0.1965 |
| combo_long / net | plain | 10.9772 | 11.0162 | 982.10 | 915.68 | 110.330 | 204.181 | 0.0746 |
| combo_diff_huber / net | plain | 11.2821 | 11.0489 | 609.80 | 986.37 | 128.024 | 246.679 | 0.0760 |
| combo_long / net + ridge Ip + limiter net | plain | 10.4981 | 11.2609 | 1417.10 | 961.61 | 110.330 | 204.181 | 0.1730 |

## Recommendation (latency within the limit, ranked by the all-16 nRMSE)

- trained on clean data, best on clean test: **combo_long / net + ridge Ip + limiter net** (as combo_diff_huber, 150 epochs for the general network and for the limiter network); summary nRMSE clean 0.0575, noisy 10.4981 (all-16 clean 0.0730, noisy 11.2609), latency 0.1730 ms.
- trained on clean data, best on noisy test: **ens3** (ensemble of 3 seeds, baseline recipe); summary nRMSE clean 0.0665, noisy 0.4570 (all-16 clean 0.0956, noisy 0.5145), latency 0.1826 ms.
- trained with noise plus drift augmentation, best on clean test: **combo_diff_huber / net + ridge Ip + limiter net** (as combo_diff with Huber loss (delta 0.5) in the networks); summary nRMSE clean 0.1205, noisy 0.2828 (all-16 clean 0.1389, noisy 0.3278), latency 0.1264 ms.
- trained with noise plus drift augmentation, best on noisy test: **combo_raw / net + ridge Ip** (raw inputs; ridge for plasma current; limited-row specialist (network or LightGBM) for the limiter point); summary nRMSE clean 0.1901, noisy 0.2715 (all-16 clean 0.2195, noisy 0.3072), latency 0.0288 ms.

## Per-target: combo_long / net + ridge Ip + limiter net (plain) against the baseline recipe (plain), clean test

| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 1.488 | 0.03455 | -98 % | 0.0271 | 0.0004 | 5 |
| R_mag_axis | mm | 0.3772 | 0.1973 | -48 % | 0.1394 | 0.1023 | 5 |
| Z_mag_axis | mm | 0.3915 | 0.245 | -37 % | 0.1069 | 0.0879 | 5 |
| elongation |  | 0.00569 | 0.003402 | -40 % | 0.0408 | 0.0349 | 5 |
| triangularity |  | 0.002844 | 0.001725 | -39 % | 0.0483 | 0.0394 | 5 |
| triangularity_upper |  | 0.002966 | 0.001837 | -38 % | 0.0797 | 0.0488 | 5 |
| triangularity_lower |  | 0.003679 | 0.002337 | -36 % | 0.0440 | 0.0384 | 5 |
| R_x_point | mm | 0.2024 | 0.1795 | -11 % | 0.0673 | 0.0666 | 4 |
| Z_x_point | mm | 0.1952 | 0.1293 | -34 % | 0.0387 | 0.0338 | 4 |
| R_strike_point_1 | mm | 0.2646 | 0.1733 | -35 % | 0.0509 | 0.0390 | 5 |
| Z_strike_point_1 | mm | 0.1307 | 0.07795 | -40 % | 0.0666 | 0.0521 | 5 |
| R_strike_point_2 | mm | 0.2281 | 0.1746 | -23 % | 0.0447 | 0.0485 | 4 |
| Z_strike_point_2 | mm | 0.05517 | 0.04388 | -20 % | 0.0681 | 0.0683 | 4 |
| R_limiter | mm | 10.73 | 4.711 | -56 % | 0.3170 | 0.1965 | 5 |
| Z_limiter | mm | 22.19 | 9.696 | -56 % | 0.2702 | 0.1668 | 5 |
| is_limited |  | 0.02027 | 0.0141 | -30 % | 0.1440 | 0.1449 | 5 |

## Per-target: combo_long / net + ridge Ip + limiter net (plain) against the baseline recipe (plain), provided noisy test

| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 6.01 | 4.399 | -27 % | 0.0740 | 0.0499 | 5 |
| R_mag_axis | mm | 10.15 | 110.3 | +987 % | 1.9144 | 17.5377 | 0 |
| Z_mag_axis | mm | 4.119 | 204.2 | +4857 % | 0.4314 | 19.5168 | 0 |
| elongation |  | 0.03182 | 1.116 | +3407 % | 0.1675 | 5.6246 | 0 |
| triangularity |  | 0.01824 | 0.6474 | +3449 % | 0.2178 | 7.3768 | 0 |
| triangularity_upper |  | 0.02582 | 1.152 | +4364 % | 0.4885 | 19.7040 | 0 |
| triangularity_lower |  | 0.02289 | 1.049 | +4483 % | 0.1911 | 7.8995 | 0 |
| R_x_point | mm | 4.401 | 39.45 | +797 % | 0.7184 | 6.2962 | 0 |
| Z_x_point | mm | 3.168 | 107.7 | +3301 % | 0.3324 | 12.3448 | 0 |
| R_strike_point_1 | mm | 3.317 | 124.1 | +3641 % | 0.3426 | 13.5614 | 0 |
| Z_strike_point_1 | mm | 1.256 | 34.82 | +2673 % | 0.3622 | 8.8892 | 0 |
| R_strike_point_2 | mm | 4.711 | 103 | +2086 % | 0.5353 | 12.1813 | 0 |
| Z_strike_point_2 | mm | 0.8991 | 13.58 | +1411 % | 0.5098 | 8.5185 | 0 |
| R_limiter | mm | 46.82 | 1417 | +2927 % | 1.1828 | 24.4072 | 0 |
| Z_limiter | mm | 62.62 | 961.6 | +1436 % | 0.6821 | 8.7932 | 0 |
| is_limited |  | 0.04148 | 2.826 | +6713 % | 0.2194 | 7.4728 | 0 |

## Per-target: combo_diff_huber / net + ridge Ip + limiter net (aug) against the baseline recipe (aug), clean test

| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 2.004 | 0.4996 | -75 % | 0.0321 | 0.0057 | 5 |
| R_mag_axis | mm | 1.905 | 0.8165 | -57 % | 0.4754 | 0.2732 | 5 |
| Z_mag_axis | mm | 1.241 | 0.7129 | -43 % | 0.2147 | 0.1409 | 5 |
| elongation |  | 0.01239 | 0.008357 | -33 % | 0.0823 | 0.0633 | 5 |
| triangularity |  | 0.00598 | 0.003786 | -37 % | 0.0925 | 0.0645 | 5 |
| triangularity_upper |  | 0.005991 | 0.003879 | -35 % | 0.1507 | 0.1032 | 5 |
| triangularity_lower |  | 0.008002 | 0.005083 | -36 % | 0.0879 | 0.0600 | 5 |
| R_x_point | mm | 1.523 | 0.6643 | -56 % | 0.3451 | 0.1987 | 5 |
| Z_x_point | mm | 1.286 | 0.5471 | -57 % | 0.1744 | 0.0984 | 5 |
| R_strike_point_1 | mm | 1.125 | 0.5455 | -52 % | 0.1437 | 0.0947 | 5 |
| Z_strike_point_1 | mm | 0.4886 | 0.2441 | -50 % | 0.1966 | 0.1166 | 5 |
| R_strike_point_2 | mm | 1.816 | 0.7838 | -57 % | 0.2876 | 0.1609 | 5 |
| Z_strike_point_2 | mm | 0.3462 | 0.1607 | -54 % | 0.2596 | 0.1556 | 5 |
| R_limiter | mm | 16.62 | 7.68 | -54 % | 0.4824 | 0.2923 | 5 |
| Z_limiter | mm | 27.32 | 15.94 | -42 % | 0.3649 | 0.2432 | 5 |
| is_limited |  | 0.02414 | 0.01882 | -22 % | 0.1642 | 0.1511 | 5 |

## Per-target: combo_diff_huber / net + ridge Ip + limiter net (aug) against the baseline recipe (aug), provided noisy test

| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| plasma_current | kA | 4.702 | 4.026 | -14 % | 0.0574 | 0.0456 | 5 |
| R_mag_axis | mm | 2.776 | 2.846 | +3 % | 0.6857 | 0.7098 | 0 |
| Z_mag_axis | mm | 2.152 | 2.245 | +4 % | 0.2896 | 0.2911 | 0 |
| elongation |  | 0.02025 | 0.02129 | +5 % | 0.1226 | 0.1314 | 0 |
| triangularity |  | 0.01035 | 0.01082 | +5 % | 0.1365 | 0.1438 | 0 |
| triangularity_upper |  | 0.01036 | 0.01075 | +4 % | 0.2251 | 0.2372 | 0 |
| triangularity_lower |  | 0.014 | 0.01453 | +4 % | 0.1278 | 0.1330 | 0 |
| R_x_point | mm | 2.44 | 2.542 | +4 % | 0.4569 | 0.4627 | 0 |
| Z_x_point | mm | 2.319 | 2.485 | +7 % | 0.2684 | 0.2834 | 0 |
| R_strike_point_1 | mm | 2.288 | 2.439 | +7 % | 0.2491 | 0.2641 | 0 |
| Z_strike_point_1 | mm | 0.9075 | 0.9529 | +5 % | 0.2887 | 0.2916 | 1 |
| R_strike_point_2 | mm | 2.933 | 3.1 | +6 % | 0.3838 | 0.3923 | 0 |
| Z_strike_point_2 | mm | 0.557 | 0.5916 | +6 % | 0.3510 | 0.3674 | 0 |
| R_limiter | mm | 23.3 | 24.16 | +4 % | 0.6286 | 0.7209 | 1 |
| Z_limiter | mm | 38.76 | 45.67 | +18 % | 0.4880 | 0.5657 | 0 |
| is_limited |  | 0.03269 | 0.0306 | -6 % | 0.1985 | 0.2053 | 5 |
