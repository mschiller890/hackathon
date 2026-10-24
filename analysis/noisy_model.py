#!/usr/bin/env python
"""Natrénuje a uloží zašuměný model: model pro zašuměná měření, který predict.py spustí jen s numpy.
(Model pro čistá měření vyrábí clean_model.py.)

Zašuměný model se učí jako závěrečná fáze experimentu ipp1_noise_window.py (čísla jsou v results/ipp1-noise-window.md):
základní síť z common.fit_mlp (60 epoch, semínko 0) na všech 119 vývojových výbojích. Každý řádek tam je dvakrát:
čistý a poškozený šumem a driftem (final_evaluation.corrupt, šum 0,15 a drift 0,15 směrodatné odchylky vstupu). Vstupem sítě
nejsou jen měření v daném okamžiku, ale měření z posledních 5 okamžiků téhož výboje (aktuální a čtyři předchozí),
což šum částečně zprůměruje. Poškozuje se PŘED sestavením oken, ať mají okna šum konzistentní.

    python analysis/noisy_model.py       (asi 20 s)

Uloží out/model/ipp1-noisy.npz a .json. VÁHY JSOU ODVOZENÉ Z DŮVĚRNÝCH DAT IPP: složka out/ je v .gitignore.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # predict.py v kořeni repozitáře
import final_evaluation as F
from common import OUT, fit_mlp
from predict import Model, window_rows

MODEL_FOLDER = OUT / "model"
WINDOW = 5  # kolik posledních řádků téhož výboje vidí jeden odhad


def main():
    torch.set_num_threads(4)
    assert not F.SMOKE
    (table, X, Y, discharges, exists), noisy_X = F.aligned_data()
    _, development_rows, locked_rows = F.split(discharges)

    input_names = [name for name in table.columns if name.startswith(("IPR", "FL"))]
    expected_names = [f"IPR{i:02d}" for i in range(1, 17)] + [f"FL{i:02d}" for i in range(1, 9)]
    assert input_names == expected_names, "vstupy v datech nejsou v očekávaném pořadí IPR01..16, FL01..08"
    scales = np.array([F.UNIT[name][0] for name in F.TARGETS], dtype=np.float64)
    units = [F.UNIT[name][1] for name in F.TARGETS]

    MODEL_FOLDER.mkdir(parents=True, exist_ok=True)
    train_and_export(table, X, noisy_X, Y, discharges, exists, development_rows, locked_rows, input_names, scales, units)


def train_and_export(table, X, noisy_X, Y, discharges, exists, development_rows, locked_rows, input_names, scales, units):
    """Natrénuje zašuměný model na vývojových výbojích a uloží ho."""
    torch.set_num_threads(4)
    started = time.time()
    relative_time = table.time.to_numpy()
    train_rows = development_rows

    # window[i] = čísla řádků, které odhad pro řádek i vidí (řádek sám a čtyři předchozí téhož výboje)
    window = window_rows(discharges, relative_time, WINDOW)

    # Poškozená kopie vstupů. Poškozují se jen učicí řádky; okna učicích řádků leží celá uvnitř vývojových výbojů.
    corrupted_X = X.copy()
    corrupted_X[train_rows] = F.corrupt(X[train_rows], discharges[train_rows], relative_time[train_rows],
                                        X[train_rows].std(axis=0), F.NOISE, F.DRIFT, F.AUG_SEED + 50)
    clean_windows = X[window[train_rows]].reshape(len(train_rows), -1)
    corrupted_windows = corrupted_X[window[train_rows]].reshape(len(train_rows), -1)
    x_train = np.concatenate([clean_windows, corrupted_windows]).astype(np.float32)
    y_train, exists_train = np.tile(Y[train_rows], (2, 1)), np.tile(exists[train_rows], (2, 1))

    predict, network, (input_mean, input_std) = fit_mlp(x_train, y_train, exists_train, 60, seed=0)
    linear_layers = [layer for layer in network.layers if isinstance(layer, nn.Linear)]
    assert len(linear_layers) == 4 and all(isinstance(layer, (nn.Linear, nn.SiLU)) for layer in network.layers)

    # Váhy a standardizace ve formátu, který čte predict.py (vstupy x výstupy, tedy matice transponovaná proti torchi).
    arrays = {}
    for i, layer in enumerate(linear_layers):
        arrays[f"gen_W{i}"] = layer.weight.detach().numpy().T.astype(np.float32)
        arrays[f"gen_b{i}"] = layer.bias.detach().numpy().astype(np.float32)
    arrays["gen_mu"], arrays["gen_sd"] = np.asarray(input_mean, np.float32), np.asarray(input_std, np.float32)
    arrays["gen_ym"] = np.nanmean(y_train, 0).astype(np.float32)
    arrays["gen_ys"] = (np.nanstd(y_train, 0) + 1e-9).astype(np.float32)

    path = MODEL_FOLDER / "ipp1-noisy.npz"
    np.savez(path, **arrays, input_names=np.array(input_names), output_names=np.array(F.TARGETS), output_scales=scales,
             window_rows=np.array(WINDOW), limiter_columns=np.array(F.LIMITER),
             plasma_current_column=np.array(F.TARGET_COLUMN["plasma_current"]),
             is_limited_column=np.array(F.TARGET_COLUMN["is_limited"]))

    # Kontrola: výpočet v numpy (predict.py) musí dát totéž co síť v torchi (na zašuměných odložených řádcích v oknech).
    checked_rows = locked_rows[:2000]
    checked_x = noisy_X[window[checked_rows]].reshape(len(checked_rows), -1).astype(np.float32)
    reference = predict(checked_x)
    relative_difference = np.abs(Model(path).predict(checked_x) - reference) / (np.abs(reference) + 1e-6)
    worst_median_difference = np.nanmax(np.median(relative_difference, 0))
    assert worst_median_difference < 1e-4, worst_median_difference

    description = {
        "input_names": input_names, "output_names": list(F.TARGETS), "output_units": units,
        "output_scale_to_unit": scales.tolist(),
        "raw_units": "positions in m, plasma current in A, shape numbers and is_limited dimensionless; the output scale turns them into mm and kA",
        "window_rows": WINDOW,
        "window_rule": f"each estimate uses the 24 inputs of rows t, t-1, .. t-{WINDOW - 1} of the SAME discharge ordered by time, stacked in that order "
                       f"({24 * WINDOW} columns, current row first); where the discharge has fewer earlier rows its first row is repeated; never a later row. "
                       "k counts rows, so the input must have the sampling interval of the training data",
        "features": "the stacked raw inputs only (no neighbouring-coil differences, no ridge, no limiter network): one network answers all 16 outputs",
        "activation": "SiLU", "hidden_layers": [256, 256, 128],
        "trained_on": f"the {len(np.unique(discharges[development_rows]))} development discharges ({len(development_rows)} rows) twice: clean, and one copy corrupted per row with "
                      f"noise {F.NOISE} and drift {F.DRIFT} of each input's SD (final_evaluation.corrupt, seed {F.AUG_SEED + 50}) before windowing; "
                      "baseline network of common.fit_mlp, 60 epochs, MSE, seed 0 (config base_aug_stack5 of ipp1_noise_window.py, locked stage)",
        "evidence": "results/ipp1-noise-window.md: on the 30 locked discharges with the provided noisy inputs, axis MAE R 1.85 mm and Z 1.25 mm",
        "numpy_check": f"median relative difference numpy vs torch on 2000 locked noisy rows, max over outputs: {worst_median_difference:.1e}",
        "confidential": "weights are derived from the confidential IPP data: for the submission package, never for git",
    }
    (MODEL_FOLDER / "ipp1-noisy.json").write_text(json.dumps(description, indent=1) + "\n")
    size = sum(file.stat().st_size for file in MODEL_FOLDER.glob("ipp1-noisy.*"))
    print(f"wrote {MODEL_FOLDER}/ipp1-noisy.npz and .json (noise model, window {WINDOW} rows), "
          f"{size / 1e6:.2f} MB in total, {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
