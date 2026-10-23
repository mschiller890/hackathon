#!/usr/bin/env python
"""Learning curves using nested subsets of TRAINING discharges and fixed test folds."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipp1_common import OUT, group_folds, load, score
from ipp1_robustness import figure_grid, fit_checked, options, write_report


def training_subset(train, groups, fraction, seed):
    if not 0 < fraction <= 1:
        raise ValueError("Training fraction must be in (0, 1]")
    order = np.random.default_rng(seed).permutation(np.unique(groups[train]))
    selected = order[:max(1, int(np.ceil(fraction * len(order))))]
    return train[np.isin(groups[train], selected)]


def main():
    args = options(__doc__)
    started = time.perf_counter()
    _, x, y, groups, mask = load()
    fractions = [.05, .10, .25, .50, 1.0]
    records = []
    for fold, (tr, te) in enumerate(group_folds(x, y, groups, args.folds)):
        for fraction in fractions:
            subset = training_subset(tr, groups, fraction, args.seed + fold)
            assert not set(groups[subset]) & set(groups[te])
            predict = fit_checked(x[subset], y[subset], mask[subset], args.epochs, fold)
            records.append({"fold": fold, "case": f"fraction_{fraction:g}", "fraction": fraction,
                            "training_discharges": len(np.unique(groups[subset])), "training_rows": len(subset),
                            "test_discharges": len(np.unique(groups[te])), "test_rows": len(te),
                            "scores": score(predict(x[te]), y[te], mask[te])})
        print(f"learning curve fold {fold + 1}/{args.folds}: {time.perf_counter() - started:.1f}s", flush=True)
    notes = ["Shared masked MLP, group-held-out evaluation; a fixed test fold across every training fraction.",
             "5, 10, 25, 50, 100 percent of training discharges; ceil rounding, nested seeded group subsets. All rows of a selected discharge are retained.",
             "Input and target normalization use only the selected training subset. Seeds for model fitting equal fold index.",
             "Fixed epochs, not fixed optimizer updates: small datasets get fewer updates. The curve combines information availability and this training-budget effect.",
             "One subset ordering and one initialization per fold; between-fold SD is not a confidence interval. No test-based choice of model or sample count."]
    avg = write_report("learning_curve", args, records, notes, started)
    fig, axes = figure_grid("IPP 1 · How much training data is enough?")
    counts = [np.mean([r["training_discharges"] for r in records if r["fraction"] == f]) for f in fractions]
    for ax, target in zip(axes, ["R_mag_axis", "Z_mag_axis", "elongation", "Z_limiter"]):
        means = [avg[f"fraction_{f:g}"][target]["mae"] for f in fractions]
        ax.plot(counts, means, "o-", color="#176b87")
        for fold in range(args.folds):
            rows = [r for r in records if r["fold"] == fold]
            ax.plot([r["training_discharges"] for r in rows], [r["scores"][target]["mae"] for r in rows],
                    color="#176b87", alpha=.18, linewidth=1)
        ax.set(title=target, xlabel="Training discharges (bold = fold mean)",
               ylabel=f"MAE ({avg['fraction_1'][target]['unit'] or 'dimensionless'})")
        ax.grid(alpha=.2)
    fig.savefig(OUT / "ipp1-learning_curve.png", dpi=150)
    print(f"Saved {OUT / 'ipp1-learning_curve.json'}", flush=True)


if __name__ == "__main__":
    main()
