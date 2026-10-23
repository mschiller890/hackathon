#!/usr/bin/env python
"""Latency of one estimate of the shipped model with the weights hot in cache and with the cache evicted between the calls.

    python analysis/ipp1_latency_cache.py --label "Ryzen 5 7535HS" [--model out/model/ipp1-selected.npz] [--core 2] [--n 3000]

Needs the model file written by analysis/export_model.py (numpy only here, no torch). Per estimate (one row, numpy path of analysis/predict.py) only the
call itself is timed; between the calls a buffer is read, which pushes the weights out of the cache level named in the table:
  hot        no buffer: the weights stay in L1/L2 (what results/ipp1-latency-shipped.md measures)
  evict L2   a buffer of 4 x the L2 size (taken from lscpu or the Linux cache info, else 16 MB): weights fall back to L3 or memory
  evict L3   a buffer of 2 x the L3 size (else 128 MB): weights are fetched from main memory
On Linux the process is pinned to one core (--core) so that the cache sizes of that core apply. Prints a markdown report; with --out writes it to a file.
The model is 0.9 MB, so it fits an L2 cache of 1 MB or more only partly: the table shows what a smaller L2 costs.
"""
import argparse
import os
import platform
import re
import subprocess
import time
from pathlib import Path

import numpy as np

import predict


def cache_sizes():
    """(L2 bytes, L3 bytes) from lscpu when available (per instance), else None."""
    try:
        txt = subprocess.run(["lscpu", "--caches"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return None, None
    sizes = {}
    for line in txt.splitlines():
        m = re.match(r"\s*(L[123])\S*\s+(\d+(?:\.\d+)?)\s*([KMG]i?B)", line)
        if m:
            unit = {"K": 1 << 10, "M": 1 << 20, "G": 1 << 30}[m.group(3)[0]]
            sizes[m.group(1)] = int(float(m.group(2)) * unit)
    return sizes.get("L2"), sizes.get("L3")


def timing(model, rows, evict_buf, n):
    t = []
    sink = 0.0
    for i in range(n):
        if evict_buf is not None:
            sink += float(evict_buf[:: 16].sum())  # touches one float32 per cache line
        x = rows[i % len(rows)][None, :]
        t0 = time.perf_counter()
        model.predict(x)
        t.append((time.perf_counter() - t0) * 1e3)
    t = np.array(t)
    return {"median": float(np.median(t)), "p99": float(np.percentile(t, 99)), "p99.9": float(np.percentile(t, 99.9)), "max": float(t.max()), "sink": sink}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=str(predict.DEFAULT_MODEL))
    ap.add_argument("--label", default=platform.processor() or platform.machine())
    ap.add_argument("--core", type=int, default=None, help="pin to this core (Linux only)")
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.core is not None and hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, {a.core})
    model = predict.Model(a.model)
    mu = model.z["gen_mu"][:24].astype(np.float64)
    sd = model.z["gen_sd"][:24].astype(np.float64)
    rng = np.random.default_rng(0)
    rows = (mu + rng.normal(size=(256, 24)) * sd * 0.5).astype(np.float32)  # plausible inputs; the weights, not the values, are what is timed
    gated = int((model.predict(rows)[:, model.cls_col] > 0.5).sum())
    l2, l3 = cache_sizes()
    buf2 = np.ones(max(4 * (l2 or 4 << 20), 16 << 20) // 4, dtype=np.float32)
    buf3 = np.ones(max(2 * (l3 or 32 << 20), 128 << 20) // 4, dtype=np.float32)
    for _ in range(200):
        model.predict(rows[:1])  # warm-up
    res = {"hot": timing(model, rows, None, a.n), "evict L2": timing(model, rows, buf2, a.n), "evict L3": timing(model, rows, buf3, a.n)}
    lines = [f"# Latency of the shipped model with the cache evicted ({a.label})", "",
             f"CPU: {a.label}; L2 per core {l2 and l2 // 1024} KiB, L3 {l3 and l3 // 1024} KiB (lscpu); model file {Path(a.model).stat().st_size / 1e6:.2f} MB; "
             f"{a.n} single-row estimates per row of the table; pinned core: {a.core}; rows gated to the limiter network: {gated} of 256 (random plausible inputs).",
             "", "| state | median ms | p99 ms | p99.9 ms | max ms |", "|---|---:|---:|---:|---:|"]
    for k, v in res.items():
        lines.append(f"| {k} | {v['median']:.4f} | {v['p99']:.4f} | {v['p99.9']:.4f} | {v['max']:.4f} |")
    lines += ["", "Reading: `hot` is the number used elsewhere; `evict L2` is the cost when the weights must come from L3; `evict L3` when they come from main memory. "
              "Timing includes only the call, not the buffer read. Machine load and frequency scaling are not controlled."]
    text = "\n".join(lines)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
