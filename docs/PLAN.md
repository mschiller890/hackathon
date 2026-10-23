# Implementation Plan

**Authoritative task tracker for this repository.** There is exactly one; no other file
mirrors it. Process rules live in [`../AGENTS.md`](../AGENTS.md) (§3).

## Status: IMPLEMENTATION, task IPP 1 (plasma shape)

Event: Fri 23 Oct 2026 16:00 to Sat 24 Oct 14:00. Requirements: [`REQUIREMENTS.md`](REQUIREMENTS.md).
Decisions: [`DECISIONS.md`](DECISIONS.md).

Statuses: `TODO` · `IN PROGRESS` · `BLOCKED` · `DONE`. A task is `DONE` only when its acceptance
criteria are met **and verified** (`AGENTS.md` §15).

## Task board

| ID | Task | Status | Acceptance criteria | Verification |
|---|---|---|---|---|
| PREP-1 to PREP-4 | Repository inspection, workflow, documentation system, git identity | DONE | See `DECISIONS.md` DEC-001 | Commits on `origin/main` |
| PREP-5 | Analyze the assignment specification | DONE | Requirements extracted and classified in `REQUIREMENTS.md` | Source file read in full; five tasks compared; task chosen (DEC-002) |
| IMPL-1 | Data intake | DONE | Magnetic data downloaded, extracted into its own folder, read-only, profiled | `analysis/profile_data.py` output; 42,972 rows, 57 columns, 149 discharges |
| IMPL-2 | Exploratory analysis | DONE | Structure, missing values, noise, redundancy of inputs, traps written down | `analysis/ipp1_eda.py`; figures; `DECISIONS.md` DEC-003 |
| IMPL-3 | Baseline models (ridge, small neural network), group split by discharge. Lane L | DONE | Per-parameter accuracy and latency, 5 folds | `results/ipp1-baseline.md`: 0.06 to 0.4 mm on axis, X-point, strike points; limiter point 11 and 22 mm; `is_limited` 99.3 %; 0.015 ms per sample on CPU (REQ-001) |
| IMPL-4 | Required analyses: accuracy per parameter, stability over time, real-time verdict, fewer inputs. Lane L | IN PROGRESS | REQ-002, REQ-003, REQ-004 | Measured: `results/ipp1-inputs.md` (24 inputs 0.063 relative error, top 12 0.077, top 8 0.094, IPR coils only 0.066, flux loops only 0.285), `results/ipp1-time.md` (error grows at the start and end of a discharge, jitter ratio about 1), `results/ipp1-latency.md` (0.0145 ms per sample on CPU, 0.24 ms on the Apple GPU); independent review pending |
| IMPL-5 | Robustness to noise and drift; amount of data; time context. Lane R (GPT) | DONE | REQ-B02, REQ-B04, REQ-B06 | `results/ipp1-robustness-findings.md` + 3 figures. Clean model 0.38 mm on clean but 10.2 mm on the noisy file; noise-trained 2.6 mm; 30 discharges give about 1 mm on the axis; 3-row window helps on noisy input (Z axis 2.01 to 1.51 mm) and hurts on clean. 4 checks in `results/ipp1-robustness-checks.py` pass; one fix (time compare tolerance 1e-9 in `aligned_data`) |
| IMPL-6 | Camera data: download (876 MB), match images to rows | IN PROGRESS | Zip complete and checked; mapping to rows verified | Zip downloaded, 876,259,021 bytes (equals the Drive size); extraction and mapping still to do |
| IMPL-7 | Camera model | TODO | REQ-B01, REQ-B03, REQ-B05 | Notebook outputs |
| IMPL-8 | Notebooks that run top to bottom, README and results table | TODO | REQ-005 | Clean run on a second machine |
| IMPL-9 | Presentation, video, motion reel | TODO | REQ-006 | Delivered files |
| IMPL-10 | Plasma shape viewer (offline page, true against predicted). Lane U | IN PROGRESS | Opens by double click, shows wall, boundary, key points, slider, errors | Browser screenshot checked; v0 checked in headless Chrome at 1920x1080 and 1280x720 (slider, 149 discharges, table, error chart). Open: wall outline (needs the owner's OK to download `COMPASS_stena.csv`), predicted boundary (needs `R_top`, `Z_top`, `R_bottom`, `Z_bottom`, `R_outer`, `Z_outer`, `R_inner`, `Z_inner`, `squareness_*` among the predicted targets) |
| IMPL-11 | Reproducibility check on a second machine; presentation outline in Czech. Lane K | IN PROGRESS | README commands work; `presentation/outline.md` exists with numbers only from `results/` | Run log; the file. Split of the extra items: deck (`presentation/deck/slides.pptx`) K-Repro-Opus; rehearsal notes and glossary (`presentation/slovnicek.md`) K-Sonnet; deck v1 b9a29d9, waits for pitch-script.md and presentation/assets/ |

Lanes, owners, paths and briefs: [`WORKERS.md`](WORKERS.md).

## Open questions and blockers

See `REQUIREMENTS.md` (OQ-001 to OQ-004). No blocker for IMPL-3 to IMPL-5.

### Reproducibility check, second machine (IMPL-11, lane K)

Machine: Fedora Linux, kernel 7.2, 12 CPU threads, 14 GB RAM, RTX 2050; system Python 3.14 only, no `uv`.
Fresh clone at `~/GitHub/hackathon`. Each row is a point where `README.md` alone was not enough.

| ID | Problem | What I did | Proposed fix to `README.md` |
|---|---|---|---|
| RP-1 | The layout assumes `hackathon/{data,repo}`, but `git clone` names the repository folder `hackathon/` itself, so there is no `hackathon/` folder next to it and `repo/analysis/...` in the run commands does not exist | Created `~/GitHub/hackathon-home/` with `data/raw` and `out`, used it as `HACKATHON_HOME` | Say "pick any folder for the data, export `HACKATHON_HOME=<it>`" and write the run commands relative to the clone |
| RP-2 | No source for the data: no Drive link, file name, size or checksum, no unzip target | Owner of this machine downloaded `uloha_1-magneticka_data.zip` (37,368,783 bytes, sha256 `0b2b3dd1…3781381`) and unzipped it into `data/raw/ipp1-magnetic/`, made read-only. CSVs: `equil_data.csv` 43,161,674 bytes, `equil_data_noisy.csv` 44,246,279 bytes | Name the zip, its size and where to unzip it; point to the Drive folder without putting the link in the repository if it is private |
| RP-3 | `uv` is required but not installed and not explained | `python3 -m pip install --user uv` (uv 0.13.5); `uv venv --python 3.12` then fetched CPython 3.12.15 itself | One line: how to install `uv` |
| RP-4 | On Linux, plain `uv pip install torch` pulls the CUDA build: torch 2.14.1 plus 16 NVIDIA/triton wheels, about 3.0 GB to download (measured from PyPI). Here at about 1 MB/s it took more than 25 minutes. The scripts only use the CPU | Let the download finish to keep the README command as written | Offer `--index-url https://download.pytorch.org/whl/cpu` for torch on Linux (about 200 MB) |
| RP-5 | The README pins no versions. This machine got torch 2.14.1+cu130, pandas 3.1.0, numpy 2.5.4, scikit-learn 1.9.1; the owner's versions are not recorded, so a mismatch could not be traced to a version | Ran with what `uv` resolved | Record the versions that produced `results/` (a `requirements.txt` or `uv pip freeze`) |
| RP-6 | `results/ipp1-time.png` (middle and right panels) plots the true `R_mag_axis` and elongation of one real discharge row by row. That is close to raw data (CON-001), and WORKERS.md allows only aggregate numbers on slides | The deck uses only the left, aggregate panel until the owner decides | Owner: is a single discharge trace allowed in the public talk? The same question applies to the planned viewer stills `presentation/assets/viewer-*.png` (lane U), which would put true shapes of real discharges into git |
| RP-7 | Latency is hardware bound: here (AMD Ryzen 5 7535HS) one sample takes 0.032 ms median, p99 0.048 ms, batch of 4096 3.7 ms, against 0.015 / 0.042 / 2.3 ms in `results/ipp1-baseline.md`. The real-time verdict still holds (two orders of magnitude under 1 ms) | Recorded | Name the CPU next to every latency figure in `results/` and on the slides |
| RP-8 | WORKERS.md (lane U, item 2) plans to test the portable viewer "on another Mac … on the colleague's machine through lane K", but the colleague's machine is Fedora Linux, not a Mac | Lane K can still test it here (Chrome or Firefox on Linux) once `viewer/dist/index.html` exists | Owner: is a Linux browser test enough, or is a second Mac needed? |

**Result of the check (Fri 17:10).** Both scripts run end to end from a fresh clone once RP-1 to RP-4 are worked
around: `HACKATHON_HOME=~/GitHub/hackathon-home ~/.venvs/hackathon/bin/python -I analysis/ipp1_eda.py` (2.9 s) and
`.../ipp1_baseline.py` (54 s wall, 5 folds, 60 epochs, CPU). EDA matches IMPL-1 and DEC-003: 42,972 rows, 57 columns,
149 discharges (17 to 439 rows), 24 inputs, 31 targets, 44.2 % limited, PCA 92.8 % at two components and 99.93 % at five.
Baseline against `results/ipp1-baseline.md`: all 16 MLP MAE and R2 values identical at the printed precision, `is_limited`
accuracy identical (ridge 0.912, MLP 0.993), 107,152 parameters. Ridge differs only in the third or fourth digit
(`plasma_current` 0.0323 against 0.0346 kA, `elongation` 0.0921 against 0.092, triangularities +0.0001), likely
library versions (RP-5); no reported conclusion changes. Latency differs by hardware (RP-7). Still open for the
acceptance criterion "README commands work": the README fixes for RP-1 to RP-5 (owner's file).

## Milestones (checkpoints, Fri to Sat)

| Time | Checkpoint |
|---|---|
| Fri 18:00 | Baseline table and latency recorded |
| Fri 22:00 | All required analyses have a number and a graph |
| Sat 02:30 | Everything runs top to bottom in the notebooks |
| Sat 08:00 | Polish; reel first cut can start |
| Sat 10:00 | Feature freeze |
| Sat 12:00 to 13:00 | Submission checklist and submit |
