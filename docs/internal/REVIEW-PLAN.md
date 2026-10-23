---
tags:
  - hackathon
---

# Review plan: planned critiques until the submission

Why: the first review (Fri 18:10) found real faults (no locked test set, unconditional real-time claim, wrong stability claim, collinear importance, stale statuses). Reviews are cheap compared with a wrong claim in front of the IPP jury. Each gate has an owner, a method, a pass condition and what happens on failure. The watch loop (Lead) runs the gates; heavy reviews are run by agents only when the token budget allows (weekly limit about 80 percent), otherwise by the Lead with scripts.

| Gate | Time (CEST) | What is checked | Method | Pass condition |
|---|---|---|---|---|
| G1 numbers | Fri 22:00 (CP2) | Cloud results (camera, search) against our own: same folds, no tuning on the locked set, selection inside training folds, units | Lead reads the branches, reruns the best script locally if a claim reaches a slide | Every cloud number on a slide is in `results/` and reproduced or marked as the session's measurement |
| G2 claims | Fri 23:00 | Every sentence and number on the slides, the pitch script and the README against `results/` and `docs/claims-corrections.md` | Script: extract numbers from the deck and the pitch, grep them in `results/`; Lead reads the rest | No unsourced number; conditional wording for real time, stability, noise |
| G3 clean run | Sat 02:30 (CP3) | Five notebooks and `make_all` from a clean clone on the colleague's machine | Lane K runs it; the Lead reads the log | All notebooks execute top to bottom without error; times documented |
| G4 independent critic | Sat 08:00 | A fresh reviewer that sees only the deck, the viewer screenshots, the pitch and the assignment (no our reasoning): would a mixed jury of IPP physicists and ML people be convinced, what is unclear or overclaimed, ten hostile questions | One cheap agent (or the colleague's Claude); findings to `docs/internal/review-findings-2.md` | No blocker left; every hostile question has a truthful answer in the pitch |
| G5 demo safety | Sat 09:00 | The live demo on the presentation laptop and a second device; the backup (stills, clip, PDF of the deck) | Owner and colleague | Viewer opens offline from `file://`; backup video plays |
| G6 freeze | Sat 10:00 | Nothing new after this line; repository clean (no data, no keys), README accurate | Lead script: `git status`, scan for large files and secrets, README commands | `git ls-files` has no data or keys; README runs |
| G7 submission | Sat 12:00 to 13:00 | The organizers' list: every item of the assignment met, deliverables in the required form, links open logged out | `Hackathon-Brain/06-Submission-Checklist.md` walked line by line | All ticked with evidence; confirmation of the submission saved |

## Standing red flags for the loop
- A number on a slide that is not in `results/`.
- Anything from the cloud sessions used before gate G1.
- The locked test set used for tuning (it is read once, `results/ipp1-final.md`).
- Raw IPP data or generated viewer data in git (`.gitignore` covers `data/`, `out/`, `viewer/data.js`, `viewer/dist/`).
- An agent idle with work left; a cloud session "waiting on a human".

## Watching (the Lead's standing task)
Two cloud sessions (Kritik = camera, Tester = search), the viewer fork (done, stopped on purpose), one free terminal session (bladed-85 now on the multi-seed check; bladed-55 on the input ranking), the colleague (deck, notebooks), GPT (not started). Loop tick every 60 s while something may change; written to `Status-Board` and `Build-Log`.
