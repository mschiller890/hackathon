#!/usr/bin/env python
"""Does the architecture found by the cloud search beat the shipped recipe `cand`, measured on the 119 development discharges only?

The cloud search (results/cloud-search.md, analysis/cloud_search.py) saw all 149 discharges, so its numbers say nothing about the 30 locked ones.
Here its residual MLP is retrained on the development discharges alone, 5 folds by discharge x 3 seeds, with the masked loss and the inputs of `cand`
(24 inputs + 22 differences of neighbouring coils, standardised; the cloud feature set `diff` is the same).

Configurations (hyperparameters read from results/cloud-search.json):
  resA  the trial with the lowest inner validation objective of the search
  resB  the trial that agrees with most of the winning choices of the choice table (arch, feat, loss, sched, act, width, depth, batch)
Models:
  cand        ipp1_final.py recipe `cand`: general MLP + ridge for plasma_current + limiter network, gated (seed 0 is the cached cross-validation of ipp1_final.py)
  res*_pipe   the same pipeline with the general network and the limiter network replaced by the residual MLP (the question: would we swap the architecture?)
  res*_alone  the residual MLP alone, one network for all 16 targets, as the search measured it (no ridge, no limiter network)

DECISION RULE, fixed before the first result was seen. Relative MAE of a target = pooled out-of-fold MAE / SD of the target over the development rows;
the score of a model in a group of rows = mean of that over the 11 headline targets (plasma_current, R and Z of axis, X point, both strike points, limiter).
Ship `resA_pipe` only if, with the mean over the 3 seeds: (1) its score is at least 5 % below that of `cand` in the group of negative-current discharges AND in
the group of positive-current discharges; (2) its MAE of R_limiter and of Z_limiter is each at least 5 % below that of `cand` (all development rows);
(3) in each of the 3 seeds its score over all development rows is below that of `cand`. Otherwise: do not ship. Only after a ship verdict is `resA_pipe` scored
on the locked 30 discharges, once, and logged in results/ipp1-search-dev.md.

    python -I analysis/ipp1_search_dev.py --job <fold>:<seed>:<cand|resA|resB>      # one training, cached in out/ipp1-search-dev-cache/
    python -I analysis/ipp1_search_dev.py --report                                  # results/ipp1-search-dev.md, out/ipp1-search-dev.json
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import cloud_search_lib as S
import ipp1_final as F
from ipp1_common import OUT, ROOT

REPO = ROOT / "repo"
CACHE = OUT / "ipp1-search-dev-cache"
SEEDS = (0, 1, 2)
# winning value of each choice of the search, from the choice table of results/cloud-search.md (best inner objective per value)
CHOICE_WINNERS = {"arch": "resmlp", "feat": "diff", "loss": "huber", "sched": "cosine", "act": "gelu", "width": 256, "depth": 3, "batch": 512}
HEADLINE = ["plasma_current", "R_mag_axis", "Z_mag_axis", "R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1",
            "R_strike_point_2", "Z_strike_point_2", "R_limiter", "Z_limiter"]
MARGIN = 0.95


def configs():
    runs = json.loads((REPO / "results/cloud-search.json").read_text())["search"]["nn"]
    a = min(runs, key=lambda r: r["best_value"])
    b = max(runs, key=lambda r: (sum(r["best_params"].get(k) == v for k, v in CHOICE_WINNERS.items()), -r["best_value"]))
    return {"resA": a, "resB": b}


def fit_res(xtr, ytr, mtr, hp, seed, rows=None):
    """The residual MLP of the search on the cand inputs; returns predict(raw inputs) -> raw targets."""
    if rows is not None:
        xtr, ytr, mtr = xtr[rows], ytr[rows], mtr[rows]
    ftr = F.feats(xtr)
    mu, sd = ftr.mean(0), ftr.std(0) + 1e-9
    predict, _, _ = S.fit_net(hp["arch"], hp, (ftr - mu) / sd, ytr, mtr, seed)
    return lambda x: predict(((F.feats(x) - mu) / sd).astype(np.float32))


def res_pipeline(xt, yt, mt, hp, seed):
    """General residual network + ridge for plasma_current + residual network on limited rows, gated like `cand`; also the general network alone."""
    gen = fit_res(xt, yt, mt, hp, seed)
    spec = fit_res(xt, yt, mt, hp, seed, rows=yt[:, F.J["is_limited"]] > 0.5)
    ridge = F.override(gen, F.J["plasma_current"], F.fit_ridge_col(xt, yt, mt, F.J["plasma_current"]))
    return F.gate(ridge, spec, F.LIMITER), gen


def job(spec, threads):
    torch.set_num_threads(threads)
    fold, s, recipe = spec.split(":")
    fold, s = int(fold), int(s)
    (df, X, Y, G, M), _ = F.aligned_data()
    times = df.time.to_numpy()
    _, dev_idx, _ = F.split(G)
    tr_l, te_l = F.group_folds(X[dev_idx], Y[dev_idx], G[dev_idx], 5)[fold]
    tr, te = dev_idx[tr_l], dev_idx[te_l]
    assert not set(G[tr]) & set(G[te])
    seed = fold + 10 * s                                   # seed 0 is the seed of the cached cross-validation of ipp1_final.py
    t0 = time.time()
    if recipe == "cand":
        out = {"pipe": F.train("cand", X[tr], Y[tr], M[tr], G[tr], times[tr], seed, 0)(X[te])}
    else:
        pipe, gen = res_pipeline(X[tr], Y[tr], M[tr], configs()[recipe]["best_params"], seed)
        out = {"pipe": pipe(X[te]), "alone": gen(X[te])}
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE / f"{recipe}_{fold}_{s}.npz", idx=te, **{k: v.astype(np.float32) for k, v in out.items()})
    print(f"{recipe} fold {fold} seed {s}: {time.time() - t0:.0f} s", flush=True)


# ----------------------------------------------------------------------------- report
def load_predictions(dev_idx):
    """{model: {seed: predictions for dev_idx rows (n_dev x 16)}} from the caches; cand seed 0 is the cached cross-validation of ipp1_final.py."""
    pos = {int(i): k for k, i in enumerate(dev_idx)}
    out = {}
    for model, recipe, kind in (("cand", "cand", "pipe"), ("resA_pipe", "resA", "pipe"), ("resA_alone", "resA", "alone"),
                                ("resB_pipe", "resB", "pipe"), ("resB_alone", "resB", "alone")):
        for s in SEEDS:
            P = np.full((len(dev_idx), len(F.TARGETS)), np.nan, dtype=np.float32)
            for fold in range(5):
                f = F.CACHE / f"cv_cand_{fold}.npz" if (recipe == "cand" and s == 0) else CACHE / f"{recipe}_{fold}_{s}.npz"
                if not f.exists():
                    break
                d = np.load(f)
                P[[pos[int(i)] for i in d["idx"]]] = d["clean"] if "clean" in d else d[kind]
            else:
                out.setdefault(model, {})[s] = P
    return out


def report():
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, _ = F.split(G)
    P = load_predictions(dev_idx)
    complete = {m: v for m, v in P.items() if len(v) == len(SEEDS)}
    assert "cand" in complete and "resA_pipe" in complete, f"missing cached predictions: {[m for m in P if len(P[m]) < len(SEEDS)]}"
    y, m, g = Y[dev_idx], M[dev_idx], G[dev_idx]
    sign = {d: np.sign(np.nanmedian(y[g == d][:, 0])) for d in np.unique(g)}
    groups = {"all development rows": np.ones(len(g), bool), "negative plasma current": np.array([sign[d] < 0 for d in g]),
              "positive plasma current": np.array([sign[d] > 0 for d in g])}
    n_disch = {k: len(np.unique(g[sel])) for k, sel in groups.items()}
    sd = {t: float(np.nanstd(y[:, F.J[t]])) * F.UNIT[t][0] for t in HEADLINE}   # report units (mm, kA), like the MAE below

    def mae(pred, sel, t):
        j = F.J[t]
        k = sel & m[:, j]
        return float(np.abs(pred[k, j] - y[k, j]).mean() * F.UNIT[t][0])

    def score(pred, sel):
        return float(np.mean([mae(pred, sel, t) / sd[t] for t in HEADLINE]))
    models = list(complete)
    res = {k: {mod: {t: [mae(complete[mod][s], sel, t) for s in SEEDS] for t in HEADLINE} for mod in models} for k, sel in groups.items()}
    sc = {k: {mod: [score(complete[mod][s], sel) for s in SEEDS] for mod in models} for k, sel in groups.items()}
    A = "resA_pipe"
    mean = lambda v: float(np.mean(v))
    c1 = {k: mean(sc[k][A]) <= MARGIN * mean(sc[k]["cand"]) for k in ("negative plasma current", "positive plasma current")}
    all_ = "all development rows"
    c2 = {t: mean(res[all_][A][t]) <= MARGIN * mean(res[all_]["cand"][t]) for t in ("R_limiter", "Z_limiter")}
    c3 = [sc[all_][A][i] < sc[all_]["cand"][i] for i in range(len(SEEDS))]
    ship = all(c1.values()) and all(c2.values()) and all(c3)
    decision = {"ship": bool(ship), "criterion_1_polarity": c1, "criterion_2_limiter": c2, "criterion_3_seeds": c3,
                "score": {k: {mod: [round(v, 4) for v in sc[k][mod]] for mod in models} for k in sc}, "configs": {k: v["best_params"] for k, v in configs().items()}}
    (OUT / "ipp1-search-dev.json").write_text(json.dumps(decision, indent=1) + "\n")

    fmt = lambda v, d=3: f"{np.mean(v):.{d}g} ({np.std(v, ddof=1):.2g})"
    unit = {t: F.UNIT[t][1] or "-" for t in HEADLINE}
    cfg = configs()
    L = ["# IPP 1: the architecture of the cloud search against `cand`, on the development discharges only", "",
         "Script `analysis/ipp1_search_dev.py`; protocol and the **decision rule written before the first result** are in its docstring. The cloud search saw all 149 discharges, so "
         "nothing here uses the locked 30; this is 5-fold cross-validation by discharge inside the 119 development discharges, 3 seeds per fold (3 x 5 = 15 trainings per model), "
         "masked loss, the 46 inputs of `cand`. Both the search and the design of `cand` used these discharges, so the comparison is fair between them but optimistic for both.", "",
         "Configurations (hyperparameters of `results/cloud-search.json`):", "",
         "| name | from fold | inner objective | arch | width | depth | act | dropout | lr | wd | epochs | batch | sched | loss | delta | w_lim | w_cls |", "|---|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|"]
    for name, r in cfg.items():
        p = r["best_params"]
        L.append(f"| {name} | {r['fold']} | {r['best_value']:.4f} | {p['arch']} | {p['width']} | {p['depth']} | {p['act']} | {p['dropout']} | {p['lr']:.2g} | {p['wd']:.2g} | {p['epochs']} | {p['batch']} | {p['sched']} | {p['loss']} | "
                 f"{p.get('delta', float('nan')):.2g} | {p['w_lim']:.2g} | {p['w_cls']:.2g} |")
    L += ["", "`cand`: general MLP 256-256-128 + ridge for plasma_current + limiter network, gated (`analysis/ipp1_final.py`); `*_pipe`: the same pipeline with the residual network "
          "in place of both networks; `*_alone`: the residual network alone for all 16 targets (what the search measured). Seed 0 of `cand` is the cached cross-validation of `ipp1_final.py`."]
    for k in groups:
        L += ["", f"## {k} ({n_disch[k]} discharges): MAE, mean (SD over 3 seeds); unit mm, plasma current in kA", "",
              "| target | unit | " + " | ".join(models) + " | resA_pipe / cand |", "|---|---|" + "---:|" * (len(models) + 1)]
        for t in HEADLINE:
            L.append(f"| {t} | {unit[t]} | " + " | ".join(fmt(res[k][mod][t]) for mod in models) + f" | {mean(res[k][A][t]) / mean(res[k]['cand'][t]):.2f} |")
        L.append(f"| **relative score** (mean of MAE / target SD over the 11 targets) | | " + " | ".join(fmt(sc[k][mod], 3) for mod in models) + f" | {mean(sc[k][A]) / mean(sc[k]['cand']):.2f} |")
    L += ["", "## Decision rule and verdict", "",
          f"1. resA_pipe score at least 5 % below `cand`, negative-current group: {mean(sc['negative plasma current'][A]):.4f} against {mean(sc['negative plasma current']['cand']):.4f} (ratio {mean(sc['negative plasma current'][A]) / mean(sc['negative plasma current']['cand']):.2f}): **{'yes' if c1['negative plasma current'] else 'no'}**; "
          f"positive-current group: {mean(sc['positive plasma current'][A]):.4f} against {mean(sc['positive plasma current']['cand']):.4f} (ratio {mean(sc['positive plasma current'][A]) / mean(sc['positive plasma current']['cand']):.2f}): **{'yes' if c1['positive plasma current'] else 'no'}**.",
          f"2. MAE at least 5 % below `cand` on the limiter point: R_limiter ratio {mean(res[all_][A]['R_limiter']) / mean(res[all_]['cand']['R_limiter']):.2f} (**{'yes' if c2['R_limiter'] else 'no'}**), "
          f"Z_limiter ratio {mean(res[all_][A]['Z_limiter']) / mean(res[all_]['cand']['Z_limiter']):.2f} (**{'yes' if c2['Z_limiter'] else 'no'}**).",
          f"3. Score below `cand` in every seed (all development rows): per seed resA_pipe {', '.join(f'{v:.4f}' for v in sc[all_][A])} against `cand` {', '.join(f'{v:.4f}' for v in sc[all_]['cand'])}: **{'yes' if all(c3) else 'no'}**.", "",
          f"**Verdict: {'SHIP' if ship else 'DO NOT SHIP'}** (`resA_pipe` against `cand`). " + ("The locked 30 discharges are scored once for it, below." if ship else "The locked 30 discharges were not used.")]
    text = "\n".join(L) + "\n"
    target = REPO / "results/ipp1-search-dev.md"
    if target.exists() and "\n## Reading" in target.read_text():   # the hand-written reading is kept
        text += "\n## Reading" + target.read_text().split("\n## Reading", 1)[1]
    target.write_text(text)
    print(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job", default="")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    assert not F.SMOKE
    if a.job:
        job(a.job, a.threads)
    if a.report:
        report()
