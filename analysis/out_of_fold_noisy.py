#!/usr/bin/env python
"""Predikce mimo učicí sady na dodaných zašuměných vstupech: síť naučená na čistých datech proti síti zocelené šumem.

    HACKATHON_HOME=<složka hackathonu> python -I analysis/out_of_fold_noisy.py [--epochs 60] [--folds 5]

V každém foldu se obě sítě učí jen na učicích výbojích a odhadují odložené výboje ze souboru equil_data_noisy.csv.
„Zocelená“ znamená, že učicí sada obsahuje čisté řádky plus jednu poškozenou kopii (gaussovský šum a lineární drift
s náhodným sklonem pro každý výboj a cívku, amplitudy 0,15 rozptylu každého vstupu), což se osvědčilo.
Zapíše out/ipp1-predictions-noise.csv (sloupce <cíl>_clean_on_noisy a <cíl>_hardened_on_noisy) a vypíše chyby.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
from common import OUT, TARGETS, fit_mlp, group_folds, load, score

parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=int, default=60)
parser.add_argument("--folds", type=int, default=5)
parser.add_argument("--amplitude", type=float, default=0.15)
args = parser.parse_args()

table, measurements, targets, discharges, exists = load()
noisy_measurements = load(noisy=True)[1]
relative_time = table["time"].values.astype(np.float32)
rng = np.random.default_rng(20261023)
predictions = {name: np.full(targets.shape, np.nan, dtype=np.float32) for name in ("clean", "hardened")}
for fold, (train, test) in enumerate(group_folds(measurements, targets, discharges, args.folds)):
    predict_clean, _, _ = fit_mlp(measurements[train], targets[train], exists[train], args.epochs, seed=fold)
    predictions["clean"][test] = predict_clean(noisy_measurements[test])

    # Poškozená kopie učicích řádků: šum + drift, jehož sklon je pro každý výboj a vstup jiný.
    input_std = measurements[train].std(0)
    drift_slopes = {discharge: rng.normal(0, args.amplitude, measurements.shape[1]) * input_std
                    for discharge in np.unique(discharges[train])}
    drift = np.stack([drift_slopes[discharge] for discharge in discharges[train]]) * relative_time[train, None]
    corrupted = (measurements[train] + rng.normal(0, args.amplitude, measurements[train].shape) * input_std + drift).astype(np.float32)

    # Dvakrát tolik řádků, poloviční počet epoch: zhruba stejný počet kroků optimalizace jako u čistého modelu.
    predict_hardened, _, _ = fit_mlp(np.concatenate([measurements[train], corrupted]), np.concatenate([targets[train], targets[train]]),
                                     np.concatenate([exists[train], exists[train]]), max(args.epochs // 2, 1), seed=fold)
    predictions["hardened"][test] = predict_hardened(noisy_measurements[test])
    print(f"fold {fold + 1}/{args.folds} done", flush=True)

result = table[["discharge", "time"]].copy()
for name, model_predictions in predictions.items():
    for column, target in enumerate(TARGETS):
        result[f"{target}_{name}_on_noisy"] = model_predictions[:, column]
OUT.mkdir(exist_ok=True)
result.to_csv(OUT / "ipp1-predictions-noise.csv", index=False, float_format="%.6g")
print(f"wrote {OUT / 'ipp1-predictions-noise.csv'}: {len(result)} rows")
for name, model_predictions in predictions.items():
    scores = score(model_predictions, targets, exists)
    print(name, " | ".join(f"{target} {scores[target]['mae']:.3g} {scores[target]['unit']}" for target in
                           ("R_mag_axis", "Z_mag_axis", "R_x_point", "plasma_current")), f"| elongation {scores['elongation']['mae']:.4f}")
