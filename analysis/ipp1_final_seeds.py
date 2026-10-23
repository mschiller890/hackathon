#!/usr/bin/env python
"""Seed noise of the final comparison: baseline MLP against the plain candidate on the locked test set.

Uses the recipes, the split and the metrics of ipp1_final.py unchanged (no recipe change). Each model is trained on the 119
development discharges with another seed and scored on the 30 locked discharges, clean inputs; the seed-0 predictions of
ipp1_final.py are read from its cache and counted as the first seed.

    python -I analysis/ipp1_final_seeds.py --seed 1            # trains base and cand with seed 1, caches the locked predictions
    python -I analysis/ipp1_final_seeds.py --report            # results/ipp1-final-seeds.md (aggregate numbers only)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ipp1_final as F
from ipp1_common import OUT, ROOT

CACHE = OUT / "ipp1-final-seeds-cache"
SHOWN = ["R_mag_axis", "Z_mag_axis", "R_x_point", "R_strike_point_2", "R_limiter", "Z_limiter", "plasma_current"]
RECIPES = ["base", "cand"]


def job(seed, threads):
    torch.set_num_threads(threads)
    (df, X, Y, G, M), _ = F.aligned_data()
    times = df.time.to_numpy()
    _, dev, lock = F.split(G)
    assert not set(G[dev]) & set(G[lock])
    CACHE.mkdir(parents=True, exist_ok=True)
    for recipe in RECIPES:
        t0 = time.time()
        predict = F.train(recipe, X[dev], Y[dev], M[dev], G[dev], times[dev], seed, 0)
        np.savez(CACHE / f"{recipe}_{seed}.npz", idx=lock, clean=predict(X[lock]).astype(np.float32))
        print(f"{recipe} seed {seed}: {time.time() - t0:.0f} s", flush=True)


def load_predictions(lock):
    """{recipe: {seed: predictions on the locked rows}}; seed 0 comes from the cache of ipp1_final.py."""
    out = {r: {} for r in RECIPES}
    for r in RECIPES:
        files = {0: F.CACHE / f"locked_{r}.npz", **{int(p.stem.split("_")[-1]): p for p in CACHE.glob(f"{r}_*.npz")}}
        for s, f in sorted(files.items()):
            if f.exists():
                d = np.load(f)
                assert np.array_equal(d["idx"], lock)
                out[r][s] = d["clean"]
    return out


def report():
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev, lock = F.split(G)
    P = load_predictions(lock)
    seeds = sorted(set(P["base"]) & set(P["cand"]))
    mae = {r: {s: {t: F.tstats(P[r][s], Y[lock], M[lock])[t]["mae"] for t in SHOWN} for s in seeds} for r in RECIPES}
    unit = {t: F.UNIT[t][1] for t in SHOWN}
    L = ["# IPP 1: seed noise of the final comparison (locked test set)", "",
         f"Baseline MLP against the plain candidate (differences, Huber, 150 epochs, ridge for plasma current, gated limiter network), clean inputs, "
         f"{len(seeds)} seeds each ({', '.join(map(str, seeds))}; seed 0 is the model of `results/ipp1-final.md`). Recipes, split and metrics are those of "
         "`analysis/ipp1_final.py` unchanged; every model is trained on the 119 development discharges and scored on the 30 locked discharges, nothing was "
         "tuned after seeing them. Pooled MAE over the locked rows (mm, plasma current in kA); mean and standard deviation (n-1) over seeds. "
         "Aggregate numbers only.", "",
         "| target | baseline mean (SD) | candidate mean (SD) | ratio of means | paired ratio per seed, min to max | candidate better in | worst candidate seed against best baseline seed |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for t in SHOWN:
        b = np.array([mae["base"][s][t] for s in seeds])
        c = np.array([mae["cand"][s][t] for s in seeds])
        ratio = c / b
        L.append(f"| {t} ({unit[t]}) | {b.mean():.3g} ({b.std(ddof=1):.2g}) | {c.mean():.3g} ({c.std(ddof=1):.2g}) | {c.mean() / b.mean():.2f} | "
                 f"{ratio.min():.2f} to {ratio.max():.2f} | {int((ratio < 1).sum())} of {len(seeds)} | {c.max() / b.min():.2f} |")
    L += ["", "The last column is the maximum candidate MAE over the minimum baseline MAE: below 1 the two seed ranges do not overlap, so the ordering "
          "holds for any pair of seeds, not only for equal seeds. Paired ratio = candidate over baseline with the same seed."]
    L += ["", "Per seed pooled MAE (baseline / candidate):", "", "| target | " + " | ".join(f"seed {s}" for s in seeds) + " |", "|---|" + "---:|" * len(seeds)]
    for t in SHOWN:
        L.append(f"| {t} ({unit[t]}) | " + " | ".join(f"{mae['base'][s][t]:.3g} / {mae['cand'][s][t]:.3g}" for s in seeds) + " |")
    text = "\n".join(L) + "\n"
    target = ROOT / "repo/results/ipp1-final-seeds.md"
    if target.exists() and "\n## Reading" in target.read_text():  # the hand-written reading is kept
        text += "\n## Reading" + target.read_text().split("\n## Reading", 1)[1]
    target.write_text(text)
    print(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.seed is not None:
        assert a.seed > 0, "seed 0 is the model of ipp1_final.py"
        job(a.seed, a.threads)
    if a.report:
        report()
