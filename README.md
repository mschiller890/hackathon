# Plasma shape from magnetic measurements (COMPASS tokamak, task IPP 1)

**Česky:** [README.cs.md](README.cs.md) (kompletní popis, výsledky, problémy a jejich řešení).

CVUT ML Hackathon 2026. A small neural network estimates 16 numbers that describe the position and shape of the plasma from 24 magnetic measurements, in about 0.05 ms per estimate. All errors are agreement with the institute's reference reconstruction, not accuracy against the real plasma.

**Headline (agreement with the reference reconstruction, protocol next to every number):** radial axis position 0.056 mm [0.048; 0.066] and vertical 0.063 mm on 30 discharges set aside before the final model choice, with 99.9 % (R) and 99.7 % (Z) of the instants under 1 mm; X point 0.047 / 0.053 mm, limiter point 2.9 / 4.5 mm (the weak spot: about 2 % of the limited rows are off by more than 32 mm), plasma current 0.034 kA; overall accuracy 95.8 % (100 x (1 - RMSE / spread of the reference), mean over the 16 outputs; charts in `results/ipp1-accuracy-*.png`, numbers in `results/bench-mm.md`). The shipped model for clean inputs divides every measurement by the plasma current (the shape depends on the ratios of the fields, not on their size; `analysis/ipn_model.py`, `results/ipp1-ipn.md`): in 5-fold cross-validation by whole discharges it halves the mean relative error of the earlier recipe (0.095 to 0.045). The 30 discharges had already been scored for the earlier recipes (general network 0.13 mm, with a separate axis network 0.063 mm), so they are not a fresh test for this one. One estimate takes about 0.05 ms through `predict.py` on one Apple M5 core (only the network computation was measured, not a real-time control loop). Noisy measurements: a second, noise-trained model, axis 1.85 mm (R) and 1.25 mm (Z) on the provided noisy file (`results/ipp1-noise-window.md`); the clean-input model is not meant for noisy inputs.

## What is in this folder

| File | What it is |
|---|---|
| `notebooks/01 .. 10` | The notebooks with all conclusions, executed (outputs are saved, they can be read without running). Order: 01 data, 02 baseline models, 03 inputs and importance, 04 stability over time, 05 latency, 06 camera, 07 uneven distribution and unusual shapes, 08 noise, drift and amount of data, 09 shipped model on the 30 set-aside discharges, 10 synthetic test with a known truth |
| `slides.pdf`, `slides.pptx` | The presentation (7 minutes, with a live demo of the shape viewer) |
| `handout.pdf` | One-page summary for the jury (Czech) |
| `requirements.txt` | Python 3.12 packages with the versions that produced the results (`python -m pip install -r requirements.txt`) |
| `run.py` | **The one file that runs everything** (see below) |
| `analysis/` | 17 scripts: the pipeline of `make_all.py`, the training (`ipp1_common.py`, `ipp1_final.py`, `export_model.py`), the live demo `mini_pipeline.py` (learning epoch by epoch, one unseen discharge instant by instant, full speed) and a second live demo with a ReLU network (`ipp1_live_train_fast.py`, `python run.py --relu-demo`), `predict.py` and the synthetic test |
| `results/` | The aggregate results and figures that the notebooks read |
| `predict.py` | Try the model: `python predict.py input.csv` (numpy only). The CSV has the columns IPR01..IPR16 and FL01..FL08; the output is the 16 estimates per row in mm and kA. Needs `model/ipp1-ipn.npz` and `model/ipp1-ipn.json` (or `out/model/`, where `run.py` exports them) (given to the organisers separately: the weights are derived from the confidential IPP data and are not published). For noisy measurements: `python predict.py input.csv --noisy` (second model `ipp1-noisy.npz`, needs the columns `discharge` and `time`) |

## Run it: one file

```
python3.12 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py            # about 1.5 to 2 min on an Apple M5: live training, test on unseen discharges, export of the two models, a first estimate, the noisy inputs
python run.py --full     # about 9 to 10 min: all analysis steps and all ten notebooks, executed
python run.py --check    # only checks the packages and the data
```

`run.py` needs the IPP data in `data/raw/ipp1-magnetic/uloha_1-magneticka_data/` (`equil_data.csv`, `equil_data_noisy.csv`) or `HACKATHON_HOME` pointing to a folder that holds `data/`. The data are confidential (IPP provided them only for this hackathon) and are **not in git**; no raw rows are in the repository. The live demo (`analysis/ipp1_live_train_fast.py`, written by the team's second member) prints rows of the data to the terminal: show it in the room, do not record or send it. Try the exported model on your own file with `python predict.py input.csv --model out/model/ipp1-ipn.npz`. For noisy measurements `run.py` also exports a second, noise-trained model (`out/model/ipp1-noisy.npz`: trained on clean rows plus a copy with noise and drift added, and each estimate sees the last 5 instants of the same discharge); `python predict.py input.csv --noisy` runs it and needs the columns `discharge` and `time`. On the provided noisy file and the 30 set-aside discharges its axis error is 1.85 mm (R) and 1.25 mm (Z), where the selected model, trained on clean inputs, fails (`results/ipp1-noise-window.md`, step 6 of `run.py`). Millimetre deviation from the institute's reconstruction per quantity (MAE, percentiles, share under 1 mm, bootstrap intervals by discharge): `python analysis/bench_mm.py [--set locked|dev|all] [--noisy] [--csv FILE] [--json OUT]`; its output on the 30 set-aside discharges is in `results/bench-mm.md`.

## Limits (what was not shown)

Physical accuracy against the real plasma (only agreement with the reference reconstruction); shapes outside the data range (18 most unusual discharges were held out of training: about 2.5 times larger axis error, but 14 of them are early discharges); a real-time control system (signal acquisition and worst case on real hardware were not measured); noisy inputs for the selected model, which is trained on clean data and fails on them: noisy measurements need the separate noise model (`--noisy`), which is less accurate on clean inputs, needs rows in time order with the training's sampling interval, and was checked only on the provided white noise. Drift results are synthetic: the provided noisy file has white noise only. The camera part uses a small 48x64 network on 78 discharges and is weaker than the coils.

Czech summary: malá neuronová síť odhadne z 24 magnetických měření polohu a tvar plazmatu v tokamaku COMPASS za setiny milisekundy; čísla jsou shoda s rekonstrukcí ústavu, ne přesnost vůči skutečnému plazmatu.
