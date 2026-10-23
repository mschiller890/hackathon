#!/usr/bin/env python
"""Does the disagreement of five networks predict the real error on held-out discharges?

On each of the 5 group folds five networks with different seeds are trained on the same data. For every held-out row
the spread (standard deviation) of the five predictions is the uncertainty and the absolute error of their mean is the
error. Reported per target: Spearman correlation between the two, the error of the 10 % most uncertain rows against
the other 90 %, and the share of the total absolute error those 10 % hold (10 % would mean the warning is useless).
The ensemble mean is also compared with the average single network.

Run: HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/ipp1_uncertainty.py [--epochs 60]
Writes out/ipp1-uncertainty.{json,md,png}.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipp1_common import OUT, TARGETS, UNIT, fit_mlp, group_folds, load
from ipp1_robustness import options

MEMBERS = 5
SHOWN = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "R_x_point", "Z_x_point", "R_limiter", "Z_limiter"]


def warning_stats(spread, error):
    """Spearman correlation and the top 10 % uncertain rows against the rest, for one target."""
    top = spread >= np.quantile(spread, .9)
    return {"spearman": float(spearmanr(spread, error)[0]),
            "mae_top10": float(error[top].mean()), "mae_rest": float(error[~top].mean()),
            "ratio": float(error[top].mean() / error[~top].mean()),
            "error_share_top10": float(error[top].sum() / error.sum())}


def main():
    args = options(__doc__)
    started = time.perf_counter()
    df, x, y, groups, mask = load()
    members = np.full((MEMBERS,) + y.shape, np.nan, dtype=np.float32)
    for f, (tr, te) in enumerate(group_folds(x, y, groups, args.folds)):
        for m in range(MEMBERS):
            predict, _, _ = fit_mlp(x[tr], y[tr], mask[tr], epochs=args.epochs, seed=1000 * f + m)
            members[m, te] = predict(x[te])
        print(f"uncertainty fold {f + 1}/{args.folds}: {time.perf_counter() - started:.0f}s", flush=True)

    mean, spread = members.mean(0), members.std(0)
    result = {}
    for j, t in enumerate(TARGETS):
        k = np.flatnonzero(mask[:, j])
        scale = UNIT[t][0]
        err = np.abs(mean[k, j] - y[k, j]) * scale
        single = np.mean([np.abs(members[m, k, j] - y[k, j]).mean() for m in range(MEMBERS)]) * scale
        result[t] = {"unit": UNIT[t][1], "rows": len(k), "mae_ensemble": float(err.mean()), "mae_single_mean": float(single),
                     "median_spread": float(np.median(spread[k, j]) * scale), **warning_stats(spread[k, j] * scale, err)}
        if t == "is_limited":
            wrong = ((mean[k, j] > .5) != (y[k, j] > .5)).astype(float)
            result[t]["accuracy_ensemble"] = float(1 - wrong.mean())
    # A single row-level warning for the main shape targets: mean standardized spread over them.
    main_j = [TARGETS.index(t) for t in ["R_mag_axis", "Z_mag_axis", "elongation", "triangularity"]]
    rows = mask[:, main_j].all(1)  # a few rows lack a label
    sd = np.nanstd(y[:, main_j], 0)
    row_spread = (spread[rows][:, main_j] / sd).mean(1)
    row_err = (np.abs(mean[rows][:, main_j] - y[rows][:, main_j]) / sd).mean(1)
    result["_row_level_main_targets"] = warning_stats(row_spread, row_err)

    notes = {"members": MEMBERS, "epochs": args.epochs, "folds": args.folds, "seconds": time.perf_counter() - started,
             "row_level": "mean over R axis, Z axis, elongation, triangularity of spread and error, each divided by the target SD"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ipp1-uncertainty.json").write_text(json.dumps({"notes": notes, "targets": result}, indent=2, allow_nan=False) + "\n")
    write_markdown(result, notes)
    plot(spread, mean, y, mask)
    print(f"Saved {OUT / 'ipp1-uncertainty.json'}", flush=True)


def write_markdown(result, notes):
    lines = ["# IPP 1: does the disagreement of five networks predict the error?", "",
             f"{MEMBERS} networks per fold, seeds differ, same data; {notes['folds']} group folds; held-out rows only. Spread = SD of the five predictions; "
             "error = absolute error of their mean. Top 10 % = the rows with the largest spread.", "",
             "| Target | Unit | Spearman | MAE top 10 % | MAE rest | Ratio | Share of all error in top 10 % | Ensemble MAE | Single net MAE |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for t in SHOWN:
        r = result[t]
        lines.append(f"| {t} | {r['unit'] or '-'} | {r['spearman']:.2f} | {r['mae_top10']:.4g} | {r['mae_rest']:.4g} | {r['ratio']:.1f}x | "
                     f"{r['error_share_top10']:.0%} | {r['mae_ensemble']:.4g} | {r['mae_single_mean']:.4g} |")
    r = result["_row_level_main_targets"]
    lines += ["", f"Row level warning ({notes['row_level']}): Spearman {r['spearman']:.2f}, top 10 % error {r['ratio']:.1f}x the rest, "
              f"holds {r['error_share_top10']:.0%} of the error.",
              f"`is_limited`: ensemble accuracy {result['is_limited']['accuracy_ensemble']:.4f}."]
    (OUT / "ipp1-uncertainty.md").write_text("\n".join(lines) + "\n")


def plot(spread, mean, y, mask):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for ax, t in zip(axes, ["R_mag_axis", "Z_limiter"]):
        j = TARGETS.index(t)
        k = np.flatnonzero(mask[:, j])
        s, e = spread[k, j] * UNIT[t][0], np.abs(mean[k, j] - y[k, j]) * UNIT[t][0]
        bins = np.quantile(s, np.linspace(0, 1, 11))
        idx = np.clip(np.digitize(s, bins[1:-1]), 0, 9)
        ax.plot(range(1, 11), [e[idx == d].mean() for d in range(10)], "o-", color="#176b87")
        ax.set(title=t, xlabel="spread decile (10 = most uncertain)", ylabel=f"mean absolute error ({UNIT[t][1] or 'dimensionless'})")
        ax.grid(alpha=.2)
    fig.suptitle("IPP 1 · Does the ensemble know when it is wrong?")
    fig.savefig(OUT / "ipp1-uncertainty.png", dpi=150)


if __name__ == "__main__":
    main()
