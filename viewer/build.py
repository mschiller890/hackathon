#!/usr/bin/env python
"""Build viewer/dist/index.html: the viewer and its data inlined into one file that opens by double click.

    python viewer/build.py            (run analysis/export_viewer_data.py first)

The result holds the IPP data, so it never leaves the participants' computers and is gitignored (CON-001).
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
html = (HERE / "index.html").read_text(encoding="utf-8")
data = (HERE / "data.js").read_text(encoding="utf-8")
tag = '<script src="data.js"></script>'
assert html.count(tag) == 1 and "</script" not in data, "unexpected page or data"
out = HERE / "dist" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html.replace(tag, "<script>\n" + data + "</script>"), encoding="utf-8")
print(f"wrote {out}: {out.stat().st_size / 1e6:.1f} MB")
