# Fewer inputs: accuracy against the number of inputs (REQ-004)

5 folds by discharge; summary = mean of the relative error (RMSE / spread) over 13 targets, without the limiter point; lower is better. Ranking by permutation importance on training rows only.

| inputs | summary error | plasma_current (kA) | R_mag_axis (mm) | Z_mag_axis (mm) | elongation (abs) | R_x_point (mm) | R_strike_point_1 (mm) | R_limiter (mm) |
|---|---|---|---|---|---|---|---|---|
| all 24 | 0.063 ± 0.028 | 1.49 | 0.377 | 0.391 | 0.00569 | 0.202 | 0.265 | 10.7 |
| top 16 | 0.067 ± 0.022 | 1.42 | 0.43 | 0.471 | 0.00619 | 0.178 | 0.23 | 12.3 |
| top 12 | 0.077 ± 0.024 | 1.51 | 0.629 | 0.662 | 0.00634 | 0.267 | 0.221 | 11.7 |
| top 8 | 0.094 ± 0.022 | 1.48 | 0.904 | 1.17 | 0.00665 | 0.457 | 0.263 | 13.5 |
| top 6 | 0.143 ± 0.053 | 2.08 | 1.62 | 1.58 | 0.00879 | 0.981 | 0.814 | 17 |
| top 5 | 0.157 ± 0.061 | 2.2 | 2.01 | 1.86 | 0.011 | 1.12 | 0.932 | 16.4 |
| top 4 | 0.204 ± 0.074 | 2.91 | 2.43 | 2.33 | 0.0136 | 1.63 | 1.69 | 18 |
| top 3 | 0.265 ± 0.083 | 3.77 | 3.01 | 3.19 | 0.019 | 1.98 | 2.32 | 22.5 |
| top 2 | 0.404 ± 0.069 | 6.49 | 3.69 | 3.96 | 0.0237 | 4.17 | 4.67 | 33.2 |
| IPR only (16) | 0.066 ± 0.032 | 1.28 | 0.492 | 0.401 | 0.00546 | 0.284 | 0.344 | 12.3 |
| FL only (8) | 0.285 ± 0.053 | 6.57 | 2.32 | 1.72 | 0.0203 | 1.49 | 3.03 | 21.9 |

Ranking by permutation importance (most important first): IPR14, IPR01, IPR13, IPR12, IPR02, FL01, IPR09, IPR10, FL08, IPR05, IPR16, IPR08, FL04, IPR11, IPR07, FL05, FL06, IPR06, IPR15, IPR04, IPR03, FL03, FL07, FL02

Note (independent review): the ranking is the importance for the trained network (single column permutation on near collinear inputs), not the information content of a sensor. Each fold ranks and retrains with its own top k set, so a "top 8" row estimates the procedure, not the 8 sensors printed above. What holds as evidence: the top k curve, and IPR coils only (0.066) against flux loops only (0.285), 4.3 times worse.

This ranking is the importance of an input for the trained network, not information content: the inputs are collinear, so permuting one column creates rows off the data manifold. Do not read it as 'the important sensors'; the evidence for the number of inputs is the retrain curve ('top k' sets are chosen inside each fold) and its controls in ipp1-inputs-controls.md.
