#!/usr/bin/env python
"""Export the shipped model (`cand` of analysis/ipp1_final.py) as one file that analysis/predict.py runs with numpy alone.

Trained on the 119 DEVELOPMENT discharges, seed 0, exactly as the job `locked:cand` of ipp1_final.py (so the exported model is the model behind every number reported for the 30
locked discharges, and analysis/check_predict.py can reproduce the cached predictions). It is the same training code: the networks and the ridge are made by ipp1_final.fit_net and
fit_ridge_col, and their weights and constants are read out of the returned functions.

    HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/export_model.py       (about 1 minute with --no-axis-net, 2 CPU threads)

Also trains, on the same rows and seed, a separate network for R_mag_axis and Z_mag_axis only (ipp1_final.fit_axis_net, 256-256-128,
400 epochs) and stores it in the same file under the keys axis_*; predict.py then takes the two axis columns from it. `--no-axis-net`
writes the file without it, as before.

Writes out/model/ipp1-selected.npz and out/model/ipp1-selected.json. THE WEIGHTS ARE DERIVED FROM THE CONFIDENTIAL IPP DATA: out/ is git-ignored and the files go only into the
submission package for the organizers.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_final as F
from ipp1_common import OUT

MODEL = OUT / "model"
AXIS_ARCH, AXIS_EPOCHS = (256, 256, 128), 400


def closure(fn, names):
    """The variables a function of ipp1_final closes over (weights and scaling constants live there)."""
    cells = dict(zip(fn.__code__.co_freevars, (c.cell_contents for c in fn.__closure__)))
    assert set(names) <= set(cells), (names, sorted(cells))
    return cells


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-axis-net", action="store_true", help="do not train and store the separate network for R_mag_axis and Z_mag_axis")
    args = ap.parse_args()
    torch.set_num_threads(2)
    assert not F.SMOKE
    started = time.time()
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, lock_idx = F.split(G)
    xt, yt, mt = X[dev_idx], Y[dev_idx], M[dev_idx]
    # the recipe `cand` of ipp1_final.train: a general network, a network on the limited rows, a ridge for the plasma current (seed 0, 150 epochs)
    gen = F.fit_net(xt, yt, mt, 0, 150)
    spec = F.fit_net(xt, yt, mt, 0, 150, rows=yt[:, F.J["is_limited"]] > 0.5)
    ridge = F.fit_ridge_col(xt, yt, mt, F.J["plasma_current"])
    nets = [("gen", gen, 4), ("spec", spec, 4)]
    if not args.no_axis_net:
        nets.append(("axis", F.fit_axis_net(xt, yt, mt, 0, AXIS_EPOCHS, AXIS_ARCH), len(AXIS_ARCH) + 1))
    arrays = {}
    for tag, fn, depth in nets:
        c = closure(fn, ("net", "mu32", "sd32", "ym", "ys"))
        layers = [m for m in c["net"].f if isinstance(m, nn.Linear)]
        assert len(layers) == depth and all(isinstance(m, (nn.Linear, nn.SiLU)) for m in c["net"].f)
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
    if not args.no_axis_net:
        arrays["axis_columns"] = np.array(F.AXIS)
        meta["axis_net"] = {"arch": list(AXIS_ARCH), "epochs": AXIS_EPOCHS, "targets": [F.TARGETS[j] for j in F.AXIS]}
    MODEL.mkdir(parents=True, exist_ok=True)
    np.savez(MODEL / "ipp1-selected.npz", **arrays, input_names=np.array(inputs), output_names=np.array(F.TARGETS), output_scales=scales,
             limiter_columns=np.array(F.LIMITER), plasma_current_column=np.array(F.J["plasma_current"]), is_limited_column=np.array(F.J["is_limited"]))
    (MODEL / "ipp1-selected.json").write_text(json.dumps(meta, indent=1) + "\n")
    size = sum(p.stat().st_size for p in MODEL.glob("ipp1-selected.*"))
    print(f"wrote {MODEL}/ipp1-selected.npz and .json, {size / 1e6:.2f} MB in total, {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
