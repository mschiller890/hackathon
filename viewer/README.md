# Plasma shape viewer

An offline page that shows, for one discharge of the COMPASS data, the true plasma shape against the prediction of the **shipped model** (`cand` of `analysis/ipp1_final.py`, see `results/ipp1-final.md`), with the
parameter table, the error over time, magnifier tiles around the key points, the latency of the shipped pair and a "measurement noise" mode (the shipped model trained on clean data
against the baseline network trained with noise, both on the provided noisy inputs).

**CON-001: the page holds IPP data. It never goes to a public site, a deployment service or a chat.** `data.js` and `dist/` are gitignored.

## Build from a fresh checkout

**Default (shipped model).** `python analysis/make_all.py --missing` builds the cache `out/ipp1-final-cache/` (the 21 `ipp1_final.py --job` steps), then `python analysis/export_viewer_data.py`
reads it together with `results/ipp1-latency-shipped.md` and writes `viewer/data.js` (`"model": "shipped"`): the 30 locked discharges first (ids in `results/ipp1-locked-test-ids.txt`),
whose predictions come from the model trained on the 119 development discharges, then the 119 development discharges out of fold. The model predicts 16 targets, so **no predicted outline is
drawn, only the predicted points**. The latency tile, the CPU name and the per-discharge axis errors in the picker are read from files, none is typed into the page. Then `python viewer/build.py`
for the one-file `viewer/dist/index.html`.

**Fallback (baseline network, with the predicted outline).** Without the cache the exporter uses the baseline network's out-of-fold predictions, steps 1 to 5 below.

Set `HACKATHON_HOME` to the folder that holds `data/` and `repo/`, and use the environment of the main README (Python 3.12, pandas).

| Step | Command | Needs |
|---|---|---|
| 1 | `python analysis/ipp1_oof.py` | `data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv`; writes `out/ipp1-predictions.csv` |
| 2 | `python analysis/ipp1_oof_full.py` | the same data; writes `out/ipp1-predictions-full.csv` (all 31 targets as `<name>_pred`, including the 12 outline columns). **Without this file the predicted outline is not drawn**, only the predicted points. |
| 3 | `python analysis/ipp1_oof_noise.py` | `equil_data_noisy.csv`; writes `out/ipp1-predictions-noise.csv`. Without it the "Šum měření" switch is hidden. |
| 4 | optional: save the organizers' `notebooks/COMPASS_stena.csv` as `data/raw/organizers/COMPASS_stena.csv` | draws the vacuum wall |
| 5 | `python analysis/export_viewer_data.py` | writes `viewer/data.js` (reads `ipp1-predictions-full.csv` if it exists, else `ipp1-predictions.csv`) |
| 6 | open `viewer/index.html`, or `python viewer/build.py` for the one-file `viewer/dist/index.html` | |

`python viewer/record.py --stills presentation/assets --clip out/viewer-demo.mp4` makes the slide stills and a 15 s clip (needs Chrome, ffmpeg and `websocket-client`).

## Use

- Address options: `index.html#d=<discharge>&f=<0..1>&noise=1&play=1` (discharge, position in the discharge, noise mode, autoplay).
- Space plays, left and right arrows step, Home and End jump; clicking or dragging in the error chart seeks.
- Every prediction is of a model that never saw the discharge: the 30 set-aside discharges (first in the picker) by the model trained on the other 119, the 119 development discharges out of fold.
  "Set aside" is not "unseen by the idea": the recipe was designed on cross-validation over all 149 discharges (`docs/review-findings-2.md`, H2).
- The axis error in the picker is the mean distance between the true and the predicted magnetic axis over the rows the viewer shows (every third row), so it can differ slightly from a mean over all rows.

## Known limits (show them, do not hide them)

- Start and end of a discharge are less reliable; the opening frame is a divertor mid-discharge frame on purpose.
- The shipped model has no predicted outline (fallback mode: on limited frames the predicted outline can be off by 25 to 30 mm at the inner side). The limiter point is the weakest target in both modes.
- In the noise mode the red series is the shipped model trained on clean data, which fails on noisy inputs (hundreds of mm); the green series is the baseline network trained with noise.
- Tested in Chrome only (the page uses CSS `:has` and `color-mix`).
