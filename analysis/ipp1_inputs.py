#!/usr/bin/env python
"""Which inputs matter and how few are enough (REQ-004), measured on whole held-out discharges.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_inputs.py [--epochs 60] [--folds 5]

For every fold: train on all 24 inputs, rank the inputs by permutation importance computed on the
TRAINING rows only (so the ranking never sees the test discharges), retrain with the top-k inputs,
and also with only the 16 IPR coils or only the 8 flux loops. Writes out/ipp1-inputs.{json,md,png}.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, fit_mlp, group_folds, load, score

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=60)
ap.add_argument("--folds", type=int, default=5)
args = ap.parse_args()

df, X, Y, G, M = load()
NAMES = [c for c in df.columns if c.startswith(("IPR", "FL"))]
# The summary leaves out the two limiter coordinates and is_limited, which are far harder than the rest.
SUMMARY = [t for t in TARGETS if t not in ("R_limiter", "Z_limiter", "is_limited")]
SHOW = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "R_x_point", "R_strike_point_1", "R_limiter"]
K_LIST = [16, 12, 8, 6, 5, 4, 3, 2]
rng = np.random.default_rng(0)


def summary(res):
    return float(np.mean([res[t]["nrmse"] for t in SUMMARY]))


importance = np.zeros((args.folds, X.shape[1]))
runs = {}
for f, (tr, te) in enumerate(group_folds(X, Y, G, args.folds)):
    predict, _, _ = fit_mlp(X[tr], Y[tr], M[tr], args.epochs, seed=f)
    sub = rng.choice(tr, size=min(6000, len(tr)), replace=False)
    base = score(predict(X[sub]), Y[sub], M[sub])
    base_s = summary(base)
    for j in range(X.shape[1]):
        xp = X[sub].copy()
        xp[:, j] = rng.permutation(xp[:, j])
        importance[f, j] = summary(score(predict(xp), Y[sub], M[sub])) - base_s
    order = np.argsort(-importance[f])
    full = score(predict(X[te]), Y[te], M[te])
    runs.setdefault("all 24", []).append(full)
    for k in K_LIST:
        cols = np.sort(order[:k])
        p, _, _ = fit_mlp(X[tr][:, cols], Y[tr], M[tr], args.epochs, seed=f)
        runs.setdefault(f"top {k}", []).append(score(p(X[te][:, cols]), Y[te], M[te]))
    for name, cols in (("IPR only (16)", [i for i, c in enumerate(NAMES) if c.startswith("IPR")]),
                       ("FL only (8)", [i for i, c in enumerate(NAMES) if c.startswith("FL")])):
        p, _, _ = fit_mlp(X[tr][:, cols], Y[tr], M[tr], args.epochs, seed=f)
        runs.setdefault(name, []).append(score(p(X[te][:, cols]), Y[te], M[te]))
    print(f"fold {f + 1}/{args.folds} done", flush=True)

imp = importance.mean(0)
table = {}
for name, rs in runs.items():
    table[name] = {"summary_nrmse_mean": float(np.mean([summary(r) for r in rs])),
                   "summary_nrmse_std": float(np.std([summary(r) for r in rs])),
                   "targets": {t: {"mae": float(np.mean([r[t]["mae"] for r in rs])), "unit": rs[0][t]["unit"],
                                   "nrmse": float(np.mean([r[t]["nrmse"] for r in rs]))} for t in SHOW}}
ranking = [NAMES[i] for i in np.argsort(-imp)]
json.dump({"folds": args.folds, "epochs": args.epochs, "inputs": NAMES, "permutation_importance": dict(zip(NAMES, imp.tolist())),
           "ranking": ranking, "runs": table}, open(OUT / "ipp1-inputs.json", "w"), indent=1)

order_names = ["all 24"] + [f"top {k}" for k in K_LIST] + ["IPR only (16)", "FL only (8)"]
lines = ["# Fewer inputs: accuracy against the number of inputs (REQ-004)", "",
         f"{args.folds} folds by discharge; summary = mean of the relative error (RMSE / spread) over {len(SUMMARY)} targets, "
         "without the limiter point; lower is better. Ranking by permutation importance on training rows only.", "",
         "| inputs | summary error | " + " | ".join(f"{t} ({table['all 24']['targets'][t]['unit'] or 'abs'})" for t in SHOW) + " |",
         "|---|---|" + "---|" * len(SHOW)]
for n in order_names:
    lines.append(f"| {n} | {table[n]['summary_nrmse_mean']:.3f} ± {table[n]['summary_nrmse_std']:.3f} | "
                 + " | ".join(f"{table[n]['targets'][t]['mae']:.3g}" for t in SHOW) + " |")
lines += ["", "Inputs ranked by permutation importance (most important first): " + ", ".join(ranking)]
(OUT / "ipp1-inputs.md").write_text("\n".join(lines), encoding="utf-8")

plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False, "font.size": 8})
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
ks = [24] + K_LIST
vals = [table["all 24" if k == 24 else f"top {k}"]["summary_nrmse_mean"] for k in ks]
errs = [table["all 24" if k == 24 else f"top {k}"]["summary_nrmse_std"] for k in ks]
ax[0].errorbar(ks, vals, yerr=errs, marker="o", color="#5b7cff", capsize=2)
for n, c in (("IPR only (16)", "#e07a5f"), ("FL only (8)", "#3d405b")):
    ax[0].axhline(table[n]["summary_nrmse_mean"], color=c, ls="--", lw=1, label=n)
ax[0].set_xlabel("počet použitých vstupů")
ax[0].set_ylabel("průměrná relativní chyba")
ax[0].set_yscale("log")
ax[0].legend()
ax[0].set_title("Kolik vstupů stačí")
o = np.argsort(-imp)
ax[1].bar(range(len(o)), imp[o], color=["#e07a5f" if NAMES[i].startswith("FL") else "#5b7cff" for i in o])
ax[1].set_xticks(range(len(o)))
ax[1].set_xticklabels([NAMES[i] for i in o], rotation=90)
ax[1].set_title("Důležitost vstupů (modře cívky IPR, oranžově smyčky FL)")
fig.tight_layout()
fig.savefig(OUT / "ipp1-inputs.png")
print("\n".join(lines))
