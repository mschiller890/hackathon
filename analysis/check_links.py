"""Report repository paths mentioned in tracked text files that do not exist.

Usage: python analysis/check_links.py   (exit code 1 if any reference dangles)

A mention is a token starting with docs/, analysis/, results/, presentation/,
notebooks/ or viewer/. Skipped: globs and placeholders (results/<name>),
git-ignored paths (out/, data/, viewer/dist), abbreviations that are the start of a
real file name (notebooks/01), figures that a script writes (a png/pdf/pptx path that
appears in a tracked .py file) and the optional hand-written inputs in OPTIONAL.
Not scanned: docs/PLAN.md and docs/internal/, which keep the history of the work.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".md", ".py", ".ipynb", ".json", ".html", ".txt", ".gitignore"}
SKIP_SOURCES = {"docs/PLAN.md"}
SKIP_DIRS = ("docs/internal/",)
OPTIONAL = {"results/cloud-search-findings.md"}  # read by cloud_search_report.py only if present
OUTPUT_EXT = {".png", ".pdf", ".pptx"}
MENTION = re.compile(r"(?<![\w/.\-~])((?:docs|analysis|results|presentation|notebooks|viewer)/[\w./\-]*)([*{<\[%$]?)")


def git(*args, stdin=None):
    return subprocess.run(["git", *args], cwd=ROOT, input=stdin, capture_output=True, text=True).stdout


def main() -> int:
    mentions: dict[str, set[str]] = {}
    tracked = git("ls-files").splitlines()
    py_text = "\n".join((ROOT / f).read_text(errors="replace") for f in tracked if f.endswith(".py"))
    for rel in tracked:
        if rel in SKIP_SOURCES or rel.startswith(SKIP_DIRS) or Path(rel).suffix not in TEXT:
            continue
        for m in MENTION.finditer((ROOT / rel).read_text(encoding="utf-8", errors="replace")):
            if m.group(2):
                continue  # glob or placeholder
            path = m.group(1).rstrip(".,;:-/")
            if path.count("/") or "." in path:
                mentions.setdefault(path, set()).add(rel)
    missing = [q for q in sorted(mentions) if not (ROOT / q).exists() and q not in OPTIONAL
               and not any(f.startswith(q) for f in tracked)
               and not (Path(q).suffix in OUTPUT_EXT and q in py_text)]
    asked = "\n".join(missing + [q + "/" for q in missing])
    ignored = set(git("check-ignore", "--no-index", "--stdin", stdin=asked).split("\n")) if missing else set()
    dangling = [q for q in missing if q not in ignored and q + "/" not in ignored]
    for q in dangling:
        print(f"DANGLING {q}  <- {', '.join(sorted(mentions[q]))}")
    print(f"{len(dangling)} dangling references ({len(mentions)} distinct paths checked)")
    return 1 if dangling else 0


if __name__ == "__main__":
    sys.exit(main())
