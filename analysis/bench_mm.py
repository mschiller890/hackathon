#!/usr/bin/env python
"""Benchmark of the millimetre deviation of a model from the institute's reconstruction (IPP task 1).

    python analysis/bench_mm.py [--model out/model/ipp1-selected.npz] [--set locked|dev|all] [--noisy] [--csv FILE] [--json OUT]
    python analysis/bench_mm.py --make-synthetic DIR      # SYNTHETIC data and model, to test this script without the IPP data

Data: by default the IPP file equil_data.csv (equil_data_noisy.csv with --noisy) from data/raw/ipp1-magnetic/uloha_1-magneticka_data/
under HACKATHON_HOME, else under the repository, as run.py looks for it. --csv takes any file with the 24 inputs IPR01..IPR16 and
FL01..FL08, a `discharge` column, optionally `time`, and any of the target columns; quantities whose column is absent are skipped.
Sets: `locked` = the 30 discharges of results/ipp1-locked-test-ids.txt (the set of results/ipp1-final.md), `dev` = all others, `all`.
Default: `locked` for the IPP data, `all` for --csv.

The estimates come from predict.Model of the repository root, the numpy code the jury runs. Every quantity is scored on the rows where
its reference value exists (X point and strike points only for diverted rows, limiter point only for limited rows, whatever the model's
own limited/diverted call is), which is how results/ipp1-final.md scores. The 95 % intervals are a cluster bootstrap: whole discharges
resampled with replacement, 1000 times, numpy RandomState(20261025), the same draws as ipp1_final.bootstrap. The output describes rows
only by discharge id and relative time; no input value is printed or written.
"""
import argparse
import json
import os
import sys
import textwrap
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # the root predict.py (the jury's copy), also under python -I
from predict import Model

DATA_SUB = Path("data/raw/ipp1-magnetic/uloha_1-magneticka_data")
LOCKED_IDS = REPO / "results/ipp1-locked-test-ids.txt"
INPUTS = [f"IPR{i:02d}" for i in range(1, 17)] + [f"FL{i:02d}" for i in range(1, 9)]
TARGETS = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "triangularity_upper", "triangularity_lower",
           "R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2",
           "R_limiter", "Z_limiter", "is_limited"]
POSITIONS = {"R_mag_axis": "osa R", "Z_mag_axis": "osa Z", "R_x_point": "X bod R", "Z_x_point": "X bod Z",
             "R_strike_point_1": "bod dopadu 1 R", "Z_strike_point_1": "bod dopadu 1 Z",
             "R_strike_point_2": "bod dopadu 2 R", "Z_strike_point_2": "bod dopadu 2 Z",
             "R_limiter": "bod limiteru R", "Z_limiter": "bod limiteru Z"}
AXIS_2D, CURRENT = "osa 2D vzdálenost", "proud plazmatu kA"
THRESHOLDS_MM = (0.1, 0.5, 1.0, 2.0, 5.0)
PCTS = (90, 95, 99, 99.9)
N_BOOT, BOOT_SEED = 1000, 20261025


def fail(msg):
    sys.exit(f"bench_mm: {msg}")


# ----------------------------------------------------------------------------- inputs
def default_model():
    homes = [Path(os.environ["HACKATHON_HOME"])] if os.environ.get("HACKATHON_HOME") else []
    cands = [h / "out/model/ipp1-selected.npz" for h in homes + [REPO, REPO.parent]] + [REPO / "model/ipp1-selected.npz"]
    return next((p for p in cands if p.exists()), cands[0])


def ipp_file(noisy):
    name = "equil_data_noisy.csv" if noisy else "equil_data.csv"
    homes = [Path(os.environ["HACKATHON_HOME"])] if os.environ.get("HACKATHON_HOME") else []
    for home in homes + [REPO, Path.cwd()]:
        if (home / DATA_SUB / name).exists():
            return home / DATA_SUB / name
    fail(f"data nenalezena: {name} není v {DATA_SUB} pod HACKATHON_HOME "
         f"({os.environ.get('HACKATHON_HOME', 'nenastaveno')}) ani pod {REPO}. Nastavte HACKATHON_HOME nebo použijte --csv.")


def read_table(path, model_inputs):
    import pandas as pd
    try:
        df = pd.read_csv(path)
    except Exception as e:  # unreadable or empty file: say so instead of a traceback
        fail(f"soubor {path} nelze načíst: {e}")
    missing = [c for c in model_inputs + ["discharge"] if c not in df.columns]
    if missing:
        fail(f"v {path} chybí sloupce: {', '.join(missing)}")
    present = [t for t in POSITIONS if t in df.columns]
    if not present:
        fail(f"v {path} není žádný sloupec polohy ({', '.join(POSITIONS)}), není s čím srovnávat")
    try:
        X = df[model_inputs].to_numpy(np.float64)
    except ValueError:
        fail(f"vstupní sloupce v {path} nejsou číselné")
    if not np.isfinite(X).all():
        fail(f"vstupní sloupce v {path} mají prázdné nebo nečíselné hodnoty")
    ref = {}
    for t in TARGETS:
        if t in df.columns:
            v = pd.to_numeric(df[t].astype(float) if df[t].dtype == bool else df[t], errors="coerce")
            ref[t] = v.to_numpy(np.float64)
    time = df["time"].to_numpy(np.float64) if "time" in df.columns else np.full(len(df), np.nan)
    return X, ref, df["discharge"].to_numpy(), time


def select(G, which):
    if which == "all":
        return np.ones(len(G), bool), "všechny výboje souboru"
    if not LOCKED_IDS.exists():
        fail(f"seznam odložených výbojů chybí: {LOCKED_IDS}")
    line = next((s for s in LOCKED_IDS.read_text().splitlines() if s.startswith("locked discharge ids")), None)
    if line is None:
        fail(f"v {LOCKED_IDS} chybí řádek 'locked discharge ids'")
    lock = np.array([int(v) for v in line.split(":", 1)[1].split()])
    rows = np.isin(G, lock)
    if which == "locked":
        return rows, f"odložené výboje ({len(lock)} v {LOCKED_IDS.relative_to(REPO)})"
    return ~rows, "vývojové výboje (všechny kromě odložených)"


# ----------------------------------------------------------------------------- statistics
def describe(a):
    """a: absolute deviations of one quantity (mm or kA)."""
    s = {"n": len(a), "mae": float(a.mean()), "median": float(np.median(a)), "rmse": float(np.sqrt((a ** 2).mean()))}
    s.update({f"p{p:g}": float(np.percentile(a, p)) for p in PCTS})
    s["max"] = float(a.max())
    return s


def boot_counts(n_groups):
    # same generator and order of draws as ipp1_final.bootstrap, so on the same set the MAE intervals agree with results/ipp1-final.md
    rng = np.random.RandomState(BOOT_SEED)
    return np.stack([np.bincount(rng.randint(0, n_groups, n_groups), minlength=n_groups) for _ in range(N_BOOT)]).astype(np.float64)


def ci(sums, counts, boot):
    """95 % percentile interval of sum/count over the bootstrap draws (per-discharge sums and counts)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        v = (boot @ sums) / (boot @ counts)
    return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


def quantity(a, inv, boot, mm=True):
    """Statistics of one quantity; a: absolute deviations, inv: discharge index (0..D-1) of each row."""
    s = describe(a)
    s["n_discharges"] = len(np.unique(inv))
    D = boot.shape[1]
    ct = np.bincount(inv, minlength=D).astype(np.float64)
    s["mae_ci95"] = ci(np.bincount(inv, weights=a, minlength=D), ct, boot)
    if mm:
        s["share_below_mm"] = {f"{t:g}": float((a < t).mean()) for t in THRESHOLDS_MM}
        s["share_below_1mm_ci95"] = ci(np.bincount(inv, weights=(a < 1.0).astype(float), minlength=D), ct, boot)
    return s


def run(model, X, ref, G, time):
    est = model.estimates(X)  # mm, kA, dimensionless
    col = {t: j for j, t in enumerate(model.outputs)}
    scale = dict(zip(model.outputs, model.scales))
    ids, inv = np.unique(G, return_inverse=True)
    boot = boot_counts(len(ids))
    R = {"quantities": {}, "absent": []}
    dev = {}  # signed deviation in report units, NaN where no reference
    for t in list(POSITIONS) + ["plasma_current"]:
        if t not in ref:
            R["absent"].append(t)
            continue
        dev[t] = est[:, col[t]] - ref[t] * scale[t]
        k = np.isfinite(dev[t])
        if k.any():
            R["quantities"][t] = quantity(np.abs(dev[t][k]), inv[k], boot, mm=t != "plasma_current")
    if "R_mag_axis" in dev and "Z_mag_axis" in dev:
        d = np.hypot(dev["R_mag_axis"], dev["Z_mag_axis"])
        k = np.isfinite(d)
        if k.any():
            R["axis_2d"] = quantity(d[k], inv[k], boot)
    if "is_limited" in ref:
        k = np.isfinite(ref["is_limited"])
        r, p = ref["is_limited"][k] > 0.5, est[k, col["is_limited"]] > 0.5
        R["limited_diverted"] = {"n": int(k.sum()), "agreement": float((r == p).mean()) if k.any() else float("nan"),
                                 "ref_limited_pred_limited": int((r & p).sum()), "ref_limited_pred_diverted": int((r & ~p).sum()),
                                 "ref_diverted_pred_limited": int((~r & p).sum()), "ref_diverted_pred_diverted": int((~r & ~p).sum()),
                                 "discharges_with_disagreement": len(np.unique(G[k][r != p]))}
    # worst rows: each row once, ranked by its largest position deviation
    pos = [t for t in POSITIONS if t in dev]
    A = np.abs(np.column_stack([dev[t] for t in pos]))
    worst_val = np.where(np.isfinite(A).any(1), np.nanmax(np.where(np.isfinite(A), A, -1.0), 1), np.nan)
    order = [i for i in np.argsort(-np.nan_to_num(worst_val, nan=-1.0)) if np.isfinite(worst_val[i])][:10]
    axis2d = np.hypot(dev["R_mag_axis"], dev["Z_mag_axis"]) if "R_mag_axis" in dev and "Z_mag_axis" in dev else np.full(len(G), np.nan)
    R["worst_rows"] = [{"discharge": G[i].item() if hasattr(G[i], "item") else G[i], "relative_time": None if np.isnan(time[i]) else float(time[i]),
                        "quantity": pos[int(np.nanargmax(np.where(np.isfinite(A[i]), A[i], -1.0)))], "deviation_mm": float(worst_val[i]),
                        "axis_2d_mm": None if np.isnan(axis2d[i]) else float(axis2d[i])} for i in order]
    return R


# ----------------------------------------------------------------------------- terminal output
def f(v):
    if v is None or not np.isfinite(v):
        return "–"
    return f"{v:.0f}" if abs(v) >= 1000 else f"{v:.3g}"


def render(R, head):
    W = 100
    out = ["Odchylka od rekonstrukce ústavu (absolutní hodnota |model − rekonstrukce|)", "=" * W]
    for k, v in head:
        out += textwrap.wrap(v, W, initial_indent=f"{k:<8}", subsequent_indent=" " * 8, break_on_hyphens=False)
    rows = [(POSITIONS[t], R["quantities"][t]) for t in POSITIONS if t in R["quantities"]]
    if "axis_2d" in R:
        rows.insert(2, (AXIS_2D, R["axis_2d"]))
    cur = R["quantities"].get("plasma_current")
    out += ["", "Rozdělení odchylky v mm (proud plazmatu v kA), na řádcích, kde rekonstrukce veličinu má", "-" * W,
            f"{'veličina':<19}{'řádků':>7}{'výb.':>5}" + "".join(f"{h:>8}" for h in ("MAE", "medián", "RMSE", "p90", "p95", "p99", "p99.9", "max"))]
    for name, s in rows + ([(CURRENT, cur)] if cur else []):
        out.append(f"{name:<19}{s['n']:>7}{s['n_discharges']:>5}" + "".join(f"{f(s[k]):>8}" for k in ("mae", "median", "rmse", "p90", "p95", "p99", "p99.9", "max")))
    out += ["", f"Podíl řádků s odchylkou pod prahem (%) a 95% interval (bootstrap po výbojích, {N_BOOT}×)", "-" * W,
            f"{'veličina':<19}" + "".join(f"{'<' + format(t, 'g'):>7}" for t in THRESHOLDS_MM) + f"  {'MAE [95% interval]':<21} {'pod 1 mm % [95% int.]'}"]
    for name, s in rows + ([(CURRENT, cur)] if cur else []):
        if "share_below_mm" in s:
            shares = "".join(f"{100 * s['share_below_mm'][format(t, 'g')]:>7.2f}" for t in THRESHOLDS_MM)
            lo, hi = s["share_below_1mm_ci95"]
            one = f"{100 * s['share_below_mm']['1']:.2f} [{100 * lo:.2f}, {100 * hi:.2f}]"
        else:
            shares, one = "".join(f"{'–':>7}" for _ in THRESHOLDS_MM), "–"
        mae = f"{f(s['mae'])} [{f(s['mae_ci95'][0])}, {f(s['mae_ci95'][1])}]"
        out.append(f"{name:<19}{shares}  {mae:<21} {one}")
    if R["absent"]:
        out += [""] + textwrap.wrap("Ve vstupu chybí, nehodnoceno: " + ", ".join(POSITIONS.get(t, CURRENT) for t in R["absent"]), W)
    c = R.get("limited_diverted")
    if c:
        out += ["", "Konfigurace limitovaná / divertorová (model: is_limited > 0.5)", "-" * W,
                f"shoda s rekonstrukcí {100 * c['agreement']:.2f} % z {c['n']} řádků; výbojů s aspoň jedním rozdílem: {c['discharges_with_disagreement']}",
                f"{'':<26}{'model limitovaná':>18}{'model divertorová':>19}",
                f"{'rekonstrukce limitovaná':<26}{c['ref_limited_pred_limited']:>18}{c['ref_limited_pred_diverted']:>19}",
                f"{'rekonstrukce divertorová':<26}{c['ref_diverted_pred_limited']:>18}{c['ref_diverted_pred_diverted']:>19}"]
    out += ["", "10 řádků s největší odchylkou (řádek jednou, podle jeho největší odchylky polohy)", "-" * W,
            f"{'#':>3}  {'výboj':>8}  {'rel. čas':>8}  {'veličina':<19}{'odchylka mm':>12}{'osa 2D mm':>11}"]
    for i, w in enumerate(R["worst_rows"], 1):
        t = "–" if w["relative_time"] is None else f"{w['relative_time']:.3f}"
        out.append(f"{i:>3}  {w['discharge']!s:>8}  {t:>8}  {POSITIONS[w['quantity']]:<19}{f(w['deviation_mm']):>12}{f(w['axis_2d_mm']):>11}")
    out += ["", "Čísla jsou shoda s rekonstrukcí ústavu, ne odchylka od plazmatu samotného."]
    return "\n".join(line.rstrip() for line in out)


# ----------------------------------------------------------------------------- synthetic test data and model
def make_synthetic(root, n_discharges=60, seed=0):
    """Write a SYNTHETIC stand-in in the IPP layout under root (data and a model in the .npz format of export_model.py).

    Data: analysis/synth_equilibrium.py, discharges numbered 1..n so that the locked ids up to n fall into the locked set. It provides only
    8 targets (no strike points, no limiter point, no upper/lower triangularity). Model: the network shape of the shipped one with random
    hidden layers and a least-squares output layer (no torch needed), trained on the synthetic development discharges, and a least-squares
    line for the plasma current. It exists to run this benchmark end to end, not as a model of COMPASS.
    """
    import pandas as pd
    sys.path.insert(0, str(REPO / "analysis"))
    import synth_equilibrium as S
    data = S.generate(n_discharges, 100, seed=seed)
    df = pd.DataFrame(data["X"].astype(np.float64), columns=S.SIGNAL_NAMES)
    df.insert(0, "time", data["time"])
    df.insert(0, "discharge", data["groups"] + 1)
    for j, t in enumerate(S.TARGET_NAMES):
        df[t] = data["Y"][:, j]
    rng = np.random.default_rng(seed + 1)
    noisy = df.copy()
    noisy[S.SIGNAL_NAMES] += 0.15 * df[S.SIGNAL_NAMES].std().to_numpy() * rng.standard_normal((len(df), len(S.SIGNAL_NAMES)))
    d = Path(root) / DATA_SUB
    d.mkdir(parents=True, exist_ok=True)
    df.to_csv(d / "equil_data.csv", index=False)
    noisy.to_csv(d / "equil_data_noisy.csv", index=False)
    (Path(root) / "SYNTHETIC-README.txt").write_text("SYNTHETIC data and model made by analysis/bench_mm.py --make-synthetic. Not IPP data, not COMPASS.\n")

    rows, _ = select(df["discharge"].to_numpy(), "dev")
    X = df.loc[rows, INPUTS].to_numpy(np.float64)
    Y = np.column_stack([df.loc[rows, t].to_numpy(np.float64) if t in df else np.full(rows.sum(), np.nan) for t in TARGETS])
    F = Model.features(X).astype(np.float64)
    mu, sd = F.mean(0), F.std(0) + 1e-9
    widths = [F.shape[1], 256, 256, 128]
    hidden = [(rng.standard_normal((a, b)) * np.sqrt(2.0 / a), 0.1 * rng.standard_normal(b)) for a, b in zip(widths[:-1], widths[1:])]

    def last_hidden(Fz):
        h = Fz
        for W, b in hidden:
            h = h @ W + b
            h = h / (1 + np.exp(-h))
        return h

    H = last_hidden((F - mu) / sd)
    arrays = {}
    for tag, keep in (("gen", np.ones(len(Y), bool)), ("spec", Y[:, TARGETS.index("is_limited")] > 0.5)):
        ym, ys = np.zeros(len(TARGETS)), np.ones(len(TARGETS))
        W3, b3 = np.zeros((widths[-1], len(TARGETS))), np.zeros(len(TARGETS))
        for j in range(len(TARGETS)):
            k = keep & np.isfinite(Y[:, j])
            if k.sum() < 10:
                continue  # a target the synthetic data do not have: the output stays 0
            ym[j], ys[j] = Y[k, j].mean(), Y[k, j].std() + 1e-9
            Hk = np.column_stack([H[k], np.ones(k.sum())])
            sol = np.linalg.solve(Hk.T @ Hk + 1e-3 * np.eye(Hk.shape[1]), Hk.T @ ((Y[k, j] - ym[j]) / ys[j]))
            W3[:, j], b3[j] = sol[:-1], sol[-1]
        for i, (W, b) in enumerate(hidden + [(W3, b3)]):
            arrays[f"{tag}_W{i}"], arrays[f"{tag}_b{i}"] = W.astype(np.float32), b.astype(np.float32)
        arrays[f"{tag}_mu"], arrays[f"{tag}_sd"] = mu.astype(np.float32), sd.astype(np.float32)
        arrays[f"{tag}_ym"], arrays[f"{tag}_ys"] = ym.astype(np.float32), ys.astype(np.float32)
    ip = Y[:, TARGETS.index("plasma_current")]
    xm, xs = X.mean(0), X.std(0) + 1e-12
    A = np.column_stack([(X - xm) / xs, np.ones(len(X))])
    c = np.linalg.solve(A.T @ A + 1e-6 * np.eye(A.shape[1]), A.T @ ip)
    arrays["ridge_w"], arrays["ridge_b"] = c[:-1] / xs, np.array(c[-1] - (c[:-1] * xm / xs).sum())
    scales = np.array([1000.0 if t.startswith(("R_", "Z_")) else 1e-3 if t == "plasma_current" else 1.0 for t in TARGETS])
    m = Path(root) / "out/model"
    m.mkdir(parents=True, exist_ok=True)
    np.savez(m / "ipp1-synthetic.npz", **arrays, input_names=np.array(INPUTS), output_names=np.array(TARGETS), output_scales=scales,
             limiter_columns=np.array([TARGETS.index("R_limiter"), TARGETS.index("Z_limiter")]),
             plasma_current_column=np.array(TARGETS.index("plasma_current")), is_limited_column=np.array(TARGETS.index("is_limited")))
    n_dev = len(np.unique(df.loc[rows, "discharge"]))
    meta = {"synthetic": True, "trained_on": f"SYNTHETIC: {n_dev} synthetic development discharges ({int(rows.sum())} rows) of analysis/synth_equilibrium.py "
            f"seed {seed}; random hidden layers 256-256-128 (SiLU, numpy seed {seed + 1}) and a least-squares output layer, least-squares line for the plasma current"}
    (m / "ipp1-synthetic.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(f"wrote {d}/equil_data.csv and equil_data_noisy.csv ({len(df)} rows, {n_discharges} discharges) and {m}/ipp1-synthetic.npz (.json)")


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", help="exported model .npz (default: out/model/ipp1-selected.npz under HACKATHON_HOME or the repository)")
    ap.add_argument("--set", choices=("locked", "dev", "all"), help="which discharges (default: locked for the IPP data, all for --csv)")
    ap.add_argument("--noisy", action="store_true", help="the IPP noisy file equil_data_noisy.csv instead of equil_data.csv")
    ap.add_argument("--csv", help="any CSV with the 24 inputs, `discharge`, optionally `time`, and target columns")
    ap.add_argument("--json", help="also write all numbers to this JSON file")
    ap.add_argument("--make-synthetic", metavar="DIR", help="write SYNTHETIC data and a synthetic model under DIR and stop")
    args = ap.parse_args()
    if args.make_synthetic:
        make_synthetic(args.make_synthetic)
        return
    if args.csv and args.noisy:
        fail("--noisy platí jen pro data ústavu; zašuměný soubor předejte přímo přes --csv")
    model_path = Path(args.model) if args.model else default_model()
    if not model_path.exists():
        fail(f"model nenalezen: {model_path} (vytvoří ho analysis/export_model.py nebo run.py; jiný předejte přes --model)")
    try:
        model = Model(model_path)
    except Exception as e:  # a wrong or truncated file
        fail(f"model {model_path} nelze načíst: {e}")
    if model.inputs != INPUTS or model.outputs != TARGETS:
        fail(f"model {model_path} nemá očekávané vstupy a výstupy (24 vstupů IPR01..FL08, 16 výstupů v pořadí export_model.py)")
    meta_path = model_path.with_suffix(".json")
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    path = Path(args.csv) if args.csv else ipp_file(args.noisy)
    if not path.exists():
        fail(f"soubor nenalezen: {path}")
    which = args.set or ("all" if args.csv else "locked")
    X, ref, G, time = read_table(path, model.inputs)
    rows, set_text = select(G, which)
    if not rows.any():
        fail(f"sada '{which}' nemá v {path} žádný řádek")
    X, G, time = X[rows], G[rows], time[rows]
    ref = {t: v[rows] for t, v in ref.items()}
    R = run(model, X, ref, G, time)
    kind = "vlastní CSV" if args.csv else ("zašuměné vstupy" if args.noisy else "čisté vstupy")
    head = [("model", f"{model_path}" + (f" ({meta['trained_on']})" if "trained_on" in meta else "")),
            ("data", f"{path} ({kind})"),
            ("sada", f"{which}: {set_text}; {len(np.unique(G))} výbojů, {len(G)} řádků")]
    if meta.get("synthetic"):
        head.append(("POZOR", "syntetický model, čísla nevypovídají o COMPASS"))
    print(render(R, head))
    if args.json:
        R["protocol"] = {"model": str(model_path), "model_trained_on": meta.get("trained_on"), "data": str(path), "data_kind": kind,
                         "set": which, "n_discharges": len(np.unique(G)), "n_rows": len(G),
                         "bootstrap": {"resamples": N_BOOT, "unit": "discharge", "seed": BOOT_SEED, "interval": "95 % percentile"},
                         "units": "positions mm, plasma current kA; deviations are model minus the institute's reconstruction"}
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(R, indent=1, ensure_ascii=False) + "\n")
        print(f"\nJSON: {args.json}")


if __name__ == "__main__":
    main()
