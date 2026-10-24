#!/usr/bin/env python
"""Odhad tvaru plazmatu z 24 magnetických měření nasazeným modelem. Jen numpy: žádný torch, scikit-learn ani pandas.

    python predict.py vstup.csv [--model out/model/ipp1-ipn.npz] [--out odhady.csv] [--all]
    python predict.py vstup.csv --noisy [--out odhady.csv] [--all]     zašuměná měření: model ipp1-noisy.npz

Vstup: CSV se záhlavím a jedním řádkem na časový okamžik, se sloupci IPR01..IPR16 (cívky) a FL01..FL08 (smyčky)
v libovolném pořadí a v jednotkách datového souboru. Další sloupce (např. `discharge` a `time`) se předají do výstupu.

Výchozí model (čistá měření) počítá každý řádek zvlášť, na pořadí řádků tedy nezáleží. Rozdíly, které používá,
jsou rozdíly SOUSEDNÍCH CÍVEK uvnitř jednoho řádku (IPR02-IPR01 ... FL08-FL07), ne rozdíly mezi časy.

--noisy použije druhý model, učený na čistých řádcích plus kopii s přidaným šumem a driftem (analysis/noisy_model.py,
results/ipp1-noise-window.md). Ten NEPOČÍTÁ po řádcích: každý odhad vidí měření z posledních 5 okamžiků téhož výboje
(řádky t, t-1 ... t-4 podle `time`; u prvních řádků výboje se opakuje první řádek; nikdy se nepoužije pozdější řádek).
Soubor proto musí mít sloupce `discharge` a `time`. Řádky smějí přijít v libovolném pořadí, výstup zachová pořadí vstupu.
Okno počítá řádky, takže soubor musí mít stejný krok vzorkování jako trénovací data.

Výstup, jeden řádek na řádek vstupu: 16 odhadnutých hodnot v mm a kA (tvarová čísla a pravděpodobnost limiterové
konfigurace bez jednotky) a `is_limited_flag` (1 = limiterové plazma). Bod X a dotykové body existují jen v divertorové
konfiguraci a bod limiteru jen v limiterové, proto se buňky, které se na daný řádek nevztahují, nechávají prázdné;
s `--all` se vypíše všech 16 čísel u každého řádku. Hodnoty jsou odhady rekonstrukce ústavu (`results/ipp1-final.md`),
ne měření plazmatu.

Na konci se vypíše doba na jeden řádek: pro celý soubor najednou a po jednom řádku (medián, jedno jádro procesoru).
"""
import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent


def find_model_file(name):
    """Najde soubor modelu: v balíčku pro organizátory je v model/, po `python run.py` v out/model/,
    v repozitáři vedle složky repozitáře. Když nikde není, vrátí cestu v model/ (a pozdější chyba řekne, co chybí)."""
    candidates = (REPO_ROOT / "model" / name, REPO_ROOT / "out" / "model" / name, REPO_ROOT.parent / "out" / "model" / name)
    return next((path for path in candidates if path.exists()), REPO_ROOT / "model" / name)


DEFAULT_MODEL = find_model_file("ipp1-ipn.npz")
DEFAULT_NOISY = find_model_file("ipp1-noisy.npz")

# Veličiny, které existují jen v jedné konfiguraci: v druhé se v souboru s odhady nechávají prázdné.
DIVERTOR_ONLY = ("R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2")
LIMITED_ONLY = ("R_limiter", "Z_limiter")

MIN_CURRENT = 1e4  # pod 10 kA už model nikdy neviděl data: dělení proudem tam nemá smysl a odhady nejsou spolehlivé


def silu(values):
    """Aktivační funkce SiLU: x / (1 + exp(-x))."""
    with np.errstate(over="ignore"):  # exp(-x) může pro velké záporné x přetéct na inf; 1/inf je 0, což je správná limita
        return values * (1.0 / (1.0 + np.exp(-values)))


def window_rows(discharge, time, size):
    """Pro každý řádek čísla řádků jeho okna: matice (počet řádků, size).

    Sloupec j je řádek, který je v témž výboji o j okamžiků dřív podle `time` (u začátku výboje se opakuje první řádek),
    nikdy ne pozdější. Řádky smějí přijít v libovolném pořadí. Stejnou funkci používá i učení zašuměného modelu.
    """
    _, discharge_index = np.unique(np.asarray(discharge), return_inverse=True)
    n_rows = len(discharge_index)
    # Řádky seřazené podle výboje a uvnitř výboje podle času.
    order = np.lexsort((np.asarray(time, dtype=np.float64), discharge_index))
    sorted_discharge = discharge_index[order]
    first_of_discharge = np.r_[0, np.flatnonzero(sorted_discharge[1:] != sorted_discharge[:-1]) + 1]
    first_of_each_row = np.repeat(first_of_discharge, np.diff(np.r_[first_of_discharge, n_rows]))
    position_in_discharge = np.arange(n_rows) - first_of_each_row
    window_in_sorted_order = np.stack(
        [order[first_of_each_row + np.maximum(position_in_discharge - back, 0)] for back in range(size)], 1)
    window = np.empty_like(window_in_sorted_order)
    window[order] = window_in_sorted_order  # zpátky do původního pořadí řádků
    return window


class Model:
    """Natrénovaný model načtený ze souboru .npz.

    Buď model čistých měření (ipp1-ipn.npz, vyrábí ho analysis/clean_model.py): obecná síť, síť pro bod limiteru a ridge
    pro proud plazmatem; řádky jsou nezávislé. Nebo zašuměný model (ipp1-noisy.npz, vyrábí ho analysis/noisy_model.py):
    jedna síť, která vidí měření z posledních `window` řádků výboje, viz estimates_noisy.
    """

    def __init__(self, path):
        stored = np.load(path, allow_pickle=False)
        self.arrays = {name: stored[name] for name in stored.files}
        self.inputs = [str(name) for name in self.arrays["input_names"]]
        self.outputs = [str(name) for name in self.arrays["output_names"]]
        self.scales = self.arrays["output_scales"]  # násobky, které převedou výstupy na mm a kA
        self.limiter_columns = [int(column) for column in self.arrays["limiter_columns"]]
        self.current_column = int(self.arrays["plasma_current_column"])
        self.is_limited_column = int(self.arrays["is_limited_column"])
        self.window = int(self.arrays["window_rows"]) if "window_rows" in self.arrays else 1  # okno má jen zašuměný model
        self.depth = {tag: sum(name.startswith(f"{tag}_W") for name in self.arrays) for tag in ("gen", "spec")}
        self.divides_by_current = "ipn" in self.arrays  # model z clean_model.py: měření dělená proudem plazmatem
        self.feature_mode = str(self.arrays["feature_mode"]) if self.divides_by_current else None
        if not self.divides_by_current and self.window == 1:
            sys.exit(f"{path}: not a model of this package (the clean-input model is ipp1-ipn.npz, "
                     "the noise model ipp1-noisy.npz; make them with python run.py)")

    def plasma_current(self, measurements):
        """Proud plazmatem odhadnutý ridge regresí ze 24 měření (v ampérech, se znaménkem)."""
        return measurements.astype(np.float64) @ self.arrays["ridge_w"] + float(self.arrays["ridge_b"])

    def build_features(self, measurements):
        """Vstup sítí modelu čistých měření: měření vydělená odhadem proudu (se znaménkem), jejich rozdíly uvnitř řádku
        (u diff2 i druhé diference) a samotný proud / ip_scale. Stejně je skládá analysis/clean_model.build_features."""
        scale = float(self.arrays["ip_scale"])
        current = self.plasma_current(measurements)
        too_small = np.abs(current) < MIN_CURRENT
        if too_small.any() and not getattr(self, "_warned", False):
            self._warned = True
            print(f"warning: {int(too_small.sum())} rows with an estimated plasma current under 10 kA, outside the training range; "
                  "their estimates are not reliable", file=sys.stderr)
        divided = measurements * (scale / current)[:, None]
        parts = [divided, np.diff(divided[:, :16], axis=1), np.diff(divided[:, 16:24], axis=1)]
        if self.feature_mode == "diff2":
            parts += [np.diff(divided[:, :16], 2, axis=1), np.diff(divided[:, 16:24], 2, axis=1)]
        return np.concatenate(parts + [(current / scale)[:, None]], axis=1).astype(np.float32)

    def run_network(self, tag, features):
        """Spočítá jednu uloženou síť ("gen" = obecná, "spec" = limiterová): standardizace, vrstvy se SiLU, zpět do jednotek dat."""
        arrays = self.arrays
        activations = (features - arrays[f"{tag}_mu"]) / arrays[f"{tag}_sd"]
        n_layers = self.depth[tag]
        for i in range(n_layers):
            activations = activations @ arrays[f"{tag}_W{i}"] + arrays[f"{tag}_b{i}"]
            if i < n_layers - 1:  # za poslední vrstvou se aktivace nepoužívá
                activations = silu(activations)
        return activations * arrays[f"{tag}_ys"] + arrays[f"{tag}_ym"]

    def predict(self, measurements):
        """(n, 24) surových měření -> (n, 16) výstupů v jednotkách dat (m, A, bez jednotky) v pořadí `self.outputs`.

        U zašuměného modelu je vstup (n, 24 * window): naskládané řádky t, t-1, ... (viz estimates_noisy).
        """
        measurements = np.asarray(measurements, dtype=np.float32)
        if self.window > 1:
            return self.run_network("gen", measurements)

        features = self.build_features(measurements)
        output = self.run_network("gen", features)
        output[:, self.current_column] = self.plasma_current(measurements)  # proud je přímo ridge, ne síť

        # Bod limiteru: jen u řádků, které obecná síť označila za limiterové (is_limited > 0,5).
        limited = np.flatnonzero(output[:, self.is_limited_column] > 0.5)
        if len(limited):
            # Limiterová síť odpoví: strana (+ nahoře, - dole), pak R a Z pro stranu nahoře a R a Z pro stranu dole.
            specialist = self.run_network("spec", features[limited])
            answer_for_chosen_side = np.where((specialist[:, 0] > 0)[:, None], specialist[:, 1:3], specialist[:, 3:5])
            general_answer = output[np.ix_(limited, self.limiter_columns)]
            output[np.ix_(limited, self.limiter_columns)] = 0.5 * (answer_for_chosen_side + general_answer)
        return output

    def estimates(self, measurements):
        """Totéž co predict, ale v jednotkách pro lidi (mm, kA, bez jednotky)."""
        return self.predict(measurements) * self.scales

    def stack(self, measurements, discharge, time):
        """(n, 24) řádků celých výbojů (v libovolném pořadí) -> (n, 24 * window): vstupy každého řádku následují vstupy řádků před ním."""
        measurements = np.asarray(measurements, dtype=np.float32)
        return measurements[window_rows(discharge, time, self.window)].reshape(len(measurements), -1)

    def estimates_noisy(self, measurements, discharge, time):
        """Zašuměný model na (n, 24) řádcích s číslem výboje a časem; v jednotkách pro lidi, pořadí řádků jako ve vstupu."""
        return self.estimates(self.stack(measurements, discharge, time))


def read_csv(path, input_names):
    """Přečte vstupní CSV. Při chybě skončí jedním řádkem, který pojmenuje řádek tak, jak ho číslují tabulkové
    procesory (záhlaví je řádek 1), s kódem 1. Vrací (matice měření, [(název sloupce, hodnoty)] pro discharge a time)."""
    with open(path, newline="", encoding="utf-8-sig") as file:  # utf-8-sig: "CSV UTF-8" z Excelu začíná znakem BOM
        reader = csv.reader(file)
        header = next(reader, None)
        rows = [(reader.line_num, row) for row in reader if any(value.strip() for value in row)]
    if header is None:
        sys.exit(f"{path}: empty file")
    header = [name.strip() for name in header]
    missing = [name for name in input_names if name not in header]
    if missing:
        sys.exit(f"missing columns in {path}: {', '.join(missing)}")
    if not rows:
        sys.exit(f"{path}: no data rows after the header")

    column_of_input = [header.index(name) for name in input_names]
    measurements = np.empty((len(rows), len(column_of_input)))
    for i, (line_number, row) in enumerate(rows):
        if len(row) < len(header):
            sys.exit(f"{path}: row {line_number}: {len(row)} values, the header has {len(header)} columns")
        for j, column in enumerate(column_of_input):
            try:
                measurements[i, j] = float(row[column])
            except ValueError:
                measurements[i, j] = np.nan
            if not np.isfinite(measurements[i, j]):
                sys.exit(f"{path}: row {line_number}: column {input_names[j]} is empty or not a number ({row[column]!r})")
    extra_columns = [(name, [row[header.index(name)] for _, row in rows]) for name in ("discharge", "time") if name in header]
    return measurements, extra_columns


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="CSV with the columns IPR01..IPR16 and FL01..FL08")
    parser.add_argument("--model", default=None, help="the exported model (default: ipp1-ipn.npz in model/ or out/model/ next to this file; "
                                                      "with --noisy ipp1-noisy.npz in the same places)")
    parser.add_argument("--noisy", action="store_true", help="noisy measurements: the noise-trained model on the last 5 instants of each "
                                                             "discharge (needs the columns discharge and time)")
    parser.add_argument("--out", help="write the estimates to this CSV instead of printing the first rows")
    parser.add_argument("--all", action="store_true", help="write all 16 numbers for every row "
                                                           "(default: leave the cells that do not apply to the configuration empty)")
    return parser.parse_args()


def discharge_and_time_columns(extra_columns, model, input_path):
    """Pro --noisy: vrátí (čísla výbojů, časy). Skončí chybou, když sloupce chybí nebo čas není číslo."""
    columns = dict(extra_columns)
    missing = [name for name in ("discharge", "time") if name not in columns]
    if missing:
        sys.exit(f"--noisy needs the columns discharge and time (each estimate uses the last {model.window} instants of the same discharge); "
                 f"missing in {input_path}: {', '.join(missing)}")
    try:
        times = np.array([float(value) for value in columns["time"]])
    except ValueError:
        times = np.array([np.nan])
    if not np.isfinite(times).all():
        sys.exit(f"{input_path}: column time must be a number in every row")
    return columns["discharge"], times


def column_names_with_units(model):
    """Názvy sloupců výstupu: u poloh s příponou _mm, u proudu _kA, ostatní beze změny."""
    names = []
    for name in model.outputs:
        if name.startswith(("R_", "Z_")):
            names.append(f"{name}_mm")
        elif name == "plasma_current":
            names.append(f"{name}_kA")
        else:
            names.append(name)
    return names


def main():
    args = parse_arguments()
    args.model = args.model or str(DEFAULT_NOISY if args.noisy else DEFAULT_MODEL)
    if not Path(args.model).exists():
        sys.exit(f"model not found: {args.model} (make it with analysis/noisy_model.py)")
    if not Path(args.input).is_file():
        sys.exit(f"input file not found: {args.input}")

    model = Model(args.model)
    print(f"model: {args.model}", file=sys.stderr)  # který soubor se načetl
    if args.noisy != (model.window > 1):
        sys.exit(f"{args.model} is {'not ' if args.noisy else ''}the noise model: "
                 + ("use ipp1-noisy.npz with --noisy" if args.noisy else "run it with --noisy"))
    measurements, extra_columns = read_csv(args.input, model.inputs)

    # Vstup, který model opravdu dostane: u zašuměného modelu okna z posledních řádků výboje.
    model_input = measurements
    if args.noisy:
        discharges, times = discharge_and_time_columns(extra_columns, model, args.input)
        model_input = model.stack(measurements, discharges, times)

    started = time.perf_counter()
    estimates = model.estimates_noisy(measurements, discharges, times) if args.noisy else model.estimates(measurements)
    whole_file_seconds = time.perf_counter() - started

    single_row_seconds = []
    for i in range(min(len(model_input), 500)):
        started = time.perf_counter()
        model.estimates(model_input[i:i + 1])
        single_row_seconds.append(time.perf_counter() - started)

    # Sestavení výstupních řádků: předané sloupce, 16 odhadů (prázdné tam, kde se nevztahují ke konfiguraci) a příznak.
    is_limited_flag = (estimates[:, model.is_limited_column] > 0.5).astype(int)
    header = [name for name, _ in extra_columns] + column_names_with_units(model) + ["is_limited_flag"]
    output_rows = []
    for r in range(len(measurements)):
        row = [values[r] for _, values in extra_columns]
        for j, output_name in enumerate(model.outputs):
            not_in_this_configuration = ((is_limited_flag[r] and output_name in DIVERTOR_ONLY)
                                         or (not is_limited_flag[r] and output_name in LIMITED_ONLY))
            row.append("" if (not args.all and not_in_this_configuration) else f"{estimates[r, j]:.8g}")
        output_rows.append(row + [str(is_limited_flag[r])])

    if args.out:
        with open(args.out, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(output_rows)
        print(f"wrote {len(output_rows)} rows to {args.out}")
    else:
        print(",".join(header))
        for row in output_rows[:10]:
            print(",".join(row))
        if len(output_rows) > 10:
            print(f"... ({len(output_rows) - 10} more rows; use --out to write them all)")

    noisy_note = "; noise model: the network on one row of 5 stacked instants" if args.noisy else ""
    print(f"time per row: {1e6 * whole_file_seconds / len(measurements):.1f} us for the whole file at once, "
          f"{1e6 * float(np.median(single_row_seconds)):.1f} us as the median of single-row calls (one CPU core, numpy only{noisy_note})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
