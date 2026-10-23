"""Estimate the spoken duration of the timed rows of presentation/pitch-script.md.

Usage: python presentation/timing.py [path]
Reads rows like "| 0:21 | 7 | A | spoken text | screen |", counts words (a bare number counts as 3 words,
because Czech numbers are spoken in full) and prints the written seconds against the estimate at 1.6, 1.8, 2.0 words/s.
"""
import re
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("pitch-script.md")
ROW = re.compile(r"^\|\s*(\d+:\d\d)\s*\|\s*(\d+)\s*\|\s*([A-Z+]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")


def words(text):
    n = 0
    for tok in re.findall(r"[0-9]+(?:,[0-9]+)?|[^\W\d_]+(?:-[^\W\d_]+)*", text):
        n += 3 if tok[0].isdigit() else 1
    return n


rows = []
for line in path.read_text(encoding="utf-8").splitlines():
    m = ROW.match(line)
    if m and not m.group(4).startswith("("):
        rows.append((m.group(1), int(m.group(2)), m.group(3), words(m.group(4))))

tot = {r: 0.0 for r in (1.6, 1.8, 2.0)}
written = 0
print(f"{'time':>5} {'written s':>9} {'words':>5} " + " ".join(f"{'s@' + str(r):>7}" for r in tot) + "  flag")
for t, sec, who, w in rows:
    est = {r: w / r for r in tot}
    for r in tot:
        tot[r] += est[r]
    written += sec
    flag = "LONG" if est[1.8] > sec * 1.15 else ""
    print(f"{t:>5} {sec:>9} {w:>5} " + " ".join(f"{est[r]:7.1f}" for r in tot) + f"  {flag}")
print(f"total written {written} s ({written // 60}:{written % 60:02d}); estimated "
      + ", ".join(f"{r} w/s -> {int(v) // 60}:{int(v) % 60:02d}" for r, v in tot.items()))
