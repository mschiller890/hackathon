#!/usr/bin/env python
"""IPP 1: poctivé závěrečné vyhodnocení modelu tvaru plazmatu.

Postup
  * Odložených 30 výbojů: vylosované s numpy seedem 20261024 (seznam v results/locked-test-ids.txt).
    Zbývajících 119 výbojů je vývojová sada. Výběr receptur se dělá jen pětinásobnou křížovou validací UVNITŘ
    vývojové sady; odložené výboje se hodnotí jednou, příkazem --report, s modely natrénovanými na celé vývojové sadě.
  * Receptury (všechny se učí po celých výbojích, s maskovanou ztrátou a jedním semínkem):
      base      základní síť z common.fit_mlp (60 epoch) na čistých řádcích
      base_aug  totéž na čistých řádcích plus jedné poškozené kopii (poctivá základna pro zašuměné vstupy)
      cand      obecná síť na 24 vstupech + 22 rozdílech sousedních cívek (Huberova ztráta 0,5, 150 epoch)
                + ridge pro proud plazmatem + síť učená jen na limiterových řádcích (150 epoch), která odpovídá
                za R_limiter a Z_limiter, když obecná síť předpoví is_limited > 0,5
      cand_aug  totéž na čistých řádcích plus jedné poškozené kopii (šum 0,15 a drift 0,15 směrodatné odchylky vstupu),
                75 epoch na dvojnásobném počtu řádků
  * Každá receptura se zkouší na čistých vstupech i na zadaném zašuměném souboru (tytéž řádky z equil_data_noisy.csv).
  * Metriky se počítají přes všechny testovací řádky najednou (ne jako průměr přes díly).

Úlohy (každá natrénuje jeden model a jeho odhady uloží do out/final-evaluation-cache/, nikdy ne do repozitáře):
    python analysis/final_evaluation.py --job cv:cand:0        # díl 0 vývojové sady, receptura cand
    python analysis/final_evaluation.py --job locked:cand      # celá vývojová sada -> odložené výboje
    python analysis/final_evaluation.py --job blocked:cand     # spodní polovina čísel výbojů -> horní polovina
    python analysis/final_evaluation.py --report               # složí out/final-evaluation.json/.md a results/final-evaluation.md
"""
import argparse
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as functional
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, REPO, TARGETS, UNIT, fit_mlp, group_folds, load

# S IPP1_FINAL_SMOKE se každá síť učí jen jednu epochu: slouží to jen k otestování, že všechno spolu funguje.
SMOKE = bool(os.environ.get("IPP1_FINAL_SMOKE"))
CACHE = OUT / ("final-evaluation-cache-smoke" if SMOKE else "final-evaluation-cache")

TARGET_COLUMN = {name: column for column, name in enumerate(TARGETS)}  # název veličiny -> číslo sloupce
LIMITER = [TARGET_COLUMN["R_limiter"], TARGET_COLUMN["Z_limiter"]]

NOISE, DRIFT, AUG_SEED = 0.15, 0.15, 20261023  # síla šumu a driftu při poškozování vstupů a základ jejich semínka
LOCK_SEED, N_LOCK, N_BOOT = 20261024, 30, 1000  # semínko odložených výbojů, jejich počet, počet bootstrapových vzorků
RECIPES = ["base", "base_aug", "cand", "cand_aug"]
HEADLINE = ["plasma_current", "R_mag_axis", "Z_mag_axis", "R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1",
            "R_strike_point_2", "Z_strike_point_2", "R_limiter", "Z_limiter"]


# ===================================================================================================================
# Data a rozdělení na vývojovou a odloženou část
# ===================================================================================================================
def aligned_data():
    """Načte čistá i zašuměná data a ověří, že jde o tytéž řádky se stejnými cíli.

    Vrací (čistá data jako n-tice z load, zašuměné vstupy).
    """
    clean, noisy = load(), load(noisy=True)
    clean_table, noisy_table = clean[0], noisy[0]
    same_rows = (np.array_equal(clean_table.discharge, noisy_table.discharge)
                 and np.allclose(clean_table.time, noisy_table.time, rtol=0, atol=1e-9))
    if not same_rows:
        raise ValueError("čisté a zašuměné řádky si neodpovídají")
    if not np.array_equal(clean[2], noisy[2], equal_nan=True):
        raise ValueError("čisté a zašuměné cíle se liší")
    return clean, noisy[1]


def locked_ids(discharges):
    """Čísla 30 odložených výbojů, vylosovaná vždy stejně ze semínka LOCK_SEED."""
    all_ids = np.unique(discharges)
    return np.sort(np.random.RandomState(LOCK_SEED).choice(all_ids, N_LOCK, replace=False))


def split(discharges):
    """Vrátí (čísla odložených výbojů, řádky vývojové sady, řádky odložených výbojů)."""
    locked = locked_ids(discharges)
    is_locked = np.isin(discharges, locked)
    development_rows, locked_rows = np.where(~is_locked)[0], np.where(is_locked)[0]
    return locked, development_rows, locked_rows


# ===================================================================================================================
# Sítě
# ===================================================================================================================
def corrupt(inputs, discharges, relative_time, input_std, noise_level, drift_level, seed):
    """Poškodí vstupy šumem a driftem: šum je u každého řádku jiný, drift roste lineárně s časem výboje.

    Sklon driftu je pro každý výboj a každou cívku jiný (náhodný), vynásobený relativním časem 0 až 1.
    """
    rng = np.random.default_rng(seed)
    _, discharge_index = np.unique(discharges, return_inverse=True)
    slopes = rng.normal(size=(discharge_index.max() + 1, inputs.shape[1])) * drift_level * input_std
    noise = rng.normal(size=inputs.shape) * noise_level * input_std
    return (inputs + noise + slopes[discharge_index] * relative_time[:, None]).astype(np.float32)


def add_neighbour_differences(inputs):
    """K 24 vstupům přidá rozdíly sousedních cívek IPR01..16 (15 čísel) a smyček FL01..08 (7 čísel)."""
    coil_differences = np.diff(inputs[:, :16], axis=1)
    loop_differences = np.diff(inputs[:, 16:24], axis=1)
    return np.concatenate([inputs, coil_differences, loop_differences], 1).astype(np.float32)


class MLP(nn.Module):
    """Plně propojená síť s libovolnými šířkami skrytých vrstev a aktivací SiLU."""

    def __init__(self, n_inputs, n_outputs, widths):
        super().__init__()
        modules, previous_width = [], n_inputs
        for width in widths:
            modules += [nn.Linear(previous_width, width), nn.SiLU()]
            previous_width = width
        modules.append(nn.Linear(previous_width, n_outputs))
        self.layers = nn.Sequential(*modules)

    def forward(self, x):
        return self.layers(x)


def fit_net(x_train, y_train, exists_train, seed, epochs, rows=None, arch=(256, 256, 128),
            weight_decay=1e-4, huber_delta=0.5, learning_rate=2e-3, max_learning_rate=3e-3, batch_size=512):
    """Natrénuje síť na standardizovaných vstupech a cílech (Huberova ztráta, AdamW, plán učení OneCycle).

    Chyba se počítá jen u cílů, které existují. Pokud je zadané `rows`, učí se jen na těchto řádcích.
    Vrací funkci predict(surové vstupy) -> surové cíle.
    """
    if rows is not None:
        x_train, y_train, exists_train = x_train[rows], y_train[rows], exists_train[rows]
    epochs = 1 if SMOKE else epochs
    torch.manual_seed(seed)

    features = add_neighbour_differences(x_train)
    feature_mean, feature_std = features.mean(0), features.std(0) + 1e-9
    with warnings.catch_warnings():
        # Sloupec bez jediné známé hodnoty (např. bod X na limiterových řádcích) dá NaN; maska ho z ztráty vyřadí.
        warnings.filterwarnings("ignore", "Mean of empty slice|Degrees of freedom", RuntimeWarning)
        target_mean, target_std = np.nanmean(y_train, 0), np.nanstd(y_train, 0) + 1e-9
    x_tensor = torch.tensor((features - feature_mean) / feature_std)
    y_tensor = torch.tensor(np.nan_to_num((y_train - target_mean) / target_std))
    exists_tensor = torch.tensor(exists_train.astype(np.float32))

    network = MLP(x_tensor.shape[1], y_tensor.shape[1], arch)
    optimizer = torch.optim.AdamW(network.parameters(), lr=learning_rate, weight_decay=weight_decay)
    steps = epochs * ((len(x_tensor) + batch_size - 1) // batch_size)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=max_learning_rate, total_steps=steps)

    for _ in range(epochs):
        shuffled = torch.randperm(len(x_tensor))
        for start in range(0, len(x_tensor), batch_size):
            batch = shuffled[start:start + batch_size]
            error = 2 * functional.huber_loss(network(x_tensor[batch]), y_tensor[batch], reduction="none", delta=huber_delta)
            loss = (error * exists_tensor[batch]).sum() / exists_tensor[batch].sum()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
    network.eval()
    feature_mean32, feature_std32 = feature_mean.astype(np.float32), feature_std.astype(np.float32)

    def predict(x):
        with torch.inference_mode():
            standardized = (add_neighbour_differences(x) - feature_mean32) / feature_std32
            return network(torch.from_numpy(standardized)).numpy() * target_std + target_mean

    return predict


def fit_ridge_coefficients(x_train, y_train, exists_train, column, alpha=1.0):
    """Ridge regrese pro jedinou veličinu (sloupec `column`) na standardizovaných surových vstupech.

    Vrací (váhy, posun) přepočtené tak, aby šly použít přímo na surové vstupy: odhad = vstupy @ váhy + posun.
    """
    x_mean, x_std = x_train.mean(0), x_train.std(0) + 1e-9
    rows = exists_train[:, column]
    model = Ridge(alpha=alpha).fit((x_train[rows] - x_mean) / x_std, y_train[rows, column])
    weights = (model.coef_ / x_std).astype(np.float64)
    offset = float(model.intercept_ - (x_mean * weights).sum())
    return weights, offset


def fit_ridge_col(x_train, y_train, exists_train, column, alpha=1.0):
    """Jako fit_ridge_coefficients, ale vrátí rovnou funkci: surové vstupy -> odhad veličiny."""
    weights, offset = fit_ridge_coefficients(x_train, y_train, exists_train, column, alpha)
    return lambda x: x.astype(np.float64) @ weights + offset


def replace_column(predict, column, replacement):
    """Z funkce predict udělá novou, která ve sloupci `column` vrací odhad funkce `replacement`."""
    def predict_with_replacement(x):
        prediction = predict(x).copy()
        prediction[:, column] = replacement(x)
        return prediction
    return predict_with_replacement


def answer_limiter_with_specialist(general, specialist, columns):
    """Sloupce `columns` (bod limiteru) předpoví specialista, ale jen na řádcích, které obecná síť označila
    za limiterové (is_limited > 0,5). Všude jinde odpovídá obecná síť."""
    columns = list(columns)

    def predict(x):
        prediction = general(x).copy()
        limited = prediction[:, TARGET_COLUMN["is_limited"]] > 0.5
        if limited.any():
            prediction[np.ix_(limited, columns)] = specialist(x[limited])[:, columns]
        return prediction

    return predict


def train(recipe, x, y, exists, discharges, relative_time, seed, augmentation_seed):
    """Natrénuje jednu recepturu na zadaných (čistých) řádcích. Receptury *_aug přidají jednu poškozenou kopii řádků."""
    augmented = recipe.endswith("_aug")
    if augmented:
        corrupted = corrupt(x, discharges, relative_time, x.std(axis=0), NOISE, DRIFT, augmentation_seed)
        x, y, exists = np.concatenate([x, corrupted]), np.tile(y, (2, 1)), np.tile(exists, (2, 1))
    if recipe.startswith("base"):
        return fit_mlp(x, y, exists, 1 if SMOKE else 60, seed=seed)[0]

    epochs = 75 if augmented else 150
    general = fit_net(x, y, exists, seed, epochs)
    limiter_specialist = fit_net(x, y, exists, seed, epochs, rows=y[:, TARGET_COLUMN["is_limited"]] > 0.5)
    current_column = TARGET_COLUMN["plasma_current"]
    general_with_ridge_current = replace_column(general, current_column, fit_ridge_col(x, y, exists, current_column))
    return answer_limiter_with_specialist(general_with_ridge_current, limiter_specialist, LIMITER)


# ===================================================================================================================
# Úlohy: natrénuje jeden model a uloží jeho odhady
# ===================================================================================================================
def job(spec, threads):
    """Spustí jednu úlohu zadanou jako 'cv:receptura:díl', 'locked:receptura' nebo 'blocked:receptura'."""
    torch.set_num_threads(threads)
    (table, X, Y, discharges, exists), noisy_X = aligned_data()
    relative_time = table.time.to_numpy()
    locked, development_rows, locked_rows = split(discharges)
    kind, recipe, *rest = spec.split(":")
    assert recipe in RECIPES

    if kind == "cv":
        # díl k pětinásobné křížové validace uvnitř vývojové sady
        fold = int(rest[0])
        train_pos, test_pos = group_folds(X[development_rows], Y[development_rows], discharges[development_rows], 5)[fold]
        train_rows, test_rows = development_rows[train_pos], development_rows[test_pos]
        seed, augmentation_seed, name = fold, AUG_SEED + fold, f"cv_{recipe}_{fold}"
    elif kind == "locked":
        # celá vývojová sada -> odložené výboje (ty hodnotí až --report)
        train_rows, test_rows = development_rows, locked_rows
        seed, augmentation_seed, name = 0, AUG_SEED + 50, f"locked_{recipe}"
    elif kind == "blocked":
        # spodní polovina čísel výbojů -> horní polovina (čísla jdou chronologicky)
        ids = np.unique(discharges[development_rows])
        lower_ids = ids[:len(ids) - len(ids) // 2]
        in_lower = np.isin(discharges[development_rows], lower_ids)
        train_rows, test_rows = development_rows[in_lower], development_rows[~in_lower]
        seed, augmentation_seed, name = 0, AUG_SEED + 60, f"blocked_{recipe}"
    else:
        raise ValueError(spec)

    assert not set(discharges[train_rows]) & set(discharges[test_rows])
    if kind != "locked":
        assert not set(discharges[test_rows]) & set(locked)  # odložené výboje se mimo --report nesmí dotknout

    CACHE.mkdir(parents=True, exist_ok=True)
    started = time.time()
    predict = train(recipe, X[train_rows], Y[train_rows], exists[train_rows], discharges[train_rows],
                    relative_time[train_rows], seed, augmentation_seed)
    np.savez(CACHE / f"{name}.npz", idx=test_rows,
             clean=predict(X[test_rows]).astype(np.float32), noisy=predict(noisy_X[test_rows]).astype(np.float32))
    print(f"{name}: train {len(train_rows)} rows / {len(np.unique(discharges[train_rows]))} discharges, "
          f"test {len(test_rows)} rows / {len(np.unique(discharges[test_rows]))} discharges, "
          f"{time.time() - started:.0f} s", flush=True)


# ===================================================================================================================
# Metriky
# ===================================================================================================================
def pooled_stats(prediction, targets, exists):
    """Statistiky po veličinách přes všechny dané řádky najednou, v jednotkách z tabulek (mm, kA)."""
    stats = {}
    for column, name in enumerate(TARGETS):
        rows = exists[:, column]
        if rows.sum() < 2:
            stats[name] = None
            continue
        scale, unit = UNIT[name]
        error = (prediction[rows, column] - targets[rows, column]).astype(np.float64)
        absolute = np.abs(error) * scale
        spread = targets[rows, column].astype(np.float64).std()
        sum_of_squares = ((targets[rows, column] - targets[rows, column].mean()) ** 2).sum()
        values = {
            "n": int(rows.sum()), "unit": unit,
            "mae": absolute.mean(), "median": np.median(absolute), "rmse": np.sqrt((error ** 2).mean()) * scale,
            "p95": np.percentile(absolute, 95), "p99": np.percentile(absolute, 99), "max": absolute.max(),
            "nrmse": np.sqrt((error ** 2).mean()) / spread if spread > 0 else None,
            "r2": 1 - (error ** 2).sum() / sum_of_squares if sum_of_squares > 0 else None,
        }
        if name == "is_limited":
            values["accuracy"] = float(((prediction[rows, column] > 0.5) == (targets[rows, column] > 0.5)).mean())
        stats[name] = {key: (float(v) if isinstance(v, (float, np.floating)) else v) for key, v in values.items()}
    return stats


def mean_nrmse(stats):
    """Průměr relativní chyby (nRMSE) přes všech 16 veličin: číslo, podle kterého se vybírají receptury."""
    return float(np.mean([stats[name]["nrmse"] for name in TARGETS]))


def bootstrap(predictions, targets, exists, discharges, target_names, seed=LOCK_SEED + 1):
    """Bootstrap po výbojích (náhodně se losují celé výboje) s 95% intervaly.

    predictions: {název receptury: odhady}. Pro každou recepturu a veličinu vrátí střední chybu a RMSE s intervaly
    a pro všechny receptury kromě první i poměr střední chyby k první receptuře (párově, na týchž vzorcích).
    """
    discharge_ids = np.unique(discharges)
    discharge_index = np.searchsorted(discharge_ids, discharges)
    rng = np.random.RandomState(seed)
    # counts[i, d] = kolikrát se výboj d dostal do i-tého bootstrapového vzorku
    counts = np.stack([np.bincount(rng.randint(0, len(discharge_ids), len(discharge_ids)), minlength=len(discharge_ids))
                       for _ in range(N_BOOT)]).astype(np.float64)
    recipe_names = list(predictions)

    # Pro každý výboj zvlášť: součet absolutních chyb, součet čtverců chyb a počet řádků.
    per_discharge = {}
    for recipe in recipe_names:
        for target in target_names:
            column = TARGET_COLUMN[target]
            rows = exists[:, column]
            error = np.where(rows, (predictions[recipe][:, column] - targets[:, column]).astype(np.float64), 0.0)
            sum_abs = np.bincount(discharge_index, weights=np.abs(error), minlength=len(discharge_ids))
            sum_sq = np.bincount(discharge_index, weights=error ** 2, minlength=len(discharge_ids))
            n_rows = np.bincount(discharge_index, weights=rows.astype(float), minlength=len(discharge_ids))
            per_discharge[(recipe, target)] = (sum_abs, sum_sq, n_rows)

    def interval(values):
        return [float(np.nanpercentile(values, 2.5)), float(np.nanpercentile(values, 97.5))]

    result = {recipe: {} for recipe in recipe_names}
    for recipe in recipe_names:
        for target in target_names:
            sum_abs, sum_sq, n_rows = per_discharge[(recipe, target)]
            scale = UNIT[target][0]
            rows_in_sample = counts @ n_rows
            with np.errstate(invalid="ignore", divide="ignore"):
                mae = (counts @ sum_abs) / rows_in_sample * scale
                rmse = np.sqrt((counts @ sum_sq) / rows_in_sample) * scale
            result[recipe][target] = {
                "mae": float(sum_abs.sum() / n_rows.sum() * scale), "mae_ci": interval(mae),
                "rmse": float(np.sqrt(sum_sq.sum() / n_rows.sum()) * scale), "rmse_ci": interval(rmse),
            }
    first = recipe_names[0]
    for recipe in recipe_names[1:]:
        for target in target_names:
            this, reference = per_discharge[(recipe, target)], per_discharge[(first, target)]
            with np.errstate(invalid="ignore", divide="ignore"):
                ratio = ((counts @ this[0]) / (counts @ this[2])) / ((counts @ reference[0]) / (counts @ reference[2]))
            result[recipe][target]["mae_ratio_vs_" + first] = float(this[0].sum() / this[2].sum() / (reference[0].sum() / reference[2].sum()))
            result[recipe][target]["mae_ratio_ci"] = interval(ratio)
    return result


# ===================================================================================================================
# Zpráva: složí uložené odhady do out/final-evaluation.json a results/final-evaluation.md
# ===================================================================================================================
def assemble(prefix, recipes, n_folds=None):
    """Načte uložené odhady jedné fáze (cv / locked / blocked) a seřadí je podle čísel řádků.

    Pro každou recepturu vrátí {"idx": řádky, "clean": odhady na čistých vstupech, "noisy": odhady na zašuměných}.
    Receptury, jejichž soubory ještě nejsou, se přeskočí.
    """
    assembled = {}
    for recipe in recipes:
        if n_folds is None:
            files = [CACHE / f"{prefix}_{recipe}.npz"]
        else:
            files = [CACHE / f"{prefix}_{recipe}_{fold}.npz" for fold in range(n_folds)]
        if not all(file.exists() for file in files):
            continue
        parts = [np.load(file) for file in files]
        rows = np.concatenate([part["idx"] for part in parts])
        order = np.argsort(rows)
        assembled[recipe] = {
            "idx": rows[order],
            "clean": np.concatenate([part["clean"] for part in parts])[order],
            "noisy": np.concatenate([part["noisy"] for part in parts])[order],
        }
    return assembled


def fmt(value, digits=3):
    """Číslo na tři platné číslice, nebo n/a, když chybí."""
    return "n/a" if value is None else f"{value:.{digits}g}"


def report():
    (table, X, Y, discharges, exists), noisy_X = aligned_data()
    relative_time = table.time.to_numpy()
    locked, development_rows, locked_rows = split(discharges)

    # Soubor se seznamem odložených výbojů (je v repozitáři, ať je vidět, které to jsou).
    ids_file = REPO / "results/locked-test-ids.txt"
    ids_file.parent.mkdir(parents=True, exist_ok=True)
    development_ids = np.unique(discharges[development_rows])
    ids_file.write_text(
        f"Locked test set of IPP 1 (hackathon task 1): {N_LOCK} of {len(np.unique(discharges))} discharges.\n"
        f"Drawn with numpy.random.RandomState({LOCK_SEED}).choice(sorted unique discharge ids, {N_LOCK}, replace=False), then sorted.\n"
        f"The other {len(development_ids)} discharges are the development set; every recipe choice uses 5-fold GroupKFold inside it.\n"
        f"The locked discharges are scored once, by models trained on all development discharges (analysis/final_evaluation.py --report).\n\n"
        f"locked discharge ids ({len(locked)}): {' '.join(str(i) for i in locked)}\n")

    results = {"protocol": {
        "locked_seed": LOCK_SEED, "locked_ids": [int(i) for i in locked], "n_dev_discharges": int(len(development_ids)),
        "n_dev_rows": int(len(development_rows)), "n_locked_rows": int(len(locked_rows)), "bootstrap": N_BOOT,
        "seed": "one per model"}}

    # --- vývojová sada: odhady z křížové validace, podle nich se vybírají receptury
    cross_validation = assemble("cv", RECIPES, 5)
    development = {}
    for recipe, predictions in cross_validation.items():
        if len(predictions["idx"]) != len(development_rows):
            continue  # ještě nejsou hotové všechny díly
        development[recipe] = {kind: pooled_stats(predictions[kind], Y[predictions["idx"]], exists[predictions["idx"]])
                               for kind in ("clean", "noisy")}
        development[recipe]["all16_clean"] = mean_nrmse(development[recipe]["clean"])
        development[recipe]["all16_noisy"] = mean_nrmse(development[recipe]["noisy"])
    results["development_cv"] = development
    choice = {}
    for kind in ("clean", "noisy"):
        if development:
            choice[kind] = min(development, key=lambda recipe: development[recipe]["all16_" + kind])
    results["choice"] = choice

    # --- odložené výboje
    locked_predictions = assemble("locked", RECIPES)
    locked_predictions = {recipe: p for recipe, p in locked_predictions.items() if np.array_equal(p["idx"], locked_rows)}
    names = [recipe for recipe in RECIPES if recipe in locked_predictions]
    locked_y, locked_exists, locked_discharges = Y[locked_rows], exists[locked_rows], discharges[locked_rows]
    locked_stats = {recipe: {kind: pooled_stats(locked_predictions[recipe][kind], locked_y, locked_exists)
                             for kind in ("clean", "noisy")} for recipe in names}
    for recipe in names:
        locked_stats[recipe]["all16_clean"] = mean_nrmse(locked_stats[recipe]["clean"])
        locked_stats[recipe]["all16_noisy"] = mean_nrmse(locked_stats[recipe]["noisy"])
    results["locked"] = locked_stats
    if names:
        bootstraps = {kind: bootstrap({recipe: locked_predictions[recipe][kind] for recipe in names},
                                      locked_y, locked_exists, locked_discharges, HEADLINE) for kind in ("clean", "noisy")}
    else:
        bootstraps = {}
    results["bootstrap"] = bootstraps

    # --- rozpad odložených výbojů podle polarity, času ve výboji a konfigurace
    polarity = np.sign(np.array([np.nanmedian(Y[locked_rows][locked_discharges == d, 0]) for d in locked_discharges]))
    time_in_discharge = relative_time[locked_rows]
    is_limited = Y[locked_rows][:, TARGET_COLUMN["is_limited"]] > 0.5
    groups = {
        "polarity": {"negative plasma current": polarity < 0, "positive plasma current": polarity > 0},
        "relative time": {"first 2 %": time_in_discharge <= 0.02,
                          "middle": (time_in_discharge > 0.02) & (time_in_discharge < 0.98),
                          "last 2 %": time_in_discharge >= 0.98},
        "configuration": {"divertor": ~is_limited, "limited": is_limited},
    }
    results["polarity_discharges"] = {"positive": int(len(np.unique(locked_discharges[polarity > 0]))),
                                      "negative": int(len(np.unique(locked_discharges[polarity < 0])))}
    breakdown = {}
    for group_name, cells in groups.items():
        for cell_name, selected in cells.items():
            breakdown[f"{group_name}: {cell_name}"] = {
                "rows": int(selected.sum()), "discharges": int(len(np.unique(locked_discharges[selected]))),
                **{recipe: {kind: pooled_stats(locked_predictions[recipe][kind][selected], locked_y[selected], locked_exists[selected])
                            for kind in ("clean", "noisy")} for recipe in names}}
    results["breakdown"] = breakdown

    # --- dělení podle čísel výbojů (blokové) proti náhodným dílům, jen ve vývojové sadě
    blocked_predictions = assemble("blocked", RECIPES)
    blocked = {}
    if blocked_predictions:
        ids = np.unique(discharges[development_rows])
        upper_ids = ids[len(ids) - len(ids) // 2:]
        for recipe, predictions in blocked_predictions.items():
            upper_rows = predictions["idx"]
            row = {"train_discharges": int(len(ids) - len(upper_ids)), "test_discharges": int(len(upper_ids)),
                   "test_rows": int(len(upper_rows))}
            row["blocked"] = {kind: pooled_stats(predictions[kind], Y[upper_rows], exists[upper_rows]) for kind in ("clean", "noisy")}
            if recipe in cross_validation and len(cross_validation[recipe]["idx"]) == len(development_rows):
                same_discharges = np.isin(cross_validation[recipe]["idx"], upper_rows)
                rows_of_cv = cross_validation[recipe]["idx"][same_discharges]
                row["random_folds_same_discharges"] = {
                    kind: pooled_stats(cross_validation[recipe][kind][same_discharges], Y[rows_of_cv], exists[rows_of_cv])
                    for kind in ("clean", "noisy")}
                row["random_folds_all_dev"] = development[recipe]
            blocked[recipe] = row
    results["blocked"] = blocked

    (OUT / "final-evaluation.json").write_text(json.dumps(results, indent=1))
    markdown = render(results, names)
    notes = OUT / "final-evaluation-notes.md"
    if notes.exists():
        markdown = markdown.replace("\n## Development set", "\n" + notes.read_text().strip() + "\n\n## Development set", 1)
    (OUT / "final-evaluation.md").write_text(markdown)
    (REPO / "results").mkdir(parents=True, exist_ok=True)
    (REPO / "results/final-evaluation.md").write_text(markdown)
    print(markdown)


RECIPE_LABEL = {"base": "baseline MLP", "base_aug": "baseline MLP, augmented (extra)",
                "cand": "candidate, plain", "cand_aug": "candidate, augmented"}


def render(results, names):
    """Složí výsledky do markdownu results/final-evaluation.md (text je anglicky, protože ho čtou i organizátoři)."""
    lines = []
    protocol = results["protocol"]
    lines += ["# IPP 1: final evaluation on a locked test set", "",
              f"Locked test set: {N_LOCK} discharges ({protocol['n_locked_rows']} rows) drawn with numpy seed {LOCK_SEED}; ids in `results/locked-test-ids.txt`. "
              f"Development set: the other {protocol['n_dev_discharges']} discharges ({protocol['n_dev_rows']} rows). Recipe choices use 5-fold GroupKFold inside the "
              "development set only; the locked set was scored once, with models trained on all development discharges. All metrics are pooled over "
              "the rows of the test set (not means of folds). Every model is one seed (seed noise of earlier runs: 8 to 19 %), so read differences "
              "below about 20 % between recipes as unresolved unless the bootstrap interval excludes 1.", "",
              "Recipes: `baseline MLP` = common.fit_mlp, 60 epochs. `candidate` = network on 24 inputs + 22 neighbouring-coil differences "
              "(Huber 0.5, 150 epochs) + ridge for plasma_current + a limited-rows network for R_limiter and Z_limiter gated by the predicted is_limited. "
              "`augmented` = trained on the clean rows plus one copy with noise 0.15 and drift 0.15 of each input's SD (candidate: 75 epochs on twice the rows; "
              "baseline: 60 epochs on twice the rows, an extra control). `clean` = clean inputs, `noisy` = the provided noisy file (same rows).", ""]

    if results["choice"]:
        lines += ["## Which recipe to ship", ""]
        development = results["development_cv"]
        for kind in ("clean", "noisy"):
            chosen = results["choice"][kind]
            all_recipes = ", ".join(f"{RECIPE_LABEL[r]} {development[r]['all16_' + kind]:.4f}" for r in development)
            lines.append(f"- **{kind} inputs: {RECIPE_LABEL[chosen]}** (`{chosen}`): lowest mean nRMSE over the 16 targets in the development cross-validation "
                         f"({all_recipes}).")
        if names:
            lines.append("- Locked-set check of that choice: mean nRMSE over 16 targets, " + "; ".join(
                f"{kind}: " + ", ".join(f"{RECIPE_LABEL[r]} {results['locked'][r]['all16_' + kind]:.4f}" for r in names)
                for kind in ("clean", "noisy")) + ".")
        lines.append("")

    lines += ["## Development set: pooled out-of-fold scores (5 group folds inside the 119 development discharges)", ""]
    development = results["development_cv"]
    if development:
        lines += ["| recipe | inputs | mean nRMSE (16) | " + " | ".join(f"{t} MAE" for t in HEADLINE) + " |",
                  "|---|---|---:|" + "---:|" * len(HEADLINE)]
        for recipe in development:
            for kind in ("clean", "noisy"):
                lines.append(f"| {RECIPE_LABEL[recipe]} | {kind} | {development[recipe]['all16_' + kind]:.4f} | "
                             + " | ".join(fmt(development[recipe][kind][t]["mae"]) for t in HEADLINE) + " |")
        lines.append("")
        lines.append("Units: mm for R and Z targets, kA for plasma_current.")
        lines.append("")
    if not names:
        lines += ["## Locked test", "", "No locked predictions cached yet.", ""]
        return "\n".join(lines) + "\n"

    for kind in ("clean", "noisy"):
        lines += [f"## Locked test, {kind} inputs: all metrics per target, pooled over {protocol['n_locked_rows']} rows", ""]
        for recipe in names:
            stats = results["locked"][recipe][kind]
            lines += [f"### {RECIPE_LABEL[recipe]}, {kind} inputs (mean nRMSE over 16 targets {results['locked'][recipe]['all16_' + kind]:.4f})", "",
                      "| target | unit | n | MAE | median | RMSE | p95 | p99 | max | nRMSE | R2 |",
                      "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
            for target in TARGETS:
                row = stats[target]
                lines.append(f"| {target} | {row['unit']} | {row['n']} | "
                             + " | ".join(fmt(row[key]) for key in ("mae", "median", "rmse", "p95", "p99", "max", "nrmse", "r2")) + " |")
            lines += ["", f"is_limited accuracy: {stats['is_limited']['accuracy']:.4f}", ""]

    for kind in ("clean", "noisy"):
        lines += [f"## Locked test, {kind} inputs: cluster bootstrap by discharge ({N_BOOT} resamples, 95 % intervals)", "",
                  "MAE and RMSE with intervals; ratio = MAE of the recipe over MAE of the baseline MLP on the same resamples (below 1 means better).", ""]
        boot = results["bootstrap"][kind]
        lines += ["| target | unit | " + " | ".join(f"{RECIPE_LABEL[r]} MAE [95 %]" for r in names) + " | "
                  + " | ".join(f"MAE ratio {r}/{names[0]} [95 %]" for r in names[1:]) + " |",
                  "|---|---|" + "---:|" * (2 * len(names) - 1)]
        for target in HEADLINE:
            mae_cells = [f"{fmt(boot[r][target]['mae'])} [{fmt(boot[r][target]['mae_ci'][0])}, {fmt(boot[r][target]['mae_ci'][1])}]" for r in names]
            ratio_cells = [f"{boot[r][target]['mae_ratio_vs_' + names[0]]:.2f} "
                           f"[{boot[r][target]['mae_ratio_ci'][0]:.2f}, {boot[r][target]['mae_ratio_ci'][1]:.2f}]" for r in names[1:]]
            lines.append(f"| {target} | {UNIT[target][1]} | " + " | ".join(mae_cells) + " | " + " | ".join(ratio_cells) + " |")
        lines += ["", "RMSE with intervals:", "",
                  "| target | unit | " + " | ".join(f"{RECIPE_LABEL[r]} RMSE [95 %]" for r in names) + " |", "|---|---|" + "---:|" * len(names)]
        for target in HEADLINE:
            lines.append(f"| {target} | {UNIT[target][1]} | " + " | ".join(
                f"{fmt(boot[r][target]['rmse'])} [{fmt(boot[r][target]['rmse_ci'][0])}, {fmt(boot[r][target]['rmse_ci'][1])}]" for r in names) + " |")
        lines.append("")

    polarity = results["polarity_discharges"]
    lines += ["## Locked test: breakdowns (MAE per headline target; p95 is in the json)", "",
              f"Polarity is the sign of the plasma current of the discharge: {polarity['negative']} negative and {polarity['positive']} positive locked discharges. "
              "Relative time is the row's time scaled to 0..1 within its discharge. Configuration is the true is_limited. n = rows.", ""]
    for key, cell in results["breakdown"].items():
        lines += [f"### {key} ({cell['rows']} rows, {cell['discharges']} discharges)", "",
                  "| target | unit | " + " | ".join(f"{RECIPE_LABEL[r]} {kind}" for kind in ("clean", "noisy") for r in names) + " |",
                  "|---|---|" + "---:|" * (2 * len(names))]
        for target in HEADLINE:
            values = []
            for kind in ("clean", "noisy"):
                for recipe in names:
                    stats = cell[recipe][kind][target]
                    values.append("n/a" if stats is None else fmt(stats["mae"]) + (f" (n={stats['n']})" if stats["n"] < 100 else ""))
            lines.append(f"| {target} | {UNIT[target][1]} | " + " | ".join(values) + " |")
        lines.append("")

    if results["blocked"]:
        lines += ["## Blocked-by-id split against random group folds (development set only)", "",
                  "Train on the lower half of the development discharge ids, test on the upper half. Discharge ids are chronological, so this is a test on later "
                  "campaigns. The random-fold numbers are the pooled out-of-fold errors of the SAME recipe on the SAME upper-half discharges, and on all "
                  "development discharges. Caveat: the blocked model trains on about 60 discharges, the random folds on about 95, so part of the gap is the "
                  "smaller training set, not only the drift between campaigns.", ""]
        for recipe, row in results["blocked"].items():
            lines += [f"### {RECIPE_LABEL[recipe]} ({row['train_discharges']} training, {row['test_discharges']} test discharges, {row['test_rows']} test rows)", "",
                      "| target | unit | inputs | blocked MAE | random folds, same discharges MAE | ratio | random folds, all development MAE |",
                      "|---|---|---|---:|---:|---:|---:|"]
            for target in HEADLINE:
                for kind in ("clean", "noisy"):
                    blocked_mae = row["blocked"][kind][target]["mae"]
                    same = row.get("random_folds_same_discharges", {}).get(kind, {}).get(target)
                    all_dev = row.get("random_folds_all_dev", {}).get(kind, {}).get(target)
                    if same:
                        lines.append(f"| {target} | {UNIT[target][1]} | {kind} | {fmt(blocked_mae)} | {fmt(same['mae'])} | "
                                     f"{blocked_mae / same['mae']:.2f} | {fmt(all_dev['mae']) if all_dev else 'n/a'} |")
                    else:
                        lines.append(f"| {target} | {UNIT[target][1]} | {kind} | {fmt(blocked_mae)} | n/a | n/a | n/a |")
            lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--job", default="", help="cv:<receptura>:<díl>, locked:<receptura> nebo blocked:<receptura>")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.job:
        job(args.job, args.threads)
    if args.report:
        report()
