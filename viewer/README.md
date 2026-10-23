# Plasma shape viewer

An offline page that shows, for one discharge of the COMPASS data, the true plasma shape against the shape predicted by the network, with the
parameter table, the error over time, magnifier tiles around the key points and a "measurement noise" mode (plain against hardened network).

**CON-001: the page holds IPP data. It never goes to a public site, a deployment service or a chat.** `data.js` and `dist/` are gitignored.

## Build from a fresh checkout

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
- Predictions are out of fold: every discharge was predicted by a network that never saw it.

## Known limits (show them, do not hide them)

- Start and end of a discharge are less reliable; the opening frame is a divertor mid-discharge frame on purpose.
- Limited frames: the predicted outline can be off by 25 to 30 mm at the inner side (`Z_inner`, inner squareness); the limiter point is the weakest target.
- Tested in Chrome only (the page uses CSS `:has` and `color-mix`).
