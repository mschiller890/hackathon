#!/usr/bin/env python
"""A bigger camera network (96x128) with augmentation, a shift and rotation test and an occlusion map. Protocol and settings: results/ipp1-camera-v2.md (written before the first run).

    HACKATHON_HOME=... nice -n 10 ~/.venvs/hackathon/bin/python -I analysis/ipp1_camera_v2.py --arm A [--seed 0] [--folds 0 1 2 3 4]    arm A: width 32, 20 epochs
    ... --arm B                                       arm B: A plus random shifts up to 2 px and rotations up to 2 degrees, then C (test moved by 1 px / 1 degree) and D (occlusion map)
    ... --arm mag                                     the magnetic MLP on the same training and test frames
    ... --probe                                       time a few training steps and stop
    ... --report                                      results/ipp1-camera-v2.md (below the protocol) and results/ipp1-camera-v2-occlusion.png

Needs out/ipp1-camera-v2-grey.npy (ipp1_camera_v2_prepare.py) and out/ipp1-camera-labels.npz (ipp1_camera_prepare.py). Aggregates only; no frame leaves out/.
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
import torch.nn.functional as Fn

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, ROOT, TARGETS, UNIT, fit_mlp, group_folds, score as _score

DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
GREY = OUT / "ipp1-camera-v2-grey.npy"
LABELS = OUT / "ipp1-camera-labels.npz"
CACHE = OUT / "ipp1-camera-v2-cache"
REPO = ROOT / "repo"
MD = REPO / "results/ipp1-camera-v2.md"
MARKER = "<!-- RESULTS BELOW -->"
MOVES = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]       # (dx pixels, dy pixels, degrees)
PATCH, STEP = 16, 16                                                                   # occlusion patch and step in pixels
OCC_TARGETS = ["R_mag_axis", "Z_mag_axis", "elongation", "R_strike_point_1"]
ARMS = {"A": dict(width=32, epochs=20, augment=False), "B": dict(width=32, epochs=20, augment=True)}
J = {t: i for i, t in enumerate(TARGETS)}


class CamNet(nn.Module):
    """The network of analysis/cloud_camera_model.py: two coordinate channels, six convolution blocks, 4x4 pooling, a head of 256 units (coordinates built on the input's device)."""

    def __init__(self, c_in, n_out, width):
        super().__init__()
        block = lambda i, o, s: nn.Sequential(nn.Conv2d(i, o, 3, s, 1, bias=False), nn.BatchNorm2d(o), nn.SiLU())
        w = width
        self.conv = nn.Sequential(block(c_in + 2, w, 2), block(w, 2 * w, 1), block(2 * w, 4 * w, 2), block(4 * w, 4 * w, 1), block(4 * w, 8 * w, 2), block(8 * w, 8 * w, 1),
                                  nn.AdaptiveAvgPool2d(4), nn.Flatten())
        self.head = nn.Sequential(nn.Linear(8 * w * 16, 256), nn.SiLU(), nn.Linear(256, n_out))

    def forward(self, img):
        n, _, h, w = img.shape
        yy, xx = torch.meshgrid(torch.linspace(-1, 1, h, device=img.device), torch.linspace(-1, 1, w, device=img.device), indexing="ij")
        return self.head(self.conv(torch.cat([img, torch.stack([xx, yy]).expand(n, -1, -1, -1)], 1)))


def affine(batch, dx, dy, deg):
    """Move the image content by (dx, dy) pixels and rotate it by deg degrees about the centre; per sample tensors on the device of the batch (border padding)."""
    n, _, h, w = batch.shape
    a = torch.deg2rad(deg)
    theta = torch.zeros(n, 2, 3, device=batch.device)
    theta[:, 0, 0], theta[:, 0, 1] = torch.cos(a), -torch.sin(a) * h / w
    theta[:, 1, 0], theta[:, 1, 1] = torch.sin(a) * w / h, torch.cos(a)
    theta[:, 0, 2], theta[:, 1, 2] = -2 * dx / w, -2 * dy / h
    return Fn.grid_sample(batch, Fn.affine_grid(theta, batch.shape, align_corners=False), padding_mode="border", align_corners=False)


def perturb(b, max_shift, max_deg):
    n = len(b)
    u = lambda m: (torch.rand(n, device=b.device) * 2 - 1) * m
    return affine(b, u(max_shift), u(max_shift), u(max_deg))


def fixed(b, dx, dy, deg):
    full = lambda v: torch.full((len(b),), float(v), device=b.device)
    return affine(b, full(dx), full(dy), full(deg))


def load_data():
    lab = np.load(LABELS)
    g = lab["discharge"]
    order = np.argsort(g, kind="stable")
    start = np.r_[0, np.flatnonzero(np.diff(g[order])) + 1]
    rank = np.empty(len(g), dtype=np.int64)
    rank[order] = np.arange(len(g)) - np.repeat(start, np.diff(np.r_[start, len(g)]))
    return np.load(GREY, mmap_mode="r"), lab["y"], lab["mask"], lab["x"].astype(np.float32), g, rank


def make_folds(y, g, rank):
    """Test frames: every 8th frame of the held-out discharges (those of the old network); training frames: every 4th frame of the others. GroupKFold on the sizes of the stride-8 groups
    reproduces the fold assignment of the cloud run."""
    k8, k4 = np.flatnonzero(rank % 8 == 0), np.flatnonzero(rank % 4 == 0)
    folds = []
    for _, te8 in group_folds(np.zeros((len(k8), 1)), y[k8], g[k8], 5):
        held = np.unique(g[k8][te8])
        folds.append((k4[~np.isin(g[k4], held)], k8[te8]))
    return folds


def fit_cnn(img, y, m, width, epochs, seed, augment, max_steps=None, log=None):
    """Masked-loss training as ipp1_common.fit_mlp. img: uint8 (n, H, W). Returns predict(img, transform=None, patch=None) -> raw targets, and the network."""
    torch.manual_seed(seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        ym, ys = np.nanmean(y, 0), np.nanstd(y, 0) + 1e-9
    yt = torch.tensor(np.nan_to_num((y - ym) / ys), dtype=torch.float32, device=DEV)
    mt = torch.tensor(m.astype(np.float32), device=DEV)
    imgs = torch.from_numpy(np.ascontiguousarray(img)).to(DEV).unsqueeze(1)
    probe = imgs[torch.randperm(len(imgs))[:2000].to(DEV)].float() / 255
    pm, ps = probe.mean(), probe.std() + 1e-6
    net = CamNet(1, y.shape[1], width).to(DEV)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    batch = 128
    steps = epochs * ((len(imgs) + batch - 1) // batch)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=steps)
    net.train()
    done = 0
    for epoch in range(epochs):
        perm = torch.randperm(len(imgs)).to(DEV)
        for i in range(0, len(perm), batch):
            b = perm[i:i + batch]
            if len(b) < 2:
                continue
            xb = imgs[b].float() / 255
            if augment:
                xb = perturb(xb, 2.0, 2.0)
            loss = ((net((xb - pm) / ps) - yt[b]) ** 2 * mt[b]).sum() / mt[b].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            done += 1
            if max_steps and done >= max_steps:
                return None, net
        if log:
            log(f"epoch {epoch + 1}/{epochs}")
    net.eval()

    def predict(im, transform=None, patch=None, chunk=512):
        out = []
        with torch.no_grad():
            for i in range(0, len(im), chunk):
                xb = torch.from_numpy(np.ascontiguousarray(im[i:i + chunk])).to(DEV).unsqueeze(1).float() / 255
                if transform is not None:
                    xb = transform(xb)
                xb = (xb - pm) / ps
                if patch is not None:                        # the patch has the mean grey level of the training frames: 0 after standardisation
                    r, c = patch
                    xb[:, :, r:r + PATCH, c:c + PATCH] = 0.0
                out.append(net(xb).cpu().numpy())
        return np.concatenate(out) * ys + ym
    return predict, net


def score(pred, y, m):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return _score(pred, y, m)


def run_arm(arm, seed, fold_ids, epochs_override=None):
    img, y, m, x, g, rank = load_data()
    folds = make_folds(y, g, rank)
    CACHE.mkdir(parents=True, exist_ok=True)
    t_all = time.perf_counter()
    for k in fold_ids:
        out_file = CACHE / f"{arm}_s{seed}_f{k}.npz"
        if out_file.exists():
            print(f"{arm} seed {seed} fold {k}: cached, skipped", flush=True)
            continue
        tr, te = folds[k]
        t0 = time.perf_counter()
        if arm == "mag":
            predict, _, _ = fit_mlp(x[tr], y[tr], m[tr], 60, seed=k + 10 * seed)
            np.savez(out_file, idx_test=te, pred=predict(x[te]).astype(np.float32), seconds=time.perf_counter() - t0)
            print(f"mag seed {seed} fold {k}: {time.perf_counter() - t0:.0f} s", flush=True)
            continue
        cfg = dict(ARMS[arm])
        if epochs_override:
            cfg["epochs"] = epochs_override
        predict, net = fit_cnn(img[tr], y[tr], m[tr], cfg["width"], cfg["epochs"], k + 10 * seed, cfg["augment"],
                               log=lambda s: print(f"  {arm} seed {seed} fold {k} {s}, {time.perf_counter() - t0:.0f} s", flush=True))
        train_s = time.perf_counter() - t0
        pred = predict(img[te])
        moved = np.stack([predict(img[te], transform=lambda b, mv=mv: fixed(b, *mv)) for mv in MOVES])
        payload = dict(idx_test=te, pred=pred.astype(np.float32), moved=moved.astype(np.float32), seconds=train_s, parameters=int(sum(p.numel() for p in net.parameters())))
        if arm == "B":                                      # D: the occlusion map of the B network
            h, w = img.shape[1:]
            rows, cols = range(0, h - PATCH + 1, STEP), range(0, w - PATCH + 1, STEP)
            base = {t: np.abs(pred[:, J[t]] - y[te, J[t]]) * UNIT[t][0] for t in OCC_TARGETS}
            occ = np.zeros((len(OCC_TARGETS), len(rows), len(cols)), dtype=np.float32)
            for a, r in enumerate(rows):
                for b, c in enumerate(cols):
                    po = predict(img[te], patch=(r, c))
                    for ti, t in enumerate(OCC_TARGETS):
                        ok = m[te, J[t]]
                        occ[ti, a, b] = float((np.abs(po[ok, J[t]] - y[te][ok, J[t]]) * UNIT[t][0] - base[t][ok]).mean())
            payload["occlusion"] = occ
        np.savez(out_file, **payload)
        print(f"{arm} seed {seed} fold {k}: trained {train_s:.0f} s, total {time.perf_counter() - t0:.0f} s, {payload['parameters']} parameters", flush=True)
    print(f"done in {time.perf_counter() - t_all:.0f} s", flush=True)


def probe():
    img, y, m, x, g, rank = load_data()
    tr, te = make_folds(y, g, rank)[0]
    print(f"device {DEV}; fold 0: {len(tr)} training frames, {len(te)} test frames", flush=True)
    for arm in ("A", "B"):
        cfg = ARMS[arm]
        t0 = time.perf_counter()
        fit_cnn(img[tr], y[tr], m[tr], cfg["width"], 1, 0, cfg["augment"], max_steps=60)
        dt = time.perf_counter() - t0
        steps = cfg["epochs"] * ((len(tr) + 127) // 128)
        print(f"arm {arm}: 60 steps in {dt:.1f} s (including start-up), {dt / 60:.3f} s per step; 20 epochs = {steps} steps = about {steps * dt / 60 / 60:.0f} min per fold, {5 * steps * dt / 60 / 60:.0f} min for 5 folds", flush=True)


# ----------------------------------------------------------------------------- report
def load_arm(arm, seed):
    files = [CACHE / f"{arm}_s{seed}_f{k}.npz" for k in range(5)]
    return [np.load(f) for f in files] if all(f.exists() for f in files) else None


def aggregate(arm, seed, y, m):
    folds = load_arm(arm, seed)
    if folds is None:
        return None
    per = [score(d["pred"], y[d["idx_test"]], m[d["idx_test"]]) for d in folds]
    agg = {}
    for t in TARGETS:
        v = lambda k: float(np.nanmean([f[t][k] for f in per]))
        agg[t] = {"mae": v("mae"), "nrmse": v("nrmse"), "mae_sd": float(np.std([f[t]["mae"] for f in per])), "unit": per[0][t]["unit"]}
        if t == "is_limited":
            agg[t]["accuracy"] = v("accuracy")
    return agg, folds


def write_report():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _, y, m, x, g, rank = load_data()
    cloud = json.loads((REPO / "results/cloud-camera-main.json").read_text())["results"]["grey"]
    res = {k: aggregate(*spec, y, m) for k, spec in {"mag": ("mag", 0), "A": ("A", 0), "B": ("B", 0), "A1": ("A", 1)}.items()}
    done = {k: v is not None for k, v in res.items()}
    fmt = lambda v: f"{v:.3g}"
    unit = {t: UNIT[t][1] or "-" for t in TARGETS}
    L = ["", "## Results", "", "Status: " + ", ".join(f"{n} {'finished' if done[k] else 'NOT RUN or not finished'}" for k, n in
                                                    (("mag", "magnetic MLP"), ("A", "arm A"), ("B", "arm B (with C and D)"), ("A1", "second seed of A"))) + ".", ""]
    cols = [("mag", "magnetic MLP (same frames)"), ("old", "old small network"), ("A", "this 96x128 network, A"), ("B", "this 96x128 network, B (augmented)")]
    L += ["MAE in mm (plasma current in kA, shape numbers dimensionless) and nRMSE (RMSE / SD of the target), mean over the 5 folds, test frames = every 8th frame of the held-out discharges. "
          "Old small network = grey, 48x64, width 16, 12 epochs (`results/cloud-camera-main.md`, seed 0).", "",
          "| target | unit | " + " | ".join(f"{n} MAE | nRMSE" for _, n in cols) + " |", "|---|---|" + "---:|---:|" * len(cols)]
    for t in TARGETS:
        if t == "is_limited":
            continue
        cells = []
        for k, _ in cols:
            r = cloud[t] if k == "old" else (res[k][0][t] if res[k] else None)
            cells.append(f"{fmt(r['mae'])} | {fmt(r['nrmse'])}" if r else "n/a | n/a")
        L.append(f"| {t} | {unit[t]} | " + " | ".join(cells) + " |")
    acc = {k: (res[k][0]["is_limited"]["accuracy"] if res[k] else None) for k in ("mag", "A", "B")}
    L += ["", "`is_limited` agreement: magnetic MLP " + (f"{acc['mag']:.3f}" if acc["mag"] else "n/a") + f", old small network 0.975, A " + (f"{acc['A']:.3f}" if acc["A"] else "n/a")
          + ", B " + (f"{acc['B']:.3f}" if acc["B"] else "n/a") + ".", ""]
    secs = {k: [float(d["seconds"]) for d in res[k][1]] for k in ("A", "B") if res[k]}
    params = {k: int(res[k][1][0]["parameters"]) for k in ("A", "B") if res[k]}
    L += ["Training time per fold on the Apple GPU: " + ", ".join(f"{k} {np.mean(v):.0f} s" for k, v in secs.items()) + "; parameters: " + ", ".join(f"{k} {v:,}" for k, v in params.items()) + ".", ""]
    # C
    if done["A"] or done["B"]:
        head = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "R_x_point", "R_strike_point_1", "R_limiter", "Z_limiter"]
        L += ["## C. Robustness: the test frame moved by 1 pixel or rotated by 1 degree (REQ-B05)", "",
              "Ratio = MAE with the moved test frame / MAE with the unmoved test frame, mean over the six moves (right, left, down, up by 1 pixel at 96x128; +1 and -1 degree) and the 5 folds; 1.00 = no change.", "",
              "| target | " + " | ".join(f"A, unmoved MAE | A ratio" if k == "A" else "B, unmoved MAE | B ratio" for k in ("A", "B") if done[k]) + " |", "|---|" + "---:|---:|" * sum(done[k] for k in ("A", "B"))]
        for t in head:
            row = []
            for k in ("A", "B"):
                if not done[k]:
                    continue
                ratios = []
                for mv in range(len(MOVES)):
                    num = np.mean([np.abs(d["moved"][mv][:, J[t]] - y[d["idx_test"], J[t]])[m[d["idx_test"], J[t]]].mean() for d in res[k][1]])
                    den = np.mean([np.abs(d["pred"][:, J[t]] - y[d["idx_test"], J[t]])[m[d["idx_test"], J[t]]].mean() for d in res[k][1]])
                    ratios.append(num / den)
                row.append(f"{fmt(res[k][0][t]['mae'])} | {np.mean(ratios):.2f} (worst move {max(ratios):.2f})")
            L.append(f"| {t} | " + " | ".join(row) + " |")
        L.append("")
    # D
    if done["B"]:
        occ = np.mean([d["occlusion"] for d in res["B"][1]], axis=0)
        fig, ax = plt.subplots(1, len(OCC_TARGETS), figsize=(14, 2.9), constrained_layout=True)
        for a, (t, mp) in zip(ax, zip(OCC_TARGETS, occ)):
            im = a.imshow(mp, cmap="magma", aspect="auto")
            a.set_title(f"{t} [{unit[t]}]", fontsize=9)
            a.set_xticks(range(mp.shape[1])); a.set_xticklabels([f"{PATCH // 1 * c}" for c in range(mp.shape[1])], fontsize=6)
            a.set_yticks(range(mp.shape[0])); a.set_yticklabels([f"{PATCH * r}" for r in range(mp.shape[0])], fontsize=6)
            a.set_xlabel("patch column (px)", fontsize=7); a.set_ylabel("patch row (px)", fontsize=7)
            fig.colorbar(im, ax=a, shrink=0.8).ax.tick_params(labelsize=6)
        fig.suptitle("This 96x128 camera network (B): rise of the mean absolute error when a 16x16 px grey patch hides that part of the frame (mean over frames and 5 folds)", fontsize=9)
        fig.savefig(REPO / "results/ipp1-camera-v2-occlusion.png", dpi=150)
        L += ["## D. Occlusion map (REQ-B07)", "", f"`results/ipp1-camera-v2-occlusion.png`: for every position of a {PATCH}x{PATCH} px grey patch (grid of {occ.shape[1]} x {occ.shape[2]}, steps of {STEP} px) the rise of the mean absolute error of "
              "the B network over the unoccluded frame, aggregate over the test frames and the 5 folds; no frame is shown.", "",
              "| target | unit | error unoccluded | largest rise | at patch (row, column in px) | median rise over the grid | patches with a rise above half of the largest |", "|---|---|---:|---:|---|---:|---:|"]
        for t, mp in zip(OCC_TARGETS, occ):
            base_mae = res["B"][0][t]["mae"]
            r, c = np.unravel_index(np.argmax(mp), mp.shape)
            L.append(f"| {t} | {unit[t]} | {fmt(base_mae)} | {fmt(mp.max())} | ({PATCH * r}, {PATCH * c}) | {fmt(np.median(mp))} | {int((mp > mp.max() / 2).sum())} of {mp.size} |")
        L.append("")
    # seed spread
    if done["A"] and done["A1"]:
        L += ["## Second seed of arm A (seed spread)", "", "| target | unit | MAE seed 0 | MAE seed 1 | difference | relative |", "|---|---|---:|---:|---:|---:|"]
        for t in TARGETS:
            if t == "is_limited":
                continue
            a0, a1 = res["A"][0][t]["mae"], res["A1"][0][t]["mae"]
            L.append(f"| {t} | {unit[t]} | {fmt(a0)} | {fmt(a1)} | {fmt(a1 - a0)} | {100 * (a1 / a0 - 1):+.0f} % |")
        L.append("")
    old = MD.read_text()
    MD.write_text(old.split(MARKER)[0] + MARKER + "\n" + "\n".join(L) + "\n" + (("\n## Reading" + old.split("\n## Reading", 1)[1]) if "\n## Reading" in old else ""))
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=["A", "B", "mag"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--folds", type=int, nargs="*", default=list(range(5)))
    ap.add_argument("--epochs", type=int, default=None, help="override the epochs of the arm (for a test run only; not the protocol)")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    if a.probe:
        probe()
    if a.arm:
        run_arm(a.arm, a.seed, a.folds, a.epochs)
    if a.report:
        write_report()


if __name__ == "__main__":
    main()
