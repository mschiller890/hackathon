#!/usr/bin/env python
"""Latence sítě pro rozhodnutí v reálném čase (REQ-002). Váhy dobu nemění, proto se měří čerstvě inicializovaná síť
natrénované architektury.

    HACKATHON_HOME=<složka hackathonu> python -I analysis/latency.py
    HACKATHON_HOME=<složka hackathonu> python -I analysis/latency.py --shipped    # nasazená dvojice z final_evaluation.py

Zapíše out/ipp1-latency.{json,md}. Markdown uvádí procesor a zátěž (load average) během běhu: chvost (p99,9, max) naměřený
na vytíženém stroji nebo v operačním systému bez záruk reálného času není mez. Pro čistý údaj spusťte, když `uptime`
ukazuje load average pod 8.
"""
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
from common import OUT, Net


def cpu_name():
    """Název procesoru z macOS, jinak to, co ohlásí platform."""
    try:
        return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return platform.processor() or platform.machine()


def time_calls(function, n_calls=5000, n_warmup=300):
    """Doba jednoho volání v milisekundách: medián, p99, p99,9 a maximum z `n_calls` volání po zahřátí."""
    for _ in range(n_warmup):
        function()
    durations_ms = np.empty(n_calls)
    for i in range(n_calls):
        started = time.perf_counter()
        function()
        durations_ms[i] = (time.perf_counter() - started) * 1000
    return {"median_ms": float(np.median(durations_ms)), "p99_ms": float(np.percentile(durations_ms, 99)),
            "p999_ms": float(np.percentile(durations_ms, 99.9)), "max_ms": float(durations_ms.max())}


def numpy_forward_pass(network):
    """Dopředný průchod MLP z final_evaluation.py v čistém numpy (SiLU) pro jeden vzorek."""
    layers = [(layer.weight.detach().numpy().T.copy(), layer.bias.detach().numpy().copy())
              for layer in network.layers if isinstance(layer, torch.nn.Linear)]

    def forward(hidden):
        for i, (weights, bias) in enumerate(layers):
            hidden = hidden @ weights + bias
            if i < len(layers) - 1:
                hidden = hidden * (1.0 / (1.0 + np.exp(-hidden)))
        return hidden
    return forward


def measure_shipped_pair():
    """Latence nasazené dvojice modelů z final_evaluation.py (recept `cand`): jeden vzorek od 24 surových vstupů k 16 výstupům.

    Dvojice je obecná síť (24 vstupů + 22 rozdílů sousedních cívek = 46 vstupů), ridge pro plasma_current a síť naučená na
    limiterových řádcích, která odpovídá R_limiter a Z_limiter, když obecná síť předpoví is_limited > 0,5. Váhy dobu nemění,
    měří se náhodné váhy natrénovaných tvarů. Zapíše out/ipp1-latency-shipped.json a results/ipp1-latency-shipped.md.
    """
    from common import REPO, TARGETS
    os.environ["IPP1_FINAL_SMOKE"] = "1"   # final_evaluation učí každou síť jednu epochu: zajímá nás jen doba predict()
    from final_evaluation import MLP, add_neighbour_differences, aligned_data, split, train
    torch.manual_seed(0)
    general_net, limiter_net = MLP(46, 16, (256, 256, 128)).eval(), MLP(46, 16, (256, 256, 128)).eval()
    general_forward, limiter_forward = numpy_forward_pass(general_net), numpy_forward_pass(limiter_net)
    rng = np.random.default_rng(0)
    raw_sample = rng.normal(size=24).astype(np.float32)
    input_mean, input_std = rng.normal(size=46).astype(np.float32), rng.random(46).astype(np.float32) + 0.5
    target_mean, target_std = rng.normal(size=16).astype(np.float32), rng.random(16).astype(np.float32) + 0.5
    ridge_weights, ridge_bias = rng.normal(size=24).astype(np.float32), np.float32(0.1)   # ridge pro plasma_current: skalární součin
    limiter_columns = [TARGETS.index("R_limiter"), TARGETS.index("Z_limiter")]
    current_column, is_limited_column = TARGETS.index("plasma_current"), TARGETS.index("is_limited")
    features = torch.from_numpy((add_neighbour_differences(raw_sample[None]) - input_mean) / input_std)
    with torch.no_grad():
        assert (np.allclose(general_forward(features.numpy()), general_net(features).numpy(), atol=1e-4)
                and np.allclose(limiter_forward(features.numpy()), limiter_net(features).numpy(), atol=1e-4))

    def end_to_end(sample, limited):
        """Celá cesta jednoho vzorku v numpy; `limited` vynutí větev (skutečné rozhodnutí se řídí předpovězeným is_limited)."""
        extended = np.concatenate([sample, np.diff(sample[:16]), np.diff(sample[16:24])])   # 22 rozdílů sousedních cívek
        standardized = (extended - input_mean) / input_std
        output = general_forward(standardized)
        output[current_column] = (sample @ ridge_weights + ridge_bias - target_mean[current_column]) / target_std[current_column]   # ridge, standardizovaný jako výstup sítě
        if limited:                                                  # rozhodnutí: bod limiteru odpoví specialista
            output[limiter_columns] = limiter_forward(standardized)[limiter_columns]
        return output * target_std + target_mean

    result = {"cpu": cpu_name(), "cores": os.cpu_count(), "load_average_start": [round(v, 2) for v in os.getloadavg()],
              "parameters_general": int(sum(p.numel() for p in general_net.parameters())),
              "parameters_limiter": int(sum(p.numel() for p in limiter_net.parameters()))}
    with torch.no_grad():
        for threads in (1, 4):
            torch.set_num_threads(threads)
            result[f"torch_{threads}_thread_general_net_only"] = time_calls(lambda: general_net(features))
            result[f"torch_{threads}_thread_both_nets"] = time_calls(lambda: (general_net(features), limiter_net(features)))
    result["numpy_end_to_end_diverted"] = time_calls(lambda: end_to_end(raw_sample, False))
    result["numpy_end_to_end_limited"] = time_calls(lambda: end_to_end(raw_sample, True))
    # Uzávěr predict(), který final_evaluation.py staví pro stejný recept (torch tenzory, alokace při každém volání), jeden vzorek, jedno vlákno.
    torch.set_num_threads(1)
    (table, measurements, targets, discharges, exists), _ = aligned_data()
    _, development_rows, _ = split(discharges)
    predict = train("cand", measurements[development_rows], targets[development_rows], exists[development_rows],
                    discharges[development_rows], table.time.to_numpy()[development_rows], 0, 0)
    is_limited_predicted = predict(measurements[development_rows[:3000]])[:, is_limited_column] > 0.5
    for name, rows in (("diverted", np.flatnonzero(~is_limited_predicted)), ("limited", np.flatnonzero(is_limited_predicted))):
        if len(rows):
            one_row = measurements[development_rows[rows[0]]][None]
            result[f"ipp1_final_predict_{name}"] = time_calls(lambda: predict(one_row), n_calls=2000, n_warmup=200)
    del measurements, targets, discharges, exists, table
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        general_gpu, limiter_gpu = MLP(46, 16, (256, 256, 128)).to(device).eval(), MLP(46, 16, (256, 256, 128)).to(device).eval()

        def gpu_limited_with_transfers():
            extended = np.concatenate([raw_sample, np.diff(raw_sample[:16]), np.diff(raw_sample[16:24])])
            standardized = torch.from_numpy((extended - input_mean) / input_std)[None].to(device)
            output = general_gpu(standardized).cpu().numpy()[0]
            output[limiter_columns] = limiter_gpu(standardized).cpu().numpy()[0][limiter_columns]
            return output * target_std + target_mean
        with torch.no_grad():
            result["mps_end_to_end_limited_with_transfers"] = time_calls(gpu_limited_with_transfers, n_calls=2000, n_warmup=200)
    result["load_average_end"] = [round(v, 2) for v in os.getloadavg()]
    with open(OUT / "ipp1-latency-shipped.json", "w") as json_file:
        json.dump(result, json_file, indent=1, allow_nan=False)
    busy = max(result["load_average_start"][0], result["load_average_end"][0], result["load_average_end"][1]) >= 8
    lines = ["# Latency of the shipped model pair (review finding H1a)", "",
             f"One sample, clean-input recipe `cand` of `analysis/final_evaluation.py`: the general network ({result['parameters_general']:,} parameters, 46 inputs, 16 outputs), the ridge for plasma_current "
             f"and the limiter network ({result['parameters_limiter']:,} parameters), gated by the predicted `is_limited`. Random weights of the trained shapes (weights do not change the timing). "
             "Same protocol as `results/ipp1-latency.md`: 5000 calls after 300 warm-up calls (2000 and 200 for the GPU row), times in milliseconds.", "",
             f"CPU: {result['cpu']} ({result['cores']} logical cores); the GPU row is the Apple GPU of the same chip through torch MPS. Load average (1, 5, 15 minutes) at the start "
             f"{result['load_average_start']}, at the end {result['load_average_end']}: "
             + ("the machine was busy (a load of 8 or more), so the medians are somewhat pessimistic and the tails are pessimistic: not a clean benchmark. "
                if busy else "below 8 in all windows, but other programs were running (not an isolated benchmark machine). ")
             + "The tail columns come from a general-purpose operating system without real-time guarantees: they show what happens on such a machine, they are not a worst-case bound.", "",
             "| setting | median | p99 | p99.9 | max |", "|---|---|---|---|---|"]
    for name, timing in result.items():
        if isinstance(timing, dict):
            lines.append(f"| {name} | {timing['median_ms']:.4f} | {timing['p99_ms']:.4f} | {timing['p999_ms']:.4f} | {timing['max_ms']:.3f} |")
    lines += ["", "`ipp1_final_predict_*` time the `predict()` closure that `analysis/final_evaluation.py` builds for the same recipe (the implementation used in the evaluation scripts: torch "
              "tensors and array copies on every call, one thread; one-epoch weights, which do not change the timing; the gate follows the network's own prediction on a real row). "
              "`numpy_end_to_end_*` is the whole per-sample path from the 24 raw inputs: 22 coil differences, standardisation, the general network, the ridge, the gate, "
              "(limited case only) the limiter network and the de-standardisation; `diverted` skips the limiter network, `limited` is the slower case and the one to quote as the bound. "
              "The `torch_*` rows time the networks only. **Included:** everything from the 24 raw numbers to the 16 outputs of the shipped pair, on one CPU core (numpy) or the GPU with its copies. "
              "**Not included:** collecting and integrating the coil signals, the noise-trained model needed for noisy inputs, the camera, and the accuracy of random weights (this is timing only)."]
    text = "\n".join(lines) + "\n"
    report_file = REPO / "results/ipp1-latency-shipped.md"
    if report_file.exists() and "\n## Reading" in report_file.read_text(encoding="utf-8"):   # ručně psaný komentář „Reading“ se zachová
        text += "\n## Reading" + report_file.read_text(encoding="utf-8").split("\n## Reading", 1)[1]
    report_file.write_text(text, encoding="utf-8")
    print(text)


if "--shipped" in sys.argv:
    measure_shipped_pair()
    sys.exit(0)


# ===================================================================================================================
# Základní síť: jeden vzorek, dávky, numpy, GPU
# ===================================================================================================================
torch.manual_seed(0)
net = Net(24, 16).eval()
one_sample = torch.randn(1, 24)
result = {"parameters": int(sum(p.numel() for p in net.parameters())), "cpu": cpu_name(), "cores": os.cpu_count(),
          "load_average_start": [round(v, 2) for v in os.getloadavg()]}


with torch.no_grad():
    for threads in (1, 4):
        torch.set_num_threads(threads)
        result[f"cpu_{threads}_thread_single_sample"] = time_calls(lambda: net(one_sample))
    torch.set_num_threads(4)
    for batch_size in (64, 1024, 4096):
        batch = torch.randn(batch_size, 24)
        result[f"cpu_batch_{batch_size}"] = time_calls(lambda: net(batch), n_calls=500, n_warmup=50)
    # Týž dopředný průchod v čistém numpy, aby bylo vidět, že v řídicí smyčce není potřeba žádný framework pro hluboké učení.
    layers = [(layer.weight.detach().numpy().T.copy(), layer.bias.detach().numpy().copy())
              for layer in net.layers if isinstance(layer, torch.nn.Linear)]
    one_sample_numpy = one_sample.numpy()

    def numpy_forward(hidden=one_sample_numpy):
        for i, (weights, bias) in enumerate(layers):
            hidden = hidden @ weights + bias
            if i < len(layers) - 1:
                hidden = hidden * (1.0 / (1.0 + np.exp(-hidden)))  # SiLU
        return hidden
    assert np.allclose(numpy_forward(), net(one_sample).numpy(), atol=1e-5), "numpy forward pass differs from torch"
    result["numpy_single_sample"] = time_calls(numpy_forward)
    # Celá cesta na CPU: surový vzorek v numpy dovnitř, standardizace, síť, zpětná standardizace, numpy ven.
    input_mean, input_std = np.random.randn(24).astype(np.float32), np.random.rand(24).astype(np.float32) + 0.5
    target_mean, target_std = np.random.randn(16).astype(np.float32), np.random.rand(16).astype(np.float32) + 0.5
    raw_sample = (one_sample_numpy * input_std + input_mean).astype(np.float32)
    result["cpu_end_to_end_numpy"] = time_calls(lambda: numpy_forward((raw_sample - input_mean) / input_std) * target_std + target_mean)
    result["mps_available"] = bool(torch.backends.mps.is_available())
    if result["mps_available"]:
        device = torch.device("mps")
        net_gpu = Net(24, 16).to(device).eval()
        sample_gpu = torch.randn(1, 24, device=device)

        def gpu_single_sample():
            net_gpu(sample_gpu)
            torch.mps.synchronize()
        result["mps_single_sample"] = time_calls(gpu_single_sample, n_calls=2000, n_warmup=200)

        def gpu_end_to_end():
            # numpy dovnitř, standardizace na CPU, kopie na GPU, síť, kopie zpět (kopie zpět počká na výsledek).
            on_gpu = torch.from_numpy((raw_sample - input_mean) / input_std).to(device)
            return net_gpu(on_gpu).cpu().numpy() * target_std + target_mean
        result["mps_single_sample_with_transfers"] = time_calls(gpu_end_to_end, n_calls=2000, n_warmup=200)
        batch_gpu = torch.randn(4096, 24, device=device)

        def gpu_batch():
            net_gpu(batch_gpu)
            torch.mps.synchronize()
        result["mps_batch_4096"] = time_calls(gpu_batch, n_calls=300, n_warmup=50)
result["load_average_end"] = [round(v, 2) for v in os.getloadavg()]
with open(OUT / "ipp1-latency.json", "w") as json_file:
    json.dump(result, json_file, indent=1, allow_nan=False)

loaded = max(result["load_average_start"][0], result["load_average_end"][0], result["load_average_end"][1]) >= 8
lines = ["# Latency (REQ-002)", "", "The assignment asks for a reaction in units to tens of milliseconds. "
         f"Network: {result['parameters']:,} parameters, 24 inputs, 16 outputs (a freshly initialised network of the trained "
         "architecture; weights do not change the timing). Times in milliseconds.", "",
         f"CPU: {result['cpu']} ({result['cores']} logical cores); GPU rows: the Apple GPU of the same chip through torch MPS. "
         f"Load average (1, 5, 15 minutes) at the start {result['load_average_start']}, at the end {result['load_average_end']}; "
         f"{'the machine was shared and busy (a load of 8 or more in the 1 or 5 minute average on 10 cores), so the medians are somewhat pessimistic and the tails are pessimistic: not a clean benchmark.' if loaded else 'the load average was below 8 in all windows.'} "
         "The tail columns (p99.9, max) come from 5000 calls (500 or fewer for the batch rows) on a general-purpose operating system "
         "without real-time guarantees: they show what happens on such a machine, they are not a worst-case bound. "
         "A loaded machine earlier gave p99 0.65 ms and max 21 ms for a single CPU sample (reviewer measurement, load 16), still inside a 1 to 10 ms budget at the p99.", "",
         "| setting | median | p99 | p99.9 | max |", "|---|---|---|---|---|"]
for name, timing in result.items():
    if isinstance(timing, dict):
        lines.append(f"| {name} | {timing['median_ms']:.4f} | {timing['p99_ms']:.4f} | {timing['p999_ms']:.4f} | {timing['max_ms']:.3f} |")
lines += ["", "cpu_end_to_end_numpy and mps_single_sample_with_transfers include the standardisation of the inputs, the copy to and "
          "from the GPU (the GPU row) and the de-standardisation of the outputs, which any real loop needs; the other single-sample "
          "rows time the network only. What these numbers do not cover: collecting and integrating the coil signals, and the "
          "accuracy on really noisy signals (see the robustness results)."]
(OUT / "ipp1-latency.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
