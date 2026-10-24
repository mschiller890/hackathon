#!/usr/bin/env python
"""Export the shipped models as files that analysis/predict.py runs with numpy alone: the selected model (`cand` of analysis/ipp1_final.py)
and, after it, the noise model for noisy measurements (recipe base_aug with a causal window of 5 rows, results/ipp1-noise-window.md).

Trained on the 119 DEVELOPMENT discharges, seed 0, exactly as the job `locked:cand` of ipp1_final.py (so the exported model is the model behind every number reported for the 30
locked discharges, and analysis/check_predict.py can reproduce the cached predictions). It is the same training code: the networks and the ridge are made by ipp1_final.fit_net and
fit_ridge_col, and their weights and constants are read out of the returned functions.

The noise model is trained as the locked stage of the experiment analysis/ipp1_noise_window.py (lead repository; its numbers are in
results/ipp1-noise-window.md): the baseline network of ipp1_common.fit_mlp (60 epochs, seed 0) on all 119 development discharges, clean rows plus
one copy corrupted per row with ipp1_final.corrupt (noise 0.15, drift 0.15 of each input's SD, seed AUG_SEED + 50) BEFORE windowing, every row
given as the inputs of rows t, t-1 .. t-4 of its discharge (predict.window_rows, the same function predict.py uses).

    HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/export_model.py       (about 1.5 minutes: 2 CPU threads, then 4 for the noise model)

Writes out/model/ipp1-selected.npz and .json, then out/model/ipp1-noisy.npz and .json. THE WEIGHTS ARE DERIVED FROM THE CONFIDENTIAL IPP DATA: out/ is git-ignored and the files go only into the
submission package for the organizers.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_final as F
from ipp1_common import OUT, fit_mlp
from predict import Model, window_rows

MODEL = OUT / "model"
NOISY_WINDOW = 5


def closure(fn, names):
    """The variables a function of ipp1_final closes over (weights and scaling constants live there)."""
    cells = dict(zip(fn.__code__.co_freevars, (c.cell_contents for c in fn.__closure__)))
    assert set(names) <= set(cells), (names, sorted(cells))
    return cells


def main():
    torch.set_num_threads(2)
    assert not F.SMOKE
    started = time.time()
    (df, X, Y, G, M), XN = F.aligned_data()
    _, dev_idx, lock_idx = F.split(G)
    xt, yt, mt = X[dev_idx], Y[dev_idx], M[dev_idx]
    # the recipe `cand` of ipp1_final.train: a general network, a network on the limited rows, a ridge for the plasma current (seed 0, 150 epochs)
    gen = F.fit_net(xt, yt, mt, 0, 150)
    spec = F.fit_net(xt, yt, mt, 0, 150, rows=yt[:, F.J["is_limited"]] > 0.5)
    ridge = F.fit_ridge_col(xt, yt, mt, F.J["plasma_current"])
    arrays = {}
    for tag, fn in (("gen", gen), ("spec", spec)):
        c = closure(fn, ("net", "mu32", "sd32", "ym", "ys"))
        layers = [m for m in c["net"].f if isinstance(m, nn.Linear)]
        assert len(layers) == 4 and all(isinstance(m, (nn.Linear, nn.SiLU)) for m in c["net"].f)
        for i, m in enumerate(layers):
            arrays[f"{tag}_W{i}"] = m.weight.detach().numpy().T.astype(np.float32)      # (inputs, outputs)
            arrays[f"{tag}_b{i}"] = m.bias.detach().numpy().astype(np.float32)
        arrays[f"{tag}_mu"], arrays[f"{tag}_sd"] = c["mu32"].astype(np.float32), c["sd32"].astype(np.float32)
        arrays[f"{tag}_ym"], arrays[f"{tag}_ys"] = c["ym"].astype(np.float32), c["ys"].astype(np.float32)
    rc = closure(ridge, ("w", "b"))
    arrays["ridge_w"], arrays["ridge_b"] = np.asarray(rc["w"], dtype=np.float64), np.asarray(rc["b"], dtype=np.float64)
    inputs = [c for c in df.columns if c.startswith(("IPR", "FL"))]
    assert len(inputs) == 24 and inputs[:16] == [f"IPR{i:02d}" for i in range(1, 17)] and inputs[16:] == [f"FL{i:02d}" for i in range(1, 9)]
    scales = np.array([F.UNIT[t][0] for t in F.TARGETS], dtype=np.float64)
    units = [F.UNIT[t][1] for t in F.TARGETS]
    meta = {"input_names": inputs, "output_names": list(F.TARGETS), "output_units": units, "output_scale_to_unit": scales.tolist(),
            "raw_units": "positions in m, plasma current in A, shape numbers and is_limited dimensionless; the output scale turns them into mm and kA",
            "features": "the 24 inputs, then the 15 differences of neighbouring coils IPR02-IPR01 ... IPR16-IPR15, then the 7 differences FL02-FL01 ... FL08-FL07, inside ONE row (46 columns); "
                        "rows are independent, no time ordering is used",
            "gate": f"R_limiter and Z_limiter come from the limiter network ('spec') on the rows where the general network predicts is_limited > 0.5",
            "plasma_current": "linear (ridge) fit on the 24 raw inputs, not from the network",
            "activation": "SiLU", "hidden_layers": [256, 256, 128],
            "trained_on": f"the {len(np.unique(G[dev_idx]))} development discharges ({len(dev_idx)} rows), seed 0, recipe cand of analysis/ipp1_final.py (150 epochs, Huber 0.5)",
            "confidential": "weights are derived from the confidential IPP data: for the submission package, never for git"}
    MODEL.mkdir(parents=True, exist_ok=True)
    np.savez(MODEL / "ipp1-selected.npz", **arrays, input_names=np.array(inputs), output_names=np.array(F.TARGETS), output_scales=scales,
             limiter_columns=np.array(F.LIMITER), plasma_current_column=np.array(F.J["plasma_current"]), is_limited_column=np.array(F.J["is_limited"]))
    (MODEL / "ipp1-selected.json").write_text(json.dumps(meta, indent=1) + "\n")
    size = sum(p.stat().st_size for p in MODEL.glob("ipp1-selected.*"))
    print(f"wrote {MODEL}/ipp1-selected.npz and .json, {size / 1e6:.2f} MB in total, {time.time() - started:.0f} s")
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
