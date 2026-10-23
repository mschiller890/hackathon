#!/usr/bin/env python
"""Capture stills and a short clip of the viewer through headless Chrome (DevTools protocol), then cut the clip with ffmpeg.

    ~/.venvs/hackathon/bin/python viewer/record.py --stills presentation/assets --clip out/viewer-demo.mp4 --discharge 123

Needs viewer/data.js (analysis/export_viewer_data.py) and ffmpeg. The images show one discharge of the IPP data: keep them
inside the team (CON-001). The clip is not committed.
"""
import argparse
import base64
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGE = Path(__file__).resolve().parent / "index.html"
# name, discharge, position in the discharge (0 to 1), noise mode
STILLS = [("viewer-start-limited", 123, 0.03, False), ("viewer-middle-divertor", 123, 0.5, False),
          ("viewer-rough-end", 11, 1.0, False), ("viewer-noise", 4, 0.45, True)]


class Page:
    def __init__(self, port=9341):
        self.dir = tempfile.mkdtemp()
        self.proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", f"--remote-debugging-port={port}", f"--remote-allow-origins=http://127.0.0.1:{port}", f"--user-data-dir={self.dir}",
                                      "--window-size=1920,1080", "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1))
                url = next(t["webSocketDebuggerUrl"] for t in targets if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise SystemExit("Chrome did not start")
        self.ws, self.n = websocket.create_connection(url, max_size=None), 0
        self.call("Emulation.setDeviceMetricsOverride", width=1920, height=1080, deviceScaleFactor=1, mobile=False)
        self.call("Page.navigate", url=PAGE.as_uri())
        for _ in range(120):
            if self.js("typeof render === 'function' && !!window.VIEWER") is True:
                break
            time.sleep(0.5)

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                return msg.get("result", msg)

    def js(self, code):
        r = self.call("Runtime.evaluate", expression=code, returnByValue=True)
        return r.get("result", {}).get("value")

    def show(self, discharge, noise=False, frac=0.0):
        self.js(f"(() => {{ state.noise = {str(noise).lower()}; document.querySelector('#showNoise').checked = state.noise;"
                f" selectDischarge(D.discharges.findIndex(d => d.id === {discharge})); state.i = Math.round({frac} * (cur().n - 1)); render(); }})()")

    def shot(self, path):
        Path(path).write_bytes(base64.b64decode(self.call("Page.captureScreenshot", format="png")["data"]))

    def close(self):
        self.proc.terminate()
        shutil.rmtree(self.dir, ignore_errors=True)


ap = argparse.ArgumentParser()
ap.add_argument("--stills", help="folder for the still images")
ap.add_argument("--clip", help="output mp4")
ap.add_argument("--discharge", type=int, default=123)
ap.add_argument("--seconds", type=float, default=15)
args = ap.parse_args()
page = Page()
try:
    if args.stills:
        Path(args.stills).mkdir(parents=True, exist_ok=True)
        for name, d, frac, noise in STILLS:
            page.show(d, noise, frac)
            time.sleep(0.3)
            page.shot(Path(args.stills) / f"{name}.png")
            print("wrote", name)
    if args.clip:
        page.show(args.discharge)
        frames = page.js("cur().n")
        tmp = Path(tempfile.mkdtemp())
        for i in range(frames):
            page.js(f"state.i = {i}; render();")
            page.shot(tmp / f"f{i:04d}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", f"{frames / args.seconds:.4f}", "-i", str(tmp / "f%04d.png"),
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", args.clip], check=True)
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"wrote {args.clip}: {frames} frames over {args.seconds:g} s")
finally:
    page.close()
