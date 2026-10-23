#!/usr/bin/env python
"""Which parts of the camera image carry the plasma shape (REQ-B07), and how well a smaller part does (REQ-004).

    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_camera_explain.py occlusion|parts [options]

occlusion  per fold, train the CNN (same settings as cloud_camera_model.py main), then fill each patch of a grid on every
           sweep-step-th test frame with the training mean and record MAE(occluded) / MAE(clean) per target group, and the
           drop of is_limited accuracy. Models are saved to $HACKATHON_HOME/out/cloud-camera/models (never git).
parts      train and test on fixed parts of the image, chosen before any result: top, bottom, left and right halves,
           the centre (half height and half width) and the whole frame at half resolution.
Writes results/cloud-camera-<experiment>.{json,md,png}. The figures show the grid only, never a camera frame (CON-001).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import cloud_camera_model as cm
from ipp1_common import TARGETS, UNIT

GROUPS = {"axis": ["R_mag_axis", "Z_mag_axis"],
          "shape": ["elongation", "triangularity", "triangularity_upper", "triangularity_lower"],
          "divertor": ["R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2"],
          "limiter": ["R_limiter", "Z_limiter"],
          "current": ["plasma_current"]}


def parts_of(h, w):
    """Fixed image parts as (row slice, column slice, pool factor); fixed before any result was seen."""
    return {"full": (slice(0, h), slice(0, w), 1), "top": (slice(0, h // 2), slice(0, w), 1),
            "bottom": (slice(h // 2, h), slice(0, w), 1), "left": (slice(0, h), slice(0, w // 2), 1),
            "right": (slice(0, h), slice(w // 2, w), 1), "centre": (slice(h // 4, 3 * h // 4), slice(w // 4, 3 * w // 4), 1),
            "half_resolution": (slice(0, h), slice(0, w), 2)}


def cut(img, rows, cols, pool):
    sub = img[:, :, rows, cols]
    if pool > 1:
        sub = F.avg_pool2d(sub.float(), pool).round().to(torch.uint8)
    return sub.contiguous()


def group_ratio(occ, clean):
    """Mean over the group's targets of MAE(occluded) / MAE(clean), skipping targets absent from the test part."""
    out = {}
    for name, ts in GROUPS.items():
        r = [occ[t]["mae"] / clean[t]["mae"] for t in ts if np.isfinite(occ[t]["mae"]) and clean[t]["mae"] > 0]
        out[name] = float(np.mean(r)) if r else float("nan")
    out["is_limited_accuracy_drop"] = clean["is_limited"]["accuracy"] - occ["is_limited"]["accuracy"]
    return out


def run_occlusion(args, img, y, g, m, folds):
    _, _, h, w = img.shape
    p = args.patch
    grid = [(r, c) for r in range(0, h, p) for c in range(0, w, p)]
    models = cm.OUT / "cloud-camera" / "models"
    models.mkdir(parents=True, exist_ok=True)
    per_fold_clean, maps, seconds = [], [], []
    for k, (tr, te) in enumerate(folds):
        predict, net, sec = cm.fit_cnn(img[tr], y[tr], m[tr], epochs=args.epochs, seed=args.seed + k, width=args.width, batch=args.batch)
        seconds.append(sec)
        torch.save({"state": net.state_dict(), "channels": args.channels, "size": args.size, "width": args.width,
                    "fold": k, "seed": args.seed + k}, models / f"{args.out_name}-fold{k + 1}.pt")
        per_fold_clean.append(cm.score(predict(img[te]), y[te], m[te]))
        sub = te[::args.sweep_step]
        clean = cm.score(predict(img[sub]), y[sub], m[sub])
        fill = (img[tr[::16]].float() / 255).mean((0, 2, 3)).view(1, -1, 1, 1)

        def occluder(r, c):
            def f(b):
                b = b.clone()
                b[:, :, r:r + p, c:c + p] = fill
                return b
            return f

        fold_map = {}
        for r, c in grid:
            fold_map[f"{r},{c}"] = group_ratio(cm.score(predict(img[sub], transform=occluder(r, c)), y[sub], m[sub]), clean)
        maps.append(fold_map)
        print(f"occlusion fold {k + 1}/{len(folds)}: train {sec:.0f} s, {len(grid)} patches on {len(sub)} frames", flush=True)
    mean_map = {key: {gname: float(np.nanmean([fm[key][gname] for fm in maps])) for gname in maps[0][key]} for key in maps[0]}
    return {"clean": cm.aggregate(per_fold_clean), "map": mean_map, "grid": {"patch": p, "rows": h // p, "cols": w // p},
            "train_seconds_per_fold": seconds}


def plot_occlusion(res, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows, cols, p = res["grid"]["rows"], res["grid"]["cols"], res["grid"]["patch"]
    names = list(GROUPS) + ["is_limited_accuracy_drop"]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.2))
    for ax, name in zip(axes.flat, names):
        a = np.array([[res["map"][f"{r * p},{c * p}"][name] for c in range(cols)] for r in range(rows)])
        im = ax.imshow(a, cmap="magma", origin="upper")
        ax.set(title=name if name != "is_limited_accuracy_drop" else "is_limited: accuracy drop",
               xlabel="image column (patch)", ylabel="image row (patch)")
        fig.colorbar(im, ax=ax, fraction=0.046, label="error ratio" if name in GROUPS else "accuracy drop")
        for r in range(rows):
            for c in range(cols):
                ax.text(c, r, f"{a[r, c]:.2f}" if name in GROUPS else f"{a[r, c]:.3f}", ha="center", va="center", fontsize=6,
                        color="white" if a[r, c] < np.nanmedian(a) else "black")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130)


def run_parts(args, img, y, g, m, folds):
    _, _, h, w = img.shape
    out, seconds, shapes = {}, {}, {}
    for name, (rows, cols, pool) in parts_of(h, w).items():
        if name == "full" and not args.with_full:
            continue
        sub_img = cut(img, rows, cols, pool)
        shapes[name] = list(sub_img.shape[2:])
        per_fold, seconds[name] = [], []
        for k, (tr, te) in enumerate(folds):
            predict, _, sec = cm.fit_cnn(sub_img[tr], y[tr], m[tr], epochs=args.epochs, seed=args.seed + k, width=args.width, batch=args.batch)
            per_fold.append(cm.score(predict(sub_img[te]), y[te], m[te]))
            seconds[name].append(sec)
        out[name] = cm.aggregate(per_fold)
        out[name]["mae_per_fold"] = {t: [f[t]["mae"] for f in per_fold] for t in TARGETS}
        print(f"part {name} {shapes[name]}: {np.mean(seconds[name]):.0f} s per fold, R_mag_axis {out[name]['R_mag_axis']['mae']:.3g} mm", flush=True)
    return {"results": out, "shapes": shapes, "train_seconds_per_fold": seconds}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("experiment", choices=["occlusion", "parts"])
    ap.add_argument("--size", default="48x64")
    ap.add_argument("--channels", choices=["rgb", "grey"], default="grey")
    ap.add_argument("--stride", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--width", type=int, default=16)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--patch", type=int, default=8)
    ap.add_argument("--sweep-step", type=int, default=4)
    ap.add_argument("--with-full", action="store_true", help="parts: also retrain the whole frame")
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--results-dir", type=Path, default=cm.RESULTS)
    ap.add_argument("--out-name")
    args = ap.parse_args()
    args.out_name = args.out_name or args.experiment
    args.results_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    img, x, y, g, m = cm.load_cache(args.size, args.channels, args.stride)
    folds = cm.make_folds(g, y, args)
    info = cm.common_info(args, g, folds)
    if args.experiment == "occlusion":
        res = run_occlusion(args, img, y, g, m, folds)
        plot_occlusion(res, args.results_dir / f"cloud-camera-{args.out_name}.png",
                       f"Error ratio when one {args.patch}x{args.patch} patch of the {args.size} {args.channels} frame is hidden "
                       f"({len(folds)} folds)")
        rows, cols, p = res["grid"]["rows"], res["grid"]["cols"], res["grid"]["patch"]
        lines = [f"# Occlusion map, {args.channels} {args.size}, {len(folds)} folds by discharge", "",
                 f"Each {p}x{p} patch (grid {rows} rows x {cols} columns, row 0 at the top of the image) is filled with the training "
                 f"mean on every {args.sweep_step}th test frame. Values: MAE with the patch hidden / MAE without, mean over the "
                 "targets of the group and over folds (1.00 = the patch does not matter).", ""]
        for name in list(GROUPS) + ["is_limited_accuracy_drop"]:
            lines += [f"## {name}", "", "| row \\ column | " + " | ".join(str(c) for c in range(cols)) + " |", "|---|" + "---|" * cols]
            for r in range(rows):
                lines.append(f"| {r} | " + " | ".join(f"{res['map'][f'{r * p},{c * p}'][name]:.3g}" for c in range(cols)) + " |")
            lines.append("")
        lines.append("Clean scores of these models (reproducibility check against main): "
                     + ", ".join(f"{t} {res['clean'][t]['mae']:.3g}" for t in ["R_mag_axis", "Z_mag_axis", "elongation"]) + ".")
    else:
        res = run_parts(args, img, y, g, m, folds)
        names = list(res["results"])
        lines = [f"# A smaller part of the image, {args.channels} {args.size}, {len(folds)} folds by discharge", "",
                 "Parts fixed before any result: halves of the frame, the centre (half height x half width) and the whole frame at "
                 "half resolution. MAE mean over folds.", "",
                 "| target | unit | " + " | ".join(f"{n} {res['shapes'][n][0]}x{res['shapes'][n][1]}" for n in names) + " |",
                 "|---|---|" + "---|" * len(names)]
        for t in TARGETS:
            lines.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(f"{res['results'][n][t]['mae']:.3g}" for n in names) + " |")
        lines += ["", "is_limited accuracy: " + ", ".join(f"{n} {res['results'][n]['is_limited']['accuracy']:.3f}" for n in names)]
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 3.8))
        width = 0.8 / len(names)
        for i, n in enumerate(names):
            ax.bar(np.arange(len(TARGETS)) + (i - len(names) / 2) * width, [res["results"][n][t]["nrmse"] for t in TARGETS], width, label=n)
        ax.set_xticks(np.arange(len(TARGETS)), TARGETS, rotation=60, ha="right", fontsize=7)
        ax.set(ylabel="nRMSE (RMSE / spread)", yscale="log")
        ax.legend(fontsize=7, ncol=4)
        ax.grid(alpha=.25, axis="y")
        fig.tight_layout()
        fig.savefig(args.results_dir / f"cloud-camera-{args.out_name}.png", dpi=130)
    (args.results_dir / f"cloud-camera-{args.out_name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.results_dir / f"cloud-camera-{args.out_name}.json").write_text(
        json.dumps({**info, "channels": args.channels, **res, "seconds": time.perf_counter() - started}, indent=1), encoding="utf-8")
    print("\n".join(lines), flush=True)
    print(f"total {time.perf_counter() - started:.0f} s", flush=True)


if __name__ == "__main__":
    main()
