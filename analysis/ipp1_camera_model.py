#!/usr/bin/env python
"""Lane R: camera model for the plasma shape (REQ-B01, REQ-B03, REQ-B05).

Five models on the same frames and the same 5 folds by whole discharge (78 discharges that have camera data):
  magnetic     MLP on the 24 magnetic inputs interpolated to the frame times (the reference)
  rgb          small CNN on the colour frame
  gray         the same CNN on the luma of the frame (a black and white camera)
  multimodal   the CNN features and the magnetic inputs together
  rgb_aug      the colour CNN trained with random shift and rotation
The rgb and rgb_aug models are then tested on frames shifted or rotated after the fact (a camera that moved).

Needs out/ipp1-camera-images.npy and out/ipp1-camera-labels.npz from ipp1_camera_prepare.py.
Run: HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/ipp1_camera_model.py [--epochs 12] [--folds 5]
"""
import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipp1_common import OUT, TARGETS, fit_mlp, group_folds, score
from ipp1_robustness import figure_grid, write_report

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
BATCH, EPOCH_FRACTION = 128, 0.25  # each epoch sees a fresh random quarter of the training frames
SHIFTS = [-16, -8, -4, 0, 4, 8, 16]  # px at 112 px; the view differs by about 3 px between typical discharges, about 20 px at the extremes
ROTATIONS = [-10, -5, -2, 0, 2, 5, 10]  # degrees
AUG_SHIFT, AUG_ROT = 8, 5


def to_input(img, gray):
    """uint8 NHWC batch to a float NCHW tensor; sqrt for the dynamic range, then per image standardization.

    Exposure and colour balance differ a lot between discharges, so each image is normalized by itself.
    """
    x = torch.as_tensor(img).to(DEVICE).permute(0, 3, 1, 2).float() / 255
    if gray:
        x = (x * torch.tensor([.299, .587, .114], device=DEVICE).view(1, 3, 1, 1)).sum(1, keepdim=True)
    x = x.sqrt()
    return (x - x.mean((1, 2, 3), keepdim=True)) / (x.std((1, 2, 3), keepdim=True) + 1e-4)


def affine(x, dx, dy, deg):
    """Shift by (dx, dy) px and rotate by deg around the image centre; per sample tensors or floats."""
    n, _, h, w = x.shape
    dx, dy, deg = (torch.as_tensor(v, dtype=torch.float32, device=x.device).expand(n) for v in (dx, dy, deg))
    a = deg * math.pi / 180
    theta = torch.stack([torch.stack([a.cos(), -a.sin(), dx * 2 / w], 1),
                         torch.stack([a.sin(), a.cos(), dy * 2 / h], 1)], 1)
    return F.grid_sample(x, F.affine_grid(theta, x.shape, align_corners=False), padding_mode="zeros", align_corners=False)


def block(i, o):
    return nn.Sequential(nn.Conv2d(i, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.SiLU(),
                         nn.Conv2d(o, o, 3, stride=2, padding=1, bias=False), nn.BatchNorm2d(o), nn.SiLU())


class CamNet(nn.Module):
    """Four conv blocks (112 to 7 px), global average pooling, optional magnetic branch, linear head."""

    def __init__(self, channels, n_out, n_mag=0):
        super().__init__()
        self.cnn = nn.Sequential(block(channels, 24), block(24, 48), block(48, 96), block(96, 192),
                                 nn.AdaptiveAvgPool2d(1), nn.Flatten())
        self.mag = nn.Sequential(nn.Linear(n_mag, 128), nn.SiLU()) if n_mag else None
        self.head = nn.Sequential(nn.Linear(192 + (128 if n_mag else 0), 256), nn.SiLU(), nn.Linear(256, n_out))

    def forward(self, x, m=None):
        f = self.cnn(x)
        if self.mag is not None:
            f = torch.cat([f, self.mag(m)], 1)
        return self.head(f)


def fit_cnn(imgs, xm, y, mask, train, epochs, seed, gray=False, augment=False, magnetic=False):
    """Masked MSE on standardized targets, like ipp1_common.fit_mlp. Returns predict(indices, perturbation)."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    ym, ys = np.nanmean(y[train], 0), np.nanstd(y[train], 0) + 1e-9
    mu, sd = xm[train].mean(0), xm[train].std(0) + 1e-9
    yt = torch.tensor(np.nan_to_num((y - ym) / ys), dtype=torch.float32)
    mt = torch.tensor(mask, dtype=torch.float32)
    xt = torch.tensor((xm - mu) / sd, dtype=torch.float32)
    net = CamNet(1 if gray else 3, y.shape[1], xm.shape[1] if magnetic else 0).to(DEVICE)
    per_epoch = int(len(train) * EPOCH_FRACTION) // BATCH
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=epochs * per_epoch)
    for _ in range(epochs):
        net.train()
        for _ in range(per_epoch):
            b = np.sort(rng.choice(train, BATCH, replace=False))  # sorted: faster memmap gather
            x = to_input(imgs[b], gray)
            if augment:
                n = len(b)
                x = affine(x, (torch.rand(n, device=DEVICE) * 2 - 1) * AUG_SHIFT, (torch.rand(n, device=DEVICE) * 2 - 1) * AUG_SHIFT,
                           (torch.rand(n, device=DEVICE) * 2 - 1) * AUG_ROT)
            out = net(x, xt[b].to(DEVICE) if magnetic else None)
            loss = ((out - yt[b].to(DEVICE)) ** 2 * mt[b].to(DEVICE)).sum() / mt[b].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
    net.eval()

    def predict(idx, shift=(0, 0), rotation=0):
        out = []
        with torch.no_grad():
            for s in range(0, len(idx), 512):
                b = idx[s:s + 512]
                x = to_input(imgs[b], gray)
                if shift != (0, 0) or rotation:
                    x = affine(x, shift[0], shift[1], rotation)
                out.append(net(x, xt[b].to(DEVICE) if magnetic else None).cpu().numpy())
        return np.concatenate(out) * ys + ym
    return predict


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--run-folds", type=int, default=None, help="run only the first n of the folds (time budget)")
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--stride", type=int, default=3, help="evaluate every n-th test frame (frames are near copies)")
    args = ap.parse_args()
    started = time.perf_counter()
    lab = np.load(OUT / "ipp1-camera-labels.npz")
    y, mask, xm, groups = lab["y"], lab["mask"], lab["x"].astype(np.float32), lab["discharge"]
    assert list(lab["targets"]) == TARGETS
    imgs = np.load(OUT / "ipp1-camera-images.npy")  # into RAM: random access during training
    print(f"{DEVICE}, {len(y)} frames, {len(np.unique(groups))} discharges", flush=True)
    records = []

    def add(fold, case, pred, te):
        records.append({"fold": fold, "case": case, "test_frames": len(te), "scores": score(pred, y[te], mask[te])})

    for fold, (tr, te) in enumerate(group_folds(xm, y, groups, args.folds)):
        assert not set(groups[tr]) & set(groups[te])
        if fold >= (args.run_folds or args.folds):
            break
        te = te[::args.stride]
        t0 = time.perf_counter()
        mlp, _, _ = fit_mlp(xm[tr][::2], y[tr][::2], mask[tr][::2], epochs=60, seed=fold)
        add(fold, "magnetic", mlp(xm[te]), te)
        for case, kw in [("rgb", {}), ("gray", {"gray": True}), ("multimodal", {"magnetic": True}), ("rgb_aug", {"augment": True})]:
            predict = fit_cnn(imgs, xm, y, mask, tr, args.epochs, fold, **kw)
            add(fold, case, predict(te), te)
            if case in ("rgb", "rgb_aug"):
                for dx in SHIFTS[:3] + SHIFTS[4:]:
                    add(fold, f"{case}/shift_x_{dx}", predict(te, shift=(dx, 0)), te)
                    add(fold, f"{case}/shift_y_{dx}", predict(te, shift=(0, dx)), te)
                for deg in ROTATIONS[:3] + ROTATIONS[4:]:
                    add(fold, f"{case}/rotate_{deg}", predict(te, rotation=deg), te)
            r = records[-1 if case not in ("rgb", "rgb_aug") else -(1 + 18)]["scores"]  # the unperturbed case
            print(f"fold {fold + 1}/{args.folds} {case}: {time.perf_counter() - t0:.0f}s, "
                  f"R axis {r['R_mag_axis']['mae']:.2f} mm, elongation {r['elongation']['mae']:.4f}", flush=True)
    notes = ["Frames matched to labels by linear interpolation inside each discharge (analysis/ipp1_camera_prepare.py); 78 discharges.",
             f"Same masked loss and targets as the magnetic baseline; folds by whole discharge (the first {args.run_folds or args.folds} of {args.folds}); model seed equals the fold index.",
             f"CNN: 4 conv blocks, 112x112 input, per image standardization after a square root; {args.epochs} epochs of a random quarter of the training frames.",
             "magnetic: MLP on the 24 inputs interpolated to the frame times, trained on every second frame (60 epochs).",
             "gray: luma of the colour frame, one channel. Shift in px (112 px image) and rotation in degrees are applied to the test frames only (zero padding).",
             "rgb_aug is trained with random shift up to 8 px and rotation up to 5 degrees; tested on the same perturbed frames as rgb.",
             f"Every {args.stride}th test frame is scored. One initialization per fold; the fold SD is not a confidence interval."]
    avg = write_report("camera", args, records, notes, started)
    plot(avg)


def plot(avg):
    fig, axes = figure_grid("IPP 1 · Camera against magnetics on unseen discharges")
    cases = ["magnetic", "rgb", "gray", "multimodal", "rgb_aug"]
    for ax, target in zip(axes[:2], ["R_mag_axis", "elongation"]):
        ax.bar(cases, [avg[c][target]["mae"] for c in cases], color=["#9aabb1", "#176b87", "#6c8f9c", "#b9770e", "#2e8b57"])
        ax.set(title=target, ylabel=f"MAE ({avg['rgb'][target]['unit'] or 'dimensionless'})")
        ax.set_yscale("log")
        ax.grid(axis="y", alpha=.2)
    for ax, kind, values in [(axes[2], "shift_x", SHIFTS), (axes[3], "rotate", ROTATIONS)]:
        for case in ("rgb", "rgb_aug"):
            ax.plot(values, [avg[case if v == 0 else f"{case}/{kind}_{v}"]["R_mag_axis"]["mae"] for v in values], "o-", label=case)
        ax.set(title="R_mag_axis under " + ("horizontal shift" if kind == "shift_x" else "rotation"),
               xlabel="px" if kind == "shift_x" else "degrees", ylabel="MAE (mm)")
        ax.grid(alpha=.2)
    axes[2].legend()
    fig.savefig(OUT / "ipp1-camera.png", dpi=150)


if __name__ == "__main__":
    main()
