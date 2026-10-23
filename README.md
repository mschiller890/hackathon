# Hackathon: plasma shape from magnetic measurements (CVUT ML Hackathon 2026)

Solution of **IPP task 1** (tokamak COMPASS): determine the shape and position of the plasma from
magnetic measurements, and optionally from fast camera images, fast enough to be considered for
real-time control. The classical reconstruction takes minutes; the network computation takes a small
fraction of a millisecond (median 0.0145 ms per sample for the baseline network, 0.015 to 0.027 ms for the shipped
model, one core of an Apple M5 on a shared machine; see the real-time caveats below).

**Current status (Fri 23 Oct 2026, after the independent review and the audit):** baseline, shipped model, required
analyses and the camera model measured; notebooks in progress. Requirements and their status:
[`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md); task board: [`docs/PLAN.md`](docs/PLAN.md). No result is
claimed here until it is measured and recorded.

**Shipped model and headline number.** For clean inputs the shipped model is `candidate` of
[`results/ipp1-final.md`](results/ipp1-final.md): the network on the 24 inputs plus 22 neighbouring-coil differences,
a ridge for the plasma current and a network for the limiter point gated by the predicted `is_limited`. Its radial axis
error is **0.133 mm on 30 discharges set aside before the final models were trained and scored once** (baseline network
0.307 mm on the same 30; pooled mean absolute error). The recipe itself was chosen earlier by cross validation over all
149 discharges, so these 30 are not "never seen". The same model gives 0.23 mm in 5-fold cross validation on the 119
development discharges and 0.397 mm when trained on the 60 lowest discharge ids and tested on the 59 highest (the baseline
network 0.448 mm on random folds of those 59 and 1.23 mm blocked). Plasma current on the 30: 0.035 kA against 1.20 kA.
For the provided noisy inputs a different model is shipped (baseline network trained with noise and drift): 2.38 mm on
the axis on the same 30. A model trained on clean data fails on them (the plain baseline gives 9.16 mm).

**How to read the numbers** (details and sources in [`results/`](results/) and
[`docs/review-findings.md`](docs/review-findings.md)). The figures below are for the **baseline network** and 5 folds over
all 149 discharges unless a protocol is named:

- Accuracy is measured with folds split by whole discharge, so it is the accuracy on *randomly chosen new
  discharges*. The discharge ids are chronological (`results/ipp1-final.md`; not confirmed with the organizers); on
  contiguous blocks of ids the clean-input error of the baseline network is 1.5 to 2.9 times larger (radial axis 1.23
  against 0.448 mm).
- The headline errors are means: the baseline radial axis error is 0.38 mm on average, the median is 0.15 mm, 99 % of rows
  are under 3.74 mm, and the worst rows are tens of millimetres (the end of a discharge). Limited plasmas are about
  2.3 times worse than divertor ones (`results/ipp1-distribution.md`).
- Plasma current: the linear (ridge) model gives 0.0346 kA, the baseline network 1.49 kA; the shipped model uses the ridge
  for it.
- Real-time verdict: conditional. The network computation is not an obstacle: baseline network median 0.0145 ms, p99
  0.0209 ms for one sample; 0.0140 ms median and 0.0503 ms p99 end to end with numpy in and out
  (`results/ipp1-latency.md`); shipped model 0.0154 ms (diverted) and 0.0274 ms (limited) median, p99 0.057 and 0.093 ms
  end to end (`results/ipp1-latency-shipped.md`). All on one core of an Apple M5 on a shared machine (load average 5.7
  and 7.0, not a clean benchmark). On a general-purpose system tails reach milliseconds (an earlier loaded run gave p99
  0.65 ms and max 21 ms for the baseline network); budget 1 to 10 ms. Not verified: acquisition and integration of the coil
  signals, the worst case on a real-time system, and accuracy on really noisy signals (see the noisy-input model above).
- The provided `equil_data_noisy.csv` has white noise and no measurable drift; all drift results are synthetic.

**Agents and contributors:** read [`CLAUDE.md`](CLAUDE.md) (Claude Code) or [`AGENTS.md`](AGENTS.md) and then
[`docs/WORKERS.md`](docs/WORKERS.md); it assigns the lanes and says what each one does first.

## Data (not in this repository)

The data come from Ústav fyziky plazmatu AV ČR and may be used only for this hackathon; they must not be
published or shared outside the participants. They live in a folder outside the repository, and every script finds
them through `HACKATHON_HOME`:

```
$HACKATHON_HOME/
├── data/raw/ipp1-magnetic/uloha_1-magneticka_data/   equil_data.csv, equil_data_noisy.csv
├── data/raw/ipp1-photron-zip/                        camera archive (optional)
└── out/                                              everything the scripts write (created on the first run)
```

Any folder works. On the owner's Mac it is the `hackathon/` folder that also holds this clone as `repo/`; on a plain
`git clone` pick a sibling folder, for example `~/GitHub/hackathon-home`. Download `uloha_1-magneticka_data.zip` from the
organizers' Drive (participants only; 37,368,783 bytes). The sha256 recorded earlier (`0b2b3dd1aaaeb51b4a6dacbdaf63222f14ea055a82b54e6cf9da2923781381`)
has only 62 of 64 hex digits, so `sha256sum -c` cannot use it: check the size and that the hash starts with `0b2b3dd1`.
Unzip it into `$HACKATHON_HOME/data/raw/ipp1-magnetic/` and check that this file exists (every script stops without it):

```bash
ls "$HACKATHON_HOME/data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv"
```

If the two csv files landed directly in `ipp1-magnetic/`, move them into a new folder `uloha_1-magneticka_data/` there.

## Repository structure

| Path | Purpose |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Engineering workflow and the start-here notes for Claude Code sessions. |
| `docs/PLAN.md` | The single task tracker. |
| `docs/REQUIREMENTS.md` | Requirements, constraints, assumptions, open questions, status and evidence. |
| `docs/DECISIONS.md` | Significant technical decisions and why. |
| `docs/` (other files) | Reviews, audit (`audit.md`), claims corrections, submission checklist, timeline, worker lanes. |
| `analysis/` | Scripts: data profiling, exploratory analysis, models, latency, robustness, the submission builder. |
| `notebooks/` | Five Jupyter notebooks with stored outputs (data, baseline, inputs, stability over time, latency). |
| `results/` | Committed aggregate results (`.md`, `.json`, `.png`); no raw data. |
| `presentation/` | Outline, pitch script, glossary and the deck (`deck/slides.pptx`). |
| `viewer/` | Single-file browser viewer of true and predicted shapes; needs the data to build (`viewer/README.md`). |
| `cloud/` | Briefs for the two cloud sessions (camera model, hyperparameter search). |

## Setup and run

Python 3.12 through [`uv`](https://docs.astral.sh/uv/) (`python3 -m pip install --user uv` if it is missing; `uv` downloads
Python 3.12 itself). From the root of your clone:

```bash
uv venv ~/.venvs/hackathon --python 3.12
# Linux: install the CPU build of torch first (see the notes below), otherwise the next line pulls about 3 GB of CUDA wheels
uv pip install --python ~/.venvs/hackathon/bin/python pandas pyarrow openpyxl matplotlib scikit-learn scipy torch \
    charset-normalizer nbconvert ipykernel
~/.venvs/hackathon/bin/python -m ipykernel install --user --name hackathon   # the notebooks ask for this kernel
export HACKATHON_HOME=~/GitHub/hackathon-home                                # your data folder, see above
~/.venvs/hackathon/bin/python -I analysis/make_all.py --quick --notebooks
```

Install the packages into the venv, not with `pip install --user`: `python -I` ignores user site packages.

Extra packages for the delivery tools only (not needed for the analysis or for `analysis/make_submission.py`, which uses
only the standard library): `uv pip install --python ~/.venvs/hackathon/bin/python python-pptx markdown`.
`python-pptx` is for `presentation/deck/build_deck.py`; `analysis/make_pdf.py` and `viewer/record.py` also need headless
Chrome, ffmpeg and `websocket-client` (none of these were tested on a clean checkout).

Commands that run without data: `python -I analysis/make_submission.py --out <path that does not exist yet>` builds the
submission package and checks it, deck and viewer page included (`docs/SUBMISSION.md`). Every other script and the five notebooks need the data and stop
with an error without it (even `ipp1_latency.py`, which does not use the data, audit R-1). Not for a first run: `analysis/check_claims.py` rewrites the tracked file
`docs/claims-audit.md` (restore it with `git restore docs/claims-audit.md`), `analysis/profile_data.py` needs a data path
argument, and `viewer/build.py` needs `viewer/data.js`, which is made from the data and is not in git.

`analysis/make_all.py` creates `out/`, runs the analysis scripts in the order their outputs depend on each other and then
executes the five notebooks into `out/notebooks/` (the committed notebooks are not rewritten). It stops at the first failing
step. Wall times on a Ryzen 5 7535HS laptop CPU:

| Step | Writes (in `out/`) | Time |
|---|---|---|
| `ipp1_eda.py` | `ipp1-eda.json`, figures | 2 s |
| `ipp1_baseline.py` | `ipp1-baseline.json` | 1 min |
| `ipp1_oof.py` | `ipp1-predictions.csv` | 45 s |
| `ipp1_oof_noise.py` | `ipp1-predictions-noise.csv` | 1.5 min |
| `ipp1_time.py` | `ipp1-time.json` | 3 s |
| `ipp1_inputs.py` | `ipp1-inputs.json` | about 1 h; `--quick` copies `results/ipp1-inputs.json` instead |
| `ipp1_latency.py` | `ipp1-latency.json` | 10 s |
| five notebooks | `notebooks/*.ipynb` | 2 min |

Without `--quick` the whole run takes a little over an hour (`ipp1_inputs.py` alone about 13 minutes per fold), with it 6 to 7 minutes (383 s measured from a fresh clone). Notebook `04` stopped with `KeyError: 'is_limited'` at `b70e773`; `b7f5011` fixed it, but a full `make_all.py --notebooks` run
after that fix is not recorded (`docs/PLAN.md`, IMPL-8). `--missing` skips steps whose outputs already exist. Aggregate results and their interpretation are in `results/` and the notebooks.

Notes from the second-machine check (`docs/PLAN.md`, RP-1 to RP-14):
- On Linux `uv pip install torch` downloads the CUDA build, about 3 GB (a 5.7 GB venv). The scripts use only the CPU, so
  install the CPU build first and the rest afterwards (tested: `torch 2.14.1+cpu` in 110 s, a 1.3 GB venv, and
  `ipp1_baseline.py` gave all 16 MAE and R2 values of `results/ipp1-baseline.md` unchanged):
  `uv pip install --python ~/.venvs/hackathon/bin/python torch --index-url https://download.pytorch.org/whl/cpu`, then the
  `uv pip install` line above.
- Versions that reproduced `results/ipp1-baseline.md` on the second machine: Python 3.12.15, torch 2.14.1, numpy 2.5.4,
  pandas 3.1.0, scikit-learn 1.9.1, scipy 1.18.1, nbconvert 7.17.2. Latency figures depend on the processor.

## Engineering approach

Development follows [`AGENTS.md`](AGENTS.md): requirements-driven work, claims backed by evidence, small
Conventional Commits, regular pushes.
