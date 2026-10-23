#!/usr/bin/env python
"""Throughput of the trained baseline network in bulk: how many estimates per second when many time steps are batched.

    HACKATHON_HOME=<hackathon folder> taskset -c 0,2,4,6,8,10 python analysis/ipp1_throughput.py --label "Ryzen 5 7535HS" \
        --out results/ipp1-throughput-ryzen.md

This is not the real-time number. A controller needs each new measurement answered at once, which is the single-sample latency
of analysis/ipp1_latency.py; a batch of 2048 time steps only exists after 2048 time steps have arrived. Throughput answers a
different question: how fast stored discharges (or a camera-rate stream that may be buffered) can be processed.

1. Trains with ipp1_common.fit_mlp (group fold 0, seed 0, 60 epochs), the project's baseline network.
2. Builds a fast forward pass from those weights: the input standardisation folded into the first layer and the output scaling
   into the last (exact algebra), preallocated buffers, in-place SiLU. Checked against fit_mlp's predict() on every held-out row.
3. Streams the held-out time steps (raw sensor values in, physical units out) through it for 3 s per batch size and divides the
   rows processed by the wall clock. The held-out set is repeated, so after the first pass its inputs are already in cache.
The working set per batch (weights plus the activations of one batch) is printed next to the rate; it fits a 16 MB L3 up to
about 4096 rows. Writes aggregate numbers only (no IPP data rows).
"""
import argparse
import os
import platform
import time

import numpy as np
import torch

import ipp1_common as C


def fast_pass(net, mu, sd, ym, ys):
    """(weights, biases) of a forward pass that maps raw sensor values to physical units with no separate scaling step."""
    lin = [m for m in net.f if isinstance(m, torch.nn.Linear)]
    with torch.no_grad():
        W = [m.weight.T.double().clone() for m in lin]  # (in, out), so a batch is x @ W + b
        b = [m.bias.double().clone() for m in lin]
        mu, sd = torch.tensor(mu, dtype=torch.float64), torch.tensor(sd, dtype=torch.float64)
        b[0] = b[0] - (mu / sd) @ W[0]
        W[0] = W[0] / sd[:, None]
        ys, ym = torch.tensor(ys, dtype=torch.float64), torch.tensor(ym, dtype=torch.float64)
        W[-1], b[-1] = W[-1] * ys, b[-1] * ys + ym
    return [w.float().contiguous() for w in W], [v.float().contiguous() for v in b]


def make_forward(W, B, n, n_in):
    """Forward pass for batches of up to n rows into preallocated buffers; returns (fwd, working-set bytes of weights and one batch)."""
    bufs = [torch.empty(n, w.shape[1]) for w in W]

    def fwd(x):
        h, m = x, x.shape[0]
        for i, (w, b) in enumerate(zip(W, B)):
            out = bufs[i][:m]
            torch.addmm(b, h, w, out=out)
            if i < len(W) - 1:
                torch.nn.functional.silu(out, inplace=True)
            h = out
        return h
    weights = sum(w.numel() + b.numel() for w, b in zip(W, B)) * 4
    return fwd, weights + (sum(b.numel() for b in bufs) + n * n_in) * 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default=platform.processor() or platform.machine())
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--out", help="write the markdown report here as well")
    a = ap.parse_args()

    df, X, Y, groups, mask = C.load()
    tr, te = C.group_folds(X, Y, groups)[0]
    t = time.time()
    predict, net, (mu, sd) = C.fit_mlp(X[tr], Y[tr], mask[tr])
    fit_s = time.time() - t
    ym, ys = np.nanmean(Y[tr], 0), np.nanstd(Y[tr], 0) + 1e-9  # the output scaling fit_mlp applies inside predict()
    W, B = fast_pass(net, mu, sd, ym, ys)
    iR = C.TARGETS.index("R_mag_axis")

    torch.set_num_threads(a.threads)
    xte = torch.tensor(X[te], dtype=torch.float32).contiguous()
    fwd, _ = make_forward(W, B, len(xte), X.shape[1])
    with torch.inference_mode():
        fast = fwd(xte).numpy().copy()
    ref = predict(X[te])
    diff_mm = float(np.nanmax(np.abs(fast[:, iR] - ref[:, iR]))) * 1000
    err_mm = float(np.nanmean(np.abs(fast[:, iR] - Y[te, iR]))) * 1000
    err_ref_mm = float(np.nanmean(np.abs(ref[:, iR] - Y[te, iR]))) * 1000

    rows = []
    for n in (1, 256, 512, 1024, 2048, 4096, 8192):
        torch.set_num_threads(1 if n == 1 else a.threads)  # one row: more threads only add synchronisation
        fwd, ws = make_forward(W, B, n, X.shape[1])
        starts = list(range(0, len(xte), n))
        with torch.inference_mode():
            for s in starts[:5]:
                fwd(xte[s:s + n])
            done, per_batch, t0 = 0, [], time.perf_counter()
            while time.perf_counter() - t0 < 3.0:
                for s in starts:
                    tb = time.perf_counter_ns()
                    fwd(xte[s:s + n])
                    if s + n <= len(xte):  # the median is over full batches only; the partial last one still counts in the rate
                        per_batch.append((time.perf_counter_ns() - tb) / 1e3)
                done += len(xte)
            rate = done / (time.perf_counter() - t0)
        rows.append((n, ws / 1e6, float(np.median(per_batch)), rate))
        print(f"batch {n:5d}: {rate:12,.0f} estimates per second", flush=True)

    load = os.getloadavg()[0] if hasattr(os, "getloadavg") else float("nan")
    cores = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else "not available"
    lines = [
        f"# Throughput of the trained baseline network in bulk ({a.label})", "",
        f"Network: ipp1_common.fit_mlp, group fold 0, seed 0, 60 epochs (trained in {fit_s:.0f} s), 24 inputs, 16 outputs. "
        f"Fast pass: scaling folded into the first and last layer, preallocated buffers, torch {torch.__version__}, "
        f"{a.threads} threads (batch 1: one thread), cores {cores}, load average {load:.2f} at the end.", "",
        f"Check on all {len(xte)} held-out time steps: axis R mean absolute error {err_mm:.3f} mm with the fast pass, "
        f"{err_ref_mm:.3f} mm with fit_mlp's predict(); largest difference between the two {diff_mm:.6f} mm.", "",
        "| batch | weights + one batch | median time per batch | estimates per second |",
        "|---:|---:|---:|---:|",
    ]
    lines += [f"| {n} | {ws:.2f} MB | {med:.1f} µs | {rate:,.0f} |" for n, ws, med, rate in rows]
    lines += ["", "Reading: the rate is held-out time steps processed divided by the wall clock over 3 s, with the held-out set "
              "repeated. It is bulk throughput, not the latency a controller sees: a batch of n rows waits for n time steps to "
              "arrive. Batch 1 is the one-at-a-time case. Above about 4096 rows the batch no longer fits the 16 MB L3 of this "
              "CPU and the rate drops. Machine load and frequency scaling are not controlled."]
    text = "\n".join(lines) + "\n"
    print("\n" + text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()
