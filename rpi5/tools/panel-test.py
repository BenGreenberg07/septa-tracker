#!/usr/bin/env python3
"""Test every pixel of the 4x4 array: dead pixels, dead rows, wiring, colour.

Run it through try-script.sh so it cannot fight the display service:

    ./pi/try-script.sh rpi5/tools/panel-test.py           cycle all patterns
    ./pi/try-script.sh rpi5/tools/panel-test.py --hold red
    ./pi/try-script.sh rpi5/tools/panel-test.py --seconds 15
    ./pi/try-script.sh rpi5/tools/panel-test.py --list

What to look for, pattern by pattern:

  panels   Each of the 16 panels numbered 1-16, left to right, top to bottom,
           with a border. Every number must be upright, in order, and inside
           its own box. If they are jumbled or mirrored, the pixel map or the
           panel wiring is wrong, not the pixels.
  white    Any pixel that stays dark is dead. Any that looks pink, green or
           blue has one dead colour channel.
  red/green/blue
           One channel at a time, which is how you tell a fully dead pixel
           from a single dead channel. A pixel dark in all three is dead.
  gray     Half brightness. Catches pixels that only fail when not driven
           hard, and shows up brightness differences between panels, which
           usually means a power problem rather than a pixel problem.
  black    Everything must be off. Anything still lit is stuck on.
  checker  Alternating single pixels. Neighbours bleeding into each other
           show up here.
  rows/cols
           Alternating single lines. A whole missing line is a shift register
           or a ribbon cable, not a pixel.
  sweep    One lit line walking down, then across, to pin down exactly which
           row or column is out.

The patterns are drawn on a normal canvas and pushed through the display's own
to_framebuffer(), so this tests the same path the real board uses.
"""

import argparse
import importlib.util
import os
import sys
import time

import numpy as np
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
RPI5 = os.path.dirname(HERE)
sys.path.insert(0, RPI5)

# Reuse the display's geometry, pixel map and transforms rather than copying
# them: the map is easy to get subtly wrong, and one copy cannot drift.
spec = importlib.util.spec_from_file_location(
    "board", os.path.join(RPI5, "prod", "swarthmore-tracked.py"))
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)

W, H = D.WIDTH, D.HEIGHT
PANEL_W, PANEL_H = 64, 32
COLS, ROWS = W // PANEL_W, H // PANEL_H


def blank(color=(0, 0, 0)):
    return Image.new("RGB", (W, H), color)


def p_panels():
    img = blank()
    d = ImageDraw.Draw(img)
    font = D._font(16)
    for r in range(ROWS):
        for c in range(COLS):
            n = r * COLS + c + 1
            x0, y0 = c * PANEL_W, r * PANEL_H
            d.rectangle([x0, y0, x0 + PANEL_W - 1, y0 + PANEL_H - 1],
                        outline=(0, 90, 120))
            label = str(n)
            tw = d.textlength(label, font=font)
            d.text((x0 + (PANEL_W - tw) / 2, y0 + 7), label,
                   font=font, fill=(255, 255, 255))
    return img


def p_solid(color):
    return lambda: blank(color)


def p_checker():
    a = np.indices((H, W)).sum(axis=0) % 2
    return Image.fromarray((a[:, :, None] * np.uint8([255, 255, 255])).astype(np.uint8))


def p_lines(horizontal):
    a = np.zeros((H, W, 3), np.uint8)
    if horizontal:
        a[::2, :, :] = 255
    else:
        a[:, ::2, :] = 255
    return Image.fromarray(a)


PATTERNS = [
    ("panels", p_panels),
    ("white",  p_solid((255, 255, 255))),
    ("red",    p_solid((255, 0, 0))),
    ("green",  p_solid((0, 255, 0))),
    ("blue",   p_solid((0, 0, 255))),
    ("gray",   p_solid((128, 128, 128))),
    ("black",  p_solid((0, 0, 0))),
    ("checker", p_checker),
    ("rows",   lambda: p_lines(True)),
    ("cols",   lambda: p_lines(False)),
]


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--hold", metavar="PATTERN",
                    help="show one pattern and stay on it")
    ap.add_argument("--seconds", type=float, default=6,
                    help="seconds per pattern when cycling (default 6)")
    ap.add_argument("--list", action="store_true", help="list pattern names")
    args = ap.parse_args()

    names = [n for n, _ in PATTERNS] + ["sweep"]
    if args.list:
        print("  ".join(names))
        return
    if args.hold and args.hold not in names:
        print(f"No pattern '{args.hold}'. Try: {'  '.join(names)}")
        sys.exit(1)

    m1, across = D.build_map(W, 64, D.N_ADDR_LINES, True, row_offset=64)
    m2, _ = D.build_map(W, 64, D.N_ADDR_LINES, True, row_offset=0)
    framebuffer = D.to_framebuffer(blank())
    matrix = D.piomatter.PioMatter(
        colorspace=D.piomatter.Colorspace.RGB888Packed,
        pinout=D.piomatter.Pinout.Active3,
        framebuffer=framebuffer,
        geometry=D.piomatter.Geometry(
            width=W, height=H, n_addr_lines=D.N_ADDR_LINES,
            map=D.combine_maps(m2, m1, across), n_lanes=D.N_LANES,
            n_planes=D.N_PLANES, n_temporal_planes=D.N_TEMPORAL_PLANES),
    )

    def show(img):
        framebuffer[:] = D.to_framebuffer(img)
        matrix.show()

    def sweep():
        """One lit line walking down, then across."""
        for y in range(H):
            img = blank(); ImageDraw.Draw(img).line([(0, y), (W, y)], fill=(255, 255, 255))
            show(img); time.sleep(0.05)
        for x in range(W):
            img = blank(); ImageDraw.Draw(img).line([(x, 0), (x, H)], fill=(255, 255, 255))
            show(img); time.sleep(0.03)

    print(f"{'Simulator' if not D.HARDWARE else 'Panels'}: Ctrl-C to stop.\n")
    try:
        if args.hold:
            print(f"Holding: {args.hold}")
            if args.hold == "sweep":
                while True:
                    sweep()
            show(dict(PATTERNS)[args.hold]())
            while True:
                matrix.show()
                time.sleep(1)
        while True:
            for name, make in PATTERNS:
                print(f"  {name}")
                show(make())
                end = time.time() + args.seconds
                while time.time() < end:
                    matrix.show()
                    time.sleep(0.2)
            print("  sweep")
            sweep()
    except KeyboardInterrupt:
        show(blank())
        print("\nStopped; panels cleared.")


if __name__ == "__main__":
    main()
