#!/usr/bin/env python
"""Grafy přesnosti nasazeného modelu: celková přesnost a přesnost každé veličiny, v procentech.

Přesnost = 100 x (1 - nRMSE), kde nRMSE je střední kvadratická chyba veličiny dělená směrodatnou odchylkou
rekonstrukce ústavu na týchž řádcích. 100 % by byla přesná kopie rekonstrukce. Celková přesnost je průměr přes
16 veličin, stejně jako v demu (mini_pipeline.overall_accuracy). Je to shoda s rekonstrukcí ústavu, ne s plazmatem.

    python analysis/plot_accuracy.py [--model out/model/ipp1-ipn.npz] [--lang en|cs]

Uloží results/ipp1-accuracy-overall-<jazyk>.png, results/ipp1-accuracy-outputs-<jazyk>.png a
results/ipp1-accuracy-ladder-<jazyk>.png: jen souhrnná čísla, žádné řádky dat.
Pro základní síť a `cand` potřebuje uložené odhady z ipp1_final.py (out/ipp1-final-cache), nasazený model čte
z exportovaného souboru. Žebříček zlepšení čte tabulku vývojové sady z results/ipp1-ipn.md.
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
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # predict.py v kořeni repozitáře
import ipp1_common as C
import ipp1_final as F
from predict import Model

RESULTS_FOLDER = Path(__file__).resolve().parents[1] / "results"

# --- vzhled -----------------------------------------------------------------------------------------------------
TEXT_COLOUR, SECONDARY_TEXT_COLOUR, FOOTNOTE_COLOUR = "#0b0b0b", "#52514e", "#8a8985"
GRID_COLOUR, BACKGROUND_COLOUR = "#e4e3df", "#fcfcfb"
MODEL_COLOURS = {"base": "#2a78d6", "cand": "#eb6834", "ipn": "#1baf7a"}  # tři barvy, vždy ve stejném pořadí
MODELS = ["base", "cand", "ipn"]

# --- popisky v češtině a angličtině -----------------------------------------------------------------------------
MODEL_NAMES = {
    "en": {"base": "baseline network", "cand": "previous model (cand)", "ipn": "shipped model (divided by the current)"},
    "cs": {"base": "základní síť", "cand": "předchozí model (cand)", "ipn": "nasazený model (dělení proudem)"},
}
OUTPUT_NAMES = {
    "en": {
        "plasma_current": "plasma current", "R_mag_axis": "axis R", "Z_mag_axis": "axis Z",
        "elongation": "elongation", "triangularity": "triangularity",
        "triangularity_upper": "triangularity, upper", "triangularity_lower": "triangularity, lower",
        "R_x_point": "X point R", "Z_x_point": "X point Z",
        "R_strike_point_1": "strike point 1 R", "Z_strike_point_1": "strike point 1 Z",
        "R_strike_point_2": "strike point 2 R", "Z_strike_point_2": "strike point 2 Z",
        "R_limiter": "limiter point R", "Z_limiter": "limiter point Z", "is_limited": "limited / divertor",
    },
    "cs": {
        "plasma_current": "proud plazmatem", "R_mag_axis": "osa R", "Z_mag_axis": "osa Z",
        "elongation": "elongace", "triangularity": "triangularita",
        "triangularity_upper": "triangularita horní", "triangularity_lower": "triangularita dolní",
        "R_x_point": "bod X R", "Z_x_point": "bod X Z",
        "R_strike_point_1": "dotykový bod 1 R", "Z_strike_point_1": "dotykový bod 1 Z",
        "R_strike_point_2": "dotykový bod 2 R", "Z_strike_point_2": "dotykový bod 2 Z",
        "R_limiter": "bod limiteru R", "Z_limiter": "bod limiteru Z", "is_limited": "limiter / divertor",
    },
}
TEXT = {
    "en": {
        "overall": "Overall accuracy on the 30 set-aside discharges",
        "outputs": "Accuracy of every output on the 30 set-aside discharges",
        "ladder": "Overall accuracy on the development set (5-fold cross-validation)",
        "unit": "accuracy, 100 % = exact copy of the reconstruction",
        "foot": "accuracy = 100 x (1 - RMSE / spread of the reference); mean over the 16 outputs",
        "axis": "the axis starts at {start:.0f} %, not at 0", "seed": "one seed",
    },
    "cs": {
        "overall": "Celková přesnost na 30 odložených výbojích",
        "outputs": "Přesnost každé veličiny na 30 odložených výbojích",
        "ladder": "Celková přesnost na vývojové sadě (pětinásobná křížová validace)",
        "unit": "přesnost, 100 % = přesná kopie rekonstrukce",
        "foot": "přesnost = 100 x (1 - RMSE / rozptyl reference); průměr přes 16 veličin",
        "axis": "osa začíná na {start:.0f} %, ne na 0", "seed": "jedno semínko",
    },
}

# Kroky žebříčku zlepšení: (název řádku v results/ipp1-ipn.md, český popisek, anglický popisek).
LADDER_STEPS = [
    ("cand general network (Huber 0.5)", "výchozí síť (Huber 0,5)", "start: general network"),
    ("Huber 0.2", "užší Huberova ztráta (0,2)", "narrower loss"),
    ("Huber 0.2, divided by the current", "+ dělení proudem", "+ divided by the current"),
    ("Huber 0.2, divided by the current, second differences", "+ druhé diference", "+ second differences"),
]


# ===================================================================================================================
# Společné pomocné funkce
# ===================================================================================================================
def style_axes(axes):
    """Jednotný vzhled os: bez horního, pravého a levého rámu, jemná spodní čára, tiché popisky."""
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(GRID_COLOUR)
    axes.tick_params(colors=SECONDARY_TEXT_COLOUR, length=0, labelsize=8)
    axes.set_facecolor(BACKGROUND_COLOUR)


def accuracy(stats):
    """Přesnost v procentech pro každou veličinu z výstupu ipp1_final.pooled_stats."""
    return {name: 100 * (1 - stats[name]["nrmse"]) for name in C.TARGETS}


def collect(model_path):
    """Přesnosti tří modelů na 30 odložených výbojích: {"base": ..., "cand": ..., "ipn": ...}, každý {veličina: %}."""
    (_, X, Y, discharges, exists), _ = F.aligned_data()
    _, _, locked_rows = F.split(discharges)
    locked_targets, locked_exists = Y[locked_rows], exists[locked_rows]
    cached = F.assemble("locked", ["base", "cand"])  # odhady základní sítě a cand uložené z ipp1_final.py
    result = {name: accuracy(F.pooled_stats(cached[name]["clean"], locked_targets, locked_exists)) for name in ("base", "cand")}
    result["ipn"] = accuracy(F.pooled_stats(Model(model_path).predict(X[locked_rows]), locked_targets, locked_exists))
    return result


def save_and_close(figure, path, footnote_height):
    figure.tight_layout(rect=(0, footnote_height, 1, 1))
    figure.savefig(path, dpi=200, facecolor=BACKGROUND_COLOUR)
    plt.close(figure)


# ===================================================================================================================
# Tři grafy
# ===================================================================================================================
def overall_chart(accuracies, language, path):
    """Sloupce: celková přesnost základní sítě, předchozího a nasazeného modelu. Vrací {model: přesnost}."""
    figure, axes = plt.subplots(figsize=(6.6, 3.4), facecolor=BACKGROUND_COLOUR)
    overall = [np.mean(list(accuracies[model].values())) for model in MODELS]
    bars = axes.bar(range(3), overall, width=0.5, color=[MODEL_COLOURS[m] for m in MODELS], edgecolor=BACKGROUND_COLOUR, linewidth=2)
    for bar, value in zip(bars, overall):
        axes.text(bar.get_x() + bar.get_width() / 2, value + 0.2, f"{value:.2f} %", ha="center", va="bottom",
                  fontsize=10, color=TEXT_COLOUR, fontweight="bold")
    axes.set_xticks(range(3))
    axes.set_xticklabels([MODEL_NAMES[language][m].replace(" (", "\n(") for m in MODELS], fontsize=8, color=TEXT_COLOUR)
    axis_start = min(overall) - 4
    axes.set_ylim(axis_start, 100)
    axes.set_yticks(np.arange(np.ceil(axis_start / 2) * 2, 101, 2))
    axes.yaxis.grid(True, color=GRID_COLOUR, linewidth=0.8)
    axes.set_axisbelow(True)
    axes.set_ylabel(TEXT[language]["unit"], fontsize=8, color=SECONDARY_TEXT_COLOUR)
    axes.set_title(TEXT[language]["overall"], loc="left", fontsize=10.5, color=TEXT_COLOUR, fontweight="bold")
    style_axes(axes)
    figure.text(0.01, 0.01, TEXT[language]["foot"] + "; " + TEXT[language]["axis"].format(start=axis_start),
                fontsize=7, color=FOOTNOTE_COLOUR)
    save_and_close(figure, path, footnote_height=0.04)
    return dict(zip(MODELS, overall))


def outputs_chart(accuracies, language, path):
    """Vodorovné sloupce: přesnost každé z 16 veličin pro tři modely, nejhorší veličina nasazeného modelu nahoře."""
    worst_first = sorted(C.TARGETS, key=lambda name: accuracies["ipn"][name])
    figure, axes = plt.subplots(figsize=(8.2, 6.6), facecolor=BACKGROUND_COLOUR)
    bar_height = 0.24
    positions = np.arange(len(worst_first))
    for model, shift in (("base", -bar_height), ("cand", 0), ("ipn", bar_height)):
        values = [accuracies[model][name] for name in worst_first]
        axes.barh(positions + shift, values, height=bar_height - 0.03, color=MODEL_COLOURS[model],
                  edgecolor=BACKGROUND_COLOUR, linewidth=1.2, label=MODEL_NAMES[language][model])
        if model == "ipn":  # u nasazeného modelu je vedle sloupce vidět i číslo
            for y, value in zip(positions + shift, values):
                axes.text(min(value, 100) + 0.3, y, f"{value:.1f} %", va="center", fontsize=7, color=TEXT_COLOUR)
    axes.set_yticks(positions)
    axes.set_yticklabels([OUTPUT_NAMES[language][name] for name in worst_first], fontsize=8, color=TEXT_COLOUR)
    lowest = min(min(per_output.values()) for per_output in accuracies.values())
    axis_start = max(0, np.floor(lowest / 5) * 5 - 5)
    axes.set_xlim(axis_start, 103)
    axes.xaxis.grid(True, color=GRID_COLOUR, linewidth=0.8)
    axes.set_axisbelow(True)
    axes.set_xlabel(TEXT[language]["unit"], fontsize=8, color=SECONDARY_TEXT_COLOUR)
    axes.set_title(TEXT[language]["outputs"], loc="left", fontsize=10.5, color=TEXT_COLOUR, fontweight="bold")
    axes.legend(loc="upper center", bbox_to_anchor=(0.45, -0.07), ncol=3, fontsize=7.5, frameon=False,
                labelcolor=SECONDARY_TEXT_COLOUR)
    style_axes(axes)
    figure.text(0.01, 0.01, TEXT[language]["foot"] + "; " + TEXT[language]["axis"].format(start=axis_start),
                fontsize=7, color=FOOTNOTE_COLOUR)
    save_and_close(figure, path, footnote_height=0.03)


def ladder_chart(language, path):
    """Sloupce: jak celková přesnost na vývojové sadě rostla s jednotlivými kroky. Čísla čte z results/ipp1-ipn.md."""
    table_text = (RESULTS_FOLDER / "ipp1-ipn.md").read_text().replace("`", "")
    accuracies, labels = [], []
    for row_name, czech, english in LADDER_STEPS:
        match = re.search(r"^\| " + re.escape(row_name) + r" \| ([\d.]+) \|", table_text, re.M)
        if not match:
            raise SystemExit(f"row not found in results/ipp1-ipn.md: {row_name}")
        accuracies.append(100 * (1 - float(match.group(1))))  # v tabulce je střední nRMSE
        labels.append(czech if language == "cs" else english)

    figure, axes = plt.subplots(figsize=(7.4, 3.6), facecolor=BACKGROUND_COLOUR)
    bars = axes.bar(range(len(accuracies)), accuracies, width=0.52, color=MODEL_COLOURS["ipn"],
                    edgecolor=BACKGROUND_COLOUR, linewidth=2)
    for bar, value, previous in zip(bars, accuracies, [None] + accuracies[:-1]):
        label = f"{value:.2f} %" + ("" if previous is None else f"\n({value - previous:+.2f})")  # u dalších kroků i přírůstek
        axes.text(bar.get_x() + bar.get_width() / 2, value + 0.15, label, ha="center", va="bottom", fontsize=8.5, color=TEXT_COLOUR)
    axes.set_xticks(range(len(accuracies)))
    axes.set_xticklabels([label.replace(" (", "\n(") for label in labels], fontsize=7.5, color=TEXT_COLOUR)
    axis_start = np.floor(min(accuracies) - 2)
    axes.set_ylim(axis_start, 100)
    axes.yaxis.grid(True, color=GRID_COLOUR, linewidth=0.8)
    axes.set_axisbelow(True)
    axes.set_ylabel(TEXT[language]["unit"], fontsize=8, color=SECONDARY_TEXT_COLOUR)
    axes.set_title(TEXT[language]["ladder"], loc="left", fontsize=10.5, color=TEXT_COLOUR, fontweight="bold")
    style_axes(axes)
    figure.text(0.01, 0.01, TEXT[language]["foot"] + "; " + TEXT[language]["axis"].format(start=axis_start)
                + "; " + TEXT[language]["seed"], fontsize=7, color=FOOTNOTE_COLOUR)
    save_and_close(figure, path, footnote_height=0.04)
    return dict(zip(labels, accuracies))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default=str(C.OUT / "model" / "ipp1-ipn.npz"))
    parser.add_argument("--lang", default="en", choices=["en", "cs"])
    args = parser.parse_args()

    accuracies = collect(args.model)
    overall = overall_chart(accuracies, args.lang, RESULTS_FOLDER / f"ipp1-accuracy-overall-{args.lang}.png")
    outputs_chart(accuracies, args.lang, RESULTS_FOLDER / f"ipp1-accuracy-outputs-{args.lang}.png")
    ladder = ladder_chart(args.lang, RESULTS_FOLDER / f"ipp1-accuracy-ladder-{args.lang}.png")

    print("overall accuracy on the 30 set-aside discharges:", {model: round(value, 2) for model, value in overall.items()})
    print("development ladder:", {label: round(value, 2) for label, value in ladder.items()})
    for model in MODELS:
        worst_three = sorted(accuracies[model].items(), key=lambda item: item[1])[:3]
        print(f"lowest outputs, {model}:", [(name, round(value, 1)) for name, value in worst_three])


if __name__ == "__main__":
    main()
