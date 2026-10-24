#!/usr/bin/env python
"""Predikce mimo učicí sady (out-of-fold) pro úlohu IPP 1: každý řádek odhaduje síť, která jeho výboj nikdy neviděla.

    HACKATHON_HOME=<složka hackathonu> python -I analysis/ipp1_oof.py [--epochs 60] [--folds 5]

Zapíše $HACKATHON_HOME/out/ipp1-predictions.csv se sloupci discharge, time, fold a <cíl>_pred.
Skutečné hodnoty zůstávají v equil_data.csv (spojit podle discharge a time).
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
from ipp1_common import OUT, TARGETS, fit_mlp, group_folds, load

parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=int, default=60)
parser.add_argument("--folds", type=int, default=5)
args = parser.parse_args()

table, measurements, targets, discharges, exists = load()
predictions = np.full(targets.shape, np.nan, dtype=np.float32)
fold_of_row = np.zeros(len(measurements), dtype=int)
for fold, (train, test) in enumerate(group_folds(measurements, targets, discharges, args.folds)):
    predict, _, _ = fit_mlp(measurements[train], targets[train], exists[train], args.epochs, seed=fold)
    predictions[test] = predict(measurements[test])
    fold_of_row[test] = fold
    print(f"fold {fold + 1}/{args.folds} done", flush=True)

result = table[["discharge", "time"]].copy()
result["fold"] = fold_of_row
for column, target in enumerate(TARGETS):
    result[f"{target}_pred"] = predictions[:, column]
OUT.mkdir(exist_ok=True)
result.to_csv(OUT / "ipp1-predictions.csv", index=False, float_format="%.6g")
print(f"wrote {OUT / 'ipp1-predictions.csv'}: {len(result)} rows")
