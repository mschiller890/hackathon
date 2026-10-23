# Requirements and Traceability

**Authoritative requirements record for this repository.** Process rules live in
[`../AGENTS.md`](../AGENTS.md) (§2, §6).

## Status: SPECIFICATION RECEIVED, TASK CHOSEN

Hackathon: **CVUT ML Hackathon 2026**. Five tasks were offered (two from Ústav fyziky plazmatu
AV ČR, three from Datové centrum Ústeckého kraje). The team chose **IPP task 1, "Určení tvaru a
pozice plazmatu z magnetických měření a ze snímků z ultrarychlé kamery"** (plasma shape and
position from magnetic measurements and fast camera images, tokamak COMPASS); see
[`DECISIONS.md`](DECISIONS.md) DEC-002. Source text: `FJFI hackaton 2026 - úloha 1 (ekvilibrium) -
zadání.docx` (kept outside this repository, with the data). Every row below carries its source.

## Identifier scheme

- `REQ-NNN` a requirement, `ASM-NNN` an assumption, `OQ-NNN` an open question,
  `CON-NNN` a constraint. Identifiers are never reused or renumbered.
- Status: `TODO` · `IN PROGRESS` · `BLOCKED` · `DONE`. **A requirement is `DONE` only when its
  acceptance criteria are checked against evidence** (`AGENTS.md` §0, §15).

## Confirmed requirements (stated in the assignment)

| ID | Requirement | Source | Acceptance criteria | Status |
|---|---|---|---|---|
| REQ-001 | A model that determines plasma shape and position from magnetic measurements (the easier route) or from camera images (harder) | Cíle, 1 | Per-parameter errors on discharges unseen in training | IN PROGRESS |
| REQ-002 | Assess whether the model could run in real time (reaction in units to tens of milliseconds); GPU may be assumed | Cíle, 2 | Measured latency per sample and a written verdict | TODO |
| REQ-003 | Evaluate accuracy for each shape parameter and the stability of the outputs during the time evolution of the plasma | Cíle, 3 | Table per parameter and a plot over a discharge | TODO |
| REQ-004 | Show how success changes with fewer inputs (fewer magnetic measurements or a smaller part of the image) and whether some inputs matter more | Cíle, 4 | Accuracy against the set of removed inputs; importance ranking | TODO |
| REQ-005 | Jupyter notebooks (Colab allowed) with the models and graphs, holding all detailed conclusions | Poznámky | Notebooks run top to bottom on a clean checkout | TODO |
| REQ-006 | A presentation summarising the results | Poznámky | Delivered; the owner states 7 minutes plus a video | TODO |
| REQ-007 | Account for the uneven distribution of parameter values in training and evaluation | Poznámky | Documented handling and its effect on the metrics | TODO |

## Optional bonus items (stated in the assignment)

| ID | Item | Status |
|---|---|---|
| REQ-B01 | A model for the second data source, or a multimodal one, and a comparison | TODO |
| REQ-B02 | Dependence of success on the number of training data | TODO |
| REQ-B03 | Effect of a black and white camera | TODO |
| REQ-B04 | Whether several consecutive times (time context) improve the output | TODO |
| REQ-B05 | Sensitivity of the camera model to camera position and rotation | TODO |
| REQ-B06 | Robustness to measurement noise and linear drift (`equil_data_noisy.csv`, or drift generated as signal + noise + random coefficient per discharge times t) | TODO |
| REQ-B07 | Which image parts or magnetic measurements the model relies on | TODO |
| REQ-B08 | Behaviour for a new, unusual shape that breaks the correlation between parameters | TODO |

## Constraints

| ID | Constraint | Source |
|---|---|---|
| CON-001 | The data were provided by ÚFP only for this hackathon. They must **not** be published or made accessible to anyone outside the participants without ÚFP's permission. Raw data never enter this repository | Dataset section |
| CON-002 | Train and test must be split by whole discharges (column `discharge`), not by rows | Poznámky |
| CON-003 | Columns `time` and `discharge` only index the rows and are not model inputs | Dataset section |
| CON-004 | No graphical user interface is required | Poznámky |

## Assumptions

| ID | Assumption | Basis |
|---|---|---|
| ASM-001 | Work on the magnetic data first; the camera model is a late bonus | The assignment calls the magnetic route the easier one |
| ASM-002 | Errors are reported in physical units (millimetres, kiloampères) and relative to each parameter's spread | Target spreads are only 2 to 14 mm (measured, `docs/DECISIONS.md` DEC-003) |
| ASM-003 | The hackathon's judging weights favour presentation and functionality | Owner's statement; not confirmed by the organizers |

## Open questions

| ID | Question | Needs |
|---|---|---|
| OQ-001 | Judging criteria weights and the jury | Organizers |
| OQ-002 | Exact submission time and the length limit of the video | Organizers |
| OQ-003 | The task text allows the column `mode` as an input, but `equil_data.csv` has no such column | Organizers |
| OQ-004 | The example plotting code needs `COMPASS_stena.csv` (wall outline), which is not in either data zip | Organizers' repository |
