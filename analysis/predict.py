#!/usr/bin/env python
"""Estimate the plasma shape from the 24 magnetic measurements with the shipped model. Numpy only: no torch, no scikit-learn, no pandas.

    python analysis/predict.py input.csv [--model out/model/ipp1-selected.npz] [--out estimates.csv] [--all]
    python analysis/predict.py input.csv --noisy [--out estimates.csv] [--all]        noisy measurements: the noise-trained model ipp1-noisy.npz

input.csv: a header row and one row per time instant, with the columns IPR01 .. IPR16 (coils) and FL01 .. FL08 (flux loops) in any order, in the units of the data file
(extra columns such as `discharge` and `time` are passed through to the output). Default model: rows are independent: the neighbouring-coil differences that the model
uses are differences between ADJACENT COILS inside a row (IPR02-IPR01 ... FL08-FL07), not between time steps, so the order of the rows does not matter and the first row is not special.

--noisy uses the second model, trained on clean rows plus a copy with noise and drift added (analysis/export_model.py, results/ipp1-noise-window.md). It is NOT row by row:
each estimate sees the measurements of the last 5 instants of the same discharge (rows t, t-1, .. t-4 in `time` order; the first rows of a discharge repeat its first row; never
a later row), so the file needs the columns `discharge` and `time`. Rows may come in any order; the output keeps the input order. The window counts rows, so the file must have
the sampling interval of the training data.

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
# in the submission package the model sits in model/ next to analysis/, or in out/model/ where run.py exports it; in the repository it is hackathon/out/model next to the repository folder
def _default(name):
    return next((p for p in (_ROOT / "model" / name, _ROOT / "out" / "model" / name, _ROOT.parent / "out" / "model" / name) if p.exists()), _ROOT / "model" / name)


DEFAULT_MODEL, DEFAULT_NOISY = _default("ipp1-selected.npz"), _default("ipp1-noisy.npz")
DIVERTOR_ONLY = ("R_x_point", "Z_x_point", "R_strike_point_1", "Z_strike_point_1", "R_strike_point_2", "Z_strike_point_2")
LIMITED_ONLY = ("R_limiter", "Z_limiter")


def silu(h):
    with np.errstate(over="ignore"):          # exp(-h) may overflow to inf for a large negative h; 1/inf is 0 and the result is the correct limit
        return h * (1.0 / (1.0 + np.exp(-h)))


def window_rows(discharge, time, k):
    """(n, k) row indices of the causal window: column j is the row j instants earlier in the same discharge by `time` (clipped at the
    discharge's first row), never a later row. Rows may come in any order. The training of the noise model uses this same function."""
    _, g = np.unique(np.asarray(discharge), return_inverse=True)
    n = len(g)
    order = np.lexsort((np.asarray(time, dtype=np.float64), g))
    gs = g[order]
    start = np.r_[0, np.flatnonzero(gs[1:] != gs[:-1]) + 1]
    first = np.repeat(start, np.diff(np.r_[start, n]))
    rank = np.arange(n) - first
    w = np.stack([order[first + np.maximum(rank - j, 0)] for j in range(k)], 1)
    out = np.empty_like(w)
    out[order] = w
    return out


class Model:
    """The shipped selected model: a general network, a network for the limiter point, a ridge for the plasma current, rows independent,
    and, if the file has one, a separate network that answers R_mag_axis and Z_mag_axis (keys axis_*).
    Or the noise model (ipp1-noisy.npz): one network on the inputs of the last `window` rows of the discharge, see estimates_noisy.
    Both are made by analysis/export_model.py."""

    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.z = {k: z[k] for k in z.files}
        self.inputs = [str(v) for v in self.z["input_names"]]
        self.outputs = [str(v) for v in self.z["output_names"]]
        self.scales = self.z["output_scales"]
        self.lim_cols = [int(v) for v in self.z["limiter_columns"]]
        self.ip_col, self.cls_col = int(self.z["plasma_current_column"]), int(self.z["is_limited_column"])
        self.window = int(self.z["window_rows"]) if "window_rows" in self.z else 1   # only the noise model has a window
        self.axis_cols = [int(v) for v in self.z["axis_columns"]] if "axis_columns" in self.z else None
        self.depth = {tag: sum(k.startswith(f"{tag}_W") for k in self.z) for tag in ("gen", "spec", "axis")}
        self.ipn = "ipn" in self.z        # the model of analysis/ipn_model.py: measurements divided by the plasma current
        self.feature_mode = str(self.z["feature_mode"]) if self.ipn else "diff"

    @staticmethod
    def features(x):
        """The 24 inputs plus the differences of neighbouring coils (15) and of neighbouring flux loops (7), inside each row: 46 columns."""
        return np.concatenate([x, np.diff(x[:, :16], axis=1), np.diff(x[:, 16:24], axis=1)], axis=1).astype(np.float32)

    def ipn_features(self, x):
        """ipn model: the measurements divided by the plasma current (the ridge on the 24 inputs, signed), their differences inside the row
        (diff2 adds the second differences) and the current / ip_scale. Made by analysis/ipn_model.features."""
        scale = float(self.z["ip_scale"])
        cur = x.astype(np.float64) @ self.z["ridge_w"] + float(self.z["ridge_b"])
        xs = x * (scale / cur)[:, None]
        parts = [xs, np.diff(xs[:, :16], axis=1), np.diff(xs[:, 16:24], axis=1)]
        if self.feature_mode == "diff2":
            parts += [np.diff(xs[:, :16], 2, axis=1), np.diff(xs[:, 16:24], 2, axis=1)]
        return np.concatenate(parts + [(cur / scale)[:, None]], axis=1).astype(np.float32)

    def _net(self, tag, f):
        z = self.z
        h = (f - z[f"{tag}_mu"]) / z[f"{tag}_sd"]
        n = self.depth[tag]
        for i in range(n):
            h = h @ z[f"{tag}_W{i}"] + z[f"{tag}_b{i}"]
            if i < n - 1:
                h = silu(h)
        return h * z[f"{tag}_ys"] + z[f"{tag}_ym"]

    def predict(self, x):
        """(n, 24) raw inputs -> (n, 16) outputs in raw units (m, A, dimensionless), in the order of `self.outputs`.
        Noise model: (n, 24 * window) stacked rows t, t-1, ... (see estimates_noisy), one network for all 16 outputs."""
        x = np.asarray(x, dtype=np.float32)
        if self.window > 1:
            return self._net("gen", x)
        f = self.ipn_features(x) if self.ipn else self.features(x)
        out = self._net("gen", f)
        if self.axis_cols:
            out[:, self.axis_cols] = self._net("axis", f)
        out[:, self.ip_col] = x.astype(np.float64) @ self.z["ridge_w"] + self.z["ridge_b"]
        gate = np.flatnonzero(out[:, self.cls_col] > 0.5)
        if len(gate):
            sp = self._net("spec", f[gate])
            if sp.shape[1] == 5:       # ipn model: side (+up / -down), then R, Z when up and R, Z when down
                out[np.ix_(gate, self.lim_cols)] = np.where((sp[:, 0] > 0)[:, None], sp[:, 1:3], sp[:, 3:5])
            else:
                out[np.ix_(gate, self.lim_cols)] = sp[:, self.lim_cols]
        return out

    def estimates(self, x):
        """Like predict, in the report units (mm, kA, dimensionless)."""
        return self.predict(x) * self.scales

    def stack(self, x, discharge, time):
        """(n, 24) rows of whole discharges in any order -> (n, 24 * window): each row's inputs followed by those of the rows before it."""
        x = np.asarray(x, dtype=np.float32)
        return x[window_rows(discharge, time, self.window)].reshape(len(x), -1)

    def estimates_noisy(self, x, discharge, time):
        """The noise model on (n, 24) rows with their discharge and time; report units, rows in the input order."""
        return self.estimates(self.stack(x, discharge, time))


def read_csv(path, inputs):
    """Bad input stops with one line naming the row as a spreadsheet numbers it (the header is row 1), exit code 1."""
    with open(path, newline="", encoding="utf-8-sig") as fh:  # utf-8-sig: Excel's "CSV UTF-8" starts with a byte order mark
        reader = csv.reader(fh)
        header = next(reader, None)
        rows = [(reader.line_num, r) for r in reader if any(v.strip() for v in r)]
    if header is None:
        sys.exit(f"{path}: empty file")
    header = [h.strip() for h in header]
    missing = [c for c in inputs if c not in header]
    if missing:
        sys.exit(f"missing columns in {path}: {', '.join(missing)}")
    if not rows:
        sys.exit(f"{path}: no data rows after the header")
    idx = [header.index(c) for c in inputs]
    x = np.empty((len(rows), len(idx)))
    for k, (line, r) in enumerate(rows):
        if len(r) < len(header):
            sys.exit(f"{path}: row {line}: {len(r)} values, the header has {len(header)} columns")
        for j, i in enumerate(idx):
            try:
                x[k, j] = float(r[i])
            except ValueError:
                x[k, j] = np.nan
            if not np.isfinite(x[k, j]):
                sys.exit(f"{path}: row {line}: column {inputs[j]} is empty or not a number ({r[i]!r})")
    extra = [(c, [r[header.index(c)] for _, r in rows]) for c in ("discharge", "time") if c in header]
    return x, extra


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="CSV with the columns IPR01..IPR16 and FL01..FL08")
    ap.add_argument("--model", default=None, help="the exported model (default: model/ipp1-selected.npz or out/model/ipp1-selected.npz next to analysis/, else out/model/ipp1-selected.npz next to the repository; with --noisy ipp1-noisy.npz in the same places)")
    ap.add_argument("--noisy", action="store_true", help="noisy measurements: the noise-trained model on the last 5 instants of each discharge (needs the columns discharge and time)")
    ap.add_argument("--out", help="write the estimates to this CSV instead of printing the first rows")
    ap.add_argument("--all", action="store_true", help="write all 16 numbers for every row (default: leave the cells that do not apply to the configuration empty)")
    args = ap.parse_args()
    args.model = args.model or str(DEFAULT_NOISY if args.noisy else DEFAULT_MODEL)
    if not Path(args.model).exists():
        sys.exit(f"model not found: {args.model} (make it with analysis/export_model.py)")
    if not Path(args.input).is_file():
        sys.exit(f"input file not found: {args.input}")
    model = Model(args.model)
    if args.noisy != (model.window > 1):
        sys.exit(f"{args.model} is {'not ' if args.noisy else ''}the noise model: " + ("use ipp1-noisy.npz with --noisy" if args.noisy else "run it with --noisy"))
    x, extra = read_csv(args.input, model.inputs)
    rows = x
    if args.noisy:
        cols = dict(extra)
        missing = [c for c in ("discharge", "time") if c not in cols]
        if missing:
            sys.exit(f"--noisy needs the columns discharge and time (each estimate uses the last {model.window} instants of the same discharge); missing in {args.input}: {', '.join(missing)}")
        try:
            times = np.array([float(v) for v in cols["time"]])
        except ValueError:
            times = np.array([np.nan])
        if not np.isfinite(times).all():
            sys.exit(f"{args.input}: column time must be a number in every row")
        rows = model.stack(x, cols["discharge"], times)
    t0 = time.perf_counter()
    est = model.estimates_noisy(x, cols["discharge"], times) if args.noisy else model.estimates(x)
    batch = time.perf_counter() - t0
    singles = []
    for i in range(min(len(rows), 500)):
        t = time.perf_counter()
        model.estimates(rows[i:i + 1])
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
    print(f"time per row: {1e6 * batch / len(x):.1f} us for the whole file at once, {1e6 * float(np.median(singles)):.1f} us as the median of single-row calls (one CPU core, numpy only"
          f"{'; noise model: the network on one row of 5 stacked instants' if args.noisy else ''})", file=sys.stderr)


if __name__ == "__main__":
    main()
