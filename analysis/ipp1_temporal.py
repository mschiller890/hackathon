#!/usr/bin/env python
"""Compare current-row and causal three-row MLPs on clean and provided noisy inputs."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipp1_common import OUT, TARGETS, UNIT, group_folds, score
from ipp1_robustness import aligned_data, figure_grid, fit_checked, options, write_report


def history_indices(groups, times, window):
    if window < 1:
        raise ValueError("Window must be positive")
    result = np.empty((len(groups), window), dtype=int)
    for group in np.unique(groups):
        rows = np.flatnonzero(groups == group)
        rows = rows[np.argsort(times[rows], kind="stable")]
        if np.any(np.diff(times[rows]) <= 0):
            raise ValueError("Times must be distinct within each discharge")
        positions = np.maximum(np.arange(len(rows))[:, None] - np.arange(window - 1, -1, -1), 0)
        result[rows] = rows[positions]
    return result


def step_errors(pred, y, mask, groups, times):
    """Error increment MAE catches jitter AND lag; a constant predictor cannot win by smoothness.

    Successive samples can be unevenly spaced: these are differences, not derivatives.
    No pair crosses a discharge or a target's missing-value boundary.
    """
    previous = history_indices(groups, times, 2)[:, 0]
    current = np.arange(len(y))
    valid = (previous != current)[:, None] & mask & mask[previous]
    delta_y = y - y[previous]
    delta_pred = pred - pred[previous]
    output = {}
    for j, target in enumerate(TARGETS):
        k = valid[:, j]
        factor = UNIT[target][0]
        output[target] = {"error_step_mae": float(np.mean(np.abs(delta_pred[k, j] - delta_y[k, j])) * factor),
                          "prediction_step_mae": float(np.mean(np.abs(delta_pred[k, j])) * factor),
                          "true_step_mae": float(np.mean(np.abs(delta_y[k, j])) * factor),
                          "pairs": int(k.sum())}
    return output


def main():
    args = options(__doc__)
    started = time.perf_counter()
    (df, x, y, groups, mask), xn = aligned_data()
    times = df.time.to_numpy()
    history = history_indices(groups, times, 3)
    assert np.all(groups[history] == groups[:, None])
    assert np.all(times[history] <= times[:, None])
    records = []
    for fold, (tr, te) in enumerate(group_folds(x, y, groups, args.folds)):
        for condition, source in [("clean", x), ("provided_noisy", xn)]:
            for window in [1, 3]:
                features = source[history[:, -window:]].reshape(len(x), -1)
                assert set(history[tr, -window:].ravel()) <= set(tr)
                assert set(history[te, -window:].ravel()) <= set(te)
                predict = fit_checked(features[tr], y[tr], mask[tr], args.epochs, fold)
                pred = predict(features[te])
                metrics = score(pred, y[te], mask[te])
                stability = step_errors(pred, y[te], mask[te], groups[te], times[te])
                for target in TARGETS:
                    metrics[target].update(stability[target])
                records.append({"fold": fold, "case": f"{condition}/window_{window}",
                                "condition": condition, "window": window, "input_columns": features.shape[1],
                                "scores": metrics})
        print(f"temporal fold {fold + 1}/{args.folds}: {time.perf_counter() - started:.1f}s", flush=True)
    notes = ["Current row versus t-2, t-1, t within the same discharge, ordered by relative time; earliest available row repeats at startup.",
             "No future row, no target history, no discharge or time as features. Whole-discharge folds prevent any window crossing train/test.",
             "Clean models train/test on clean; noisy models train/test on the provided noisy file. No interpolation across missing times.",
             "Same hidden-layer sizes and epochs; the 72-input temporal MLP has more first-layer parameters than the 24-input baseline.",
             "Stability is MAE of successive prediction-error differences, alongside true/predicted step magnitudes. Units are per observed step, not per second. Lower raw movement alone does not establish better tracking.",
             "All consecutive available times are used, including gaps. Scores use only labels that exist; step scores need both adjacent labels.",
             "Model seeds equal fold index. No hyperparameter tuning on held-out folds."]
    avg = write_report("temporal", args, records, notes, started)
    fig, axes = figure_grid("IPP 1 · Causal time context on unseen discharges")
    cases = list(avg)
    labels = ["Clean\n1 row", "Clean\n3 rows", "Noisy\n1 row", "Noisy\n3 rows"]
    for ax, (target, metric) in zip(axes, [("R_mag_axis", "mae"), ("Z_mag_axis", "mae"),
                                         ("R_mag_axis", "error_step_mae"), ("Z_mag_axis", "error_step_mae")]):
        ax.bar(labels, [avg[c][target][metric] for c in cases], color=["#9aabb1", "#176b87"] * 2)
        ax.set(title=target, ylabel="Position MAE (mm)" if metric == "mae" else "Error-step MAE (mm / step)")
        ax.grid(axis="y", alpha=.2)
    fig.savefig(OUT / "ipp1-temporal.png", dpi=150)
    print(f"Saved {OUT / 'ipp1-temporal.json'}", flush=True)


if __name__ == "__main__":
    main()
