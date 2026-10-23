"""Build presentation/drill-cards.json, the flashcards for the Q and A drill, from the written sources.

    python -I analysis/build_drill_cards.py

Sources: presentation/REHEARSAL.md section 2 (drill questions with the 15 s answers, star = most dangerous), the current
presentation/pitch-script.md question sections (long answers, put under `full`) and docs/internal/review-physics.md section 5
(F1 to F10; the ones the pitch already asks are merged, not repeated). The text is copied as written; no number is typed here. Aggregate statements only.
"""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WHO = {"IPP physicist": "IPP fyzik", "ML person": "ML", "Organizer / business": "organizátor"}
cards = []
clean = lambda s: re.sub(r"\s+", " ", s.replace("`", "").strip())

drill = (REPO / "presentation/REHEARSAL.md").read_text()
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

pitch = (REPO / "presentation/pitch-script.md").read_text()
pitch_full, pitch_f, pitch_q, pitch_who = {}, {}, {}, {}
for m in re.finditer(r"### (N?\d+)\. (.+?)\nOtázka: (.+?)\n\nOdpovídá [AB]: (.+?)(?=\n\n### |\n\n## |\Z)", pitch, re.S):
    pid = m.group(1) if m.group(1).startswith("N") else "Q" + m.group(1)
    pitch_full[pid] = clean(m.group(4))
    pitch_q[pid] = re.sub(r"\s*\(F\d+\)\s*$", "", clean(m.group(3)))
    pitch_who[pid] = {'Fyzik': 'IPP fyzik', 'Odborník na strojové učení': 'ML', 'Podnikatel': 'organizátor'}.get(m.group(2).strip(), 'IPP fyzik')
    tag = re.search(r"\((F\d+)\)\s*$", m.group(3).strip())
    if tag:
        pitch_f[tag.group(1)] = pid
by_id = {c["id"]: c for c in cards}
skip = {x for c in cards for x in c["also"]}
for pid, txt in pitch_full.items():
    c = by_id.get(pid)
    if c and len(txt) > len(c["a"]) + 20:
        c["full"] = txt
    elif not c and pid not in skip:
        sent = re.split(r"(?<=[.!?])\s+", txt)
        short = sent[0]
        for nxt in sent[1:]:
            if len(short) + len(nxt) > 260:
                break
            short += " " + nxt
        cards.append(dict(id=pid, also=[], who=pitch_who[pid], danger=False, q=pitch_q[pid], a=short, full=txt if txt != short else "", src="presentation/pitch-script.md"))

phys = (REPO / "docs/internal/review-physics.md").read_text().split("## 5. Ten hardest physics questions", 1)[1].split("## 6.", 1)[0]
for m in re.finditer(r"\*\*(F\d+)\. (.+?)\*\*\n(.+?)(?=\n\n\*\*F|\Z)", phys, re.S):
    full = clean(m.group(3))
    sent = re.split(r"(?<=[.!?])\s+", full)
    short = sent[0]
    for nxt in sent[1:]:
        if len(short) + len(nxt) > 260:
            break
        short += " " + nxt
    dup = next((x for x in cards if x['q'][:40].lower() == clean(m.group(2))[:40].lower()), None)
    if dup and m.group(1) not in pitch_f:
        pitch_f[m.group(1)] = dup['id']
        by_id[dup['id']] = dup
    if m.group(1) in pitch_f:  # same question as a pitch card: keep its short answer, offer the longer text under full
        c = by_id[pitch_f[m.group(1)]]
        if len(full) > len(c["full"] or c["a"]):
            c["full"] = full
        c["src"] += ", docs/internal/review-physics.md §5 (" + m.group(1) + ")"
        continue
    cards.append(dict(id=m.group(1), also=[], who="IPP fyzik", danger=False, q=clean(m.group(2)), a=short, full=full if full != short else "", src="docs/internal/review-physics.md §5"))

out = REPO / "presentation/drill-cards.json"
out.write_text(json.dumps(cards, ensure_ascii=False, indent=1))
print(len(cards), "cards;", sum(c["danger"] for c in cards), "marked dangerous;", {w: sum(c["who"] == w for c in cards) for w in set(c["who"] for c in cards)})
