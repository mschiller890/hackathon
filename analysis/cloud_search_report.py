#!/usr/bin/env python
"""Score the predictions saved by cloud_search.py; write results/cloud-search.{md,json} and the figures.

    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_search_report.py

Reads $HACKATHON_HOME/out/cloud-search/ (predictions, tuning studies, latency). Only aggregate numbers leave that
folder. If results/cloud-search-findings.md exists its text is placed at the top of the report (written by hand
after reading the tables).
"""
import json
import os
import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_common as C
from cloud_search_lib import CLS, LIM, SUMMARY, summary

REPO = Path(__file__).resolve().parent.parent
RES = Path(os.environ.get("CLOUD_SEARCH_RESULTS", REPO / "results"))  # redirected for smoke tests
WORK = (C.OUT / "cloud-search").resolve()
FAST_MS = 0.1  # "far below 1 ms": the recommendation must be at least ten times faster than the 1 ms budget
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
                                                          "#008300", "#6250d6", "#e34948")
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

_, X, Y, G, M = C.load()
FOLDS = C.group_folds(X, Y, G, 5)
FOLD_IDS = list(range(5))  # a subset only for smoke tests (--folds)
ALIASES = json.load(open(WORK / "aliases.json")) if (WORK / "aliases.json").exists() else {}
LAT = json.load(open(WORK / "latency.json"))["latency_ms"] if (WORK / "latency.json").exists() else {}


def pred(fold, name, tag=""):
    p = WORK / "pred" / f"fold{fold}" / f"{name}{tag}.npy"
    return np.load(p) if p.exists() else None


def stem(fold, name, tag=""):
    """Name of the trained configuration behind a candidate name (several names can share one configuration)."""
    if pred(fold, f"{name}_s0", tag) is not None or pred(fold, name, tag) is not None:
        return name
    for key, names in ALIASES.items():
        f, s = key.split("/")
        if int(f) == fold and name in names:
            return s.rsplit("_s", 1)[0]
    return None


def ens(fold, name, k, tag=""):
    s = stem(fold, name, tag)
    if s is None:
        return None
    ps = [pred(fold, f"{s}_s{i}", tag) for i in range(k)]
    return None if any(p is None for p in ps) else np.mean(ps, 0)


def col(a, cols):
    return None if a is None else a[:, cols]


def hybrid(fold, main, lim, gate):
    m, l, g = ens(fold, *main), ens(fold, *lim), pred(fold, gate)
    if m is None or l is None or g is None:
        return None
    out = m.copy()
    out[:, LIM] = l
    out[:, CLS] = g
    return out


def single(name):
    return lambda f: pred(f, name)


# key -> (label, builder(fold), latency parts [(model file stem, count)])
ENTRIES = {
    "ridge": ("ridge", single("ridge"), [("ridge_linear", 1)]),
    "baseline": ("baseline MLP 256-256-128 (60 ep, seed 0)", single("baseline_s0"), [("baseline_untrained_net", 1)]),
    "baseline_ens5": ("baseline MLP x5 seeds", lambda f: ens(f, "baseline", 5), [("baseline_untrained_net", 5)]),
    "nn_best": ("tuned MLP / ResMLP (1 seed)", lambda f: ens(f, "nn_best", 1), [("nn_best_s0", 1)]),
    "nn_best_ens5": ("tuned MLP / ResMLP x5 seeds", lambda f: ens(f, "nn_best", 5), [("nn_best_s0", 5)]),
    "nn_best_ens10": ("tuned MLP / ResMLP x10 seeds", lambda f: ens(f, "nn_best", 10), [("nn_best_s0", 10)]),
    "nn_mlp": ("best plain MLP (1 seed)", lambda f: ens(f, "nn_arch-mlp", 1), [("@nn_arch-mlp", 1)]),
    "nn_resmlp": ("best residual MLP (1 seed)", lambda f: ens(f, "nn_arch-resmlp", 1), [("@nn_arch-resmlp", 1)]),
    "feat_raw": ("best net on standardised inputs", lambda f: ens(f, "nn_feat-raw", 1), [("@nn_feat-raw", 1)]),
    "feat_diff": ("best net on inputs + neighbour differences", lambda f: ens(f, "nn_feat-diff", 1), [("@nn_feat-diff", 1)]),
    "feat_pca16": ("best net on 16 PCA components", lambda f: ens(f, "nn_feat-pca16", 1), [("@nn_feat-pca16", 1)]),
    "feat_pca24": ("best net on 24 PCA components", lambda f: ens(f, "nn_feat-pca24", 1), [("@nn_feat-pca24", 1)]),
    "attn": ("transformer over the 24 coil values (1 seed)", lambda f: ens(f, "attn", 1), [("attn_s0", 1)]),
    "attn_ens5": ("transformer x5 seeds", lambda f: ens(f, "attn", 5), [("attn_s0", 5)]),
    "lgbm": ("LightGBM per target", single("lgbm"), [("lgbm", 1)]),
    "et": ("ExtraTrees per target", single("et"), [("et", 1)]),
    "hyb_nn": ("tuned net x5 + limiter specialist net x5 + gate net",
               lambda f: hybrid(f, ("nn_best", 5), ("lim_nn", 5), "gate_nn"),
               [("nn_best_s0", 5), ("lim_nn_s0", 5)]),
    "hyb_lgbm": ("tuned net x5 + limiter LightGBM + gate LightGBM",
                 lambda f: hybrid(f, ("nn_best", 5), ("lim_lgbm", 1), "gate_lgbm"),
                 [("nn_best_s0", 5), ("lim_lgbm", 1)]),
}


def agg(builder):
    preds = [builder(f) for f in FOLD_IDS]
    if any(p is None for p in preds):
        return None
    rs = [C.score(p, Y[FOLDS[f][1]], M[FOLDS[f][1]]) for p, f in zip(preds, FOLD_IDS)]
    sums = [summary(r) for r in rs]
    out = {"summary": float(np.mean(sums)), "summary_std": float(np.std(sums)), "summary_per_fold": sums,
           "limiter_z_per_fold": [r["Z_limiter"]["mae"] for r in rs],
           "per_target": {t: {k: float(np.mean([r[t][k] for r in rs])) for k in ("mae", "r2", "nrmse")} | {"unit": rs[0][t]["unit"]}
                          for t in C.TARGETS},
           "is_limited_accuracy": float(np.mean([r["is_limited"]["accuracy"] for r in rs]))}
    for t in ("R_limiter", "Z_limiter", "R_mag_axis"):
        out[t + "_mae"] = out["per_target"][t]["mae"]
    return out


def latency_of(parts, fold_name_lookup):
    med, par = 0.0, 0
    for name, k in parts:
        name = fold_name_lookup(name)
        if name not in LAT:
            return None, None
        med += k * LAT[name]["median"]
        par += k * LAT[name]["parameters"]
    return med, par


def lat_lookup(name):
    if name.startswith("@"):  # candidate name -> stem of the configuration trained on fold 0
        s = stem(0, name[1:])
        return f"{s}_s0" if s else name
    return name


def pareto(points):
    """Indices not dominated in (latency, summary): no other point is at least as fast and at least as accurate."""
    return [i for i, (l, s) in enumerate(points)
            if not any((l2 <= l and s2 <= s) and (l2 < l or s2 < s) for j, (l2, s2) in enumerate(points) if j != i)]


def plain_log(ax):
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=8)


def fmt(v, d=3):
    return "n/a" if v is None else f"{v:.{d}g}"


def main():
    RES.mkdir(exist_ok=True)
    table = {}
    for key, (label, builder, parts) in ENTRIES.items():
        a = agg(builder)
        if a is None:
            continue
        a["label"] = label
        a["latency_ms_median"], a["parameters"] = latency_of(parts, lat_lookup)
        table[key] = a
    base = table.get("baseline")
    json_out = {"protocol": "5-fold GroupKFold by discharge (ipp1_common.group_folds); summary = mean nRMSE over 13 targets "
                            "without the limiter point; hyperparameters chosen on an inner split by discharge of each "
                            "outer training set", "models": table}

    # ---- Pareto table ----
    rows = [k for k in table if table[k]["latency_ms_median"] is not None]
    pts = [(table[k]["latency_ms_median"], table[k]["summary"]) for k in rows]
    front = {rows[i] for i in pareto(pts)}
    fast = [k for k in rows if table[k]["latency_ms_median"] is not None and 0 < table[k]["latency_ms_median"] <= FAST_MS]
    rec = min(fast, key=lambda k: table[k]["summary"]) if fast else None
    rec_lim = min(fast, key=lambda k: table[k]["Z_limiter_mae"]) if fast else None
    L = ["| model | summary rel. error | folds better than baseline | R_limiter MAE (mm) | Z_limiter MAE (mm) | R_mag_axis MAE (mm) |"
         " is_limited acc. | parameters | latency (ms / sample) | Pareto |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k in sorted(rows, key=lambda k: table[k]["summary"]):
        t = table[k]
        better = (f"{sum(a < b for a, b in zip(t['summary_per_fold'], base['summary_per_fold']))}/5" if base else "")
        L.append(f"| {t['label']} | {t['summary']:.4f} ± {t['summary_std']:.4f} | {better} | {t['R_limiter_mae']:.2f} | "
                 f"{t['Z_limiter_mae']:.2f} | {t['R_mag_axis_mae']:.3f} | {t['is_limited_accuracy']:.4f} | "
                 f"{t['parameters'] if t['parameters'] is not None else 'n/a'} | {fmt(t['latency_ms_median'])} | "
                 f"{'yes' if k in front else ''}{' **recommended**' if k == rec else ''} |")
    pareto_md = "\n".join(L)

    # ---- per target table for the main candidates ----
    show = [k for k in ("baseline", "nn_best_ens5", "attn_ens5", "lgbm", "hyb_nn") if k in table]
    T = ["| target | unit | " + " | ".join(f"{table[k]['label']} MAE" for k in show) + " |", "|---|---|" + "---|" * len(show)]
    for t in C.TARGETS if show else []:
        T.append(f"| {t} | {table[show[0]]['per_target'][t]['unit']} | " +
                 " | ".join(f"{table[k]['per_target'][t]['mae']:.3g}" for k in show) + " |")
    target_md = "\n".join(T) if show else "(not run)"

    # ---- limiter specialist and gate ----
    lim_md, gate_md = limiter_section(table)

    # ---- what the search found ----
    search_md, search_json = search_section()
    json_out["search"] = search_json

    # ---- noise ----
    noisy_md, noisy_json = noisy_section()
    json_out["noisy"] = noisy_json

    json_out["recommended"] = {"fast_limit_ms": FAST_MS, "best_summary": rec, "best_limiter_z": rec_lim,
                               "pareto_front": sorted(front)}
    json.dump(json_out, open(RES / "cloud-search.json", "w"), indent=1)

    figures(table, rows, front, pts)
    missing = [n for n, ok in (("model evaluation on the test folds", bool(table)), ("latency", bool(LAT)),
                               ("noisy-data runs", bool(noisy_json)), ("limiter specialist", "Z_limiter" in lim_md or "specialist" in lim_md),
                               ) if not ok]
    status = ("**Status: PARTIAL.** Not yet in this file: " + ", ".join(missing) + ". Tables below show only what has run so far.") if missing else ""
    findings = (RES / "cloud-search-findings.md").read_text() if (RES / "cloud-search-findings.md").exists() else ""
    cpu = Path("/proc/cpuinfo").read_text().split("model name")[1].split(":")[1].split("\n")[0].strip() if Path("/proc/cpuinfo").exists() else "?"
    md = [f"# Cloud model search, IPP 1 magnetic part", "",
          "Produced by `analysis/cloud_search.py` and `analysis/cloud_search_report.py`. Protocol of the baseline: 5 folds by whole "
          "discharge (same test folds as `results/ipp1-baseline.md`), masked loss, errors from `ipp1_common.score`. "
          "**Summary relative error** = mean over folds of the mean nRMSE (RMSE / spread) of the 13 targets without the limiter "
          "point, as in `results/ipp1-inputs.md`. Hyperparameters of every model were chosen only on an inner split by discharge "
          f"of the training part of each fold (objective: summary error + 0.2 x mean limiter nRMSE); the test fold was never used "
          f"for tuning. Latency: one sample, one CPU thread, whole pipeline from the 24 raw numbers ({cpu}); ensembles and hybrids "
          "are the sum of their parts run one after the other (a fused batched network would be faster).", "", status, "", findings, "",
          "## Pareto table (mean of 5 folds; sorted by summary error)", "", pareto_md, "",
          f"Recommendation rule: the lowest summary error among models with median latency <= {FAST_MS} ms (ten times below the 1 ms budget): "
          f"**{table[rec]['label'] if rec else 'none'}**; lowest Z_limiter error among them: "
          f"**{table[rec_lim]['label'] if rec_lim else 'none'}**. Figure: `results/cloud-search-pareto.png`.", "",
          "## Error per target (MAE, mean of 5 folds)", "", target_md, "", "Figure: `results/cloud-search-targets.png`.", "",
          "## Limiter point: specialist and gate", "", lim_md, "", gate_md, "",
          "## What the search found", "", search_md, "", "Figure: `results/cloud-search-search.png`.", "",
          "## Noisy data (`equil_data_noisy.csv`)", "", noisy_md, "", "Figure: `results/cloud-search-noisy.png`."]
    (RES / "cloud-search.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


def limiter_section(table):
    lm = []
    out = {}
    for label, getter in (("main net x5", lambda f: col(ens(f, "nn_best", 5), LIM)),
                          ("specialist net x5", lambda f: ens(f, "lim_nn", 5)),
                          ("specialist LightGBM", lambda f: pred(f, "lim_lgbm"))):
        errs = []
        for f in FOLD_IDS:
            te = FOLDS[f][1]
            p = getter(f)
            if p is None:
                errs = None
                break
            rows_l = M[te][:, LIM[0]] & M[te][:, LIM[1]]
            errs.append([np.abs(p[rows_l, j] - Y[te][rows_l, LIM[j]]).mean() * 1000 for j in range(2)])
        if errs:
            out[label] = np.mean(errs, 0).tolist()
    if out:
        lm = ["| model | R_limiter MAE (mm) | Z_limiter MAE (mm) |", "|---|---|---|"] + \
             [f"| {k} | {v[0]:.2f} | {v[1]:.2f} |" for k, v in out.items()]
    gm = []
    gates = {}
    for label, getter in (("main net x5 (is_limited output)", lambda f: col(ens(f, "nn_best", 5), CLS)),
                          ("gate net", lambda f: pred(f, "gate_nn")), ("gate LightGBM", lambda f: pred(f, "gate_lgbm"))):
        acc, fn, fp = [], [], []
        for f in FOLD_IDS:
            te = FOLDS[f][1]
            p = getter(f)
            if p is None:
                acc = None
                break
            truth = Y[te][:, CLS] > 0.5
            say = p > 0.5
            acc.append((say == truth).mean())
            fn.append((~say & truth).sum() / max(1, truth.sum()))
            fp.append((say & ~truth).sum() / max(1, (~truth).sum()))
        if acc:
            gates[label] = (np.mean(acc), np.mean(fn), np.mean(fp))
    if gates:
        gm = ["| classifier for is_limited | accuracy | limited rows missed | not limited rows flagged |", "|---|---|---|---|"] + \
             [f"| {k} | {v[0]:.4f} | {v[1]:.4f} | {v[2]:.4f} |" for k, v in gates.items()]
    return "\n".join(lm) or "(not run)", "\n".join(gm) or "(not run)"


def tune_files():
    return sorted((WORK / "tune").glob("fold*_*.json")) if (WORK / "tune").exists() else []


def search_section():
    by = {}
    for p in tune_files():
        j = json.load(open(p))
        by.setdefault(j["family"], []).append(j)
    lines, js = [], {}
    lines += ["| family | folds | trials per fold | search time (CPU-min, 1 thread each) | best inner objective per fold |",
              "|---|---|---|---|---|"]
    for fam, js_ in by.items():
        lines.append(f"| {fam} | {len(js_)} | {np.mean([j['n_trials'] for j in js_]):.0f} | {sum(j['seconds'] for j in js_) / 60:.0f} | "
                     + ", ".join(f"{j['best_value']:.4f}" for j in sorted(js_, key=lambda j: j['fold'])) + " |")
        js[fam] = [{k: j[k] for k in ("fold", "n_trials", "seconds", "best_value", "best_params")} for j in js_]
    nn = by.get("nn", [])
    if nn:
        lines += ["", "Best inner-validation objective reached with each choice (lower is better; mean over the folds that tried it):", "",
                  "| choice | value | best objective | trials (all folds) |", "|---|---|---|---|"]
        for key in ("arch", "feat", "loss", "sched", "act", "width", "depth", "batch"):
            vals = {}
            for j in nn:
                for v, info in j["choices"].get(key, {}).items():
                    vals.setdefault(v, []).append(info)
            for v in sorted(vals, key=lambda v: np.mean([i["best"] for i in vals[v]])):
                lines.append(f"| {key} | {v} | {np.mean([i['best'] for i in vals[v]]):.4f} | {sum(i['n'] for i in vals[v])} |")
    return "\n".join(lines) or "(not run)", js


def noisy_section():
    rows, js = [], {}
    settings = [("clean", "clean", ""), ("clean", "noisy", "__tr-clean_te-noisy"), ("noisy", "noisy", "__tr-noisy_te-noisy"),
                ("noisy", "clean", "__tr-noisy_te-clean")]
    for cfg, label in (("nn_best", "tuned net x5"), ("baseline", "baseline MLP x5")):
        for tr_s, te_s, tag in settings:
            def b(f, cfg=cfg, tag=tag):
                return ens(f, cfg, 5, tag)
            a = agg(b)
            if a is None:
                continue
            js[f"{cfg}:{tr_s}->{te_s}"] = {k: a[k] for k in ("summary", "summary_std", "R_limiter_mae", "Z_limiter_mae", "R_mag_axis_mae", "is_limited_accuracy")}
            rows.append(f"| {label} | {tr_s} | {te_s} | {a['summary']:.4f} ± {a['summary_std']:.4f} | {a['R_mag_axis_mae']:.3f} | "
                        f"{a['R_limiter_mae']:.2f} | {a['Z_limiter_mae']:.2f} | {a['is_limited_accuracy']:.4f} |")
    if not rows:
        return "(not run)", js
    return "\n".join(["| model | trained on | tested on | summary rel. error | R_mag_axis MAE (mm) | R_limiter MAE (mm) | Z_limiter MAE (mm) | is_limited acc. |",
                      "|---|---|---|---|---|---|---|---|"] + rows), js


def figures(table, rows, front, pts):
    # Pareto: latency against summary error
    if rows:
        pareto_fig(table, rows, front)
    targets_fig(table)
    search_fig()
    noisy_fig()


def pareto_fig(table, rows, front):
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    style(ax)
    xs = [table[k]["latency_ms_median"] for k in rows]
    ys = [table[k]["summary"] for k in rows]
    ax.scatter(xs, ys, s=36, color=BLUE, zorder=3, edgecolor="white", linewidth=1.0)
    fr = sorted((x, y) for k, x, y in zip(rows, xs, ys) if k in front)
    ax.step([p[0] for p in fr], [p[1] for p in fr], where="post", color=ORANGE, lw=1.6, zorder=2)
    for k, x, y in zip(rows, xs, ys):
        ax.annotate(k, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=7.5, color=INK)
    ax.axvline(1.0, color=MUTED, ls="--", lw=1)
    ax.text(1.05, ax.get_ylim()[1], "1 ms", color=MUTED, fontsize=8, va="top")
    ax.axvline(FAST_MS, color=MUTED, ls=":", lw=1)
    ax.text(FAST_MS * 1.05, ax.get_ylim()[1], f"{FAST_MS} ms", color=MUTED, fontsize=8, va="top")
    ax.set_xscale("log")
    ax.set_xlabel("CPU latency per sample, 1 thread (ms, log scale)", color=MUTED)
    ax.set_ylabel("summary relative error (lower is better)", color=MUTED)
    ax.set_title("Accuracy against speed; orange: Pareto front", loc="left", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(RES / "cloud-search-pareto.png", dpi=150)
    plt.close(fig)


def targets_fig(table):
    show = [k for k in ("baseline", "nn_best_ens5", "hyb_nn") if k in table]
    if show:
        fig, ax = plt.subplots(figsize=(9.5, 4.6))
        style(ax)
        w = 0.8 / len(show)
        for i, (k, c) in enumerate(zip(show, (BLUE, ORANGE, AQUA))):
            ax.bar(np.arange(len(C.TARGETS)) + i * w, [table[k]["per_target"][t]["nrmse"] for t in C.TARGETS], w, color=c,
                   label=table[k]["label"], zorder=3)
        ax.set_xticks(np.arange(len(C.TARGETS)) + w * (len(show) - 1) / 2)
        ax.set_xticklabels(C.TARGETS, rotation=60, ha="right", fontsize=7.5)
        ax.set_yscale("log")
        plain_log(ax)
        ax.set_ylabel("nRMSE (RMSE / spread)", color=MUTED)
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(RES / "cloud-search-targets.png", dpi=150)
        plt.close(fig)

def search_fig():
    nn = [json.load(open(p)) for p in tune_files() if p.name.endswith("_nn.json")]
    if nn:
        fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
        for a in axs:
            style(a)
        for j, c in zip(sorted(nn, key=lambda j: j["fold"]), (BLUE, ORANGE, AQUA, YELLOW, MAGENTA)):
            vals = [v for _, v in sorted(j["trial_values"].items(), key=lambda kv: int(kv[0]))]
            axs[0].plot(np.arange(1, len(vals) + 1), np.minimum.accumulate(vals), color=c, lw=1.6, label=f"fold {j['fold']}")
        axs[0].set_xlabel("trial", color=MUTED)
        axs[0].set_ylabel("best inner objective so far", color=MUTED)
        axs[0].legend(frameon=False, fontsize=8)
        feats = sorted({p["feat"] for j in nn for p in j["trial_params"].values()})
        data = [[v for j in nn for t, v in j["trial_values"].items() if j["trial_params"][t]["feat"] == f] for f in feats]
        axs[1].boxplot(data, tick_labels=feats, patch_artist=True, boxprops=dict(facecolor="#cfe2f8", color=BLUE),
                       medianprops=dict(color=ORANGE), flierprops=dict(markersize=3))
        axs[1].set_yscale("log")
        plain_log(axs[1])
        axs[1].set_ylabel("inner objective of every trial", color=MUTED)
        axs[1].set_xlabel("input features", color=MUTED)
        fig.tight_layout()
        fig.savefig(RES / "cloud-search-search.png", dpi=150)
        plt.close(fig)

def noisy_fig():
    js = json.load(open(RES / "cloud-search.json")) if (RES / "cloud-search.json").exists() else {}
    nz = js.get("noisy", {})
    if nz:
        fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
        for a in axs:
            style(a)
        keys = [k for k in nz if k.startswith("nn_best:")]
        base_keys = [k for k in nz if k.startswith("baseline:")]
        for ax, metric, lab in ((axs[0], "summary", "summary relative error"), (axs[1], "R_mag_axis_mae", "R_mag_axis MAE (mm)")):
            xs = np.arange(len(keys))
            ax.bar(xs - 0.2, [nz[k][metric] for k in keys], 0.4, color=ORANGE, label="tuned net x5", zorder=3)
            if base_keys:
                bk = [k.replace("nn_best", "baseline") for k in keys]
                ax.bar(xs + 0.2, [nz[k][metric] if k in nz else np.nan for k in bk], 0.4, color=BLUE, label="baseline MLP x5", zorder=3)
            ax.set_xticks(xs)
            ax.set_xticklabels([k.split(":")[1] for k in keys], fontsize=8)
            ax.set_yscale("log")
            plain_log(ax)
            ax.set_ylabel(lab, color=MUTED)
        axs[0].legend(frameon=False, fontsize=8)
        axs[0].set_xlabel("trained on -> tested on", color=MUTED)
        fig.tight_layout()
        fig.savefig(RES / "cloud-search-noisy.png", dpi=150)
        plt.close(fig)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--folds", type=int, nargs="+", default=list(range(5)))
    FOLD_IDS = ap.parse_args().folds
    main()
