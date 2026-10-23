#!/usr/bin/env python
"""Error against the uneven distribution of the data (REQ-007), from the out-of-fold predictions.

    HACKATHON_HOME=<hackathon folder> ~/.venvs/hackathon/bin/python -I analysis/ipp1_distribution.py

Needs out/ipp1-predictions.csv (analysis/ipp1_oof.py). Writes out/ipp1-distribution.{json,md}.
Nothing is trained here: the predictions are already out-of-fold, so every number below is pooled over
rows the network did not see in training, and no split is repeated.

The headline MAE of the baseline is a row-weighted average over a very uneven data set: 44 % of the rows
are limited, only 16 of 149 discharges have positive plasma current, and the equilibrium at the very start
and end of a discharge is least well defined. This script cuts the same out-of-fold error four ways:

1. configuration: limited rows against diverted rows (the truth of is_limited, not the prediction);
2. current polarity: discharges whose mean true plasma current is positive against the rest, by whole discharge;
3. value quantile: quintiles of the TRUE value of each target, among the rows where that target exists;
4. position in the discharge: the first 2 %, the middle and the last 2 % of the relative time.

Metrics per group are pooled (not averaged over folds) and follow ipp1_common.score_extended exactly:
MAE, median, RMSE, p95, p99 and max of the absolute error in report units, plus nRMSE and R2 against the
spread of the truth inside that group. `share_of_sq_error` is the group's share of the total squared error
of that target, next to its share of the rows: a group far above its row share is where the error lives.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, UNIT, load, score_extended

torch.set_num_threads(2)

MAIN = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity",
        "R_x_point", "Z_x_point", "R_strike_point_1", "R_limiter", "Z_limiter"]
N_QUANTILES = 5

df, X, Y, G, M = load()
pr = pd.read_csv(OUT / "ipp1-predictions.csv")
assert np.array_equal(pr.discharge.values, df.discharge.values) and np.allclose(pr.time.values, df.time.values), \
    "out/ipp1-predictions.csv is not row-aligned with the data; rerun analysis/ipp1_oof.py"
P = pr[[f"{t}_pred" for t in TARGETS]].values

ERR = P - Y  # NaN where the target does not exist; every use is masked by M


def pooled(rows):
    """score_extended restricted to `rows`, with None for a target that has no row in the group.

    The formulas are copied from ipp1_common.score_extended so the measurement matches the other lanes;
    the assertion below checks that on the full row set this returns exactly score_extended's output.
    """
    res = {}
    for j, t in enumerate(TARGETS):
        k = M[:, j] & rows
        n = int(k.sum())
        if n == 0:
            res[t] = None
            continue
        e = P[k, j].astype(np.float64) - Y[k, j]
        a = np.abs(e) * UNIT[t][0]
        y = Y[k, j]
        spread = y.std()
        res[t] = {"n": n, "mae": float(a.mean()), "median": float(np.median(a)),
                  "rmse": float(np.sqrt((a ** 2).mean())), "p95": float(np.percentile(a, 95)),
                  "p99": float(np.percentile(a, 99)), "max": float(a.max()), "unit": UNIT[t][1],
                  "nrmse": None if spread == 0 else float(np.sqrt((e ** 2).mean()) / spread),
                  "r2": None if spread == 0 else float(1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum()),
                  "share_of_rows": n / int(M[:, j].sum()),
                  "share_of_sq_error": float((e ** 2).sum() / np.nansum(ERR[M[:, j], j].astype(np.float64) ** 2))}
    return res


all_rows = np.ones(len(df), dtype=bool)
_mine, _theirs = pooled(all_rows), score_extended(P, Y, M)
for t in TARGETS:  # the whole point of REQ-007 is that these overall numbers hide the groups below
    for key, v in _theirs[t].items():
        assert np.isclose(_mine[t][key], v) if isinstance(v, float) else _mine[t][key] == v, f"{t}.{key} differs"

# --- the four cuts -------------------------------------------------------------------------------
limited = Y[:, TARGETS.index("is_limited")] > 0.5  # truth, not the prediction
cur = Y[:, TARGETS.index("plasma_current")]
per_discharge_sign = pd.Series(cur).groupby(df.discharge.values).mean()
positive_discharges = set(per_discharge_sign.index[per_discharge_sign > 0])
positive = np.isin(df.discharge.values, list(positive_discharges))
t_rel = df.time.values
edges = {"first 2 %": t_rel < 0.02, "middle 96 %": (t_rel >= 0.02) & (t_rel <= 0.98), "last 2 %": t_rel > 0.98}

cuts = {
    "configuration": {"limited": limited, "diverted": ~limited},
    "polarity": {"positive current": positive, "negative current": ~positive},
    "position in discharge": edges,
}
result = {name: {label: pooled(rows) for label, rows in groups.items()} for name, groups in cuts.items()}

# Quantiles of the true value of each target, among the rows where that target exists.
quantiles = {}
for t in TARGETS:
    j = TARGETS.index(t)
    k = M[:, j]
    y = Y[k, j]
    qs = np.quantile(y, np.linspace(0, 1, N_QUANTILES + 1))
    qs[-1] = np.inf  # keep the maximum inside the last bin
    groups = {}
    for i in range(N_QUANTILES):
        rows = np.zeros(len(df), dtype=bool)
        idx = np.where(k)[0]
        sel = (y >= qs[i]) & (y < qs[i + 1]) if i < N_QUANTILES - 1 else (y >= qs[i])
        rows[idx[sel]] = True
        lo, hi = float(qs[i]), (float(y.max()) if not np.isfinite(qs[i + 1]) else float(qs[i + 1]))
        groups[f"Q{i + 1}"] = {"range": [lo, hi], **(pooled(rows)[t] or {"n": 0})}
    quantiles[t] = groups

meta = {"rows": int(len(df)), "discharges": int(df.discharge.nunique()),
        "limited_rows": float(limited.mean()), "positive_current_discharges": int(len(positive_discharges)),
        "positive_current_rows": float(positive.mean()),
        "rows_first_2_pct": int(edges["first 2 %"].sum()), "rows_last_2_pct": int(edges["last 2 %"].sum()),
        "source": "out/ipp1-predictions.csv (analysis/ipp1_oof.py, 5 folds by discharge)"}
with open(OUT / "ipp1-distribution.json", "w") as fh:
    json.dump({"meta": meta, "overall": _mine, "cuts": result, "value_quantiles": quantiles}, fh, indent=1,
              allow_nan=False)

# --- report --------------------------------------------------------------------------------------
L = ["# Error against the uneven distribution of the data (REQ-007)", "",
     f"Pooled over the {meta['rows']:,} out-of-fold rows of {meta['discharges']} discharges "
     f"(`{meta['source']}`); no model is trained here. {meta['limited_rows']:.1%} of the rows are limited, "
     f"{meta['positive_current_discharges']} of {meta['discharges']} discharges have positive plasma current "
     f"({meta['positive_current_rows']:.1%} of the rows), {meta['rows_first_2_pct']:,} rows lie in the first 2 % "
     f"and {meta['rows_last_2_pct']:,} in the last 2 % of the relative discharge time.", "",
     "All errors are absolute errors in the report unit of the target. `rows` is the group's share of the rows "
     "of that target and `sq err` its share of that target's total squared error: where `sq err` is far above "
     "`rows`, a minority of the data carries the error. Metrics follow `ipp1_common.score_extended` (the script "
     "asserts this on the full row set), so they are comparable with the other reports. `n/a` means the group "
     "has no row of that target, which is expected: the X-point and the strike points exist only in diverted "
     "rows, the limiter point only in limited rows.", ""]


def table(groups, title, note=""):
    out = [f"## {title}", ""]
    if note:
        out += [note, ""]
    labels = list(groups)
    out += ["| target | unit | " + " | ".join(f"MAE {g} | p99 {g} | rows {g} | sq err {g}" for g in labels) + " |",
            "|---|---|" + "---|" * (4 * len(labels))]
    for t in TARGETS:
        cells = []
        for g in labels:
            r = groups[g][t]
            cells.append("n/a | n/a | n/a | n/a" if r is None else
                         f"{r['mae']:.3g} | {r['p99']:.3g} | {r['share_of_rows']:.1%} | {r['share_of_sq_error']:.1%}")
        out.append(f"| {t} | {UNIT[t][1]} | " + " | ".join(cells) + " |")
    return out + [""]


L += ["## Overall, for reference", "",
      "| target | unit | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 | n |", "|---|---|" + "---|" * 9]
for t in TARGETS:
    r = _mine[t]
    L.append(f"| {t} | {r['unit']} | {r['mae']:.3g} | {r['median']:.3g} | {r['rmse']:.3g} | {r['p95']:.3g} | "
             f"{r['p99']:.3g} | {r['max']:.3g} | {r['nrmse']:.3g} | {r['r2']:.4g} | {r['n']:,} |")
L += [""]
L += table(result["configuration"], "By configuration (limited against diverted)",
           "Split by the truth of `is_limited`. The limited rows are the minority and the harder case.")
L += table(result["polarity"], "By current polarity",
           f"Split by whole discharges on the sign of the mean true plasma current: "
           f"{meta['positive_current_discharges']} of {meta['discharges']} discharges are positive. The folds are "
           "not stratified on polarity, so these few discharges are also unevenly spread over the folds.")
L += table(result["position in discharge"], "By position in the discharge",
           "The first and last 2 % of the relative time, against the middle. This is where the equilibrium "
           "reconstruction itself is least well defined.")

L += ["## By value quantile of the target", "",
      f"Quintiles of the TRUE value of each target, over the rows where that target exists. `range` is the "
      f"quintile edge in the report unit. A target whose error grows towards one edge is a target whose rare "
      f"values are predicted worse, which is the point of REQ-007. Shown for the {len(MAIN)} main targets; "
      f"all 16 are in `out/ipp1-distribution.json`.", ""]
for t in MAIN:
    scale, unit = UNIT[t]
    L += [f"### {t} ({unit})" if unit else f"### {t}", "",
          "| quintile | range of the true value | n | MAE | median | p95 | p99 | max | rows | sq err |",
          "|---|---|" + "---|" * 8]
    for q, r in quantiles[t].items():
        if not r.get("n"):
            L.append(f"| {q} | n/a | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        lo, hi = r["range"]
        L.append(f"| {q} | {lo * scale:.4g} to {hi * scale:.4g} | {r['n']:,} | {r['mae']:.3g} | {r['median']:.3g} | "
                 f"{r['p95']:.3g} | {r['p99']:.3g} | {r['max']:.3g} | {r['share_of_rows']:.1%} | "
                 f"{r['share_of_sq_error']:.1%} |")
    L += [""]

(OUT / "ipp1-distribution.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
