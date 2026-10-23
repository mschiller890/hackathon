#!/usr/bin/env python
"""Can the limiter point be improved by changing only the limiter network of `cand`?  (protocol and rule: results/ipp1-limiter-swap.md, written before the first run)

Arms on the 119 development discharges, 5 group folds x 3 seeds, paired (seed = fold + 10 x s for every arm):
  arm 0  `cand` as is (cached predictions: ipp1_final.py cross-validation for seed 0, ipp1_search_dev.py for seeds 1 and 2)
  arm 1  only the limiter network replaced by the residual network of the best search trial (resA: width 192, depth 4, GELU, 100 epochs, loss weight 1.5 on the limiter targets)
  arm 2  CONTROL: cand's own limiter network trained with the same loss weight 1.5 and 100 epochs
The general network, the ridge for plasma_current and the gate of `cand` are untouched, so only R_limiter and Z_limiter can change; this is verified.

An arm PASSES only if: (1) the relative gain of the mean pooled MAE is at least 15 % for R_limiter AND Z_limiter; (2) for each of the two targets the absolute gain is larger than the
seed SD of the arm and of arm 0; (3) every other column is identical to arm 0 (checked) and the axis error in the limited rows does not get worse (printed); (4) the median latency of the
limited path (numpy path of results/ipp1-latency-shipped.md, one core, 5,000 calls) stays below 0.1 ms, measured here for all arms in the same run.
WINNER: arm 2 if it passes and (its gain is at least half of arm 1's gain for both targets, or arm 1 does not pass); else arm 1 if it passes; else cand stays.
LOCKED 30 discharges: only for the winner, once, logged; the script refuses a second run. Results freeze at 01:00.

    python -I analysis/ipp1_limiter_swap.py --job <fold>:<seed>      # trains the two limiter networks of one fold and seed, caches their limiter outputs
    python -I analysis/ipp1_limiter_swap.py --report                 # results/ipp1-limiter-swap.md (below the pre-written protocol), out/ipp1-limiter-swap.json
    python -I analysis/ipp1_limiter_swap.py --locked                 # the winner on the locked 30 discharges, once
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from scipy.special import erf

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_final as F
import ipp1_search_dev as SD
from ipp1_common import OUT, ROOT

REPO = ROOT / "repo"
CACHE = OUT / "ipp1-limiter-swap-cache"
MD = REPO / "results/ipp1-limiter-swap.md"
MARKER = "<!-- RESULTS BELOW -->"
LIM, LIM_NAMES = F.LIMITER, ["R_limiter", "Z_limiter"]
SEEDS = SD.SEEDS


def fit_specialist(arm, xtr, ytr, mtr, seed):
    """The limiter network of an arm: trained on the limited rows of the training discharges; predict(raw inputs) -> all 16 outputs."""
    hp = SD.configs()["resA"]["best_params"]
    rows = ytr[:, F.J["is_limited"]] > 0.5
    if arm == "arm1":
        return SD.fit_res(xtr, ytr, mtr, hp, seed, rows=rows)
    w = np.ones(len(F.TARGETS), dtype=np.float32)
    w[LIM] = hp["w_lim"]                     # F.fit_net normalises its loss by the sum of the mask, so a float mask is a weight matrix
    return F.fit_net(xtr, ytr, mtr.astype(np.float32) * w, seed, hp["epochs"], rows=rows)


def job(spec, threads):
    torch.set_num_threads(threads)
    fold, s = (int(v) for v in spec.split(":"))
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, _ = F.split(G)
    tr_l, te_l = F.group_folds(X[dev_idx], Y[dev_idx], G[dev_idx], 5)[fold]
    tr, te = dev_idx[tr_l], dev_idx[te_l]
    assert not set(G[tr]) & set(G[te])
    seed, t0 = fold + 10 * s, time.time()
    out = {arm: fit_specialist(arm, X[tr], Y[tr], M[tr], seed)(X[te])[:, LIM].astype(np.float32) for arm in ("arm1", "arm2")}
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE / f"{fold}_{s}.npz", idx=te, **out)
    print(f"fold {fold} seed {s}: {time.time() - t0:.0f} s", flush=True)


# ----------------------------------------------------------------------------- latency
def numpy_mlp(net):
    layers = [(m.weight.detach().numpy().T.copy(), m.bias.detach().numpy().copy()) for m in net.f if isinstance(m, torch.nn.Linear)]

    def forward(h):
        for i, (w, b) in enumerate(layers):
            h = h @ w + b
            if i < len(layers) - 1:
                h = h * (1.0 / (1.0 + np.exp(-h)))        # SiLU
        return h
    return forward


def numpy_resmlp(net):
    gelu = lambda h: 0.5 * h * (1.0 + erf(h / np.sqrt(2.0)))
    stem = (net.stem.weight.detach().numpy().T.copy(), net.stem.bias.detach().numpy().copy())
    blocks = [(b[0].weight.detach().numpy().T.copy(), b[0].bias.detach().numpy().copy(), b[3].weight.detach().numpy().T.copy(), b[3].bias.detach().numpy().copy()) for b in net.blocks]
    head = (net.head.weight.detach().numpy().T.copy(), net.head.bias.detach().numpy().copy())

    def forward(h):
        h = h @ stem[0] + stem[1]
        for w1, b1, w2, b2 in blocks:
            h = h + gelu(h @ w1 + b1) @ w2 + b2
        return gelu(h) @ head[0] + head[1]
    return forward


def timeit(fn, n=5000, warm=300):
    for _ in range(warm):
        fn()
    ts = np.empty(n)
    for i in range(n):
        a = time.perf_counter()
        fn()
        ts[i] = (time.perf_counter() - a) * 1000
    return {"median_ms": float(np.median(ts)), "p99_ms": float(np.percentile(ts, 99))}


def latency():
    """Median and p99 of the limited path (both networks run) for the three arms; random weights of the trained shapes, same protocol as ipp1_latency.py --shipped."""
    hp = SD.configs()["resA"]["best_params"]
    assert hp["act"] == "gelu"
    torch.manual_seed(0)
    gen, spec0 = F.MLP(46, 16, (256, 256, 128)).eval(), F.MLP(46, 16, (256, 256, 128)).eval()
    res = SD.S.ResMLP(46, 16, hp["width"], hp["depth"], hp["act"], hp["dropout"]).eval()
    for p in res.parameters():                       # the blocks start at zero; give them weights so that the timing is that of a trained network
        torch.nn.init.normal_(p, std=0.05)
    fg, f0, f1 = numpy_mlp(gen), numpy_mlp(spec0), numpy_resmlp(res)
    rng = np.random.default_rng(0)
    xraw = rng.normal(size=24).astype(np.float32)
    mu, sd = rng.normal(size=46).astype(np.float32), rng.random(46).astype(np.float32) + 0.5
    ym, ys = rng.normal(size=16).astype(np.float32), rng.random(16).astype(np.float32) + 0.5
    rw = rng.normal(size=24).astype(np.float32)
    ip = F.J["plasma_current"]
    with torch.no_grad():                            # the numpy forward passes agree with torch
        x1 = torch.randn(1, 46)
        assert np.allclose(f1(x1.numpy()), res(x1).numpy(), atol=1e-4) and np.allclose(f0(x1.numpy()), spec0(x1).numpy(), atol=1e-4)

    def step(spec):
        f = np.concatenate([xraw, np.diff(xraw[:16]), np.diff(xraw[16:24])])
        h = (f - mu) / sd
        out = fg(h)
        out[ip] = (xraw @ rw + 0.1 - ym[ip]) / ys[ip]
        out[LIM] = spec(h)[LIM]
        return out * ys + ym
    return {"arm0": timeit(lambda: step(f0)), "arm1": timeit(lambda: step(f1)), "arm2": timeit(lambda: step(f0))}


# ----------------------------------------------------------------------------- report
def build_arms(dev_idx, P0):
    pos = {int(i): k for k, i in enumerate(dev_idx)}
    arms = {"arm0": P0, "arm1": {}, "arm2": {}}
    for s in SEEDS:
        for arm in ("arm1", "arm2"):
            P = P0[s].copy()
            gate = P0[s][:, F.J["is_limited"]] > 0.5           # the gate of cand: its general network says limited
            for fold in range(5):
                d = np.load(CACHE / f"{fold}_{s}.npz")
                rows = np.array([pos[int(i)] for i in d["idx"]])
                g = gate[rows]
                P[np.ix_(rows[g], LIM)] = d[arm][g]
            arms[arm][s] = P
    return arms


def report(remeasure=False):
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, _ = F.split(G)
    P0 = SD.load_predictions(dev_idx)["cand"]
    assert len(P0) == len(SEEDS)
    arms = build_arms(dev_idx, P0)
    y, m = Y[dev_idx], M[dev_idx]
    limited = y[:, F.J["is_limited"]] > 0.5
    other = [j for j in range(len(F.TARGETS)) if j not in LIM]

    def mae(P, t, sel=None):
        j = F.J[t]
        k = m[:, j] if sel is None else (m[:, j] & sel)
        return float(np.abs(P[k, j] - y[k, j]).mean() * F.UNIT[t][0])
    mm = {a: {t: [mae(arms[a][s], t) for s in SEEDS] for t in LIM_NAMES} for a in arms}
    axis = {a: {t: [mae(arms[a][s], t, limited) for s in SEEDS] for t in ("R_mag_axis", "Z_mag_axis")} for a in arms}
    identical = {a: float(max(np.abs(arms[a][s][:, other] - arms["arm0"][s][:, other]).max() for s in SEEDS)) for a in arms}
    stored = OUT / "ipp1-limiter-swap.json"
    # The latency is measured once and kept (a new measurement on every report would change the table of a finished experiment); --remeasure repeats it.
    lat = json.loads(stored.read_text())["latency"] if stored.exists() and not remeasure else latency()
    mean, sd = np.mean, lambda v: float(np.std(v, ddof=1))
    verdict = {}
    for a in ("arm1", "arm2"):
        gain = {t: 1 - mean(mm[a][t]) / mean(mm["arm0"][t]) for t in LIM_NAMES}
        absg = {t: mean(mm["arm0"][t]) - mean(mm[a][t]) for t in LIM_NAMES}
        c1 = all(gain[t] >= 0.15 for t in LIM_NAMES)
        c2 = all(absg[t] > max(sd(mm[a][t]), sd(mm["arm0"][t])) for t in LIM_NAMES)
        c3 = identical[a] == 0.0 and all(mean(axis[a][t]) <= mean(axis["arm0"][t]) + 1e-12 for t in axis[a])
        c4 = lat[a]["median_ms"] < 0.1
        verdict[a] = {"gain": gain, "abs_gain_mm": absg, "c1_gain_15pct": c1, "c2_above_seed_sd": c2, "c3_nothing_else_changes": c3, "c4_latency": c4, "passes": c1 and c2 and c3 and c4}
    half = all(verdict["arm2"]["gain"][t] >= 0.5 * verdict["arm1"]["gain"][t] for t in LIM_NAMES)
    winner = "arm2" if verdict["arm2"]["passes"] and (half or not verdict["arm1"]["passes"]) else "arm1" if verdict["arm1"]["passes"] else "none"
    prev = json.loads(stored.read_text()) if stored.exists() else {}
    keep = {k: prev[k] for k in ("latency_post_hoc", "post_hoc_winner") if k in prev}    # written by --latency5
    stored.write_text(json.dumps({"winner": winner, "verdict": verdict, "mae_mm": mm, "latency": lat, **keep}, indent=1) + "\n")

    f = lambda v: f"{mean(v):.3g} ({sd(v):.2g})"
    name = {"arm0": "arm 0, `cand`", "arm1": "arm 1, residual limiter network", "arm2": "arm 2, control: own network, weight 1.5, 100 epochs"}
    L = ["", "## Results (119 development discharges, 5 folds x 3 seeds, pooled out-of-fold MAE in mm, mean (SD over seeds))", "",
         "| arm | R_limiter | Z_limiter | gain R | gain Z | axis in limited rows R / Z | median latency, limited path (ms) | p99 (ms) |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for a in arms:
        g = verdict.get(a)
        L.append(f"| {name[a]} | {f(mm[a]['R_limiter'])} | {f(mm[a]['Z_limiter'])} | " + (f"{100 * g['gain']['R_limiter']:.0f} % | {100 * g['gain']['Z_limiter']:.0f} % | " if g else "| | ")
                 + f"{mean(axis[a]['R_mag_axis']):.3g} / {mean(axis[a]['Z_mag_axis']):.3g} | {lat[a]['median_ms']:.4f} | {lat[a]['p99_ms']:.3f} |")
    L += ["", f"Check of criterion 3: the largest absolute difference of any column other than `R_limiter` and `Z_limiter` to arm 0 is {identical['arm1']:.1g} (arm 1) and {identical['arm2']:.1g} (arm 2).",
          "Latency: random weights of the trained shapes, numpy path from 24 raw inputs (differences, standardisation, general network, ridge, gate, limiter network, de-standardisation), one core, "
          f"load average {[round(v, 1) for v in __import__('os').getloadavg()]} (`nice` job on a shared laptop, so the tails are pessimistic).", "",
          "| arm | gain >= 15 % on both | gain above seed SD | nothing else changes | latency < 0.1 ms | **passes** |", "|---|---|---|---|---|---|"]
    yn = lambda b: "yes" if b else "no"
    for a in ("arm1", "arm2"):
        v = verdict[a]
        L.append(f"| {name[a]} | {yn(v['c1_gain_15pct'])} | {yn(v['c2_above_seed_sd'])} | {yn(v['c3_nothing_else_changes'])} | {yn(v['c4_latency'])} | **{yn(v['passes'])}** |")
    L += ["", f"Arm 2 gets {', '.join(f'{100 * verdict['arm2']['gain'][t] / verdict['arm1']['gain'][t]:.0f} % of the gain of arm 1 on {t}' for t in LIM_NAMES) if verdict['arm1']['gain']['R_limiter'] > 0 and verdict['arm1']['gain']['Z_limiter'] > 0 else 'no gain to compare'}.",
          "", f"**Winner by the rule: {'arm 2 (the control: only a hyperparameter changes)' if winner == 'arm2' else 'arm 1 (the residual limiter network)' if winner == 'arm1' else 'nobody, `cand` stays'}.**"]
    old = MD.read_text()
    ph = keep.get("latency_post_hoc")
    if ph:
        L += ["", "## Post hoc latency under the amended criterion 4 (5 runs at normal priority, each run measures the three arms one after the other)", "",
              "| run | load average (1, 5, 15 min) | cand (ms) | arm 1 (ms) | arm 2 (ms) | arm 1 p99 (ms) |", "|---:|---|---:|---:|---:|---:|"]
        L += [f"| {i + 1} | {r['load']} | {r['arm0']['median_ms']:.4f} | {r['arm1']['median_ms']:.4f} | {r['arm2']['median_ms']:.4f} | {r['arm1']['p99_ms']:.3f} |" for i, r in enumerate(ph["runs"])]
        mo = ph["median_of_medians_ms"]
        L += [f"| **median of the 5 runs** | | **{mo['arm0']:.4f}** | **{mo['arm1']:.4f}** | **{mo['arm2']:.4f}** | |", "",
              f"Amended criterion 4: median latency of arm 1 over the runs {mo['arm1']:.4f} ms against the limit 0.1 ms: **{'passes' if ph['arm1_passes'] else 'does not pass'}**; arm 1 costs {mo['arm1'] / mo['arm0']:.1f} times as much as `cand` "
              f"({mo['arm1']:.4f} against {mo['arm0']:.4f} ms). " + ("Criteria 1 to 3 hold as before, so arm 1 passes the amended rule (**post hoc**); the formal verdict of the original rule above is unchanged." if "post_hoc_winner" in keep else "")]
    head = old.split(MARKER)[0] + MARKER + "\n"
    reading = ("\n## Reading" + old.split("\n## Reading", 1)[1].split("\n## Locked", 1)[0]) if "\n## Reading" in old else ""   # hand-written, kept
    tail = ("\n## Locked" + old.split("\n## Locked", 1)[1]) if "\n## Locked" in old else ""
    MD.write_text(head + "\n".join(L) + "\n" + reading.rstrip("\n") + "\n" + tail)
    print("\n".join(L))


def latency_post_hoc():
    """The amended criterion 4: five runs of the latency measurement at normal priority, median over the runs; then the report is rewritten."""
    runs = []
    for _ in range(5):
        run = latency()
        runs.append({"load": [round(v, 1) for v in os.getloadavg()], **run})
        print({a: round(run[a]["median_ms"], 4) for a in run}, flush=True)
    med = {a: float(np.median([r[a]["median_ms"] for r in runs])) for a in ("arm0", "arm1", "arm2")}
    stored = OUT / "ipp1-limiter-swap.json"
    data = json.loads(stored.read_text())
    data["latency_post_hoc"] = {"runs": runs, "median_of_medians_ms": med, "arm1_passes": med["arm1"] < 0.1}
    v = data["verdict"]["arm1"]
    if data["latency_post_hoc"]["arm1_passes"] and v["c1_gain_15pct"] and v["c2_above_seed_sd"] and v["c3_nothing_else_changes"]:
        data["post_hoc_winner"] = "arm1"
    stored.write_text(json.dumps(data, indent=1) + "\n")
    report()


def locked():
    dec = json.loads((OUT / "ipp1-limiter-swap.json").read_text())
    winner, post_hoc = dec["winner"], False
    if winner == "none" and dec.get("post_hoc_winner"):       # accepted explicitly: the Lead amended criterion 4 after the first run (see the md)
        winner, post_hoc = dec["post_hoc_winner"], True
    done = OUT / "ipp1-limiter-swap-locked.done"
    assert winner in ("arm1", "arm2"), "no winner: the locked set is not used"
    assert not done.exists(), f"the locked set was scored already ({done.read_text().strip()})"
    torch.set_num_threads(2)
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, lock_idx = F.split(G)
    done.write_text(f"{datetime.now():%Y-%m-%d %H:%M} {winner}")          # written first: a crash does not allow a retry with other settings
    spec = fit_specialist(winner, X[dev_idx], Y[dev_idx], M[dev_idx], 0)
    cached = np.load(F.CACHE / "locked_cand.npz")
    assert np.array_equal(cached["idx"], lock_idx)
    P = cached["clean"].copy()
    gate = np.flatnonzero(P[:, F.J["is_limited"]] > 0.5)
    P[np.ix_(gate, LIM)] = spec(X[lock_idx])[gate][:, LIM]
    yl, ml = Y[lock_idx], M[lock_idx]
    mae = lambda Q, t: float(np.abs(Q[ml[:, F.J[t]], F.J[t]] - yl[ml[:, F.J[t]], F.J[t]]).mean() * F.UNIT[t][0])
    rows = {t: (mae(cached["clean"], t), mae(P, t)) for t in LIM_NAMES}
    other = [j for j in range(len(F.TARGETS)) if j not in LIM]
    text = ["", f"## Locked 30 discharges, scored once ({datetime.now():%Y-%m-%d %H:%M}, winner {winner}{' by the POST HOC amended criterion 4, not by the original rule' if post_hoc else ''}, trained on the 119 development discharges, seed 0)", "",
            "| target | `cand` (cached) | winner | change |", "|---|---:|---:|---:|"]
    text += [f"| {t} (mm) | {a:.3g} | {b:.3g} | {100 * (b / a - 1):+.0f} % |" for t, (a, b) in rows.items()]
    text += ["", f"All other columns identical to `cand`: {bool(np.array_equal(P[:, other], cached['clean'][:, other]))}. Pooled over the 8,761 rows of the 30 locked discharges (the limited rows have the target), one seed, clean inputs."]
    MD.write_text(MD.read_text().split("\n## Locked")[0].rstrip("\n") + "\n" + "\n".join(text) + "\n")
    print("\n".join(text))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job", default="")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--locked", action="store_true")
    ap.add_argument("--latency5", action="store_true", help="the amended criterion 4: 5 runs of the latency measurement at normal priority")
    ap.add_argument("--remeasure", action="store_true", help="measure the latency again in --report")
    a = ap.parse_args()
    assert not F.SMOKE
    if a.job:
        job(a.job, a.threads)
    if a.report:
        report(a.remeasure)
    if a.latency5:
        latency_post_hoc()
    if a.locked:
        locked()
