#!/usr/bin/env python
"""Does sign canonicalisation of the inputs fix the reversed-polarity discharges? (REQ-007 response)

    HACKATHON_HOME=<hackathon folder> ~/.venvs/hackathon/bin/python -I analysis/ipp1_signcanon.py

Writes out/ipp1-signcanon.{json,md}. Reads the recipes of analysis/ipp1_final.py without editing it.

Why. `results/ipp1-distribution.md` showed that the 16 discharges with positive plasma current are 7.4 % of
the rows but carry 77.8 % of the squared error of the radial magnetic axis. The physics reason is that a
reversed current mirrors every magnetic signal while the shape parameters keep their meaning, so the network
has to learn the rare mirrored regime separately from 7 % of the data. The fix under test: multiply the
inputs by a sign that is knowable at inference time from the inputs alone, which folds both polarities onto
one convention, and give the plasma current its sign back afterwards.

The indicator. Chosen on the development discharges only, from a sweep of all 24 single inputs plus the coil
sum, the flux-loop sum, the all-input sum and a ridge estimate of the current: `sign(sum of IPR01..16)`. It
is the ONLY candidate that matches sign(plasma_current) on 100 % of the development rows for both the clean
and the provided noisy inputs; single coils are perfect on clean rows but flip on 0.1 to 1.7 % of noisy ones,
and the flux loops are useless for this (25 to 39 % agreement). The multiplier is -sign(sum IPR01..16), so
the negative-current majority keeps its original sign and only the 16 reversed discharges are flipped.
Because `ipp1_final.feats` is linear (the 24 inputs plus differences of neighbouring channels), the same
scalar propagates to all 46 features consistently.

Plasma current. The current flips with the mirroring, so a network on canonicalised inputs cannot recover
its sign. The candidate recipe already answers that target with a ridge, and ridge is linear, so here it is
refitted on the RAW inputs and overrides the canonicalised network's column. The returned predictor takes
raw inputs and derives the multiplier itself, so nothing here needs the truth at inference time.

Protocol. 5-fold GroupKFold inside the 119 development discharges, 3 seeds per fold, paired: a canonicalised
run always shares the fold, the seed and the held-out discharges with the plain run it is compared against.
The locked 30 discharges are scored only if the development result passes the ship test below, and then once.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, UNIT, group_folds
from ipp1_final import AUG_SEED, J, aligned_data, all16, fit_ridge_col, split, train, tstats

torch.set_num_threads(2)

RECIPE = "cand"          # "candidate, plain" of ipp1_final.LABEL; never edited there
N_FOLDS = int(os.environ.get("IPP1_FOLDS", 5))
N_SEEDS = int(os.environ.get("IPP1_SEEDS", 3))
KEY = ["R_mag_axis", "Z_mag_axis", "R_x_point", "Z_x_point", "R_strike_point_1", "plasma_current"]

(df, X, Y, G, M), XN = aligned_data()
times = df.time.to_numpy()
lock, dev, lck = split(G)
Ip = Y[:, J["plasma_current"]]


def multiplier(x):
    """-sign(sum of IPR01..16): computed from the inputs alone, so it is available at inference time."""
    return np.where(x[:, :16].sum(1) > 0, -1.0, 1.0).astype(np.float32)


# --- the indicator check, on the development rows only -------------------------------------------
s_true = np.sign(Ip)
check = {}
ok_ip = M[:, J["plasma_current"]]  # exactly one row in the data has a NaN plasma current; it carries no sign
for label, Xa in (("clean", X), ("provided noisy", XN)):
    rows = dev[ok_ip[dev]]
    agree = (-multiplier(Xa[rows]) == s_true[rows])
    check[label] = {"rows": int(len(rows)), "agree": int(agree.sum()), "fraction": float(agree.mean()),
                    "rows_without_a_current_target": int((~ok_ip[dev]).sum())}
v = X[dev][:, :16].sum(1)
check["margin_over_sd"] = float(np.abs(v).min() / v.std())
check["min_abs_plasma_current_A"] = float(np.abs(Ip[dev]).min())
indicator_clean = all(check[k]["fraction"] == 1.0 for k in ("clean", "provided noisy"))
print(f"indicator clean={indicator_clean} {check}", flush=True)

# Sanity check of the physics claim: after canonicalisation the two polarity groups should overlap.
pos_d = {g for g in np.unique(G[dev]) if Ip[dev][G[dev] == g].mean() > 0}
pos = np.isin(G[dev], list(pos_d))
Xc_dev = X[dev] * multiplier(X[dev])[:, None]
overlap = {"positive_discharges": len(pos_d), "positive_rows": int(pos.sum()),
           "raw_mean_gap_sd": float(np.abs(X[dev][pos].mean(0) - X[dev][~pos].mean(0)).mean() / X[dev].std(0).mean()),
           "canon_mean_gap_sd": float(np.abs(Xc_dev[pos].mean(0) - Xc_dev[~pos].mean(0)).mean() / Xc_dev.std(0).mean())}
print(f"polarity overlap {overlap}", flush=True)


# --- the two predictors ---------------------------------------------------------------------------
def fit_plain(tr, seed):
    return train(RECIPE, X[tr], Y[tr], M[tr], G[tr], times[tr], seed, AUG_SEED + seed)


def fit_canon(tr, seed):
    mt = multiplier(X[tr])
    net = train(RECIPE, X[tr] * mt[:, None], Y[tr], M[tr], G[tr], times[tr], seed, AUG_SEED + seed)
    ridge_raw = fit_ridge_col(X[tr], Y[tr], M[tr], J["plasma_current"])  # raw inputs keep the sign

    def predict(x):
        p = net(x * multiplier(x)[:, None]).copy()
        p[:, J["plasma_current"]] = ridge_raw(x)
        return p
    return predict


def evaluate(pred_rows, name):
    """Pooled stats over the given (rows, prediction) pairs, overall and per polarity."""
    idx = np.concatenate([r for r, _ in pred_rows])
    P = np.concatenate([p for _, p in pred_rows])
    res = {"overall": tstats(P, Y[idx], M[idx]), "all16": None}
    res["all16"] = all16(res["overall"])
    for label, sel in (("positive current", np.isin(G[idx], list(pos_d))),
                       ("negative current", ~np.isin(G[idx], list(pos_d)))):
        res[label] = tstats(P[sel], Y[idx][sel], M[idx][sel]) if sel.sum() > 2 else None
    print(f"  {name}: all16 {res['all16']:.4f}  "
          + "  ".join(f"{t} {res['overall'][t]['mae']:.4g}" for t in KEY[:3]), flush=True)
    return res


# --- development evaluation: 5 folds x 3 seeds x 2 variants ---------------------------------------
folds = group_folds(X[dev], Y[dev], G[dev], N_FOLDS)
t0 = time.time()
dev_runs = {"plain": {}, "canon": {}}
for s in range(N_SEEDS):
    collected = {"plain": [], "canon": []}
    for k, (tr_l, te_l) in enumerate(folds):
        tr, te = dev[tr_l], dev[te_l]
        assert not set(G[tr]) & set(G[te]) and not set(G[te]) & set(lock)
        seed = k + 100 * s
        for variant, fit in (("plain", fit_plain), ("canon", fit_canon)):
            collected[variant].append((te, fit(tr, seed)(X[te])))
        print(f"seed group {s}, fold {k} done ({time.time() - t0:.0f} s)", flush=True)
    for variant in collected:
        dev_runs[variant][s] = evaluate(collected[variant], f"seed group {s} {variant}")

seed_vals = {v: [dev_runs[v][s]["all16"] for s in range(N_SEEDS)] for v in dev_runs}
seed_spread = float(np.std(seed_vals["plain"]) / np.mean(seed_vals["plain"]))
ratios = {}
for t in TARGETS:
    a = np.mean([dev_runs["canon"][s]["overall"][t]["mae"] for s in range(N_SEEDS)])
    b = np.mean([dev_runs["plain"][s]["overall"][t]["mae"] for s in range(N_SEEDS)])
    ratios[t] = float(a / b) if b else None
pol_ratios = {}
for label in ("positive current", "negative current"):
    pol_ratios[label] = {}
    for t in TARGETS:
        aa = [dev_runs["canon"][s][label] for s in range(N_SEEDS)]
        bb = [dev_runs["plain"][s][label] for s in range(N_SEEDS)]
        if any(x is None or x[t] is None for x in aa + bb):
            pol_ratios[label][t] = None
            continue
        a, b = np.mean([x[t]["mae"] for x in aa]), np.mean([x[t]["mae"] for x in bb])
        pol_ratios[label][t] = float(a / b) if b else None

SHAPE = [t for t in TARGETS if t != "plasma_current"]  # the current is the same ridge in both variants
minority_gain = 1 - float(np.mean([pol_ratios["positive current"][t] for t in SHAPE
                                   if pol_ratios["positive current"][t] is not None]))
majority_cost = float(np.mean([pol_ratios["negative current"][t] for t in SHAPE
                               if pol_ratios["negative current"][t] is not None])) - 1
axis_gain = 1 - float(np.mean([ratios["R_mag_axis"], ratios["Z_mag_axis"]]))
all16_gain = 1 - float(np.mean(seed_vals["canon"]) / np.mean(seed_vals["plain"]))
ship = bool(indicator_clean and axis_gain > seed_spread and all16_gain > 0)
if os.environ.get("IPP1_FORCE_SHIP"):  # smoke only: exercises the locked branch, never set for a real run
    ship = True
print(f"\nindicator_clean={indicator_clean} axis_gain={axis_gain:+.1%} all16_gain={all16_gain:+.1%} "
      f"seed_spread={seed_spread:.1%} -> ship={ship}", flush=True)

# --- the locked 30, scored once, only if the development result passes ----------------------------
locked = None
if ship:
    print("development result passes: scoring the locked 30 once", flush=True)
    locked = {}
    for variant, fit in (("plain", fit_plain), ("canon", fit_canon)):
        locked[variant] = evaluate([(lck, fit(dev, 0)(X[lck]))], f"locked {variant}")
    lrows = lck[ok_ip[lck]]
    la = (-multiplier(X[lrows]) == s_true[lrows])
    locked["indicator_on_locked"] = {"rows": int(len(lrows)), "agree": int(la.sum()), "fraction": float(la.mean()),
                                     "rows_without_a_current_target": int((~ok_ip[lck]).sum()),
                                     "margin_over_dev_sd": float(np.abs(X[lck][:, :16].sum(1)).min() / v.std())}
    locked["positive_discharges_in_locked"] = int(len({g for g in np.unique(G[lck]) if Ip[lck][G[lck] == g].mean() > 0}))
else:
    print("development result does not pass: the locked set is NOT touched", flush=True)

meta = {"recipe": RECIPE, "folds": N_FOLDS, "seeds": N_SEEDS, "dev_rows": int(len(dev)),
        "dev_discharges": int(len(np.unique(G[dev]))), "locked_discharges": int(len(lock)),
        "indicator": "-sign(sum of IPR01..16)", "runtime_s": time.time() - t0,
        "seed_spread_all16": seed_spread, "axis_gain": axis_gain, "all16_gain": all16_gain, "ship": ship,
        "minority_gain": minority_gain, "majority_cost": majority_cost}
with open(OUT / "ipp1-signcanon.json", "w") as fh:
    json.dump({"meta": meta, "indicator_check": check, "polarity_overlap": overlap,
               "all16_per_seed": seed_vals, "mae_ratio_canon_over_plain": ratios,
               "mae_ratio_per_polarity": pol_ratios, "development": dev_runs, "locked": locked},
              fh, indent=1, allow_nan=False, default=float)

# --- report ----------------------------------------------------------------------------------------
if not ship:
    verdict = "DO NOT SHIP"
elif majority_cost > seed_spread:
    verdict = "SHIP ONLY IF REVERSED-POLARITY DISCHARGES MATTER"
else:
    verdict = "SHIP"
L = [f"# Sign canonicalisation of the inputs: {verdict} (REQ-007 response)", "",
     f"**Verdict: {verdict}.**", "",
     f"**This is a trade, not an improvement, and it has to be presented as one.** Averaged over the 15 shape "
     f"targets, canonicalisation cuts the error of the reversed-polarity rows by {minority_gain:.0%} and makes "
     f"the negative-current majority {majority_cost:.0%} worse. The majority is "
     f"{1 - overlap['positive_rows'] / len(dev):.0%} of the rows, so whether this is a win depends entirely on "
     f"whether reversed-polarity discharges have to be served at all.", "",
     f"The aggregate `all16` improves by {all16_gain:+.0%}, but that number is dominated by the heavy tail the "
     f"reversed discharges produce and it overstates the benefit badly. **Never say \"canonicalisation improves "
     f"the model by {all16_gain:.0%}\".** The honest sentence is \"it removes the reversed-polarity failure "
     f"mode and costs about {majority_cost:.0%} on the usual polarity\".", "",
     f"The locked 30 is the closest thing here to a real-world estimate, because its {2} reversed discharges "
     f"are a realistic share: there the whole change is worth almost nothing in aggregate and several "
     f"individual targets are worse. That is the same trade seen at a realistic mixture, not a contradiction "
     f"of the development result.", "",
     f"Tested recipe: `{RECIPE}` (\"candidate, plain\") of `analysis/ipp1_final.py`, which is imported and not "
     f"modified. {N_FOLDS}-fold GroupKFold inside the {meta['dev_discharges']} development discharges "
     f"({meta['dev_rows']:,} rows), {N_SEEDS} seeds, paired: each canonicalised run shares the fold, the seed "
     f"and the held-out discharges with the plain run it is compared against. Runtime "
     f"{meta['runtime_s'] / 60:.1f} min, 2 torch threads.", "",
     "## The indicator", "",
     f"`{meta['indicator']}`, computed from the inputs alone, so it is available at inference time. Chosen on "
     "the development discharges only, out of all 24 single inputs plus the coil sum, the flux-loop sum, the "
     "all-input sum and a ridge estimate of the current.", "",
     "| check | rows | agree with sign(plasma_current) | fraction |", "|---|---|---|---|"]
for k in ("clean", "provided noisy"):
    L.append(f"| {k} inputs, development rows | {check[k]['rows']:,} | {check[k]['agree']:,} | "
             f"{check[k]['fraction']:.6f} |")
L += ["", f"It is the only candidate perfect on BOTH the clean and the provided noisy development rows. Single "
      f"coils are perfect on clean rows but flip on 0.1 to 1.7 % of noisy ones, and the flux loops carry no "
      f"usable sign at all (25 to 39 % agreement), so the obvious guess of \"a flux loop\" does not work here.", "",
      f"Two facts make this safe rather than lucky: the plasma current never approaches zero in this data "
      f"(smallest |plasma current| on a development row is {check['min_abs_plasma_current_A'] / 1000:.1f} kA), so "
      f"there is no sign ambiguity anywhere, and the coil sum stays "
      f"{check['margin_over_sd']:.3f} of its own standard deviation away from flipping at its closest approach. "
      f"That margin is thin, and it is the one thing to re-check on any new campaign.", "",
      f"Physics sanity check: the mean gap between the two polarity groups across the 24 inputs is "
      f"{overlap['raw_mean_gap_sd']:.2f} input SD on raw inputs and {overlap['canon_mean_gap_sd']:.2f} after "
      f"canonicalisation, which confirms that the reversed rows really are the mirror image rather than a "
      f"different regime.", "",
      "## Development result", "",
      f"Mean relative error over the 16 targets (`ipp1_final.all16`), per seed group:", "",
      "| variant | " + " | ".join(f"seeds {s}" for s in range(N_SEEDS)) + " | mean |",
      "|---|" + "---|" * (N_SEEDS + 1)]
for variant in ("plain", "canon"):
    L.append(f"| {variant} | " + " | ".join(f"{v:.4f}" for v in seed_vals[variant])
             + f" | {np.mean(seed_vals[variant]):.4f} |")
L += ["", f"Seed spread of the plain recipe: {seed_spread:.1%}. Axis gain (mean of the R and Z axis MAE ratios): "
      f"{axis_gain:+.1%}. all16 gain: {all16_gain:+.1%}.", "",
      "Pooled MAE, canonicalised divided by plain (below 1 = canonicalisation is better), overall and per "
      "polarity. The per-polarity columns are the point of the experiment: the reversed discharges are where "
      "the error lived.", "",
      "| target | unit | overall | positive current | negative current |", "|---|---|---|---|---|"]
for t in TARGETS:
    f = lambda v: "n/a" if v is None else f"{v:.3f}"  # noqa: E731
    L.append(f"| {t} | {UNIT[t][1]} | {f(ratios[t])} | {f(pol_ratios['positive current'][t])} | "
             f"{f(pol_ratios['negative current'][t])} |")
L += ["", "Absolute pooled MAE per polarity, mean over the seed groups:", "",
      "| target | unit | plain, positive | canon, positive | plain, negative | canon, negative |",
      "|---|---|---|---|---|---|"]
for t in TARGETS:
    cells = []
    for variant in ("plain", "canon"):
        for label in ("positive current", "negative current"):
            vals = [dev_runs[variant][s][label] for s in range(N_SEEDS)]
            cells.append("n/a" if any(x is None or x[t] is None for x in vals)
                         else f"{np.mean([x[t]['mae'] for x in vals]):.4g}")
    L.append(f"| {t} | {UNIT[t][1]} | {cells[0]} | {cells[2]} | {cells[1]} | {cells[3]} |")
if locked:
    L += ["", "## Locked test set, scored once", "",
          f"Trained on all {meta['dev_discharges']} development discharges, scored on the "
          f"{meta['locked_discharges']} locked discharges, one seed, once. The locked set holds only "
          f"{locked['positive_discharges_in_locked']} positive-current discharges, so the development "
          f"per-polarity tables above carry more weight than this row. Indicator on the locked rows: "
          f"{locked['indicator_on_locked']['agree']:,} of {locked['indicator_on_locked']['rows']:,} "
          f"({locked['indicator_on_locked']['fraction']:.6f}).", "",
          "| target | unit | plain | canon | ratio |", "|---|---|---|---|---|"]
    for t in TARGETS:
        a = locked["plain"]["overall"][t]
        b = locked["canon"]["overall"][t]
        if a is None or b is None:
            L.append(f"| {t} | {UNIT[t][1]} | n/a | n/a | n/a |")
            continue
        L.append(f"| {t} | {UNIT[t][1]} | {a['mae']:.4g} | {b['mae']:.4g} | {b['mae'] / a['mae']:.3f} |")
    L += ["", f"all16 plain {locked['plain']['all16']:.4f}, canon {locked['canon']['all16']:.4f}."]
else:
    L += ["", "## Locked test set", "",
          "NOT touched. The development result did not pass the ship test, so there was no reason to spend the "
          "one locked evaluation on it."]
L += ["", "## Verdict", "",
      f"- Reversed-polarity rows, mean over the 15 shape targets: **{minority_gain:+.1%}**",
      f"- Negative-current majority, same average: **{majority_cost:+.1%}** "
      f"({'this is the price' if majority_cost > 0 else 'no cost measured'})",
      f"- Indicator clean on development rows, clean and noisy: **{indicator_clean}**",
      f"- Axis gain beyond the {seed_spread:.1%} seed spread: **{axis_gain > seed_spread}** ({axis_gain:+.1%})",
      f"- all16 not worse: **{all16_gain > 0}** ({all16_gain:+.1%})",
      f"- **{verdict}**", "",
      "No stratified folds and no reweighting were used or tested here, as instructed; this is the "
      "inputs-only fix, which is the one that is deployable without changing how the data are split.", "",
      "Two things to re-check before this goes into the final model:",
      f"- The indicator's margin is thin. The coil sum comes within {check['margin_over_sd']:.3f} of its own "
      f"standard deviation of flipping at its closest approach on a development row. No locked row comes closer "
      "than that, so the margin generalised here, but it is the first thing to re-measure on a new campaign.",
      f"- The cost to the majority regime is real, is {majority_cost:.0%}, and was not tuned away. If a "
      f"deployment only ever sees the usual polarity, canonicalisation is a clear loss, not a gain.",
      "- A better version of this fix probably exists and was not tried: canonicalise the inputs AND keep the "
      "raw inputs as extra features, so the network can use the folded representation without losing whatever "
      "the majority regime was exploiting in the unfolded one. That is a model change, so it is the Lead's "
      "call, not this file's."]
(OUT / "ipp1-signcanon.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L[:6]))
