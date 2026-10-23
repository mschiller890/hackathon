# Sign canonicalisation of the inputs: SHIP ONLY IF REVERSED-POLARITY DISCHARGES MATTER (REQ-007 response)

**Verdict: SHIP ONLY IF REVERSED-POLARITY DISCHARGES MATTER.**

**This is a trade, not an improvement, and it has to be presented as one.** Averaged over the 15 shape targets, canonicalisation cuts the error of the reversed-polarity rows by 64% and makes the negative-current majority 20% worse. The majority is 92% of the rows, so whether this is a win depends entirely on whether reversed-polarity discharges have to be served at all.

The aggregate `all16` improves by +33%, but that number is dominated by the heavy tail the reversed discharges produce and it overstates the benefit badly. **Never say "canonicalisation improves the model by 33%".** The honest sentence is "it removes the reversed-polarity failure mode and costs about 20% on the usual polarity".

The locked 30 is the closest thing here to a real-world estimate, because its 2 reversed discharges are a realistic share: there the whole change is worth almost nothing in aggregate and several individual targets are worse. That is the same trade seen at a realistic mixture, not a contradiction of the development result.

Tested recipe: `cand` ("candidate, plain") of `analysis/ipp1_final.py`, which is imported and not modified. 5-fold GroupKFold inside the 119 development discharges (34,211 rows), 3 seeds, paired: each canonicalised run shares the fold, the seed and the held-out discharges with the plain run it is compared against. Runtime 8.2 min, 2 torch threads.

## The indicator

`-sign(sum of IPR01..16)`, computed from the inputs alone, so it is available at inference time. Chosen on the development discharges only, out of all 24 single inputs plus the coil sum, the flux-loop sum, the all-input sum and a ridge estimate of the current.

| check | rows | agree with sign(plasma_current) | fraction |
|---|---|---|---|
| clean inputs, development rows | 34,211 | 34,211 | 1.000000 |
| provided noisy inputs, development rows | 34,211 | 34,211 | 1.000000 |

It is the only candidate perfect on BOTH the clean and the provided noisy development rows. Single coils are perfect on clean rows but flip on 0.1 to 1.7 % of noisy ones, and the flux loops carry no usable sign at all (25 to 39 % agreement), so the obvious guess of "a flux loop" does not work here.

Two facts make this safe rather than lucky: the plasma current never approaches zero in this data (smallest |plasma current| on a development row is 10.1 kA), so there is no sign ambiguity anywhere, and the coil sum stays 0.093 of its own standard deviation away from flipping at its closest approach. That margin is thin, and it is the one thing to re-check on any new campaign.

Physics sanity check: the mean gap between the two polarity groups across the 24 inputs is 2.00 input SD on raw inputs and 0.13 after canonicalisation, which confirms that the reversed rows really are the mirror image rather than a different regime.

## Development result

Mean relative error over the 16 targets (`ipp1_final.all16`), per seed group:

| variant | seeds 0 | seeds 1 | seeds 2 | mean |
|---|---|---|---|---|
| plain | 0.0912 | 0.0994 | 0.0954 | 0.0953 |
| canon | 0.0638 | 0.0639 | 0.0648 | 0.0642 |

Seed spread of the plain recipe: 3.5%. Axis gain (mean of the R and Z axis MAE ratios): +18.6%. all16 gain: +32.7%.

Pooled MAE, canonicalised divided by plain (below 1 = canonicalisation is better), overall and per polarity. The per-polarity columns are the point of the experiment: the reversed discharges are where the error lived.

| target | unit | overall | positive current | negative current |
|---|---|---|---|---|
| plasma_current | kA | 1.000 | 1.000 | 1.000 |
| R_mag_axis | mm | 0.851 | 0.326 | 1.234 |
| Z_mag_axis | mm | 0.776 | 0.366 | 0.998 |
| elongation |  | 0.820 | 0.295 | 1.063 |
| triangularity |  | 0.854 | 0.277 | 1.133 |
| triangularity_upper |  | 0.899 | 0.348 | 1.089 |
| triangularity_lower |  | 0.883 | 0.304 | 1.175 |
| R_x_point | mm | 0.642 | 0.151 | 1.363 |
| Z_x_point | mm | 0.895 | 0.442 | 1.300 |
| R_strike_point_1 | mm | 1.030 | 0.569 | 1.342 |
| Z_strike_point_1 | mm | 0.909 | 0.463 | 1.287 |
| R_strike_point_2 | mm | 0.619 | 0.142 | 1.507 |
| Z_strike_point_2 | mm | 0.776 | 0.295 | 1.286 |
| R_limiter | mm | 0.965 | 0.483 | 1.111 |
| Z_limiter | mm | 0.859 | 0.388 | 0.967 |
| is_limited |  | 1.005 | 0.523 | 1.171 |

Absolute pooled MAE per polarity, mean over the seed groups:

| target | unit | plain, positive | canon, positive | plain, negative | canon, negative |
|---|---|---|---|---|---|
| plasma_current | kA | 0.04386 | 0.04386 | 0.03236 | 0.03236 |
| R_mag_axis | mm | 1.34 | 0.4363 | 0.1508 | 0.1861 |
| Z_mag_axis | mm | 1.451 | 0.5309 | 0.2205 | 0.2201 |
| elongation |  | 0.01657 | 0.004885 | 0.00295 | 0.003135 |
| triangularity |  | 0.00913 | 0.002527 | 0.001549 | 0.001755 |
| triangularity_upper |  | 0.007014 | 0.002439 | 0.001666 | 0.001815 |
| triangularity_lower |  | 0.01326 | 0.004036 | 0.002161 | 0.002539 |
| R_x_point | mm | 2.135 | 0.3228 | 0.105 | 0.1432 |
| Z_x_point | mm | 1.333 | 0.5896 | 0.108 | 0.1405 |
| R_strike_point_1 | mm | 1.225 | 0.6973 | 0.1307 | 0.1753 |
| Z_strike_point_1 | mm | 0.7472 | 0.3463 | 0.06369 | 0.08198 |
| R_strike_point_2 | mm | 2.669 | 0.3786 | 0.1038 | 0.1564 |
| Z_strike_point_2 | mm | 0.38 | 0.112 | 0.02599 | 0.03341 |
| R_limiter | mm | 13.1 | 6.328 | 4.066 | 4.517 |
| Z_limiter | mm | 26.44 | 10.25 | 10.93 | 10.57 |
| is_limited |  | 0.05081 | 0.02659 | 0.01211 | 0.01418 |

## Locked test set, scored once

Trained on all 119 development discharges, scored on the 30 locked discharges, one seed, once. The locked set holds only 2 positive-current discharges, so the development per-polarity tables above carry more weight than this row. Indicator on the locked rows: 8,760 of 8,760 (1.000000).

| target | unit | plain | canon | ratio |
|---|---|---|---|---|
| plasma_current | kA | 0.03465 | 0.03465 | 1.000 |
| R_mag_axis | mm | 0.1331 | 0.1259 | 0.946 |
| Z_mag_axis | mm | 0.1721 | 0.1778 | 1.033 |
| elongation |  | 0.002807 | 0.0028 | 0.998 |
| triangularity |  | 0.001353 | 0.001411 | 1.043 |
| triangularity_upper |  | 0.001526 | 0.001568 | 1.028 |
| triangularity_lower |  | 0.00183 | 0.00192 | 1.050 |
| R_x_point | mm | 0.1153 | 0.112 | 0.971 |
| Z_x_point | mm | 0.09686 | 0.1237 | 1.277 |
| R_strike_point_1 | mm | 0.108 | 0.1384 | 1.281 |
| Z_strike_point_1 | mm | 0.04591 | 0.06935 | 1.511 |
| R_strike_point_2 | mm | 0.1356 | 0.1378 | 1.016 |
| Z_strike_point_2 | mm | 0.02636 | 0.02619 | 0.993 |
| R_limiter | mm | 4.549 | 4.898 | 1.077 |
| Z_limiter | mm | 8.348 | 8.959 | 1.073 |
| is_limited |  | 0.01359 | 0.01425 | 1.048 |

all16 plain 0.0590, canon 0.0573.

## Verdict

- Reversed-polarity rows, mean over the 15 shape targets: **+64.2%**
- Negative-current majority, same average: **+20.2%** (this is the price)
- Indicator clean on development rows, clean and noisy: **True**
- Axis gain beyond the 3.5% seed spread: **True** (+18.6%)
- all16 not worse: **True** (+32.7%)
- **SHIP ONLY IF REVERSED-POLARITY DISCHARGES MATTER**

No stratified folds and no reweighting were used or tested here, as instructed; this is the inputs-only fix, which is the one that is deployable without changing how the data are split.

Two things to re-check before this goes into the final model:
- The indicator's margin is thin. The coil sum comes within 0.093 of its own standard deviation of flipping at its closest approach on a development row. No locked row comes closer than that, so the margin generalised here, but it is the first thing to re-measure on a new campaign.
- The cost to the majority regime is real, is 20%, and was not tuned away. If a deployment only ever sees the usual polarity, canonicalisation is a clear loss, not a gain.
- A better version of this fix probably exists and was not tried: canonicalise the inputs AND keep the raw inputs as extra features, so the network can use the folded representation without losing whatever the majority regime was exploiting in the unfolded one. That is a model change, so it is the Lead's call, not this file's.
