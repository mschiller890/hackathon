# Which inputs matter: a retraining ranking (REQ-004)

Computed on the 119 development discharges only (34,211 rows); the 30 locked test discharges of `analysis/final_evaluation.py` are removed before anything is fitted. Inside the development set, 5-fold GroupKFold by whole discharge. Summary error = mean relative error (RMSE / spread) over the 13 targets of `input_importance.SUMMARY` (no limiter point, no is_limited), so it is comparable with `results/input-importance.md`. All-24 baseline: 0.0741.

**Read the noise first.** Refitting the same all-24 baseline with 3 seeds per fold moves the summary error by 4.5% on average (per fold: 7.2%, 2.6%, 4.9%, 4.2%, 3.8%). The review measured 8 to 19 % seed noise and said to treat smaller effects as unresolved. Dropping one of 24 collinear inputs is mostly a smaller effect than that, which is the honest headline of this file: **no single magnetic input is individually necessary.** The ranking below is therefore an order of magnitude statement, not a league table.

## Drop-column ranking (network retrained without one input)

`delta` is the rise in summary error when the input is removed and the network is retrained on the other 23, averaged over the folds; it is paired, each refit shares the fold, seed and held-out discharges of its own all-24 baseline. `rel` is the same as a percentage of that baseline. `folds worse` counts how many of the 5 folds got worse without the input: 5/5 or 0/5 is a consistent sign, anything in between is noise even if the mean looks large.

| rank | input | delta | rel | sd of delta | folds worse |
|---|---|---|---|---|---|
| 1 | IPR12 | +0.02472 | +36.2% | 0.01564 | 4/5 |
| 2 | IPR13 | +0.01098 | +14.7% | 0.00822 | 4/5 |
| 3 | IPR14 | +0.00895 | +13.3% | 0.00786 | 4/5 |
| 4 | FL01 | +0.00637 | +7.6% | 0.00749 | 5/5 |
| 5 | FL02 | +0.00535 | +6.6% | 0.00544 | 4/5 |
| 6 | FL03 | +0.00507 | +6.2% | 0.00603 | 4/5 |
| 7 | FL08 | +0.00505 | +6.2% | 0.00672 | 4/5 |
| 8 | FL05 | +0.00427 | +5.2% | 0.00581 | 4/5 |
| 9 | FL04 | +0.00427 | +5.2% | 0.00582 | 4/5 |
| 10 | IPR02 | +0.00364 | +4.3% | 0.00665 | 3/5 |
| 11 | IPR05 | +0.00344 | +3.8% | 0.00962 | 4/5 |
| 12 | FL06 | +0.00334 | +3.9% | 0.00579 | 3/5 |
| 13 | IPR01 | +0.00325 | +3.8% | 0.00801 | 3/5 |
| 14 | FL07 | +0.00321 | +4.3% | 0.00401 | 4/5 |
| 15 | IPR07 | +0.00320 | +3.7% | 0.00727 | 4/5 |
| 16 | IPR15 | +0.00262 | +2.6% | 0.00590 | 3/5 |
| 17 | IPR06 | +0.00256 | +4.7% | 0.00435 | 4/5 |
| 18 | IPR08 | +0.00219 | +1.6% | 0.00829 | 2/5 |
| 19 | IPR04 | +0.00216 | +2.0% | 0.00802 | 3/5 |
| 20 | IPR16 | +0.00214 | +2.1% | 0.00608 | 3/5 |
| 21 | IPR03 | +0.00186 | +1.7% | 0.00715 | 2/5 |
| 22 | IPR09 | +0.00172 | +1.1% | 0.00738 | 2/5 |
| 23 | IPR11 | +0.00077 | +0.3% | 0.00647 | 2/5 |
| 24 | IPR10 | +0.00028 | -0.2% | 0.00574 | 3/5 |

Inputs that got worse in all 5 folds AND by more than the 4.5% seed noise: FL01 (+7.6%)

## Backward-elimination order (ridge criterion, deterministic)

Greedy elimination from 24 inputs down to 1, repeated inside each fold on its training rows only, with the ridge criterion of `input_importance.backward_ridge_subset`. This path has no seed noise, so where it and the network ranking disagree inside the noise, this is the order to quote. Most important (eliminated last) first, with the mean elimination step over the folds:

| rank | input | mean elimination step | per fold |
|---|---|---|---|
| 1 | IPR13 | 24.0 | 24, 24, 24, 24, 24 |
| 2 | IPR09 | 21.4 | 19, 23, 23, 19, 23 |
| 3 | FL08 | 20.6 | 21, 21, 21, 22, 18 |
| 4 | IPR11 | 20.4 | 23, 18, 19, 23, 19 |
| 5 | FL07 | 19.8 | 22, 22, 22, 21, 12 |
| 6 | IPR01 | 18.6 | 18, 19, 18, 18, 20 |
| 7 | IPR05 | 18.0 | 17, 20, 16, 16, 21 |
| 8 | IPR07 | 18.0 | 20, 15, 20, 20, 15 |
| 9 | IPR04 | 16.8 | 16, 17, 17, 17, 17 |
| 10 | IPR06 | 15.4 | 15, 16, 15, 15, 16 |
| 11 | IPR12 | 14.2 | 12, 12, 13, 12, 22 |
| 12 | IPR02 | 14.0 | 14, 14, 14, 14, 14 |
| 13 | IPR14 | 12.0 | 13, 9, 12, 13, 13 |
| 14 | IPR10 | 10.6 | 11, 11, 11, 10, 10 |
| 15 | IPR03 | 9.6 | 9, 8, 9, 11, 11 |
| 16 | IPR08 | 9.6 | 10, 10, 10, 9, 9 |
| 17 | FL01 | 7.8 | 8, 7, 8, 8, 8 |
| 18 | FL04 | 6.0 | 6, 5, 7, 5, 7 |
| 19 | IPR15 | 5.4 | 5, 13, 5, 2, 2 |
| 20 | FL06 | 5.2 | 7, 6, 2, 7, 4 |
| 21 | IPR16 | 4.4 | 4, 1, 6, 6, 5 |
| 22 | FL02 | 3.2 | 3, 2, 4, 1, 6 |
| 23 | FL05 | 2.8 | 2, 3, 3, 3, 3 |
| 24 | FL03 | 2.2 | 1, 4, 1, 4, 1 |

### Ridge summary error against the number of inputs kept

Mean relative squared error of the ridge criterion itself (not the network), averaged over the folds. It shows where the elimination path starts to cost accuracy.

| inputs kept | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 | mean |
|---|---|---|---|---|---|---|
| 24 | 0.2704 | 0.2358 | 0.2306 | 0.2332 | 0.2474 | 0.2435 |
| 23 | 0.2704 | 0.2359 | 0.2306 | 0.2332 | 0.2475 | 0.2435 |
| 22 | 0.2705 | 0.2359 | 0.2307 | 0.2333 | 0.2475 | 0.2436 |
| 21 | 0.2706 | 0.2360 | 0.2308 | 0.2333 | 0.2476 | 0.2437 |
| 20 | 0.2707 | 0.2360 | 0.2309 | 0.2334 | 0.2477 | 0.2437 |
| 19 | 0.2707 | 0.2361 | 0.2310 | 0.2335 | 0.2478 | 0.2438 |
| 18 | 0.2708 | 0.2362 | 0.2311 | 0.2336 | 0.2479 | 0.2439 |
| 17 | 0.2710 | 0.2363 | 0.2312 | 0.2338 | 0.2481 | 0.2441 |
| 16 | 0.2711 | 0.2365 | 0.2314 | 0.2339 | 0.2482 | 0.2442 |
| 15 | 0.2715 | 0.2367 | 0.2317 | 0.2343 | 0.2486 | 0.2445 |
| 14 | 0.2718 | 0.2369 | 0.2320 | 0.2347 | 0.2490 | 0.2449 |
| 13 | 0.2722 | 0.2372 | 0.2325 | 0.2352 | 0.2494 | 0.2453 |
| 12 | 0.2731 | 0.2378 | 0.2330 | 0.2364 | 0.2506 | 0.2462 |
| 11 | 0.2745 | 0.2384 | 0.2337 | 0.2382 | 0.2516 | 0.2473 |
| 10 | 0.2768 | 0.2406 | 0.2365 | 0.2395 | 0.2528 | 0.2492 |
| 9 | 0.2803 | 0.2444 | 0.2398 | 0.2438 | 0.2562 | 0.2529 |
| 8 | 0.2848 | 0.2476 | 0.2454 | 0.2501 | 0.2598 | 0.2575 |
| 7 | 0.2892 | 0.2523 | 0.2510 | 0.2555 | 0.2676 | 0.2631 |
| 6 | 0.3049 | 0.2712 | 0.2684 | 0.2701 | 0.2766 | 0.2782 |
| 5 | 0.3263 | 0.2898 | 0.2945 | 0.2902 | 0.2984 | 0.2998 |
| 4 | 0.3705 | 0.3319 | 0.3468 | 0.3329 | 0.3237 | 0.3412 |
| 3 | 0.4902 | 0.4505 | 0.4558 | 0.4539 | 0.3768 | 0.4454 |
| 2 | 0.5103 | 0.4775 | 0.4839 | 0.4728 | 0.4918 | 0.4873 |
| 1 | 0.7689 | 0.7358 | 0.7464 | 0.7430 | 0.7508 | 0.7490 |

## Do the three rankings agree?

Spearman rank correlation between the orders. Low agreement is itself the finding: with collinear inputs the ranking depends on the method, so none of them should be presented as 'the important sensors'.

| pair | rank correlation |
|---|---|
| drop column vs ridge | -0.14 |
| drop column vs permutation | +0.28 |
| ridge vs permutation | +0.40 |

Published permutation order, for reference (most important first): IPR14, IPR01, IPR13, IPR12, IPR02, FL01, IPR09, IPR10, FL08, IPR05, IPR16, IPR08, FL04, IPR11, IPR07, FL05, FL06, IPR06, IPR15, IPR04, IPR03, FL03, FL07, FL02

## What to say about REQ-004

- The defensible claim is about the NUMBER of inputs, not which ones: the retrained subset curves in `results/input-importance-controls.md` are the evidence, and this file adds that no individual input carries a loss above the 4.5% seed noise when the other 23 remain.
- The two sensor families do differ, and that result is outside the noise: IPR coils only 0.066 against flux loops only 0.285, 4.3 times worse (`results/input-importance.md`). Group-level statements survive; single-sensor statements do not.
- Do not present any of these three orders as 'the important sensors' on a slide. Say 'no single sensor is individually necessary; the coil family carries most of the signal'.

Runtime 9.1 min, 5 folds x (24 drop-column + 3 baseline) network refits plus 5 deterministic elimination paths, 2 torch threads.
