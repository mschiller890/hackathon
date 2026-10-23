#!/usr/bin/env python
"""Does the activation function of the shipped general network matter? SiLU (as shipped) against ReLU and GELU. Protocol: results/ipp1-activation.md (written before the first run).

    HACKATHON_HOME=... nice -n 10 ~/.venvs/hackathon/bin/python -I analysis/ipp1_activation.py [--threads 2]     train what is missing (cached per activation, seed, fold)
    ... --probe                                                                                                 time 3 epochs of one network and stop
    ... --report                                                                                                results/ipp1-activation.md (below the protocol)

Imports analysis/ipp1_final.py and swaps its MLP class for one with the chosen activation; ipp1_final.py itself is not changed. Development discharges only; the locked set is never read.
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_final as F
from ipp1_common import OUT, TARGETS, UNIT, group_folds

CACHE = OUT / "ipp1-activation-cache"
MD = Path(__file__).resolve().parents[1] / "results/ipp1-activation.md"
MARKER = "<!-- RESULTS BELOW -->"
ACTS = {"silu": nn.SiLU, "relu": nn.ReLU, "gelu": nn.GELU}
SEEDS = [0, 1, 2]
FIVE = ["R_mag_axis", "Z_mag_axis", "R_x_point", "R_strike_point_1", "elongation"]
J = F.J


def make_mlp(act):
    class MLPAct(F.MLP):
        """The MLP of ipp1_final with another activation: same layers in the same order, so the same seed gives the same initial weights."""

        def __init__(self, n_in, n_out, widths):
            nn.Module.__init__(self)
            layers, d = [], n_in
            for w in widths:
                layers += [nn.Linear(d, w), ACTS[act]()]
                d = w
            layers.append(nn.Linear(d, n_out))
            self.f = nn.Sequential(*layers)
    return MLPAct


def setup():
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, _ = F.split(G)
    return X, Y, G, M, dev_idx


def run(threads):
    torch.set_num_threads(threads)
    X, Y, G, M, dev_idx = setup()
    folds = group_folds(X[dev_idx], Y[dev_idx], G[dev_idx], 5)
    CACHE.mkdir(parents=True, exist_ok=True)
    for s in SEEDS:                       # seed 0 uses the seed of fold k, as the shipped recipe; paired: all activations share seed, folds and initial weights
        for k, (tr_l, te_l) in enumerate(folds):
            tr, te = dev_idx[tr_l], dev_idx[te_l]
            assert not set(G[tr]) & set(G[te])
            for act in ACTS:
                f = CACHE / f"{act}_s{s}_f{k}.npz"
                if f.exists():
                    continue
                F.MLP = make_mlp(act)
                t0 = time.time()
                pred = F.fit_net(X[tr], Y[tr], M[tr], k + 10 * s, 150)
                np.savez(f, idx=te, pred=pred(X[te]).astype(np.float32))
                print(f"{act} seed {s} fold {k}: {time.time() - t0:.0f} s", flush=True)
    print("done", flush=True)


def probe(threads):
    torch.set_num_threads(threads)
    X, Y, G, M, dev_idx = setup()
    tr_l, te_l = group_folds(X[dev_idx], Y[dev_idx], G[dev_idx], 5)[0]
    tr = dev_idx[tr_l]
    for act in ACTS:
        F.MLP = make_mlp(act)
        t0 = time.time()
        F.fit_net(X[tr], Y[tr], M[tr], 0, 3)
        dt = time.time() - t0
        print(f"{act}: 3 epochs on {len(tr)} rows in {dt:.1f} s; 150 epochs = {50 * dt / 60:.1f} min; 45 networks = {45 * 50 * dt / 3600:.1f} h (all activations)", flush=True)


def load_oof(act, s, n_rows):
    parts = [np.load(CACHE / f"{act}_s{s}_f{k}.npz") for k in range(5)]
    idx = np.concatenate([p["idx"] for p in parts])
    P = np.full((n_rows, len(TARGETS)), np.nan, dtype=np.float32)
    P[idx] = np.concatenate([p["pred"] for p in parts])
    return P, idx


def metrics(P, Y, M, idx, rev):
    """Pooled MAE (mm) of the five asked targets, the axis (mean of R and Z), the same by polarity group, and the mean nRMSE over the 16 targets."""
    out = {}
    m = np.zeros(len(Y), dtype=bool)
    m[idx] = True
    for t in FIVE:
        j = J[t]
        k = M[:, j] & m
        out[t] = float((np.abs(P[k, j] - Y[k, j]) * UNIT[t][0]).mean())
        for name, grp in (("reversed", rev), ("usual", ~rev)):
            kk = k & grp
            out[f"{t}|{name}"] = float((np.abs(P[kk, j] - Y[kk, j]) * UNIT[t][0]).mean())
    out["axis"] = (out["R_mag_axis"] + out["Z_mag_axis"]) / 2
    out["axis|reversed"] = (out["R_mag_axis|reversed"] + out["Z_mag_axis|reversed"]) / 2
    out["axis|usual"] = (out["R_mag_axis|usual"] + out["Z_mag_axis|usual"]) / 2
    nr = []
    for t in TARGETS:
        j = J[t]
        k = M[:, j] & m
        e = (P[k, j] - Y[k, j]).astype(np.float64)
        nr.append(np.sqrt((e ** 2).mean()) / Y[k, j].astype(np.float64).std())
    out["nrmse16"] = float(np.mean(nr))
    return out


def report():
    X, Y, G, M, dev_idx = setup()
    # polarity of a discharge = sign of its median reference plasma current (positive = reversed), as analysis/ipp1_confidence.py
    ipc = Y[:, J["plasma_current"]]
    sign = {d: np.sign(np.nanmedian(ipc[G == d])) for d in np.unique(G[dev_idx])}
    rev = np.array([sign.get(d, -1) > 0 for d in G])
    n_rev = sum(v > 0 for v in sign.values())
    res = {a: [] for a in ACTS}
    for a in ACTS:
        for s in SEEDS:
            P, idx = load_oof(a, s, len(Y))
            res[a].append(metrics(P, Y, M, idx, rev))
    # sanity: seed 0 SiLU against the cached out-of-fold predictions of the shipped recipe on the columns the gate and the ridge do not change
    chk = None
    try:
        keep = [j for j in range(len(TARGETS)) if j not in (J["plasma_current"], *F.LIMITER)]
        diffs = []
        for k in range(5):
            c, p = np.load(F.CACHE / f"cv_cand_{k}.npz"), np.load(CACHE / f"silu_s0_f{k}.npz")
            assert np.array_equal(c["idx"], p["idx"])
            diffs.append(np.abs(c["clean"][:, keep] - p["pred"][:, keep]).max())
        chk = float(max(diffs))
    except FileNotFoundError:
        pass
    keys = ["axis", *FIVE, "axis|reversed", "axis|usual", "nrmse16"]
    mean = lambda a, key: float(np.mean([r[key] for r in res[a]]))
    sd = lambda a, key: float(np.std([r[key] for r in res[a]], ddof=1))
    L = ["", "## Results", "", f"Out-of-fold predictions of the general network on the 119 development discharges, pooled over the 5 folds; mean over the 3 seeds, and the SD over the 3 seeds in brackets. "
         f"MAE in mm; `nrmse16` = mean over the 16 targets of RMSE / SD of the target (dimensionless). `axis` = mean of the MAE of R_mag_axis and Z_mag_axis. "
         f"Reversed polarity = {n_rev} development discharges, usual = {len(sign) - n_rev}.", "",
         "| quantity | SiLU (shipped) | ReLU | GELU |", "|---|---:|---:|---:|"]
    for key in keys:
        L.append(f"| {key} | " + " | ".join(f"{mean(a, key):.4g} ({sd(a, key):.2g})" for a in ACTS) + " |")
    L += ["", "Paired difference to SiLU (activation minus SiLU, same seed, folds and initial weights), mean over the 3 seeds and its SD; negative = better than SiLU.", "",
          "| quantity | ReLU minus SiLU | GELU minus SiLU |", "|---|---:|---:|"]
    for key in keys:
        d = {a: np.array([r[key] for r in res[a]]) - np.array([r[key] for r in res["silu"]]) for a in ("relu", "gelu")}
        L.append(f"| {key} | " + " | ".join(f"{d[a].mean():+.4g} ({d[a].std(ddof=1):.2g})" for a in ("relu", "gelu")) + " |")
    L.append("")
    verdict = "SiLU stays"
    better = []
    for a in ("relu", "gelu"):
        ok = all(mean("silu", key) - mean(a, key) > sd("silu", key) for key in ("axis", "nrmse16"))
        if ok:
            better.append(a)
    if better:
        verdict = "NOT 'SiLU stays': " + " and ".join(a.upper() for a in better) + " is better than SiLU by more than the seed SD of SiLU on both the axis and the 16-target mean"
    L += [f"**Verdict: {verdict}.**", "", "Rule (fixed in advance): SiLU stays unless another activation beats SiLU by more than the SD over the 3 seeds of SiLU itself, on BOTH `axis` and `nrmse16`.", ""]
    if chk is not None:
        L += [f"Check: the SiLU control of seed 0 against the cached out-of-fold predictions of the shipped recipe (`cv_cand_*`), on the 13 columns that the plasma current ridge and the limiter gate do not change: largest absolute difference {chk:.2g} (raw units).", ""]
    old = MD.read_text()
    MD.write_text(old.split(MARKER)[0] + MARKER + "\n" + "\n".join(L) + "\n")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.probe:
        probe(a.threads)
    elif a.report:
        report()
    else:
        run(a.threads)


if __name__ == "__main__":
    main()
