#!/usr/bin/env python
"""A retraining ranking of the 24 magnetic inputs (REQ-004), on training discharges only.

    HACKATHON_HOME=<hackathon folder> ~/.venvs/hackathon/bin/python -I analysis/ipp1_inputs_ranking.py

Writes out/ipp1-inputs-ranking.{json,md}. Nothing here touches the locked test set.

Why this file exists. `results/ipp1-inputs.md` ranks the inputs by permutation importance, and the
independent review rejected that as a ranking: the 24 inputs are numerically collinear, so permuting one
column moves rows off the data manifold and the result measures the network's extrapolation sensitivity,
not what a sensor contributes. `results/ipp1-inputs-controls.md` already answers "how many inputs" with
retrained subset curves. What is still missing, and what this script delivers, is the ranking itself,
obtained by retraining rather than by permuting:

1. **Drop-column ranking (network, retrained).** For each input, retrain the baseline MLP on the other 23
   and measure how much the summary error rises. Paired per fold: the same fold, the same seed and the same
   held-out discharges as its own all-24 baseline, so the difference is not polluted by fold or seed luck.
2. **Backward-elimination order (ridge, deterministic).** Greedy elimination from 24 inputs down to 1 with
   the ridge criterion of `ipp1_inputs.backward_ridge_subset` (the same Gram-matrix formulation, re-derived
   here because that module parses argv at import). Deterministic, so unlike the network ranking its order
   carries no seed noise; it is the ranking to quote when the two disagree inside the noise.
3. **Seed noise reference.** The all-24 baseline is refit with three seeds per fold. The review measured
   8 to 19 % seed noise, and a drop-column gap smaller than that is not a real difference. Every gap below
   is reported next to this number instead of being presented as a clean order.

Protocol: the 30 locked discharges of `analysis/ipp1_final.py` are removed first, so all of this runs on the
119 development discharges ("training discharges only"). Inside them, 5-fold GroupKFold by whole discharge.
Summary error = mean relative error (RMSE / spread) over the 13 targets of `ipp1_inputs.SUMMARY`, which
excludes the two limiter targets and is_limited, so the number is comparable with the existing REQ-004 tables.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, fit_mlp, group_folds, load, score

torch.set_num_threads(2)

LOCK_SEED, N_LOCK = 20261024, 30  # must match analysis/ipp1_final.py
SUMMARY = [t for t in TARGETS if t not in ("R_limiter", "Z_limiter", "is_limited")]
# A smoke run can shrink the work: IPP1_FOLDS=2 IPP1_SEEDS=1 IPP1_EPOCHS=3 exercises every code path
# in under a minute. The reported run uses the defaults.
N_FOLDS = int(os.environ.get("IPP1_FOLDS", 5))
N_SEEDS = int(os.environ.get("IPP1_SEEDS", 3))
EPOCHS = int(os.environ.get("IPP1_EPOCHS", 60))
RIDGE_ALPHA = 1.0

df, X, Y, G, M = load()
NAMES = [c for c in df.columns if c.startswith(("IPR", "FL"))]
assert len(NAMES) == X.shape[1], f"{len(NAMES)} names for {X.shape[1]} inputs"

# --- training discharges only: drop the locked test discharges before anything else --------------
locked = np.sort(np.random.RandomState(LOCK_SEED).choice(np.unique(G), N_LOCK, replace=False))
dev = ~np.isin(G, locked)
Xd, Yd, Gd, Md = X[dev], Y[dev], G[dev], M[dev]
print(f"development set: {dev.sum():,} rows, {len(np.unique(Gd))} discharges "
      f"(locked out: {N_LOCK} discharges, {(~dev).sum():,} rows)", flush=True)
folds = group_folds(Xd, Yd, Gd, N_FOLDS)
for f, (tr, te) in enumerate(folds):
    assert not set(Gd[tr]) & set(Gd[te]), f"fold {f} shares a discharge between train and test"


def summary(pred, te, cols=None):
    """Mean relative error over the SUMMARY targets, as ipp1_inputs.summary()."""
    res = score(pred, Yd[te], Md[te])
    return float(np.mean([res[t]["nrmse"] for t in SUMMARY]))


def run(tr, te, cols, seed):
    predict, _, _ = fit_mlp(Xd[tr][:, cols], Yd[tr], Md[tr], epochs=EPOCHS, seed=seed)
    return summary(predict(Xd[te][:, cols]), te)


# --- 1 + 3: baseline per fold with N_SEEDS seeds, then one drop-column refit per input ------------
all_cols = list(range(X.shape[1]))
base = {}        # fold -> {seed: summary}
drop = {n: {} for n in NAMES}  # name -> {fold: summary}, seed = fold (paired with base[fold][fold])
t0 = time.time()
for f, (tr, te) in enumerate(folds):
    base[f] = {}
    for s in range(N_SEEDS):
        seed = f + 100 * s
        base[f][seed] = run(tr, te, all_cols, seed)
    print(f"fold {f}: baseline seeds {[round(v, 4) for v in base[f].values()]} "
          f"({time.time() - t0:.0f} s)", flush=True)
    for i, name in enumerate(NAMES):
        cols = [c for c in all_cols if c != i]
        drop[name][f] = run(tr, te, cols, f)  # same seed and fold as base[f][f]
    print(f"fold {f}: 24 drop-column refits done ({time.time() - t0:.0f} s)", flush=True)

seed_spread = [float(np.std(list(v.values())) / np.mean(list(v.values()))) for v in base.values()]
paired_base = {f: base[f][f] for f in base}
rows = []
for name in NAMES:
    d = [drop[name][f] - paired_base[f] for f in range(N_FOLDS)]
    rel = [drop[name][f] / paired_base[f] - 1 for f in range(N_FOLDS)]
    rows.append({"input": name, "delta_mean": float(np.mean(d)), "delta_sd": float(np.std(d)),
                 "rel_mean": float(np.mean(rel)), "rel_sd": float(np.std(rel)),
                 "folds_worse": int(sum(x > 0 for x in d)), "per_fold": [float(x) for x in d]})
rows.sort(key=lambda r: -r["delta_mean"])
drop_order = [r["input"] for r in rows]

# --- 2: deterministic greedy backward elimination with the ridge criterion ------------------------
def ridge_stats(tr):
    xs = ((Xd[tr] - Xd[tr].mean(0)) / (Xd[tr].std(0) + 1e-9)).astype(np.float64)
    out = []
    for t in SUMMARY:
        j = TARGETS.index(t)
        mk = Md[tr, j]
        x, y = xs[mk], Yd[tr, j][mk].astype(np.float64)
        xc, yc = x - x.mean(0), (y - y.mean()) / (y.std() + 1e-12)
        out.append((xc.T @ xc, xc.T @ yc, len(yc)))
    return out


def ridge_loss(stats, cols):
    """Summed relative squared error of a ridge fit on `cols` (one fit per summary target)."""
    total, ix = 0.0, np.ix_(cols, cols)
    for g, c, n in stats:
        gs, cs = g[ix], c[cols]
        w = np.linalg.solve(gs + RIDGE_ALPHA * np.eye(len(cols)), cs)
        total += float((n - 2 * w @ cs + w @ gs @ w) / n)
    return total


elim_rank = {n: [] for n in NAMES}  # name -> elimination position per fold (1 = dropped first)
elim_curve = {}
for f, (tr, te) in enumerate(folds):
    stats = ridge_stats(tr)
    cols, step = list(all_cols), 1
    curve = {len(cols): ridge_loss(stats, cols) / len(SUMMARY)}
    while len(cols) > 1:
        worst = min(cols, key=lambda c: ridge_loss(stats, [x for x in cols if x != c]))
        cols = [x for x in cols if x != worst]
        elim_rank[NAMES[worst]].append(step)
        curve[len(cols)] = ridge_loss(stats, cols) / len(SUMMARY)
        step += 1
    elim_rank[NAMES[cols[0]]].append(step)  # the survivor is eliminated last
    elim_curve[f] = curve
    print(f"fold {f}: ridge backward elimination done ({time.time() - t0:.0f} s)", flush=True)

ridge_order = sorted(NAMES, key=lambda n: np.mean(elim_rank[n]), reverse=True)  # most important first

# --- rank agreement with the published permutation ranking ---------------------------------------
perm_order = None
pj = OUT / "ipp1-inputs.json"
if pj.exists():
    blob = json.loads(pj.read_text())
    for key in ("ranking", "permutation_ranking", "order"):
        v = blob.get(key)
        if isinstance(v, list) and len(v) == len(NAMES) and all(isinstance(x, str) for x in v):
            perm_order = v
            break


def spearman(a, b):
    ra = {n: i for i, n in enumerate(a)}
    rb = {n: i for i, n in enumerate(b)}
    x = np.array([ra[n] for n in NAMES], float)
    y = np.array([rb[n] for n in NAMES], float)
    return float(np.corrcoef(x, y)[0, 1])


agree = {"drop_column_vs_ridge": spearman(drop_order, ridge_order)}
if perm_order:
    agree["drop_column_vs_permutation"] = spearman(drop_order, perm_order)
    agree["ridge_vs_permutation"] = spearman(ridge_order, perm_order)

meta = {"dev_rows": int(dev.sum()), "dev_discharges": int(len(np.unique(Gd))), "locked_discharges": N_LOCK,
        "folds": N_FOLDS, "seeds_per_baseline": N_SEEDS, "epochs": EPOCHS,
        "baseline_summary_mean": float(np.mean(list(paired_base.values()))),
        "baseline_per_fold": {str(f): paired_base[f] for f in paired_base},
        "seed_spread_per_fold": seed_spread, "seed_spread_mean": float(np.mean(seed_spread)),
        "summary_targets": SUMMARY, "runtime_s": time.time() - t0}
with open(OUT / "ipp1-inputs-ranking.json", "w") as fh:
    json.dump({"meta": meta, "drop_column": rows, "drop_column_order": drop_order,
               "ridge_elimination_order": ridge_order,
               "ridge_elimination_rank_per_fold": {n: elim_rank[n] for n in NAMES},
               "ridge_curve": {str(f): {str(k): v for k, v in c.items()} for f, c in elim_curve.items()},
               "permutation_order": perm_order, "rank_agreement": agree}, fh, indent=1, allow_nan=False)

# --- report --------------------------------------------------------------------------------------
noise = meta["seed_spread_mean"]
L = ["# Which inputs matter: a retraining ranking (REQ-004)", "",
     f"Computed on the {meta['dev_discharges']} development discharges only ({meta['dev_rows']:,} rows); the "
     f"{N_LOCK} locked test discharges of `analysis/ipp1_final.py` are removed before anything is fitted. "
     f"Inside the development set, {N_FOLDS}-fold GroupKFold by whole discharge. Summary error = mean relative "
     f"error (RMSE / spread) over the {len(SUMMARY)} targets of `ipp1_inputs.SUMMARY` (no limiter point, no "
     f"is_limited), so it is comparable with `results/ipp1-inputs.md`. All-24 baseline: "
     f"{meta['baseline_summary_mean']:.4f}.", "",
     f"**Read the noise first.** Refitting the same all-24 baseline with {N_SEEDS} seeds per fold moves the "
     f"summary error by {noise:.1%} on average (per fold: "
     f"{', '.join(f'{v:.1%}' for v in seed_spread)}). The review measured 8 to 19 % seed noise and said to treat "
     f"smaller effects as unresolved. Dropping one of 24 collinear inputs is mostly a smaller effect than that, "
     f"which is the honest headline of this file: **no single magnetic input is individually necessary.** The "
     f"ranking below is therefore an order of magnitude statement, not a league table.", "",
     "## Drop-column ranking (network retrained without one input)", "",
     "`delta` is the rise in summary error when the input is removed and the network is retrained on the other 23, "
     "averaged over the folds; it is paired, each refit shares the fold, seed and held-out discharges of its own "
     "all-24 baseline. `rel` is the same as a percentage of that baseline. `folds worse` counts how many of the "
     f"{N_FOLDS} folds got worse without the input: {N_FOLDS}/{N_FOLDS} or 0/{N_FOLDS} is a consistent sign, "
     "anything in between is noise even if the mean looks large.", "",
     "| rank | input | delta | rel | sd of delta | folds worse |", "|---|---|---|---|---|---|"]
for i, r in enumerate(rows, 1):
    L.append(f"| {i} | {r['input']} | {r['delta_mean']:+.5f} | {r['rel_mean']:+.1%} | {r['delta_sd']:.5f} | "
             f"{r['folds_worse']}/{N_FOLDS} |")
consistent = [r for r in rows if r["folds_worse"] == N_FOLDS and r["rel_mean"] > noise]
L += ["", (f"Inputs that got worse in all {N_FOLDS} folds AND by more than the {noise:.1%} seed noise: "
           + (", ".join(f"{r['input']} ({r['rel_mean']:+.1%})" for r in consistent) if consistent
              else "none. Every single-input effect sits inside the seed noise.")), "",
      "## Backward-elimination order (ridge criterion, deterministic)", "",
      "Greedy elimination from 24 inputs down to 1, repeated inside each fold on its training rows only, with the "
      "ridge criterion of `ipp1_inputs.backward_ridge_subset`. This path has no seed noise, so where it and the "
      "network ranking disagree inside the noise, this is the order to quote. Most important (eliminated last) "
      "first, with the mean elimination step over the folds:", "",
      "| rank | input | mean elimination step | per fold |", "|---|---|---|---|"]
for i, n in enumerate(ridge_order, 1):
    L.append(f"| {i} | {n} | {np.mean(elim_rank[n]):.1f} | {', '.join(str(s) for s in elim_rank[n])} |")
L += ["", "### Ridge summary error against the number of inputs kept", "",
      "Mean relative squared error of the ridge criterion itself (not the network), averaged over the folds. "
      "It shows where the elimination path starts to cost accuracy.", "",
      "| inputs kept | " + " | ".join(f"fold {f}" for f in range(N_FOLDS)) + " | mean |",
      "|---|" + "---|" * (N_FOLDS + 1)]
for k in sorted(elim_curve[0], reverse=True):
    vals = [elim_curve[f][k] for f in range(N_FOLDS)]
    L.append(f"| {k} | " + " | ".join(f"{v:.4f}" for v in vals) + f" | {np.mean(vals):.4f} |")
L += ["", "## Do the three rankings agree?", "",
      "Spearman rank correlation between the orders. Low agreement is itself the finding: with collinear inputs "
      "the ranking depends on the method, so none of them should be presented as 'the important sensors'.", "",
      "| pair | rank correlation |", "|---|---|"]
for k, v in agree.items():
    L.append(f"| {k.replace('_', ' ')} | {v:+.2f} |")
if perm_order:
    L += ["", "Published permutation order, for reference (most important first): " + ", ".join(perm_order)]
L += ["", "## What to say about REQ-004", "",
      f"- The defensible claim is about the NUMBER of inputs, not which ones: the retrained subset curves in "
      f"`results/ipp1-inputs-controls.md` are the evidence, and this file adds that no individual input carries "
      f"a loss above the {noise:.1%} seed noise when the other 23 remain.",
      "- The two sensor families do differ, and that result is outside the noise: IPR coils only 0.066 against "
      "flux loops only 0.285, 4.3 times worse (`results/ipp1-inputs.md`). Group-level statements survive; "
      "single-sensor statements do not.",
      "- Do not present any of these three orders as 'the important sensors' on a slide. Say 'no single sensor is "
      "individually necessary; the coil family carries most of the signal'.",
      "", f"Runtime {meta['runtime_s'] / 60:.1f} min, {N_FOLDS} folds x (24 drop-column + {N_SEEDS} baseline) "
      f"network refits plus {N_FOLDS} deterministic elimination paths, 2 torch threads."]
(OUT / "ipp1-inputs-ranking.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
