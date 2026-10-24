#!/usr/bin/env python
"""The whole idea of the project, live in the terminal: 24 magnetic measurements in, plasma shape out.

    HACKATHON_HOME=<hackathon folder> python analysis/mini_pipeline.py [--epochs 60] [--seconds 10] [--dump-rows N] [--plain]

What it prints, in order (Czech, it is the demo for the jury):
  0. a title banner: inputs, outputs, network, split, machine;
  1. the network learning epoch by epoch: a live two-panel chart of the training loss and of the axis error on the
     30 discharges it never sees (log scales), with elapsed time and epochs per second;
  2. the error of all 16 outputs on those 30 discharges, as bars relative to each output's spread, and the share of
     instants where the limited/diverted call agrees with the institute's reconstruction;
  3. the share of those instants inside a tolerance: a chart of the share whose R and Z axis error is under each
     tolerance from 0.01 to 10 mm (log scale), tiles at 0.1, 0.5, 1 and 2 mm, a bar of the limited/diverted
     agreement and the R² of every output;
  4. one unseen discharge instant by instant: every single-row estimate is timed first in one tight loop, then a live
     chart replays the reference and the estimated R and Z axis position with the error and the time of each estimate,
     then the distribution of those times (median, p99);
  5. full speed: the 30 unseen discharges again and again in batches, a live gauge of estimates per second against
     the target, then a summary box;
  6. every estimate of one full-speed pass (--dump-rows 0 skips it).

--plain (automatic when stdout is not a terminal) prints the same without redrawing and without colour codes: the
per-epoch, per-instant and per-second tables of the earlier version, then each chart once.

Same data, network (ipp1_common.Net) and 119/30 split as the project (ipp1_final.locked_ids), one seed, so the
axis error at the end is the baseline network's number on the locked discharges (results/ipp1-final.md, `base`).
Writes nothing. The core of the project, for the reader of this file:
    ipp1_common.py   data loading, the network, masked training, scoring
    ipp1_final.py    the shipped model and the locked 30-discharge test
    export_model.py  predict.py   the shipped model as one numpy-only file
    make_all.py      runs the analysis steps in dependency order
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
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import TARGETS, UNIT, Net, load, score
from ipp1_final import locked_ids

R, Z = TARGETS.index("R_mag_axis"), TARGETS.index("Z_mag_axis")
AXIS_W = 10                       # characters left of every plot: an 8-character label, a space, the axis line
SPARK = " ▁▂▃▄▅▆▇█"
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
HIDE_CURSOR, SHOW_CURSOR = "\033[?25l", "\033[?25h"
LABELS = {  # Czech names of the 16 outputs, for the jury
    "plasma_current": "proud plazmatem", "R_mag_axis": "magnetická osa R", "Z_mag_axis": "magnetická osa Z",
    "elongation": "protažení (elongace)", "triangularity": "trojúhelníkovost",
    "triangularity_upper": "trojúhelníkovost horní", "triangularity_lower": "trojúhelníkovost dolní",
    "R_x_point": "bod X R", "Z_x_point": "bod X Z", "R_strike_point_1": "dotykový bod 1 R",
    "Z_strike_point_1": "dotykový bod 1 Z", "R_strike_point_2": "dotykový bod 2 R", "Z_strike_point_2": "dotykový bod 2 Z",
    "R_limiter": "bod u limiteru R", "Z_limiter": "bod u limiteru Z", "is_limited": "limiterová konfigurace",
}


# ----------------------------------------------------------------------------- terminal output
class Style:
    """ANSI colour codes; every code is an empty string in plain mode, so a log carries no escape codes."""

    # One meaning per colour in every section: reference, estimate, axis R, axis Z; green / yellow / red only for
    # good / acceptable / weak.
    CODES = {"bold": "1", "red": "31", "green": "32", "yellow": "33", "grey": "90",
             "ref": "97", "est": "96", "axis_r": "95", "axis_z": "94"}

    def __init__(self, on):
        for name, code in self.CODES.items():
            setattr(self, name, f"\033[{code}m" if on else "")
        self.end = "\033[0m" if on else ""

    def paint(self, colour, text):
        """`text` in `colour`, reset afterwards (unchanged when colour is off)."""
        return f"{colour}{text}{self.end}" if colour else text


ST = Style(False)   # replaced in main() once we know whether stdout is a terminal


def visible_len(text):
    """Length of `text` as it appears on screen, colour codes not counted."""
    return len(ANSI.sub("", text))


def pad(text, width):
    """`text` padded with spaces to `width` visible characters."""
    return text + " " * max(0, width - visible_len(text))


def fit(text, width):
    """`text` cut to `width` visible characters without breaking a colour code (a wrapped line would break the redraw)."""
    if visible_len(text) <= width:
        return text
    out, used = [], 0
    for piece in re.split(r"(\x1b\[[0-9;?]*[A-Za-z])", text):
        if ANSI.fullmatch(piece):
            out.append(piece)
            continue
        take = piece[:width - used]
        out.append(take)
        used += len(take)
        if used >= width:
            break
    return "".join(out) + ST.end


class LiveBlock:
    """A block of lines redrawn in place: the cursor goes back to the block's first line and rewrites every line.

    Lines are cut to the terminal width and the block to the terminal height, because a wrapped line or a block
    taller than the screen would leave the cursor somewhere else than where the next redraw expects it.
    """

    def __init__(self):
        self.height = 0

    def draw(self, lines):
        size = shutil.get_terminal_size((100, 40))
        lines = [fit(line, size.columns - 1) for line in lines][:max(1, size.lines - 1)]
        out = [f"\r\033[{self.height}A"] if self.height else []
        out += [line + "\033[K\n" for line in lines]
        out.append("\033[J")              # clears what is left of a taller previous frame
        sys.stdout.write("".join(out))
        sys.stdout.flush()
        self.height = len(lines)


def terminal_rows(live):
    """Rows the live charts may use; plain mode draws at a fixed size."""
    return shutil.get_terminal_size((100, 40)).lines if live else 40


def section(number, title, width):
    """A numbered section heading on a full-width rule."""
    head = f"━━ {number} · {title} "
    print("\n\n" + ST.paint(ST.bold, head + "━" * max(0, width - len(head))) + "\n")


def box(title, rows, width, colour=""):
    """A rounded box of `width` characters with a title in the top border; rows are cut to fit."""
    inner = width - 4
    top = f"╭─ {title} " if title else "╭"
    lines = [ST.paint(colour, top + "─" * (width - 1 - len(top)) + "╮")]
    for row in rows:
        lines.append(ST.paint(colour, "│ ") + pad(fit(row, inner), inner) + ST.paint(colour, " │"))
    lines.append(ST.paint(colour, "╰" + "─" * (width - 2) + "╯"))
    return lines


def say(text, width):
    """Print prose wrapped to `width` columns."""
    print(textwrap.fill(text, width))


def fmt_int(n):
    return f"{n:,}".replace(",", " ")


def progress(fraction, width):
    """A progress bar of `width` cells filled to `fraction`."""
    filled = int(round(min(max(fraction, 0), 1) * width))
    return "█" * filled + ST.paint(ST.grey, "░" * (width - filled))


def bar(err_mm, width=40):
    """Log scale from 0.1 mm (empty) to 10 mm (full); colour says the same as the number: red over 2 mm, green under 0.5."""
    n = int(np.clip((np.log10(max(err_mm, 1e-6)) + 1) / 2 * width, 0, width))
    colour = ST.red if err_mm > 2 else ST.yellow if err_mm > 0.5 else ST.green
    return f"{colour}{err_mm:7.3f} mm {'█' * n:{width}}{ST.end}"


# ----------------------------------------------------------------------------- charts
BRAILLE_BIT = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))   # [dot row][dot column] of one character


class Canvas:
    """Braille canvas: every character cell holds 2 x 4 dots and remembers which series drew in it."""

    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.bits = [[0] * cols for _ in range(rows)]
        self.series = [[0] * cols for _ in range(rows)]

    def dot(self, x, y, series):
        """Set the dot at (x, y), counted in dots from the top left; dots outside the canvas are dropped."""
        if 0 <= x < 2 * self.cols and 0 <= y < 4 * self.rows:
            row, col = y // 4, x // 2
            self.bits[row][col] |= BRAILLE_BIT[y % 4][x % 2]
            self.series[row][col] |= 1 << series

    def line(self, x0, y0, x1, y1, series):
        """A straight line between two dots, with enough steps that no dot in between is skipped."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(steps + 1):
            self.dot(round(x0 + (x1 - x0) * k / steps), round(y0 + (y1 - y0) * k / steps), series)

    def text_rows(self, colour_of):
        """The canvas as text rows; colour_of(series bit mask) gives each cell's colour."""
        rows = []
        for r in range(self.rows):
            parts, run_colour, run = [], None, ""
            for c in range(self.cols):
                bits = self.bits[r][c]
                colour = colour_of(self.series[r][c]) if bits else ""
                char = chr(0x2800 + bits) if bits else " "
                if colour != run_colour and run:
                    parts.append(ST.paint(run_colour, run))
                    run = ""
                run_colour = colour
                run += char
            parts.append(ST.paint(run_colour, run))
            rows.append("".join(parts))
        return rows


def decade_range(values):
    """Whole decades around positive values, for a log axis (e.g. 0.3 .. 8.6 gives 0.1 .. 10)."""
    lo = 10 ** math.floor(math.log10(min(values)))
    hi = 10 ** math.ceil(math.log10(max(values)))
    return (lo, hi * 10) if hi <= lo else (lo, hi)


def padded_range(values, share=0.08):
    """Min and max of `values` widened by `share` of the span on both sides, for a linear axis."""
    lo, hi = float(np.min(values)), float(np.max(values))
    margin = (hi - lo) * share or 1.0
    return lo - margin, hi + margin


def axis_ticks(lo, hi, log):
    """Round tick values inside [lo, hi]: decades on a log axis (plus 2x and 5x when it spans one decade),
    about three steps of 1, 2 or 5 x 10^k on a linear one."""
    if log:
        decades = range(round(math.log10(lo)), round(math.log10(hi)) + 1)
        mults = (1, 2, 5) if len(decades) <= 2 else (1,)
        return [m * 10.0 ** d for d in decades for m in mults if lo <= m * 10.0 ** d <= hi]
    raw = (hi - lo) / 3
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw)
    first = math.ceil(lo / step) * step
    return [first + k * step for k in range(int((hi - first) / step) + 1)]


def fmt_tick(v):
    """A tick value in at most 8 characters."""
    return f"{v:.6g}" if abs(v) >= 1e-3 or v == 0 else f"{v:.0e}"


def plot(series, x_lim, y_lim, cols, rows, log=False, unit="", both=None):
    """A line chart on a braille canvas with a labelled y axis; returns `rows` text lines of AXIS_W + cols characters.

    series: list of (xs, ys, colour). A cell where several series meet gets colour `both` (default: the last series').
    Points outside y_lim are left out, so a line never pretends a value sits on the edge.
    """
    f = (lambda v: math.log10(v)) if log else (lambda v: v)
    y_lo, y_hi = f(y_lim[0]), f(y_lim[1])
    canvas = Canvas(cols, rows)
    for s, (xs, ys, _) in enumerate(series):
        points = []
        for xv, yv in zip(xs, ys):
            if not np.isfinite(yv) or (log and yv <= 0) or not (y_lim[0] <= yv <= y_lim[1]):
                continue
            fx = (xv - x_lim[0]) / (x_lim[1] - x_lim[0])
            fy = (f(yv) - y_lo) / (y_hi - y_lo)
            points.append((round(fx * (2 * cols - 1)), round((1 - fy) * (4 * rows - 1))))
        if len(points) == 1:
            canvas.dot(*points[0], s)
        for p, q in zip(points, points[1:]):
            canvas.line(*p, *q, s)
    colours = [c for _, _, c in series]

    def colour_of(mask):
        if mask & (mask - 1):                    # more than one series in this cell
            return both if both is not None else colours[mask.bit_length() - 1]
        return colours[mask.bit_length() - 1]

    labels = {}
    for t in axis_ticks(y_lim[0], y_lim[1], log):
        row = min(rows - 1, int((y_hi - f(t)) / (y_hi - y_lo) * rows))
        labels.setdefault(row, (fmt_tick(t) + (" " + unit if unit else ""))[:8])
    return [ST.paint(ST.grey, f"{labels.get(r, ''):>8} {'┤' if r in labels else '│'}") + text
            for r, text in enumerate(canvas.text_rows(colour_of))]


def x_axis(cols, ticks):
    """Two lines under a plot: the axis with tick marks, and the tick labels. ticks: list of (fraction 0..1, label)."""
    line, labels = ["─"] * cols, [" "] * cols
    for frac, text in ticks:
        c = min(cols - 1, round(frac * (cols - 1)))
        line[c] = "┬"
        start = min(max(c - len(text) // 2, 0), cols - len(text))
        if all(ch == " " for ch in labels[max(0, start - 1):start + len(text) + 1]):
            labels[start:start + len(text)] = list(text)
    return [ST.paint(ST.grey, " " * (AXIS_W - 1) + "└" + "".join(line)),
            ST.paint(ST.grey, " " * AXIS_W + "".join(labels))]


def column_spark(fractions, values, cols, top, colour):
    """One text row aligned with a plot: in each column the largest value that falls there, in eighths of `top`.

    Any value above zero shows at least one eighth; values above `top` are drawn full and red.
    """
    best = [None] * cols
    for frac, v in zip(fractions, values):
        c = min(cols - 1, int(frac * cols))
        best[c] = v if best[c] is None else max(best[c], v)
    cells = []
    for v in best:
        if v is None:
            cells.append(" ")
        elif v > top:
            cells.append(ST.paint(ST.red, SPARK[8]))
        else:
            cells.append(ST.paint(colour, SPARK[min(8, max(1, math.ceil(v / top * 8)))]))
    return "".join(cells)


def sparkline(values, top, colour):
    """Values as a row of block characters, each in eighths of `top`."""
    return ST.paint(colour, "".join(SPARK[min(8, max(1 if v > 0 else 0, math.ceil(v / top * 8)))] for v in values))


# ----------------------------------------------------------------------------- the network
def axis_error(pred, y):
    """Mean absolute error of the magnetic axis in mm (R, Z); the axis exists in every row."""
    return [float(np.abs(pred[:, j] - y[:, j]).mean() * 1000) for j in (R, Z)]


def train(x, y, x_test, y_test, epochs, on_epoch, seed=0):
    """The masked training of ipp1_common.fit_mlp, with the test error measured after every epoch.

    on_epoch(epoch, mean training loss, axis R error mm, axis Z error mm, seconds so far) shows it.
    Returns the trained net and the input/target scalers; the test rows are only measured, never trained on.
    """
    torch.manual_seed(seed)
    mu, sd = x.mean(0), x.std(0) + 1e-9
    ym, ys = np.nanmean(y, 0), np.nanstd(y, 0) + 1e-9     # scale each target so mm and kA weigh alike
    xt, xv = torch.tensor((x - mu) / sd), torch.tensor((x_test - mu) / sd)
    yt = torch.tensor(np.nan_to_num((y - ym) / ys))
    exists = torch.tensor((~np.isnan(y)).astype(np.float32))   # 1 where the target exists in that row
    net = Net(x.shape[1], y.shape[1])
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    steps = epochs * ((len(xt) + 511) // 512)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=steps)
    started = time.perf_counter()
    for epoch in range(1, epochs + 1):
        order = torch.randperm(len(xt))
        losses = []
        for i in range(0, len(xt), 512):
            b = order[i:i + 512]
            # Masked squared error: a missing target contributes nothing instead of a bogus error.
            loss = ((net(xt[b]) - yt[b]) ** 2 * exists[b]).sum() / exists[b].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            losses.append(loss.item())
        with torch.no_grad():
            err_r, err_z = axis_error(net(xv).numpy() * ys + ym, y_test)
        on_epoch(epoch, float(np.mean(losses)), err_r, err_z, time.perf_counter() - started)
    net.eval()
    return net, (mu, sd, ym, ys)


def fast_predictor(net, scalers, chunk=2048):
    """The trained network as a fast pass: raw inputs in, physical units out, no autograd, same numbers.

    As in the earlier live-training script: the input standardisation is folded into the first layer and the output scaling into
    the last one (exact algebra), float32, torch.addmm into preallocated buffers and SiLU in place, `chunk` rows at a time.
    Weights plus the buffers are about 6 MB, so a call stays inside the L3 cache and runs on all torch threads.
    """
    mu, sd, ym, ys = (torch.as_tensor(np.asarray(a), dtype=torch.float64) for a in scalers)
    lin = [m for m in net.f if isinstance(m, torch.nn.Linear)]
    with torch.no_grad():
        w = [m.weight.T.double().clone() for m in lin]
        b = [m.bias.double().clone() for m in lin]
        b[0] = b[0] - (mu / sd) @ w[0]
        w[0] = w[0] / sd[:, None]
        w[-1], b[-1] = w[-1] * ys, b[-1] * ys + ym
    fw = [x.float().contiguous() for x in w]
    fb = [x.float().contiguous() for x in b]
    bufs = [torch.empty(chunk, x.shape[1]) for x in fw]

    def predict(rows):
        rows = torch.as_tensor(np.ascontiguousarray(rows, dtype=np.float32))
        out = np.empty((len(rows), fw[-1].shape[1]), np.float32)
        with torch.inference_mode():
            for s in range(0, len(rows), chunk):
                h = rows[s:s + chunk]
                m = len(h)
                for k in range(len(fw)):
                    o = bufs[k][:m]
                    torch.addmm(fb[k], h, fw[k], out=o)
                    if k < len(fw) - 1:
                        torch.nn.functional.silu(o, inplace=True)
                    h = o
                out[s:s + m] = h.numpy()
        return out
    return predict


# ----------------------------------------------------------------------------- the machine
def cpu_name():
    """Processor name as the operating system reports it, or the machine type when it does not say."""
    try:
        if sys.platform == "darwin":
            out = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=2)
            if out.stdout.strip():
                return out.stdout.strip()
        elif sys.platform.startswith("linux"):
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return platform.processor() or platform.machine() or "neznámý"


# ----------------------------------------------------------------------------- 0. banner
def banner(width, n_in, layer_sizes, params, dev_ids, dev_rows, lock, lock_rows, cpu):
    """The title box: what goes in, what comes out, the network, the split, the machine, the colours."""
    def key(text):
        return ST.paint(ST.bold, f"{text:<8}")

    rows = [
        ST.paint(ST.bold, "TVAR PLAZMATU Z MAGNETICKÝCH MĚŘENÍ") + ST.paint(ST.grey, "   COMPASS · úloha IPP 1 · živě v terminálu"),
        "",
        f"{key('vstup')}{n_in} čísel z magnetických měření v jednom okamžiku",
        f"{key('výstup')}{len(TARGETS)} čísel o plazmatu: proud, poloha, tvar, bod X, dotykové body, limiter",
        f"{key('síť')}malá neuronová síť {' → '.join(str(n) for n in layer_sizes)}, {fmt_int(params)} vah, pevný seed 0",
        f"{key('data')}učí se na {dev_ids} výbojích ({fmt_int(dev_rows)} okamžiků); na {lock} odložených "
        f"({fmt_int(lock_rows)} okamžiků) se neučí",
        f"{key('chyba')}rozdíl od rekonstrukce ústavu (shoda s ní, ne s plazmatem samotným)",
        f"{key('stroj')}{cpu}",
        f"{key('barvy')}{ST.paint(ST.ref, 'bílá')} = rekonstrukce ústavu, {ST.paint(ST.est, 'tyrkysová')} = odhad sítě",
        f"{key('')}{ST.paint(ST.green, 'zelená')} / {ST.paint(ST.yellow, 'žlutá')} / {ST.paint(ST.red, 'červená')} "
        f"= dobře / ujde / slabě",
    ]
    for line in box("", rows, width, ST.grey):
        print(line)


# ----------------------------------------------------------------------------- 1. learning
class LearningView:
    """The learning on screen: a live two-panel chart redrawn every epoch, or in plain mode a table line per epoch
    and the chart once at the end."""

    def __init__(self, epochs, live, width):
        self.epochs, self.live, self.width = epochs, live, width
        self.block = LiveBlock() if live else None
        self.loss, self.err_r, self.err_z, self.elapsed = [], [], [], 0.0
        if not live:
            print(f"{'epocha':^6} | {'ztráta učení':^12} | {'chyba osy R na neviděných výbojích':<51} | {'osa Z':^9} | {'čas':>7}")

    def __call__(self, epoch, loss, err_r, err_z, elapsed):
        self.loss.append(loss)
        self.err_r.append(err_r)
        self.err_z.append(err_z)
        self.elapsed = elapsed
        if self.live:
            self.block.draw(self.frame())
        else:
            print(f"{epoch:^6d} | {loss:^12.4f} | {bar(err_r)} | {err_z:6.3f} mm | {elapsed:5.1f} s")

    def finish(self):
        """Plain mode: the chart once, after the table."""
        if not self.live:
            print()
            for line in self.frame():
                print(line)

    def frame(self):
        """Title, legend, the two charts and two status lines for the epochs so far."""
        cols = (self.width - 3) // 2 - AXIS_W
        rows = min(10, max(4, terminal_rows(self.live) - 1 - 10))
        n = len(self.loss)
        xs = list(range(1, n + 1))
        x_lim = (1, max(2, self.epochs))
        left = plot([(xs, self.loss, ST.bold)], x_lim, decade_range(self.loss), cols, rows, log=True)
        right = plot([(xs, self.err_r, ST.axis_r), (xs, self.err_z, ST.axis_z)], x_lim,
                     decade_range(self.err_r + self.err_z), cols, rows, log=True, unit="mm")
        ticks = [(0, "1"), (0.5, str(round(1 + (self.epochs - 1) / 2))), (1, f"{self.epochs}")]
        panel_w, gap = AXIS_W + cols, "   "
        lines = [
            ST.paint(ST.bold, "Jak se síť učí: vlevo ztráta při učení, vpravo chyba polohy osy na 30 odložených výbojích"),
            ST.paint(ST.grey, "U obou grafů nižší je lepší. Svisle logaritmická škála, vodorovně epocha (průchod daty)."),
            "",
            pad(ST.paint(ST.grey, "ztráta (bez jednotky)  ") + ST.paint(ST.bold, "━━ ztráta"), panel_w) + gap
            + ST.paint(ST.grey, "chyba (mm)  ") + ST.paint(ST.axis_r, "━━ osa R purpurová") + "  "
            + ST.paint(ST.axis_z, "━━ osa Z modrá"),
        ]
        lines += [a + gap + b for a, b in zip(left, right)]
        lines += [a + gap + b for a, b in zip(x_axis(cols, ticks), x_axis(cols, ticks))]
        rate = n / self.elapsed if self.elapsed > 0 else 0
        lines += [
            "",
            f"epocha {ST.paint(ST.bold, f'{n:>3}/{self.epochs}')}     chyba osy R {ST.paint(ST.bold, f'{self.err_r[-1]:.3f} mm')}"
            f"     osa Z {ST.paint(ST.bold, f'{self.err_z[-1]:.3f} mm')}",
            progress(n / self.epochs, 30) + ST.paint(ST.grey, f"  ztráta {self.loss[-1]:.4f} · {self.elapsed:.1f} s · "
                                                              f"{rate:.1f} epoch za sekundu"),
        ]
        return lines


# ----------------------------------------------------------------------------- 2. all outputs
def held_out_scores(pred, y):
    """Per output on the set-aside rows where it exists: (name, rows, mean absolute error, std of the reference), in
    report units (mm, kA, none)."""
    scores = []
    for j, name in enumerate(TARGETS):
        exists = ~np.isnan(y[:, j])
        scale = UNIT[name][0]
        if not exists.any():
            scores.append((name, 0, float("nan"), float("nan")))
            continue
        mae = float(np.abs(pred[exists, j] - y[exists, j]).mean() * scale)
        spread = float(y[exists, j].std() * scale)
        scores.append((name, int(exists.sum()), mae, spread))
    return scores


def scores_table(pred, y, agree, width):
    """Bars of the error of all 16 outputs on the 30 set-aside discharges, each relative to its own spread
    (log scale, 0.01 % .. 100 %), and the limited/diverted agreement (a share 0..1)."""
    bar_w, bar_at = 36, 42
    scores = held_out_scores(pred, y)
    lines = [ST.paint(ST.bold, f"Chyba všech {len(TARGETS)} veličin na 30 odložených výbojích (nižší je lepší)"),
             ST.paint(ST.grey, "Pruh = chyba vůči rozptylu veličiny, logaritmicky: zelená pod 2 %, žlutá pod 10 %, "
                               "červená nad."),
             "",
             ST.paint(ST.grey, f"{'veličina':<24} {'průměrná chyba':>14}   {'chyba vůči rozptylu veličiny':<{bar_w}}")]
    for name, n, mae, spread in scores:
        unit = UNIT[name][1]
        if n == 0:
            lines.append(f"{LABELS[name]:<24} {'—':>10}")
            continue
        pct = 100 * mae / spread
        filled = int(np.clip((math.log10(max(pct, 1e-9)) + 2) / 4 * bar_w, 0, bar_w))
        colour = ST.green if pct < 2 else ST.yellow if pct < 10 else ST.red
        head = f"{LABELS[name]:<24} {mae:>10.3g} {unit:<3}"
        if name in ("R_mag_axis", "Z_mag_axis"):         # the headline numbers of the project
            head = ST.paint(ST.bold, head)
        lines.append(f"{head}   {ST.paint(colour, '█' * filled)}{ST.paint(ST.grey, '·' * (bar_w - filled))}"
                     + ST.paint(ST.grey, f" {pct:6.2f} %"))
    scale = [" "] * (bar_w + 6)
    for k, text in enumerate(("0.01", "0.1", "1", "10", "100 %")):       # each label starts at its tick
        pos = round(k * bar_w / 4)
        scale[pos:pos + len(text)] = list(text)
    lines.append(ST.paint(ST.grey, " " * bar_at + "".join(scale)))
    rows_of = {name: n for name, n, _, _ in scores}
    lines += ["", f"Limiterová nebo divertorová konfigurace: shoda s rekonstrukcí ústavu v "
                  f"{ST.paint(ST.bold, f'{100 * agree:.2f} %')} okamžiků."]
    note = (f"Průměrná chyba = průměrný rozdíl odhadu od rekonstrukce ústavu. Rozptyl veličiny = její směrodatná "
            f"odchylka na týchž okamžicích. Bod X a dotykové body existují jen v divertorové konfiguraci "
            f"({fmt_int(rows_of['R_x_point'])} okamžiků), bod u limiteru jen v limiterové "
            f"({fmt_int(rows_of['R_limiter'])}). Je to základní síť (60 epoch), ne vybraný model; ten má vlastní "
            f"výsledky v results/ipp1-final.md.")
    lines += [ST.paint(ST.grey, row) for row in textwrap.wrap(note, width)]
    return [fit(line, width) for line in lines]


# ----------------------------------------------------------------------------- 3. share inside a tolerance
TILE_MM = (0.1, 0.5, 1, 2)          # the tolerances of the tiles; 1 mm is the headline one


def share_under(err_mm, tol_mm):
    """Percent of instants whose error is below each tolerance (err_mm: one error per instant, tol_mm: array)."""
    return (np.asarray(err_mm)[:, None] < np.asarray(tol_mm, dtype=float)[None, :]).mean(0) * 100


def success_lines(pred, y, scores, live, width):
    """The share of set-aside instants whose axis error is under a tolerance: a chart over 0.01 .. 10 mm (log),
    tiles at TILE_MM, a bar of the limited/diverted agreement, and the R² of every output; scores from ipp1_common.score."""
    err = {"R": np.abs(pred[:, R] - y[:, R]) * 1000, "Z": np.abs(pred[:, Z] - y[:, Z]) * 1000}
    colour = {"R": ST.axis_r, "Z": ST.axis_z}
    cols = width - AXIS_W
    rows = min(10, max(5, terminal_rows(live) - 20))
    log_tol = np.linspace(-2, 1, 2 * cols)           # one tolerance per braille dot column
    lines = [ST.paint(ST.bold, "Kolik okamžiků 30 odložených výbojů má chybu polohy osy pod danou tolerancí "
                               "(vyšší je lepší)"),
             ST.paint(ST.grey, "podíl okamžiků (%)  ") + ST.paint(ST.axis_r, "━━ osa R purpurová") + "  "
             + ST.paint(ST.axis_z, "━━ osa Z modrá"),
             ""]
    lines += plot([(log_tol, share_under(err[a], 10 ** log_tol), colour[a]) for a in ("R", "Z")],
                  (-2, 1), (0, 100), cols, rows, unit="%")
    lines += x_axis(cols, [(0, "0.01"), (1 / 3, "0.1"), (2 / 3, "1"), (1, "10 mm")])
    lines += [ST.paint(ST.grey, f"{'':>10}vodorovně tolerance chyby osy, logaritmicky; svisle podíl okamžiků "
                                f"s menší chybou"), ""]

    tile_w = (width - 3) // 4
    bar_w = max(3, tile_w - 4 - 10)
    tiles = []
    for tol in TILE_MM:
        strong = ST.bold if tol == 1 else ""
        body = []
        for a in ("R", "Z"):
            pct = float(share_under(err[a], [tol])[0])
            body.append(ST.paint(colour[a], a + " " + progress(pct / 100, bar_w)) + " "
                        + ST.paint(strong, f"{pct:5.1f} %"))
        tiles.append(box(f"pod {tol:g} mm", body, tile_w, strong or ST.grey))
    lines += [" ".join(parts) for parts in zip(*tiles)]

    agree = scores["is_limited"]["accuracy"]
    known = int((~np.isnan(y[:, -1])).sum())
    gauge_w = width - 30
    lines += ["",
              ST.paint(ST.bold, "Limiterová nebo divertorová konfigurace: shoda s rekonstrukcí ústavu"),
              f"{'shoda':<20}{progress(agree, gauge_w)} " + ST.paint(ST.bold, f"{100 * agree:.2f} %"),
              ST.paint(ST.grey, f"{'':<20}0 %{'100 %':>{gauge_w - 3}}"),
              ST.paint(ST.grey, f"{'':<20}jinak určená konfigurace v {fmt_int(round((1 - agree) * known))} "
                                f"z {fmt_int(known)} okamžiků"),
              "",
              ST.paint(ST.bold, "Koeficient determinace R² každé veličiny (1 = odhad vysvětlí celý rozptyl veličiny)"),
              ST.paint(ST.grey, "Pruh od 0 do 1: zelená od 0.99, žlutá od 0.9, červená pod."), ""]
    col_w = (width - 3) // 2
    r2_bar = max(4, col_w - 32)
    cells = []
    for name in TARGETS:
        r2 = scores[name]["r2"]
        if not np.isfinite(r2):
            cells.append(f"{LABELS[name]:<24} {'—':>{r2_bar + 7}}")
            continue
        tint = ST.green if r2 >= 0.99 else ST.yellow if r2 >= 0.9 else ST.red
        filled = int(round(min(max(r2, 0), 1) * r2_bar))
        cells.append(f"{LABELS[name]:<24} {ST.paint(tint, '█' * filled)}{ST.paint(ST.grey, '·' * (r2_bar - filled))} "
                     f"{r2:6.4f}")
    half = (len(cells) + 1) // 2
    lines += [pad(left, col_w) + "   " + right for left, right in zip(cells[:half], cells[half:] + [""])]
    note = ("Chyba = rozdíl odhadu od rekonstrukce ústavu, tedy shoda s ní, ne s plazmatem samotným. Je to základní "
            "síť z této ukázky, ne vybraný model; ten má vlastní výsledky v results/ipp1-final.md.")
    lines += [""] + [ST.paint(ST.grey, row) for row in textwrap.wrap(note, width)]
    return [fit(line, width) for line in lines]


# ----------------------------------------------------------------------------- 4. one unseen discharge
class DischargeView:
    """One unseen discharge instant by instant: a live chart of reference and estimate for the R and Z axis,
    the error and the time of each estimate under it; in plain mode a table line per instant and the chart once."""

    def __init__(self, disc, times, ref_r, ref_z, live, width):
        self.disc, self.times, self.live, self.width = disc, times, live, width
        self.ref_r, self.ref_z = ref_r, ref_z
        self.lim_r, self.lim_z = padded_range(ref_r), padded_range(ref_z)
        self.t_lim = (float(times.min()), float(times.max()) if times.max() > times.min() else float(times.min()) + 1)
        self.est_r, self.est_z, self.ms = [], [], []
        self.block = LiveBlock() if live else None
        if not live:
            print("čas   | osa R ústav     odhad   chyba | osa Z ústav     odhad   chyba | doba odhadu")

    def add(self, est_r, est_z, ms):
        """Record one estimate (mm, mm, ms) and show it."""
        self.est_r.append(est_r)
        self.est_z.append(est_z)
        self.ms.append(ms)
        k = len(self.ms) - 1
        if self.live:
            self.block.draw(self.frame())
        else:
            tr_r, tr_z = self.ref_r[k], self.ref_z[k]
            print(f"{self.times[k]:.3f} | {tr_r:9.2f} mm {est_r:8.2f} {abs(est_r - tr_r):5.2f} | "
                  f"{tr_z:8.2f} mm {est_z:8.2f} {abs(est_z - tr_z):5.2f} | {ms:6.3f} ms")

    def finish(self):
        """Plain mode: the chart once, after the table."""
        if not self.live:
            print()
            for line in self.frame():
                print(line)

    def frame(self):
        """Title, legend, the R and Z charts, error and time rows, status line for the instants so far."""
        n = len(self.ms)
        cols = self.width - AXIS_W
        height = min(7, max(3, (terminal_rows(self.live) - 1 - 17) // 2))
        t = self.times[:n]
        frac = (t - self.t_lim[0]) / (self.t_lim[1] - self.t_lim[0])
        err_r = np.abs(np.array(self.est_r) - self.ref_r[:n])
        err_z = np.abs(np.array(self.est_z) - self.ref_z[:n])
        ms_top = float(np.percentile(self.ms, 99))
        lines = [
            ST.paint(ST.bold, f"Výboj {self.disc}, okamžik po okamžiku: poloha magnetické osy, odhad sítě proti "
                              f"rekonstrukci ústavu"),
            ST.paint(ST.ref, "━━ bílá = rekonstrukce ústavu") + "   " + ST.paint(ST.est, "━━ tyrkysová = odhad sítě")
            + ST.paint(ST.grey, "   (kreslí se navrch a bílou zakryje)"),
            "",
            ST.paint(ST.grey, f"{'':>8}  osa R (mm)"),
        ]
        lines += plot([(t, self.ref_r[:n], ST.ref), (t, self.est_r, ST.est)], self.t_lim, self.lim_r, cols, height,
                      both=ST.est)
        lines.append(ST.paint(ST.grey, f"{'':>8}  osa Z (mm)"))
        lines += plot([(t, self.ref_z[:n], ST.ref), (t, self.est_z, ST.est)], self.t_lim, self.lim_z, cols, height,
                      both=ST.est)
        lines += [
            ST.paint(ST.grey, f"{'chyba R':>8} │") + column_spark(frac, err_r, cols, 1.0, ST.axis_r),
            ST.paint(ST.grey, f"{'chyba Z':>8} │") + column_spark(frac, err_z, cols, 1.0, ST.axis_z),
            ST.paint(ST.grey, f"{'doba':>8} │") + column_spark(frac, self.ms, cols, ms_top, ""),
        ]
        lines += x_axis(cols, [(0, "0"), (0.25, "0.25"), (0.5, "0.5"), (0.75, "0.75"), (1, "1")])
        lines += [
            ST.paint(ST.grey, f"{'':>10}vodorovně normovaný čas výboje: 0 = začátek, 1 = konec"),
            ST.paint(ST.grey, "chyba R, Z = rozdíl odhadu od ústavu (plná výška 1 mm, nižší je lepší); doba = čas "
                              "jednoho odhadu"),
            ST.paint(ST.grey, f"(plná výška {ms_top:.4f} ms = p99, tj. 99 % odhadů je rychlejších; delší červeně)"),
            "",
            f"okamžik {n:>3}/{len(self.times)}     chyba osy R {ST.paint(ST.bold, f'{err_r[-1]:5.2f} mm')}"
            f"     osa Z {ST.paint(ST.bold, f'{err_z[-1]:5.2f} mm')}     tento odhad {ST.paint(ST.bold, f'{self.ms[-1]:.4f} ms')}",
            ST.paint(ST.grey, f"ústav R {self.ref_r[n - 1]:.2f} mm, síť {self.est_r[-1]:.2f} mm · "
                              f"ústav Z {self.ref_z[n - 1]:.2f} mm, síť {self.est_z[-1]:.2f} mm"),
        ]
        return lines


def latency_lines(ms, width):
    """Distribution of the single-estimate times: a histogram from the fastest to p99, then median, p99, max."""
    lo, p99 = float(np.min(ms)), float(np.percentile(ms, 99))
    bins = max(10, min(60, width - 30))
    counts = np.histogram(np.clip(ms, lo, p99), bins=bins, range=(lo, p99 if p99 > lo else lo + 1e-6))[0]
    return [ST.paint(ST.bold, "Jak dlouho trvá jeden odhad (kratší je lepší)"),
            f"{lo:.4f} ms ▕{sparkline(counts, counts.max(), '')}▏ {p99:.4f} ms",
            ST.paint(ST.grey, "svisle počet odhadů, vodorovně doba od nejkratší po p99 (delší jsou v posledním sloupci)"),
            f"medián {ST.paint(ST.bold, f'{np.median(ms):.4f} ms')}     p99 {ST.paint(ST.bold, f'{p99:.4f} ms')}"
            + ST.paint(ST.grey, "  (p99: 99 % odhadů je rychlejších)"),
            ST.paint(ST.grey, f"nejdelší {np.max(ms):.4f} ms · {len(ms)} odhadů po jednom řádku, včetně Pythonu kolem sítě, "
                              f"tento procesor")]


# ----------------------------------------------------------------------------- 5. full speed
def gauge(value, target, top, width):
    """A bar from 0 to `top` with the target marked ┃; green once the value reaches the target, yellow below."""
    filled = int(round(min(value, top) / top * width))
    mark = min(width - 1, int(round(target / top * width)))
    colour = ST.green if value >= target else ST.yellow
    cells = []
    for c in range(width):
        if c == mark:
            cells.append(ST.paint(ST.bold, "┃"))
        elif c < filled:
            cells.append(ST.paint(colour, "█"))
        else:
            cells.append(ST.paint(ST.grey, "░"))
    return "".join(cells), mark


class ThroughputView:
    """The full-speed run as a gauge of estimates per second against the target, with the per-second history."""

    def __init__(self, target, seconds, width):
        self.target, self.seconds, self.width = target, seconds, width
        self.block = LiveBlock()

    def frame(self, elapsed, total, windows, rate=None):
        """windows: (estimates, seconds) of every finished window of about one second; rate: current speed, if known."""
        if rate is not None:
            pass
        elif windows:
            rate = windows[-1][0] / windows[-1][1]
        else:
            rate = total / elapsed if elapsed > 0 else 0
        rates = [count / secs for count, secs in windows]
        top = max([1.5 * self.target, rate * 1.1] + [r * 1.1 for r in rates])
        gauge_w = self.width - 36
        bar_text, mark = gauge(rate, self.target, top, gauge_w)
        scale = [" "] * gauge_w
        target_text = f"cíl {fmt_int(self.target)}"
        start = min(max(mark - len(target_text) // 2, 2), gauge_w - len(target_text))
        scale[0] = "0"
        scale[start:start + len(target_text)] = list(target_text)
        history = "".join(ST.paint(ST.green if r >= self.target else ST.yellow, SPARK[min(8, max(1, math.ceil(r / top * 8)))])
                          for r in rates)
        return [
            ST.paint(ST.bold, "Plná rychlost: kolik odhadů za sekundu zvládne tento procesor (vyšší je lepší)"),
            ST.paint(ST.grey, f"Svislá čára ┃ = cíl {fmt_int(self.target)}. Zelená = cíl splněn, žlutá = pod cílem."),
            "",
            f"{'odhadů za sekundu':<20}{bar_text} {ST.paint(ST.bold, f'{fmt_int(int(rate)):>11}')}",
            ST.paint(ST.grey, f"{'':<20}{''.join(scale)}"),
            f"{'každá sekunda':<20}{history}" + ST.paint(ST.grey, f"  {len(rates)} oken po 1 s"),
            "",
            ST.paint(ST.grey, f"{'průběh':<20}") + progress(elapsed / self.seconds, 30)
            + ST.paint(ST.grey, f"  {elapsed:4.1f} / {self.seconds:.0f} s · odhadů celkem {fmt_int(total)}"),
        ]

    def draw(self, elapsed, total, windows, rate=None):
        self.block.draw(self.frame(elapsed, total, windows, rate))


# ----------------------------------------------------------------------------- the demo
def run_demo(args, live, width):
    """All sections in order; `width` is the number of characters every line may use."""
    demo_started = time.perf_counter()
    df, x, y, groups, _ = load()
    lock = locked_ids(groups)
    test = np.isin(groups, lock)
    x_tr, y_tr, x_te, y_te = x[~test], y[~test], x[test], y[test]
    shape_net = Net(x.shape[1], y.shape[1])          # only for the banner; train() seeds torch again before its own net
    linears = [m for m in shape_net.f if isinstance(m, torch.nn.Linear)]
    layer_sizes = [linears[0].in_features] + [m.out_features for m in linears]
    params = sum(p.numel() for p in shape_net.parameters())
    cpu = cpu_name()

    print()
    banner(width, x.shape[1], layer_sizes, params, len(np.unique(groups[~test])), len(x_tr), len(lock), len(x_te), cpu)

    # 1. Learning.
    section(1, "Síť se učí", width)
    say(f"Učení: {len(np.unique(groups[~test]))} výbojů ({fmt_int(len(x_tr))} okamžiků). "
        f"Kontrola: {len(lock)} odložených výbojů, na kterých se síť neučí.", width)
    print()
    started = time.perf_counter()
    view = LearningView(args.epochs, live, width)
    net, scalers = train(x_tr, y_tr, x_te, y_te, args.epochs, view)
    view.finish()
    train_s = time.perf_counter() - started
    print(f"\nNaučeno za {train_s:.0f} s." + ST.paint(ST.grey, f" ({args.epochs / train_s:.1f} epoch za sekundu, "
                                                             f"včetně výpisu na obrazovku)"))

    # 2. All outputs on the set-aside discharges.
    section(2, f"Všech {len(TARGETS)} veličin na {len(lock)} odložených výbojích", width)
    predict = fast_predictor(net, scalers)
    with torch.no_grad():
        mu, sd, ym, ys = scalers
        torch_pred = net(torch.tensor((x_te - mu) / sd)).numpy() * ys + ym
    scores = score(torch_pred, y_te, ~np.isnan(y_te))      # R² of every output and the configuration agreement
    agree = scores["is_limited"]["accuracy"]
    for line in scores_table(torch_pred, y_te, agree, width):
        print(line)
    print()
    print(ST.paint(ST.grey, textwrap.fill(
        f"Kontrola rychlé cesty (složené váhy, float32): na všech {fmt_int(len(x_te))} neviděných okamžicích se od sítě "
        f"liší nejvýš o {np.abs(predict(x_te) - torch_pred)[:, [R, Z]].max() * 1000:.6f} mm.", width)))

    # 3. Share of the set-aside instants inside a tolerance.
    section(3, "Úspěšnost: kolik okamžiků je v toleranci", width)
    say(f"Pro každou toleranci podíl okamžiků {len(lock)} odložených výbojů, ve kterých se poloha osy od "
        f"rekonstrukce ústavu liší méně. Čím dřív křivka dojde ke 100 %, tím lépe.", width)
    print()
    for line in success_lines(torch_pred, y_te, scores, live, width):
        print(line)
    under_1mm = [float(share_under(np.abs(torch_pred[:, j] - y_te[:, j]) * 1000, [1])[0]) for j in (R, Z)]

    # 4. One unseen discharge, instant by instant, each estimate timed as a single-row call.
    disc = int(lock[0])
    rows = np.where(groups == disc)[0]
    section(4, f"Výboj {disc}, na kterém se síť neučila, okamžik po okamžiku", width)
    say(f"Síť dostane výboj {disc}, na kterém se neučila: {len(rows)} okamžiků, každý jako samostatný odhad z jednoho "
        f"řádku měření. Časy se nejdřív změří v jedné těsné smyčce (kreslení by je zkreslilo), pak se odhady ukážou "
        f"okamžik po okamžiku.", width)
    print()
    single_ms, estimates = [], []
    for i in rows:
        t0 = time.perf_counter()
        p = predict(x[i:i + 1])[0]
        single_ms.append((time.perf_counter() - t0) * 1000)
        estimates.append(p)
    times = df["time"].values[rows]
    dview = DischargeView(disc, times, y[rows, R] * 1000, y[rows, Z] * 1000, live, width)
    errs_r, errs_z = [], []
    for i, p, ms in zip(rows, estimates, single_ms):
        errs_r.append(abs(p[R] * 1000 - y[i, R] * 1000))
        errs_z.append(abs(p[Z] * 1000 - y[i, Z] * 1000))
        dview.add(p[R] * 1000, p[Z] * 1000, ms)
        if live and args.pace > 0:
            time.sleep(args.pace / 1000)      # only so the room can watch the replay
    dview.finish()
    print()
    for line in latency_lines(single_ms, width):
        print(fit(line, width))
    print()
    print(f"Výboj {disc}: průměrná chyba osy R {ST.paint(ST.bold, f'{np.mean(errs_r):.2f} mm')}, "
          f"osy Z {ST.paint(ST.bold, f'{np.mean(errs_z):.2f} mm')}.")
    print(ST.paint(ST.grey, f"Medián doby jednoho odhadu {np.median(single_ms):.3f} ms."))

    # 5. Full speed: the unseen rows again and again in batches.
    section(5, "Plná rychlost", width)
    say(f"Všech {len(lock)} odložených výbojů ({fmt_int(len(x_te))} okamžiků) se odhaduje znovu a znovu, po dávkách "
        f"{args.batch} okamžiků, po dobu {args.seconds:.0f} s. Cíl je {fmt_int(args.target)} odhadů za sekundu.", width)
    print()
    batches = [x_te[i:i + args.batch] for i in range(0, len(x_te), args.batch)]
    err_r, err_z = axis_error(predict(x_te), y_te)
    tview = ThroughputView(args.target, args.seconds, width)
    if not live:
        print("     čas | odhadů celkem | odhadů za poslední sekundu | chyba osy R")
    total = 0
    compute = 0.0                       # seconds inside predict() only; drawing and printing are not counted
    batch_times, windows = [], []
    win_rows, win_secs = 0, 0.0
    last_draw = time.perf_counter()
    while compute < args.seconds:
        for b in batches:
            t0 = time.perf_counter()
            predict(b)
            dt = time.perf_counter() - t0
            batch_times.append(dt * 1000)
            compute += dt
            total += len(b)
            win_rows += len(b)
            win_secs += dt
            if win_secs >= 1:
                windows.append((win_rows, win_secs))
                if not live:
                    print(f"{compute:6.1f} s | {fmt_int(total):>13} | {fmt_int(int(win_rows / win_secs)):>22}     | {err_r:6.3f} mm")
                win_rows, win_secs = 0, 0.0
        if live and time.perf_counter() - last_draw >= 1:   # outside the timed loop
            tview.draw(compute, total, windows)
            last_draw = time.perf_counter()
    elapsed = compute
    rate = total / elapsed
    if live:
        tview.draw(elapsed, total, windows)
    else:
        print()
        for line in tview.frame(elapsed, total, windows):
            print(line)
    print()
    print(textwrap.fill(f"Celkem {fmt_int(int(rate))} odhadů za sekundu ({rate / args.target:.2f}x cíl "
                        f"{fmt_int(args.target)}) se stejnou vyškolenou sítí; jedna dávka {args.batch} okamžiků trvá "
                        f"asi {np.median(batch_times):.1f} ms.", width))
    print()
    median_batch = float(np.median(batch_times))
    summary = [
        f"{'rychlost':<14}" + ST.paint(ST.bold, f"{fmt_int(int(rate))} odhadů za sekundu")
        + f" = {rate / args.target:.2f}x cíl {fmt_int(args.target)}",
        f"{'jeden odhad':<14}medián " + ST.paint(ST.bold, f"{np.median(single_ms):.4f} ms")
        + f", p99 {np.percentile(single_ms, 99):.4f} ms (99 % odhadů je rychlejších)",
        f"{'chyba osy':<14}R " + ST.paint(ST.bold, f"{err_r:.3f} mm") + ", Z " + ST.paint(ST.bold, f"{err_z:.3f} mm")
        + f" vůči rekonstrukci ústavu, {len(lock)} odložených výbojů",
        f"{'pod 1 mm':<14}R " + ST.paint(ST.bold, f"{under_1mm[0]:.1f} %") + ", Z "
        + ST.paint(ST.bold, f"{under_1mm[1]:.1f} %") + " okamžiků má chybu osy pod 1 mm",
        f"{'konfigurace':<14}limiterová nebo divertorová: shoda s rekonstrukcí ústavu v "
        + ST.paint(ST.bold, f"{100 * agree:.2f} %") + " okamžiků",
        "",
        ST.paint(ST.grey, f"{'dávka':<14}{args.batch} okamžiků za {median_batch:.1f} ms (medián) = "
                          f"{median_batch / args.batch * 1000:.2f} µs na odhad; {fmt_int(total)} odhadů za {elapsed:.1f} s"),
        ST.paint(ST.grey, f"{'učení':<14}{args.epochs} epoch za {train_s:.1f} s, {fmt_int(params)} vah, seed 0, "
                          f"základní síť"),
        ST.paint(ST.grey, f"{'stroj':<14}{cpu} ({platform.machine()}); torch {args.threads} vláken"),
        ST.paint(ST.grey, f"{'software':<14}Python {platform.python_version()}, torch {torch.__version__}, "
                          f"numpy {np.__version__}"),
    ]
    for line in box("Souhrn", summary, width, ST.grey):
        print(line)

    # 6. Every estimate of one full-speed pass, measured first and listed afterwards.
    if args.dump_rows != 0:
        section(6, "Výpis odhadů jednoho průchodu", width)
        dump_rows(df, y, groups, test, predict, batches, args)
    print(ST.paint(ST.grey, f"\nCelé demo trvalo {time.perf_counter() - demo_started:.0f} s. Nic se neukládá na disk."))


def dump_rows(df, y, groups, test, predict, batches, args):
    """Every estimate of one full-speed pass, timed first and printed afterwards."""
    t0 = time.perf_counter()
    preds, per_row_us = [], []
    for b in batches:
        tb = time.perf_counter()
        preds.append(predict(b))
        per_row_us.append((time.perf_counter() - tb) * 1e6 / len(b))
    pass_ms = (time.perf_counter() - t0) * 1000
    pred = np.concatenate(preds)
    n_rows = sum(len(b) for b in batches)
    say(f"Každý odhad jednoho průchodu plnou rychlostí: {fmt_int(n_rows)} odhadů za {pass_ms:.2f} ms "
        f"({fmt_int(int(n_rows / pass_ms * 1000))} za sekundu). Vypisují se až po změření; "
        f"µs = mikrosekundy na jeden odhad v dávce.", 99)
    print("  odhad | výboj   čas  | osa R ústav     odhad   chyba | osa Z ústav     odhad   chyba | dávka   µs")
    idx = np.where(test)[0]
    n = len(idx) if args.dump_rows < 0 else min(args.dump_rows, len(idx))
    for k in range(n):
        i, p = idx[k], pred[k]
        tr_r, tr_z, p_r, p_z = y[i, R] * 1000, y[i, Z] * 1000, p[R] * 1000, p[Z] * 1000
        print(f"{k + 1:7d} | {groups[i]:5d}  {df['time'].iloc[i]:.3f} | {tr_r:9.2f} mm {p_r:8.2f} {abs(p_r - tr_r):5.2f} | "
              f"{tr_z:8.2f} mm {p_z:8.2f} {abs(p_z - tr_z):5.2f} | {k // args.batch + 1:4d}   {per_row_us[k // args.batch]:8.3f}")
    print(f"\n{fmt_int(n)} odhadů vypsáno. Průměrná chyba osy R {axis_error(pred, y[test])[0]:.3f} mm.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--seconds", type=float, default=10, help="length of the full-speed run")
    ap.add_argument("--batch", type=int, default=2048, help="rows per estimate call in the full-speed run")
    ap.add_argument("--target", type=int, default=800_000, help="estimates per second the full-speed run is compared with")
    ap.add_argument("--dump-rows", type=int, default=-1, help="rows of the final listing (default all, 0 none)")
    ap.add_argument("--threads", type=int, default=min(6, os.cpu_count() or 1))
    ap.add_argument("--plain", action="store_true",
                    help="no redraw and no colour codes, for logs (automatic when stdout is not a terminal)")
    ap.add_argument("--pace", type=float, default=15,
                    help="ms between instants when the live view replays the unseen discharge (the estimates are timed before)")
    args = ap.parse_args()
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
