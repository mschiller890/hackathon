#!/usr/bin/env python
"""Základní model úlohy IPP 1: ridge a malá vícevýstupová síť s maskou, data dělená podle výbojů.

    HACKATHON_HOME=<složka hackathonu> python -I analysis/ipp1_baseline.py [--epochs 60] [--folds 5]

Zapíše $HACKATHON_HOME/out/ipp1-baseline.json a .md.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
from ipp1_common import OUT, TARGETS, fit_mlp, fit_ridge, group_folds, load, score

parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=int, default=60)
parser.add_argument("--folds", type=int, default=5)
args = parser.parse_args()
torch.set_num_threads(4)
np.random.seed(0)

_, measurements, targets, discharges, exists = load()
fold_scores = {"ridge": [], "mlp": []}
latency = None
started = time.time()
for fold, (train, test) in enumerate(group_folds(measurements, targets, discharges, args.folds)):
    ridge_predict = fit_ridge(measurements[train], targets[train], exists[train])
    fold_scores["ridge"].append(score(ridge_predict(measurements[test]), targets[test], exists[test]))
    predict, net, (input_mean, input_std) = fit_mlp(measurements[train], targets[train], exists[train], args.epochs, seed=fold)
    fold_scores["mlp"].append(score(predict(measurements[test]), targets[test], exists[test]))
    print(f"fold {fold + 1}/{args.folds} done, {time.time() - started:.0f} s", flush=True)

    if latency is None:  # latenci sítě stačí změřit jednou, na první sadě
        one_row = torch.tensor((measurements[test][:1] - input_mean) / input_std)
        with torch.no_grad():
            for _ in range(200):  # zahřátí
                net(one_row)
            durations = []
            for _ in range(2000):
                call_started = time.perf_counter()
                net(one_row)
                durations.append(time.perf_counter() - call_started)
            big_batch = torch.tensor((measurements[test][:4096] - input_mean) / input_std)
            call_started = time.perf_counter()
            net(big_batch)
            batch_duration = time.perf_counter() - call_started
        latency = {"single_sample_cpu_ms_median": float(np.median(durations) * 1000),
                   "single_sample_cpu_ms_p99": float(np.percentile(durations, 99) * 1000),
                   "batch_4096_cpu_ms": float(batch_duration * 1000), "parameters": int(sum(p.numel() for p in net.parameters()))}

# Průměr každé metriky přes sady; jednotka se nepočítá, jen opíše.
average = {model: {target: {metric: (float(np.mean([fold[target][metric] for fold in fold_scores[model]])) if metric != "unit"
                                     else fold_scores[model][0][target]["unit"])
                            for metric in fold_scores[model][0][target]} for target in TARGETS} for model in fold_scores}
OUT.mkdir(exist_ok=True)
json.dump({"folds": args.folds, "epochs": args.epochs, "average": average, "latency": latency,
           "seconds": time.time() - started}, open(OUT / "ipp1-baseline.json", "w"), indent=1)

lines = [f"# Baseline IPP 1: group split by discharge, {args.folds} folds, {args.epochs} epochs", "",
         "| target | unit | ridge MAE | MLP MAE | ridge R2 | MLP R2 | MLP nRMSE |", "|---|---|---|---|---|---|---|"]
for target in TARGETS:
    lines.append(f"| {target} | {average['mlp'][target]['unit']} | {average['ridge'][target]['mae']:.3g} | {average['mlp'][target]['mae']:.3g} | "
                 f"{average['ridge'][target]['r2']:.3f} | {average['mlp'][target]['r2']:.3f} | {average['mlp'][target]['nrmse']:.3f} |")
lines += ["", f"is_limited accuracy: ridge {average['ridge']['is_limited']['accuracy']:.3f}, MLP {average['mlp']['is_limited']['accuracy']:.3f}",
          f"Latency (MLP, CPU, one sample): median {latency['single_sample_cpu_ms_median']:.3f} ms, "
          f"p99 {latency['single_sample_cpu_ms_p99']:.3f} ms; batch of 4096: {latency['batch_4096_cpu_ms']:.1f} ms; "
          f"{latency['parameters']:,} parameters"]
(OUT / "ipp1-baseline.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
