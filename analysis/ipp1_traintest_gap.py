#!/usr/bin/env python
"""Overfitting check: mean absolute error on the TRAINING rows against the held-out rows, for `cand` (shipped) and the baseline network.

Development: the 5 group folds inside the 119 development discharges of ipp1_final.py, one seed (seed = fold, as the cached cross-validation); for each
fold the model is trained once and scored on its own training rows and on its held-out rows; the table gives the mean over the 5 folds of the pooled MAE of
a fold. Locked: the models trained on all 119 development discharges (seed 0, as the cache `locked_*`), scored on those 119 discharges and on the 30 locked
ones. The held-out predictions of the retrained models are compared with the cached ones as a check that this is the same model.

    HACKATHON_HOME=... nice -n 10 ~/.venvs/hackathon/bin/python -I analysis/ipp1_traintest_gap.py [--threads 2]

Writes results/ipp1-traintest-gap.md and out/ipp1-traintest-gap.json.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_final as F
from ipp1_common import OUT, ROOT

REPO = ROOT / "repo"
RECIPES = {"cand": "shipped candidate", "base": "baseline network"}


def mae_by_target(pred, y, m):
    """MAE per target in report units (mm, kA; is_limited and the shape numbers dimensionless)."""
    out = {}
    for j, t in enumerate(F.TARGETS):
        k = m[:, j]
        out[t] = float(np.abs(pred[k, j] - y[k, j]).mean() * F.UNIT[t][0])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threads", type=int, default=2)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    assert not F.SMOKE
    started = time.time()
    (df, X, Y, G, M), _ = F.aligned_data()
    times = df.time.to_numpy()
    _, dev_idx, lock_idx = F.split(G)
    cache_ok = {}
    res = {r: {"folds": [], "locked": None} for r in RECIPES}
    for recipe in RECIPES:
        for fold, (tr_l, te_l) in enumerate(F.group_folds(X[dev_idx], Y[dev_idx], G[dev_idx], 5)):
            tr, te = dev_idx[tr_l], dev_idx[te_l]
            assert not set(G[tr]) & set(G[te])
            predict = F.train(recipe, X[tr], Y[tr], M[tr], G[tr], times[tr], fold, F.AUG_SEED + fold)
            p_te, cached = predict(X[te]), np.load(F.CACHE / f"cv_{recipe}_{fold}.npz")
            cache_ok[f"{recipe}_cv{fold}"] = float(np.abs(p_te - cached["clean"]).max())
            res[recipe]["folds"].append({"train": mae_by_target(predict(X[tr]), Y[tr], M[tr]), "test": mae_by_target(p_te, Y[te], M[te]),
                                         "train_rows": int(len(tr)), "test_rows": int(len(te))})
            print(f"{recipe} fold {fold}: {time.time() - started:.0f} s", flush=True)
        predict = F.train(recipe, X[dev_idx], Y[dev_idx], M[dev_idx], G[dev_idx], times[dev_idx], 0, F.AUG_SEED + 50)
        p_lk, cached = predict(X[lock_idx]), np.load(F.CACHE / f"locked_{recipe}.npz")
        cache_ok[f"{recipe}_locked"] = float(np.abs(p_lk - cached["clean"]).max())
        res[recipe]["locked"] = {"train": mae_by_target(predict(X[dev_idx]), Y[dev_idx], M[dev_idx]), "test": mae_by_target(p_lk, Y[lock_idx], M[lock_idx]),
                                 "train_rows": int(len(dev_idx)), "test_rows": int(len(lock_idx))}
        print(f"{recipe} locked: {time.time() - started:.0f} s", flush=True)
    summary = {}
    for recipe, r in res.items():
        dev = {t: (float(np.mean([f["train"][t] for f in r["folds"]])), float(np.mean([f["test"][t] for f in r["folds"]]))) for t in F.TARGETS}
        lk = {t: (r["locked"]["train"][t], r["locked"]["test"][t]) for t in F.TARGETS}
        summary[recipe] = {"development_cv": dev, "locked": lk}
    (OUT / "ipp1-traintest-gap.json").write_text(json.dumps({"summary": summary, "max_abs_diff_to_cache": cache_ok, "per_fold": res}, indent=1) + "\n")
    write_md(summary, cache_ok)


def write_md(summary, cache_ok):
    unit = {t: F.UNIT[t][1] or "-" for t in F.TARGETS}
    worst_cache = max(cache_ok.values())
    L = ["# IPP 1: error on the training rows against the held-out rows", "",
         "Script `analysis/ipp1_traintest_gap.py`. MAE per target (mm, plasma current in kA, shape numbers and `is_limited` dimensionless). **gap = held-out MAE / training MAE**; a value near 1 means "
         "the model is as good on unseen discharges as on the ones it trained on, a large value means it fits its training discharges much better than new ones.", "",
         "- **Development**: the 5 group folds inside the 119 development discharges (about 95 training and 24 held-out discharges per fold), one seed (seed = fold). For each fold the model is trained once "
         "and scored on its own training rows and on its held-out rows; the table is the mean over the 5 folds of the pooled MAE of a fold.",
         "- **Locked**: the models trained on all 119 development discharges (seed 0), scored on those 119 discharges (training) and on the 30 locked discharges (held out). Clean inputs throughout.",
         f"- Check: the held-out predictions of the retrained models differ from the cached ones of `ipp1_final.py` by at most {worst_cache:.2g} (raw units) over all ten models, so these are the same models.", ""]
    for recipe, name in RECIPES.items():
        L += [f"## {name} (`{recipe}`)", "", "| target | unit | dev train | dev held-out | gap | locked: train | locked: held-out | gap |", "|---|---|---:|---:|---:|---:|---:|---:|"]
        for t in F.TARGETS:
            (dt, dh), (lt, lh) = summary[recipe]["development_cv"][t], summary[recipe]["locked"][t]
            L.append(f"| {t} | {unit[t]} | {dt:.4g} | {dh:.4g} | {dh / dt:.1f} | {lt:.4g} | {lh:.4g} | {lh / lt:.1f} |")
        L.append("")
    for recipe, name in RECIPES.items():
        gaps = {t: summary[recipe]["development_cv"][t][1] / summary[recipe]["development_cv"][t][0] for t in F.TARGETS}
        lo, hi = min(gaps, key=gaps.get), max(gaps, key=gaps.get)
        big = [t for t in F.TARGETS if gaps[t] >= 3]
        L.append(f"Reading, {name}: the development gap ranges from {gaps[lo]:.1f} ({lo}) to {gaps[hi]:.1f} ({hi}); "
                 + (f"{len(big)} of 16 targets have a gap of 3 or more ({', '.join(big)})." if big else "no target has a gap of 3 or more."))
    (REPO / "results/ipp1-traintest-gap.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
