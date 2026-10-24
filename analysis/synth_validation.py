"""Uzavřený test receptu sítě s maskou na SIMULOVANÝCH rovnováhách se známým plazmatem (ne data z COMPASSu).

    python -I analysis/synth_validation.py [--discharges 40] [--epochs 150] [--seeds 3] [--threads 2]

Vygeneruje syntetické výboje (analysis/synth_equilibrium.py), natrénuje týž recept sítě jako analysis/ipp1_common.py
(256-256-128, SiLU, AdamW, OneCycle, standardizované vstupy i cíle, ztráta maskovaná na cíle, které existují)
s GroupKFold po celých syntetických výbojích a hodnotí proti ZNÁMÉ pravdě.
Zapíše results/synthetic-validation.json; zpráva results/synthetic-validation.md vzniká ve write_report() z tohoto
JSONu a pevného textu, takže čísla a text se nemohou rozejít.

Recept je zkopírovaný, ne importovaný, protože ipp1_common při importu skončí, když chybí složka s daty ÚFP.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
import synth_equilibrium as se

TARGETS = se.TARGET_NAMES
UNIT = {"plasma_current": (1e-3, "kA"), "R_mag_axis": (1e3, "mm"), "Z_mag_axis": (1e3, "mm"), "elongation": (1.0, ""),
        "triangularity": (1.0, ""), "R_x_point": (1e3, "mm"), "Z_x_point": (1e3, "mm"), "is_limited": (1.0, "")}
NOISE_FRACTION = {"coil": 0.15, "loop": 0.09}   # z rozptylu každého signálu, jako v results/ipp1-data-checks.md
SCENARIOS = [("clean", "clean"), ("clean", "noisy"), ("noisy", "noisy")]   # (vstupy při učení, vstupy při testu)
RESULTS = Path(__file__).resolve().parent.parent / "results"


# ===================================================================================================================
# Recept z analysis/ipp1_common.py
# ===================================================================================================================
class Net(nn.Module):
    """Plně propojená síť 256-256-128 se SiLU."""

    def __init__(self, n_inputs, n_outputs, width=256):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(n_inputs, width), nn.SiLU(), nn.Linear(width, width), nn.SiLU(),
                                    nn.Linear(width, width // 2), nn.SiLU(), nn.Linear(width // 2, n_outputs))

    def forward(self, x):
        return self.layers(x)


def fit_mlp(train_inputs, train_targets, train_exists, epochs, seed=0):
    """Standardizované vstupy a cíle, ztráta maskovaná na cíle, které existují. Vrací predict(surové vstupy) -> surové cíle."""
    torch.manual_seed(seed)
    input_mean, input_std = train_inputs.mean(0), train_inputs.std(0) + 1e-9
    target_mean, target_std = np.nanmean(train_targets, 0), np.nanstd(train_targets, 0) + 1e-9
    inputs = torch.tensor((train_inputs - input_mean) / input_std, dtype=torch.float32)
    standardized_targets = torch.tensor(np.nan_to_num((train_targets - target_mean) / target_std), dtype=torch.float32)
    mask = torch.tensor(train_exists.astype(np.float32))
    net = Net(inputs.shape[1], standardized_targets.shape[1])
    optimizer = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    total_steps = epochs * ((len(inputs) + 511) // 512)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=3e-3, total_steps=total_steps)
    for _ in range(epochs):
        order = torch.randperm(len(inputs))
        for start in range(0, len(inputs), 512):
            batch = order[start:start + 512]
            loss = ((net(inputs[batch]) - standardized_targets[batch]) ** 2 * mask[batch]).sum() / mask[batch].sum()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
    net.eval()

    def predict(x):
        with torch.no_grad():
            return net(torch.tensor((x - input_mean) / input_std, dtype=torch.float32)).numpy() * target_std + target_mean
    return predict


def fit_ridge(train_inputs, train_targets, train_exists):
    """Ridge regrese zvlášť pro každý cíl na standardizovaných vstupech. Vrací predict(surové vstupy) -> cíle."""
    input_mean, input_std = train_inputs.mean(0), train_inputs.std(0) + 1e-9
    models = [Ridge(alpha=1.0).fit((train_inputs[train_exists[:, column]] - input_mean) / input_std,
                                   train_targets[train_exists[:, column], column]) for column in range(train_targets.shape[1])]
    return lambda x: np.column_stack([model.predict((x - input_mean) / input_std) for model in models])


# ===================================================================================================================
# Šum a hodnocení
# ===================================================================================================================
def add_noise(signals, rng, spread):
    """Bílý šum na kanál: 15 % (cívky) a 9 % (smyčky toku) rozptylu kanálu přes celou sadu."""
    fraction = np.r_[np.full(se.N_COILS, NOISE_FRACTION["coil"]), np.full(se.N_LOOPS, NOISE_FRACTION["loop"])]
    return (signals + rng.normal(size=signals.shape) * spread * fraction).astype(np.float32)


def score(predictions, truth, exists):
    """Souhrnná chyba proti známé pravdě: MAE / RMSE / p95 / max v jednotkách hlášení, nRMSE = RMSE / std(pravdy)."""
    result = {}
    for column, target in enumerate(TARGETS):
        has_value = exists[:, column]
        error = predictions[has_value, column].astype(np.float64) - truth[has_value, column]
        absolute_error = np.abs(error) * UNIT[target][0]
        result[target] = {"mae": float(absolute_error.mean()), "rmse": float(np.sqrt((absolute_error ** 2).mean())),
                          "p95": float(np.percentile(absolute_error, 95)), "max": float(absolute_error.max()),
                          "unit": UNIT[target][1], "nrmse": float(np.sqrt((error ** 2).mean()) / truth[has_value, column].std()),
                          "truth_std": float(truth[has_value, column].std() * UNIT[target][0])}
    has_value = exists[:, -1]
    result["is_limited"]["accuracy"] = float(((predictions[has_value, -1] > 0.5) == (truth[has_value, -1] > 0.5)).mean())
    return result


def cross_validate(data, epochs, seeds, folds=5, log=print):
    """Predikce mimo učicí sady pro ridge a MLP ve třech scénářích vstupů při učení a testu."""
    signals, truth, groups = data["X"], data["Y"], data["groups"]
    exists = ~np.isnan(truth)
    spread = signals.std(0)
    noisy_test = add_noise(signals, np.random.default_rng(1001), spread)      # jedna pevná zašuměná kopie pro test
    noisy_train = add_noise(signals, np.random.default_rng(2002), spread)     # jiný tah pro učení, jako zašuměný soubor
    inputs = {"clean": signals, "noisy_train": noisy_train, "noisy_test": noisy_test}
    results = {}
    started = time.time()
    for train_kind, test_kind in SCENARIOS:
        all_train_inputs = inputs["noisy_train" if train_kind == "noisy" else "clean"]
        all_test_inputs = inputs["noisy_test" if test_kind == "noisy" else "clean"]
        out_of_fold = {"ridge": np.zeros(truth.shape), "mlp": [np.zeros(truth.shape) for _ in range(seeds)]}
        fold_axis_errors = []
        for fold, (train, test) in enumerate(GroupKFold(n_splits=folds).split(signals, truth, groups)):
            out_of_fold["ridge"][test] = fit_ridge(all_train_inputs[train], np.nan_to_num(truth[train]), exists[train])(all_test_inputs[test])
            for seed in range(seeds):
                out_of_fold["mlp"][seed][test] = fit_mlp(all_train_inputs[train], truth[train], exists[train], epochs,
                                                         seed=100 * seed + fold)(all_test_inputs[test])
            fold_axis_errors.append(float(np.abs(out_of_fold["mlp"][0][test, 1] - truth[test, 1]).mean() * 1e3))
        name = f"train {train_kind}, test {test_kind}"
        results[name] = {"ridge": score(out_of_fold["ridge"], truth, exists),
                         "mlp_seeds": [score(predictions, truth, exists) for predictions in out_of_fold["mlp"]],
                         "mlp_fold_axis_R_mae_mm": fold_axis_errors}
        log(f"{name}: done, {time.time() - started:.0f} s; MLP R axis MAE {results[name]['mlp_seeds'][0]['R_mag_axis']['mae']:.3f} mm")
        if (train_kind, test_kind) == ("clean", "clean"):
            results[name]["oof_example"] = {"truth": truth[:, 1:3].tolist(), "pred": out_of_fold["mlp"][0][:, 1:3].tolist()}
    return results


def summarise(results):
    """Průměr a rozptyl přes semínka MLP pro každý scénář a cíl."""
    summary = {}
    for name, scenario in results.items():
        summary[name] = {"ridge": scenario["ridge"], "mlp": {}}
        for target in TARGETS:
            metrics = [key for key in scenario["mlp_seeds"][0][target] if key != "unit"]
            summary[name]["mlp"][target] = {key: float(np.mean([seed_score[target][key] for seed_score in scenario["mlp_seeds"]]))
                                            for key in metrics}
            summary[name]["mlp"][target]["mae_seed_std"] = float(np.std([seed_score[target]["mae"] for seed_score in scenario["mlp_seeds"]]))
            summary[name]["mlp"][target]["unit"] = UNIT[target][1]
        summary[name]["mlp_fold_axis_R_mae_mm"] = scenario["mlp_fold_axis_R_mae_mm"]
    return summary


def generator_checks():
    """Čísla, která ukazují, že generátor řeší rovnici, kterou slibuje (přeměřená, ne opsaná)."""
    x, y = np.meshgrid(np.linspace(0.5, 1.5, 7), np.linspace(-0.6, 0.6, 7))
    checks = {"homogeneous_residual": max(float(np.abs(d["xx"](x, y) - d["x"](x, y) / x + d["yy"](x, y)).max())
                                          for d in se.BASIS_DERIVATIVES)}
    for config in ("limited", "diverted"):
        equilibrium = se.Equilibrium(0.56, 0.2, 1.5, 0.3, 0.1, 200e3, 0.01, config)
        d = equilibrium.derivatives
        residual = d["xx"](x, y) - d["x"](x, y) / x + d["yy"](x, y) - ((1 - equilibrium.A) * x ** 2 + equilibrium.A)
        boundary_R, boundary_Z = equilibrium.boundary(2000)
        poloidal_field = np.array(equilibrium.field(boundary_R, boundary_Z))
        segments = np.stack([np.roll(boundary_R, 1) - boundary_R, np.roll(boundary_Z, 1) - boundary_Z])   # smysl +Ip v rovině (R, Z)
        checks[config] = {"source_residual": float(np.abs(residual).max()),
                          "ampere_ratio": float((poloidal_field * segments).sum() / (se.MU0 * equilibrium.Ip)),
                          "kappa_requested": 1.5, "kappa_measured": float(equilibrium.kappa_true),
                          "delta_requested": 0.3, "delta_measured": float(equilibrium.delta_true)}
    return checks


def data_stats(data):
    """Minimum, maximum a směrodatná odchylka každého cíle v jednotkách hlášení."""
    truth = data["Y"]
    return {target: {"min": float(np.nanmin(truth[:, column]) * UNIT[target][0]), "max": float(np.nanmax(truth[:, column]) * UNIT[target][0]),
                     "std": float(np.nanstd(truth[:, column]) * UNIT[target][0]), "unit": UNIT[target][1]}
            for column, target in enumerate(TARGETS)}


def run_all(discharges, slices, epochs_list, seeds, log=print):
    """Vygeneruje data, provede křížovou validaci pro každý počet epoch a vrátí (meta, běhy)."""
    data = se.generate(discharges, slices, seed=0)
    log(f"generated {len(data['X'])} rows")
    runs = {str(epochs): summarise(cross_validate(data, epochs, seeds, log=log)) for epochs in epochs_list}
    meta = {"discharges": discharges, "slices": slices, "rows": int(len(data["X"])), "epochs": epochs_list,
            "seeds": seeds, "share_limited": float(np.nanmean(data["Y"][:, -1])), "redrawn": data["n_redrawn"],
            "stats": data_stats(data), "checks": generator_checks()}
    return meta, runs


def _g(value):
    """Číslo na tři platné číslice."""
    return f"{value:.3g}"


def _table(runs_for_epochs, targets):
    """Markdown tabulka MLP přes tři scénáře pro jedno nastavení epoch."""
    names = [f"train {train}, test {test}" for train, test in SCENARIOS]
    labels = [name.replace("train ", "").replace(", test ", " to ") for name in names]
    lines = ["| target | unit | truth std | " + " | ".join(f"MAE {label} | nRMSE {label}" for label in labels) + " |",
             "|---|---|---:|" + "---:|---:|" * len(names)]
    for target in targets:
        row = f"| {target} | {UNIT[target][1] or '-'} | {_g(runs_for_epochs[names[0]]['mlp'][target]['truth_std'])} |"
        for name in names:
            metrics = runs_for_epochs[name]["mlp"][target]
            row += f" {_g(metrics['mae'])} | {_g(metrics['nrmse'])} |"
        lines.append(row)
    return "\n".join(lines)


def _ridge_table(runs_for_epochs, targets):
    """Markdown tabulka ridge baseline přes tři scénáře."""
    names = [f"train {train}, test {test}" for train, test in SCENARIOS]
    labels = [name.replace("train ", "").replace(", test ", " to ") for name in names]
    lines = ["| target | unit | " + " | ".join(f"MAE {label} | nRMSE {label}" for label in labels) + " |",
             "|---|---|" + "---:|---:|" * len(names)]
    for target in targets:
        row = f"| {target} | {UNIT[target][1] or '-'} |"
        for name in names:
            metrics = runs_for_epochs[name]["ridge"][target]
            row += f" {_g(metrics['mae'])} | {_g(metrics['nrmse'])} |"
        lines.append(row)
    return "\n".join(lines)


def write_report(json_path=RESULTS / "synthetic-validation.json", md_path=RESULTS / "synthetic-validation.md"):
    """Přepíše markdown zprávu z JSONu s čísly (text je pevný, čísla se do něj dosazují)."""
    saved = json.load(open(json_path))
    meta, runs = saved["meta"], saved["runs"]
    epochs_low, epochs_high = str(min(meta["epochs"])), str(max(meta["epochs"]))
    clean_to_clean, clean_to_noisy, noisy_to_noisy = (f"train {train}, test {test}" for train, test in SCENARIOS)
    long_run, short_run = runs[epochs_high], runs[epochs_low]
    checks = meta["checks"]
    stats = meta["stats"]
    fold_errors = ", ".join(f"{value:.2f}" for value in long_run[clean_to_clean]["mlp_fold_axis_R_mae_mm"])

    def table_value(run, scenario, target, metric="mae"):
        return _g(run[scenario]["mlp"][target][metric])
    stats_rows = "\n".join(f"| {target} | {stats[target]['unit'] or '-'} | {_g(stats[target]['min'])} | {_g(stats[target]['max'])} | {_g(stats[target]['std'])} |"
                           for target in TARGETS)
    md = f"""# Synthetic validation: a known plasma, simulated probe signals

**SIMULATED, NOT COMPASS DATA.** No IPP file was read or copied; the vessel contour, the probe layout and
every parameter range below are invented and only COMPASS-sized. Produced by `analysis/synth_validation.py`
(numbers in `results/synthetic-validation.json`), generator in `analysis/synth_equilibrium.py`,
walk-through in `notebooks/10_synthetic_validation.ipynb`.

## Plain reading (read this first)

- This is the closed test that `docs/internal/review-physics.md` (H1, section 2) asks for: the truth is known
  because we built the plasma. It shows that **the method can recover a known plasma from simulated probe
  signals**: the same masked network recipe as the main work gets the magnetic axis to
  {table_value(long_run, clean_to_clean, 'R_mag_axis')} mm (R) and {table_value(long_run, clean_to_clean, 'Z_mag_axis')} mm (Z), the elongation to {table_value(long_run, clean_to_clean, 'elongation')},
  the triangularity to {table_value(long_run, clean_to_clean, 'triangularity')} and the lower X point to {table_value(long_run, clean_to_clean, 'R_x_point')} mm (R) and
  {table_value(long_run, clean_to_clean, 'Z_x_point')} mm (Z), on whole synthetic discharges it never saw ({epochs_high} epochs, clean signals, mean absolute error
  against the known truth).
- With white noise of the size of the organizers' noisy file (15 % of the spread on the coils, 9 % on the flux loops)
  the same quantities degrade to {table_value(long_run, clean_to_noisy, 'R_mag_axis')} mm, {table_value(long_run, clean_to_noisy, 'Z_mag_axis')} mm, {table_value(long_run, clean_to_noisy, 'elongation')},
  {table_value(long_run, clean_to_noisy, 'triangularity')}, {table_value(long_run, clean_to_noisy, 'R_x_point')} mm and {table_value(long_run, clean_to_noisy, 'Z_x_point')} mm when the network was trained on clean
  signals: noise at that size is the dominant error source, several times the clean error.
- **It says nothing about the real COMPASS reference labels**, about how close the reference reconstruction is to the real
  plasma, or about real probe calibration. The errors here are against an analytic truth; the 0.13 mm and 0.38 mm in
  `ipp1-final.md` and `ipp1-baseline.md` are agreements with the institute's reconstruction. The two sets of numbers are
  not comparable and neither is a bound on the other: the synthetic family has about seven free parameters, so the 24
  signals overdetermine it far more than they do a real plasma (see "What is NOT simulated").
- The synthetic clean error is not zero ({table_value(long_run, clean_to_clean, 'R_mag_axis')} mm on the axis) although the family is deterministic and noise
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
  {checks['homogeneous_residual']:.1e}; largest `|Delta* psi - source|` {checks['limited']['source_residual']:.1e} (limited) and
  {checks['diverted']['source_residual']:.1e} (diverted); Ampere's law, loop integral of `B.dl` over `mu0 Ip` along the traced boundary,
  {checks['limited']['ampere_ratio']:.4f} and {checks['diverted']['ampere_ratio']:.4f}; requested to measured shape for one example
  (kappa 1.5, delta 0.3): limited {checks['limited']['kappa_measured']:.4f} and {checks['limited']['delta_measured']:.4f},
  diverted {checks['diverted']['kappa_measured']:.4f} and {checks['diverted']['delta_measured']:.4f} (the diverted values include the
  X point as the bottom).

Spread of the truth over the {meta['rows']} rows:

| target | unit | min | max | std |
|---|---|---:|---:|---:|
{stats_rows}

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
- Epochs: {epochs_low} (the recipe's default) and {epochs_high}. With about {meta['rows'] * 4 // 5} training rows, 60 epochs is only about
  {60 * ((meta['rows'] * 4 // 5 + 511) // 512)} optimiser steps and the network is under-trained, so both settings are given in full. Neither was tuned further.
  Each MLP number is the mean over {meta['seeds']} seeds of the pooled out-of-fold error.
- MAE is in mm for positions, kA for the current and dimensionless for kappa, delta and `is_limited` (for the last one it is the
  mean absolute difference of the network output and the 0/1 flag; the accuracy is in the JSON). nRMSE is the pooled RMSE divided by the
  standard deviation of the truth, so 1.0 is the error of always guessing the mean.

## Results: MLP, {epochs_high} epochs

{_table(long_run, TARGETS)}

Fold-to-fold spread of the R axis MAE for clean to clean (seed 0, mm): {fold_errors}.

## Results: MLP, {epochs_low} epochs

{_table(short_run, TARGETS)}

## Results: ridge baseline (independent of the epochs)

{_ridge_table(long_run, TARGETS)}

## What these numbers do and do not support

- Supported: on simulated static equilibria of this family, with exact invented probes, a 107 k-parameter network trained on
  whole discharges recovers the axis, elongation, triangularity and X point of a discharge it has not seen to a small fraction of the spread of the truth
  (nRMSE {table_value(long_run, clean_to_clean, 'R_mag_axis', 'nrmse')} for R axis, {table_value(long_run, clean_to_clean, 'Z_mag_axis', 'nrmse')} for Z axis, {table_value(long_run, clean_to_clean, 'R_x_point', 'nrmse')} for the X point R,
  clean signals). On clean signals ridge regression is clearly worse on every position-like target (they are not linear in the
  probe signals), while the current is nearly linear in the signals (ridge nRMSE {_g(long_run[clean_to_clean]['ridge']['plasma_current']['nrmse'])},
  network {table_value(long_run, clean_to_clean, 'plasma_current', 'nrmse')}).
- Supported: noise at the size of the organizers' noisy file moves the axis error from about a millimetre to several millimetres.
  Training on one fixed noisy copy did not reduce it on the radial axis ({table_value(short_run, clean_to_noisy, 'R_mag_axis')} mm trained clean against
  {table_value(short_run, noisy_to_noisy, 'R_mag_axis')} mm trained noisy at {epochs_low} epochs, {table_value(long_run, clean_to_noisy, 'R_mag_axis')} against {table_value(long_run, noisy_to_noisy, 'R_mag_axis')} mm at {epochs_high}),
  and under noise ridge is as good as the network on the radial axis ({_g(long_run[noisy_to_noisy]['ridge']['R_mag_axis']['mae'])} mm). That the long run
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--discharges", type=int, default=40)
    parser.add_argument("--slices", type=int, default=100)
    parser.add_argument("--epochs", type=int, nargs="+", default=[60, 400])
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--out", default=str(RESULTS / "synthetic-validation.json"))
    parser.add_argument("--report", action="store_true", help="only rewrite the markdown report from the json")
    args = parser.parse_args()
    if args.report:
        write_report(args.out)
        return
    torch.set_num_threads(args.threads)
    started = time.time()
    meta, runs = run_all(args.discharges, args.slices, args.epochs, args.seeds)
    meta["seconds"] = time.time() - started
    json.dump({"meta": meta, "runs": runs}, open(args.out, "w"), indent=1)
    write_report(args.out)
    print(json.dumps({key: value for key, value in meta.items() if key not in ("stats", "checks")}))


if __name__ == "__main__":
    main()
