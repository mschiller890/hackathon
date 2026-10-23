# Tidy-up report

Branch `cloud/tidy` (from `origin/main` 3b10670, rollback tag `pre-cleanup-20261023-2248` exists on origin), session of Fri 23 Oct 2026 about 23:00 to 00:30 CEST.
Static verification only: the IPP data are not in this mirror, so no analysis script, no notebook execution and no viewer build was run.
Nothing under `analysis/`, `notebooks/` or `results/` was renamed, moved or deleted. 203 tracked files before, 203 after
(+ `analysis/README.md`, `analysis/check_links.py`, `docs/README.md`, this file; minus 3 deleted).

## 1. Moves (`git mv`, commit "refactor: move internal working documents ...")

To `docs/internal/` (21): `audit.md`, `bonus-gaps.md`, `claims-audit.md`, `czech-edit.md`, `deck-visual-qa.md`, `fresh-eyes.md`,
`jury-simulation.md`, `notebook-proofread.md`, `notebook-review.md`, `plan-review.md`, `review-findings.md`, `review-findings-2.md`,
`review-findings-3.md`, `review-findings-4.md`, `review-physics.md`, `viewer-qa.md`, `WORKERS.md`, `TIMELINE.md`, `GOAL-BRIEF.md`,
`REVIEW-PLAN.md` (from `docs/`) and `BRIEF-camera.md`, `BRIEF-search.md` (from `cloud/`; the empty `cloud/` folder is gone).
To `presentation/` (3): `CHEAT-SHEET.md`, `REHEARSAL.md`, `demo-facts.md` (from `docs/`).
Total 25 renames (`git diff --name-status -M origin/main HEAD` lists 25 `R` lines).

### References updated (every tracked text file)

Exact-path replacement of each old path by the new one, by one script over `git ls-files` (53 files in the commit). Where it mattered:

| File | Change |
|---|---|
| `analysis/check_claims.py` | `AUDIT` now `docs/internal/claims-audit.md` (also the usage line). Run once: it wrote the file at the new path; that output was discarded with `git checkout` because the committed audit is stale against the generator (see section 5). |
| `analysis/make_chatgpt_brief.py` | reads `presentation/CHEAT-SHEET.md` (the path was built as `ROOT / "docs" / "CHEAT-SHEET.md"`, so text search missed it) |
| `analysis/build_drill_cards.py` | reads `presentation/REHEARSAL.md`, `docs/internal/review-physics.md`; docstring and the `src` strings it writes |
| `presentation/drill-cards.json`, `presentation/CHATGPT-BRIEF.md` | `src` / "Zdroj" lines: rerunning `build_drill_cards.py` and `make_chatgpt_brief.py` reproduces exactly the sed result (checked: 34 changed lines each side, paths only) |
| `analysis/ipp1_claim_support.py`, `ipp1_confidence.py`, `ipp1_unusual_heldout.py`, `ipp1_unusual_shapes.py`, `synth_validation.py`, `presentation/deck/build_deck.py` | one docstring or comment path each |
| `notebooks/07_...`, `notebooks/10_...` | one markdown line each (1 line changed per file, outputs untouched; `check_notebooks.py` 0 FAIL) |
| `results/ipp1-camera-local-findings.md`, `ipp1-claim-support.md`, `ipp1-limiter-swap.md`, `ipp1-unusual-shapes.md`, `synthetic-validation.md` | one line each (a path in prose; `numstat` 1/1) |
| `README.md`, `CLAUDE.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/REQUIREMENTS.md`, `docs/PLAN.md`, `docs/deck-fixes.md`, `docs/claims-corrections.md`, `viewer/README.md`, `presentation/pitch-script.md`, `presentation/REHEARSAL.md` | path prefixes; `docs/PLAN.md` also the bare `WORKERS.md` etc. now `internal/WORKERS.md` and the link `(internal/WORKERS.md)` |
| moved files | only path prefixes inside them, plus relative links that would break one folder deeper: `TIMELINE.md` and `WORKERS.md` links to `PLAN.md` / `REQUIREMENTS.md` became `../PLAN.md` / `../REQUIREMENTS.md`, `../AGENTS.md` and `../README.md` became `../../...`. History text was not rewritten. |
| `CLAUDE.md` | the pointer "README.md ('Setup and run')" became "('Run it')" because the rewritten README has that heading |
| `AGENTS.md`, `docs/DECISIONS.md` | `docs/ARCHITECTURE.md`, `docs/TESTING.md`, `docs/ISSUES.md` and the rejected-documents table named files that never existed; written without the `docs/` prefix so they are not mistaken for paths. In `AGENTS.md` "analysis/refinement" became "analysis and refinement" (same reason). |

`.gitignore` held no moved path and needed no change. No `.html` file referenced a moved path (`grep` over `viewer/index.html`,
`presentation/drill-page.template.html`: no hit).

## 2. Deletions (commit "chore: delete the applied README proposal, the old handout PDF and the hidden-slides deck PDF")

Evidence: `git grep -n -I -F <name>` over every tracked file, run after the README rewrite.

| Deleted | References left | Verdict |
|---|---|---|
| `docs/README.proposed.md` | `docs/PLAN.md:80` (FRESH-1 row), `docs/internal/fresh-eyes.md` lines 5, 43, 110 (the review that wrote it) | history only; the proposal is applied in `README.md` |
| `presentation/handout.pdf` | `docs/PLAN.md:48` (IMPL-HO row, history), `docs/internal/fresh-eyes.md:34`, `docs/README.proposed.md` (deleted with it) | no script, doc or notebook uses it; `analysis/make_pdf.py` can rebuild it from `docs/HANDOUT.md` |
| `presentation/deck/slides-all.pdf` | `docs/PLAN.md:55` (PDF-1 row, history), `presentation/deck/PDF-NOTES.md` (describes how it was made) | `PDF-NOTES.md` got one sentence saying the file was removed and how to make it again; `slides.pdf` and `slides.pptx` stay |

Candidates in `analysis/`, `notebooks/`, `results/` that were checked and **kept**: a recursive search for the file name found no reference outside `docs/PLAN.md` and `docs/internal/` for
`build_drill_cards.py`, `failure_gallery.py`, `ipp1_final_seeds.py`, `ipp1_inputs_ranking.py`, `ipp1_latency_cache.py`, `ipp1_signcanon.py`,
`make_chatgpt_brief.py`, `make_read_aloud.py` (and `cloud_search_lib.py`, `ipp1_learning_curve.py`, `ipp1_temporal.py` are only imported or named by other scripts).
All of them write a tracked output (`presentation/drill-cards.json`, `presentation/assets/failure-*`, `results/ipp1-final-seeds.md`, `ipp1-inputs-ranking.md`,
`ipp1-latency-shipped.md`, `ipp1-signcanon.md`, `presentation/CHATGPT-BRIEF.md`, `presentation/READ-ALOUD.md`, ...), so deleting the script would orphan the file it produced. They are listed in `analysis/README.md`.
Every file under `results/` and `notebooks/` is named by at least one other tracked file. No deletion was made there.

## 3. README and indexes (commit "docs: rewrite README ...")

`README.md` is the proposal of `docs/internal/fresh-eyes.md` (154 lines down to 98), with these adaptations: notebook table has 10 rows (the proposal knew nine;
notebook 10 is the simulated-plasma test and needs no IPP data), `handout.pdf` is gone from the text, the deck PDF is named with its 12 pages, a "shipped model without torch" bullet
and the `fetch_wall.py` pointer were kept from the old README, the Files table names the new folders, and a short repository tree is at the end.
`docs/README.md` (15-line index) and `analysis/README.md` (one table: pipeline rows in `make_all.py` order, libraries, experiments with their `results/` file, tools) are new.
The `results/` file names in `analysis/README.md` were checked against `git ls-files results`; the script list against `git ls-files analysis` (no script missing, none unknown).
`analysis/check_links.py` (stdlib only, 56 lines including the docstring) is new.

## 4. Verification (run on the final tree)

```
$ python3 analysis/check_links.py
0 dangling references (172 distinct paths checked)          exit 0
$ python3 -m compileall -q analysis presentation viewer     exit 0
$ python3 analysis/check_notebooks.py
10 notebooks, 0 FAIL, 0 WARNING                              exit 0   (nbformat installed with pip for this run)
```

The same script (final version) on a checkout of `origin/main` reports 15 dangling references: 10 are in `AGENTS.md` and `docs/DECISIONS.md` (nine never-created documents and `analysis/refinement`; fixed, section 1), and the other 5 sit in files that are now in `docs/internal/` or in the proposal (`analysis/make_all.sh`, `presentation/video-plan.md`, `results/ipp1-camera-findings.md` and a notebook name that `WORKERS.md` and `TIMELINE.md` announced and nobody wrote; `docs/internal` named in `fresh-eyes.md` before it existed). Section 5 lists what it skips and why.
Also run: `presentation/timing.py` (still reads `pitch-script.md`: "total written 420 s (7:00)"), `analysis/make_read_aloud.py` (output identical to the committed `READ-ALOUD.md`),
`analysis/build_drill_cards.py` and `make_chatgpt_brief.py` (see above), `analysis/check_claims.py` (runs, finds its new path), and
`python -I analysis/make_submission.py --out <new folder>` on `origin/main` and on this branch: both end with "FAILED CHECKS: none" and list the same missing items
(model files, video); the package contents differ only in the files with changed paths and in the new `check_links.py`.

## 5. What `check_links.py` skips, and what I did not dare to change

`check_links.py` does not scan `docs/PLAN.md` and `docs/internal/` (history of the work, as the task allowed for the PLAN), skips globs and placeholders, git-ignored paths,
abbreviations that begin a real file name (`notebooks/01`), and a `.png`, `.pdf` or `.pptx` path that a tracked `.py` file names (figures the scripts write but the mirror does not hold:
`results/cloud-search-pareto.png`, `-targets.png`, `-noisy.png`, `results/ipp1-camera-v2-occlusion.png`, `presentation/slides.pdf` inside `make_submission.py`).
It also lets `results/cloud-search-findings.md` pass (an optional hand-written input, read only if present). It checks paths with the six prefixes only: a bare file name or a path built in code
(`ROOT / "docs" / "X.md"`) is not seen, so I searched for the bare names of all moved files by hand (section 1).

Not changed, on purpose:

- **`docs/deck-fixes.md`** is in neither of your lists. It is an open to-do list for the deck owner and is still in use, so it stays in `docs/` and is indexed in `docs/README.md`. If it is internal, one `git mv` moves it (its own references are already correct).
- **Bare file names in prose**: `presentation/CHEAT-SHEET.md`, `CHATGPT-BRIEF.md` and `drill-cards.json` say "zdroje: claims-corrections.md, review-physics.md, ipp1-traintest-gap.md" without a folder, and `[demo-facts.md]` in the same files. They are not paths and the names are unique, so I left the Czech speaker text alone.
- **`docs/internal/claims-audit.md`** is stale against its generator: running `check_claims.py` now gives 452 claims in the pitch script against 298 in the committed file (the pitch script changed after the last run). I restored the committed file; the Lead should rerun `python -I analysis/check_claims.py` after the results freeze and commit the new audit.
- **`results/`, `notebooks/` content**: only the single path line listed in section 1 changed; no number, output or figure was touched.
- **`README.md` still says `Team: DOPLNIT (owner)`**: the team name is unknown to me and was a placeholder in the proposal. The owner must fill it in or delete the sentence before the hand-in.
- **`docs/PLAN.md` history rows** (IMPL-HO, PDF-1, FRESH-1) still name the deleted files as they were at the time; one new row, TIDY-1, records this tidy-up.
- **Package README**: `make_submission.py` copies `README.md` into the package, whose links to `docs/` do not resolve there. This was already so before the tidy-up and I did not change the package builder.
- **Branch name**: the session instructions named `claude/nifty-hypatia-31sy0m`; your task named `cloud/tidy` and said to push only that branch, so I followed the task.
