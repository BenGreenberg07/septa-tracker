#!/usr/bin/env python3
"""Pictures for the simple case build guide (fig-*.svg next to this file).

    /opt/homebrew/bin/python3 docs/simple-build/figures.py

Dimensions are in inches and use the guide's example sheet, 44 x 24 in.
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

# example build: sheet 44 x 24, box 4-1/2 deep
W, H, D = 44.0, 24.0, 4.5
T = 0.25                 # ACM drawn a little thicker than 1/8 in. so it reads

INK = "#1d1d1f"
ACM = "#c9ced6"
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

def rim(s, color=ACM):
    s.box(0, 0, 0, W, D, T, color)
    s.box(0, 0, H - T, W, D, T, color)
    s.box(0, 0, T, T, D, H - 2 * T, color)
    s.box(W - T, 0, T, T, D, H - 2 * T, color)


def back(s, color=ACM, y=D):
    s.box(0, y, 0, W, T, H, color)


def rails(s, color=ANGLE):
    s.box(T + 0.2, 0.25, H - T - 0.15, W - 2 * T - 0.4, 1.5, 0.15, color)
    s.box(T + 0.2, 1.6, H - T - 1.65, W - 2 * T - 0.4, 0.15, 1.5, color)
    s.box(T + 0.2, 0.25, T, W - 2 * T - 0.4, 1.5, 0.15, color)
    s.box(T + 0.2, 1.6, T + 0.15, W - 2 * T - 0.4, 0.15, 1.5, color)


def panels(s, color=PANEL):
    s.box(1.85, 0.6, 1.9, 40.3, 0.9, 20.2, color)


def clamp_frame(s, y=0, color=ANGLE):
    s.box(0, y - 0.15, H - 1, W, 0.15, 1, color)
    s.box(0, y - 0.15, 0, W, 0.15, 1, color)
    s.box(0, y - 0.15, 1, 1, 0.15, H - 2, color)
    s.box(W - 1, y - 0.15, 1, 1, 0.15, H - 2, color)
    s.box(0, y - 0.15, H, W, 1.0, 0.12, color)
    s.box(W, y - 0.15, 0, 0.12, 1.0, H, color)


# ---------------------------------------------------------------- figures

def fig_overview():
    fig, ax = canvas(7.4, 3.9, (-24, 72), (-6, 32))
    s = Scene()
    back(s, y=D + 9)
    rim(s)
    rails(s)
    panels(s)
    s.box(0, -6, 0, W, 0.12, H, SHEET, alpha=0.55)
    clamp_frame(s, y=-12)
    s.draw(ax)
    note(ax, proj(W, D + 9, H - 3), (W + 9, H + 5), "Back panel (ACM)")
    note(ax, proj(W, 2.5, 12), (W + 9, 13), "Box rim: 4 ACM strips")
    note(ax, proj(42, 0.6, 18), (W + 9, 6), "LED panels on 2 rails")
    note(ax, proj(3, -6, 4), (-23.5, 6), "Your plastic sheet")
    note(ax, proj(0, -12, 14), (-23.5, 17), "Clamp frame\n(the service door)")
    save(fig, "fig-overview.svg")


def fig_mounted():
    fig, ax = canvas(7.2, 4.6, (-27, 41), (-9, 33))
    ax.add_patch(Rectangle((-8, -9), 8, 42, fc=BRICK, ec=INK, lw=0.8))
    for z in range(-9, 33, 3):
        ax.plot([-8, 0], [z, z], color=MORTAR, lw=1.3)
    bx = 0.55
    ax.add_patch(Rectangle((bx, 0), D + T, H, fc=ACM, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((bx + 0.3, 0.3), D + T - 0.6, H - 0.6, fc="white", ec=INK, lw=0.5))
    ax.add_patch(Rectangle((bx + D + T, 0), 0.15, H, fc=SHEET, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((bx + D + T - 1.4, 1.9), 0.9, 20.2, fc=PANEL, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((bx + 0.3, 9), 2.0, 8.5, fc=PSU, ec=INK, lw=0.6))
    ax.text(bx + 1.3, 13.2, "PSU", rotation=90, ha="center", va="center", fontsize=6.5)
    ax.add_patch(Rectangle((bx + 0.3, 3), 1.4, 3.5, fc=PI, ec=INK, lw=0.6))
    # Z-bar: wall piece hooks up, case piece hooks down
    ax.add_patch(Polygon([(0, H - 4.0), (0.18, H - 4.0), (0.18, H - 2.3), (0.45, H - 2.0),
                          (0.45, H - 1.3), (0.3, H - 1.3), (0.3, H - 1.9), (0, H - 2.2)],
                         fc=ANGLE, ec=INK, lw=0.5))
    ax.add_patch(Polygon([(bx, H - 0.7), (bx - 0.05, H - 0.7), (bx - 0.05, H - 1.4), (0.22, H - 1.9),
                          (0.22, H - 2.4), (0.36, H - 2.4), (0.36, H - 2.0), (bx, H - 1.6)],
                         fc=NEW, ec=INK, lw=0.5))
    for zz in (H - 3.2, 0.9):
        ax.add_patch(Rectangle((-2.6, zz - 0.13), 2.8, 0.26, fc="#5a6270", ec=INK, lw=0.4))
    ax.add_patch(Polygon([(0, 0.4), (0, 2.4), (0.2, 2.4), (0.2, -0.0), (bx + 1.6, 0.0),
                          (bx + 1.6, 0.2), (0.2, 0.2), (0.2, 0.4)], fc=NEW, ec=INK, lw=0.5))
    arrow(ax, (bx + 2.4, -5.5), (bx + 2.4, -0.4), AIR)
    arrow(ax, (bx + 2.4, 2), (bx + 2.4, 21.5), AIR)
    arrow(ax, (bx + 2.4, H - 0.2), (bx + 2.4, H + 4.5), AIR)
    note(ax, (0.3, H - 1.6), (-26.5, H + 5.5), "Z-bar cleat: wall half hooks up,\ncase half hooks down")
    note(ax, (-1.2, H - 3.2), (-26.5, H - 4), "1/4 in. stainless\nsleeve anchor")
    note(ax, (bx + 1.0, 0.1), (-26.5, -4), "anti-lift bracket\n(stops theft and wind)")
    note(ax, (bx + D + 0.5, H), (bx + 13, H + 5.5), "under the station canopy:\nno rain hood needed")
    note(ax, (bx + D + T + 0.1, 12), (bx + 13, 13), "your plastic sheet")
    note(ax, (bx + D - 0.9, 18), (bx + 13, 19), "LED panels")
    note(ax, (bx + 2.4, 0), (bx + 13, 2), "vent windows, top and bottom,\nwith screen behind")
    dim(ax, (bx, -7.3), (bx + D + T, -7.3), "≈ 4-3/4 in.", off=(0, -1.1))
    save(fig, "fig-mounted.svg")


def fig_cutlist():
    fig, ax = canvas(7.4, 3.2, (-2, 106), (-5, 28))
    for n, x0 in enumerate((0, 56)):
        ax.add_patch(Rectangle((x0, 0), 48, 24, fc="#f4f5f7", ec=INK, lw=1.0))
        ax.text(x0, 25.4, f"Sheet {n + 1}: 24 × 48 in.", fontsize=8, weight="bold")
    ax.add_patch(Rectangle((0, 0), 44, 24, fc=ACM, ec=INK, lw=0.8))
    ax.text(22, 12, "BACK\nW × H\n(44 × 24)", ha="center", va="center", fontsize=9, weight="bold")
    ax.add_patch(Rectangle((44, 0), 4, 24, fc="none", ec=MUTED, lw=0.5, hatch="///"))
    y = 24
    for name in ("TOP   W × 4-1/2", "BOTTOM   W × 4-1/2"):
        y -= 4.5
        ax.add_patch(Rectangle((56, y), 44, 4.5, fc=ACM, ec=INK, lw=0.8))
        ax.text(78, y + 2.25, name, ha="center", va="center", fontsize=7.5)
    y -= 4.5
    for i in range(2):
        ax.add_patch(Rectangle((56 + i * 23.85, y), 23.75, 4.5, fc=ACM, ec=INK, lw=0.8))
        ax.text(56 + i * 23.85 + 11.9, y + 2.25, "SIDE  (H − 1/4) × 4-1/2", ha="center", va="center", fontsize=6.3)
    ax.add_patch(Rectangle((56, 0), 48, y, fc="none", ec=MUTED, lw=0.5, hatch="///"))
    ax.text(80, y / 2, "spare: practice cuts and mistakes", ha="center", va="center",
            fontsize=7, color=MUTED, backgroundcolor="#f4f5f7")
    ax.text(-1, -3.3, "Example numbers for a 44 × 24 in. sheet. Strips are cut along the 48 in. length first, then to length.",
            fontsize=7, color=MUTED)
    save(fig, "fig-cutlist.svg")


def fig_score_snap():
    fig, ax = canvas(7.4, 2.4, (0, 120), (-7, 24))
    def panel_side(x0):
        ax.add_patch(Rectangle((x0, 10), 30, 3, fc=ACM, ec=INK, lw=0.8))
        ax.add_patch(Rectangle((x0, 10.4), 30, 2.2, fc="#4d4d4d", ec="none"))
    panel_side(2)
    ax.add_patch(Rectangle((2, 13), 14, 1.6, fc="#999", ec=INK, lw=0.6))
    ax.text(9, 15.8, "straightedge", ha="center", fontsize=6.5)
    ax.add_patch(Polygon([(17.2, 13.3), (19.5, 19), (21, 19), (17.8, 13)], fc="#d9d9d9", ec=INK, lw=0.6))
    ax.plot([17.3, 17.3], [12.3, 13], color=WARN, lw=1.8)
    ax.text(23, 17, "through the top skin\ninto the black core", fontsize=6.5, color=WARN)
    ax.text(17, -4.5, "1  Clamp a straightedge on the line.\nScore 4 to 5 light passes, fresh blade.",
            ha="center", fontsize=7.4)
    x0 = 42
    ax.add_patch(Rectangle((x0, 4), 18, 6, fc="#b88d5a", ec=INK, lw=0.6))
    ax.text(x0 + 9, 6.5, "table", ha="center", fontsize=6.5, color="white")
    ax.add_patch(Polygon([(x0, 10), (x0 + 18, 10), (x0 + 18, 13), (x0, 13)], fc=ACM, ec=INK, lw=0.8))
    ax.add_patch(Polygon([(x0 + 18, 10), (x0 + 30, 4.5), (x0 + 31.3, 7.2), (x0 + 18, 13)], fc=ACM, ec=INK, lw=0.8))
    arrow(ax, (x0 + 28, 16), (x0 + 29, 8.5))
    ax.text(x0 + 16, -4.5, "2  Score line on the table edge, scored\nside up. Press the overhang down.",
            ha="center", fontsize=7.4)
    x0 = 82
    ax.add_patch(Polygon([(x0, 10), (x0 + 18, 10), (x0 + 18, 13), (x0, 13)], fc=ACM, ec=INK, lw=0.8))
    ax.add_patch(Polygon([(x0 + 18.4, 9.4), (x0 + 30, 3.5), (x0 + 31.3, 6.2), (x0 + 18.4, 12.4)], fc=ACM, ec=INK, lw=0.8))
    ax.add_patch(Polygon([(x0 + 17.6, 8.5), (x0 + 19.4, 8.5), (x0 + 20.6, 1.5), (x0 + 19.4, 1.2)], fc="#d9d9d9", ec=INK, lw=0.6))
    ax.text(x0 + 16, -4.5, "3  Run the knife along the bottom skin\nin the crease. File the edge smooth.",
            ha="center", fontsize=7.4)
    save(fig, "fig-score-snap.svg")


def fig_angles():
    fig, ax = canvas(7.4, 3.7, (-2, 104), (-3, 48))
    bars = [
        ("A  1 × 1 × 1/16 in. angle, 8 ft", 96, [("back edge, top   W − 2", 42, 0), ("back edge, bottom   W − 2", 42, 0)]),
        ("B  1 × 1 × 1/16 in. angle, 8 ft", 96, [("back edge, side   H − 2-1/4", 21.75, 0), ("back edge, side", 21.75, 0),
                                                 ("", 3, 0), ("", 3, 0), ("", 3, 0), ("corners ×4, 3 in. each", 3, 0)]),
        ("C  1 × 1 × 1/16 in. angle, 8 ft", 96, [("clamp frame, top   W", 44, 0), ("clamp frame, bottom   W", 44, 0)]),
        ("D  1 × 1 × 1/16 in. angle, 8 ft", 96, [("clamp frame, side   H − 2", 22, 0), ("clamp frame, side", 22, 0)]),
        ("E  1-1/2 × 1-1/2 × 1/8 in. angle, 8 ft", 96, [("panel rail, top   W − 1/2", 43.5, 1), ("panel rail, bottom", 43.5, 1)]),
        ("F  1-1/2 × 1-1/2 × 1/8 in. angle, 4 ft", 48, [("cleat backing bar, 32", 32, 1), ("brackets ×2", 2, 1), ("", 2, 1)]),
    ]
    y = 44
    for title, length, cuts in bars:
        ax.text(0, y + 1.7, title, fontsize=7.4, weight="bold")
        ax.add_patch(Rectangle((0, y - 2.2), length, 2.6, fc="#eceef1", ec=MUTED, lw=0.6))
        x = 0
        for name, L, heavy in cuts:
            ax.add_patch(Rectangle((x, y - 2.2), L, 2.6, fc=NEW if heavy else ANGLE, ec=INK, lw=0.7))
            if name:
                inside = L > 14
                ax.text(x + L / 2 if inside else x + L + 3, y - 0.9, name, ha="center" if inside else "left",
                        va="center", fontsize=6.0, color="white" if inside else INK)
            x += L + 0.5
        y -= 7.5
    ax.text(0, -2, "Grey: thin 1/16 in. angle. Orange: thick 1/8 in. angle (these carry the weight). Lengths in inches.",
            fontsize=7, color=MUTED)
    save(fig, "fig-angles.svg")


def fig_rim():
    fig, ax = canvas(7.0, 4.0, (-6, 60), (-3, 33))
    s = Scene()
    rim(s)
    for x, sx in ((T, 1), (W - T, -1)):
        for z, sz in ((T, 1), (H - T, -1)):
            s.box(x if sx > 0 else x - 1.2, 0.5, z if sz > 0 else z - 0.15, 1.2, 3, 0.15, NEW)
            s.box(x if sx > 0 else x - 0.15, 0.5, z if sz > 0 else z - 1.2, 0.15, 3, 1.2, NEW)
    s.draw(ax)
    for i, (x, z) in enumerate(((T + 2.6, T + 2.6), (W - T - 2.6, T + 2.6), (T + 2.6, H - T - 2.6),
                                (W - T - 2.6, H - T - 2.6)), 1):
        tag(ax, proj(x, 0.5, z), i)
    note(ax, proj(W, D * 0.6, 14), (W + 5, 14), "side strip\n(H − 1/4) long,\nfits between\ntop and bottom")
    note(ax, proj(30, D * 0.6, H), (W + 5, H + 4), "top strip, W long")
    save(fig, "fig-rim.svg")


def fig_rivet():
    fig, ax = canvas(7.4, 2.3, (0, 120), (-7, 24))
    def plates(x0):
        ax.add_patch(Rectangle((x0, 10), 26, 2, fc=ACM, ec=INK, lw=0.8))
        ax.add_patch(Rectangle((x0, 8.3), 26, 1.7, fc=ANGLE, ec=INK, lw=0.8))
    plates(3)
    ax.add_patch(Rectangle((14.7, 12), 1.0, 9, fc="#cfa86b", ec=INK, lw=0.6))
    arrow(ax, (15.2, 22.5), (15.2, 13))
    ax.text(16, -4.5, "1  Clamp the parts together.\nDrill 3/16 in. through both.", ha="center", fontsize=7.4)
    plates(43)
    ax.add_patch(Rectangle((54.6, 12), 2.2, 0.7, fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((55.2, 7.0), 1.0, 5.0, fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((55.5, 12.7), 0.4, 6, fc="#777", ec=INK, lw=0.5))
    ax.text(56, -4.5, "2  Push the rivet in from the side\nyou can reach. Flange flat.", ha="center", fontsize=7.4)
    plates(83)
    ax.add_patch(Rectangle((94.6, 12), 2.2, 0.7, fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((95.2, 8.3), 1.0, 3.7, fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Polygon([(94.6, 8.3), (96.8, 8.3), (97.2, 6.6), (94.2, 6.6)], fc="#bdbdbd", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((94, 12.7), 3.4, 3, fc="#555", ec=INK, lw=0.5))
    ax.text(99, 14.2, "rivet tool", fontsize=6.5, va="center")
    ax.text(96, -4.5, "3  Squeeze the tool until the pin snaps.\nThe tail swells behind and locks.", ha="center", fontsize=7.4)
    save(fig, "fig-rivet.svg")


def fig_back():
    fig, ax = canvas(7.0, 4.3, (-6, 64), (-3, 37))
    s = Scene()
    rim(s)
    s.box(T + 1, D - 0.15, T, W - 2 - 2 * T, 0.15, 1, NEW)
    s.box(T + 1, D - 0.15, H - T - 1, W - 2 - 2 * T, 0.15, 1, NEW)
    s.box(T, D - 0.15, T + 1, 1, 0.15, H - 2 * T - 2, NEW)
    s.box(W - T - 1, D - 0.15, T + 1, 1, 0.15, H - 2 * T - 2, NEW)
    back(s, y=D + 7)
    s.draw(ax)
    for f in (0.3, 0.55, 0.8):
        arrow(ax, proj(W * f, D + 7, H + 1.0), proj(W * f, D + 1.0, H + 1.0), NEW, lw=1.6)
    note(ax, proj(W * 0.62, D - 0.15, H - T - 0.5), (W * 0.3, H + 9), "back-edge angles (orange), riveted inside the rim")
    note(ax, proj(W, D + 7, H * 0.55), (W + 10, H * 0.25), "back panel")
    save(fig, "fig-back.svg")


def fig_vents():
    fig, ax = canvas(7.4, 2.5, (-4, 50), (-3.5, 9.2))
    ax.add_patch(Rectangle((0, 0), W, D, fc=ACM, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((0, 0), W, 1.75, fc="#e7c79b", ec="none", alpha=0.6))
    ax.text(W / 2, 0.85, "front 1-3/4 in.: the panel rail goes here, keep clear", ha="center", va="center",
            fontsize=6.5, color="#7a4b10")
    for x0 in (4, 24):
        ax.add_patch(Rectangle((x0, 2.15), 16, 1.75, fc="white", ec=INK, lw=0.9, hatch="xx"))
        for cx, cy in ((x0, 2.15), (x0 + 16, 2.15), (x0, 3.9), (x0 + 16, 3.9)):
            ax.add_patch(Circle((cx, cy), 0.25, fc="none", ec=WARN, lw=0.8))
    ax.text(W / 2, D + 1.3, "TOP or BOTTOM strip, seen from outside. Front edge at the bottom of the picture.",
            ha="center", fontsize=7.5)
    dim(ax, (4, -1.0), (20, -1.0), "16 in.", off=(0, -0.9))
    dim(ax, (0, -1.0), (4, -1.0), "4", off=(0, -0.9))
    dim(ax, (20, -1.0), (24, -1.0), "4", off=(0, -0.9))
    dim(ax, (46, 2.15), (46, 3.9), "", off=(0, 0))
    ax.text(46.8, 3.0, "1-3/4", fontsize=7, color=MUTED, va="center")
    dim(ax, (-1.6, 0), (-1.6, 2.15), "", off=(0, 0))
    ax.text(-2.1, 1.07, "2-1/8", fontsize=6.5, color=MUTED, va="center", ha="right")
    ax.text(48.5, 0.9, "red circles:\n1/2 in. corner\nholes", fontsize=6.3, color=WARN, va="center")
    save(fig, "fig-vents.svg")


def fig_inside():
    fig, ax = canvas(7.4, 4.0, (-13, 64), (-3, 31))
    ax.add_patch(Rectangle((0, 0), W, H, fc=ACM, ec=INK, lw=1.2))
    ax.add_patch(Rectangle((T, T), W - 2 * T, H - 2 * T, fc="#f1f3f5", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((T + 0.2, H - T - 1.5), W - 2 * T - 0.4, 1.5, fc=NEW, ec=INK, lw=0.7))
    ax.add_patch(Rectangle((T + 0.2, T), W - 2 * T - 0.4, 1.5, fc=NEW, ec=INK, lw=0.7))
    ax.add_patch(Rectangle((6, H - 4.4), 32, 1.5, fc="none", ec=INK, lw=0.8, ls="--"))
    ax.add_patch(Rectangle((24, 7), 8.5, 4.5, fc=PSU, ec=INK, lw=0.8))
    ax.text(28.25, 9.25, "PSU", ha="center", va="center", fontsize=8, weight="bold")
    ax.add_patch(Rectangle((8, 4), 3.5, 2.3, fc=PI, ec=INK, lw=0.8))
    ax.text(9.75, 5.15, "Pi", ha="center", va="center", fontsize=7.5, color="white", weight="bold")
    for x0 in (4, 24):
        ax.add_patch(Rectangle((x0, -0.05), 16, 0.3, fc="white", ec=INK, lw=0.4, hatch="xx"))
        ax.add_patch(Rectangle((x0, H - 0.25), 16, 0.3, fc="white", ec=INK, lw=0.4, hatch="xx"))
    ax.add_patch(Circle((36, 2.3), 0.55, fc="#333", ec=INK, lw=0.6))
    ax.plot([36, 36, 32.5], [2.85, 8.5, 8.5], color=INK, lw=1.2)
    ax.add_patch(Circle((40, 4.3), 0.45, fc=EARTH, ec=INK, lw=0.6))
    ax.plot([40, 33.6, 33.6], [4.3, 4.3, 7], color=EARTH, lw=1.2)
    note(ax, (W - 6, H - 0.9), (W + 3, H + 2.2), "top panel rail")
    note(ax, (W - 6, 0.9), (W + 3, -1.6), "bottom panel rail")
    note(ax, (37, H - 3.6), (W + 3, H - 5), "cleat backing bar\n(on the back, dashed)")
    note(ax, (32.5, 10), (W + 3, 12), "PSU: 4 screws through\nthe back, silicone on each")
    note(ax, (8, 5), (-12.5, 12.5), "Pi on 4 nylon\nstandoffs")
    note(ax, (36, 2.3), (W + 3, 3.2), "mains cable gland,\nin the bottom strip")
    note(ax, (40, 4.3), (W + 3, 7.4), "earth: PSU earth terminal\nto a bare-metal rivet")
    save(fig, "fig-inside.svg")


def fig_panels_in():
    fig, ax = canvas(7.0, 4.0, (-6, 60), (-3, 33))
    s = Scene()
    back(s)
    rim(s)
    rails(s)
    panels(s, color=PANEL)
    s.draw(ax)
    note(ax, proj(22, 0.6, 22.1), (6, H + 5.5), "panel array, bolted to both rails")
    note(ax, proj(W - T - 1, 1.6, H - 1.0), (W + 5, H - 2.5), "top rail")
    note(ax, proj(W - T - 1, 1.6, 1.0), (W + 5, 1.5), "bottom rail")
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
    ax.text(-16, -7.8, "1  foam tape on the rim's front edge     2  your plastic sheet     "
            "3  clamp frame, screwed into well nuts", fontsize=7.4)
    save(fig, "fig-front.svg")


def fig_wellnut():
    fig, ax = canvas(7.4, 2.6, (0, 120), (-8, 24))
    ax.add_patch(Rectangle((10, 4), 3, 14, fc=ACM, ec=INK, lw=0.8))
    ax.add_patch(Rectangle((7, 9.6), 3, 2.8, fc="#222", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((10, 9.9), 5.5, 2.2, fc="#222", ec=INK, lw=0.6))
    ax.text(4, 15, "outside", fontsize=6.5, color=MUTED)
    ax.text(15, 15, "inside", fontsize=6.5, color=MUTED)
    ax.text(11, -4.5, "1  Push the well nut into a 3/8 in. hole\nfrom outside. Flange stays outside.",
            ha="center", fontsize=7.3)
    ax.add_patch(Rectangle((50, 4), 3, 14, fc=ACM, ec=INK, lw=0.8))
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
    ax.add_patch(Rectangle((x0 + 18, 2), 3, 18, fc=ACM, ec=INK, lw=0.8))
    ax.add_patch(Rectangle((x0 + 18, 19.4), 3, 0.6, fc=NEW, ec=INK, lw=0.4))
    ax.add_patch(Rectangle((x0 + 6, 20), 17, 0.9, fc=SHEET, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((x0 + 17.6, 20.9), 6.4, 0.5, fc=NEW, ec=INK, lw=0.4))
    ax.add_patch(Polygon([(x0 + 17, 21.4), (x0 + 25.2, 21.4), (x0 + 25.2, 13), (x0 + 24.3, 13),
                          (x0 + 24.3, 20.6), (x0 + 17, 20.6)], fc=ANGLE, ec=INK, lw=0.6))
    ax.text(x0 + 11, 22.5, "plastic sheet", fontsize=6.6, ha="center")
    ax.text(x0 + 26, 17, "clamp\nframe", fontsize=6.6)
    ax.text(x0 + 17, 9, "rim\nstrip", fontsize=6.6, ha="right")
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
    fig, ax = canvas(7.4, 3.7, (-4, 66), (-6.5, 29))
    ax.add_patch(Rectangle((0, 0), W, H, fc=ACM, ec=INK, lw=1.2))
    ax.add_patch(Rectangle((6, H - 4.4), 32, 1.5, fc="none", ec=INK, lw=0.8, ls="--"))
    ax.add_patch(Rectangle((7, H - 4.2), 30, 1.1, fc=NEW, ec=INK, lw=0.8))
    for xb in (9, 15.5, 22, 28.5, 35):
        ax.add_patch(Circle((xb, H - 3.65), 0.22, fc="white", ec=INK, lw=0.5))
    for x in (6, W - 8):
        ax.add_patch(Rectangle((x, -1.6), 2, 1.6, fc=NEW, ec=INK, lw=0.8))
    ax.add_patch(Rectangle((11.5, 7), 8.5, 4.5, fc="none", ec=MUTED, lw=0.6, ls=":"))
    ax.text(15.75, 9.25, "PSU screw heads\n(sealed)", ha="center", va="center", fontsize=6.5, color=MUTED)
    ax.text(W / 2, H + 1.4, "BACK OF THE CASE (seen from behind)", ha="center", fontsize=8, weight="bold")
    note(ax, (36, H - 3.65), (W + 3, H + 1.5), "case half of the 30 in. Z-bar,\nhook pointing DOWN, centred,\n"
         "bolted through the back\nand the backing bar")
    note(ax, (W - 7, -0.8), (W + 3, -2.5), "anti-lift brackets\n(on the bottom)")
    dim(ax, (7, H + 3.8), (37, H + 3.8), "30 in., centred", off=(0, 0.9))
    save(fig, "fig-back-view.svg")


def fig_wall():
    fig, ax = canvas(7.4, 3.9, (-6, 62), (-13, 32))
    ax.add_patch(Rectangle((-5, -12), 60, 43, fc=BRICK, ec=INK, lw=0.8))
    for r in range(-12, 31, 2):
        ax.plot([-5, 55], [r, r], color=MORTAR, lw=0.8)
        off = 0 if (r // 2) % 2 == 0 else 2
        for c in range(-5 + off, 55, 4):
            if r + 2 <= 31:
                ax.plot([c, c], [r, r + 2], color=MORTAR, lw=0.8)
    ax.add_patch(Rectangle((0, 0), W, H, fc="none", ec="white", lw=1.4, ls="--"))
    ax.text(W / 2, H / 2 - 2, "case outline\n(painter's tape)", ha="center", va="center", color="white", fontsize=8.5)
    ax.plot([-3, W + 3], [H - 3.1, H - 3.1], color="#ffe14d", lw=1.4)
    ax.text(W + 3.3, H - 3.1, "level line", color="#ffe14d", va="center", fontsize=7.5)
    ax.add_patch(Rectangle((7, H - 3.7), 30, 1.1, fc=NEW, ec=INK, lw=0.8))
    for xa in (9, 17, 27, 35):
        ax.add_patch(Circle((xa, H - 3.15), 0.32, fc="#333", ec=INK, lw=0.5))
    for x in (6, W - 8):
        ax.add_patch(Circle((x + 1, -1.0), 0.32, fc="#333", ec=INK, lw=0.5))
        ax.add_patch(Rectangle((x, -1.6), 2, 1.6, fc="none", ec="white", lw=1.0))
    ax.text(-4, -7.5, "Wall half of the Z-bar, hook pointing UP, 4 anchors into whole bricks.", fontsize=7.2, color="white")
    ax.text(-4, -9.6, "Bracket anchors (white boxes) are drilled last, after the case is hanging.", fontsize=7.2, color="white")
    save(fig, "fig-wall.svg")


def fig_hang():
    fig, ax = canvas(7.4, 2.9, (0, 120), (-9, 31))
    for x0, title, mode in ((0, "1  Two people lift the case\nso its cleat is above the wall cleat", "up"),
                            (42, "2  Lower it straight down until\nthe two cleats hook together", "down"),
                            (84, "3  Bolt the anti-lift brackets:\nwall anchor, then case bottom", "bracket")):
        ax.add_patch(Rectangle((x0 + 2, -4), 5, 34, fc=BRICK, ec=INK, lw=0.6))
        lift = 3 if mode == "up" else 0
        cx = x0 + 7.6
        ax.add_patch(Rectangle((cx, 2 + lift), 5, 22, fc=ACM, ec=INK, lw=0.8))
        ax.add_patch(Rectangle((cx + 5, 2 + lift), 0.3, 22, fc=SHEET, ec=INK, lw=0.5))
        ax.add_patch(Rectangle((x0 + 7, 20), 0.5, 2.2, fc=ANGLE, ec=INK, lw=0.5))
        ax.add_patch(Rectangle((cx - 0.15, 21.0 + lift), 0.45, 1.8, fc=NEW, ec=INK, lw=0.5))
        if mode == "up":
            arrow(ax, (cx + 9, 17), (cx + 9, 23))
        elif mode == "down":
            arrow(ax, (cx + 9, 23), (cx + 9, 17))
        else:
            ax.add_patch(Polygon([(x0 + 7, 0.2), (x0 + 7, 2.8), (x0 + 7.4, 2.8), (x0 + 7.4, 0.6),
                                  (cx + 2.6, 0.6), (cx + 2.6, 2.0), (cx + 3.0, 2.0), (cx + 3.0, 0.2)],
                                 fc=NEW, ec=INK, lw=0.5))
        ax.text(x0 + 14, -7.4, title, ha="center", fontsize=7.4)
    save(fig, "fig-hang.svg")


def fig_bracket():
    fig, ax = canvas(7.4, 2.2, (-12, 66), (-5, 14))
    ax.add_patch(Polygon([(0, 0), (0, 10), (1, 10), (1, 1), (10, 1), (10, 0)], fc=ANGLE, ec=INK, lw=0.9))
    ax.add_patch(Circle((0.5, 6.5), 0.35, fc="white", ec=INK, lw=0.6))
    ax.add_patch(Circle((6.5, 0.5), 0.3, fc="white", ec=INK, lw=0.6))
    ax.text(-1, 6.5, "1/4 in. hole\n(wall anchor)", ha="right", va="center", fontsize=7)
    ax.text(6.5, -1.4, "#10 hole (case bottom,\ninto a well nut)", ha="center", va="top", fontsize=7)
    ax.text(-11, 12.6, "Anti-lift bracket: a 2 in. long piece of 1-1/2 in. angle (side view)", fontsize=7.5, weight="bold")
    ax.add_patch(Rectangle((26, 1), 1.3, 10, fc=BRICK, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((28, 3), 5, 8, fc=ACM, ec=INK, lw=0.7))
    ax.add_patch(Polygon([(27.3, 0.3), (27.3, 3.6), (27.6, 3.6), (27.6, 0.6), (30.9, 0.6), (30.9, 3),
                          (31.2, 3), (31.2, 0.3)], fc=NEW, ec=INK, lw=0.6))
    ax.text(35, 6, "One leg flat on the wall, the other\nunder the case. With the case hanging,\n"
            "it cannot be lifted off the cleat or\npulled away at the bottom.", fontsize=7.2, va="center")
    save(fig, "fig-bracket.svg")


if __name__ == "__main__":
    for f in (fig_overview, fig_mounted, fig_cutlist, fig_score_snap, fig_angles, fig_rim,
              fig_rivet, fig_back, fig_vents, fig_inside, fig_panels_in, fig_front,
              fig_wellnut, fig_seal, fig_back_view, fig_wall, fig_hang, fig_bracket):
        f()
