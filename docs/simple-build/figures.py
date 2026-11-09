#!/usr/bin/env python3
"""Pictures for the simple case build guide (fig-*.svg next to this file).

    /opt/homebrew/bin/python3 docs/simple-build/figures.py

Dimensions are in inches and use the guide's example sheet, 44 x 24 in., in a 6 in. deep box.
The 3-D views use a cabinet projection: the front face is drawn true to
shape, and depth recedes up and to the right at about half scale.
"""

import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "svg.fonttype": "path"})

# example build: sheet 44 x 24, box 6 deep
W, H, D = 44.0, 24.0, 6.0
T = 0.12                 # 1/16 in. sheet, drawn a little thicker so it reads
LIP = 1.0                # the folded lips on every wall
VX = (3, 13, 23, 33)     # vent windows: 8 x 2-1/2, y = 3 to 5.5 from the front
VESA_W, VESA_H = 23.62, 15.75   # 600 x 400 mm

INK = "#1d1d1f"
ALU = "#c9ced6"
ANGLE = "#8f97a3"
NEW = "#f28c28"          # the part a step adds
SHEET = "#bfe3f2"
PANEL = "#2b2b2b"
PSU = "#e9e9e9"
PI = "#3f8f4f"
BRICK = "#c96f4a"
MORTAR = "#efe7da"
AIR = "#2a7fbf"
MUTED = "#6b6b6b"
WARN = "#b3261e"
OK = "#2d6a3e"
EARTH = "#2e8b57"

K = 0.55                 # depth scale
ANG = math.radians(32)


def proj(x, y, z):
    return (x + y * K * math.cos(ANG), z + y * K * math.sin(ANG))


def shade(hexcol, f):
    hexcol = hexcol.lstrip("#")
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * f))) for c in (r, g, b))


class Scene:
    """Cuboids drawn far-to-near so nearer ones cover farther ones."""

    def __init__(self):
        self.items = []

    def box(self, x, y, z, dx, dy, dz, color, alpha=1.0, lw=0.6):
        self.items.append((x, y, z, dx, dy, dz, color, alpha, lw))

    def draw(self, ax):
        def key(it):
            x, y, z, dx, dy, dz = it[:6]
            return (-(y + dy / 2), (x + dx / 2) * 0.001 + (z + dz / 2) * 0.001)
        for x, y, z, dx, dy, dz, col, a, lw in sorted(self.items, key=key):
            x1, y1, z1 = x + dx, y + dy, z + dz
            top = [(x, y, z1), (x1, y, z1), (x1, y1, z1), (x, y1, z1)]
            right = [(x1, y, z), (x1, y1, z), (x1, y1, z1), (x1, y, z1)]
            front = [(x, y, z), (x1, y, z), (x1, y, z1), (x, y, z1)]
            for pts, f in ((top, 1.12), (right, 0.80), (front, 1.0)):
                ax.add_patch(Polygon([proj(*p) for p in pts], closed=True,
                                     fc=shade(col, f), ec=INK, lw=lw, alpha=a,
                                     joinstyle="round"))


def canvas(w, h, xlim, ylim):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    return fig, ax


def tag(ax, xy, n, color=NEW, r=1.15):
    ax.add_patch(Circle(xy, r, fc=color, ec="white", lw=1.2, zorder=30))
    ax.text(*xy, str(n), ha="center", va="center", color="white",
            fontsize=8, weight="bold", zorder=31)


def note(ax, xy, txy, s, ha="left", color=INK, size=8):
    ax.annotate(s, xy=xy, xytext=txy, ha=ha, va="center", fontsize=size,
                color=color, zorder=40,
                arrowprops=dict(arrowstyle="-", lw=0.7, color=MUTED, shrinkA=2, shrinkB=1))


def arrow(ax, a, b, color=INK, lw=1.4, z=35):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=10,
                                 lw=lw, color=color, zorder=z))


def dim(ax, a, b, s, off=(0, -1.2), size=7):
    ax.annotate("", xy=a, xytext=b, arrowprops=dict(arrowstyle="<->", lw=0.6, color=MUTED))
    ax.text((a[0] + b[0]) / 2 + off[0], (a[1] + b[1]) / 2 + off[1], s, ha="center",
            va="center", fontsize=size, color=MUTED)


def save(fig, name):
    fig.savefig(os.path.join(HERE, name), bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print("wrote", name)


# ------------------------------------------------------------ box pieces
# x across (0..W), z up (0..H), y into the box (0 = front edge, D = back).

def rim(s, color=ALU, lips=True):
    s.box(0, 0, 0, W, D, T, color)
    s.box(0, 0, H - T, W, D, T, color)
    s.box(0, 0, T, T, D, H - 2 * T, color)
    s.box(W - T, 0, T, T, D, H - 2 * T, color)
    ys = (D - T, 0) if lips else (D - T,)
    for y in ys:
        s.box(0, y, T, W, T, LIP, color)
        s.box(0, y, H - T - LIP, W, T, LIP, color)
        s.box(T, y, T + LIP, LIP, T, H - 2 * T - 2 * LIP, color)
        s.box(W - T - LIP, y, T + LIP, LIP, T, H - 2 * T - 2 * LIP, color)


def back(s, color=ALU, y=D):
    s.box(0, y, 0, W, T, H, color)


def rails(s, color=ANGLE):
    L = W - 2 * T - 0.4
    s.box(T + 0.2, 1.25, H - T - 0.15, L, 1.5, 0.15, color)
    s.box(T + 0.2, 1.25, H - T - 1.65, L, 0.15, 1.5, color)
    s.box(T + 0.2, 1.25, T, L, 1.5, 0.15, color)
    s.box(T + 0.2, 1.25, T + 0.15, L, 0.15, 1.5, color)


def panels(s, color=PANEL):
    s.box(1.85, 0.25, 1.9, 40.3, 1.0, 20.2, color)


def clamp_frame(s, y=0, color=ANGLE):
    s.box(0, y - 0.15, H - 1, W, 0.15, 1, color)
    s.box(0, y - 0.15, 0, W, 0.15, 1, color)
    s.box(0, y - 0.15, 1, 1, 0.15, H - 2, color)
    s.box(W - 1, y - 0.15, 1, 1, 0.15, H - 2, color)
    s.box(0, y - 0.15, H, W, 1.0, 0.12, color)
    s.box(W, y - 0.15, 0, 0.12, 1.0, H, color)


# ---------------------------------------------------------------- figures

def fig_overview():
    fig, ax = canvas(7.4, 3.9, (-24, 74), (-6, 34))
    s = Scene()
    back(s, y=D + 9)
    rim(s)
    rails(s)
    panels(s)
    s.box(0, -6, 0, W, 0.12, H, SHEET, alpha=0.55)
    clamp_frame(s, y=-12)
    s.draw(ax)
    note(ax, proj(W, D + 9, H - 3), (W + 10, H + 6), "Flat back panel, 1/16 in.")
    note(ax, proj(W, 2.5, 12), (W + 10, 13), "4 walls: CNC-cut 1/16 in.\nsheet, folded into channels")
    note(ax, proj(42, 0.6, 18), (W + 10, 6), "LED panels on 2 rails")
    note(ax, proj(3, -6, 4), (-23.5, 6), "Your plastic sheet")
    note(ax, proj(0, -12, 14), (-23.5, 17), "Clamp frame\n(the service door)")
    save(fig, "fig-overview.svg")


def fig_mounted():
    fig, ax = canvas(7.2, 4.6, (-27, 43), (-9, 33))
    ax.add_patch(Rectangle((-8, -9), 8, 42, fc=BRICK, ec=INK, lw=0.8))
    for z in range(-9, 33, 3):
        ax.plot([-8, 0], [z, z], color=MORTAR, lw=1.3)
    bx = 1.25
    ax.add_patch(Rectangle((0, 1.55), 0.16, 20.9, fc=NEW, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((bx - 0.35, 2.5), 0.35, 19, fc=NEW, ec=INK, lw=0.6))
    ax.add_patch(Polygon([(0.16, 20.5), (bx - 0.35, 20.5), (bx - 0.35, 21.2), (0.16, 21.2)], fc=NEW, ec=INK, lw=0.5))
    ax.add_patch(Polygon([(0.16, 3.0), (bx - 0.35, 3.0), (bx - 0.35, 3.7), (0.16, 3.7)], fc=NEW, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((bx, 0), D + T, H, fc=ALU, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((bx + 0.14, 0.14), D + T - 0.28, H - 0.28, fc="white", ec=INK, lw=0.5))
    ax.add_patch(Rectangle((bx + D + T, 0), 0.15, H, fc=SHEET, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((bx + D + T - 1.25, 1.9), 1.0, 20.2, fc=PANEL, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((bx + 0.14, 8), 2.0, 8.5, fc=PSU, ec=INK, lw=0.6))
    ax.text(bx + 1.14, 12.2, "PSU", rotation=90, ha="center", va="center", fontsize=6.5)
    ax.add_patch(Rectangle((bx + 0.14, 2.6), 1.4, 3.2, fc=PI, ec=INK, lw=0.6))
    for zz in (20.1, 3.9):
        ax.add_patch(Rectangle((-2.6, zz - 0.13), 2.8, 0.26, fc="#5a6270", ec=INK, lw=0.4))
    ax.add_patch(Rectangle((bx + 0.14, 12 + VESA_H / 2 - 0.1), 1.5, 0.2, fc=ANGLE, ec=INK, lw=0.4))
    ax.add_patch(Rectangle((bx + 0.14, 12 - VESA_H / 2 - 0.1), 1.5, 0.2, fc=ANGLE, ec=INK, lw=0.4))
    ax0 = bx + 3.2
    arrow(ax, (ax0, -5.5), (ax0, -0.4), AIR)
    arrow(ax, (ax0, 2), (ax0, 21.5), AIR)
    arrow(ax, (ax0, H - 0.2), (ax0, H + 4.5), AIR)
    note(ax, (0.08, 19), (-26.5, H + 5.5), "TV mount wall plate, on\nstainless sleeve anchors")
    note(ax, (bx - 0.2, 10), (-26.5, 11), "mount arms: bolted to the\ncase, hooked on the plate")
    note(ax, (bx + 0.9, 12 + VESA_H / 2), (bx + 14, H + 1.5), "1/8 in. backing bars\ninside, for the 4 mount bolts")
    note(ax, (bx + D + T + 0.1, 12), (bx + 14, 13), "your plastic sheet")
    note(ax, (bx + D - 0.6, 17), (bx + 14, 18.2), "LED panels")
    note(ax, (ax0, 0), (bx + 14, 2), "printed vents, top and bottom,\nwith mesh on the inside")
    note(ax, (bx + D * 0.5, H), (bx + 14, H + 6.5), "under the station canopy")
    dim(ax, (bx, -7.3), (bx + D + T, -7.3), "6 in.", off=(0, -1.1))
    dim(ax, (0, -3.5), (bx, -3.5), "", off=(0, 0))
    ax.text(-0.5, -3.5, "1-1/4 in. air gap", fontsize=6.5, color=MUTED, ha="right", va="center")
    save(fig, "fig-mounted.svg")


def fig_angles():
    fig, ax = canvas(7.4, 1.7, (-2, 104), (-3, 20))
    bars = [
        ("A  1-1/2 × 1-1/2 × 1/8 in. angle, 8 ft", 96, [("panel rail, top   W − 1/2", 43.5), ("panel rail, bottom", 43.5)]),
        ("B  1-1/2 × 1-1/2 × 1/8 in. angle, 8 ft", 96, [("mount backing bar, 28", 28), ("mount backing bar, 28", 28)]),
    ]
    y = 15.5
    for title, length, cuts in bars:
        ax.text(0, y + 1.7, title, fontsize=7.4, weight="bold")
        ax.add_patch(Rectangle((0, y - 2.2), length, 2.6, fc="#eceef1", ec=MUTED, lw=0.6))
        x = 0
        for name, L in cuts:
            ax.add_patch(Rectangle((x, y - 2.2), L, 2.6, fc=NEW, ec=INK, lw=0.7))
            ax.text(x + L / 2, y - 0.9, name, ha="center", va="center", fontsize=6.0, color="white")
            x += L + 0.5
        y -= 7.5
    ax.text(0, -2.2, "These four bars carry the weight. They are the only metal you cut with a saw. Lengths in inches.", fontsize=7, color=MUTED)
    save(fig, "fig-angles.svg")


def fig_rim():
    fig, ax = canvas(7.0, 4.0, (-6, 62), (-3, 34))
    s = Scene()
    rim(s, lips=False)
    for x, sx in ((T, 1), (W - T, -1)):
        for z, sz in ((T, 1), (H - T, -1)):
            s.box(x if sx > 0 else x - 1.2, 1, z if sz > 0 else z - 0.15, 1.2, 4, 0.15, NEW)
            s.box(x if sx > 0 else x - 0.15, 1, z if sz > 0 else z - 1.2, 0.15, 4, 1.2, NEW)
    s.draw(ax)
    for i, (x, z) in enumerate(((T + 2.6, T + 2.6), (W - T - 2.6, T + 2.6), (T + 2.6, H - T - 2.6),
                                (W - T - 2.6, H - T - 2.6)), 1):
        tag(ax, proj(x, 0.5, z), i)
    note(ax, proj(W, D * 0.6, 14), (W + 6, 14), "side wall\nfits between\ntop and bottom")
    note(ax, proj(30, D * 0.6, H), (W + 6, H + 5), "top wall, W long")
    ax.text(-5, -2, "Front lips left out of this picture so you can see the four corner pieces.", fontsize=7, color=MUTED)
    save(fig, "fig-rim.svg")


def fig_rivet():
    fig, ax = canvas(7.4, 2.3, (0, 120), (-7, 24))
    def plates(x0):
        ax.add_patch(Rectangle((x0, 10.5), 26, 1.5, fc=ALU, ec=INK, lw=0.8))
        ax.add_patch(Rectangle((x0, 10.1), 26, 0.4, fc=NEW, ec="none"))
        ax.add_patch(Rectangle((x0, 8.6), 26, 1.5, fc=ANGLE, ec=INK, lw=0.8))
    plates(3)
    ax.text(16, 15, "bead of silicone between\nthe parts (orange)", ha="center", fontsize=7, color="#7a4b10")
    ax.text(16, -4.5, "1  Bead of silicone on one part, then\nclamp the parts so the holes line up.", ha="center", fontsize=7.4)
    plates(43)
    ax.add_patch(Rectangle((54.6, 12), 2.2, 0.7, fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((55.2, 6.3), 1.0, 5.7, fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((55.5, 12.7), 0.4, 6, fc="#777", ec=INK, lw=0.5))
    ax.text(62, 5.8, "closed end: no\nhole for water", fontsize=6.8, va="center")
    ax.text(56, -4.5, "2  Push in a closed-end rivet from the\noutside. Flange flat.", ha="center", fontsize=7.4)
    plates(83)
    ax.add_patch(Rectangle((94.6, 12), 2.2, 0.7, fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((95.2, 8.6), 1.0, 3.4, fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Polygon([(94.6, 8.6), (96.8, 8.6), (97.2, 6.7), (94.2, 6.7)], fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((94, 12.7), 3.4, 3, fc="#555", ec=INK, lw=0.5))
    ax.text(99, 14.2, "rivet tool", fontsize=6.5, va="center")
    ax.text(96, -4.5, "3  Squeeze until the pin snaps. Silicone\nshould show around the seam.", ha="center", fontsize=7.4)
    save(fig, "fig-rivet.svg")


def fig_back():
    fig, ax = canvas(7.0, 4.3, (-6, 64), (-3, 38))
    s = Scene()
    rim(s)
    back(s, y=D + 7)
    s.draw(ax)
    for a, b in (((LIP / 2, D, H - LIP / 2), (W - LIP / 2, D, H - LIP / 2)),
                 ((LIP / 2, D, LIP / 2), (W - LIP / 2, D, LIP / 2)),
                 ((LIP / 2, D, LIP / 2), (LIP / 2, D, H - LIP / 2)),
                 ((W - LIP / 2, D, LIP / 2), (W - LIP / 2, D, H - LIP / 2))):
        pa, pb = proj(*a), proj(*b)
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color=NEW, lw=2.2, zorder=22)
    for f in (0.3, 0.55, 0.8):
        arrow(ax, proj(W * f, D + 7, H + 1.0), proj(W * f, D + 1.0, H + 1.0), NEW, lw=1.6)
    note(ax, proj(W * 0.2, D, H - LIP / 2), (W * 0.05, H + 10), "bead of silicone on all four back lips")
    note(ax, proj(W, D + 7, H * 0.55), (W + 10, H * 0.25), "back panel")
    save(fig, "fig-back.svg")


def fig_vents():
    fig, ax = canvas(7.4, 2.8, (-4, 51), (-3.5, 11))
    ax.add_patch(Rectangle((0, 0), W, D, fc=ALU, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((0, 0), W, 2.75, fc="#e7c79b", ec="none", alpha=0.6))
    ax.text(W / 2, 1.9, "front 2-3/4 in.: the panel rail goes here, keep clear", ha="center", va="center", fontsize=6.5, color="#7a4b10")
    for x0 in VX:
        ax.add_patch(Rectangle((x0, 3), 8, 2.5, fc="white", ec=INK, lw=0.9, hatch="xx"))
        for cx in (x0 - 0.2, x0 + 8.2):
            for cy in (2.8, 5.7):
                ax.add_patch(Circle((cx, cy), 0.09, fc="white", ec=INK, lw=0.4))
    for cx, cy in ((1.2, 5.5), (W - 1.2, 5.5), (1.2, 0.6), (W - 1.2, 0.6)):
        ax.add_patch(Circle((cx, cy), 0.18, fc="white", ec=WARN, lw=0.9))
    ax.text(W / 2, D + 1.6, "TOP or BOTTOM wall, outside view. Front edge at the bottom of the picture.", ha="center", fontsize=7.5)
    dim(ax, (3, -1.0), (11, -1.0), "8 in.", off=(0, -0.9))
    dim(ax, (11, -1.0), (13, -1.0), "2", off=(0, -0.9))
    dim(ax, (0, -1.0), (3, -1.0), "3", off=(0, -0.9))
    dim(ax, (45.5, 3), (45.5, 5.5), "", off=(0, 0))
    ax.text(46, 4.25, "2-1/2", fontsize=7, color=MUTED, va="center")
    dim(ax, (-1.4, 0), (-1.4, 3), "", off=(0, 0))
    ax.text(-1.9, 1.5, "3", fontsize=6.5, color=MUTED, va="center", ha="right")
    ax.text(45.5, 0.9, "red: 1/8 in. weep\nholes, BOTTOM\nwall only", fontsize=6.3, color=WARN, va="center")
    save(fig, "fig-vents.svg")


def fig_inside():
    fig, ax = canvas(7.4, 4.0, (-13, 66), (-3, 31))
    ax.add_patch(Rectangle((0, 0), W, H, fc=ALU, ec=INK, lw=1.2))
    ax.add_patch(Rectangle((T, T), W - 2 * T, H - 2 * T, fc="#f1f3f5", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((T + 0.2, H - T - 1.5), W - 2 * T - 0.4, 1.5, fc=NEW, ec=INK, lw=0.7))
    ax.add_patch(Rectangle((T + 0.2, T), W - 2 * T - 0.4, 1.5, fc=NEW, ec=INK, lw=0.7))
    for zz in (12 + VESA_H / 2, 12 - VESA_H / 2):
        ax.add_patch(Rectangle((8, zz - 0.75), 28, 1.5, fc="none", ec=INK, lw=0.8, ls="--"))
    ax.add_patch(Rectangle((24, 7), 8.5, 4.5, fc=PSU, ec=INK, lw=0.8))
    ax.text(28.25, 9.25, "PSU", ha="center", va="center", fontsize=8, weight="bold")
    ax.add_patch(Rectangle((23.4, 12.1), 9.7, 0.5, fc=NEW, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((3, 2.6), 3.4, 2.3, fc=PI, ec=INK, lw=0.8))
    ax.text(4.7, 3.75, "Pi", ha="center", va="center", fontsize=7.5, color="white", weight="bold")
    ax.add_patch(Rectangle((2.5, 5.3), 4.4, 0.4, fc=NEW, ec=INK, lw=0.6))
    for x0 in VX:
        ax.add_patch(Rectangle((x0, -0.05), 8, 0.3, fc="white", ec=INK, lw=0.4, hatch="xx"))
        ax.add_patch(Rectangle((x0, H - 0.25), 8, 0.3, fc="white", ec=INK, lw=0.4, hatch="xx"))
    ax.add_patch(Circle((32, 2.3), 0.55, fc="#333", ec=INK, lw=0.6))
    ax.plot([32, 32, 30], [2.85, 7, 7], color=INK, lw=1.2)
    ax.add_patch(Circle((40, 8), 0.45, fc=EARTH, ec=INK, lw=0.6))
    ax.plot([40, 33.6, 33.6], [8, 8, 7], color=EARTH, lw=1.2)
    note(ax, (W - 6, H - 0.9), (W + 3, H + 2.2), "top panel rail")
    note(ax, (W - 6, 0.9), (W + 3, -1.6), "bottom panel rail")
    note(ax, (35, 12 + VESA_H / 2), (W + 3, 18), "mount backing bars\n(on the back, dashed)")
    note(ax, (32.5, 10), (W + 3, 11.5), "PSU: 4 screws through\nthe back")
    note(ax, (33, 12.4), (W + 3, 14.6), "bent drip shield")
    note(ax, (3, 3.8), (-12.5, 8), "Pi, low and near\nthe cool intake,\nwith a drip shield")
    note(ax, (32, 2.3), (W + 3, 3.4), "mains cable gland,\nin the bottom wall")
    note(ax, (40, 8), (W + 3, 7.4), "earth: PSU to a bolt\non bare metal")
    save(fig, "fig-inside.svg")


def fig_panels_in():
    fig, ax = canvas(7.0, 4.0, (-6, 62), (-3, 34))
    s = Scene()
    back(s)
    rim(s, lips=False)
    rails(s)
    panels(s, color=PANEL)
    s.draw(ax)
    note(ax, proj(22, 0.25, 22.1), (6, H + 5.5), "panel array, bolted to both rails")
    note(ax, proj(W - T - 1, 1.25, H - 1.0), (W + 6, H - 2.5), "top rail")
    note(ax, proj(W - T - 1, 1.25, 1.0), (W + 6, 1.5), "bottom rail")
    ax.text(-5, -2, "Front lips left out so the rails show.", fontsize=7, color=MUTED)
    save(fig, "fig-panels-in.svg")


def fig_front():
    fig, ax = canvas(7.4, 4.0, (-17, 63), (-9, 30))
    s = Scene()
    back(s)
    rim(s)
    panels(s)
    s.box(0, -6, 0, W, 0.12, H, SHEET, alpha=0.6)
    clamp_frame(s, y=-13)
    s.draw(ax)
    for (x0, z0, x1, z1) in ((0, H - 0.2, W, H - 0.2), (0, 0.2, W, 0.2), (0.15, 0, 0.15, H), (W - 0.15, 0, W - 0.15, H)):
        a, b = proj(x0, 0, z0), proj(x1, 0, z1)
        ax.plot([a[0], b[0]], [a[1], b[1]], color=NEW, lw=3.2, solid_capstyle="butt", zorder=20)
    a = proj(W, 0, H / 2)
    tag(ax, (a[0] + 2.6, a[1]), 1)
    b = proj(W, -6, H / 2)
    tag(ax, (b[0] + 2.4, b[1] - 3.5), 2)
    c = proj(0, -13, H / 2)
    tag(ax, (c[0] - 2.8, c[1]), 3)
    ax.text(-16, -7.8, "1  foam tape on the front lips     2  your plastic sheet     "
            "3  clamp frame, screwed into well nuts", fontsize=7.4)
    save(fig, "fig-front.svg")


def fig_wellnut():
    fig, ax = canvas(7.4, 2.6, (0, 120), (-8, 24))
    ax.add_patch(Rectangle((10, 4), 3, 14, fc=ALU, ec=INK, lw=0.8))
    ax.add_patch(Rectangle((7, 9.6), 3, 2.8, fc="#222", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((10, 9.9), 5.5, 2.2, fc="#222", ec=INK, lw=0.6))
    ax.text(4, 15, "outside", fontsize=6.5, color=MUTED)
    ax.text(15, 15, "inside", fontsize=6.5, color=MUTED)
    ax.text(11, -4.5, "1  Push the well nut into a 3/8 in. hole\nfrom outside. Flange stays outside.",
            ha="center", fontsize=7.3)
    ax.add_patch(Rectangle((50, 4), 3, 14, fc=ALU, ec=INK, lw=0.8))
    ax.add_patch(Rectangle((44.5, 2.5), 1.2, 17, fc=ANGLE, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((45.7, 9.6), 1.3, 2.8, fc="#222", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((47, 9.9), 3, 2.2, fc="#222", ec=INK, lw=0.6))
    ax.add_patch(Polygon([(53, 9.2), (56.5, 8.8), (56.5, 13.2), (53, 12.8)], fc="#222", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((40.5, 10.3), 11, 1.4, fc="#9aa3ad", ec=INK, lw=0.5))
    ax.add_patch(Rectangle((39.5, 9.4), 1.2, 3.2, fc="#9aa3ad", ec=INK, lw=0.5))
    ax.text(42, 20.5, "clamp frame", fontsize=6.5, ha="center")
    ax.text(50, -4.5, "2  The screw passes through the clamp frame;\nthe rubber bulges behind and grips. Watertight.",
            ha="center", fontsize=7.3)
    x0 = 80
    ax.add_patch(Rectangle((x0 + 18, 2), 3, 18, fc=ALU, ec=INK, lw=0.8))
    ax.add_patch(Rectangle((x0 + 18, 19.4), 3, 0.6, fc=NEW, ec=INK, lw=0.4))
    ax.add_patch(Rectangle((x0 + 6, 20), 17, 0.9, fc=SHEET, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((x0 + 17.6, 20.9), 6.4, 0.5, fc=NEW, ec=INK, lw=0.4))
    ax.add_patch(Polygon([(x0 + 17, 21.4), (x0 + 25.2, 21.4), (x0 + 25.2, 13), (x0 + 24.3, 13),
                          (x0 + 24.3, 20.6), (x0 + 17, 20.6)], fc=ANGLE, ec=INK, lw=0.6))
    ax.text(x0 + 11, 22.5, "plastic sheet", fontsize=6.6, ha="center")
    ax.text(x0 + 26, 17, "clamp\nframe", fontsize=6.6)
    ax.text(x0 + 17, 9, "wall", fontsize=6.6, ha="right")
    ax.text(x0 + 15, -4.5, "3  Cut-away: the sheet is squeezed\nbetween two strips of foam tape (orange).",
            ha="center", fontsize=7.3)
    save(fig, "fig-wellnut.svg")


def fig_seal():
    fig, ax = canvas(7.0, 4.0, (-6, 60), (-3, 33))
    s = Scene()
    back(s)
    rim(s)
    clamp_frame(s, y=0)
    s.draw(ax)
    for a, b in (((0, D + T, H), (W, D + T, H)), ((W + 0.12, D + T, 0), (W + 0.12, D + T, H)),
                 ((W + 0.12, 0.85, H + 0.12), (W + 0.12, D + T, H + 0.12)), ((0, 0.85, H + 0.12), (0, D + T, H + 0.12))):
        pa, pb = proj(*a), proj(*b)
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color=NEW, lw=3.0, zorder=25, solid_capstyle="round")
    note(ax, proj(W * 0.4, D + T, H + 0.1), (6, H + 6.5), "silicone along every outside seam and corner (orange)")
    save(fig, "fig-seal.svg")


def fig_back_view():
    fig, ax = canvas(7.4, 3.8, (-4, 68), (-6, 31))
    ax.add_patch(Rectangle((0, 0), W, H, fc=ALU, ec=INK, lw=1.2))
    cx, cz = W / 2, H / 2
    for zz in (cz + VESA_H / 2, cz - VESA_H / 2):
        ax.add_patch(Rectangle((8, zz - 0.75), 28, 1.5, fc="none", ec=INK, lw=0.8, ls="--"))
    for xx in (cx - VESA_W / 2, cx + VESA_W / 2):
        ax.add_patch(Rectangle((xx - 0.8, 2.2), 1.6, 19.6, fc=NEW, ec=INK, lw=0.8, alpha=0.9))
        for zz in (cz + VESA_H / 2, cz - VESA_H / 2):
            ax.add_patch(Circle((xx, zz), 0.34, fc="white", ec=INK, lw=0.7))
    ax.add_patch(Rectangle((11.5, 7), 8.5, 4.5, fc="none", ec=MUTED, lw=0.6, ls=":"))
    ax.text(W / 2, H + 1.4, "BACK OF THE CASE (seen from behind)", ha="center", fontsize=8, weight="bold")
    note(ax, (cx + VESA_W / 2, cz + VESA_H / 2), (W + 3, H + 1.5), "4 M8 bolts through the back\nand the backing bars")
    note(ax, (cx + VESA_W / 2 + 0.6, 10), (W + 3, 11), "mount arms (orange)\nbolt on here")
    note(ax, (30, cz - VESA_H / 2), (W + 3, 3), "backing bars on the\ninside (dashed)")
    dim(ax, (cx - VESA_W / 2, -1.6), (cx + VESA_W / 2, -1.6), "600 mm (23-5/8 in.)", off=(0, -1.0))
    ax.annotate("", xy=(-1.5, cz + VESA_H / 2), xytext=(-1.5, cz - VESA_H / 2), arrowprops=dict(arrowstyle="<->", lw=0.6, color=MUTED))
    ax.text(-2, cz, "400 mm\n(15-3/4 in.)", rotation=90, fontsize=6.5, color=MUTED, ha="right", va="center")
    save(fig, "fig-back-view.svg")


def fig_wall():
    fig, ax = canvas(7.4, 3.9, (-6, 62), (-13, 32))
    ax.add_patch(Rectangle((-5, -7), 60, 38, fc=BRICK, ec=INK, lw=0.8))
    for r in range(-7, 31, 2):
        ax.plot([-5, 55], [r, r], color=MORTAR, lw=0.8)
        off = 0 if (r // 2) % 2 == 0 else 2
        for c in range(-5 + off, 55, 4):
            if r + 2 <= 31:
                ax.plot([c, c], [r, r + 2], color=MORTAR, lw=0.8)
    ax.add_patch(Rectangle((0, 0), W, H, fc="none", ec="white", lw=1.4, ls="--"))
    ax.add_patch(Rectangle((6.35, 1.55), 31.3, 20.9, fc=NEW, ec=INK, lw=0.8, alpha=0.9))
    ax.text(W / 2, H / 2, "TV mount wall plate", ha="center", va="center", color="white", fontsize=9, weight="bold")
    for xa in (9, 22, 35):
        for zz in (3.2, 20.8):
            ax.add_patch(Circle((xa, zz), 0.34, fc="#333", ec=INK, lw=0.5))
    ax.text(W / 2, H + 1.4, "case outline (painter's tape)", ha="center", color="white", fontsize=8)
    ax.text(-5, -9.2, "6 anchors, each in the middle of a whole brick. Use the plate's slots that land best.", fontsize=7.4)
    ax.text(-5, -11.6, "Level the plate before the last anchor is tightened.", fontsize=7.4)
    save(fig, "fig-wall.svg")


def fig_hang():
    fig, ax = canvas(7.4, 2.9, (0, 120), (-9, 31))
    for x0, title, mode in ((0, "1  Two people lift the case so its\narms are above the wall plate", "up"),
                            (42, "2  Lower it until the arms hook\nover the plate", "down"),
                            (84, "3  Lock the mount's tabs and\nfit a padlock or security screw", "lock")):
        ax.add_patch(Rectangle((x0 + 2, -4), 5, 34, fc=BRICK, ec=INK, lw=0.6))
        lift = 3 if mode == "up" else 0
        cx = x0 + 9.0
        ax.add_patch(Rectangle((x0 + 7, 3.5), 0.4, 19, fc=ANGLE, ec=INK, lw=0.5))
        ax.add_patch(Rectangle((cx - 0.7, 4 + lift), 0.7, 18, fc=NEW, ec=INK, lw=0.5))
        ax.add_patch(Rectangle((x0 + 7.4, 20.2 + lift), 0.9, 0.8, fc=NEW, ec=INK, lw=0.4))
        ax.add_patch(Rectangle((cx, 2 + lift), 5, 22, fc=ALU, ec=INK, lw=0.8))
        ax.add_patch(Rectangle((cx + 5, 2 + lift), 0.3, 22, fc=SHEET, ec=INK, lw=0.5))
        if mode == "up":
            arrow(ax, (cx + 9, 17), (cx + 9, 23))
        elif mode == "down":
            arrow(ax, (cx + 9, 23), (cx + 9, 17))
        else:
            ax.add_patch(Circle((x0 + 8, 5.5), 1.1, fc="#333", ec=INK, lw=0.5))
        ax.text(x0 + 14, -7.4, title, ha="center", fontsize=7.4)
    save(fig, "fig-hang.svg")


def fig_nest():
    fig, ax = canvas(7.4, 4.05, (-1, 98), (-5.5, 50))
    ax.add_patch(Rectangle((0, 0), 96, 48, fc="#f4f5f7", ec=INK, lw=1.0))
    ax.text(0, 49, "One 48 × 96 in. sheet, 1/16 in. thick (example sizes for a 44 × 24 in. window)", fontsize=8, weight="bold")

    def part(x, y, w, h, label, fs=7.2, scores=False):
        ax.add_patch(Rectangle((x, y), w, h, fc=ALU, ec=INK, lw=0.8))
        if label:
            ax.text(x + w / 2, y + (h * 0.73 if scores and w > 40 else h / 2), label, ha="center", va="center", fontsize=fs, weight="bold")
        if scores:
            for yy in (y + 15 / 16, y + h - 15 / 16):
                ax.plot([x, x + w], [yy, yy], color=AIR, lw=0.9, ls=(0, (3, 2)))

    part(1, 23, 44, 24, "BACK\nW × H  (44 × 24)", fs=9)
    for y, lab in ((14.75, "TOP WALL  44 × 7-3/4"), (6.5, "BOTTOM WALL  44 × 7-3/4")):
        part(1, y, 44, 7.75, lab, scores=True)
        for x in VX:
            ax.add_patch(Rectangle((1 + x, y + 7.75 - 15 / 16 - 5.5), 8, 2.5, fc="white", ec=INK, lw=0.5, hatch="xx"))
    part(1, 4.125, 44, 1.875, "FRAME, TOP", fs=6)
    part(1, 1.75, 44, 1.875, "FRAME, BOTTOM", fs=6)
    part(46, 39.25, 23.875, 7.75, "SIDE WALL", scores=True)
    part(46, 31, 23.875, 7.75, "SIDE WALL", scores=True)
    part(46, 28.6, 22, 1.875, "FRAME, SIDE", fs=6)
    part(46, 26.2, 22, 1.875, "FRAME, SIDE", fs=6)
    for i in range(4):
        part(46 + i * 4.5, 23.7, 4, 1.875, "", fs=5)
    ax.text(64.5, 24.6, "×4 corners", fontsize=5.6, va="center")
    for i in range(3):
        part(46 + i * 7, 18, 6, 4, f"test {i + 1}", fs=6)
    ax.add_patch(Rectangle((71, 2), 24, 44, fc="none", ec=MUTED, lw=0.5, hatch="///"))
    ax.text(83, 24, "spare:\nmistakes,\ndrip shields", ha="center", va="center", fontsize=7.5, color=MUTED, backgroundcolor="#f4f5f7")
    ax.plot([1, 7], [-2.5, -2.5], color=AIR, lw=0.9, ls=(0, (3, 2)))
    ax.text(8, -2.5, "score line (V-bit, inside face)", fontsize=7, va="center", color=MUTED)
    ax.add_patch(Rectangle((42, -3.2), 3, 1.4, fc="white", ec=INK, lw=0.5, hatch="xx"))
    ax.text(46, -2.5, "vent window, through-cut", fontsize=7, va="center", color=MUTED)
    save(fig, "fig-nest.svg")


def fig_blanks():
    fig, ax = canvas(7.4, 3.5, (-3, 64), (-7, 15))
    L, B, n = 23.875, 7.75, 15 / 16
    ax.add_patch(Polygon([(n, 0), (L - n, 0), (L - n, n), (L, n), (L, B - n), (L - n, B - n), (L - n, B), (n, B),
                          (n, B - n), (0, B - n), (0, n), (n, n)], fc=ALU, ec=INK, lw=1.0))
    for yy in (n, B - n):
        ax.plot([n, L - n], [yy, yy], color=AIR, lw=1.1, ls=(0, (3, 2)))
    for cx, cy in ((n, n), (L - n, n), (n, B - n), (L - n, B - n)):
        ax.add_patch(Circle((cx, cy), 0.14, fc="white", ec=WARN, lw=0.8))
    for i in range(6):
        xx = 2 + i * (L - 4) / 5
        ax.add_patch(Circle((xx, B - 0.45), 0.09, fc="white", ec=INK, lw=0.5))
    ax.text(L / 2, 4, "SIDE WALL, inside face up\n(top and bottom walls are the same,\n44 long, with no corner notches)", ha="center", va="center", fontsize=7.4)
    dim(ax, (0, -1.3), (L, -1.3), "H − 1/8", off=(0, -0.9))
    dim(ax, (-1.2, 0), (-1.2, B), "", off=(0, 0))
    ax.text(-1.6, B / 2, "7-3/4", fontsize=7, color=MUTED, rotation=90, ha="right", va="center")
    dim(ax, (L + 1, 0), (L + 1, n), "", off=(0, 0))
    ax.text(L + 1.4, n / 2, "15/16", fontsize=6.5, color=MUTED, va="center")
    dim(ax, (L + 1, n), (L + 1, B - n), "", off=(0, 0))
    ax.text(L + 1.4, B / 2, "5-7/8", fontsize=6.5, color=MUTED, va="center")
    dim(ax, (L + 1, B - n), (L + 1, B), "", off=(0, 0))
    ax.text(L + 1.4, B - n / 2, "15/16", fontsize=6.5, color=MUTED, va="center")
    ax.text(0, -4.9, "Red circles: 1/8 in. relief holes where notches meet score lines, so the fold cannot tear into the corner.", fontsize=7, color=WARN)
    ox, oy = 40, 0.5
    ax.plot([ox + 1.0, ox, ox, ox + 1.0], [oy, oy, oy + 6, oy + 6], color=INK, lw=3.0, solid_joinstyle="miter")
    ax.text(ox + 2.0, oy + 3, "6 in. wall\n(the box depth)", fontsize=7.2, va="center")
    ax.text(ox + 1.3, oy + 6, "1 in. lip: back panel\nis riveted to this", fontsize=7.2, va="center")
    ax.text(ox + 1.3, oy, "1 in. lip: the window\nsits on this", fontsize=7.2, va="center")
    ax.text(ox + 3, 12.3, "End view once folded", ha="center", fontsize=8, weight="bold")
    save(fig, "fig-blanks.svg")


def fig_cnc():
    fig, ax = canvas(7.4, 2.7, (0, 120), (-7, 34))
    ax.add_patch(Rectangle((2, 4), 52, 26, fc="#d8c6a4", ec=INK, lw=0.8))
    ax.text(4, 31.4, "Top view: sheet on a surfaced MDF spoilboard", fontsize=7.4, weight="bold")
    ax.add_patch(Rectangle((6, 7), 44, 20, fc="#e2e5e9", ec=INK, lw=0.8))
    for x in range(8, 51, 7):
        for y in (8.2, 25.8):
            ax.add_patch(Circle((x, y), 0.45, fc="#555", ec=INK, lw=0.4))
    ax.add_patch(Rectangle((11, 11), 34, 12, fc="none", ec=NEW, lw=1.4))
    for x, y, dx, dy in ((20, 11, 1.8, 0), (36, 11, 1.8, 0), (20, 23, 1.8, 0), (36, 23, 1.8, 0)):
        ax.plot([x, x + dx], [y, y + dy], color="white", lw=2.6, zorder=8)
    tag(ax, (15, 19.5), 1, r=1.5)
    for xx in (22, 26, 30, 34):
        ax.add_patch(Circle((xx, 21), 0.4, fc="white", ec=INK, lw=0.5))
    ax.plot([11, 45], [14, 14], color=AIR, lw=1.1, ls=(0, (3, 2)))
    tag(ax, (40, 14), 2, r=1.5)
    ax.add_patch(Rectangle((22, 16.2), 12, 3.2, fc="white", ec=INK, lw=0.6, hatch="xx"))
    tag(ax, (37, 18), 3, r=1.5)
    tag(ax, (11, 27.8), 4, r=1.5)
    ax.text(28, -2.4, "1 holes   2 scores   3 windows   4 outlines, with small tabs\nScrews go through waste, never through a part.",
            ha="center", va="center", fontsize=7.2)
    x0 = 66
    ax.text(x0, 31.4, "Side view: why the board must be flat", fontsize=7.4, weight="bold")
    ax.add_patch(Rectangle((x0, 10), 48, 7, fc="#d8c6a4", ec=INK, lw=0.8))
    ax.text(x0 + 24, 13.5, "MDF spoilboard, surfaced first", ha="center", va="center", fontsize=7)
    ax.add_patch(Rectangle((x0, 17), 48, 1.8, fc=ALU, ec=INK, lw=0.8))
    ax.add_patch(Polygon([(x0 + 18, 18.8), (x0 + 15.5, 25), (x0 + 20.5, 25)], fc="#d9d9d9", ec=INK, lw=0.7))
    ax.add_patch(Rectangle((x0 + 16.2, 25), 3.6, 4.5, fc="#777", ec=INK, lw=0.6))
    ax.add_patch(Polygon([(x0 + 15.9, 18.8), (x0 + 20.1, 18.8), (x0 + 18, 17.75)], fc="white", ec=WARN, lw=0.8, zorder=5))
    ax.text(x0 + 24, 22, "A score only 0.030 in. deep:\na warped board or a lifted\nsheet changes it completely.", fontsize=7, va="center")
    ax.text(x0 + 24, 3.8, "Surface the board, then use a touch-off\nplate on top of the sheet.", ha="center", va="center", fontsize=7.2)
    save(fig, "fig-cnc.svg")


def fig_coupon():
    fig, ax = canvas(7.4, 2.3, (0, 120), (-5, 25))
    for i, (depth, land, verdict) in enumerate((("0.025 in. deep", "0.038 left", "likely stiffest to fold"),
                                                 ("0.030 in. deep", "0.033 left", "start here"),
                                                 ("0.040 in. deep", "0.023 left", "likely too thin"))):
        x0 = 3 + i * 40
        ax.text(x0 + 15, 22.6, f"Test {i + 1}", ha="center", fontsize=8, weight="bold")
        ax.add_patch(Rectangle((x0, 12), 30, 4.5, fc=ALU, ec=INK, lw=0.8))
        h = {0: 1.8, 1: 2.2, 2: 2.9}[i]
        ax.add_patch(Polygon([(x0 + 15 - h, 16.5), (x0 + 15 + h, 16.5), (x0 + 15, 16.5 - h)], fc="white", ec=WARN, lw=0.9))
        ax.text(x0 + 15, 9.2, depth, ha="center", fontsize=7.6, color=WARN)
        ax.text(x0 + 15, 6.7, land, ha="center", fontsize=7.2, color=MUTED)
        ax.text(x0 + 15, 3.5, verdict, ha="center", fontsize=7.2)
    ax.text(60, -2.2, "Drawn much larger than life. Fold each by hand to 90°, then look at the outside of the corner under a light.",
            ha="center", fontsize=7.4)
    save(fig, "fig-coupon.svg")


def fig_score_fold():
    fig, ax = canvas(7.4, 2.5, (0, 120), (-7, 25))
    ax.add_patch(Rectangle((3, 11), 30, 3.4, fc=ALU, ec=INK, lw=0.8))
    ax.add_patch(Polygon([(16, 14.4), (20, 14.4), (18, 12.4)], fc="white", ec=WARN, lw=0.9))
    ax.add_patch(Polygon([(18, 14.4), (15.5, 21), (20.5, 21)], fc="#d9d9d9", ec=INK, lw=0.7, alpha=0.6))
    ax.plot([18, 18], [11, 12.4], color=WARN, lw=1.6)
    ax.text(21, 18.5, "V-bit, inside face", fontsize=6.8)
    ax.text(22, 9.2, "leave about half", fontsize=6.8, color=WARN)
    ax.text(18, -4.2, "1  Score on the INSIDE of the fold, in two\nlight passes, tool centred on the line.", ha="center", fontsize=7.3)
    x0 = 44
    ax.add_patch(Rectangle((x0, 4), 24, 6, fc="#b88d5a", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((x0, 10), 21, 1.2, fc=ALU, ec=INK, lw=0.7))
    ax.add_patch(Rectangle((x0, 11.2), 19.5, 3, fc="#8f97a3", ec=INK, lw=0.7))
    ax.text(x0 + 9.5, 12.7, "clamped bar", ha="center", va="center", fontsize=6.3)
    ax.add_patch(Polygon([(x0 + 21, 10), (x0 + 21 + 8.4, 18.4), (x0 + 20.6 + 7.6, 19.3), (x0 + 20.2, 11.2)], fc=ALU, ec=INK, lw=0.7))
    arrow(ax, (x0 + 33, 13), (x0 + 28, 21.5))
    ax.text(x0 + 15, -4.2, "2  Score faces up, on the edge of the bar.\nClamp every 8 in. One slow push to 90°.", ha="center", fontsize=7.3)
    x0 = 90
    ax.add_patch(Polygon([(x0, 10), (x0 + 20, 10), (x0 + 20, 22), (x0 + 18.8, 22), (x0 + 18.8, 11.2), (x0, 11.2)], fc=ALU, ec=INK, lw=0.8))
    ax.add_patch(Circle((x0 + 20, 10), 0.8, fc="none", ec=OK, lw=1.2))
    ax.text(x0 + 15, 5.5, "Outside corner: no cracks", fontsize=7, ha="center")
    ax.text(x0 + 11, -4.2, "3  Never unbend and refold. A fold\nthat opens is scrap.", ha="center", fontsize=7.3)
    save(fig, "fig-score-fold.svg")


def fig_vent_section():
    fig, ax = canvas(7.4, 3.3, (0, 120), (-8, 39))

    def section(x0, top):
        y = 20
        sign = 1 if top else -1
        ax.add_patch(Rectangle((x0, y - 0.5), 12, 1, fc=ALU, ec=INK, lw=0.8))
        ax.add_patch(Rectangle((x0 + 36, y - 0.5), 12, 1, fc=ALU, ec=INK, lw=0.8))
        ax.add_patch(Rectangle((x0 + 7, y + sign * 0.5 - (0 if top else 1.4)), 34, 1.4, fc=NEW, ec=INK, lw=0.6, alpha=0.9))
        for i in range(6):
            xs = x0 + 13.3 + i * 4.3
            if top:
                pts = [(xs, y + 2.0), (xs + 3.6, y + 7.0), (xs + 4.4, y + 7.0), (xs + 0.9, y + 2.0)]
            else:
                pts = [(xs, y - 2.0), (xs + 3.6, y - 7.0), (xs + 4.4, y - 7.0), (xs + 0.9, y - 2.0)]
            ax.add_patch(Polygon(pts, fc=NEW, ec=INK, lw=0.5))
        my = y - sign * 3.0
        ax.plot([x0 + 7.5, x0 + 40.5], [my, my], color=INK, lw=1.0, ls=(0, (1, 1)))
        for xf in (x0 + 7.5, x0 + 37.5):
            ax.add_patch(Rectangle((xf, min(y - sign * 0.5, my)), 3, abs(my - (y - sign * 0.5)), fc=NEW, ec=INK, lw=0.5, alpha=0.65))
        ax.text(x0 + 3, y + 2.5 if top else y - 2.5, "wall", fontsize=6.8, ha="center", va="center")
        ax.text(x0 + 12, my - sign * 2.2, "mesh, on the inside", ha="center", va="center", fontsize=7)
    section(4, True)
    section(66, False)
    ax.text(28, 36.5, "TOP wall: warm air leaves", ha="center", fontsize=8, weight="bold")
    arrow(ax, (28, 11), (28, 34), AIR, lw=1.6)
    ax.text(90, 36.5, "BOTTOM wall: cool air comes in", ha="center", fontsize=8, weight="bold")
    arrow(ax, (90, 8), (90, 31), AIR, lw=1.6)
    ax.text(60, -6.3, "Printed ASA louvres outside, mesh behind them, held by a printed frame. 8 in. long so it prints on an ordinary bed.\n"
            "Slats tilt so nothing falling can land on the mesh. Water on the bottom vents simply runs out.",
            ha="center", va="center", fontsize=7.2)
    save(fig, "fig-vent-section.svg")


def fig_condensation():
    fig, ax = canvas(7.4, 2.8, (0, 120), (-7, 34))

    def box(x0, title, wall, inner, outer, wet):
        ax.text(x0 + 25, 32, title, ha="center", fontsize=8, weight="bold")
        ax.add_patch(Rectangle((x0 + 5, 7), 40, 20, fc="#f6f7f9", ec=INK, lw=1.8))
        ax.text(x0 + 25, 20, inner, ha="center", va="center", fontsize=7.6)
        ax.text(x0 + 25, 11.2, wall, ha="center", va="center", fontsize=7.2, weight="bold", color=(WARN if wet else OK))
        ax.text(x0 + 25, 2.8, outer, ha="center", va="center", fontsize=7.2, color=MUTED)
        if wet:
            for i in range(12):
                ax.add_patch(Circle((x0 + 7.5 + i * 3.1, 26.2), 0.42, fc=AIR, ec="none", zorder=8))
                if i % 3 == 0:
                    ax.add_patch(Circle((x0 + 7.5 + i * 3.1, 24.6), 0.32, fc=AIR, ec="none", zorder=8))
    box(4, "Board running", "metal 44 °F: above dew point, stays dry", "the board keeps the box warm",
        "example: outside 36 °F, dew point 32 °F", False)
    box(66, "Off overnight, then a warm damp morning", "metal 40 °F: below dew point, water forms", "the metal is still cold",
        "example: outside 62 °F, dew point 58 °F", True)
    ax.text(60, -5, "Water only forms on a surface colder than the air's dew point. So keep it powered, and let it breathe.", ha="center", fontsize=7.6)
    save(fig, "fig-condensation.svg")


if __name__ == "__main__":
    for f in (fig_overview, fig_mounted, fig_nest, fig_blanks, fig_cnc, fig_coupon, fig_score_fold,
              fig_angles, fig_rim, fig_rivet, fig_back, fig_vents, fig_vent_section, fig_inside,
              fig_panels_in, fig_front, fig_wellnut, fig_seal, fig_back_view, fig_wall, fig_hang,
              fig_condensation):
        f()
