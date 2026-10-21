#!/usr/bin/env python3
"""Pictures for sheets 2-4 of the wiring document (fig-*.svg next to this file).

    /opt/homebrew/bin/python3 docs/wiring/figures.py

Wire colours match sheet 1 (rpi5/tools/make-wiring-diagram.py). The load
estimates come from rendering real board frames and scaling by the E90
figure of 5 A per panel at full white; see LOAD below.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "svg.fonttype": "path"})

V5 = "#d62728"
GND = "#111111"
DATA = "#0b7a75"
L_COL = "#8b4513"
N_COL = "#1f4fd1"
PE_COL = "#2e8b57"
INK = "#1d1d1f"
MUTED = "#6b6b6b"
FAINT = "#b0b0b0"
RATING = "#6a3d9a"
STEP = "#f28c28"         # a recommended change
STEP_D = "#b25d0a"
SHARED = "#fde3c8"       # wire both loads share
PANEL = "#f4f4f4"
OK = "#2d6a3e"
WARN = "#b3261e"


def sheet(w, h, x1, y1):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, x1)
    ax.set_ylim(0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, label=None, size=8, fill="white", lw=1.3, color=INK,
        weight="bold", rounded=True):
    style = "round,pad=0,rounding_size=0.8" if rounded else "square,pad=0"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fill, ec=color, lw=lw))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=size,
                weight=weight, color=INK, linespacing=1.25)


def line(ax, pts, color, lw=1.6, ls="-", z=2):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="round", zorder=z)


def pair(ax, pts, off=0.6, lw=1.8):
    line(ax, pts, V5, lw=lw)
    line(ax, [(x + off, y - off) for x, y in pts], GND, lw=lw * 0.8)


def arrow(ax, x0, y0, x1, y1, color, lw=1.6, ms=10):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=4,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                mutation_scale=ms, shrinkA=0, shrinkB=0))


def badge(ax, x, y, n, color=INK, r=1.5):
    ax.add_patch(Circle((x, y), r, fc=color, ec="white", lw=1.2, zorder=8))
    ax.text(x, y - 0.05, str(n), ha="center", va="center", fontsize=8.5,
            weight="bold", color="white", zorder=9)


def tag(ax, x, y, s, size=7, ha="left", color=RATING, weight="bold"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=size, color=color, weight=weight,
            zorder=7, linespacing=1.2,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))


def resistor(ax, x0, x1, y, color, label=None, n=5, amp=0.9):
    """A horizontal zigzag between x0 and x1: wire resistance drawn as a part."""
    lead = (x1 - x0) * 0.2
    xs = [x0, x0 + lead]
    ys = [y, y]
    step = (x1 - x0 - 2 * lead) / (2 * n)
    for i in range(2 * n):
        xs.append(x0 + lead + step * (i + 0.5))
        ys.append(y + (amp if i % 2 == 0 else -amp))
    xs += [x1 - lead, x1]
    ys += [y, y]
    ax.plot(xs, ys, color=color, lw=1.6, zorder=3, solid_joinstyle="miter")
    if label:
        ax.text((x0 + x1) / 2, y + 1.6, label, ha="center", va="bottom", fontsize=6.8,
                color=MUTED, linespacing=1.2)


def panels(ax, x, y, cols=4, rows=4, w=7.4, h=4.4, gap=0.7):
    """A small 4 x 4 array from (x, y) up; returns each row's mid-height."""
    mids = []
    for r in range(rows):
        top = y + rows * (h + gap) - r * (h + gap)
        for c in range(cols):
            px = x + c * (w + gap)
            ax.add_patch(Rectangle((px, top - h), w, h, fc=PANEL, ec=INK, lw=0.9))
        mids.append(top - h / 2)
    ax.text(x + (cols * (w + gap) - gap) / 2, y - 0.6, "16 LED panels, 4 rows of 4",
            ha="center", va="top", fontsize=7.2, weight="bold")
    return mids


def save(fig, name):
    fig.savefig(os.path.join(HERE, f"fig-{name}.svg"))
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- overview

def fig_overview():
    fig, ax = sheet(11, 4.8, 112, 48.9)

    box(ax, 2, 13, 15, 12, "WALL\nOUTLET\n120 V AC", size=8)
    badge(ax, 3.6, 25.4, 1)
    for y, c in ((21.5, L_COL), (19, N_COL), (16.5, PE_COL)):
        line(ax, [(17, y), (28, y)], c, ls=(0, (3, 2)) if c == PE_COL else "-")
    ax.add_patch(Rectangle((20.4, 20.7), 2.6, 1.6, fc="white", ec=INK, lw=0.9, zorder=3))
    ax.text(21.7, 23.0, "F1 fuse,\nS1 switch", ha="center", va="bottom", fontsize=6.3, color=MUTED)
    ax.text(22.5, 14.8, "L, N, earth", ha="center", va="top", fontsize=6.3, color=MUTED)

    box(ax, 28, 10, 15, 18, "PSU\n\n120 V AC in\n5 V DC out\n100 A max", size=7.5)
    badge(ax, 29.6, 28.4, 2)

    pair(ax, [(43, 20), (53, 20)], lw=2.6)
    ax.text(48, 21.6, "main feed", ha="center", fontsize=6.8, color=MUTED)

    box(ax, 53, 8, 10, 22, None, rounded=False)
    ax.add_patch(Rectangle((55.2, 10), 1.3, 18, fc="#ffd0d0", ec=V5, lw=0.9, zorder=3))
    ax.add_patch(Rectangle((59.6, 10), 1.3, 18, fc="#d8d8d8", ec=GND, lw=0.9, zorder=3))
    ax.text(58, 6.8, "distribution\nblock", ha="center", va="top", fontsize=7, weight="bold")
    badge(ax, 54.6, 30.4, 3)

    mids = panels(ax, 80, 6)
    for i, ym in enumerate(mids):
        xch = 66 + i * 1.6
        pair(ax, [(63, 26 - i * 4.4), (xch, 26 - i * 4.4), (xch, ym + 1.6), (80, ym + 1.6)], lw=1.4)
    ax.text(71.5, 5.0, "4 branches,\none per row", ha="center", va="center", fontsize=6.6, color=MUTED)
    badge(ax, 68.4, 28.4, 4)

    box(ax, 30, 37, 13, 8.5, "Raspberry\nPi 5", size=7.5)
    box(ax, 47, 37, 13, 8.5, "Active3\nbonnet", size=7.5)
    badge(ax, 31.6, 45.9, 5)
    line(ax, [(43, 41.6), (47, 41.6)], "#777777", lw=1.0)
    line(ax, [(43, 40.6), (47, 40.6)], "#777777", lw=1.0)
    ax.text(45, 43.2, "GPIO", ha="center", fontsize=6, color="#777777")
    line(ax, [(55.85, 30), (55.85, 34), (51.5, 34), (51.5, 37)], V5, lw=1.4)
    line(ax, [(60.25, 30), (60.25, 34.8), (54.5, 34.8), (54.5, 37)], GND, lw=1.2)
    ax.text(61.4, 32.6, "Pi feed", fontsize=6.6, color=V5)

    for k, row in enumerate((0, 2)):
        yy = 43.5 - k * 2.2
        ych = mids[row] - 0.6
        xch = 75 + k * 1.6
        line(ax, [(60, yy), (xch, yy), (xch, ych), (78.2, ych)], DATA, lw=1.8, z=3)
        arrow(ax, 78, ych, 80, ych, DATA)
    ax.text(68, 45.6, "data, 2 chains of 8", ha="center", fontsize=6.6, color=DATA, weight="bold")
    badge(ax, 61.8, 46.4, 6, color=DATA)

    save(fig, "overview")


# ------------------------------------------------------------- why it sags

def fig_sag():
    fig, ax = sheet(11, 4.4, 112, 44)

    ax.add_patch(Rectangle((14.5, 22.4), 29, 7.6, fc=SHARED, ec="none", zorder=1))
    ax.text(29, 31.0, "SHARED WIRING", ha="center", fontsize=7.5, weight="bold", color=STEP_D)

    box(ax, 2, 15, 12, 18, "PSU\n5.00 V", size=8.5)
    line(ax, [(14, 25.7), (17, 25.7)], V5)
    resistor(ax, 17, 33, 25.7, V5, "main feed wire\n+ connections")
    line(ax, [(33, 25.7), (42, 25.7)], V5)
    ax.plot([42], [25.7], "o", ms=5, color=V5, zorder=5)
    ax.text(40.8, 23.3, "block", ha="right", va="center", fontsize=7, weight="bold")

    line(ax, [(42, 25.7), (42, 13)], V5)
    box(ax, 33, 3, 18, 10, "16 PANELS\n8 A normal board\n80 A all white", size=7.3)
    arrow(ax, 45.5, 22.5, 45.5, 14.5, V5, lw=2.6, ms=14)
    ax.text(47, 18.5, "big, changing\ncurrent", fontsize=6.8, color=V5, va="center")

    line(ax, [(42, 25.7), (52, 25.7)], V5)
    resistor(ax, 52, 64, 25.7, V5, "Pi tap\nwire")
    resistor(ax, 64, 76, 25.7, V5, "bonnet +\nheader pins")
    line(ax, [(76, 25.7), (80, 25.7)], V5)
    box(ax, 80, 18, 14, 15, "Pi 5\n+ bonnet\n1–3 A", size=8)

    ax.text(2, 39.5, "Volts at the Pi, measured:", fontsize=7.6, weight="bold", va="center")
    tag(ax, 25, 39.5, "4.99 V on a dark screen", size=7.6, color=OK)
    tag(ax, 47, 39.5, "4.64 V on a white screen", size=7.6, color=WARN)
    ax.text(70, 39.5, "(throttles below 4.63 V)", fontsize=7.4, color=MUTED, va="center")

    ax.text(97, 33, "Volts lost in a wire\n= current × resistance",
            ha="left", va="top", fontsize=7.4, weight="bold")
    ax.text(97, 27.6, "More panel current\nmeans more volts lost\nin the shared wiring,\n"
            "so less is left\nfor the Pi.\n\nThe PSU holds 5.00 V\nat its own terminals;\n"
            "the loss is all in\nthe wiring after it.",
            ha="left", va="top", fontsize=6.8, color=MUTED, linespacing=1.3)

    line(ax, [(8, 15), (8, 1.2), (42, 1.2), (42, 3)], GND, lw=1.4)
    line(ax, [(87, 18), (87, 1.2), (51, 1.2)], GND, lw=1.4)
    ax.text(69, 2.4, "0 V return path: shared as well, so it loses volts the same way",
            ha="center", fontsize=6.6, color=MUTED)

    save(fig, "sag")


# ------------------------------------------------------------ load chart

# Amps for the whole array. "estimate" rows are rendered board frames scaled
# by 5 A per panel at full white (E90): LED current only, linear in pixel
# value, panel logic not included. The 16 A and 80 A rows are E90 figures.
LOAD = [
    ("Overnight, dimmed to 25 %", 1.9, "estimate from rendered frames"),
    ("Normal board, two trains each way", 7.9, "estimate from rendered frames"),
    ("E90 typical, about 1 A per panel", 16, "E90 report"),
    ("Full-white test screen", 80, "E90 report"),
]
CAP = 30


def fig_load():
    fig = plt.figure(figsize=(7.4, 2.7))
    ax = fig.add_axes([0.36, 0.2, 0.6, 0.72])
    ys = list(range(len(LOAD)))[::-1]
    for y, (lab, a, kind) in zip(ys, LOAD):
        over = a > CAP
        ax.barh(y, a, height=0.5, color="#d5d9df" if over else "#5b7083", zorder=2)
        if over:
            ax.barh(y, CAP, height=0.5, color="#5b7083", zorder=3)
        ax.text(a + 1.2, y, f"{a:g} A", va="center", fontsize=8, weight="bold", color=INK)
        ax.text(-1.5, y + 0.13, lab, va="center", ha="right", fontsize=8, color=INK)
        ax.text(-1.5, y - 0.2, kind, va="center", ha="right", fontsize=6.6, color=MUTED)
    ax.axvline(CAP, color=STEP, lw=1.6, ls=(0, (4, 2)), zorder=4)
    ax.text(CAP + 1, 3.62, f"proposed software cap, {CAP} A", color=STEP_D,
            fontsize=7.4, weight="bold", va="center")
    ax.text(55, 0.62, "light grey: what the cap removes", fontsize=6.8, color=MUTED,
            va="center", ha="center")
    ax.set_xlim(0, 88)
    ax.set_ylim(-0.5, 3.9)
    ax.set_yticks([])
    ax.set_xticks([0, 20, 40, 60, 80])
    ax.set_xticklabels([f"{v} A" for v in (0, 20, 40, 60, 80)], fontsize=7.4, color=MUTED)
    ax.grid(axis="x", color="#e6e6e6", lw=0.7, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(FAINT)
    ax.tick_params(axis="x", length=0)
    fig.text(0.36, 0.04, "Current drawn by the whole LED array, 5 V side",
             fontsize=7.4, color=MUTED)
    fig.savefig(os.path.join(HERE, "fig-load.svg"))
    plt.close(fig)
    print("wrote load")


# ----------------------------------------------------------- volts at Pi

def fig_volts():
    fig = plt.figure(figsize=(7.4, 2.2))
    ax = fig.add_axes([0.36, 0.24, 0.6, 0.68])
    rows = [
        ("Now, dark screen", 4.99, "measured", OK),
        ("Now, white screen", 4.64, "measured", WARN),
        ("After steps 1 and 2, white screen", 5.05, "estimate", OK),
    ]
    ax.axvspan(4.40, 4.63, color="#fbe3e1", zorder=0)
    ax.axvline(4.63, color=WARN, lw=1.0, zorder=1)
    ax.text(4.615, 2.65, "Pi throttles\nbelow 4.63 V", ha="right", va="center",
            fontsize=6.8, color=WARN)
    for y, (lab, v, kind, c) in zip((2, 1, 0), rows):
        ax.plot([4.40, v], [y, y], color="#d9d9d9", lw=1.0, zorder=1)
        ax.plot([v], [y], "o", ms=9, color=c, mec="white", mew=1.5, zorder=3)
        ax.text(v + 0.018, y, f"{v:.2f} V", va="center", fontsize=8, weight="bold")
        ax.text(4.385, y + 0.13, lab, va="center", ha="right", fontsize=8)
        ax.text(4.385, y - 0.24, kind, va="center", ha="right", fontsize=6.6, color=MUTED)
    ax.set_xlim(4.40, 5.20)
    ax.set_ylim(-0.6, 3.0)
    ax.set_yticks([])
    ax.set_xticks([4.4, 4.6, 4.8, 5.0, 5.2])
    ax.set_xticklabels(["4.4 V", "4.6 V", "4.8 V", "5.0 V", "5.2 V"], fontsize=7.4, color=MUTED)
    ax.grid(axis="x", color="#ececec", lw=0.7, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(FAINT)
    ax.tick_params(axis="x", length=0)
    fig.text(0.36, 0.04, "Voltage at the Pi's power input (axis starts at 4.4 V)",
             fontsize=7.4, color=MUTED)
    fig.savefig(os.path.join(HERE, "fig-volts.svg"))
    plt.close(fig)
    print("wrote volts")


# ------------------------------------------------------ recommended layout

def fig_after():
    fig, ax = sheet(11, 5.4, 112, 55)

    box(ax, 2, 14, 17, 22, None)
    ax.text(10.5, 31.5, "PSU", ha="center", fontsize=10, weight="bold")
    ax.text(10.5, 27.6, "5 V DC, 100 A", ha="center", fontsize=7.2)
    tag(ax, 10.5, 22.4, "trim V-ADJ to\n5.10 V", size=7.2, ha="center", color=STEP_D)
    badge(ax, 4.2, 36.2, 2, STEP)
    for y in (30, 19):
        ax.add_patch(Rectangle((19, y - 2.2), 2.2, 4.4, fc="#ffe5e5", ec=INK, lw=0.8))
    ax.text(10.5, 12.6, "uses two of the PSU's\noutput terminal pairs", ha="center", va="top",
            fontsize=6.3, color=MUTED)

    pair(ax, [(21.2, 30.6), (36, 30.6)], lw=2.6)
    ax.text(28.6, 32.6, "main feed, 10 AWG", ha="center", fontsize=6.8, color=MUTED)
    tag(ax, 28.6, 27.4, "≤ 30 A with cap", size=6.8, ha="center")

    box(ax, 36, 16, 15, 30, None, rounded=False, lw=1.8, color=STEP)
    ax.text(39.8, 47.5, "FUSED BLOCK", ha="left", fontsize=7.6, weight="bold")
    ax.text(51.6, 47.5, "blade fuses + 0 V bus", ha="left", fontsize=6.3, color=MUTED)
    badge(ax, 37.6, 46.6, 4, STEP)
    ax.add_patch(Rectangle((38, 18), 1.3, 26, fc="#ffd0d0", ec=V5, lw=0.9, zorder=3))
    ax.add_patch(Rectangle((48.2, 18), 1.3, 26, fc="#d8d8d8", ec=GND, lw=0.9, zorder=3))
    mids = panels(ax, 76, 14, w=8.0, h=5.6, gap=0.8)
    for i, ym in enumerate(mids):
        fy = 41 - i * 6.6
        line(ax, [(39.3, fy), (41.4, fy)], V5, lw=1.4)
        ax.add_patch(Rectangle((41.4, fy - 0.95), 3.6, 1.9, fc="#fff3c4", ec=INK, lw=0.8, zorder=4))
        ax.text(43.2, fy - 0.05, "25 A", ha="center", va="center", fontsize=5.6, weight="bold", zorder=5)
        xch = 58 + i * 1.8
        line(ax, [(45, fy), (xch, fy), (xch, ym + 1.6), (76, ym + 1.6)], V5, lw=1.4)
        gy = fy - 2.4
        line(ax, [(49.5, gy), (xch + 0.7, gy), (xch + 0.7, ym + 0.9), (76, ym + 0.9)], GND, lw=1.1)
    ax.text(64, 49.5, "branches, 12 AWG, ≤ 20 A each", ha="center", va="center", fontsize=6.6, color=MUTED)

    line(ax, [(21.2, 19.6), (27.6, 19.6), (27.6, 7.3), (33.5, 7.3)], V5, lw=1.9)
    line(ax, [(21.2, 18.4), (26.4, 18.4), (26.4, 6.1), (33.5, 6.1)], GND, lw=1.5)
    tag(ax, 29.0, 12.6, "Pi only:\n16 AWG pair", size=6.8, color=STEP_D)
    badge(ax, 24.4, 13.5, 1, STEP)
    box(ax, 33.5, 2, 13, 8.5, "Active3\nbonnet", size=7.2)
    box(ax, 50.5, 2, 13, 8.5, "Pi 5", size=8)
    line(ax, [(46.5, 6.8), (50.5, 6.8)], "#777777", lw=1.0)
    line(ax, [(46.5, 5.8), (50.5, 5.8)], "#777777", lw=1.0)
    tag(ax, 67, 4.0, "software\ncurrent cap,\n30 A total", size=6.8, ha="left", color=STEP_D)
    badge(ax, 65.3, 6.6, 3, STEP)

    line(ax, [(41, 10.5), (41, 13.4), (71, 13.4), (71, mids[0] - 0.6), (74.2, mids[0] - 0.6)], DATA, lw=1.8, z=3)
    arrow(ax, 74, mids[0] - 0.6, 76, mids[0] - 0.6, DATA)
    line(ax, [(43.5, 10.5), (43.5, 12.2), (72.6, 12.2), (72.6, mids[2] - 0.6), (74.2, mids[2] - 0.6)], DATA, lw=1.8, z=3)
    arrow(ax, 74, mids[2] - 0.6, 76, mids[2] - 0.6, DATA)

    ax.text(2, 52.8, "Gone: the old Pi feed from the block. The Pi now shares no wire with the panels.",
            fontsize=7, color=MUTED, va="center")

    save(fig, "after")


if __name__ == "__main__":
    fig_overview()
    fig_sag()
    fig_load()
    fig_volts()
    fig_after()
