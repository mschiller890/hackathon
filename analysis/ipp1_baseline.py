#!/usr/bin/env python
"""Baseline for IPP task 1: ridge and a small masked multi-output network, split by discharge.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_baseline.py [--epochs 60] [--folds 5]

Writes $HACKATHON_HOME/out/ipp1-baseline.json and .md.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, TARGETS, fit_mlp, fit_ridge, group_folds, load, score

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=60)
ap.add_argument("--folds", type=int, default=5)
args = ap.parse_args()
torch.set_num_threads(4)
np.random.seed(0)

_, X, Y, G, M = load()
results = {"ridge": [], "mlp": []}
latency = None
t0 = time.time()
for k, (tr, te) in enumerate(group_folds(X, Y, G, args.folds)):
    results["ridge"].append(score(fit_ridge(X[tr], Y[tr], M[tr])(X[te]), Y[te], M[te]))
    predict, net, (mu, sd) = fit_mlp(X[tr], Y[tr], M[tr], args.epochs, seed=k)
    results["mlp"].append(score(predict(X[te]), Y[te], M[te]))
    print(f"fold {k + 1}/{args.folds} done, {time.time() - t0:.0f} s", flush=True)
    if latency is None:
        one = torch.tensor((X[te][:1] - mu) / sd)
        with torch.no_grad():
            for _ in range(200):
                net(one)
            ts = []
            for _ in range(2000):
                a = time.perf_counter()
                net(one)
                ts.append(time.perf_counter() - a)
            big = torch.tensor((X[te][:4096] - mu) / sd)
            a = time.perf_counter()
            net(big)
            tb = time.perf_counter() - a
        latency = {"single_sample_cpu_ms_median": float(np.median(ts) * 1000),
                   "single_sample_cpu_ms_p99": float(np.percentile(ts, 99) * 1000),
                   "batch_4096_cpu_ms": float(tb * 1000), "parameters": int(sum(p.numel() for p in net.parameters()))}

avg = {m: {t: {key: (float(np.mean([f[t][key] for f in results[m]])) if key != "unit" else results[m][0][t]["unit"])
               for key in results[m][0][t]} for t in TARGETS} for m in results}
OUT.mkdir(exist_ok=True)
json.dump({"folds": args.folds, "epochs": args.epochs, "average": avg, "latency": latency,
           "seconds": time.time() - t0}, open(OUT / "ipp1-baseline.json", "w"), indent=1)

lines = [f"# Baseline IPP 1: group split by discharge, {args.folds} folds, {args.epochs} epochs", "",
         "| target | unit | ridge MAE | MLP MAE | ridge R2 | MLP R2 | MLP nRMSE |", "|---|---|---|---|---|---|---|"]
for t in TARGETS:
    lines.append(f"| {t} | {avg['mlp'][t]['unit']} | {avg['ridge'][t]['mae']:.3g} | {avg['mlp'][t]['mae']:.3g} | "
                 f"{avg['ridge'][t]['r2']:.3f} | {avg['mlp'][t]['r2']:.3f} | {avg['mlp'][t]['nrmse']:.3f} |")
lines += ["", f"is_limited accuracy: ridge {avg['ridge']['is_limited']['accuracy']:.3f}, MLP {avg['mlp']['is_limited']['accuracy']:.3f}",
          f"Latency (MLP, CPU, one sample): median {latency['single_sample_cpu_ms_median']:.3f} ms, "
          f"p99 {latency['single_sample_cpu_ms_p99']:.3f} ms; batch of 4096: {latency['batch_4096_cpu_ms']:.1f} ms; "
          f"{latency['parameters']:,} parameters"]
(OUT / "ipp1-baseline.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
