#!/usr/bin/env python
"""Does the numpy-only predict.py reproduce the shipped model? Compares it with the predictions of ipp1_final.py cached for the 30 locked discharges.

    HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/check_predict.py [--model out/model/ipp1-selected.npz]

1. The library path: Model.estimates on the 8,761 rows of the 30 locked discharges against out/ipp1-final-cache/locked_cand.npz (torch, float32), per target in the report unit.
2. The command line path: one locked discharge is written to a CSV, `analysis/predict.py ... --all --out` is run as a separate process, and its output is compared with the cache.
Passes if every difference is below 1e-3 of the unit (mm, kA, or the dimensionless number). Prints the largest differences and the time per row.
"""
import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script folder
import ipp1_final as F
import predict as P
from ipp1_common import OUT

LIMIT = 1e-3


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=str(OUT / "model" / "ipp1-selected.npz"))
    args = ap.parse_args()
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, lock_idx = F.split(G)
    cached = np.load(F.CACHE / "locked_cand.npz")
    assert np.array_equal(cached["idx"], lock_idx)
    model = P.Model(args.model)
    ref = cached["clean"].astype(np.float64) * model.scales          # cached predictions in the report units
    mine = model.estimates(X[lock_idx])
    diff = np.abs(mine - ref)
    gate_flips = int(((mine[:, model.cls_col] > 0.5) != (ref[:, model.cls_col] > 0.5)).sum())
    print(f"1. library path: {len(lock_idx)} rows of {len(np.unique(G[lock_idx]))} locked discharges against the cache of ipp1_final.py; rows where the limited flag differs: {gate_flips}")
    print("   target               unit   max |difference|   mean |difference|")
    for j, t in enumerate(model.outputs):
        print(f"   {t:20s} {F.UNIT[t][1] or '-':>4s}   {diff[:, j].max():14.3g}   {diff[:, j].mean():15.3g}")
    worst = float(diff.max())
    print(f"   largest difference over all targets: {worst:.3g}")

    first = lock_idx[G[lock_idx] == G[lock_idx][0]]
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "input.csv", Path(tmp) / "estimates.csv"
        with open(src, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["discharge", "time"] + model.inputs)
            for i in first:
                w.writerow([int(G[i]), f"{df.time.values[i]:.9g}"] + [f"{v:.9g}" for v in X[i].astype(np.float64)])
        run = subprocess.run([sys.executable, "-I", str(HERE / "predict.py"), str(src), "--model", args.model, "--all", "--out", str(dst)], capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        with open(dst, newline="") as fh:
            r = csv.reader(fh)
            header = next(r)
            out = np.array([[float(v) for v in row[2:-1]] for row in r])
        cli_diff = np.abs(out - ref[np.searchsorted(lock_idx, first)])
        print(f"2. command line path: discharge {int(G[first[0]])}, {len(first)} rows through `predict.py --all --out`; largest difference {cli_diff.max():.3g}")
        print("   " + run.stderr.strip())
    ok = worst < LIMIT and float(cli_diff.max()) < LIMIT
    print(f"{'PASS' if ok else 'FAIL'}: all differences below {LIMIT:g} of the unit" if ok else f"FAIL: a difference above {LIMIT:g} of the unit")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
