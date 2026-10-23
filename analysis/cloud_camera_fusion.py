#!/usr/bin/env python
"""Camera against realistic magnetics for IPP task 1 (REQ-B01), on the same frames and folds as cloud_camera_model.py.

    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_camera_fusion.py [--channels grey --stride 8 ...]

The magnetic inputs come from the organizers' equil_data_noisy.csv, taken at the nearest equilibrium row of each frame
(interpolating two noisy rows would average part of the noise away). Variants per fold:
  magnetic   ipp1_common.fit_mlp on the noisy inputs (60 epochs)
  camera     the CNN on the image alone
  early      the CNN with the noisy inputs as a second branch
  late       per-target weighted average of camera and magnetic, weights 1/variance of their errors in the OTHER folds
Test cases: the noisy inputs as given, and the same inputs with lane R's extra corruption (noise 0.15 and a linear
drift per discharge 0.30 of the training SD); the image is the same in both. Writes results/cloud-camera-<name>.{json,md,png}
and the per-frame predictions to $HACKATHON_HOME/out/cloud-camera/runs/ (never git).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import cloud_camera_model as cm
from cloud_camera_prepare import interpolate_equilibrium
from ipp1_common import TARGETS, UNIT, fit_mlp, load
from ipp1_robustness import corrupt

VARIANTS = ("magnetic", "camera", "early", "late")
CASES = ("noisy", "noisy+drift")


def late_weights(pred_cam, pred_mag, y, m, rows):
    """Per-target weight of the camera, 1/var(camera error) / (1/var(camera) + 1/var(magnetic)), from the given rows."""
    w = np.full(len(TARGETS), 0.5)
    for j in range(len(TARGETS)):
        k = rows[m[rows, j]]
        if len(k) > 1:
            vc, vm = np.var(pred_cam[k, j] - y[k, j]), np.var(pred_mag[k, j] - y[k, j])
            w[j] = (1 / vc) / (1 / vc + 1 / vm)
    return w


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--size", default="48x64")
    ap.add_argument("--channels", choices=["rgb", "grey"], default="grey")
    ap.add_argument("--stride", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--width", type=int, default=16)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--results-dir", type=Path, default=cm.RESULTS)
    ap.add_argument("--out-name", default="fusion")
    args = ap.parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    img, x_clean, y, g, m = cm.load_cache(args.size, args.channels, args.stride)
    meta = np.load(cm.CACHE / f"meta_{args.size}.npz")
    keep = cm.stride_keep(meta["discharge"], args.stride)
    t = meta["time"][keep]
    x_cols = [str(c) for c in meta["x_cols"]]
    assert np.array_equal(meta["discharge"][keep], g)

    # Alignment guard (the earlier label shift bug): re-interpolating the clean file must reproduce the cached inputs.
    clean_df = load()[0]
    x_check, inside, _ = interpolate_equilibrium(clean_df, g, t, x_cols, set())
    assert inside.all(), "a cached frame is outside its discharge"
    dev = np.abs(x_check - x_clean).max(0) / x_clean.std(0)
    assert dev.max() < 1e-4, f"cached inputs do not match the clean file (max {dev.max():.2e} SD)"
    noisy_df = load(noisy=True)[0]
    x_noisy, inside, _ = interpolate_equilibrium(noisy_df, g, t, x_cols, set(x_cols))
    assert inside.all() and np.isfinite(x_noisy).all()
    x_noisy = x_noisy.astype(np.float32)
    print(f"noisy minus clean inputs on the frames: {np.abs(x_noisy - x_clean).mean(0).mean() / x_clean.std(0).mean():.3f} "
          f"of the input SD on average", flush=True)

    folds = cm.make_folds(g, y, args)
    preds = {(v, c): np.full(y.shape, np.nan, np.float32) for v in VARIANTS for c in CASES}
    fold_of = np.full(len(g), -1)
    seconds = {v: [] for v in ("magnetic", "camera", "early")}
    for k, (tr, te) in enumerate(folds):
        fold_of[te] = k
        x_drift = corrupt(x_noisy[te], g[te], t[te], scale=x_noisy[tr].std(0), noise=0.15, drift=0.30, seed=2000 + k)
        a = time.perf_counter()
        predict_mag, _, _ = fit_mlp(x_noisy[tr], y[tr], m[tr], 60, seed=args.seed + k)
        seconds["magnetic"].append(time.perf_counter() - a)
        preds["magnetic", "noisy"][te] = predict_mag(x_noisy[te])
        preds["magnetic", "noisy+drift"][te] = predict_mag(x_drift)
        predict_cam, _, sec = cm.fit_cnn(img[tr], y[tr], m[tr], epochs=args.epochs, seed=args.seed + k,
                                         width=args.width, batch=args.batch)
        seconds["camera"].append(sec)
        preds["camera", "noisy"][te] = preds["camera", "noisy+drift"][te] = predict_cam(img[te])
        predict_both, _, sec = cm.fit_cnn(img[tr], y[tr], m[tr], x=x_noisy[tr], epochs=args.epochs, seed=args.seed + k,
                                          width=args.width, batch=args.batch)
        seconds["early"].append(sec)
        preds["early", "noisy"][te] = predict_both(img[te], x_noisy[te])
        preds["early", "noisy+drift"][te] = predict_both(img[te], x_drift)
        print(f"fold {k + 1}/{len(folds)}: magnetic {seconds['magnetic'][-1]:.0f} s, camera {seconds['camera'][-1]:.0f} s, "
              f"early {seconds['early'][-1]:.0f} s", flush=True)

    # Late fusion: weights for fold k come only from the other folds' errors under normal operation (noisy case).
    weights = []
    for k, (_, te) in enumerate(folds):
        other = np.flatnonzero((fold_of >= 0) & (fold_of != k))
        w = late_weights(preds["camera", "noisy"], preds["magnetic", "noisy"], y, m, other)
        weights.append(w.tolist())
        for c in CASES:
            preds["late", c][te] = w * preds["camera", c][te] + (1 - w) * preds["magnetic", c][te]

    per_fold = {c: {v: [cm.score(preds[v, c][te], y[te], m[te]) for _, te in folds] for v in VARIANTS} for c in CASES}
    results = {c: {v: cm.aggregate(per_fold[c][v]) for v in VARIANTS} for c in CASES}
    wins = {c: {v: {t: int(sum(per_fold[c][v][k][t]["mae"] < per_fold[c]["magnetic"][k][t]["mae"] for k in range(len(folds))))
                    for t in TARGETS} for v in ("camera", "early", "late")} for c in CASES}
    info = cm.common_info(argparse.Namespace(**{**vars(args), "experiment": "fusion"}), g, folds)
    payload = {**info, "channels": args.channels, "magnetic_inputs": "equil_data_noisy.csv, nearest row",
               "results": results, "mae_per_fold": {c: {v: {t: [f[t]["mae"] for f in per_fold[c][v]] for t in TARGETS}
                                                          for v in VARIANTS} for c in CASES},
               "folds_better_than_magnetic": wins, "late_camera_weight_per_fold": dict(zip([f"fold_{k + 1}" for k in range(len(folds))], weights)),
               "train_seconds_per_fold": seconds, "seconds": time.perf_counter() - started}
    (args.results_dir / f"cloud-camera-{args.out_name}.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    runs = cm.OUT / "cloud-camera" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    np.savez(runs / f"{args.out_name}.npz", keep=keep, fold=fold_of, **{f"{v}|{c}": p for (v, c), p in preds.items()})

    lines = [f"# Camera against realistic (noisy) magnetics, {len(folds)} folds by discharge", "",
             f"{info['frames']} frames of {info['discharges']} discharges, {args.channels} {args.size}, every {args.stride}th frame, "
             f"{args.epochs} epochs. Magnetic inputs: equil_data_noisy.csv at the nearest equilibrium row of each frame. "
             "MAE mean over folds; in brackets the number of folds in which the variant beats the magnetic MLP.", ""]
    for c in CASES:
        lines += [f"## Test inputs: {c}", "", "| target | unit | " + " | ".join(VARIANTS) + " |", "|---|---|" + "---|" * len(VARIANTS)]
        for t in TARGETS:
            cells = [f"{results[c]['magnetic'][t]['mae']:.3g}"]
            cells += [f"{results[c][v][t]['mae']:.3g} ({wins[c][v][t]}/{len(folds)})" for v in ("camera", "early", "late")]
            lines.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(cells) + " |")
        lines += ["", "is_limited accuracy: " + ", ".join(f"{v} {results[c][v]['is_limited']['accuracy']:.3f}" for v in VARIANTS), ""]
    lines += ["Late-fusion camera weight per target (mean over folds): "
              + ", ".join(f"{t} {np.mean([w[j] for w in weights]):.2f}" for j, t in enumerate(TARGETS)) + ".",
              f"Training seconds per fold: " + ", ".join(f"{v} {np.mean(s):.0f}" for v, s in seconds.items()) + "."]
    (args.results_dir / f"cloud-camera-{args.out_name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    width = 0.2
    for ax, c in zip(axes, CASES):
        for i, v in enumerate(VARIANTS):
            ax.bar(np.arange(len(TARGETS)) + (i - 1.5) * width, [results[c][v][t]["nrmse"] for t in TARGETS], width, label=v)
        ax.set(ylabel="nRMSE (RMSE / spread)", yscale="log", title=f"test inputs: {c}")
        ax.grid(alpha=.25, axis="y")
    axes[0].legend(ncol=4, fontsize=8)
    axes[1].set_xticks(np.arange(len(TARGETS)), TARGETS, rotation=60, ha="right", fontsize=7)
    fig.tight_layout()
    fig.savefig(args.results_dir / f"cloud-camera-{args.out_name}.png", dpi=130)
    print("\n".join(lines), flush=True)
    print(f"total {time.perf_counter() - started:.0f} s", flush=True)


if __name__ == "__main__":
    main()
