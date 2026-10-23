"""Shared code for the IPP task 1 experiments: data loading, the masked network, scoring.

Everything reads the data from $HACKATHON_HOME/data/raw (never from the repository) and
writes to $HACKATHON_HOME/out. Rows of one discharge are near copies, so every split here
is by whole discharges.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

ROOT = Path(os.environ.get("HACKATHON_HOME", "."))
OUT = ROOT / "out"
DATA = ROOT / "data/raw/ipp1-magnetic/uloha_1-magneticka_data"
if not DATA.exists():
    raise SystemExit(f"Data folder not found: {DATA}\nSet HACKATHON_HOME to the hackathon/ folder that holds "
                     "data/raw/ipp1-magnetic/uloha_1-magneticka_data/ (HACKATHON_HOME is "
                     f"{'unset' if 'HACKATHON_HOME' not in os.environ else 'set to ' + os.environ['HACKATHON_HOME']}).")
OUT.mkdir(parents=True, exist_ok=True)

# Targets that exist only in one configuration are NaN elsewhere: R_x_point.. and the strike
# points in the divertor configuration, R_limiter and Z_limiter when the plasma is limited.
TARGETS = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity",
           "triangularity_upper", "triangularity_lower", "R_x_point", "Z_x_point",
           "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2",
           "R_limiter", "Z_limiter", "is_limited"]
# (factor, unit) that turns the raw value into the unit used in reports: metres to mm, A to kA.
UNIT = {t: (1000.0, "mm") for t in TARGETS if t.startswith(("R_", "Z_"))}
UNIT.update({"plasma_current": (1e-3, "kA"), "elongation": (1.0, ""), "triangularity": (1.0, ""),
             "triangularity_upper": (1.0, ""), "triangularity_lower": (1.0, ""), "is_limited": (1.0, "")})


def load(noisy=False):
    """Return (frame, X, Y, groups, mask). Y has NaN where a target does not exist; mask is ~isnan(Y)."""
    df = pd.read_csv(DATA / ("equil_data_noisy.csv" if noisy else "equil_data.csv"))
    df["is_limited"] = df["is_limited"].astype(float)
    x_cols = [c for c in df.columns if c.startswith(("IPR", "FL"))]
    X = df[x_cols].values.astype(np.float32)
    Y = df[TARGETS].values.astype(np.float32)
    return df, X, Y, df["discharge"].values, ~np.isnan(Y)


def group_folds(X, Y, groups, n_splits=5):
    return list(GroupKFold(n_splits=n_splits).split(X, Y, groups))


class Net(nn.Module):
    def __init__(self, n_in, n_out, h=256):
        super().__init__()
        self.f = nn.Sequential(nn.Linear(n_in, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU(),
                               nn.Linear(h, h // 2), nn.SiLU(), nn.Linear(h // 2, n_out))

    def forward(self, x):
        return self.f(x)


def fit_mlp(xtr, ytr, mtr, epochs=60, seed=0):
    """Train on standardized inputs and targets with a loss masked to the targets that exist.

    Returns (predict, net, (input_mean, input_std)); predict maps raw inputs to raw targets.
    """
    torch.manual_seed(seed)
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-9
    ym, ys = np.nanmean(ytr, 0), np.nanstd(ytr, 0) + 1e-9
    xt = torch.tensor((xtr - mu) / sd)
    yt = torch.tensor(np.nan_to_num((ytr - ym) / ys))
    mt = torch.tensor(mtr.astype(np.float32))
    net = Net(xt.shape[1], yt.shape[1])
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    steps = epochs * ((len(xt) + 511) // 512)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=steps)
    for _ in range(epochs):
        perm = torch.randperm(len(xt))
        for i in range(0, len(xt), 512):
            b = perm[i:i + 512]
            loss = ((net(xt[b]) - yt[b]) ** 2 * mt[b]).sum() / mt[b].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
    net.eval()

    def predict(x):
        with torch.no_grad():
            return net(torch.tensor((x - mu) / sd)).numpy() * ys + ym
    return predict, net, (mu, sd)


def fit_ridge(xtr, ytr, mtr):
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-9
    models = [Ridge(alpha=1.0).fit((xtr[mtr[:, j]] - mu) / sd, ytr[mtr[:, j], j]) for j in range(ytr.shape[1])]
    return lambda x: np.column_stack([m.predict((x - mu) / sd) for m in models])


def score(pred, y, m):
    """Per target: MAE in report units, R squared, RMSE relative to the spread; accuracy for is_limited."""
    res = {}
    for j, t in enumerate(TARGETS):
        k = m[:, j]
        e = pred[k, j] - y[k, j]
        scale, unit = UNIT[t]
        res[t] = {"mae": float(np.abs(e).mean() * scale), "unit": unit,
                  "r2": float(1 - (e ** 2).sum() / ((y[k, j] - y[k, j].mean()) ** 2).sum()),
                  "nrmse": float(np.sqrt((e ** 2).mean()) / y[k, j].std())}
    res["is_limited"]["accuracy"] = float(((pred[m[:, -1], -1] > 0.5) == (y[m[:, -1], -1] > 0.5)).mean())
    return res


def score_extended(pred, y, m):
    """Pooled metrics per target over all given rows (not averaged over folds): MAE, median, RMSE, p95, p99, max
    of the absolute error in report units, plus nRMSE and R2 against the pooled spread."""
    res = {}
    for j, t in enumerate(TARGETS):
        k = m[:, j]
        e = pred[k, j].astype(np.float64) - y[k, j]
        a = np.abs(e) * UNIT[t][0]
        res[t] = {"mae": float(a.mean()), "median": float(np.median(a)), "rmse": float(np.sqrt((a ** 2).mean())),
                  "p95": float(np.percentile(a, 95)), "p99": float(np.percentile(a, 99)), "max": float(a.max()),
                  "unit": UNIT[t][1], "nrmse": float(np.sqrt((e ** 2).mean()) / y[k, j].std()),
                  "r2": float(1 - (e ** 2).sum() / ((y[k, j] - y[k, j].mean()) ** 2).sum())}
    return res
