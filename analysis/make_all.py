#!/usr/bin/env python
"""Regenerate every file the notebooks read, in dependency order, then optionally execute the notebooks.

    HACKATHON_HOME=<hackathon folder> ~/.venvs/hackathon/bin/python -I analysis/make_all.py [--quick] [--missing] [--notebooks]
        [--viewer]

Runs the existing analysis scripts unchanged with this interpreter and writes to $HACKATHON_HOME/out. Stops at the first
failing step.
--quick    for a step that takes longer than 10 minutes, copy its committed aggregate from results/ into out/ instead of
           recomputing it (today only ipp1_inputs.py, about an hour since it trains the control subsets).
--missing  skip a step whose outputs all exist.
--notebooks then execute notebooks/*.ipynb into out/notebooks/, so the committed notebooks are not rewritten.
--viewer   then build the plasma shape viewer: all-31-target baseline predictions, viewer/data.js and the single file
           viewer/dist/index.html. The viewer's default "shipped" mode reads the ipp1_final.py caches that the steps above
           write. Both viewer files hold IPP data and are gitignored (CON-001).
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (script, outputs that later steps or the notebooks read, wall time on a Ryzen 5 7535HS laptop CPU, Fri 23 Oct).
# ipp1_time.py needs ipp1_oof.py's predictions and adds the noisy-input rows of results/ipp1-time.md only when
# ipp1_oof_noise.py ran first.
STEPS = [
    ("ipp1_eda.py", ["ipp1-eda.json"], "2 s"),
    ("ipp1_baseline.py", ["ipp1-baseline.json"], "1 min"),
    ("ipp1_oof.py", ["ipp1-predictions.csv"], "45 s"),
    ("ipp1_oof_noise.py", ["ipp1-predictions-noise.csv"], "1.5 min"),
    ("ipp1_time.py", ["ipp1-time.json"], "3 s"),
    ("ipp1_inputs.py", ["ipp1-inputs.json"], "about 1 h"),
    ("ipp1_latency.py", ["ipp1-latency.json"], "10 s"),
]
# Notebook 09 reads the predictions that ipp1_final.py caches in out/ipp1-final-cache/: the recipes `base`, `cand` and `base_aug` (the noisy-input
# model) on the 30 locked discharges, on the blocked split and on the 5 development folds, 21 networks. One job each (295 s in total on an Apple M5, the longest 32 s);
# `--report` is not run here because it rewrites the committed results/ipp1-final.md.
FINAL_JOBS = ([f"locked:{r}" for r in ("base", "cand", "base_aug")] + [f"blocked:{r}" for r in ("base", "cand", "base_aug")]
              + [f"cv:{r}:{k}" for r in ("base", "cand", "base_aug") for k in range(5)])
STEPS += [(f"ipp1_final.py --job {j}", [f"ipp1-final-cache/{j.replace(':', '_')}.npz"], "5 min in total") for j in FINAL_JOBS]
STEPS.append(("export_model.py", ["model/ipp1-selected.npz"], "30 s"))   # the shipped model for analysis/predict.py (notebook 09 calls it); trained on the 119 development discharges
SLOW = {"ipp1_inputs.py"}  # over 10 minutes: --quick copies results/<output> instead
# Executing the notebooks afterwards takes about 2 minutes.
VIEWER_STEPS = [
    ("analysis/ipp1_oof_full.py", ["ipp1-predictions-full.csv"]),  # needs ipp1-predictions-noise.csv from STEPS
    ("analysis/export_viewer_data.py", []),                          # writes viewer/data.js, not out/
    ("viewer/build.py", []),                                         # writes viewer/dist/index.html
]


def run(cmd, env):
    t0 = time.time()
    print("$", " ".join(str(c) for c in cmd), flush=True)
    rc = subprocess.run(cmd, cwd=REPO, env=env).returncode
    print(f"  exit {rc}, {time.time() - t0:.0f} s", flush=True)
    if rc:
        sys.exit(f"stopped: {cmd[-1]} failed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="copy results/ for steps over 10 minutes instead of rerunning")
    ap.add_argument("--missing", action="store_true", help="skip steps whose outputs already exist")
    ap.add_argument("--notebooks", action="store_true", help="execute the notebooks into out/notebooks afterwards")
    ap.add_argument("--viewer", action="store_true", help="build viewer/dist/index.html afterwards")
    args = ap.parse_args()

    home = os.environ.get("HACKATHON_HOME")
    if not home:
        sys.exit("set HACKATHON_HOME to the folder that holds data/raw (see README.md)")
    home = Path(home).expanduser().resolve()
    data = home / "data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv"
    if not data.exists():
        sys.exit(f"missing {data}; unzip uloha_1-magneticka_data.zip into {home / 'data/raw/ipp1-magnetic'}")
    out = home / "out"
    out.mkdir(exist_ok=True)  # ipp1_inputs.py and ipp1_latency.py write into it without creating it
    env = {**os.environ, "HACKATHON_HOME": str(home)}

    for step, outputs, _ in STEPS:
        script, *extra = step.split()  # a step may carry arguments: "ipp1_final.py --job cv:cand:0"
        if args.missing and all((out / o).exists() for o in outputs):
            print(f"skip {step}: {', '.join(outputs)} present")
            continue
        if args.quick and script in SLOW:
            for o in outputs:
                shutil.copyfile(REPO / "results" / o, out / o)
            print(f"quick: copied results/{', results/'.join(outputs)} instead of running {script}")
            continue
        run([sys.executable, "-I", f"analysis/{script}", *extra], env)

    if args.viewer:
        for script, outputs in VIEWER_STEPS:
            if args.missing and outputs and all((out / o).exists() for o in outputs):
                print(f"skip {script}: {', '.join(outputs)} present")
                continue
            run([sys.executable, "-I", script], env)

    if args.notebooks:
        nb_out = out / "notebooks"
        for nb in sorted((REPO / "notebooks").glob("*.ipynb")):
            run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
                 "--ExecutePreprocessor.timeout=1800", "--output-dir", str(nb_out), str(nb.relative_to(REPO))], env)
    print("done")


if __name__ == "__main__":
    main()
