# Audit for gates G6 (freeze) and G7 (submission)

Auditor session (cloud, read only apart from this file and one `PLAN.md` row). Branch `cloud/auditor`, base `main` at `b70e773`
(Fri 23 Oct 2026). Severity: **High** = would put a wrong or unsourced claim in front of the jury, fix before the freeze;
**Medium** = fix before sending; **Low** = tidy; **Info** = no action.

**Cannot be checked here:** the IPP data are not on this machine, so no number in `results/` could be reproduced. For each
claim below I read the code that is said to produce it, compared the committed files with each other (md against json,
notebook outputs against results, deck against results) and ran only what needs no data. Whatever says "reproduces" means
"the committed files agree", not "I re-ran it".

## Verdict

- **G6 hygiene: pass with two items.** No data file, key, token, personal e-mail in content, or file over 25 MB in any branch or
  any commit. Open: raw-looking values in figures (H-1), a scanner that cannot see inside the deck (H-5).
- **G6 README accuracy: fail.** Two numbers in the README have no source (T-1), one claim contradicts the committed run (T-2), the
  headline is for the baseline model while the deck presents another (T-4). Fixes are one-line edits.
- **G7 traceability:** nothing fabricated found. Three wording problems must be fixed before the deck is sent (T-1, T-3, T-5). The
  `REQUIREMENTS.md` status column is stale in 6 rows (table in section 2).

## 1. Confidentiality and hygiene

Scope: `main` (50 commits), `origin/cloud/camera` (31), `origin/cloud/search` (23), the local branches. `git ls-remote` shows only
`main`, `cloud/camera`, `cloud/search` (plus the session branches). Commands are in the last column.

| Check | Result | Command |
|---|---|---|
| Data file types ever committed (csv, tsv, npy, npz, zip, jpg, parquet, pkl, pt, h5, mat, xlsx, mp4, db), `viewer/data.js`, `viewer/dist/`, `.env` | none in any commit of any branch | `git log --all --name-only --pretty=format: \| sort -u \| grep -iE '\.(csv\|npy\|...)$\|data\.js\|dist/\|\.env'` |
| Blobs over 1 MB in all history | `presentation/deck/slides.pptx` 7.0 to 7.2 MiB (5 versions in `main`) and 5 deck png 1.2 to 1.5 MB. Nothing over 25 MB. Pack size 22 MB | `git rev-list --objects --all \| git cat-file --batch-check` |
| Keys and tokens: `sk-ant`, `wrkspc_`, `ghp_`, `github_pat_`, `AKIA`, `xox`, private key blocks, `password`/`api_key`/`secret`/`token` assignments | none. The only hits are the regex of `make_submission.py` and prose in `AGENTS.md`, `docs/*.md` | `git grep -P ... $(git rev-list --all)` |
| E-mail addresses in file content | none (the user's iCloud address is not in the repository) | `git grep -hoP '[A-Za-z0-9._%+-]+@...' $(git rev-list --all)` |
| Raw IPP rows in `results/` (20 or more comma separated numbers in a line, long numeric lists in json) | none. `results/ipp1-locked-test-ids.txt` lists 30 discharge numbers, which are identifiers, not measurements | regex over `results/ docs/ presentation/*.md`; json walk |
| Notebook outputs | 5 notebooks, 47 code cells, all with stored output, 0 error outputs, no `/Users/` path, no `head()`, `sample()` or `to_csv`. Per input `describe()` min, mean, max, std only | python over `notebooks/*.ipynb` |
| Deck text (14 slides) | no `DOPLNIT`, `TODO`, path or key. Only aggregate numbers | `ppt/slides/slide*.xml` |
| `.gitignore` takes effect for `data/`, `out/`, `viewer/data.js`, `viewer/dist/`, `.env*`, `__pycache__`, `presentation/assets/*.mp4` | yes | `git check-ignore` |
| Camera caches and model outputs written inside the repository | no: caches go to `$HACKATHON_HOME/out/`; only `.md`, `.json`, `.png` go to `results/` | grep of `savez`, `save`, `write_text`, `savefig` |

### H-1 (Medium) Raw measured values appear in committed figures

CON-001 and `WORKERS.md` allow aggregate numbers and figures only. Three places show individual real values row by row:

1. `presentation/assets/viewer-*.png` (4 stills; three of them are embedded in `presentation/deck/slides.pptx` as `ppt/media/image6.png` to `image8.png`). I opened
   `viewer-middle-divertor.png`: discharge 123 at t = 0.501, true plasma current, elongation, triangularity, R and Z of the axis,
   X-point, strike points, to four digits, plus the full error trace of the discharge.
2. `notebooks/01_data_exploration.ipynb`, cell 14 ("One discharge in time"): six signals of the median discharge drawn row by row,
   including the raw input `IPR05`. The notebook's own text says it "never" shows raw rows.
3. `results/ipp1-time.png` middle and right panels (already `PLAN.md` RP-6).

The other `results/*.png` (for example `ipp1-camera-local.png`) are aggregate: checked, no problem.

Not a leak while the repository stays private. It becomes one the moment the repository, the notebooks or the deck are public, and
`SUBMISSION.md` OQ-S2 says "links open logged out", which pushes towards public.
**Fix:** the owner decides with ÚFP whether one real discharge may be shown (RP-6 asked this and has no answer). Until answered:
write the answer into `DECISIONS.md`; do not make the repository public (`gh repo edit ... --visibility private` is the rollback);
if the answer is no, replace the cell 14 figure by a plot of a synthetic discharge or of per-time-decile aggregates, and drop the
three stills from the deck and `presentation/assets/`.

### H-2 (Low) Author e-mails in every commit

`klada1708@gmail.com` (41 commits), `mschiller890@gmail.com` (29), `noreply@anthropic.com` (14). Harmless while private; public
history would publish both gmail addresses. History must not be rewritten (`AGENTS.md` §0), so: **Fix:** only for future commits,
`git config user.email <id>+<login>@users.noreply.github.com`; nothing else.

### H-3 (Low) The owner's home path in 8 tracked files

`/Users/bladed/...` in `docs/PLAN.md`, `docs/internal/WORKERS.md`, `docs/internal/GOAL-BRIEF.md`, `docs/SUBMISSION.md`,
`results/ipp1-camera-local-findings.md`, `results/ipp1-uncertainty.md`, `results/ipp1-unusual-shapes.md` and as a test string in
`analysis/make_submission.py:67-68` (intended). A local account name, not a secret. **Fix:** in the three `results/` files replace
`HACKATHON_HOME=/Users/bladed/Documents/AIprogramy/hackathon` by `HACKATHON_HOME=<hackathon folder>` (`sed -i`).

### H-4 (Low) `.gitignore` does not cover the file types that CON-001 forbids

Not ignored today (tested with `git check-ignore`): `*.csv`, `*.npy`, `*.npz`, `*.zip`, `*.jpg`, `*.parquet`, `*.pt`, `*.mp4` outside
`presentation/assets/`, `video/`, `.venv/`, `.ipynb_checkpoints/`. A stray `git add -A` would stage them. `AGENTS.md` §14.4 says
stage explicitly, but a second net is cheap.
**Fix (append to `.gitignore`):**
```
*.csv
*.tsv
*.npy
*.npz
*.zip
*.jpg
*.jpeg
*.parquet
*.pt
*.pth
*.pkl
*.h5
*.mp4
*.mov
video/
.venv/
.ipynb_checkpoints/
```
No tracked file matches these patterns (`git ls-files | grep -E '\.(csv|npy|npz|zip|jpe?g|parquet|pt|pkl|h5|mp4)$'` is empty).

### H-5 (Medium) The submission scanner is blind where the risk is

`analysis/make_submission.py` (run here: exit 0, 87 files, 14.93 MB, no failed checks, so `SUBMISSION.md` "86 files, 10.8 MB" is stale):
- It scans `.md .py .txt .json .ipynb` only. The deck `slides.pptx` (images with real values, H-1) and `viewer/index.html` are
  not scanned; images are never inspected.
- `python-pptx` is not in the README package list. Without it the placeholder check is skipped and reported under "MISSING",
  not as a failure. I checked all 14 slides by hand: none left.

**Fix:** add `python-pptx` to the README install line, or make `deck_placeholders` exit 1 when the import fails. Add the
H-1 stills to a checklist item "owner confirmed that the figures may leave the participants" in `SUBMISSION.md` section 5, step 4.

### H-6 (Info) Cloud branches

`cloud/camera` and `cloud/search` are clean by every check above. They share **no common ancestor** with `main`
(`git merge-base main origin/cloud/camera` is empty), so a merge needs `--allow-unrelated-histories`; the Lead copied the results
instead. Byte comparison of the copied files (`git show origin/cloud/...:file | sha1sum` against `main`): of 12 results and scripts
compared, 11 are identical, except `analysis/cloud_camera_fusion.py`, where the branch is newer (adds `--clean-inputs` and `--locked`).
No result produced by that newer script is in `main`.

## 2. Traceability (`docs/REQUIREMENTS.md`)

Every cited evidence file exists. Proposed status cells, with what I read:

| ID | Evidence file | Code read | Agreement | Proposed status |
|---|---|---|---|---|
| REQ-001 | `ipp1-baseline.md/.json`, `ipp1-final.md` | `ipp1_baseline.py`, `ipp1_common.py` (`score`, `GroupKFold`), `ipp1_final.py` | md = json = notebook 02 output to 5 digits (ridge plasma current 0.03455, MLP R axis 0.37724). 16 targets, folds by discharge. Locked set 30 discharges in `ipp1-locked-test-ids.txt` | **DONE** once T-3 and T-4 wording is fixed |
| REQ-002 | `ipp1-latency.md/.json`, notebook 05 | `ipp1_latency.py` (weights random, timing only; numpy forward asserted equal to torch) | md = json = deck. **README and REQUIREMENTS disagree with them (T-1, T-2); notebook 05 is stale (T-6)** | IN PROGRESS until T-1, T-2, T-5, T-6 are fixed, then **DONE** (verdict stays conditional) |
| REQ-003 | `ipp1-time.md/.json/.png`, notebook 04 | `ipp1_time.py` | Now covers **all 16 targets**, clean and noisy (plain and hardened). Pooled MAE of R axis 0.377 equals baseline and notebook 04 (0.37711). Cell text "7 of 16 targets, noisy not yet in table" is stale | **DONE** (rewrite the cell; keep "jitter near 1 only on clean input", on noisy input the plain network's ratio is 1.1 to 17.8) |
| REQ-004 | `ipp1-inputs.md`, `-controls.md`, `-ranking.md`, notebook 03 | `ipp1_inputs.py`, `ipp1_inputs_ranking.py` (locked set removed first, line 59 to 61) | Numbers quoted in the cell equal the file (FL01 +7.6 % 5/5, IPR13 last in 5/5 ridge folds, 4.5 % seed noise). See T-8 | **DONE** with the T-8 wording; notebook 03 still ranks by permutation importance only |
| REQ-005 | `notebooks/01` to `05` | all five read | Stored outputs complete. Clean run unverifiable here (needs data). Notebooks hold no result for the final model, locked set, robustness, camera, learning curve, unusual shapes, time context (`grep` of the five notebooks: `locked`, `camera`, `temporal` 0 hits) | **IN PROGRESS** (T-6, T-7, section 4) |
| REQ-006 | `presentation/`, `deck/slides.pptx` | `build_deck.py` not rerun | 14 slides, no placeholder, numbers on slides 5, 7, 11, 12 equal `results/` (slide 7 = `ipp1-final.md`, slide 11 = `ipp1-latency.md`, slide 5 = `cloud-camera-main.md`). PDF and video do not exist | **IN PROGRESS** |
| REQ-007 | `ipp1-distribution.md` | `ipp1_distribution.py` (asserts equality with `score_extended`) | R axis 0.553 / 0.237 mm = 2.3x, median 0.153, p99 3.74, max 64.3: as the README says. Handling (stratified folds, weighting) not done; the candidate model is not a response to it | **IN PROGRESS** |
| REQ-B01 | `cloud-camera-multimodal.md/.json/.png` (same 14,520 frames and folds, magnetic MLP like for like) | `cloud_camera_model.py` | exists on `main`; camera+magnetic beats camera on every target, loses to magnetics except R and Z limiter (12.6 and 28.0 against 16.7 and 30.4 mm) | **DONE** (caveat: 78 of 149 discharges, 48x64 pixels, every 8th frame, 12 epochs) |
| REQ-B02 | `ipp1-robustness-findings.md` section 2, `ipp1-learning_curve.png` | `ipp1_learning_curve.py` | table reproduces the baseline at 119 discharges (0.38 mm) | **DONE** (caveat stated in the file: fixed 60 epochs) |
| REQ-B03 | `cloud-camera-main.md` (colour 1.79, grey 1.70 mm R axis, 5 folds); local 2-fold in `ipp1-camera-local-findings.md` | `cloud_camera_model.py` | consistent (local 1.54 vs 1.53 is 2 folds) | **DONE**: grey is not worse |
| REQ-B04 | `ipp1-robustness-findings.md` section 3 | `ipp1_temporal.py` | table matches the text; reason for the clean-input loss is labelled hypothesis | **DONE** |
| REQ-B05 | `cloud-camera-findings.md` "Shifted and rotated camera", `cloud-camera-main-sensitivity.png`, `ipp1-camera-local.png` | `cloud_camera_model.py` | shift 1 px (1/64 of the width) doubles the error, 5 degrees x1.5 to x2.3 | **DONE** for the sensitivity. Training with shifts (`augment`) is still `DOPLNIT` at lines 95 and 128 of the findings; the only augmented result is the 2-fold local figure |
| REQ-B06 | `ipp1-robustness-findings.md` section 1, `ipp1-final.md` | `ipp1_robustness.py`, `ipp1_final.py` | "27 times larger" = 10.15 / 0.38 is 26.7: ok | **DONE** (synthetic drift stated) |
| REQ-B07 | `ipp1-inputs*.md` | see REQ-004 | no per sensor ranking is claimed | **DONE** with the REQ-004 wording |
| REQ-B08 | `ipp1-unusual-shapes.md` | `ipp1_unusual_shapes.py` (uses all 149, no locked set involved) | "1.0 to 3.0 times larger" matches the table; only 18 truly unusual discharges, never held out alone, stated in the file | **IN PROGRESS** rather than DONE: the file itself says the extreme was never tested. Say "tested on groups containing the 18 unusual shapes" |

Stale cells in `REQUIREMENTS.md` to rewrite: REQ-003, REQ-B01 (TODO), REQ-B03, REQ-B05 (TODO), plus the status line "Missing notebooks are
the main delivery risk" which is correct. `results/ipp1-unusual-shapes.md` and `ipp1-robustness-findings.md` name `out/ipp1-unusual_shapes.*`
(underscore) while `results/` holds hyphens: harmless.

### T-1 (High) "0.053 ms end to end" has no source

`README.md:24` (and `REQUIREMENTS.md` wording rules) say "0.053 ms end to end with numpy in and out". No file in `results/`, `docs/` or the
notebooks contains 0.053 for latency (`grep -rn '0\.053'`). The committed run says `cpu_end_to_end_numpy` median **0.0140 ms**, p99 **0.0503 ms**
(`results/ipp1-latency.md`), and deck slide 11 says 0.0140. The README also says "0.03 to 0.07 ms on a loaded or different CPU": 0.032 is the
colleague's Ryzen (RP-7), 0.0514 the loaded notebook run, 0.07 is a p99.9. **Fix:** in README and REQUIREMENTS write "0.014 ms median, 0.050 ms p99
end to end with numpy in and out (`results/ipp1-latency.md`)" and "0.03 to 0.05 ms on a loaded or different CPU".

### T-2 (High) "idle Apple M5" contradicts the committed run

`README.md:6` and the note in `results/ipp1-baseline.md:25` say idle. `results/ipp1-latency.json` has load average at start [5.67, 14.52, 29.34] on
10 cores and its md says "the machine was shared and busy". Notebook 05 says load 21.5. **Fix:** replace "on an idle Apple M5 CPU" by "on an Apple M5 CPU
(shared machine, load average 5.7; see `results/ipp1-latency.md`)" in both files.

### T-3 (High) "30 discharges nobody saw during development" is not literally true

Deck slide 7 ("na 30 zamčených výbojích, které při vývoji nikdo neviděl") and `ipp1-final.md` ("recipe choices use development only") overstate. The
candidate recipe is "combo_long of `ipp1_improve.py`" (`ipp1_final.py` header), and `ipp1_improve.py` selects it by 5-fold `group_folds(X, Y, G)` over **all
149 discharges** (`ipp1_improve.py:338`), committed Fri 18:09 (`03baa75`); the locked ids were drawn Fri 18:20 (`aa1cf2d`). The 30 discharges were
not used to train the evaluated models and were scored once, but they had already counted in choosing Huber loss, difference features, 150 epochs and the
gated limiter network. The gain (about 2x) is far above any selection effect, but the sentence is wrong. **Fix:** slide 7 and `ipp1-final.md`: "30 discharges
that were set aside before the final models were trained and scored once; the recipe itself was chosen earlier by cross validation over all 149".

### T-4 (Medium) README headline is for the baseline, the deck presents another model

README: 0.38 mm axis error, "final model should use ridge" for the current. Deck slide 7 and `ipp1-final.md`: candidate, 0.13 mm axis, 0.035 kA, on the
locked set. Also: "contiguous blocks ... about 1.5 times larger" (README, REQUIREMENTS, `ipp1-baseline.md:25`) but `ipp1-final.md:37-38` gives 1.5 to 2.9 times
for the baseline (R axis 1.23 against 0.448 mm is 2.7). "99 % of rows under 3.7 mm": p99 is 3.74 (`ipp1-distribution.md`). **Fix:** "1.5 to 2.9 times", "99 % under
3.74 mm", and add one README line naming the shipped model and pointing to `results/ipp1-final.md`.

### T-5 (Medium) Slide 14 latency belongs to the baseline, not the shipped model

Slide 14 pairs "0,0145 ms" with the accuracy of the candidate. The candidate (differences, ridge, gated limiter network) measured 0.035 ms (one
torch thread) to 0.18 ms (loaded), `results/ipp1-improve.md:13,50-51`; slide 11 says so in small print, slide 14 does not, and there is no latency file for
the shipped model. **Fix:** slide 14: "0,0145 ms (základní síť); nasazený model 0,035 až 0,18 ms", or time the candidate with a script that writes `results/`.

### T-6 (Medium) Notebook 05 holds an older latency run than `results/`

Notebook 05 reads `out/ipp1-latency.json` and its stored text quotes "p99.9 0.070 ms, slowest 0.090 ms, GPU 0.24 ms". Committed
`results/ipp1-latency.json`: p99.9 0.0812, max 0.148, GPU median 0.2681 (single CPU sample; p99 0.0209 against 0.0288). Two latency measurements
exist and the notebook disagrees with the deck. **Fix:** copy `results/ipp1-latency.json` to `out/`, re-execute notebook 05, check slide 11 against it.

### T-7 (Medium) REQ-005: conclusions live in `results/*.md`, not in notebooks

The assignment wants "all detailed conclusions" in notebooks. None of the five notebooks mentions the locked set, camera or time context; the final model,
robustness, learning curve, unusual shapes, distribution and camera exist only as `results/*.md` and scripts (already `PLAN.md` IMPL-8). Notebook 03 ranks by
permutation importance, which REQ-004 itself calls rejected. **Fix:** either one more notebook that reads the committed `results/*.json` and shows the
figures, or state in `README.md` which `results/*.md` hold which conclusion (cheaper; owner decides, OQ-S4).

### T-8 (Low) REQ-004 sentence is an artifact of its own rule

"Only FL01 clears the seed noise" is the output of the rule "worse in 5 of 5 folds and above 4.5 %". `ipp1-inputs-ranking.md` also shows IPR12 +36.2 % (4/5 folds), IPR13
+14.7 %, IPR14 +13.3 %, larger than FL01 but in 4 of 5 folds. **Fix:** "removing any single input changes the error by less than the seed noise in at least one fold,
except FL01 (+7.6 %, 5 of 5); IPR12, IPR13, IPR14 rise most (+36, +15, +13 %) but not in every fold".

## 3. README accuracy: commands on a clean checkout

Environment: Linux x86, Python 3.12.3, fresh `git clone` of `main` into `.../hh/repo`, no data, `HACKATHON_HOME` unset, `python -I` as written.

| Command | Result |
|---|---|
| `uv venv ~/.venvs/hackathon --python 3.12` and `uv pip install ... pandas pyarrow openpyxl matplotlib scikit-learn torch charset-normalizer` | works (torch pulls the CUDA wheels, `RP-4`) |
| `python -I repo/analysis/ipp1_baseline.py` | exits 1 with a clear message "Data folder not found ... Set HACKATHON_HOME" (as designed) |
| `python -I repo/analysis/ipp1_eda.py` | exits 1 with a **raw `FileNotFoundError` traceback**; no hint about `HACKATHON_HOME` (it does not use `ipp1_common`) |
| `python -I analysis/ipp1_latency.py` | **fails without data although it needs none** ("Data folder not found"): `ipp1_common` checks the folder at import (`ipp1_common.py:20-24`) |
| `python -I results/ipp1-robustness-checks.py` ("4 tests, OK", synthetic fixtures only) | **4 errors, exit 1**, same cause |
| `python -I analysis/make_submission.py --out <dir>` | works: exit 0, 87 files |
| `python -I analysis/check_claims.py` | runs, but **overwrites `docs/internal/claims-audit.md` in the working tree** (I restored it with `git restore`) |
| `python -I analysis/profile_data.py` | usage error: needs a path argument (README does not mention it) |
| `analysis/make_pdf.py`, `viewer/record.py` | need `markdown`, headless Chrome, ffmpeg, `websocket-client`: not in the README list; not run |
| `viewer/build.py` | needs `viewer/data.js` (data, gitignored): fails on a clean clone by design |

**R-1 (Medium)** `ipp1_common.py` raises and creates `out/` at import. **Fix:** move the folder check into `load()`, create `OUT` lazily, so
`ipp1_latency.py` and the 4 fixture tests run without data (that is also the only cheap check a reviewer can run).
**R-2 (Medium)** Four scripts hard-code a folder named `repo`: `ipp1_final.py:305,382-383`, `ipp1_claim_support.py:47`, `ipp1_final_seeds.py:82`,
`ipp1_improve.py:464-465` write to `$HACKATHON_HOME/repo/results`. Any other clone name (including this one) writes into the wrong place or fails (RP-1). **Fix:**
`Path(__file__).resolve().parents[1] / "results"`, as `cloud_camera_model.py:30` already does.
**R-3 (Medium)** `check_claims.py` rewrites a tracked file. **Fix:** write to `out/` or stdout.
**R-4 (Low)** README gaps (see RP-1 to RP-5, still open): no data source and unzip target, no `uv` install line, no CPU torch index, no versions, no
`ipykernel`/`jupyter`, no `python-pptx`, `markdown`. The "Repository structure" table lists 5 of 12 top level paths (no `notebooks/`, `results/`, `presentation/`,
`viewer/`, `cloud/`, other `docs/`). The status paragraph says "notebooks in progress" (true) but REQUIREMENTS has more rows done than it says.
**R-5 (Low)** `eda.py` should fail like `ipp1_common`: one line `if not DATA.exists(): raise SystemExit(...)`.

All relative links in `README.md`, `docs/`, `viewer/`, `presentation/`, `cloud/` markdown resolve (script check).

## 4. What a fresh clone lacks for the notebooks

1. **Data:** `equil_data.csv`, `equil_data_noisy.csv` at `$HACKATHON_HOME/data/raw/ipp1-magnetic/uloha_1-magneticka_data/`. The notebooks default `HACKATHON_HOME`
   to the **parent of the clone**; the scripts default to the **current folder**: different defaults, same error if the clone is not next to `data/`.
2. **`out/` is gitignored**, notebooks read: `out/ipp1-baseline.json`, `out/ipp1-inputs.json`, `out/ipp1-time.json`, `out/ipp1-latency.json` (committed copies of all four are in
   `results/`: copy them, mind T-6) and `out/ipp1-predictions.csv` (not in git, row level predictions; make it with `python -I analysis/ipp1_oof.py`, about 50 s per RP-13).
3. **Kernel:** every notebook says `kernelspec hackathon`. Needs `uv pip install ipykernel jupyter nbconvert` and `python -m ipykernel install --user --name hackathon`.
4. **Time:** notebook 02 retrains 5 folds (171.8 s stored), notebook 05 trains one epoch. No `make_all` exists although `REVIEW-PLAN.md` G3 and `SUBMISSION.md`
   mention it.
5. The five notebooks need the same Python packages as the README plus a Jupyter front end.

## 5. Open items (not fixable by this lane; one row in `docs/PLAN.md`)

Owner: H-1 (decision with ÚFP, RP-6), OQ-S1, OQ-S2 (private repository versus "logged out"). Lead: T-1 to T-5, T-8, REQUIREMENTS cells; deck slides 7 and 14 (the colleague's
`build_deck.py`). Analysis lane: R-1 to R-3, H-4, T-6, T-7. Nobody yet: deck PDF and video (`SUBMISSION.md` section 2).

## Fixed

Auditor session 2, branch `cloud/auditor-2` (base `origin/main` `1e19dec`, Fri 23 Oct 2026). One line per fix; the commit subject says the same.

- **T-1, T-2, T-4 (README):** `README.md` now names the shipped model with its protocol (0.133 mm radial axis on the 30 set-aside discharges, 0.23 mm in 5-fold cross validation on the 119 development discharges, 0.397 mm on the 59 highest ids; baseline network 0.307, 0.38 and 1.23 mm), takes every latency number from `results/ipp1-latency.md` and `results/ipp1-latency-shipped.md` (no "0.053 ms", no "idle"; the machine was shared, load average 5.7 and 7.0), says "1.5 to 2.9 times" for contiguous blocks and "99 % under 3.74 mm".
- **R-4, clean checkout (README):** data section checks the file the scripts need and handles the two possible unzip layouts; the recorded sha256 has 62 of 64 digits and is flagged (size and first 8 digits are the check); a CPU-torch warning sits inside the install block; the stale "notebook 04 stops with KeyError" note is replaced (fixed by `b7f5011`, full run after the fix not recorded); the structure table lists every top-level folder and file; the commands that need no data, need extra packages or rewrite a tracked file (`check_claims.py`) are named. Not run here: no data and no torch on this machine.
- **REQUIREMENTS cells:** `docs/REQUIREMENTS.md` REQ-003, REQ-004, REQ-B01 to B04, B06, B07 are `DONE`, REQ-B05 `DONE` for the sensitivity, each with its evidence file and caveat; REQ-001, 002, 005, 006, 007 and REQ-B08 stay `IN PROGRESS` with the open item written in the row (REQ-001 becomes `DONE` when the T-3 sentences below are applied); the latency wording rule and the T-8 wording are corrected.
- **H-4:** `.gitignore` now ignores the 17 patterns of H-4 (checked with `git check-ignore`; `git ls-files` shows no tracked file that matches).
- **H-5 and the deck:** `analysis/make_submission.py` reads the deck as a zip (no `python-pptx` needed, so the "skipped" case is gone) and fails on a placeholder (`DOPLNIT`, `TODO`, `XXX`, `lorem`, `[[`) in slide or notes text, a secret or `/Users/` path in any part, a chart series or embedded workbook over 200 points or rows (the deck has 6 workbooks of 5 to 11 rows and charts of at most 10 points), a forbidden file type or an unknown embedded file; it also scans `viewer/index.html` in place, scans `.html .js .css .svg .xml` in the package, warns on `/Users/` paths (H-3: three `results/` files) and lists the deck images (it recognises the three viewer stills by hash) and the figures it cannot judge. Negative tests with a changed copy of the deck (placeholder, key in the notes, 300-point chart, `.jpg` in the media) each gave a failed check. Dry run on this branch: `python3 -I analysis/make_submission.py --out <new folder>`: exit 0, 91 files, 14.99 MB, "FAILED CHECKS: none", only the video missing, 4 warnings (viewer stills in the deck, three `/Users/` paths). Pictures are still not inspected by any script: the owner's confirmation of the figures below stays a manual step (the script prints it).
- **Not changed (by instruction):** deck, pitch, notebooks, `results/`, other scripts. Their fixes are listed below for the Lead.

## H-1 figure list: keep or regenerate (proposal, nothing deleted)

Every committed image was opened or, where marked, judged from the code that draws it. "Aggregate" = counts, means, error summaries or model comparisons with no individual discharge. The audit named 3 places; two more were found (rows 5 and 6).

| # | Figure | What it shows | Proposal |
|---|---|---|---|
| 1 | `presentation/assets/viewer-start-limited.png`, `viewer-middle-divertor.png`, `viewer-rough-end.png` (deck file `ppt/slides/slide10.xml` as `image6` to `image8`) | Discharge 123 (and discharge 4 in the noise still): true boundary, true parameter table to four digits, error trace of the whole discharge | **Regenerate** unless ÚFP allows one discharge (RP-6): crop to the plasma cross section and the three tiles of errors, hide the table of true values and the full error trace (or draw a synthetic shape). Then rebuild the deck. Until then the deck must not leave the participants |
| 2 | `presentation/assets/viewer-noise.png` | Discharge 4, true Ip, elongation, R and Z of the axis to four digits, full error trace; not in the deck | **Keep in the private repository only**; not packaged (the package copies only `results/*.png` and the deck). Delete before the repository is ever public |
| 3 | `results/ipp1-time.png`, middle and right panels | Error trace of one discharge, clean and noisy input (derived from true values row by row; the audit and RP-6 wrote "true values", the file shows errors) | **Regenerate** both panels as the median and the 10 to 90 % band of the absolute error per time decile over all discharges (`analysis/ipp1_time.py:164`, lane owner). Keep the left panel (aggregate) |
| 4 | `results/ipp1-unusual-shapes.png`, left panel | One dot per discharge: median elongation and triangularity of each of 149 discharges | **Regenerate** as a 2-D density of the same two numbers (as `notebooks/01` cell 12 does) with the 18 unusual shapes marked by their count. Keep the right panel (bar chart of errors) |
| 5 | `notebooks/01_data_exploration.ipynb` cell 14 ("One discharge in time") | Six true signals of the median discharge row by row, including raw input `IPR05` | **Regenerate**: median and 10 to 90 % band over all discharges against relative time. The notebook text says it "never" shows raw rows |
| 6 | `notebooks/04_stability_over_time.ipynb` cell 11, first figure | True and predicted plasma current, R axis, elongation, triangularity of two discharges (the median-error and the worst one) | **Regenerate** as error bands over relative time for all discharges, or keep the worst-discharge panel only if ÚFP allows one discharge. Second output of the cell (error against discharge length, one dot per discharge, error is an aggregate) and the histogram: keep |
| 7 | `notebooks/02` cell 12 and `notebooks/01` cell 12 (hexbin of true against predicted, density of shapes) | 2-D histograms of all rows; the sparse bins are single rows | **Keep** (aggregate density); note the isolated hexes in `R_limiter` and `Z_limiter` |
| 8 | `results/ipp1-uncertainty.png`, `ipp1-robustness.png`, `ipp1-temporal.png`, `ipp1-learning_curve.png` (thin lines are folds), `ipp1-inputs.png`, `ipp1-camera-local.png`, `cloud-camera-main-sensitivity.png`, `cloud-camera-multimodal.png`, `cloud-search-search.png`, left panel of `ipp1-time.png` | Error summaries, model comparisons, search progress | **Keep** (aggregate; opened) |
| 9 | Notebooks 01 c8, c10, c16, c18; 02 c11, c14, c16; 03 c7, c12; 04 c5, c9; 05 c11 | Histograms of pooled values, PCA and correlations, error curves, timing; c8 and the second output of 04 c11 opened, the rest judged from the code and titles | **Keep** |
| 10 | `presentation/assets/01-hero.png` to `07-closing.png` | Generated illustrations (`prompts.md`: no text, no numbers) | **Keep** |

Order of work if the answer is "no" (the owner decides with ÚFP; RP-6 has no answer yet): rows 1, 3, 4, 5, 6 before the freeze at 10:00; rebuild the deck; run `make_submission.py`; the script cannot tell the pictures apart, so re-open the five figures once.

## Replacement sentences for the Lead (T-1 to T-3)

Czech text is plain, without English words and without dashes. Every number is from `results/` as committed on `main` at `1e19dec`. Files marked "mine" are already fixed on this branch; the others belong to the Lead or the deck owner and were not touched.

### T-1 "0,053 ms end to end" (no source; the committed run says 0,0140 median, 0,0503 p99, 0,105 max)

| Where | Replacement |
|---|---|
| `docs/claims-corrections.md:26` (feeds the outline, pitch and deck; the pitch and outline already say 0,0140 and 0,0503) | Celý odhad základní sítě od surových čísel na vstupu po čísla na výstupu trvá medián 0,0140 milisekundy a 99 procent odhadů je rychlejších než 0,0503 milisekundy. Na systému bez reálného času se ojediněle objeví špičky až do milisekund; nejvyšší hodnota z 5 000 měření byla 0,105 milisekundy, to není horní mez. |
| `docs/claims-corrections.md:38` (evidence, English) | `results/ipp1-latency.md`, row `cpu_end_to_end_numpy`: median 0.0140, p99 0.0503, max 0.105 ms. The 0.053 ms of reviewer 2 appears in no committed file. |
| shipped model, wherever the end to end figure of the selected model is wanted (`outline.md:75`, `pitch-script.md:120`) | Vybraný model trvá od 24 surových čísel po 16 výstupů medián 0,0154 milisekundy u divertorového plazmatu a 0,0274 milisekundy u limitovaného; 99 procent odhadů je pod 0,057 a pod 0,093 milisekundy (`results/ipp1-latency-shipped.md`). |
| `README.md:6`, `README.md` verdict bullet, `docs/REQUIREMENTS.md` wording rule | mine, fixed |

### T-2 "idle Apple M5" (the committed run: load average 5,67 at the start on 10 cores, "the machine was shared and busy"; the shipped run 7,01)

| Where | Replacement |
|---|---|
| `docs/claims-corrections.md:20` | Výpočet sítě rychlosti nebrání: základní síť trvá medián 0,0145 milisekundy a vybraný model 0,015 až 0,027 milisekundy na jednom jádru procesoru Apple M5 na sdíleném počítači, rozpočet je 1 až 10 milisekund. |
| `docs/claims-corrections.md:29` | 0,0145 milisekundy. Tolik trvá výpočet základní sítě na jednom jádru procesoru Apple M5 na sdíleném počítači; k tomu patří věta, že sběr signálů a napojení na řídicí systém jsme nezkoušeli. |
| `docs/claims-corrections.md:37` (evidence) | `results/ipp1-latency.md` (median 0.0145 ms, max 0.148 ms, one thread, shared machine, load average 5.7 on 10 cores). |
| `results/ipp1-baseline.md:25`, last sentence (English) | The latency line was measured on one core of an Apple M5 on a shared machine (load average 5.7 on 10 cores); see `ipp1-latency.md` for the conditions. |
| `results/ipp1-baseline.md:25`, third sentence (T-4) | On contiguous blocks of discharge numbers the clean-input error is 1.5 to 2.9 times larger (radial axis 1.23 against 0.448 mm, `ipp1-final.md`). |
| `presentation/outline.md:75` and `:126`, `presentation/pitch-script.md:280` and `:394`, `docs/deck-fixes.md:104` (all say "klidný stroj" or "klidný počítač", and `outline.md:75` and `pitch-script.md:280` say "dvanáctkrát víc") | The measurement exists and the machine was not quiet. Spoken line: Vybraný model trvá 0,027 milisekundy u limitovaného plazmatu a 0,015 u divertorového, tedy asi dvakrát víc než základní síť; počítač byl sdílený. Dřívější odhad 0,1775 milisekundy z jiného postupu se nepotvrdil. Tile label: "vybraný model, procesor Apple M5, jedno jádro, sdílený počítač". |
| the `[[latency shipped]]` placeholders (`outline.md:11,71,75,107,126`, `pitch-script.md:113,120,158,241,280,375,394`, `docs/deck-fixes.md:104,138,153`) and `presentation/deck/build_deck.py:427-430` | Fill with 0,027 ms (limitované plazma, the bound to quote) and 0,015 ms (divertorové); drop "asi 0,18 ms". `build_deck.py:427-428`: "Vybraný model se třemi částmi trvá 0,027 ms u limitovaného a 0,015 ms u divertorového plazmatu; procesor Apple M5, jedno jádro, sdílený počítač." and the source line `results/ipp1-latency-shipped.md` instead of `results/ipp1-improve.md (0,18 ms nasazeného receptu)` at `:430`. This also settles T-5 for slide 14. |

### T-3 "30 výbojů, které při vývoji nikdo neviděl"

The recipe (`combo_long`) was chosen by the 5-fold `group_folds(X, Y, G, folds)` of `analysis/ipp1_improve.py:338` over all 149 discharges, and `results/ipp1-improve.md` reports it; `ipp1_final.py` takes it from there. The 30 were not used to train the evaluated models and were scored once, but they were among the 149. (The audit named commits for the order; `git log` shows the same commit time, 18:20:30, for many commits, so the order cannot be proven from history and is not needed: the 30 were inside the 149 either way.)

| Where | Replacement |
|---|---|
| `presentation/deck/build_deck.py:354` (slide 7 caption; `docs/deck-fixes.md:63` proposes a wording that keeps "před finálním výběrem") | Průměrná chyba v mm na 30 výbojích odložených před učením konečných modelů a vyhodnocených jednou. Postup jsme vybrali dříve křížovou validací na všech 149 výbojích. |
| `presentation/deck/build_deck.py:345` (title), `:368` (source) | "Na 30 odložených výbojích: osa 0,13 mm"; source "results/ipp1-final.md (odložená sada, 30 výbojů)". |
| `presentation/deck/build_deck.py:357` | series name "vybraný model" instead of "nasazený model". |
| `results/ipp1-final.md:3`, sentence "Recipe choices use 5-fold GroupKFold inside the development set only; the locked set was scored once, ..." | The 30 discharges were set aside before the final models were trained and were scored once. The recipe `candidate` was chosen earlier by 5-fold cross validation over all 149 discharges (`analysis/ipp1_improve.py`, `results/ipp1-improve.md`), so these 30 took part in that choice; the choice among the four recipes below used the 119 development discharges only. |
| `results/ipp1-final.md:46` | No recipe was changed after the locked numbers were seen, but the candidate recipe itself was selected on all 149 discharges, including these 30, before they were set aside. |
| `presentation/outline.md:12`, `pitch-script.md:166`, `docs/deck-fixes.md:11` | already forbid the words "zamčená" and "nikdo neviděl"; add: "Postup byl vybrán dříve na všech 149 výbojích" to the spoken answer N2 (it says so already at `pitch-script.md:226`). |
| `README.md`, `docs/REQUIREMENTS.md` | mine, fixed |
