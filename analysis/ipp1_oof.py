#!/usr/bin/env python
"""Out-of-fold predictions for IPP task 1: every row is predicted by a network that never saw its discharge.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_oof.py [--epochs 60] [--folds 5]

Writes $HACKATHON_HOME/out/ipp1-predictions.csv with columns discharge, time, fold and <target>_pred.
The true values stay in equil_data.csv (join on discharge and time).
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, fit_mlp, group_folds, load

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=60)
ap.add_argument("--folds", type=int, default=5)
args = ap.parse_args()

df, X, Y, G, M = load()
pred = np.full(Y.shape, np.nan, dtype=np.float32)
fold = np.zeros(len(X), dtype=int)
for k, (tr, te) in enumerate(group_folds(X, Y, G, args.folds)):
    predict, _, _ = fit_mlp(X[tr], Y[tr], M[tr], args.epochs, seed=k)
    pred[te] = predict(X[te])
    fold[te] = k
    print(f"fold {k + 1}/{args.folds} done", flush=True)

out = df[["discharge", "time"]].copy()
out["fold"] = fold
for j, t in enumerate(TARGETS):
    out[f"{t}_pred"] = pred[:, j]
OUT.mkdir(exist_ok=True)
out.to_csv(OUT / "ipp1-predictions.csv", index=False, float_format="%.6g")
print(f"wrote {OUT / 'ipp1-predictions.csv'}: {len(out)} rows")
