#!/usr/bin/env python
"""One file that runs the whole project: python run.py

    python run.py            training live, test on unseen discharges, export of the two models, a first estimate, the noisy inputs (about 1.5 to 2 min on an Apple M5)
    python run.py --full     everything: all analysis steps and all ten notebooks (about 9 to 10 min)
    python run.py --check    only check the Python packages and the data
    python run.py --relu-demo   the same, with the second live demo (ReLU network)

The IPP data are confidential: the repository is private and only the hackathon participants may have access. The files are in ./data; or set
HACKATHON_HOME to the folder that holds data/ (by default the folder of this file; the two CSV files are in the repository). The live demo prints rows of the data to the terminal: show it in the room, do not record or send it.
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
FLAT = Path("data")                                                  # data/equil_data.csv, data/equil_data_noisy.csv (the files are in the repository)
NESTED = Path("data/raw/ipp1-magnetic/uloha_1-magneticka_data")      # the layout of the original archive, also understood
EQUIL = FLAT / "equil_data.csv"
NOISY = FLAT / "equil_data_noisy.csv"   # export_model.py reads it too


def data_folder(home):
    """The folder under `home` that holds both CSV files (data/ or the original nested layout), or None."""
    return next((home / d for d in (FLAT, NESTED) if all((home / d / n).exists() for n in ("equil_data.csv", "equil_data_noisy.csv"))), None)
B, G, R, D, X = "\033[1m", "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def step(title):
    print(f"\n{B}=== {title} ==={X}", flush=True)


def check_packages():
    step("1. Python packages")
    if sys.version_info < (3, 10):
        sys.exit(f"{R}Python 3.10 or newer is needed (3.12 recommended), this is {sys.version.split()[0]}{X}")
    missing = []
    for mod, pip in [("numpy", "numpy"), ("pandas", "pandas"), ("sklearn", "scikit-learn"), ("scipy", "scipy"), ("torch", "torch"),
                     ("matplotlib", "matplotlib"), ("nbformat", "nbformat"), ("nbconvert", "nbconvert"), ("ipykernel", "ipykernel")]:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pip)
    if missing:
        sys.exit(f"{R}Missing packages: {', '.join(missing)}{X}\nInstall all with:  {sys.executable} -m pip install -r requirements.txt")
    print(f"{G}all packages found{X} (Python {sys.version.split()[0]})")


def find_home():
    step("2. Data")
    for home in [os.environ.get("HACKATHON_HOME"), str(HERE)]:
        if not home:
            continue
        home = Path(home).expanduser().resolve()  # the children run with cwd=HERE, so a relative path would point elsewhere
        folder = data_folder(home)
        if folder:
            print(f"{G}data found{X} in {folder}")
            return home
        if any((home / d / n).exists() for d in (FLAT, NESTED) for n in ("equil_data.csv", "equil_data_noisy.csv")):
            sys.exit(f"{R}Only one of the two data files is there{X} in {home / FLAT}: both equil_data.csv and equil_data_noisy.csv are needed.")
    sys.exit(f"{R}The data were not found.{X}\nThey belong in {HERE / FLAT} (equil_data.csv and equil_data_noisy.csv; the repository has them)\n"
             f"or set HACKATHON_HOME to a folder that holds data/ with these two files.")


def run(cmd, env, title=None):
    if title:
        print(f"{D}$ {' '.join(str(c) for c in cmd)}{X}", flush=True)
    t0 = time.time()
    rc = subprocess.run(cmd, cwd=HERE, env=env).returncode
    if rc:
        sys.exit(f"{R}Step failed (exit code {rc}).{X}")
    print(f"{D}done in {time.time() - t0:.0f} s{X}", flush=True)


def locked_ids():
    """The 30 set-aside discharges, from the file that records them (no import of the training code)."""
    line = next(l for l in (HERE / "results" / "ipp1-locked-test-ids.txt").read_text().splitlines() if l.startswith("locked discharge ids"))
    ids = [int(v) for v in line.split(":", 1)[1].split()]
    assert len(ids) == 30, len(ids)
    return ids


def noisy_inputs(home):
    """Step 6: axis MAE of both exported models on the provided noisy file, 30 set-aside discharges. Prints aggregates only, no data rows."""
    import numpy as np
    import pandas as pd
    sys.path.insert(0, str(HERE / "analysis"))
    import predict
    df = pd.read_csv(data_folder(home) / NOISY.name)
    df = df[df["discharge"].isin(locked_ids())]
    sel, noise = (predict.Model(home / "out" / "model" / f) for f in ("ipp1-ipn.npz", "ipp1-noisy.npz"))
    x = df[sel.inputs].to_numpy()
    est = {"clean-input model (trained on clean inputs)": (sel, sel.estimates(x)),
           f"noise model (trained with noise, last {noise.window} instants)": (noise, noise.estimates_noisy(x, df["discharge"].to_numpy(), df["time"].to_numpy()))}
    print(f"mean absolute error of the axis position on {len(df):,} rows of {df['discharge'].nunique()} set-aside discharges, noisy inputs:")
    for name, (m, e) in est.items():
        mae = [np.nanmean(np.abs(e[:, m.outputs.index(t)] - df[t].to_numpy() * 1000)) for t in ("R_mag_axis", "Z_mag_axis")]
        print(f"  {name:<52} R axis {mae[0]:7.2f} mm   Z axis {mae[1]:7.2f} mm")
    print("Why: the clean-input model learned only clean inputs, so the noise moves it far off; the noise model learned with noise added "
          f"and sees the last {noise.window} instants of the discharge, so the noise partly averages out.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", action="store_true", help="all analysis steps and all ten notebooks (about 9 to 10 min)")
    ap.add_argument("--check", action="store_true", help="only check packages and data")
    ap.add_argument("--relu-demo", action="store_true", help="use the second live demo (ReLU network, 6 cores) instead of mini_pipeline.py")
    a = ap.parse_args()
    print(f"{B}Plasma shape from magnetic measurements (COMPASS, task IPP 1){X}")
    check_packages()
    home = find_home()
    if a.check:
        print(f"\n{G}OK{X}: run `python run.py` for the live demo or `python run.py --full` for everything.")
        return
    env = {**os.environ, "HACKATHON_HOME": str(home), "PYTHONPATH": str(HERE / "analysis") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    py = sys.executable
    if a.full:
        step("3. Everything: all analysis steps, then all ten notebooks")
        run([py, "analysis/make_all.py", "--quick", "--notebooks"], env, True)
        print(f"\n{G}Finished.{X} Executed notebooks: {home / 'out' / 'notebooks'}")
        return
    step("3. Live: the network learns, then estimates a discharge it never saw, then runs at full speed")
    if a.relu_demo:
        run([py, "-u", "analysis/ipp1_live_train_fast.py"], env, True)
    else:
        run([py, "-u", "analysis/mini_pipeline.py", "--dump-rows", "0"], env, True)
    step("4. Train the shipped models and export them (out/model/ipp1-ipn.npz for clean inputs, out/model/ipp1-noisy.npz for noisy inputs)")
    run([py, "analysis/export_model.py", "--no-axis-net"], env, True)
    run([py, "-u", "analysis/ipn_model.py", "--live"], env, True)   # the shipped model learns with the same live chart as the demo
    step("5. First estimate with the exported model (reference reconstruction against our estimate)")
    # the paths go through argv, not into the source, so a quote in a folder name cannot break the code
    code = (
        "import sys, numpy as np, pandas as pd; sys.path.insert(0, 'analysis'); import predict; from ipp1_final import locked_ids;"
        "df = pd.read_csv(sys.argv[1]); m = predict.Model(sys.argv[2]); g = df['discharge'].values;"
        "df = df[~np.isin(g, locked_ids(g))]; disc = df['discharge'].iloc[0]; df = df[df['discharge'] == disc];"
        "x = df[m.inputs].values[:5]; e = m.estimates(x);"
        "print('outputs:', len(m.outputs)); "
        "ref = df['R_mag_axis'].values[:5] * 1000;"
        "print(f'first 5 rows of development discharge {disc} (the exported model was trained on it, so this only checks the export):');"
        "[print(f'  row {i}: reference R axis {ref[i]:.2f} mm, estimate {e[i, m.outputs.index(\"R_mag_axis\")]:.2f} mm') for i in range(5)] if 'R_mag_axis' in m.outputs else print(e[:2])")
    model = home / "out" / "model" / "ipp1-ipn.npz"
    run([py, "-c", code, str(data_folder(home) / EQUIL.name), str(model)], env)
    step("6. Noisy inputs: the provided noisy file on the 30 set-aside discharges")
    noisy_inputs(home)
    print(f"\n{G}Done.{X} Everything: python run.py --full. Try the model on your own file: python predict.py input.csv --model {shlex.quote(str(model))}"
          f"\nNoisy measurements (needs the columns discharge and time): python predict.py input.csv --noisy --model {shlex.quote(str(model.with_name('ipp1-noisy.npz')))}")


if __name__ == "__main__":
    main()
