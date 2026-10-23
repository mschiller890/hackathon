# Requirements and Traceability

**Authoritative requirements record for this repository.** Process rules live in
[`../AGENTS.md`](../AGENTS.md) (§2, §6).

## Status: SPECIFICATION OUTSTANDING

**Zero requirements are recorded, because the assignment specification has not been
supplied.** This is deliberate. Fabricating requirements — or leaving placeholder rows
that imply requirements exist — would misrepresent the project's state.

This document currently defines **how** requirements will be tracked. It is populated
when the specification is read.

## How requirements will be recorded

Each substantive requirement receives a stable identifier once the specification
supplies it.

### Identifier scheme

- `REQ-NNN` — a requirement, numbered in the order it appears in the specification.
- `ASM-NNN` — a confirmed assumption we adopted where the specification was silent.
- `OQ-NNN` — an open question requiring clarification or a decision.
- `CON-NNN` — a constraint or restriction imposed by the specification or environment.

### Traceability fields

| Field | Meaning |
|---|---|
| ID | Stable identifier (`REQ-001`, …). Never reused or renumbered. |
| Requirement | What must be delivered. |
| Source | Location in the specification text. |
| Priority | Grading significance, if the specification indicates it. |
| Acceptance criteria | The observable conditions that make it satisfied. |
| Implementation | Component or file that satisfies it. |
| Tests | Tests exercising it. |
| Evidence | The verifiable output proving it passes. |
| Status | `TODO` · `IN PROGRESS` · `BLOCKED` · `DONE`. |
| Limitations | Known gaps, degraded cases, or caveats. |

### Classification

Every item is classified so a reader can tell what is certain:

- **Confirmed requirement** — stated in the specification.
- **Assumption** — inferred where the specification was silent, and recorded as `ASM-NNN`.
- **Proposed improvement** — our suggestion, not a requirement.
- **Open question** — unresolved; recorded as `OQ-NNN`.

### The completion rule

**A requirement is never `DONE` because code appears to implement it.** It is `DONE` only
when its acceptance criteria are checked against evidence — a real command, a real test
result, a real measurement. This mirrors `AGENTS.md` §0 and §15.

## Requirements

_None recorded. Specification outstanding — see [`PLAN.md`](PLAN.md) blocker Q-1._

## Traceability matrix

_Populated from the table above once requirements exist. For a small assignment, the
table itself is sufficient and this section may be dropped._
