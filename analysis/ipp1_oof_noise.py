#!/usr/bin/env python
"""Out-of-fold predictions on the provided noisy inputs: a network trained on clean data against one hardened with noise.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_oof_noise.py [--epochs 60] [--folds 5]

For every fold both networks are trained on the training discharges only and predict the held-out discharges from
equil_data_noisy.csv. "Hardened" means the training set holds the clean rows plus one corrupted copy (Gaussian noise and a
linear drift with a random slope per discharge and coil, amplitudes 0.15 of each input's spread), as lane R found useful.
Writes out/ipp1-predictions-noise.csv (columns <target>_clean_on_noisy and <target>_hardened_on_noisy) and prints the errors.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, fit_mlp, group_folds, load, score

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=60)
ap.add_argument("--folds", type=int, default=5)
ap.add_argument("--amplitude", type=float, default=0.15)
args = ap.parse_args()

df, X, Y, G, M = load()
Xn = load(noisy=True)[1]
t = df["time"].values.astype(np.float32)
rng = np.random.default_rng(20261023)
pred = {name: np.full(Y.shape, np.nan, dtype=np.float32) for name in ("clean", "hardened")}
for k, (tr, te) in enumerate(group_folds(X, Y, G, args.folds)):
    p_clean, _, _ = fit_mlp(X[tr], Y[tr], M[tr], args.epochs, seed=k)
    pred["clean"][te] = p_clean(Xn[te])
    sd = X[tr].std(0)
    slopes = {g: rng.normal(0, args.amplitude, X.shape[1]) * sd for g in np.unique(G[tr])}
    drift = np.stack([slopes[g] for g in G[tr]]) * t[tr, None]
    Xc = (X[tr] + rng.normal(0, args.amplitude, X[tr].shape) * sd + drift).astype(np.float32)
    # Twice the rows, half the epochs: roughly the same number of optimizer updates as the clean model.
    p_hard, _, _ = fit_mlp(np.concatenate([X[tr], Xc]), np.concatenate([Y[tr], Y[tr]]),
                           np.concatenate([M[tr], M[tr]]), max(args.epochs // 2, 1), seed=k)
    pred["hardened"][te] = p_hard(Xn[te])
    print(f"fold {k + 1}/{args.folds} done", flush=True)

out = df[["discharge", "time"]].copy()
for name, P in pred.items():
    for j, tg in enumerate(TARGETS):
        out[f"{tg}_{name}_on_noisy"] = P[:, j]
OUT.mkdir(exist_ok=True)
out.to_csv(OUT / "ipp1-predictions-noise.csv", index=False, float_format="%.6g")
print(f"wrote {OUT / 'ipp1-predictions-noise.csv'}: {len(out)} rows")
for name, P in pred.items():
    res = score(P, Y, M)
    print(name, " | ".join(f"{tg} {res[tg]['mae']:.3g} {res[tg]['unit']}" for tg in
                           ("R_mag_axis", "Z_mag_axis", "R_x_point", "plasma_current")), f"| elongation {res['elongation']['mae']:.4f}")
