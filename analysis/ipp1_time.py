#!/usr/bin/env python
"""Stabilita výstupu v čase výboje (REQ-003) z predikcí mimo učicí sady.

    HACKATHON_HOME=<složka hackathonu> python -I analysis/ipp1_time.py

Potřebuje out/ipp1-predictions.csv (analysis/ipp1_oof.py). Když existuje out/ipp1-predictions-noise.csv (analysis/ipp1_oof_noise.py,
sloupce <cíl>_clean_on_noisy a <cíl>_hardened_on_noisy), spočítají se stejná čísla i pro zašuměné vstupy.
Zapíše out/ipp1-time.{json,md,png}. Pokryty jsou všech 16 cílů.

Metriky pro každý cíl na řádcích, které jsou v čase sousední (krok pod 0,01 relativního času):
- poměr chvění (jitter ratio): RMS změny odhadu z řádku na řádek / RMS změny skutečné hodnoty. Zůstává kolem 1, kdykoli se
  skutečná hodnota hýbe, takže sám zašuměný výstup neodhalí.
- skok chyby (error step): RMS změny CHYBY odhadu (odhad minus skutečnost) z řádku na řádek, v jednotkách hlášení.
  Tak vypadá kolísání výstupu; uveden je i jeho poměr k RMS změny skutečné hodnoty.
- podíl posunu (offset share): podíl čtverce chyby, který je konstantním posunem celého výboje.
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
from ipp1_common import OUT, TARGETS, UNIT, load

table, measurements, targets, discharges, exists = load()
relative_time = table.time.values
VARIANTS = {}  # název -> matice predikcí
clean_table = pd.read_csv(OUT / "ipp1-predictions.csv")
assert np.array_equal(clean_table.discharge.values, discharges) and np.allclose(clean_table.time.values, relative_time)
VARIANTS["clean"] = clean_table[[f"{target}_pred" for target in TARGETS]].values
noise_file = OUT / "ipp1-predictions-noise.csv"
if noise_file.exists():
    noisy_table = pd.read_csv(noise_file)
    assert np.array_equal(noisy_table.discharge.values, discharges) and np.allclose(noisy_table.time.values, relative_time)
    for kind in ("clean_on_noisy", "hardened_on_noisy"):
        VARIANTS[kind] = noisy_table[[f"{target}_{kind}" for target in TARGETS]].values
LABEL = {"clean": "clean inputs, network trained on clean data",
         "clean_on_noisy": "noisy inputs, network trained on clean data",
         "hardened_on_noisy": "noisy inputs, network trained with noise and drift augmentation"}

time_decile = np.minimum((relative_time * 10).astype(int), 9)
# Sousední řádky téhož výboje: previous_row[i] a next_row[i] jsou pozice řádků, next_row je další řádek v čase.
by_time = np.lexsort((relative_time, discharges))
previous_row, next_row = by_time[:-1], by_time[1:]
is_neighbour = (discharges[previous_row] == discharges[next_row]) & (relative_time[next_row] - relative_time[previous_row] < 0.01)
previous_row, next_row = previous_row[is_neighbour], next_row[is_neighbour]


def rms(values):
    return float(np.sqrt(np.mean(np.square(values))))


def stability_statistics(predictions):
    """Všechny metriky stability pro jednu matici predikcí; vrací slovník metrika -> {cíl: hodnota}."""
    result = {"mae_by_time_decile": {}, "jitter_ratio": {}, "error_step": {}, "error_step_ratio": {}, "bias_share": {},
              "truth_step": {}}
    for target in TARGETS:
        column = TARGETS.index(target)
        exists_column = exists[:, column]
        unit_scale = UNIT[target][0]
        error = predictions[:, column] - targets[:, column]
        result["mae_by_time_decile"][target] = [
            float(np.abs(error[exists_column & (time_decile == decile)]).mean() * unit_scale)
            if (exists_column & (time_decile == decile)).any() else None for decile in range(10)]
        both_exist = exists_column[previous_row] & exists_column[next_row]
        truth_change = (targets[next_row, column] - targets[previous_row, column])[both_exist]
        prediction_change = (predictions[next_row, column] - predictions[previous_row, column])[both_exist]
        error_change = (error[next_row] - error[previous_row])[both_exist]
        result["truth_step"][target] = rms(truth_change) * unit_scale
        result["jitter_ratio"][target] = rms(prediction_change) / rms(truth_change)
        result["error_step"][target] = rms(error_change) * unit_scale
        result["error_step_ratio"][target] = rms(error_change) / rms(truth_change)
        per_discharge = pd.Series(error[exists_column]).groupby(discharges[exists_column])
        result["bias_share"][target] = float((per_discharge.mean() ** 2 * per_discharge.size()).sum() / (error[exists_column] ** 2).sum())
    return result


statistics = {name: stability_statistics(predictions) for name, predictions in VARIANTS.items()}


def clean_json(value):
    """NaN není platný JSON: zapíše se None."""
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_json(item) for item in value]
    return None if isinstance(value, float) and not np.isfinite(value) else value


with open(OUT / "ipp1-time.json", "w") as json_file:
    json.dump(clean_json({"variants": LABEL, "n_neighbour_pairs": int(len(previous_row)), **statistics["clean"],
                          "noisy": {name: values for name, values in statistics.items() if name != "clean"}}),
              json_file, indent=1, allow_nan=False)


def format_or_na(value, spec):
    return "n/a" if value is None else format(value, spec)


clean_stats = statistics["clean"]
lines = ["# Stability over time (REQ-003)", "",
         "Out-of-fold predictions, all 16 targets. MAE by tenth of the relative discharge time (n/a = no rows of that target in the "
         "decile, for example the X-point and strike points do not exist at the start of a discharge), jitter ratio (RMS of the "
         "row-to-row change of the prediction divided by the same for the truth; amplitude weighted, it stays near 1 whenever the truth "
         "moves, so it does not prove a quiet output), error step (RMS of the row-to-row change of the prediction error, in report "
         "units) and the share of the squared error that is a constant offset of a whole discharge. The first and last tenth are the "
         "start and end of the discharge, where the equilibrium is least well defined.", "",
         f"## {LABEL['clean']}", "",
         "| target | unit | " + " | ".join(f"{d * 10}-{d * 10 + 10} %" for d in range(10)) + " | jitter | error step | step / truth step | offset share |",
         "|---|---|" + "---|" * 14]
for target in TARGETS:
    lines.append(f"| {target} | {UNIT[target][1]} | " + " | ".join(format_or_na(v, ".3g") for v in clean_stats["mae_by_time_decile"][target])
                 + f" | {clean_stats['jitter_ratio'][target]:.2f} | {clean_stats['error_step'][target]:.3g} | "
                 f"{clean_stats['error_step_ratio'][target]:.2f} | {clean_stats['bias_share'][target]:.2f} |")
if len(VARIANTS) > 1:
    lines += ["", "## Noisy inputs (equil_data_noisy.csv, out-of-fold)", "",
              "Same metrics for the plain network on noisy inputs and for the network hardened with noise and drift augmentation. "
              "jitter = jitter ratio, step = error step in report units, ratio = error step / RMS change of the truth. "
              "A ratio near 0 means the error does not wobble from row to row; above 1 the wobble of the error is larger than the "
              "movement of the truth.", "",
              "| target | unit | truth step | jitter clean | jitter plain | jitter hardened | step clean | step plain | step hardened "
              "| ratio clean | ratio plain | ratio hardened |", "|---|---|" + "---|" * 10]
    for target in TARGETS:
        on_clean, on_noisy, hardened = statistics["clean"], statistics["clean_on_noisy"], statistics["hardened_on_noisy"]
        lines.append(f"| {target} | {UNIT[target][1]} | {on_clean['truth_step'][target]:.3g} | {on_clean['jitter_ratio'][target]:.2f} | "
                     f"{on_noisy['jitter_ratio'][target]:.2f} | "
                     f"{hardened['jitter_ratio'][target]:.2f} | {on_clean['error_step'][target]:.3g} | {on_noisy['error_step'][target]:.3g} | "
                     f"{hardened['error_step'][target]:.3g} | "
                     f"{on_clean['error_step_ratio'][target]:.2f} | {on_noisy['error_step_ratio'][target]:.2f} | {hardened['error_step_ratio'][target]:.2f} |")
    for kind in ("clean_on_noisy", "hardened_on_noisy"):
        lines += ["", f"### MAE by tenth of the discharge, {LABEL[kind]}", "",
                  "| target | unit | " + " | ".join(f"{d * 10}-{d * 10 + 10} %" for d in range(10)) + " | offset share |",
                  "|---|---|" + "---|" * 11]
        for target in TARGETS:
            lines.append(f"| {target} | {UNIT[target][1]} | " + " | ".join(format_or_na(v, ".3g") for v in statistics[kind]["mae_by_time_decile"][target])
                         + f" | {statistics[kind]['bias_share'][target]:.2f} |")
else:
    lines += ["", "out/ipp1-predictions-noise.csv not found: stability on noisy inputs not computed."]
(OUT / "ipp1-time.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

# Obrázek: kde v čase model chybuje a jak vypadá chyba osy v jednom výboji.
PLOTTED_TARGETS = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "R_x_point", "R_strike_point_1",
                   "R_limiter", "Z_limiter"]
plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False, "font.size": 8})
fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))
for target in PLOTTED_TARGETS:
    mae_by_decile = np.array([np.nan if value is None else value for value in clean_stats["mae_by_time_decile"][target]])
    axes[0].plot(np.arange(10) * 10 + 5, mae_by_decile / np.nanmean(mae_by_decile), marker="o", label=target)
axes[0].set_xlabel("čas výboje (%)")
axes[0].set_ylabel("chyba / průměrná chyba")
axes[0].set_title("Kde v čase model chybuje")
axes[0].legend(fontsize=6)
# Kreslí se jen chyba odhadu jednoho výboje (ne měřený signál), v mm; vybere se výboj uprostřed pořadí podle střední chyby.
colors = {"clean": "#1a1d23", "clean_on_noisy": "#8d99ae", "hardened_on_noisy": "#e07a5f"}
shown_names = {"clean": "čisté vstupy", "clean_on_noisy": "šum, síť na čistých datech", "hardened_on_noisy": "šum, síť s augmentací"}
r_axis_column = TARGETS.index("R_mag_axis")
mean_error_per_discharge = pd.Series(np.abs(VARIANTS["clean"][:, r_axis_column] - targets[:, r_axis_column])).groupby(discharges).mean().sort_values()
shown_discharge = mean_error_per_discharge.index[len(mean_error_per_discharge) // 2]
shown_rows = np.where(discharges == shown_discharge)[0]
shown_rows = shown_rows[np.argsort(relative_time[shown_rows])]
for axis, target in zip(axes[1:], ("R_mag_axis", "Z_mag_axis")):
    column = TARGETS.index(target)
    for name, predictions in VARIANTS.items():
        axis.plot(relative_time[shown_rows], (predictions[shown_rows, column] - targets[shown_rows, column]) * 1000,
                  color=colors[name], lw=1, label=shown_names[name])
    axis.axhline(0, color="#bbbbbb", lw=0.5)
    axis.set_xlabel("relativní čas výboje")
    axis.set_ylabel("chyba predikce (mm)")
    axis.set_title(f"{target}: chyba v jednom výboji")
axes[1].legend(fontsize=6)
fig.tight_layout()
fig.savefig(OUT / "ipp1-time.png")
print("\n".join(lines))
