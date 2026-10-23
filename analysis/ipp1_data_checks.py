#!/usr/bin/env python
"""Data checks quoted on the slides: spreads of the targets, structure of the provided noise, a five-component PCA model.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_data_checks.py

Writes results/ipp1-data-checks.md next to the repository (aggregate numbers only).
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import TARGETS, UNIT, fit_mlp, group_folds, load, score

torch.set_num_threads(2)
df, X, Y, G, M = load()
Xn = load(noisy=True)[1]
t = df["time"].values
lines = ["# Data checks quoted on the slides", "", "Measured with `analysis/ipp1_data_checks.py` (aggregate numbers only).", "",
         "## Spread of the targets (standard deviation, and the width of the band holding 98 percent of the values)", "",
         "| target | unit | standard deviation | 98 percent band width |", "|---|---|---:|---:|"]
for j, tg in enumerate(TARGETS[:-1]):
    v = Y[M[:, j], j] * UNIT[tg][0]
    lines.append(f"| {tg} | {UNIT[tg][1] or '-'} | {v.std():.4g} | {np.percentile(v, 99) - np.percentile(v, 1):.4g} |")

noise = Xn - X
names = [c for c in df.columns if c.startswith(("IPR", "FL"))]
ipr = [i for i, c in enumerate(names) if c.startswith("IPR")]
fl = [i for i, c in enumerate(names) if c.startswith("FL")]
ratio = noise.std(0) / X.std(0)
slopes = []
lag = []
for g in np.unique(G):
    k = np.where(G == g)[0]
    k = k[np.argsort(t[k])]
    if len(k) < 20:
        continue
    for i in range(X.shape[1]):
        r = noise[k, i]
        slopes.append(abs(np.corrcoef(t[k], r)[0, 1]))
        lag.append(np.corrcoef(r[:-1], r[1:])[0, 1])
lines += ["", "## Structure of the noise in `equil_data_noisy.csv`", "",
          f"- Noise standard deviation over the standard deviation of the signal: IPR coils median {np.median(ratio[ipr]):.3f}, flux loops median {np.median(ratio[fl]):.3f}, overall range {ratio.min():.3f} to {ratio.max():.3f}.",
          f"- Mean absolute correlation of the noise with time inside a discharge (a linear drift would show here): {np.nanmean(slopes):.3f}.",
          f"- Mean lag-1 autocorrelation of the noise inside a discharge (white noise is about 0): {np.nanmean(lag):.3f}.",
          "- Reading: white noise, no measurable drift; every drift result of ours is synthetic."]

pc = np.linalg.svd((X - X.mean(0)) / X.std(0), full_matrices=False)
res_full, res_pca = [], []
for tr, te in group_folds(X, Y, G, 5):
    mu, sd = X[tr].mean(0), X[tr].std(0)
    _, _, vt = np.linalg.svd((X[tr] - mu) / sd, full_matrices=False)
    P = vt[:5].T
    z = lambda a: (((a - mu) / sd) @ P).astype(np.float32)
    p, _, _ = fit_mlp(X[tr], Y[tr], M[tr], 60, seed=0)
    res_full.append(score(p(X[te]), Y[te], M[te]))
    q, _, _ = fit_mlp(z(X[tr]), Y[tr], M[tr], 60, seed=0)
    res_pca.append(score(q(z(X[te])), Y[te], M[te]))
lines += ["", "## A network that sees only the first five principal components of the 24 inputs (5 folds by discharge, 60 epochs, seed 0)", "",
          "| target | unit | all 24 inputs MAE | 5 components MAE | ratio |", "|---|---|---:|---:|---:|"]
for tg in ("R_mag_axis", "Z_mag_axis", "elongation", "R_x_point", "R_limiter"):
    a = np.mean([r[tg]["mae"] for r in res_full])
    b = np.mean([r[tg]["mae"] for r in res_pca])
    lines.append(f"| {tg} | {UNIT[tg][1] or '-'} | {a:.4g} | {b:.4g} | {b / a:.2f} |")
lines += ["", "Reading: 99.9 percent of the variance is not 99.9 percent of the information; the low-variance directions carry what the targets need."]
out = Path(__file__).resolve().parent.parent / "results" / "ipp1-data-checks.md"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[-22:]))
