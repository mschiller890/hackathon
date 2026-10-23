@AGENTS.md

# Start here (Claude Code sessions in this repository)

A 22 hour hackathon: **CVUT ML Hackathon 2026**, task **IPP 1, plasma shape from magnetic measurements**.
It ends **Sat 24 Oct 2026 at 14:00** (feature freeze Sat 10:00). Several agents and two students work at
the same time, so follow this order before you touch anything:

1. `git pull --rebase origin main`. Read `README.md`, `docs/PLAN.md`, `docs/REQUIREMENTS.md`, `docs/internal/WORKERS.md`.
2. Find your lane in `docs/internal/WORKERS.md` (L Lead, U viewer, R robustness, K colleague). If it is not clear which one is
   yours, ask your user. Work only in the paths of your lane.
3. The user is a Czech student: talk to the user in Czech, write files and code in English. The presentation text
   (lane K) is written in plain Czech, without English words and without dashes.
4. Data are confidential (CON-001). They live outside the repository in `hackathon/data/raw/` and never go into
   git, a public website or a chat. Aggregate numbers and figures go to `results/`.
5. Report evidence: the command you ran and the number you saw. When a task is finished, update its row in
   `docs/PLAN.md` and push a small Conventional Commit (`git pull --rebase` first, stage files explicitly).

## Lane K, the colleague's Claude: your first steps

1. Set up Python 3.12 and the packages in `README.md` ("Setup and run"). Ask your user for the link to the organizers'
   Google Drive folder of IPP task 1 and download `uloha_1-magneticka_data.zip` (37 MB) yourself. Unzip it into its own
   new folder so the layout is `hackathon/data/raw/ipp1-magnetic/uloha_1-magneticka_data/equil_data.csv`.
   Set `HACKATHON_HOME` to the `hackathon/` folder that holds `data/` and `repo/`.
2. Run `analysis/ipp1_eda.py` and `analysis/ipp1_baseline.py` and compare your output with `results/ipp1-baseline.md`.
   Write every problem you hit (missing package, path, different numbers) into the open questions of `docs/PLAN.md`.
3. Write `presentation/outline.md`: the 7 minute talk, slide by slide, with the seconds and the one sentence each slide
   must say. Story: the plasma must be kept off the wall within milliseconds, the classical computation takes minutes;
   the data; the method; the results (numbers only from `results/`, unknown ones marked `DOPLNIT`); the real-time
   verdict; the limits and what the model cannot do. Ask your user which slide tool they will use.
4. Do not do other lanes' work. Material for the motion reel is needed only after the results exist (not before Sat 08:00).
