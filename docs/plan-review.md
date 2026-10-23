# Plan review: `TIMELINE.md` and `GOAL-BRIEF.md`

Written Fri 23 Oct by the Planovac (cloud planner) from the repository state at `b70e773`. It reads `CLAUDE.md`, `PLAN.md`,
`WORKERS.md`, `REVIEW-PLAN.md`, `REQUIREMENTS.md`, `SUBMISSION.md`, `TIMELINE.md`, `GOAL-BRIEF.md` and checks claims against the files in
this checkout. Probabilities and impacts below are judgement, not measurements. This file is a review; the Lead decides which proposals
enter `TIMELINE.md`, which is not edited here.

## Verdict

The plan is sound in shape: gates with pass conditions, a cut list, a finite overnight checklist. It has four real defects: the cut-off for
new results is stated four ways, the overnight run is allowed to change files that the claims gate has already passed, nobody owns the
last unmeasured fact behind the main story (latency of the shipped model), and the morning is overloaded on one person. The brief
(`GOAL-BRIEF.md`) is tightened in this commit; the timeline fixes are listed in section 2 for the Lead.

## 1. Facts checked in this checkout

| Fact | Evidence |
|---|---|
| `analysis/make_all.sh` does not exist yet | `ls analysis/make_all*`: no such file. G3 and the brief's notebook step depend on it |
| Notebooks 06 to 08 do not exist | `git ls-files notebooks`: 01 to 05 only |
| `results/ipp1-final.md` holds no latency of the shipped model | `grep -i latency results/ipp1-final.md`: no match; KQ-9(c) is still open and the deck quotes 0.18 ms from `ipp1-improve.md` on a loaded machine |
| Viewer stills of real discharges are in git | `git ls-files presentation/assets/viewer-*.png` (4 files); `results/ipp1-time.png` plots one real discharge (RP-6, owner has not decided) |
| The Drive file id of the confidential zip is in git | `cloud/BRIEF-search.md` line 13 and `cloud/BRIEF-camera.md` line 12 (`1MBev-...`) |
| `PLAN.md` has two rows with id IMPL-16 | Packager row and the G2 audit row; "update your row" is ambiguous |
| The audit leaves 372 of 410 claims matched only by common or medium values | `docs/claims-audit.md` table; the gate passes on a hand read of a few sentences |

## 2. Gaps, impossible dependencies, missing buffers (`TIMELINE.md`)

| # | Finding | Why it bites | Proposed fix (owner) |
|---|---|---|---|
| T1 | **Four cut-offs for new results.** Cloud "last push 21:30", G1 reads at 22:00, "hard stop 00:30", "results freeze 01:00"; and `PLAN.md` KQ-3 plus "Sat 07:00 integrate the last cloud pushes" copy cloud runs at 08:00, after the freeze and after the claims gate G2 (23:00) | A late cloud number can reach a slide with no claims audit after it. The freeze is not a freeze | One rule: cloud numbers after 21:30 Fri are not used in the deck at all; at 08:00 the Lead may add them only as an appendix slide or a "bonus" line, with a rerun of `check_claims.py` (Lead) |
| T2 | **No claims re-audit after the last integration.** G2 is at 23:00, integration continues to 01:00, G3 (02:30) checks only notebooks, the brief reruns the audit only if `presentation/` changed | A change in `results/` alone (a corrected figure) changes a claim without touching the deck | Lead runs `check_claims.py` at 01:30 after the final integration and writes the count in `Build-Log` (a script, almost free) |
| T3 | **G3 depends on files that do not exist** (`make_all.sh`, notebooks 06 to 08) and on lane R (GPT), which `REVIEW-PLAN.md` lists as "not started" and which needs the owner to paste a line at 19:00 | If GPT never starts, G3 "eight notebooks" cannot pass and nobody is named to write the fallback | Decision at CP2 (22:00): if `06` does not exist, K or L writes markdown-only notebooks that quote `results/` and the producing command. Fallback owner: K (own budget) |
| T4 | **The cut list cuts the wrong notebook.** Item 3 shrinks `06` and `07`; `07` holds the final model, the deck's headline numbers (locked-test result, `ipp1-final.md`), while `01` to `05` describe the baseline only | REQ-005 says all conclusions in notebooks; the headline conclusion would be the one without code | Rule: `07` may shrink to quoted results plus the command, but is never dropped; camera `08` goes first (already item 1) |
| T5 | **Latency of the shipped model is measured by nobody.** The verdict "not an obstacle" is the closing slide; `ipp1_latency.py` times the baseline, the deck quotes 0.18 ms for a similar recipe under load (KQ-9c). The overnight rerun repeats the baseline only | The central claim of the talk rests on a number for a different model | Lead, Friday: time the shipped recipe on the quiet machine into `results/` (one script call), before G2; otherwise the slide says "baseline network" in words |
| T6 | **Latency "idle Apple M5" is already stated in `results/` and the README, yet `PLAN.md` says the reruns were on a loaded machine.** Both cannot be true | A quiet rerun at 03:00 on a Mac that is also running Claude and notebooks is not quiet | Run the latency step alone, before the notebooks, and record load average with the figure; on disagreement the stored value stays and both are reported (brief step 2) |
| T7 | **The morning is one person deep.** 07:00 read `NOW.md`, 08:00 G4, 09:00 G5, 10:00 freeze, 10:00 to 12:00 video recording, two timed rehearsals, deck PDF by hand, and approving the last wording; G7 at 12:00. The owner sleeps about 3.5 hours | Any slip in G4 or G5 eats the rehearsals; the video is the likeliest casualty | The viewer is already DONE and results freeze at 01:00, so record the screen video at 08:30 to 09:30 (before the freeze at 10:00, not after); then rehearsals; G7 keeps its hour. Owner decides at 02:30 |
| T8 | **Video lane V has not started** (owner order: plan only) and its plan is due Fri 20:00 to 22:00, yet it needs the owner's paste at 19:00 | If the owner does not paste, there is no plan, no shot list, no PDF | Early warning: no V session by 21:00. Fallback: the existing 15 s `viewer-demo.mp4` plus a screen recording with voice at 08:30, no editing |
| T9 | **Deck PDF has three owners** (V in `WORKERS.md`, "owner by hand from Keynote" in `SUBMISSION.md`, K in the 22:00 slot); `analysis/make_pdf.py` converts markdown, not pptx; LibreOffice is missing | Nobody exports it; the backup for a failing laptop does not exist | One owner: the owner exports from Keynote or PowerPoint on Fri 22:00 to 23:00 after deck v3, checks Czech characters on every slide, copies the PDF to a USB stick |
| T10 | **Submission channel unknown** (OQ-002, OQ-S1 to S5). "Ask the organizers tonight" names no person, no time, no fallback | The 12:00 slot may be unexecutable (upload, private repo access, handover on the day) | Owner asks once, Fri 19:30, by the channel the organizers gave; if there is no answer by Sat 08:00, plan for handover on the day: zip and PDF on a USB stick, repository access for the organizers prepared, CON-001 respected |
| T11 | **G4 critic has no named owner or budget** ("a cheap agent or the colleague's Claude"); G5 "presentation laptop" and "second device" are not identified; the colleague's wake-up time is not stated | Gates with no named person tend to be skipped | Lead names them at CP3: G4 = one `Explore`-type agent given only the deck PDF, stills, pitch and assignment; G5 = owner plus the Mac that will present |
| T12 | **Budget table has no margin.** 81 % used at 19:00, extra usage off, plan ends at 97 to 99 %; cloud draws are "unverified"; the overnight floor in the brief was 90 % while the morning needs 8 to 10 points | A 2-point error locks the account at G4, the worst moment. The brief and the table agree only if nothing goes wrong | Overnight run starts only at 88 % or less and spends at most 2 points; the Lead stops the cloud sessions at 21:30 as T1 says (they are the unverified draw); re-read `get_usage` at each gate. Nothing saved past Sat 14:00 has value, the limit resets Sun 18:00, so spend the reserve on G4 and G7 first |
| T13 | **README is wrong for a clean machine** (RP-1 to RP-5: layout, data source, `uv`, CPU torch, versions) and "Lead or owner" fixes it, so nobody does; G3 (clean run) follows the README and G6 checks it | G3 passes on K's machine because K worked around it, and the jury fails on the first command | Lead fixes the README on Fri 23:00 to 02:30 (one commit) and K re-follows it as written; add the notebook command and `make_all.sh` |
| T14 | **Ten-minute heartbeat of the Lead (`L` row) and "no polling" in the budget section contradict** (the watch loop ticks every 10 minutes, one line says "no polling") | Hidden spend in the same weekly limit | Heartbeat only while a cloud session is alive; after 21:30 no ticks, the Lead reads at gates |
| T15 | **CON-001 vs the planned artifacts.** Viewer stills and `ipp1-time.png` show real discharges (RP-6 open); the cloud mirror is a repository on a second account (`BLADED-K`); Drive id in the briefs; submission may mean adding collaborators or a link | The one hard legal constraint has open items nobody must close before the submission | Owner decides RP-6 at 19:30 (aggregate-only is the safe default: swap the stills for the noise-bar chart and the aggregate panel); remove the Drive ids from `cloud/BRIEF-*.md` when the cloud sessions finish (Lead); mirror stays private and nobody is added to it |

## 3. Tasks without an owner (rows added to `PLAN.md`)

Only gaps that no existing row or table entry covers were added: T5 (shipped-model latency, a pre-existing KQ-9 question with no row), T7/T8
(record the screen video before the freeze), T9 (one owner for the deck PDF), T10 (submission fallback), T11 (G4 and G5 named persons), T13
(README fix as an actual task), T15 (CON-001 clean-up: Drive ids, stills), a re-audit after the last integration (T2), the duplicate
IMPL-16 id.

## 4. What the overnight run could do wrongly without the owner

| # | Failure | In the first brief? | Change in the tightened brief |
|---|---|---|---|
| N1 | **Connector tools.** The Lead's session may carry the owner's connectors (Slack, Drive, Notion, Figma, Metricool, Higgsfield, ElevenLabs, GitHub). Posting, sharing, publishing, generating images or video all spend credits or leave the machine. The first brief named some outward actions but never forbade spending or the paid generators | Partly | All MCP connector tools forbidden by name, including anything that spends credits or money; the pre-flight asks the owner to deny them in the session settings |
| N2 | **`git push cloud main`** pushes to a mirror on another GitHub account, unattended | Allowed | Removed; push only `origin main`, only own PLAN rows and README typos |
| N3 | **Copying cloud results (item D)** on the judgement of a sleeping agent that "the same folds and no tuning on the locked set" hold. This is exactly "cloud branch with unreviewed numbers", and it contradicts the freeze | Allowed | Fetch and list only; copy nothing; the Lead and the owner decide at 08:00 |
| N4 | **Rerunning existing scripts overwrites `results/` files** that the claims gate already passed (`ipp1-latency.md`, notebook outputs). Torch is not bit-reproducible, so numbers move in the last digit and slides drift from sources | Allowed ("usual outputs") | Reruns write to `out/night/`; nothing under `results/` or `notebooks/` is committed overnight |
| N5 | **Merge noise.** Executed notebooks committed by the run conflict with K's fixes; `--autostash` hides a dirty tree; the colleague's Claude also pushes main | Allowed | No executed notebook is committed; plain `git pull --rebase`, on conflict `git rebase --abort`, leave local, log |
| N6 | **`CLAUDE.md` is the first file read** and tells a session to "ask your user" when its lane is unclear and, for lane K, to download the confidential zip. The brief says "do not ask" | Conflict not resolved | The brief states that it overrides `CLAUDE.md` and says to ignore the lane K steps |
| N7 | **Permission prompt stalls the night**, or the owner flips to a bypass mode to avoid it, which makes every forbidden action technically possible | Pre-flight only | Pre-flight: allowlist plus deny rules, never bypass; a blocked step is logged as blocked; a prompt nobody answers simply ends the run, which is safe |
| N8 | **`get_usage` or `ScheduleWakeup` may not exist in a `/goal` session.** The brief makes an unreadable usage a stop condition (safe), but the night would be wasted | Unverified | Pre-flight: run `get_usage` once in that session; the wake-up option is removed (a high 5 hour window simply stops the run) |
| N9 | **Overwriting `NOW.md`** destroys the owner's previous status | "rewrite it" | Copy to `NOW-before-night.md` first |
| N10 | **Deleting.** No rule said "delete nothing"; "fix stale paths" and "scan" can drift into cleaning up | Not stated | Explicit: delete nothing |
| N11 | **`/goal` length.** The first block was about 8,500 characters. I believe `/goal` limits the condition to about 4,000 characters but have not verified it | Unknown | Block shortened to about 4,600 characters (26 lines); pre-flight says to paste once and check it was not cut |
| N12 | **A rerun that "differs" gets "both written" into the file** the deck cites | Allowed | Both go into `NOW.md`, the stored value is not touched |

## 5. Risk register (top ten)

P = probability, I = impact (L/M/H; P as a rough chance of the event happening to this team before 14:00 Sat).

| # | Risk | P | I | Early warning sign | Mitigation (and owner) |
|---|---|---|---|---|---|
| 1 | **Weekly Claude limit runs out** (81 % at 19:00, extra usage off, cloud draw unverified) before G4 or G7 | M (30 %) | H | `get_usage` jumps more than 3 points in a period; cloud sessions still alive after 21:30 | Stop cloud sessions at 21:30; no fan-outs; overnight start only at 88 % or less and at most 2 points; heavy work to GPT and K; Lead reads usage at every gate |
| 2 | **Live demo fails** on the presentation laptop (browser, fonts, file path, screen resolution) | M (25 %) | H | G5 at 09:00 not run, or run only on the owner's Mac; Firefox slider issue (RP-14) | Backup chain: viewer from `file://`, then the screen video recorded at 08:30, then the PDF of the deck on a USB stick; G5 on the real laptop and one other device (owner, K) |
| 3 | **A claim on a slide has no valid source** (372 claims matched only by common values; shipped-model latency unmeasured; "idle" not checked) | H (50 %) | H | `check_claims.py` count of unsourced numbers above 0 at 01:30; a number on a slide that is not in `results/` | Re-audit at 01:30 and 08:00; hand-read only the real-time, stability, noise and uncertainty sentences; T5 measured or the slide says "baseline"; conservative wording rule in the brief |
| 4 | **Notebooks do not run on a clean machine** (no `make_all.sh`, CUDA torch download of 3 GB, `out/` not in git, `06` to `08` missing) | M (35 %) | H | No `make_all.sh` in `git ls-files` at 22:00; K's run not started by 23:00 | K's clean run from 23:00; README fixes T13; fallback `06` to `08` as quoted markdown (T3); stored outputs stay in the notebooks as evidence |
| 5 | **IPP data leaks** (real-discharge stills and trace in git, Drive ids in the cloud briefs, private mirror on a second account, viewer file with data shared by mistake, repository made public for submission) | L (10 %) | H | `git ls-files` hits a data pattern; owner is asked to "send the repo link"; any step that makes something public | Owner decides RP-6 tonight, aggregate-only by default; scan in the brief step 5 and G6; Drive ids removed after the cloud sessions end; nothing built from data is deployed or shared; submission package built by `make_submission.py` only, which fails on data patterns |
| 6 | **Cloud branch with unreviewed numbers reaches the deck or `results/`** (late C2 search, camera multimodal, copied by a tired person or an unattended agent) | M (30 %) | H | A cloud file newer than 21:30 in `results/`; a cloud number on a slide without a "session's own measurement" tag | T1 single cut-off; brief copies nothing; G1 rules unchanged; locked test set read once (`ipp1-final.md`); late runs go to an appendix only |
| 7 | **The overnight run acts outward or spends** (connectors, push to mirror, credits) or silently changes frozen numbers | L (10 %) | H | Unexpected commit on `origin/main` touching `results/`, `presentation/`, `notebooks/`; a connector call in the transcript | Section 4 changes; deny rules in session settings; owner reads `git log origin/main` first thing at 07:00 |
| 8 | **Submission channel or deadline unclear**, or the owner is the only person who can submit and is late or unwell | M (25 %) | H | No answer from the organizers by Sat 08:00 | T10 fallback; the package is built and kept ready by 12:00; the only owner-only steps are listed in `SUBMISSION.md` section 7; a second person (colleague) knows the plan and the package location |
| 9 | **Morning overload of the owner** (G4, G5, video, two rehearsals, PDF, wording approval) after 3.5 hours of sleep | H (55 %) | M | G4 not started by 08:30; rehearsal not started by 10:30 | Screen video moved to 08:30 (T7); PDF done Friday (T9); `NOW.md` has an ordered Needs owner list; cut list item 2 (reel polish) is dropped first without discussion |
| 10 | **Colleague or his Claude unavailable** (single Linux machine for G3 and the deck; his Claude does not run without him; he sleeps after about 03:00) | M (35 %) | M | K silent for more than 90 minutes after 23:00 | Lead does a degraded clean run on the Mac (brief step 3, executed in a copy) so G3 has some independent evidence; K's deck work is finished by 23:00; G4 does not depend on K |

Below the cut: the pitch tells two versions of the real-time story (baseline 0.0145 ms against the shipped model 0.18 ms), the cloud mirror
lags `main` (a session reads an outdated plan), the owner speaks past 7:00, a clean-room check on Windows is not possible. All have an owner in
an existing row or are covered by rehearsal.

## 6. Edits made by this review

- `docs/GOAL-BRIEF.md`: tightened (scope narrowed to verify only, results and notebooks never committed overnight, cloud fetch is list-only, connectors
  and spending forbidden, push narrowed, usage start threshold 88 %, no wake-ups, `CLAUDE.md` overridden, ordered steps, length about 4,600 characters).
- `docs/PLAN.md`: rows added to "Rows or items without an owner" for the gaps above. No other row touched.
- Not edited (proposals above for the Lead): `TIMELINE.md`, `REQUIREMENTS.md`, `WORKERS.md`, `README.md`.
