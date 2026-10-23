#!/usr/bin/env python
"""Which inputs matter and how few are enough (REQ-004), measured on whole held-out discharges.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_inputs.py [--epochs 60] [--folds 5]

For every fold: train on all 24 inputs, rank the inputs by permutation importance computed on the
TRAINING rows only (so the ranking never sees the test discharges), retrain with the top-k inputs,
and also with only the 16 IPR coils or only the 8 flux loops. For k in 12, 8, 6 two controls are
added, both chosen on the training discharges only: a random subset of the same size (3 draws,
averaged) and a model-free subset (QR with column pivoting of the standardised inputs) and a greedy
backward-elimination subset (ridge regression criterion). Writes out/ipp1-inputs.{json,md,png}.

The permutation ranking is the importance of an input for the TRAINED NETWORK, not information content:
the inputs are collinear, so permuting one column creates rows off the data manifold.

Controls only (a cheaper run, writes out/ipp1-inputs-controls.{json,md} and leaves the main files alone):

    ... ipp1_inputs.py --controls-only --only-folds 0,1 --ks 12 --threads 1      (one piece, repeat per fold and k)
    ... ipp1_inputs.py --merge                                                   (collect the pieces)

A piece also refits the all-24 network and the permutation top-k of the same fold, so the controls are
compared on identical folds and seeds.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import torch
from scipy.linalg import qr

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, fit_mlp, group_folds, load, score

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=60)
ap.add_argument("--folds", type=int, default=5)
ap.add_argument("--controls-only", action="store_true")
ap.add_argument("--only-folds", default=None, help="comma separated fold numbers (controls-only)")
ap.add_argument("--ks", default="12,8,6", help="comma separated subset sizes for the controls")
ap.add_argument("--threads", type=int, default=2)
ap.add_argument("--merge", action="store_true", help="collect the controls-only pieces into the controls report")
args = ap.parse_args()
torch.set_num_threads(args.threads)

df, X, Y, G, M = load()
NAMES = [c for c in df.columns if c.startswith(("IPR", "FL"))]
# The summary leaves out the two limiter coordinates and is_limited, which are far harder than the rest.
SUMMARY = [t for t in TARGETS if t not in ("R_limiter", "Z_limiter", "is_limited")]
SHOW = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "R_x_point", "R_strike_point_1", "R_limiter"]
K_LIST = [16, 12, 8, 6, 5, 4, 3, 2]
K_CTRL = [int(k) for k in args.ks.split(",")]
PARTS = OUT / "ipp1-inputs-controls-parts"
rng = np.random.default_rng(0)


def summary(res):
    return float(np.mean([res[t]["nrmse"] for t in SUMMARY]))


def permutation_order(predict, tr, f):
    """Inputs sorted by permutation importance on 6000 training rows; returns (order, importance)."""
    sub = rng.choice(tr, size=min(6000, len(tr)), replace=False)
    base_s = summary(score(predict(X[sub]), Y[sub], M[sub]))
    imp = np.zeros(X.shape[1])
    for j in range(X.shape[1]):
        xp = X[sub].copy()
        xp[:, j] = rng.permutation(xp[:, j])
        imp[j] = summary(score(predict(xp), Y[sub], M[sub])) - base_s
    return np.argsort(-imp), imp


def qr_pivot_subset(tr, k):
    """Columns picked by QR with column pivoting on the standardised training inputs (model free)."""
    xs = (X[tr] - X[tr].mean(0)) / (X[tr].std(0) + 1e-9)
    return np.sort(qr(xs.astype(np.float64), mode="economic", pivoting=True)[2][:k])


def backward_ridge_subset(tr, k):
    """Greedy backward elimination on the training rows: drop the input whose removal raises the summed
    relative squared error of a ridge fit (alpha 1, one fit per summary target) the least."""
    xs = ((X[tr] - X[tr].mean(0)) / (X[tr].std(0) + 1e-9)).astype(np.float64)
    stats = []
    for t in SUMMARY:
        j = TARGETS.index(t)
        mk = M[tr, j]
        x, y = xs[mk], Y[tr, j][mk].astype(np.float64)
        xc, yc = x - x.mean(0), (y - y.mean()) / (y.std() + 1e-12)
        stats.append((xc.T @ xc, xc.T @ yc, len(yc)))

    def loss(cols):
        total, ix = 0.0, np.ix_(cols, cols)
        for g, c, n in stats:
            w = np.linalg.solve(g[ix] + np.eye(len(cols)), c[cols])
            total += (n - 2 * c[cols] @ w + w @ g[ix] @ w) / n
        return total
    cols = list(range(X.shape[1]))
    while len(cols) > k:
        cols.remove(min(cols, key=lambda i: loss([c for c in cols if c != i])))
    return np.array(sorted(cols))


def fit_score(cols, tr, te, f):
    p, _, _ = fit_mlp(X[tr][:, cols], Y[tr], M[tr], args.epochs, seed=f)
    return score(p(X[te][:, cols]), Y[te], M[te])


def random_subsets(f, k, n_draws=3):
    r = np.random.default_rng(1000 * (f + 1) + k)  # independent of the data, so no leakage
    return [np.sort(r.choice(X.shape[1], size=k, replace=False)) for _ in range(n_draws)]


def average_scores(rs):
    """Mean of several score dicts (the 3 random draws) in the structure fit_score returns."""
    return {t: {"mae": float(np.mean([r[t]["mae"] for r in rs])), "nrmse": float(np.mean([r[t]["nrmse"] for r in rs])),
                "unit": rs[0][t]["unit"]} for t in TARGETS}


def controls_for_fold(f, tr, te, k):
    """The three controls for one fold and one k; returns {name: (subsets, score)}."""
    draws = random_subsets(f, k)
    rand = [fit_score(c, tr, te, f) for c in draws]
    qr_cols, bw_cols = qr_pivot_subset(tr, k), backward_ridge_subset(tr, k)
    return {"random": (draws, average_scores(rand), [summary(r) for r in rand]),
            "qr": ([qr_cols], fit_score(qr_cols, tr, te, f), None),
            "ridge": ([bw_cols], fit_score(bw_cols, tr, te, f), None)}


def table_row(rs):
    return {"summary_nrmse_mean": float(np.mean([summary(r) for r in rs])),
            "summary_nrmse_std": float(np.std([summary(r) for r in rs])),
            "targets": {t: {"mae": float(np.mean([r[t]["mae"] for r in rs])), "unit": rs[0][t]["unit"],
                            "nrmse": float(np.mean([r[t]["nrmse"] for r in rs]))} for t in SHOW}}


def md_table(table, names, header_first):
    unit0 = table[names[0]]["targets"]
    lines = [f"| {header_first} | summary error | " + " | ".join(f"{t} ({unit0[t]['unit'] or 'abs'})" for t in SHOW) + " |",
             "|---|---|" + "---|" * len(SHOW)]
    for n in names:
        lines.append(f"| {n} | {table[n]['summary_nrmse_mean']:.3f} ± {table[n]['summary_nrmse_std']:.3f} | "
                     + " | ".join(f"{table[n]['targets'][t]['mae']:.3g}" for t in SHOW) + " |")
    return lines


# ---------------------------------------------------------------- controls-only pieces and their merge
if args.merge:
    parts = [json.load(open(q)) for q in sorted(PARTS.glob("f*_k*.json"))]
    assert parts, f"no pieces in {PARTS}"
    ks = sorted({p["k"] for p in parts}, reverse=True)
    # Only folds for which every k finished, so that every row of the table is paired on the same folds.
    folds = sorted(f for f in {p["fold"] for p in parts} if all(any(p["fold"] == f and p["k"] == k for p in parts) for k in ks))
    parts = [p for p in parts if p["fold"] in folds]
    runs = {"all 24": []}
    for f in folds:
        runs["all 24"].append(next(p for p in parts if p["fold"] == f)["all24"])
    for k in ks:
        for key, label in (("perm", "permutation top"), ("random", "random (mean of 3 draws)"), ("qr", "QR-pivot"),
                           ("ridge", "backward ridge")):
            runs[f"{label} {k}"] = [p[key]["score"] for f in folds for p in parts if p["fold"] == f and p["k"] == k]
    table = {n: table_row(rs) for n, rs in runs.items()}
    names = list(runs)
    extra = {}
    for k in ks:
        ps = [p for p in parts if p["k"] == k]
        extra[str(k)] = {"random_draw_summaries": {str(p["fold"]): p["random"]["draw_summaries"] for p in ps},
                         "subsets": {str(p["fold"]): {key: [[NAMES[i] for i in c] for c in p[key]["subsets"]]
                                                      for key in ("perm", "random", "qr", "ridge")} for p in ps}}
    per_fold = {n: [summary(r) for r in rs] for n, rs in runs.items()}
    json.dump({"folds_run": folds, "epochs": parts[0]["epochs"], "runs": table, "per_fold_summary": per_fold,
               "subsets": extra}, open(OUT / "ipp1-inputs-controls.json", "w"), indent=1, allow_nan=False)
    lines = ["# Fewer inputs: controls for the permutation-ranked subsets (REQ-004)", "",
             f"Folds run: {', '.join(str(f) for f in folds)} of 5{'' if len(folds) == 5 else ' (partial)'}. One seed per cell, fold SD is about 40 % of the mean, "
             "so read differences under 10 to 15 % as noise. Every subset was chosen on the training discharges of its fold only; "
             "all rows of one fold use the same seed and the same test discharges, so the rows are paired. "
             f"Epochs {parts[0]['epochs']}. Summary error = mean relative error (RMSE / fold spread) over {len(SUMMARY)} targets, "
             "without the limiter point; lower is better. Columns after it are the mean absolute error in report units.", ""]
    lines += md_table(table, names, "inputs")
    lines += ["", "Summary error per fold (same order as the folds above):", "",
              "| inputs | " + " | ".join(f"fold {f}" for f in folds) + " |", "|---|" + "---|" * len(folds)]
    lines += [f"| {n} | " + " | ".join(f"{v:.3f}" for v in per_fold[n]) + " |" for n in names]
    lines += ["", "Reading: the permutation ranking is the importance of an input for the trained network, not information content. "
              "A random subset of the same size and a model-free QR-pivot or ridge-selected subset show how much of the "
              "top-k curve comes from the ranking method and how much from the number of inputs."]
    (OUT / "ipp1-inputs-controls.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0)

if args.controls_only:
    folds_all = group_folds(X, Y, G, 5)
    PARTS.mkdir(parents=True, exist_ok=True)
    for f in [int(v) for v in (args.only_folds or "0,1,2,3,4").split(",")]:
        tr, te = folds_all[f]
        predict, _, _ = fit_mlp(X[tr], Y[tr], M[tr], args.epochs, seed=f)
        all24 = score(predict(X[te]), Y[te], M[te])
        order, _ = permutation_order(predict, tr, f)
        for k in K_CTRL:
            perm_cols = np.sort(order[:k])
            perm = {"subsets": [perm_cols.tolist()], "score": fit_score(perm_cols, tr, te, f)}
            ctrl = controls_for_fold(f, tr, te, k)
            piece = {"fold": f, "k": k, "epochs": args.epochs, "all24": all24, "perm": perm}
            for key, (subs, sc, draws) in ctrl.items():
                piece[key] = {"subsets": [list(map(int, s)) for s in subs], "score": sc}
                if draws is not None:
                    piece[key]["draw_summaries"] = draws
            json.dump(piece, open(PARTS / f"f{f}_k{k}.json", "w"), allow_nan=False)
            print(f"fold {f} k {k}: all24 {summary(all24):.3f} perm {summary(perm['score']):.3f} "
                  f"random {summary(piece['random']['score']):.3f} qr {summary(piece['qr']['score']):.3f} "
                  f"ridge {summary(piece['ridge']['score']):.3f}", flush=True)
    sys.exit(0)

# ---------------------------------------------------------------- the full run
importance = np.zeros((args.folds, X.shape[1]))
runs = {}
chosen = {}
for f, (tr, te) in enumerate(group_folds(X, Y, G, args.folds)):
    predict, _, _ = fit_mlp(X[tr], Y[tr], M[tr], args.epochs, seed=f)
    order, importance[f] = permutation_order(predict, tr, f)
    runs.setdefault("all 24", []).append(score(predict(X[te]), Y[te], M[te]))
    for k in K_LIST:
        cols = np.sort(order[:k])
        runs.setdefault(f"top {k}", []).append(fit_score(cols, tr, te, f))
    for k in K_CTRL:
        for key, label in (("random", "random"), ("qr", "QR-pivot"), ("ridge", "backward ridge")):
            subs, sc, _ = controls_for_fold(f, tr, te, k)[key]
            runs.setdefault(f"{label} {k}", []).append(sc)
            chosen.setdefault(f"{label} {k}", []).append([[NAMES[i] for i in s] for s in subs])
    for name, cols in (("IPR only (16)", [i for i, c in enumerate(NAMES) if c.startswith("IPR")]),
                       ("FL only (8)", [i for i, c in enumerate(NAMES) if c.startswith("FL")])):
        runs.setdefault(name, []).append(fit_score(cols, tr, te, f))
    print(f"fold {f + 1}/{args.folds} done", flush=True)

imp = importance.mean(0)
table = {name: table_row(rs) for name, rs in runs.items()}
ranking = [NAMES[i] for i in np.argsort(-imp)]
json.dump({"folds": args.folds, "epochs": args.epochs, "inputs": NAMES, "permutation_importance": dict(zip(NAMES, imp.tolist())),
           "permutation_importance_per_fold": importance.tolist(), "ranking": ranking, "control_subsets": chosen,
           "runs": table}, open(OUT / "ipp1-inputs.json", "w"), indent=1, allow_nan=False)

order_names = ["all 24"]
for k in K_LIST:
    order_names.append(f"top {k}")
    if k in K_CTRL:
        order_names += [f"random {k}", f"QR-pivot {k}", f"backward ridge {k}"]
order_names += ["IPR only (16)", "FL only (8)"]
lines = ["# Fewer inputs: accuracy against the number of inputs (REQ-004)", "",
         f"{args.folds} folds by discharge; summary = mean of the relative error (RMSE / spread) over {len(SUMMARY)} targets, "
         "without the limiter point; lower is better. 'top k' = the k inputs ranked by permutation importance on training rows only; "
         "the sensor set is chosen inside each fold, so a row estimates the procedure, not one fixed set of sensors. "
         "Controls for k in " + ", ".join(map(str, K_CTRL)) + ", also chosen on the training discharges of each fold only: "
         "'random k' = a random subset of the same size (mean of 3 draws), 'QR-pivot k' = columns picked by QR with column "
         "pivoting of the standardised inputs (model free), 'backward ridge k' = greedy backward elimination with a ridge criterion. "
         "One seed per cell; fold SD is large, so differences under 10 to 15 % are noise.", ""]
lines += md_table(table, order_names, "inputs")
lines += ["", "Ranking by permutation importance (most important first): " + ", ".join(ranking),
          "", "This ranking is the importance of an input for the trained network, not information content: the inputs are "
          "collinear, so permuting one column creates rows off the data manifold. Do not read it as 'the important sensors'; "
          "the evidence for the number of inputs is the retrain curve and its controls above."]
(OUT / "ipp1-inputs.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False, "font.size": 8})
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
ks = [24] + K_LIST
vals = [table["all 24" if k == 24 else f"top {k}"]["summary_nrmse_mean"] for k in ks]
errs = [table["all 24" if k == 24 else f"top {k}"]["summary_nrmse_std"] for k in ks]
ax[0].errorbar(ks, vals, yerr=errs, marker="o", color="#5b7cff", capsize=2, label="top k by permutation importance")
for label, c, mk in (("random", "#8d99ae", "s"), ("QR-pivot", "#2a9d8f", "^"), ("backward ridge", "#e9c46a", "D")):
    ax[0].plot(K_CTRL, [table[f"{label} {k}"]["summary_nrmse_mean"] for k in K_CTRL], marker=mk, ls=":", color=c, label=f"{label} k")
for n, c in (("IPR only (16)", "#e07a5f"), ("FL only (8)", "#3d405b")):
    ax[0].axhline(table[n]["summary_nrmse_mean"], color=c, ls="--", lw=1, label=n)
ax[0].set_xlabel("počet použitých vstupů")
ax[0].set_ylabel("průměrná relativní chyba")
ax[0].set_yscale("log")
ax[0].legend(fontsize=6)
ax[0].set_title("Kolik vstupů stačí (a kontroly výběru)")
o = np.argsort(-imp)
ax[1].bar(range(len(o)), imp[o], color=["#e07a5f" if NAMES[i].startswith("FL") else "#5b7cff" for i in o])
ax[1].set_xticks(range(len(o)))
ax[1].set_xticklabels([NAMES[i] for i in o], rotation=90)
ax[1].set_title("Důležitost pro naučenou síť, ne obsah informace (modře IPR, oranžově FL)")
fig.tight_layout()
fig.savefig(OUT / "ipp1-inputs.png")
print("\n".join(lines))
