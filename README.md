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
published or shared outside the participants. They live next to the repository, never inside it:

```
hackathon/
├── data/raw/ipp1-magnetic/uloha_1-magneticka_data/   equil_data.csv, equil_data_noisy.csv
├── data/raw/ipp1-photron-zip/                        camera archive (optional)
└── repo/                                             this repository
```

Set `HACKATHON_HOME` to the `hackathon/` folder if you run the scripts from elsewhere.

## Repository structure

| Path | Purpose |
|---|---|
| `AGENTS.md` | Engineering workflow, coding standards, Git practice. |
| `docs/PLAN.md` | The single task tracker. |
| `docs/REQUIREMENTS.md` | Requirements, constraints, assumptions, open questions. |
| `docs/DECISIONS.md` | Significant technical decisions and why. |
| `analysis/` | Scripts: data profiling, exploratory analysis, baseline models. |

## Setup and run

Python 3.12. From the folder that holds `data/` and `repo/`:

```bash
uv venv ~/.venvs/hackathon --python 3.12
uv pip install --python ~/.venvs/hackathon/bin/python pandas pyarrow openpyxl matplotlib scikit-learn torch charset-normalizer
~/.venvs/hackathon/bin/python -I repo/analysis/ipp1_eda.py
~/.venvs/hackathon/bin/python -I repo/analysis/ipp1_baseline.py
```

Install the packages into the venv, not with `pip install --user`: `python -I` ignores user site packages.
Outputs are written to `out/` (outside the repository). Results and their interpretation are documented
in the notebooks once they exist.

## Engineering approach

Development follows [`AGENTS.md`](AGENTS.md): requirements-driven work, claims backed by evidence, small
Conventional Commits, regular pushes.
