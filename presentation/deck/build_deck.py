#!/usr/bin/env python
"""Build presentation/deck/slides.pptx (16:9, Czech) for IPP task 1.

    ~/.venvs/hackathon/bin/python -I presentation/deck/build_deck.py

Structure and seconds follow presentation/pitch-script.md (Lead's decision, docs/PLAN.md RP-11): talk slides 1 to 8
plus the 95 s live demo between 4 and 5. A talk slide may span several screens (slide 1 switches image at 0:24,
slide 4 has schematic, results and inputs); every screen keeps its talk number in the footer, and its speaker notes
carry only the script lines spoken while it is up. A hidden backup screen holds the viewer stills for the
"ukázka selže" fallback.

Numbers come only from the aggregate files in results/ (CON-001: no raw rows). The baseline, inputs, latency and
time figures are read from the JSON; lane R wrote its aggregates only as Markdown
(results/ipp1-robustness-findings.md), so those few values are copied below with that file as the source.
Rebuild after the pitch script, the images or the results change.
"""
import json
import re
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
ASSETS = REPO / "presentation/assets"
OUT = Path(__file__).resolve().parent / "slides.pptx"

NAVY, PANEL, LINE = RGBColor(0x0B, 0x17, 0x30), RGBColor(0x14, 0x25, 0x4A), RGBColor(0x2A, 0x3D, 0x66)
TEXT, MUTED = RGBColor(0xF2, 0xF5, 0xFA), RGBColor(0x9A, 0xA9, 0xC6)
ORANGE, BLUE = RGBColor(0xFF, 0x8A, 0x3D), RGBColor(0x4C, 0x9B, 0xFF)
FONT = "Arial"  # present on Mac, Windows and LibreOffice; carries Czech diacritics

W, H = Emu(12192000), Emu(6858000)  # 13.333 x 7.5 in, 16:9
IN = 914400


def cz(x, nd):
    """Czech number: decimal comma, non-breaking space between thousands."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", " ").replace(".", ",")


def load():
    j = {n: json.loads((RES / f"ipp1-{n}.json").read_text()) for n in ("baseline", "inputs", "latency", "time")}
    # Lane R aggregates (results/ipp1-robustness-findings.md, tables 1 to 3), R_mag_axis MAE in mm.
    j["noise"] = [("učeno bez šumu,\ntest bez šumu", 0.38), ("učeno bez šumu,\ntest se šumem", 10.15),
                  ("učeno se šumem,\ntest se šumem", 2.64), ("se šumem a\ntřemi časy", 2.33)]
    j["curve"] = [(6, 7.3), (12, 6.9), (30, 1.47), (60, 0.83), (119, 0.38)]
    return j


def secs(t):
    m, s = t.split(":")
    return int(m) * 60 + int(s)


def script_sections():
    """Map 1..8 and "demo" to (seconds, main sentence, rows) from presentation/pitch-script.md.

    rows are (start "m:ss", seconds, speaker, spoken text) taken from the timed tables.
    """
    text = (REPO / "presentation/pitch-script.md").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^### (Snímek (\d+)|Živá ukázka)[^\n]*?, (\d+) s\)\n(.*?)(?=^##)", text, re.S | re.M):
        key = int(m.group(2)) if m.group(2) else "demo"
        body = m.group(4)
        main = re.search(r"^Hlavní věta: (.+)$", body, re.M)
        rows = [tuple(c.strip() for c in r.split("|")[1:5])
                for r in body.splitlines() if re.match(r"^\| \d+:\d\d \|", r)]
        out[key] = (int(m.group(3)), main.group(1) if main else "", rows)
    return out


def notes_text(section, name, start=None, end=None):
    """Speaker notes for one screen: the script rows spoken while it is up (start <= time < end)."""
    total, main, rows = section
    picked = [r for r in rows if (start is None or secs(r[0]) >= secs(start)) and (end is None or secs(r[0]) < secs(end))]
    span = sum(int(r[1]) for r in picked)
    head = f"{name}: {span} s z {total} s" if (start or end) else f"{name}: {total} s"
    return "\n".join([head, f"Hlavní věta: {main}"] + [f"{r[0]} ({r[1]} s) {r[2]}: {r[3]}" for r in picked])


# ---------- drawing helpers ----------

def box(slide, x, y, w, h, fill=None, line=None, alpha=None):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if fill and alpha is None else MSO_SHAPE.RECTANGLE,
                               Emu(int(x * IN)), Emu(int(y * IN)), Emu(int(w * IN)), Emu(int(h * IN)))
    if fill:
        if alpha is None:
            s.adjustments[0] = 0.06
        s.fill.solid()
        s.fill.fore_color.rgb = fill
        if alpha is not None:  # python-pptx has no API for fill transparency
            clr = s.fill._xPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
            etree.SubElement(clr, qn("a:alpha")).set("val", str(int(alpha * 100000)))
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def picture(slide, name, x, y, w, h=None):
    return slide.shapes.add_picture(str(ASSETS / name), Emu(int(x * IN)), Emu(int(y * IN)), Emu(int(w * IN)),
                                    Emu(int(h * IN)) if h else None)


def text(slide, x, y, w, h, runs, size=18, color=TEXT, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """runs: a string, or a list of paragraphs, each a string or a list of (text, size, color, bold)."""
    tb = box(slide, x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = [runs] if isinstance(runs, str) else runs
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(size * 0.35)
        for t in ([(para, size, color, bold)] if isinstance(para, str) else para):
            r = p.add_run()
            r.text, (sz, col, b) = t[0], t[1:]
            r.font.name, r.font.size, r.font.color.rgb, r.font.bold = FONT, Pt(sz), col, b
    return tb


def tile(slide, x, y, w, h, number, label, accent=ORANGE, size=44):
    box(slide, x, y, w, h, fill=PANEL)
    box(slide, x, y + 0.18, 0.07, h - 0.36, fill=accent)
    text(slide, x + 0.3, y + 0.15, w - 0.45, h * 0.55, number, size=size, color=accent, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
    text(slide, x + 0.3, y + 0.15 + h * 0.55, w - 0.45, h * 0.4 - 0.2, label, size=14, color=MUTED)


def frame(prs, n, kicker, title, notes, background=None, shade=0.0):
    """One screen of talk slide n. background: an asset drawn full bleed, darkened by a navy veil of opacity shade."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = NAVY
    if background:
        picture(s, background, 0, 0, 13.333, 7.5)
        if shade:
            box(s, 0, 0, 13.333, 7.5, fill=NAVY, alpha=shade)
    bar = box(s, 0.6, 0.55, 0.6, 0.06, fill=ORANGE)
    bar.adjustments[0] = 0.5
    text(s, 0.6, 0.72, 10, 0.35, kicker.upper(), size=13, color=ORANGE, bold=True)
    if title:
        text(s, 0.6, 1.05, 12.1, 0.9, title, size=30, bold=True)
    text(s, 0.6, 7.0, 9, 0.3, "Tvar plazmatu z magnetických měření · tokamak COMPASS · úloha ÚFP 1", size=10,
         color=MUTED)
    text(s, 11.7, 7.0, 1.0, 0.3, f"{n} / 8" if isinstance(n, int) else n, size=10, color=MUTED, align=PP_ALIGN.RIGHT)
    s.notes_slide.notes_text_frame.text = notes
    return s


def caption(slide, x, y, w, words):
    text(slide, x, y, w, 0.3, words, size=11, color=MUTED)


def style_chart(chart, legend=True, size=12):
    chart.font.name, chart.font.size, chart.font.color.rgb = FONT, Pt(size), MUTED
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False
        chart.legend.font.color.rgb, chart.legend.font.size = TEXT, Pt(size)
    for ax in (chart.category_axis, chart.value_axis):
        ax.format.line.color.rgb = LINE
        ax.tick_labels.font.color.rgb, ax.tick_labels.font.size = MUTED, Pt(size)
    chart.value_axis.has_major_gridlines = True
    chart.value_axis.major_gridlines.format.line.color.rgb = LINE
    chart.category_axis.has_major_gridlines = False


def label_points(series, values, nd, color, size=12, suffix=""):
    """Write each data label as text so the decimal comma does not depend on the viewer's locale.

    nd is the number of decimals, or a function of the value that returns it.
    """
    for i, v in enumerate(values):
        dl = series.points[i].data_label
        dl.has_text_frame = True
        dl.text_frame.text = cz(v, nd(v) if callable(nd) else nd) + suffix
        dl.position = XL_LABEL_POSITION.OUTSIDE_END
        r = dl.text_frame.paragraphs[0].runs[0]
        r.font.size, r.font.color.rgb, r.font.bold, r.font.name = Pt(size), color, True, FONT


def chart(slide, x, y, w, h, kind, cats, series, colors):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, vals)
    gf = slide.shapes.add_chart(kind, Emu(int(x * IN)), Emu(int(y * IN)), Emu(int(w * IN)), Emu(int(h * IN)), cd)
    c = gf.chart
    c.has_title = False
    for s, col in zip(c.plots[0].series, colors):
        if kind in (XL_CHART_TYPE.LINE_MARKERS,):
            s.format.line.color.rgb, s.format.line.width = col, Pt(3)
            s.marker.format.fill.solid()
            s.marker.format.fill.fore_color.rgb = col
            s.marker.format.line.color.rgb = col
            s.smooth = False
        else:
            s.format.fill.solid()
            s.format.fill.fore_color.rgb = col
    return c


def highlight(c, idx, color=ORANGE):
    for i in idx:
        pt = c.plots[0].series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = color


# ---------- slides ----------

def build():
    j, sc = load(), script_sections()
    b, mlp, ridge = j["baseline"], j["baseline"]["average"]["mlp"], j["baseline"]["average"]["ridge"]
    lat, inp, tm = j["latency"], j["inputs"], j["time"]
    one = lat["cpu_1_thread_single_sample"]
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # 1 Problem, screen a (0:00 to 0:24): the fear, full bleed illustration
    s = frame(prs, 1, "Problém", None, notes_text(sc[1], "Snímek 1a", end="0:24"), "04-wall-damage.png", 0.35)
    box(s, 0, 4.9, 13.333, 2.6, fill=NAVY, alpha=0.75)
    text(s, 0.6, 5.2, 12.1, 1.0, "Plazma se musí udržet dál od stěny", size=40, bold=True)
    text(s, 0.6, 6.05, 12.1, 0.5, "Celý výboj trvá jen 150 až 200 milisekund.", size=20, color=MUTED)
    caption(s, 9.2, 6.6, 3.5, "Ilustrace, ne fotografie.")

    # 1 Problem, screen b (0:24 to 0:50): minutes against milliseconds, then the question
    s = frame(prs, 1, "Problém", "Minuty proti milisekundám",
              notes_text(sc[1], "Snímek 1b", start="0:24"), "02-minutes-vs-ms.png", 0.55)
    tile(s, 0.6, 2.5, 5.8, 2.0, "minuty", "trvá klasický výpočet tvaru plazmatu", accent=MUTED, size=54)
    tile(s, 6.9, 2.5, 5.8, 2.0, "jednotky ms", "na reakci dává zadání úlohy", accent=ORANGE, size=54)
    box(s, 0.6, 4.95, 12.1, 1.5, fill=PANEL)
    text(s, 0.9, 5.15, 11.5, 1.2, [[("Otázka: ", 24, ORANGE, True),
                                    ("odhadne malá neuronová síť tvar plazmatu z magnetických měření dost přesně "
                                     "a dost rychle?", 24, TEXT, False)]])

    # 2 Data: tiles left, coil schematic right
    rows, dis = 42972, 149
    s = frame(prs, 2, "Data", f"{cz(rows, 0)} okamžiků ze {dis} výbojů tokamaku COMPASS",
              notes_text(sc[2], "Snímek 2"))
    tile(s, 0.6, 2.2, 5.2, 1.3, "24", "magnetických měření: 16 cívek a 8 smyček toku", accent=BLUE, size=36)
    tile(s, 0.6, 3.65, 5.2, 1.3, "16", "hledaných veličin tvaru: osa, bod X, dotykové body, protažení", ORANGE, 36)
    tile(s, 0.6, 5.1, 5.2, 1.3, str(dis), "výbojů; učení a test dělíme vždy po celých výbojích", accent=BLUE, size=36)
    picture(s, "03-coils.png", 6.2, 2.2, 6.5)
    caption(s, 6.2, 5.95, 6.5, "Schéma, ne skutečný řez. Smyčky toku na něm nejsou.")
    text(s, 6.2, 6.3, 6.5, 0.5, [[("Data jsou důvěrná: ", 14, ORANGE, True),
                                  ("ukazujeme jen souhrnná čísla.", 14, TEXT, False)]])

    # 3 Method: flow tiles left, principle illustration right
    s = frame(prs, 3, "Metoda", "Malá neuronová síť proti lineárnímu modelu", notes_text(sc[3], "Snímek 3"))
    steps = [("24", "magnetických měření", BLUE), (cz(lat["parameters"], 0), "parametrů sítě 256 · 256 · 128", ORANGE),
             ("16", "veličin tvaru najednou", BLUE)]
    for i, (num, lab, col) in enumerate(steps):
        y = 2.1 + i * 1.45
        tile(s, 0.6, y, 5.2, 1.15, num, lab, accent=col, size=32)
        if i < 2:
            text(s, 0.6, y + 1.12, 5.2, 0.35, "↓", size=18, color=MUTED, align=PP_ALIGN.CENTER)
    picture(s, "06-neural-bridge.png", 6.2, 2.1, 6.5)
    caption(s, 6.2, 5.85, 6.5, "Ilustrace principu; skutečných vstupů je 24, ne 16.")
    text(s, 0.6, 6.35, 12.1, 0.6, [[("Ověření: ", 16, ORANGE, True),
                                    (f"{b['folds']} různých rozdělení výbojů; chyby vždy na výbojích, které model "
                                     "neviděl.", 16, TEXT, False)]])

    # 4 Results, screen a (1:45 to 1:54): what we estimate
    s = frame(prs, 4, "Výsledky", "Co odhadujeme", notes_text(sc[4], "Snímek 4a", end="1:54"))
    picture(s, "05-shape-schematic.png", 2.3, 1.9, 8.7)
    for (x, y, words) in [(0.6, 3.5, "osa plazmatu\nuprostřed"), (0.6, 5.5, "bod X\ndole"),
                          (10.9, 5.5, "dva dotykové body,\nkam dopadá okraj")]:
        text(s, x, y, 2.0, 0.9, words, size=16, color=TEXT, bold=True)
    caption(s, 2.3, 6.8 - 0.05, 8.7, "Schéma tvaru, ne skutečný výboj.")

    # 4 Results, screen b (1:54 to 2:14): errors against the linear model
    s = frame(prs, 4, "Výsledky", "Osa, bod X i dotykové body s chybou pod půl milimetru",
              notes_text(sc[4], "Snímek 4b", start="1:54", end="2:14"))
    tile(s, 0.6, 2.2, 3.6, 1.45, f"{cz(mlp['R_mag_axis']['mae'], 2)} mm", "průměrná chyba polohy osy", BLUE, 34)
    tile(s, 0.6, 3.8, 3.6, 1.45, f"{cz(mlp['R_x_point']['mae'], 2)} mm", "průměrná chyba bodu X", BLUE, 34)
    tile(s, 0.6, 5.4, 3.6, 1.45, f"{cz(mlp['is_limited']['accuracy'] * 100, 1)} %",
         "správně určeno, zda plazma leží na limiteru", ORANGE, 34)
    keys = [("R_mag_axis", "osa R"), ("Z_mag_axis", "osa Z"), ("R_x_point", "bod X R"), ("Z_x_point", "bod X Z"),
            ("R_strike_point_1", "dotyk 1 R"), ("Z_strike_point_1", "dotyk 1 Z")]
    rv, mv = [ridge[k]["mae"] for k, _ in keys], [mlp[k]["mae"] for k, _ in keys]
    text(s, 4.6, 2.15, 8.1, 0.4, "Průměrná chyba v mm na náhodně vybraných výbojích, které model neviděl", size=14,
         color=MUTED)
    c = chart(s, 4.5, 2.45, 8.3, 4.4, XL_CHART_TYPE.COLUMN_CLUSTERED, [n for _, n in keys],
              [("lineární model", rv), ("neuronová síť", mv)], [MUTED, ORANGE])
    style_chart(c)
    c.plots[0].gap_width, c.plots[0].overlap = 60, -10
    label_points(c.plots[0].series[0], rv, 1, MUTED, 11)
    label_points(c.plots[0].series[1], mv, 2, ORANGE, 11)
    c.value_axis.visible = False

    # 4 Results, screen c (2:14 to 2:30): how many inputs are needed (pitch script, Lead note 1b)
    runs = inp["runs"]
    topk = sorted((int(k.split()[1]), v) for k, v in runs.items() if k.startswith("top"))
    topk.append((24, runs["all 24"]))
    s = frame(prs, 4, "Výsledky", "Kolik vstupů stačí", notes_text(sc[4], "Snímek 4c", start="2:14"))
    text(s, 0.6, 2.05, 8.0, 0.4, "Souhrnná relativní chyba podle počtu vstupů (menší je lepší)", size=14, color=MUTED)
    vals = [v["summary_nrmse_mean"] for _, v in topk]
    c = chart(s, 0.5, 2.35, 8.3, 4.4, XL_CHART_TYPE.LINE_MARKERS, [str(k) for k, _ in topk], [("chyba", vals)],
              [ORANGE])
    style_chart(c, legend=False)
    label_points(c.plots[0].series[0], vals, 3, TEXT, 11)
    for i in range(len(vals)):
        c.plots[0].series[0].points[i].data_label.position = XL_LABEL_POSITION.ABOVE
    c.value_axis.visible = False
    caption(s, 0.6, 6.7, 8.0, "počet vstupů; nejlepší sada vybraná zvlášť v každém rozdělení")
    tile(s, 9.1, 2.35, 3.6, 1.35, cz(runs["IPR only (16)"]["summary_nrmse_mean"], 3), "jen 16 cívek", BLUE, 32)
    tile(s, 9.1, 3.85, 3.6, 1.35, cz(runs["FL only (8)"]["summary_nrmse_mean"], 3), "jen 8 smyček toku", MUTED, 32)
    text(s, 9.1, 5.4, 3.6, 1.3, "Pořadí důležitosti platí pro naučenou síť, neříká, kolik informace vstup nese.",
         size=13, color=MUTED)

    # Live demo divider (2:30 to 4:05); the presenter switches to the browser
    s = frame(prs, "ukázka", "Živá ukázka", None, notes_text(sc["demo"], "Živá ukázka"))
    text(s, 0.6, 2.6, 12.1, 1.2, "Živá ukázka", size=60, bold=True, align=PP_ALIGN.CENTER)
    text(s, 0.6, 3.9, 12.1, 0.8, "Skutečný a odhadnutý tvar plazmatu vedle sebe, chyba v čase", size=24, color=MUTED,
         align=PP_ALIGN.CENTER)
    text(s, 0.6, 5.0, 12.1, 0.6, "Prohlížeč tvaru běží bez připojení k internetu", size=16, color=BLUE,
         align=PP_ALIGN.CENTER)

    # Hidden backup: the stills for "Záloha, když ukázka selže"
    s = frame(prs, "záloha", "Záloha ukázky", "Uložené obrázky z prohlížeče tvaru",
              "Skrytý snímek pro zálohu, když ukázka selže (pitch-script.md, Záloha). Ukázat začátek, střed a konec.")
    s._element.set("show", "0")
    for i, (name, words) in enumerate([("viewer-start-limited.png", "začátek výboje"),
                                       ("viewer-middle-divertor.png", "střed výboje"),
                                       ("viewer-rough-end.png", "konec výboje")]):
        x = 0.6 + i * 4.1
        picture(s, name, x, 2.4, 3.9)
        text(s, x, 4.75, 3.9, 0.4, words, size=16, color=TEXT, bold=True, align=PP_ALIGN.CENTER)

    # 5 Real time verdict, over the minutes against milliseconds image
    s = frame(prs, 5, "Verdikt pro řízení v reálném čase", "Jeden odhad trvá setiny milisekundy",
              notes_text(sc[5], "Snímek 5"), "02-minutes-vs-ms.png", 0.8)
    tile(s, 0.6, 2.3, 5.9, 2.3, f"{cz(one['median_ms'], 4)} ms", "medián jednoho odhadu na procesoru", ORANGE, 60)
    # p99, not the maximum: 5000 calls on an ordinary OS bound nothing (docs/review-findings.md, latency finding)
    tile(s, 6.85, 2.3, 5.9, 2.3, f"{cz(one['p99_ms'], 4)} ms", "99 % odhadů je rychlejších", BLUE, 60)
    text(s, 0.6, 5.0, 12.1, 1.8, [
        [("Výpočet sítě není překážkou: ", 20, ORANGE, True),
         ("zadání dává jednotky až desítky milisekund. Neověřeno: sběr signálů z čidel a běh na systému "
          "reálného času.", 20, TEXT, False)],
        [("Grafická karta nepomůže: ", 20, ORANGE, True),
         (f"pro tak malou síť je pomalejší ({cz(lat['mps_single_sample']['median_ms'], 2)} ms).", 20, TEXT, False)],
        [("Měřeno na nezatíženém počítači Mac vedoucího týmu; na druhém počítači vyšel medián 0,032 ms.", 14, MUTED,
          False)]])

    # 6 Limits
    s = frame(prs, 6, "Meze", "Nejslabší je bod u limiteru a konec výboje", notes_text(sc[6], "Snímek 6"))
    tile(s, 0.6, 2.2, 3.6, 2.0, f"{cz(mlp['R_limiter']['mae'], 1)} mm", "chyba bodu u limiteru, radiálně", ORANGE, 40)
    tile(s, 0.6, 4.4, 3.6, 2.0, f"{cz(mlp['Z_limiter']['mae'], 1)} mm", "chyba bodu u limiteru, svisle", ORANGE, 40)
    dec = tm["mae_by_time_decile"]["R_mag_axis"]
    cats = [f"{i * 10 + 5} %" for i in range(10)]  # middle of each tenth of the discharge
    text(s, 4.6, 2.15, 8.1, 0.4, "Chyba polohy osy (mm) podle času výboje", size=14, color=MUTED)
    c = chart(s, 4.5, 2.45, 8.3, 4.0, XL_CHART_TYPE.COLUMN_CLUSTERED, cats, [("osa R", dec)], [BLUE])
    style_chart(c, legend=False)
    c.plots[0].gap_width = 40
    highlight(c, (0, 8, 9))
    label_points(c.plots[0].series[0], dec, 2, TEXT, 11)
    c.value_axis.visible = False
    jr = tm["jitter_ratio"].values()  # all targets in the file, not the most favourable one (review finding)
    text(s, 4.6, 6.45, 8.1, 0.4, f"Na čistých vstupech kolísá výstup podobně jako skutečnost: poměr {cz(min(jr), 2)} "
         f"až {cz(max(jr), 2)} u {len(jr)} veličin.", size=13, color=MUTED)

    # 7 What the model cannot do
    s = frame(prs, 7, "Co model neumí", "Zná jen tvary z dat a šum v měření mu vadí nejvíc", notes_text(sc[7], "Snímek 7"))
    nz = j["noise"]
    text(s, 0.6, 2.15, 6.2, 0.4, "Chyba polohy osy (mm) při šumu v měření", size=14, color=MUTED)
    c = chart(s, 0.5, 2.45, 6.4, 3.6, XL_CHART_TYPE.COLUMN_CLUSTERED, [n for n, _ in nz], [("osa", [v for _, v in nz])],
              [BLUE])
    style_chart(c, legend=False, size=10)
    c.plots[0].gap_width = 50
    highlight(c, (1,))
    label_points(c.plots[0].series[0], [v for _, v in nz], 2, TEXT, 11)
    c.value_axis.visible = False
    cv = j["curve"]
    text(s, 7.2, 2.15, 5.6, 0.4, "Chyba osy (mm) podle počtu učících výbojů, vždy 60 epoch", size=14, color=MUTED)
    c = chart(s, 7.1, 2.45, 5.8, 3.6, XL_CHART_TYPE.LINE_MARKERS, [str(n) for n, _ in cv],
              [("osa", [v for _, v in cv])], [ORANGE])
    style_chart(c, legend=False, size=11)
    label_points(c.plots[0].series[0], [v for _, v in cv], lambda v: 1 if v >= 5 else 2, TEXT, 11)  # source precision
    for i in range(len(cv)):
        c.plots[0].series[0].points[i].data_label.position = XL_LABEL_POSITION.ABOVE
    c.value_axis.visible = False
    text(s, 0.6, 6.15, 12.1, 0.8, [
        [("Neobvyklý tvar mimo data: ", 16, ORANGE, True), ("DOPLNIT, zatím neměřeno. ", 16, TEXT, False),
         ("Jen jeden tokamak. Model odhaduje tvar, řízení sám nenahradí.", 16, MUTED, False)]])

    # 8 Close: one number
    s = frame(prs, 8, "Závěr", None, notes_text(sc[8], "Snímek 8"), "07-closing.png", 0.45)
    text(s, 0.6, 2.0, 6.8, 0.5, "Jeden odhad tvaru plazmatu", size=22, color=MUTED)
    text(s, 0.6, 2.5, 6.8, 1.6, f"{cz(one['median_ms'], 4)} ms", size=88, color=ORANGE, bold=True)
    text(s, 0.6, 4.2, 6.8, 1.0, "Klasický výpočet trvá minuty. Zadání chce jednotky až desítky milisekund.",
         size=20, color=TEXT)
    for i, (head, body, col) in enumerate([
            ("Přesný", "desetiny milimetru na ose, bodu X a dotykových bodech", BLUE),
            ("Zbývá", "bod u limiteru, neobvyklé tvary, odolnost proti šumu, napojení na řízení", MUTED)]):
        y = 2.0 + i * 1.9
        box(s, 7.9, y, 4.8, 1.6, fill=PANEL)
        box(s, 7.9, y + 0.2, 0.07, 1.2, fill=col)
        text(s, 8.2, y + 0.2, 4.4, 1.3, [[(head, 22, col, True)], [(body, 15, TEXT, False)]])
    text(s, 0.6, 6.1, 12.1, 0.6, "Desetiny milimetru za setiny milisekundy.", size=22, bold=True,
         align=PP_ALIGN.CENTER)

    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build())
