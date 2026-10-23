# Cloud brief: camera model for IPP task 1 (independent second attempt)

Hackathon: CVUT ML Hackathon 2026, ends Sat 24 Oct 2026 14:00 CEST. Task IPP 1: the plasma shape of the tokamak COMPASS.
The magnetic model is done (0.06 to 0.4 mm on most parameters, `results/ipp1-baseline.md`). You build the **camera model**.
Another agent (GPT, lane R) also works on it locally; you are an independent second attempt, so write only new files named
`cloud_camera*` and work on your own branch `cloud/camera`.

1. Read `CLAUDE.md`, `README.md`, `docs/PLAN.md`, `docs/REQUIREMENTS.md`, `docs/internal/WORKERS.md`. Use `analysis/ipp1_common.py`
   (load, group_folds, fit_mlp, score, TARGETS, UNIT). Protocol: 5-fold GroupKFold by whole discharges, masked loss for targets
   that exist in one configuration only, errors in mm and kA and relative to the spread.
2. Data (confidential, IPP, only for this hackathon): never commit it, never print raw rows, never send it anywhere.
   Download with gdown into a folder you choose and point `HACKATHON_HOME` at it (layout in `README.md`): the magnetic zip,
   Drive file id `1MBev-lb4l5Z7m33PeRJ4sjHQmeN5ELVp` (37 MB, `equil_data.csv`), and the camera zip, file id
   `1JvBiTYtuu7gTNjrpCjIogFlpW-QUl3yt` (876 MB: JPEGs plus a CSV mapping images to discharge and time). Each into its own new
   empty folder; check zip entry names for absolute or parent paths first. Install gdown pandas torch torchvision scikit-learn
   matplotlib pillow.
3. `analysis/cloud_camera_prepare.py`: match every image to a row of `equil_data.csv` by discharge and time as the organizers'
   notebook describes (https://repo.tok.ipp.cas.cz/seidl/cvut-ml-hackaton-2026-compass/-/raw/master/notebooks/uloha-1-ekvilibrium-nacteni-dat.ipynb:
   interpolate the equilibrium in time), downscale to small grayscale and colour arrays, cache outside git.
   `analysis/cloud_camera_model.py`: a small convolutional network for the 15 main shape parameters; compare with
   `results/ipp1-baseline.md`. Then colour against black and white (REQ-B03), shifted or rotated images (REQ-B05), accuracy against
   the number of training images, and a multimodal model that adds the 24 magnetic inputs (REQ-B01). There may be no GPU: size
   the images and the network so a run takes minutes and report the timings.
4. Outputs: `results/cloud-camera-findings.md` (numbers per target, what the camera can and cannot do, honest limits) and figures
   in `results/`. Small Conventional Commits on `cloud/camera`, stage files explicitly (never data or arrays), push, open a pull
   request, do not merge. Push intermediate results at least every 45 minutes; the Lead integrates around 22:00 Fri and 08:00 Sat.
5. Report evidence only: the command and the number you saw. Talk to the user in Czech, write files in English.
