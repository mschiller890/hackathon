#!/usr/bin/env python
"""Latency of the network for the real-time verdict (REQ-002). Weights do not change the timing, so a freshly
initialised network of the trained architecture is timed.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_latency.py

Writes out/ipp1-latency.{json,md}. The md names the CPU and the load average during the run: a tail (p99.9, max) measured on a
loaded machine, or on an operating system without real-time guarantees, is not a bound. Run it when `uptime` shows a load
average below 8 for a clean figure.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, Net


def cpu_name():
    try:
        return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        import platform
        return platform.processor() or platform.machine()


torch.manual_seed(0)
net = Net(24, 16).eval()
x1 = torch.randn(1, 24)
res = {"parameters": int(sum(p.numel() for p in net.parameters())), "cpu": cpu_name(), "cores": os.cpu_count(),
       "load_average_start": [round(v, 2) for v in os.getloadavg()]}


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

    def numpy_forward(h=xn):
        for i, (w, b) in enumerate(Ws):
            h = h @ w + b
            if i < len(Ws) - 1:
                h = h * (1.0 / (1.0 + np.exp(-h)))  # SiLU
        return h
    assert np.allclose(numpy_forward(), net(x1).numpy(), atol=1e-5), "numpy forward pass differs from torch"
    res["numpy_single_sample"] = timeit(numpy_forward)
    # End to end on the CPU: raw numpy sample in, standardisation, network, de-standardisation, numpy out.
    mu, sd = np.random.randn(24).astype(np.float32), np.random.rand(24).astype(np.float32) + 0.5
    ym, ys = np.random.randn(16).astype(np.float32), np.random.rand(16).astype(np.float32) + 0.5
    xraw = (xn * sd + mu).astype(np.float32)
    res["cpu_end_to_end_numpy"] = timeit(lambda: numpy_forward((xraw - mu) / sd) * ys + ym)
    res["mps_available"] = bool(torch.backends.mps.is_available())
    if res["mps_available"]:
        dev = torch.device("mps")
        netm = Net(24, 16).to(dev).eval()
        xm = torch.randn(1, 24, device=dev)

        def mps_single():
            netm(xm)
            torch.mps.synchronize()
        res["mps_single_sample"] = timeit(mps_single, n=2000, warm=200)

        def mps_end_to_end():
            # numpy in, standardise on the CPU, copy to the GPU, network, copy back (the copy back waits for the result).
            xt = torch.from_numpy((xraw - mu) / sd).to(dev)
            return netm(xt).cpu().numpy() * ys + ym
        res["mps_single_sample_with_transfers"] = timeit(mps_end_to_end, n=2000, warm=200)
        xb = torch.randn(4096, 24, device=dev)

        def mps_batch():
            netm(xb)
            torch.mps.synchronize()
        res["mps_batch_4096"] = timeit(mps_batch, n=300, warm=50)
res["load_average_end"] = [round(v, 2) for v in os.getloadavg()]
with open(OUT / "ipp1-latency.json", "w") as fh:
    json.dump(res, fh, indent=1, allow_nan=False)

loaded = max(res["load_average_start"][0], res["load_average_end"][0], res["load_average_end"][1]) >= 8
lines = ["# Latency (REQ-002)", "", "The assignment asks for a reaction in units to tens of milliseconds. "
         f"Network: {res['parameters']:,} parameters, 24 inputs, 16 outputs (a freshly initialised network of the trained "
         "architecture; weights do not change the timing). Times in milliseconds.", "",
         f"CPU: {res['cpu']} ({res['cores']} logical cores); GPU rows: the Apple GPU of the same chip through torch MPS. "
         f"Load average (1, 5, 15 minutes) at the start {res['load_average_start']}, at the end {res['load_average_end']}; "
         f"{'the machine was shared and busy (a load of 8 or more in the 1 or 5 minute average on 10 cores), so the medians are somewhat pessimistic and the tails are pessimistic: not a clean benchmark.' if loaded else 'the load average was below 8 in all windows.'} "
         "The tail columns (p99.9, max) come from 5000 calls (500 or fewer for the batch rows) on a general-purpose operating system "
         "without real-time guarantees: they show what happens on such a machine, they are not a worst-case bound. "
         "A loaded machine earlier gave p99 0.65 ms and max 21 ms for a single CPU sample (reviewer measurement, load 16), still inside a 1 to 10 ms budget at the p99.", "",
         "| setting | median | p99 | p99.9 | max |", "|---|---|---|---|---|"]
for k, v in res.items():
    if isinstance(v, dict):
        lines.append(f"| {k} | {v['median_ms']:.4f} | {v['p99_ms']:.4f} | {v['p999_ms']:.4f} | {v['max_ms']:.3f} |")
lines += ["", "cpu_end_to_end_numpy and mps_single_sample_with_transfers include the standardisation of the inputs, the copy to and "
          "from the GPU (the GPU row) and the de-standardisation of the outputs, which any real loop needs; the other single-sample "
          "rows time the network only. What these numbers do not cover: collecting and integrating the coil signals, and the "
          "accuracy on really noisy signals (see the robustness results)."]
(OUT / "ipp1-latency.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
