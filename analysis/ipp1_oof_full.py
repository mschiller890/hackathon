#!/usr/bin/env python
"""Out-of-fold predictions of ALL 31 targets of equil_data.csv, so the viewer can draw the predicted plasma outline.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_oof_full.py [--epochs 60] [--folds 5] [--from-csv]

Same protocol as ipp1_oof.py (GroupKFold by discharge, same folds, same masked MLP, 60 epochs), but the network has 31
outputs instead of 16: the extra 15 are the geometry the outline needs (a, R_geom, Z_geom, the four extreme points and the
four squareness columns). Plasma current is overridden by a ridge regression (linear in the 24 inputs: 0.035 kA against
1.5 kA of the MLP, see results/ipp1-improve.md).

Writes under $HACKATHON_HOME/out:
  ipp1-predictions-full.csv   discharge, time, fold, <target>_pred for all 31 targets
  ipp1-oof-full.md            per-target errors and outline errors
  ipp1-outline-check.png      true against predicted outline of two held-out discharges at three times each
--from-csv skips the training and rebuilds the report and the figure from the existing CSV.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import torch

from ipp1_common import DATA, OUT, fit_mlp, fit_ridge, group_folds

torch.set_num_threads(2)

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=60)
ap.add_argument("--folds", type=int, default=5)
ap.add_argument("--from-csv", action="store_true")
args = ap.parse_args()

df = pd.read_csv(DATA / "equil_data.csv")
df["is_limited"] = df["is_limited"].astype(float)
X_COLS = [c for c in df.columns if c.startswith(("IPR", "FL"))]
ALL = [c for c in df.columns if c not in X_COLS and c not in ("time", "discharge")]  # the 31 targets
assert len(ALL) == 31, ALL
X = df[X_COLS].values.astype(np.float32)
Y = df[ALL].values.astype(np.float32)
M = ~np.isnan(Y)
G = df["discharge"].values
J_IP = ALL.index("plasma_current")
PRED_CSV = OUT / "ipp1-predictions-full.csv"

if not args.from_csv:
    pred = np.full(Y.shape, np.nan, dtype=np.float32)
    fold = np.zeros(len(X), dtype=int)
    for k, (tr, te) in enumerate(group_folds(X, Y, G, args.folds)):
        predict, _, _ = fit_mlp(X[tr], Y[tr], M[tr], args.epochs, seed=k)
        p = predict(X[te])
        # plasma current is linear in the measurements: a ridge fit beats the network by a factor of about 40
        p[:, J_IP] = fit_ridge(X[tr], Y[tr][:, [J_IP]], M[tr][:, [J_IP]])(X[te])[:, 0]
        pred[te] = p
        fold[te] = k
        print(f"fold {k + 1}/{args.folds} done", flush=True)
    out = df[["discharge", "time"]].copy()
    out["fold"] = fold
    for j, t in enumerate(ALL):
        out[f"{t}_pred"] = pred[:, j]
    OUT.mkdir(exist_ok=True)
    out.to_csv(PRED_CSV, index=False, float_format="%.6g")
    print(f"wrote {PRED_CSV}: {len(out)} rows")

P = pd.read_csv(PRED_CSV)
assert (P["discharge"].values == G).all() and np.allclose(P["time"].values, df["time"].values), "row order differs"
pred = P[[f"{t}_pred" for t in ALL]].values.astype(np.float64)
Yd = df[ALL].values.astype(np.float64)

# ---- per-target errors ------------------------------------------------------------------------------------------------
GEOM = ["a", "R_geom", "Z_geom", "R_top", "Z_top", "R_bottom", "Z_bottom", "R_outer", "Z_outer", "R_inner", "Z_inner",
        "squareness_upper_outer", "squareness_upper_inner", "squareness_lower_outer", "squareness_lower_inner"]
METRES = {t for t in ALL if t.startswith(("R_", "Z_")) or t == "a"}


def unit(t):
    return (1000.0, "mm") if t in METRES else (1e-3, "kA") if t == "plasma_current" else (1.0, "")


rows = []
for j, t in enumerate(ALL):
    k = M[:, j]
    e = pred[k, j] - Yd[k, j]
    s, u = unit(t)
    ae = np.abs(e) * s
    rows.append(dict(target=t, unit=u or "raw", n=int(k.sum()), mae=ae.mean(), median=np.median(ae), p95=np.percentile(ae, 95),
                     p99=np.percentile(ae, 99), max=ae.max(), spread=Yd[k, j].std() * s,
                     r2=1 - (e ** 2).sum() / ((Yd[k, j] - Yd[k, j].mean()) ** 2).sum()))
err = pd.DataFrame(rows).set_index("target")
lim = M[:, ALL.index("is_limited")]
acc = float(((pred[lim, ALL.index("is_limited")] > 0.5) == (Yd[lim, ALL.index("is_limited")] > 0.5)).mean())


# ---- outline, same construction as boundary() in viewer/index.html (Luce 2013 superellipses) ---------------------------
def boundary(g, n=60):
    """g maps a column name to an array over rows (or a scalar). Returns R, Z of shape (rows, 4n)."""
    quads = [("upper_outer", "outer", "top", False), ("upper_inner", "inner", "top", True),
             ("lower_inner", "inner", "bottom", False), ("lower_outer", "outer", "bottom", True)]
    Rs_, Zs_ = [], []
    phi = np.linspace(0, np.pi / 2, n)
    for q, side, tip, rev in quads:
        diag = 1 / np.sqrt(2) + np.asarray(g["squareness_" + q], float) * (1 - 1 / np.sqrt(2))
        p = -np.log(2) / np.log(np.clip(diag, 0.01, 0.99))
        Rs, Zs, Rt, Zt = (np.asarray(g[f"{c}_{s}"], float) for c, s in (("R", side), ("Z", side), ("R", tip), ("Z", tip)))
        e = (2 / p)[..., None]
        qr = Rt[..., None] + (Rs - Rt)[..., None] * np.cos(phi) ** e
        qz = Zs[..., None] + (Zt - Zs)[..., None] * np.sin(phi) ** e
        if rev:
            qr, qz = qr[..., ::-1], qz[..., ::-1]
        Rs_.append(qr)
        Zs_.append(qz)
    return np.concatenate(Rs_, -1), np.concatenate(Zs_, -1)


NAMES = ["R_top", "Z_top", "R_bottom", "Z_bottom", "R_outer", "Z_outer", "R_inner", "Z_inner",
         "squareness_upper_outer", "squareness_upper_inner", "squareness_lower_outer", "squareness_lower_inner"]
ok = np.isfinite(Yd[:, [ALL.index(n) for n in NAMES]]).all(1)
gt = {n: Yd[ok, ALL.index(n)] for n in NAMES}
gp = {n: pred[ok, ALL.index(n)] for n in NAMES}
Rt_, Zt_ = boundary(gt)
Rp_, Zp_ = boundary(gp)
# vertex distance (same parameter phi on both outlines) and a symmetric Hausdorff distance, both in mm
vert = np.hypot(Rp_ - Rt_, Zp_ - Zt_) * 1000
haus = np.empty(len(Rt_))
for i in range(0, len(Rt_), 400):
    a = np.stack([Rt_[i:i + 400], Zt_[i:i + 400]], -1)
    b = np.stack([Rp_[i:i + 400], Zp_[i:i + 400]], -1)
    d = np.linalg.norm(a[:, :, None, :] - b[:, None, :, :], axis=-1)
    haus[i:i + 400] = np.maximum(d.min(2).max(1), d.min(1).max(1)) * 1000
diag_pred = 1 / np.sqrt(2) + np.stack([gp[n] for n in NAMES[8:]], 1) * (1 - 1 / np.sqrt(2))
clamped = float(((diag_pred < 0.01) | (diag_pred > 0.99)).any(1).mean())
diag_true = 1 / np.sqrt(2) + np.stack([gt[n] for n in NAMES[8:]], 1) * (1 - 1 / np.sqrt(2))
q = lambda v: f"{np.mean(v):.2f} / {np.median(v):.2f} / {np.percentile(v, 95):.2f} / {np.percentile(v, 99):.2f} / {np.max(v):.1f}"

# the discharge whose mean Hausdorff is the median of all discharges, and the one at the 95th percentile (no cherry-picking)
dis = df.loc[ok, "discharge"].values
per = pd.Series(haus).groupby(dis).mean().sort_values()
d_med, d_p95 = per.index[len(per) // 2], per.index[int(0.95 * (len(per) - 1))]

# ---- report -----------------------------------------------------------------------------------------------------------
L = ["# Out-of-fold predictions of all 31 targets (for the viewer outline)", "",
     f"`analysis/ipp1_oof_full.py`: GroupKFold by discharge, {args.folds} folds (same folds as `ipp1_oof.py`), masked MLP "
     f"256-256-128 on the 24 inputs, {args.epochs} epochs, standardised targets, mask for missing values; 31 outputs. "
     "Plasma current replaced by a ridge regression. Data: `out/ipp1-predictions-full.csv` "
     f"({len(P)} rows, columns discharge, time, fold, `<target>_pred`). Every row is predicted by a network that never saw its discharge.",
     "", "## Per-target error (all out-of-fold rows where the target exists)", "",
     "Unit mm for R, Z and a (metres in the data), kA for the current, raw for elongation, triangularity, squareness, is_limited.", "",
     "| target | unit | rows | MAE | median | p95 | p99 | max | std of target | R2 |", "|---|---|---|---|---|---|---|---|---|---|"]
for t, r in err.iterrows():
    L.append(f"| {t} | {r.unit} | {r.n} | {r.mae:.4g} | {r['median']:.3g} | {r.p95:.3g} | {r.p99:.3g} | {r['max']:.4g} | {r.spread:.3g} | {r.r2:.4f} |")
L += ["", f"is_limited accuracy (threshold 0.5): {acc:.4f}.", "",
      "## Outline error (what the viewer draws)", "",
      f"Outline = four superellipses with 60 points each, built from the 12 boundary columns exactly as `boundary()` in `viewer/index.html` "
      f"(rows with all 12 true columns: {int(ok.sum())} of {len(df)}). Distance between the true and the predicted outline in mm, "
      "mean / median / p95 / p99 / max over rows:", "",
      f"- Hausdorff distance (worst gap between the two curves): {q(haus)}",
      f"- distance between points at the same angle: {q(vert.mean(1))} (mean over the 240 vertices of a row), {q(vert.max(1))} (worst vertex of a row)",
      f"- rows where a predicted squareness leaves the range the construction accepts (clamped to 0.01..0.99 of the diagonal): {clamped * 100:.2f} %"
      f" (true data: {float(((diag_true < 0.01) | (diag_true > 0.99)).any(1).mean()) * 100:.2f} %)",
      "", "By configuration (Hausdorff mean / median / p95 mm; MAE mm of Z_inner; MAE of squareness_upper_inner and squareness_lower_inner):", ""]
LIM = df.loc[ok, "is_limited"].values > 0.5
for name, sel in (("limited", LIM), ("diverted", ~LIM)):
    zi = np.abs(pred[ok][sel, ALL.index("Z_inner")] - Yd[ok][sel, ALL.index("Z_inner")]) * 1000
    sq = [np.abs(pred[ok][sel, ALL.index(n)] - Yd[ok][sel, ALL.index(n)]).mean() for n in ("squareness_upper_inner", "squareness_lower_inner")]
    L.append(f"- {name} ({int(sel.sum())} rows): {haus[sel].mean():.2f} / {np.median(haus[sel]):.2f} / {np.percentile(haus[sel], 95):.2f}; "
             f"Z_inner {zi.mean():.2f}; squareness_upper_inner {sq[0]:.4f}, squareness_lower_inner {sq[1]:.4f}")
L += [
      "", f"Figure `out/ipp1-outline-check.png`: held-out discharge {d_med} (median of the per-discharge mean Hausdorff, {per[d_med]:.2f} mm) "
      f"and discharge {d_p95} (95th percentile, {per[d_p95]:.2f} mm), at 25, 55 and 85 % of the discharge.", ""]
(OUT / "ipp1-oof-full.md").write_text("\n".join(L))
print("\n".join(L))

# ---- figure -----------------------------------------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axs = plt.subplots(2, 3, figsize=(12, 9.5))
for r, d in enumerate((d_med, d_p95)):
    idx = np.where(df["discharge"].values == d)[0]
    idx = idx[ok[idx]]
    for c, f in enumerate((0.25, 0.55, 0.85)):
        i = idx[int(f * (len(idx) - 1))]
        g1 = {n: Yd[i, ALL.index(n)] for n in NAMES}
        g2 = {n: pred[i, ALL.index(n)] for n in NAMES}
        a, b = boundary(g1), boundary(g2)
        ax = axs[r, c]
        ax.plot(a[0], a[1], "k-", lw=2, label="true")
        ax.plot(b[0], b[1], "r--", lw=2, label="predicted")
        dd = np.linalg.norm(np.stack(a, -1)[:, None] - np.stack(b, -1)[None], axis=-1)
        h = max(dd.min(1).max(), dd.min(0).max()) * 1000
        for n, s in (("R_geom", "Z_geom"),):
            ax.plot(Yd[i, ALL.index(n)], Yd[i, ALL.index(s)], "k+", ms=9)
            ax.plot(pred[i, ALL.index(n)], pred[i, ALL.index(s)], "rx", ms=7)
        ax.set_aspect("equal")
        ax.set_title(f"discharge {d}, t = {df['time'].values[i]:.3f} s, "
                     f"{'limited' if df['is_limited'].values[i] > 0.5 else 'diverted'}\nHausdorff gap {h:.2f} mm", fontsize=10)
        ax.set_xlabel("R (m)")
        ax.set_ylabel("Z (m)")
        ax.grid(alpha=0.3)
        if r == 0 and c == 0:
            ax.legend(loc="upper left", fontsize=9)
fig.suptitle("Held-out discharges: true against out-of-fold predicted outline (viewer boundary construction)")
fig.tight_layout()
fig.savefig(OUT / "ipp1-outline-check.png", dpi=110)
print("wrote", OUT / "ipp1-outline-check.png")
