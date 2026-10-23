# Timeline: from Fri 23 Oct 19:00 to Sat 24 Oct 14:00 (CEST)

**Authoritative for who does what and when from now on.** What remains to build stays in [`PLAN.md`](PLAN.md); lanes and
paths in [`WORKERS.md`](WORKERS.md); the review gates G1 to G7 in [`REVIEW-PLAN.md`](REVIEW-PLAN.md); the hand-over text for the
night in [`GOAL-BRIEF.md`](GOAL-BRIEF.md). Written Fri 23 Oct about 19:00 by the planner. Assumptions are marked **(A)**; the owner
corrects them, the Lead re-cuts the plan.

## Fixed points

| Time | Point |
|---|---|
| Fri 20:10 | The 5 hour Claude window resets (measured 19:00: 40 % used). |
| Fri 21:30 | Cloud sessions C1 (Kritik) and C2 (Tester) push their last results. |
| Fri 22:00 | CP2 and gate G1. |
| Fri 23:00 | Gate G2. |
| Sat 01:00 | **Results freeze**: no new training result enters `results/` after this (only corrections). |
| Sat 02:30 | CP3 and gate G3. Owner decides the hand-over with `/goal` and sleeps. |
| Sat 07:00 (A) | Owner wakes and reads `NOW.md`. The overnight run stops by 07:30 at the latest. |
| Sat 08:00 | CP4 and gate G4. Reel first cut can start. |
| Sat 09:00 | Gate G5. |
| Sat 10:00 | Feature freeze, gate G6. |
| Sat 12:00 to 13:00 | Gate G7, the owner submits. |
| Sat 14:00 | End. 13:00 to 14:00 is buffer, no features. |

## Budgets (the real constraint)

Measured Fri 19:00: **weekly Claude limit (all models) 81 % used, 19 % left, resets Sun 25 Oct 18:00; extra usage off.**
The viewer fork, the terminal sessions (bladed-55, bladed-85), the cloud sessions and the Lead draw from the same account.
GPT (lane R) and the colleague's Claude (lane K) have their own budgets. Rule: heavy work goes to GPT and K; the account's Claude does
integration, checks and short fixes only. No wide fan-outs, no polling.

| Period | Claude weekly points the account may spend | Used after it (guess) |
|---|---|---|
| Fri 19:00 to 22:00 | up to 3 | 84 |
| Fri 22:00 to Sat 02:30 | up to 3 | 87 |
| Overnight run (03:00 to 07:30) | up to 2, hard floor in the brief at 90 % used | 89 |
| Sat 07:00 to 13:00 | the reserve, 8 to 10 points: G4 critic, fixes, rehearsal, submission | up to 98 |

These are planning numbers, not measurements. The Lead reads `get_usage` at every gate and rewrites the row; if a period overruns,
the cut list below applies, not a bigger budget.

## Hour by hour

(L Lead, U viewer fork, R GPT, K colleague and his Claude, V third Claude, T bladed-55 / bladed-85 terminals, C1 Kritik, C2 Tester, O owner)

### Fri 19:00 to 20:00
- **O (needed):** paste the lane lines to GPT (lane R) and to a third Claude (lane V); tell the organizers' contact what is unclear
  (OQ-002: submission time, video length limit, how a submission is made); decide RP-6 (single discharge trace in the public talk).
- **R (GPT):** the notebooks that do not exist yet (see "Gap" below): `06` robustness, data amount, time context from
  `results/ipp1-robustness-findings.md`. Own budget.
- **K:** `analysis/make_all.sh` and the clean top to bottom run of notebooks `01` to `05` on the Linux machine; every failure goes to the IMPL-8 row.
- **V:** `presentation/video-plan.md` only (no recording yet, owner's order); PDF of the deck to `presentation/deck/`.
- **T (bladed-85):** finish the claims audit (G2 input: `docs/claims-audit.md`, one unsourced number to fix).
- **L:** answer questions in `PLAN.md`, tick the watch loop every 10 minutes, no new analyses.
- **C1, C2:** continue; told once more: last push at 21:30, hard stop 00:30.

### Fri 20:00 to 22:00
- **L (after the 20:10 reset):** read the cloud mirror at 21:30; run the quiet-machine latency rerun when nothing else trains (needs the Mac idle for 2 minutes; if impossible, it is moved to the overnight run at 03:00).
- **R:** notebook `07` final model, distribution, unusual shapes, uncertainty (from `results/ipp1-final*.md`, `ipp1-distribution.md`, `ipp1-unusual-shapes.md`, `ipp1-uncertainty.md`).
- **K:** deck v3 with the final wording; reads `docs/claims-audit.md`; second machine runs `make_all`.
- **V:** video plan finished; deck PDF.
- **Buffer:** 21:30 to 22:00 is slack for the gate.

### Fri 22:00: CP2 and G1 (numbers)
Pass: every required analysis has a number and a graph in `results/`; each cloud number that reaches a slide is reproduced or marked as the
session's own measurement; the locked test set was read once. **Cloud rule:** if C2 (search) has no tested result by 21:30, the final
model stays the locked test recipe (plain candidate for clean inputs, baseline trained with noise and drift for noisy inputs). Failure:
the Lead drops the claim from the slides, not the gate.

### Fri 22:00 to 23:00: G2 prep, then G2 at 23:00 (claims)
- **T or L:** `python -I analysis/check_claims.py` against the deck, outline and pitch; read the "medium and common" matches by hand only for the sentences about real time, stability, noise, uncertainty.
- **K:** apply the findings to the deck; **R:** notebook `08` camera summary from the cloud files (`results/cloud-camera-*.md`) if the PR is final, otherwise a short markdown cell that says the camera is a bonus and where the numbers are.
- Pass: no unsourced number; conditional wording for real time, stability, noise.

### Fri 23:00 to Sat 02:30: notebooks and freeze
- **00:30** hard stop for C1 and C2. **01:00 results freeze.** L integrates the last cloud files (verified only), runs G1 again for what changed.
- **K (own budget, the main load now):** clean clone, `make_all`, all notebooks top to bottom, times written down. A failing cell is fixed in the setup cell only; conclusions stay generated from outputs.
- **R:** executed notebooks `06` to `08` committed.
- **L:** README table of results (numbers from `results/` only), IMPL-8 and IMPL-9 rows current, `NOW.md` and `Status-Board.md` rewritten at 02:00.
- **O:** rehearse the talk once aloud from the deck with a stopwatch, at least the first half; note what is unclear. Sleep prepared: Mac plugged in, never asleep, permissions tested (see the pre-flight list in `GOAL-BRIEF.md`).
- **Buffer 02:30 to 03:30:** if G3 fails, fix until 03:30 at the latest; the hand-over slips, the sleep does not move later than 03:30.

### Sat 02:30: CP3 and G3 (clean run)
Pass: the five (eight) notebooks execute top to bottom without error on a clean clone (K's machine) and `make_all` finishes; `git status` clean;
`git ls-files` has no data or keys. If it passes: the owner pastes the text from `GOAL-BRIEF.md` and sleeps. If it fails after 03:30: the owner
pastes the brief anyway with the single item "notebook failures listed in IMPL-8", nothing else, and sleeps.

### Sat 03:00 to 07:30: the overnight run (unattended, finishing and verifying only)
Finite checklist in `GOAL-BRIEF.md`: quiet-machine latency rerun (if not done), claims audit rerun after any change, a second clean notebook
run on the owner's Mac, `git fetch cloud` once at about 04:00 and 06:30 (verified files only), README commands, scan for data and secrets, handover
note. No new analysis, no agents beyond one read-only check, no outward action. K's Claude may keep fixing notebooks on its own budget if the
colleague leaves it running; it writes only in lane K paths.
**What can run unattended:** reruns of existing scripts, checks, scans, notes. **What must wait for the owner:** any decision between two
results, any wording change that makes a claim stronger, rehearsal, recording of the voice, the reel, the demo on the laptop, everything outward.

### Sat 07:00 to 08:00: wake up
- **O:** read `NOW.md` (Needs owner list), eat, 15 minutes.
- **L:** integrate the last cloud pushes (CP4 rule, WORKERS.md), answer the overnight "Needs owner" list in order.

### Sat 08:00: CP4 and G4 (independent critic)
- **G4:** a fresh reviewer (a cheap agent or the colleague's Claude) sees only the deck, viewer stills, pitch and assignment, writes `docs/review-findings-2.md`: ten hostile questions, what is unclear or overclaimed. Pass: no blocker; every hostile question has a truthful answer in the pitch.
- Reel first cut starts (O and the colleague, with V); second device test of the viewer starts.

### Sat 08:00 to 10:00
- **L:** fixes from G4 (wording only, never new numbers), refreshed `check_claims.py`.
- **09:00 G5 demo safety:** viewer opens offline from `file://` on the presentation laptop and on a second device in a clean browser profile; backup clip and PDF of the deck play. O and K.
- **10:00 G6 freeze:** the Lead's script: `git status`, `git ls-files` for data and large files, secret scan, README commands. After this line only fixes of defects, each one logged.

### Sat 10:00 to 12:00
- Reel final and the 60 to 90 s video (owner and colleague, V's plan); render checked on the file, not the preview.
- Rehearsal with the stopwatch, 7:00 maximum, hostile questions (`presentation/rehearsal-notes.md`). Two full runs.
- L: only the submission list is prepared (below), no new content.

### Sat 12:00 to 13:00: G7 (submission)
- Walk `Hackathon-Brain/06-Submission-Checklist.md` line by line with evidence. **Only the owner submits.** Confirmation saved to `Build/Build-Log.md`.

### Sat 13:00 to 14:00
- Buffer. No features. Last `git status` and push; the owner may answer questions.

## Gap found while planning (REQ-005)
Notebooks `01` to `05` cover data, baseline, inputs, stability and latency. The assignment wants **all conclusions in notebooks**; robustness,
data amount, time context, the final model, distribution, unusual shapes, uncertainty and the camera have only scripts and `results/*.md`.
Plan: three short notebooks `06` to `08` that load the numbers from `results/` and show the figures, without retraining (lane R, then K checks).
If budget or time is short, the notebooks become markdown cells that quote the results file and the command that produced it.

## Cut list (in this order, when time or tokens run out)
1. Camera slide and notebook `08` (bonus, 3 to 13 times worse than the coils).
2. Reel polish (the 60 to 90 s video of the viewer stays).
3. Notebooks `06` and `07` shrink to quoted results.
4. Claim checks beyond real time, stability and noise.
Never cut: notebooks `01` to `05` running top to bottom, the deck and its speaker notes, the viewer with its backup clip, the data-confidentiality scan, the owner's submission.

## Risks that need a decision before 02:30
- **The Mac must not sleep and the run must not stall on a permission prompt.** The first workflow of the day failed because tool calls were refused or interrupted (Status-Board 17:25). Test every command class of the brief once before sleeping.
- **Colleague's hours (A):** he works until about 03:00, then sleeps; his Claude does not run without him. If he stays up, K's notebook run continues on his budget.
- **Weekly limit shared** by all local and cloud Claude sessions (cloud draws unverified): if the number moves faster than planned, the Lead stops the cloud sessions first.
- **Submission mechanism unknown** (OQ-002). Ask the organizers tonight; the 12:00 slot assumes an upload or a form the owner can complete in under an hour.
