#!/usr/bin/env python
"""Jeden soubor, který spustí celý projekt: python run.py

    python run.py            živé učení, test na neviděných výbojích, export modelů, první odhad, zašuměná měření (asi 3 minuty)
    python run.py --full     všechno: všechny analýzy a všech deset notebooků (asi 10 minut)
    python run.py --check    jen zkontroluje balíčky a data

Data od ÚFP jsou důvěrná: repozitář je soukromý a smějí k němu mít přístup jen účastníci hackathonu. Soubory jsou ve složce
data/; jiná složka se dá zadat proměnnou HACKATHON_HOME (musí mít data/ se dvěma datovými soubory). Živé demo vypisuje do terminálu řádky
dat: ukazujte ho v místnosti, ale nenahrávejte ho a nepřeposílejte.
"""
import argparse
import importlib
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Kde jsou data: složka data/ (lokální soubory od organizátorů, v gitu nejsou), nebo původní struktura z archivu.
FLAT_DATA = Path("data")
NESTED_DATA = Path("data/raw/ipp1-magnetic/uloha_1-magneticka_data")
CLEAN_NAME, NOISY_NAME = "equil_data", "equil_data_noisy"   # soubory .zip nebo .csv (původní z archivu)

# Barvy ve výpisu terminálu.
BOLD, GREEN, RED, DIM, RESET = "\033[1m", "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def data_file(folder, name):
    """Soubor `name`.zip, nebo `name`.csv ve složce (pandas čte CSV rovnou ze zipu); None, když není ani jeden."""
    return next((folder / f"{name}{suffix}" for suffix in (".zip", ".csv") if (folder / f"{name}{suffix}").exists()), None)


def data_folder(home):
    """Složka pod `home`, která má obě datové soubory (data/ nebo původní vnořená struktura), nebo None."""
    for folder in (FLAT_DATA, NESTED_DATA):
        if all(data_file(home / folder, name) for name in (CLEAN_NAME, NOISY_NAME)):
            return home / folder
    return None


def print_step(title):
    print(f"\n{BOLD}=== {title} ==={RESET}", flush=True)


def check_packages():
    print_step("1. Python packages")
    if sys.version_info < (3, 10):
        sys.exit(f"{RED}Python 3.10 or newer is needed (3.12 recommended), this is {sys.version.split()[0]}{RESET}")
    # (název při importu, název při instalaci pomocí pip)
    required = [("numpy", "numpy"), ("pandas", "pandas"), ("sklearn", "scikit-learn"), ("scipy", "scipy"), ("torch", "torch"),
                ("matplotlib", "matplotlib"), ("nbformat", "nbformat"), ("nbconvert", "nbconvert"), ("ipykernel", "ipykernel")]
    missing = []
    for import_name, pip_name in required:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)
    if missing:
        sys.exit(f"{RED}Missing packages: {', '.join(missing)}{RESET}\n"
                 f"Install all with:  {sys.executable} -m pip install -r requirements.txt")
    print(f"{GREEN}all packages found{RESET} (Python {sys.version.split()[0]})")


def find_home():
    """Najde domovskou složku s daty: HACKATHON_HOME, jinak složka tohoto souboru."""
    print_step("2. Data")
    for candidate in [os.environ.get("HACKATHON_HOME"), str(HERE)]:
        if not candidate:
            continue
        # Podprocesy běží s cwd=HERE, relativní cesta by tedy mířila jinam. Proto absolutní.
        home = Path(candidate).expanduser().resolve()
        folder = data_folder(home)
        if folder:
            print(f"{GREEN}data found{RESET} in {folder}")
            return home
        if any(data_file(home / where, name) for where in (FLAT_DATA, NESTED_DATA) for name in (CLEAN_NAME, NOISY_NAME)):
            sys.exit(f"{RED}Only one of the two data files is there{RESET} in {home / FLAT_DATA}: "
                     f"both {CLEAN_NAME} and {NOISY_NAME} (.zip or .csv) are needed.")
    sys.exit(f"{RED}The data were not found.{RESET}\n"
             f"They belong in {HERE / FLAT_DATA} ({CLEAN_NAME}.zip and {NOISY_NAME}.zip or the .csv files; the data are confidential and not in git)\n"
             "or set HACKATHON_HOME to a folder that holds data/ with these two files.")


def run_command(command, env, show_command=False):
    """Spustí podproces ve složce repozitáře; když selže, skončí celý run.py."""
    if show_command:
        print(f"{DIM}$ {' '.join(str(part) for part in command)}{RESET}", flush=True)
    started = time.time()
    return_code = subprocess.run(command, cwd=HERE, env=env).returncode
    if return_code:
        sys.exit(f"{RED}Step failed (exit code {return_code}).{RESET}")
    print(f"{DIM}done in {time.time() - started:.0f} s{RESET}", flush=True)


def locked_discharge_ids():
    """Čísla 30 odložených výbojů, přečtená ze souboru, který je zapisuje (nezávisle na kódu učení)."""
    lines = (HERE / "results" / "locked-test-ids.txt").read_text().splitlines()
    ids_line = next(line for line in lines if line.startswith("locked discharge ids"))
    ids = [int(value) for value in ids_line.split(":", 1)[1].split()]
    assert len(ids) == 30, len(ids)
    return ids


def first_estimate(home, model_path):
    """Krok 5: odhad prvních 5 řádků jednoho vývojového výboje exportovaným modelem vedle rekonstrukce ústavu."""
    import numpy as np
    import pandas as pd
    sys.path.insert(0, str(HERE))
    import predict

    started = time.time()
    table = pd.read_csv(data_file(data_folder(home), CLEAN_NAME))
    model = predict.Model(model_path)
    development = table[~np.isin(table["discharge"].values, locked_discharge_ids())]
    discharge = development["discharge"].iloc[0]
    rows = development[development["discharge"] == discharge]

    estimates = model.estimates(rows[model.inputs].values[:5])
    print("outputs:", len(model.outputs))
    reference_mm = rows["R_mag_axis"].values[:5] * 1000
    print(f"first 5 rows of development discharge {discharge} "
          "(the exported model was trained on it, so this only checks the export):")
    axis_column = model.outputs.index("R_mag_axis")
    for i in range(5):
        print(f"  row {i}: reference R axis {reference_mm[i]:.2f} mm, estimate {estimates[i, axis_column]:.2f} mm")
    print(f"{DIM}done in {time.time() - started:.0f} s{RESET}", flush=True)


def compare_models_on_noisy_inputs(home):
    """Krok 6: průměrná chyba osy obou exportovaných modelů na zadaném zašuměném souboru, na 30 odložených výbojích.
    Vypisuje jen souhrny, žádné řádky dat."""
    import numpy as np
    import pandas as pd
    sys.path.insert(0, str(HERE))
    import predict

    table = pd.read_csv(data_file(data_folder(home), NOISY_NAME))
    table = table[table["discharge"].isin(locked_discharge_ids())]
    clean_model = predict.Model(home / "out" / "model" / "clean-model.npz")
    noise_model = predict.Model(home / "out" / "model" / "noisy-model.npz")

    measurements = table[clean_model.inputs].to_numpy()
    estimates = {
        "clean-input model (trained on clean inputs)": (clean_model, clean_model.estimates(measurements)),
        f"noise model (trained with noise, last {noise_model.window} instants)":
            (noise_model, noise_model.estimates_noisy(measurements, table["discharge"].to_numpy(), table["time"].to_numpy())),
    }
    print(f"mean absolute error of the axis position on {len(table):,} rows of {table['discharge'].nunique()} "
          "set-aside discharges, noisy inputs:")
    for name, (model, estimate) in estimates.items():
        errors_mm = []
        for target in ("R_mag_axis", "Z_mag_axis"):
            reference_mm = table[target].to_numpy() * 1000
            errors_mm.append(np.nanmean(np.abs(estimate[:, model.outputs.index(target)] - reference_mm)))
        print(f"  {name:<52} R axis {errors_mm[0]:7.2f} mm   Z axis {errors_mm[1]:7.2f} mm")
    print("Why: the clean-input model learned only clean inputs, so the noise moves it far off; the noise model learned with noise added "
          f"and sees the last {noise_model.window} instants of the discharge, so the noise partly averages out.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--full", action="store_true", help="all analysis steps and all ten notebooks (about 9 to 10 min)")
    parser.add_argument("--check", action="store_true", help="only check packages and data")
    args = parser.parse_args()

    print(f"{BOLD}Plasma shape from magnetic measurements (COMPASS, task IPP 1){RESET}")
    check_packages()
    home = find_home()
    if args.check:
        print(f"\n{GREEN}OK{RESET}: run `python run.py` for the live demo or `python run.py --full` for everything.")
        return

    env = {**os.environ, "HACKATHON_HOME": str(home),
           "PYTHONPATH": str(HERE / "analysis") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    python = sys.executable

    if args.full:
        print_step("3. Everything: all analysis steps, then all ten notebooks")
        run_command([python, "analysis/run_analyses.py", "--quick", "--notebooks"], env, show_command=True)
        print(f"\n{GREEN}Finished.{RESET} Executed notebooks: {home / 'out' / 'notebooks'}")
        return

    print_step("3. Live: the network learns, then estimates a discharge it never saw, then runs at full speed")
    run_command([python, "-u", "analysis/live_demo.py", "--dump-rows", "0"], env, show_command=True)

    print_step("4. Train the shipped models and export them "
               "(out/model/clean-model.npz for clean inputs, out/model/noisy-model.npz for noisy inputs)")
    run_command([python, "analysis/noisy_model.py"], env, show_command=True)
    run_command([python, "-u", "analysis/clean_model.py", "--live"], env, show_command=True)  # nasazený model se učí se stejným živým grafem jako demo

    model_path = home / "out" / "model" / "clean-model.npz"
    print_step("5. First estimate with the exported model (reference reconstruction against our estimate)")
    first_estimate(home, model_path)

    print_step("6. Noisy inputs: the provided noisy file on the 30 set-aside discharges")
    compare_models_on_noisy_inputs(home)

    noisy_model_path = model_path.with_name("noisy-model.npz")
    print(f"\n{GREEN}Done.{RESET} Everything: python run.py --full. "
          f"Try the model on your own file: python predict.py input.csv --model {shlex.quote(str(model_path))}"
          f"\nNoisy measurements (needs the columns discharge and time): "
          f"python predict.py input.csv --noisy --model {shlex.quote(str(noisy_model_path))}")


if __name__ == "__main__":
    main()
