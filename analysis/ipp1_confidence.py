#!/usr/bin/env python
"""The complete per-target confidence table (docs/internal/bonus-gaps.md, item A). Nothing is trained: it reads out-of-fold predictions that already exist.

Sources
  baseline, 31 targets   out/ipp1-predictions-full.csv (analysis/ipp1_oof_full.py): out-of-fold predictions of the BASIC network for all 31 targets, 5 random group folds over all 149 discharges
  shipped model, 16      out/ipp1-final-cache/ of ipp1_final.py: recipe `cand` on the 119 development discharges (5-fold cross-validation inside them) and on the 30 locked ones (trained on the 119),
                         read from the cache, never re-scored; the baseline of the same protocol (`base`) next to it
Per target: MAE, median, p95 and p99 of the absolute error pooled over rows, a 95 % percentile interval of the MAE from 1,000 resamples of WHOLE discharges, and the share of discharges whose
mean error is under a stated tolerance (two tolerances per target: tight and loose). Slices: reversed (positive) plasma current, limited against diverted rows (the truth of is_limited), first and last 2 %
of the relative time of the discharge.

    HACKATHON_HOME=... nice -n 10 ~/.venvs/hackathon/bin/python -I analysis/ipp1_confidence.py      writes results/ipp1-confidence.md and out/ipp1-confidence.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_final as F
from ipp1_common import DATA, OUT, ROOT

N_BOOT, SEED = 1000, 20261024
FULL = OUT / "ipp1-predictions-full.csv"
SLICE_TARGETS = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "R_x_point", "R_strike_point_1", "R_limiter", "Z_limiter"]


def unit_of(t):
    """(factor to the report unit, unit, tight tolerance, loose tolerance) in report units."""
    if t in F.UNIT:
        scale, u = F.UNIT[t]
    elif t.startswith(("R_", "Z_")) or t == "a":
        scale, u = 1000.0, "mm"
    else:
        scale, u = 1.0, ""
    tight, loose = {"mm": (1.0, 5.0), "kA": (1.0, 5.0), "": (0.01, 0.05)}[u]
    return scale, u, tight, loose


class Scorer:
    """Whole-discharge bootstrap and the per-discharge shares for one set of rows (predictions, truth, mask, discharge ids)."""

    def __init__(self, groups):
        self.ids, self.inv = np.unique(groups, return_inverse=True)
        rng = np.random.RandomState(SEED)
        self.counts = np.stack([np.bincount(rng.randint(0, len(self.ids), len(self.ids)), minlength=len(self.ids)) for _ in range(N_BOOT)]).astype(np.float64)

    def score(self, pred, y, m, t, rows=None):
        scale, unit, tight, loose = unit_of(t)
        k = m if rows is None else (m & rows)
        e = np.where(k, np.abs(pred - y), 0.0).astype(np.float64) * scale
        sa = np.bincount(self.inv, weights=e, minlength=len(self.ids))
        ct = np.bincount(self.inv, weights=k.astype(float), minlength=len(self.ids))
        with np.errstate(invalid="ignore", divide="ignore"):
            boot = (self.counts @ sa) / (self.counts @ ct)
            per = sa[ct > 0] / ct[ct > 0]
        a = e[k]
        return {"n": int(k.sum()), "discharges": int((ct > 0).sum()), "mae": float(sa.sum() / ct.sum()), "lo": float(np.nanpercentile(boot, 2.5)), "hi": float(np.nanpercentile(boot, 97.5)),
                "median": float(np.median(a)), "p95": float(np.percentile(a, 95)), "p99": float(np.percentile(a, 99)),
                "share_tight": float((per < tight).mean()), "share_loose": float((per < loose).mean()), "unit": unit, "tight": tight, "loose": loose}


def fmt(v):
    return f"{v:.3g}"


def main():
    true = pd.read_csv(DATA / "equil_data.csv")
    full = pd.read_csv(FULL)
    assert len(true) == len(full) and (true["discharge"].values == full["discharge"].values).all() and np.abs(true["time"].values - full["time"].values).max() < 1e-6
    targets = [c[:-5] for c in full.columns if c.endswith("_pred")]
    assert len(targets) == 31, len(targets)
    true["is_limited"] = true["is_limited"].astype(float)
    G, tim = true["discharge"].values, true["time"].values
    (df, X, Y, Gf, M), _ = F.aligned_data()
    lock, dev_idx, lock_idx = F.split(Gf)
    sign = {d: np.sign(np.nanmedian(true.loc[true.discharge == d, "plasma_current"])) for d in np.unique(G)}
    positive = np.array([sign[d] > 0 for d in G])
    limited = true["is_limited"].values > 0.5
    slices = {"all rows": None, "negative plasma current (normal)": ~positive, "positive plasma current (reversed)": positive, "diverted rows": ~limited, "limited rows": limited,
              "first 2 % of the discharge": tim <= 0.02, "middle": (tim > 0.02) & (tim < 0.98), "last 2 % of the discharge": tim >= 0.98}

    # ---- baseline, 31 targets, all 149 discharges
    sc_all = Scorer(G)
    base = {}
    for t in targets:
        y, p = true[t].values, full[t + "_pred"].values
        m = ~np.isnan(y) & ~np.isnan(p)
        if t == "is_limited":
            ok = ((p > 0.5) == (y > 0.5)).astype(float)
            r = sc_all.score(np.zeros_like(ok), 1 - ok, m, t)            # error = 1 when wrong: the MAE is the error rate
            r["accuracy"] = 1 - r["mae"]
        else:
            r = sc_all.score(p, y, m, t)
        base[t] = r
    base_slices = {}
    for t in SLICE_TARGETS:
        y, p = true[t].values, full[t + "_pred"].values
        m = ~np.isnan(y) & ~np.isnan(p)
        base_slices[t] = {name: sc_all.score(p, y, m, t, rows)["mae"] if (rows is None or (m & rows).sum() > 50) else None for name, rows in slices.items()}

    # ---- shipped model (cand) and the baseline of the same protocol, development folds and locked 30
    cv = F.assemble("cv", None, ["cand", "base"], 5)
    lk = F.assemble("locked", None, ["cand", "base"])
    assert all(np.array_equal(cv[r]["idx"], dev_idx) and np.array_equal(lk[r]["idx"], lock_idx) for r in ("cand", "base"))
    sc_dev, sc_lock = Scorer(Gf[dev_idx]), Scorer(Gf[lock_idx])
    shipped = {}
    for j, t in enumerate(F.TARGETS):
        if t == "is_limited":
            continue
        shipped[t] = {}
        for rec in ("cand", "base"):
            shipped[t][rec] = {"dev": sc_dev.score(cv[rec]["clean"][:, j], Y[dev_idx, j], M[dev_idx, j], t), "locked": sc_lock.score(lk[rec]["clean"][:, j], Y[lock_idx, j], M[lock_idx, j], t)}
    ship_slices = {}
    lim_dev, tim_dev = limited[dev_idx], tim[dev_idx]
    pos_dev = positive[dev_idx]
    dev_slices = {"all rows": None, "negative plasma current (normal)": ~pos_dev, "positive plasma current (reversed)": pos_dev, "diverted rows": ~lim_dev, "limited rows": lim_dev,
                  "first 2 % of the discharge": tim_dev <= 0.02, "middle": (tim_dev > 0.02) & (tim_dev < 0.98), "last 2 % of the discharge": tim_dev >= 0.98}
    for t in SLICE_TARGETS:
        j = F.J[t]
        ship_slices[t] = {name: sc_dev.score(cv["cand"]["clean"][:, j], Y[dev_idx, j], M[dev_idx, j], t, rows)["mae"] if (rows is None or (M[dev_idx, j] & rows).sum() > 50) else None
                          for name, rows in dev_slices.items()}
    n16 = {rec: {k: float(np.mean([F.tstats(cv[rec]["clean"] if k == "dev" else lk[rec]["clean"], Y[dev_idx] if k == "dev" else Y[lock_idx], M[dev_idx] if k == "dev" else M[lock_idx])[t]["nrmse"] for t in F.TARGETS])) for k in ("dev", "locked")} for rec in ("cand", "base")}
    (OUT / "ipp1-confidence.json").write_text(json.dumps({"baseline31": base, "shipped": shipped, "slices_baseline": base_slices, "slices_shipped_dev": ship_slices, "mean_nrmse16": n16}, indent=1) + "\n")
    write_md(targets, base, shipped, base_slices, ship_slices, n16, len(np.unique(G)), len(dev_idx), len(lock_idx), int(positive[dev_idx].sum() > 0), sc_all, sc_dev, sc_lock)


def write_md(targets, base, shipped, base_slices, ship_slices, n16, n_all, n_dev_rows, n_lock_rows, _, sc_all, sc_dev, sc_lock):
    L = ["# IPP 1: how accurate, and how certain, for every parameter", "",
         "Script `analysis/ipp1_confidence.py`; nothing is trained, the out-of-fold predictions that already exist are read. MAE, median, p95 and p99 of the absolute error pooled over rows, in mm (plasma current in kA, "
         "shape numbers and squareness dimensionless). **95 % interval = percentile interval of the MAE from 1,000 resamples of whole discharges** (rows of one discharge are near copies, so resampling rows would give "
         "intervals that are too narrow). *Share of discharges under a tolerance* = the share of discharges whose mean absolute error for that target is below the stated tolerance (tight: 1 mm, 1 kA, 0.01; loose: 5 mm, 5 kA, 0.05).", "",
         "**Which model is which.** The table of 31 targets is the **basic network's** (`ipp1_oof_full.py`: 5 random group folds over all 149 discharges; a masked MLP with 31 outputs, **with the plasma current taken from a ridge regression** (linear in the 24 inputs), not from the network): the shipped model predicts 16 of the 31 targets only. "
         "The second table is the shipped model (`cand`, 16 targets, no `is_limited` row) on the 119 development discharges (cross-validation inside them) and on the 30 locked discharges, side by side with the basic network "
         "trained on the same discharges. **The locked set is easier than development:** the mean relative error over the 16 targets is "
         f"{100 * (1 - n16['cand']['locked'] / n16['cand']['dev']):.0f} % lower for the shipped model and {100 * (1 - n16['base']['locked'] / n16['base']['dev']):.0f} % lower for the basic network "
         "(0.0590 against 0.0912 and 0.0803 against 0.1228, `notebooks/09_final_model_locked_test.ipynb`), so quote the development column next to it. Both models were designed on all 149 discharges, so the locked column is "
         "a check, not clean evidence.", "",
         f"## 1. The basic network, all 31 targets ({n_all} discharges, 5 random group folds)", "",
         "| target | unit | rows | MAE | 95 % interval | median | p95 | p99 | share of discharges < tight | < loose |", "|---|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for t in targets:
        r = base[t]
        if t == "is_limited":
            L.append(f"| {t} | accuracy | {r['n']} | {100 * r['accuracy']:.2f} % | [{100 * (1 - r['hi']):.2f}, {100 * (1 - r['lo']):.2f}] % | | | | | |")
            continue
        L.append(f"| {t} | {r['unit'] or '-'} | {r['n']} | {fmt(r['mae'])} | [{fmt(r['lo'])}, {fmt(r['hi'])}] | {fmt(r['median'])} | {fmt(r['p95'])} | {fmt(r['p99'])} | {100 * r['share_tight']:.0f} % ({fmt(r['tight'])}) | {100 * r['share_loose']:.0f} % ({fmt(r['loose'])}) |")
    L += ["", "## 2. The shipped model (`cand`) and the basic network of the same protocol: development cross-validation next to the 30 locked discharges", "",
          "| target | unit | shipped, development: MAE [95 %] | shipped, locked 30: MAE [95 %] | basic, development | basic, locked | shipped: share of discharges < tight (dev / locked) | < loose (dev / locked) |", "|---|---|---|---|---:|---:|---|---|"]
    for t, r in shipped.items():
        d, k, bd, bk = r["cand"]["dev"], r["cand"]["locked"], r["base"]["dev"], r["base"]["locked"]
        L.append(f"| {t} | {d['unit'] or '-'} | {fmt(d['mae'])} [{fmt(d['lo'])}, {fmt(d['hi'])}] | {fmt(k['mae'])} [{fmt(k['lo'])}, {fmt(k['hi'])}] | {fmt(bd['mae'])} | {fmt(bk['mae'])} | "
                 f"{100 * d['share_tight']:.0f} % / {100 * k['share_tight']:.0f} % ({fmt(d['tight'])}) | {100 * d['share_loose']:.0f} % / {100 * k['share_loose']:.0f} % ({fmt(d['loose'])}) |")
    L += ["", "Protocol: shipped and basic network trained once (seed per fold, seed 0 for the locked set), clean inputs; the locked interval is wide because it rests on 30 discharges.", "",
          "## 3. Slices: where the error lives (MAE in report units)", "",
          "Rows are cut by the truth: reversed polarity = discharges with positive median plasma current (16 of 149 discharges, 14 of them in the development set, 2 in the locked set, so no locked column here); "
          "limited / diverted = the true `is_limited`; the first and last 2 % of the relative time of each discharge. A slice with at most 50 rows with the target is left empty.", ""]
    for title, sl in (("basic network, 149 discharges, 31-target table above", base_slices), ("shipped model `cand`, 119 development discharges (cross-validation)", ship_slices)):
        names = list(next(iter(sl.values())))
        L += [f"### {title}", "", "| target | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
        for t in SLICE_TARGETS:
            L.append(f"| {t} ({unit_of(t)[1] or '-'}) | " + " | ".join("" if sl[t][n] is None else fmt(sl[t][n]) for n in names) + " |")
        L.append("")
    L += ["**Limits.** No row of a tolerance share is a probability of a future discharge being that accurate: it is the share among these discharges, and a discharge counts as accurate on its mean error, not on its worst frame "
          "(see p99 and the last 2 %). The intervals say how much the MAE would move with another set of discharges drawn from the same data, not with another tokamak campaign (blocked split, `results/ipp1-final.md`, is 1.1 to 2.8 times worse). "
          "One network and one seed per cell; the baseline's 31-target numbers must not be read as the shipped model's."]
    (ROOT / "repo/results/ipp1-confidence.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
