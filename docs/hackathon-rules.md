# CVUT ML Hackathon 2026 - public rules research

Date seen for all rows: 2026-10-23. Only public pages were opened (no logins, forms or downloads).

IMPORTANT: the official page calls the event "Hackathon ML/AI 2026". It is run by the Department of Software Engineering (KSI) of FJFI CTU, in Decin, and is aimed at secondary-school students. The COMPASS tasks sit in the organisers' repository. Confirm this is the event in the brief.

| Question | Answer | Source URL | Date seen | Confidence |
|---|---|---|---|---|
| Official event page | KSI FJFI page "Hackathon ML/AI 2026" (linked from the KSI calendar nodes 1390 and 1483, 23-24 Oct 2026) | https://ksi.fjfi.cvut.cz/udalosti/hackathon-mlai-2026 | 2026-10-23 | high |
| Organiser and venue | Dept. of Software Engineering, FJFI CTU. Location: Decin. No room or building given. Teams sleep in the classroom (sleeping bag and mat) | https://ksi.fjfi.cvut.cz/udalosti/hackathon-mlai-2026 | 2026-10-23 | high |
| Who competes | Secondary-school students, teams of 2 to 4, basic programming, Python recommended | same | 2026-10-23 | high |
| Dates and times | Fri 23 Oct 2026 14:00 to Sat 24 Oct 2026 17:00 (estimated end 16:30-17:00). Check-in 14:00-16:00; hackathon start 16:00 | same | 2026-10-23 | high |
| Friday schedule | Optional ML intro 14:30-15:30; topics presented 15:30-16:00; start 16:00; dinner 18:00-19:00 | same | 2026-10-23 | high |
| Saturday schedule | Breakfast 7:30-9:00; lunch 12:00-13:00; work ends and presentations are submitted 14:00; presentations 14:30-16:30; results and prizes after | same | 2026-10-23 | high |
| Presentation length | At most 15 minutes per team, drawn order | same | 2026-10-23 | high |
| Q and A length | UNKNOWN | - | 2026-10-23 | high |
| Room for presentations / projector / how a demo laptop connects | UNKNOWN | - | 2026-10-23 | high |
| Exact submission deadline | Sat 24 Oct 2026 14:00 ("results and presentation") | same | 2026-10-23 | high |
| HOW to submit (upload, e-mail, repo link, Drive folder) | UNKNOWN. The page does not say. The 2025 edition page is equally silent | https://ksi.fjfi.cvut.cz/udalosti/hackathon-mlai-2025 | 2026-10-23 | high |
| What must be submitted; length, size and format limits | Only "results and presentation" is stated. Notebooks, slides, video, size and format limits: UNKNOWN | https://ksi.fjfi.cvut.cz/udalosti/hackathon-mlai-2026 | 2026-10-23 | high |
| Judging criteria and weights | An expert committee judges after the presentations. Criteria and weights: UNKNOWN (not published; the intro says teams compete for "the best program or model") | same | 2026-10-23 | high |
| Rules | Organisers may remove a team for inappropriate behaviour or suspected drug use. Registering means consent to photo and video for promotion and documentation | same | 2026-10-23 | high |
| Data confidentiality | UNKNOWN. Neither the event page nor the repo README states any rule | same + repo README | 2026-10-23 | high |
| Prizes | 1st 25,000 CZK, 2nd 15,000 CZK, 3rd 10,000 CZK (supported by the Usti Region) | https://ksi.fjfi.cvut.cz/udalosti/hackathon-mlai-2026 | 2026-10-23 | high |
| Are results shown publicly | Results and prizes are announced at the event after the presentations. The 2025 page lists winners publicly. Whether 2026 results go online: UNKNOWN | https://ksi.fjfi.cvut.cz/udalosti/hackathon-mlai-2025 | 2026-10-23 | medium |
| Task topics | Announced Friday before the start; the event page does not list them | https://ksi.fjfi.cvut.cz/udalosti/hackathon-mlai-2026 | 2026-10-23 | high |
| Partners | Usti Region, City of Decin, Autodesk, IT Decin | same | 2026-10-23 | high |
| Contacts | Technical: RNDr. Petr Kubera, Ph.D., [e-mail on the official page], [phone on the official page]. Organisational: Helena Hauzirkova, [e-mail on the official page], [phone on the official page]| same | 2026-10-23 | high |
| Organisers' COMPASS repo: what it is | GitLab project "CVUT ML Hackaton 2026 COMPASS", owner Jakub Seidl, created 12 Oct 2026, 9 commits, 1 branch. Setup-only README (Czech): clone, pixi or pip venv, run Jupyter notebooks in `notebooks/`. No rules, deadline, metric or submission info | https://repo.tok.ipp.cas.cz/seidl/cvut-ml-hackaton-2026-compass (README: .../-/raw/master/README.md) | 2026-10-23 | high |
| Repo file list (via the public GitLab tree API, listing only) | `.gitattributes`, `.gitignore`, `README.md`, `pixi.lock`, `pyproject.toml`, `src/cvut_ml_hackaton_2026_compass/__init__.py`, `notebooks/`: `.gitkeep`, `COMPASS_stena.csv`, 4 plasma-shape PNGs, `uloha-1-ekvilibrium-nacteni-dat.ipynb`, `uloha-2-ubihajici_elektrony-nacteni-dat.ipynb` | https://repo.tok.ipp.cas.cz/api/v4/projects/seidl%2Fcvut-ml-hackaton-2026-compass/repository/tree | 2026-10-23 | high |
| Task 1 (equilibrium) as described in the public notebook | Predict plasma shape and position parameters from magnetic diagnostics; optional use of fast-camera (Photron) images. Data files (`uloha_1-magneticka_data.zip`, Photron zip ~1.5 GB) are NOT in the repo; notebook expects `./data/`. `equil_data.csv` (low noise) and `equil_data_noisy.csv`, 42,972 rows x 57 columns, 149 anonymised discharges. Inputs: 16 integrated partial Rogowski coils (IPR01-16) and 8 flux loops (FL01-08). Targets: 31 columns; main ones are is_limited, plasma_current, R/Z magnetic axis, elongation, triangularity, X-point, two strike points, limiter point. Notebook defines no metric and no submission format | https://repo.tok.ipp.cas.cz/seidl/cvut-ml-hackaton-2026-compass/-/raw/master/notebooks/uloha-1-ekvilibrium-nacteni-dat.ipynb (only the first 100,000 of 346,346 characters read) | 2026-10-23 | medium |
| Task 2 (runaway electrons) | Notebook `uloha-2-ubihajici_elektrony-nacteni-dat.ipynb` exists; content NOT read | file list above | 2026-10-23 | low |

Context from the previous edition (2025), for orientation only, not a rule for 2026: same schedule pattern, 15 minutes per team, expert committee, same three prizes (https://ksi.fjfi.cvut.cz/udalosti/hackathon-mlai-2025).

## Public COMPASS and IPP references

| Title | URL | Why a jury may know it |
|---|---|---|
| COMPASS Tokamak (IPP CAS page; R 0.56 m, a 0.23 m, Ip max 400 kA, D-shaped, SND, ~1 s pulses) | https://www.ipp.cas.cz/vedecka_struktura_ufp/tokamak/COMPASS/ | The institute's own device page; the data in the task comes from this machine |
| COMPASS magnetic diagnostics (over 400 coils; flux loops, saddle loops and internal partial Rogowski coils feed real-time control and EFIT) | https://www.ipp.cas.cz/vedecka_struktura_ufp/tokamak/COMPASS/magnetic-diagnostics.html | Describes exactly the sensor families in the task inputs (IPR, FL) and how EFIT uses them |
| Urban et al., "Validation of equilibrium tools on the COMPASS tokamak" (arXiv 1412.1924, 2014) | https://arxiv.org/abs/1412.1924 | Benchmarks EFIT++, FREEBIE and VacTH on COMPASS; the standard citation for classical reconstruction here |
| Janky et al., "Upgrade of the COMPASS tokamak real-time control system", Fusion Eng. Des. 89(3), 2014 (co-author Jakub Seidl, owner of the hackathon repo) | https://asep.lib.cas.cz/arl-cav/cs/detail-cav_un_epca-0436059-Upgrade-of-the-COMPASS-tokamak-realtime-control-system | Real-time control system (MARTe framework) in the keywords; the jury may include its authors |
| Hron et al., "Overview of the COMPASS CODAC system", Fusion Eng. Des. 89(3), 2014 | https://asep.lib.cas.cz/arl-cav/en/detail-cav_un_epca-0428443-Overview-of-the-COMPASS-CODAC-system | Overview of the COMPASS control and data acquisition; context for real-time use |
| Janky et al., "Determination of the plasma position for its real-time control in the COMPASS tokamak", Fusion Eng. Des. 86, 2011 | https://asep.lib.cas.cz/arl-cav/en/detail-cav_un_epca-0367371-Determination-of-the-plasma-position-for-its-realtime-control-in-the-COMPASS-tokamak/ | The real-time position reconstruction that a learned model would compete with |
| Windsor et al., "Real-time electronic neural networks for ITER-like multiparameter equilibrium reconstruction and control in COMPASS-D" | https://scientific-publications.ukaea.uk/papers/real-time-electronic-neural-networks-for-iter-like-multiparameter-equilibrium-reconstructioncontrol-in-compass-d/ | Earlier neural-network reconstruction on the same tokamak (up to 48 magnetic inputs, 75 kHz); good prior-art line for a slide |
| Entler et al., "Tokamak COMPASS" (2020 popular overview) | https://asep.lib.cas.cz/arl-cav/en/detail-cav_un_epca-0525287-Tokamak-COMPASS/ | Short Czech overview of the machine |

Only title/author/abstract-level information was read for these; no full texts. Search-result claims that a paper describes "MARTe cycles of 500 and 50 microseconds" came from search snippets, not from a page I opened, so they are not used above.

## What we must still ask the organisers

1. How exactly do we submit (upload link, e-mail, repository URL, shared Drive folder), and to whom? What counts as "submitted" at 14:00 Saturday?
2. What must be in the submission (notebook, slides, model files, video) and are there size or format limits?
3. Is the deadline hard, and is anything allowed to change after 14:00 (for example fixing the slides while waiting)?
4. Judging criteria and weights for the COMPASS equilibrium task: which metric, which test set, are the targets of the hidden test discharges scored automatically, and is model accuracy weighed against presentation?
5. Presentation: Q and A length, room, projector connection (HDMI, USB-C, wireless), is a team laptop allowed, are slides loaded from a shared machine?
6. Data confidentiality: may the COMPASS data and results be published, kept after the event, shown on a team's own portfolio or posted online?
7. May teams use external pretrained models, online AI tools and internet during the event?
8. Are results (placement, scores) shown publicly, and are the teams' projects published afterwards?
9. Where do we get the task data (the zips are not in the repo): download link and any access code?
10. Is "ML Hackathon 2026" in the brief the same event as the KSI "Hackathon ML/AI 2026" in Decin (secondary-school category)?
