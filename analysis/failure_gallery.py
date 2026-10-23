"""Failure gallery for the talk: the worst real discharges of the selected model, as six clean stills.

    VIEWER_DATA=<path to viewer/data.js> python -I analysis/failure_gallery.py

Reads the local viewer data (never in git), picks the 4 discharges with the largest mean magnetic axis error and
the 2 worst last frames (other discharges), draws true outline (line) and model estimate (points), and writes
presentation/assets/failure-*.png and failure-gallery.md. Real discharges are allowed in the talk (decision D-RP6).
"""
import json
import math
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
SRC = Path(os.environ.get("VIEWER_DATA", REPO / "viewer/data.js"))
OUT = REPO / "presentation/assets"
t = SRC.read_text()
D = json.loads(t[t.index("{"):t.rindex("}") + 1])
BG, FG, DIM, ACC, WARN = "#0b1220", "#e8eefc", "#7f8fb0", "#5fd4e8", "#ffb347"


def arr(c, k):
    return np.array([np.nan if v is None else v for v in c[k]], float)


def boundary(get, n=60):
    quads = [("upper_outer", "outer", "top", False), ("upper_inner", "inner", "top", True), ("lower_inner", "inner", "bottom", False), ("lower_outer", "outer", "bottom", True)]
    R, Z = [], []
    for q, side, tip, rev in quads:
        diag = 1 / math.sqrt(2) + get("squareness_" + q) * (1 - 1 / math.sqrt(2))
        p = -math.log(2) / math.log(min(0.99, max(0.01, diag)))
        Rs, Zs, Rt, Zt = get("R_" + side), get("Z_" + side), get("R_" + tip), get("Z_" + tip)
        phi = np.linspace(0, math.pi / 2, n)
        qr = Rt + (Rs - Rt) * np.cos(phi) ** (2 / p)
        qz = Zs + (Zt - Zs) * np.sin(phi) ** (2 / p)
        if rev:
            qr, qz = qr[::-1], qz[::-1]
        R += list(qr); Z += list(qz)
    return np.array(R), np.array(Z)


rows = []
for d in D["discharges"]:
    c = d["c"]
    ex = (arr(c, "R_mag_axis_pred") - arr(c, "R_mag_axis")) * 1000
    ez = (arr(c, "Z_mag_axis_pred") - arr(c, "Z_mag_axis")) * 1000
    e = np.hypot(ex, ez)
    ok = np.isfinite(e)
    if not ok.any():
        continue
    tt = arr(c, "time")
    last = np.where(ok)[0][-1]
    cur = arr(c, "plasma_current")
    lim_t, lim_p = arr(c, "is_limited") > 0.5, arr(c, "is_limited_pred") > 0.5
    rows.append(dict(id=d["id"], locked=d["locked"], fold=d["fold"], n=d["n"], mean=float(np.nanmean(e)), e=e, t=tt, last=int(last), last_err=float(e[last]),
                     worst_i=int(np.nanargmax(e)), cur=float(np.nanmean(cur)), flag_miss=float(np.mean(lim_t != lim_p)), flips=int(np.sum(np.diff(lim_p.astype(int)) != 0)),
                     limited_share=float(lim_t.mean()), c=c))
worst4 = sorted(rows, key=lambda r: -r["mean"])[:4]
rest = [r for r in rows if r["id"] not in {w["id"] for w in worst4}]
worst_last = sorted(rest, key=lambda r: -r["last_err"])[:2]
picks = [(r, r["worst_i"], "nejhorší průměrná chyba osy") for r in worst4] + [(r, r["last"], "nejhorší poslední snímek") for r in worst_last]
pos_share = float(np.mean([r["cur"] > 0 for r in rows]))


def story(r, i):
    s, e, tn = [], r["e"], r["t"]
    t_rel = (r["t"][i] - r["t"][0]) / max(1e-9, (r["t"][-1] - r["t"][0]))
    if r["cur"] > 0:
        s.append(f"proud plazmatu má kladné znaménko (obrácená polarita), a takových výbojů je v datech jen {pos_share * 100:.0f} %")
    if t_rel > 0.9:
        s.append("největší chyba je těsně před koncem výboje")
    elif t_rel < 0.1:
        s.append("největší chyba je hned na začátku výboje")
    if r["flag_miss"] > 0.1:
        s.append(f"model se v {r['flag_miss'] * 100:.0f} % snímků plete v tom, zda je plazma omezené, a příznak {r['flips']}krát přeskočí")
    elif r["flips"] >= 2:
        s.append(f"příznak omezeného plazmatu v odhadu přeskočí {r['flips']}krát")
    if not s:
        s.append("z dat vidíme jen velkou chybu osy, její příčinu z nich nepoznáme")
    return "; ".join(s)


md = ["# Galerie selhání (skutečné výboje, jen pro vystoupení)", "",
      "Čára je obrys z rekonstrukce ústavu, křížky jsou její klíčové body a modré body jsou odhad vybraného modelu (magnetická osa, X-bod, dopadové body, limiter). Odhad obrysu v datech prohlížeče není, proto se porovnávají body. Chyby jsou v milimetrech. Věty říkají jen to, co plyne z dat.", ""]
for k, (r, i, why) in enumerate(picks, 1):
    c = r["c"]
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    ax = fig.add_axes([0.04, 0.07, 0.50, 0.86], facecolor=BG)
    if D.get("wall"):
        ax.plot(D["wall"]["R"], D["wall"]["Z"], color=DIM, lw=1.2)
    tr = boundary(lambda n: float(c[n][i]))
    ax.plot(*tr, color=FG, lw=2.2, label="Rekonstrukce ústavu")
    pts = [("osa", "R_mag_axis", "Z_mag_axis"), ("X-bod", "R_x_point", "Z_x_point"), ("dopad 1", "R_strike_point_1", "Z_strike_point_1"), ("dopad 2", "R_strike_point_2", "Z_strike_point_2"), ("limiter", "R_limiter", "Z_limiter")]
    errs = []
    first = True
    for name, rk, zk in pts:
        tv, pv = (c[rk][i], c[zk][i]), (c.get(rk + "_pred", [None] * (i + 1))[i], c.get(zk + "_pred", [None] * (i + 1))[i])
        if None in tv or None in pv:
            continue
        ax.plot([tv[0], pv[0]], [tv[1], pv[1]], color=WARN, lw=1, alpha=.8)
        ax.plot(tv[0], tv[1], "+", color=FG, ms=13, mew=2)
        ax.plot(pv[0], pv[1], "o", color=ACC, ms=7, label="Odhad modelu" if first else None); first = False
        errs.append((name, math.hypot(tv[0] - pv[0], tv[1] - pv[1]) * 1000))
    ax.set_aspect("equal"); ax.set_xlim(*D["view"]["R"]); ax.set_ylim(*D["view"]["Z"])
    ax.tick_params(colors=DIM, labelsize=9)
    for sp in ax.spines.values():
        sp.set_color("#2a3a5c")
    ax.set_xlabel("R [m]", color=DIM); ax.set_ylabel("Z [m]", color=DIM)
    ax.legend(loc="lower right", facecolor=BG, edgecolor="#2a3a5c", labelcolor=FG, fontsize=11)
    which = "zamčená sada 30 výbojů" if r["locked"] else f"při učení neviděl, díl {r['fold'] + 1} z 5"
    t_rel = (r["t"][i] - r["t"][0]) / max(1e-9, (r["t"][-1] - r["t"][0]))
    fig.text(0.58, 0.88, f"Výboj {r['id']}", color=FG, fontsize=30, fontweight="bold")
    fig.text(0.58, 0.83, which, color=ACC, fontsize=15)
    fig.text(0.58, 0.64, f"{r['e'][i]:.1f} mm", color=WARN, fontsize=54, fontweight="bold")
    fig.text(0.58, 0.60, "chyba osy v tomto snímku", color=DIM, fontsize=14)
    fig.text(0.58, 0.50, f"průměr přes výboj: {r['mean']:.1f} mm", color=FG, fontsize=16)
    fig.text(0.58, 0.45, f"snímek v čase {t_rel * 100:.0f} % výboje · {why}", color=DIM, fontsize=12)
    for q, (nm, ev) in enumerate(errs):
        fig.text(0.58, 0.38 - q * 0.04, f"{nm}: {ev:.1f} mm", color=FG if nm == "osa" else DIM, fontsize=13)
    fig.text(0.58, 0.07, "Skutečný výboj, pouze pro vystoupení", color=DIM, fontsize=10)
    f = OUT / f"failure-{k}.png"
    fig.savefig(f, facecolor=BG); plt.close(fig)
    md += [f"## failure-{k}.png, výboj {r['id']} ({which})", f"- {why}, chyba osy ve snímku {r['e'][i]:.1f} mm, průměr přes výboj {r['mean']:.1f} mm.",
           f"- {story(r, i).capitalize()}.", ""]
    print(k, r["id"], which, f"mean {r['mean']:.1f} frame {r['e'][i]:.1f} mm", why)
(OUT / "failure-gallery.md").write_text("\n".join(md))
