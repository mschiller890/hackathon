#!/usr/bin/env python
"""The whole idea of the project, live in the terminal: 24 magnetic measurements in, plasma shape out.

    HACKATHON_HOME=<hackathon folder> python -I analysis/mini_pipeline.py [--epochs 60] [--seconds 10] [--dump-rows N]

What it prints, in order (Czech, it is the demo for the jury):
  1. the network learning epoch by epoch: training loss, axis error on the 30 discharges it never sees, time;
  2. one unseen discharge instant by instant: reference, estimate, error and the time of each single estimate;
  3. full speed: the 30 unseen discharges again and again in batches, estimates per second;
  4. every estimate of one full-speed pass (--dump-rows 0 skips it).

Same data, network (ipp1_common.Net) and 119/30 split as the project (ipp1_final.locked_ids), one seed, so the
axis error at the end is the baseline network's number on the locked discharges (results/ipp1-final.md, `base`).
Writes nothing. The core of the project, for the reader of this file:
    ipp1_common.py   data loading, the network, masked training, scoring
    ipp1_final.py    the shipped model and the locked 30-discharge test
    export_model.py  predict.py   the shipped model as one numpy-only file
    make_all.py      runs the analysis steps in dependency order
"""
import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import TARGETS, Net, load
from ipp1_final import locked_ids

R, Z = TARGETS.index("R_mag_axis"), TARGETS.index("Z_mag_axis")
BOLD, DIM, RED, YELLOW, GREEN, END = "\033[1m", "\033[2m", "\033[31m", "\033[33m", "\033[32m", "\033[0m"


def bar(err_mm, width=40):
    """Log scale from 0.1 mm (empty) to 10 mm (full); colour says the same as the number: red over 2 mm, green under 0.5."""
    n = int(np.clip((np.log10(max(err_mm, 1e-6)) + 1) / 2 * width, 0, width))
    colour = RED if err_mm > 2 else YELLOW if err_mm > 0.5 else GREEN
    return f"{colour}{err_mm:7.3f} mm {'█' * n:{width}}{END}"


def axis_error(pred, y):
    """Mean absolute error of the magnetic axis in mm (R, Z); the axis exists in every row."""
    return [float(np.abs(pred[:, j] - y[:, j]).mean() * 1000) for j in (R, Z)]


def train(x, y, x_test, y_test, epochs, seed=0):
    """The masked training of ipp1_common.fit_mlp with the test error printed after every epoch.

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
    print(f"{DIM}{'epocha':^6} | {'ztráta učení':^12} | {'chyba osy R na neviděných výbojích':<51} | {'osa Z':^9} | {'čas':>7}{END}")
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
        print(f"{epoch:^6d} | {np.mean(losses):^12.4f} | {bar(err_r)} | {err_z:6.3f} mm | {time.perf_counter() - started:5.1f} s")
    net.eval()
    return net, (mu, sd, ym, ys)


def numpy_predictor(net, scalers):
    """The trained network as plain numpy matrix products: no torch on the fast path, same numbers."""
    mu, sd, ym, ys = scalers
    layers = [(m.weight.detach().numpy().T.copy(), m.bias.detach().numpy().copy()) for m in net.f if isinstance(m, torch.nn.Linear)]

    def predict(rows):
        h = (rows - mu) / sd
        for k, (w, b) in enumerate(layers):
            h = h @ w + b
            if k < len(layers) - 1:
                h = h / (1 + np.exp(-h))     # SiLU, as in ipp1_common.Net
        return h * ys + ym
    return predict


def fmt_int(n):
    return f"{n:,}".replace(",", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--seconds", type=float, default=10, help="length of the full-speed run")
    ap.add_argument("--batch", type=int, default=2048, help="rows per estimate call in the full-speed run")
    ap.add_argument("--target", type=int, default=800_000, help="estimates per second the full-speed run is compared with")
    ap.add_argument("--dump-rows", type=int, default=-1, help="rows of the final listing (default all, 0 none)")
    ap.add_argument("--threads", type=int, default=min(6, os.cpu_count() or 1))
    args = ap.parse_args()
    torch.set_num_threads(args.threads)

    df, x, y, groups, _ = load()
    lock = locked_ids(groups)
    test = np.isin(groups, lock)
    x_tr, y_tr, x_te, y_te = x[~test], y[~test], x[test], y[test]
    print(f"{BOLD}Tvar plazmatu z magnetických měření: síť se učí živě (aktivace SiLU){END}\n")
    print(f"Učení: {len(np.unique(groups[~test]))} výbojů ({fmt_int(len(x_tr))} okamžiků). "
          f"Kontrola: {len(lock)} výbojů, které síť nikdy neuvidí.\n")

    started = time.perf_counter()
    net, scalers = train(x_tr, y_tr, x_te, y_te, args.epochs)
    print(f"\nNaučeno za {time.perf_counter() - started:.0f} s. Teď síť dostane výboj, který nikdy neviděla, okamžik po okamžiku.\n")

    predict = numpy_predictor(net, scalers)
    with torch.no_grad():
        mu, sd, ym, ys = scalers
        torch_pred = net(torch.tensor((x_te - mu) / sd)).numpy() * ys + ym
    print(f"Rychlá cesta ověřena na všech {fmt_int(len(x_te))} neviděných okamžicích: "
          f"od sítě se liší nejvýš o {np.abs(predict(x_te) - torch_pred)[:, [R, Z]].max() * 1000:.6f} mm.\n")

    # One unseen discharge, instant by instant, each estimate timed as a single-row call.
    disc = int(lock[0])
    rows = np.where(groups == disc)[0]
    print(f"Výboj {disc}: {len(rows)} okamžiků.")
    print("čas   | osa R skutečná  odhad   chyba | osa Z skutečná  odhad   chyba | doba odhadu")
    single_ms, errs_r = [], []
    for i in rows:
        t0 = time.perf_counter()
        p = predict(x[i:i + 1])[0]
        single_ms.append((time.perf_counter() - t0) * 1000)
        tr_r, tr_z, p_r, p_z = y[i, R] * 1000, y[i, Z] * 1000, p[R] * 1000, p[Z] * 1000
        errs_r.append(abs(p_r - tr_r))
        print(f"{df['time'].iloc[i]:.3f} | {tr_r:9.2f} mm {p_r:8.2f} {abs(p_r - tr_r):5.2f} | "
              f"{tr_z:8.2f} mm {p_z:8.2f} {abs(p_z - tr_z):5.2f} | {single_ms[-1]:6.3f} ms")
    print(f"\nVýboj {disc}: průměrná chyba osy R {np.mean(errs_r):.2f} mm; doba jednoho odhadu medián "
          f"{np.median(single_ms):.3f} ms (včetně Pythonu kolem sítě, tento procesor)\n")

    # Full speed: the unseen rows again and again in batches, reported once a second.
    print(f"Plná rychlost: všech {len(lock)} neviděných výbojů ({fmt_int(len(x_te))} okamžiků) znovu a znovu, "
          f"dávky po {args.batch}, {args.threads} vláken, cíl {fmt_int(args.target)} odhadů za sekundu")
    print("    čas | odhadů celkem | odhadů za poslední sekundu | chyba osy R")
    batches = [x_te[i:i + args.batch] for i in range(0, len(x_te), args.batch)]
    err_r = axis_error(predict(x_te), y_te)[0]
    total = last = 0
    t_start = t_tick = time.perf_counter()
    batch_times = []
    while (now := time.perf_counter()) - t_start < args.seconds:
        for b in batches:
            t0 = time.perf_counter()
            predict(b)
            batch_times.append((time.perf_counter() - t0) * 1000)
            total += len(b)
        if now - t_tick >= 1:
            print(f"{now - t_start:6.1f} s | {fmt_int(total):>13} | {fmt_int(total - last):>22}     | {err_r:6.3f} mm")
            last, t_tick = total, now
    elapsed = time.perf_counter() - t_start
    rate = total / elapsed
    print(f"\nCelkem {fmt_int(int(rate))} odhadů za sekundu ({rate / args.target:.2f}x cíl {fmt_int(args.target)}) se stejnou "
          f"vyškolenou sítí; jedna dávka {args.batch} okamžiků trvá asi {np.median(batch_times):.1f} ms.\n")

    # Every estimate of one full-speed pass, measured first and listed afterwards.
    if args.dump_rows == 0:
        return
    t0 = time.perf_counter()
    preds, per_row_us = [], []
    for b in batches:
        tb = time.perf_counter()
        preds.append(predict(b))
        per_row_us.append((time.perf_counter() - tb) * 1e6 / len(b))
    pass_ms = (time.perf_counter() - t0) * 1000
    pred = np.concatenate(preds)
    print(f"Každý odhad jednoho průchodu plnou rychlostí: {fmt_int(len(x_te))} odhadů za {pass_ms:.2f} ms "
          f"({fmt_int(int(len(x_te) / pass_ms * 1000))} za sekundu). Vypisují se až po změření.")
    print("  odhad | výboj   čas  | osa R skutečná  odhad   chyba | osa Z skutečná  odhad   chyba | dávka  µs na odhad v dávce")
    idx = np.where(test)[0]
    n = len(idx) if args.dump_rows < 0 else min(args.dump_rows, len(idx))
    for k in range(n):
        i, p = idx[k], pred[k]
        tr_r, tr_z, p_r, p_z = y[i, R] * 1000, y[i, Z] * 1000, p[R] * 1000, p[Z] * 1000
        print(f"{k + 1:7d} | {groups[i]:5d}  {df['time'].iloc[i]:.3f} | {tr_r:9.2f} mm {p_r:8.2f} {abs(p_r - tr_r):5.2f} | "
              f"{tr_z:8.2f} mm {p_z:8.2f} {abs(p_z - tr_z):5.2f} | {k // args.batch + 1:4d}   {per_row_us[k // args.batch]:8.3f}")
    print(f"\n{fmt_int(n)} odhadů vypsáno. Průměrná chyba osy R {axis_error(pred, y_te)[0]:.3f} mm.")


if __name__ == "__main__":
    main()
