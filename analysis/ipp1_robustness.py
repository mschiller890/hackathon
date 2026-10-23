#!/usr/bin/env python
"""Lane R: clean/noisy training, held-out noise and drift, fixed noise augmentation.

Run with HACKATHON_HOME set and python -I. Reports stay in its out/ directory.
Also supplies reporting helpers to the other two lane-R experiments.
"""
import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import sklearn
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipp1_common import DATA, OUT, TARGETS, fit_mlp, group_folds, load, score


def corrupt(x, groups, times, scale, noise, drift, seed):
    """Gaussian row noise plus an independent Gaussian slope per discharge and coil.

    Both amplitudes are fractions of TRAINING input standard deviations. Drift is
    c*t using the supplied relative time, not physical seconds or a model input.
    """
    if noise < 0 or drift < 0:
        raise ValueError("Corruption amplitudes must be non-negative")
    rng = np.random.default_rng(seed)
    _, inverse = np.unique(groups, return_inverse=True)
    slopes = rng.normal(size=(inverse.max() + 1, x.shape[1])) * drift * scale
    result = x + rng.normal(size=x.shape) * noise * scale + slopes[inverse] * times[:, None]
    return result.astype(np.float32)


def aligned_data():
    clean = load()
    noisy = load(noisy=True)
    # The noisy file's time column differs from the clean one by float rounding (about 1e-16).
    if not (np.array_equal(clean[0].discharge, noisy[0].discharge)
            and np.allclose(clean[0].time, noisy[0].time, rtol=0, atol=1e-9)):
        raise ValueError("Clean/noisy rows must have identical discharge/time alignment")
    if not np.array_equal(clean[2], noisy[2], equal_nan=True):
        raise ValueError("Clean/noisy targets differ")
    if not np.isfinite(clean[1]).all() or not np.isfinite(noisy[1]).all():
        raise ValueError("Nonfinite model inputs")
    return clean, noisy[1]


def options(description):
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--threads", type=int, default=2)
    args = ap.parse_args()
    if args.epochs < 1 or args.folds < 2 or args.threads < 1:
        ap.error("epochs/threads must be positive; folds must be at least two")
    torch.set_num_threads(args.threads)
    return args


def fit_checked(x, y, mask, epochs, seed):
    if not mask.any(axis=0).all():
        absent = [t for t, present in zip(TARGETS, mask.any(axis=0)) if not present]
        raise ValueError(f"Training subset has no labels for {absent}")
    predict, _, _ = fit_mlp(x, y, mask, epochs=epochs, seed=seed)
    return predict


def summarize(records):
    average = {}
    for case in dict.fromkeys(r["case"] for r in records):
        scores = [r["scores"] for r in records if r["case"] == case]
        average[case] = {}
        for target in TARGETS:
            keys = scores[0][target]
            stats = {key: (keys[key] if key == "unit" else float(np.mean([s[target][key] for s in scores])))
                     for key in keys}
            stats["mae_std"] = float(np.std([s[target]["mae"] for s in scores]))
            average[case][target] = stats
    return average


def write_report(name, args, records, notes, started):
    """Save full fold-level aggregate evidence; never save input rows or predictions."""
    average = summarize(records)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (DATA / "equil_data.csv", DATA / "equil_data_noisy.csv",
                        Path(__file__), Path(__file__).with_name("ipp1_common.py"),
                        Path(sys.argv[0]).resolve())}
    payload = {"experiment": name, "options": vars(args), "notes": notes,
               "versions": {"python": platform.python_version(), "numpy": np.__version__,
                            "torch": torch.__version__, "sklearn": sklearn.__version__},
               "sha256": hashes, "seconds": time.perf_counter() - started,
               "records": records, "average": average}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"ipp1-{name}.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    lines = [f"# IPP 1: {name}", "", *notes, "",
             f"Options: `{json.dumps(vars(args))}`. Equal-weight mean across held-out folds; "
             "SD is descriptive between-fold variation, not a confidence interval."]
    for case, metrics in average.items():
        lines += ["", f"## {case}", "", "| Target | Unit | MAE | Fold SD | R2 | nRMSE |",
                  "|---|---|---:|---:|---:|---:|"]
        for target, s in metrics.items():
            lines.append(f"| {target} | {s['unit']} | {s['mae']:.6g} | {s['mae_std']:.4g} | {s['r2']:.5g} | {s['nrmse']:.5g} |")
        lines += ["", f"Configuration accuracy: {metrics['is_limited']['accuracy']:.6f}."]
        if "error_step_mae" in metrics[TARGETS[0]]:
            lines += ["", "| Target | Error-step MAE | Prediction-step MAE | True-step MAE |",
                      "|---|---:|---:|---:|"]
            for target, s in metrics.items():
                lines.append(f"| {target} | {s['error_step_mae']:.6g} | {s['prediction_step_mae']:.6g} | {s['true_step_mae']:.6g} |")
    (OUT / f"ipp1-{name}.md").write_text("\n".join(lines) + "\n")
    return average


def figure_grid(title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    fig.suptitle(title, fontsize=17)
    return fig, axes.ravel()


def main():
    args = options(__doc__)
    started = time.perf_counter()
    (df, x, y, groups, mask), xn = aligned_data()
    times = df.time.to_numpy()
    records = []
    levels = [.0, .05, .15, .30]
    for fold, (tr, te) in enumerate(group_folds(x, y, groups, args.folds)):
        assert not set(groups[tr]) & set(groups[te])
        scale = x[tr].std(axis=0)
        augmented = corrupt(x[tr], groups[tr], times[tr], scale, .15, .15, args.seed + fold)
        training = {"clean": (x[tr], y[tr], mask[tr], args.epochs),
                    "provided_noisy": (xn[tr], y[tr], mask[tr], args.epochs),
                    "augmented": (np.concatenate([x[tr], augmented]), np.tile(y[tr], (2, 1)),
                                  np.tile(mask[tr], (2, 1)), max(1, args.epochs // 2))}
        tests = {"clean": x[te], "provided_noisy": xn[te]}
        for level in levels:
            if level:
                tests[f"noise_{level:g}"] = corrupt(x[te], groups[te], times[te], scale, level, 0, args.seed + 1000 + fold)
            tests[f"drift_{level:g}"] = corrupt(x[te], groups[te], times[te], scale, .15, level, args.seed + 2000 + fold)
        for model, (xt, yt, mt, epochs) in training.items():
            predict = fit_checked(xt, yt, mt, epochs, fold)
            for condition, test in tests.items():
                records.append({"fold": fold, "case": f"{model}/{condition}",
                                "model": model, "condition": condition,
                                "train_groups": len(np.unique(groups[tr])),
                                "test_groups": len(np.unique(groups[te])),
                                "scores": score(predict(test), y[te], mask[te])})
        print(f"robustness fold {fold + 1}/{args.folds}: {time.perf_counter() - started:.1f}s", flush=True)
    notes = ["Shared masked MLP; all preprocessing fitted on training discharges only.",
             "Synthetic noise SD and slope SD are fractions of each training input's SD. Drift is independent per coil/discharge, c*t, t in relative units.",
             "Noise sweep has no drift; drift sweep adds fixed Gaussian noise of 0.15. Identical held-out corruptions are used for all models.",
             "Augmentation: original plus one fixed seeded corrupted copy (noise=0.15, drift=0.15). Half as many epochs on twice as many rows approximates the same optimizer-update budget.",
             "Model seeds equal fold index, matching the baseline. No test-based tuning; one corruption realization per fold, amplitudes fixed before the run.",
             "Averages weight folds equally and rows equally within each fold. Conditional targets are scored only where they exist."]
    avg = write_report("robustness", args, records, notes, started)
    fig, axes = figure_grid("IPP 1 · Robustness on unseen discharges")
    for ax, target in zip(axes, ["R_mag_axis", "Z_mag_axis", "elongation", "Z_limiter"]):
        for model, label in [("clean", "Clean training"), ("provided_noisy", "Noisy training"), ("augmented", "Augmented training")]:
            ax.plot(levels, [avg[f"{model}/drift_{v:g}"][target]["mae"] for v in levels], "o-", label=label)
        ax.set(title=target, xlabel="Drift slope SD / training input SD (noise SD = 0.15)",
               ylabel=f"MAE ({avg['clean/clean'][target]['unit'] or 'dimensionless'})")
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=9)
    fig.savefig(OUT / "ipp1-robustness.png", dpi=150)
    print(f"Saved {OUT / 'ipp1-robustness.json'}", flush=True)


if __name__ == "__main__":
    main()
