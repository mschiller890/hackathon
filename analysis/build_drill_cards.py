"""Build presentation/drill-cards.json, the flashcards for the Q and A drill, from the written sources.

    python -I analysis/build_drill_cards.py

Sources: docs/REHEARSAL.md section 2 (23 drill questions, star = most dangerous) and docs/review-physics.md
section 5 (F1 to F10). The text is copied as written; no number is typed here. Aggregate statements only.
"""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WHO = {"IPP physicist": "IPP fyzik", "ML person": "ML", "Organizer / business": "organizátor"}
cards = []
clean = lambda s: re.sub(r"\s+", " ", s.replace("`", "").strip())

drill = (REPO / "docs/REHEARSAL.md").read_text()
sec = drill.split("## 2. Drill sheet", 1)[1].split("## 3.", 1)[0]
who = None
for line in sec.splitlines():
    m = re.match(r"\*\*(.+?)\*\*$", line.strip())
    if m and m.group(1) in WHO:
        who = WHO[m.group(1)]
        continue
    if line.startswith("| ") and who:
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 4 and re.match(r"^[QN]\d+", c[0]):
            ids = re.findall(r"[QN]\d+", c[0])
            ans = re.sub(r"\s*\((oprava|correction)[^)]*\)\s*$", "", clean(c[2])).strip().strip('"').strip("“”")
            cards.append(dict(id=ids[0], also=ids[1:], who=who, danger="★" in c[0], q=clean(c[1]), a=ans, full="", src=clean(c[3])))

phys = (REPO / "docs/review-physics.md").read_text().split("## 5. Ten hardest physics questions", 1)[1].split("## 6.", 1)[0]
for m in re.finditer(r"\*\*(F\d+)\. (.+?)\*\*\n(.+?)(?=\n\n\*\*F|\Z)", phys, re.S):
    full = clean(m.group(3))
    sent = re.split(r"(?<=[.!?])\s+", full)
    short = sent[0]
    for nxt in sent[1:]:
        if len(short) + len(nxt) > 260:
            break
        short += " " + nxt
    cards.append(dict(id=m.group(1), also=[], who="IPP fyzik", danger=False, q=clean(m.group(2)), a=short, full=full if full != short else "", src="docs/review-physics.md §5"))

out = REPO / "presentation/drill-cards.json"
out.write_text(json.dumps(cards, ensure_ascii=False, indent=1))
print(len(cards), "cards;", sum(c["danger"] for c in cards), "marked dangerous;", {w: sum(c["who"] == w for c in cards) for w in set(c["who"] for c in cards)})
