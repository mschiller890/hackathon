#!/usr/bin/env python
"""Estimate the plasma shape from the 24 magnetic measurements with the shipped model. Numpy only: no torch, no scikit-learn, no pandas.

    python analysis/predict.py input.csv [--model out/model/ipp1-selected.npz] [--out estimates.csv] [--all]

input.csv: a header row and one row per time instant, with the columns IPR01 .. IPR16 (coils) and FL01 .. FL08 (flux loops) in any order, in the units of the data file
(extra columns such as `discharge` and `time` are passed through to the output). Rows are independent: the neighbouring-coil differences that the model uses are
differences between ADJACENT COILS inside a row (IPR02-IPR01 ... FL08-FL07), not between time steps, so the order of the rows does not matter and the first row is not special.

Output, one row per input row: the 16 estimated values in mm and kA (shape numbers and the limited probability dimensionless) and `is_limited_flag` (1 = limited plasma).
The X point and strike points exist only in the divertor configuration and the limiter point only in the limited one, so by default the cells that do not apply to the row are left
empty; `--all` writes all 16 numbers for every row. The values are estimates of the institute's reference reconstruction (`results/ipp1-final.md`), not measurements of the plasma.

Also printed: the time per row, for the whole file at once and row by row (the median of single-row calls, one CPU core).
"""
import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
# in the submission package the model sits in model/ next to analysis/; in the repository it is hackathon/out/model next to the repository folder
DEFAULT_MODEL = next((p for p in (_ROOT / "model" / "ipp1-selected.npz", _ROOT.parent / "out" / "model" / "ipp1-selected.npz") if p.exists()), _ROOT / "model" / "ipp1-selected.npz")
DIVERTOR_ONLY = ("R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2")
LIMITED_ONLY = ("R_limiter", "Z_limiter")


def silu(h):
    with np.errstate(over="ignore"):          # exp(-h) may overflow to inf for a large negative h; 1/inf is 0 and the result is the correct limit
        return h * (1.0 / (1.0 + np.exp(-h)))


class Model:
    """The shipped pair: a general network, a network for the limiter point, a ridge for the plasma current (see analysis/export_model.py)."""

    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.z = {k: z[k] for k in z.files}
        self.inputs = [str(v) for v in self.z["input_names"]]
        self.outputs = [str(v) for v in self.z["output_names"]]
        self.scales = self.z["output_scales"]
        self.lim_cols = [int(v) for v in self.z["limiter_columns"]]
        self.ip_col, self.cls_col = int(self.z["plasma_current_column"]), int(self.z["is_limited_column"])

    @staticmethod
    def features(x):
        """The 24 inputs plus the differences of neighbouring coils (15) and of neighbouring flux loops (7), inside each row: 46 columns."""
        return np.concatenate([x, np.diff(x[:, :16], axis=1), np.diff(x[:, 16:24], axis=1)], axis=1).astype(np.float32)

    def _net(self, tag, f):
        z = self.z
        h = (f - z[f"{tag}_mu"]) / z[f"{tag}_sd"]
        for i in range(4):
            h = h @ z[f"{tag}_W{i}"] + z[f"{tag}_b{i}"]
            if i < 3:
                h = silu(h)
        return h * z[f"{tag}_ys"] + z[f"{tag}_ym"]

    def predict(self, x):
        """(n, 24) raw inputs -> (n, 16) outputs in raw units (m, A, dimensionless), in the order of `self.outputs`."""
        x = np.asarray(x, dtype=np.float32)
        f = self.features(x)
        out = self._net("gen", f)
        out[:, self.ip_col] = x.astype(np.float64) @ self.z["ridge_w"] + self.z["ridge_b"]
        gate = np.flatnonzero(out[:, self.cls_col] > 0.5)
        if len(gate):
            out[np.ix_(gate, self.lim_cols)] = self._net("spec", f[gate])[:, self.lim_cols]
        return out

    def estimates(self, x):
        """Like predict, in the report units (mm, kA, dimensionless)."""
        return self.predict(x) * self.scales


def read_csv(path, inputs):
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [r for r in reader if r]
    missing = [c for c in inputs if c not in header]
    if missing:
        sys.exit(f"missing columns in {path}: {', '.join(missing)}")
    idx = [header.index(c) for c in inputs]
    x = np.array([[float(r[i]) for i in idx] for r in rows], dtype=np.float64)
    if not np.isfinite(x).all():
        sys.exit("the input has empty or non-numeric values")
    extra = [(c, [r[header.index(c)] for r in rows]) for c in ("discharge", "time") if c in header]
    return x, extra


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="CSV with the columns IPR01..IPR16 and FL01..FL08")
    ap.add_argument("--model", default=str(DEFAULT_MODEL), help="the exported model (default: model/ipp1-selected.npz next to analysis/, else out/model/ipp1-selected.npz next to the repository)")
    ap.add_argument("--out", help="write the estimates to this CSV instead of printing the first rows")
    ap.add_argument("--all", action="store_true", help="write all 16 numbers for every row (default: leave the cells that do not apply to the configuration empty)")
    args = ap.parse_args()
    if not Path(args.model).exists():
        sys.exit(f"model not found: {args.model} (make it with analysis/export_model.py)")
    model = Model(args.model)
    x, extra = read_csv(args.input, model.inputs)
    t0 = time.perf_counter()
    est = model.estimates(x)
    batch = time.perf_counter() - t0
    singles = []
    for i in range(min(len(x), 500)):
        t = time.perf_counter()
        model.estimates(x[i:i + 1])
        singles.append(time.perf_counter() - t)
    flag = (est[:, model.cls_col] > 0.5).astype(int)
    names = [f"{t}_{u}" if u else t for t, u in zip(model.outputs, ["mm" if t.startswith(("R_", "Z_")) else "kA" if t == "plasma_current" else "" for t in model.outputs])]
    header = [c for c, _ in extra] + names + ["is_limited_flag"]
    cells = []
    for r in range(len(x)):
        row = [vals[r] for _, vals in extra]
        for j, t in enumerate(model.outputs):
            skip = not args.all and ((flag[r] and t in DIVERTOR_ONLY) or (not flag[r] and t in LIMITED_ONLY))
            row.append("" if skip else f"{est[r, j]:.8g}")
        cells.append(row + [str(flag[r])])
    if args.out:
        with open(args.out, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(cells)
        print(f"wrote {len(cells)} rows to {args.out}")
    else:
        print(",".join(header))
        for row in cells[:10]:
            print(",".join(row))
        if len(cells) > 10:
            print(f"... ({len(cells) - 10} more rows; use --out to write them all)")
    print(f"time per row: {1e6 * batch / len(x):.1f} us for the whole file at once, {1e6 * float(np.median(singles)):.1f} us as the median of single-row calls (one CPU core, numpy only)", file=sys.stderr)


if __name__ == "__main__":
    main()
