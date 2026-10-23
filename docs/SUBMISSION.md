# Submission plan

**Authoritative for what is delivered, in which form, in which order, and how to roll back.** Task board:
[`PLAN.md`](PLAN.md) (IMPL-16). Requirements: [`REQUIREMENTS.md`](REQUIREMENTS.md) REQ-005, REQ-006, CON-001.
No agent submits, uploads, posts or sends anything; the owner does every step in section 5 himself.

## 1. What the organizers ask for (source: `ipp-uloha1.txt`, section "Poznámky")

- "Součástí práce ale musí být např. Jupyter notebooky (lze i Google Colab) s modely a grafy, které budou obsahovat všechny
  vaše detailní závěry." So: notebooks with the models, the graphs and all detailed conclusions. No GUI needed.
- "Výstupem je prezentace, ve které shrnete své výsledky." So: one presentation.
- The data must not be published or made available to anyone outside the participants (CON-001).
- Nothing else is stated: no submission channel, no format of the presentation, no video, no length limit, no repository
  requirement. `ipp-uvodni-prezentace.txt` is the organizers' physics introduction and says nothing about handing in work.
- The 7 minutes and the video come from the owner (Assignment note), not from the organizers' text (OQ-002).

## 2. What is delivered

| Item | Form | Built from | Status on Fri 23 Oct |
|---|---|---|---|
| Notebooks | 5 `.ipynb` with stored outputs and figures (`notebooks/01` to `05`) plus `analysis/` (they import `analysis/ipp1_common.py`) | repository | present; all 47 code cells have stored outputs and no error. A clean top to bottom run on a second machine is **not** verified (IMPL-8) |
| Deck | `presentation/slides.pptx` and `slides.pdf` | `presentation/deck/slides.pptx` | pptx present, no `DOPLNIT`/TODO text left in it. **PDF missing**: no LibreOffice on this Mac, export by hand from Keynote or PowerPoint |
| Video | `video/<file>` | owner | **missing**: only the 15 s viewer clip `out/viewer-demo.mp4` exists (a clip, not the presentation video) |
| Short results README | `README.md` (project front page) and `results/*.md` + figures | repository | present; `README.md` still says "in progress", refresh after the freeze |
| Repository link | `https://github.com/mschiller890/hackathon` | git | **private**, so a link will not open logged out (see OQ-S2) |

The package holds no data: no csv, npy, zip, jpg, no camera frames. Figures are png in `results/` only. The 11 MB offline
viewer (`viewer/dist/index.html`) embeds data and is **not** in the package.

## 3. The build

```bash
cd ~/Documents/AIprogramy/hackathon/repo
git status --short            # must be clean, otherwise the package contains uncommitted files
~/.venvs/hackathon/bin/python -I analysis/make_submission.py \
    --deck-pdf <slides.pdf exported by hand> --video <final video> --zip
```

It writes `/tmp/hackathon-submission/` (and `.zip` with `--zip`), refuses to wipe a folder it did not create, and fails
(exit 1) on: a forbidden file type, a possible key or token, 20 or more comma-separated numbers in one line (a raw data
row), a notebook cell with an error output or without stored output, an absolute `/Users/` path in a notebook. It warns
on a file over 25 MB, on png outside `results/`, on a package over 100 MB, and lists what is missing. `MANIFEST.txt` in the
package lists size and a hash per file. Checked on a planted csv, key and data row: all three are caught.

**Dry run, Fri 23 Oct (committed state plus working tree):** 86 files, 10.8 MB, 5 notebooks, 35 scripts, 42 results files.
Failed checks: none. Missing: deck PDF, presentation video. Warnings: none.

## 4. Open questions for the owner (ask the organizers)

| ID | Question | Why it matters |
|---|---|---|
| OQ-S1 | **Where and how is the work handed in?** (upload form, e-mail, shared Drive folder, repository link, handed over on the day) | The text names no channel. Everything below depends on it |
| OQ-S2 | Is a repository link accepted, and is a **private** repository enough (add the organizers as collaborators) or must the link open logged out? Making it public is not our call: CON-001, and the notebooks hold figures made from the data | The checklist says "links open logged out" |
| OQ-S3 | Format and limits of the presentation (pptx, PDF, Google Slides) and of the video (length, format, size, whether a screen recording with voice is enough) | OQ-002 |
| OQ-S4 | Are the stored notebook outputs enough, or will the jury re-run them? Re-running needs the data and `HACKATHON_HOME`; the notebooks read the data from disk, so on Colab the participants' data would have to be uploaded there | REQ-005 says "run top to bottom" |
| OQ-S5 | Exact time of the deadline (the schedule says Sat 14:00; is it the hand-in or the end of presentations?) and whether presenting happens in person | Plan: hand in by 13:00 |
| OQ-S6 | Is one language fine (deck in Czech, notebooks and results in English)? | Assumed yes |

## 5. Final order of steps (after the freeze, Sat 10:00)

1. **Lead:** confirm the freeze; `git pull --rebase`, tree clean, last commit pushed. Refresh the status wording in
   `README.md` and `REQUIREMENTS.md` (still "in progress"). Optional, if time: one clean run of the notebooks in a fresh
   checkout (IMPL-8), so the claim "runs top to bottom" is evidence.
2. **Owner:** export the final deck to PDF from Keynote or PowerPoint; export or finish the video; check both play to the end.
3. **Packager (this lane, called again by the Lead):** run the build of section 3 with the two files. Read the report:
   zero failed checks, zero missing items.
4. **Owner:** unzip the package into an empty folder on another device or a clean user and open `slides.pdf`, the video and
   one notebook (outputs visible). Walk `Hackathon-Brain/06-Submission-Checklist.md` line by line (G7, 12:00 to 13:00).
5. **Owner:** keep a copy of the exact zip sent (and its `MANIFEST.txt`) outside the repository.
6. **Owner:** send by the channel from OQ-S1. Save the confirmation (screenshot or mail) next to the kept zip.
7. **Owner:** after sending, open the link or message as the receiver would, logged out where possible.

## 6. Rollback

- The package is disposable: rerun the script, it rebuilds from scratch. It only deletes a folder carrying its own
  marker file. Nothing is changed in the repository.
- A wrong file was sent: send the corrected package at once with a one-line note saying it replaces the earlier one, and
  name the file that was wrong. If the channel allows deleting an upload, delete the wrong one after the new one is in.
- Data or a key was sent by mistake (the checks make this unlikely): tell the organizers immediately and ask them to
  delete it; rotate the key. If the repository was made public by mistake: set it back to private first
  (`gh repo edit mschiller890/hackathon --visibility private`, owner only), then tell the organizers.
- The repository stays the source of truth: the sent zip can always be rebuilt from the tagged commit. Tag it when sending
  (`git tag submission-2026-10-24`, owner or Lead; do not push the tag anywhere public).

## 7. Things only the owner can do

- Decide and ask the organizers: OQ-S1 to OQ-S5.
- Record, finish and export the video; export the deck to PDF (Keynote or PowerPoint, both installed).
- Rehearse and give the 7 minute talk.
- Add the organizers (or jury) to the private repository, if a link is wanted; never make it public without their OK.
- Press send / upload / submit and save the confirmation. No agent does this.
- Approve the last wording of the claims in the deck (`docs/claims-corrections.md`) before the freeze.
