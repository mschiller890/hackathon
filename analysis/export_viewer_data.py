#!/usr/bin/env python
"""Write viewer/data.js for the plasma shape viewer (the file is gitignored: the IPP data must not be published).

    HACKATHON_HOME=<hackathon folder> python -I analysis/export_viewer_data.py

Two sources of predictions, chosen by what exists in out/:
  shipped   (default, needs out/ipp1-final-cache/ made by analysis/make_all.py) the predictions of the shipped recipe `cand` of
            ipp1_final.py for all 149 discharges: the 30 locked discharges (results/ipp1-locked-test-ids.txt) from the model trained on
            the 119 development discharges, the 119 development discharges out of fold. The model predicts 16 targets, so no predicted
            outline is drawn, only the predicted points. The noise mode compares `cand` (trained on clean data) with `base_aug`
            (the baseline network trained with noise), both on the provided noisy inputs.
  baseline  (fallback) the out-of-fold predictions of the baseline network, out/ipp1-predictions[-full|-noise].csv, with the outline.
The true values come from equil_data.csv row by row; every STEP-th row of every discharge is kept and written to one script that the page loads
from the same folder. The wall outline is added when data/raw/organizers/COMPASS_stena.csv exists.
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("HACKATHON_HOME", "."))
DATA = ROOT / "data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv"
PRED = ROOT / "out/ipp1-predictions.csv"
FULL = ROOT / "out/ipp1-predictions-full.csv"  # all 31 targets incl. the geometry columns; draws the predicted outline
NOISE = ROOT / "out/ipp1-predictions-noise.csv"
WALL = ROOT / "data/raw/organizers/COMPASS_stena.csv"
REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "viewer/data.js"
CACHE = ROOT / "out/ipp1-final-cache"
LATENCY_MD = REPO / "results/ipp1-latency-shipped.md"
SHIPPED_FILES = [f"{kind}_{r}.npz" for kind in ("locked",) for r in ("cand", "base_aug")] + [f"cv_{r}_{k}.npz" for r in ("cand", "base_aug") for k in range(5)]
STEP = 3  # time resolution is far finer than the screen needs; with the noise predictions this keeps the page near 12 MB

TRUE_COLS = ["time", "is_limited", "plasma_current", "elongation", "triangularity", "triangularity_upper",
             "triangularity_lower", "a", "R_geom", "Z_geom", "R_top", "Z_top", "R_bottom", "Z_bottom",
             "R_outer", "Z_outer", "R_inner", "Z_inner", "squareness_upper_outer", "squareness_upper_inner",
             "squareness_lower_outer", "squareness_lower_inner", "R_mag_axis", "Z_mag_axis", "R_x_point",
             "Z_x_point", "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2",
             "R_limiter", "Z_limiter"]


def column(values, decimals):
    return [None if np.isnan(v) else round(float(v), decimals) for v in values]


def shipped_frame(true):
    """Columns of the shipped recipe for every row of `true`, the id list of the locked discharges and the fold of each development discharge."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
    import ipp1_final as F
    (df, X, Y, G, M), _ = F.aligned_data()
    assert len(df) == len(true) and (df["discharge"].values == true["discharge"].values).all()
    assert np.allclose(df["time"].values, true["time"].values, atol=1e-5)
    lock, dev_idx, lock_idx = F.split(G)
    lk = F.assemble("locked", None, ["cand", "base_aug"])
    cv = F.assemble("cv", None, ["cand", "base_aug"], 5)
    assert all(np.array_equal(lk[r]["idx"], lock_idx) and np.array_equal(cv[r]["idx"], dev_idx) for r in ("cand", "base_aug"))
    # (suffix, recipe, inputs): the shipped recipe on clean inputs; on the provided noisy inputs the same recipe (it fails there) and the noise-trained baseline
    sets = [("_pred", "cand", "clean"), ("_clean_on_noisy", "cand", "noisy"), ("_hardened_on_noisy", "base_aug", "noisy")]
    cols = {}
    for suffix, recipe, inputs in sets:
        P = np.full((len(true), len(F.TARGETS)), np.nan, dtype=np.float32)
        P[lock_idx], P[dev_idx] = lk[recipe][inputs], cv[recipe][inputs]
        cols.update({t + suffix: P[:, j] for j, t in enumerate(F.TARGETS)})
    fold = np.full(len(true), -1)
    for k, (_, te) in enumerate(F.group_folds(X[dev_idx], Y[dev_idx], G[dev_idx], 5)):
        fold[dev_idx[te]] = k
    return pd.DataFrame(cols), [int(i) for i in lock], fold


def shipped_latency():
    """The shipped pair's per sample latency from results/ipp1-latency-shipped.md: the slower (limited) path is the one to quote."""
    text = LATENCY_MD.read_text(encoding="utf-8")
    cpu = re.search(r"CPU: ([^(]+)\(", text).group(1).strip()
    row = lambda name: [float(v) for v in re.search(rf"\| {name} \| ([\d.]+) \| ([\d.]+) \|", text).groups()]
    (lim_med, lim_p99), (div_med, _) = row("numpy_end_to_end_limited"), row("numpy_end_to_end_diverted")
    return {"cpu": cpu, "medianMs": lim_med, "p99Ms": lim_p99, "divertedMedianMs": div_med, "source": "results/ipp1-latency-shipped.md"}


true = pd.read_csv(DATA, usecols=["discharge"] + TRUE_COLS)
shipped = all((CACHE / f).exists() for f in SHIPPED_FILES) and LATENCY_MD.exists()
lock_ids, latency, noise_cols = [], None, []
if shipped:
    pred, lock_ids, fold = shipped_frame(true)
    latency = shipped_latency()
    pred_cols = [c for c in pred.columns if c.endswith("_pred")]
    noise_cols = [c for c in pred.columns if c.endswith(("_clean_on_noisy", "_hardened_on_noisy"))]
    parts = [true.reset_index(drop=True), pred, pd.Series(fold, name="fold")]
else:
    pred = pd.read_csv(FULL if FULL.exists() else PRED)
    # The prediction file prints time with fewer digits, so a join on the float time loses rows; the rows have
    # the same order, which the checks below enforce.
    assert len(true) == len(pred), (len(true), len(pred))
    assert (true["discharge"].values == pred["discharge"].values).all()
    assert np.allclose(true["time"].values, pred["time"].values, atol=1e-5)
    pred_cols = [c for c in pred.columns if c.endswith("_pred")]
    parts = [true.reset_index(drop=True), pred[pred_cols + ["fold"]].reset_index(drop=True)]
    if NOISE.exists():  # a plain and a hardened network on the provided noisy inputs, same row order
        noise = pd.read_csv(NOISE)
        assert len(noise) == len(true) and (noise["discharge"].values == true["discharge"].values).all()
        assert np.allclose(noise["time"].values, true["time"].values, atol=1e-5)
        noise_cols = [c for c in noise.columns if c.endswith(("_clean_on_noisy", "_hardened_on_noisy"))]
        parts.append(noise[noise_cols].reset_index(drop=True))
frame = pd.concat(parts, axis=1)
frame["is_limited"] = frame["is_limited"].astype(float)

discharges, full_row_err = [], {}
for did, g_all in frame.groupby("discharge", sort=True):
    g = g_all.iloc[::STEP]
    err = np.hypot(g["R_mag_axis"] - g["R_mag_axis_pred"], g["Z_mag_axis"] - g["Z_mag_axis_pred"]) * 1000
    full_row_err[int(did)] = float(np.hypot(g_all["R_mag_axis"] - g_all["R_mag_axis_pred"], g_all["Z_mag_axis"] - g_all["Z_mag_axis_pred"]).mean() * 1000)
    cols = {c: column(g[c].values, 0 if c.startswith("plasma_current") else 5) for c in TRUE_COLS + pred_cols + noise_cols}
    for c in ["is_limited_pred"] + [n for n in noise_cols if n.startswith("is_limited")]:
        cols[c] = column(g[c].values, 3)
    discharges.append({"id": int(did), "fold": int(g["fold"].iloc[0]), "locked": int(did) in lock_ids, "n": len(g),
                       "axisErrMm": round(float(err.mean()), 2),
                       "limitedShare": round(float(g["is_limited"].mean()), 3), "c": cols})
discharges.sort(key=lambda d: (not d["locked"], d["id"]))  # the locked discharges first

wall = None
if WALL.exists():
    w = pd.read_csv(WALL)
    wall = {"R": [round(float(v), 5) for v in w["R"]], "Z": [round(float(v), 5) for v in w["Z"]]}

R_all = np.concatenate([frame["R_inner"].dropna(), frame["R_outer"].dropna()] + ([w["R"].values] if wall else []))
Z_all = np.concatenate([frame["Z_top"].dropna(), frame["Z_bottom"].dropna()] + ([w["Z"].values] if wall else []))
pad = 0.06
view = {"R": [round(float(R_all.min()) - pad, 3), round(float(R_all.max()) + pad, 3)],
        "Z": [round(float(Z_all.min()) - pad, 3), round(float(Z_all.max()) + pad, 3)]}

payload = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "step": STEP, "wall": wall, "view": view,
           "model": "shipped" if shipped else "baseline", "lockedIds": lock_ids, "latency": latency,
           "predColumns": pred_cols, "hasNoise": bool(noise_cols), "discharges": discharges}
TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text("window.VIEWER = " + json.dumps(payload, separators=(",", ":")) + ";\n", encoding="utf-8")
print(f"wrote {TARGET}: {len(discharges)} discharges, {sum(d['n'] for d in discharges)} rows, "
      f"{TARGET.stat().st_size / 1e6:.1f} MB, model: {payload['model']}, noise: {'yes' if noise_cols else 'no'}, wall: {'yes' if wall else 'no'}")
if shipped:
    print(f"locked discharges: {sum(d['locked'] for d in discharges)}; latency {latency['medianMs']} ms median ({latency['cpu']})")
