#!/usr/bin/env python
"""Exploratory analysis of IPP task 1 (magnetic data). Read-only on data/raw, writes to out/.

    ~/.venvs/hackathon/bin/python -I analysis/ipp1_eda.py
"""
import json
import os
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(os.environ.get("HACKATHON_HOME", "."))
D = ROOT / "data/raw/ipp1-magnetic/uloha_1-magneticka_data"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
df = pd.read_csv(D / "equil_data.csv")
dn = pd.read_csv(D / "equil_data_noisy.csv")
X = [c for c in df.columns if c.startswith(("IPR", "FL"))]
IDX = ["time", "discharge"]
Y = [c for c in df.columns if c not in X + IDX]
MAIN = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "triangularity_upper",
        "triangularity_lower", "R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1",
        "R_strike_point_2", "Z_strike_point_2", "R_limiter", "Z_limiter"]
r = {}

r["shape"] = list(df.shape)
r["noisy_shape"] = list(dn.shape)
r["n_inputs"], r["n_targets"] = len(X), len(Y)
r["discharges"] = int(df.discharge.nunique())
per = df.groupby("discharge").size()
r["rows_per_discharge"] = per.describe().round(1).to_dict()
r["time_range"] = [float(df.time.min()), float(df.time.max())]
dt = df.sort_values(["discharge", "time"]).groupby("discharge").time.diff().dropna()
r["time_step_relative"] = {"median": float(dt.median()), "min": float(dt.min()), "max": float(dt.max())}
r["is_limited_share"] = float(df.is_limited.astype(float).mean())
r["x_nan"] = int(df[X].isna().sum().sum())
r["y_missing_share"] = (df[Y].isna().mean().round(3)).to_dict()
r["same_row_order_in_noisy"] = bool(np.allclose(df[IDX].values, dn[IDX].values))
r["targets_identical_in_noisy"] = bool(np.allclose(df[Y].fillna(-999).values.astype(float),
                                                    dn[Y].fillna(-999).values.astype(float)))
r["x_std"] = df[X].std().round(5).to_dict()
r["x_range"] = {c: [float(df[c].min()), float(df[c].max())] for c in X}

noise = dn[X].values - df[X].values
r["noise_std_over_signal_std"] = {c: float(noise[:, i].std() / df[c].std()) for i, c in enumerate(X)}
# is the added noise drift-like? correlation of the residual with time inside each discharge
drift = []
for g, idxs in df.groupby("discharge").groups.items():
    t = df.loc[idxs, "time"].values
    if len(t) > 5:
        drift.append(np.mean([abs(np.corrcoef(t, noise[df.index.get_indexer(idxs), i])[0, 1]) for i in range(len(X))]))
r["noise_abs_corr_with_time_mean"] = float(np.nanmean(drift))

summ = df[MAIN].describe().T[["count", "min", "mean", "max", "std"]].round(4)
r["main_targets"] = summ.to_dict("index")

# redundancy of the inputs
Z = (df[X] - df[X].mean()) / df[X].std()
ev = np.linalg.svd(Z.values, compute_uv=False) ** 2
ev = ev / ev.sum()
r["pca_cum_explained"] = np.cumsum(ev).round(5)[:10].tolist()
r["pca_components_for_99_9pct"] = int(np.searchsorted(np.cumsum(ev), 0.999) + 1)

# strike point ordering
sp = df.dropna(subset=["R_strike_point_1", "R_strike_point_2"])
r["strike_order_shuffled_share"] = float((sp.R_strike_point_1 > sp.R_strike_point_2).mean())
cur = df.groupby("discharge").plasma_current.median()
r["plasma_current_per_discharge_median"] = cur.describe().round(0).to_dict()
r["negative_current_share"] = float((df.plasma_current < 0).mean())

# a quick look at how similar the shapes are (the assignment warns about correlated parameters)
cm = df[["elongation", "triangularity", "R_mag_axis", "Z_mag_axis", "plasma_current", "a"]].corr().round(2)
r["target_correlations"] = cm.to_dict()
json.dump(r, open(OUT / "ipp1-eda.json", "w"), indent=1, default=float)

# figures
plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False, "font.size": 8})
fig, ax = plt.subplots(2, 4, figsize=(11, 4.6))
for a, c in zip(ax.ravel(), ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation",
                             "triangularity_upper", "triangularity_lower", "R_x_point", "Z_x_point"]):
    a.hist(df[c].dropna(), bins=60, color="#5b7cff")
    a.set_title(c)
fig.suptitle("Rozdělení hlavních cílových veličin (data jsou nerovnoměrná)")
fig.tight_layout()
fig.savefig(OUT / "fig-ipp1-targets.png")
plt.close(fig)

d0 = df[df.discharge == df.discharge.unique()[10]].sort_values("time")
fig, ax = plt.subplots(2, 3, figsize=(11, 4.6), sharex=True)
for a, c in zip(ax.ravel(), ["plasma_current", "elongation", "R_mag_axis", "Z_mag_axis", "triangularity", "IPR05"]):
    a.plot(d0.time, d0[c], color="#1a1d23")
    a.fill_between(d0.time, a.get_ylim()[0], a.get_ylim()[1],
                   where=d0.is_limited.astype(bool), color="#8aa0ff", alpha=0.25)
    a.set_title(c)
fig.suptitle("Jeden výboj v čase (modře: plazma se dotýká limiteru)")
fig.tight_layout()
fig.savefig(OUT / "fig-ipp1-discharge.png")
plt.close(fig)

fig, ax = plt.subplots(1, 3, figsize=(11, 3.2))
ax[0].hist(per.values, bins=30, color="#5b7cff")
ax[0].set_title("Počet řezů na výboj")
ax[1].plot(range(1, 11), np.cumsum(ev)[:10], marker="o", color="#5b7cff")
ax[1].set_title("Kolik nezávislé informace nese 24 vstupů (PCA)")
ax[1].set_ylim(0.9, 1.001)
ax[2].scatter(df.sample(4000, random_state=0).elongation, df.sample(4000, random_state=0).triangularity,
              s=3, alpha=0.4, color="#5b7cff")
ax[2].set_title("Elongace a triangularita: shluk podobných tvarů")
fig.tight_layout()
fig.savefig(OUT / "fig-ipp1-structure.png")
plt.close(fig)

print(json.dumps({k: r[k] for k in ["shape", "n_inputs", "n_targets", "discharges", "rows_per_discharge", "time_range",
                                     "time_step_relative", "is_limited_share", "x_nan", "same_row_order_in_noisy",
                                     "targets_identical_in_noisy", "noise_abs_corr_with_time_mean",
                                     "pca_components_for_99_9pct", "pca_cum_explained", "strike_order_shuffled_share",
                                     "negative_current_share", "plasma_current_per_discharge_median"]}, indent=1))
print("missing share:", {k: v for k, v in r["y_missing_share"].items() if v > 0})
print("noise std / signal std (min, median, max):", np.round([min(r["noise_std_over_signal_std"].values()),
      float(np.median(list(r["noise_std_over_signal_std"].values()))), max(r["noise_std_over_signal_std"].values())], 3))
print(summ.to_string())
