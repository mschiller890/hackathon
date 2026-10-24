# IPP 1: measurements divided by the plasma current (`analysis/ipn_model.py`)

The field of the coils is proportional to the currents, so the plasma shape depends on the ratios of the measurements to the plasma current, not on their size. The plasma current
is known from the inputs alone (ridge on the 24 measurements, 0.03 kA), so each measurement is divided by it (signed) and the current is one more input. Everything else is the
`cand` recipe of `ipp1_final.py`; the limiter point is the mean of two answers: the general network's own, and a network that first decides the side of the vessel (up or down), then the position on that side.

## Development set (119 discharges, 5-fold GroupKFold, one seed, general network alone, all 16 outputs)

| variant | mean nRMSE (16) | R axis MAE mm | Z axis MAE mm | R x-point mm | R limiter mm | Z limiter mm |
|---|---:|---:|---:|---:|---:|---:|
| `cand` general network (Huber 0.5) | 0.0954 | 0.229 | 0.339 | 0.210 | 4.92 | 12.7 |
| Huber 0.2 | 0.0898 | 0.213 | 0.295 | 0.194 | 5.19 | 12.6 |
| Huber 0.2, divided by the current | 0.0476 | 0.077 | 0.093 | 0.057 | 2.94 | 7.6 |
| Huber 0.2, divided by the current, second differences | 0.0447 | 0.071 | 0.101 | 0.056 | 2.37 | 6.8 |

Other things tried on the same folds and not kept: wider network (0.0926), 300 epochs (0.0918), weight decay (no effect), batch size, learning rate, GELU, input noise (worse),
inputs from the previous 1 or 2 instants (worse: 0.1154, 0.1084), average of 2 seeds (axis Z 0.238 mm, the total unchanged). Single seed: differences below about 5 to 10 % are not established.
Limiter by side on its own (previous model): Z limiter MAE 11.6 -> 6.2 mm, rows with an error above 100 mm 349 -> 110 of 15,389.

### How the limiter point is answered (development set, 5 folds, the shipped recipe, one seed)

| answer for R_limiter and Z_limiter | R accuracy | Z accuracy | Z MAE mm | mean nRMSE (16) |
|---|---:|---:|---:|---:|
| from the side network (this was shipped first) | 79.8 % | 84.4 % | 4.63 | 0.0488 |
| from the general network | 85.0 % | 85.3 % | 6.91 | 0.0450 |
| Z from the side network, R from the general network | 85.0 % | 84.4 % | 4.63 | 0.0455 |
| **mean of the two (shipped now)** | 84.4 % | **86.4 %** | 5.25 | **0.0447** |

Accuracy = 100 x (1 - nRMSE). The side network alone was the worst of the four in the total; the mean of the two is the best. Chosen on the development set.

## Locked test (30 discharges, 8,761 rows), model trained on the 119 development discharges, `python analysis/bench_mm.py --model out/model/ipp1-ipn.npz --set locked`

Scored once for this recipe, after the recipe was fixed on the development set. These discharges had already been scored for earlier recipes (`ipp1-final.md`), so this is not a fresh test set.

| output | MAE, `cand` (ipp1-final.md) | MAE, this model | share under 1 mm |
|---|---:|---:|---:|
| R axis | 0.133 mm | 0.0562 mm | 99.93 % |
| Z axis | 0.172 mm | 0.0647 mm | 99.71 % |
| R x-point / Z x-point | 0.115 / 0.097 mm | 0.0472 / 0.0526 mm | 99.79 / 99.83 % |
| R strike point 1 / Z | 0.108 / 0.046 mm | 0.0744 / 0.0277 mm | 99.08 / 99.98 % |
| R strike point 2 / Z | 0.136 / 0.026 mm | 0.0518 / 0.0116 mm | 99.71 / 99.96 % |
| R limiter / Z limiter | 4.55 / 8.35 mm | 2.85 / 4.49 mm | 71.8 / 44.1 % |
| plasma current | 0.0347 kA | 0.0343 kA | |
| limited / diverted agreement | 99.16 % | 99.20 % | |
| mean nRMSE (16), "overall accuracy" 100 x (1 - nRMSE) | 0.0588 (94.12 %, with the axis network) | 0.0417 (95.83 %) | |

The tails of the limiter point are about as before: the worst single rows are 352 mm (R) and 439 mm (Z), the old ones 357 and 485 mm; about 2 % of the limited rows are off by more than 32 mm. Not tested here: the noisy inputs (the estimate of the current
is noisy, and the division enlarges that at small currents); the noise model of `ipp1-noise-window.md` is unchanged.

Re-training is not bit for bit repeatable (threads): the limiter network of two exports gave 95.81 and 95.83 % overall; the axis and the other outputs came out the same to the printed digits.
