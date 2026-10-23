#!/usr/bin/env python
"""IPP task 1: try to beat the baseline network, with the same protocol and also under noise.

Protocol (unchanged): 5-fold GroupKFold by whole discharges, masked loss, ipp1_common.score, >= 60 epochs.
Every configuration is trained on the clean training discharges (plain) or on clean + one corrupted copy
(aug: Gaussian noise 0.15 and per-coil drift 0.15 of the training input SD, exactly the augmentation of
ipp1_robustness.py) and tested on the SAME held-out discharges twice: the clean file and the provided noisy file.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_improve.py --run base,wide [--aug] [--threads 2]
    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_improve.py --report

--run trains the named configurations and caches aggregate scores in out/ipp1-improve-cache/ (no rows are stored);
--report assembles out/ipp1-improve.json, out/ipp1-improve.md and the copy repo/results/ipp1-improve.md.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, ROOT, TARGETS, fit_mlp, group_folds, load, score

CACHE = OUT / "ipp1-improve-cache"
FAST = False   # --latency trains for one epoch: timing does not depend on the weights
DEV = torch.device("cpu")   # --device mps trains on the Apple GPU; the trained net is moved back to the CPU
J = {t: i for i, t in enumerate(TARGETS)}
LIMITER = [J["R_limiter"], J["Z_limiter"]]
SUMMARY_T = [t for t in TARGETS if t not in ("R_limiter", "Z_limiter")]       # 14 targets, incl. is_limited
SUMMARY_T13 = [t for t in SUMMARY_T if t != "is_limited"]                      # 13 continuous targets
NOISE, DRIFT, AUG_SEED = 0.15, 0.15, 20261023                                  # as ipp1_robustness.py


# ----------------------------------------------------------------------------- data
def aligned_data():
    clean = load()
    noisy = load(noisy=True)
    if not (np.array_equal(clean[0].discharge, noisy[0].discharge)
            and np.allclose(clean[0].time, noisy[0].time, rtol=0, atol=1e-9)):
        raise ValueError("clean and noisy rows are not aligned")
    if not np.array_equal(clean[2], noisy[2], equal_nan=True):
        raise ValueError("clean and noisy targets differ")
    return clean, noisy[1]


def corrupt(x, groups, times, scale, noise, drift, seed):
    """Row noise plus an independent Gaussian slope per discharge and coil (same as ipp1_robustness.corrupt)."""
    rng = np.random.default_rng(seed)
    _, inverse = np.unique(groups, return_inverse=True)
    slopes = rng.normal(size=(inverse.max() + 1, x.shape[1])) * drift * scale
    return (x + rng.normal(size=x.shape) * noise * scale + slopes[inverse] * times[:, None]).astype(np.float32)


def feats(x, kind):
    """raw: the 24 inputs. diff: plus differences of neighbouring coils IPR01..16 (15) and loops FL01..08 (7)."""
    if kind == "raw":
        return x
    return np.concatenate([x, np.diff(x[:, :16], axis=1), np.diff(x[:, 16:24], axis=1)], 1).astype(np.float32)


# ----------------------------------------------------------------------------- the network trainer
class MLP(nn.Module):
    def __init__(self, n_in, n_out, widths, skip):
        super().__init__()
        layers, d = [], n_in
        for w in widths:
            layers += [nn.Linear(d, w), nn.SiLU()]
            d = w
        layers.append(nn.Linear(d, n_out))
        self.f = nn.Sequential(*layers)
        self.lin = nn.Linear(n_in, n_out) if skip else None   # linear skip: net = MLP(x) + W x

    def forward(self, x):
        return self.f(x) if self.lin is None else self.f(x) + self.lin(x)


def fit_net(xtr, ytr, mtr, seed=0, arch=(256, 256, 128), epochs=60, wd=1e-4, loss="mse", delta=1.0,
            tw=None, skip=False, feat="raw", lr=2e-3, max_lr=3e-3, batch=512, rows=None, resid=False):
    """Same recipe as ipp1_common.fit_mlp (standardised inputs and targets, masked loss, AdamW, OneCycle),
    with the knobs of this experiment. rows: optional boolean mask of training rows to use. resid: first fit a ridge
    regression per target (closed form, alpha 1, as ipp1_common.fit_ridge) and let the network learn only what the
    linear map leaves over; the plasma current is almost exactly linear in the 24 measurements, and the ridge
    gets 0.03 kA where the plain network gets 1.5 kA."""
    if rows is not None:
        xtr, ytr, mtr = xtr[rows], ytr[rows], mtr[rows]
    epochs = 1 if FAST else epochs
    torch.manual_seed(seed)
    ftr = feats(xtr, feat)
    mu, sd = ftr.mean(0), ftr.std(0) + 1e-9
    ym, ys = np.nanmean(ytr, 0), np.nanstd(ytr, 0) + 1e-9
    xt = torch.tensor((ftr - mu) / sd)
    yt = torch.tensor(np.nan_to_num((ytr - ym) / ys))
    xcpu = xt.numpy()
    w = np.ones(len(TARGETS), np.float32)
    for t, v in (tw or {}).items():
        w[J[t]] = v
    mt = torch.tensor(mtr.astype(np.float32) * w)
    if resid:
        from sklearn.linear_model import Ridge
        z = (ytr - ym) / ys
        rg = [Ridge(alpha=1.0).fit(xcpu[mtr[:, j]], z[mtr[:, j], j]) for j in range(z.shape[1])]
        rw = np.column_stack([m.coef_ for m in rg]).astype(np.float32)
        rb = np.array([m.intercept_ for m in rg], np.float32)
        base_t = xt @ torch.from_numpy(rw) + torch.from_numpy(rb)
    else:
        base_t = torch.zeros_like(yt)
    net = MLP(xt.shape[1], yt.shape[1], arch, skip).to(DEV)
    xt, yt, mt, base_t = xt.to(DEV), yt.to(DEV), mt.to(DEV), base_t.to(DEV)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=wd)
    steps = epochs * ((len(xt) + batch - 1) // batch)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=max_lr, total_steps=steps)
    for _ in range(epochs):
        perm = torch.randperm(len(xt), device=DEV)
        for i in range(0, len(xt), batch):
            b = perm[i:i + batch]
            out = net(xt[b]) + base_t[b]
            e = (out - yt[b]) ** 2 if loss == "mse" else 2 * F.huber_loss(out, yt[b], reduction="none", delta=delta)
            l = (e * mt[b]).sum() / mt[b].sum()
            opt.zero_grad()
            l.backward()
            opt.step()
            sched.step()
    net.cpu().eval()
    mu32, sd32 = mu.astype(np.float32), sd.astype(np.float32)
    if resid:
        rwt, rbt = torch.from_numpy(rw), torch.from_numpy(rb)

    def predict(x):
        with torch.inference_mode():
            z = torch.from_numpy((feats(x, feat) - mu32) / sd32)
            o = net(z) + (z @ rwt + rbt if resid else 0.0)
            return o.numpy() * ys + ym
    return predict


def ensemble(preds):
    return lambda x: np.mean([p(x) for p in preds], axis=0)


def fit_lgbm_limiter(xtr, ytr, mtr, seed=0, feat="diff", n=300, lr=0.1):
    """One LightGBM per limiter coordinate, trained on the limited rows only. Returns predict -> (n, 16) with NaN
    outside the two limiter columns. Inference goes through Booster.predict: the sklearn wrapper adds about 0.4 ms of
    input checking per call, the booster itself takes about 0.06 ms for 300 trees."""
    import lightgbm as lgb
    rows = ytr[:, J["is_limited"]] > 0.5
    ftr = feats(xtr[rows], feat)
    boosters = {}
    for j in LIMITER:
        k = mtr[rows, j]
        boosters[j] = lgb.LGBMRegressor(n_estimators=n, learning_rate=lr, num_leaves=63, subsample=0.8, subsample_freq=1,
                                        colsample_bytree=0.8, min_child_samples=10, n_jobs=1, verbose=-1,
                                        random_state=seed).fit(ftr[k], ytr[rows][k, j]).booster_

    def predict(x):
        f = feats(x, feat).astype(np.float64)
        out = np.full((len(x), len(TARGETS)), np.nan, np.float32)
        for j, b in boosters.items():
            out[:, j] = b.predict(f, num_threads=1)
        return out
    return predict


def gate(general, special, cols):
    """Use the specialist for the given columns on rows where the general net predicts is_limited > 0.5; the
    general net answers everywhere else (including a truly limited row it wrongly calls divertor)."""
    cols = list(cols)

    def predict(x):
        p = general(x).copy()
        g = p[:, J["is_limited"]] > 0.5
        if g.any():
            s = special(x[g])
            p[np.ix_(g, cols)] = s[:, cols]
        return p
    return predict


# ----------------------------------------------------------------------------- configurations
BASE = dict(arch=(256, 256, 128), epochs=60)
STRONG = ("R_limiter", "Z_limiter", "R_mag_axis", "Z_mag_axis")


def S_net(**kw):
    """A plain network configuration."""
    cfg = {**BASE, **kw}
    return lambda xt, yt, mt, fold: {"": fit_net(xt, yt, mt, seed=fold, **cfg)}


def S_ens(n, **kw):
    cfg = {**BASE, **kw}
    return lambda xt, yt, mt, fold: {"": ensemble([fit_net(xt, yt, mt, seed=fold + 100 * s, **cfg) for s in range(n)])}


def S_gate_nn(spec_cfg=None, general_cfg=None):
    """General network + a network trained on the limited rows only, gated by the predicted is_limited."""
    gcfg = {**BASE, **(general_cfg or {})}
    scfg = {**BASE, "epochs": 120, **(spec_cfg or {})}

    def fn(xt, yt, mt, fold):
        gen = fit_net(xt, yt, mt, seed=fold, **gcfg)
        rows = yt[:, J["is_limited"]] > 0.5
        spec = fit_net(xt, yt, mt, seed=fold, rows=rows, **scfg)
        allc = [j for j in range(len(TARGETS)) if mt[rows, j].any() and j != J["is_limited"]]
        return {"general only": gen, "limiter point from specialist": gate(gen, spec, LIMITER),
                "all limited targets from specialist": gate(gen, spec, allc)}
    return fn


def S_gate_lgbm(general_cfg=None):
    gcfg = {**BASE, **(general_cfg or {})}

    def fn(xt, yt, mt, fold):
        gen = fit_net(xt, yt, mt, seed=fold, **gcfg)
        return {"limiter point from LightGBM": gate(gen, fit_lgbm_limiter(xt, yt, mt, seed=fold), LIMITER)}
    return fn


def fit_ridge_col(xtr, ytr, mtr, j, alpha=1.0):
    """Ridge regression for ONE target on standardised inputs (the same ridge as ipp1_common.fit_ridge), folded into raw
    coefficients so that predict is one dot product (about a microsecond)."""
    from sklearn.linear_model import Ridge
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-9
    m = Ridge(alpha=alpha).fit((xtr[mtr[:, j]] - mu) / sd, ytr[mtr[:, j], j])
    w = (m.coef_ / sd).astype(np.float64)
    b = float(m.intercept_ - (mu * w).sum())
    return lambda x: x.astype(np.float64) @ w + b


def override(pred, col, fn):
    def predict(x):
        p = pred(x).copy()
        p[:, col] = fn(x)
        return p
    return predict


def S_combo(feat="diff", n_gen=1, **kw):
    """General network (+ ridge for the plasma current, which is linear in the measurements) (+ a specialist network on the
    limited rows for the limiter point, gated by the predicted is_limited)."""
    ip = J["plasma_current"]

    def fn(xt, yt, mt, fold):
        gens = [fit_net(xt, yt, mt, seed=fold + 100 * s, feat=feat, **{**BASE, **kw}) for s in range(n_gen)]
        gen = gens[0] if n_gen == 1 else ensemble(gens)
        rows = yt[:, J["is_limited"]] > 0.5
        spec = fit_net(xt, yt, mt, seed=fold, rows=rows, feat=feat, **{**BASE, "epochs": 120, **kw})
        gen_ip = override(gen, ip, fit_ridge_col(xt, yt, mt, ip))
        return {"net": gen, "net + ridge Ip": gen_ip, "net + ridge Ip + limiter net": gate(gen_ip, spec, LIMITER),
                "net + ridge Ip + limiter LightGBM": gate(gen_ip, fit_lgbm_limiter(xt, yt, mt, seed=fold, feat=feat), LIMITER)}
    return fn


def S_common():
    return lambda xt, yt, mt, fold: {"": fit_mlp(xt, yt, mt, 60, seed=fold)[0]}


SPECS = {
    "base": (S_common(), "baseline: ipp1_common.fit_mlp, 256-256-128, 60 epochs"),
    "base_mine": (S_net(), "baseline recipe re-implemented in this script (sanity check)"),
    # (1) width, depth, training length, weight decay
    "wide": (S_net(arch=(512, 512, 256)), "wider 512-512-256, 60 epochs"),
    "deep": (S_net(arch=(256, 256, 256, 256, 128)), "deeper 256x4-128, 60 epochs"),
    "long150": (S_net(epochs=150), "256-256-128, 150 epochs"),
    "wd1e-2": (S_net(wd=1e-2), "weight decay 1e-2"),
    "wd1e-1": (S_net(wd=1e-1), "weight decay 1e-1"),
    "wide_long": (S_net(arch=(512, 512, 256), epochs=120), "512-512-256, 120 epochs"),
    # (2) loss
    "huber": (S_net(loss="huber", delta=0.5), "Huber loss (delta 0.5 SD of the target)"),
    "weights": (S_net(tw={t: 3.0 for t in STRONG}), "per-target loss weight 3 on R/Z_limiter and R/Z_mag_axis"),
    # (5) inputs
    "lin": (S_net(skip=True), "linear skip connection (MLP + linear map of the standardised inputs)"),
    "diff": (S_net(feat="diff"), "inputs + differences of neighbouring coils (46 features)"),
    "lin_diff": (S_net(skip=True, feat="diff"), "linear skip + neighbour differences"),
    "resid": (S_net(resid=True), "ridge first, network on the residual (frozen linear part)"),
    "resid_diff": (S_net(resid=True, feat="diff"), "ridge first + network on the residual, neighbour-difference features"),
    # combinations (neighbour differences, ridge for the plasma current, limited-configuration specialist)
    "combo_diff": (S_combo("diff"), "neighbour-difference features; ridge for plasma current; limited-row specialist (network or LightGBM) for the limiter point"),
    "combo_raw": (S_combo("raw"), "raw inputs; ridge for plasma current; limited-row specialist (network or LightGBM) for the limiter point"),
    "combo_diff_huber": (S_combo("diff", 1, loss="huber", delta=0.5), "as combo_diff with Huber loss (delta 0.5) in the networks"),
    "combo_deep_huber": (S_combo("diff", 1, arch=(256, 256, 256, 256, 128), loss="huber", delta=0.5),
                         "as combo_diff_huber with the networks 256x4-128 deep"),
    "combo_long": (S_combo("diff", 1, loss="huber", delta=0.5, epochs=150),
                   "as combo_diff_huber, 150 epochs for the general network and for the limiter network"),
    "combo_diff_ens3": (S_combo("diff", 3), "as combo_diff with the general network an ensemble of 3 seeds"),
    # (4) ensembles
    "ens3": (S_ens(3), "ensemble of 3 seeds, baseline recipe"),
    "ens5": (S_ens(5), "ensemble of 5 seeds, baseline recipe"),
    # (3) limited-configuration specialists
    "gate_nn": (S_gate_nn(), "specialist network (limited rows only, 120 epochs) gated by predicted is_limited"),
    "gate_lgbm": (S_gate_lgbm(), "LightGBM, 300 trees, neighbour-difference features (limited rows only) for the limiter point, gated by predicted is_limited"),
}


def add_spec(name, desc, fn):
    SPECS[name] = (fn, desc)


# ----------------------------------------------------------------------------- running and caching
def time_predict(pred, x1, reps=1500, rounds=3):
    """Median end-to-end latency of predict() for ONE raw sample, ms (best of rounds, shared loaded machine)."""
    for _ in range(100):
        pred(x1)
    best = []
    for _ in range(rounds):
        ts = np.empty(reps)
        for i in range(reps):
            a = time.perf_counter()
            pred(x1)
            ts[i] = time.perf_counter() - a
        best.append(float(np.median(ts) * 1000))
    return min(best)


def fold_aggregate(scores):
    out = {}
    for t in TARGETS:
        out[t] = {k: float(np.mean([s[t][k] for s in scores])) for k in scores[0][t] if k != "unit"}
        out[t]["unit"] = scores[0][t]["unit"]
        out[t]["fold_mae"] = [float(s[t]["mae"]) for s in scores]
    return out


def summary(agg, targets):
    return float(np.mean([agg[t]["nrmse"] for t in targets]))


def run(names, aug, threads, device="cpu", folds=5):
    global DEV
    torch.set_num_threads(threads)
    DEV = torch.device(device)
    (df, X, Y, G, M), XN = aligned_data()
    times = df.time.to_numpy()
    fold_idx = group_folds(X, Y, G, folds)
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in names:
        fn, desc = SPECS[name]
        t0 = time.time()
        res = {}
        for fold, (tr, te) in enumerate(fold_idx):
            assert not set(G[tr]) & set(G[te])
            xt, yt, mt = X[tr], Y[tr], M[tr]
            if aug:
                xa = corrupt(X[tr], G[tr], times[tr], X[tr].std(axis=0), NOISE, DRIFT, AUG_SEED + fold)
                xt, yt, mt = np.concatenate([xt, xa]), np.tile(yt, (2, 1)), np.tile(mt, (2, 1))
            variants = fn(xt, yt, mt, fold)
            lim_row = X[te][Y[te][:, J["is_limited"]] > 0.5][:1]          # worst case for gating: both nets run
            for v, pred in variants.items():
                r = res.setdefault(v, {"clean": [], "noisy": []})
                r["clean"].append(score(pred(X[te]), Y[te], M[te]))
                r["noisy"].append(score(pred(XN[te]), Y[te], M[te]))
                if fold == 0:
                    r["latency_ms"] = time_predict(pred, lim_row)
            print(f"{name}{'+aug' if aug else ''} fold {fold + 1}/{folds}  {time.time() - t0:.0f} s", flush=True)
        for v, r in res.items():
            key = f"{name}{' / ' + v if v else ''}"
            clean, noisy = fold_aggregate(r["clean"]), fold_aggregate(r["noisy"])
            rec = {"config": key, "base_config": name, "variant": v, "description": desc, "training": "aug" if aug else "plain",
                   "clean": clean, "noisy": noisy, "latency_ms": r["latency_ms"],
                   "summary_nrmse_clean": summary(clean, SUMMARY_T), "summary_nrmse_noisy": summary(noisy, SUMMARY_T),
                   "summary13_nrmse_clean": summary(clean, SUMMARY_T13), "summary13_nrmse_noisy": summary(noisy, SUMMARY_T13),
                   "train_seconds": time.time() - t0}
            fname = f"{key.replace(' / ', '__').replace(' ', '_')}__{rec['training']}.json"
            (CACHE / fname).write_text(json.dumps(rec, indent=1))
            print(f"  {key} [{rec['training']}] summary nRMSE clean {rec['summary_nrmse_clean']:.4f} noisy {rec['summary_nrmse_noisy']:.4f} | "
                  f"R_lim {clean['R_limiter']['mae']:.2f} Z_lim {clean['Z_limiter']['mae']:.2f} R_mag {clean['R_mag_axis']['mae']:.3f} mm | "
                  f"latency {rec['latency_ms']:.4f} ms", flush=True)


def latency_check(names, threads=1):
    """Latency of every variant of the named configurations: one fold, one-epoch networks (the weights do not change the
    timing; the LightGBM trees are real), median of 3000 end-to-end predictions of one limited sample, ms."""
    global FAST
    FAST = True
    torch.set_num_threads(threads)
    (df, X, Y, G, M), _ = aligned_data()
    tr, te = group_folds(X, Y, G)[0]
    x1 = X[te][Y[te][:, J["is_limited"]] > 0.5][:1]
    out = {}
    for name in names:
        for v, pred in SPECS[name][0](X[tr], Y[tr], M[tr], 0).items():
            key = f"{name}{' / ' + v if v else ''}"
            out[key] = time_predict(pred, x1, reps=3000, rounds=5)
            print(f"{key}: {out[key]:.4f} ms (torch threads {threads})", flush=True)
    path = OUT / "ipp1-improve-latency.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update(out)
    path.write_text(json.dumps(old, indent=1))


# ----------------------------------------------------------------------------- report
def report():
    recs = [json.loads(p.read_text()) for p in sorted(CACHE.glob("*.json"))]
    if not recs:
        sys.exit("nothing cached; run --run first")
    for r in recs:      # mean nRMSE over all 16 targets: the limiter point counts, so a limiter specialist shows up in the ranking
        for cond in ("clean", "noisy"):
            r["all16_nrmse_" + cond] = summary(r[cond], TARGETS)
    base = next(r for r in recs if r["config"] == "base" and r["training"] == "plain")
    base_aug = next((r for r in recs if r["config"] == "base" and r["training"] == "aug"), None)
    LAT = 0.2   # ms per sample: "far below 1 ms" taken as at most 0.2 ms

    def row(r, cond):
        c = r[cond]
        return (f"| {r['config']} | {r['training']} | {r['summary_nrmse_' + cond]:.4f} | {r['all16_nrmse_' + cond]:.4f} | {c['R_limiter']['mae']:.2f} | "
                f"{c['Z_limiter']['mae']:.2f} | {c['R_mag_axis']['mae']:.3f} | {c['Z_mag_axis']['mae']:.3f} | {r['latency_ms']:.4f} |")

    head = ("| configuration | training | summary nRMSE | all-16 nRMSE | R_limiter MAE mm | Z_limiter MAE mm | R_mag_axis MAE mm | "
            "Z_mag_axis MAE mm | latency ms/sample |\n|---|---|---:|---:|---:|---:|---:|---:|---:|")
    order = lambda cond: sorted(recs, key=lambda r: (r["training"], r["all16_nrmse_" + cond]))
    ok = [r for r in recs if r["latency_ms"] <= LAT]
    best = {}
    for tr in ("plain", "aug"):
        sub = [r for r in ok if r["training"] == tr]
        if sub:
            best[tr] = {"by_clean": min(sub, key=lambda r: r["all16_nrmse_clean"]),
                        "by_noisy": min(sub, key=lambda r: r["all16_nrmse_noisy"])}

    def pct(a, b):
        return f"{(a / b - 1) * 100:+.0f} %"

    def compare(r, ref, cond):
        lines = ["| target | unit | baseline MAE | this MAE | change | baseline nRMSE | this nRMSE | folds better (of 5) |",
                 "|---|---|---:|---:|---:|---:|---:|---:|"]
        for t in TARGETS:
            a, b = ref[cond][t], r[cond][t]
            better = sum(x < y for x, y in zip(b["fold_mae"], a["fold_mae"]))
            lines.append(f"| {t} | {a['unit']} | {a['mae']:.4g} | {b['mae']:.4g} | {pct(b['mae'], a['mae'])} | "
                         f"{a['nrmse']:.4f} | {b['nrmse']:.4f} | {better} |")
        return lines

    md = ["# IPP 1: improving the model (same protocol as the baseline)", "",
          "5-fold GroupKFold by whole discharge, masked loss, `ipp1_common.score`, at least 60 epochs. Every number is the mean of the "
          "5 held-out folds. `summary nRMSE` = mean nRMSE over the 14 targets without the limiter point (all targets except R_limiter and "
          "Z_limiter, is_limited included); the json also has the 13-target mean without is_limited. `all-16 nRMSE` adds the two limiter targets (mean over all 16); tables are sorted by it. Latency = end-to-end `predict` of one raw "
          "sample (features, standardisation, forward pass, de-standardisation), median in ms, measured on a shared, loaded machine "
          f"(use it for ranking, not as a guarantee); gated rows are timed on a limited sample, i.e. both models run. Latency limit used for the "
          f"recommendation: {LAT} ms.", "",
          "`plain` = trained on the clean training discharges. `aug` = trained on the clean rows plus one corrupted copy "
          "(noise 0.15, drift 0.15 of the training input SD, the augmentation of `ipp1_robustness.py`), same number of epochs over twice the rows. "
          "Both are tested on the clean file and on the provided noisy file (same held-out discharges).", "",
          "## Held-out clean data", "", head] + [row(r, "clean") for r in order("clean")]
    md += ["", "## Held-out provided noisy data", "", head] + [row(r, "noisy") for r in order("noisy")]
    md += ["", "## Recommendation (latency within the limit, ranked by the all-16 nRMSE)", ""]
    for tr, label in (("plain", "trained on clean data"), ("aug", "trained with noise plus drift augmentation")):
        if tr in best:
            for by, cond in (("by_clean", "clean"), ("by_noisy", "noisy")):
                r = best[tr][by]
                md.append(f"- {label}, best on {cond} test: **{r['config']}** ({r['description']}); summary nRMSE clean {r['summary_nrmse_clean']:.4f}, "
                          f"noisy {r['summary_nrmse_noisy']:.4f} (all-16 clean {r['all16_nrmse_clean']:.4f}, noisy {r['all16_nrmse_noisy']:.4f}), latency {r['latency_ms']:.4f} ms.")
    for tr, ref, lab in (("plain", base, "plain"), ("aug", base_aug, "aug")):
        if tr in best and ref is not None:
            r = best[tr]["by_clean"]
            md += ["", f"## Per-target: {r['config']} ({lab}) against the baseline recipe ({lab}), clean test", ""] + compare(r, ref, "clean")
            md += ["", f"## Per-target: {r['config']} ({lab}) against the baseline recipe ({lab}), provided noisy test", ""] + compare(r, ref, "noisy")
    notes = OUT / "ipp1-improve-notes.md"          # hand-written findings, kept next to the generated tables
    if notes.exists():
        md = md[:2] + [notes.read_text().strip(), ""] + md[2:]
    (OUT / "ipp1-improve.md").write_text("\n".join(md) + "\n")
    (ROOT / "repo/results").mkdir(parents=True, exist_ok=True)
    (ROOT / "repo/results/ipp1-improve.md").write_text("\n".join(md) + "\n")
    payload = {"protocol": "5-fold GroupKFold by discharge, masked loss, ipp1_common.score, >=60 epochs",
               "latency_limit_ms": LAT, "recommended": {tr: {k: v["config"] for k, v in d.items()} for tr, d in best.items()},
               "records": recs}
    (OUT / "ipp1-improve.json").write_text(json.dumps(payload, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="", help="comma separated configuration names (see SPECS)")
    ap.add_argument("--aug", action="store_true", help="train on clean + one noise/drift corrupted copy")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--device", default="cpu", help="cpu or mps for training")
    ap.add_argument("--latency", default="", help="comma separated configuration names: time them only")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, (_, d) in SPECS.items():
            print(f"{k:12s} {d}")
    if a.run:
        run([n for n in a.run.split(",") if n], a.aug, a.threads, a.device)
    if a.latency:
        latency_check([n for n in a.latency.split(",") if n], a.threads)
    if a.report:
        report()
