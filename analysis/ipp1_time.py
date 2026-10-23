#!/usr/bin/env python
"""Stability of the output over the time of a discharge (REQ-003), from the out-of-fold predictions.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_time.py

Needs out/ipp1-predictions.csv (analysis/ipp1_oof.py). Writes out/ipp1-time.{json,md,png}.
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, UNIT, load

df, X, Y, G, M = load()
pr = pd.read_csv(OUT / "ipp1-predictions.csv")
assert np.array_equal(pr.discharge.values, df.discharge.values) and np.allclose(pr.time.values, df.time.values)
P = pr[[f"{t}_pred" for t in TARGETS]].values
KEY = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "R_x_point", "R_strike_point_1"]
bins = np.minimum((df.time.values * 10).astype(int), 9)
res = {"mae_by_time_decile": {}, "jitter_ratio": {}, "bias_share": {}}
order = df.sort_values(["discharge", "time"]).index.values
for t in KEY:
    j = TARGETS.index(t)
    k = M[:, j]
    scale, unit = UNIT[t]
    err = P[:, j] - Y[:, j]
    res["mae_by_time_decile"][t] = [float(np.abs(err[k & (bins == b)]).mean() * scale) for b in range(10)]
    # Row-to-row change of the prediction against the change of the truth, only across neighbouring rows.
    d_pred, d_true = [], []
    for g, idx in df.loc[order].groupby("discharge").groups.items():
        idx = np.asarray(idx)
        ok = (np.diff(df.time.values[idx]) < 0.01) & k[idx][1:] & k[idx][:-1]
        d_pred += list(np.diff(P[idx, j])[ok])
        d_true += list(np.diff(Y[idx, j])[ok])
    res["jitter_ratio"][t] = float(np.sqrt(np.mean(np.square(d_pred))) / np.sqrt(np.mean(np.square(d_true))))
    # Share of the squared error that is a constant offset of a whole discharge rather than row-to-row noise.
    per = pd.Series(err[k]).groupby(df.discharge.values[k])
    res["bias_share"][t] = float((per.mean() ** 2 * per.size()).sum() / (err[k] ** 2).sum())
json.dump(res, open(OUT / "ipp1-time.json", "w"), indent=1)

lines = ["# Stability over time (REQ-003)", "", "Out-of-fold predictions. MAE by tenth of the relative discharge time, "
         "jitter ratio (RMS of the row-to-row change of the prediction divided by the same for the truth; 1 means equally smooth) "
         "and the share of the squared error that is a whole-discharge offset.", "",
         "| target | unit | " + " | ".join(f"{b * 10}-{b * 10 + 10} %" for b in range(10)) + " | jitter | offset share |",
         "|---|---|" + "---|" * 12]
for t in KEY:
    lines.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(f"{v:.3g}" for v in res["mae_by_time_decile"][t])
                 + f" | {res['jitter_ratio'][t]:.2f} | {res['bias_share'][t]:.2f} |")
(OUT / "ipp1-time.md").write_text("\n".join(lines), encoding="utf-8")

plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False, "font.size": 8})
fig, ax = plt.subplots(1, 3, figsize=(12, 3.4))
for t in KEY:
    v = np.array(res["mae_by_time_decile"][t])
    ax[0].plot(np.arange(10) * 10 + 5, v / v.mean(), marker="o", label=t)
ax[0].set_xlabel("čas výboje (%)")
ax[0].set_ylabel("chyba / průměrná chyba")
ax[0].set_title("Kde v čase model chybuje")
ax[0].legend(fontsize=6)
j = TARGETS.index("R_mag_axis")
pd_err = pd.Series(np.abs(P[:, j] - Y[:, j])).groupby(df.discharge.values).mean().sort_values()
g = pd_err.index[len(pd_err) // 2]
d = df[df.discharge == g].sort_values("time")
for a, t in zip(ax[1:], ("R_mag_axis", "elongation")):
    jj = TARGETS.index(t)
    ax[1 + ("elongation" == t)].plot(d.time, d[t], color="#1a1d23", label="skutečnost")
    ax[1 + ("elongation" == t)].plot(d.time, P[d.index, jj], color="#e07a5f", label="model")
    ax[1 + ("elongation" == t)].set_title(f"{t}, výboj s mediánovou chybou")
ax[1].legend()
fig.tight_layout()
fig.savefig(OUT / "ipp1-time.png")
print("\n".join(lines))
