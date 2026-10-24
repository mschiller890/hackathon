#!/usr/bin/env python
"""Accuracy charts of the shipped model: overall accuracy and accuracy of every output, in per cent.

Accuracy = 100 x (1 - nRMSE): the root mean square error of an output divided by the spread (standard deviation) of the reference reconstruction on the same rows, 100 % is an exact
copy of the reconstruction. The overall accuracy is the mean of the 16 outputs, as in the demo (mini_pipeline.overall_accuracy). It is agreement with the institute's reconstruction, not with the plasma.

    HACKATHON_HOME=<folder> python analysis/plot_accuracy.py [--model out/model/ipp1-ipn.npz] [--lang en|cs]
Writes results/ipp1-accuracy-overall-<lang>.png, results/ipp1-accuracy-outputs-<lang>.png and results/ipp1-accuracy-ladder-<lang>.png: aggregates only, no data rows.
Needs the cached predictions of ipp1_final.py (out/ipp1-final-cache) for the baseline and `cand`; the shipped model is read from the exported file.
The ladder chart parses the development-set table of results/ipp1-ipn.md.
"""
import argparse
import re
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # predict.py of the repository root
import ipp1_common as C
import ipp1_final as F
from predict import Model

RES = Path(__file__).resolve().parents[1] / "results"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8985", "#e4e3df", "#fcfcfb"
COLOURS = {"base": "#2a78d6", "cand": "#eb6834", "ipn": "#1baf7a"}          # validated categorical slots 1 to 3, fixed order
NAMES = {"en": {"base": "baseline network", "cand": "previous model (cand)", "ipn": "shipped model (divided by the current)"},
         "cs": {"base": "základní síť", "cand": "předchozí model (cand)", "ipn": "nasazený model (dělení proudem)"}}
OUT_NAMES = {"en": {"plasma_current": "plasma current", "R_mag_axis": "axis R", "Z_mag_axis": "axis Z", "elongation": "elongation", "triangularity": "triangularity",
                    "triangularity_upper": "triangularity, upper", "triangularity_lower": "triangularity, lower", "R_x_point": "X point R", "Z_x_point": "X point Z",
                    "R_strike_point_1": "strike point 1 R", "Z_strike_point_1": "strike point 1 Z", "R_strike_point_2": "strike point 2 R",
                    "Z_strike_point_2": "strike point 2 Z", "R_limiter": "limiter point R", "Z_limiter": "limiter point Z", "is_limited": "limited / divertor"},
             "cs": {"plasma_current": "proud plazmatem", "R_mag_axis": "osa R", "Z_mag_axis": "osa Z", "elongation": "elongace", "triangularity": "triangularita",
                    "triangularity_upper": "triangularita horní", "triangularity_lower": "triangularita dolní", "R_x_point": "bod X R", "Z_x_point": "bod X Z",
                    "R_strike_point_1": "dotykový bod 1 R", "Z_strike_point_1": "dotykový bod 1 Z", "R_strike_point_2": "dotykový bod 2 R",
                    "Z_strike_point_2": "dotykový bod 2 Z", "R_limiter": "bod limiteru R", "Z_limiter": "bod limiteru Z", "is_limited": "limiter / divertor"}}
TEXT = {"en": {"overall": "Overall accuracy on the 30 set-aside discharges", "outputs": "Accuracy of every output on the 30 set-aside discharges",
               "ladder": "Overall accuracy on the development set (5-fold cross-validation)", "unit": "accuracy, 100 % = exact copy of the reconstruction",
               "foot": "accuracy = 100 x (1 - RMSE / spread of the reference); mean over the 16 outputs",
               "axis": "the axis starts at {lo:.0f} %, not at 0", "seed": "one seed"},
        "cs": {"overall": "Celková přesnost na 30 odložených výbojích", "outputs": "Přesnost každé veličiny na 30 odložených výbojích",
               "ladder": "Celková přesnost na vývojové sadě (pětinásobná křížová validace)", "unit": "přesnost, 100 % = přesná kopie rekonstrukce",
               "foot": "přesnost = 100 x (1 - RMSE / rozptyl reference); průměr přes 16 veličin",
               "axis": "osa začíná na {lo:.0f} %, ne na 0", "seed": "jedno semínko"}}
LADDER = [("cand general network (Huber 0.5)", "výchozí síť (Huber 0,5)", "start: general network"),
          ("Huber 0.2", "užší Huberova ztráta (0,2)", "narrower loss"),
          ("Huber 0.2, divided by the current", "+ dělení proudem", "+ divided by the current"),
          ("Huber 0.2, divided by the current, second differences", "+ druhé diference", "+ second differences")]


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, length=0, labelsize=8)
    ax.set_facecolor(SURFACE)


def accuracy(stats):
    """Per output accuracy in per cent from pooled tstats."""
    return {t: 100 * (1 - stats[t]["nrmse"]) for t in C.TARGETS}


def collect(model_path):
    (df, X, Y, G, M), _ = F.aligned_data()
    _, dev_idx, lock_idx = F.split(G)
    yl, ml = Y[lock_idx], M[lock_idx]
    lk = F.assemble("locked", None, ["base", "cand"])
    acc = {r: accuracy(F.tstats(lk[r]["clean"], yl, ml)) for r in ("base", "cand")}
    acc["ipn"] = accuracy(F.tstats(Model(model_path).predict(X[lock_idx]), yl, ml))
    return acc


def overall_chart(acc, lang, path):
    fig, ax = plt.subplots(figsize=(6.6, 3.4), facecolor=SURFACE)
    keys = ["base", "cand", "ipn"]
    vals = [np.mean(list(acc[k].values())) for k in keys]
    bars = ax.bar(range(3), vals, width=0.5, color=[COLOURS[k] for k in keys], edgecolor=SURFACE, linewidth=2)
    for b, v, k in zip(bars, vals, keys):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.2, f"{v:.2f} %", ha="center", va="bottom", fontsize=10, color=INK, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels([NAMES[lang][k].replace(" (", "\n(") for k in keys], fontsize=8, color=INK)
    lo = min(vals) - 4
    ax.set_ylim(lo, 100)
    ax.set_yticks(np.arange(np.ceil(lo / 2) * 2, 101, 2))
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_ylabel(TEXT[lang]["unit"], fontsize=8, color=INK2)
    ax.set_title(TEXT[lang]["overall"], loc="left", fontsize=10.5, color=INK, fontweight="bold")
    style(ax)
    fig.text(0.01, 0.01, TEXT[lang]["foot"] + "; " + TEXT[lang]["axis"].format(lo=lo), fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return dict(zip(keys, vals))


def outputs_chart(acc, lang, path):
    order = sorted(C.TARGETS, key=lambda t: acc["ipn"][t])                      # worst output at the top
    fig, ax = plt.subplots(figsize=(8.2, 6.6), facecolor=SURFACE)
    h, y = 0.24, np.arange(len(order))
    for k, (key, off) in enumerate((("base", -h), ("cand", 0), ("ipn", h))):
        v = [acc[key][t] for t in order]
        ax.barh(y + off, v, height=h - 0.03, color=COLOURS[key], edgecolor=SURFACE, linewidth=1.2, label=NAMES[lang][key])
        if key == "ipn":
            for yy, vv in zip(y + off, v):
                ax.text(min(vv, 100) + 0.3, yy, f"{vv:.1f} %", va="center", fontsize=7, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([OUT_NAMES[lang][t] for t in order], fontsize=8, color=INK)
    lo = max(0, np.floor(min(min(a.values()) for a in acc.values()) / 5) * 5 - 5)
    ax.set_xlim(lo, 103)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel(TEXT[lang]["unit"], fontsize=8, color=INK2)
    ax.set_title(TEXT[lang]["outputs"], loc="left", fontsize=10.5, color=INK, fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.07), ncol=3, fontsize=7.5, frameon=False, labelcolor=INK2)
    style(ax)
    fig.text(0.01, 0.01, TEXT[lang]["foot"] + "; " + TEXT[lang]["axis"].format(lo=lo), fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def ladder_chart(lang, path):
    text = (RES / "ipp1-ipn.md").read_text().replace("`", "")
    vals, labels = [], []
    for en, cs, short in LADDER:
        m = re.search(r"^\| " + re.escape(en) + r" \| ([\d.]+) \|", text, re.M)
        if not m:
            raise SystemExit(f"row not found in results/ipp1-ipn.md: {en}")
        vals.append(100 * (1 - float(m.group(1))))
        labels.append(cs if lang == "cs" else short)
    fig, ax = plt.subplots(figsize=(7.4, 3.6), facecolor=SURFACE)
    bars = ax.bar(range(len(vals)), vals, width=0.52, color=COLOURS["ipn"], edgecolor=SURFACE, linewidth=2)
    for b, v, prev in zip(bars, vals, [None] + vals[:-1]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.15, f"{v:.2f} %" + ("" if prev is None else f"\n({v - prev:+.2f})"), ha="center", va="bottom", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels([l.replace(" (", "\n(") for l in labels], fontsize=7.5, color=INK)
    lo = np.floor(min(vals) - 2)
    ax.set_ylim(lo, 100)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_ylabel(TEXT[lang]["unit"], fontsize=8, color=INK2)
    ax.set_title(TEXT[lang]["ladder"], loc="left", fontsize=10.5, color=INK, fontweight="bold")
    style(ax)
    fig.text(0.01, 0.01, TEXT[lang]["foot"] + "; " + TEXT[lang]["axis"].format(lo=lo) + "; " + TEXT[lang]["seed"], fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return dict(zip(labels, vals))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=str(C.OUT / "model" / "ipp1-ipn.npz"))
    ap.add_argument("--lang", default="en", choices=["en", "cs"])
    a = ap.parse_args()
    acc = collect(a.model)
    overall = overall_chart(acc, a.lang, RES / f"ipp1-accuracy-overall-{a.lang}.png")
    outputs_chart(acc, a.lang, RES / f"ipp1-accuracy-outputs-{a.lang}.png")
    ladder = ladder_chart(a.lang, RES / f"ipp1-accuracy-ladder-{a.lang}.png")
    print("overall accuracy on the 30 set-aside discharges:", {k: round(v, 2) for k, v in overall.items()})
    print("development ladder:", {k: round(v, 2) for k, v in ladder.items()})
    for k in ("base", "cand", "ipn"):
        worst = sorted(acc[k].items(), key=lambda kv: kv[1])[:3]
        print(f"lowest outputs, {k}:", [(t, round(v, 1)) for t, v in worst])


if __name__ == "__main__":
    main()
