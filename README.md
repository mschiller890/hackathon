# Plasma shape from magnetic measurements (COMPASS tokamak, task IPP 1)

CVUT ML Hackathon 2026. A small neural network estimates 16 numbers that describe the position and shape of the plasma from 24 magnetic measurements, in about 0.03 ms per estimate. All errors are agreement with the institute's reference reconstruction, not accuracy against the real plasma.

**Headline (agreement with the reference reconstruction, protocol next to every number):** radial axis position 0.13 mm [0.10; 0.18] on 30 discharges set aside before the final model choice, 0.23 mm in 5-fold cross-validation by whole discharges, 0.40 mm on the newest discharge numbers; limiter point 4.55 mm and 8.35 mm; plasma current 0.035 kA; one estimate takes 0.015 to 0.027 ms on one Apple M5 core (only the network computation was measured, not a real-time control loop).

## What is in this folder

| File | What it is |
|---|---|
| `notebooks/01 .. 10` | The notebooks with all conclusions, executed (outputs are saved, they can be read without running). Order: 01 data, 02 baseline models, 03 inputs and importance, 04 stability over time, 05 latency, 06 camera, 07 uneven distribution and unusual shapes, 08 noise, drift and amount of data, 09 shipped model on the 30 set-aside discharges, 10 synthetic test with a known truth |
| `slides.pdf`, `slides.pptx` | The presentation (7 minutes, with a live demo of the shape viewer) |
| `handout.pdf` | One-page summary for the jury (Czech) |
| `predict.py` | Try the model: `python predict.py input.csv` (numpy only). The CSV has the columns IPR01..IPR16 and FL01..FL08; the output is the 16 estimates per row in mm and kA. Needs `model/ipp1-selected.npz` and `model/ipp1-selected.json` (given to the organisers separately: the weights are derived from the confidential IPP data and are not published) |
| `code.zip` | Everything needed to rerun from the data: `analysis/` (scripts), `results/` (aggregate results and figures read by the notebooks), `viewer/` (shape viewer sources). Unzip it next to `notebooks/` |

## Run it again (needs the IPP data)

```
unzip code.zip
export HACKATHON_HOME=<folder that has data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv>
python -m pip install numpy pandas scikit-learn torch matplotlib nbclient nbformat ipykernel
python analysis/make_all.py --quick --notebooks     # about 9 minutes; --viewer also builds the viewer
```

The data are confidential (IPP provided them only for this hackathon) and are not included; no raw rows are in this folder.

## Limits (what was not shown)

Physical accuracy against the real plasma (only agreement with the reference reconstruction); shapes outside the data range (18 most unusual discharges were held out of training: about 2.5 times larger axis error, but 14 of them are early discharges); a real-time control system (signal acquisition and worst case on real hardware were not measured); noisy inputs for the model trained on clean data (it fails: use the noise-trained one). Drift results are synthetic: the provided noisy file has white noise only. The camera part uses a small 48x64 network on 78 discharges and is weaker than the coils.

Czech summary: malá neuronová síť odhadne z 24 magnetických měření polohu a tvar plazmatu v tokamaku COMPASS za setiny milisekundy; čísla jsou shoda s rekonstrukcí ústavu, ne přesnost vůči skutečnému plazmatu.
