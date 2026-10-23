#!/usr/bin/env python
"""The 18 oddest discharges held out of training alone (REQ-B08, docs/bonus-gaps.md, item E).

Groups, by the median elongation of a discharge (the grouping of ipp1_unusual_shapes.py):
  odd18    the discharges with median elongation below 1.74 (18 of 149: elongation 1.0 to 1.74, triangularity 0.02 to 0.33), trained without them: 131 train, 18 test
  lowest5  the 5 discharges with the lowest median elongation, trained without them: 144 train, 5 test
Reference: the error on the same discharges in the usual random 5-fold split by discharge (they are then held out together with about 24 others and neighbours of
their own campaign are in training), same network (the shared masked MLP of ipp1_common.fit_mlp, 60 epochs), same seeds. 3 seeds for every fit.
Also checked: whether the ids of the 18 are contiguous, in which case leaving them out is also a test on a block of the campaign order.

Wording for the slides: "the 18 oddest discharges were left out of training", never "new shapes": 18 discharges, one network, shapes outside the range of the data are not tested.

    HACKATHON_HOME=... nice -n 10 ~/.venvs/hackathon/bin/python -I analysis/ipp1_unusual_heldout.py [--threads 2]      writes results/ipp1-unusual-heldout.md
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_final as F
import ipp1_unusual_shapes as US
from ipp1_common import OUT, ROOT, group_folds, load

SEEDS = (0, 1, 2)
SHOWN = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "R_x_point", "Z_x_point", "R_strike_point_1", "R_strike_point_2", "R_limiter", "Z_limiter"]


def runs_of(ids):
    ids = sorted(int(i) for i in ids)
    out, start = [], ids[0]
    for a, b in zip(ids, ids[1:] + [None]):
        if b != a + 1:
            out.append((start, a))
            start = b
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--md-only", action="store_true", help="rewrite the md from out/ipp1-unusual-heldout.json without training")
    args = ap.parse_args()
    if args.md_only:
        res = json.loads((OUT / "ipp1-unusual-heldout.json").read_text())
        res.setdefault("id_quartile", float(np.quantile(np.unique(load()[3]), 0.25)))
        write_md(res)
        return
    torch.set_num_threads(args.threads)
    started = time.time()
    df, x, y, groups, mask = load()
    ids = np.unique(groups)
    el = np.array([np.nanmedian(df.elongation[groups == g]) for g in ids])
    tri = np.array([np.nanmedian(df.triangularity[groups == g]) for g in ids])
    odd = ids[el < 1.74]
    assert len(odd) == 18, len(odd)
    low5 = ids[np.argsort(el)[:5]]
    holdouts = {"odd18": odd, "lowest5": low5}
    el_range = float(np.nanmax(y[:, F.J["elongation"]]) - np.nanmin(y[:, F.J["elongation"]]))
    result = {"id_quartile": float(np.quantile(ids, 0.25)), "seconds": None, "ids": {k: [int(i) for i in v] for k, v in holdouts.items()}, "elongation_range": el_range, "groups": {}}
    folds = group_folds(x, y, groups, 5)
    random_oof = {}
    for s in SEEDS:
        oof = np.full(y.shape, np.nan, dtype=np.float32)
        for f, (tr, te) in enumerate(folds):
            oof[te] = US.fit_without(x, y, mask, tr, 60, f + 10 * s)[te]
        random_oof[s] = oof
        print(f"random folds, seed {s}: {time.time() - started:.0f} s", flush=True)
    for name, held in holdouts.items():
        test = np.flatnonzero(np.isin(groups, held))
        train = np.flatnonzero(~np.isin(groups, held))
        per = {"random": [], "alone": []}
        for s in SEEDS:
            pred = US.fit_without(x, y, mask, train, 60, 100 + s)
            per["alone"].append(F.tstats(np.nan_to_num(pred[test]), y[test], mask[test] & ~np.isnan(pred[test])))
            per["random"].append(F.tstats(random_oof[s][test], y[test], mask[test]))
            print(f"{name}, seed {s}: {time.time() - started:.0f} s", flush=True)
        result["groups"][name] = {"discharges": int(len(held)), "rows": int(len(test)), "train_discharges": int(len(np.unique(groups[train]))),
                                  "median_elongation": [float(np.min(el[np.isin(ids, held)])), float(np.max(el[np.isin(ids, held)]))],
                                  "median_triangularity": [float(np.min(tri[np.isin(ids, held)])), float(np.max(tri[np.isin(ids, held)]))],
                                  "runs": runs_of(held), **{k: v for k, v in per.items()}}
    result["seconds"] = time.time() - started
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ipp1-unusual-heldout.json").write_text(json.dumps(result, indent=1, default=float) + "\n")
    write_md(result)


def write_md(res):
    def agg(runs, t, key):
        v = [r[t][key] for r in runs if r[t] is not None]          # None: fewer than 2 labelled rows in the group
        return (float(np.mean(v)), float(np.std(v, ddof=1))) if len(v) > 1 else (float("nan"), float("nan"))
    unit = {t: F.UNIT[t][1] or "-" for t in SHOWN}
    L = ["# IPP 1: the oddest discharges left out of training alone (REQ-B08)", "",
         "Script `analysis/ipp1_unusual_heldout.py`. **Wording: \"osmnáct nejodlišnějších výbojů vynecháno z učení\"; this does not test new shapes**: 18 discharges, one network, 3 seeds, and nothing is said about shapes "
         "outside the range of the data.", "",
         "Network: the shared masked MLP of `ipp1_common.fit_mlp` (the baseline network, 60 epochs). Groups by the median elongation of a discharge: **odd18** = the 18 discharges with median elongation below 1.74 "
         f"(elongation {res['groups']['odd18']['median_elongation'][0]:.2f} to {res['groups']['odd18']['median_elongation'][1]:.2f}, triangularity {res['groups']['odd18']['median_triangularity'][0]:.2f} to "
         f"{res['groups']['odd18']['median_triangularity'][1]:.2f}; the other 131 discharges train, 18 test) and **lowest5** = the 5 with the lowest median elongation (144 train, 5 test). Reference: the error on the same "
         "discharges in the random 5-fold split by discharge, same network and seeds (there they are held out together with other discharges and neighbours from the same campaign are in training). "
         "MAE and p99 of the absolute error pooled over the rows of the group, in mm (plasma current in kA, elongation and triangularity dimensionless); mean (SD over 3 seeds).", ""]
    for name, g in res["groups"].items():
        L += [f"## {name}: {g['discharges']} discharges, {g['rows']} rows, {g['train_discharges']} training discharges", "",
              "| target | unit | MAE random folds | MAE left out | factor | p99 random folds | p99 left out |", "|---|---|---:|---:|---:|---:|---:|"]
        for t in SHOWN:
            (r, rs), (a, as_) = agg(g["random"], t, "mae"), agg(g["alone"], t, "mae")
            (r9, _), (a9, _) = agg(g["random"], t, "p99"), agg(g["alone"], t, "p99")
            L.append(f"| {t} | {unit[t]} | {r:.3g} ({rs:.2g}) | {a:.3g} ({as_:.2g}) | {a / r:.1f} | {r9:.3g} | {a9:.3g} |")
        e, _ = agg(g["alone"], "elongation", "mae")
        L += ["", f"The elongation error left out, {e:.4f}, is {100 * e / res['elongation_range']:.1f} % of the range of the elongation in the data ({res['elongation_range']:.2f}).", ""]
    for name in res["groups"]:
        runs = res["groups"][name]["runs"]
        L.append(f"Ids of {name}: {', '.join(str(i) for i in res['ids'][name])}; runs of consecutive numbers: {', '.join(f'{a} to {b}' if a != b else str(a) for a, b in runs)}"
                 f" ({len(runs)} run{'s' if len(runs) != 1 else ''}).")
    r18 = res["groups"]["odd18"]["runs"]
    early = sum(1 for i in res["ids"]["odd18"] if i <= res["id_quartile"])
    L += ["", f"**Campaign order.** {early} of the 18 ids lie in the lowest quarter of all discharge numbers (up to {res['id_quartile']:.0f}), the start of the campaign order; so the factor mixes the shape with the early campaign, and the second group (the 5 lowest) has no rows of the X point and the strike points (those discharges are limited) which are marked n/a."]
    L += ["", "**Contiguity.** " + (f"The 18 ids form {len(r18)} runs of consecutive numbers, so leaving them out is partly also a test on blocks of the campaign order, and the factor mixes shape with campaign."
                                    if len(r18) <= 3 else f"The 18 ids form {len(r18)} runs of consecutive numbers (the longest {max(b - a + 1 for a, b in r18)} numbers long), so they are not one block of the campaign order, but most of them are early (see above).")]
    L += ["", "**Limits.** 18 discharges (5 in the second group) and 3 seeds; the random-fold reference has about 24 test discharges per fold and shares its training discharges with its neighbours, so it is optimistic; "
          "only the baseline network was used, not the shipped model; the least elongated discharges have conditional targets (X point, strike points, limiter) in few rows."]
    text = re.sub(r"\bnan\b", "n/a", re.sub(r"nan \(nan\)", "n/a", "\n".join(L)))
    (ROOT / "repo/results/ipp1-unusual-heldout.md").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
