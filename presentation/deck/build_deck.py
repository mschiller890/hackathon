#!/usr/bin/env python
"""Build presentation/deck/slides.pptx (16:9, Czech) for IPP task 1.

    ~/.venvs/hackathon/bin/python -I presentation/deck/build_deck.py

Structure and seconds follow presentation/pitch-script.md (Lead's decision, docs/PLAN.md RP-11): talk slides 1 to 8
plus the live demo between 4 and 5. A talk slide may span several screens (slide 1 switches image at 0:21, slide 4
has schematic, results and inputs); its speaker notes carry only the script lines spoken while it is up. Two hidden
backup screens hold the camera bonus and the viewer stills for the "ukázka selže" fallback. No page counter: the
audience sees 14 screens (docs/deck-fixes.md 0.1).

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
from pptx.chart.data import CategoryChartData, XyChartData
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
# LIGHT: the comparison series, lighter than MUTED so it differs from orange in luminance too; BAD: highlight for a failure,
# so that orange keeps one meaning on every chart ("the model we use").
LIGHT, BAD = RGBColor(0xD5, 0xDC, 0xEB), RGBColor(0xD5, 0x5E, 0x00)
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
                  ("učeno se šumem,\ntest se šumem", 2.64)]
    j["noisy_on_clean"] = 2.22  # trained on noise, tested clean (same table)
    j["curve"] = [(6, 7.3), (12, 6.9), (30, 1.47), (60, 0.83), (119, 0.38)]
    # results/ipp1-distribution.md (REQ-007), R_mag_axis in mm: median, p99, MAE on limited and on diverted rows.
    j["tails"] = {"median": 0.153, "p99": 3.74, "limited": 0.553, "diverted": 0.237}
    # results/ipp1-final.md: blocked by discharge id against random group folds, plain baseline, clean inputs.
    j["blocked"] = (1.5, 2.9)
    # results/ipp1-unusual-shapes.md (REQ-B08): error factor range when a shape family is left out of training, and the
    # R axis MAE of the low elongation group (random fold against family held out).
    j["unusual"] = {"factor": (1.0, 3.0), "axis": (0.68, 1.63)}
    # results/ipp1-final.md, locked test set (30 discharges), clean inputs, pooled MAE: (baseline MLP, shipped candidate).
    # The candidate ships for clean inputs (docs/PLAN.md KQ-8); p99 and worst rows from the same tables.
    j["final"] = {"R_mag_axis": (0.307, 0.133), "Z_mag_axis": (0.321, 0.172), "R_x_point": (0.161, 0.115),
                  "R_strike_point_1": (0.212, 0.108), "R_limiter": (10.6, 4.55), "Z_limiter": (22.5, 8.35),
                  "plasma_current": (1.2, 0.0347), "p99_limiter": (77.5, 92.2), "x_worst": (2.76, 10.1),
                  "cv_axis": 0.23, "blocked_axis": 0.397}
    # Same file, noisy inputs, 30 held-out discharges: the noise-trained baseline that is used there, and the selected
    # model, which collapses on noisy inputs.
    j["noisy_final"] = {"axis": 2.38, "current": 4.65, "limiter": (25.8, 38.9), "selected_axis": 190}
    # results/ipp1-latency-shipped.md, rows numpy_end_to_end_limited and _diverted: selected model pair, one core, Apple M5
    # on a busy machine (load about 7), random weights of the trained shapes, so timing only.
    j["shipped_latency"] = {"limited": 0.0274, "diverted": 0.0154, "p99": 0.093}
    # results/cloud-camera-findings.md, 5 folds, grey camera CNN MAE against the magnetic baseline; nRMSE ratio range.
    j["camera"] = {"R_mag_axis": (1.70, 0.377), "Z_mag_axis": (2.40, 0.391), "R_x_point": (1.50, 0.202),
                   "R_strike_point_1": (2.25, 0.265), "ratio": (1.3, 13), "colour_grey": (1.79, 1.70), "current": 14.0}
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


def tile(slide, x, y, w, h, number, label, accent=ORANGE, size=44, label_size=16):
    box(slide, x, y, w, h, fill=PANEL)
    box(slide, x, y + 0.18, 0.07, h - 0.36, fill=accent)
    text(slide, x + 0.3, y + 0.1, w - 0.45, h * 0.5, number, size=size, color=accent, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
    text(slide, x + 0.3, y + 0.1 + h * 0.5, w - 0.45, h * 0.45 - 0.1, label, size=label_size, color=MUTED)


def frame(prs, kicker, title, notes, background=None, shade=0.0):
    """One screen. background: an asset drawn full bleed, darkened by a navy veil of opacity shade."""
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
    s.notes_slide.notes_text_frame.text = notes
    return s


def add_sources(slide, files):
    """Append the files the screen's numbers come from to its notes, so each number can be checked against its own file."""
    tf = slide.notes_slide.notes_text_frame
    tf.text = tf.text + "\nZdroje čísel: " + "; ".join(files)


def backup_notes(section, head):
    """Notes for a hidden screen from an untimed pitch-script section such as "## Záloha: kamera"."""
    text = (REPO / "presentation/pitch-script.md").read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(section)}[^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
    rows = [[c.strip() for c in r.split("|")[1:5]] for r in (m.group(1) if m else "").splitlines()
            if r.startswith("| ") and not r.startswith("| Čas") and not r.startswith("|---")]
    return "\n".join([head] + [f"{r[0]} ({r[1]} s) {r[2]}: {r[3]}" for r in rows])


def log_axis(axis, lo, hi):
    """Logarithmic value axis; python-pptx has no API for it, so set c:logBase in the axis scaling."""
    scaling = axis._element.find(qn("c:scaling"))
    lb = etree.SubElement(scaling, qn("c:logBase"))
    lb.set("val", "10")
    scaling.remove(lb)
    scaling.insert(0, lb)  # schema order: logBase comes first in c:scaling
    axis.minimum_scale, axis.maximum_scale = lo, hi


def caption(slide, x, y, w, words, size=14):
    text(slide, x, y, w, 0.4, words, size=size, color=MUTED)


def chart_title(slide, x, y, w, words):
    """The chart's own title with its unit at 16 pt (the value axes stay hidden; the data labels carry the values)."""
    text(slide, x, y, w, 0.45, words, size=16, color=TEXT, bold=True)


def notes_extra(slide, lines):
    """Text taken off the screen for the projector (fix 1) stays in the speaker notes, ready for questions."""
    tf = slide.notes_slide.notes_text_frame
    tf.text = tf.text + "\nNa obrazovce není, řekni při dotazu:\n" + "\n".join("• " + l for l in lines)


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
    c.value_axis.minimum_scale = 0
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
# Wording follows docs/deck-fixes.md (review 2): "základní síť", "vybraný model", "odložené výboje"; item numbers in comments.

def build():
    j, sc = load(), script_sections()
    b = j["baseline"]
    lat, inp, tm = j["latency"], j["inputs"], j["time"]
    one, e2e = lat["cpu_1_thread_single_sample"], lat["cpu_end_to_end_numpy"]
    fn, cm, us, nf = j["final"], j["camera"], j["unusual"], j["noisy_final"]
    sl = j["shipped_latency"]
    shipped_txt = (f"{cz(sl['limited'], 3)} ms", "vybraný model, limitované plazma, procesor Apple M5, vytížený notebook")
    assert sl["p99"] < 0.1  # the footnote promises p99 under 0,1 ms
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # 1 Problem, screen a (0:00 to 0:21): the fear, full bleed illustration
    s = frame(prs, "Problém", None, notes_text(sc[1], "Snímek 1a", end="0:21"), "04-wall-damage.png", 0.35)
    box(s, 0, 4.9, 13.333, 2.6, fill=NAVY, alpha=0.75)
    text(s, 0.6, 5.2, 12.1, 1.0, "Plazma se musí udržet dál od stěny", size=40, bold=True)
    text(s, 0.6, 6.05, 12.1, 0.5, "Celý výboj trvá podle organizátorů jen 150 až 200 milisekund.", size=20, color=MUTED)
    text(s, 9.2, 6.55, 3.5, 0.4, "Ilustrace, ne fotografie.", size=14, color=TEXT)
    add_sources(s, ["results/ipp1-data.md (150 až 200 ms je údaj organizátorů)"])

    # 1 Problem, screen b (0:21 to 0:38): minutes against milliseconds, then the question
    s = frame(prs, "Problém", "Minuty proti milisekundám", notes_text(sc[1], "Snímek 1b", start="0:21"),
              "02-minutes-vs-ms.png", 0.55)
    tile(s, 0.6, 2.5, 5.8, 2.0, "minuty", "trvá klasický výpočet tvaru plazmatu", accent=MUTED, size=54)
    tile(s, 6.9, 2.5, 5.8, 2.0, "jednotky ms", "na reakci dává zadání úlohy", accent=ORANGE, size=54)
    box(s, 0.6, 4.95, 12.1, 1.5, fill=PANEL)
    text(s, 0.9, 5.15, 11.5, 1.2, [[("Otázka: ", 24, ORANGE, True),
                                    ("odhadne malá neuronová síť tvar plazmatu z magnetických měření dost přesně "
                                     "a dost rychle?", 24, TEXT, False)]])
    caption(s, 11.6, 6.65, 1.2, "Ilustrace.")
    add_sources(s, ["zadání úlohy (minuty, jednotky ms)"])

    # 2 Data: tiles left, coil schematic right
    rows, dis = 42972, 149
    s = frame(prs, "Data", f"{cz(rows, 0)} okamžiků ze {dis} výbojů tokamaku COMPASS", notes_text(sc[2], "Snímek 2"))
    tile(s, 0.6, 2.1, 5.2, 1.4, "24", "magnetických měření: 16 cívek, 8 smyček toku", accent=BLUE, size=36)
    tile(s, 0.6, 3.65, 5.2, 1.4, "16", "hledaných veličin tvaru", ORANGE, 36)
    tile(s, 0.6, 5.2, 5.2, 1.4, str(dis), "výbojů; dělíme vždy po celých výbojích", accent=BLUE, size=36)
    picture(s, "03-coils.png", 6.2, 2.1, 6.5)
    caption(s, 6.2, 5.85, 6.5, "Schéma, ne skutečný řez. Smyčky toku na něm nejsou.")
    text(s, 6.2, 6.3, 6.5, 0.5, [[("Data jsou důvěrná: ", 18, ORANGE, True),
                                  ("jen souhrnná čísla.", 18, TEXT, False)]])
    notes_extra(s, ["16 veličin: osa, bod X, dotykové body, protažení, trojúhelníkovost, proud, bod u limiteru"])
    add_sources(s, ["results/ipp1-data.md"])

    # 3 Method (items 3.1 to 3.3)
    s = frame(prs, "Metoda", "Malá neuronová síť proti lineárnímu modelu", notes_text(sc[3], "Snímek 3"))
    steps = [("24", "magnetických měření", BLUE), (cz(lat["parameters"], 0), "parametrů, vrstvy 256, 256 a 128", ORANGE),
             ("16", "veličin tvaru najednou", BLUE)]
    for i, (num, lab, col) in enumerate(steps):
        y = 2.1 + i * 1.35
        tile(s, 0.6, y, 5.2, 1.08, num, lab, accent=col, size=30, label_size=14)
        if i < 2:
            text(s, 0.6, y + 1.04, 5.2, 0.32, "↓", size=16, color=MUTED, align=PP_ALIGN.CENTER)
    text(s, 0.6, 6.15, 5.4, 0.6, "Vybraný model: základní síť plus tři úpravy.", size=16, color=TEXT)
    picture(s, "06-neural-bridge.png", 6.2, 2.1, 6.5)
    caption(s, 6.2, 5.85, 6.5, "Ilustrace principu; skutečných vstupů je 24, ne 16.")
    text(s, 6.2, 6.3, 6.5, 0.5, [[("Ověření: ", 16, ORANGE, True),
                                  ("5 dělení po výbojích a 30 odložených výbojů.", 16, TEXT, False)]])
    notes_extra(s, ["Vybraný model = základní síť + rozdíly sousedních cívek + lineární model pro proud + zvláštní síť "
                    "pro bod u limiteru.",
                    f"Základní síť: {b['folds']} různých rozdělení po výbojích (křížová validace: 5krát jiné rozdělení "
                    "na učení a test). Vybraný model: navíc 30 výbojů odložených před posledním výběrem."])
    add_sources(s, ["results/ipp1-baseline.md (107 152 parametrů, 5 dělení)", "results/ipp1-final.md (30 odložených)"])

    # 3b Camera, hidden backup (items 0.4, 5.1 to 5.5); spoken text from the script's "Záloha: kamera" section
    s = frame(prs, "Bonus: kamera",
              f"Kamerová síť je {cz(cm['ratio'][0], 1)} až {cz(cm['ratio'][1], 0)}krát horší než cívky",
              backup_notes("Záloha: kamera", "Skrytý snímek 5, kamera (bez vteřin v časovém plánu)"))
    s._element.set("show", "0")
    keys = [("R_mag_axis", "osa R"), ("Z_mag_axis", "osa Z"), ("R_x_point", "bod X R"), ("R_strike_point_1", "dotyk 1 R")]
    cv_, mv_ = [cm[k][0] for k, _ in keys], [cm[k][1] for k, _ in keys]
    chart_title(s, 0.6, 2.0, 8.0, "Průměrná chyba (mm), 5 dělení po výbojích")
    c = chart(s, 0.5, 2.45, 8.3, 4.2, XL_CHART_TYPE.COLUMN_CLUSTERED, [n for _, n in keys],
              [("kamera, šedá", cv_), ("magnetická síť", mv_)], [LIGHT, ORANGE])
    style_chart(c, size=14)
    c.plots[0].gap_width, c.plots[0].overlap = 60, -10
    label_points(c.plots[0].series[0], cv_, 2, LIGHT, 14)
    label_points(c.plots[0].series[1], mv_, 2, ORANGE, 14)
    c.value_axis.visible = False
    tile(s, 9.1, 2.45, 3.6, 1.5, f"{cz(cm['current'], 0)} kA", "proud: tato síť ho neurčí", MUTED, 32)
    tile(s, 9.1, 4.1, 3.6, 1.5, f"{cz(cm['colour_grey'][0], 2)} mm", f"osa R barevně, šedá {cz(cm['colour_grey'][1], 2)}",
         LIGHT, 32)
    notes_extra(s, ["Barva nepomáhá. Srovnání je jen orientační: snímky jen ze 78 výbojů, 12 epoch, každý osmý snímek. "
                    "Platí pro tuto malou síť, ne pro kameru jako takovou."])
    add_sources(s, ["results/cloud-camera-findings.md (5 dělení, šedá kamera)"])

    # 4 Results, screen a (1:26 to 1:33): what we estimate
    s = frame(prs, "Výsledky", "Co odhadujeme", notes_text(sc[4], "Snímek 4a", end="1:33"))
    picture(s, "05-shape-schematic.png", 2.3, 1.9, 8.7)
    for (x, y, words) in [(0.6, 3.5, "osa plazmatu\nuprostřed"), (0.6, 5.5, "bod X\ndole"),
                          (10.9, 5.5, "dva dotykové body,\nkam dopadá okraj")]:
        text(s, x, y, 2.0, 0.9, words, size=16, color=TEXT, bold=True)
    caption(s, 2.3, 6.75, 8.7, "Schéma tvaru, ne skutečný výboj. R vodorovně, Z svisle.")

    # 4 Results, screen b (1:33 to 2:17): the selected model on the 30 held-out discharges (deck-fixes 7, visual QA 1, 3, 4)
    s = frame(prs, "Výsledky", f"Na 30 odložených výbojích: osa {cz(fn['R_mag_axis'][1], 2)} mm",
              notes_text(sc[4], "Snímek 4b", start="1:33", end="2:17"))
    text(s, 0.6, 1.72, 12.1, 0.4, f"v křížové validaci na 119 výbojích {cz(fn['cv_axis'], 2)} mm, na novějších číslech "
                                  f"výbojů {cz(fn['blocked_axis'], 2)} mm", size=18, color=MUTED)
    tile(s, 0.6, 2.35, 3.6, 1.45, f"{cz(fn['R_mag_axis'][1], 2)} mm", "průměrná chyba osy", BLUE, 32)
    tile(s, 0.6, 3.95, 3.6, 1.45, f"{cz(fn['R_limiter'][1], 2)} mm",
         f"bod u limiteru, dříve {cz(fn['R_limiter'][0], 1)} mm", ORANGE, 32)
    tile(s, 0.6, 5.55, 3.6, 1.45, f"{cz(fn['plasma_current'][1], 3)} kA",
         f"proud, lineární model (síť {cz(fn['plasma_current'][0], 1)} kA)", BLUE, 32)
    keys = [("R_mag_axis", "osa R"), ("Z_mag_axis", "osa Z"), ("R_x_point", "bod X R"), ("R_strike_point_1", "dotyk 1 R")]
    bv, nv = [fn[k][0] for k, _ in keys], [fn[k][1] for k, _ in keys]
    chart_title(s, 4.6, 2.35, 8.1, "Průměrná chyba (mm), 30 odložených výbojů")
    c = chart(s, 4.5, 2.8, 8.3, 4.2, XL_CHART_TYPE.COLUMN_CLUSTERED, [n for _, n in keys],
              [("základní síť", bv), ("vybraný model", nv)], [LIGHT, ORANGE])
    style_chart(c, size=14)
    c.plots[0].gap_width, c.plots[0].overlap = 60, -10
    label_points(c.plots[0].series[0], bv, 3, LIGHT, 14)
    label_points(c.plots[0].series[1], nv, 3, ORANGE, 14)
    c.value_axis.visible = False
    notes_extra(s, [
        "Výboje byly odloženy před posledním výběrem modelu; náměty na úpravy modelu vznikly na všech 149 výbojích.",
        f"Osa R, vybraný model: 30 odložených výbojů {cz(fn['R_mag_axis'][1], 2)} mm | křížová validace na 119 výbojích "
        f"{cz(fn['cv_axis'], 2)} mm | novější čísla výbojů {cz(fn['blocked_axis'], 2)} mm (učení na 60 nejnižších číslech).",
        f"Několik jednotlivých řádků je horších: nejhorší řádek bodu X {cz(fn['x_worst'][1], 1)} mm proti "
        f"{cz(fn['x_worst'][0], 2)} mm.",
        f"Zašuměné vstupy (soubor organizátorů): jiný model, učený se šumem: osa {cz(nf['axis'], 2)} mm, proud "
        f"{cz(nf['current'], 2)} kA, bod u limiteru {cz(nf['limiter'][0], 1)} a {cz(nf['limiter'][1], 1)} mm."])
    add_sources(s, ["results/ipp1-final.md (30 odložených výbojů, křížová validace, bloky, zašuměné vstupy)"])

    # 4 Results, screen c (2:17 to 2:29): how many inputs are needed (deck-fixes 8, visual QA 3 and 5a)
    runs = inp["runs"]
    topk = sorted((int(k.split()[1]), v) for k, v in runs.items() if k.startswith("top"))
    topk.append((24, runs["all 24"]))
    ipr, fl, top8 = (runs[k]["summary_nrmse_mean"] for k in ("IPR only (16)", "FL only (8)", "top 8"))
    s = frame(prs, "Výsledky", "Kolik vstupů stačí", notes_text(sc[4], "Snímek 4c", start="2:17"))
    text(s, 0.6, 1.72, 12.1, 0.4, f"Samotné cívky stačí skoro na stejnou chybu ({cz(ipr, 3)} proti "
                                  f"{cz(runs['all 24']['summary_nrmse_mean'], 3)}); osm nejlepších už ne ({cz(top8, 3)}).",
         size=18, color=MUTED)
    chart_title(s, 0.6, 2.35, 8.2, "Souhrnná chyba podle počtu vstupů (menší je lepší)")
    # Real spacing of 2 to 24 inputs (XY scatter), not nine equally spaced categories (visual QA fix 3)
    cd = XyChartData()
    ser = cd.add_series("chyba")
    for k, v in topk:
        ser.add_data_point(k, v["summary_nrmse_mean"])
    gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES, Emu(int(0.5 * IN)), Emu(int(2.8 * IN)), Emu(int(8.3 * IN)),
                            Emu(int(3.8 * IN)), cd)
    c = gf.chart
    c.has_title = False
    c.value_axis.minimum_scale = 0
    style_chart(c, legend=False, size=14)
    c.category_axis.minimum_scale, c.category_axis.maximum_scale = 0, 25
    se = c.plots[0].series[0]
    se.format.line.color.rgb, se.format.line.width, se.smooth = ORANGE, Pt(3), False
    se.marker.format.fill.solid()
    se.marker.format.fill.fore_color.rgb = ORANGE
    se.marker.format.line.color.rgb = ORANGE
    vals = [v["summary_nrmse_mean"] for _, v in topk]
    label_points(se, vals, 3, TEXT, 13)
    for i, (k, _) in enumerate(topk):
        # the steep part (3, 4 inputs) gets its labels beside the points so they do not sit on the line
        se.points[i].data_label.position = (XL_LABEL_POSITION.RIGHT if k in (3, 4) else
                                            XL_LABEL_POSITION.BELOW if k == 5 else XL_LABEL_POSITION.ABOVE)
    c.value_axis.visible = False
    caption(s, 0.6, 6.6, 8.2, "Vodorovně počet vstupů; body = nejlepší sada vybraná v každém dělení.")
    tile(s, 9.1, 2.45, 3.6, 1.5, cz(ipr, 3), "jen 16 cívek (pevná sada)", BLUE, 32)
    tile(s, 9.1, 4.1, 3.6, 1.5, cz(fl, 3), f"jen 8 smyček, {cz(fl / ipr, 1)}krát horší", MUTED, 32)
    text(s, 9.1, 5.8, 3.6, 1.0, "Chyba v násobcích rozptylu veličiny.", size=16, color=MUTED)
    notes_extra(s, [
        "Souhrnná relativní chyba: průměr přes 13 veličin bez bodu u limiteru, chyba vztažená k rozptylu veličiny.",
        f"Dlaždice {cz(ipr, 3)} je pevná sada 16 cívek; bod grafu u 16 ({cz(runs['top 16']['summary_nrmse_mean'], 3)}) "
        "je 16 nejlepších vstupů vybraných zvlášť v každém dělení. Dva různé běhy, proto se liší.",
        "Pořadí důležitosti platí pro naučenou síť, neříká, kolik informace vstup nese."])
    add_sources(s, ["results/ipp1-inputs.json", "results/ipp1-inputs.md"])

    # Live demo divider (2:29 to 3:49); the presenter switches to the browser (items 9.1, 9.2)
    s = frame(prs, "Živá ukázka", None,
              notes_text(sc["demo"], "Živá ukázka") + "\nZáloha: klávesa H otevře skrytý snímek s uloženými obrázky (jen PowerPoint; v Keynote a Google "
              "Slides odkrýt snímek předem).")
    text(s, 0.6, 2.6, 12.1, 1.2, "Živá ukázka", size=60, bold=True, align=PP_ALIGN.CENTER)
    # Since e50b1ee the viewer shows the selected model on the 30 held-out discharges, which predicts the points but
    # not the outline (its legend: "obrys model nepředpovídá"); docs/PLAN.md KQ-18
    text(s, 0.6, 3.9, 12.1, 0.9, [[("Skutečný tvar plazmatu a odhadnuté body, chyba v čase", 24, MUTED, False)],
                                  [("Výboj 85, odložený, vybraný model; obrys se nepředpovídá, ukazuje body (osa, bod X, "
                                    "dotykové body).", 18, MUTED, False)]], align=PP_ALIGN.CENTER)
    text(s, 0.6, 5.4, 12.1, 0.6, "Prohlížeč tvaru běží bez připojení k internetu", size=16, color=BLUE,
         align=PP_ALIGN.CENTER)

    # Hidden backup: the stills for "Záloha, když ukázka selže" (item 10)
    s = frame(prs, "Záloha ukázky", "Uložené obrázky z prohlížeče tvaru",
              "Skrytý snímek pro zálohu, když ukázka selže (pitch-script.md, Záloha). Ukázat začátek, střed a konec.")
    s._element.set("show", "0")
    for i, (name, words) in enumerate([("viewer-start-limited.png", "začátek výboje"),
                                       ("viewer-middle-divertor.png", "střed výboje"),
                                       ("viewer-rough-end.png", "konec výboje")]):
        x = 0.6 + i * 4.1
        picture(s, name, x, 2.4, 3.9)
        text(s, x, 4.75, 3.9, 0.4, words, size=16, color=TEXT, bold=True, align=PP_ALIGN.CENTER)
    caption(s, 0.6, 5.4, 12.1, "Začátek a střed: výboj 85, typický. Konec: výboj 147, špatný konec výboje (osa 33,7 mm). "
                               "Vybraný model, obrys se nepředpovídá, ukazuje body.", size=16)

    # 5 Real time verdict (deck-fixes 11, visual QA 1 and screen 11)
    s = frame(prs, "Verdikt pro řízení v reálném čase", "Výpočet sítě rychlosti nebrání", notes_text(sc[5], "Snímek 5"),
              "02-minutes-vs-ms.png", 0.8)
    # p99, not the maximum: 5000 calls on an ordinary OS bound nothing (docs/review-findings.md, latency finding)
    tile(s, 0.6, 2.3, 3.85, 2.2, f"{cz(one['median_ms'], 4)} ms", f"základní síť, medián, {lat['cpu']}", ORANGE, 44)
    tile(s, 4.72, 2.3, 3.85, 2.2, f"{cz(one['p99_ms'], 4)} ms", "základní síť, 99 % odhadů rychlejších", BLUE, 44)
    tile(s, 8.84, 2.3, 3.85, 2.2, shipped_txt[0], "vybraný model, limitované plazma", LIGHT, 44)
    text(s, 0.6, 4.9, 12.1, 1.6, [
        [("Zadání: jednotky až desítky ms; náš rozpočet 1 až 10 ms.", 20, ORANGE, True)],
        [("Neověřeno: ", 20, ORANGE, True), ("sběr signálů, nejhorší doba, zašuměné signály.", 20, TEXT, False)]])
    caption(s, 11.6, 6.65, 1.2, "Ilustrace.")
    notes_extra(s, [
        f"Celý odhad základní sítě od čísel na vstupu po čísla na výstupu: medián {cz(e2e['median_ms'], 4)} ms.",
        "p99: 99 % odhadů je rychlejších. Na systému bez reálného času se ojediněle objeví špičky.",
        f"Vybraný model: {shipped_txt[1]}; výpočet v Pythonu (numpy), náhodné váhy stejného tvaru, měří se jen čas; "
        f"divertorové plazma {cz(sl['diverted'], 3)} ms, p99 pod 0,1 ms."])
    add_sources(s, ["results/ipp1-latency.json (procesor, medián, p99, celý odhad)",
                    "results/ipp1-latency-shipped.md (vybraný model, numpy, 0,027 ms limitované, 0,015 ms divertorové)"])

    # 6 Limits (deck-fixes 12, visual QA 1, 4 and screen 12)
    s = frame(prs, "Meze", "Nejslabší je bod u limiteru, začátek a konec výboje", notes_text(sc[6], "Snímek 6"))
    tile(s, 0.6, 2.2, 3.6, 2.0, f"{cz(fn['R_limiter'][1], 2)} mm", f"bod u limiteru radiálně, p99 "
         f"{cz(fn['p99_limiter'][0], 1)} mm", ORANGE, 40)
    tile(s, 0.6, 4.4, 3.6, 2.0, f"{cz(fn['Z_limiter'][1], 2)} mm", f"svisle, p99 {cz(fn['p99_limiter'][1], 1)} mm", ORANGE, 40)
    caption(s, 0.6, 6.5, 3.6, "Vybraný model, 30 odložených výbojů.")
    dec = tm["mae_by_time_decile"]["R_mag_axis"]
    cats = [f"{i * 10 + 5} %" for i in range(10)]  # middle of each tenth of the discharge
    chart_title(s, 4.6, 2.2, 8.1, "Základní síť: chyba osy R (mm) podle času výboje")
    c = chart(s, 4.5, 2.65, 8.3, 3.8, XL_CHART_TYPE.COLUMN_CLUSTERED, cats, [("osa R", dec)], [BLUE])
    style_chart(c, legend=False, size=14)
    c.plots[0].gap_width = 40
    highlight(c, (0, 8, 9))
    label_points(c.plots[0].series[0], dec, 2, TEXT, 13)
    c.value_axis.visible = False
    caption(s, 4.6, 6.5, 8.1, "Vodorovně čas výboje v procentech jeho délky; 5 dělení po výbojích.")
    # Range over every target except the limiter outputs, not the most favourable one (claims-corrections.md item 2);
    # the limiter point sits near 0,5 because its truth jumps between wall contacts.
    jr = [v for k, v in tm["jitter_ratio"].items() if "limit" not in k]
    nz_c, nz_h = (tm["noisy"][v]["jitter_ratio"] for v in ("clean_on_noisy", "hardened_on_noisy"))
    lo, hi = j["blocked"]
    notes_extra(s, [
        f"Kolísání výstupu proti skutečnosti, základní síť: na čistých vstupech {cz(min(jr), 2)} až {cz(max(jr), 2)} "
        f"({len(jr)} veličin), na zašuměných {cz(nz_c['R_mag_axis'], 1)}krát (osa R) a {cz(nz_c['Z_mag_axis'], 1)}krát "
        f"(osa Z), po učení se šumem {cz(nz_h['R_mag_axis'], 1)} a {cz(nz_h['Z_mag_axis'], 2)}krát.",
        f"Na souvislých blocích čísel výbojů je chyba základní sítě {cz(lo, 1)} až {cz(hi, 1)}krát větší než na náhodně "
        "vybraných."])
    add_sources(s, ["results/ipp1-final.md (bod u limiteru, bloky čísel výbojů)",
                    "results/ipp1-time.json (chyba v čase, kolísání)"])

    # 7 What the model cannot do (deck-fixes 13, visual QA 1, 2, 3 and screen 13)
    s = frame(prs, "Co model neumí", "Šum mu vadí nejvíc; tvary mimo rozsah dat jsme neověřili", notes_text(sc[7], "Snímek 7"))
    nz = j["noise"]
    chart_title(s, 0.6, 1.95, 6.3, "Základní síť: chyba osy (mm) při šumu")
    c = chart(s, 0.5, 2.4, 6.4, 2.8, XL_CHART_TYPE.COLUMN_CLUSTERED, [n for n, _ in nz], [("osa", [v for _, v in nz])],
              [BLUE])
    style_chart(c, legend=False, size=14)
    c.plots[0].gap_width = 50
    highlight(c, (1,), BAD)
    label_points(c.plots[0].series[0], [v for _, v in nz], 2, TEXT, 14)
    c.value_axis.visible = False
    # fix 2: the failure of the selected model on noisy inputs is the talk's biggest caveat, so it gets a tile, not 11 pt
    tile(s, 0.6, 5.35, 6.3, 1.5, f"{cz(nf['selected_axis'], 0)} mm", f"osa, vybraný model, zašuměné vstupy; síť učená se "
         f"šumem {cz(nf['axis'], 2)} mm", BAD, 36)
    cv = j["curve"]
    chart_title(s, 7.2, 1.95, 5.6, "Chyba osy (mm) podle počtu učících výbojů")
    # Real spacing of 6 to 119 discharges on a log axis (deck-fixes 13.4); each label carries the count, because a log axis
    # labels only 5 and 50 (visual QA fix 3)
    cd = XyChartData()
    ser = cd.add_series("osa")
    for n, v in cv:
        ser.add_data_point(n, v)
    gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES, Emu(int(7.1 * IN)), Emu(int(2.4 * IN)), Emu(int(5.8 * IN)),
                            Emu(int(3.6 * IN)), cd)
    c = gf.chart
    c.has_title = False
    c.value_axis.minimum_scale = 0
    style_chart(c, legend=False, size=14)
    log_axis(c.category_axis, 5, 150)
    c.category_axis.has_major_gridlines = False
    c.category_axis.tick_labels.font.size = Pt(1)  # replaced by the counts in the labels
    se = c.plots[0].series[0]
    se.format.line.color.rgb, se.format.line.width, se.smooth = ORANGE, Pt(3), False
    se.marker.format.fill.solid()
    se.marker.format.fill.fore_color.rgb = ORANGE
    se.marker.format.line.color.rgb = ORANGE
    label_points(se, [v for _, v in cv], lambda v: 1 if v >= 5 else 2, TEXT, 13)  # source precision
    for i, (n, _) in enumerate(cv):
        tf = se.points[i].data_label.text_frame
        tf.paragraphs[0].runs[0].text += f" ({n})"
        se.points[i].data_label.position = XL_LABEL_POSITION.BELOW if n == 30 else XL_LABEL_POSITION.ABOVE
    c.value_axis.visible = False
    caption(s, 7.2, 6.05, 5.6, "V závorce počet učících výbojů; logaritmická osa, 60 epoch.")
    notes_extra(s, [
        f"Učeno se šumem, test bez šumu: {cz(j['noisy_on_clean'], 2)} mm.",
        f"Na 30 odložených výbojích: síť učená se šumem, zašuměné vstupy: osa {cz(nf['axis'], 2)} mm, proud "
        f"{cz(nf['current'], 2)} kA.",
        f"Vynechání celé rodiny tvarů: chyba {cz(us['factor'][0], 1)} až {cz(us['factor'][1], 1)}krát větší. Skutečně "
        "neobvyklých výbojů je jen 18 ze 149 a samostatně nikdy vynechány nebyly; tvary mimo rozsah dat jsme neověřili. "
        "Jen jeden tokamak, řízení model sám nenahradí."])
    add_sources(s, ["results/ipp1-robustness-findings.md (šum, počet výbojů)", "results/ipp1-final.md (30 odložených)",
                    "results/ipp1-unusual-shapes.md (neviděné tvary)"])

    # 8 Close: one number (deck-fixes 14, visual QA screen 14)
    s = frame(prs, "Závěr", None, notes_text(sc[8], "Snímek 8") + f"\nK číslu (KQ-7): celý odhad od vstupu po výstup "
              f"medián {cz(e2e['median_ms'], 3)} ms, 99 % pod {cz(e2e['p99_ms'], 2)} ms, procesor {lat['cpu']}.",
              "07-closing.png", 0.45)
    # both speeds in one row: the selected model is the one the talk ships, so it is not the smaller number
    for x, num, words, col in [(0.6, f"{cz(one['median_ms'], 4)} ms", "základní síť", ORANGE),
                               (4.25, shipped_txt[0], "vybraný model, limitované plazma", ORANGE)]:
        text(s, x, 1.55, 3.6, 0.9, num, size=44, color=col, bold=True)
        text(s, x, 2.45, 3.6, 0.7, words, size=18, color=MUTED)
    text(s, 0.6, 3.25, 6.9, 1.2, f"Jeden odhad, procesor {lat['cpu']}. Klasický výpočet trvá minuty; obojí je pod naším "
                                 "rozpočtem 1 až 10 ms.", size=20, color=TEXT)
    for i, (head, body, col) in enumerate([
            ("Přesnost", f"osa {cz(fn['R_mag_axis'][1], 2)} mm; bod u limiteru {cz(fn['R_limiter'][1], 2)} a "
                         f"{cz(fn['Z_limiter'][1], 2)} mm; se šumem osa {cz(nf['axis'], 2)} mm", BLUE),
            ("Zbývá", "bod u limiteru, neobvyklé tvary, šum, napojení na řízení", MUTED)]):
        y = 1.6 + i * 2.15
        box(s, 7.9, y, 4.8, 1.95, fill=PANEL)
        box(s, 7.9, y + 0.2, 0.07, 1.55, fill=col)
        text(s, 8.2, y + 0.2, 4.4, 1.65, [[(head, 22, col, True)], [(body, 18, TEXT, False)]])
    text(s, 0.6, 6.0, 12.1, 0.6, "Na čistých vstupech: desetiny milimetru za setiny milisekundy.", size=24, bold=True,
         align=PP_ALIGN.CENTER)
    text(s, 11.6, 6.6, 1.2, 0.4, "Ilustrace.", size=14, color=TEXT)
    notes_extra(s, [
        f"Přesnost podrobně: čisté vstupy, osa, bod X a dotykové body desetiny milimetru; zašuměné vstupy: bod u limiteru "
        f"{cz(nf['limiter'][0], 1)} a {cz(nf['limiter'][1], 1)} mm, proud {cz(nf['current'], 2)} kA (30 odložených výbojů).",
        "Neobvyklé tvary jsme samostatně neověřili."])
    add_sources(s, ["results/ipp1-latency.json (0,0145 ms, Apple M5)", "results/ipp1-latency-shipped.md (0,027 ms)",
                    "results/ipp1-final.md (přesnost)"])

    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build())
