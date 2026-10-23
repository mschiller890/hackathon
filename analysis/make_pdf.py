#!/usr/bin/env python
"""Turn a markdown file into a clean A4 PDF through headless Chrome.

    ~/.venvs/hackathon/bin/python analysis/make_pdf.py in.md out/overview.pdf

Images in the markdown resolve relative to the markdown file.
"""
import argparse
import re
import subprocess
import tempfile
from pathlib import Path

import markdown

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.5; color: #1a1d23; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 24pt; line-height: 1.15; margin: 0 0 4mm; letter-spacing: -0.01em; }
h2 { font-size: 15pt; margin: 8mm 0 2mm; padding-bottom: 1.5mm; border-bottom: 1.5px solid #d9dde4; }
h3 { font-size: 12pt; margin: 5mm 0 1.5mm; }
p, ul, ol { margin: 0 0 3mm; }
li { margin-bottom: 1mm; }
table { border-collapse: collapse; width: 100%; margin: 3mm 0 5mm; font-size: 9.5pt; }
th, td { border: 1px solid #d9dde4; padding: 1.6mm 2.4mm; text-align: left; vertical-align: top; }
th { background: #f1f3f7; }
tr:nth-child(even) td { background: #fafbfc; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 9pt; background: #f1f3f7; padding: 0 1mm; border-radius: 1mm; }
pre { background: #f1f3f7; padding: 3mm; border-radius: 2mm; overflow-wrap: anywhere; white-space: pre-wrap; }
pre code { background: none; padding: 0; }
img { max-width: 100%; height: auto; }
blockquote { margin: 3mm 0; padding: 1mm 4mm; border-left: 3px solid #8aa0ff; color: #3b4252; }
h1, h2, h3, table, img, pre { break-inside: avoid; }
h1, h2, h3 { break-after: avoid; }
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dest")
    a = ap.parse_args()
    src = Path(a.src).expanduser().resolve()
    dest = Path(a.dest).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists"])
    title = (re.search(r"^#\s+(.+)$", src.read_text(encoding="utf-8"), re.M) or [None, src.stem])[1]
    page = (f'<!doctype html><html lang="cs"><head><meta charset="utf-8"><title>{title}</title>'
            f'<base href="{src.parent.as_uri()}/"><style>{CSS}</style></head><body>{body}</body></html>')
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "page.html"
        html.write_text(page, encoding="utf-8")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={tmp}/profile", f"--print-to-pdf={dest}", html.as_uri()],
                       check=True, timeout=120, capture_output=True)
    pages = len(re.findall(rb"/Type\s*/Page[^s]", dest.read_bytes()))
    print(f"wrote {dest} ({dest.stat().st_size // 1024} KB, {pages} pages)")


if __name__ == "__main__":
    main()
