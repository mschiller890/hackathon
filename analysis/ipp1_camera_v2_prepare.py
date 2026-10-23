#!/usr/bin/env python
"""Grey 96x128 cache of the matched camera frames for analysis/ipp1_camera_v2.py (outside git: the frames are confidential).

    HACKATHON_HOME=... nice -n 10 ~/.venvs/hackathon/bin/python -I analysis/ipp1_camera_v2_prepare.py

The frames and labels are those of ipp1_camera_prepare.py (the same matching, 115,872 frames of 78 discharges); here every frame is read again from the JPEG, converted to grey and
scaled from 640x500 to 128 wide and 96 high. Needs out/ipp1-camera-labels.npz (ipp1_camera_prepare.py) and the extracted frames. Writes out/ipp1-camera-v2-grey.npy (uint8 N x 96 x 128).
"""
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_camera_prepare as P
from ipp1_common import OUT, load

GREY = OUT / "ipp1-camera-v2-grey.npy"
H, W = 96, 128


def decode(name):
    im = Image.open(P.CAM / "jpeg" / name)
    im.draft("L", (160, 125))
    im = im.convert("L")
    return np.asarray(im.resize((W, H), Image.BOX))


def decode_chunk(args):
    start, names = args
    out = np.load(GREY, mmap_mode="r+")
    for i, name in enumerate(names):
        out[start + i] = decode(name)
    out.flush()
    return len(names)


def main():
    started = time.perf_counter()
    df, x, y, _, _ = load()
    frames = pd.read_csv(P.CAM / "camera_data.csv")
    fi, lo, hi, w = P.bracket_frames(frames, df)
    kept = frames.iloc[fi].reset_index(drop=True)
    lab = np.load(OUT / "ipp1-camera-labels.npz")
    assert len(kept) == len(lab["discharge"]) and np.array_equal(kept.discharge.to_numpy(), lab["discharge"]) and np.allclose(kept.time.to_numpy(), lab["time"]), "frames differ from the labels"
    np.lib.format.open_memmap(GREY, mode="w+", dtype=np.uint8, shape=(len(kept), H, W)).flush()
    names = kept.filename.tolist()
    with Pool(6) as pool:
        done = sum(pool.imap_unordered(decode_chunk, [(s, names[s:s + 1000]) for s in range(0, len(names), 1000)]))
    assert done == len(names)
    print(f"wrote {GREY.name}: {len(names)} frames of {H}x{W}, {time.perf_counter() - started:.0f} s", flush=True)


if __name__ == "__main__":
    main()
