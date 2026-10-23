# Plasma shape from magnetic measurements (COMPASS, IPP task 1)

CVUT ML Hackathon 2026. Team: DOPLNIT (owner). Repository state: see the last commit; the numbers below come from `results/`. Documents index: [`docs/README.md`](docs/README.md); script index: [`analysis/README.md`](analysis/README.md).

1. **Task.** From 24 magnetic signals (16 coils, 8 flux loops) of the COMPASS tokamak estimate 16 plasma quantities (magnetic axis, X point, strike points, limiter point, current, elongation, triangularity) fast enough for control. The classical reconstruction takes minutes.
2. **Data.** 42,972 rows from 149 discharges, provided by the Institute of Plasma Physics (IPP). The labels are the institute's reference reconstruction, so every error is **agreement with that reconstruction**, not physical accuracy. The data are confidential and are not in this repository.
3. **Method.** A small neural network (the "basic network"). The **shipped model** adds 22 differences of neighbouring coils, a ridge regression for the plasma current and a separate network for the limiter point. For the provided noisy inputs we ship another network, trained with noise.
4. **Main result.** Radial magnetic axis error **0.133 mm** (mean absolute error, pooled over rows) on **30 discharges set aside** before the final model choice and scored once; the basic network gives 0.307 mm on the same 30. Plasma current 0.035 kA against 1.20 kA. Source: [`results/ipp1-final.md`](results/ipp1-final.md).
5. **Other protocols for the same number.** 0.23 mm in 5-fold cross validation on the other 119 discharges; 0.397 mm when trained on the 60 lowest discharge ids and tested on the 59 highest (ids look chronological, not confirmed). The recipe was chosen by cross validation over all 149 discharges, so the 30 are "set aside", not "unseen by the idea".
6. **Speed.** One sample takes a median 0.015 ms (diverted) to 0.027 ms (limited), p99 0.06 to 0.09 ms, one core of an Apple M5 on a shared machine (`results/ipp1-latency-shipped.md`). Only the network computation was timed. Real-time verdict: conditional.
7. **Noise.** A model trained on clean data fails on the provided noisy file (radial axis 9.16 mm for the basic network on the 30); the noise-trained network gives 2.38 mm.
8. **Also done.** Fewer inputs, stability over time, error distribution and unusual shapes, amount of data, time context, a closed test on simulated plasmas, and a small camera network (axis 1.7 to 1.8 mm, worse than magnetics).
9. **Talk and one-page summary.** [`docs/HANDOUT.md`](docs/HANDOUT.md) (English; Czech: [`docs/HANDOUT.cs.md`](docs/HANDOUT.cs.md)); the deck is [`presentation/deck/slides.pdf`](presentation/deck/slides.pdf) (Czech) and the 7 minute talk is in Czech, see Files.
10. **Not shown.** See Limits.

## How to read this repository

Start with the handout (2 minutes), then the notebooks. Every notebook has its outputs stored, so you can read it on GitHub without running anything. Order:

| # | Notebook | Answers | Needs the data to re-run |
|---|---|---|---|
| 1 | `notebooks/01_data_exploration.ipynb` | what the data look like, why folds must be whole discharges | yes |
| 2 | `notebooks/02_baseline_models.ipynb` | ridge against the basic network, 5 folds | yes |
| 3 | `notebooks/09_final_model_locked_test.ipynb` | **the main result**: shipped model on the 30 set-aside discharges | yes |
| 4 | `notebooks/03_inputs_and_importance.ipynb` | which of the 24 inputs matter | yes |
| 5 | `notebooks/04_stability_over_time.ipynb` | error and smoothness during a discharge | yes |
| 6 | `notebooks/05_realtime_latency.ipynb` | speed of one prediction | yes |
| 7 | `notebooks/07_distribution_and_unusual_shapes.ipynb` | where the error sits, unseen shape families | no |
| 8 | `notebooks/08_robustness_and_data_amount.ipynb` | noise, drift, amount of data, time context | no |
| 9 | `notebooks/06_camera_models.ipynb` | bonus: camera network | no |
| 10 | `notebooks/10_synthetic_validation.ipynb` | closed test on simulated plasmas (not COMPASS data) | no data at all; trains small networks |

Numbers in the notebooks come from the aggregate files in [`results/`](results/); the main one is `results/ipp1-final.md`.

## Run it

**The data are not in the repository** (confidential, for this hackathon only). They are the file `uloha_1-magneticka_data.zip` from the organisers' shared folder (participants only; the link is not published here). Unzip it so that this file exists, and point `HACKATHON_HOME` at the folder that holds `data/`:

```
$HACKATHON_HOME/data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv   (and equil_data_noisy.csv)
```

Setup (Python 3.12 with [`uv`](https://docs.astral.sh/uv/)):

```bash
uv venv ~/.venvs/hackathon --python 3.12
uv pip install --python ~/.venvs/hackathon/bin/python pandas pyarrow openpyxl matplotlib scikit-learn scipy torch charset-normalizer nbconvert ipykernel
~/.venvs/hackathon/bin/python -m ipykernel install --user --name hackathon   # notebooks 01 to 05 and 09 ask for this kernel
```

On Linux install the CPU build of torch first (`uv pip install torch --index-url https://download.pytorch.org/whl/cpu`), otherwise about 3 GB of CUDA wheels come in.

- **Without the data** (5 to 9 seconds each, run inside a `git clone`: they check their inputs against `git ls-files`): `~/.venvs/hackathon/bin/python -m jupyter nbconvert --to notebook --execute notebooks/07_distribution_and_unusual_shapes.ipynb --output-dir /tmp/nb` (same for `06` and `08`). They read only the committed `results/`.
- **With the data**: `export HACKATHON_HOME=<your folder>` and `~/.venvs/hackathon/bin/python -I analysis/make_all.py --quick --notebooks` (6 to 7 minutes; without `--quick` about an hour). Output goes to `out/`; the committed notebooks are not rewritten.
- **Shipped model without torch.** `python -I analysis/export_model.py` (needs the data, about 30 s) writes the weights to `out/model/`, then `python analysis/predict.py input.csv` estimates the 16 quantities from a CSV with the columns `IPR01` to `IPR16` and `FL01` to `FL08`, numpy only. The weights come from confidential data and never go into git; `analysis/check_predict.py` compares the command line with the cached predictions of the 30.
- **Demo.** `viewer/index.html` is only a template: without `viewer/data.js` it shows one error line, because the page embeds IPP data and is never committed. Without the data look at the stills `presentation/assets/viewer-*.png` and `failure-*.png`. With the data: `python -I analysis/make_all.py --quick --missing --viewer` (about 11 minutes), then open `viewer/dist/index.html` in Chrome (the page is in Czech). The wall outline comes from one public file, `analysis/fetch_wall.py`. Details: [`viewer/README.md`](viewer/README.md).

## Limits

- Agreement with the institute's reconstruction, not physical accuracy; no independent measurement.
- Errors are means. The radial axis median is 0.15 mm against a mean of 0.38 mm for the basic network; limited plasmas are about 2.3 times worse; the last tenth of a discharge is the worst.
- Random folds by discharge are optimistic: on later discharge ids the error is 1.5 to 2.9 times larger (basic network).
- 30 set-aside discharges, one seed per model, only 2 of the 30 with positive plasma current.
- The shipped model gives 16 numbers, not the plasma boundary. Unusual shape families were 1.0 to 3.0 times worse when held out.
- The model trained on clean data does not work on noisy inputs; two models are shipped and the caller must know which input it has. The provided noisy file has white noise and no measurable drift; the drift results are synthetic.
- Real time: only the network computation was timed (one core, shared machine). Signal acquisition and the worst case on a real-time system were not measured; budget 1 to 10 ms.
- The camera network is small (48x64 pixels, 811 thousand parameters) and worse than magnetics (axis 1.7 to 1.8 mm against 0.38 mm); it is a bonus, not a result.

## Files

| Path | What |
|---|---|
| `notebooks/` | ten notebooks with stored outputs (order above) |
| `results/` | aggregate numbers and figures (`.md`, `.json`, `.png`); no raw data. Start with `ipp1-final.md` |
| `analysis/` | the scripts the notebooks use; `make_all.py` runs the pipeline in order; index in [`analysis/README.md`](analysis/README.md) |
| `docs/HANDOUT.md`, `docs/HANDOUT.cs.md` | one-page summary (English, Czech) |
| `docs/REQUIREMENTS.md`, `docs/DECISIONS.md`, `docs/PLAN.md` | what the task asked for and where it is answered; why we chose what we chose; the task board |
| `docs/SUBMISSION.md`, `docs/claims-corrections.md`, `docs/hackathon-rules.md`, `docs/related-work.md` | hand-in checklist; sentences not to say; the organisers' rules; related work (index: [`docs/README.md`](docs/README.md)) |
| `docs/internal/` | working notes of the team and its assistants (plans, reviews, audits, rehearsal); not needed to understand the result |
| `presentation/` | `deck/slides.pptx` (14 slides, Czech) and `deck/slides.pdf` (12 pages, the two hidden slides left out, see `deck/PDF-NOTES.md`), `outline.md` and `pitch-script.md` (the 7 minute talk, Czech), speaker material (`CHEAT-SHEET.md`, `REHEARSAL.md`, `demo-facts.md`) |
| `viewer/` | offline shape viewer, built from the data; see Run it |
| `AGENTS.md`, `CLAUDE.md` | instructions for the coding assistants that worked on this repository |

## Repository tree

```
.
├── README.md, AGENTS.md, CLAUDE.md
├── analysis/        scripts: pipeline, experiments, tools (README.md lists them)
├── notebooks/       10 notebooks with stored outputs
├── results/         aggregate numbers and figures
├── presentation/    talk (outline, pitch script), speaker material
│   ├── deck/        slides.pptx, slides.pdf, build_deck.py
│   └── assets/      images for the deck and the failure gallery
├── viewer/          offline shape viewer (data.js is git-ignored)
└── docs/            handout, requirements, decisions, plan, submission checklist
    └── internal/    working notes: reviews, audits, briefs, timeline
```
