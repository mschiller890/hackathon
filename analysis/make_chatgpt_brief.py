"""Build presentation/CHATGPT-BRIEF.md: one self-contained study file to upload to a voice tutor (ChatGPT).

Aggregate results only; no raw IPP data. Re-run after the pitch or the cards change:  python analysis/make_chatgpt_brief.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "presentation"


def read(path):
    return Path(path).read_text(encoding="utf-8").strip()


def strip_h1(text):
    return re.sub(r"^# .*\n+", "", text, count=1)


FRONT = """# Studijní podklad pro hlasový rozhovor (ChatGPT)

Tento soubor je určený pro hlasový rozhovor s ChatGPT. Obsahuje jen souhrnné výsledky a texty z naší prezentace; žádná surová data ústavu v něm nejsou. Rozhovor je v češtině.

## Co říct ChatGPT na začátku (vlož jako první zprávu)

Jsi můj trenér před vystoupením na hackathonu. Přečti si přiložený soubor celý. Pak:
1. Nejdřív mi bez odborných slov vysvětli, o čem projekt je, jako bych byl chytrý student, který o plazmatu nic neví. Maximálně dvě minuty, pak se zeptej, jestli je to jasné.
2. Potom mě učíš po krocích podle části "Plán rozhovoru" na konci souboru. Po každém kroku mi dej jednu kontrolní otázku a čekej na mou odpověď. Opravuj mě jen podle čísel a vět v tomto souboru; když něco v souboru není, řekni "to v podkladu není" a nevymýšlej.
3. Na konci hraj porotce: nejdřív fyzika z Ústavu fyziky plazmatu, potom odborníka na strojové učení, potom učitele. Ptej se na těžké otázky z části "Zlé otázky", jednu po druhé, a po mé odpovědi řekni, co chybělo nebo bylo příliš silné.
4. Mluv pomalu, krátkými větami, česky. Čísla vždy s jednotkou a s tím, na čem se měřila.

## Pravidla, která v rozhovoru platí

* Chyba 0,13 milimetru je shoda s rekonstrukcí, kterou nám dal ústav, ne přesnost vůči skutečnému plazmatu.
* Nikdy neříkej "nikdo neviděl", "skutečný tvar", "přesnost" pro shodu s rekonstrukcí, ani že je řízení v reálném čase vyřešené.
* Když nevíme, řekni: "Tohle jsme neměřili, měřili jsme ...".
* Na otázku, zda jsme používali umělou inteligenci, se odpovídá pravdivě: ano, jako pomocníky; zadání, rozhodnutí a kontrolu čísel jsme dělali my.

## Projekt vysvětlený od nuly

Tokamak je prstenec, ve kterém magnetické pole drží velmi horký plyn, plazma. Aby se plazma nedotklo stěn, musí řídicí systém v řádu milisekund vědět, kde plazma je a jaký má tvar. Přesný výpočet tvaru z měření trvá po výboji minuty. Dostali jsme data z tokamaku COMPASS Ústavu fyziky plazmatu: 149 výbojů, asi 43 tisíc časových okamžiků, a v každém 24 magnetických měření (16 cívek a 8 smyček toku). K tomu má každý okamžik hodnoty, které spočítala rekonstrukce rovnováhy ústavu: poloha magnetické osy, bod X, dva dotykové body, bod u limiteru, protažení, trojúhelníkovost, proud plazmatem a další.

Náš úkol: naučit malou neuronovou síť, aby z 24 měření odhadla těch 16 hlavních veličin, a změřit, jak dobře a jak rychle to umí. Dělíme vždy po celých výbojích, protože sousední okamžiky jednoho výboje jsou skoro kopie. Základní síť má 107 152 parametrů. Vybraný model je základní síť plus rozdíly sousedních cívek, lineární model pro proud a zvláštní síť pro bod u limiteru.

Co ukazuje demo: prohlížeč přehrává výboj; tmavá čára je tvar z rekonstrukce ústavu, barevné body jsou odhad vybraného modelu (obrys se nepředpovídá, jen body: osa, bod X, dotykové body, bod u limiteru). Ukázkové výboje: 85 (typický, osa o čtvrt milimetru vedle) a 147 (nejhorší konec, osa o 34 milimetrů vedle na posledním snímku, ale průměr celého výboje pod milimetrem).

"""

PLAN = """

## Plán rozhovoru (pro ChatGPT: vést mě podle něj)

1. Úvod bez odborných slov (2 minuty) a otázka: "Řekni vlastními slovy, co síť dělá a proč to někdo chce."
2. Pojmy ze slovníčku: osm pojmů, ke každému jedna otázka (tokamak, plazma, bod X, dotykový bod, limiter, protažení, výboj, odezva).
3. Čísla: projdi tabulku čísel; pak se ptej na čísla v náhodném pořadí: "Kolik je chyba osy na odložených výbojích a jaký je to protokol?" Chci slyšet číslo, jednotku i protokol.
4. Co neumíme a co jsme neměřili: nové tvary, zašuměné vstupy u modelu učeného na čistých datech, reálný čas na skutečném systému, fyzikální přesnost vůči plazmatu.
5. Přečtu nahlas celý talk (7 minut); ty hlídáš, jestli neřeknu větu ze seznamu zakázaných, a po každém slajdu řekneš jednu věc, která zněla špatně.
6. Zlé otázky: hraješ tři porotce a ptáš se; já odpovídám; ty hodnotíš odpověď 1 až 5 a říkáš přesně, co zlepšit.
7. Na závěr: tři věty, které si mám odnést, a tři věci, ve kterých jsem nejistý.
"""


def numbers_section():
    text = strip_h1(read(ROOT / "presentation" / "CHEAT-SHEET.md"))
    return "## Čísla k zapamatování a věty, které se nesmí říct\n\n" + text


def talk_section():
    text = strip_h1(read(P / "READ-ALOUD.md"))
    return "## Talk, tak jak ho čteme nahlas\n\n" + text


def gloss_section():
    return "## Slovníček\n\n" + strip_h1(read(P / "slovnicek.md"))


def cards_section():
    cards = json.loads(read(P / "drill-cards.json"))
    out = ["## Zlé otázky a odpovědi (porotce se ptá, ty hodnotíš)\n"]
    for c in cards:
        star = " (nebezpečná)" if c.get("danger") else ""
        out.append(f"### {c['id']} – ptá se: {c['who']}{star}\n\n**Otázka:** {c['q']}\n\n**Krátká odpověď:** {c['a']}\n")
        if c.get("full"):
            out.append(f"**Úplná odpověď:** {c['full']}\n")
        if c.get("src"):
            out.append(f"*Zdroj: {c['src']}*\n")
    return "\n".join(out)


body = "\n\n".join([FRONT, gloss_section(), numbers_section(), talk_section(), cards_section(), PLAN])
(P / "CHATGPT-BRIEF.md").write_text(body + "\n", encoding="utf-8")
print("words:", len(body.split()))
