# Hackathon: plasma shape from magnetic measurements (CVUT ML Hackathon 2026)

Solution of **IPP task 1** (tokamak COMPASS): determine the shape and position of the plasma from
magnetic measurements, and optionally from fast camera images, fast enough to be considered for
real-time control. The classical reconstruction takes minutes; the network computation takes a small
fraction of a millisecond (median 0.015 ms per sample on an idle Apple M5 CPU; see the real-time caveats below).

**Current status (Fri 23 Oct 2026, after the independent review):** baseline and required analyses measured;
notebooks and the camera model in progress. Requirements and their status:
[`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md); task board: [`docs/PLAN.md`](docs/PLAN.md). No result is
claimed here until it is measured and recorded.

**How to read the numbers** (details and sources in [`results/`](results/) and
[`docs/review-findings.md`](docs/review-findings.md)):

- Accuracy is measured with 5 folds split by whole discharge, so it is the accuracy on *randomly chosen new
  discharges*. The discharge numbers appear to follow time (not confirmed with the organizers); on contiguous blocks
  of numbers the radial axis error is about 1.5 times larger.
- The headline errors are means: the radial axis error is 0.38 mm on average, the median is 0.15 mm, 99 % of rows
  are under 3.7 mm, and the worst rows are tens of millimetres (the end of a discharge). Limited plasmas are about
  2.3 times worse than divertor ones.
- Plasma current: the linear (ridge) model gives 0.0346 kA, the network 1.49 kA; the final model should use ridge for it.
- Real-time verdict: conditional. The network computation is not an obstacle (median 0.015 ms on an idle CPU,
  0.03 to 0.07 ms on a loaded or different CPU, 0.053 ms end to end with numpy in and out, tails up to milliseconds
  without a real-time system, budget 1 to 10 ms). Not verified: acquisition and integration of the coil signals,
  the worst case on a real-time system, and accuracy on really noisy signals (a network trained on clean data fails
  on them, one trained with noise gives 2.6 mm on the axis).
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
organizers' Drive (participants only; 37,368,783 bytes, sha256 `0b2b3dd1aaaeb51b4a6dacbdaf63222f14ea055a82b54e6cf9da2923781381`)
and unzip it into `$HACKATHON_HOME/data/raw/ipp1-magnetic/`.

## Repository structure

| Path | Purpose |
|---|---|
| `AGENTS.md` | Engineering workflow, coding standards, Git practice. |
| `docs/PLAN.md` | The single task tracker. |
| `docs/REQUIREMENTS.md` | Requirements, constraints, assumptions, open questions. |
| `docs/DECISIONS.md` | Significant technical decisions and why. |
| `analysis/` | Scripts: data profiling, exploratory analysis, baseline models. |

## Setup and run

Python 3.12 through [`uv`](https://docs.astral.sh/uv/) (`python3 -m pip install --user uv` if it is missing; `uv` downloads
Python 3.12 itself). From the root of your clone:

```bash
uv venv ~/.venvs/hackathon --python 3.12
uv pip install --python ~/.venvs/hackathon/bin/python pandas pyarrow openpyxl matplotlib scikit-learn scipy torch \
    charset-normalizer nbconvert ipykernel
~/.venvs/hackathon/bin/python -m ipykernel install --user --name hackathon   # the notebooks ask for this kernel
export HACKATHON_HOME=~/GitHub/hackathon-home                                # your data folder, see above
~/.venvs/hackathon/bin/python -I analysis/make_all.py --quick --notebooks
```

Install the packages into the venv, not with `pip install --user`: `python -I` ignores user site packages.

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

Without `--quick` the whole run takes a little over an hour (`ipp1_inputs.py` alone about 13 minutes per fold), with it 6 to 7 minutes (383 s measured from a fresh clone). **Known problem:** since `e4d4fa7` notebook `04` stops with `KeyError: 'is_limited'` (`docs/PLAN.md`, IMPL-8); `make_all.py` stops there, so run notebook `05` by hand until it is fixed. `--missing` skips steps whose outputs
already exist. `--viewer` also builds the plasma shape viewer (`ipp1_oof_full.py` about 3 min, then `viewer/data.js` and the
single file `viewer/dist/index.html`, both gitignored because they hold IPP data); open it by double click. Aggregate results and their interpretation are in `results/` and the notebooks.

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
