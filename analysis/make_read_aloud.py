"""Write presentation/READ-ALOUD.md, the spoken text of the talk for a stopwatch run, from presentation/pitch-script.md.

    python -I analysis/make_read_aloud.py

Only the column 'Co se říká' of the timed rows, in order, with the clock stamp and speaker (A, B) at the start of each
row and the cumulative target time (sum of the written seconds) at the end of each slide. No table, no screen column,
no notes. The last line repeats the total of presentation/timing.py. Regenerate after every change of the script.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "presentation/pitch-script.md"
OUT = ROOT / "presentation/READ-ALOUD.md"
ROW = re.compile(r"^\|\s*(\d+:\d\d)\s*\|\s*(\d+)\s*\|\s*([A-Z+]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")
HEAD = re.compile(r"^### (.+?) \((\d+:\d\d) až (\d+:\d\d), (\d+) s\)\s*$")


def mmss(s):
    return f"{s // 60}:{s % 60:02d}"


def secs(stamp):
    m, s = stamp.split(":")
    return int(m) * 60 + int(s)


text = SRC.read_text(encoding="utf-8")
body = text.split("## Časovaný scénář", 1)[1].split("## Pravidla řeči", 1)[0]
sections, cur = [], None
for line in body.splitlines():
    h = HEAD.match(line)
    if h:
        cur = dict(title=h.group(1), start=h.group(2), end=h.group(3), rows=[])
        sections.append(cur)
        continue
    m = ROW.match(line)
    if m and cur is not None and not m.group(4).startswith("("):
        cur["rows"].append((m.group(1), int(m.group(2)), m.group(3), m.group(4)))

out = ["# Čti nahlas: sedm minut", "",
       "Stopky spusť na prvním řádku. A a B jsou dva řečníci, tučné časy říkají, kdy má řádek začít. Na konci každého snímku je cílový čas, od něj se dívej, jestli běžíte rychleji, nebo pomaleji.",
       "Čísla čti celými slovy, jak jsou napsaná v textu. Při nejistotě řekni: \"Tohle jsme neměřili.\"", ""]
cum, total_words, first_gap = 0, 0, None
for s in sections:
    out += ["---", "", f"## {s['title']}", ""]
    for stamp, sec, who, txt in s["rows"]:
        out += [f"**{stamp}   {who.replace('+', ' + ')}**", "", txt, ""]
        cum += sec
        total_words += len(txt.split())
    flag = "" if mmss(cum) == s["end"] else f" (v hlavičce skriptu je {s['end']}, součet sekund řádků dává {mmss(cum)})"
    if flag and first_gap is None:
        first_gap = (s["title"], secs(s["end"]) - cum)
    out += [f"**Konec snímku: cílový čas {mmss(cum)}{flag}**", ""]
timing = subprocess.run([sys.executable, str(ROOT / "presentation/timing.py")], capture_output=True, text=True, cwd=ROOT).stdout.strip().splitlines()[-1]
if first_gap:
    out += [f"POZOR: sekundy řádků dávají {mmss(cum)}, hlavičky skriptu 7:00. Rozdíl {first_gap[1]} s vzniká už v části \"{first_gap[0]}\": hlavička udává delší okno, než součet sekund jejích řádků. Řečníci mají tedy na konci rezervu, nebo je třeba v hlavičce opravit čas.", ""]
out += ["---", "", f"Celkem podle `presentation/timing.py`: {timing}.", "", f"Sečteno z řádků: {mmss(cum)}, slov ve všech řádcích {total_words}.", ""]
OUT.write_text("\n".join(out), encoding="utf-8")
print(f"{len(sections)} sections, {sum(len(s['rows']) for s in sections)} rows, total {mmss(cum)}")
print(timing)
