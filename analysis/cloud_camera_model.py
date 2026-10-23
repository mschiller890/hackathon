#!/usr/bin/env python
"""Camera model for IPP task 1: a small CNN on downscaled frames, split by whole discharges.

    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_camera_model.py <experiment> [options]

Experiments (each writes results/cloud-camera-<experiment>.{json,md,png}, aggregates only):
  main        colour against grey (REQ-B03) and the sensitivity of both to a shifted or rotated test image (REQ-B05)
  augment     the same sensitivity for a model trained with random shifts and rotations
  curve       accuracy against the number of training discharges (and frames)
  multimodal  magnetic MLP, camera CNN and both together on identical folds and rows (REQ-B01)
Add --dev to run on one inner split of the training discharges of fold 0 (for choosing epochs, size, width
without touching the test folds). Inputs come from cloud_camera_prepare.py.
"""
import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, UNIT, fit_mlp, group_folds, score as _score

CACHE = OUT / "cloud-camera"
RESULTS = Path(__file__).resolve().parent.parent / "results"
SHIFTS = (-4, -2, -1, 1, 2, 4)  # pixels at the cached size
ROTATIONS = (-5, -2, -1, 1, 2, 5)  # degrees
FRACTIONS = (0.05, 0.10, 0.25, 0.50, 1.0)


class CamNet(nn.Module):
    """Convolutions with two coordinate channels (absolute position matters), a 4x4 map, an optional magnetic branch."""

    def __init__(self, c_in, n_out, n_extra=0, width=16):
        super().__init__()

        def block(i, o, stride):
            return nn.Sequential(nn.Conv2d(i, o, 3, stride, 1, bias=False), nn.BatchNorm2d(o), nn.SiLU())

        w = width
        self.conv = nn.Sequential(block(c_in + 2, w, 2), block(w, 2 * w, 1), block(2 * w, 4 * w, 2), block(4 * w, 4 * w, 1),
                                  block(4 * w, 8 * w, 2), block(8 * w, 8 * w, 1), nn.AdaptiveAvgPool2d(4), nn.Flatten())
        self.mag = nn.Sequential(nn.Linear(n_extra, 64), nn.SiLU()) if n_extra else None
        self.head = nn.Sequential(nn.Linear(8 * w * 16 + (64 if n_extra else 0), 256), nn.SiLU(), nn.Linear(256, n_out))

    def forward(self, img, extra=None):
        n, _, h, w = img.shape
        yy, xx = torch.meshgrid(torch.linspace(-1, 1, h), torch.linspace(-1, 1, w), indexing="ij")
        coords = torch.stack([xx, yy]).expand(n, -1, -1, -1)
        feat = self.conv(torch.cat([img, coords], 1))
        if self.mag is not None:
            feat = torch.cat([feat, self.mag(extra)], 1)
        return self.head(feat)


def affine(batch, dx, dy, deg):
    """Move image content by (dx, dy) pixels and rotate it by deg degrees about the centre; per-sample tensors."""
    n, _, h, w = batch.shape
    a = torch.deg2rad(deg)
    # Pixel-space rotation R and shift conjugated into the normalized [-1, 1] coordinates of grid_sample.
    theta = torch.zeros(n, 2, 3)
    theta[:, 0, 0] = torch.cos(a)
    theta[:, 0, 1] = -torch.sin(a) * h / w
    theta[:, 1, 0] = torch.sin(a) * w / h
    theta[:, 1, 1] = torch.cos(a)
    theta[:, 0, 2] = -2 * dx / w
    theta[:, 1, 2] = -2 * dy / h
    grid = F.affine_grid(theta, batch.shape, align_corners=False)
    return F.grid_sample(batch, grid, padding_mode="border", align_corners=False)


def fixed(dx=0.0, dy=0.0, deg=0.0):
    return lambda b: affine(b, torch.full((len(b),), float(dx)), torch.full((len(b),), float(dy)), torch.full((len(b),), float(deg)))


def random_perturbation(b, max_shift=3.0, max_deg=3.0):
    n = len(b)
    return affine(b, (torch.rand(n) * 2 - 1) * max_shift, (torch.rand(n) * 2 - 1) * max_shift, (torch.rand(n) * 2 - 1) * max_deg)


def fit_cnn(img, y, m, x=None, epochs=15, seed=0, width=16, batch=128, augment=False, threads=4):
    """Masked-loss training as in ipp1_common.fit_mlp. img: uint8 tensor (N, C, H, W); x: optional magnetic inputs.

    Returns predict(img, x=None, transform=None) -> raw targets (numpy), the network and the training seconds.
    """
    torch.manual_seed(seed)
    torch.set_num_threads(threads)
    started = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # a target absent from the training part stays NaN in the output
        ym, ys = np.nanmean(y, 0), np.nanstd(y, 0) + 1e-9
    yt = torch.tensor(np.nan_to_num((y - ym) / ys), dtype=torch.float32)
    mt = torch.tensor(m.astype(np.float32))
    probe = img[torch.randperm(len(img))[:2000]].float() / 255
    pm, ps = probe.mean((0, 2, 3), keepdim=True), probe.std((0, 2, 3), keepdim=True) + 1e-6
    if x is not None:
        xm, xs = x.mean(0), x.std(0) + 1e-9
        xt = torch.tensor((x - xm) / xs, dtype=torch.float32)
    net = CamNet(img.shape[1], yt.shape[1], x.shape[1] if x is not None else 0, width)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    steps = epochs * ((len(img) + batch - 1) // batch)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=steps)
    net.train()
    for _ in range(epochs):
        perm = torch.randperm(len(img))
        for i in range(0, len(perm), batch):
            b = perm[i:i + batch]
            if len(b) < 2:  # batch norm needs more than one sample
                continue
            xb = img[b].float() / 255
            if augment:
                xb = random_perturbation(xb)
            out = net((xb - pm) / ps, xt[b] if x is not None else None)
            loss = ((out - yt[b]) ** 2 * mt[b]).sum() / mt[b].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
    net.eval()
    seconds = time.perf_counter() - started

    def predict(im, xe=None, transform=None, chunk=512):
        outs = []
        with torch.no_grad():
            for i in range(0, len(im), chunk):
                xb = im[i:i + chunk].float() / 255
                if transform is not None:
                    xb = transform(xb)
                extra = torch.tensor((xe[i:i + chunk] - xm) / xs, dtype=torch.float32) if xe is not None else None
                outs.append(net((xb - pm) / ps, extra).numpy())
        return np.concatenate(outs) * ys + ym

    return predict, net, seconds


def score(pred, y, m):
    """ipp1_common.score, silent and NaN for a target that has no row in the test part (single-configuration targets)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return _score(pred, y, m)


def stride_keep(g, stride):
    """Indices of every stride-th frame of each discharge, in the order of the cache."""
    order = np.argsort(g, kind="stable")
    start = np.r_[0, np.flatnonzero(np.diff(g[order])) + 1]
    rank = np.empty(len(g), dtype=np.int64)
    rank[order] = np.arange(len(g)) - np.repeat(start, np.diff(np.r_[start, len(g)]))
    return np.flatnonzero(rank % stride == 0)


def load_cache(tag, channels, stride=1):
    """Cached frames as a uint8 tensor (N, C, H, W) with inputs, targets, discharges and mask.

    stride > 1 keeps every stride-th frame of each discharge: neighbouring frames are near copies, so this cuts the
    CPU time with little loss of information.
    """
    meta = np.load(CACHE / f"meta_{tag}.npz")
    g = meta["discharge"]
    keep = stride_keep(g, stride)
    a = np.load(CACHE / f"{channels}_{tag}.npy", mmap_mode="r")[keep]
    imgs = torch.from_numpy(a.transpose(0, 3, 1, 2) if a.ndim == 4 else a[:, None]).contiguous()
    return imgs, meta["x"][keep], meta["y"][keep], g[keep], meta["mask"][keep]


def report_folds(folds, g, m):
    """Print the rows and discharges per fold and warn when a target has no training row (its prediction is then NaN)."""
    for k, (tr, te) in enumerate(folds):
        have = {t: (int(m[tr, j].sum()), int(m[te, j].sum())) for j, t in enumerate(TARGETS)
                if t in ("R_x_point", "R_strike_point_1", "R_limiter", "is_limited")}
        print(f"fold {k + 1}: train {len(tr)} frames / {len(np.unique(g[tr]))} discharges, test {len(te)} / {len(np.unique(g[te]))}; "
              f"frames with target (train/test): " + ", ".join(f"{t} {a}/{b}" for t, (a, b) in have.items()), flush=True)
        for j, t in enumerate(TARGETS):
            if m[tr, j].sum() == 0:
                print(f"WARNING fold {k + 1}: no training frame has {t}; its prediction and score are NaN", flush=True)


def make_folds(g, y, args):
    folds = group_folds(np.zeros((len(g), 1)), y, g, args.folds)
    if args.dev:  # one inner split of the training discharges of fold 0; the test fold of fold 0 stays untouched
        tr = folds[0][0]
        ug = np.random.default_rng(args.seed).permutation(np.unique(g[tr]))
        val = np.isin(g[tr], ug[:max(1, len(ug) // 5)])
        folds = [(tr[~val], tr[val])]
    report_folds(folds, g, ~np.isnan(y))
    return folds


def aggregate(per_fold):
    """Mean over folds of every score field, plus the fold-to-fold standard deviation of the MAE."""
    out = {}
    for t in TARGETS:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # all folds NaN: the target has no test row
            rec = {}
            for k in per_fold[0][t]:
                if k != "unit":
                    v = np.array([f[t][k] for f in per_fold], dtype=float)
                    rec[k] = float(np.nanmean(np.where(np.isfinite(v), v, np.nan)))
            rec["mae_std"] = float(np.nanstd([f[t]["mae"] for f in per_fold]))
        rec["folds_with_target"] = int(np.sum([np.isfinite(f[t]["mae"]) for f in per_fold]))
        rec["unit"] = per_fold[0][t]["unit"]
        out[t] = rec
    return out


def latency(net, img, extra=None):
    one = img[:1].float() / 255
    ex = torch.tensor(extra[:1], dtype=torch.float32) if extra is not None else None
    big = img[:256].float() / 255
    with torch.no_grad():
        for _ in range(20):
            net(one, ex)
        ts = []
        for _ in range(200):
            a = time.perf_counter()
            net(one, ex)
            ts.append(time.perf_counter() - a)
        a = time.perf_counter()
        net(big, torch.tensor(extra[:256], dtype=torch.float32) if extra is not None else None)
        tb = time.perf_counter() - a
    return {"single_frame_cpu_ms_median": float(np.median(ts) * 1000), "single_frame_cpu_ms_p99": float(np.percentile(ts, 99) * 1000),
            "batch_256_cpu_ms": float(tb * 1000), "parameters": int(sum(p.numel() for p in net.parameters()))}


def sweep(predict, img, y, m, step):
    """Scores of the test frames (every step-th) under each shift and rotation."""
    sub = slice(None, None, step)
    cases = {"clean": None}
    cases.update({f"shift_x={v:+d}": fixed(dx=v) for v in SHIFTS})
    cases.update({f"shift_y={v:+d}": fixed(dy=v) for v in SHIFTS})
    cases.update({f"rotate={v:+d}": fixed(deg=v) for v in ROTATIONS})
    return {k: score(predict(img[sub], transform=f), y[sub], m[sub]) for k, f in cases.items()}


def write_markdown(name, title, variants, notes):
    """One table of MAE (mean over folds, in report units) and nRMSE per variant."""
    names = list(variants)
    lines = [f"# {title}", "", "MAE in the unit shown, mean over folds; nRMSE is the RMSE divided by the spread of the target.", ""]
    lines += ["| target | unit | " + " | ".join(f"{n} MAE | {n} nRMSE" for n in names) + " |",
              "|---|---|" + "---|---|" * len(names)]
    for t in TARGETS:
        cells = " | ".join(f"{variants[n][t]['mae']:.3g} | {variants[n][t]['nrmse']:.3f}" for n in names)
        lines.append(f"| {t} | {variants[names[0]][t]['unit']} | {cells} |")
    lines += ["", "is_limited accuracy: " + ", ".join(f"{n} {variants[n]['is_limited']['accuracy']:.3f}" for n in names), ""]
    lines += notes
    (RESULTS / f"cloud-camera-{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_sweep(name, title, sweeps, targets=("R_mag_axis", "Z_mag_axis", "elongation", "R_x_point")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(targets), 2, figsize=(9, 2.6 * len(targets)), squeeze=False)
    for row, t in enumerate(targets):
        for col, (kind, values, xl) in enumerate([("shift", SHIFTS, "shift in x or y, mean of both (pixels of the cached image)"),
                                                  ("rotate", ROTATIONS, "rotation (degrees)")]):
            ax = axes[row][col]
            for label, agg in sweeps.items():
                if kind == "shift":
                    ys = {v: np.mean([agg[f"shift_x={v:+d}"][t]["mae"], agg[f"shift_y={v:+d}"][t]["mae"]]) for v in SHIFTS}
                else:
                    ys = {v: agg[f"rotate={v:+d}"][t]["mae"] for v in values}
                ys[0] = agg["clean"][t]["mae"]
                xs = sorted(ys)
                ax.plot(xs, [ys[v] for v in xs], "o-", label=label)
            ax.set(xlabel=xl, ylabel=f"{t} MAE ({UNIT[t][1] or 'dimensionless'})")
            ax.set_yscale("log")
            ax.grid(alpha=.25)
            if row == 0 and col == 0:
                ax.legend(fontsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(RESULTS / f"cloud-camera-{name}.png", dpi=130)


def dump(name, payload):
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"cloud-camera-{name}.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")


def common_info(args, g, folds):
    return {"experiment": args.experiment, "dev": args.dev, "size": args.size, "epochs": args.epochs, "width": args.width,
            "seed": args.seed, "stride": args.stride, "frames": int(len(g)), "discharges": int(len(np.unique(g))), "folds": len(folds),
            "test_discharges_per_fold": [int(len(np.unique(g[te]))) for _, te in folds]}


def run_main(args):
    folds, results, sweeps, times, lat = None, {}, {}, {}, {}
    for channels in ("rgb", "grey"):
        img, x, y, g, m = load_cache(args.size, channels, args.stride)
        folds = folds or make_folds(g, y, args)
        per_fold, per_sweep, times[channels] = [], [], []
        for k, (tr, te) in enumerate(folds):
            predict, net, sec = fit_cnn(img[tr], y[tr], m[tr], epochs=args.epochs, seed=args.seed + k, width=args.width, batch=args.batch)
            per_fold.append(score(predict(img[te]), y[te], m[te]))
            per_sweep.append(sweep(predict, img[te], y[te], m[te], args.sweep_step))
            times[channels].append(sec)
            if k == 0:
                lat[channels] = latency(net, img[te])
            print(f"{channels} fold {k + 1}/{len(folds)}: {sec:.0f} s", flush=True)
        results[channels] = aggregate(per_fold)
        sweeps[channels] = {case: aggregate([s[case] for s in per_sweep]) for case in per_sweep[0]}
    info = common_info(args, g, folds)
    dump(args.out_name, {**info, "results": results, "sweeps": sweeps, "train_seconds_per_fold": times, "latency": lat})
    write_markdown(args.out_name, "Camera CNN: colour against grey", results,
                   [f"{info['frames']} frames, {info['discharges']} discharges, {info['folds']} folds by discharge, "
                    f"{args.epochs} epochs, image {args.size}, width {args.width}.",
                    "Training seconds per fold: " + ", ".join(f"{c} {np.mean(t):.0f}" for c, t in times.items()) + "."])
    plot_sweep(args.out_name + "-sensitivity", "Camera CNN: error under a shifted or rotated test image", sweeps)
    return results


def run_augment(args):
    img, x, y, g, m = load_cache(args.size, args.channels, args.stride)
    folds = make_folds(g, y, args)
    results, sweeps, times = {}, {}, {}
    for label, aug in (("plain", False), ("augmented", True)):
        per_fold, per_sweep, times[label] = [], [], []
        for k, (tr, te) in enumerate(folds):
            predict, _, sec = fit_cnn(img[tr], y[tr], m[tr], epochs=args.epochs, seed=args.seed + k, width=args.width, batch=args.batch, augment=aug)
            per_fold.append(score(predict(img[te]), y[te], m[te]))
            per_sweep.append(sweep(predict, img[te], y[te], m[te], args.sweep_step))
            times[label].append(sec)
            print(f"{label} fold {k + 1}/{len(folds)}: {sec:.0f} s", flush=True)
        results[label] = aggregate(per_fold)
        sweeps[label] = {case: aggregate([s[case] for s in per_sweep]) for case in per_sweep[0]}
    info = common_info(args, g, folds)
    dump(args.out_name, {**info, "channels": args.channels, "results": results, "sweeps": sweeps, "train_seconds_per_fold": times})
    write_markdown(args.out_name, "Camera CNN: training with random shifts (up to 3 px) and rotations (up to 3 degrees)", results,
                   [f"Channels {args.channels}; {info['frames']} frames, {info['folds']} folds, {args.epochs} epochs."])
    plot_sweep(args.out_name + "-sensitivity", "Plain and augmented training under a shifted or rotated test image", sweeps)
    return results


def subset_by_discharge(tr, g, fraction, seed):
    order = np.random.default_rng(seed).permutation(np.unique(g[tr]))
    chosen = order[:max(1, int(np.ceil(fraction * len(order))))]
    return tr[np.isin(g[tr], chosen)]


def run_curve(args):
    img, x, y, g, m = load_cache(args.size, args.channels, args.stride)
    folds = make_folds(g, y, args)
    records = {f: [] for f in FRACTIONS}
    counts = {f: [] for f in FRACTIONS}
    for k, (tr, te) in enumerate(folds):
        for f in FRACTIONS:
            sub = subset_by_discharge(tr, g, f, args.seed + k)
            assert not set(g[sub]) & set(g[te])
            predict, _, sec = fit_cnn(img[sub], y[sub], m[sub], epochs=args.epochs, seed=args.seed + k, width=args.width, batch=args.batch)
            records[f].append(score(predict(img[te]), y[te], m[te]))
            counts[f].append((len(np.unique(g[sub])), len(sub)))
            print(f"fold {k + 1}/{len(folds)} fraction {f}: {len(np.unique(g[sub]))} discharges, {sec:.0f} s", flush=True)
    results = {f"fraction_{f:g}": aggregate(records[f]) for f in FRACTIONS}
    info = common_info(args, g, folds)
    info["training"] = {f"fraction_{f:g}": {"discharges": float(np.mean([c[0] for c in counts[f]])),
                                            "frames": float(np.mean([c[1] for c in counts[f]]))} for f in FRACTIONS}
    dump(args.out_name, {**info, "channels": args.channels, "results": results})
    write_markdown(args.out_name, "Camera CNN: accuracy against the number of training discharges", results,
                   [f"Channels {args.channels}; fixed epochs ({args.epochs}), so small subsets get fewer updates. "
                    "Training discharges (mean over folds): " + ", ".join(f"{k} {v['discharges']:.0f}" for k, v in info["training"].items()) + "."])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.2))
    xs = [info["training"][f"fraction_{f:g}"]["discharges"] for f in FRACTIONS]
    for ax, t in zip(axes, ["R_mag_axis", "Z_mag_axis", "elongation", "R_x_point"]):
        ax.plot(xs, [results[f"fraction_{f:g}"][t]["mae"] for f in FRACTIONS], "o-")
        ax.set(title=t, xlabel="training discharges", ylabel=f"MAE ({UNIT[t][1] or 'dimensionless'})", xscale="log", yscale="log")
        ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(RESULTS / f"cloud-camera-{args.out_name}.png", dpi=130)
    return results


def run_multimodal(args):
    img, x, y, g, m = load_cache(args.size, args.channels, args.stride)
    folds = make_folds(g, y, args)
    per_fold = {"magnetic": [], "camera": [], "camera+magnetic": []}
    times = {k: [] for k in per_fold}
    lat = None
    for k, (tr, te) in enumerate(folds):
        a = time.perf_counter()
        predict_mag, _, _ = fit_mlp(x[tr], y[tr], m[tr], 60, seed=args.seed + k)
        times["magnetic"].append(time.perf_counter() - a)
        per_fold["magnetic"].append(score(predict_mag(x[te]), y[te], m[te]))
        predict_cam, _, sec = fit_cnn(img[tr], y[tr], m[tr], epochs=args.epochs, seed=args.seed + k, width=args.width, batch=args.batch)
        times["camera"].append(sec)
        per_fold["camera"].append(score(predict_cam(img[te]), y[te], m[te]))
        predict_both, net, sec = fit_cnn(img[tr], y[tr], m[tr], x=x[tr], epochs=args.epochs, seed=args.seed + k, width=args.width, batch=args.batch)
        times["camera+magnetic"].append(sec)
        per_fold["camera+magnetic"].append(score(predict_both(img[te], x[te]), y[te], m[te]))
        if k == 0:
            lat = latency(net, img[te], x[te])
        print(f"fold {k + 1}/{len(folds)} done", flush=True)
    results = {v: aggregate(f) for v, f in per_fold.items()}
    info = common_info(args, g, folds)
    dump(args.out_name, {**info, "channels": args.channels, "results": results, "train_seconds_per_fold": times, "latency_multimodal": lat})
    write_markdown(args.out_name, "Magnetic MLP, camera CNN and both, on the same frames and folds", results,
                   [f"Channels {args.channels}; {info['frames']} camera frames with interpolated magnetic inputs, {info['folds']} folds by discharge. "
                    "The magnetic MLP is ipp1_common.fit_mlp (60 epochs) on these frames, so it is the like-for-like reference."])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 3.6))
    width = 0.27
    for i, v in enumerate(results):
        ax.bar(np.arange(len(TARGETS)) + (i - 1) * width, [results[v][t]["nrmse"] for t in TARGETS], width, label=v)
    ax.set_xticks(np.arange(len(TARGETS)), TARGETS, rotation=60, ha="right", fontsize=7)
    ax.set(ylabel="nRMSE (RMSE / spread of the target)", yscale="log")
    ax.legend()
    ax.grid(alpha=.25, axis="y")
    fig.tight_layout()
    fig.savefig(RESULTS / f"cloud-camera-{args.out_name}.png", dpi=130)
    return results


def main():
    global RESULTS
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("experiment", choices=["main", "augment", "curve", "multimodal"])
    ap.add_argument("--size", default="64x64", help="cache tag written by cloud_camera_prepare.py")
    ap.add_argument("--channels", choices=["rgb", "grey"], default="rgb", help="images for augment, curve, multimodal")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--width", type=int, default=16)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--stride", type=int, default=1, help="use every n-th frame of each discharge")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sweep-step", type=int, default=4, help="evaluate the shift and rotation sweep on every n-th test frame")
    ap.add_argument("--dev", action="store_true", help="one inner split of the training discharges of fold 0")
    ap.add_argument("--results-dir", type=Path, default=RESULTS, help="where the json, md and png are written")
    ap.add_argument("--out-name", help="output file stem after cloud-camera- (default: the experiment, plus -dev)")
    args = ap.parse_args()
    RESULTS = args.results_dir
    RESULTS.mkdir(parents=True, exist_ok=True)
    args.out_name = args.out_name or args.experiment + ("-dev" if args.dev else "")
    started = time.perf_counter()
    {"main": run_main, "augment": run_augment, "curve": run_curve, "multimodal": run_multimodal}[args.experiment](args)
    print(f"total {time.perf_counter() - started:.0f} s; wrote results/cloud-camera-{args.out_name}.*", flush=True)


if __name__ == "__main__":
    main()
