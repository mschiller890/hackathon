# Numbers cited by the pitch that were missing from results/

Made by `analysis/ipp1_claim_support.py` (gate G2, `docs/internal/claims-audit.md`).

## Variance of the 24 inputs in principal components (inputs standardized, all 42,972 rows)

| components | share of the variance |
|---:|---:|
| 1 | 62.18 % |
| 2 | 92.78 % |
| 5 | 99.93 % |

That is variance, not information: the share says how redundant the inputs are, not how much of the shape they determine.

## Axis error per discharge (out-of-fold predictions of the baseline network, 149 discharges)

Row error = distance between the true and the predicted magnetic axis. Discharge error = mean over its rows.

| measure | value |
|---|---:|
| discharges with mean axis error below 1 mm | 128 of 149 (85.9 %) |
| discharges with mean axis error above 5 mm | 3 of 149 |
| median over discharges of the mean axis error | 0.40 mm |
| median radial axis error over all rows | 0.153 mm |

Out-of-fold means every discharge was predicted by a network that did not train on it; folds are random by discharge, so this is the optimistic split (`results/ipp1-final.md` has the blocked one).
