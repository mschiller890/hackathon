#!/usr/bin/env python
"""REQ-B08: how much worse is the network on a family of shapes it has never seen?

Discharges are clustered on the ranks of their median elongation and triangularity. For each cluster (and two tail groups) the
network is trained without it and tested on it. The reference is the error on the very same discharges when they are
held out by the usual random 5-fold split by discharge, so a difference comes from the unseen shape and not from
the choice of discharges. `nn_distance` is how far the held-out discharges lie from the nearest training discharge in
(elongation, triangularity), in ranks: it shows how much more unusual the cluster split is than the random one.

Discharge ids are chronological, so the random split still leaves near neighbours in training (docs/internal/review-findings.md);
the random-fold error is therefore an optimistic baseline.

Run: HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/ipp1_unusual_shapes.py
Writes out/ipp1-unusual_shapes.{json,md,png}.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipp1_common import OUT, TARGETS, UNIT, fit_mlp, group_folds, load
from ipp1_robustness import options

SHOWN = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "R_x_point", "Z_x_point", "R_limiter", "Z_limiter"]
MIN_LABELS = 50  # a target is scored (and trained) only where this many labelled rows exist


def mae_by_target(pred, y, mask, rows):
    """MAE in report units per target on `rows`; None where fewer than MIN_LABELS labels exist."""
    out = {}
    for j, t in enumerate(TARGETS):
        k = rows[mask[rows, j] & ~np.isnan(pred[rows, j])]  # NaN: the target was not trained
        out[t] = float(np.abs(pred[k, j] - y[k, j]).mean() * UNIT[t][0]) if len(k) >= MIN_LABELS else None
    return out


def fit_without(x, y, mask, train, epochs, seed):
    """Fit on `train` rows, dropping targets that have too few labels there. Returns predictions for all rows (NaN where dropped)."""
    keep = np.flatnonzero(mask[train].sum(0) >= MIN_LABELS)
    predict, _, _ = fit_mlp(x[train], y[train][:, keep], mask[train][:, keep], epochs=epochs, seed=seed)
    pred = np.full(y.shape, np.nan, dtype=np.float32)
    pred[:, keep] = predict(x)
    return pred


def main():
    args = options(__doc__)
    started = time.perf_counter()
    df, x, y, groups, mask = load()
    ids = np.unique(groups)
    med = np.array([[np.nanmedian(df.elongation[groups == g]), np.nanmedian(df.triangularity[groups == g])] for g in ids])
    # Ranks, not raw values: on raw values a few extreme discharges form tiny clusters and one cluster holds almost everything,
    # and leaving that one out would just mean training on very few discharges.
    z = (np.argsort(np.argsort(med, axis=0), axis=0) + .5) / len(ids)
    label = KMeans(n_clusters=4, n_init=10, random_state=args.seed).fit_predict(z)
    # Relabel clusters by their mean elongation so the output is stable and readable.
    order = np.argsort([med[label == c, 0].mean() for c in range(4)])
    label = np.argsort(order)[label]
    holdouts = {f"cluster_{c}": ids[label == c] for c in range(4)}
    holdouts["high_triangularity_15pct"] = ids[med[:, 1] >= np.quantile(med[:, 1], .85)]
    holdouts["low_elongation_15pct"] = ids[med[:, 0] <= np.quantile(med[:, 0], .15)]

    folds = group_folds(x, y, groups, args.folds)
    oof = np.full(y.shape, np.nan, dtype=np.float32)
    fold_of = {}
    for f, (tr, te) in enumerate(folds):
        oof[te] = fit_without(x, y, mask, tr, args.epochs, f)[te]
        fold_of.update({g: f for g in np.unique(groups[te])})
    print(f"random folds done {time.perf_counter() - started:.0f}s", flush=True)

    def nn_distance(test_ids, train_ids_for):
        d = []
        for g in test_ids:
            tr = np.isin(ids, train_ids_for(g))
            d.append(np.linalg.norm(z[tr] - z[ids == g], axis=1).min())
        return float(np.mean(d))

    result = {}
    for c, (name, held) in enumerate(holdouts.items()):
        test = np.flatnonzero(np.isin(groups, held))
        train = np.flatnonzero(~np.isin(groups, held))
        pred = fit_without(x, y, mask, train, args.epochs, 100 + c)
        ref = mae_by_target(oof, y, mask, test)
        out = mae_by_target(pred, y, mask, test)
        acc = float(((pred[test, -1] > .5) == (y[test, -1] > .5)).mean())
        acc_ref = float(((oof[test, -1] > .5) == (y[test, -1] > .5)).mean())
        result[name] = {
            "discharges": len(held), "rows": len(test),
            "median_elongation": float(np.median(med[np.isin(ids, held), 0])),
            "median_triangularity": float(np.median(med[np.isin(ids, held), 1])),
            "nn_distance_cluster_out": nn_distance(held, lambda g: ids[~np.isin(ids, held)]),
            "nn_distance_random_fold": nn_distance(held, lambda g: np.unique(groups[folds[fold_of[g]][0]])),
            "mae_random_fold": ref, "mae_cluster_out": out,
            "is_limited_accuracy_random_fold": acc_ref, "is_limited_accuracy_cluster_out": acc,
        }
        print(f"{name}: {len(held)} discharges, R axis {ref['R_mag_axis']:.2f} -> {out['R_mag_axis']:.2f} mm "
              f"({time.perf_counter() - started:.0f}s)", flush=True)

    notes = {"clusters": "KMeans k=4 on the ranks of the per-discharge median of elongation and triangularity; tails are the top 15 % "
                         "triangularity and the bottom 15 % elongation discharges",
             "scoring": f"MAE per target in report units on the held-out rows; a target with fewer than {MIN_LABELS} labels is not scored or trained",
             "seed": args.seed, "epochs": args.epochs, "folds": args.folds, "seconds": time.perf_counter() - started}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ipp1-unusual_shapes.json").write_text(json.dumps({"notes": notes, "holdouts": result}, indent=2, allow_nan=False) + "\n")
    write_markdown(result, notes)
    plot(result, med, label, ids, holdouts)
    print(f"Saved {OUT / 'ipp1-unusual_shapes.json'}", flush=True)


def write_markdown(result, notes):
    lines = ["# IPP 1: unusual shapes (leave one family of shapes out)", "", notes["clusters"] + ".", notes["scoring"] + ".", "",
             "| Held out | Discharges | Median elongation | Median triangularity | Distance to nearest training discharge: random fold, family out |",
             "|---|---:|---:|---:|---:|"]
    for n, r in result.items():
        lines.append(f"| {n} | {r['discharges']} | {r['median_elongation']:.2f} | {r['median_triangularity']:.2f} | "
                     f"{r['nn_distance_random_fold']:.2f}, {r['nn_distance_cluster_out']:.2f} |")
    for t in SHOWN:
        lines += ["", f"MAE of {t} ({UNIT[t][1] or 'dimensionless'}), same discharges: random fold, then family out, factor", "",
                  "| Held out | Random fold | Family out | Factor |", "|---|---:|---:|---:|"]
        for n, r in result.items():
            a, b = r["mae_random_fold"][t], r["mae_cluster_out"][t]
            lines.append(f"| {n} | " + (f"{a:.4g} | {b:.4g} | {b / a:.1f}x |" if a is not None and b is not None else "n/a | n/a | n/a |"))
    lines += ["", "`is_limited` accuracy, random fold then family out: " +
              "; ".join(f"{n} {r['is_limited_accuracy_random_fold']:.3f} then {r['is_limited_accuracy_cluster_out']:.3f}" for n, r in result.items())]
    (OUT / "ipp1-unusual_shapes.md").write_text("\n".join(lines) + "\n")


def plot(result, med, label, ids, holdouts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)
    for c in range(4):
        a.scatter(med[label == c, 0], med[label == c, 1], s=22, label=f"cluster {c} ({(label == c).sum()})")
    a.set(xlabel="median elongation", ylabel="median triangularity", title="Discharges by shape")
    a.legend(fontsize=9)
    names, width = list(result), .38
    t = "R_mag_axis"
    pos = np.arange(len(names))
    b.bar(pos - width / 2, [result[n]["mae_random_fold"][t] for n in names], width, label="random fold, same discharges", color="#9aabb1")
    b.bar(pos + width / 2, [result[n]["mae_cluster_out"][t] for n in names], width, label="family held out", color="#176b87")
    b.set(xticks=pos, xticklabels=[n.replace("_", "\n") for n in names], ylabel="R axis MAE (mm)", title="Error on an unseen family")
    b.set_yscale("log")
    b.legend(fontsize=9)
    fig.savefig(OUT / "ipp1-unusual_shapes.png", dpi=150)


if __name__ == "__main__":
    main()
