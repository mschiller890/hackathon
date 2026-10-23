#!/usr/bin/env python
"""Write viewer/data.js for the plasma shape viewer (the file is gitignored: the IPP data must not be published).

    HACKATHON_HOME=<hackathon folder> python -I analysis/export_viewer_data.py

Joins the true values (equil_data.csv) with the out-of-fold predictions (out/ipp1-predictions.csv) row by row,
keeps every STEP-th row of every discharge and writes one script that the page loads from the same folder.
The wall outline is added when data/raw/organizers/COMPASS_stena.csv exists.
"""
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("HACKATHON_HOME", "."))
DATA = ROOT / "data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv"
PRED = ROOT / "out/ipp1-predictions.csv"
WALL = ROOT / "data/raw/organizers/COMPASS_stena.csv"
TARGET = Path(__file__).resolve().parents[1] / "viewer/data.js"
STEP = 2  # time resolution is far finer than the screen needs; this keeps the page near 7 MB

TRUE_COLS = ["time", "is_limited", "plasma_current", "elongation", "triangularity", "triangularity_upper",
             "triangularity_lower", "a", "R_geom", "Z_geom", "R_top", "Z_top", "R_bottom", "Z_bottom",
             "R_outer", "Z_outer", "R_inner", "Z_inner", "squareness_upper_outer", "squareness_upper_inner",
             "squareness_lower_outer", "squareness_lower_inner", "R_mag_axis", "Z_mag_axis", "R_x_point",
             "Z_x_point", "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2",
             "R_limiter", "Z_limiter"]


def column(values, decimals):
    return [None if np.isnan(v) else round(float(v), decimals) for v in values]


true = pd.read_csv(DATA, usecols=["discharge"] + TRUE_COLS)
pred = pd.read_csv(PRED)
# The prediction file prints time with fewer digits, so a join on the float time loses rows; the rows have
# the same order, which the checks below enforce.
assert len(true) == len(pred), (len(true), len(pred))
assert (true["discharge"].values == pred["discharge"].values).all()
assert np.allclose(true["time"].values, pred["time"].values, atol=1e-5)
pred_cols = [c for c in pred.columns if c.endswith("_pred")]
frame = pd.concat([true.reset_index(drop=True), pred[pred_cols + ["fold"]].reset_index(drop=True)], axis=1)
frame["is_limited"] = frame["is_limited"].astype(float)

discharges = []
for did, g in frame.groupby("discharge", sort=True):
    g = g.iloc[::STEP]
    err = np.hypot(g["R_mag_axis"] - g["R_mag_axis_pred"], g["Z_mag_axis"] - g["Z_mag_axis_pred"]) * 1000
    cols = {c: column(g[c].values, 0 if c == "plasma_current" else 5) for c in TRUE_COLS + pred_cols}
    cols["is_limited_pred"] = column(g["is_limited_pred"].values, 3)
    discharges.append({"id": int(did), "fold": int(g["fold"].iloc[0]), "n": len(g),
                       "axisErrMm": round(float(err.mean()), 2),
                       "limitedShare": round(float(g["is_limited"].mean()), 3), "c": cols})

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
           "predColumns": pred_cols, "discharges": discharges}
TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text("window.VIEWER = " + json.dumps(payload, separators=(",", ":")) + ";\n", encoding="utf-8")
print(f"wrote {TARGET}: {len(discharges)} discharges, {sum(d['n'] for d in discharges)} rows, "
      f"{TARGET.stat().st_size / 1e6:.1f} MB, wall: {'yes' if wall else 'no'}")
