#!/usr/bin/env python
"""Stability of the output over the time of a discharge (REQ-003), from the out-of-fold predictions.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_time.py

Needs out/ipp1-predictions.csv (analysis/ipp1_oof.py). If out/ipp1-predictions-noise.csv exists (analysis/ipp1_oof_noise.py,
columns <target>_clean_on_noisy and <target>_hardened_on_noisy) the same numbers are computed for the noisy inputs.
Writes out/ipp1-time.{json,md,png}. All 16 targets are covered.

Metrics per target, over rows that are neighbours in time (step below 0.01 of the relative time):
- jitter ratio: RMS of the row-to-row change of the prediction / RMS of the change of the truth. It stays near 1
  whenever the truth itself moves, so it cannot detect a noisy output on its own.
- error step: RMS of the row-to-row change of the prediction ERROR (prediction minus truth), in report units. This is
  what the wobble of the output looks like; its ratio to the RMS change of the truth is given too.
- offset share: share of the squared error that is a constant offset of a whole discharge.
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
VARIANTS = {"clean": None}  # name -> prediction matrix, filled below
pr = pd.read_csv(OUT / "ipp1-predictions.csv")
assert np.array_equal(pr.discharge.values, df.discharge.values) and np.allclose(pr.time.values, df.time.values)
VARIANTS["clean"] = pr[[f"{t}_pred" for t in TARGETS]].values
noise_file = OUT / "ipp1-predictions-noise.csv"
if noise_file.exists():
    pn = pd.read_csv(noise_file)
    assert np.array_equal(pn.discharge.values, df.discharge.values) and np.allclose(pn.time.values, df.time.values)
    for kind in ("clean_on_noisy", "hardened_on_noisy"):
        VARIANTS[kind] = pn[[f"{t}_{kind}" for t in TARGETS]].values
LABEL = {"clean": "clean inputs, network trained on clean data",
         "clean_on_noisy": "noisy inputs, network trained on clean data",
         "hardened_on_noisy": "noisy inputs, network trained with noise and drift augmentation"}

bins = np.minimum((df.time.values * 10).astype(int), 9)
# Neighbouring rows of one discharge: a[i], b[i] are row positions with b the next row in time.
srt = np.lexsort((df.time.values, df.discharge.values))
a, b = srt[:-1], srt[1:]
adj = (df.discharge.values[a] == df.discharge.values[b]) & (df.time.values[b] - df.time.values[a] < 0.01)
a, b = a[adj], b[adj]


def stats(P):
    out = {"mae_by_time_decile": {}, "jitter_ratio": {}, "error_step": {}, "error_step_ratio": {}, "bias_share": {},
           "truth_step": {}}
    for t in TARGETS:
        j = TARGETS.index(t)
        k = M[:, j]
        scale = UNIT[t][0]
        err = P[:, j] - Y[:, j]
        out["mae_by_time_decile"][t] = [float(np.abs(err[k & (bins == d)]).mean() * scale) if (k & (bins == d)).any() else None
                                        for d in range(10)]
        ok = k[a] & k[b]
        rms = lambda v: float(np.sqrt(np.mean(np.square(v))))  # noqa: E731
        d_true, d_pred, d_err = (Y[b, j] - Y[a, j])[ok], (P[b, j] - P[a, j])[ok], (err[b] - err[a])[ok]
        out["truth_step"][t] = rms(d_true) * scale
        out["jitter_ratio"][t] = rms(d_pred) / rms(d_true)
        out["error_step"][t] = rms(d_err) * scale
        out["error_step_ratio"][t] = rms(d_err) / rms(d_true)
        per = pd.Series(err[k]).groupby(df.discharge.values[k])
        out["bias_share"][t] = float((per.mean() ** 2 * per.size()).sum() / (err[k] ** 2).sum())
    return out


res = {name: stats(P) for name, P in VARIANTS.items()}


def clean_json(o):
    """NaN is not valid JSON: write None."""
    if isinstance(o, dict):
        return {k: clean_json(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean_json(v) for v in o]
    return None if isinstance(o, float) and not np.isfinite(o) else o


with open(OUT / "ipp1-time.json", "w") as fh:
    json.dump(clean_json({"variants": LABEL, "n_neighbour_pairs": int(len(a)), **res["clean"], "noisy": {k: v for k, v in res.items() if k != "clean"}}),
              fh, indent=1, allow_nan=False)


def fmt(v, spec):
    return "n/a" if v is None else format(v, spec)


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
s = res["clean"]
for t in TARGETS:
    lines.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(fmt(v, ".3g") for v in s["mae_by_time_decile"][t])
                 + f" | {s['jitter_ratio'][t]:.2f} | {s['error_step'][t]:.3g} | {s['error_step_ratio'][t]:.2f} | {s['bias_share'][t]:.2f} |")
if len(VARIANTS) > 1:
    lines += ["", "## Noisy inputs (equil_data_noisy.csv, out-of-fold)", "",
              "Same metrics for the plain network on noisy inputs and for the network hardened with noise and drift augmentation. "
              "jitter = jitter ratio, step = error step in report units, ratio = error step / RMS change of the truth. "
              "A ratio near 0 means the error does not wobble from row to row; above 1 the wobble of the error is larger than the "
              "movement of the truth.", "",
              "| target | unit | truth step | jitter clean | jitter plain | jitter hardened | step clean | step plain | step hardened "
              "| ratio clean | ratio plain | ratio hardened |", "|---|---|" + "---|" * 10]
    for t in TARGETS:
        c, p, h = res["clean"], res["clean_on_noisy"], res["hardened_on_noisy"]
        lines.append(f"| {t} | {UNIT[t][1]} | {c['truth_step'][t]:.3g} | {c['jitter_ratio'][t]:.2f} | {p['jitter_ratio'][t]:.2f} | "
                     f"{h['jitter_ratio'][t]:.2f} | {c['error_step'][t]:.3g} | {p['error_step'][t]:.3g} | {h['error_step'][t]:.3g} | "
                     f"{c['error_step_ratio'][t]:.2f} | {p['error_step_ratio'][t]:.2f} | {h['error_step_ratio'][t]:.2f} |")
    for kind in ("clean_on_noisy", "hardened_on_noisy"):
        lines += ["", f"### MAE by tenth of the discharge, {LABEL[kind]}", "",
                  "| target | unit | " + " | ".join(f"{d * 10}-{d * 10 + 10} %" for d in range(10)) + " | offset share |",
                  "|---|---|" + "---|" * 11]
        for t in TARGETS:
            lines.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(fmt(v, ".3g") for v in res[kind]["mae_by_time_decile"][t])
                         + f" | {res[kind]['bias_share'][t]:.2f} |")
else:
    lines += ["", "out/ipp1-predictions-noise.csv not found: stability on noisy inputs not computed."]
(OUT / "ipp1-time.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

PLOT = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "R_x_point", "R_strike_point_1",
        "R_limiter", "Z_limiter"]
plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False, "font.size": 8})
fig, ax = plt.subplots(1, 3, figsize=(12, 3.4))
for t in PLOT:
    v = np.array([np.nan if x is None else x for x in res["clean"]["mae_by_time_decile"][t]])
    ax[0].plot(np.arange(10) * 10 + 5, v / np.nanmean(v), marker="o", label=t)
ax[0].set_xlabel("čas výboje (%)")
ax[0].set_ylabel("chyba / průměrná chyba")
ax[0].set_title("Kde v čase model chybuje")
ax[0].legend(fontsize=6)
# Only the prediction error of one discharge is drawn (not the measured signal), in mm, with the mid-ranked mean error.
colors = {"clean": "#1a1d23", "clean_on_noisy": "#8d99ae", "hardened_on_noisy": "#e07a5f"}
shown = {"clean": "čisté vstupy", "clean_on_noisy": "šum, síť na čistých datech", "hardened_on_noisy": "šum, síť s augmentací"}
j0 = TARGETS.index("R_mag_axis")
pd_err = pd.Series(np.abs(VARIANTS["clean"][:, j0] - Y[:, j0])).groupby(df.discharge.values).mean().sort_values()
g = pd_err.index[len(pd_err) // 2]
rows = np.where(df.discharge.values == g)[0]
rows = rows[np.argsort(df.time.values[rows])]
for a_, t in zip(ax[1:], ("R_mag_axis", "Z_mag_axis")):
    jj = TARGETS.index(t)
    for name, P in VARIANTS.items():
        a_.plot(df.time.values[rows], (P[rows, jj] - Y[rows, jj]) * 1000, color=colors[name], lw=1, label=shown[name])
    a_.axhline(0, color="#bbbbbb", lw=0.5)
    a_.set_xlabel("relativní čas výboje")
    a_.set_ylabel("chyba predikce (mm)")
    a_.set_title(f"{t}: chyba v jednom výboji")
ax[1].legend(fontsize=6)
fig.tight_layout()
fig.savefig(OUT / "ipp1-time.png")
print("\n".join(lines))
