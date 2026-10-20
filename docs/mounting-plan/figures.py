#!/usr/bin/env python3
"""Drawings for the mounting and case build plan (fig-*.svg next to this file).

    /opt/homebrew/bin/python3 docs/mounting-plan/figures.py

All dimensions in millimetres. These are design-intent drawings for review and
quoting, not fabrication drawings: final dimensions come from CAD once the
panel assembly and PSU are measured.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5,
                     "svg.fonttype": "path"})

INK = "#1d1d1f"
AL = "#c9ced6"        # aluminium
AL_DARK = "#8f97a3"
BRICK = "#c96f4a"
MORTAR = "#e9e2d6"
POLY = "#9fd3e6"
LED = "#2b2b2b"
EPOXY = "#e3b23c"
SS = "#5a6270"
GASKET = "#222222"
AIR = "#2a7fbf"
DIM = "#6b6b6b"
NOTE = "#b3261e"

# Case envelope (outer), mm
W, H, D = 1100, 600, 120
STANDOFF = 13              # Z-clip pair projection, about 1/2 in
HOOD = 25


def new(w_in, h_in):
    fig = plt.figure(figsize=(w_in, h_in))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def rect(ax, x, y, w, h, fc, ec=INK, lw=0.8, z=2):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=z))


def label(ax, xy, text_xy, s, ha="left", color=INK, size=7.2):
    ax.annotate(s, xy=xy, xytext=text_xy, fontsize=size, ha=ha, va="center",
                color=color, zorder=20,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=DIM,
                                shrinkA=1, shrinkB=0))


def dim_h(ax, x0, x1, y, s, above=True):
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", lw=0.6, color=DIM), zorder=15)
    ax.text((x0 + x1) / 2, y + (7 if above else -7), s, ha="center",
            va="bottom" if above else "top", color=DIM, fontsize=7)


def dim_v(ax, x, y0, y1, s, right=True):
    ax.annotate("", xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", lw=0.6, color=DIM), zorder=15)
    ax.text(x + (6 if right else -6), (y0 + y1) / 2, s, ha="left" if right else "right",
            va="center", color=DIM, fontsize=7, rotation=90)


def air(ax, pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                     mutation_scale=7, lw=1.1, color=AIR, zorder=12))


def save(fig, name):
    fig.savefig(os.path.join(HERE, name), bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- fig 1
# Side section through the mounted case, wall on the left.

def fig_section():
    fig, ax = new(7.6, 6.2)
    ax.set_xlim(-345, 470)
    ax.set_ylim(-70, 735)

    # brick wall with mortar courses
    rect(ax, -130, -60, 130, 770, BRICK, lw=0.8, z=1)
    for y in range(-60, 710, 57):
        ax.plot([-130, 0], [y, y], color=MORTAR, lw=1.6, zorder=1.5)
    ax.text(-65, 690, "BRICK WALL", ha="center", fontsize=7, color="white", weight="bold")

    x0 = STANDOFF            # case back face
    x1 = x0 + D              # case front face

    # anchors: top set at the rail, bottom set at the brackets
    def anchor(y):
        rect(ax, -90, y - 6, 90, 12, EPOXY, lw=0.5, z=2.5)        # epoxy
        rect(ax, -86, y - 4.8, 100, 9.6, SS, lw=0.4, z=3)          # 3/8 rod
        rect(ax, 5, y - 9, 4, 18, SS, lw=0.4, z=3)                 # nut + washer
    anchor(548)
    anchor(30)

    # wall Z-clip (hooks up) and case Z-clip (hooks down)
    ax.add_patch(Polygon([(0, 515), (4, 515), (4, 562), (10, 568), (10, 582), (6, 582),
                          (6, 572), (0, 566)], fc=AL_DARK, ec=INK, lw=0.6, zorder=6))
    ax.add_patch(Polygon([(x0, 600), (x0 - 4, 600), (x0 - 4, 590), (x0 - 10, 584),
                          (x0 - 10, 572), (x0 - 6, 572), (x0 - 6, 580), (x0, 586)],
                         fc=AL, ec=INK, lw=0.6, zorder=6))

    # bottom anti-lift bracket: L from wall to case bottom, screwed into a rivnut
    ax.add_patch(Polygon([(0, 12), (x0 + 30, 12), (x0 + 30, 16), (4, 16), (4, 48), (0, 48)],
                         fc=AL_DARK, ec=INK, lw=0.6, zorder=6))

    # case shell
    rect(ax, x0, 0, 2, H, AL, lw=0.7, z=5)                 # back skin
    rect(ax, x0, H - 2, D, 2, AL, lw=0.7, z=5)              # top skin
    rect(ax, x0, 0, D, 2, AL, lw=0.7, z=5)                  # bottom skin
    rect(ax, x1 - 2, H - 40, 2, 40, AL, lw=0.7, z=7)        # bezel lips
    rect(ax, x1 - 2, 0, 2, 40, AL, lw=0.7, z=7)
    rect(ax, x1 - 7, 22, 4.5, H - 44, POLY, lw=0.6, z=6)    # polycarbonate
    rect(ax, x1 - 2.6, 24, 0.6, 12, GASKET, lw=0, z=8)
    rect(ax, x1 - 2.6, H - 36, 0.6, 12, GASKET, lw=0, z=8)

    # frame (1x1 in. angle) at the four corners of the section
    for (cx, cy, sx, sy) in ((x0 + 2, 2, 1, 1), (x0 + 2, H - 2, 1, -1),
                             (x1 - 9, 2, -1, 1), (x1 - 9, H - 2, -1, -1)):
        ax.add_patch(Polygon([(cx, cy), (cx + 25 * sx, cy), (cx + 25 * sx, cy + 3 * sy),
                              (cx + 3 * sx, cy + 3 * sy), (cx + 3 * sx, cy + 25 * sy),
                              (cx, cy + 25 * sy)], fc=AL_DARK, ec=INK, lw=0.5, zorder=6))

    # LED panels on their aluminium backplates
    rect(ax, x1 - 26, 44, 16, H - 88, LED, lw=0.5, z=4)
    rect(ax, x1 - 29, 44, 3, H - 88, AL, lw=0.5, z=4)

    # electronics tray, PSU, Pi
    rect(ax, x0 + 30, 60, 3, 380, AL, lw=0.5, z=4)
    rect(ax, x0 + 33, 250, 50, 183, "#f2f2f2", lw=0.7, z=4)
    ax.text(x0 + 58, 341, "PSU", rotation=90, ha="center", va="center", fontsize=7)
    rect(ax, x0 + 33, 90, 22, 85, "#3f8f4f", lw=0.6, z=4)
    ax.text(x0 + 44, 132, "Pi", rotation=90, ha="center", va="center", fontsize=6.5,
            color="white")

    # vents: bottom intake slots, top exhaust under the hood
    for xv in range(x0 + 22, x0 + 95, 9):
        rect(ax, xv, -0.5, 5, 3, "white", ec="white", lw=0, z=8)
        rect(ax, xv, H - 2.5, 5, 3, "white", ec="white", lw=0, z=8)
    ax.add_patch(Polygon([(x0 - 2, H), (x0 - 2, H + HOOD), (x1 + 12, H + HOOD),
                          (x1 + 12, H + 8), (x1 + 9, H + 8), (x1 + 9, H + HOOD - 3),
                          (x0 + 1, H + HOOD - 3), (x0 + 1, H)],
                         fc=AL, ec=INK, lw=0.6, zorder=7))

    # airflow
    air(ax, [(x0 + 60, -45), (x0 + 60, -5)])
    air(ax, [(x0 + 70, 20), (x0 + 82, 300), (x0 + 75, 560), (x0 + 70, H - 6)])
    air(ax, [(x0 + 60, H + 10), (x1 + 4, H + 14), (x1 + 30, H + 6)])

    # labels
    L = 175
    label(ax, (-45, 548), (-340, 548), "3/8 in. 316 stainless\nrod in SET-3G epoxy\n(4 at the rail)")
    label(ax, (-45, 30), (-340, 30), "same anchor at each\nbottom bracket (2)")
    label(ax, (6, 575), (-340, 650), "Z-clip pair\n(Monarch MFSTR-050):\nwall rail hooks up,\ncase rail hooks down")
    label(ax, (x0 + 25, 14), (L, -40), "anti-lift bracket: pin-in Torx screw\ninto a rivnut in the case bottom")
    label(ax, (x1 + 5, H + 20), (L + 120, H + 75), "rain hood over the exhaust slots")
    label(ax, (x0 + 80, H - 1), (L + 120, H + 35), "top exhaust slots + insect mesh")
    label(ax, (x0 + 50, 1), (L + 120, 20), "bottom intake slots + insect mesh")
    label(ax, (x1 - 5, 300), (L + 120, 300), "UV-protected polycarbonate,\n3/16 in., held by gaskets only")
    label(ax, (x1 - 18, 420), (L + 120, 410), "LED panels on existing\naluminium backplates")
    label(ax, (x0 + 58, 400), (L + 120, 510), "PSU and Pi on a removable\nelectronics tray")
    label(ax, (x0 + 10, 26), (L + 120, 110), "1 x 1 x 1/8 in. 6061 angle frame\n(carries all loads)")
    label(ax, (x0 + 1, 200), (L + 120, 200), "0.080 in. 5052 aluminium skins,\npowder-coated, EPDM gasketed")

    dim_v(ax, x1 + 40, 0, H, f"{H} mm (23.6 in.)")
    dim_h(ax, x0, x1, -58, f"{D} mm (4.7 in.)", above=False)
    ax.annotate("", xy=(0, 640), xytext=(x0, 640),
                arrowprops=dict(arrowstyle="<->", lw=0.6, color=DIM), zorder=15)
    ax.text(x0 + 4, 640, "≈13 mm standoff", va="center", color=DIM, fontsize=7)
    ax.text(-340, 728, "Air enters at the bottom, rises past the PSU and Pi, and leaves under the hood.",
            fontsize=7, color=AIR)
    save(fig, "fig-section.svg")


# ---------------------------------------------------------------- fig 2
# Front elevation with hidden mounting hardware.

def fig_front():
    fig, ax = new(7.2, 4.4)
    ax.set_xlim(-120, W + 120)
    ax.set_ylim(-150, H + 40)

    rect(ax, 0, 0, W, H, AL, lw=1.0, z=2)
    ow, oh = 1034, 522
    ox, oy = (W - ow) / 2, (H - oh) / 2
    rect(ax, ox, oy, ow, oh, "#1a1a1a", lw=0.8, z=3)
    for i in range(1, 4):
        ax.plot([ox + 5 + i * 256, ox + 5 + i * 256], [oy + 5, oy + oh - 5], color="#444", lw=0.6, zorder=4)
        ax.plot([ox + 5, ox + ow - 5], [oy + 5 + i * 128, oy + 5 + i * 128], color="#444", lw=0.6, zorder=4)
    ax.text(W / 2, H / 2 - 25, "16 panels, 1024 x 512 mm active area", ha="center", va="center",
            color="#bbbbbb", fontsize=8, zorder=5)
    for yy in ((0, oy), (oy + oh, H)):
        ax.plot([W / 2, W / 2], yy, color=INK, lw=0.8, zorder=4)
    ax.text(W / 2 + 8, -18, "bezel seam (splice plate behind)", fontsize=6.5, va="center", zorder=6)
    rect(ax, -6, H, W + 12, HOOD, AL_DARK, lw=0.8, z=2)
    ax.text(W / 2, H + HOOD / 2, "rain hood", ha="center", va="center", fontsize=6.5, zorder=6)

    ax.plot([100, W - 100], [H - 52, H - 52], color=NOTE, lw=1.0, ls=(0, (6, 3)), zorder=6)
    for xa in (130, 400, 700, 970):
        ax.add_patch(plt.Circle((xa, H - 52), 9, fc="none", ec=NOTE, lw=1.0, ls="--", zorder=6))
    for xb in (180, W - 180):
        rect(ax, xb - 25, 6, 50, 30, "none", ec=NOTE, lw=1.0, z=6)
        ax.add_patch(plt.Circle((xb, 21), 7, fc="none", ec=NOTE, lw=1.0, ls="--", zorder=6))
        ax.text(xb, 48, "anti-lift bracket", ha="center", color=NOTE, fontsize=6.5, zorder=6)
    ax.text(W / 2, H - 72, "wall Z-rail, about 900 mm, 4 anchors (hidden, behind the case)",
            ha="center", color=NOTE, fontsize=6.8, zorder=6, va="top")

    dim_h(ax, 0, W, -55, "1,100 mm (43.3 in.)", above=False)
    dim_h(ax, ox, ox + ow, -105, "window opening 1,034 mm", above=False)
    dim_v(ax, W + 40, 0, H, "600 mm (23.6 in.)")
    dim_v(ax, -40, oy, oy + oh, "522 mm", right=False)
    save(fig, "fig-front.svg")


# ---------------------------------------------------------------- fig 3
# Every flat sheet-metal part against the powder-coat size limit.

PARTS = [  # name, qty, flat width mm, flat height mm
    ("Front bezel half", 2, 565, 630),
    ("Back panel half", 2, 580, 630),
    ("Top skin half", 2, 580, 150),
    ("Bottom skin half", 2, 580, 150),
    ("Side skin", 2, 150, 630),
    ("Rain hood half", 2, 580, 75),
    ("Electronics tray", 1, 520, 300),
    ("Service hatch", 1, 220, 120),
    ("Bezel splice plate", 2, 120, 60),
    ("Corner gusset", 8, 80, 80),
]


def fig_parts():
    LIMIT_W, LIMIT_H = 914, 762          # 36 x 30 in. powder-coat limit
    fig, ax = new(7.2, 4.0)
    cols = 5
    cell_w, cell_h = 990, 1000
    rows = (len(PARTS) + cols - 1) // cols
    ax.set_xlim(-30, cols * cell_w)
    ax.set_ylim(-rows * cell_h - 60, 90)
    for i, (name, qty, w, h) in enumerate(PARTS):
        cx, cy = (i % cols) * cell_w, -(i // cols) * cell_h
        rect(ax, cx, cy - LIMIT_H, LIMIT_W, LIMIT_H, "none", ec=DIM, lw=0.6, z=1)
        if h > LIMIT_H:                   # turned to fit, as it would be nested
            w, h = h, w
        ok = w <= LIMIT_W and h <= LIMIT_H
        rect(ax, cx + 20, cy - 20 - h, w, h, "#dfe4ea", ec="#2d6a3e" if ok else NOTE, lw=1.0, z=2)
        ax.text(cx, cy + 95, f"{name} ×{qty}", fontsize=6.4, va="bottom", weight="bold")
        ax.text(cx, cy + 20, f"{max(w, h)} × {min(w, h)} mm flat", fontsize=6.0, va="bottom",
                color="#2d6a3e" if ok else NOTE)
    save(fig, "fig-parts.svg")


# ---------------------------------------------------------------- fig 4
# Window retention detail (bottom edge, enlarged).

def fig_window():
    fig, ax = new(4.4, 3.0)
    ax.set_xlim(-30, 100)
    ax.set_ylim(-10, 62)
    rect(ax, 60, 0, 2, 50, AL, lw=0.8, z=5)
    rect(ax, 0, 0, 62, 2, AL, lw=0.8, z=5)
    rect(ax, 51, 8, 4.5, 54, POLY, lw=0.7, z=4)
    rect(ax, 55.5, 10, 4.5, 26, GASKET, lw=0, z=6)
    rect(ax, 46.5, 10, 4.5, 26, GASKET, lw=0, z=6)
    ax.add_patch(Polygon([(30, 2), (46.5, 2), (46.5, 38), (43.5, 38), (43.5, 5), (30, 5)],
                         fc=AL_DARK, ec=INK, lw=0.6, zorder=6))
    rect(ax, 36, 2, 4, 7, SS, lw=0.4, z=7)
    ax.annotate("", xy=(53, 2.3), xytext=(53, 7.7),
                arrowprops=dict(arrowstyle="<->", lw=0.5, color=NOTE))
    label(ax, (53, 55), (68, 58), "polycarbonate", size=6.5)
    label(ax, (61, 44), (68, 48), "bezel lip", size=6.5)
    label(ax, (57.7, 30), (68, 36), "EPDM gasket, front", size=6.5)
    label(ax, (48.7, 20), (20, 28), "EPDM gasket,\nrear", size=6.5, ha="right")
    label(ax, (44.5, 34), (20, 44), "retainer angle,\nscrewed to rivnuts", size=6.5, ha="right")
    label(ax, (53, 5), (68, 10), "about 5 mm free edge\nfor expansion", size=6.5, color=NOTE)
    save(fig, "fig-window.svg")


if __name__ == "__main__":
    fig_section()
    fig_front()
    fig_parts()
    fig_window()
