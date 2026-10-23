#!/usr/bin/env python
"""Lane R: match camera frames to equilibrium labels and cache small RGB arrays outside git.

Labels are linear interpolations of equil_data.csv inside each discharge. A frame is dropped when its time lies
outside the discharge's labelled range (no extrapolation) or inside a gap of the labels longer than MAX_GAP,
because the shape can change a lot over a long gap. A conditional target (X point, strike points, limiter point)
is kept only when both neighbouring rows have it; `is_limited` takes the nearest row.

Images: JPEG decoded at 1/4 scale (160x125), cropped to 112x112 px so that the whole vessel view fits in every
discharge (the left edge of the view varies between 115 and 198 px at full resolution across discharges).

Run: HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/ipp1_camera_prepare.py
Writes out/ipp1-camera-images.npy (uint8 N x 112 x 112 x 3) and out/ipp1-camera-labels.npz
(targets y, mask, the magnetic inputs x interpolated to the frame times, discharge, time, mode).
"""
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipp1_common import OUT, ROOT, TARGETS, load

CAM = ROOT / "data/raw/ipp1-photron/uloha_1-photron"
IMAGES = OUT / "ipp1-camera-images.npy"
LABELS = OUT / "ipp1-camera-labels.npz"
CROP = (24, 6, 136, 118)  # left, top, right, bottom in the 1/4 scale image
SIZE = 112
MAX_GAP = 0.01  # relative time; the median label spacing is 0.0034


def bracket_frames(frames, df):
    """For every usable frame return the two neighbouring label rows and the weight of the later one.

    Returns (frame_index, lo_row, hi_row, w): arrays over the kept frames, rows index `df`.
    """
    times = df.time.to_numpy()
    out = []
    for discharge, rows in df.groupby("discharge").indices.items():
        rows = rows[np.argsort(times[rows], kind="stable")]
        t = times[rows]
        fi = np.flatnonzero(frames.discharge.to_numpy() == discharge)
        ft = frames.time.to_numpy()[fi]
        inside = (ft >= t[0]) & (ft <= t[-1])
        fi, ft = fi[inside], ft[inside]
        hi = np.clip(np.searchsorted(t, ft, side="left"), 1, len(t) - 1)
        lo = hi - 1
        ok = (t[hi] - t[lo]) <= MAX_GAP
        fi, ft, lo, hi = fi[ok], ft[ok], lo[ok], hi[ok]
        out.append((fi, rows[lo], rows[hi], (ft - t[lo]) / (t[hi] - t[lo])))
    fi, lo, hi, w = (np.concatenate(a) for a in zip(*out))
    order = np.argsort(fi)
    return fi[order], lo[order], hi[order], w[order].astype(np.float32)[:, None]


def interpolate(a, lo, hi, w):
    return (1 - w) * a[lo] + w * a[hi]  # NaN stays NaN if either neighbour is missing


def decode(name):
    im = Image.open(CAM / "jpeg" / name)
    im.draft("RGB", (160, 125))
    im = im.convert("RGB")
    if im.size != (160, 125):
        im = im.resize((160, 125), Image.BILINEAR)
    return np.asarray(im.crop(CROP))


def decode_chunk(args):
    start, names = args
    out = np.load(IMAGES, mmap_mode="r+")
    for i, name in enumerate(names):
        out[start + i] = decode(name)
    out.flush()
    return len(names)


def main():
    started = time.perf_counter()
    df, x, y, _, _ = load()
    frames = pd.read_csv(CAM / "camera_data.csv")
    assert not frames.filename.duplicated().any()
    fi, lo, hi, w = bracket_frames(frames, df)
    kept = frames.iloc[fi].reset_index(drop=True)
    lab = interpolate(y, lo, hi, w)
    lim = TARGETS.index("is_limited")
    lab[:, lim] = y[np.where(w[:, 0] < .5, lo, hi), lim]  # a class: take the nearest row
    mask, xf = ~np.isnan(lab), interpolate(x, lo, hi, w)
    print(f"frames {len(frames)}, kept {len(fi)} ({len(fi) / len(frames):.1%}), discharges {kept.discharge.nunique()}", flush=True)
    print("labels present per target:", {t: f"{mask[:, j].mean():.1%}" for j, t in enumerate(TARGETS)}, flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    np.lib.format.open_memmap(IMAGES, mode="w+", dtype=np.uint8, shape=(len(kept), SIZE, SIZE, 3)).flush()
    names = kept.filename.tolist()
    chunks = [(s, names[s:s + 1000]) for s in range(0, len(names), 1000)]
    with Pool(8) as pool:
        done = sum(pool.imap_unordered(decode_chunk, chunks))
    assert done == len(names)
    np.savez(LABELS, y=lab, x=xf, mask=mask, discharge=kept.discharge.to_numpy(), time=kept.time.to_numpy(),
             mode=kept["mode"].to_numpy().astype(str), targets=np.array(TARGETS))
    print(f"wrote {IMAGES.name} and {LABELS.name} in {time.perf_counter() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
