"""Desktop stand-in for adafruit_blinka_raspberry_pi5_piomatter.

Presents the same Geometry / PioMatter / Colorspace / Pinout surface the Pi 5
library does, but instead of driving HUB75 panels it writes each frame to a PNG
and serves it from a small HTTP page that refreshes itself. That lets the
production display script be developed and reviewed on a laptop.
"""

import enum
import http.server
import io
import os
import threading

import numpy as np
from PIL import Image

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_frames")
SCALE = 4          # on-screen pixels per LED
GAP = 1            # dark gutter between LEDs, to read like a real panel


class Colorspace(enum.Enum):
    RGB888Packed = "RGB888Packed"
    RGB888 = "RGB888"


class Pinout(enum.Enum):
    Active3 = "Active3"
    AdafruitMatrixBonnet = "AdafruitMatrixBonnet"


class Geometry:
    def __init__(self, width, height, n_addr_lines=4, map=None,
                 n_lanes=2, n_planes=4, n_temporal_planes=1, **kw):
        self.width = width
        self.height = height
        self.n_addr_lines = n_addr_lines
        self.map = map
        self.n_lanes = n_lanes
        self.n_planes = n_planes
        self.n_temporal_planes = n_temporal_planes


_PAGE = b"""<!doctype html><title>SEPTA panel simulator</title>
<style>
 body{background:#15171b;margin:0;display:flex;flex-direction:column;
      align-items:center;justify-content:center;height:100vh;
      font:13px ui-monospace,Menlo,monospace;color:#8d949e}
 img{image-rendering:pixelated;border:10px solid #d8dade;border-radius:4px;
     box-shadow:0 18px 50px #0009}
 p{margin:14px 0 0}
</style>
<img id=f src="/frame.png">
<p>256 x 128 &middot; 16 panels &middot; simulated</p>
<script>setInterval(()=>{document.getElementById('f').src='/frame.png?'+Date.now()},1000)</script>
"""


class _Handler(http.server.BaseHTTPRequestHandler):
    matter = None

    def do_GET(self):
        if self.path.startswith("/frame.png"):
            png = self.matter.png_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(png)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(png)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(_PAGE)))
            self.end_headers()
            self.wfile.write(_PAGE)

    def log_message(self, *a):
        pass


class PioMatter:
    """Frame sink: keeps the latest framebuffer, renders it on demand."""

    def __init__(self, colorspace=None, pinout=None, framebuffer=None,
                 geometry=None, serve=True, port=8800, save_png=True):
        self.framebuffer = framebuffer
        self.geometry = geometry
        self.save_png = save_png
        self._lock = threading.Lock()
        self._png = None
        os.makedirs(OUT_DIR, exist_ok=True)
        self.png_path = os.path.join(OUT_DIR, "latest.png")
        self.port = port
        if serve:
            self._serve()

    def _serve(self):
        _Handler.matter = self
        self._httpd = http.server.ThreadingHTTPServer(("127.0.0.1", self.port), _Handler)
        t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        t.start()
        print(f"Panel simulator: http://127.0.0.1:{self.port}")

    def _upscale(self, arr):
        """Blow each LED up to a lit square on a dark grid."""
        h, w, _ = arr.shape
        cell = SCALE + GAP
        out = np.zeros((h * cell, w * cell, 3), dtype=np.uint8)
        big = np.repeat(np.repeat(arr, SCALE, axis=0), SCALE, axis=1)
        for y in range(h):
            for_y = y * cell
            out[for_y:for_y + SCALE, :] = 0
        # Place each LED block, leaving the gutter dark.
        ys = (np.arange(h * SCALE) // SCALE) * cell + (np.arange(h * SCALE) % SCALE)
        xs = (np.arange(w * SCALE) // SCALE) * cell + (np.arange(w * SCALE) % SCALE)
        out[np.ix_(ys, xs)] = big
        return out

    def show(self):
        arr = np.asarray(self.framebuffer)
        if arr.ndim == 1:
            arr = arr.reshape((self.geometry.height, self.geometry.width, 3))
        img = Image.fromarray(self._upscale(arr.astype(np.uint8)), "RGB")
        buf = io.BytesIO()
        img.save(buf, "PNG")
        with self._lock:
            self._png = buf.getvalue()
        if self.save_png:
            with open(self.png_path, "wb") as f:
                f.write(self._png)

    def png_bytes(self):
        with self._lock:
            return self._png or b""
