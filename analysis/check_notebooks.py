"""Static checks of the executed notebooks before the hand-in. Prints FAIL and WARNING lines; exit code 1 on any FAIL.

    python analysis/check_notebooks.py [notebooks/01_data_exploration.ipynb ...]   (default: notebooks/*.ipynb)

FAIL: an error output; an absolute path in a cell or an output; the words DOPLNIT, TODO, ground truth, nobody saw,
important sensors, quiet run, 0,18 / 0.18 ms; 'locked' used outside the name 'locked test set'; accurate / accuracy in a
paragraph that says neither 'agreement' nor 'reference'; 'real-time' in a paragraph without a conditional marker.
WARNING (best effort): a number in the markdown of 04, 05 or 09 that is neither in a cell output nor in results/*.md.
Writes nothing; needs nbformat only besides the standard library.
"""
import re
import sys
from pathlib import Path

import nbformat

REPO = Path(__file__).resolve().parents[1]
files = [Path(a) for a in sys.argv[1:]] or sorted((REPO / "notebooks").glob("*.ipynb"))
PATH = re.compile(r"(/Users/|/home/|[A-Za-z]:\\)")
BANNED = [("DOPLNIT", r"DOPLNIT"), ("TODO", r"\bTODO\b"), ("ground truth", r"ground[ -]truth"), ("nobody saw", r"nobody (?:ever )?saw|nikdo nevid"),
          ("important sensors", r"important sensors"), ("quiet run", r"quiet run|quieter machine"), ("0,18 estimate", r"0[.,]18 ?ms|0[.,]1775")]
LOCKED = re.compile(r"\blocked\b(?! test set| test|-test-ids)", re.I)   # "ipp1-locked-test-ids.txt" is a file name, not a claim
ACC = re.compile(r"\baccura(?:te|cy)\b", re.I)
AGREE = re.compile(r"agree|reference|misclassif|classif|flag|is_limited|rows are wrong|wrongly", re.I)
RT = re.compile(r"real[- ]time|reálném čase", re.I)
COND = re.compile(r"conditional|not verified|only the network computation|only the forward pass|forward pass|not a guarantee|no real-time guarantee|without real-time guarantees|real-time system|did not test|not tested|nezkouš", re.I)
NUM = re.compile(r"(?<![\w.])(\d+[.,]\d+)(?![\w])")


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def out_text(cell):
    t = []
    for o in cell.get("outputs", []):
        if o.get("output_type") == "stream":
            t.append(o.get("text", ""))
        elif "data" in o:
            for k in ("text/plain", "text/markdown", "text/html"):
                if k in o["data"]:
                    t.append("".join(o["data"][k]) if isinstance(o["data"][k], list) else o["data"][k])
        elif o.get("output_type") == "error":
            t.append("")
    return "\n".join(t)


def floats(text):
    return [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?", text)]


results_text = [r.read_text(errors="ignore") for r in (REPO / "results").glob("*.md")]
fails, warns = [], []
for f in files:
    nb = nbformat.read(f, 4)
    name = f.name
    outs = ""
    for i, c in enumerate(nb.cells):
        if c.cell_type != "code":
            continue
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                fails.append(f"{name} cell {i}: error output {o.get('ename')}")
        outs += "\n" + out_text(c)
    pool_text = outs + "\n".join(results_text)
    pool_tokens = {t.replace(",", ".") for t in re.findall(r"\d+[.,]\d+", pool_text)}
    pool_long = [float(t.replace(",", ".")) for t in pool_tokens if len(t.split(".")[1]) >= 3]
    for i, c in enumerate(nb.cells):
        src = "".join(c.source)
        text_for_words = src + "\n" + (out_text(c) if c.cell_type == "code" else "")
        if PATH.search(text_for_words):
            fails.append(f"{name} cell {i}: absolute path: {PATH.search(text_for_words).group(0)}")
        for label, pat in BANNED:
            if re.search(pat, text_for_words, re.I):
                fails.append(f"{name} cell {i}: '{label}'")
        body = None
        if c.cell_type == "markdown":
            body = src
        else:  # generated text: only what the cell displayed as markdown, not its source code
            md = [o["data"]["text/markdown"] for o in c.get("outputs", []) if "data" in o and "text/markdown" in o["data"]]
            body = "\n\n".join(m if isinstance(m, str) else "".join(m) for m in md) if md else None
        if body:
            for p in paragraphs(body):
                if LOCKED.search(p):
                    fails.append(f"{name} cell {i}: 'locked' outside 'locked test set': {LOCKED.search(p).group(0)!r} in: {p.strip()[:70]!r}")
                if ACC.search(p) and not AGREE.search(p):
                    fails.append(f"{name} cell {i}: accurate/accuracy without agreement/reference: {p.strip()[:80]!r}")
                if RT.search(p) and not COND.search(p) and not p.lstrip().startswith("#"):
                    fails.append(f"{name} cell {i}: real-time without a conditional marker: {p.strip()[:80]!r}")
        if c.cell_type == "markdown" and name[:2] in ("04", "05", "09"):
            for m in NUM.finditer(src):
                s = m.group(1); v = float(s.replace(",", ".")); d = len(re.split(r"[.,]", s)[1])
                if s.replace(",", ".") not in pool_tokens and not any(abs(round(x, d) - v) < 1e-9 for x in pool_long):
                    warns.append(f"{name} cell {i}: number {s} not found in any output or results/*.md")
for w in sorted(set(warns)):
    print("WARNING", w)
for x in fails:
    print("FAIL", x)
print(f"{len(files)} notebooks, {len(fails)} FAIL, {len(set(warns))} WARNING")
sys.exit(1 if fails else 0)
