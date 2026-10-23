# Fresh eyes: the repository as a stranger sees it

Reviewer role: an IPP physicist with 10 minutes who has never seen this repository and starts only from `README.md`.
Mirror: `main` at `d184205` (167 commits, 174 tracked files, 30 in `docs/`), read Fri 23 Oct 2026 20:20 to about 20:30 CEST on branch `cloud/fresh-eyes`.
Nothing was moved or edited except this file, `docs/README.proposed.md` and one `docs/PLAN.md` row. No raw data in this mirror.

**Two kinds of times below.** "Clock" is what my session measured (CEST; exact for commands, approximate for the reading steps, which overlapped). "Stranger" is an **estimate** for a human, not a measurement: README reading at 250 words per minute (1,674 words), other files at the same rate, a click and a skim at 20 to 30 s each.

## Verdict in five lines

1. The content is honest and the numbers agree across README, handout, outline and `results/` (I checked 0.133, 0.307, 0.23, 0.397, 1.20, 2.38, 9.16 mm in `results/ipp1-final.md`). The loss of time is all in **navigation**, not in substance.
2. The README is 154 lines and 1,674 words: about **7 of the 10 minutes** just to read it, and the headline number sits in its third paragraph, mixed with four protocols and three model names.
3. The README is **stale on the notebooks**: it says five, the folder has nine; notebooks 06 to 09 are never named and no document gives a reading order.
4. The **demo cannot be opened** without the data, and nothing near the viewer link says so (a stranger gets one Czech error line).
5. The **handout is not mentioned** in the README; the talk and the slide titles are Czech without a warning.

## Log: the 7 questions, step by step

| Clock | Stranger | Step | Result |
|---|---|---|---|
| 20:20:57 | 0:00 | `git fetch origin main`, new branch from `origin/main` | `d184205`, 167 commits |
| 20:21:01 | 0:00 | Open `README.md` | 154 lines, 1,674 words, longest line 385 characters, 3 lines with internal IDs (`IMPL-8`, `RP-1 to RP-14`, `audit R-1`) |
| 20:21:06 | 2:00 | **Q1 task and what the team did.** First paragraph answers the task (plasma shape, minutes against a fraction of a millisecond). "What the team did" needs paragraph 3. | Answered in about 2 min. First dead end: "Current status (Fri 23 Oct, after the independent review and the audit) ... notebooks in progress". A stranger cannot tell if this is finished. |
| 20:21:06 | 4:30 | **Q2 main result.** Paragraph 3 ("Shipped model and headline number"): 0.133 mm on 30 set-aside discharges, then in the same paragraph 0.23, 0.397, 1.23, 0.448, 0.035, 1.20, 2.38, 9.16. | Found, but 14 numbers and 5 protocols in 12 lines. Units are present (mm, kA), the protocol is present, the one sentence "the 30 are not never seen" is honest and good. Time to a clean "single number": about 2.5 min after the first paragraph. |
| 20:21:19 | 5:30 | **Q3 notebooks.** README table row: "Five Jupyter notebooks with stored outputs (data, baseline, inputs, stability over time, latency)". `ls notebooks/` shows nine. | **Stale.** Notebooks 06 camera, 07 distribution and unusual shapes, 08 robustness and data amount, 09 final model on the locked test are not in the README. I opened all nine with a script: every code cell has a stored output (01: 11 of 11, 06: 13 of 13, 09: 12 of 12, etc.). No file gives a reading order. The main result lives in **09**, the last one by number. |
| 20:21:32 | 6:00 | **Q4 how to run.** README "Data (not in this repository)" and "Setup and run". | Data absence is stated clearly, with the folder layout. The way to get them: "the organizers' Drive (participants only)", no link. An IPP physicist has them; an outside jury member does not (fine, but say so). Then a 3 line paragraph about a **sha256 with 62 of 64 hex digits** (an internal defect note, useless to a stranger). |
| 20:21:45 | | Run the README setup (`uv venv --python 3.12`, `uv pip install ...` without torch) | `uv venv` 0.3 s; packages 1 min 38 s. Works as written. (torch skipped; see below.) |
| 20:23:53 | | `python -I analysis/make_all.py --quick --notebooks` with no data | One clear line: "set HACKATHON_HOME to the folder that holds data/raw (see README.md)". Good message. |
| 20:23:55 | | `nbconvert --execute notebooks/02_baseline_models.ipynb` | `NoSuchKernel: hackathon`. The README says to install the kernel, but a stranger who opens a notebook first gets a traceback. |
| 20:23:30 | | `nbconvert --execute` notebooks 06, 07, 08 in the fresh venv, no data | **All three run: 06 in 9 s, 07 in 6 s, 08 in 5 s** (kernel `python3`, they read only committed `results/` and call `git ls-files`, so they need a git clone). This is the only thing a stranger can really re-run, and **the README says the opposite**: "Every other script and the five notebooks need the data". |
| 20:24:03 | | `analysis/make_submission.py --out <new folder>` (no data) | Works, "FAILED CHECKS: none". It also warns of two `/Users/` paths in `results/` and lists figures the owner must confirm against CON-001 (see finding 12). |
| 20:24:15 | 7:00 | **Q5 limits.** README "How to read the numbers" (after the headline) and `docs/HANDOUT.md` "What we did NOT show". | Found in about 1 min; they are honest and specific (labels are the institute's own reconstruction; means against median 0.15 mm; random folds optimistic, 1.5 to 2.9 times worse on later ids; noisy inputs; drift only synthetic; real time only the network). In the README they come as bullets inside a numbers block, in the handout as a clean list. The handout version is better. |
| 20:24:44 | 8:00 | **Q6 demo.** README row "`viewer/` Single-file browser viewer ... needs the data to build". Open `viewer/index.html` in Chromium (headless, file://). | **Dead end.** The page shows only "Chybí soubor data.js. Vytvoří se příkazem analysis/export_viewer_data.py." (Czech; screenshot checked). `viewer/dist/index.html` is gitignored because it embeds IPP data. Not stated near the link. Four stills (`presentation/assets/viewer-*.png`) and six failure stills (`failure-*.png`) exist and **are not pointed to** from the README. Build with data: `make_all.py --quick --missing --viewer`, 650 s (PLAN RP-15). |
| 20:24:15 | 9:30 | **Q7 talk and handout.** README: "`presentation/` Outline, pitch script, glossary and the deck (`deck/slides.pptx`)". | The deck is a 7.5 MB `.pptx`, 14 slides, titles in Czech (PROBLÉM, DATA, METODA ... CO MODEL NEUMÍ); GitHub does not render it and no PDF is committed (`docs/SUBMISSION.md` says the PDF is missing). `outline.md` (142 lines) and `pitch-script.md` (466 lines) are Czech, not marked as Czech. The **handout** (`docs/HANDOUT.md`, English; `docs/HANDOUT.cs.md`, Czech; `presentation/handout.pdf`, 72 KB, English) is **not mentioned in the README at all**; I found it only by `ls docs/`. It is the best one-page answer to Q1, Q2 and Q5 and should be the first link. |
| 20:25:20 | 10:00 | Budget used up. | Q1, Q2, Q5 answered; Q3 answered wrongly (five); Q4 half; Q6 failed; Q7 half. |

## Findings, ranked by how much time a stranger loses

Time is the estimate for a stranger, per finding. "Fix" is what the proposed README or the owner can do.

| # | Finding | Time lost | Fix |
|---|---|---|---|
| 1 | **README is too long and has no summary.** 154 lines, 1,674 words, about 7 min of 10. The first screen is two dense paragraphs; the single headline result is the third. A stranger reads 14 numbers and 5 protocols (random 5-fold, 30 set aside, 119 dev 5-fold, blocked ids, noisy) before knowing which is "the" result. | about 5 min | `docs/README.proposed.md`: 10 line summary, one main result with its protocol, the other protocols as one line. |
| 2 | **README is stale on notebooks.** Says "five" in the structure table, in "Setup and run" ("the five notebooks"), in the make_all paragraph ("executes the five notebooks"), and in the timing table ("five notebooks 2 min"). There are nine. `make_all.py --notebooks` does run all nine (`sorted(glob("*.ipynb"))`), so the text is also wrong about what the command does. Notebooks 06 to 09 are never named. No reading order. The main result is in 09. | about 3 min, and a wrong picture of the work | Table with the order in the proposal (01, 02, 09, 03, 04, 05, 07, 08, 06). |
| 3 | **Demo cannot be opened without the data, and this is not said at the link.** `viewer/index.html` is committed but empty without `data.js`; the error line is Czech. The committed stills are not referenced. A stranger loses the demo entirely. | about 2 min and the demo itself | Say it in the README next to the viewer, point to the stills; optionally commit a 15 s clip or a GIF made from non-confidential statistics only (owner decides under CON-001). |
| 4 | **Handout not mentioned; talk is Czech and unflagged; no PDF of the deck.** The one-page summary is the best entry point and is invisible. `.pptx` is not previewable on GitHub. | about 2 min | Link the handout first; say "(Czech)" after deck, outline, pitch; commit `slides.pdf` if the owner agrees (SUBMISSION already lists it as missing). |
| 5 | **Two models, five names.** "baseline network", "basic network" (handout, outline), "candidate" / "`cand`" / "shipped model" / "selected model" (handout) / "vybraný model" (viewer). README uses "baseline network" and "shipped" in one sentence. | about 1.5 min of re-reading | Pick two: "basic network" and "shipped model"; state once that `cand` is the code name. |
| 6 | **`docs/` is mostly internal chatter (25 of 30 files).** README links `docs/review-findings.md`, `docs/PLAN.md` (12,379 words; table rows run to thousands of characters), `docs/WORKERS.md`. A stranger who clicks lands in agent lanes, gate lists, "Fri 22:00 to Sat 02:30" timelines and an overnight `/goal` prompt. | about 2 min per click, and a loss of trust | Move to `docs/internal/` (list below); the proposal links only HANDOUT, REQUIREMENTS, DECISIONS. |
| 7 | **Internal status text in the README.** "after the independent review and the audit", "Notebook 04 stopped with `KeyError` ... fixed in `b7f5011` ... not yet re-run on a second machine", "RP-1 to RP-14", "audit R-1", "on the owner's Mac", "shared machine, load average 5.7 and 7.0", the 62-digit sha256 paragraph, "Agents and contributors: read CLAUDE.md". `CLAUDE.md` itself starts with "Start here (Claude Code sessions)" and "Lane K, the colleague's Claude: ask your user for the link". | about 1 min | Delete from the README; keep in PLAN. Mention `CLAUDE.md`/`AGENTS.md` once, last, as assistant instructions. |
| 8 | **README says the notebooks need the data; three do not.** 06, 07, 08 run in 5 to 9 s from the committed `results/` (verified). They need a git clone (`git ls-files` check); a ZIP download without `.git` is untested. Kernel names differ: 01 to 05 and 09 want `hackathon`, 06 to 08 use `python3`. | about 1 min, and the only runnable proof is hidden | Proposal "Run it" lists both paths. |
| 9 | **How to get the data is half a sentence.** "the organizers' Drive (participants only)" with no link; the zip name and size are given. Fine for IPP, a dead end for anyone else. | about 1 min | One sentence saying so (done in the proposal). |
| 10 | **Stale or mismatched internal facts a stranger can trip on.** `docs/SUBMISSION.md` says "5 `.ipynb`" and "`presentation/slides.pptx`" (the deck is `presentation/deck/slides.pptx`); `docs/REHEARSAL.md` says the viewer shows the basic network while `viewer/README.md` and `docs/demo-facts.md` say it shows the shipped model (PLAN KQ-20 already knows); PLAN has duplicate IDs IMPL-13, IMPL-16, IMPL-20 (KQ-17). | seconds each, but each one is a doubt about the rest | Fix when moving to `docs/internal/`; they do not matter once hidden. |
| 11 | **README latency line quotes a re-implementation.** "0.015 to 0.027 ms for the shipped model" is the numpy path; the `predict()` that produced the scores has medians 0.026 and 0.054 ms (`results/ipp1-latency-shipped.md`). Both are far below 1 ms, so the verdict does not change, but the README does not say which path was scored. | about 30 s for a careful reader | One clause, or quote both. |
| 12 | **Confidentiality exposure a stranger could notice.** `make_submission.py` itself asks the owner to confirm viewer stills, `results/ipp1-time.png`, `ipp1-unusual-shapes.png`, notebook 01 cell 14 and notebook 04 cell 11 (true traces of single discharges) against CON-001 before the package is public. Two `results/*.md` contain absolute `/Users/` paths. The repo is private today, and the claim in the README that no raw data are in git is what the script checks; I did not judge the figures. | not time, but a risk | Owner decision before any public link. |
| 13 | **Small things.** `docs/REVIEW-PLAN.md` and `presentation/pitch-script.md` begin with Obsidian front matter (`tags: - hackathon`), which GitHub renders as a table; no licence file; no team names or repository URL in the README; `results/` has 52 files with no index (the proposal points to `ipp1-final.md`); the README gives no commit or date stamp for its numbers. | seconds each | One line each. |

## Where the README is stale, misleading, too long, or points at files that do not exist

Link check (script, 20:21:06): all 8 relative links resolve (`AGENTS.md`, `CLAUDE.md`, `docs/PLAN.md`, `docs/REQUIREMENTS.md`, `docs/WORKERS.md`, `docs/review-findings.md`, `results/`, `results/ipp1-final.md`), and about 20 further file names written in code spans resolve (`analysis/*.py`, `viewer/*`, `presentation/deck/*`, `docs/SUBMISSION.md`, `docs/audit.md`, `docs/claims-audit.md`, `results/*.md`). **No broken links and no missing files.** The external `docs.astral.sh/uv` link was not fetched.

| README place | Problem | Kind |
|---|---|---|
| Opening paragraph | "median 0.0145 ms per sample for the baseline network, 0.015 to 0.027 ms for the shipped model" before either model is defined | misleading order |
| "Current status (Fri 23 Oct 2026 ...)": "notebooks in progress" | Nine notebooks, all with stored outputs; the line is a time-stamped status in a front page | stale |
| Paragraph "Shipped model and headline number" | 12 lines, 14 numbers, 5 protocols, 3 models | too long |
| Bullet list "How to read the numbers" | Real-time bullet is 9 lines; "Apple M5 on a shared machine" repeated 3 times | too long |
| "Agents and contributors" | Instructions for assistants on the front page | internal |
| "Data" section, sha256 paragraph | Documents a defect of an internal note | internal |
| Structure table: "Five Jupyter notebooks ..." | Nine | **stale** |
| Structure table: `docs/ (other files)` "Reviews, audit, claims corrections, submission checklist, timeline, worker lanes" | Describes internal chatter as if it were documentation; omits the handout | misleading |
| Structure table: `cloud/` "Briefs for the two cloud sessions" | Internal | internal |
| "Setup and run": "the five notebooks need the data" | 06, 07, 08 do not | **wrong** |
| make_all paragraph: "executes the five notebooks", timing table "five notebooks 2 min" | Runs nine; time not re-measured with nine | stale |
| make_all paragraph: "Notebook `04` stopped with `KeyError: 'is_limited'` ... fixed in `b7f5011`, not yet re-run" | Process note; `b7f5011` exists (checked) but the re-run is not recorded | internal |
| "Notes from the second-machine check (RP-1 to RP-14)" | Useful install facts (CPU torch, versions) buried in a work log | too long |
| Whole file | No pointer to the handout, to the stills, to the Czech language of the talk | missing |

## `docs/` files that read as internal chatter: proposal for `docs/internal/`

Do not move anything yet: inbound references from other files are counted (any `.md`, `.py`, `.ipynb`, `.json`), so the owner can see the breakage. `docs/PLAN.md` and `docs/WORKERS.md` are named in `AGENTS.md` and `CLAUDE.md` as authoritative paths; moving them means editing those two files, so the safer option is to **leave them in place and stop linking them from the README**.

| File | Why a stranger is confused | Inbound refs |
|---|---|---|
| `docs/GOAL-BRIEF.md` | An overnight `/goal` prompt for the owner's Claude session | 3 |
| `docs/TIMELINE.md`, `docs/REVIEW-PLAN.md`, `docs/plan-review.md` | Hour by hour plan, review gates G1 to G7 | 4, 4, 2 |
| `docs/WORKERS.md` | Lanes for agents and students (leave in place, see above) | 13 |
| `docs/REHEARSAL.md`, `docs/CHEAT-SHEET.md` | Run sheet of the live demo, drill questions, the speakers' crib sheet | 8, 1 |
| `docs/deck-fixes.md` (306 lines), `docs/deck-visual-qa.md`, `docs/viewer-qa.md` | Fix lists for the slides and the viewer | 10, 2, 2 |
| `docs/notebook-proofread.md` (418 lines), `docs/notebook-review.md` | Patch lists for the notebooks | 1, 3 |
| `docs/review-findings.md`, `review-findings-2.md`, `review-findings-3.md`, `review-physics.md`, `jury-simulation.md`, `bonus-gaps.md` | Reviews written by other agents about this work; `review-findings.md` is linked from the README as a source of numbers | 20, 13, 6, 7, 1, 5 |
| `docs/claims-corrections.md` (204), `docs/claims-audit.md` (229), `docs/audit.md` (311) | Wording rules and audits for the claims | 15, 9, 12 |
| `docs/demo-facts.md`, `docs/SUBMISSION.md`, `docs/hackathon-rules.md` | Pitch crib numbers, the hand-in checklist (says "5 notebooks"), rules research | 8, 8, 2 |
| `docs/PLAN.md` | The task tracker, 12,379 words, rows of thousands of characters (leave in place, see above) | 28 |
| `cloud/BRIEF-camera.md`, `cloud/BRIEF-search.md`, `presentation/rehearsal-notes.md` | Prompts for the cloud sessions, a rehearsal log | n/a |

Keep in `docs/`: `HANDOUT.md`, `HANDOUT.cs.md`, `REQUIREMENTS.md`, `DECISIONS.md`, `related-work.md`. One README line for the new folder: "`docs/internal/` working notes of the team and its assistants (plans, reviews, audits, rehearsal); not needed to understand the result."

Because `claims-corrections.md` and `review-findings*.md` are referenced from `results/`, `docs/` and the notebooks, the move is a 20 to 40 minute job with a link check (the same script I used: every `](path)` and every code span path must still exist). My recommendation: **do it after the freeze, or not at all**, and for now only change the README (the proposal does that), so no link can break in the last hours.

## What I could not check

- Notebooks 01 to 05 and 09 and `make_all.py` with data (no data in this mirror); only their stored outputs, first cells and the error messages without data.
- The viewer with data and the 14 slides rendered (read slide titles only); `analysis/make_pdf.py` and `viewer/record.py` (README itself says untested).
- A ZIP download without `.git` for notebooks 06 to 08 (they call `git ls-files`, so I expect a failure; not tested).
- The `uv` link, and the organisers' Drive.
- Whether the Czech talk text is correct; I read titles and structure only.

## How the proposal answers the 7 questions

`docs/README.proposed.md` is 79 lines (the limit was 120): summary in 10 numbered lines (1 task and what was done, 4 the single result with protocol and units, 9 the handout), then "How to read this repository" with the notebook order, "Run it" (with and without data, and the demo), "Limits", "Files". Every number in it is taken from `results/ipp1-final.md`, `results/ipp1-latency-shipped.md`, the handout or the current README; nothing is new. The only invented item is the placeholder "Team: DOPLNIT (owner)". The owner of the README applies it; I did not edit `README.md`.
