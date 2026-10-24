#!/usr/bin/env bash
# Vyzkouší už natrénovaný model a vypíše stručné shrnutí výsledku.
#
#   ./try_model.sh            shrnutí na 30 odložených výbojích (čistý i zašuměný model)
#   ./try_model.sh vstup.csv  navíc odhad na vlastním CSV (24 vstupů IPR01..16, FL01..08, sloupec discharge)
#
# Potřebuje data v data/ (README, kapitola 3) a natrénované modely v out/model/ (vytvoří je `python run.py`).
set -euo pipefail
cd "$(dirname "$0")"

# Python: proměnná PYTHON, jinak .venv v projektu, jinak python3.
if [ -n "${PYTHON:-}" ]; then PY="$PYTHON"
elif [ -x .venv/bin/python ]; then PY=.venv/bin/python
else PY=python3; fi

CLEAN=out/model/clean-model.npz
NOISY=out/model/noisy-model.npz

if [ ! -f "$CLEAN" ] || [ ! -f "$NOISY" ]; then
    echo "Chybí natrénované modely ($CLEAN, $NOISY)." >&2
    echo "Nejdřív spusťte:  $PY run.py   (asi 3 minuty)" >&2
    exit 1
fi
if [ ! -f data/equil_data.csv ] && [ ! -f data/equil_data.zip ]; then
    echo "Chybí data: dejte equil_data.csv a equil_data_noisy.csv do složky data/ (README, kapitola 3)." >&2
    exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== 1. Čistý model na 30 odložených výbojích (výboje, na kterých se neučil) =="
"$PY" analysis/error_in_mm.py --model "$CLEAN" --set locked --json "$TMP/clean.json" > "$TMP/clean.txt" 2> "$TMP/clean.err" || { cat "$TMP/clean.err" >&2; exit 1; }
"$PY" - "$TMP/clean.json" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1]))
q, p = r["quantities"], r["protocol"]
print(f"   {p['n_discharges']} výbojů, {p['n_rows']} okamžiků")
names = [("R_mag_axis", "osa R"), ("Z_mag_axis", "osa Z"), ("R_x_point", "X bod R"), ("R_strike_point_1", "dotykový bod 1 R"),
         ("R_limiter", "bod limiteru R"), ("Z_limiter", "bod limiteru Z")]
print(f"   {'veličina':<20}{'průměrná chyba':>16}{'pod 1 mm':>12}")
for key, label in names:
    if key in q:
        print(f"   {label:<20}{q[key]['mae']:>13.3f} mm{100 * q[key]['share_below_mm']['1']:>10.1f} %")
if "plasma_current" in q:
    print(f"   {'proud plazmatu':<20}{q['plasma_current']['mae']:>13.3f} kA")
if "limited_diverted" in r:
    print(f"   limiterová / divertorová konfigurace: shoda {100 * r['limited_diverted']['agreement']:.1f} %")
PYEOF

echo
echo "== 2. Zašuměná měření (dodaný zašuměný soubor, týchž 30 výbojů) =="
"$PY" - <<'PYEOF'
import pathlib, sys
sys.path.insert(0, ".")
import run
run.compare_models_on_noisy_inputs(pathlib.Path(run.HERE))
PYEOF

if [ $# -ge 1 ]; then
    echo
    echo "== 3. Odhad na vašem souboru: $1 =="
    "$PY" predict.py "$1" --model "$CLEAN" --out "$TMP/odhad.csv"
    echo "   Hotovo, prvních pět řádků odhadu:"
    head -n 6 "$TMP/odhad.csv" | cut -c1-160 | sed 's/^/   /'
    cp "$TMP/odhad.csv" ./odhad.csv && echo "   Celý odhad je v ./odhad.csv"
fi

echo
echo "Podrobně: results/error-in-mm.md (chyby s intervaly), results/final-evaluation.md (porovnání receptur)."
