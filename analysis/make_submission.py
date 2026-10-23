#!/usr/bin/env python
"""Build the clean submission package and check that it holds no data and no secrets.

    ~/.venvs/hackathon/bin/python -I analysis/make_submission.py [--out /tmp/hackathon-submission]
        [--deck-pdf PATH] [--video PATH] [--zip]

Package layout mirrors the repository, so the notebooks still find analysis/ipp1_common.py:
README.md, PACKAGE-README.md, notebooks/, analysis/, results/, presentation/slides.pptx (+ slides.pdf), video/ (if given), model/ (the exported shipped model, if
hackathon/out/model exists: see --model-dir), MANIFEST.txt.
Exit code 0 = package built and every check passed (missing optional items are listed but do not fail the run),
1 = a check failed (data or secret found, notebook with an error, placeholder or data-sized table in the deck).
Needs no data and no packages beyond the standard library. Nothing is uploaded or sent anywhere.
"""
import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MARKER = ".hackathon-submission-build"  # only a folder carrying this file may be wiped and rebuilt

# Never allowed anywhere in the package: raw data and bulk binaries (CON-001). Images are limited to png in results/.
FORBIDDEN_EXT = {".csv", ".tsv", ".npy", ".npz", ".zip", ".jpg", ".jpeg", ".parquet", ".pkl", ".pickle", ".pt", ".pth",
                 ".h5", ".hdf5", ".feather", ".xlsx", ".mat"}
SECRET_RE = re.compile(r"sk-ant-[\w-]{10,}|ghp_[A-Za-z0-9]{20,}|github_pat_\w{20,}|AKIA[0-9A-Z]{16}|"
                       r"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?i:(api[_-]?key|secret|token|passwd|password))\s*[=:]\s*['\"]?[\w\-]{16,}")
NUMBER_ROW_RE = re.compile(r"(?:-?\d+\.\d+(?:e[+-]?\d+)?\s*,\s*){19,}-?\d+")  # 20+ comma-separated numbers = a data row
# The one derived binary that is allowed: the weights of the shipped model (model/ipp1-selected.npz), for the organizers only. Exactly this path, at most 2 MB.
ALLOWED_BINARIES = {"model/ipp1-selected.npz": 2 * 2**20}
MODEL_FILES = ("ipp1-selected.npz", "ipp1-selected.json")
MAX_FILE_MB = 25
MAX_TOTAL_MB = 100
TEXT_EXT = {".md", ".py", ".txt", ".json", ".ipynb", ".html", ".js", ".css", ".svg", ".xml"}
# A chart in the deck holds a handful of aggregate points; thousands of points or rows would be measured data.
MAX_CHART_POINTS = 200
# Public-facing files that are not copied into the package but are scanned in place.
SCAN_IN_PLACE = [REPO / "viewer/index.html"]
# Figures that show individual discharges and that no script can recognise (audit H-1); the owner decides with ÚFP.
FIGURES_TO_CONFIRM = [
    "presentation/assets/viewer-*.png and the deck images that equal them: reference and estimated values of one set-aside discharge (85, its worst end 147)",
    "results/ipp1-time.png, middle and right panels: the error trace of one discharge",
    "results/ipp1-unusual-shapes.png, left panel: one dot per discharge (median elongation and triangularity)",
    "notebooks/01_data_exploration.ipynb cell 14: six true signals of one discharge; notebooks/04 cell 11: true traces of two discharges",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def copy(src: Path, dst: Path, log: list):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log.append(dst)


def export_pdf(pptx: Path, out_dir: Path):
    """PDF of the deck with LibreOffice if present; None otherwise (Keynote / PowerPoint export is the owner's step)."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx)],
                   check=True, capture_output=True, timeout=300)
    pdf = out_dir / (pptx.stem + ".pdf")
    return pdf if pdf.exists() else None


def check_notebooks(nbs):
    problems, notes = [], []
    for nb in nbs:
        d = json.loads(nb.read_text())
        code = [c for c in d["cells"] if c["cell_type"] == "code"]
        unexecuted = sum(1 for c in code if not c.get("execution_count"))
        errors = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
        if errors:
            problems.append(f"{nb.name}: {errors} cell(s) with an error output")
        if unexecuted:
            problems.append(f"{nb.name}: {unexecuted} of {len(code)} code cells have no stored output")
        if "/Users/" in nb.read_text():
            problems.append(f"{nb.name}: contains an absolute /Users/ path")
        notes.append(f"{nb.name}: {len(code)} code cells, stored outputs present")
    return problems, notes


def scan_deck(pptx: Path):
    """Return (failures, warnings) for the deck, read as a zip so that python-pptx is not needed.

    Looks at everything the jury can open: slide, notes and chart text for placeholders, secrets and home paths;
    chart series and embedded workbooks for data-sized tables; the media for forbidden types. The pictures themselves
    are not inspected; they are listed so that the owner confirms them (FIGURES_TO_CONFIRM).
    """
    fails, warns = [], []
    with zipfile.ZipFile(pptx) as z:
        names = z.namelist()
        for n in names:
            low = n.lower()
            if low.startswith("ppt/media/") and Path(low).suffix in FORBIDDEN_EXT:
                fails.append(f"deck: forbidden file type inside: {n}")
            elif low.startswith("ppt/embeddings/") and low.endswith(".xlsx"):
                with zipfile.ZipFile(io.BytesIO(z.read(n))) as wb:
                    rows = sum(len(re.findall(r"<row ", wb.read(m).decode("utf8", "replace")))
                               for m in wb.namelist() if m.startswith("xl/worksheets/sheet"))
                if rows > MAX_CHART_POINTS:
                    fails.append(f"deck: embedded workbook {n} has {rows} rows (a chart needs a few)")
            elif low.startswith("ppt/embeddings/"):
                fails.append(f"deck: embedded file of an unchecked type: {n}")
            if not low.endswith(".xml"):
                continue
            xml = z.read(n).decode("utf8", "replace")
            text = " ".join(re.findall(r"<a:t>([^<]*)</a:t>", xml)) if low.startswith("ppt/slides/slide") or \
                low.startswith("ppt/notesslides/") else ""
            where = f"slide {m.group(1)}" if (m := re.search(r"slide(\d+)\.xml$", low)) and "notes" not in low else n
            if text and re.search(r"DOPLNIT|TODO|XXX|lorem|\[\[", text, re.I):
                fails.append(f"deck: placeholder in {where}")
            if SECRET_RE.search(xml) or "/Users/" in xml:
                fails.append(f"deck: secret or home path in {n}")
            if low.startswith("ppt/charts/chart"):
                points = max((len(re.findall(r"<c:pt ", c)) for c in re.findall(r"<c:numCache>.*?</c:numCache>", xml, re.S)),
                             default=0)
                if points > MAX_CHART_POINTS:
                    fails.append(f"deck: chart {n} has a series of {points} points")
        media = [n for n in names if n.lower().startswith("ppt/media/")]
        stills = {hashlib.sha256((REPO / "presentation/assets" / f.name).read_bytes()).hexdigest(): f.name
                  for f in (REPO / "presentation/assets").glob("viewer-*.png")}
        shown = [f"{n} = {stills[h]}" for n in media if (h := hashlib.sha256(z.read(n)).hexdigest()) in stills]
        warns.append(f"deck: {len(media)} images not inspected by this script; viewer stills inside: "
                     f"{', '.join(shown) or 'none'}")
    return fails, warns


def scan(pkg: Path):
    """Return (failures, warnings, total_bytes) for the built package."""
    fails, warns, total = [], [], 0
    for p in sorted(pkg.rglob("*")):
        if not p.is_file() or p.name == MARKER:
            continue
        rel = p.relative_to(pkg)
        size = p.stat().st_size
        total += size
        ext = p.suffix.lower()
        if ext in FORBIDDEN_EXT and not (rel.as_posix() in ALLOWED_BINARIES and size <= ALLOWED_BINARIES[rel.as_posix()]):
            fails.append(f"forbidden file type: {rel}")
        if ext in {".png"} and rel.parts[0] != "results":
            warns.append(f"png outside results/: {rel}")
        if size > MAX_FILE_MB * 2**20:
            warns.append(f"large file ({size / 2**20:.1f} MB): {rel}")
        if ext in TEXT_EXT:
            text = p.read_text(errors="replace")
            if SECRET_RE.search(text):
                fails.append(f"possible secret: {rel}")
            if NUMBER_ROW_RE.search(text):
                fails.append(f"looks like a raw data row (20+ comma-separated numbers): {rel}")
            if "/Users/" in text and rel.name not in ("make_submission.py", "check_notebooks.py"):  # these files hold the string as a check
                warns.append(f"absolute /Users/ path (audit H-3): {rel}")
            if ext == ".ipynb" and re.search(r'"(?:equil_data|camera_data)[^"]*\.csv"', text) and "image/png" not in text:
                warns.append(f"notebook mentions a data file but stores no figures: {rel}")
    if total > MAX_TOTAL_MB * 2**20:
        warns.append(f"package is {total / 2**20:.1f} MB (limit assumed {MAX_TOTAL_MB} MB; the channel's real limit is unknown)")
    return fails, warns, total


def scan_in_place():
    """Same text checks for public-facing repository files that the package does not copy."""
    fails = []
    for p in SCAN_IN_PLACE:
        if not p.exists():
            fails.append(f"expected file missing: {p.relative_to(REPO)}")
            continue
        text = p.read_text(errors="replace")
        if SECRET_RE.search(text) or NUMBER_ROW_RE.search(text) or "/Users/" in text:
            fails.append(f"secret, data row or home path in {p.relative_to(REPO)}")
        if p.stat().st_size > 2**20:
            fails.append(f"{p.relative_to(REPO)} is over 1 MB: it must not embed data")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/hackathon-submission")
    ap.add_argument("--deck", default=str(REPO / "presentation/deck/slides.pptx"))
    ap.add_argument("--deck-pdf", help="PDF exported by hand from PowerPoint or Keynote (used when LibreOffice is absent)")
    ap.add_argument("--video", help="the presentation video file; copied into video/ only if given")
    ap.add_argument("--zip", action="store_true", help="also write <out>.zip next to the folder")
    ap.add_argument("--model-dir", default=str(REPO.parent / "out" / "model"), help="the folder with ipp1-selected.npz and .json made by analysis/export_model.py (default: ../out/model next to the repository)")
    a = ap.parse_args()

    out = Path(a.out)
    if out.exists():
        if not (out / MARKER).exists():
            sys.exit(f"refusing to wipe {out}: it was not created by this script (no {MARKER})")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARKER).write_text("built by analysis/make_submission.py\n")

    log, missing, deck_fails, deck_warns = [], [], [], []
    copy(REPO / "README.md", out / "README.md", log)
    nbs = sorted((REPO / "notebooks").glob("*.ipynb"))
    for nb in nbs:
        copy(nb, out / "notebooks" / nb.name, log)
    for py in sorted((REPO / "analysis").glob("*.py")):
        copy(py, out / "analysis" / py.name, log)
    for ext in ("*.md", "*.png", "*.json", "*.txt"):
        for f in sorted((REPO / "results").glob(ext)):
            copy(f, out / "results" / f.name, log)

    model_dir, have_model = Path(a.model_dir), False
    if all((model_dir / f).exists() for f in MODEL_FILES):
        for f in MODEL_FILES:
            copy(model_dir / f, out / "model" / f, log)
        have_model = True
        size = sum((out / "model" / f).stat().st_size for f in MODEL_FILES)
        (out / "PACKAGE-README.md").write_text(
            "# Package note: the model files\n\n"
            f"`model/ipp1-selected.npz` and `model/ipp1-selected.json` ({size / 1e6:.2f} MB) are the weights of the shipped model, trained on the 119 development discharges (`analysis/export_model.py`). "
            "**They are derived from the confidential IPP data and are included for the organizers only; they must not be published.** "
            "The package contains **no data rows and no sample CSV**: the organizers have the data, and `analysis/predict.py` (numpy only) reads any CSV with the columns IPR01..IPR16 and FL01..FL08, e.g. "
            "`python analysis/predict.py input.csv` (it finds `model/ipp1-selected.npz` next to `analysis/`; `--model` names another file). "
            "`analysis/check_predict.py` and notebook 09 need the raw data and write their own temporary CSV from it; they are not meant to run inside this package without the data.\n")
    else:
        missing.append(f"model files ({model_dir}: run analysis/export_model.py)")

    deck = Path(a.deck)
    if deck.exists():
        copy(deck, out / "presentation/slides.pptx", log)
        deck_fails, deck_warns = scan_deck(deck)
        pdf = Path(a.deck_pdf) if a.deck_pdf else export_pdf(out / "presentation/slides.pptx", out / "presentation")
        if pdf and pdf.exists():
            if pdf.parent != out / "presentation":
                copy(pdf, out / "presentation/slides.pdf", log)
        else:
            missing.append("deck PDF (no LibreOffice here; export from PowerPoint/Keynote and pass --deck-pdf)")
    else:
        missing.append(f"deck pptx ({deck})")
    if a.video:
        v = Path(a.video)
        if v.exists():
            copy(v, out / "video" / v.name, log)
        else:
            missing.append(f"video file not found: {v}")
    else:
        missing.append("presentation video (pass --video PATH; not in the repository)")

    nb_problems, nb_notes = check_notebooks(nbs)
    # The video is the one allowed large binary; scan everything else.
    fails, warns, total = scan(out)
    fails = [f"notebook: {p}" for p in nb_problems] + deck_fails + scan_in_place() + fails
    warns = deck_warns + warns

    lines = [f"{sha(p)}  {p.stat().st_size:>9}  {p.relative_to(out)}" for p in sorted(out.rglob("*"))
             if p.is_file() and p.name not in (MARKER, "MANIFEST.txt")]
    (out / "MANIFEST.txt").write_text("sha256[:16]  bytes  path\n" + "\n".join(lines) + "\n")

    print(f"package: {out}  ({len([p for p in out.rglob('*') if p.is_file()])} files, {total / 2**20:.2f} MB)")
    for n in nb_notes:
        print("  ", n)
    print("MISSING:" if missing else "MISSING: nothing")
    for m in missing:
        print("  -", m)
    print("WARNINGS:" if warns else "WARNINGS: none")
    for w in warns:
        print("  -", w)
    print("FAILED CHECKS:" if fails else "FAILED CHECKS: none (no forbidden file types, no secrets, no data rows, "
          "deck and viewer page scanned)")
    for f in fails:
        print("  -", f)
    print("OWNER MUST CONFIRM (CON-001, figures no script can check; the package is not safe to make public until then):")
    for f in FIGURES_TO_CONFIRM:
        print("  -", f)

    if a.zip and not fails:
        zpath = out.with_suffix(".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(out.rglob("*")):
                if p.is_file() and p.name != MARKER:
                    z.write(p, Path(out.name) / p.relative_to(out))
        print(f"zip: {zpath} ({zpath.stat().st_size / 2**20:.2f} MB)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
