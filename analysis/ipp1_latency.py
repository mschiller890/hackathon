#!/usr/bin/env python
"""Latency of the network for the real-time verdict (REQ-002). Weights do not change the timing, so a freshly
initialised network of the trained architecture is timed.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_latency.py

Writes out/ipp1-latency.{json,md}.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, Net

torch.manual_seed(0)
net = Net(24, 16).eval()
x1 = torch.randn(1, 24)
res = {"parameters": int(sum(p.numel() for p in net.parameters()))}


def timeit(fn, n=5000, warm=300):
    for _ in range(warm):
        fn()
    ts = np.empty(n)
    for i in range(n):
        a = time.perf_counter()
        fn()
        ts[i] = (time.perf_counter() - a) * 1000
    return {"median_ms": float(np.median(ts)), "p99_ms": float(np.percentile(ts, 99)),
            "p999_ms": float(np.percentile(ts, 99.9)), "max_ms": float(ts.max())}


with torch.no_grad():
    for threads in (1, 4):
        torch.set_num_threads(threads)
        res[f"cpu_{threads}_thread_single_sample"] = timeit(lambda: net(x1))
    torch.set_num_threads(4)
    for b in (64, 1024, 4096):
        xb = torch.randn(b, 24)
        res[f"cpu_batch_{b}"] = timeit(lambda: net(xb), n=500, warm=50)
    # The same forward pass in plain numpy, to show that no deep learning framework is needed in a control loop.
    Ws = [(m.weight.detach().numpy().T.copy(), m.bias.detach().numpy().copy()) for m in net.f if isinstance(m, torch.nn.Linear)]
    xn = x1.numpy()

    def numpy_forward():
        h = xn
        for i, (w, b) in enumerate(Ws):
            h = h @ w + b
            if i < len(Ws) - 1:
                h = h / (1.0 + np.exp(-h)) if False else h * (1.0 / (1.0 + np.exp(-h)))
        return h
    res["numpy_single_sample"] = timeit(numpy_forward)
    res["mps_available"] = bool(torch.backends.mps.is_available())
    if res["mps_available"]:
        dev = torch.device("mps")
        netm = Net(24, 16).to(dev).eval()
        xm = torch.randn(1, 24, device=dev)

        def mps_single():
            netm(xm)
            torch.mps.synchronize()
        res["mps_single_sample"] = timeit(mps_single, n=2000, warm=200)
        xb = torch.randn(4096, 24, device=dev)

        def mps_batch():
            netm(xb)
            torch.mps.synchronize()
        res["mps_batch_4096"] = timeit(mps_batch, n=300, warm=50)
json.dump(res, open(OUT / "ipp1-latency.json", "w"), indent=1)

lines = ["# Latency (REQ-002)", "", "The assignment asks for a reaction in units to tens of milliseconds. "
         f"Network: {res['parameters']:,} parameters, 24 inputs, 16 outputs. Times in milliseconds.", "",
         "| setting | median | p99 | p99.9 | max |", "|---|---|---|---|---|"]
for k, v in res.items():
    if isinstance(v, dict):
        lines.append(f"| {k} | {v['median_ms']:.4f} | {v['p99_ms']:.4f} | {v['p999_ms']:.4f} | {v['max_ms']:.3f} |")
worst = max(v["max_ms"] for v in res.values() if isinstance(v, dict) and "single" in "".join(k for k in res if res[k] is v))
(OUT / "ipp1-latency.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
