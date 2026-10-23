#!/usr/bin/env python
"""Latency of the network for the real-time verdict (REQ-002). Weights do not change the timing, so a freshly
initialised network of the trained architecture is timed.

    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_latency.py
    HACKATHON_HOME=<hackathon folder> python -I analysis/ipp1_latency.py --shipped    # the shipped pair of ipp1_final.py

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


def numpy_mlp(net):
    """The forward pass of an MLP of ipp1_final.py in plain numpy (SiLU), for one sample."""
    layers = [(m.weight.detach().numpy().T.copy(), m.bias.detach().numpy().copy()) for m in net.f if isinstance(m, torch.nn.Linear)]

    def forward(h):
        for i, (w, b) in enumerate(layers):
            h = h @ w + b
            if i < len(layers) - 1:
                h = h * (1.0 / (1.0 + np.exp(-h)))
        return h
    return forward


def shipped():
    """Latency of the shipped model pair of ipp1_final.py (recipe `cand`): one sample, from the 24 raw inputs to the 16 outputs.

    The pair is the general network (24 inputs + 22 neighbouring-coil differences = 46 inputs), the ridge for plasma_current and the
    network trained on limited rows, which answers R_limiter and Z_limiter when the general network predicts is_limited > 0.5.
    Weights do not change the timing; random weights of the trained shapes are timed. Writes out/ipp1-latency-shipped.json and
    results/ipp1-latency-shipped.md.
    """
    from ipp1_common import ROOT, TARGETS
    os.environ["IPP1_FINAL_SMOKE"] = "1"   # ipp1_final trains one epoch per network: only the timing of predict() is wanted
    from ipp1_final import MLP, aligned_data, feats, split, train
    torch.manual_seed(0)
    gen, spec = MLP(46, 16, (256, 256, 128)).eval(), MLP(46, 16, (256, 256, 128)).eval()
    fg, fs = numpy_mlp(gen), numpy_mlp(spec)
    rng = np.random.default_rng(0)
    xraw = rng.normal(size=24).astype(np.float32)
    mu, sd = rng.normal(size=46).astype(np.float32), rng.random(46).astype(np.float32) + 0.5
    ym, ys = rng.normal(size=16).astype(np.float32), rng.random(16).astype(np.float32) + 0.5
    rw, rb = rng.normal(size=24).astype(np.float32), np.float32(0.1)   # the ridge of plasma_current: a dot product
    cols = [TARGETS.index("R_limiter"), TARGETS.index("Z_limiter")]
    ip, lim = TARGETS.index("plasma_current"), TARGETS.index("is_limited")
    x1 = torch.from_numpy((feats(xraw[None]) - mu) / sd)
    with torch.no_grad():
        assert np.allclose(fg(x1.numpy()), gen(x1).numpy(), atol=1e-4) and np.allclose(fs(x1.numpy()), spec(x1).numpy(), atol=1e-4)

    def step(x, limited):
        """The whole per-sample path in numpy; `limited` forces the branch (the real gate follows the predicted is_limited)."""
        f = np.concatenate([x, np.diff(x[:16]), np.diff(x[16:24])])   # 22 neighbouring-coil differences
        h = (f - mu) / sd
        out = fg(h)
        out[ip] = (x @ rw + rb - ym[ip]) / ys[ip]                     # ridge, standardised like the network output
        if limited:                                                  # the gate: the specialist answers the limiter point
            out[cols] = fs(h)[cols]
        return out * ys + ym

    res = {"cpu": cpu_name(), "cores": os.cpu_count(), "load_average_start": [round(v, 2) for v in os.getloadavg()],
           "parameters_general": int(sum(p.numel() for p in gen.parameters())), "parameters_limiter": int(sum(p.numel() for p in spec.parameters()))}
    with torch.no_grad():
        for threads in (1, 4):
            torch.set_num_threads(threads)
            res[f"torch_{threads}_thread_general_net_only"] = timeit(lambda: gen(x1))
            res[f"torch_{threads}_thread_both_nets"] = timeit(lambda: (gen(x1), spec(x1)))
    res["numpy_end_to_end_diverted"] = timeit(lambda: step(xraw, False))
    res["numpy_end_to_end_limited"] = timeit(lambda: step(xraw, True))
    # The predict() closure that ipp1_final.py builds for the same recipe (torch tensors, allocations per call), one sample, one thread.
    torch.set_num_threads(1)
    (df, X, Y, G, M), _ = aligned_data()
    _, dev, _ = split(G)
    predict = train("cand", X[dev], Y[dev], M[dev], G[dev], df.time.to_numpy()[dev], 0, 0)
    gate = predict(X[dev[:3000]])[:, lim] > 0.5
    for name, rows in (("diverted", np.flatnonzero(~gate)), ("limited", np.flatnonzero(gate))):
        if len(rows):
            xs = X[dev[rows[0]]][None]
            res[f"ipp1_final_predict_{name}"] = timeit(lambda: predict(xs), n=2000, warm=200)
    del X, Y, G, M, df
    if torch.backends.mps.is_available():
        dev = torch.device("mps")
        gm, sm = MLP(46, 16, (256, 256, 128)).to(dev).eval(), MLP(46, 16, (256, 256, 128)).to(dev).eval()

        def mps_limited():
            f = np.concatenate([xraw, np.diff(xraw[:16]), np.diff(xraw[16:24])])
            h = torch.from_numpy((f - mu) / sd)[None].to(dev)
            o = gm(h).cpu().numpy()[0]
            o[cols] = sm(h).cpu().numpy()[0][cols]
            return o * ys + ym
        with torch.no_grad():
            res["mps_end_to_end_limited_with_transfers"] = timeit(mps_limited, n=2000, warm=200)
    res["load_average_end"] = [round(v, 2) for v in os.getloadavg()]
    with open(OUT / "ipp1-latency-shipped.json", "w") as fh:
        json.dump(res, fh, indent=1, allow_nan=False)
    busy = max(res["load_average_start"][0], res["load_average_end"][0], res["load_average_end"][1]) >= 8
    L = ["# Latency of the shipped model pair (review finding H1a)", "",
         f"One sample, clean-input recipe `cand` of `analysis/ipp1_final.py`: the general network ({res['parameters_general']:,} parameters, 46 inputs, 16 outputs), the ridge for plasma_current "
         f"and the limiter network ({res['parameters_limiter']:,} parameters), gated by the predicted `is_limited`. Random weights of the trained shapes (weights do not change the timing). "
         "Same protocol as `results/ipp1-latency.md`: 5000 calls after 300 warm-up calls (2000 and 200 for the GPU row), times in milliseconds.", "",
         f"CPU: {res['cpu']} ({res['cores']} logical cores); the GPU row is the Apple GPU of the same chip through torch MPS. Load average (1, 5, 15 minutes) at the start "
         f"{res['load_average_start']}, at the end {res['load_average_end']}: "
         + ("the machine was busy (a load of 8 or more), so the medians are somewhat pessimistic and the tails are pessimistic: not a clean benchmark. "
            if busy else "below 8 in all windows, but other programs were running (not an isolated benchmark machine). ")
         + "The tail columns come from a general-purpose operating system without real-time guarantees: they show what happens on such a machine, they are not a worst-case bound.", "",
         "| setting | median | p99 | p99.9 | max |", "|---|---|---|---|---|"]
    for k, v in res.items():
        if isinstance(v, dict):
            L.append(f"| {k} | {v['median_ms']:.4f} | {v['p99_ms']:.4f} | {v['p999_ms']:.4f} | {v['max_ms']:.3f} |")
    L += ["", "`ipp1_final_predict_*` time the `predict()` closure that `analysis/ipp1_final.py` builds for the same recipe (the implementation used in the evaluation scripts: torch "
          "tensors and array copies on every call, one thread; one-epoch weights, which do not change the timing; the gate follows the network's own prediction on a real row). "
          "`numpy_end_to_end_*` is the whole per-sample path from the 24 raw inputs: 22 coil differences, standardisation, the general network, the ridge, the gate, "
          "(limited case only) the limiter network and the de-standardisation; `diverted` skips the limiter network, `limited` is the slower case and the one to quote as the bound. "
          "The `torch_*` rows time the networks only. **Included:** everything from the 24 raw numbers to the 16 outputs of the shipped pair, on one CPU core (numpy) or the GPU with its copies. "
          "**Not included:** collecting and integrating the coil signals, the noise-trained model needed for noisy inputs, the camera, and the accuracy of random weights (this is timing only)."]
    text = "\n".join(L) + "\n"
    target = ROOT / "repo/results/ipp1-latency-shipped.md"
    if target.exists() and "\n## Reading" in target.read_text(encoding="utf-8"):   # the hand-written reading is kept
        text += "\n## Reading" + target.read_text(encoding="utf-8").split("\n## Reading", 1)[1]
    target.write_text(text, encoding="utf-8")
    print(text)


if "--shipped" in sys.argv:
    shipped()
    sys.exit(0)


torch.manual_seed(0)
net = Net(24, 16).eval()
x1 = torch.randn(1, 24)
res = {"parameters": int(sum(p.numel() for p in net.parameters())), "cpu": cpu_name(), "cores": os.cpu_count(),
       "load_average_start": [round(v, 2) for v in os.getloadavg()]}


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
