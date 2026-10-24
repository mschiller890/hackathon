#!/usr/bin/env python
"""Export the noise model: the model for noisy measurements, as a file that predict.py runs with numpy alone (the model for clean inputs is made by ipn_model.py).

The noise model is trained as the locked stage of the experiment analysis/ipp1_noise_window.py (its numbers are in results/ipp1-noise-window.md): the baseline network of
ipp1_common.fit_mlp (60 epochs, seed 0) on all 119 development discharges, clean rows plus one copy corrupted per row with ipp1_final.corrupt (noise 0.15, drift 0.15 of each
input's SD, seed AUG_SEED + 50) BEFORE windowing, every row given as the inputs of rows t, t-1 .. t-4 of its discharge (predict.window_rows, the same function predict.py uses).

    python analysis/export_model.py       (about 20 s)

Writes out/model/ipp1-noisy.npz and .json. THE WEIGHTS ARE DERIVED FROM THE CONFIDENTIAL IPP DATA: out/ is git-ignored.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # predict.py of the repository root
import ipp1_final as F
from ipp1_common import OUT, fit_mlp
from predict import Model, window_rows

MODEL = OUT / "model"
NOISY_WINDOW = 5


def main():
    torch.set_num_threads(4)
    assert not F.SMOKE
    (df, X, Y, G, M), XN = F.aligned_data()
    _, dev_idx, lock_idx = F.split(G)
    inputs = [c for c in df.columns if c.startswith(("IPR", "FL"))]
    assert len(inputs) == 24 and inputs[:16] == [f"IPR{i:02d}" for i in range(1, 17)] and inputs[16:] == [f"FL{i:02d}" for i in range(1, 9)]
    scales = np.array([F.UNIT[t][0] for t in F.TARGETS], dtype=np.float64)
    units = [F.UNIT[t][1] for t in F.TARGETS]
    MODEL.mkdir(parents=True, exist_ok=True)
    export_noisy(df, X, XN, Y, G, M, dev_idx, lock_idx, inputs, scales, units)


def export_noisy(df, X, XN, Y, G, M, dev_idx, lock_idx, inputs, scales, units):
    """The noise model: the locked stage of ipp1_noise_window.py for its config base_aug_stack5 (same seeds, epochs and rows)."""
    torch.set_num_threads(4)
    started = time.time()
    times = df.time.to_numpy()
    tr = dev_idx
    W = window_rows(G, times, NOISY_WINDOW)
    xa = X.copy()
    xa[tr] = F.corrupt(X[tr], G[tr], times[tr], X[tr].std(axis=0), F.NOISE, F.DRIFT, F.AUG_SEED + 50)
    xt = np.concatenate([X[W[tr]].reshape(len(tr), -1), xa[W[tr]].reshape(len(tr), -1)]).astype(np.float32)
    yt, mt = np.tile(Y[tr], (2, 1)), np.tile(M[tr], (2, 1))
    pred, net, (mu, sd) = fit_mlp(xt, yt, mt, 60, seed=0)
    layers = [m for m in net.f if isinstance(m, nn.Linear)]
    assert len(layers) == 4 and all(isinstance(m, (nn.Linear, nn.SiLU)) for m in net.f)
    arrays = {}
    for i, m in enumerate(layers):
        arrays[f"gen_W{i}"] = m.weight.detach().numpy().T.astype(np.float32)
        arrays[f"gen_b{i}"] = m.bias.detach().numpy().astype(np.float32)
    arrays["gen_mu"], arrays["gen_sd"] = np.asarray(mu, np.float32), np.asarray(sd, np.float32)
    arrays["gen_ym"], arrays["gen_ys"] = np.nanmean(yt, 0).astype(np.float32), (np.nanstd(yt, 0) + 1e-9).astype(np.float32)
    path = MODEL / "ipp1-noisy.npz"
    np.savez(path, **arrays, input_names=np.array(inputs), output_names=np.array(F.TARGETS), output_scales=scales, window_rows=np.array(NOISY_WINDOW),
             limiter_columns=np.array(F.LIMITER), plasma_current_column=np.array(F.J["plasma_current"]), is_limited_column=np.array(F.J["is_limited"]))
    # the numpy forward pass of predict.py must give what the torch network gives (locked noisy rows, windowed)
    xs = XN[W[lock_idx[:2000]]].reshape(len(lock_idx[:2000]), -1).astype(np.float32)
    ref = pred(xs)
    rel = np.nanmax(np.median(np.abs(Model(path).predict(xs) - ref) / (np.abs(ref) + 1e-6), 0))
    assert rel < 1e-4, rel
    meta = {"input_names": inputs, "output_names": list(F.TARGETS), "output_units": units, "output_scale_to_unit": scales.tolist(),
            "raw_units": "positions in m, plasma current in A, shape numbers and is_limited dimensionless; the output scale turns them into mm and kA",
            "window_rows": NOISY_WINDOW,
            "window_rule": f"each estimate uses the 24 inputs of rows t, t-1, .. t-{NOISY_WINDOW - 1} of the SAME discharge ordered by time, stacked in that order "
                           f"({24 * NOISY_WINDOW} columns, current row first); where the discharge has fewer earlier rows its first row is repeated; never a later row. "
                           "k counts rows, so the input must have the sampling interval of the training data",
            "features": "the stacked raw inputs only (no neighbouring-coil differences, no ridge, no limiter network): one network answers all 16 outputs",
            "activation": "SiLU", "hidden_layers": [256, 256, 128],
            "trained_on": f"the {len(np.unique(G[dev_idx]))} development discharges ({len(dev_idx)} rows) twice: clean, and one copy corrupted per row with "
                          f"noise {F.NOISE} and drift {F.DRIFT} of each input's SD (ipp1_final.corrupt, seed {F.AUG_SEED + 50}) before windowing; "
                          "baseline network of ipp1_common.fit_mlp, 60 epochs, MSE, seed 0 (config base_aug_stack5 of ipp1_noise_window.py, locked stage)",
            "evidence": "results/ipp1-noise-window.md: on the 30 locked discharges with the provided noisy inputs, axis MAE R 1.85 mm and Z 1.25 mm",
            "numpy_check": f"median relative difference numpy vs torch on 2000 locked noisy rows, max over outputs: {rel:.1e}",
            "confidential": "weights are derived from the confidential IPP data: for the submission package, never for git"}
    (MODEL / "ipp1-noisy.json").write_text(json.dumps(meta, indent=1) + "\n")
    size = sum(p.stat().st_size for p in MODEL.glob("ipp1-noisy.*"))
    print(f"wrote {MODEL}/ipp1-noisy.npz and .json (noise model, window {NOISY_WINDOW} rows), {size / 1e6:.2f} MB in total, {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
