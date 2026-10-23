# Hackathon: plasma shape from magnetic measurements (CVUT ML Hackathon 2026)

Solution of **IPP task 1** (tokamak COMPASS): determine the shape and position of the plasma from
magnetic measurements, and optionally from fast camera images, fast enough to be considered for
real-time control. The classical reconstruction takes minutes; the model should answer in
milliseconds.

**Current status:** data profiled, baseline models in progress. Requirements and their status:
[`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md); task board: [`docs/PLAN.md`](docs/PLAN.md). No result is
claimed here until it is measured and recorded.

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

Outputs are written to `out/` (outside the repository). Results and their interpretation are documented
in the notebooks once they exist.

## Engineering approach

Development follows [`AGENTS.md`](AGENTS.md): requirements-driven work, claims backed by evidence, small
Conventional Commits, regular pushes.
