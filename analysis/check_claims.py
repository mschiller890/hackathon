#!/usr/bin/env python
"""Gate G2: find every number with a unit or percent on the slides and in the pitch and look for it in results/.

Texts checked: presentation/pitch-script.md, presentation/outline.md, presentation/deck/slides.pptx (shapes, tables,
grouped shapes and speaker notes). Sources: results/*.md and results/*.json (every number in them).

A claim is a number followed by a unit word (mm, kA, ms, %, "procent", "milimetru", a count noun such as "výbojů", ...).
A range "150 až 200 ms" gives both ends the unit. Speech timings (seconds, minutes) and bare numbers are skipped; the report
counts the skipped bare numbers so nothing is hidden. Numbers inside pictures cannot be read.

Bare decimals with at least two decimal places (a score such as 0,063) are claims too.

A claim is sourced when some source number equals it after rounding to the digits shown, allowing the usual conversions
(percent from a fraction or from a ratio, mm from m, kA from A, ms from s). Czech decimal comma, thin and no-break spaces
as thousand separators on the claim side; both "42,972" readings on the source side.

Finding a number among 10 000 or more source numbers proves little for a short number, so every sourced claim gets a strength:
specific (four or more significant digits, or at most 5 matching source numbers), medium (6 to 25) or common (more than 25).
Only specific matches are real evidence; medium and common ones are listed for reading by hand.

Run: python -I analysis/check_claims.py            (writes docs/claims-audit.md, keeps a hand-written "## Review" section)
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEXTS = [REPO / "presentation/pitch-script.md", REPO / "presentation/outline.md"]
DECK = REPO / "presentation/deck/slides.pptx"
AUDIT = REPO / "docs/claims-audit.md"

NUM = r"\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?(?![\d])|\d+(?:[.,]\d+)?"
UNITS = [  # (regex of the word after the number, class)
    (r"%|procent\w*", "percent"), (r"mm\b|milimetr\w*", "mm"), (r"µm\b|mikrometr\w*", "um"),
    (r"kA\b|kiloampér\w*", "kA"), (r"ms\b|milisekund\w*", "ms"), (r"µs\b|mikrosekund\w*", "us"),
    (r"krát\b|násob\w*", "ratio"),
    (r"(?:výboj|okamžik|vstup|parametr|snímk|cívek|cívk|smyč|veličin|epoch|vzork|řádk|diskretiz|sítí|síť|sít)\w*", "count"),
    (r"(?:MB|GB|kB)\b", "size"), (r"(?:kHz|Hz)\b", "hz"),
]
UNIT_RE = re.compile(r"\s*(" + "|".join(f"(?P<u{i}>{u})" for i, (u, _) in enumerate(UNITS)) + ")", re.I)
RANGE_RE = re.compile(r"^\s*(?:až|–|-|—)\s*(" + NUM + ")")


def num_value(tok):
    t = re.sub(r"[   ]", "", tok).replace(",", ".")
    return float(t), (len(t.split(".")[1]) if "." in t else 0)


def claims_in(text):
    """Yield (value, decimals, unit class, unit text, number text, context) for the claims in one text."""
    found, skipped = [], 0
    for m in re.finditer(NUM, text):
        if m.start() and (text[m.start() - 1].isalnum() or text[m.start() - 1] in ".,:/") and not text[m.start() - 1].isspace():
            continue  # part of a word, a time like 0:24 or a path
        rest = text[m.end():m.end() + 40]
        u = UNIT_RE.match(rest)
        rng = RANGE_RE.match(rest)
        if not u and rng:                       # "150 až 200 milisekund": the first end inherits the unit
            u2 = UNIT_RE.match(rest[rng.end():])
            u, off = (u2, rng.end()) if u2 else (None, 0)
        v, d = num_value(m.group())
        if not u and d >= 2 and not re.match(r"\s*[:/]", rest):  # a bare decimal such as a score or ratio
            found.append((v, d, "bare", "", m.group(), re.sub(r"\s+", " ", text[max(0, m.start() - 35):m.end() + 45]).strip()))
            continue
        if not u:
            skipped += 1
            continue
        cls = next(UNITS[i][1] for i in range(len(UNITS)) if u.group(f"u{i}"))
        ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 35):m.end() + 45]).strip()
        found.append((v, d, cls, u.group(1), m.group(), ctx))
    return found, skipped


# ----------------------------------------------------------------------------- sources
def source_numbers():
    """All numbers in results/*.md and *.json as (value, file)."""
    out = []
    for f in sorted((REPO / "results").glob("*")):
        if f.suffix == ".json":
            def walk(o):
                if isinstance(o, bool):
                    return
                if isinstance(o, (int, float)):
                    out.append((float(o), f.name))
                elif isinstance(o, dict):
                    for x in o.values():
                        walk(x)
                elif isinstance(o, list):
                    for x in o:
                        walk(x)
            try:
                walk(json.loads(f.read_text()))
            except ValueError:
                pass
        elif f.suffix == ".md":
            for m in re.finditer(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?", f.read_text()):
                tok = m.group().rstrip(",")
                out.append((float(tok.replace(",", "")) if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", tok) else _plain(tok), f.name))
                if re.fullmatch(r"\d+,\d{3}", tok):  # "8,761" may also be a decimal comma
                    out.append((float(tok.replace(",", ".")), f.name))
    return out


def _plain(tok):
    try:
        return float(tok.replace(",", "."))
    except ValueError:
        return float("nan")


TRANSFORMS = {  # claim unit class: functions mapping a source number to what the claim may show
    "percent": [lambda s: s, lambda s: s * 100, lambda s: 100 * (1 - s), lambda s: 100 * (s - 1)],
    "mm": [lambda s: s, lambda s: s * 1000], "um": [lambda s: s * 1000, lambda s: s],
    "kA": [lambda s: s, lambda s: s / 1000], "ms": [lambda s: s, lambda s: s * 1000], "us": [lambda s: s, lambda s: s * 1000],
    "ratio": [lambda s: s, lambda s: 1 / s if s else float("nan")],
}
IDENT = [lambda s: s]


def sig_digits(v, d):
    t = f"{v:.{d}f}".replace(".", "").lstrip("0")
    return len(t.rstrip("0")) if d == 0 else len(t)


def match(v, d, cls, sources):
    """Return (kind, strength, file, hits) or None. kind: exact, rounded or converted; strength from the number of matching source numbers."""
    tol = 0.5 * 10 ** -d + 1e-9
    hits, best = 0, None
    for k, tf in enumerate(TRANSFORMS.get(cls, IDENT)):
        for s, f in sources:
            if s == s and abs(tf(s) - v) <= tol:
                hits += 1
                kind = "exact" if k == 0 and abs(tf(s) - v) < 1e-9 else "rounded" if k == 0 else "converted"
                if best is None or ["exact", "rounded", "converted"].index(kind) < ["exact", "rounded", "converted"].index(best[0]):
                    best = (kind, f)
    if best is None:
        return None
    strength = "specific" if sig_digits(v, d) >= 4 or hits <= 5 else "medium" if hits <= 25 else "common"
    return best[0], strength, best[1], hits


def closest(v, cls, sources, cited=()):
    """The source number nearest to the claim within 10 %, as a hint for a rounding or typing mismatch.

    When the text cites results files, only those are searched: a near value in an unrelated file is no hint.
    """
    pool = [x for x in sources if x[1] in cited] or sources
    cand = [(abs(tf(s) - v) / max(abs(v), 1e-12), tf(s), f) for tf in TRANSFORMS.get(cls, IDENT) for s, f in pool if s == s and abs(v) > 0]
    cand = [c for c in cand if c[0] <= 0.10]
    return min(cand) if cand else None


# ----------------------------------------------------------------------------- texts
def md_blocks(path):
    heading = ""
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if line.startswith("#"):
            heading = line.lstrip("# ").strip()[:50]
        yield f"{path.name}, line {n}" + (f" ({heading})" if heading else ""), line


def deck_blocks(path):
    from pptx import Presentation

    def shapes(group):
        for sh in group:
            if sh.shape_type == 6:
                yield from shapes(sh.shapes)
            else:
                yield sh
    for i, slide in enumerate(Presentation(str(path)).slides, 1):
        for sh in shapes(slide.shapes):
            if sh.has_text_frame and sh.text_frame.text.strip():
                yield f"{path.name}, slide {i}, text", sh.text_frame.text
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    yield f"{path.name}, slide {i}, table", " | ".join(c.text for c in row.cells)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            yield f"{path.name}, slide {i}, notes", slide.notes_slide.notes_text_frame.text


def main():
    sources = source_numbers()
    rows, skipped, total = [], {}, {}
    blocks = [b for t in TEXTS for b in md_blocks(t)] + list(deck_blocks(DECK))
    for loc, text in blocks:
        found, sk = claims_in(text)
        file = loc.split(",")[0]
        skipped[file] = skipped.get(file, 0) + sk
        for v, d, cls, unit, tok, ctx in found:
            m = match(v, d, cls, sources)
            key = m[1] if m else "unsourced"
            total.setdefault(file, {}).setdefault(key, 0)
            total[file][key] += 1
            cited = {n for n in re.findall(r"[\w-]+\.(?:md|json)", text)}
            rows.append((loc, f"{tok} {unit}".strip(), ctx, key, closest(v, cls, sources, cited) if m is None else None, m[2] if m else "", m[3] if m else 0))
    write_audit(rows, total, skipped, len(sources))


def fix_hint(near):
    if near:
        return f"check the digits: `{near[2]}` holds {near[1]:.4g}"
    return "no source: put the computation into a results file or remove the number"


def write_audit(rows, total, skipped, n_sources):
    L = ["# Claims audit (gate G2)", "",
         "Generated by `python -I analysis/check_claims.py`. Every number followed by a unit, a percent sign or a count noun, and every bare decimal with two or more "
         "decimal places, in the pitch script, the outline and the deck (text, tables, speaker notes) is looked up among the numbers of `results/*.md` and `results/*.json` "
         f"({n_sources} source numbers). Rounding to the shown digits and the usual unit conversions are allowed (percent from a fraction or a ratio, mm from m, "
         "kA from A, ms from s). Speech timings in seconds and minutes and integers without a unit are not claims here (counted below). Numbers inside pictures cannot be read.", "",
         "**How much a match proves.** The sources hold several thousand numbers, so a short number is found by chance almost always. A match is *specific* "
         "(four or more significant digits, or at most 5 matching source numbers) and counts as evidence, *medium* (6 to 25 matches) or *common* "
         "(more than 25): common and medium matches only show that the number exists somewhere in `results/`, not that it is the right one, and are listed below for reading by hand.", "",
         "| Text | claims | no source | specific | medium | common | skipped integers |", "|---|---:|---:|---:|---:|---:|---:|"]
    for f, t in total.items():
        L.append(f"| {f} | {sum(t.values())} | {t.get('unsourced', 0)} | {t.get('specific', 0)} | {t.get('medium', 0)} | {t.get('common', 0)} | {skipped.get(f, 0)} |")
    uns = [r for r in rows if r[3] == "unsourced"]
    L += ["", f"## Numbers without a source ({len(uns)})", "", "| Where | Number | Context | Closest in results (within 10 %) | Proposed fix |", "|---|---|---|---|---|"]
    for loc, num, ctx, kind, near, _, _ in uns:
        L.append(f"| {loc} | {num} | {ctx.replace('|', '/')} | " + (f"{near[1]:.4g} in `{near[2]}`" if near else "none") + f" | {fix_hint(near)} |")
    weak = {}
    for loc, num, ctx, kind, near, f, hits in rows:
        if kind in ("medium", "common"):
            weak.setdefault(loc, []).append(f"{num} ({kind[0]})")
    L += ["", f"## Matched only by a medium (m) or common (c) value: read by hand ({sum(len(v) for v in weak.values())} claims in {len(weak)} places)", "",
          "| Where | Numbers |", "|---|---|"]
    for loc, nums in weak.items():
        L.append(f"| {loc} | {', '.join(nums)} |")
    text = "\n".join(L) + "\n"
    if AUDIT.exists() and "\n## Review" in AUDIT.read_text():  # the hand-written review is kept
        text += "\n## Review" + AUDIT.read_text().split("\n## Review", 1)[1]
    AUDIT.write_text(text)
    print(text)


if __name__ == "__main__":
    sys.exit(main())
