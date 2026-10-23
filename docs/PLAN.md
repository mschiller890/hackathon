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
| IMPL-5 | Robustness to noise and drift; amount of data; time context. Lane R (GPT) | IN PROGRESS | REQ-B02, REQ-B04, REQ-B06 | Plan: test causal windows, whole-discharge subsets and seeded drift; run the three assigned scripts with 5 group folds, shared MLP and fixed seeds; inspect JSON/MD/PNG outputs and hand aggregate findings to Lead for notebook integration. |
| IMPL-6 | Camera data: download (876 MB), match images to rows | IN PROGRESS | Zip complete and checked; mapping to rows verified | Zip downloaded, 876,259,021 bytes (equals the Drive size); extraction and mapping still to do |
| IMPL-7 | Camera model | TODO | REQ-B01, REQ-B03, REQ-B05 | Notebook outputs |
| IMPL-8 | Notebooks that run top to bottom, README and results table | TODO | REQ-005 | Clean run on a second machine |
| IMPL-9 | Presentation, video, motion reel | TODO | REQ-006 | Delivered files |
| IMPL-10 | Plasma shape viewer (offline page, true against predicted). Lane U | IN PROGRESS | Opens by double click, shows wall, boundary, key points, slider, errors | Browser screenshot checked; v0 checked in headless Chrome at 1920x1080 and 1280x720 (slider, 149 discharges, table, error chart). Open: wall outline (needs the owner's OK to download `COMPASS_stena.csv`), predicted boundary (needs `R_top`, `Z_top`, `R_bottom`, `Z_bottom`, `R_outer`, `Z_outer`, `R_inner`, `Z_inner`, `squareness_*` among the predicted targets) |
| IMPL-11 | Reproducibility check on a second machine; presentation outline in Czech. Lane K | TODO | README commands work; `presentation/outline.md` exists with numbers only from `results/` | Run log; the file |

Lanes, owners, paths and briefs: [`WORKERS.md`](WORKERS.md).

## Open questions and blockers

See `REQUIREMENTS.md` (OQ-001 to OQ-004). No blocker for IMPL-3 to IMPL-5.

## Milestones (checkpoints, Fri to Sat)

| Time | Checkpoint |
|---|---|
| Fri 18:00 | Baseline table and latency recorded |
| Fri 22:00 | All required analyses have a number and a graph |
| Sat 02:30 | Everything runs top to bottom in the notebooks |
| Sat 08:00 | Polish; reel first cut can start |
| Sat 10:00 | Feature freeze |
| Sat 12:00 to 13:00 | Submission checklist and submit |
