#!/usr/bin/env python
"""Průzkumná analýza úlohy IPP 1 (magnetická data). Data jen čte, výsledky zapisuje do out/.

    ~/.venvs/hackathon/bin/python -I analysis/explore_data.py
"""
import json
import os
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(os.environ.get("HACKATHON_HOME") or Path(__file__).resolve().parents[1])
DATA_FOLDERS = (ROOT / "data", ROOT / "data/raw/ipp1-magnetic/uloha_1-magneticka_data")
DATA = next((folder for folder in DATA_FOLDERS if (folder / "equil_data.csv").exists()), ROOT / "data")
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
clean = pd.read_csv(DATA / "equil_data.csv")
noisy = pd.read_csv(DATA / "equil_data_noisy.csv")
INPUTS = [name for name in clean.columns if name.startswith(("IPR", "FL"))]
ROW_KEYS = ["time", "discharge"]
TARGET_COLUMNS = [name for name in clean.columns if name not in INPUTS + ROW_KEYS]
MAIN_TARGETS = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "triangularity_upper",
                "triangularity_lower", "R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1",
                "R_strike_point_2", "Z_strike_point_2", "R_limiter", "Z_limiter"]
facts = {}  # všechna zjištění, uloží se do eda.json

# Rozměry a časování dat.
facts["shape"] = list(clean.shape)
facts["noisy_shape"] = list(noisy.shape)
facts["n_inputs"], facts["n_targets"] = len(INPUTS), len(TARGET_COLUMNS)
facts["discharges"] = int(clean.discharge.nunique())
rows_per_discharge = clean.groupby("discharge").size()
facts["rows_per_discharge"] = rows_per_discharge.describe().round(1).to_dict()
facts["time_range"] = [float(clean.time.min()), float(clean.time.max())]
time_steps = clean.sort_values(["discharge", "time"]).groupby("discharge").time.diff().dropna()
facts["time_step_relative"] = {"median": float(time_steps.median()), "min": float(time_steps.min()), "max": float(time_steps.max())}
facts["is_limited_share"] = float(clean.is_limited.astype(float).mean())
facts["x_nan"] = int(clean[INPUTS].isna().sum().sum())
facts["y_missing_share"] = (clean[TARGET_COLUMNS].isna().mean().round(3)).to_dict()
facts["same_row_order_in_noisy"] = bool(np.allclose(clean[ROW_KEYS].values, noisy[ROW_KEYS].values))
facts["targets_identical_in_noisy"] = bool(np.allclose(clean[TARGET_COLUMNS].fillna(-999).values.astype(float),
                                                       noisy[TARGET_COLUMNS].fillna(-999).values.astype(float)))
facts["x_std"] = clean[INPUTS].std().round(5).to_dict()
facts["x_range"] = {name: [float(clean[name].min()), float(clean[name].max())] for name in INPUTS}

# Šum přidaný do zašuměného souboru a jestli připomíná drift: korelace zbytku s časem uvnitř každého výboje.
noise = noisy[INPUTS].values - clean[INPUTS].values
facts["noise_std_over_signal_std"] = {name: float(noise[:, i].std() / clean[name].std()) for i, name in enumerate(INPUTS)}
drift_correlations = []
for discharge, row_labels in clean.groupby("discharge").groups.items():
    times = clean.loc[row_labels, "time"].values
    if len(times) > 5:
        discharge_noise = noise[clean.index.get_indexer(row_labels)]
        drift_correlations.append(np.mean([abs(np.corrcoef(times, discharge_noise[:, i])[0, 1]) for i in range(len(INPUTS))]))
facts["noise_abs_corr_with_time_mean"] = float(np.nanmean(drift_correlations))

main_summary = clean[MAIN_TARGETS].describe().T[["count", "min", "mean", "max", "std"]].round(4)
facts["main_targets"] = main_summary.to_dict("index")

# Redundance vstupů: kolik hlavních komponent vysvětlí rozptyl.
standardized_inputs = (clean[INPUTS] - clean[INPUTS].mean()) / clean[INPUTS].std()
explained = np.linalg.svd(standardized_inputs.values, compute_uv=False) ** 2
explained = explained / explained.sum()
facts["pca_cum_explained"] = np.cumsum(explained).round(5)[:10].tolist()
facts["pca_components_for_99_9pct"] = int(np.searchsorted(np.cumsum(explained), 0.999) + 1)

# Pořadí dotykových bodů a proud plazmatu.
strike_rows = clean.dropna(subset=["R_strike_point_1", "R_strike_point_2"])
facts["strike_order_shuffled_share"] = float((strike_rows.R_strike_point_1 > strike_rows.R_strike_point_2).mean())
current_per_discharge = clean.groupby("discharge").plasma_current.median()
facts["plasma_current_per_discharge_median"] = current_per_discharge.describe().round(0).to_dict()
facts["negative_current_share"] = float((clean.plasma_current < 0).mean())

# Jak jsou si tvary podobné (zadání upozorňuje na korelované parametry).
correlations = clean[["elongation", "triangularity", "R_mag_axis", "Z_mag_axis", "plasma_current", "a"]].corr().round(2)
facts["target_correlations"] = correlations.to_dict()
json.dump(facts, open(OUT / "eda.json", "w"), indent=1, default=float)

# Obrázky.
plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False, "font.size": 8})
fig, axes = plt.subplots(2, 4, figsize=(11, 4.6))
for axis, name in zip(axes.ravel(), ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation",
                                     "triangularity_upper", "triangularity_lower", "R_x_point", "Z_x_point"]):
    axis.hist(clean[name].dropna(), bins=60, color="#5b7cff")
    axis.set_title(name)
fig.suptitle("Rozdělení hlavních cílových veličin (data jsou nerovnoměrná)")
fig.tight_layout()
fig.savefig(OUT / "fig-targets.png")
plt.close(fig)

example_discharge = clean[clean.discharge == clean.discharge.unique()[10]].sort_values("time")
fig, axes = plt.subplots(2, 3, figsize=(11, 4.6), sharex=True)
for axis, name in zip(axes.ravel(), ["plasma_current", "elongation", "R_mag_axis", "Z_mag_axis", "triangularity", "IPR05"]):
    axis.plot(example_discharge.time, example_discharge[name], color="#1a1d23")
    axis.fill_between(example_discharge.time, axis.get_ylim()[0], axis.get_ylim()[1],
                      where=example_discharge.is_limited.astype(bool), color="#8aa0ff", alpha=0.25)
    axis.set_title(name)
fig.suptitle("Jeden výboj v čase (modře: plazma se dotýká limiteru)")
fig.tight_layout()
fig.savefig(OUT / "fig-discharge.png")
plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
axes[0].hist(rows_per_discharge.values, bins=30, color="#5b7cff")
axes[0].set_title("Počet řezů na výboj")
axes[1].plot(range(1, 11), np.cumsum(explained)[:10], marker="o", color="#5b7cff")
axes[1].set_title("Kolik nezávislé informace nese 24 vstupů (PCA)")
axes[1].set_ylim(0.9, 1.001)
axes[2].scatter(clean.sample(4000, random_state=0).elongation, clean.sample(4000, random_state=0).triangularity,
                s=3, alpha=0.4, color="#5b7cff")
axes[2].set_title("Elongace a triangularita: shluk podobných tvarů")
fig.tight_layout()
fig.savefig(OUT / "fig-structure.png")
plt.close(fig)

print(json.dumps({key: facts[key] for key in ["shape", "n_inputs", "n_targets", "discharges", "rows_per_discharge", "time_range",
                                              "time_step_relative", "is_limited_share", "x_nan", "same_row_order_in_noisy",
                                              "targets_identical_in_noisy", "noise_abs_corr_with_time_mean",
                                              "pca_components_for_99_9pct", "pca_cum_explained", "strike_order_shuffled_share",
                                              "negative_current_share", "plasma_current_per_discharge_median"]}, indent=1))
print("missing share:", {name: share for name, share in facts["y_missing_share"].items() if share > 0})
noise_ratios = list(facts["noise_std_over_signal_std"].values())
print("noise std / signal std (min, median, max):", np.round([min(noise_ratios), float(np.median(noise_ratios)), max(noise_ratios)], 3))
print(main_summary.to_string())
