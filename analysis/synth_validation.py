"""Closed test of the masked-MLP recipe on SIMULATED equilibria with a known plasma (not COMPASS data).

    python -I analysis/synth_validation.py [--discharges 40] [--epochs 150] [--seeds 3] [--threads 2]

Generates synthetic discharges (analysis/synth_equilibrium.py), trains the same network recipe as
analysis/ipp1_common.py (256-256-128, SiLU, AdamW, OneCycle, standardised inputs and targets, loss masked to
the targets that exist) with GroupKFold by whole synthetic discharge, and scores against the KNOWN truth.
Writes results/synthetic-validation.json; the report results/synthetic-validation.md is written by
synth_report() from that json plus fixed text, so numbers and prose cannot drift apart.

The recipe is copied, not imported, because ipp1_common exits at import when the IPP data folder is missing.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import synth_equilibrium as se

TARGETS = se.TARGET_NAMES
UNIT = {"plasma_current": (1e-3, "kA"), "R_mag_axis": (1e3, "mm"), "Z_mag_axis": (1e3, "mm"), "elongation": (1.0, ""),
        "triangularity": (1.0, ""), "R_x_point": (1e3, "mm"), "Z_x_point": (1e3, "mm"), "is_limited": (1.0, "")}
NOISE_FRACTION = {"coil": 0.15, "loop": 0.09}   # of the spread of each signal, as in results/ipp1-data-checks.md
SCENARIOS = [("clean", "clean"), ("clean", "noisy"), ("noisy", "noisy")]   # (train inputs, test inputs)
RESULTS = Path(__file__).resolve().parent.parent / "results"


# ---------- the recipe of analysis/ipp1_common.py ----------
class Net(nn.Module):
    def __init__(self, n_in, n_out, h=256):
        super().__init__()
        self.f = nn.Sequential(nn.Linear(n_in, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU(),
                               nn.Linear(h, h // 2), nn.SiLU(), nn.Linear(h // 2, n_out))

    def forward(self, x):
        return self.f(x)


def fit_mlp(xtr, ytr, mtr, epochs, seed=0):
    """Standardised inputs and targets, loss masked to the targets that exist. Returns predict(raw x) -> raw y."""
    torch.manual_seed(seed)
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-9
    ym, ys = np.nanmean(ytr, 0), np.nanstd(ytr, 0) + 1e-9
    xt = torch.tensor((xtr - mu) / sd, dtype=torch.float32)
    yt = torch.tensor(np.nan_to_num((ytr - ym) / ys), dtype=torch.float32)
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
            return net(torch.tensor((x - mu) / sd, dtype=torch.float32)).numpy() * ys + ym
    return predict


def fit_ridge(xtr, ytr, mtr):
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-9
    models = [Ridge(alpha=1.0).fit((xtr[mtr[:, j]] - mu) / sd, ytr[mtr[:, j], j]) for j in range(ytr.shape[1])]
    return lambda x: np.column_stack([m.predict((x - mu) / sd) for m in models])


# ---------- noise and scoring ----------
def add_noise(X, rng, spread):
    """White noise per channel: 15 % (coils) and 9 % (flux loops) of the channel's spread over the whole set."""
    frac = np.r_[np.full(se.N_COILS, NOISE_FRACTION["coil"]), np.full(se.N_LOOPS, NOISE_FRACTION["loop"])]
    return (X + rng.normal(size=X.shape) * spread * frac).astype(np.float32)


def score(pred, y, m):
    """Pooled error against the known truth: MAE / RMSE / p95 / max in report units, nRMSE = RMSE / std(truth)."""
    res = {}
    for j, t in enumerate(TARGETS):
        k = m[:, j]
        e = pred[k, j].astype(np.float64) - y[k, j]
        a = np.abs(e) * UNIT[t][0]
        res[t] = {"mae": float(a.mean()), "rmse": float(np.sqrt((a ** 2).mean())), "p95": float(np.percentile(a, 95)),
                  "max": float(a.max()), "unit": UNIT[t][1], "nrmse": float(np.sqrt((e ** 2).mean()) / y[k, j].std()),
                  "truth_std": float(y[k, j].std() * UNIT[t][0])}
    k = m[:, -1]
    res["is_limited"]["accuracy"] = float(((pred[k, -1] > 0.5) == (y[k, -1] > 0.5)).mean())
    return res


def cross_validate(data, epochs, seeds, folds=5, log=print):
    """Out-of-fold predictions for ridge and the MLP in the three train/test input scenarios."""
    X, Y, G = data["X"], data["Y"], data["groups"]
    M = ~np.isnan(Y)
    spread = X.std(0)
    Xn_test = add_noise(X, np.random.default_rng(1001), spread)      # one fixed noisy copy for testing
    Xn_train = add_noise(X, np.random.default_rng(2002), spread)     # a different draw for training, like a noisy file
    inputs = {"clean": X, "noisy_train": Xn_train, "noisy_test": Xn_test}
    out = {}
    t0 = time.time()
    for tr_in, te_in in SCENARIOS:
        xtr_all = inputs["noisy_train" if tr_in == "noisy" else "clean"]
        xte_all = inputs["noisy_test" if te_in == "noisy" else "clean"]
        oof = {"ridge": np.zeros(Y.shape), "mlp": [np.zeros(Y.shape) for _ in range(seeds)]}
        fold_axis = []
        for k, (tr, te) in enumerate(GroupKFold(n_splits=folds).split(X, Y, G)):
            oof["ridge"][te] = fit_ridge(xtr_all[tr], np.nan_to_num(Y[tr]), M[tr])(xte_all[te])
            for s in range(seeds):
                oof["mlp"][s][te] = fit_mlp(xtr_all[tr], Y[tr], M[tr], epochs, seed=100 * s + k)(xte_all[te])
            fold_axis.append(float(np.abs(oof["mlp"][0][te, 1] - Y[te, 1]).mean() * 1e3))
        name = f"train {tr_in}, test {te_in}"
        out[name] = {"ridge": score(oof["ridge"], Y, M),
                     "mlp_seeds": [score(p, Y, M) for p in oof["mlp"]],
                     "mlp_fold_axis_R_mae_mm": fold_axis}
        log(f"{name}: done, {time.time() - t0:.0f} s; MLP R axis MAE {out[name]['mlp_seeds'][0]['R_mag_axis']['mae']:.3f} mm")
        if (tr_in, te_in) == ("clean", "clean"):
            out[name]["oof_example"] = {"truth": Y[:, 1:3].tolist(), "pred": oof["mlp"][0][:, 1:3].tolist()}
    return out


def summarise(res):
    """Mean and spread over the MLP seeds, per scenario and target."""
    summ = {}
    for name, r in res.items():
        summ[name] = {"ridge": r["ridge"], "mlp": {}}
        for t in TARGETS:
            keys = [k for k in r["mlp_seeds"][0][t] if k != "unit"]
            summ[name]["mlp"][t] = {k: float(np.mean([s[t][k] for s in r["mlp_seeds"]])) for k in keys}
            summ[name]["mlp"][t]["mae_seed_std"] = float(np.std([s[t]["mae"] for s in r["mlp_seeds"]]))
            summ[name]["mlp"][t]["unit"] = UNIT[t][1]
        summ[name]["mlp_fold_axis_R_mae_mm"] = r["mlp_fold_axis_R_mae_mm"]
    return summ


def generator_checks():
    """Numbers that show the generator solves the equation it claims to (re-measured, not typed in)."""
    x, y = np.meshgrid(np.linspace(0.5, 1.5, 7), np.linspace(-0.6, 0.6, 7))
    out = {"homogeneous_residual": max(float(np.abs(d["xx"](x, y) - d["x"](x, y) / x + d["yy"](x, y)).max())
                                       for d in se._BASIS_D)}
    for cfg in ("limited", "diverted"):
        eq = se.Equilibrium(0.56, 0.2, 1.5, 0.3, 0.1, 200e3, 0.01, cfg)
        d = eq.d
        res = d["xx"](x, y) - d["x"](x, y) / x + d["yy"](x, y) - ((1 - eq.A) * x ** 2 + eq.A)
        bR, bZ = eq.boundary(2000)
        Bp = np.array(eq.field(bR, bZ))
        dl = np.stack([np.roll(bR, 1) - bR, np.roll(bZ, 1) - bZ])   # the sense of +Ip in the (R, Z) plane
        out[cfg] = {"source_residual": float(np.abs(res).max()),
                    "ampere_ratio": float((Bp * dl).sum() / (se.MU0 * eq.Ip)),
                    "kappa_requested": 1.5, "kappa_measured": float(eq.kappa_true),
                    "delta_requested": 0.3, "delta_measured": float(eq.delta_true)}
    return out


def data_stats(data):
    Y = data["Y"]
    return {t: {"min": float(np.nanmin(Y[:, j]) * UNIT[t][0]), "max": float(np.nanmax(Y[:, j]) * UNIT[t][0]),
                "std": float(np.nanstd(Y[:, j]) * UNIT[t][0]), "unit": UNIT[t][1]} for j, t in enumerate(TARGETS)}


def run_all(discharges, slices, epochs_list, seeds, log=print):
    data = se.generate(discharges, slices, seed=0)
    log(f"generated {len(data['X'])} rows")
    runs = {str(e): summarise(cross_validate(data, e, seeds, log=log)) for e in epochs_list}
    meta = {"discharges": discharges, "slices": slices, "rows": int(len(data["X"])), "epochs": epochs_list,
            "seeds": seeds, "share_limited": float(np.nanmean(data["Y"][:, -1])), "redrawn": data["n_redrawn"],
            "stats": data_stats(data), "checks": generator_checks()}
    return meta, runs


def _g(v):
    return f"{v:.3g}"


def _table(runs_e, targets):
    """Markdown table of the MLP over the three scenarios for one epochs setting."""
    names = [f"train {a}, test {b}" for a, b in SCENARIOS]
    label = [n.replace("train ", "").replace(", test ", " to ") for n in names]
    lines = ["| target | unit | truth std | " + " | ".join(f"MAE {lb} | nRMSE {lb}" for lb in label) + " |",
             "|---|---|---:|" + "---:|---:|" * len(names)]
    for t in targets:
        row = f"| {t} | {UNIT[t][1] or '-'} | {_g(runs_e[names[0]]['mlp'][t]['truth_std'])} |"
        for n in names:
            m = runs_e[n]["mlp"][t]
            row += f" {_g(m['mae'])} | {_g(m['nrmse'])} |"
        lines.append(row)
    return "\n".join(lines)


def _ridge_table(runs_e, targets):
    names = [f"train {a}, test {b}" for a, b in SCENARIOS]
    label = [n.replace("train ", "").replace(", test ", " to ") for n in names]
    lines = ["| target | unit | " + " | ".join(f"MAE {lb} | nRMSE {lb}" for lb in label) + " |",
             "|---|---|" + "---:|---:|" * len(names)]
    for t in targets:
        row = f"| {t} | {UNIT[t][1] or '-'} |"
        for n in names:
            m = runs_e[n]["ridge"][t]
            row += f" {_g(m['mae'])} | {_g(m['nrmse'])} |"
        lines.append(row)
    return "\n".join(lines)


def write_report(json_path=RESULTS / "synthetic-validation.json", md_path=RESULTS / "synthetic-validation.md"):
    d = json.load(open(json_path))
    meta, runs = d["meta"], d["runs"]
    e_lo, e_hi = str(min(meta["epochs"])), str(max(meta["epochs"]))
    cc, cn, nn_ = (f"train {a}, test {b}" for a, b in SCENARIOS)
    hi, lo = runs[e_hi], runs[e_lo]
    ck = meta["checks"]
    st = meta["stats"]
    folds = ", ".join(f"{v:.2f}" for v in hi[cc]["mlp_fold_axis_R_mae_mm"])

    def m(run, scen, t, k="mae"):
        return _g(run[scen]["mlp"][t][k])
    all_t = TARGETS
    stat_rows = "\n".join(f"| {t} | {st[t]['unit'] or '-'} | {_g(st[t]['min'])} | {_g(st[t]['max'])} | {_g(st[t]['std'])} |"
                          for t in TARGETS)
    md = f"""# Synthetic validation: a known plasma, simulated probe signals

**SIMULATED, NOT COMPASS DATA.** No IPP file was read or copied; the vessel contour, the probe layout and
every parameter range below are invented and only COMPASS-sized. Produced by `analysis/synth_validation.py`
(numbers in `results/synthetic-validation.json`), generator in `analysis/synth_equilibrium.py`,
walk-through in `notebooks/10_synthetic_validation.ipynb`.

## Plain reading (read this first)

- This is the closed test that `docs/review-physics.md` (H1, section 2) asks for: the truth is known
  because we built the plasma. It shows that **the method can recover a known plasma from simulated probe
  signals**: the same masked network recipe as the main work gets the magnetic axis to
  {m(hi, cc, 'R_mag_axis')} mm (R) and {m(hi, cc, 'Z_mag_axis')} mm (Z), the elongation to {m(hi, cc, 'elongation')},
  the triangularity to {m(hi, cc, 'triangularity')} and the lower X point to {m(hi, cc, 'R_x_point')} mm (R) and
  {m(hi, cc, 'Z_x_point')} mm (Z), on whole synthetic discharges it never saw ({e_hi} epochs, clean signals, mean absolute error
  against the known truth).
- With white noise of the size of the organizers' noisy file (15 % of the spread on the coils, 9 % on the flux loops)
  the same quantities degrade to {m(hi, cn, 'R_mag_axis')} mm, {m(hi, cn, 'Z_mag_axis')} mm, {m(hi, cn, 'elongation')},
  {m(hi, cn, 'triangularity')}, {m(hi, cn, 'R_x_point')} mm and {m(hi, cn, 'Z_x_point')} mm when the network was trained on clean
  signals: noise at that size is the dominant error source, several times the clean error.
- **It says nothing about the real COMPASS reference labels**, about how close the reference reconstruction is to the real
  plasma, or about real probe calibration. The errors here are against an analytic truth; the 0.13 mm and 0.38 mm in
  `ipp1-final.md` and `ipp1-baseline.md` are agreements with the institute's reconstruction. The two sets of numbers are
  not comparable and neither is a bound on the other: the synthetic family has about seven free parameters, so the 24
  signals overdetermine it far more than they do a real plasma (see "What is NOT simulated").
- The synthetic clean error is not zero ({m(hi, cc, 'R_mag_axis')} mm on the axis) although the family is deterministic and noise
  free: that is the approximation error of this network on {meta['rows'] * 4 // 5} training rows, a floor that any real-data
  error also contains.

## What is simulated

- **Equations.** Solov'ev solutions of the Grad-Shafranov equation (constant p' and FF'), built after
  Cerfon and Freidberg, Phys. Plasmas 17, 032502 (2010), as `Delta* psi = (1 - A) x^2 + A` in units of the plasma major
  radius, plus 7 (limited) or 12 (diverted) homogeneous solutions whose coefficients are fixed by requiring the
  boundary `psi = 0` to pass through the outer, inner and top points of a requested shape with matching curvatures,
  and, for the diverted family, through a lower X point.
- **Two configurations.** `limited`: up-down symmetric, no X point (target columns `R_x_point`, `Z_x_point` are missing, so
  the masked loss and the masked score are exercised exactly as on the real file); `diverted`: lower single null.
  `is_limited` is 1 for the first family. Share of limited rows: {meta['share_limited']:.3f}.
- **Size.** R0 about 0.56 m, minor radius a about 0.2 m. Each discharge draws base values: plasma major radius 0.545 to
  0.575 m, a 0.185 to 0.205 m, vertical shift +-2 cm, requested elongation 1.05 to 1.6 (limited) or 1.3 to 1.55 (diverted),
  requested triangularity 0.0 to 0.35, profile parameter A -0.25 to 0.35, peak plasma current 120 to 260 kA; then every
  parameter drifts smoothly in time (amplitudes in `make_discharge`, elongation clipped to 1.0 to 1.8, triangularity to -0.05
  to 0.45) and the current ramps up and down (lowest value 42 kA).
- **Truth is measured, not copied.** The axis is the Newton-refined minimum of psi, the X point the Newton-refined saddle,
  the boundary extremes are Newton-refined points with `psi = 0` and the right derivative zero, and
  `elongation = (Z_top - Z_bottom) / (2 a)`, `triangularity = (delta_upper + delta_lower) / 2` are computed from those
  extremes (for the diverted family the bottom is the X point, so the measured elongation is about 1.05 times the requested one).
  Plasma current is set by integrating `-Delta* psi / (mu0 R)` over the plasma.
- **Probes.** 16 tangential poloidal field probes (equal arc length) and 8 flux loops (equal angle) on an invented rounded-box
  contour (half widths 0.30 m by 0.55 m about R = 0.56 m), evaluated **exactly** from the analytic psi and its derivatives
  (`B_R = -(1/R) dpsi/dZ`, `B_Z = (1/R) dpsi/dR`, flux `2 pi psi`). The inputs are named `IPR01..16` and `FL01..08`
  only to match the recipe; they are not the COMPASS channels.
- **Discharges.** {meta['discharges']} synthetic discharges of {meta['slices']} time slices = {meta['rows']} rows. Each discharge draws a
  base shape and lets every parameter drift smoothly (two random low-frequency sinusoids) so that rows of one discharge are near
  copies, as in the real file; splits are by whole discharge (GroupKFold, 5 folds). {meta['redrawn']} discharges were redrawn
  because a slice failed to solve or left the vessel.
- **Generator checks (measured when this report was written).** Largest `|Delta* phi|` of the homogeneous solutions
  {ck['homogeneous_residual']:.1e}; largest `|Delta* psi - source|` {ck['limited']['source_residual']:.1e} (limited) and
  {ck['diverted']['source_residual']:.1e} (diverted); Ampere's law, loop integral of `B.dl` over `mu0 Ip` along the traced boundary,
  {ck['limited']['ampere_ratio']:.4f} and {ck['diverted']['ampere_ratio']:.4f}; requested to measured shape for one example
  (kappa 1.5, delta 0.3): limited {ck['limited']['kappa_measured']:.4f} and {ck['limited']['delta_measured']:.4f},
  diverted {ck['diverted']['kappa_measured']:.4f} and {ck['diverted']['delta_measured']:.4f} (the diverted values include the
  X point as the bottom).

Spread of the truth over the {meta['rows']} rows:

| target | unit | min | max | std |
|---|---|---:|---:|---:|
{stat_rows}

## What is NOT simulated

- **No real vessel currents and no coil currents.** psi is a Solov'ev solution everywhere, so outside the separatrix it is the
  analytic continuation, which carries toroidal current there and has no external coils. A real tokamak has a vacuum
  outside the plasma plus coil and wall-current fields. The probe signals therefore carry a different mixture of
  information than real ones; whether that makes the task easier or harder was not tested.
- **No real calibration.** No probe position or orientation errors, gains, offsets, integrator drift, cross-talk or
  missing channels. The flux is measured relative to the separatrix flux (the gauge is fixed by `psi = 0` on the boundary).
  The probe layout is invented, not the COMPASS layout.
- **No EFIT or any reconstruction code.** The truth is an analytic solution, not the output of a reconstruction with its grid,
  constraints and regularisation. Nothing here measures the agreement between a network and such a code.
- **No disruptions, ELMs or fast dynamics, no eddy-current delays.** Every slice is an independent static equilibrium whose
  parameters drift smoothly.
- **A narrow family.** About seven free parameters (R0p, a, kappa, delta, A, vertical shift, Ip) plus the configuration, so
  24 signals overdetermine it. Real profiles are far richer. This makes the test optimistic about recovering shape from probes.
- **No consistent vacuum exterior (tried, dropped).** An attempt to replace the continuation by the field of the plasma current
  (current filaments from the Solov'ev interior) plus fitted external coil filaments was ill-posed: the fit to the boundary flux left
  0.25 % residual, needed coil currents of order 1e8 A and gave flux-loop values that were not credible. It is not used anywhere.
- **No limiter physics and no upper X point or double null.** `limited` is only the symmetric no-X-point family.
- **No second solver.** The finite-difference fixed-boundary Grad-Shafranov solve named as a second choice was not built;
  the analytic family was enough for the closed test and the time was spent on checking it.
- Noise is white and independent per row, with no drift (as measured in `ipp1-data-checks.md` for the organizers' file).

## Method

- Network: the recipe of `analysis/ipp1_common.py` (256-256-128, SiLU, AdamW lr 2e-3 weight decay 1e-4, OneCycle max lr 3e-3,
  batch 512, standardised inputs and targets, loss masked to the targets that exist), copied into `analysis/synth_validation.py`.
  Targets: {", ".join(TARGETS)}.
- Baseline: ridge regression per target on standardised inputs (the same one `ipp1_common.py` uses).
- Splits: 5-fold GroupKFold by synthetic discharge; every row is predicted once out of fold and the errors are pooled.
- Noise: each channel gets white noise of 15 % (coils) or 9 % (flux loops) of that channel's standard deviation over all
  rows, as `ipp1-data-checks.md` measured for the organizers' noisy file. Training noise and test noise are two different draws.
- Scenarios: train clean to test clean; train clean to test noisy; train noisy to test noisy.
- Epochs: {e_lo} (the recipe's default) and {e_hi}. With about {meta['rows'] * 4 // 5} training rows, 60 epochs is only about
  {60 * ((meta['rows'] * 4 // 5 + 511) // 512)} optimiser steps and the network is under-trained, so both settings are given in full. Neither was tuned further.
  Each MLP number is the mean over {meta['seeds']} seeds of the pooled out-of-fold error.
- MAE is in mm for positions, kA for the current and dimensionless for kappa, delta and `is_limited` (for the last one it is the
  mean absolute difference of the network output and the 0/1 flag; the accuracy is in the JSON). nRMSE is the pooled RMSE divided by the
  standard deviation of the truth, so 1.0 is the error of always guessing the mean.

## Results: MLP, {e_hi} epochs

{_table(hi, all_t)}

Fold-to-fold spread of the R axis MAE for clean to clean (seed 0, mm): {folds}.

## Results: MLP, {e_lo} epochs

{_table(lo, all_t)}

## Results: ridge baseline (independent of the epochs)

{_ridge_table(hi, all_t)}

## What these numbers do and do not support

- Supported: on simulated static equilibria of this family, with exact invented probes, a 107 k-parameter network trained on
  whole discharges recovers the axis, elongation, triangularity and X point of a discharge it has not seen to a small fraction of the spread of the truth
  (nRMSE {m(hi, cc, 'R_mag_axis', 'nrmse')} for R axis, {m(hi, cc, 'Z_mag_axis', 'nrmse')} for Z axis, {m(hi, cc, 'R_x_point', 'nrmse')} for the X point R,
  clean signals). On clean signals ridge regression is clearly worse on every position-like target (they are not linear in the
  probe signals), while the current is nearly linear in the signals (ridge nRMSE {_g(hi[cc]['ridge']['plasma_current']['nrmse'])},
  network {m(hi, cc, 'plasma_current', 'nrmse')}).
- Supported: noise at the size of the organizers' noisy file moves the axis error from about a millimetre to several millimetres.
  Training on one fixed noisy copy did not reduce it on the radial axis ({m(lo, cn, 'R_mag_axis')} mm trained clean against
  {m(lo, nn_, 'R_mag_axis')} mm trained noisy at {e_lo} epochs, {m(hi, cn, 'R_mag_axis')} against {m(hi, nn_, 'R_mag_axis')} mm at {e_hi}),
  and under noise ridge is as good as the network on the radial axis ({_g(hi[nn_]['ridge']['R_mag_axis']['mae'])} mm). That the long run
  overfits the one noise draw is a plausible reading, not tested. All of this is about this synthetic noise and this family; the
  main work found a gain from noise training on the real noisy file, and this test neither confirms nor contradicts that.
- Not supported: any statement about COMPASS, about how close the reference reconstruction is to the real plasma, about calibration, drift
  or disruptions, or that the real-data errors would be larger or smaller than these. The honest sentence for the talk is: "On a plasma we
  simulated ourselves, so that the truth is known, the same network recovers the axis to about a millimetre from clean probe signals.
  That tests the method, not the COMPASS labels."

## Reproduce

```
pip install numpy scipy scikit-learn torch
python -I analysis/synth_equilibrium.py                       # generator self-checks, about 10 s
python -I analysis/synth_validation.py --epochs 60 400 --seeds 3 --threads 2   # about {meta['seconds'] / 60:.0f} min, writes the json
python -I analysis/synth_validation.py --report               # rewrites this file from the json
```
"""
    Path(md_path).write_text(md, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--discharges", type=int, default=40)
    ap.add_argument("--slices", type=int, default=100)
    ap.add_argument("--epochs", type=int, nargs="+", default=[60, 400])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=str(RESULTS / "synthetic-validation.json"))
    ap.add_argument("--report", action="store_true", help="only rewrite the markdown report from the json")
    args = ap.parse_args()
    if args.report:
        write_report(args.out)
        return
    torch.set_num_threads(args.threads)
    t0 = time.time()
    meta, runs = run_all(args.discharges, args.slices, args.epochs, args.seeds)
    meta["seconds"] = time.time() - t0
    json.dump({"meta": meta, "runs": runs}, open(args.out, "w"), indent=1)
    write_report(args.out)
    print(json.dumps({k: v for k, v in meta.items() if k not in ("stats", "checks")}))


if __name__ == "__main__":
    main()
