#!/usr/bin/env python
"""Live training demo, fast version: the baseline network learns epoch by epoch, then estimates an unseen discharge one time step
at a time through the fast pass, then runs all unseen discharges through it at full speed (batches on 6 cores, kept in L3).

The fast pass uses the trained weights with the input standardisation folded
into the first layer and the output scaling into the last one (exact algebra), preallocated buffers and in-place ReLU; it is
checked against the network itself on every unseen time step before it is used.

The training loop is ipp1_common.fit_mlp (same network, AdamW, one-cycle schedule, masked loss, 60 epochs), copied here only so
it can print progress after every epoch, with one change: ReLU instead of SiLU between the layers. On fold 0 this gave axis R
0.457 mm against 0.387 mm with SiLU (one run each, Fri 23 Oct); the throughput in results/ipp1-throughput-ryzen.md is SiLU. LOCAL ONLY: prints IPP data rows to the terminal; never record, share or commit its
output (CON-001). Aggregate throughput numbers for the report come from analysis/ipp1_throughput.py.

    HACKATHON_HOME=<hackathon folder> analysis/ipp1_live_train_fast.sh
"""
import time

import numpy as np
import torch

import ipp1_common as C

torch.set_num_threads(2)
B, D, G, R, Y0, X0 = "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[33m", "\033[0m"
EPOCHS = 60

print(f"{B}Tvar plazmatu z magnetických měření: síť se učí živě (aktivace ReLU){X0}\n")
df, X, Y, groups, mask = C.load()
tr, te = C.group_folds(X, Y, groups)[0]
print(f"Učení: {len(np.unique(groups[tr]))} výbojů ({len(tr):,} okamžiků). Kontrola: {len(np.unique(groups[te]))} výbojů, "
      f"které síť nikdy neuvidí.\n")

# --- ipp1_common.fit_mlp, with a progress line per epoch ---
torch.manual_seed(0)
xtr, ytr, mtr = X[tr], Y[tr], mask[tr]
mu, sd = xtr.mean(0), xtr.std(0) + 1e-9
ym, ys = np.nanmean(ytr, 0), np.nanstd(ytr, 0) + 1e-9
xt = torch.tensor((xtr - mu) / sd)
yt = torch.tensor(np.nan_to_num((ytr - ym) / ys))
mt = torch.tensor(mtr.astype(np.float32))
net = C.Net(xt.shape[1], yt.shape[1])
for k, m in enumerate(net.f):  # ReLU instead of the project's SiLU; SiLU has no weights, so the initial weights are unchanged
    if isinstance(m, torch.nn.SiLU):
        net.f[k] = torch.nn.ReLU()
opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
steps = EPOCHS * ((len(xt) + 511) // 512)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=steps)
iR, iZ = C.TARGETS.index("R_mag_axis"), C.TARGETS.index("Z_mag_axis")
xte = torch.tensor((X[te] - mu) / sd)


def heldout_axis_mm():
    net.eval()
    with torch.no_grad():
        p = net(xte).numpy() * ys + ym
    net.train()
    return [float(np.nanmean(np.abs(p[:, j] - Y[te, j]))) * 1000 for j in (iR, iZ)]


print(f"{D}epocha | ztráta učení | chyba osy R na neviděných výbojích | osa Z | čas{X0}")
t0 = time.time()
for ep in range(1, EPOCHS + 1):
    perm, total, nb = torch.randperm(len(xt)), 0.0, 0
    for i in range(0, len(xt), 512):
        b = perm[i:i + 512]
        loss = ((net(xt[b]) - yt[b]) ** 2 * mt[b]).sum() / mt[b].sum()
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
        total, nb = total + loss.item(), nb + 1
    eR, eZ = heldout_axis_mm()
    bar = "█" * max(1, min(40, int(40 * np.log10(1 + eR) / np.log10(11))))
    col = G if eR < 0.5 else (Y0 if eR < 2 else R)
    print(f"  {ep:3d}  | {total / nb:10.4f}   | {col}{eR:7.3f} mm {bar:40s}{X0} | {eZ:6.3f} mm | {time.time() - t0:5.1f} s",
          flush=True)
net.eval()
print(f"\n{G}Naučeno za {time.time() - t0:.0f} s.{X0} Teď síť dostane výboj, který nikdy neviděla, okamžik po okamžiku.\n")

# --- fast pass from the trained weights: raw sensor values in, physical units out ---
lin = [m for m in net.f if isinstance(m, torch.nn.Linear)]
with torch.no_grad():
    Wt = [m.weight.T.double().clone() for m in lin]
    bs = [m.bias.double().clone() for m in lin]
    mu_t, sd_t = torch.tensor(mu, dtype=torch.float64), torch.tensor(sd, dtype=torch.float64)
    bs[0] = bs[0] - (mu_t / sd_t) @ Wt[0]
    Wt[0] = Wt[0] / sd_t[:, None]
    ys_t, ym_t = torch.tensor(ys, dtype=torch.float64), torch.tensor(ym, dtype=torch.float64)
    Wt[-1], bs[-1] = Wt[-1] * ys_t, bs[-1] * ys_t + ym_t
FW = [w.float().contiguous() for w in Wt]
FB = [b.float().contiguous() for b in bs]


def make_forward(n):
    """Fast pass for batches of up to n rows: addmm into preallocated buffers, ReLU in place."""
    bufs = [torch.empty(n, w.shape[1]) for w in FW]

    def fwd(x):
        h, m = x, x.shape[0]
        for i, (w, b) in enumerate(zip(FW, FB)):
            out = bufs[i][:m]
            torch.addmm(b, h, w, out=out)
            if i < 3:
                torch.relu_(out)
            h = out
        return h
    return fwd


xraw = torch.tensor(X[te], dtype=torch.float32).contiguous()
check = make_forward(len(xraw))
with torch.inference_mode():
    ref = net(xte).numpy() * ys + ym
    diff = float(np.nanmax(np.abs(check(xraw).numpy() - ref)[:, [iR, iZ]])) * 1000
print(f"{D}Rychlá cesta ověřena na všech {len(xraw):,} neviděných okamžicích: od sítě se liší nejvýš o {diff:.6f} mm.{X0}\n")
torch.set_num_threads(1)  # one time step at a time: more threads would only add synchronisation
one = make_forward(1)


def predict_one(x):
    with torch.inference_mode():
        return one(torch.from_numpy(x.astype(np.float32))).numpy()[0]


test_ids = np.unique(groups[te])
lengths = {g: (groups == g).sum() for g in test_ids}
dis = sorted(test_ids, key=lambda g: abs(lengths[g] - np.median(list(lengths.values()))))[0]
rows = np.where(groups == dis)[0]
rows = rows[np.argsort(df["time"].values[rows])]
print(f"{B}Výboj {dis}: {len(rows)} okamžiků.{X0}")
print(f"{D}čas   | osa R skutečná  odhad   chyba | osa Z skutečná  odhad   chyba | doba odhadu{X0}")
lat, eRs = [], []
for i in rows:
    t = time.perf_counter()
    p = predict_one(X[i:i + 1])
    dt = (time.perf_counter() - t) * 1000
    lat.append(dt)
    yR, pR, yZ, pZ = Y[i, iR] * 1000, p[iR] * 1000, Y[i, iZ] * 1000, p[iZ] * 1000
    eRs.append(abs(pR - yR))
    col = G if eRs[-1] < 0.5 else (Y0 if eRs[-1] < 2 else R)
    print(f"{df['time'].values[i]:5.3f} | {yR:8.2f} mm {pR:8.2f} {col}{eRs[-1]:5.2f}{X0} | {yZ:8.2f} mm {pZ:8.2f} "
          f"{abs(pZ - yZ):5.2f} | {dt:6.3f} ms", flush=True)
    time.sleep(0.04)  # slowed down so a person can read it
print(f"\n{B}Výboj {dis}:{X0} průměrná chyba osy R {np.mean(eRs):.2f} mm; doba jednoho odhadu medián {np.median(lat):.3f} ms "
      "(včetně Pythonu kolem sítě, tento procesor)")

# --- full speed: all unseen discharges in batches of 2048 on 6 threads; weights + one batch = about 6 MB, inside the 16 MB L3 ---
BATCH, THREADS, SECONDS = 2048, 6, 10
torch.set_num_threads(THREADS)
fast = make_forward(BATCH)
starts = list(range(0, len(xraw), BATCH))  # the last batch is partial, so every unseen time step is estimated once per pass
out = np.empty((len(xraw), ym.shape[0]), np.float32)
print(f"\n{B}Plná rychlost:{X0} všech {len(test_ids)} neviděných výbojů ({len(xraw):,} okamžiků) znovu a znovu, dávky po {BATCH}, "
      f"{THREADS} vláken, cíl 800 000 odhadů za sekundu")
print(f"{D}    čas | odhadů celkem | odhadů za poslední sekundu | chyba osy R{X0}")
with torch.inference_mode():
    for s in starts[:3]:
        fast(xraw[s:s + BATCH])
    total, t_start = 0, time.perf_counter()
    while time.perf_counter() - t_start < SECONDS:
        n_sec, t_sec = 0, time.perf_counter()
        while time.perf_counter() - t_sec < 1.0:
            for s in starts:
                out[s:s + BATCH] = fast(xraw[s:s + BATCH]).numpy()
            n_sec += len(xraw)
        rate = n_sec / (time.perf_counter() - t_sec)
        total += n_sec
        eR = float(np.nanmean(np.abs(out[:, iR] - Y[te, iR]))) * 1000
        col = G if rate >= 800_000 else Y0
        print(f"{time.perf_counter() - t_start:5.1f} s | {total:13,d} | {col}{rate:22,.0f}{X0}     | {eR:6.3f} mm".replace(",", " "),
              flush=True)
    rate = total / (time.perf_counter() - t_start)
print(f"\n{B}Celkem {rate:,.0f} odhadů za sekundu{X0} ({rate / 800_000:.2f}x cíl 800 000) se stejnou vyškolenou sítí; "
      f"jedna dávka {BATCH} okamžiků trvá asi {BATCH / rate * 1000:.1f} ms.".replace(",", " ").replace(".", ",", 0))

# --- every single estimate: one more full-speed pass, timed per batch, then all of its estimates printed one per line ---
# (printing a line takes far longer than computing it, so the lines are printed after the timed pass, not during it)
batch_us = []
with torch.inference_mode():
    for s in starts:
        tb = time.perf_counter_ns()
        out[s:s + BATCH] = fast(xraw[s:s + BATCH]).numpy()
        batch_us.append((time.perf_counter_ns() - tb) / 1e3)
print(f"\n{B}Každý odhad jednoho průchodu plnou rychlostí:{X0} {len(xraw):,} odhadů za {sum(batch_us) / 1000:.2f} ms "
      f"({len(xraw) / sum(batch_us) * 1e6:,.0f} za sekundu). Vypisují se až po změření.".replace(",", " "))
print(f"{D}  odhad | výboj   čas  | osa R skutečná  odhad   chyba | osa Z skutečná  odhad   chyba | dávka  µs na odhad v dávce{X0}")
times, gte = df["time"].values[te], groups[te]
for k in range(len(xraw)):
    j = k // BATCH
    yR, pR, yZ, pZ = Y[te[k], iR] * 1000, out[k, iR] * 1000, Y[te[k], iZ] * 1000, out[k, iZ] * 1000
    eRk = abs(pR - yR)
    col = G if eRk < 0.5 else (Y0 if eRk < 2 else R)
    print(f"{k + 1:7d} | {gte[k]:5d} {times[k]:6.3f} | {yR:8.2f} mm {pR:8.2f} {col}{eRk:5.2f}{X0} | {yZ:8.2f} mm {pZ:8.2f} "
          f"{abs(pZ - yZ):5.2f} | {j + 1:4d}   {batch_us[j] / (min(BATCH, len(xraw) - j * BATCH)):8.3f}")
print(f"\n{B}{len(xraw):,} odhadů vypsáno.{X0} Průměrná chyba osy R {float(np.nanmean(np.abs(out[:, iR] - Y[te, iR]))) * 1000:.3f} mm."
      .replace(",", " "))
