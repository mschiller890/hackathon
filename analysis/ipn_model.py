#!/usr/bin/env python
"""The model with the measurements divided by the plasma current: train it and export it for analysis/predict.py.

The field of the coils is proportional to the currents, so the plasma shape depends on the RATIOS of the measurements to the plasma current,
not on their size. The plasma current is known from the inputs alone (a ridge on the 24 measurements, 0.03 kA), so every measurement is divided
by it (signed, so a reversed polarity turns into the same picture) and the current itself is one more input. On the 119 development discharges
(5-fold GroupKFold, one seed) this halves the error of the shipped recipe: mean nRMSE over the 16 outputs 0.0954 -> 0.0447 (results/ipp1-ipn.md).

Inputs of the networks (67 columns for --feat diff2): the 24 divided measurements, the 22 differences of neighbouring coils/loops, the 20 second
differences, and current / 1e5. Networks: a general network (all 16 outputs) and a limiter network on the rows that are really limited, with five
outputs: which side of the vessel the contact point is on (+1 up, -1 down) and where it is on each side (R and Z for up and for down); on the rows
where the general network says is_limited > 0.5 the side is decided and the answer for that side is used, averaged with the general network's own
answer for R_limiter and Z_limiter (predict.py): on the development set the mean of the two is better than either alone. A jump of hundreds of mm
between the two sides is what made a plain regression of the limiter point wrong by 300-500 mm on a few percent of the rows.
Loss: Huber with delta 0.2 on the standardised targets, masked to the targets that exist; AdamW, one-cycle schedule, 150 epochs, batch 512.

    HACKATHON_HOME=<folder> python analysis/ipn_model.py [--feat diff2] [--epochs 150] [--all]        writes out/model/ipp1-ipn.npz and .json
Without --all (as run.py calls it) it trains on the 119 development discharges only: the shipped file and the model behind every number measured on
the 30 set-aside discharges. --all trains on all 149 discharges (the set-aside ones too), not used for the package. THE WEIGHTS ARE DERIVED FROM THE CONFIDENTIAL IPP DATA: out/ is git-ignored.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as Fn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ipp1_final as F
from ipp1_common import OUT

MODEL = OUT / "model"
I_SCALE = 1e5
J, TARGETS = F.J, F.TARGETS
ZL, RL, IL, IP = J["Z_limiter"], J["R_limiter"], J["is_limited"], J["plasma_current"]


def base_features(x, mode):
    """The 24 inputs, the differences of neighbouring coils (15) and loops (7) and, for diff2, the second differences (14 + 6)."""
    parts = [x, np.diff(x[:, :16], axis=1), np.diff(x[:, 16:24], axis=1)]
    if mode == "diff2":
        parts += [np.diff(x[:, :16], 2, axis=1), np.diff(x[:, 16:24], 2, axis=1)]
    return np.concatenate(parts, axis=1)


def features(x, w, b, mode):
    """Divided measurements, their differences and the current itself: the input of every network of the model."""
    cur = x.astype(np.float64) @ w + b
    xs = x * (I_SCALE / cur)[:, None]
    return np.concatenate([base_features(xs, mode), (cur / I_SCALE)[:, None]], axis=1).astype(np.float32)


def fit_net(x, y, ridge, mode, seed, epochs, delta=0.2, widths=(256, 256, 128), on_epoch=None):
    """Returns (net, mu, sd, ym, ys). y may contain NaN for targets that do not exist; those rows contribute nothing to the loss.
    on_epoch(epoch, mean loss, net, mu, sd, ym, ys), if given, is called after every epoch only to show the learning; it draws no random
    numbers and changes no weight, so the trained net is the same with or without it."""
    torch.manual_seed(seed)
    f = features(x, *ridge, mode)
    mu, sd = f.mean(0), f.std(0) + 1e-9
    ym, ys = np.nan_to_num(np.nanmean(y, 0)), np.nanstd(y, 0) + 1e-9
    ys = np.where(np.isnan(ys), 1.0, ys)
    xt = torch.tensor((f - mu) / sd)
    yt = torch.tensor(np.nan_to_num((y - ym) / ys).astype(np.float32))
    mt = torch.tensor((~np.isnan(y)).astype(np.float32))
    net = F.MLP(xt.shape[1], yt.shape[1], widths)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=epochs * ((len(xt) + 511) // 512))
    for epoch in range(1, epochs + 1):
        perm = torch.randperm(len(xt))
        losses = []
        for i in range(0, len(xt), 512):
            b = perm[i:i + 512]
            e = 2 * Fn.huber_loss(net(xt[b]), yt[b], reduction="none", delta=delta)
            loss = (e * mt[b]).sum() / mt[b].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            losses.append(float(loss))
        if on_epoch:
            on_epoch(epoch, float(np.mean(losses)), net, mu, sd, ym, ys)
    net.eval()
    return net, mu.astype(np.float32), sd.astype(np.float32), ym.astype(np.float32), ys.astype(np.float32)


def ridge_current(x, y):
    """(w, b) with current = x @ w + b: the ridge of ipp1_final.fit_ridge_col, read out of its closure."""
    fn = F.fit_ridge_col(x, y, ~np.isnan(y), IP)
    cells = dict(zip(fn.__code__.co_freevars, (c.cell_contents for c in fn.__closure__)))
    return np.asarray(cells["w"], np.float64), float(cells["b"])


def limiter_targets(y):
    """Five outputs for the limiter network: side (+1 up, -1 down), R and Z when up, R and Z when down (NaN where they do not apply)."""
    up = y[:, ZL] > 0
    t = np.full((len(y), 5), np.nan, np.float32)
    t[:, 0] = np.where(up, 1.0, -1.0)
    t[np.ix_(up, [1, 2])] = y[np.ix_(up, [RL, ZL])]
    t[np.ix_(~up, [3, 4])] = y[np.ix_(~up, [RL, ZL])]
    return t


def train(x, y, mode="diff2", epochs=150, seed=0, on_epoch=None, on_spec=None):
    """The whole model trained on the rows given: a dict of arrays in the format of predict.py. on_epoch: see fit_net (general network);
    on_spec() is called before the limiter network is trained."""
    ridge = ridge_current(x, y)
    gen = fit_net(x, y, ridge, mode, seed, epochs, on_epoch=on_epoch and (lambda *a: on_epoch(*a, ridge=ridge)))
    if on_spec:
        on_spec()
    lim = y[:, IL] > 0.5
    spec = fit_net(x[lim], limiter_targets(y[lim]), ridge, mode, seed, epochs)
    arrays = {"ridge_w": ridge[0], "ridge_b": np.float64(ridge[1])}
    for tag, (net, mu, sd, ym, ys) in (("gen", gen), ("spec", spec)):
        layers = [m for m in net.f if isinstance(m, nn.Linear)]
        for i, m in enumerate(layers):
            arrays[f"{tag}_W{i}"] = m.weight.detach().numpy().T.astype(np.float32)
            arrays[f"{tag}_b{i}"] = m.bias.detach().numpy().astype(np.float32)
        arrays[f"{tag}_mu"], arrays[f"{tag}_sd"], arrays[f"{tag}_ym"], arrays[f"{tag}_ys"] = mu, sd, ym, ys
    return arrays


def live_view(x_show, y_show, mode, epochs, started):
    """The learning chart of analysis/mini_pipeline.py for the shipped model: after each epoch the general network estimates the set-aside
    rows (only measured, never trained on) and the chart shows the loss, the axis error in mm and the overall agreement."""
    import shutil
    import mini_pipeline as MP
    live = sys.stdout.isatty()
    MP.ST = MP.Style(live)
    width = min(100, shutil.get_terminal_size((100, 40)).columns) - 1 if live else 99
    view = MP.LearningView(epochs, live, width)
    jr, jz = J["R_mag_axis"], J["Z_mag_axis"]

    def on_epoch(epoch, loss, net, mu, sd, ym, ys, ridge):
        with torch.no_grad():
            pred = net(torch.tensor((features(x_show, *ridge, mode) - mu) / sd)).numpy() * ys + ym
        err = [float(np.nanmean(np.abs(pred[:, j] - y_show[:, j]))) * 1000 for j in (jr, jz)]
        view(epoch, loss, err[0], err[1], time.time() - started, MP.overall_accuracy(pred, y_show))

    def on_spec():
        print(MP.ST.paint(MP.ST.grey, "učí se specialista na bod u limiteru (strana a poloha)"), flush=True)

    return on_epoch, on_spec, view


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--feat", default="diff2", choices=["diff", "diff2"])
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--all", action="store_true", help="train on all 149 discharges instead of the 119 development ones")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--out", default="ipp1-ipn")
    ap.add_argument("--live", action="store_true", help="show the learning as the live chart of the demo: loss, and the axis error on the 30 set-aside "
                    "discharges after every epoch (measured only, never trained on)")
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    started = time.time()
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, lock_idx = F.split(G)
    tr = np.arange(len(X)) if args.all else dev_idx
    on_epoch = on_spec = view = None
    if args.live:
        on_epoch, on_spec, view = live_view(X[lock_idx], Y[lock_idx], args.feat, args.epochs, started)
    arrays = train(X[tr], Y[tr], args.feat, args.epochs, on_epoch=on_epoch, on_spec=on_spec)
    if view:
        view.finish()
    inputs = [c for c in df.columns if c.startswith(("IPR", "FL"))]
    scales = np.array([F.UNIT[t][0] for t in TARGETS], dtype=np.float64)
    meta = {"input_names": inputs, "output_names": list(TARGETS), "output_units": [F.UNIT[t][1] for t in TARGETS],
            "raw_units": "positions in m, plasma current in A, shape numbers and is_limited dimensionless; the output scale turns them into mm and kA",
            "features": f"measurements divided by the plasma current (ridge on the 24 inputs), {args.feat} differences inside one row, and the current / {I_SCALE:g}",
            "limiter": "network with five outputs on the really limited rows: side, R/Z up, R/Z down; used where the general network says is_limited > 0.5",
            "trained_on": f"{len(np.unique(G[tr]))} discharges ({len(tr)} rows), seed 0, {args.epochs} epochs, Huber 0.2",
            "confidential": "weights are derived from the confidential IPP data: never for git"}
    MODEL.mkdir(parents=True, exist_ok=True)
    np.savez(MODEL / f"{args.out}.npz", **arrays, input_names=np.array(inputs), output_names=np.array(TARGETS), output_scales=scales,
             limiter_columns=np.array(F.LIMITER), plasma_current_column=np.array(IP), is_limited_column=np.array(IL),
             ipn=np.array(1), ip_scale=np.array(I_SCALE), feature_mode=np.array(args.feat))
    (MODEL / f"{args.out}.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(f"wrote {MODEL}/{args.out}.npz, {time.time() - started:.0f} s ({meta['trained_on']})")


if __name__ == "__main__":
    main()
