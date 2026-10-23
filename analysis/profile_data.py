#!/usr/bin/env python
"""Profile every file under a path and write a markdown data brief.

Read-only: it never executes, imports or extracts anything it reads.
Run isolated, with the path as an argument:

    ~/.venvs/hackathon/bin/python -I analysis/profile_data.py data/raw/<name> --out out/data-brief.md
"""
import argparse
import codecs
import collections
import csv
import datetime
import hashlib
import json
import re
import sqlite3
import warnings
import zipfile
from pathlib import Path

import pandas as pd
from charset_normalizer import from_bytes

warnings.filterwarnings("ignore")

BIG = 200 * 1024 * 1024
SAMPLE_ROWS = 200_000
PLACEHOLDERS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "?", "unknown",
                "neznámý", "neznamy", "nezadáno", "nezadano"}
DATE_RES = {
    "ISO yyyy-mm-dd": re.compile(r"^\d{4}-\d{2}-\d{2}"),
    "Czech d.m.yyyy": re.compile(r"^\d{1,2}\.\s?\d{1,2}\.\s?\d{4}"),
    "slash d/m/y or m/d/y (ambiguous)": re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}"),
}
COLUMNS_SEEN = collections.defaultdict(list)


def human(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def cell(x, width=60):
    s = str(x).replace("|", "/").replace("\n", " ").replace("\r", " ")
    return s if len(s) <= width else s[: width - 1] + "…"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def sniff_kind(p):
    with open(p, "rb") as f:
        head = f.read(4096)
    ext = p.suffix.lower()
    if head.startswith(b"PK\x03\x04"):
        if ext in (".xlsx", ".xlsm"):
            return "xlsx"
        return "office" if ext in (".docx", ".pptx") else "zip"
    if head.startswith(b"\x1f\x8b"):
        return "gzip"
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\x89PNG") or head[:3] == b"\xff\xd8\xff" or ext in (
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff"):
        return "image"
    if head[:4] == b"PAR1":
        return "parquet"
    if head.startswith(b"SQLite format 3"):
        return "sqlite"
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return "xls" if ext == ".xls" else "office-ole"
    if ext in (".mp3", ".wav", ".m4a", ".flac", ".mp4", ".mov", ".mkv", ".avi", ".webm"):
        return "media"
    if ext in (".pkl", ".pickle", ".joblib", ".npy", ".npz", ".h5", ".hdf5", ".pt", ".pth", ".onnx"):
        return "binary-model-or-array"
    if b"\x00" in head and not head.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return "binary"
    return "text"


def decode_info(p):
    with open(p, "rb") as f:
        raw = f.read(300_000)
    if raw.startswith(codecs.BOM_UTF8):
        enc, bom = "utf-8-sig", "UTF-8 BOM"
    elif raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        enc, bom = "utf-16", "UTF-16 BOM"
    else:
        best = from_bytes(raw).best()
        enc = best.encoding if best else "utf-8"
        bom = "none"
        if enc.lower() in ("ascii", "utf_8", "utf-8"):
            enc = "utf-8"
    text = raw.decode(enc, errors="replace")
    return enc, bom, ("CRLF" if "\r\n" in text else "LF"), text


def count_lines(p):
    n = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            n += chunk.count(b"\n")
    return n


def guess_delimiter(text):
    lines = [ln for ln in text.splitlines()[:30] if ln.strip()]
    if len(lines) < 2:
        return None
    counts = {d: min(ln.count(d) for ln in lines) for d in ",;\t|"}
    best = max(counts, key=counts.get)
    if counts[best] > 0:
        return best
    try:
        return csv.Sniffer().sniff("\n".join(lines), delimiters=",;\t|").delimiter
    except csv.Error:
        return None


def column_notes(s, nn, nu):
    notes = []
    if nn == 0:
        return "all empty"
    if nu <= 1:
        notes.append("constant")
    if pd.api.types.is_bool_dtype(s):
        return "; ".join(notes)
    if pd.api.types.is_numeric_dtype(s):
        notes.append(f"{s.min():g} to {s.max():g}, mean {s.mean():.4g}")
        sent = [v for v in (-1, -9, -99, -999, -9999, 99999, 999999) if (s == v).any()]
        if sent:
            notes.append("possible sentinel " + "/".join(str(v) for v in sent))
    elif pd.api.types.is_datetime64_any_dtype(s):
        notes.append(f"{s.min()} to {s.max()}")
    else:
        sv = s.dropna().astype(str).head(5000)
        sample = sv.str.strip()
        ph = int(sample.str.lower().isin(PLACEHOLDERS).sum())
        if ph:
            notes.append(f"{ph} placeholder-like values (empty/NA/-/unknown) in sample")
        num = pd.to_numeric(sample.str.replace(r"\s", "", regex=True).str.replace(",", ".", regex=False),
                            errors="coerce")
        if len(sample) and num.notna().mean() > 0.95:
            notes.append("numbers stored as text" + (" (decimal comma)" if sample.str.contains(",", regex=False).any() else ""))
        else:
            for label, rx in DATE_RES.items():
                if len(sample) and sample.str.match(rx).mean() > 0.9:
                    notes.append("dates stored as text: " + label)
                    break
        if sample.ne(sv).any():
            notes.append("leading/trailing spaces")
        if len(sample):
            ln = sample.str.len()
            notes.append(f"length {ln.min()} to {ln.max()}")
        if nu <= 12:
            top = s.astype(str).value_counts().head(8)
            notes.append("values: " + ", ".join(f"{cell(k, 20)} ({v})" for k, v in top.items()))
        else:
            notes.append("e.g. " + " ; ".join(cell(v, 24) for v in sample.drop_duplicates().head(3)))
    return "; ".join(notes)


def profile_frame(df, total_rows, out, source):
    n = len(df)
    try:
        dup = int(df.duplicated().sum())
    except TypeError:
        dup = -1
    shown = f" (first {n:,} profiled)" if total_rows and total_rows > n else ""
    out.append(f"- Rows: **{total_rows or n:,}**{shown}; columns: **{df.shape[1]}**; "
               f"duplicate rows: {dup if dup >= 0 else 'n/a'}")
    unnamed = [c for c in df.columns if str(c).startswith("Unnamed")]
    if unnamed and len(unnamed) >= df.shape[1] / 2:
        out.append("- WARNING: many unnamed columns, the header is probably not on row 1.")
    numeric_names = sum(1 for c in df.columns if re.fullmatch(r"-?\d+([.,]\d+)?", str(c).strip()))
    if numeric_names >= max(2, df.shape[1] / 2):
        out.append("- WARNING: the column names look like data, a header row may be missing.")
    out.append("")
    out.append("| column | dtype | non-null | unique | notes |")
    out.append("|---|---|---|---|---|")
    keys = []
    for c in df.columns:
        s = df[c]
        try:
            nu = int(s.nunique(dropna=True))
        except TypeError:
            s = s.astype(str)
            nu = int(s.nunique(dropna=True))
        nn = int(s.notna().sum())
        COLUMNS_SEEN[str(c).strip().lower()].append(source)
        if n > 1 and nn == n and nu == n and not pd.api.types.is_float_dtype(s):
            keys.append(str(c))
        pct = f"{nn / n:.0%}" if n else "0%"
        out.append(f"| {cell(c, 40)} | {s.dtype} | {nn:,} ({pct}) | {nu:,} | {cell(column_notes(s, nn, nu), 220)} |")
    if keys:
        out.append(f"\n- Candidate keys (unique and never empty): {', '.join(keys)}")
    out.append("\nFirst rows:\n\n```")
    out.append(df.iloc[:3, :25].to_string(max_colwidth=28))
    out.append("```")


def do_text(p, out, rel):
    enc, bom, nl, text = decode_info(p)
    ext = p.suffix.lower()
    out.append(f"- Encoding: **{enc}** (BOM: {bom}), line endings: {nl}")
    stripped = text.lstrip()
    if ext in (".jsonl", ".ndjson"):
        return do_json(p, out, rel, lines=True)
    if ext == ".json" or (stripped[:1] in "{[" and ext not in (".csv", ".tsv")):
        try:
            return do_json(p, out, rel, lines=False)
        except ValueError:
            return do_json(p, out, rel, lines=True)
    delim = guess_delimiter(text) if ext not in (".md", ".py", ".html", ".xml", ".sql") else None
    lines_total = count_lines(p)
    if delim:
        name = {",": "comma", ";": "semicolon", "\t": "tab", "|": "pipe"}[delim]
        out.append(f"- Delimited text, delimiter: **{name}**; about {max(lines_total - 1, 0):,} data lines")
        try:
            df = pd.read_csv(p, sep=delim, encoding=enc, encoding_errors="replace",
                             nrows=SAMPLE_ROWS, low_memory=False)
        except Exception as e:
            out.append(f"- WARNING: strict parse failed ({cell(e, 120)}); malformed lines were skipped.")
            df = pd.read_csv(p, sep=delim, encoding=enc, encoding_errors="replace",
                             nrows=SAMPLE_ROWS, engine="python", on_bad_lines="skip")
        profile_frame(df, max(lines_total - 1, len(df)), out, rel)
    else:
        out.append(f"- Plain text, {lines_total:,} lines. First lines:\n\n```")
        out.extend(cell(ln, 200) for ln in text.splitlines()[:10])
        out.append("```")


def do_json(p, out, rel, lines):
    if lines:
        recs, bad = [], 0
        with open(p, encoding="utf-8", errors="replace") as f:
            for i, ln in enumerate(f):
                if i >= SAMPLE_ROWS:
                    break
                if ln.strip():
                    try:
                        recs.append(json.loads(ln))
                    except ValueError:
                        bad += 1
        if not recs:
            raise ValueError("no JSON lines")
        out.append(f"- JSON Lines, {len(recs):,} records read" + (f", {bad} unparsable lines" if bad else ""))
        profile_frame(pd.json_normalize(recs), None, out, rel)
        return
    if p.stat().st_size > BIG:
        raise ValueError("JSON larger than 200 MB, convert to JSON Lines first")
    data = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
    if isinstance(data, list):
        out.append(f"- JSON array of {len(data):,} items; item types: "
                   + ", ".join(f"{k} x{v}" for k, v in collections.Counter(type(x).__name__ for x in data).items()))
        if data and isinstance(data[0], dict):
            profile_frame(pd.json_normalize(data[:SAMPLE_ROWS]), len(data), out, rel)
    elif isinstance(data, dict):
        out.append(f"- JSON object with {len(data):,} top-level keys:\n")
        for k, v in list(data.items())[:30]:
            size = f", length {len(v):,}" if hasattr(v, "__len__") and not isinstance(v, str) else ""
            out.append(f"  - `{cell(k, 40)}`: {type(v).__name__}{size}")
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                out.append(f"\n#### Records under `{k}`")
                profile_frame(pd.json_normalize(v[:SAMPLE_ROWS]), len(v), out, f"{rel}:{k}")
                break
    else:
        out.append(f"- JSON scalar: {type(data).__name__}")


def do_excel(p, out, rel, kind):
    if kind == "xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(p, read_only=True)
        hidden = [ws.title for ws in wb.worksheets if ws.sheet_state != "visible"]
        if hidden:
            out.append(f"- WARNING: hidden sheets: {', '.join(hidden)}")
        wb.close()
    xl = pd.ExcelFile(p)
    out.append(f"- Sheets: {', '.join(cell(s, 40) for s in xl.sheet_names)}")
    for sh in xl.sheet_names:
        out.append(f"\n#### Sheet `{cell(sh, 40)}`")
        df = xl.parse(sh, nrows=SAMPLE_ROWS)
        if df.empty:
            out.append("- empty")
        else:
            profile_frame(df, None, out, f"{rel}:{sh}")


def do_parquet(p, out, rel):
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(p)
    out.append(f"- Rows: {pf.metadata.num_rows:,}, row groups: {pf.num_row_groups}")
    df = next(pf.iter_batches(batch_size=SAMPLE_ROWS)).to_pandas()
    profile_frame(df, pf.metadata.num_rows, out, rel)


def do_sqlite(p, out, rel):
    con = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True)
    items = con.execute("select name, type from sqlite_master where type in ('table','view') "
                        "and name not like 'sqlite_%' order by name").fetchall()
    out.append(f"- Tables and views: {', '.join(n for n, _ in items)}")
    for name, typ in items:
        q = '"' + name.replace('"', '""') + '"'
        cnt = con.execute(f"select count(*) from {q}").fetchone()[0]
        out.append(f"\n#### {typ} `{name}`")
        fks = con.execute(f"pragma foreign_key_list({q})").fetchall()
        if fks:
            out.append("- Foreign keys: " + ", ".join(f"{r[3]} -> {r[2]}.{r[4]}" for r in fks))
        df = pd.read_sql_query(f"select * from {q} limit {SAMPLE_ROWS}", con)
        profile_frame(df, cnt, out, f"{rel}:{name}")
    con.close()


def do_zip(p, out):
    with zipfile.ZipFile(p) as z:
        infos = z.infolist()
        total = sum(i.file_size for i in infos)
        out.append(f"- {len(infos):,} entries, {human(total)} uncompressed (not extracted)")
        bad = [i.filename for i in infos if i.filename.startswith(("/", "\\")) or ".." in Path(i.filename).parts]
        if bad:
            out.append(f"- WARNING: entries with absolute or parent paths: {', '.join(cell(b, 60) for b in bad[:5])}")
        if total > 1 << 30 and total > 50 * max(p.stat().st_size, 1):
            out.append("- WARNING: very high compression ratio, possible zip bomb")
        ext = collections.Counter(Path(i.filename).suffix.lower() or "(none)" for i in infos if not i.is_dir())
        out.append("- Types inside: " + ", ".join(f"{k} x{v}" for k, v in ext.most_common(10)))
        out.append("- First entries: " + ", ".join(f"`{cell(i.filename, 50)}`" for i in infos[:12]))
    out.append("- To profile the contents, extract into its own new empty folder under `data/raw/` and run this script on that folder.")


def do_image(p, out):
    from PIL import Image
    with Image.open(p) as im:
        out.append(f"- Image {im.size[0]}x{im.size[1]}, mode {im.mode}, format {im.format}")


def do_pdf(p, out):
    n = None
    if p.stat().st_size < 50 * 1024 * 1024:
        n = len(re.findall(rb"/Type\s*/Page[^s]", p.read_bytes()))
    out.append(f"- PDF, about {n if n is not None else '?'} pages. Text is not extracted here: read it directly.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--out")
    ap.add_argument("--max-files", type=int, default=200)
    a = ap.parse_args()
    root = Path(a.path).expanduser().resolve()
    if a.out and root.is_dir() and root in Path(a.out).expanduser().resolve().parents:
        raise SystemExit("refusing to write the brief inside the raw data folder")
    base = root if root.is_dir() else root.parent
    every = [root] if root.is_file() else sorted(f for f in root.rglob("*") if f.is_file())
    files = [f for f in every if not any(part.startswith(".") or part == "__MACOSX" for part in f.relative_to(base).parts)]
    skipped = len(every) - len(files)

    out = [f"# Data brief: `{root.name}`", "",
           f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M} by `profile_data.py` (pandas {pd.__version__}). "
           f"Read-only; nothing was extracted or executed.", "",
           f"- Files: **{len(files):,}**, total {human(sum(f.stat().st_size for f in files))}"
           + (f" ({skipped} hidden or system files skipped)" if skipped else ""), ""]
    by = collections.Counter()
    size = collections.Counter()
    kinds = {}
    for f in files:
        k = sniff_kind(f)
        kinds[f] = k
        key = f"{k} ({f.suffix.lower() or 'no ext'})"
        by[key] += 1
        size[key] += f.stat().st_size
    out += ["| kind (extension) | files | size |", "|---|---|---|"]
    out += [f"| {k} | {v:,} | {human(size[k])} |" for k, v in by.most_common()]
    out += ["", "Largest files: " + ", ".join(f"`{cell(f.relative_to(base), 50)}` {human(f.stat().st_size)}"
                                              for f in sorted(files, key=lambda x: -x.stat().st_size)[:8]), ""]

    image_detail = 0
    for f in files[: a.max_files]:
        rel = str(f.relative_to(base))
        kind = kinds[f]
        if kind == "image":
            image_detail += 1
            if image_detail > 5:
                continue
        out += ["", f"## {rel}", "",
                f"- Kind: **{kind}**, size {human(f.stat().st_size)}, sha256 `{sha(f) if f.stat().st_size < BIG else 'skipped (large)'}`"]
        try:
            if kind == "text":
                do_text(f, out, rel)
            elif kind in ("xlsx", "xls"):
                do_excel(f, out, rel, kind)
            elif kind == "parquet":
                do_parquet(f, out, rel)
            elif kind == "sqlite":
                do_sqlite(f, out, rel)
            elif kind == "zip":
                do_zip(f, out)
            elif kind == "image":
                do_image(f, out)
            elif kind == "pdf":
                do_pdf(f, out)
            elif kind == "gzip":
                out.append("- Gzip. Decompress into its own new empty folder and profile that.")
            elif kind == "binary-model-or-array":
                out.append("- WARNING: model or array file. Pickle-based formats can run code when loaded; do not load it.")
            else:
                out.append("- Not profiled (binary, media or office document).")
        except Exception as e:
            out.append(f"- ERROR while reading: {cell(type(e).__name__ + ': ' + str(e), 200)}")
    if image_detail > 5:
        out += ["", f"({image_detail - 5} more images not detailed)"]
    if len(files) > a.max_files:
        out += ["", f"({len(files) - a.max_files} more files not profiled, raise --max-files)"]

    shared = {c: sorted(set(v)) for c, v in COLUMNS_SEEN.items() if len(set(v)) > 1}
    if shared:
        out += ["", "## Columns that appear in more than one file or sheet (join candidates)", ""]
        out += [f"- `{c}`: {', '.join(cell(x, 40) for x in v[:6])}" for c, v in sorted(shared.items())]

    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).expanduser().parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).expanduser().write_text(text, encoding="utf-8")
        print(f"wrote {a.out}: {len(files)} files, {len(text.splitlines())} lines")
    else:
        print(text)


if __name__ == "__main__":
    main()
