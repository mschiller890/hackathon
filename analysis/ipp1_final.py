#!/usr/bin/env python
"""IPP task 1: the honest final evaluation of the shape model.

Protocol
  * Locked test: 30 discharges drawn with numpy seed 20261024 (ids in results/ipp1-locked-test-ids.txt). The other 119
    discharges are the development set. Recipe choices use 5-fold GroupKFold INSIDE the development set only; the locked
    set is scored once, by --report, with models trained on all development discharges.
  * Recipes (all trained on whole discharges, masked loss, one seed):
      base      the baseline MLP of ipp1_common.fit_mlp (60 epochs), trained on clean rows
      base_aug  the same trained on clean rows plus one corrupted copy (extra: the fair baseline for noisy inputs)
      cand      final candidate = general network on 24 inputs + 22 neighbouring-coil differences (Huber 0.5, 150 epochs)
                + ridge for plasma_current + a network trained only on limited rows (150 epochs) that answers R_limiter and
                Z_limiter when the general network predicts is_limited > 0.5 (recipe "combo_long" of ipp1_improve.py)
      cand_aug  the same, trained on clean rows plus one corrupted copy (noise 0.15, drift 0.15 of each input's SD),
                75 epochs on twice the rows
  * Every recipe is tested on the clean inputs and on the provided noisy inputs (same rows of equil_data_noisy.csv).
  * Metrics are pooled over all test rows (not means of folds): MAE, median, RMSE, p95, p99, max, nRMSE, R2.

Jobs (each trains one model and caches its predictions in out/ipp1-final-cache/, never in the repository):
    python -I analysis/ipp1_final.py --job cv:cand:0        # development fold 0 of recipe cand
    python -I analysis/ipp1_final.py --job locked:cand      # all development discharges -> locked discharges
    python -I analysis/ipp1_final.py --job blocked:cand     # lower half of the development ids -> upper half
    python -I analysis/ipp1_final.py --report               # assemble out/ipp1-final.json/.md and results/ipp1-final.md
"""
import argparse
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, REPO, TARGETS, UNIT, fit_mlp, group_folds, load

SMOKE = bool(os.environ.get("IPP1_FINAL_SMOKE"))          # one epoch per network: only to test the plumbing
CACHE = OUT / ("ipp1-final-cache-smoke" if SMOKE else "ipp1-final-cache")
J = {t: i for i, t in enumerate(TARGETS)}
LIMITER = [J["R_limiter"], J["Z_limiter"]]
NOISE, DRIFT, AUG_SEED = 0.15, 0.15, 20261023             # as ipp1_robustness.py and ipp1_improve.py
LOCK_SEED, N_LOCK, N_BOOT = 20261024, 30, 1000
RECIPES = ["base", "base_aug", "cand", "cand_aug"]
HEADLINE = ["plasma_current", "R_mag_axis", "Z_mag_axis", "R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1",
            "R_strike_point_2", "Z_strike_point_2", "R_limiter", "Z_limiter"]


# ----------------------------------------------------------------------------- data and split
def aligned_data():
    clean, noisy = load(), load(noisy=True)
    if not (np.array_equal(clean[0].discharge, noisy[0].discharge) and np.allclose(clean[0].time, noisy[0].time, rtol=0, atol=1e-9)):
        raise ValueError("clean and noisy rows are not aligned")
    if not np.array_equal(clean[2], noisy[2], equal_nan=True):
        raise ValueError("clean and noisy targets differ")
    return clean, noisy[1]


def locked_ids(groups):
    ids = np.unique(groups)
    return np.sort(np.random.RandomState(LOCK_SEED).choice(ids, N_LOCK, replace=False))


def split(G):
    lock = locked_ids(G)
    is_lock = np.isin(G, lock)
    dev_idx, lock_idx = np.where(~is_lock)[0], np.where(is_lock)[0]
    return lock, dev_idx, lock_idx


# ----------------------------------------------------------------------------- network code (copied from ipp1_improve.py)
def corrupt(x, groups, times, scale, noise, drift, seed):
    """Row noise plus an independent Gaussian slope per discharge and coil (as ipp1_robustness.corrupt)."""
    rng = np.random.default_rng(seed)
    _, inverse = np.unique(groups, return_inverse=True)
    slopes = rng.normal(size=(inverse.max() + 1, x.shape[1])) * drift * scale
    return (x + rng.normal(size=x.shape) * noise * scale + slopes[inverse] * times[:, None]).astype(np.float32)


def feats(x):
    """The 24 inputs plus differences of neighbouring coils IPR01..16 (15) and loops FL01..08 (7)."""
    return np.concatenate([x, np.diff(x[:, :16], axis=1), np.diff(x[:, 16:24], axis=1)], 1).astype(np.float32)


class MLP(nn.Module):
    def __init__(self, n_in, n_out, widths):
        super().__init__()
        layers, d = [], n_in
        for w in widths:
            layers += [nn.Linear(d, w), nn.SiLU()]
            d = w
        layers.append(nn.Linear(d, n_out))
        self.f = nn.Sequential(*layers)

    def forward(self, x):
        return self.f(x)


def fit_net(xtr, ytr, mtr, seed, epochs, rows=None, arch=(256, 256, 128), wd=1e-4, delta=0.5, lr=2e-3, max_lr=3e-3, batch=512):
    """Standardised inputs and targets, Huber loss masked to the targets that exist, AdamW, OneCycle."""
    if rows is not None:
        xtr, ytr, mtr = xtr[rows], ytr[rows], mtr[rows]
    epochs = 1 if SMOKE else epochs
    torch.manual_seed(seed)
    ftr = feats(xtr)
    mu, sd = ftr.mean(0), ftr.std(0) + 1e-9
    with warnings.catch_warnings():  # an all-NaN column (divertor targets on limited rows) gives NaN, masked out of the loss
        warnings.filterwarnings("ignore", "Mean of empty slice|Degrees of freedom", RuntimeWarning)
        ym, ys = np.nanmean(ytr, 0), np.nanstd(ytr, 0) + 1e-9
    xt = torch.tensor((ftr - mu) / sd)
    yt = torch.tensor(np.nan_to_num((ytr - ym) / ys))
    mt = torch.tensor(mtr.astype(np.float32))
    net = MLP(xt.shape[1], yt.shape[1], arch)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=wd)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=max_lr, total_steps=epochs * ((len(xt) + batch - 1) // batch))
    for _ in range(epochs):
        perm = torch.randperm(len(xt))
        for i in range(0, len(xt), batch):
            b = perm[i:i + batch]
            e = 2 * F.huber_loss(net(xt[b]), yt[b], reduction="none", delta=delta)
            loss = (e * mt[b]).sum() / mt[b].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
    net.eval()
    mu32, sd32 = mu.astype(np.float32), sd.astype(np.float32)

    def predict(x):
        with torch.inference_mode():
            return net(torch.from_numpy((feats(x) - mu32) / sd32)).numpy() * ys + ym
    return predict



def fit_ridge_col(xtr, ytr, mtr, j, alpha=1.0):
    """Ridge for ONE target on standardised raw inputs (the ridge of ipp1_common.fit_ridge), folded into raw coefficients."""
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


def gate(general, special, cols):
    """The specialist answers `cols` on rows where the general net predicts is_limited > 0.5; the general net answers elsewhere."""
    cols = list(cols)

    def predict(x):
        p = general(x).copy()
        g = p[:, J["is_limited"]] > 0.5
        if g.any():
            p[np.ix_(g, cols)] = special(x[g])[:, cols]
        return p
    return predict


def train(recipe, xt, yt, mt, g, times, seed, aug_seed):
    """Train one recipe on the given rows (clean); the *_aug recipes add one corrupted copy of the rows."""
    aug = recipe.endswith("_aug")
    if aug:
        xa = corrupt(xt, g, times, xt.std(axis=0), NOISE, DRIFT, aug_seed)
        xt, yt, mt = np.concatenate([xt, xa]), np.tile(yt, (2, 1)), np.tile(mt, (2, 1))
    if recipe.startswith("base"):
        return fit_mlp(xt, yt, mt, 1 if SMOKE else 60, seed=seed)[0]
    epochs = 75 if aug else 150
    gen = fit_net(xt, yt, mt, seed, epochs)
    spec = fit_net(xt, yt, mt, seed, epochs, rows=yt[:, J["is_limited"]] > 0.5)
    gen_ip = override(gen, J["plasma_current"], fit_ridge_col(xt, yt, mt, J["plasma_current"]))
    return gate(gen_ip, spec, LIMITER)


# ----------------------------------------------------------------------------- jobs
def job(spec, threads):
    torch.set_num_threads(threads)
    (df, X, Y, G, M), XN = aligned_data()
    times = df.time.to_numpy()
    lock, dev_idx, lock_idx = split(G)
    kind, recipe, *rest = spec.split(":")
    assert recipe in RECIPES
    if kind == "cv":                    # fold k of 5-fold GroupKFold inside the development set
        k = int(rest[0])
        tr_l, te_l = group_folds(X[dev_idx], Y[dev_idx], G[dev_idx], 5)[k]
        tr, te, seed, aug_seed, name = dev_idx[tr_l], dev_idx[te_l], k, AUG_SEED + k, f"cv_{recipe}_{k}"
    elif kind == "locked":              # all development discharges -> the locked discharges (scored only by --report)
        tr, te, seed, aug_seed, name = dev_idx, lock_idx, 0, AUG_SEED + 50, f"locked_{recipe}"
    elif kind == "blocked":             # lower half of the development ids -> upper half
        ids = np.unique(G[dev_idx])
        low = ids[:len(ids) - len(ids) // 2]
        tr, te = dev_idx[np.isin(G[dev_idx], low)], dev_idx[~np.isin(G[dev_idx], low)]
        seed, aug_seed, name = 0, AUG_SEED + 60, f"blocked_{recipe}"
    else:
        raise ValueError(spec)
    assert not set(G[tr]) & set(G[te])
    if kind != "locked":
        assert not set(G[te]) & set(lock)
    CACHE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pred = train(recipe, X[tr], Y[tr], M[tr], G[tr], times[tr], seed, aug_seed)
    np.savez(CACHE / f"{name}.npz", idx=te, clean=pred(X[te]).astype(np.float32), noisy=pred(XN[te]).astype(np.float32))
    print(f"{name}: train {len(tr)} rows / {len(np.unique(G[tr]))} discharges, test {len(te)} rows / {len(np.unique(G[te]))} discharges, "
          f"{time.time() - t0:.0f} s", flush=True)


# ----------------------------------------------------------------------------- metrics
def tstats(p, y, m):
    """Pooled per-target statistics in report units over the rows of p/y/m."""
    out = {}
    for j, t in enumerate(TARGETS):
        k = m[:, j]
        if k.sum() < 2:
            out[t] = None
            continue
        scale, unit = UNIT[t]
        e = (p[k, j] - y[k, j]).astype(np.float64)
        a = np.abs(e) * scale
        sd = y[k, j].astype(np.float64).std()
        sst = ((y[k, j] - y[k, j].mean()) ** 2).sum()
        d = {"n": int(k.sum()), "unit": unit, "mae": a.mean(), "median": np.median(a), "rmse": np.sqrt((e ** 2).mean()) * scale,
             "p95": np.percentile(a, 95), "p99": np.percentile(a, 99), "max": a.max(),
             "nrmse": np.sqrt((e ** 2).mean()) / sd if sd > 0 else None, "r2": 1 - (e ** 2).sum() / sst if sst > 0 else None}
        if t == "is_limited":
            d["accuracy"] = float(((p[k, j] > 0.5) == (y[k, j] > 0.5)).mean())
        out[t] = {kk: (float(v) if isinstance(v, (float, np.floating)) else v) for kk, v in d.items()}
    return out


def all16(stats):
    """Mean pooled nRMSE over the 16 targets: the ranking number used for recipe choices."""
    return float(np.mean([stats[t]["nrmse"] for t in TARGETS]))


def bootstrap(P, Y, M, disc, targets, seed=LOCK_SEED + 1):
    """Cluster bootstrap by discharge. P: {name: predictions}. Returns per recipe and target the pooled MAE and RMSE
    with 95 % percentile intervals, and for every recipe but the first the MAE ratio against the first (paired)."""
    ids = np.unique(disc)
    inv = np.searchsorted(ids, disc)
    rng = np.random.RandomState(seed)
    counts = np.stack([np.bincount(rng.randint(0, len(ids), len(ids)), minlength=len(ids)) for _ in range(N_BOOT)]).astype(np.float64)
    names = list(P)
    res = {n: {} for n in names}
    sums = {}
    for n in names:
        for t in targets:
            j = J[t]
            k = M[:, j]
            e = (P[n][:, j] - Y[:, j]).astype(np.float64)
            e = np.where(k, e, 0.0)
            sa = np.bincount(inv, weights=np.abs(e), minlength=len(ids))
            sq = np.bincount(inv, weights=e ** 2, minlength=len(ids))
            ct = np.bincount(inv, weights=k.astype(float), minlength=len(ids))
            sums[(n, t)] = (sa, sq, ct)
    ci = lambda v: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
    for n in names:
        for t in targets:
            sa, sq, ct = sums[(n, t)]
            scale = UNIT[t][0]
            c = counts @ ct
            with np.errstate(invalid="ignore", divide="ignore"):
                mae = (counts @ sa) / c * scale
                rmse = np.sqrt((counts @ sq) / c) * scale
            res[n][t] = {"mae": float(sa.sum() / ct.sum() * scale), "mae_ci": ci(mae),
                         "rmse": float(np.sqrt(sq.sum() / ct.sum()) * scale), "rmse_ci": ci(rmse)}
    for n in names[1:]:
        for t in targets:
            a, b = sums[(n, t)], sums[(names[0], t)]
            with np.errstate(invalid="ignore", divide="ignore"):
                r = ((counts @ a[0]) / (counts @ a[2])) / ((counts @ b[0]) / (counts @ b[2]))
            res[n][t]["mae_ratio_vs_" + names[0]] = float(a[0].sum() / a[2].sum() / (b[0].sum() / b[2].sum()))
            res[n][t]["mae_ratio_ci"] = ci(r)
    return res


# ----------------------------------------------------------------------------- report
def assemble(prefix, n_rows, recipes, n_folds=None):
    """Load the cached predictions of one stage into arrays aligned on the rows stored in the cache (clean, noisy, idx)."""
    out = {}
    for r in recipes:
        files = [CACHE / f"{prefix}_{r}.npz"] if n_folds is None else [CACHE / f"{prefix}_{r}_{k}.npz" for k in range(n_folds)]
        if not all(f.exists() for f in files):
            continue
        parts = [np.load(f) for f in files]
        idx = np.concatenate([p["idx"] for p in parts])
        o = np.argsort(idx)
        out[r] = {"idx": idx[o], "clean": np.concatenate([p["clean"] for p in parts])[o], "noisy": np.concatenate([p["noisy"] for p in parts])[o]}
    return out


def fmt(v, d=3):
    return "n/a" if v is None else f"{v:.{d}g}"


def report():
    (df, X, Y, G, M), XN = aligned_data()
    times = df.time.to_numpy()
    lock, dev_idx, lock_idx = split(G)
    ids_txt = REPO / "results/ipp1-locked-test-ids.txt"
    ids_txt.parent.mkdir(parents=True, exist_ok=True)
    dev_ids = np.unique(G[dev_idx])
    ids_txt.write_text(
        f"Locked test set of IPP 1 (hackathon task 1): {N_LOCK} of {len(np.unique(G))} discharges.\n"
        f"Drawn with numpy.random.RandomState({LOCK_SEED}).choice(sorted unique discharge ids, {N_LOCK}, replace=False), then sorted.\n"
        f"The other {len(dev_ids)} discharges are the development set; every recipe choice uses 5-fold GroupKFold inside it.\n"
        f"The locked discharges are scored once, by models trained on all development discharges (analysis/ipp1_final.py --report).\n\n"
        f"locked discharge ids ({len(lock)}): {' '.join(str(i) for i in lock)}\n")
    R = {"protocol": {"locked_seed": LOCK_SEED, "locked_ids": [int(i) for i in lock], "n_dev_discharges": int(len(dev_ids)),
                      "n_dev_rows": int(len(dev_idx)), "n_locked_rows": int(len(lock_idx)), "bootstrap": N_BOOT, "seed": "one per model"}}

    # ---- development: pooled out-of-fold scores, the basis of every recipe choice
    cv = assemble("cv", None, RECIPES, 5)
    dev = {}
    for r, d in cv.items():
        if len(d["idx"]) != len(dev_idx):
            continue
        dev[r] = {c: tstats(d[c], Y[d["idx"]], M[d["idx"]]) for c in ("clean", "noisy")}
        dev[r]["all16_clean"], dev[r]["all16_noisy"] = all16(dev[r]["clean"]), all16(dev[r]["noisy"])
    R["development_cv"] = dev
    choice = {}
    for c in ("clean", "noisy"):
        if dev:
            choice[c] = min(dev, key=lambda r: dev[r]["all16_" + c])
    R["choice"] = choice

    # ---- locked test
    lk = assemble("locked", None, RECIPES)
    lk = {r: d for r, d in lk.items() if np.array_equal(d["idx"], lock_idx)}
    names = [r for r in RECIPES if r in lk]
    yl, ml, gl = Y[lock_idx], M[lock_idx], G[lock_idx]
    locked = {r: {c: tstats(lk[r][c], yl, ml) for c in ("clean", "noisy")} for r in names}
    for r in names:
        locked[r]["all16_clean"], locked[r]["all16_noisy"] = all16(locked[r]["clean"]), all16(locked[r]["noisy"])
    R["locked"] = locked
    boot = {c: bootstrap({r: lk[r][c] for r in names}, yl, ml, gl, HEADLINE) for c in ("clean", "noisy")} if names else {}
    R["bootstrap"] = boot

    # ---- breakdowns of the locked set
    sign = np.sign(np.array([np.nanmedian(Y[lock_idx][gl == g, 0]) for g in gl]))
    rel = times[lock_idx]
    conf = Y[lock_idx][:, J["is_limited"]] > 0.5
    groups = {"polarity": {"negative plasma current": sign < 0, "positive plasma current": sign > 0},
              "relative time": {"first 2 %": rel <= 0.02, "middle": (rel > 0.02) & (rel < 0.98), "last 2 %": rel >= 0.98},
              "configuration": {"divertor": ~conf, "limited": conf}}
    R["polarity_discharges"] = {"positive": int(len(np.unique(gl[sign > 0]))), "negative": int(len(np.unique(gl[sign < 0])))}
    brk = {}
    for gname, cells in groups.items():
        for cname, sel in cells.items():
            brk[f"{gname}: {cname}"] = {"rows": int(sel.sum()), "discharges": int(len(np.unique(gl[sel]))),
                                        **{r: {c: tstats(lk[r][c][sel], yl[sel], ml[sel]) for c in ("clean", "noisy")} for r in names}}
    R["breakdown"] = brk

    # ---- blocked by id (development set only) against the random group folds
    bl = assemble("blocked", None, RECIPES)
    blocked = {}
    if bl:
        ids = np.unique(G[dev_idx])
        upper = ids[len(ids) - len(ids) // 2:]
        for r, d in bl.items():
            up_idx = d["idx"]
            row = {"train_discharges": int(len(ids) - len(upper)), "test_discharges": int(len(upper)), "test_rows": int(len(up_idx))}
            row["blocked"] = {c: tstats(d[c], Y[up_idx], M[up_idx]) for c in ("clean", "noisy")}
            if r in cv and len(cv[r]["idx"]) == len(dev_idx):
                sel = np.isin(cv[r]["idx"], up_idx)
                row["random_folds_same_discharges"] = {c: tstats(cv[r][c][sel], Y[cv[r]["idx"][sel]], M[cv[r]["idx"][sel]]) for c in ("clean", "noisy")}
                row["random_folds_all_dev"] = dev[r]
            blocked[r] = row
    R["blocked"] = blocked

    (OUT / "ipp1-final.json").write_text(json.dumps(R, indent=1))
    md = render(R, names)
    notes = OUT / "ipp1-final-notes.md"
    if notes.exists():
        md = md.replace("\n## Development set", "\n" + notes.read_text().strip() + "\n\n## Development set", 1)
    (OUT / "ipp1-final.md").write_text(md)
    (REPO / "results").mkdir(parents=True, exist_ok=True)
    (REPO / "results/ipp1-final.md").write_text(md)
    print(md)


LABEL = {"base": "baseline MLP", "base_aug": "baseline MLP, augmented (extra)", "cand": "candidate, plain", "cand_aug": "candidate, augmented"}


def render(R, names):
    L = []
    P = R["protocol"]
    L += ["# IPP 1: final evaluation on a locked test set", "",
          f"Locked test set: {N_LOCK} discharges ({P['n_locked_rows']} rows) drawn with numpy seed {LOCK_SEED}; ids in `results/ipp1-locked-test-ids.txt`. "
          f"Development set: the other {P['n_dev_discharges']} discharges ({P['n_dev_rows']} rows). Recipe choices use 5-fold GroupKFold inside the "
          "development set only; the locked set was scored once, with models trained on all development discharges. All metrics are pooled over "
          "the rows of the test set (not means of folds). Every model is one seed (seed noise of earlier runs: 8 to 19 %), so read differences "
          "below about 20 % between recipes as unresolved unless the bootstrap interval excludes 1.", "",
          "Recipes: `baseline MLP` = ipp1_common.fit_mlp, 60 epochs. `candidate` = network on 24 inputs + 22 neighbouring-coil differences "
          "(Huber 0.5, 150 epochs) + ridge for plasma_current + a limited-rows network for R_limiter and Z_limiter gated by the predicted is_limited. "
          "`augmented` = trained on the clean rows plus one copy with noise 0.15 and drift 0.15 of each input's SD (candidate: 75 epochs on twice the rows; "
          "baseline: 60 epochs on twice the rows, an extra control). `clean` = clean inputs, `noisy` = the provided noisy file (same rows).", ""]
    if R["choice"]:
        L += ["## Which recipe to ship", ""]
        d = R["development_cv"]
        for c in ("clean", "noisy"):
            r = R["choice"][c]
            parts = ", ".join(f"{LABEL[x]} {d[x]['all16_' + c]:.4f}" for x in d)
            L.append(f"- **{c} inputs: {LABEL[r]}** (`{r}`): lowest mean nRMSE over the 16 targets in the development cross-validation "
                     f"({parts}).")
        if names:
            L.append("- Locked-set check of that choice: mean nRMSE over 16 targets, " + "; ".join(
                f"{c}: " + ", ".join(f"{LABEL[r]} {R['locked'][r]['all16_' + c]:.4f}" for r in names) for c in ("clean", "noisy")) + ".")
        L.append("")
    L += ["## Development set: pooled out-of-fold scores (5 group folds inside the 119 development discharges)", ""]
    d = R["development_cv"]
    if d:
        L += ["| recipe | inputs | mean nRMSE (16) | " + " | ".join(f"{t} MAE" for t in HEADLINE) + " |", "|---|---|---:|" + "---:|" * len(HEADLINE)]
        for r in d:
            for c in ("clean", "noisy"):
                L.append(f"| {LABEL[r]} | {c} | {d[r]['all16_' + c]:.4f} | " + " | ".join(fmt(d[r][c][t]["mae"]) for t in HEADLINE) + " |")
        L.append("")
        L.append("Units: mm for R and Z targets, kA for plasma_current.")
        L.append("")
    if not names:
        L += ["## Locked test", "", "No locked predictions cached yet.", ""]
        return "\n".join(L) + "\n"
    for c in ("clean", "noisy"):
        L += [f"## Locked test, {c} inputs: all metrics per target, pooled over {P['n_locked_rows']} rows", ""]
        for r in names:
            s = R["locked"][r][c]
            L += [f"### {LABEL[r]}, {c} inputs (mean nRMSE over 16 targets {R['locked'][r]['all16_' + c]:.4f})", "",
                  "| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
            for t in TARGETS:
                x = s[t]
                L.append(f"| {t} | {x['unit']} | {x['n']} | " + " | ".join(fmt(x[k]) for k in ("mae", "median", "rmse", "p95", "p99", "max", "nrmse", "r2")) + " |")
            L += ["", f"is_limited accuracy: {s['is_limited']['accuracy']:.4f}", ""]
    for c in ("clean", "noisy"):
        L += [f"## Locked test, {c} inputs: cluster bootstrap by discharge ({N_BOOT} resamples, 95 % intervals)", "",
              "MAE and RMSE with intervals; ratio = MAE of the recipe over MAE of the baseline MLP on the same resamples (below 1 means better).", ""]
        b = R["bootstrap"][c]
        L += ["| target | unit | " + " | ".join(f"{LABEL[r]} MAE [95 %]" for r in names) + " | " + " | ".join(f"MAE ratio {r}/{names[0]} [95 %]" for r in names[1:]) + " |",
              "|---|---|" + "---:|" * (2 * len(names) - 1)]
        for t in HEADLINE:
            cells = [f"{fmt(b[r][t]['mae'])} [{fmt(b[r][t]['mae_ci'][0])}, {fmt(b[r][t]['mae_ci'][1])}]" for r in names]
            ratios = [f"{b[r][t]['mae_ratio_vs_' + names[0]]:.2f} [{b[r][t]['mae_ratio_ci'][0]:.2f}, {b[r][t]['mae_ratio_ci'][1]:.2f}]" for r in names[1:]]
            L.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(cells) + " | " + " | ".join(ratios) + " |")
        L += ["", "RMSE with intervals:", "", "| target | unit | " + " | ".join(f"{LABEL[r]} RMSE [95 %]" for r in names) + " |", "|---|---|" + "---:|" * len(names)]
        for t in HEADLINE:
            L.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(f"{fmt(b[r][t]['rmse'])} [{fmt(b[r][t]['rmse_ci'][0])}, {fmt(b[r][t]['rmse_ci'][1])}]" for r in names) + " |")
        L.append("")
    pol = R["polarity_discharges"]
    L += ["## Locked test: breakdowns (MAE per headline target; p95 is in the json)", "",
          f"Polarity is the sign of the plasma current of the discharge: {pol['negative']} negative and {pol['positive']} positive locked discharges. "
          "Relative time is the row's time scaled to 0..1 within its discharge. Configuration is the true is_limited. n = rows.", ""]
    for key, cell in R["breakdown"].items():
        L += [f"### {key} ({cell['rows']} rows, {cell['discharges']} discharges)", "",
              "| target | unit | " + " | ".join(f"{LABEL[r]} {c}" for c in ("clean", "noisy") for r in names) + " |", "|---|---|" + "---:|" * (2 * len(names))]
        for t in HEADLINE:
            vals = []
            for c in ("clean", "noisy"):
                for r in names:
                    x = cell[r][c][t]
                    vals.append("n/a" if x is None else fmt(x["mae"]) + (f" (n={x['n']})" if x["n"] < 100 else ""))
            L.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(vals) + " |")
        L.append("")
    if R["blocked"]:
        L += ["## Blocked-by-id split against random group folds (development set only)", "",
              "Train on the lower half of the development discharge ids, test on the upper half. Discharge ids are chronological, so this is a test on later "
              "campaigns. The random-fold numbers are the pooled out-of-fold errors of the SAME recipe on the SAME upper-half discharges, and on all "
              "development discharges. Caveat: the blocked model trains on about 60 discharges, the random folds on about 95, so part of the gap is the "
              "smaller training set, not only the drift between campaigns.", ""]
        for r, row in R["blocked"].items():
            L += [f"### {LABEL[r]} ({row['train_discharges']} training, {row['test_discharges']} test discharges, {row['test_rows']} test rows)", "",
                  "| target | unit | inputs | blocked MAE | random folds, same discharges MAE | ratio | random folds, all development MAE |", "|---|---|---|---:|---:|---:|---:|"]
            for t in HEADLINE:
                for c in ("clean", "noisy"):
                    a = row["blocked"][c][t]["mae"]
                    b = row.get("random_folds_same_discharges", {}).get(c, {}).get(t)
                    e = row.get("random_folds_all_dev", {}).get(c, {}).get(t)
                    L.append(f"| {t} | {UNIT[t][1]} | {c} | {fmt(a)} | {fmt(b['mae']) if b else 'n/a'} | {a / b['mae']:.2f} | {fmt(e['mae']) if e else 'n/a'} |"
                             if b else f"| {t} | {UNIT[t][1]} | {c} | {fmt(a)} | n/a | n/a | n/a |")
            L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job", default="", help="cv:<recipe>:<fold>, locked:<recipe> or blocked:<recipe>")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.job:
        job(a.job, a.threads)
    if a.report:
        report()
