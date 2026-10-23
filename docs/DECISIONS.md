# Decision Records

**Authoritative log of significant technical decisions.** Process rules live in
[`../AGENTS.md`](../AGENTS.md) (§12).

Only decisions that materially affect architecture, algorithms, dependencies,
correctness, performance, or maintainability are recorded. Trivial coding choices are
not. When new evidence invalidates a decision, the entry is updated and the change
explained — contradictions are not left standing.

---

## DEC-001 — Documentation architecture for the pre-specification phase

**Date:** 2026-10-23
**Status:** Accepted
**Category:** Documentation / process

### Context

The repository was empty apart from `AGENTS.md`. The assignment specification was
outstanding, so no problem statement, requirements, architecture, language, or stack
could be known. The task was to build the *smallest complete* documentation system —
complete enough to receive the specification and support disciplined work, without
inventing project facts or producing empty boilerplate.

### Constraints

- No project facts, requirements, architecture, algorithms, or test results could be
  invented (`AGENTS.md` §0).
- No empty or speculative documents created for the sake of completeness.
- One authoritative source of truth per category; no competing task trackers.
- Every surviving document needed a distinct purpose and a defined keeper.

### Alternatives considered

| Option | Assessment | Outcome |
|---|---|---|
| Create all candidate docs up front (`ARCHITECTURE`, `TESTING`, `ALGORITHMS`, `BENCHMARKS`, …) | Each would contain only "pending" placeholders — no architecture to explain, no commands to document, no algorithms chosen. Fails the "unique information" test. | **Rejected** — pure boilerplate. |
| Create only `AGENTS.md`; defer all else | Avoids boilerplate but leaves no human entry point, no task tracker, and no place to record this decision — a reviewer could not understand the repo's state. | **Rejected** — incomplete. |
| Create the 5 documents that answer real questions now | Each holds information that exists today or is explicitly requested by the workflow (e.g. the traceability model). Defers everything that has no content yet. | **Chosen** |

### Decision

Create and maintain five documents; defer the rest until the assignment justifies them.

**Created:**

| File | Unique information it holds |
|---|---|
| `AGENTS.md` | How engineering work must be performed (refined in place, not replaced). |
| `README.md` | Human entry point; explicitly states the pending-specification status. |
| `docs/PLAN.md` | The single task tracker, with real completed preparation work. |
| `docs/REQUIREMENTS.md` | The traceability model (`REQ-`/`ASM-`/`OQ-`/`CON-` IDs and fields), ready to populate. |
| `docs/DECISIONS.md` | This record, and future technical reasoning. |

**Deferred, and why:**

| File | Reason |
|---|---|
| `docs/ARCHITECTURE.md` | No system exists. Creating it would mean inventing an architecture. |
| `docs/TESTING.md` | No tests, no build, no commands. Would list nothing verifiable. |
| `docs/ALGORITHMS.md` | The problem is unknown, so no algorithm is selected. |
| `docs/RESEARCH.md` | No technical question has been posed to research. |
| `docs/BENCHMARKS.md` | No performance claim has been made to measure. |
| `docs/ISSUES.md` | `PLAN.md`'s tracker suffices at current scale. |
| `docs/SECURITY.md` | No security surface is known yet. |
| `docs/DEPLOYMENT.md` | No deployment deliverable is known yet. |
| `docs/CONTRIBUTING.md` | Single contributor; `AGENTS.md` covers the working rules. |

### Rationale

The system stays minimal but complete for the current state: **instructions**
(`AGENTS.md`) govern behavior, a **plan** (`PLAN.md`) coordinates work, a
**requirements record** (`REQUIREMENTS.md`) defines the target and how acceptance will be
verified, **decision records** preserve reasoning, and the **README** makes the repo
understandable to a human. Architecture and testing documentation are intentionally
absent because architecture and tests are intentionally absent.

### Consequences

- When the specification arrives, `REQUIREMENTS.md` is populated with real `REQ-NNN`
  entries and `PLAN.md` gains implementation milestones — no new structure is needed.
- `ARCHITECTURE.md` and `TESTING.md` are created on first real use, at which point the
  README's ownership table and `AGENTS.md` §7 tree must be updated to match.
- If the assignment turns out to be very small, architecture detail may live in the
  README instead of a separate file, and `ARCHITECTURE.md` stays deferred.

---

## DEC-002 — Choice of task: IPP task 1, plasma shape from magnetic measurements

**Date:** 2026-10-23
**Status:** Accepted
**Category:** Scope

### Context

The organizers offered five tasks: IPP 1 (plasma shape), IPP 2 (runaway electrons from synthetic
infrared images), DCUK 1 (Ústí Region municipalities), DCUK 2 (air quality), DCUK 3 (Elbe level and
flow). All data together are under 1.4 GB; the only large item is the 876 MB camera archive of IPP 1.
The team has one day (to Sat 14:00), two people, and a presentation of 7 minutes plus a video.

### Alternatives considered

| Option | Assessment | Outcome |
|---|---|---|
| IPP 1, magnetic data first | Objective metrics; a baseline in hours; many bonus findings; 37 MB of data; a clear story (minutes to milliseconds) | **Chosen** |
| DCUK 3, Elbe forecast | Room for a live application; results harder to measure objectively; 172 MB plus 84 MB weather | Runner-up |
| IPP 2, runaway electrons | Image network on four datasets of increasing difficulty; heavier training | Rejected for time |
| DCUK 1, DCUK 2 | Open-ended; the result depends on the insight more than on measurable quality | Rejected |

### Decision and consequences

Work on IPP 1: magnetic route first, required analyses and bonuses next, the camera model last.
None of the tasks needs a language model API. The raw data stay outside the repository (CON-001).

---

## DEC-003 — Evaluation protocol and baseline for IPP 1

**Date:** 2026-10-23
**Status:** Accepted
**Category:** Correctness

### Context (measured with `analysis/ipp1_eda.py`)

`equil_data.csv` has 42,972 rows from 149 discharges (17 to 439 rows each), 24 inputs
(`IPR01-16`, `FL01-08`) and 31 targets. Rows of one discharge are near copies. 44.2 % of rows are
limited (no X-point or strike points), 55.8 % divertor (no limiter point). Target spreads are small
(for example 8 mm for `R_mag_axis`). Two principal components carry 92.8 % of the input variance,
five carry 99.93 %. Elongation and triangularity lie on one narrow curve.

### Decision

1. Split by whole discharges (`GroupKFold`, 5 folds, grouped by `discharge`); never by rows (CON-002).
2. Train with a masked loss so structurally missing targets are ignored, and report each target only
   on the rows where it exists. `is_limited` is predicted as a 0/1 output.
3. Report errors in physical units (mm, kA) and relative to the spread (nRMSE), plus R squared.
4. Baselines: ridge regression and a small multi-output neural network (256, 256, 128 units, SiLU,
   AdamW, one-cycle schedule); measure inference latency per sample on CPU.

### Consequences

Scores are honest but vary by fold; all five folds are reported. Raw R squared alone would hide
millimetre-level errors, hence the physical units. Results: see the notebooks and
`docs/PLAN.md` IMPL-3 once recorded.
