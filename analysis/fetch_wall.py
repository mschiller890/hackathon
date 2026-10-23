"""Download exactly one public file, the COMPASS vacuum wall outline, from the organisers' repository.

    HACKATHON_HOME=<hackathon folder> python -I analysis/fetch_wall.py [--force]

The file is `notebooks/COMPASS_stena.csv` of repo.tok.ipp.cas.cz/seidl/cvut-ml-hackaton-2026-compass (public,
the owner approved this single download). It is saved to $HACKATHON_HOME/data/raw/organizers/ and its size and
sha256 are printed. No other URL is accepted. Nothing here touches the IPP measurement data.
"""
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

ALLOWED = "https://repo.tok.ipp.cas.cz/seidl/cvut-ml-hackaton-2026-compass/-/raw/master/notebooks/COMPASS_stena.csv"
ROOT = Path(os.environ.get("HACKATHON_HOME", "."))
TARGET = ROOT / "data/raw/organizers/COMPASS_stena.csv"


def main(argv):
    url = ALLOWED
    for a in argv:
        if a.startswith("--url"):
            url = a.split("=", 1)[1] if "=" in a else ""
    if url != ALLOWED:
        sys.exit("refused: this script downloads only " + ALLOWED)
    if TARGET.exists() and "--force" not in argv:
        data = TARGET.read_bytes()
        print(f"already there: {TARGET} {len(data)} bytes sha256 {hashlib.sha256(data).hexdigest()} (use --force to fetch again)")
        return
    with urllib.request.urlopen(url, timeout=30) as r:  # one GET, public, no login
        data = r.read(1_000_000)
    head = data[:200].decode("utf-8", "replace").lower()
    if not data or "r" not in head.split("\n", 1)[0].lower():
        sys.exit("refused to save: the answer does not look like the wall outline CSV (first line: %r)" % head.split("\n", 1)[0][:60])
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(data)
    print(f"saved {TARGET} {len(data)} bytes sha256 {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main(sys.argv[1:])
