#!/usr/bin/env python
"""Build the clean submission package and check that it holds no data and no secrets.

    ~/.venvs/hackathon/bin/python -I analysis/make_submission.py [--out /tmp/hackathon-submission]
        [--deck-pdf PATH] [--video PATH] [--zip]

Package layout mirrors the repository, so the notebooks still find analysis/ipp1_common.py:
README.md, notebooks/, analysis/, results/, presentation/slides.pptx (+ slides.pdf), video/ (if given), MANIFEST.txt.
Exit code 0 = package built and every check passed (missing optional items are listed but do not fail the run),
1 = a check failed (data or secret found, notebook with an error). Nothing is uploaded or sent anywhere.
"""
import argparse
import hashlib
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
MAX_FILE_MB = 25
MAX_TOTAL_MB = 100


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


def deck_placeholders(pptx: Path):
    """Slides that still carry a placeholder (DOPLNIT, TODO, XXX); needs python-pptx, skipped without it."""
    try:
        from pptx import Presentation
    except ImportError:
        return ["python-pptx not importable, placeholders in the deck not checked"]
    hits = []
    for i, slide in enumerate(Presentation(str(pptx)).slides, 1):
        text = " ".join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)
        if re.search(r"DOPLNIT|TODO|XXX|lorem", text, re.I):
            hits.append(f"slide {i} still has a placeholder")
    return hits


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
        if ext in FORBIDDEN_EXT:
            fails.append(f"forbidden file type: {rel}")
        if ext in {".png"} and rel.parts[0] != "results":
            warns.append(f"png outside results/: {rel}")
        if size > MAX_FILE_MB * 2**20:
            warns.append(f"large file ({size / 2**20:.1f} MB): {rel}")
        if ext in {".md", ".py", ".txt", ".json", ".ipynb"}:
            text = p.read_text(errors="replace")
            if SECRET_RE.search(text):
                fails.append(f"possible secret: {rel}")
            if NUMBER_ROW_RE.search(text):
                fails.append(f"looks like a raw data row (20+ comma-separated numbers): {rel}")
            if ext == ".ipynb" and re.search(r'"(?:equil_data|camera_data)[^"]*\.csv"', text) and "image/png" not in text:
                warns.append(f"notebook mentions a data file but stores no figures: {rel}")
    if total > MAX_TOTAL_MB * 2**20:
        warns.append(f"package is {total / 2**20:.1f} MB (limit assumed {MAX_TOTAL_MB} MB; the channel's real limit is unknown)")
    return fails, warns, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/hackathon-submission")
    ap.add_argument("--deck", default=str(REPO / "presentation/deck/slides.pptx"))
    ap.add_argument("--deck-pdf", help="PDF exported by hand from PowerPoint or Keynote (used when LibreOffice is absent)")
    ap.add_argument("--video", help="the presentation video file; copied into video/ only if given")
    ap.add_argument("--zip", action="store_true", help="also write <out>.zip next to the folder")
    a = ap.parse_args()

    out = Path(a.out)
    if out.exists():
        if not (out / MARKER).exists():
            sys.exit(f"refusing to wipe {out}: it was not created by this script (no {MARKER})")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARKER).write_text("built by analysis/make_submission.py\n")

    log, missing = [], []
    copy(REPO / "README.md", out / "README.md", log)
    nbs = sorted((REPO / "notebooks").glob("*.ipynb"))
    for nb in nbs:
        copy(nb, out / "notebooks" / nb.name, log)
    for py in sorted((REPO / "analysis").glob("*.py")):
        copy(py, out / "analysis" / py.name, log)
    for ext in ("*.md", "*.png", "*.json", "*.txt"):
        for f in sorted((REPO / "results").glob(ext)):
            copy(f, out / "results" / f.name, log)

    deck = Path(a.deck)
    if deck.exists():
        copy(deck, out / "presentation/slides.pptx", log)
        missing += deck_placeholders(deck)
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
    fails = [f"notebook: {p}" for p in nb_problems] + fails

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
    print("FAILED CHECKS:" if fails else "FAILED CHECKS: none (no forbidden file types, no secrets, no data rows)")
    for f in fails:
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
