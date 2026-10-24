#!/usr/bin/env python
"""Odchylky modelu od rekonstrukce ústavu v milimetrech (IPP, úloha 1).

    python analysis/error_in_mm.py [--model out/model/clean-model.npz] [--set locked|dev|all] [--noisy] [--csv SOUBOR] [--json VÝSTUP]

Data: ve výchozím stavu equil_data.zip (s --noisy equil_data_noisy.zip; funguje i původní .csv) ze složky data/ repozitáře nebo z $HACKATHON_HOME.
--csv vezme libovolný soubor s 24 vstupy IPR01..IPR16 a FL01..FL08, sloupcem `discharge`, volitelně `time` a libovolnými
cílovými sloupci; veličiny, jejichž sloupec chybí, se přeskočí.
Sady: `locked` = 30 výbojů ze souboru results/locked-test-ids.txt (tatáž sada jako v results/final-evaluation.md),
`dev` = všechny ostatní, `all` = všechny. Výchozí je `locked` pro data ústavu a `all` pro --csv.

Odhady počítá predict.Model z kořene repozitáře, tedy tentýž numpy kód, který pouští porota. Každá veličina se hodnotí
na řádcích, kde pro ni rekonstrukce hodnotu má (bod X a dotykové body jen na divertorových řádcích, bod limiteru jen
na limiterových, ať si model o konfiguraci myslí cokoli), stejně jako v results/final-evaluation.md. 95% intervaly jsou
bootstrap po výbojích: celé výboje se 1000krát losují s vracením (numpy RandomState(20261025), tytéž tahy jako
final_evaluation.bootstrap). Výstup popisuje řádky jen číslem výboje a relativním časem, žádná vstupní hodnota se nevypisuje.
"""
import argparse
import json
import os
import sys
import textwrap
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # predict.py v kořeni repozitáře (kopie pro porotu)
from predict import Model

NESTED_DATA = Path("data/raw/ipp1-magnetic/uloha_1-magneticka_data")  # původní struktura z archivu
LOCKED_IDS_FILE = REPO / "results/locked-test-ids.txt"
INPUTS = [f"IPR{i:02d}" for i in range(1, 17)] + [f"FL{i:02d}" for i in range(1, 9)]
TARGETS = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity", "triangularity_upper", "triangularity_lower",
           "R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2",
           "R_limiter", "Z_limiter", "is_limited"]
# Polohy v mm a jejich české názvy ve výpisu.
POSITIONS = {
    "R_mag_axis": "osa R", "Z_mag_axis": "osa Z", "R_x_point": "X bod R", "Z_x_point": "X bod Z",
    "R_strike_point_1": "bod dopadu 1 R", "Z_strike_point_1": "bod dopadu 1 Z",
    "R_strike_point_2": "bod dopadu 2 R", "Z_strike_point_2": "bod dopadu 2 Z",
    "R_limiter": "bod limiteru R", "Z_limiter": "bod limiteru Z",
}
AXIS_2D_NAME, CURRENT_NAME = "osa 2D vzdálenost", "proud plazmatu kA"
THRESHOLDS_MM = (0.1, 0.5, 1.0, 2.0, 5.0)  # prahy pro podíl řádků s malou odchylkou
PERCENTILES = (90, 95, 99, 99.9)
N_BOOTSTRAP, BOOTSTRAP_SEED = 1000, 20261025


def fail(message):
    sys.exit(f"error_in_mm: {message}")


# ===================================================================================================================
# Vstupy: model, data, výběr sady výbojů
# ===================================================================================================================
def default_model():
    """Výchozí model: out/model/clean-model.npz v $HACKATHON_HOME, v repozitáři, vedle něj, nebo v model/."""
    homes = [Path(os.environ["HACKATHON_HOME"])] if os.environ.get("HACKATHON_HOME") else []
    candidates = [home / "out/model/clean-model.npz" for home in homes + [REPO, REPO.parent]] + [REPO / "model/clean-model.npz"]
    return next((path for path in candidates if path.exists()), candidates[0])


def ipp_file(noisy):
    """Soubor s daty ústavu: data/ (soubory jsou v repozitáři) nebo původní struktura z archivu."""
    stem = "equil_data_noisy" if noisy else "equil_data"
    homes = [Path(os.environ["HACKATHON_HOME"])] if os.environ.get("HACKATHON_HOME") else []
    for home in homes + [REPO, Path.cwd()]:
        for subfolder in (Path("data"), NESTED_DATA):
            for name in (f"{stem}.zip", f"{stem}.csv"):
                if (home / subfolder / name).exists():
                    return home / subfolder / name
    fail(f"data nenalezena: {stem}.zip ani {stem}.csv není v {NESTED_DATA} pod HACKATHON_HOME "
         f"({os.environ.get('HACKATHON_HOME', 'nenastaveno')}) ani pod {REPO}. Nastavte HACKATHON_HOME nebo použijte --csv.")


def read_table(path, model_inputs):
    """Načte CSV a vrátí (vstupy, {veličina: referenční hodnoty}, čísla výbojů, relativní čas)."""
    import pandas as pd
    try:
        table = pd.read_csv(path)
    except Exception as error:  # nečitelný nebo prázdný soubor: raději to říct než ukázat výpis chyby
        fail(f"soubor {path} nelze načíst: {error}")
    missing = [name for name in model_inputs + ["discharge"] if name not in table.columns]
    if missing:
        fail(f"v {path} chybí sloupce: {', '.join(missing)}")
    if not [name for name in POSITIONS if name in table.columns]:
        fail(f"v {path} není žádný sloupec polohy ({', '.join(POSITIONS)}), není s čím srovnávat")
    try:
        inputs = table[model_inputs].to_numpy(np.float64)
    except ValueError:
        fail(f"vstupní sloupce v {path} nejsou číselné")
    if not np.isfinite(inputs).all():
        fail(f"vstupní sloupce v {path} mají prázdné nebo nečíselné hodnoty")

    reference = {}
    for name in TARGETS:
        if name in table.columns:
            column = table[name].astype(float) if table[name].dtype == bool else table[name]
            reference[name] = pd.to_numeric(column, errors="coerce").to_numpy(np.float64)
    relative_time = table["time"].to_numpy(np.float64) if "time" in table.columns else np.full(len(table), np.nan)
    return inputs, reference, table["discharge"].to_numpy(), relative_time


def select_discharges(discharges, which):
    """Vybere řádky sady `which` (locked / dev / all). Vrací (maska řádků, popis sady)."""
    if which == "all":
        return np.ones(len(discharges), bool), "všechny výboje souboru"
    if not LOCKED_IDS_FILE.exists():
        fail(f"seznam odložených výbojů chybí: {LOCKED_IDS_FILE}")
    ids_line = next((line for line in LOCKED_IDS_FILE.read_text().splitlines() if line.startswith("locked discharge ids")), None)
    if ids_line is None:
        fail(f"v {LOCKED_IDS_FILE} chybí řádek 'locked discharge ids'")
    locked_ids = np.array([int(value) for value in ids_line.split(":", 1)[1].split()])
    is_locked = np.isin(discharges, locked_ids)
    if which == "locked":
        return is_locked, f"odložené výboje ({len(locked_ids)} v {LOCKED_IDS_FILE.relative_to(REPO)})"
    return ~is_locked, "vývojové výboje (všechny kromě odložených)"


# ===================================================================================================================
# Statistiky
# ===================================================================================================================
def describe(absolute_deviations):
    """Základní statistiky absolutních odchylek jedné veličiny (v mm nebo kA)."""
    stats = {"n": len(absolute_deviations), "mae": float(absolute_deviations.mean()),
             "median": float(np.median(absolute_deviations)), "rmse": float(np.sqrt((absolute_deviations ** 2).mean()))}
    stats.update({f"p{p:g}": float(np.percentile(absolute_deviations, p)) for p in PERCENTILES})
    stats["max"] = float(absolute_deviations.max())
    return stats


def bootstrap_draws(n_discharges):
    """Kolikrát se každý výboj dostal do každého z N_BOOTSTRAP vzorků. Stejný generátor a pořadí tahů jako
    final_evaluation.bootstrap, takže na téže sadě sedí intervaly středních chyb s results/final-evaluation.md."""
    rng = np.random.RandomState(BOOTSTRAP_SEED)
    draws = [np.bincount(rng.randint(0, n_discharges, n_discharges), minlength=n_discharges) for _ in range(N_BOOTSTRAP)]
    return np.stack(draws).astype(np.float64)


def interval_95(sums, counts, draws):
    """95% percentilový interval podílu součtu a počtu přes bootstrapové vzorky (součty a počty jsou po výbojích)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        values = (draws @ sums) / (draws @ counts)
    return [float(np.nanpercentile(values, 2.5)), float(np.nanpercentile(values, 97.5))]


def quantity_statistics(absolute_deviations, discharge_index, draws, in_millimetres=True):
    """Statistiky jedné veličiny. discharge_index je pořadí výboje (0..D-1) u každého řádku."""
    stats = describe(absolute_deviations)
    stats["n_discharges"] = len(np.unique(discharge_index))
    n_discharges = draws.shape[1]
    rows_per_discharge = np.bincount(discharge_index, minlength=n_discharges).astype(np.float64)
    stats["mae_ci95"] = interval_95(np.bincount(discharge_index, weights=absolute_deviations, minlength=n_discharges),
                                    rows_per_discharge, draws)
    if in_millimetres:
        stats["share_below_mm"] = {f"{threshold:g}": float((absolute_deviations < threshold).mean()) for threshold in THRESHOLDS_MM}
        below_1mm = (absolute_deviations < 1.0).astype(float)
        stats["share_below_1mm_ci95"] = interval_95(np.bincount(discharge_index, weights=below_1mm, minlength=n_discharges),
                                                    rows_per_discharge, draws)
    return stats


def evaluate(model, inputs, reference, discharges, relative_time):
    """Spočítá všechny statistiky modelu na zadaných řádcích. Vrací slovník, který se pak vypíše i uloží do JSON."""
    estimates = model.estimates(inputs)  # v mm, kA a bez jednotky
    column = {name: j for j, name in enumerate(model.outputs)}
    scale = dict(zip(model.outputs, model.scales))
    discharge_ids, discharge_index = np.unique(discharges, return_inverse=True)
    draws = bootstrap_draws(len(discharge_ids))

    result = {"quantities": {}, "absent": []}
    deviation = {}  # odchylka se znaménkem v jednotkách tabulek, NaN tam, kde chybí reference
    for name in list(POSITIONS) + ["plasma_current"]:
        if name not in reference:
            result["absent"].append(name)
            continue
        deviation[name] = estimates[:, column[name]] - reference[name] * scale[name]
        has_reference = np.isfinite(deviation[name])
        if has_reference.any():
            result["quantities"][name] = quantity_statistics(
                np.abs(deviation[name][has_reference]), discharge_index[has_reference], draws, in_millimetres=name != "plasma_current")

    if "R_mag_axis" in deviation and "Z_mag_axis" in deviation:
        axis_distance = np.hypot(deviation["R_mag_axis"], deviation["Z_mag_axis"])  # vzdálenost odhadnuté a skutečné osy v rovině
        has_reference = np.isfinite(axis_distance)
        if has_reference.any():
            result["axis_2d"] = quantity_statistics(axis_distance[has_reference], discharge_index[has_reference], draws)

    if "is_limited" in reference:
        has_reference = np.isfinite(reference["is_limited"])
        reference_limited = reference["is_limited"][has_reference] > 0.5
        predicted_limited = estimates[has_reference, column["is_limited"]] > 0.5
        agreement = float((reference_limited == predicted_limited).mean()) if has_reference.any() else float("nan")
        result["limited_diverted"] = {
            "n": int(has_reference.sum()), "agreement": agreement,
            "ref_limited_pred_limited": int((reference_limited & predicted_limited).sum()),
            "ref_limited_pred_diverted": int((reference_limited & ~predicted_limited).sum()),
            "ref_diverted_pred_limited": int((~reference_limited & predicted_limited).sum()),
            "ref_diverted_pred_diverted": int((~reference_limited & ~predicted_limited).sum()),
            "discharges_with_disagreement": len(np.unique(discharges[has_reference][reference_limited != predicted_limited])),
        }

    # Nejhorší řádky: každý řádek se počítá jednou, podle své největší odchylky polohy.
    position_names = [name for name in POSITIONS if name in deviation]
    absolute = np.abs(np.column_stack([deviation[name] for name in position_names]))
    finite = np.isfinite(absolute)
    worst_deviation = np.where(finite.any(1), np.nanmax(np.where(finite, absolute, -1.0), 1), np.nan)
    ranking = np.argsort(-np.nan_to_num(worst_deviation, nan=-1.0))
    worst_rows_order = [i for i in ranking if np.isfinite(worst_deviation[i])][:10]
    if "R_mag_axis" in deviation and "Z_mag_axis" in deviation:
        axis_2d_deviation = np.hypot(deviation["R_mag_axis"], deviation["Z_mag_axis"])
    else:
        axis_2d_deviation = np.full(len(discharges), np.nan)
    result["worst_rows"] = []
    for i in worst_rows_order:
        worst_quantity = position_names[int(np.nanargmax(np.where(np.isfinite(absolute[i]), absolute[i], -1.0)))]
        result["worst_rows"].append({
            "discharge": discharges[i].item() if hasattr(discharges[i], "item") else discharges[i],
            "relative_time": None if np.isnan(relative_time[i]) else float(relative_time[i]),
            "quantity": worst_quantity,
            "deviation_mm": float(worst_deviation[i]),
            "axis_2d_mm": None if np.isnan(axis_2d_deviation[i]) else float(axis_2d_deviation[i]),
        })
    return result


# ===================================================================================================================
# Výpis do terminálu
# ===================================================================================================================
def format_number(value):
    """Číslo na tři platné číslice (u velkých na celé číslo), nebo pomlčka, když chybí."""
    if value is None or not np.isfinite(value):
        return "–"
    return f"{value:.0f}" if abs(value) >= 1000 else f"{value:.3g}"


def render(result, header_lines):
    """Složí celý výpis (česky) z výsledků evaluate. header_lines jsou dvojice (štítek, text)."""
    width = 100
    out = ["Odchylka od rekonstrukce ústavu (absolutní hodnota |model − rekonstrukce|)", "=" * width]
    for label, text in header_lines:
        out += textwrap.wrap(text, width, initial_indent=f"{label:<8}", subsequent_indent=" " * 8, break_on_hyphens=False)

    rows = [(POSITIONS[name], result["quantities"][name]) for name in POSITIONS if name in result["quantities"]]
    if "axis_2d" in result:
        rows.insert(2, (AXIS_2D_NAME, result["axis_2d"]))  # hned za osu R a Z
    current = result["quantities"].get("plasma_current")
    rows_with_current = rows + ([(CURRENT_NAME, current)] if current else [])

    out += ["", "Rozdělení odchylky v mm (proud plazmatu v kA), na řádcích, kde rekonstrukce veličinu má", "-" * width,
            f"{'veličina':<19}{'řádků':>7}{'výb.':>5}"
            + "".join(f"{heading:>8}" for heading in ("MAE", "medián", "RMSE", "p90", "p95", "p99", "p99.9", "max"))]
    for name, stats in rows_with_current:
        out.append(f"{name:<19}{stats['n']:>7}{stats['n_discharges']:>5}"
                   + "".join(f"{format_number(stats[key]):>8}" for key in ("mae", "median", "rmse", "p90", "p95", "p99", "p99.9", "max")))

    out += ["", f"Podíl řádků s odchylkou pod prahem (%) a 95% interval (bootstrap po výbojích, {N_BOOTSTRAP}×)", "-" * width,
            f"{'veličina':<19}" + "".join(f"{'<' + format(threshold, 'g'):>7}" for threshold in THRESHOLDS_MM)
            + f"  {'MAE [95% interval]':<21} {'pod 1 mm % [95% int.]'}"]
    for name, stats in rows_with_current:
        if "share_below_mm" in stats:
            shares = "".join(f"{100 * stats['share_below_mm'][format(threshold, 'g')]:>7.2f}" for threshold in THRESHOLDS_MM)
            low, high = stats["share_below_1mm_ci95"]
            below_1mm = f"{100 * stats['share_below_mm']['1']:.2f} [{100 * low:.2f}, {100 * high:.2f}]"
        else:
            shares, below_1mm = "".join(f"{'–':>7}" for _ in THRESHOLDS_MM), "–"
        mae = f"{format_number(stats['mae'])} [{format_number(stats['mae_ci95'][0])}, {format_number(stats['mae_ci95'][1])}]"
        out.append(f"{name:<19}{shares}  {mae:<21} {below_1mm}")

    if result["absent"]:
        names = ", ".join(POSITIONS.get(name, CURRENT_NAME) for name in result["absent"])
        out += [""] + textwrap.wrap("Ve vstupu chybí, nehodnoceno: " + names, width)

    confusion = result.get("limited_diverted")
    if confusion:
        out += ["", "Konfigurace limitovaná / divertorová (model: is_limited > 0.5)", "-" * width,
                f"shoda s rekonstrukcí {100 * confusion['agreement']:.2f} % z {confusion['n']} řádků; "
                f"výbojů s aspoň jedním rozdílem: {confusion['discharges_with_disagreement']}",
                f"{'':<26}{'model limitovaná':>18}{'model divertorová':>19}",
                f"{'rekonstrukce limitovaná':<26}{confusion['ref_limited_pred_limited']:>18}{confusion['ref_limited_pred_diverted']:>19}",
                f"{'rekonstrukce divertorová':<26}{confusion['ref_diverted_pred_limited']:>18}{confusion['ref_diverted_pred_diverted']:>19}"]

    out += ["", "10 řádků s největší odchylkou (řádek jednou, podle jeho největší odchylky polohy)", "-" * width,
            f"{'#':>3}  {'výboj':>8}  {'rel. čas':>8}  {'veličina':<19}{'odchylka mm':>12}{'osa 2D mm':>11}"]
    for rank, worst in enumerate(result["worst_rows"], 1):
        time_text = "–" if worst["relative_time"] is None else f"{worst['relative_time']:.3f}"
        out.append(f"{rank:>3}  {worst['discharge']!s:>8}  {time_text:>8}  {POSITIONS[worst['quantity']]:<19}"
                   f"{format_number(worst['deviation_mm']):>12}{format_number(worst['axis_2d_mm']):>11}")
    out += ["", "Čísla jsou shoda s rekonstrukcí ústavu, ne odchylka od plazmatu samotného."]
    return "\n".join(line.rstrip() for line in out)


# ===================================================================================================================
# Spuštění
# ===================================================================================================================
def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", help="exportovaný model .npz (výchozí: out/model/clean-model.npz v $HACKATHON_HOME nebo v repozitáři)")
    parser.add_argument("--set", choices=("locked", "dev", "all"),
                        help="které výboje (výchozí: locked pro data ústavu, all pro --csv)")
    parser.add_argument("--noisy", action="store_true", help="zašuměný soubor equil_data_noisy místo equil_data")
    parser.add_argument("--csv", help="libovolné CSV s 24 vstupy, `discharge`, volitelně `time`, a cílovými sloupci")
    parser.add_argument("--json", help="uloží všechna čísla i do tohoto souboru JSON")
    args = parser.parse_args()

    if args.csv and args.noisy:
        fail("--noisy platí jen pro data ústavu; zašuměný soubor předejte přímo přes --csv")
    model_path = Path(args.model) if args.model else default_model()
    if not model_path.exists():
        fail(f"model nenalezen: {model_path} (vytvoří ho analysis/clean_model.py nebo run.py; jiný předejte přes --model)")
    try:
        model = Model(model_path)
    except Exception as error:  # špatný nebo useknutý soubor
        fail(f"model {model_path} nelze načíst: {error}")
    if model.inputs != INPUTS or model.outputs != TARGETS:
        fail(f"model {model_path} nemá očekávané vstupy a výstupy (24 vstupů IPR01..FL08, 16 výstupů v pořadí clean_model.py)")
    description_path = model_path.with_suffix(".json")
    description = json.loads(description_path.read_text()) if description_path.exists() else {}

    path = Path(args.csv) if args.csv else ipp_file(args.noisy)
    if not path.exists():
        fail(f"soubor nenalezen: {path}")
    which = args.set or ("all" if args.csv else "locked")
    inputs, reference, discharges, relative_time = read_table(path, model.inputs)
    rows, set_text = select_discharges(discharges, which)
    if not rows.any():
        fail(f"sada '{which}' nemá v {path} žádný řádek")
    inputs, discharges, relative_time = inputs[rows], discharges[rows], relative_time[rows]
    reference = {name: values[rows] for name, values in reference.items()}

    result = evaluate(model, inputs, reference, discharges, relative_time)

    kind = "vlastní CSV" if args.csv else ("zašuměné vstupy" if args.noisy else "čisté vstupy")
    header_lines = [
        ("model", f"{model_path}" + (f" ({description['trained_on']})" if "trained_on" in description else "")),
        ("data", f"{path} ({kind})"),
        ("sada", f"{which}: {set_text}; {len(np.unique(discharges))} výbojů, {len(discharges)} řádků"),
    ]
    print(render(result, header_lines))

    if args.json:
        result["protocol"] = {
            "model": str(model_path), "model_trained_on": description.get("trained_on"), "data": str(path), "data_kind": kind,
            "set": which, "n_discharges": len(np.unique(discharges)), "n_rows": len(discharges),
            "bootstrap": {"resamples": N_BOOTSTRAP, "unit": "discharge", "seed": BOOTSTRAP_SEED, "interval": "95 % percentile"},
            "units": "positions mm, plasma current kA; deviations are model minus the institute's reconstruction",
        }
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
        print(f"\nJSON: {args.json}")


if __name__ == "__main__":
    main()
