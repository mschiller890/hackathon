#!/usr/bin/env python
"""Camera data for IPP task 1: safe extraction, profile, matching to equil_data.csv, small cached arrays.

    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_camera_prepare.py [--size 64 64]

Reads the camera zip from $HACKATHON_HOME/data/raw/ipp1-photron-zip/, extracts it into the new folder
$HACKATHON_HOME/data/raw/ipp1-photron/ and writes uint8 arrays to $HACKATHON_HOME/out/cloud-camera/ (outside git).
Only aggregate numbers are printed: the data are confidential.

Matching: every frame carries a discharge number and a time. The equilibrium (inputs and targets of equil_data.csv)
is interpolated linearly in time between the two bracketing rows of the same discharge. A frame outside the time
range of its discharge is dropped (no extrapolation). A target is NaN when either bracketing row is NaN, so the
masked loss ignores it; the flag is_limited takes the nearest row instead of a value between 0 and 1.
"""
import argparse
import re
import stat
import sys
import zipfile
from multiprocessing import Pool
from pathlib import Path, PurePosixPath

import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
from ipp1_common import OUT, ROOT, TARGETS, load

ZIP_DIR = ROOT / "data/raw/ipp1-photron-zip"
EXTRACT_DIR = ROOT / "data/raw/ipp1-photron"
CACHE = OUT / "cloud-camera"
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
MAX_UNPACKED_BYTES = 20 * 2 ** 30  # zip bomb guard


def safe_extract(zip_path, dest):
    """Extract into a new or empty folder after rejecting absolute, parent and symlink entries."""
    dest = Path(dest)
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"{dest} is not empty; extraction needs its own empty folder")
    with zipfile.ZipFile(zip_path) as zf:
        total = 0
        for info in zf.infolist():
            name = PurePosixPath(info.filename.replace("\\", "/"))
            if name.is_absolute() or ".." in name.parts or re.match(r"^[A-Za-z]:", info.filename):
                raise SystemExit(f"unsafe zip entry name: {info.filename!r}")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise SystemExit(f"symlink entry in zip: {info.filename!r}")
            total += info.file_size
        if total > MAX_UNPACKED_BYTES:
            raise SystemExit(f"unpacked size {total / 2 ** 30:.1f} GiB exceeds the guard")
        print(f"zip: {len(zf.infolist())} entries, {total / 2 ** 20:.0f} MiB unpacked; names are safe", flush=True)
        dest.mkdir(parents=True, exist_ok=True)
        zf.extractall(dest)


def pick_column(columns, patterns, what, override):
    if override:
        if override not in columns:
            raise SystemExit(f"--col-{what} {override!r} is not a column; columns: {list(columns)}")
        return override
    hits = [c for c in columns if any(re.search(p, str(c), re.I) for p in patterns)]
    if len(hits) != 1:
        raise SystemExit(f"cannot choose the {what} column from {list(columns)}; candidates {hits}; use --col-{what}")
    return hits[0]


def read_mapping(folder, args):
    csvs = sorted(Path(folder).rglob("*.csv"))
    if len(csvs) != 1:
        raise SystemExit(f"expected one CSV in {folder}, found {[c.name for c in csvs]}")
    df = pd.read_csv(csvs[0])
    print(f"mapping CSV {csvs[0].name}: {len(df)} rows, columns {list(df.columns)}", flush=True)
    cols = df.columns
    file_hits = [c for c in cols if df[c].astype(str).str.lower().str.endswith(IMAGE_SUFFIXES).mean() > 0.9]
    col_file = args.col_file or (file_hits[0] if len(file_hits) == 1 else None)
    if col_file is None:
        raise SystemExit(f"cannot find the image file column in {list(cols)}; use --col-file")
    col_dis = pick_column(cols, [r"discharge", r"shot", r"^sh$"], "discharge", args.col_discharge)
    col_time = pick_column(cols, [r"^time", r"^t$", r"_t$", r"time"], "time", args.col_time)
    print(f"columns used: file={col_file!r} discharge={col_dis!r} time={col_time!r}", flush=True)
    return pd.DataFrame({"file": df[col_file].astype(str), "discharge": df[col_dis].astype(np.int64),
                         "time": df[col_time].astype(np.float64)})


def resolve_paths(folder, rel_names):
    """Map the names in the CSV to files below folder (by relative path, else by unique base name)."""
    files = [p for p in Path(folder).rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES]
    by_rel = {p.relative_to(folder).as_posix(): p for p in files}
    by_name = {}
    for p in files:
        by_name.setdefault(p.name, []).append(p)
    paths, missing = [], 0
    for name in rel_names:
        name = name.replace("\\", "/")
        p = by_rel.get(name)
        if p is None:
            cands = by_name.get(Path(name).name, [])
            p = cands[0] if len(cands) == 1 else None
        paths.append(p)
        missing += p is None
    print(f"images on disk: {len(files)}; names in CSV: {len(rel_names)}; without a file: {missing}", flush=True)
    return paths


def pick_time_scale(cam_t, cam_d, eq):
    """Return the factor that puts camera time into the unit of equil_data.csv (the share of frames inside range)."""
    lo = eq.groupby("discharge")["time"].min()
    hi = eq.groupby("discharge")["time"].max()
    inside = {}
    for s in (1.0, 1e-3, 1e-6, 1e3):
        t = cam_t * s
        ok = (t >= lo.reindex(cam_d).values - 1e-9) & (t <= hi.reindex(cam_d).values + 1e-9)
        inside[s] = float(np.mean(ok))
    print("share of frames inside the equilibrium time range by time scale: "
          + ", ".join(f"x{s:g}: {v:.3f}" for s, v in inside.items()), flush=True)
    if max(inside.values()) < 0.5:
        raise SystemExit("camera times do not overlap the equilibrium times under any unit; check the columns")
    # A too small factor also "fits" whenever the equilibrium range starts near zero, so of the factors that
    # cover almost as well as the best one, the largest is the right one.
    return max(s for s, v in inside.items() if v >= 0.9 * max(inside.values()))


def interpolate_equilibrium(eq, cam_d, cam_t, columns, nearest_columns, max_gap_factor=5.0):
    """Linear interpolation of eq[columns] at (discharge, time).

    Returns (values, inside, gap_dropped). inside is False for a frame outside the time range of its discharge or
    between two equilibrium rows further apart than max_gap_factor times the median row spacing of that discharge
    (the organizers warn that some frames have no close equilibrium time); gap_dropped marks the latter.
    """
    out = np.full((len(cam_d), len(columns)), np.nan, dtype=np.float64)
    inside = np.zeros(len(cam_d), dtype=bool)
    gap_dropped = np.zeros(len(cam_d), dtype=bool)
    near = np.array([c in nearest_columns for c in columns])
    for d, rows in eq.groupby("discharge"):
        sel = np.flatnonzero(cam_d == d)
        if sel.size == 0:
            continue
        rows = rows.sort_values("time").drop_duplicates("time")
        te = rows["time"].values
        ve = rows[columns].values.astype(np.float64)
        t = cam_t[sel]
        ok = (t >= te[0] - 1e-9) & (t <= te[-1] + 1e-9)
        if len(te) < 2 or not ok.any():
            continue
        i1 = np.clip(np.searchsorted(te, t), 1, len(te) - 1)
        i0 = i1 - 1
        wide = (te[i1] - te[i0]) > max_gap_factor * np.median(np.diff(te))
        gap_dropped[sel[ok & wide]] = True
        ok &= ~wide
        w = np.clip((t - te[i0]) / (te[i1] - te[i0]), 0.0, 1.0)[:, None]
        v = np.where(w == 0, ve[i0], np.where(w == 1, ve[i1], ve[i0] * (1 - w) + ve[i1] * w))
        v[:, near] = np.where(w < 0.5, ve[i0], ve[i1])[:, near]
        out[sel[ok]] = v[ok]
        inside[sel[ok]] = True
    return out, inside, gap_dropped


def load_image(job):
    """Decode one frame to (rgb uint8 HxWx3, grey uint8 HxW, original size, mean colour spread)."""
    path, (h, w) = job
    try:
        with Image.open(path) as im:
            size = im.size
            im.draft("RGB", (2 * w, 2 * h))  # JPEG: decode at a reduced scale, much faster
            rgb = np.asarray(im.convert("RGB").resize((w, h), Image.BOX))
    except Exception:
        return None
    grey = np.asarray(Image.fromarray(rgb).convert("L"))
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    return rgb, grey, size, float((np.abs(r - g) + np.abs(g - b)).mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", type=Path, default=None, help="camera zip (default: the only zip in ipp1-photron-zip)")
    ap.add_argument("--extract-dir", type=Path, default=EXTRACT_DIR)
    ap.add_argument("--size", type=int, nargs=2, default=[64, 64], metavar=("H", "W"))
    ap.add_argument("--col-file")
    ap.add_argument("--col-discharge")
    ap.add_argument("--col-time")
    ap.add_argument("--time-scale", type=float, help="factor from camera time to the unit of equil_data.csv")
    ap.add_argument("--max-gap-factor", type=float, default=5.0, help="drop frames between equilibrium rows this many median spacings apart")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="debug: use only the first N frames")
    args = ap.parse_args()
    h, w = args.size

    if not args.extract_dir.exists() or not any(args.extract_dir.iterdir()):
        zips = [args.zip] if args.zip else sorted(ZIP_DIR.glob("*.zip"))
        if len(zips) != 1:
            raise SystemExit(f"expected one zip in {ZIP_DIR}, found {zips}")
        safe_extract(zips[0], args.extract_dir)
    cam = read_mapping(args.extract_dir, args)
    cam["path"] = resolve_paths(args.extract_dir, cam["file"].tolist())
    cam = cam[cam["path"].notna()].reset_index(drop=True)
    if args.limit:
        cam = cam.iloc[:args.limit]
    print(f"frames: {len(cam)}, discharges: {cam['discharge'].nunique()}, frames per discharge "
          f"min/median/max: {cam.groupby('discharge').size().agg(['min', 'median', 'max']).tolist()}", flush=True)

    eq, X, Y, _, _ = load()
    x_cols = [c for c in eq.columns if c.startswith(("IPR", "FL"))]
    cam_t = cam["time"].values * (args.time_scale or pick_time_scale(cam["time"].values, cam["discharge"].values, eq))
    cam_d = cam["discharge"].values
    print(f"discharges with camera frames that exist in equil_data.csv: {len(set(cam_d) & set(eq['discharge']))} "
          f"of {len(set(cam_d))}", flush=True)
    vals, inside, gap_dropped = interpolate_equilibrium(eq, cam_d, cam_t, x_cols + TARGETS, {"is_limited"}, args.max_gap_factor)
    print(f"frames inside the time range of their discharge and without a wide gap: {inside.sum()} of {len(cam)} "
          f"({gap_dropped.sum()} dropped for a gap wider than {args.max_gap_factor:g} median row spacings)", flush=True)
    keep = inside & np.isfinite(vals[:, :len(x_cols)]).all(axis=1)
    print(f"frames with all {len(x_cols)} magnetic inputs finite: {keep.sum()}", flush=True)

    idx = np.flatnonzero(keep)
    jobs = [(cam["path"].iloc[i], (h, w)) for i in idx]
    rgb = np.empty((len(jobs), h, w, 3), np.uint8)
    grey = np.empty((len(jobs), h, w), np.uint8)
    spread, sizes, bad = np.zeros(len(jobs)), {}, []
    with Pool(args.workers) as pool:
        for n, res in enumerate(pool.imap(load_image, jobs, chunksize=64)):
            if res is None:
                bad.append(n)
                continue
            rgb[n], grey[n], size, spread[n] = res
            sizes[size] = sizes.get(size, 0) + 1
            if (n + 1) % 5000 == 0:
                print(f"decoded {n + 1}/{len(jobs)}", flush=True)
    print(f"original resolutions (width, height): {dict(sorted(sizes.items(), key=lambda kv: -kv[1])[:5])}", flush=True)
    print(f"decode failures: {len(bad)}", flush=True)
    good = np.setdiff1d(np.arange(len(jobs)), bad)
    if len(bad) > 0.01 * len(jobs):
        raise SystemExit("more than 1 % of the frames failed to decode")
    print(f"mean |R-G|+|G-B| over frames (0 means the images carry no colour): {spread[good].mean():.3f}; "
          f"share of frames above 1.0: {(spread[good] > 1.0).mean():.3f}", flush=True)

    sel = idx[good]
    m = vals[sel, len(x_cols):]  # sel indexes the rows of cam and vals; good only indexes the decoded jobs
    x_cache = vals[sel, :len(x_cols)].astype(np.float32)
    assert len(sel) == len(rgb[good]) == len(m) and np.isfinite(x_cache).all(), "labels and images are misaligned"
    CACHE.mkdir(parents=True, exist_ok=True)
    tag = f"{h}x{w}"
    np.save(CACHE / f"rgb_{tag}.npy", rgb[good])
    np.save(CACHE / f"grey_{tag}.npy", grey[good])
    np.savez(CACHE / f"meta_{tag}.npz", discharge=cam_d[sel], time=cam_t[sel], x=x_cache,
             y=m.astype(np.float32), mask=~np.isnan(m), x_cols=np.array(x_cols), targets=np.array(TARGETS))
    print(f"cached {len(good)} frames of {len(set(cam_d[sel]))} discharges as {tag} in {CACHE} "
          f"({rgb[good].nbytes / 2 ** 20:.0f} MiB colour, {grey[good].nbytes / 2 ** 20:.0f} MiB grey)", flush=True)
    for j, t in enumerate(TARGETS):
        print(f"  {t}: {int((~np.isnan(m[:, j])).sum())} frames have the target", flush=True)


if __name__ == "__main__":
    main()
