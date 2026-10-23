# Hackathon

> **Status: pre-specification.** The assignment specification has not yet been supplied,
> so this repository contains no solution, no source code, and no project description.
> Inventing any of those would be fabrication. This README will be rewritten once the
> actual problem is known.

## Purpose

This repository is the delivery target for a hackathon assignment
(`github.com/mschiller890/hackathon`). It exists to hold the engineering workflow, and
eventually the implementation, for that assignment.

Right now its only job is to be **ready to receive the specification** and to make the
working method explicit before any code is written.

## What is here

| Path | What it is |
|---|---|
| [`AGENTS.md`](AGENTS.md) | The engineering workflow. Read this first — it governs all work in this repo. |
| [`README.md`](README.md) | This file. The human entry point. |
| [`docs/PLAN.md`](docs/PLAN.md) | The task tracker. What work remains and what is done. |
| [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) | Requirement IDs and traceability. Empty until the spec arrives. |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Why significant choices were made. |

There is **no** `src/`, `tests/`, or `docs/ARCHITECTURE.md` yet. They are created only
when the assignment provides something real to put in them.

## Setup and usage

Nothing to install or run — there is no code and no build system. No language, framework,
or dependency has been chosen, because the problem that would justify the choice is
unknown.

When a stack is chosen, its setup, run, and test commands will be documented here, with
verification detail in `docs/TESTING.md`.

## How to work in this repository

Read [`AGENTS.md`](AGENTS.md) in full first. In short:

1. Inspect the repo before changing it (`AGENTS.md` §1).
2. Do not design until the problem is understood (§2).
3. Track all work in [`docs/PLAN.md`](docs/PLAN.md) — the single task board (§3).
4. Record requirements with stable IDs in [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md).
5. Test from requirements and failure modes, not from hope (§9).
6. Commit often and push to `main` regularly (§14).

## Documentation ownership

Each category has exactly one authoritative file. Do not duplicate detail across files —
link to the owner instead.

| Question | Authoritative file |
|---|---|
| How must the work be done? | [`AGENTS.md`](AGENTS.md) |
| What is this project? | [`README.md`](README.md) — this file |
| What work remains? | [`docs/PLAN.md`](docs/PLAN.md) |
| What must be delivered? | [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) |
| How is correctness verified? | `docs/TESTING.md` — *not yet created* |
| How does the solution work? | `docs/ARCHITECTURE.md` — *not yet created* |
| Why were choices made? | [`docs/DECISIONS.md`](docs/DECISIONS.md) |

## Known limitations

- The assignment specification is outstanding. No requirements, architecture, algorithms,
  or acceptance criteria have been established, and none should be assumed.
- No verification tooling (tests, linter, type checker) exists yet, so no verification
  claims can currently be made about this repository.
