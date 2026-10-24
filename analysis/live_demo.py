#!/usr/bin/env python
"""Celý nápad projektu živě v terminálu: 24 magnetických měření dovnitř, tvar plazmatu ven.

    HACKATHON_HOME=<složka hackathonu> python analysis/live_demo.py [--epochs 150] [--models 1] [--seconds 10] [--dump-rows N] [--plain]

Co se vypisuje, popořadě (česky, je to ukázka pro porotu):
  0. úvodní rámeček: vstupy, výstupy, síť, rozdělení dat, stroj;
  1. učení sítě epocha po epoše: živý graf ztráty při učení a chyby osy na 30 výbojích, které síť nikdy neviděla
     (logaritmické osy), s uplynulým časem a počtem epoch za sekundu;
  2. chyba všech 16 veličin na těch 30 výbojích jako pruhy vůči rozptylu každé veličiny a podíl okamžiků, ve kterých
     se určení limiterová / divertorová shoduje s rekonstrukcí ústavu;
  3. podíl okamžiků v toleranci: graf podílu okamžiků, jejichž chyba osy R a Z je pod danou tolerancí od 0,01 do 10 mm
     (logaritmicky), dlaždice pro 0,1; 0,5; 1 a 2 mm, pruh shody limiter / divertor a R² každé veličiny;
  4. jeden neviděný výboj okamžik po okamžiku: každý jednořádkový odhad se nejdřív změří v těsné smyčce, potom živý graf
     přehraje referenční a odhadnutou polohu osy R a Z s chybou a dobou každého odhadu, nakonec rozdělení těch dob
     (medián, p99);
  5. plná rychlost: 30 neviděných výbojů znovu a znovu po dávkách, živý ukazatel odhadů za sekundu proti cíli a souhrn;
  6. každý odhad jednoho průchodu plnou rychlostí (--dump-rows 0 to vynechá).

--plain (automaticky, když stdout není terminál) vypisuje totéž bez překreslování a bez barev: tabulky po epochách,
po okamžicích a po sekundách ze starší verze a každý graf jednou.

Stejná data, síť (common.Net) a rozdělení 119/30 jako v projektu (final_evaluation.locked_ids), jedno semínko. Síť je recept
z analysis/clean_model.py (měření dělená proudem plazmatu), jen se tu učí živě, takže její čísla jsou blízká, ne totožná
s results/ipp1-ipn.md a results/bench-mm.md. Nic nezapisuje. Jádro projektu pro čtenáře tohoto souboru:
    common.py   načtení dat, síť, učení s maskou, hodnocení
    final_evaluation.py    nasazený model a odložený test na 30 výbojích
    noisy_model.py  predict.py   nasazený model jako jediný soubor jen s numpy
    run_analyses.py      pouští kroky analýzy ve správném pořadí
"""
import argparse
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import textwrap
import time
import warnings
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I zahazuje složku skriptu
from common import TARGETS, UNIT, Net, load, score
from final_evaluation import locked_ids

# Sloupce výstupů, které demo potřebuje.
R_AXIS, Z_AXIS = TARGETS.index("R_mag_axis"), TARGETS.index("Z_mag_axis")
CURRENT_COL, IS_LIMITED_COL = TARGETS.index("plasma_current"), TARGETS.index("is_limited")
R_LIMITER_COL, Z_LIMITER_COL = TARGETS.index("R_limiter"), TARGETS.index("Z_limiter")

PLOT_MARGIN = 10                  # znaků vlevo od každého grafu: osm znaků popisku, mezera, osa
SPARK_LEVELS = " ▁▂▃▄▅▆▇█"
ANSI_CODE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
HIDE_CURSOR, SHOW_CURSOR = "\033[?25l", "\033[?25h"
LABELS = {  # české názvy 16 výstupů pro porotu
    "plasma_current": "proud plazmatem", "R_mag_axis": "magnetická osa R", "Z_mag_axis": "magnetická osa Z",
    "elongation": "protažení (elongace)", "triangularity": "trojúhelníkovost",
    "triangularity_upper": "trojúhelníkovost horní", "triangularity_lower": "trojúhelníkovost dolní",
    "R_x_point": "bod X R", "Z_x_point": "bod X Z", "R_strike_point_1": "dotykový bod 1 R",
    "Z_strike_point_1": "dotykový bod 1 Z", "R_strike_point_2": "dotykový bod 2 R", "Z_strike_point_2": "dotykový bod 2 Z",
    "R_limiter": "bod u limiteru R", "Z_limiter": "bod u limiteru Z", "is_limited": "limiterová konfigurace",
}


# ===================================================================================================================
# Výpis do terminálu
# ===================================================================================================================
class Style:
    """Barvy v terminálu (ANSI kódy). V prostém režimu je každý kód prázdný řetězec, takže log neobsahuje escape sekvence."""

    # V každé sekci má barva jeden význam: reference, odhad, osa R, osa Z; zelená / žlutá / červená jen pro
    # dobré / ujde / slabé.
    CODES = {"bold": "1", "red": "31", "green": "32", "yellow": "33", "grey": "90",
             "ref": "97", "est": "96", "axis_r": "95", "axis_z": "94"}

    def __init__(self, on):
        for name, code in self.CODES.items():
            setattr(self, name, f"\033[{code}m" if on else "")
        self.end = "\033[0m" if on else ""

    def paint(self, colour, text):
        """Text v dané barvě a potom reset (beze změny, když jsou barvy vypnuté)."""
        return f"{colour}{text}{self.end}" if colour else text


ST = Style(False)   # v main() se nahradí, až víme, jestli stdout je terminál


def visible_len(text):
    """Délka textu tak, jak je vidět na obrazovce, barevné kódy se nepočítají."""
    return len(ANSI_CODE.sub("", text))


def pad(text, width):
    """Text doplněný mezerami na `width` viditelných znaků."""
    return text + " " * max(0, width - visible_len(text))


def fit(text, width):
    """Text oříznutý na `width` viditelných znaků, aniž by se rozbil barevný kód (zalomený řádek by pokazil překreslení)."""
    if visible_len(text) <= width:
        return text
    kept, used = [], 0
    for piece in re.split(r"(\x1b\[[0-9;?]*[A-Za-z])", text):
        if ANSI_CODE.fullmatch(piece):
            kept.append(piece)
            continue
        take = piece[:width - used]
        kept.append(take)
        used += len(take)
        if used >= width:
            break
    return "".join(kept) + ST.end


class LiveBlock:
    """Blok řádků překreslovaný na místě: kurzor se vrátí na první řádek bloku a přepíše všechny řádky.

    Řádky se ořezávají na šířku terminálu a blok na jeho výšku, protože zalomený řádek nebo blok vyšší než obrazovka
    by nechal kurzor jinde, než kde ho čeká další překreslení.
    """

    def __init__(self):
        self.height = 0

    def draw(self, lines):
        size = shutil.get_terminal_size((100, 40))
        lines = [fit(line, size.columns - 1) for line in lines][:max(1, size.lines - 1)]
        output = [f"\r\033[{self.height}A"] if self.height else []
        output += [line + "\033[K\n" for line in lines]
        output.append("\033[J")              # smaže zbytek vyššího předchozího snímku
        sys.stdout.write("".join(output))
        sys.stdout.flush()
        self.height = len(lines)


def terminal_rows(live):
    """Kolik řádků smějí zabrat živé grafy; prostý režim kreslí ve stálé velikosti."""
    return shutil.get_terminal_size((100, 40)).lines if live else 40


def section(number, title, width):
    """Nadpis očíslované sekce na čáře přes celou šířku."""
    heading = f"━━ {number} · {title} "
    print("\n\n" + ST.paint(ST.bold, heading + "━" * max(0, width - len(heading))) + "\n")


def box(title, rows, width, colour=""):
    """Zaoblený rámeček široký `width` znaků s nadpisem v horní hraně; řádky se ořezávají, aby se vešly."""
    inner_width = width - 4
    top = f"╭─ {title} " if title else "╭"
    lines = [ST.paint(colour, top + "─" * (width - 1 - len(top)) + "╮")]
    for row in rows:
        lines.append(ST.paint(colour, "│ ") + pad(fit(row, inner_width), inner_width) + ST.paint(colour, " │"))
    lines.append(ST.paint(colour, "╰" + "─" * (width - 2) + "╯"))
    return lines


def say(text, width):
    """Vytiskne odstavec zalomený na `width` sloupců."""
    print(textwrap.fill(text, width))


def format_int(number):
    """Celé číslo s mezerou jako oddělovačem tisíců."""
    return f"{number:,}".replace(",", " ")


def progress_bar(fraction, width):
    """Ukazatel průběhu široký `width` buněk, vyplněný do podílu `fraction`."""
    filled = int(round(min(max(fraction, 0), 1) * width))
    return "█" * filled + ST.paint(ST.grey, "░" * (width - filled))


def error_bar(error_mm, width=40):
    """Logaritmická stupnice od 0,1 mm (prázdný) do 10 mm (plný); barva říká totéž co číslo: červená nad 2 mm, zelená pod 0,5."""
    filled = int(np.clip((np.log10(max(error_mm, 1e-6)) + 1) / 2 * width, 0, width))
    colour = ST.red if error_mm > 2 else ST.yellow if error_mm > 0.5 else ST.green
    return f"{colour}{error_mm:7.3f} mm {'█' * filled:{width}}{ST.end}"


# ===================================================================================================================
# Grafy z braillových znaků
# ===================================================================================================================
BRAILLE_BIT = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))   # [řádek bodu][sloupec bodu] v jednom znaku


class Canvas:
    """Braillovo plátno: každá buňka znaku má 2 x 4 body a pamatuje si, které řady se do ní kreslily."""

    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.bits = [[0] * cols for _ in range(rows)]
        self.series = [[0] * cols for _ in range(rows)]

    def dot(self, x, y, series):
        """Rozsvítí bod (x, y), počítáno v bodech od levého horního rohu; body mimo plátno se zahodí."""
        if 0 <= x < 2 * self.cols and 0 <= y < 4 * self.rows:
            row, col = y // 4, x // 2
            self.bits[row][col] |= BRAILLE_BIT[y % 4][x % 2]
            self.series[row][col] |= 1 << series

    def line(self, x0, y0, x1, y1, series):
        """Přímka mezi dvěma body, s tolika kroky, aby se žádný bod mezi nimi nevynechal."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for step in range(steps + 1):
            self.dot(round(x0 + (x1 - x0) * step / steps), round(y0 + (y1 - y0) * step / steps), series)

    def text_rows(self, colour_of):
        """Plátno jako řádky textu; colour_of(maska řad) vrátí barvu každé buňky."""
        text_rows = []
        for row in range(self.rows):
            parts, run_colour, run = [], None, ""
            for col in range(self.cols):
                bits = self.bits[row][col]
                colour = colour_of(self.series[row][col]) if bits else ""
                char = chr(0x2800 + bits) if bits else " "
                if colour != run_colour and run:
                    parts.append(ST.paint(run_colour, run))
                    run = ""
                run_colour = colour
                run += char
            parts.append(ST.paint(run_colour, run))
            text_rows.append("".join(parts))
        return text_rows


def decade_range(values):
    """Celé dekády kolem kladných hodnot pro logaritmickou osu (např. 0,3 .. 8,6 dá 0,1 .. 10)."""
    low = 10 ** math.floor(math.log10(min(values)))
    high = 10 ** math.ceil(math.log10(max(values)))
    return (low, high * 10) if high <= low else (low, high)


def padded_range(values, share=0.08):
    """Minimum a maximum hodnot rozšířené na obě strany o `share` rozpětí, pro lineární osu."""
    low, high = float(np.min(values)), float(np.max(values))
    margin = (high - low) * share or 1.0
    return low - margin, high + margin


def axis_ticks(low, high, log):
    """Kulaté hodnoty značek uvnitř [low, high]: dekády na logaritmické ose (a 2x a 5x, když pokrývá jednu dekádu),
    zhruba tři kroky po 1, 2 nebo 5 x 10^k na lineární."""
    if log:
        decades = range(round(math.log10(low)), round(math.log10(high)) + 1)
        multipliers = (1, 2, 5) if len(decades) <= 2 else (1,)
        return [m * 10.0 ** d for d in decades for m in multipliers if low <= m * 10.0 ** d <= high]
    raw_step = (high - low) / 3
    magnitude = 10 ** math.floor(math.log10(raw_step))
    step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= raw_step)
    first = math.ceil(low / step) * step
    return [first + k * step for k in range(int((high - first) / step) + 1)]


def format_tick(value):
    """Hodnota značky nejvýš na 8 znaků."""
    return f"{value:.6g}" if abs(value) >= 1e-3 or value == 0 else f"{value:.0e}"


def plot(series, x_limits, y_limits, cols, rows, log=False, unit="", both=None):
    """Spojnicový graf na braillově plátně s popsanou osou y; vrací `rows` řádků textu o PLOT_MARGIN + cols znacích.

    series: seznam (xs, ys, barva). Buňka, kde se potká víc řad, dostane barvu `both` (výchozí: barva poslední řady).
    Body mimo y_limits se vynechají, takže čára nikdy netvrdí, že hodnota leží na okraji.
    """
    transform = (lambda v: math.log10(v)) if log else (lambda v: v)
    y_low, y_high = transform(y_limits[0]), transform(y_limits[1])
    canvas = Canvas(cols, rows)
    for index, (xs, ys, _) in enumerate(series):
        points = []
        for x_value, y_value in zip(xs, ys):
            if not np.isfinite(y_value) or (log and y_value <= 0) or not (y_limits[0] <= y_value <= y_limits[1]):
                continue
            x_fraction = (x_value - x_limits[0]) / (x_limits[1] - x_limits[0])
            y_fraction = (transform(y_value) - y_low) / (y_high - y_low)
            points.append((round(x_fraction * (2 * cols - 1)), round((1 - y_fraction) * (4 * rows - 1))))
        if len(points) == 1:
            canvas.dot(*points[0], index)
        for start, end in zip(points, points[1:]):
            canvas.line(*start, *end, index)
    colours = [colour for _, _, colour in series]

    def colour_of(mask):
        if mask & (mask - 1):                    # v této buňce je víc řad
            return both if both is not None else colours[mask.bit_length() - 1]
        return colours[mask.bit_length() - 1]

    labels = {}
    for tick in axis_ticks(y_limits[0], y_limits[1], log):
        row = min(rows - 1, int((y_high - transform(tick)) / (y_high - y_low) * rows))
        labels.setdefault(row, (format_tick(tick) + (" " + unit if unit else ""))[:8])
    return [ST.paint(ST.grey, f"{labels.get(row, ''):>8} {'┤' if row in labels else '│'}") + text
            for row, text in enumerate(canvas.text_rows(colour_of))]


def x_axis(cols, ticks):
    """Dva řádky pod grafem: osa se značkami a popisky značek. ticks: seznam (podíl 0..1, popisek)."""
    line, labels = ["─"] * cols, [" "] * cols
    for fraction, text in ticks:
        col = min(cols - 1, round(fraction * (cols - 1)))
        line[col] = "┬"
        start = min(max(col - len(text) // 2, 0), cols - len(text))
        if all(char == " " for char in labels[max(0, start - 1):start + len(text) + 1]):
            labels[start:start + len(text)] = list(text)
    return [ST.paint(ST.grey, " " * (PLOT_MARGIN - 1) + "└" + "".join(line)),
            ST.paint(ST.grey, " " * PLOT_MARGIN + "".join(labels))]


def column_spark(fractions, values, cols, top, colour):
    """Jeden řádek textu zarovnaný s grafem: v každém sloupci největší hodnota, která tam spadá, v osminách `top`.

    Každá hodnota nad nulou je vidět aspoň jako jedna osmina; hodnoty nad `top` jsou plné a červené.
    """
    largest = [None] * cols
    for fraction, value in zip(fractions, values):
        col = min(cols - 1, int(fraction * cols))
        largest[col] = value if largest[col] is None else max(largest[col], value)
    cells = []
    for value in largest:
        if value is None:
            cells.append(" ")
        elif value > top:
            cells.append(ST.paint(ST.red, SPARK_LEVELS[8]))
        else:
            cells.append(ST.paint(colour, SPARK_LEVELS[min(8, max(1, math.ceil(value / top * 8)))]))
    return "".join(cells)


def sparkline(values, top, colour):
    """Hodnoty jako řádek blokových znaků, každá v osminách `top`."""
    return ST.paint(colour, "".join(SPARK_LEVELS[min(8, max(1 if v > 0 else 0, math.ceil(v / top * 8)))] for v in values))


# ===================================================================================================================
# Síť a celý model
# ===================================================================================================================
def axis_error(prediction, truth):
    """Průměrná absolutní chyba magnetické osy v mm (R, Z); osa existuje v každém řádku."""
    return [float(np.abs(prediction[:, column] - truth[:, column]).mean() * 1000) for column in (R_AXIS, Z_AXIS)]


def overall_accuracy(prediction, truth):
    """Celková shoda v %: 100 x (1 - průměr přes výstupy z RMSE vůči rozptylu reference), na řádcích, kde výstup existuje.
    100 % by byla přesná kopie rekonstrukce ústavu."""
    relative_errors = []
    for column in range(truth.shape[1]):
        exists = ~np.isnan(truth[:, column])
        if exists.sum() > 1 and truth[exists, column].std() > 0:
            rmse = np.sqrt(np.mean((prediction[exists, column] - truth[exists, column]) ** 2))
            relative_errors.append(rmse / truth[exists, column].std())
    return 100 * (1 - float(np.mean(relative_errors)))


HUBER_DELTA = 0.2                # delta Huberovy ztráty na standardizovaných cílech (0,2 vyšlo lépe než 0,5 a 1,0 v 5násobném hledání)
CURRENT_SCALE = 1e5              # ampéry: měření se dělí proudem / CURRENT_SCALE
BATCH_ROWS = 512                 # řádků v jednom kroku učení


def add_differences(measurements):
    """24 měření, rozdíly sousedních cívek (15) a smyček (7) a jejich druhé rozdíly (14 + 6): 66 vstupů.
    Je to lineární v měřeních, takže ji první vrstva pohltí přesně (viz Fit.folded)."""
    return np.concatenate([measurements, np.diff(measurements[:, :16], axis=1), np.diff(measurements[:, 16:24], axis=1),
                           np.diff(measurements[:, :16], 2, axis=1), np.diff(measurements[:, 16:24], 2, axis=1)], 1)


DIFFERENCE_MAP = add_differences(np.eye(24))     # 24 x 66: add_differences(x) == x @ DIFFERENCE_MAP
N_DIFFERENCE_FEATURES = DIFFERENCE_MAP.shape[1]


def fit_current_ridge(measurements, targets):
    """Proud plazmatu (A) jako lineární funkce 24 měření: ridge na standardizovaných vstupech přepočtený na koeficienty
    pro surová měření (w, b), proud = x @ w + b. Je přesný zhruba na 0,03 kA a dá se spočítat jen ze vstupů."""
    exists = ~np.isnan(targets[:, CURRENT_COL])
    mean, std = measurements.mean(0), measurements.std(0) + 1e-9
    ridge = Ridge(alpha=1.0).fit((measurements[exists] - mean) / std, targets[exists, CURRENT_COL])
    weights = (ridge.coef_ / std).astype(np.float64)
    return weights, float(ridge.intercept_ - (mean * weights).sum())


class Fit:
    """Jedna natrénovaná síť se svými škálami: surových 24 měření dovnitř, fyzikální jednotky ven.

    Vstupem je 24 měření dělených proudem plazmatu odhadnutým z nich samých (pole je úměrné proudům, takže tvar závisí
    na poměrech, ne na velikosti), jejich rozdíly sousedů a samotný proud."""

    def __init__(self, measurements, targets, ridge, epochs, seed, on_epoch=None, test_measurements=None, test_targets=None):
        """Huberova ztráta s maskou (chybějící cíl nepřispívá), AdamW, plán one-cycle, standardizované vstupy i cíle.
        on_epoch(epocha, ztráta, chyba osy R mm, osy Z mm, sekundy od začátku, celková shoda %) se volá po každé epoše
        s odhady sítě na test_measurements, které se měří, ale nikdy se na nich neučí."""
        torch.manual_seed(seed)
        self.ridge = ridge
        features = self.features(measurements)
        self.input_mean, self.input_std = features.mean(0), features.std(0) + 1e-9
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.target_mean, self.target_std = np.nanmean(targets, 0), np.nanstd(targets, 0) + 1e-9    # každý cíl na stejnou škálu, ať mm a kA váží stejně
        self.target_mean = np.nan_to_num(self.target_mean)
        self.target_std = np.where(np.isnan(self.target_std), 1.0, self.target_std)
        inputs = torch.tensor((features - self.input_mean) / self.input_std)
        standardized_targets = torch.tensor(np.nan_to_num((targets - self.target_mean) / self.target_std).astype(np.float32))
        exists = torch.tensor((~np.isnan(targets)).astype(np.float32))
        self.net = Net(features.shape[1], targets.shape[1])
        optimizer = torch.optim.AdamW(self.net.parameters(), lr=2e-3, weight_decay=1e-4)
        total_steps = epochs * ((len(inputs) + BATCH_ROWS - 1) // BATCH_ROWS)
        scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=3e-3, total_steps=total_steps)
        started = time.perf_counter()
        for epoch in range(1, epochs + 1):
            order = torch.randperm(len(inputs))
            losses = []
            for start in range(0, len(inputs), BATCH_ROWS):
                batch = order[start:start + BATCH_ROWS]
                errors = 2 * torch.nn.functional.huber_loss(self.net(inputs[batch]), standardized_targets[batch],
                                                            reduction="none", delta=HUBER_DELTA)
                loss = (errors * exists[batch]).sum() / exists[batch].sum()
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                scheduler.step()
                losses.append(loss.item())
            if on_epoch:
                prediction = self.slow(test_measurements)
                error_r, error_z = axis_error(prediction, test_targets)
                on_epoch(epoch, float(np.mean(losses)), error_r, error_z, time.perf_counter() - started,
                         overall_accuracy(prediction, test_targets))
        self.net.eval()

    def features(self, measurements):
        """Vstupy sítě: měření dělená proudem, jejich rozdíly a proud."""
        current = (measurements.astype(np.float64) @ self.ridge[0] + self.ridge[1])[:, None]
        return np.concatenate([add_differences(measurements * (CURRENT_SCALE / current)), current / CURRENT_SCALE], 1).astype(np.float32)

    def slow(self, measurements):
        """Samotná síť (torch, float32), podle ní se kontroluje rychlá cesta."""
        with torch.no_grad():
            self.net.eval()
            standardized = (self.features(measurements) - self.input_mean) / self.input_std
            return self.net(torch.from_numpy(standardized)).numpy() * self.target_std + self.target_mean

    def folded(self):
        """Váhy pro surových 24 sloupců vstupu a fyzikální výstupy. S current = x @ w + b je první vrstva
        (x @ Wa) * (CURRENT_SCALE / current) + current * c1 + b0 (mapa rozdílů, standardizace i dělení se skládají
        přesně, protože měření vstupují před dělením lineárně); škálování výstupů jde do poslední vrstvy."""
        linear_layers = [layer for layer in self.net.layers if isinstance(layer, torch.nn.Linear)]
        with torch.no_grad():
            weights = [layer.weight.T.double().clone() for layer in linear_layers]
            biases = [layer.bias.double().clone() for layer in linear_layers]
            std = torch.as_tensor(self.input_std, dtype=torch.float64)
            mean = torch.as_tensor(self.input_mean, dtype=torch.float64)
            target_std = torch.as_tensor(self.target_std, dtype=torch.float64)
            target_mean = torch.as_tensor(self.target_mean, dtype=torch.float64)
            first_layer = weights[0]                      # (N_DIFFERENCE_FEATURES + 1) x šířka: standardizované vstupy, potom proud
            n = N_DIFFERENCE_FEATURES
            weights_a = torch.as_tensor(DIFFERENCE_MAP) @ (first_layer[:n] / std[:n, None])
            current_weights = first_layer[n] / std[n] / CURRENT_SCALE
            first_bias = biases[0] - (mean[:n] / std[:n]) @ first_layer[:n] - (mean[n] / std[n]) * first_layer[n]
            middle = [(weights[k].float().contiguous(), biases[k].float().contiguous()) for k in range(1, len(weights) - 1)]
            last = ((weights[-1] * target_std).float().contiguous(), (biases[-1] * target_std + target_mean).float().contiguous())
        return (weights_a.float().contiguous(), current_weights.float().contiguous(), first_bias.float().contiguous()), middle + [last]


class Model:
    """Celý model: `members` sítí zprůměrovaných (všech 16 výstupů), proud plazmatu z ridge a specialista na limiter,
    který na řádcích, jež hlavní sítě považují za limiterové, odpoví, na které straně nádoby (nahoře nebo dole) bod dotyku
    leží a kde na ní (strana je skok o stovky mm, který obyčejná regrese rozmaže). Bod limiteru je průměr této odpovědi
    a odpovědi hlavních sítí: na vývojové sadě je průměr lepší než kterákoli sama (results/ipp1-ipn.md)."""

    def __init__(self, train_measurements, train_targets, test_measurements, test_targets, epochs, members, view):
        self.n_members, self.params = members, 0
        self.ridge = fit_current_ridge(train_measurements, train_targets)
        self.fits = [Fit(train_measurements, train_targets, self.ridge, epochs, 0, view, test_measurements, test_targets)]
        view.finish()
        self.training_data = (train_measurements, train_targets, epochs)

    def finish_training(self, announce):
        """Dotrénuje zbylé sítě a specialistu na limiter; `announce(text)` ohlašuje jednotlivé kroky."""
        train_measurements, train_targets, epochs = self.training_data
        for seed in range(1, self.n_members):
            announce(f"učí se další síť {seed + 1}/{self.n_members} (průměr sítí)")
            self.fits.append(Fit(train_measurements, train_targets, self.ridge, epochs, seed))
        announce("učí se specialista na bod dotyku limiteru (strana a poloha)")
        is_limited = train_targets[:, IS_LIMITED_COL] > 0.5
        is_up = train_targets[:, Z_LIMITER_COL] > 0
        # Cíle specialisty: strana (+1 nahoře, -1 dole), R a Z nahoře, R a Z dole; co neplatí, zůstane NaN.
        specialist_targets = np.full((len(train_targets), 5), np.nan, np.float32)
        specialist_targets[:, 0] = np.where(is_up, 1.0, -1.0)
        specialist_targets[np.ix_(is_up, [1, 2])] = train_targets[np.ix_(is_up, [R_LIMITER_COL, Z_LIMITER_COL])]
        specialist_targets[np.ix_(~is_up, [3, 4])] = train_targets[np.ix_(~is_up, [R_LIMITER_COL, Z_LIMITER_COL])]
        self.specialist = Fit(train_measurements[is_limited], specialist_targets[is_limited], self.ridge, epochs, 100)
        self.params = sum(p.numel() for fit in self.fits + [self.specialist] for p in fit.net.parameters())

    def current(self, measurements):
        """Proud plazmatu (A) z ridge."""
        return measurements.astype(np.float64) @ self.ridge[0] + self.ridge[1]

    def slow(self, measurements):
        """Odhad všech 16 výstupů samotnými torch sítěmi (referenční cesta)."""
        output = np.mean([fit.slow(measurements) for fit in self.fits], 0)
        output[:, CURRENT_COL] = self.current(measurements)
        limited = output[:, IS_LIMITED_COL] > 0.5
        if limited.any():
            specialist = self.specialist.slow(measurements[limited])
            chosen_side = np.where((specialist[:, 0] > 0)[:, None], specialist[:, 1:3], specialist[:, 3:5])
            limiter_columns = np.ix_(limited, [R_LIMITER_COL, Z_LIMITER_COL])
            output[limiter_columns] = 0.5 * (chosen_side + output[limiter_columns])
        return output

    def predictor(self, chunk=2048):
        """Rychlá cesta: float32, torch.addmm do předem vytvořených vyrovnávacích polí, SiLU na místě, `chunk` řádků
        najednou, na všech vláknech torchu. Váhy i pole mají u jedné sítě pár MB, takže volání zůstane v cache L3."""
        chains = [fit.folded() for fit in self.fits]
        specialist_chain = self.specialist.folded()
        current_weights = torch.from_numpy(self.ridge[0].astype(np.float32))
        current_bias = float(self.ridge[1])

        def make_buffers(chain):
            first, rest = chain
            return [torch.empty(chunk, first[0].shape[1])] + [torch.empty(chunk, weights.shape[1]) for weights, _ in rest]
        buffers, specialist_buffers = [make_buffers(chain) for chain in chains], make_buffers(specialist_chain)

        def run_chain(chain, chain_buffers, rows, current):
            (weights_a, current_weights_in, first_bias), rest = chain
            count = len(rows)
            hidden = chain_buffers[0][:count]
            torch.mm(rows, weights_a, out=hidden)
            hidden.mul_((CURRENT_SCALE / current)[:, None])
            hidden.addcmul_(current[:, None], current_weights_in[None, :])
            hidden.add_(first_bias)
            torch.nn.functional.silu(hidden, inplace=True)
            for k, (weights, bias) in enumerate(rest):
                next_hidden = chain_buffers[k + 1][:count]
                torch.addmm(bias, hidden, weights, out=next_hidden)
                if k < len(rest) - 1:
                    torch.nn.functional.silu(next_hidden, inplace=True)
                hidden = next_hidden
            return hidden

        def predict(measurements):
            measurements = np.ascontiguousarray(measurements, dtype=np.float32)
            result = np.empty((len(measurements), len(TARGETS)), np.float32)
            with torch.inference_mode():
                for start in range(0, len(measurements), chunk):
                    rows = torch.from_numpy(measurements[start:start + chunk])
                    current = torch.mv(rows, current_weights) + current_bias
                    total = run_chain(chains[0], buffers[0], rows, current).clone() if len(chains) > 1 \
                        else run_chain(chains[0], buffers[0], rows, current)
                    for chain, chain_buffers in zip(chains[1:], buffers[1:]):
                        total += run_chain(chain, chain_buffers, rows, current)
                    output = (total / len(chains)).numpy().copy()
                    output[:, CURRENT_COL] = current.numpy()
                    limited = output[:, IS_LIMITED_COL] > 0.5
                    if limited.any():
                        limited_tensor = torch.from_numpy(limited)
                        specialist = run_chain(specialist_chain, specialist_buffers, rows[limited_tensor], current[limited_tensor]).numpy()
                        chosen_side = np.where((specialist[:, 0] > 0)[:, None], specialist[:, 1:3], specialist[:, 3:5])
                        limiter_columns = np.ix_(limited, [R_LIMITER_COL, Z_LIMITER_COL])
                        output[limiter_columns] = 0.5 * (chosen_side + output[limiter_columns])
                    result[start:start + chunk] = output
            return result
        return predict


def cpu_name():
    """Název procesoru, jak ho hlásí systém, nebo typ stroje, když ho systém neřekne."""
    try:
        if sys.platform == "darwin":
            result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=2)
            if result.stdout.strip():
                return result.stdout.strip()
        elif sys.platform.startswith("linux"):
            with open("/proc/cpuinfo") as cpuinfo:
                for line in cpuinfo:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return platform.processor() or platform.machine() or "neznámý"


# ===================================================================================================================
# 0. Úvodní rámeček
# ===================================================================================================================
def banner(width, n_inputs, layer_sizes, params, n_development_discharges, n_development_rows, n_locked_discharges,
           n_locked_rows, cpu):
    """Titulní rámeček: co jde dovnitř, co ven, síť, rozdělení dat, stroj a význam barev."""
    def key(text):
        return ST.paint(ST.bold, f"{text:<8}")

    rows = [
        ST.paint(ST.bold, "TVAR PLAZMATU Z MAGNETICKÝCH MĚŘENÍ") + ST.paint(ST.grey, "   COMPASS · úloha IPP 1 · živě v terminálu"),
        "",
        f"{key('vstup')}{n_inputs} čísel z magnetických měření v jednom okamžiku",
        f"{key('výstup')}{len(TARGETS)} čísel o plazmatu: proud, poloha, tvar, bod X, dotykové body, limiter",
        f"{key('síť')}malá neuronová síť {' → '.join(str(n) for n in layer_sizes)}, {format_int(params)} vah, pevný seed 0",
        f"{key('data')}učí se na {n_development_discharges} výbojích ({format_int(n_development_rows)} okamžiků); na {n_locked_discharges} odložených "
        f"({format_int(n_locked_rows)} okamžiků) se neučí",
        f"{key('chyba')}rozdíl od rekonstrukce ústavu (shoda s ní, ne s plazmatem samotným)",
        f"{key('stroj')}{cpu}",
        f"{key('barvy')}{ST.paint(ST.ref, 'bílá')} = rekonstrukce ústavu, {ST.paint(ST.est, 'tyrkysová')} = odhad sítě",
        f"{key('')}{ST.paint(ST.green, 'zelená')} / {ST.paint(ST.yellow, 'žlutá')} / {ST.paint(ST.red, 'červená')} "
        f"= dobře / ujde / slabě",
    ]
    for line in box("", rows, width, ST.grey):
        print(line)


# ===================================================================================================================
# 1. Učení
# ===================================================================================================================
class LearningView:
    """Učení na obrazovce: živý graf o dvou panelech překreslovaný každou epochu, v prostém režimu řádek tabulky
    za epochu a graf jednou na konci."""

    def __init__(self, epochs, live, width):
        self.epochs, self.live, self.width = epochs, live, width
        self.block = LiveBlock() if live else None
        self.losses, self.errors_r, self.errors_z, self.accuracies, self.elapsed = [], [], [], [], 0.0
        if not live:
            print(f"{'epocha':^6} | {'ztráta učení':^12} | {'chyba osy R na neviděných výbojích':<51} | {'osa Z':^9} | {'shoda':>8} | {'čas':>7}")

    def __call__(self, epoch, loss, error_r, error_z, elapsed, accuracy):
        self.losses.append(loss)
        self.errors_r.append(error_r)
        self.errors_z.append(error_z)
        self.accuracies.append(accuracy)
        self.elapsed = elapsed
        if self.live:
            self.block.draw(self.frame())
        else:
            print(f"{epoch:^6d} | {loss:^12.4f} | {error_bar(error_r)} | {error_z:6.3f} mm | {accuracy:6.2f} % | {elapsed:5.1f} s")

    def finish(self):
        """Prostý režim: graf jednou, po tabulce."""
        if not self.live:
            print()
            for line in self.frame():
                print(line)

    def frame(self):
        """Nadpis, legenda, dva grafy a dva stavové řádky pro dosavadní epochy."""
        cols = (self.width - 3) // 2 - PLOT_MARGIN
        rows = min(10, max(4, terminal_rows(self.live) - 1 - 10))
        n_epochs_done = len(self.losses)
        epochs_so_far = list(range(1, n_epochs_done + 1))
        x_limits = (1, max(2, self.epochs))
        left = plot([(epochs_so_far, self.losses, ST.bold)], x_limits, decade_range(self.losses), cols, rows, log=True)
        right = plot([(epochs_so_far, self.errors_r, ST.axis_r), (epochs_so_far, self.errors_z, ST.axis_z)], x_limits,
                     decade_range(self.errors_r + self.errors_z), cols, rows, log=True, unit="mm")
        ticks = [(0, "1"), (0.5, str(round(1 + (self.epochs - 1) / 2))), (1, f"{self.epochs}")]
        panel_width, gap = PLOT_MARGIN + cols, "   "
        lines = [
            ST.paint(ST.bold, "Jak se síť učí: vlevo ztráta při učení, vpravo chyba polohy osy na 30 odložených výbojích"),
            ST.paint(ST.grey, "U obou grafů nižší je lepší. Svisle logaritmická škála, vodorovně epocha (průchod daty)."),
            "",
            pad(ST.paint(ST.grey, "ztráta (bez jednotky)  ") + ST.paint(ST.bold, "━━ ztráta"), panel_width) + gap
            + ST.paint(ST.grey, "chyba (mm)  ") + ST.paint(ST.axis_r, "━━ osa R purpurová") + "  "
            + ST.paint(ST.axis_z, "━━ osa Z modrá"),
        ]
        lines += [a + gap + b for a, b in zip(left, right)]
        lines += [a + gap + b for a, b in zip(x_axis(cols, ticks), x_axis(cols, ticks))]
        epochs_per_second = n_epochs_done / self.elapsed if self.elapsed > 0 else 0
        lines += [
            "",
            f"epocha {ST.paint(ST.bold, f'{n_epochs_done:>3}/{self.epochs}')}     chyba osy R {ST.paint(ST.bold, f'{self.errors_r[-1]:.3f} mm')}"
            f"     osa Z {ST.paint(ST.bold, f'{self.errors_z[-1]:.3f} mm')}"
            f"     celková shoda {ST.paint(ST.bold, f'{self.accuracies[-1]:.2f} %')}",
            progress_bar(n_epochs_done / self.epochs, 30) + ST.paint(ST.grey, f"  ztráta {self.losses[-1]:.4f} · {self.elapsed:.1f} s · "
                                                                              f"{epochs_per_second:.1f} epoch za sekundu"),
        ]
        return lines


# ===================================================================================================================
# 2. Všechny výstupy
# ===================================================================================================================
def held_out_scores(prediction, truth):
    """Po výstupech na odložených řádcích, kde existují: (název, řádků, průměrná absolutní chyba, směrodatná odchylka
    reference), v jednotkách hlášení (mm, kA, bez jednotky)."""
    scores = []
    for column, name in enumerate(TARGETS):
        exists = ~np.isnan(truth[:, column])
        unit_scale = UNIT[name][0]
        if not exists.any():
            scores.append((name, 0, float("nan"), float("nan")))
            continue
        mean_error = float(np.abs(prediction[exists, column] - truth[exists, column]).mean() * unit_scale)
        spread = float(truth[exists, column].std() * unit_scale)
        scores.append((name, int(exists.sum()), mean_error, spread))
    return scores


def scores_table(prediction, truth, agreement, width):
    """Pruhy chyby všech 16 výstupů na 30 odložených výbojích, každý vůči vlastnímu rozptylu (logaritmicky,
    0,01 % .. 100 %), a shoda limiter / divertor (podíl 0..1)."""
    bar_width, bar_start = 36, 42
    scores = held_out_scores(prediction, truth)
    lines = [ST.paint(ST.bold, f"Chyba všech {len(TARGETS)} veličin na 30 odložených výbojích (nižší je lepší)"),
             ST.paint(ST.grey, "Pruh = chyba vůči rozptylu veličiny, logaritmicky: zelená pod 2 %, žlutá pod 10 %, "
                               "červená nad."),
             "",
             ST.paint(ST.grey, f"{'veličina':<24} {'průměrná chyba':>14}   {'chyba vůči rozptylu veličiny':<{bar_width}}")]
    for name, n_rows, mean_error, spread in scores:
        unit = UNIT[name][1]
        if n_rows == 0:
            lines.append(f"{LABELS[name]:<24} {'—':>10}")
            continue
        percent = 100 * mean_error / spread
        filled = int(np.clip((math.log10(max(percent, 1e-9)) + 2) / 4 * bar_width, 0, bar_width))
        colour = ST.green if percent < 2 else ST.yellow if percent < 10 else ST.red
        head = f"{LABELS[name]:<24} {mean_error:>10.3g} {unit:<3}"
        if name in ("R_mag_axis", "Z_mag_axis"):         # hlavní čísla projektu
            head = ST.paint(ST.bold, head)
        lines.append(f"{head}   {ST.paint(colour, '█' * filled)}{ST.paint(ST.grey, '·' * (bar_width - filled))}"
                     + ST.paint(ST.grey, f" {percent:6.2f} %"))
    scale = [" "] * (bar_width + 6)
    for k, text in enumerate(("0.01", "0.1", "1", "10", "100 %")):       # každý popisek začíná u své značky
        position = round(k * bar_width / 4)
        scale[position:position + len(text)] = list(text)
    lines.append(ST.paint(ST.grey, " " * bar_start + "".join(scale)))
    rows_per_output = {name: n_rows for name, n_rows, _, _ in scores}
    lines += ["", f"Limiterová nebo divertorová konfigurace: shoda s rekonstrukcí ústavu v "
                  f"{ST.paint(ST.bold, f'{100 * agreement:.2f} %')} okamžiků."]
    note = (f"Průměrná chyba = průměrný rozdíl odhadu od rekonstrukce ústavu. Rozptyl veličiny = její směrodatná "
            f"odchylka na týchž okamžicích. Bod X a dotykové body existují jen v divertorové konfiguraci "
            f"({format_int(rows_per_output['R_x_point'])} okamžiků), bod u limiteru jen v limiterové "
            f"({format_int(rows_per_output['R_limiter'])}). Model se učí tady v ukázce (síť s rozdíly cívek, ridge pro proud, specialista na limiter); odeslaný "
            f"model je stejný recept, jeho výsledky jsou v results/ipp1-ipn.md.")
    lines += [ST.paint(ST.grey, row) for row in textwrap.wrap(note, width)]
    return [fit(line, width) for line in lines]


# ===================================================================================================================
# 3. Podíl okamžiků v toleranci
# ===================================================================================================================
TILE_TOLERANCES_MM = (0.1, 0.5, 1, 2)   # tolerance dlaždic; 1 mm je hlavní
SUCCESS_SECONDS = 2.5                   # jak dlouho se v živém demu animuje každá část sekce úspěšnosti


def share_under(errors_mm, tolerances_mm):
    """Procento okamžiků, jejichž chyba je pod každou tolerancí (errors_mm: chyba každého okamžiku, tolerances_mm: pole)."""
    return (np.asarray(errors_mm)[:, None] < np.asarray(tolerances_mm, dtype=float)[None, :]).mean(0) * 100


def ease_out(time_now, start, end):
    """Postup 0..1 kroku animace, který běží od `start` do `end` celkového času, se zpomalením na konci."""
    fraction = min(max((time_now - start) / (end - start), 0.0), 1.0)
    return 1 - (1 - fraction) ** 3


def success_lines(prediction, truth, scores, live, width, reveal=1.0, part="all"):
    """Podíl odložených okamžiků, jejichž chyba osy je pod tolerancí: graf přes 0,01 .. 10 mm (logaritmicky),
    dlaždice pro TILE_TOLERANCES_MM, pruh shody limiter / divertor a R² každého výstupu; scores z common.score.

    part "top" je graf s dlaždicemi, "bottom" pruh shody a pruhy R², "all" obojí. reveal 0..1 je čas animace té části:
    křivky se rozjedou zleva, pak dlaždice, pruh shody a pruhy R² dopočítají své hodnoty; 1 je hotový obraz
    (prostý režim tiskne jen ten)."""
    curve_progress, tile_progress = ease_out(reveal, 0, 0.6), ease_out(reveal, 0.45, 1)
    bottom_progress = ease_out(reveal, 0, 1) if part == "bottom" else 1.0
    errors_mm = {"R": np.abs(prediction[:, R_AXIS] - truth[:, R_AXIS]) * 1000,
                 "Z": np.abs(prediction[:, Z_AXIS] - truth[:, Z_AXIS]) * 1000}
    colour = {"R": ST.axis_r, "Z": ST.axis_z}
    cols = width - PLOT_MARGIN
    rows = min(10, max(5, terminal_rows(live) - 20))
    log_tolerances = np.linspace(-2, 1, 2 * cols)           # jedna tolerance na sloupec braillových bodů
    log_tolerances = log_tolerances[:max(1, int(round(curve_progress * len(log_tolerances))))]
    lines = [ST.paint(ST.bold, "Kolik okamžiků 30 odložených výbojů má chybu polohy osy pod danou tolerancí "
                               "(vyšší je lepší)"),
             ST.paint(ST.grey, "podíl okamžiků (%)  ") + ST.paint(ST.axis_r, "━━ osa R purpurová") + "  "
             + ST.paint(ST.axis_z, "━━ osa Z modrá"),
             ""]
    lines += plot([(log_tolerances, share_under(errors_mm[axis], 10 ** log_tolerances), colour[axis]) for axis in ("R", "Z")],
                  (-2, 1), (0, 100), cols, rows, unit="%")
    lines += x_axis(cols, [(0, "0.01"), (1 / 3, "0.1"), (2 / 3, "1"), (1, "10 mm")])
    lines += [ST.paint(ST.grey, f"{'':>10}vodorovně tolerance chyby osy, logaritmicky; svisle podíl okamžiků "
                                f"s menší chybou"), ""]

    tile_width = (width - 3) // 4
    tile_bar_width = max(3, tile_width - 4 - 10)
    tiles = []
    for tolerance in TILE_TOLERANCES_MM:
        emphasis = ST.bold if tolerance == 1 else ""
        body = []
        for axis in ("R", "Z"):
            percent = float(share_under(errors_mm[axis], [tolerance])[0]) * tile_progress
            body.append(ST.paint(colour[axis], axis + " " + progress_bar(percent / 100, tile_bar_width)) + " "
                        + ST.paint(emphasis, f"{percent:5.1f} %"))
        tiles.append(box(f"pod {tolerance:g} mm", body, tile_width, emphasis or ST.grey))
    lines += [" ".join(parts) for parts in zip(*tiles)]
    top_lines, lines = lines, []

    agreement = scores["is_limited"]["accuracy"]
    known_rows = int((~np.isnan(truth[:, -1])).sum())
    gauge_width = width - 30
    lines += [
              ST.paint(ST.bold, "Limiterová nebo divertorová konfigurace: shoda s rekonstrukcí ústavu"),
              f"{'shoda':<20}{progress_bar(agreement * bottom_progress, gauge_width)} " + ST.paint(ST.bold, f"{100 * agreement * bottom_progress:.2f} %"),
              ST.paint(ST.grey, f"{'':<20}0 %{'100 %':>{gauge_width - 3}}"),
              ST.paint(ST.grey, f"{'':<20}jinak určená konfigurace v {format_int(round((1 - agreement) * known_rows))} "
                                f"z {format_int(known_rows)} okamžiků"),
              "",
              ST.paint(ST.bold, "Koeficient determinace R² každé veličiny (1 = odhad vysvětlí celý rozptyl veličiny)"),
              ST.paint(ST.grey, "Pruh od 0 do 1: zelená od 0.99, žlutá od 0.9, červená pod."), ""]
    column_width = (width - 3) // 2
    r2_bar_width = max(4, column_width - 32)
    cells = []
    for name in TARGETS:
        final_r2 = scores[name]["r2"]
        r2 = final_r2 * bottom_progress
        if not np.isfinite(r2):
            cells.append(f"{LABELS[name]:<24} {'—':>{r2_bar_width + 7}}")
            continue
        tint = ST.green if final_r2 >= 0.99 else ST.yellow if final_r2 >= 0.9 else ST.red
        filled = int(round(min(max(r2, 0), 1) * r2_bar_width))
        cells.append(f"{LABELS[name]:<24} {ST.paint(tint, '█' * filled)}{ST.paint(ST.grey, '·' * (r2_bar_width - filled))} "
                     f"{r2:6.4f}")
    half = (len(cells) + 1) // 2
    lines += [pad(left, column_width) + "   " + right for left, right in zip(cells[:half], cells[half:] + [""])]
    note = ("Chyba = rozdíl odhadu od rekonstrukce ústavu, tedy shoda s ní, ne s plazmatem samotným. Model je ten z "
            "této ukázky; odeslaný model je stejný recept, jeho výsledky jsou v results/ipp1-ipn.md.")
    lines += [""] + [ST.paint(ST.grey, row) for row in textwrap.wrap(note, width)]
    chosen = {"top": top_lines, "bottom": lines, "all": top_lines + [""] + lines}[part]
    return [fit(line, width) for line in chosen]


def show_success(prediction, truth, scores, live, width):
    """Sekce 3 na obrazovce: živě nejdřív graf s dlaždicemi, potom pruhy shody a R², každá část se animuje na místě
    SUCCESS_SECONDS sekund (část vyšší než terminál se vytiskne rovnou); v prostém režimu hotový obraz jednou."""
    for part in ("top", "bottom"):
        final_lines = success_lines(prediction, truth, scores, live, width, part=part)
        if live and len(final_lines) < shutil.get_terminal_size((100, 40)).lines - 1:   # překreslení potřebuje celou část na obrazovce
            block = LiveBlock()
            started = time.perf_counter()
            while (reveal := (time.perf_counter() - started) / SUCCESS_SECONDS) < 1:
                block.draw(success_lines(prediction, truth, scores, live, width, reveal=reveal, part=part))
                time.sleep(1 / 30)
            block.draw(final_lines)
        else:
            for line in final_lines:
                print(line)
        if part == "top":
            print()


# ===================================================================================================================
# 4. Jeden neviděný výboj
# ===================================================================================================================
class DischargeView:
    """Jeden neviděný výboj okamžik po okamžiku: živý graf reference a odhadu osy R a Z, pod ním chyba a doba každého
    odhadu; v prostém režimu řádek tabulky za okamžik a graf jednou."""

    def __init__(self, discharge, times, reference_r, reference_z, live, width):
        self.discharge, self.times, self.live, self.width = discharge, times, live, width
        self.reference_r, self.reference_z = reference_r, reference_z
        self.limits_r, self.limits_z = padded_range(reference_r), padded_range(reference_z)
        self.time_limits = (float(times.min()), float(times.max()) if times.max() > times.min() else float(times.min()) + 1)
        self.estimates_r, self.estimates_z, self.durations_ms = [], [], []
        self.block = LiveBlock() if live else None
        if not live:
            print("čas   | osa R ústav     odhad   chyba | osa Z ústav     odhad   chyba | doba odhadu")

    def add(self, estimate_r, estimate_z, duration_ms):
        """Zaznamená jeden odhad (mm, mm, ms) a ukáže ho."""
        self.estimates_r.append(estimate_r)
        self.estimates_z.append(estimate_z)
        self.durations_ms.append(duration_ms)
        index = len(self.durations_ms) - 1
        if self.live:
            self.block.draw(self.frame())
        else:
            true_r, true_z = self.reference_r[index], self.reference_z[index]
            print(f"{self.times[index]:.3f} | {true_r:9.2f} mm {estimate_r:8.2f} {abs(estimate_r - true_r):5.2f} | "
                  f"{true_z:8.2f} mm {estimate_z:8.2f} {abs(estimate_z - true_z):5.2f} | {duration_ms:6.3f} ms")

    def finish(self):
        """Prostý režim: graf jednou, po tabulce."""
        if not self.live:
            print()
            for line in self.frame():
                print(line)

    def frame(self):
        """Nadpis, legenda, grafy R a Z, řádky chyby a doby a stavový řádek pro dosavadní okamžiky."""
        n_done = len(self.durations_ms)
        cols = self.width - PLOT_MARGIN
        height = min(7, max(3, (terminal_rows(self.live) - 1 - 17) // 2))
        times = self.times[:n_done]
        time_fraction = (times - self.time_limits[0]) / (self.time_limits[1] - self.time_limits[0])
        errors_r = np.abs(np.array(self.estimates_r) - self.reference_r[:n_done])
        errors_z = np.abs(np.array(self.estimates_z) - self.reference_z[:n_done])
        duration_top = float(np.percentile(self.durations_ms, 99))
        lines = [
            ST.paint(ST.bold, f"Výboj {self.discharge}, okamžik po okamžiku: poloha magnetické osy, odhad sítě proti "
                              f"rekonstrukci ústavu"),
            ST.paint(ST.ref, "━━ bílá = rekonstrukce ústavu") + "   " + ST.paint(ST.est, "━━ tyrkysová = odhad sítě")
            + ST.paint(ST.grey, "   (kreslí se navrch a bílou zakryje)"),
            "",
            ST.paint(ST.grey, f"{'':>8}  osa R (mm)"),
        ]
        lines += plot([(times, self.reference_r[:n_done], ST.ref), (times, self.estimates_r, ST.est)], self.time_limits,
                      self.limits_r, cols, height, both=ST.est)
        lines.append(ST.paint(ST.grey, f"{'':>8}  osa Z (mm)"))
        lines += plot([(times, self.reference_z[:n_done], ST.ref), (times, self.estimates_z, ST.est)], self.time_limits,
                      self.limits_z, cols, height, both=ST.est)
        lines += [
            ST.paint(ST.grey, f"{'chyba R':>8} │") + column_spark(time_fraction, errors_r, cols, 1.0, ST.axis_r),
            ST.paint(ST.grey, f"{'chyba Z':>8} │") + column_spark(time_fraction, errors_z, cols, 1.0, ST.axis_z),
            ST.paint(ST.grey, f"{'doba':>8} │") + column_spark(time_fraction, self.durations_ms, cols, duration_top, ""),
        ]
        lines += x_axis(cols, [(0, "0"), (0.25, "0.25"), (0.5, "0.5"), (0.75, "0.75"), (1, "1")])
        lines += [
            ST.paint(ST.grey, f"{'':>10}vodorovně normovaný čas výboje: 0 = začátek, 1 = konec"),
            ST.paint(ST.grey, "chyba R, Z = rozdíl odhadu od ústavu (plná výška 1 mm, nižší je lepší); doba = čas "
                              "jednoho odhadu"),
            ST.paint(ST.grey, f"(plná výška {duration_top:.4f} ms = p99, tj. 99 % odhadů je rychlejších; delší červeně)"),
            "",
            f"okamžik {n_done:>3}/{len(self.times)}     chyba osy R {ST.paint(ST.bold, f'{errors_r[-1]:5.2f} mm')}"
            f"     osa Z {ST.paint(ST.bold, f'{errors_z[-1]:5.2f} mm')}     tento odhad {ST.paint(ST.bold, f'{self.durations_ms[-1]:.4f} ms')}",
            ST.paint(ST.grey, f"ústav R {self.reference_r[n_done - 1]:.2f} mm, síť {self.estimates_r[-1]:.2f} mm · "
                              f"ústav Z {self.reference_z[n_done - 1]:.2f} mm, síť {self.estimates_z[-1]:.2f} mm"),
        ]
        return lines


def latency_lines(durations_ms, width):
    """Rozdělení dob jednoho odhadu: histogram od nejrychlejšího po p99, potom medián, p99, maximum."""
    fastest, p99 = float(np.min(durations_ms)), float(np.percentile(durations_ms, 99))
    n_bins = max(10, min(60, width - 30))
    counts = np.histogram(np.clip(durations_ms, fastest, p99), bins=n_bins, range=(fastest, p99 if p99 > fastest else fastest + 1e-6))[0]
    return [ST.paint(ST.bold, "Jak dlouho trvá jeden odhad (kratší je lepší)"),
            f"{fastest:.4f} ms ▕{sparkline(counts, counts.max(), '')}▏ {p99:.4f} ms",
            ST.paint(ST.grey, "svisle počet odhadů, vodorovně doba od nejkratší po p99 (delší jsou v posledním sloupci)"),
            f"medián {ST.paint(ST.bold, f'{np.median(durations_ms):.4f} ms')}     p99 {ST.paint(ST.bold, f'{p99:.4f} ms')}"
            + ST.paint(ST.grey, "  (p99: 99 % odhadů je rychlejších)"),
            ST.paint(ST.grey, f"nejdelší {np.max(durations_ms):.4f} ms · {len(durations_ms)} odhadů po jednom řádku, včetně Pythonu kolem sítě, "
                              f"tento procesor")]


# ===================================================================================================================
# 5. Plná rychlost
# ===================================================================================================================
def gauge(value, target, top, width):
    """Pruh od 0 do `top` s cílem označeným ┃; zelený, když hodnota cíl dosáhne, jinak žlutý."""
    filled = int(round(min(value, top) / top * width))
    target_cell = min(width - 1, int(round(target / top * width)))
    colour = ST.green if value >= target else ST.yellow
    cells = []
    for cell in range(width):
        if cell == target_cell:
            cells.append(ST.paint(ST.bold, "┃"))
        elif cell < filled:
            cells.append(ST.paint(colour, "█"))
        else:
            cells.append(ST.paint(ST.grey, "░"))
    return "".join(cells), target_cell


class ThroughputView:
    """Běh plnou rychlostí jako ukazatel odhadů za sekundu proti cíli, s historií po sekundách."""

    def __init__(self, target, seconds, width):
        self.target, self.seconds, self.width = target, seconds, width
        self.block = LiveBlock()

    def frame(self, elapsed, total, windows, rate=None):
        """windows: (odhadů, sekund) každého dokončeného okna zhruba po sekundě; rate: aktuální rychlost, je-li známa."""
        if rate is not None:
            pass
        elif windows:
            rate = windows[-1][0] / windows[-1][1]
        else:
            rate = total / elapsed if elapsed > 0 else 0
        window_rates = [count / seconds for count, seconds in windows]
        top = max([1.5 * self.target, rate * 1.1] + [r * 1.1 for r in window_rates])
        gauge_width = self.width - 36
        bar_text, target_cell = gauge(rate, self.target, top, gauge_width)
        scale = [" "] * gauge_width
        target_text = f"cíl {format_int(self.target)}"
        start = min(max(target_cell - len(target_text) // 2, 2), gauge_width - len(target_text))
        scale[0] = "0"
        scale[start:start + len(target_text)] = list(target_text)
        history = "".join(ST.paint(ST.green if r >= self.target else ST.yellow, SPARK_LEVELS[min(8, max(1, math.ceil(r / top * 8)))])
                          for r in window_rates)
        return [
            ST.paint(ST.bold, "Plná rychlost: kolik odhadů za sekundu zvládne tento procesor (vyšší je lepší)"),
            ST.paint(ST.grey, f"Svislá čára ┃ = cíl {format_int(self.target)}. Zelená = cíl splněn, žlutá = pod cílem."),
            "",
            f"{'odhadů za sekundu':<20}{bar_text} {ST.paint(ST.bold, f'{format_int(int(rate)):>11}')}",
            ST.paint(ST.grey, f"{'':<20}{''.join(scale)}"),
            f"{'každá sekunda':<20}{history}" + ST.paint(ST.grey, f"  {len(window_rates)} oken po 1 s"),
            "",
            ST.paint(ST.grey, f"{'průběh':<20}") + progress_bar(elapsed / self.seconds, 30)
            + ST.paint(ST.grey, f"  {elapsed:4.1f} / {self.seconds:.0f} s · odhadů celkem {format_int(total)}"),
        ]

    def draw(self, elapsed, total, windows, rate=None):
        self.block.draw(self.frame(elapsed, total, windows, rate))


# ===================================================================================================================
# Celé demo
# ===================================================================================================================
def run_demo(args, live, width):
    """Všechny sekce popořadě; `width` je počet znaků, které smí využít každý řádek."""
    demo_started = time.perf_counter()
    table, measurements, targets, discharges, _ = load()
    locked = locked_ids(discharges)
    is_locked = np.isin(discharges, locked)
    train_measurements, train_targets = measurements[~is_locked], targets[~is_locked]
    test_measurements, test_targets = measurements[is_locked], targets[is_locked]
    n_development_discharges = len(np.unique(discharges[~is_locked]))
    banner_net = Net(len(add_differences(measurements[:1])[0]) + 1, targets.shape[1])      # jen kvůli úvodnímu rámečku
    linear_layers = [layer for layer in banner_net.layers if isinstance(layer, torch.nn.Linear)]
    layer_sizes = [linear_layers[0].in_features] + [layer.out_features for layer in linear_layers]   # 67: 24 měření dělených proudem, jejich rozdíly, proud
    params = sum(p.numel() for p in banner_net.parameters()) * args.models
    cpu = cpu_name()

    print()
    banner(width, measurements.shape[1], layer_sizes, params, n_development_discharges, len(train_measurements),
           len(locked), len(test_measurements), cpu)

    # 1. Učení.
    section(1, "Síť se učí", width)
    say(f"Učení: {n_development_discharges} výbojů ({format_int(len(train_measurements))} okamžiků). "
        f"Kontrola: {len(locked)} odložených výbojů, na kterých se síť neučí.", width)
    print()
    started = time.perf_counter()
    view = LearningView(args.epochs, live, width)
    model = Model(train_measurements, train_targets, test_measurements, test_targets, args.epochs, args.models, view)
    model.finish_training(lambda text: print(ST.paint(ST.grey, text)))
    params = model.params
    training_seconds = time.perf_counter() - started
    print(f"\nNaučeno za {training_seconds:.0f} s." + ST.paint(ST.grey, f" ({args.epochs / training_seconds:.1f} epoch za sekundu, "
                                                                       f"včetně výpisu na obrazovku)"))

    # 2. Všechny výstupy na odložených výbojích.
    section(2, f"Všech {len(TARGETS)} veličin na {len(locked)} odložených výbojích", width)
    predict = model.predictor()
    torch_prediction = model.slow(test_measurements)
    overall = overall_accuracy(torch_prediction, test_targets)
    scores = score(torch_prediction, test_targets, ~np.isnan(test_targets))      # R² každého výstupu a shoda konfigurace
    agreement = scores["is_limited"]["accuracy"]
    for line in scores_table(torch_prediction, test_targets, agreement, width):
        print(line)
    print()
    fast_path_difference_mm = np.abs(predict(test_measurements) - torch_prediction)[:, [R_AXIS, Z_AXIS]].max() * 1000
    print(ST.paint(ST.grey, textwrap.fill(
        f"Kontrola rychlé cesty (složené váhy, float32): na všech {format_int(len(test_measurements))} neviděných okamžicích se od sítě "
        f"liší nejvýš o {fast_path_difference_mm:.6f} mm.", width)))

    # 3. Podíl odložených okamžiků v toleranci.
    section(3, "Úspěšnost: kolik okamžiků je v toleranci", width)
    say(f"Pro každou toleranci podíl okamžiků {len(locked)} odložených výbojů, ve kterých se poloha osy od "
        f"rekonstrukce ústavu liší méně. Čím dřív křivka dojde ke 100 %, tím lépe.", width)
    print()
    show_success(torch_prediction, test_targets, scores, live, width)
    under_1mm = [float(share_under(np.abs(torch_prediction[:, column] - test_targets[:, column]) * 1000, [1])[0])
                 for column in (R_AXIS, Z_AXIS)]

    # 4. Jeden neviděný výboj okamžik po okamžiku, každý odhad změřený jako jednořádkové volání.
    discharge = int(locked[0])
    rows = np.where(discharges == discharge)[0]
    section(4, f"Výboj {discharge}, na kterém se síť neučila, okamžik po okamžiku", width)
    say(f"Síť dostane výboj {discharge}, na kterém se neučila: {len(rows)} okamžiků, každý jako samostatný odhad z jednoho "
        f"řádku měření. Časy se nejdřív změří v jedné těsné smyčce (kreslení by je zkreslilo), pak se odhady ukážou "
        f"okamžik po okamžiku.", width)
    print()
    single_row_ms, single_row_estimates = [], []
    for row in rows:
        call_started = time.perf_counter()
        estimate = predict(measurements[row:row + 1])[0]
        single_row_ms.append((time.perf_counter() - call_started) * 1000)
        single_row_estimates.append(estimate)
    times = table["time"].values[rows]
    discharge_view = DischargeView(discharge, times, targets[rows, R_AXIS] * 1000, targets[rows, Z_AXIS] * 1000, live, width)
    discharge_errors_r, discharge_errors_z = [], []
    for row, estimate, duration_ms in zip(rows, single_row_estimates, single_row_ms):
        discharge_errors_r.append(abs(estimate[R_AXIS] * 1000 - targets[row, R_AXIS] * 1000))
        discharge_errors_z.append(abs(estimate[Z_AXIS] * 1000 - targets[row, Z_AXIS] * 1000))
        discharge_view.add(estimate[R_AXIS] * 1000, estimate[Z_AXIS] * 1000, duration_ms)
        if live and args.pace > 0:
            time.sleep(args.pace / 1000)      # jen aby místnost stihla přehrávání sledovat
    discharge_view.finish()
    print()
    for line in latency_lines(single_row_ms, width):
        print(fit(line, width))
    print()
    print(f"Výboj {discharge}: průměrná chyba osy R {ST.paint(ST.bold, f'{np.mean(discharge_errors_r):.2f} mm')}, "
          f"osy Z {ST.paint(ST.bold, f'{np.mean(discharge_errors_z):.2f} mm')}.")
    print(ST.paint(ST.grey, f"Medián doby jednoho odhadu {np.median(single_row_ms):.3f} ms."))

    # 5. Plná rychlost: neviděné řádky znovu a znovu po dávkách.
    section(5, "Plná rychlost", width)
    say(f"Všech {len(locked)} odložených výbojů ({format_int(len(test_measurements))} okamžiků) se odhaduje znovu a znovu, po dávkách "
        f"{args.batch} okamžiků, po dobu {args.seconds:.0f} s. Cíl je {format_int(args.target)} odhadů za sekundu.", width)
    print()
    batches = [test_measurements[i:i + args.batch] for i in range(0, len(test_measurements), args.batch)]
    axis_error_r, axis_error_z = axis_error(predict(test_measurements), test_targets)
    throughput_view = ThroughputView(args.target, args.seconds, width)
    if not live:
        print("     čas | odhadů celkem | odhadů za poslední sekundu | chyba osy R")
    total_estimates = 0
    compute_seconds = 0.0                       # sekundy jen uvnitř predict(); kreslení a tisk se nepočítají
    batch_ms, windows = [], []
    window_rows, window_seconds = 0, 0.0
    last_draw = time.perf_counter()
    while compute_seconds < args.seconds:
        for batch in batches:
            batch_started = time.perf_counter()
            predict(batch)
            batch_seconds = time.perf_counter() - batch_started
            batch_ms.append(batch_seconds * 1000)
            compute_seconds += batch_seconds
            total_estimates += len(batch)
            window_rows += len(batch)
            window_seconds += batch_seconds
            if window_seconds >= 1:
                windows.append((window_rows, window_seconds))
                if not live:
                    print(f"{compute_seconds:6.1f} s | {format_int(total_estimates):>13} | {format_int(int(window_rows / window_seconds)):>22}     | {axis_error_r:6.3f} mm")
                window_rows, window_seconds = 0, 0.0
        if live and time.perf_counter() - last_draw >= 1:   # mimo měřenou smyčku
            throughput_view.draw(compute_seconds, total_estimates, windows)
            last_draw = time.perf_counter()
    rate = total_estimates / compute_seconds
    if live:
        throughput_view.draw(compute_seconds, total_estimates, windows)
    else:
        print()
        for line in throughput_view.frame(compute_seconds, total_estimates, windows):
            print(line)
    print()
    print(textwrap.fill(f"Celkem {format_int(int(rate))} odhadů za sekundu ({rate / args.target:.2f}x cíl "
                        f"{format_int(args.target)}) se stejnou vyškolenou sítí; jedna dávka {args.batch} okamžiků trvá "
                        f"asi {np.median(batch_ms):.1f} ms.", width))
    print()
    median_batch_ms = float(np.median(batch_ms))
    summary = [
        f"{'rychlost':<14}" + ST.paint(ST.bold, f"{format_int(int(rate))} odhadů za sekundu")
        + f" = {rate / args.target:.2f}x cíl {format_int(args.target)}",
        f"{'jeden odhad':<14}medián " + ST.paint(ST.bold, f"{np.median(single_row_ms):.4f} ms")
        + f", p99 {np.percentile(single_row_ms, 99):.4f} ms (99 % odhadů je rychlejších)",
        f"{'chyba osy':<14}R " + ST.paint(ST.bold, f"{axis_error_r:.3f} mm") + ", Z " + ST.paint(ST.bold, f"{axis_error_z:.3f} mm")
        + f" vůči rekonstrukci ústavu, {len(locked)} odložených výbojů",
        f"{'shoda celkem':<14}" + ST.paint(ST.bold, f"{overall:.2f} %") + " celkem: 100 % minus průměrná relativní chyba všech 16 veličin",
        f"{'pod 1 mm':<14}R " + ST.paint(ST.bold, f"{under_1mm[0]:.1f} %") + ", Z "
        + ST.paint(ST.bold, f"{under_1mm[1]:.1f} %") + " okamžiků má chybu osy pod 1 mm",
        f"{'konfigurace':<14}limiterová nebo divertorová: shoda s rekonstrukcí ústavu v "
        + ST.paint(ST.bold, f"{100 * agreement:.2f} %") + " okamžiků",
        "",
        ST.paint(ST.grey, f"{'dávka':<14}{args.batch} okamžiků za {median_batch_ms:.1f} ms (medián) = "
                          f"{median_batch_ms / args.batch * 1000:.2f} µs na odhad; {format_int(total_estimates)} odhadů za {compute_seconds:.1f} s"),
        ST.paint(ST.grey, f"{'učení':<14}{args.epochs} epoch za {training_seconds:.1f} s, {format_int(params)} vah, seed 0, "
                          f"hlavní síť + síť pro limiter"),
        ST.paint(ST.grey, f"{'stroj':<14}{cpu} ({platform.machine()}); torch {args.threads} vláken"),
        ST.paint(ST.grey, f"{'software':<14}Python {platform.python_version()}, torch {torch.__version__}, "
                          f"numpy {np.__version__}"),
    ]
    for line in box("Souhrn", summary, width, ST.grey):
        print(line)

    # 6. Každý odhad jednoho průchodu plnou rychlostí, nejdřív změřený a potom vypsaný.
    if args.dump_rows != 0:
        section(6, "Výpis odhadů jednoho průchodu", width)
        dump_rows(table, targets, discharges, is_locked, predict, batches, args)
    print(ST.paint(ST.grey, f"\nCelé demo trvalo {time.perf_counter() - demo_started:.0f} s. Nic se neukládá na disk."))


def dump_rows(table, targets, discharges, is_locked, predict, batches, args):
    """Každý odhad jednoho průchodu plnou rychlostí: nejdřív se změří, potom se vypíše."""
    pass_started = time.perf_counter()
    predictions, microseconds_per_row = [], []
    for batch in batches:
        batch_started = time.perf_counter()
        predictions.append(predict(batch))
        microseconds_per_row.append((time.perf_counter() - batch_started) * 1e6 / len(batch))
    pass_ms = (time.perf_counter() - pass_started) * 1000
    prediction = np.concatenate(predictions)
    n_rows = sum(len(batch) for batch in batches)
    say(f"Každý odhad jednoho průchodu plnou rychlostí: {format_int(n_rows)} odhadů za {pass_ms:.2f} ms "
        f"({format_int(int(n_rows / pass_ms * 1000))} za sekundu). Vypisují se až po změření; "
        f"µs = mikrosekundy na jeden odhad v dávce.", 99)
    print("  odhad | výboj   čas  | osa R ústav     odhad   chyba | osa Z ústav     odhad   chyba | dávka   µs")
    locked_rows = np.where(is_locked)[0]
    n_listed = len(locked_rows) if args.dump_rows < 0 else min(args.dump_rows, len(locked_rows))
    for k in range(n_listed):
        row, estimate = locked_rows[k], prediction[k]
        true_r, true_z = targets[row, R_AXIS] * 1000, targets[row, Z_AXIS] * 1000
        estimate_r, estimate_z = estimate[R_AXIS] * 1000, estimate[Z_AXIS] * 1000
        batch_number = k // args.batch
        print(f"{k + 1:7d} | {discharges[row]:5d}  {table['time'].iloc[row]:.3f} | {true_r:9.2f} mm {estimate_r:8.2f} {abs(estimate_r - true_r):5.2f} | "
              f"{true_z:8.2f} mm {estimate_z:8.2f} {abs(estimate_z - true_z):5.2f} | {batch_number + 1:4d}   {microseconds_per_row[batch_number]:8.3f}")
    print(f"\n{format_int(n_listed)} odhadů vypsáno. Průměrná chyba osy R {axis_error(prediction, targets[is_locked])[0]:.3f} mm.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--models", type=int, default=1, help="networks averaged (slower: each costs one more pass per estimate)")
    parser.add_argument("--seconds", type=float, default=10, help="length of the full-speed run")
    parser.add_argument("--batch", type=int, default=2048, help="rows per estimate call in the full-speed run")
    parser.add_argument("--target", type=int, default=800_000, help="estimates per second the full-speed run is compared with")
    parser.add_argument("--dump-rows", type=int, default=-1, help="rows of the final listing (default all, 0 none)")
    parser.add_argument("--threads", type=int, default=min(6, os.cpu_count() or 1))
    parser.add_argument("--plain", action="store_true",
                        help="no redraw and no colour codes, for logs (automatic when stdout is not a terminal)")
    parser.add_argument("--pace", type=float, default=15,
                        help="ms between instants when the live view replays the unseen discharge (the estimates are timed before)")
    args = parser.parse_args()
    torch.set_num_threads(args.threads)

    global ST
    live = not args.plain and sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"
    ST = Style(live)
    width = min(100, shutil.get_terminal_size((100, 40)).columns) - 1 if live else 99
    if live:
        sys.stdout.write(HIDE_CURSOR)
    try:
        run_demo(args, live, width)
    except KeyboardInterrupt:
        print(ST.end + "\nPřerušeno.")
        sys.exit(130)
    finally:
        if live:
            sys.stdout.write(ST.end + SHOW_CURSOR)
            sys.stdout.flush()


if __name__ == "__main__":
    main()
