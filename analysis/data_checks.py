#!/usr/bin/env python
"""Kontroly dat citované na slajdech: rozptyl cílů, struktura dodaného šumu a model z pěti hlavních komponent.

    HACKATHON_HOME=<složka hackathonu> python -I analysis/data_checks.py

Zapíše results/ipp1-data-checks.md v repozitáři (jen souhrnná čísla).
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
from common import TARGETS, UNIT, fit_mlp, group_folds, load, score

torch.set_num_threads(2)
table, measurements, targets, discharges, exists = load()
noisy_measurements = load(noisy=True)[1]
relative_time = table["time"].values
lines = ["# Data checks quoted on the slides", "", "Measured with `analysis/data_checks.py` (aggregate numbers only).", "",
         "## Spread of the targets (standard deviation, and the width of the band holding 98 percent of the values)", "",
         "| target | unit | standard deviation | 98 percent band width |", "|---|---|---:|---:|"]
for column, target in enumerate(TARGETS[:-1]):
    values = targets[exists[:, column], column] * UNIT[target][0]
    lines.append(f"| {target} | {UNIT[target][1] or '-'} | {values.std():.4g} | {np.percentile(values, 99) - np.percentile(values, 1):.4g} |")

# Struktura šumu: co k čistým měřením přibylo.
noise = noisy_measurements - measurements
input_names = [name for name in table.columns if name.startswith(("IPR", "FL"))]
coil_columns = [i for i, name in enumerate(input_names) if name.startswith("IPR")]
loop_columns = [i for i, name in enumerate(input_names) if name.startswith("FL")]
noise_to_signal = noise.std(0) / measurements.std(0)
drift_correlations = []   # |korelace šumu s časem| uvnitř výboje: lineární drift by tu byl vidět
lag1_autocorrelations = []   # autokorelace šumu o jeden krok: bílý šum má kolem nuly
for discharge in np.unique(discharges):
    rows = np.where(discharges == discharge)[0]
    rows = rows[np.argsort(relative_time[rows])]
    if len(rows) < 20:
        continue
    for column in range(measurements.shape[1]):
        series = noise[rows, column]
        drift_correlations.append(abs(np.corrcoef(relative_time[rows], series)[0, 1]))
        lag1_autocorrelations.append(np.corrcoef(series[:-1], series[1:])[0, 1])
lines += ["", "## Structure of the noise in `equil_data_noisy.csv`", "",
          f"- Noise standard deviation over the standard deviation of the signal: IPR coils median {np.median(noise_to_signal[coil_columns]):.3f}, flux loops median {np.median(noise_to_signal[loop_columns]):.3f}, overall range {noise_to_signal.min():.3f} to {noise_to_signal.max():.3f}.",
          f"- Mean absolute correlation of the noise with time inside a discharge (a linear drift would show here): {np.nanmean(drift_correlations):.3f}.",
          f"- Mean lag-1 autocorrelation of the noise inside a discharge (white noise is about 0): {np.nanmean(lag1_autocorrelations):.3f}.",
          "- Reading: white noise, no measurable drift; every drift result of ours is synthetic."]

# Síť, která vidí jen prvních 5 hlavních komponent 24 vstupů, proti síti se všemi vstupy.
scores_all_inputs, scores_five_components = [], []
for train, test in group_folds(measurements, targets, discharges, 5):
    mean, std = measurements[train].mean(0), measurements[train].std(0)
    _, _, components = np.linalg.svd((measurements[train] - mean) / std, full_matrices=False)
    projection = components[:5].T

    def project(rows):
        return (((rows - mean) / std) @ projection).astype(np.float32)

    predict_all, _, _ = fit_mlp(measurements[train], targets[train], exists[train], 60, seed=0)
    scores_all_inputs.append(score(predict_all(measurements[test]), targets[test], exists[test]))
    predict_five, _, _ = fit_mlp(project(measurements[train]), targets[train], exists[train], 60, seed=0)
    scores_five_components.append(score(predict_five(project(measurements[test])), targets[test], exists[test]))
lines += ["", "## A network that sees only the first five principal components of the 24 inputs (5 folds by discharge, 60 epochs, seed 0)", "",
          "| target | unit | all 24 inputs MAE | 5 components MAE | ratio |", "|---|---|---:|---:|---:|"]
for target in ("R_mag_axis", "Z_mag_axis", "elongation", "R_x_point", "R_limiter"):
    mae_all = np.mean([fold[target]["mae"] for fold in scores_all_inputs])
    mae_five = np.mean([fold[target]["mae"] for fold in scores_five_components])
    lines.append(f"| {target} | {UNIT[target][1] or '-'} | {mae_all:.4g} | {mae_five:.4g} | {mae_five / mae_all:.2f} |")
lines += ["", "Reading: 99.9 percent of the variance is not 99.9 percent of the information; the low-variance directions carry what the targets need."]
output_file = Path(__file__).resolve().parent.parent / "results" / "ipp1-data-checks.md"
output_file.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[-22:]))
