#!/usr/bin/env python
"""Které vstupy jsou důležité a kolik jich stačí (REQ-004), měřeno na celých odložených výbojích.

    HACKATHON_HOME=<složka hackathonu> python -I analysis/input_importance.py [--epochs 60] [--folds 5]

V každém foldu: učí se síť na všech 24 vstupech, vstupy se seřadí podle permutační důležitosti spočítané JEN na učicích
řádcích (pořadí tak nikdy nevidí testovací výboje), síť se přeučí s nejlepšími k vstupy a také jen s 16 cívkami IPR nebo
jen s 8 smyčkami FL. Pro k = 12, 8, 6 se přidají dvě kontroly, obě vybrané jen na učicích výbojích: náhodná podmnožina
stejné velikosti (3 tahy, zprůměrované), podmnožina bez modelu (QR s pivotací sloupců na standardizovaných vstupech)
a podmnožina z hladového zpětného vyřazování (kritérium ridge regrese). Zapíše out/input-importance.{json,md,png}.

Permutační pořadí je důležitost vstupu pro NATRÉNOVANOU SÍŤ, ne obsah informace: vstupy jsou kolineární, takže promíchání
jednoho sloupce vytvoří řádky mimo varietu dat.

Jen kontroly (levnější běh, zapíše out/input-importance-controls.{json,md} a hlavní soubory nechá být):

    ... input_importance.py --controls-only --only-folds 0,1 --ks 12 --threads 1      (jeden kus, opakovat pro každý fold a k)
    ... input_importance.py --merge                                                   (sesbírá kusy)

Kus znovu natrénuje i síť na všech 24 vstupech a permutační top-k téhož foldu, takže se kontroly porovnávají na stejných
foldech a semínkách.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import torch
from scipy.linalg import qr

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
from common import OUT, TARGETS, fit_mlp, group_folds, load, score

parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=int, default=60)
parser.add_argument("--folds", type=int, default=5)
parser.add_argument("--controls-only", action="store_true")
parser.add_argument("--only-folds", default=None, help="comma separated fold numbers (controls-only)")
parser.add_argument("--ks", default="12,8,6", help="comma separated subset sizes for the controls")
parser.add_argument("--threads", type=int, default=2)
parser.add_argument("--merge", action="store_true", help="collect the controls-only pieces into the controls report")
args = parser.parse_args()
torch.set_num_threads(args.threads)

table, measurements, targets, discharges, exists = load()
INPUT_NAMES = [name for name in table.columns if name.startswith(("IPR", "FL"))]
# Souhrn vynechává dvě souřadnice limiteru a is_limited, které jsou mnohem těžší než zbytek.
SUMMARY_TARGETS = [target for target in TARGETS if target not in ("R_limiter", "Z_limiter", "is_limited")]
SHOWN_TARGETS = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "R_x_point", "R_strike_point_1", "R_limiter"]
TOP_K_SIZES = [16, 12, 8, 6, 5, 4, 3, 2]
CONTROL_K_SIZES = [int(k) for k in args.ks.split(",")]
PIECES_FOLDER = OUT / "input-importance-controls-parts"
rng = np.random.default_rng(0)


def summary_error(scores):
    """Souhrnná chyba: průměr relativní chyby (nRMSE) přes SUMMARY_TARGETS."""
    return float(np.mean([scores[target]["nrmse"] for target in SUMMARY_TARGETS]))


def permutation_order(predict, train_rows):
    """Vstupy seřazené podle permutační důležitosti na 6000 učicích řádcích; vrací (pořadí, důležitost)."""
    sample = rng.choice(train_rows, size=min(6000, len(train_rows)), replace=False)
    baseline_error = summary_error(score(predict(measurements[sample]), targets[sample], exists[sample]))
    importance = np.zeros(measurements.shape[1])
    for column in range(measurements.shape[1]):
        permuted = measurements[sample].copy()
        permuted[:, column] = rng.permutation(permuted[:, column])
        importance[column] = summary_error(score(predict(permuted), targets[sample], exists[sample])) - baseline_error
    return np.argsort(-importance), importance


def qr_pivot_subset(train_rows, k):
    """Sloupce vybrané QR s pivotací na standardizovaných učicích vstupech (bez modelu)."""
    standardized = (measurements[train_rows] - measurements[train_rows].mean(0)) / (measurements[train_rows].std(0) + 1e-9)
    return np.sort(qr(standardized.astype(np.float64), mode="economic", pivoting=True)[2][:k])


def backward_ridge_subset(train_rows, k):
    """Hladové zpětné vyřazování na učicích řádcích: vypadne vstup, jehož odebrání nejméně zvýší součet relativní
    čtvercové chyby ridge regrese (alpha 1, jedna regrese pro každý cíl souhrnu)."""
    standardized = ((measurements[train_rows] - measurements[train_rows].mean(0)) / (measurements[train_rows].std(0) + 1e-9)).astype(np.float64)
    per_target_statistics = []
    for target in SUMMARY_TARGETS:
        column = TARGETS.index(target)
        has_value = exists[train_rows, column]
        x, y = standardized[has_value], targets[train_rows, column][has_value].astype(np.float64)
        x_centered, y_standardized = x - x.mean(0), (y - y.mean()) / (y.std() + 1e-12)
        per_target_statistics.append((x_centered.T @ x_centered, x_centered.T @ y_standardized, len(y_standardized)))

    def loss(columns):
        total, block = 0.0, np.ix_(columns, columns)
        for gram, correlation, n_rows in per_target_statistics:
            weights = np.linalg.solve(gram[block] + np.eye(len(columns)), correlation[columns])
            total += (n_rows - 2 * correlation[columns] @ weights + weights @ gram[block] @ weights) / n_rows
        return total
    columns = list(range(measurements.shape[1]))
    while len(columns) > k:
        columns.remove(min(columns, key=lambda i: loss([c for c in columns if c != i])))
    return np.array(sorted(columns))


def fit_score(columns, train_rows, test_rows, fold):
    """Naučí síť jen na daných vstupních sloupcích a ohodnotí ji na testovacích řádcích."""
    predict, _, _ = fit_mlp(measurements[train_rows][:, columns], targets[train_rows], exists[train_rows], args.epochs, seed=fold)
    return score(predict(measurements[test_rows][:, columns]), targets[test_rows], exists[test_rows])


def random_subsets(fold, k, n_draws=3):
    """Náhodné podmnožiny k vstupů; nezávisí na datech, takže nic neuniká."""
    draw_rng = np.random.default_rng(1000 * (fold + 1) + k)
    return [np.sort(draw_rng.choice(measurements.shape[1], size=k, replace=False)) for _ in range(n_draws)]


def average_scores(score_list):
    """Průměr několika slovníků skóre (3 náhodné tahy) ve struktuře, kterou vrací fit_score."""
    return {target: {"mae": float(np.mean([s[target]["mae"] for s in score_list])),
                     "nrmse": float(np.mean([s[target]["nrmse"] for s in score_list])),
                     "unit": score_list[0][target]["unit"]} for target in TARGETS}


def controls_for_fold(fold, train_rows, test_rows, k):
    """Tři kontroly pro jeden fold a jedno k; vrací {název: (podmnožiny, skóre, souhrny tahů)}."""
    draws = random_subsets(fold, k)
    random_scores = [fit_score(columns, train_rows, test_rows, fold) for columns in draws]
    qr_columns, backward_columns = qr_pivot_subset(train_rows, k), backward_ridge_subset(train_rows, k)
    return {"random": (draws, average_scores(random_scores), [summary_error(s) for s in random_scores]),
            "qr": ([qr_columns], fit_score(qr_columns, train_rows, test_rows, fold), None),
            "ridge": ([backward_columns], fit_score(backward_columns, train_rows, test_rows, fold), None)}


def table_row(score_list):
    """Souhrn jedné varianty přes foldy: průměr a směrodatná odchylka souhrnné chyby a MAE zobrazených cílů."""
    return {"summary_nrmse_mean": float(np.mean([summary_error(s) for s in score_list])),
            "summary_nrmse_std": float(np.std([summary_error(s) for s in score_list])),
            "targets": {target: {"mae": float(np.mean([s[target]["mae"] for s in score_list])), "unit": score_list[0][target]["unit"],
                                 "nrmse": float(np.mean([s[target]["nrmse"] for s in score_list]))} for target in SHOWN_TARGETS}}


def markdown_table(rows_by_name, names, first_header):
    """Tabulka v markdownu: souhrnná chyba a MAE zobrazených cílů pro každou variantu."""
    units = rows_by_name[names[0]]["targets"]
    lines = [f"| {first_header} | summary error | " + " | ".join(f"{target} ({units[target]['unit'] or 'abs'})" for target in SHOWN_TARGETS) + " |",
             "|---|---|" + "---|" * len(SHOWN_TARGETS)]
    for name in names:
        row = rows_by_name[name]
        lines.append(f"| {name} | {row['summary_nrmse_mean']:.3f} ± {row['summary_nrmse_std']:.3f} | "
                     + " | ".join(f"{row['targets'][target]['mae']:.3g}" for target in SHOWN_TARGETS) + " |")
    return lines


# ===================================================================================================================
# Jen kontroly: kusy a jejich sloučení
# ===================================================================================================================
if args.merge:
    pieces = [json.load(open(path)) for path in sorted(PIECES_FOLDER.glob("f*_k*.json"))]
    assert pieces, f"no pieces in {PIECES_FOLDER}"
    k_sizes = sorted({piece["k"] for piece in pieces}, reverse=True)
    # Jen foldy, kde doběhla všechna k, aby každý řádek tabulky byl párový na stejných foldech.
    folds = sorted(fold for fold in {piece["fold"] for piece in pieces}
                   if all(any(piece["fold"] == fold and piece["k"] == k for piece in pieces) for k in k_sizes))
    pieces = [piece for piece in pieces if piece["fold"] in folds]
    runs = {"all 24": []}
    for fold in folds:
        runs["all 24"].append(next(piece for piece in pieces if piece["fold"] == fold)["all24"])
    for k in k_sizes:
        for key, label in (("perm", "permutation top"), ("random", "random (mean of 3 draws)"), ("qr", "QR-pivot"),
                           ("ridge", "backward ridge")):
            runs[f"{label} {k}"] = [piece[key]["score"] for fold in folds for piece in pieces if piece["fold"] == fold and piece["k"] == k]
    rows_by_name = {name: table_row(score_list) for name, score_list in runs.items()}
    names = list(runs)
    extra = {}
    for k in k_sizes:
        pieces_of_k = [piece for piece in pieces if piece["k"] == k]
        extra[str(k)] = {"random_draw_summaries": {str(piece["fold"]): piece["random"]["draw_summaries"] for piece in pieces_of_k},
                         "subsets": {str(piece["fold"]): {key: [[INPUT_NAMES[i] for i in columns] for columns in piece[key]["subsets"]]
                                                          for key in ("perm", "random", "qr", "ridge")} for piece in pieces_of_k}}
    per_fold = {name: [summary_error(s) for s in score_list] for name, score_list in runs.items()}
    json.dump({"folds_run": folds, "epochs": pieces[0]["epochs"], "runs": rows_by_name, "per_fold_summary": per_fold,
               "subsets": extra}, open(OUT / "input-importance-controls.json", "w"), indent=1, allow_nan=False)
    lines = ["# Fewer inputs: controls for the permutation-ranked subsets (REQ-004)", "",
             f"Folds run: {', '.join(str(fold) for fold in folds)} of 5{'' if len(folds) == 5 else ' (partial)'}. One seed per cell, fold SD is about 40 % of the mean, "
             "so read differences under 10 to 15 % as noise. Every subset was chosen on the training discharges of its fold only; "
             "all rows of one fold use the same seed and the same test discharges, so the rows are paired. "
             f"Epochs {pieces[0]['epochs']}. Summary error = mean relative error (RMSE / fold spread) over {len(SUMMARY_TARGETS)} targets, "
             "without the limiter point; lower is better. Columns after it are the mean absolute error in report units.", ""]
    lines += markdown_table(rows_by_name, names, "inputs")
    lines += ["", "Summary error per fold (same order as the folds above):", "",
              "| inputs | " + " | ".join(f"fold {fold}" for fold in folds) + " |", "|---|" + "---|" * len(folds)]
    lines += [f"| {name} | " + " | ".join(f"{value:.3f}" for value in per_fold[name]) + " |" for name in names]
    lines += ["", "Reading: the permutation ranking is the importance of an input for the trained network, not information content. "
              "A random subset of the same size and a model-free QR-pivot or ridge-selected subset show how much of the "
              "top-k curve comes from the ranking method and how much from the number of inputs."]
    (OUT / "input-importance-controls.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0)

if args.controls_only:
    all_folds = group_folds(measurements, targets, discharges, 5)
    PIECES_FOLDER.mkdir(parents=True, exist_ok=True)
    for fold in [int(value) for value in (args.only_folds or "0,1,2,3,4").split(",")]:
        train_rows, test_rows = all_folds[fold]
        predict, _, _ = fit_mlp(measurements[train_rows], targets[train_rows], exists[train_rows], args.epochs, seed=fold)
        all24_score = score(predict(measurements[test_rows]), targets[test_rows], exists[test_rows])
        order, _ = permutation_order(predict, train_rows)
        for k in CONTROL_K_SIZES:
            permutation_columns = np.sort(order[:k])
            permutation_result = {"subsets": [permutation_columns.tolist()], "score": fit_score(permutation_columns, train_rows, test_rows, fold)}
            controls = controls_for_fold(fold, train_rows, test_rows, k)
            piece = {"fold": fold, "k": k, "epochs": args.epochs, "all24": all24_score, "perm": permutation_result}
            for key, (subsets, subset_score, draw_summaries) in controls.items():
                piece[key] = {"subsets": [list(map(int, subset)) for subset in subsets], "score": subset_score}
                if draw_summaries is not None:
                    piece[key]["draw_summaries"] = draw_summaries
            json.dump(piece, open(PIECES_FOLDER / f"f{fold}_k{k}.json", "w"), allow_nan=False)
            print(f"fold {fold} k {k}: all24 {summary_error(all24_score):.3f} perm {summary_error(permutation_result['score']):.3f} "
                  f"random {summary_error(piece['random']['score']):.3f} qr {summary_error(piece['qr']['score']):.3f} "
                  f"ridge {summary_error(piece['ridge']['score']):.3f}", flush=True)
    sys.exit(0)

# ===================================================================================================================
# Celý běh
# ===================================================================================================================
importance_per_fold = np.zeros((args.folds, measurements.shape[1]))
runs = {}
chosen_subsets = {}
for fold, (train_rows, test_rows) in enumerate(group_folds(measurements, targets, discharges, args.folds)):
    predict, _, _ = fit_mlp(measurements[train_rows], targets[train_rows], exists[train_rows], args.epochs, seed=fold)
    order, importance_per_fold[fold] = permutation_order(predict, train_rows)
    runs.setdefault("all 24", []).append(score(predict(measurements[test_rows]), targets[test_rows], exists[test_rows]))
    for k in TOP_K_SIZES:
        columns = np.sort(order[:k])
        runs.setdefault(f"top {k}", []).append(fit_score(columns, train_rows, test_rows, fold))
    for k in CONTROL_K_SIZES:
        for key, label in (("random", "random"), ("qr", "QR-pivot"), ("ridge", "backward ridge")):
            subsets, subset_score, _ = controls_for_fold(fold, train_rows, test_rows, k)[key]
            runs.setdefault(f"{label} {k}", []).append(subset_score)
            chosen_subsets.setdefault(f"{label} {k}", []).append([[INPUT_NAMES[i] for i in subset] for subset in subsets])
    for name, columns in (("IPR only (16)", [i for i, input_name in enumerate(INPUT_NAMES) if input_name.startswith("IPR")]),
                          ("FL only (8)", [i for i, input_name in enumerate(INPUT_NAMES) if input_name.startswith("FL")])):
        runs.setdefault(name, []).append(fit_score(columns, train_rows, test_rows, fold))
    print(f"fold {fold + 1}/{args.folds} done", flush=True)

mean_importance = importance_per_fold.mean(0)
rows_by_name = {name: table_row(score_list) for name, score_list in runs.items()}
ranking = [INPUT_NAMES[i] for i in np.argsort(-mean_importance)]
json.dump({"folds": args.folds, "epochs": args.epochs, "inputs": INPUT_NAMES,
           "permutation_importance": dict(zip(INPUT_NAMES, mean_importance.tolist())),
           "permutation_importance_per_fold": importance_per_fold.tolist(), "ranking": ranking, "control_subsets": chosen_subsets,
           "runs": rows_by_name}, open(OUT / "input-importance.json", "w"), indent=1, allow_nan=False)

row_names = ["all 24"]
for k in TOP_K_SIZES:
    row_names.append(f"top {k}")
    if k in CONTROL_K_SIZES:
        row_names += [f"random {k}", f"QR-pivot {k}", f"backward ridge {k}"]
row_names += ["IPR only (16)", "FL only (8)"]
lines = ["# Fewer inputs: accuracy against the number of inputs (REQ-004)", "",
         f"{args.folds} folds by discharge; summary = mean of the relative error (RMSE / spread) over {len(SUMMARY_TARGETS)} targets, "
         "without the limiter point; lower is better. 'top k' = the k inputs ranked by permutation importance on training rows only; "
         "the sensor set is chosen inside each fold, so a row estimates the procedure, not one fixed set of sensors. "
         "Controls for k in " + ", ".join(map(str, CONTROL_K_SIZES)) + ", also chosen on the training discharges of each fold only: "
         "'random k' = a random subset of the same size (mean of 3 draws), 'QR-pivot k' = columns picked by QR with column "
         "pivoting of the standardised inputs (model free), 'backward ridge k' = greedy backward elimination with a ridge criterion. "
         "One seed per cell; fold SD is large, so differences under 10 to 15 % are noise.", ""]
lines += markdown_table(rows_by_name, row_names, "inputs")
lines += ["", "Ranking by permutation importance (most important first): " + ", ".join(ranking),
          "", "This ranking is the importance of an input for the trained network, not information content: the inputs are "
          "collinear, so permuting one column creates rows off the data manifold. Do not read it as 'the important sensors'; "
          "the evidence for the number of inputs is the retrain curve and its controls above."]
(OUT / "input-importance.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

# Obrázek: chyba podle počtu vstupů (vlevo) a důležitost jednotlivých vstupů (vpravo).
plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False, "font.size": 8})
fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
k_values = [24] + TOP_K_SIZES
errors_mean = [rows_by_name["all 24" if k == 24 else f"top {k}"]["summary_nrmse_mean"] for k in k_values]
errors_std = [rows_by_name["all 24" if k == 24 else f"top {k}"]["summary_nrmse_std"] for k in k_values]
axes[0].errorbar(k_values, errors_mean, yerr=errors_std, marker="o", color="#5b7cff", capsize=2, label="top k by permutation importance")
for label, colour, marker in (("random", "#8d99ae", "s"), ("QR-pivot", "#2a9d8f", "^"), ("backward ridge", "#e9c46a", "D")):
    axes[0].plot(CONTROL_K_SIZES, [rows_by_name[f"{label} {k}"]["summary_nrmse_mean"] for k in CONTROL_K_SIZES],
                 marker=marker, ls=":", color=colour, label=f"{label} k")
for name, colour in (("IPR only (16)", "#e07a5f"), ("FL only (8)", "#3d405b")):
    axes[0].axhline(rows_by_name[name]["summary_nrmse_mean"], color=colour, ls="--", lw=1, label=name)
axes[0].set_xlabel("počet použitých vstupů")
axes[0].set_ylabel("průměrná relativní chyba")
axes[0].set_yscale("log")
axes[0].legend(fontsize=6)
axes[0].set_title("Kolik vstupů stačí (a kontroly výběru)")
by_importance = np.argsort(-mean_importance)
axes[1].bar(range(len(by_importance)), mean_importance[by_importance],
            color=["#e07a5f" if INPUT_NAMES[i].startswith("FL") else "#5b7cff" for i in by_importance])
axes[1].set_xticks(range(len(by_importance)))
axes[1].set_xticklabels([INPUT_NAMES[i] for i in by_importance], rotation=90)
axes[1].set_title("Důležitost pro naučenou síť, ne obsah informace (modře IPR, oranžově FL)")
fig.tight_layout()
fig.savefig(OUT / "input-importance.png")
print("\n".join(lines))
