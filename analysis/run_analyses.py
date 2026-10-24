#!/usr/bin/env python
"""Vytvoří všechny soubory, které čtou notebooky, v pořadí podle závislostí, a volitelně pak spustí notebooky.

    HACKATHON_HOME=<složka hackathonu> ~/.venvs/hackathon/bin/python analysis/run_analyses.py [--quick] [--missing] [--notebooks]
        [--viewer]

Spouští stávající analytické skripty beze změny tímto interpreterem a zapisuje do $HACKATHON_HOME/out. Zastaví se u prvního
kroku, který selže.
--quick    u kroku, který trvá déle než 10 minut, zkopíruje jeho uložený souhrn z results/ do out/ místo nového výpočtu
           (dnes jen input_importance.py, asi hodina, protože učí kontrolní podmnožiny).
--missing  přeskočí krok, jehož výstupy všechny existují.
--notebooks pak spustí notebooks/*.ipynb do out/notebooks/, takže se uložené notebooky nepřepisují.
--viewer   pak postaví prohlížeč tvaru plazmatu: základní predikce všech 31 cílů, viewer/data.js a jediný soubor
           viewer/dist/index.html. Výchozí režim „shipped“ prohlížeče čte cache z final_evaluation.py, kterou zapíšou kroky výše.
           Oba soubory prohlížeče obsahují data ÚFP a jsou v .gitignore (CON-001).
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (skript, výstupy, které čtou další kroky nebo notebooky, doba na noteboocích s Ryzen 5 7535HS, pá 23. října).
# stability_over_time.py potřebuje predikce z out_of_fold.py a řádky se zašuměnými vstupy do results/stability-over-time.md přidá,
# jen když předtím proběhl out_of_fold_noisy.py.
STEPS = [
    ("explore_data.py", ["eda.json"], "2 s"),
    ("baseline_models.py", ["baseline.json"], "1 min"),
    ("out_of_fold.py", ["predictions.csv"], "45 s"),
    ("out_of_fold_noisy.py", ["predictions-noise.csv"], "1.5 min"),
    ("stability_over_time.py", ["stability-over-time.json"], "3 s"),
    ("input_importance.py", ["input-importance.json"], "about 1 h"),
    ("latency.py", ["latency.json"], "10 s"),
]
# Notebook 09 čte predikce, které final_evaluation.py ukládá do out/final-evaluation-cache/: recepty `base`, `cand` a `base_aug` (model pro zašuměné
# vstupy) na 30 odložených výbojích, na blokovém dělení a na 5 vývojových foldech, dohromady 21 sítí. Každá je jedna úloha (celkem 295 s na Apple M5, nejdelší 32 s);
# `--report` se tu nespouští, protože přepisuje uložený results/final-evaluation.md.
FINAL_JOBS = ([f"locked:{r}" for r in ("base", "cand", "base_aug")] + [f"blocked:{r}" for r in ("base", "cand", "base_aug")]
              + [f"cv:{r}:{k}" for r in ("base", "cand", "base_aug") for k in range(5)])
STEPS += [(f"final_evaluation.py --job {j}", [f"final-evaluation-cache/{j.replace(':', '_')}.npz"], "5 min in total") for j in FINAL_JOBS]
STEPS.append(("noisy_model.py", ["model/noisy-model.npz"], "20 s"))   # zašuměný model pro predict.py; učí se na 119 vývojových výbojích
STEPS.append(("clean_model.py", ["model/clean-model.npz"], "40 s"))   # nasazený model pro čistá měření (čte ho notebook 09)
SLOW = {"input_importance.py"}  # přes 10 minut: --quick místo toho zkopíruje results/<výstup>
# Spuštění notebooků po tom trvá asi 2 minuty.
VIEWER_STEPS = [
    ("analysis/ipp1_oof_full.py", ["predictions-full.csv"]),  # potřebuje predictions-noise.csv z STEPS
    ("analysis/export_viewer_data.py", []),                          # zapisuje viewer/data.js, ne do out/
    ("viewer/build.py", []),                                         # zapisuje viewer/dist/index.html
]


def run(command, env):
    """Spustí jeden krok v kořeni repozitáře a vypíše příkaz, návratový kód a dobu; při selhání skončí celý skript."""
    started = time.time()
    print("$", " ".join(str(part) for part in command), flush=True)
    return_code = subprocess.run(command, cwd=REPO, env=env).returncode
    print(f"  exit {return_code}, {time.time() - started:.0f} s", flush=True)
    if return_code:
        sys.exit(f"stopped: {command[-1]} failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="copy results/ for steps over 10 minutes instead of rerunning")
    parser.add_argument("--missing", action="store_true", help="skip steps whose outputs already exist")
    parser.add_argument("--notebooks", action="store_true", help="execute the notebooks into out/notebooks afterwards")
    parser.add_argument("--viewer", action="store_true", help="build viewer/dist/index.html afterwards")
    args = parser.parse_args()

    home = Path(os.environ.get("HACKATHON_HOME") or REPO).expanduser().resolve()      # výchozí je repozitář, kde je data/
    data_folders = (home / "data", home / "data/raw/ipp1-magnetic/uloha_1-magneticka_data")
    data = next((folder / "equil_data.csv" for folder in data_folders if (folder / "equil_data.csv").exists()), home / "data/equil_data.csv")
    if not data.exists():
        sys.exit(f"missing {data}: put equil_data.csv and equil_data_noisy.csv in data/ of the repository, or set HACKATHON_HOME to a folder that holds data/")
    out = home / "out"
    out.mkdir(exist_ok=True)  # input_importance.py a latency.py do ní zapisují a sami ji nevytvoří
    env = {**os.environ, "HACKATHON_HOME": str(home)}

    for step, outputs, _ in STEPS:
        script, *extra = step.split()  # krok může mít argumenty: "final_evaluation.py --job cv:cand:0"
        if args.missing and all((out / name).exists() for name in outputs):
            print(f"skip {step}: {', '.join(outputs)} present")
            continue
        if args.quick and script in SLOW:
            for name in outputs:
                shutil.copyfile(REPO / "results" / name, out / name)
            print(f"quick: copied results/{', results/'.join(outputs)} instead of running {script}")
            continue
        run([sys.executable, f"analysis/{script}", *extra], env)

    if args.viewer:
        for script, outputs in VIEWER_STEPS:
            if args.missing and outputs and all((out / name).exists() for name in outputs):
                print(f"skip {script}: {', '.join(outputs)} present")
                continue
            run([sys.executable, script], env)

    if args.notebooks:
        notebook_output = out / "notebooks"
        for notebook in sorted((REPO / "notebooks").glob("*.ipynb")):
            run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
                 "--ExecutePreprocessor.timeout=1800", "--ExecutePreprocessor.kernel_name=python3",
                 "--output-dir", str(notebook_output), str(notebook.relative_to(REPO))], env)
    print("done")


if __name__ == "__main__":
    main()
