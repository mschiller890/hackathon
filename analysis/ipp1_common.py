"""Společný kód pro úlohu IPP 1: načtení dat, základní neuronová síť, ridge regrese a hodnocení.

Data se čtou ze složky data/ (nebo z $HACKATHON_HOME/data), výsledky se ukládají do out/.
Řádky jednoho výboje jsou téměř kopie, proto se data vždy dělí po celých výbojích, nikdy po řádcích.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

# --- kde jsou data a kam se píše ---------------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("HACKATHON_HOME") or REPO)  # bez HACKATHON_HOME je domovem samotný repozitář
OUT = ROOT / "out"

# Data hledáme v data/ a pro jistotu i v původní struktuře z archivu od organizátorů.
_DATA_CANDIDATES = (ROOT / "data", ROOT / "data/raw/ipp1-magnetic/uloha_1-magneticka_data")
DATA = next((folder for folder in _DATA_CANDIDATES if (folder / "equil_data.csv").exists()), ROOT / "data")
if not DATA.exists():
    hackathon_home = os.environ.get("HACKATHON_HOME")
    raise SystemExit(
        f"Složka s daty nenalezena: {DATA}\n"
        "Dejte equil_data.csv a equil_data_noisy.csv do složky data/ v repozitáři, nebo nastavte HACKATHON_HOME "
        f"na složku, která data/ obsahuje (HACKATHON_HOME je {'nenastaveno' if hackathon_home is None else hackathon_home})."
    )
OUT.mkdir(parents=True, exist_ok=True)

# --- co se odhaduje ----------------------------------------------------------------------------------------------
# Některé veličiny existují jen v jedné konfiguraci plazmatu a jinde jsou v datech prázdné (NaN):
# bod X a dotykové body jen v divertorové, bod limiteru (R_limiter, Z_limiter) jen v limiterové.
TARGETS = [
    "plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity",
    "triangularity_upper", "triangularity_lower", "R_x_point", "Z_x_point",
    "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2",
    "R_limiter", "Z_limiter", "is_limited",
]

# Pro každou veličinu (násobek, jednotka), který převede hodnotu z dat do jednotky v tabulkách:
# polohy z metrů na milimetry, proud z ampér na kiloampéry, tvarová čísla beze změny.
UNIT = {name: (1000.0, "mm") for name in TARGETS if name.startswith(("R_", "Z_"))}
UNIT.update({
    "plasma_current": (1e-3, "kA"),
    "elongation": (1.0, ""), "triangularity": (1.0, ""),
    "triangularity_upper": (1.0, ""), "triangularity_lower": (1.0, ""),
    "is_limited": (1.0, ""),
})

EPSILON = 1e-9  # přičítá se ke směrodatné odchylce, aby se nikdy nedělilo nulou
BATCH_SIZE = 512


def load(noisy=False):
    """Načte data a vrátí (tabulka, vstupy, cíle, čísla výbojů, maska).

    Cíle mají NaN tam, kde veličina neexistuje. Maska je opak: True tam, kde cíl existuje.
    """
    csv_name = "equil_data_noisy.csv" if noisy else "equil_data.csv"
    table = pd.read_csv(DATA / csv_name)
    table["is_limited"] = table["is_limited"].astype(float)
    input_columns = [name for name in table.columns if name.startswith(("IPR", "FL"))]  # 16 cívek + 8 smyček
    inputs = table[input_columns].values.astype(np.float32)
    targets = table[TARGETS].values.astype(np.float32)
    return table, inputs, targets, table["discharge"].values, ~np.isnan(targets)


def group_folds(inputs, targets, discharges, n_splits=5):
    """Rozdělí řádky na n_splits dílů tak, aby žádný výboj nebyl zároveň v učení i v testu."""
    return list(GroupKFold(n_splits=n_splits).split(inputs, targets, discharges))


class Net(nn.Module):
    """Základní síť: vstup -> 256 -> 256 -> 128 -> výstup, mezi vrstvami aktivace SiLU."""

    def __init__(self, n_inputs, n_outputs, width=256):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(n_inputs, width), nn.SiLU(),
            nn.Linear(width, width), nn.SiLU(),
            nn.Linear(width, width // 2), nn.SiLU(),
            nn.Linear(width // 2, n_outputs),
        )

    def forward(self, x):
        return self.layers(x)


def fit_mlp(x_train, y_train, exists_train, epochs=60, seed=0):
    """Natrénuje základní síť na standardizovaných vstupech i cílech.

    Chyba se počítá jen tam, kde cíl existuje (exists_train), chybějící hodnoty ji neovlivní.
    Vrací (predict, síť, (střední hodnota vstupů, směrodatná odchylka vstupů)); predict převede
    surové vstupy na surové cíle.
    """
    torch.manual_seed(seed)

    # Standardizace: vstupy i cíle odečteme průměr a vydělíme směrodatnou odchylkou.
    x_mean, x_std = x_train.mean(0), x_train.std(0) + EPSILON
    y_mean, y_std = np.nanmean(y_train, 0), np.nanstd(y_train, 0) + EPSILON
    x_tensor = torch.tensor((x_train - x_mean) / x_std)
    y_tensor = torch.tensor(np.nan_to_num((y_train - y_mean) / y_std))  # chybějící cíle -> 0, maska je vyřadí
    exists_tensor = torch.tensor(exists_train.astype(np.float32))

    network = Net(x_tensor.shape[1], y_tensor.shape[1])
    optimizer = torch.optim.AdamW(network.parameters(), lr=2e-3, weight_decay=1e-4)
    steps = epochs * ((len(x_tensor) + BATCH_SIZE - 1) // BATCH_SIZE)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=3e-3, total_steps=steps)

    for _ in range(epochs):
        shuffled = torch.randperm(len(x_tensor))
        for start in range(0, len(x_tensor), BATCH_SIZE):
            batch = shuffled[start:start + BATCH_SIZE]
            squared_error = (network(x_tensor[batch]) - y_tensor[batch]) ** 2
            loss = (squared_error * exists_tensor[batch]).sum() / exists_tensor[batch].sum()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
    network.eval()

    def predict(x):
        with torch.no_grad():
            return network(torch.tensor((x - x_mean) / x_std)).numpy() * y_std + y_mean

    return predict, network, (x_mean, x_std)


def fit_ridge(x_train, y_train, exists_train):
    """Pro každý cíl zvlášť lineární (ridge) regrese na standardizovaných vstupech. Vrací funkci predict."""
    x_mean, x_std = x_train.mean(0), x_train.std(0) + EPSILON
    models = []
    for target in range(y_train.shape[1]):
        rows = exists_train[:, target]
        model = Ridge(alpha=1.0).fit((x_train[rows] - x_mean) / x_std, y_train[rows, target])
        models.append(model)
    return lambda x: np.column_stack([model.predict((x - x_mean) / x_std) for model in models])


def score(prediction, targets, exists):
    """Hodnocení po jednotlivých cílech: střední chyba v mm (kA), R², chyba vůči rozptylu a u is_limited přesnost."""
    result = {}
    for column, name in enumerate(TARGETS):
        rows = exists[:, column]
        error = prediction[rows, column] - targets[rows, column]
        scale, unit = UNIT[name]
        spread = targets[rows, column].std()
        sum_of_squares = ((targets[rows, column] - targets[rows, column].mean()) ** 2).sum()
        result[name] = {
            "mae": float(np.abs(error).mean() * scale),
            "unit": unit,
            "r2": float(1 - (error ** 2).sum() / sum_of_squares),
            "nrmse": float(np.sqrt((error ** 2).mean()) / spread),
        }
    limited = exists[:, -1]
    result["is_limited"]["accuracy"] = float(((prediction[limited, -1] > 0.5) == (targets[limited, -1] > 0.5)).mean())
    return result


def score_extended(prediction, targets, exists):
    """Jako score, ale podrobněji: medián, RMSE, 95. a 99. percentil a nejhorší řádek (vše přes všechny dané řádky)."""
    result = {}
    for column, name in enumerate(TARGETS):
        rows = exists[:, column]
        error = prediction[rows, column].astype(np.float64) - targets[rows, column]
        absolute = np.abs(error) * UNIT[name][0]
        sum_of_squares = ((targets[rows, column] - targets[rows, column].mean()) ** 2).sum()
        result[name] = {
            "mae": float(absolute.mean()),
            "median": float(np.median(absolute)),
            "rmse": float(np.sqrt((absolute ** 2).mean())),
            "p95": float(np.percentile(absolute, 95)),
            "p99": float(np.percentile(absolute, 99)),
            "max": float(absolute.max()),
            "unit": UNIT[name][1],
            "nrmse": float(np.sqrt((error ** 2).mean()) / targets[rows, column].std()),
            "r2": float(1 - (error ** 2).sum() / sum_of_squares),
        }
    return result
