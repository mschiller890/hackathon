#!/usr/bin/env python
"""Nasazený model čistých dat: měření dělená proudem plazmatem. Natrénuje ho a uloží pro predict.py.

Proč dělit proudem: pole cívek je úměrné proudům, takže tvar plazmatu závisí na POMĚRECH měření k proudu
plazmatem, ne na jejich velikosti. Proud známe ze vstupu samotného (ridge regrese ze 24 měření, chyba 0,03 kA),
takže každé měření vydělíme jeho odhadem (i se znaménkem, aby obrácená polarita dopadla stejně) a samotný proud
přidáme jako další vstup. Na 119 vývojových výbojích (5 dílů po výbojích, jedno semínko) to zmenšilo střední
relativní chybu přes 16 výstupů z 0,0954 na 0,0447 (viz results/ipp1-ipn.md).

Vstupy sítí (67 sloupců při --feat diff2): 24 vydělených měření, 22 rozdílů sousedních cívek a smyček,
20 druhých diferencí a proud / 1e5.

Dvě sítě:
  * obecná síť odpovídá na všech 16 výstupů,
  * limiterová síť se učí jen na řádcích, které jsou opravdu limiterové, a má pět výstupů: na které straně komory
    (+1 nahoře, -1 dole) bod dotyku leží a kde přesně (R a Z pro stranu nahoře a R a Z pro stranu dole).
    Bod dotyku se pak odhaduje jako průměr odpovědi obecné sítě a odpovědi limiterové sítě pro vybranou stranu
    (to dělá predict.py). Samotná regrese by mezi stranami zprůměrovala a chybovala o stovky mm.

Ztráta: Huberova s delta 0,2 na standardizovaných cílech, počítaná jen tam, kde cíl existuje. AdamW, jeden cyklus
učicí rychlosti, 150 epoch, dávky po 512 řádcích.

    python analysis/clean_model.py [--feat diff2] [--epochs 150] [--all] [--live]    uloží out/model/ipp1-ipn.npz a .json

Bez --all (tak to volá run.py) se učí jen na 119 vývojových výbojích: to je soubor, který se nasazuje, a model
za všemi čísly na 30 odložených výbojích. S --all se učí na všech 149 výbojích (i odložených); do balíčku se nedává.
VÁHY JSOU ODVOZENÉ Z DŮVĚRNÝCH DAT IPP: složka out/ je v .gitignore.
"""
import argparse
import json
import sys
import time
from collections import namedtuple
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as functional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import final_evaluation as F
from common import OUT

MODEL_FOLDER = OUT / "model"
CURRENT_SCALE = 1e5  # proud se dělí tímto číslem, aby vstup sítě byl řádově jedna (proud je ~2e5 A)
TARGETS = F.TARGETS
COLUMN = F.TARGET_COLUMN
R_LIMITER, Z_LIMITER = COLUMN["R_limiter"], COLUMN["Z_limiter"]
IS_LIMITED, PLASMA_CURRENT = COLUMN["is_limited"], COLUMN["plasma_current"]

# Natrénovaná síť spolu se standardizací, kterou potřebuje (střední hodnoty a odchylky vstupů a cílů).
TrainedNetwork = namedtuple("TrainedNetwork", "network input_mean input_std target_mean target_std")


# ===================================================================================================================
# Vstupy sítě
# ===================================================================================================================
def base_features(measurements, feature_mode):
    """24 vstupů, rozdíly sousedních cívek (15) a smyček (7) a u diff2 ještě jejich druhé diference (14 + 6)."""
    parts = [measurements, np.diff(measurements[:, :16], axis=1), np.diff(measurements[:, 16:24], axis=1)]
    if feature_mode == "diff2":
        parts += [np.diff(measurements[:, :16], 2, axis=1), np.diff(measurements[:, 16:24], 2, axis=1)]
    return np.concatenate(parts, axis=1)


def build_features(measurements, current_weights, current_offset, feature_mode):
    """Vstup každé sítě: měření vydělená odhadem proudu, jejich diference a samotný proud."""
    current = measurements.astype(np.float64) @ current_weights + current_offset
    divided = measurements * (CURRENT_SCALE / current)[:, None]
    return np.concatenate([base_features(divided, feature_mode), (current / CURRENT_SCALE)[:, None]],
                          axis=1).astype(np.float32)


# ===================================================================================================================
# Učení
# ===================================================================================================================
def fit_network(measurements, targets, ridge, feature_mode, seed, epochs,
                huber_delta=0.2, widths=(256, 256, 128), on_epoch=None):
    """Natrénuje jednu síť. Cíle smějí obsahovat NaN (veličina neexistuje): takové hodnoty chybu neovlivní.

    on_epoch(epoch, průměrná ztráta, síť, střední hodnota vstupů, odchylka vstupů, střední hodnota cílů, odchylka cílů)
    se volá po každé epoše, jen aby se dalo učení ukazovat. Nelosuje žádná čísla a nemění žádnou váhu,
    takže natrénovaná síť je stejná s ním i bez něj.
    """
    torch.manual_seed(seed)
    features = build_features(measurements, *ridge, feature_mode)
    input_mean, input_std = features.mean(0), features.std(0) + 1e-9
    target_mean = np.nan_to_num(np.nanmean(targets, 0))
    target_std = np.nanstd(targets, 0) + 1e-9
    target_std = np.where(np.isnan(target_std), 1.0, target_std)  # sloupec bez jediné hodnoty: odchylka 1

    x_tensor = torch.tensor((features - input_mean) / input_std)
    y_tensor = torch.tensor(np.nan_to_num((targets - target_mean) / target_std).astype(np.float32))
    exists_tensor = torch.tensor((~np.isnan(targets)).astype(np.float32))

    network = F.MLP(x_tensor.shape[1], y_tensor.shape[1], widths)
    optimizer = torch.optim.AdamW(network.parameters(), lr=2e-3, weight_decay=1e-4)
    batch_size = 512
    steps = epochs * ((len(x_tensor) + batch_size - 1) // batch_size)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=3e-3, total_steps=steps)

    for epoch in range(1, epochs + 1):
        shuffled = torch.randperm(len(x_tensor))
        losses = []
        for start in range(0, len(x_tensor), batch_size):
            batch = shuffled[start:start + batch_size]
            error = 2 * functional.huber_loss(network(x_tensor[batch]), y_tensor[batch], reduction="none", delta=huber_delta)
            loss = (error * exists_tensor[batch]).sum() / exists_tensor[batch].sum()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
            losses.append(loss.detach().item())
        if on_epoch:
            on_epoch(epoch, float(np.mean(losses)), network, input_mean, input_std, target_mean, target_std)
    network.eval()
    return TrainedNetwork(network, input_mean.astype(np.float32), input_std.astype(np.float32),
                          target_mean.astype(np.float32), target_std.astype(np.float32))


def ridge_current(measurements, targets):
    """Ridge regrese proudu plazmatem ze 24 měření: vrací (váhy, posun), proud = měření @ váhy + posun."""
    weights, offset = F.fit_ridge_coefficients(measurements, targets, ~np.isnan(targets), PLASMA_CURRENT)
    return np.asarray(weights, np.float64), float(offset)


def limiter_targets(targets):
    """Pět cílů limiterové sítě: strana (+1 nahoře, -1 dole), pak R a Z pro stranu nahoře a R a Z pro stranu dole.

    Hodnoty pro stranu, na které bod dotyku neleží, jsou NaN, takže chybu neovlivní.
    """
    is_up = targets[:, Z_LIMITER] > 0
    result = np.full((len(targets), 5), np.nan, np.float32)
    result[:, 0] = np.where(is_up, 1.0, -1.0)
    result[np.ix_(is_up, [1, 2])] = targets[np.ix_(is_up, [R_LIMITER, Z_LIMITER])]
    result[np.ix_(~is_up, [3, 4])] = targets[np.ix_(~is_up, [R_LIMITER, Z_LIMITER])]
    return result


def train(measurements, targets, feature_mode="diff2", epochs=150, seed=0, on_epoch=None, on_limiter_start=None):
    """Natrénuje celý model na zadaných řádcích a vrátí ho jako slovník polí ve formátu, který čte predict.py.

    on_epoch: viz fit_network (jen pro obecnou síť). on_limiter_start() se zavolá před učením limiterové sítě.
    """
    ridge = ridge_current(measurements, targets)
    on_general_epoch = on_epoch and (lambda *args: on_epoch(*args, ridge=ridge))
    general = fit_network(measurements, targets, ridge, feature_mode, seed, epochs, on_epoch=on_general_epoch)
    if on_limiter_start:
        on_limiter_start()
    is_limited = targets[:, IS_LIMITED] > 0.5
    limiter = fit_network(measurements[is_limited], limiter_targets(targets[is_limited]), ridge, feature_mode, seed, epochs)

    arrays = {"ridge_w": ridge[0], "ridge_b": np.float64(ridge[1])}
    for tag, trained in (("gen", general), ("spec", limiter)):
        linear_layers = [layer for layer in trained.network.layers if isinstance(layer, nn.Linear)]
        for i, layer in enumerate(linear_layers):
            arrays[f"{tag}_W{i}"] = layer.weight.detach().numpy().T.astype(np.float32)
            arrays[f"{tag}_b{i}"] = layer.bias.detach().numpy().astype(np.float32)
        arrays[f"{tag}_mu"], arrays[f"{tag}_sd"] = trained.input_mean, trained.input_std
        arrays[f"{tag}_ym"], arrays[f"{tag}_ys"] = trained.target_mean, trained.target_std
    return arrays


# ===================================================================================================================
# Živý graf učení (stejný jako v demu)
# ===================================================================================================================
def live_view(shown_measurements, shown_targets, feature_mode, epochs, started):
    """Graf učení z live_demo.py pro nasazený model: po každé epoše obecná síť odhadne odložené řádky
    (ty se jen měří, nikdy se na nich neučí) a graf ukáže ztrátu, chybu osy v mm a celkovou přesnost."""
    import shutil
    import live_demo as demo

    is_terminal = sys.stdout.isatty()
    demo.ST = demo.Style(is_terminal)
    width = min(100, shutil.get_terminal_size((100, 40)).columns) - 1 if is_terminal else 99
    view = demo.LearningView(epochs, is_terminal, width)
    r_axis, z_axis = COLUMN["R_mag_axis"], COLUMN["Z_mag_axis"]

    def on_epoch(epoch, loss, network, input_mean, input_std, target_mean, target_std, ridge):
        with torch.no_grad():
            standardized = (build_features(shown_measurements, *ridge, feature_mode) - input_mean) / input_std
            prediction = network(torch.tensor(standardized)).numpy() * target_std + target_mean
        axis_errors_mm = [float(np.nanmean(np.abs(prediction[:, column] - shown_targets[:, column]))) * 1000
                          for column in (r_axis, z_axis)]
        view(epoch, loss, axis_errors_mm[0], axis_errors_mm[1], time.time() - started,
             demo.overall_accuracy(prediction, shown_targets))

    def on_limiter_start():
        print(demo.ST.paint(demo.ST.grey, "učí se specialista na bod u limiteru (strana a poloha)"), flush=True)

    return on_epoch, on_limiter_start, view


# ===================================================================================================================
# Spuštění z příkazové řádky
# ===================================================================================================================
def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feat", default="diff2", choices=["diff", "diff2"], help="diff2 přidává druhé diference")
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--all", action="store_true", help="učit na všech 149 výbojích místo 119 vývojových")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--out", default="ipp1-ipn", help="název výstupního souboru bez přípony")
    parser.add_argument("--live", action="store_true",
                        help="ukazovat učení živým grafem jako demo: ztráta a chyba osy na 30 odložených výbojích po každé epoše "
                             "(jen se měří, nikdy se na nich neučí)")
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    started = time.time()

    (table, X, Y, discharges, _), _ = F.aligned_data()
    _, development_rows, locked_rows = F.split(discharges)
    train_rows = np.arange(len(X)) if args.all else development_rows

    on_epoch = on_limiter_start = view = None
    if args.live:
        on_epoch, on_limiter_start, view = live_view(X[locked_rows], Y[locked_rows], args.feat, args.epochs, started)
    arrays = train(X[train_rows], Y[train_rows], args.feat, args.epochs, on_epoch=on_epoch, on_limiter_start=on_limiter_start)
    if view:
        view.finish()

    input_names = [name for name in table.columns if name.startswith(("IPR", "FL"))]
    scales = np.array([F.UNIT[name][0] for name in TARGETS], dtype=np.float64)
    description = {
        "input_names": input_names, "output_names": list(TARGETS), "output_units": [F.UNIT[name][1] for name in TARGETS],
        "raw_units": "positions in m, plasma current in A, shape numbers and is_limited dimensionless; the output scale turns them into mm and kA",
        "features": f"measurements divided by the plasma current (ridge on the 24 inputs), {args.feat} differences inside one row, "
                    f"and the current / {CURRENT_SCALE:g}",
        "limiter": "network with five outputs on the really limited rows: side, R/Z up, R/Z down; used where the general network says is_limited > 0.5",
        "trained_on": f"{len(np.unique(discharges[train_rows]))} discharges ({len(train_rows)} rows), seed 0, {args.epochs} epochs, Huber 0.2",
        "confidential": "weights are derived from the confidential IPP data: never for git",
    }
    MODEL_FOLDER.mkdir(parents=True, exist_ok=True)
    np.savez(MODEL_FOLDER / f"{args.out}.npz", **arrays,
             input_names=np.array(input_names), output_names=np.array(TARGETS), output_scales=scales,
             limiter_columns=np.array(F.LIMITER), plasma_current_column=np.array(PLASMA_CURRENT), is_limited_column=np.array(IS_LIMITED),
             ipn=np.array(1), ip_scale=np.array(CURRENT_SCALE), feature_mode=np.array(args.feat))
    (MODEL_FOLDER / f"{args.out}.json").write_text(json.dumps(description, indent=1) + "\n")
    print(f"wrote {MODEL_FOLDER}/{args.out}.npz, {time.time() - started:.0f} s ({description['trained_on']})")


if __name__ == "__main__":
    main()
