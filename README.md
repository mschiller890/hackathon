# Plasma shape from magnetic measurements (COMPASS tokamak, task IPP 1)

CVUT ML Hackathon 2026. A small neural network estimates 16 numbers that describe the position and shape of the plasma from 24 magnetic measurements, in about 0.03 ms per estimate. All errors are agreement with the institute's reference reconstruction, not accuracy against the real plasma.

**Headline (agreement with the reference reconstruction, protocol next to every number):** radial axis position 0.13 mm [0.10; 0.18] on 30 discharges set aside before the final model choice, 0.23 mm in 5-fold cross-validation by whole discharges, 0.40 mm on the newest discharge numbers; limiter point 4.55 mm and 8.35 mm; plasma current 0.035 kA; one estimate takes 0.015 to 0.027 ms on one Apple M5 core (only the network computation was measured, not a real-time control loop).

## What is in this folder

| File | What it is |
|---|---|
| `notebooks/01 .. 10` | The notebooks with all conclusions, executed (outputs are saved, they can be read without running). Order: 01 data, 02 baseline models, 03 inputs and importance, 04 stability over time, 05 latency, 06 camera, 07 uneven distribution and unusual shapes, 08 noise, drift and amount of data, 09 shipped model on the 30 set-aside discharges, 10 synthetic test with a known truth |
| `slides.pdf`, `slides.pptx` | The presentation (7 minutes, with a live demo of the shape viewer) |
| `handout.pdf` | One-page summary for the jury (Czech) |
| `requirements.txt` | Python 3.12 packages with the versions that produced the results (`python -m pip install -r requirements.txt`) |
| `run.py` | **The one file that runs everything** (see below) |
| `analysis/` | All scripts: the pipeline of `make_all.py`, the training (`ipp1_common.py`, `ipp1_final.py`, `export_model.py`), the live training demo (`ipp1_live_train_fast.py`) and the checks |
| `results/` | The aggregate results and figures that the notebooks read |
| `viewer/` | Sources of the shape viewer (`build.py` writes one HTML file from local data) |
| `predict.py` | Try the model: `python predict.py input.csv` (numpy only). The CSV has the columns IPR01..IPR16 and FL01..FL08; the output is the 16 estimates per row in mm and kA. Needs `model/ipp1-selected.npz` and `model/ipp1-selected.json` (given to the organisers separately: the weights are derived from the confidential IPP data and are not published) |

## Run it: one file

```
python -m pip install -r requirements.txt
python run.py            # about 2 minutes: live training, test on unseen discharges, export of the model, a first estimate
python run.py --full     # about 9 minutes: all analysis steps and all ten notebooks, executed
python run.py --check    # only checks the packages and the data
```

`run.py` needs the IPP data in `data/raw/ipp1-magnetic/uloha_1-magneticka_data/` (`equil_data.csv`, `equil_data_noisy.csv`) or `HACKATHON_HOME` pointing to a folder that holds `data/`. The data are confidential (IPP provided them only for this hackathon) and are **not in git**; no raw rows are in the repository. The live demo (`analysis/ipp1_live_train_fast.py`, written by the team's second member) prints rows of the data to the terminal: show it in the room, do not record or send it. Try the exported model on your own file with `python predict.py input.csv --model out/model/ipp1-selected.npz`.

## Limits (what was not shown)

Physical accuracy against the real plasma (only agreement with the reference reconstruction); shapes outside the data range (18 most unusual discharges were held out of training: about 2.5 times larger axis error, but 14 of them are early discharges); a real-time control system (signal acquisition and worst case on real hardware were not measured); noisy inputs for the model trained on clean data (it fails: use the noise-trained one). Drift results are synthetic: the provided noisy file has white noise only. The camera part uses a small 48x64 network on 78 discharges and is weaker than the coils.

Czech summary: malá neuronová síť odhadne z 24 magnetických měření polohu a tvar plazmatu v tokamaku COMPASS za setiny milisekundy; čísla jsou shoda s rekonstrukcí ústavu, ne přesnost vůči skutečnému plazmatu.
