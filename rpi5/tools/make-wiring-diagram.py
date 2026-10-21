#!/usr/bin/env python3
"""Draw sheet 1, the as-built wiring diagram: docs/wiring-diagram.{svg,png}.

    /opt/homebrew/bin/python3 rpi5/tools/make-wiring-diagram.py

The PDF, docs/wiring-diagram.pdf, is this sheet plus the power sheets in
docs/wiring/; docs/wiring/build.sh runs this script and then prints it.

Needs matplotlib (the repo venv does not have it; Homebrew's Python does).
Kept as code rather than a drawing file so a rewire is a small, reviewable
diff: change the topology below and re-run.

Sources: E90 Final Report (May 2026) Methods I and IV, its Fig. 7 hand sketch,
HARDWARE.md (lab session 2026-09-21), and the pixel map in
rpi5/prod/swarthmore-tracked.py (build_map / combine_maps).
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs")

# Wire colours. Mains follows IEC 60446 (brown L, blue N, green/yellow PE).
V5 = "#d62728"        # +5 V DC
GND = "#111111"       # 0 V
DATA = "#0b7a75"      # HUB75 ribbon
L_COL = "#8b4513"
N_COL = "#1f4fd1"
PE_COL = "#2e8b57"
GPIO = "#777777"
INK = "#222222"
FAINT = "#9a9a9a"
PANEL_FILL = "#f4f4f4"
RATING = "#6a3d9a"    # electrical ratings

fig = plt.figure(figsize=(17, 11))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 170)
ax.set_ylim(0, 110)
ax.set_aspect("equal")
ax.axis("off")


# ------------------------------------------------------------------ helpers

def box(x, y, w, h, label=None, size=8, fill="white", lw=1.2, weight="bold",
        rounded=False, color=INK):
    if rounded:
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
                           fc=fill, ec=color, lw=lw)
    else:
        p = Rectangle((x, y), w, h, fc=fill, ec=color, lw=lw)
    ax.add_patch(p)
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=size * FONT_SCALE, weight=weight, color=color)


def wire(points, color, lw=1.4, ls="-", z=2):
    xs, ys = zip(*points)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="round",
            solid_joinstyle="miter", zorder=z)


def arrow(x0, y0, x1, y1, color, lw=1.6):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                mutation_scale=9, shrinkA=0, shrinkB=0),
                zorder=4)


def dot(x, y, color):
    ax.plot([x], [y], "o", ms=3.2, color=color, zorder=5)


FONT_SCALE = 1.0


def text(x, y, s, size=7, ha="left", va="center", color=INK, weight="normal"):
    ax.text(x, y, s, fontsize=size * FONT_SCALE, ha=ha, va=va, color=color,
            weight=weight, zorder=6)


def rating(x, y, s, size=5.6, ha="left", va="center"):
    """A voltage / current label, boxed so it reads over wires."""
    ax.text(x, y, s, fontsize=size * FONT_SCALE, ha=ha, va=va, color=RATING,
            weight="bold", zorder=7, linespacing=1.15,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))


def pair(points, offset=0.55):
    """A +5 V / GND pair: the 0 V conductor drawn just beside the +5 V one."""
    wire(points, V5, lw=1.5)
    wire([(x + offset, y - offset) for x, y in points], GND, lw=1.2)


# ------------------------------------------------------------------- border

ax.add_patch(Rectangle((2, 2), 166, 106, fc="none", ec=INK, lw=1.6))
ax.add_patch(Rectangle((3, 3), 164, 104, fc="none", ec=INK, lw=0.5))


# The circuit is drawn on its own axes so it can fill everything above the
# legend, notes and title strip: it is width-bound, so it grows by height.
SHEET = ax
CIRCUIT_Y = (44.5, 106.5)            # circuit drawing coordinates in use
ax = fig.add_axes([4 / 170, 25.5 / 110, 163 / 170, 81 / 110])
ax.set_xlim(4, 167)
ax.set_ylim(*CIRCUIT_Y)
ax.axis("off")
FONT_SCALE = 1.18


# -------------------------------------------------------------- mains + PSU

box(8, 96, 26, 7, "WALL OUTLET\n120 V AC, 60 Hz", size=7.5)
xL, xN, xPE = 13, 21, 29
for x, c, lab in ((xL, L_COL, "L"), (xN, N_COL, "N"), (xPE, PE_COL, "PE")):
    text(x + 0.8, 94.3, lab, size=6.5, color=c, weight="bold")

# L through fuse F1 and switch S1
wire([(xL, 96), (xL, 90.5)], L_COL)
box(xL - 1.1, 86.5, 2.2, 4, None, lw=1.0)
wire([(xL, 86.5), (xL, 90.5)], L_COL, lw=0.9)
text(xL - 1.8, 88.5, "F1\nfuse", size=6, ha="right")
wire([(xL, 86.5), (xL, 83)], L_COL)
dot(xL, 83, INK)
wire([(xL, 83), (xL + 2.6, 80.2)], INK, lw=1.2)
dot(xL, 79.5, INK)
text(xL - 1.8, 81.2, "S1\nswitch", size=6, ha="right")
rating(xL + 1.0, 92.2, "0.9 A typ\n4.1 A max", size=5.3)
wire([(xL, 79.5), (xL, 76)], L_COL)
wire([(xN, 96), (xN, 76)], N_COL)
wire([(xPE, 96), (xPE, 76)], PE_COL, ls=(0, (4, 2)))

box(7, 52, 28, 24, None, lw=1.6)
text(21, 68.5, "PSU", size=11, ha="center", weight="bold")
text(21, 63.8, "5 V DC, 100 A, 500 W\nswitching supply", size=7.5, ha="center")
for x, lab in ((xL, "L"), (xN, "N"), (xPE, "PE")):
    box(x - 1.3, 74, 2.6, 2, None, lw=0.8)
    text(x, 72.6, lab, size=6, ha="center")
rating(21, 59.6, "in 120 V AC, 4.1 A max\nout 5 V DC, 83 A max", size=5.6, ha="center")
text(21, 54.6, "AC in (top)   DC out (right)", size=6, ha="center", color=FAINT)

box(33.7, 63, 2.6, 2.4, None, lw=0.8, fill="#ffe5e5")
box(33.7, 58, 2.6, 2.4, None, lw=0.8, fill="#e8e8e8")
text(33.2, 64.2, "+V", size=6.5, ha="right", color=V5, weight="bold")
text(33.2, 59.2, "−V", size=6.5, ha="right", weight="bold")


# ------------------------------------------------------- distribution block

DX, DY, DW, DH = 50, 52, 13, 24
box(DX, DY, DW, DH, None, lw=1.6)
text(DX + DW / 2, DY - 1.6, "DISTRIBUTION BLOCK", size=7, ha="center", weight="bold")
ax.add_patch(Rectangle((DX + 2.5, DY + 2), 1.6, DH - 4, fc="#ffd0d0", ec=V5, lw=1.0, zorder=3))
ax.add_patch(Rectangle((DX + 8.5, DY + 2), 1.6, DH - 4, fc="#d8d8d8", ec=GND, lw=1.0, zorder=3))
text(DX + 3.3, DY + 0.9, "+5 V", size=5.5, ha="center", color=V5)
text(DX + 9.3, DY + 0.9, "0 V", size=5.5, ha="center")

wire([(36.3, 64.2), (DX + 2.5, 64.2)], V5, lw=2.4)
wire([(36.3, 59.2), (44, 59.2), (44, 57), (DX + 8.5, 57)], GND, lw=2.0)
text(42.5, 65.6, "main feed", size=6, ha="center", color=FAINT)
rating(42.5, 61.7, "17 A typ\n83 A max", size=5.6, ha="center")


# ------------------------------------------------------------ Pi + bonnet

PI = (37, 82, 15, 19)
BN = (56, 82, 17, 19)
box(*PI, None, lw=1.6)
text(PI[0] + PI[2] / 2, PI[1] + PI[3] - 3, "RASPBERRY PI 5", size=7.5, ha="center", weight="bold")
text(PI[0] + PI[2] / 2, PI[1] + PI[3] - 10,
     "user fetcar\nsepta-display.service\nWi-Fi / Ethernet\nUSB-C: unused", size=6, ha="center")
box(*BN, None, lw=1.6)
text(BN[0] + BN[2] / 2, BN[1] + BN[3] - 3, "ACTIVE3 BONNET", size=7.5, ha="center", weight="bold")
text(BN[0] + BN[2] / 2, BN[1] + BN[3] - 6.4, "Adafruit triple-output\nHUB75 RGB matrix", size=5.8, ha="center")

for dy in (0, 1.0):
    wire([(PI[0] + PI[2], 91 + dy), (BN[0], 91 + dy)], GPIO, lw=1.0)
text((PI[0] + PI[2] + BN[0]) / 2, 94.6, "40-pin\nGPIO", size=5.5, ha="center", color=GPIO)
text((PI[0] + PI[2] + BN[0]) / 2, 88.6, "+5 V,\nGND", size=5, ha="center", color=GPIO)
rating((PI[0] + PI[2] + BN[0]) / 2, 85.4, "3.3 V\nlogic", size=5, ha="center")

OUTS = {1: 91.5, 2: 88.0, 3: 84.5}
for n, y in OUTS.items():
    box(BN[0] + BN[2] - 2.6, y - 1.1, 2.6, 2.2, None, lw=0.8,
        fill="#dff3f2" if n < 3 else "white")
    text(BN[0] + BN[2] - 3.2, y, f"OUT{n}" + ("  n/c" if n == 3 else ""), size=5.6, ha="right",
         color=DATA if n < 3 else FAINT, weight="bold")

box(BN[0] + 3, BN[1] - 1.2, 2.2, 1.6, None, lw=0.8, fill="#ffe5e5")
box(BN[0] + 6.5, BN[1] - 1.2, 2.2, 1.6, None, lw=0.8, fill="#e8e8e8")
text(BN[0] + 9.4, BN[1] - 0.4, "5 V in", size=5.3)

# Pi feed: block -> bonnet terminal (note 3)
wire([(DX + 4.1, DY + DH), (DX + 4.1, 79.6), (BN[0] + 4.1, 79.6), (BN[0] + 4.1, BN[1] - 1.2)], V5, lw=1.5)
wire([(DX + 10.1, DY + DH), (DX + 10.1, 78.2), (BN[0] + 7.6, 78.2), (BN[0] + 7.6, BN[1] - 1.2)], GND, lw=1.2)
dot(DX + 4.1, DY + DH, V5)
dot(DX + 10.1, DY + DH, GND)
text(DX + 3.4, 78.0, "Pi feed\n(note 3)", size=5.8, ha="right", color=V5)
rating(DX - 2.4, 78.0, "5 V, 3 A max\n4.64 V meas.", size=5.4, ha="right")


# -------------------------------------------------------------- panel array

PW, PH = 16, 8.5
GAP = 1.8
AX0 = 90
ROW_TOP = [100, 85, 70, 55]
COLS = [AX0 + i * (PW + GAP) for i in range(4)]
ARR_R = COLS[-1] + PW

# Data order: two chains of eight, serpentine, rows 2 and 4 turned 180 degrees.
CHAINS = {"A": (1, [0, 1]), "B": (2, [2, 3])}
num = {}
n = 1
for name, (port, rows) in CHAINS.items():
    for k, r in enumerate(rows):
        for c in (range(4) if k == 0 else range(3, -1, -1)):
            num[(r, c)] = n
            n += 1


def panel(r, c):
    x, top = COLS[c], ROW_TOP[r]
    y = top - PH
    rotated = r in (1, 3)
    box(x, y, PW, PH, None, lw=1.1, fill=PANEL_FILL)
    text(x + PW / 2, y + PH / 2 + 1.0, f"P{num[(r, c)]}", size=8.5, ha="center", weight="bold")
    rating(x + PW / 2, y + 1.0, "5 V · 1 A typ / 5 A max", size=4.6, ha="center")
    text(x + PW / 2, y + PH / 2 - 1.5, "64×32 HUB75" + ("  ↻180°" if rotated else ""),
         size=5.2, ha="center", color="#555555")
    cy = y + PH / 2
    xin, xout = (x + PW - 2.2, x) if rotated else (x, x + PW - 2.2)
    box(xin, cy - 1.3, 2.2, 2.6, None, lw=0.7, fill="#dff3f2")
    box(xout, cy - 1.3, 2.2, 2.6, None, lw=0.7, fill="white")
    text(xin + 1.1, y + 1.0, "IN", size=4.6, ha="center", color=DATA, weight="bold")
    last = num[(r, c)] in (8, 16)
    text(xout + 1.1, y + 1.0, "end" if last else "OUT", size=4.6, ha="center",
         color=INK if last else FAINT, weight="bold" if last else "normal")
    box(x + PW / 2 - 1.8, top - 1.4, 3.6, 1.4, None, lw=0.7, fill="#ffe5e5")
    return (xin, xout, cy, rotated)


geo = {(r, c): panel(r, c) for r in range(4) for c in range(4)}

# Row power branches: a +5 V / GND pair from the block to a bus over each row.
for r in range(4):
    top = ROW_TOP[r]
    bus_y = top + 2.4
    chan_x = 75 + r * 1.6
    out_y = DY + DH - 5 - r * 4.2
    pair([(DX + DW, out_y), (chan_x, out_y), (chan_x, bus_y), (ARR_R - 0.5, bus_y)])
    wire([(DX + 4.1, out_y), (DX + DW, out_y)], V5, lw=1.5)
    wire([(DX + 10.1, out_y - 0.55), (DX + DW + 0.55, out_y - 0.55)], GND, lw=1.2)
    dot(DX + 4.1, out_y, V5)
    dot(DX + 10.1, out_y - 0.55, GND)
    for c in range(4):
        px = COLS[c] + PW / 2
        wire([(px - 0.6, bus_y), (px - 0.6, top)], V5, lw=1.0)
        wire([(px + 0.6, bus_y - 0.55), (px + 0.6, top)], GND, lw=0.9)
        dot(px - 0.6, bus_y, V5)
        dot(px + 0.6, bus_y - 0.55, GND)
    text(COLS[0] + 0.6, bus_y + 1.0, f"branch {r + 1}", size=5.5, color=V5)
    rating(COLS[0] + 7.0, bus_y + 1.0, "5 V · 4 panels · 4 A typ / 20 A max · 100 W", size=5.3)

# Data: bonnet outputs to the head of each chain, then panel to panel.
for name, (port, rows) in CHAINS.items():
    r0, r1 = rows
    head = geo[(r0, 0)]
    y_out = OUTS[port]
    chan = 83 + (0 if name == "A" else 1.6)
    wire([(BN[0] + BN[2], y_out), (chan, y_out), (chan, head[2]), (head[0] - 2.4, head[2])],
         DATA, lw=1.8, z=3)
    arrow(head[0] - 2.5, head[2], head[0], head[2], DATA)
    text(AX0 - 0.4, head[2] + 2.0, f"chain {name}\n(OUT{port})", size=5.6, ha="right",
         color=DATA, weight="bold")
    for c in range(3):
        a, b = geo[(r0, c)], geo[(r0, c + 1)]
        arrow(a[1] + 2.2, a[2], b[0], b[2], DATA)
    a, b = geo[(r0, 3)], geo[(r1, 3)]
    xr = ARR_R + 2.2
    wire([(a[1] + 2.2, a[2]), (xr, a[2]), (xr, b[2])], DATA, lw=1.8, z=3)
    arrow(xr, b[2], b[0] + 2.2, b[2], DATA)
    for c in range(3, 0, -1):
        a, b = geo[(r1, c)], geo[(r1, c - 1)]
        arrow(a[1], a[2], b[0] + 2.2, b[2], DATA)

text((AX0 + ARR_R) / 2, ROW_TOP[0] + 5.4,
     "LED ARRAY  ·  16 panels, 4 × 4, 256 × 128 px, each panel 256 × 128 mm",
     size=7.5, ha="center", weight="bold")


ax = SHEET
FONT_SCALE = 1.0


# ------------------------------------------------------------------- legend

text(5, 26.4, "LEGEND", size=6.8, weight="bold")
items = [
    (5, 24.2, V5, "-", "+5 V DC"),
    (21, 24.2, GND, "-", "0 V / GND"),
    (38, 24.2, DATA, "-", "HUB75 ribbon, 5 V logic, arrow = data direction"),
    (80, 24.2, GPIO, "-", "stacked 40-pin header"),
    (5, 22.0, L_COL, "-", "mains line (L)"),
    (21, 22.0, N_COL, "-", "mains neutral (N)"),
    (38, 22.0, PE_COL, (0, (4, 2)), "protective earth (PE)"),
]
for x0, y, c, ls, lab in items:
    wire([(x0, y), (x0 + 3.5, y)], c, lw=1.6, ls=ls)
    text(x0 + 4.4, y, lab, size=5.9)
dot(81.8, 22.0, INK)
text(84.4, 22.0, "junction", size=5.9)
ax.text(96, 24.2, "5 V · 20 A", fontsize=5.6, ha="left", va="center", color=RATING,
        weight="bold", bbox=dict(boxstyle="square,pad=0.15", fc="white", ec=RATING, lw=0.5))
text(103.6, 24.2, "rating (see table)", size=5.9)


# -------------------------------------------------------------------- notes

text(5, 19.4, "NOTES", size=6.8, weight="bold")
notes = [
    "1  Load: about 1 A per panel typical, 5 A at full white (E90 measurement). 16 panels → 80 A worst case, about 400 W. PSU rated 100 A. See ratings table.",
    "2  One wall outlet. Mains passes through F1 and S1 in the PSU cord. The fuse rating was not recorded; label it when found.",
    "3  The Pi takes 5 V from the PSU through wires soldered to the bonnet's power input, then the 40-pin header. Its USB-C input is unused.",
    "    Measured 4.64 V at the Pi under full white (under-voltage limit 4.63 V). Fix: dedicated 16 AWG pair from the PSU terminals; see HARDWARE.md §1.",
    "4  Two chains of eight on bonnet outputs 1 and 2; output 3 unused. One chain of sixteen refreshed at about 30 fps and flickered (E90 report, Methods I).",
    "5  Serpentine: rows 2 and 4 are mounted turned 180°, so each chain doubles back. build_map() and combine_maps() in swarthmore-tracked.py",
    "    encode this wiring; recabling the array needs a matching software change or the picture scrambles into blocks.",
    "6  Panel positions are logical, as in the original sketch. Before rewiring, confirm on the hardware: which output feeds the top half (the code",
    "    assumes OUT1), which corner each chain enters, whether the Pi feed leaves the block or the PSU terminals, and conductor gauges.",
    "7  Supersedes the May 2026 hand sketch (E90 report Fig. 7), which showed a second outlet for the Pi and one 16-panel chain.",
]
for i, s_ in enumerate(notes):
    text(5, 17.6 - i * 1.5, s_, size=5.6)


# ------------------------------------------------------------ ratings table

# typ = ordinary board content (about 1 A per panel), max = every pixel white.
# Mains current assumes 85 % PSU efficiency; the Pi peak is with no USB load.
RX, RY = 70, 20.4
COLX = (0, 15.2, 25.2, 31.0, 37.6, 43.0)
text(RX, RY, "ELECTRICAL RATINGS", size=6.8, weight="bold")
rows = [
    ("Circuit", "Voltage", "Typ", "Max", "Power", "Wire*"),
    ("Mains in, L / N", "120 V AC, 60 Hz", "0.9 A", "4.1 A", "490 W", "14 AWG"),
    ("PSU output (rated)", "5.0 V DC", "", "100 A", "500 W", "terminals"),
    ("Main feed, PSU → block", "5 V DC", "17 A", "83 A", "415 W", "4 AWG"),
    ("Each branch, 4 panels", "5 V DC", "4 A", "20 A", "100 W", "12 AWG"),
    ("Each panel", "5 V DC", "1 A", "5 A", "25 W", "panel lead"),
    ("Pi + bonnet feed", "5 V (4.64 meas.)", "1 A", "3 A", "15 W", "16 AWG"),
    ("GPIO, Pi → bonnet", "3.3 V logic", "", "", "", "header"),
    ("HUB75 ribbons", "5 V logic", "", "", "", "16-way IDC"),
]
for i, row in enumerate(rows):
    y = RY - 2.0 - i * 1.42
    for j, (cx, cell) in enumerate(zip(COLX, row)):
        text(RX + cx, y, cell, size=5.4, weight="bold" if i == 0 else "normal",
             color=INK if (i == 0 or j == 0) else RATING)
    if i == 0:
        wire([(RX, y - 0.75), (RX + 48, y - 0.75)], INK, lw=0.5)
text(RX, RY - 2.0 - len(rows) * 1.42 + 0.15,
     "typ = normal board, max = all white. Mains at 85 % PSU efficiency. Under-voltage at 4.63 V.",
     size=4.8, color="#555555")
text(RX, RY - 2.0 - len(rows) * 1.42 - 1.15,
     "* Recommended minimum copper for runs under 1 m; as-built gauges not yet verified (note 6).",
     size=4.8, color="#555555")


# -------------------------------------------------------------- title block

TX, TY, TW, TH = 120, 3, 47, 24
ax.add_patch(Rectangle((TX, TY), TW, TH, fc="white", ec=INK, lw=1.4))
for y in (TY + 17.4, TY + 12.6, TY + 8.8, TY + 4.6):
    wire([(TX, y), (TX + TW, y)], INK, lw=0.6)
wire([(TX + 24, TY), (TX + 24, TY + 8.8)], INK, lw=0.6)
text(TX + 1.2, TY + 21.7, "SEPTA SWARTHMORE STATION DISPLAY", size=8.5, weight="bold")
text(TX + 1.2, TY + 19.1, "System wiring diagram, as built", size=7.2)
text(TX + 1.2, TY + 15.9, "ENGR 090 E90 design project: A. Carretta, N. Fettig", size=6.0)
text(TX + 1.2, TY + 14.0, "Advisor: Prof. E. Masroor   ·   Swarthmore College Engineering", size=6.0)
text(TX + 1.2, TY + 11.2, "Maintainer / drawn by: B. Greenberg", size=6.0)
text(TX + 1.2, TY + 9.8, "github.com/BenGreenberg07/septa-tracker", size=5.6, color="#555555")
for x, y, k, v in (
    (TX + 1.2, TY + 6.7, "DATE", "2026-10-21"),
    (TX + 25.2, TY + 6.7, "REV", "B"),
    (TX + 1.2, TY + 2.3, "SCALE", "None (schematic)"),
    (TX + 25.2, TY + 2.3, "SHEET", "1 of 4"),
):
    text(x, y + 1.0, k, size=4.6, color="#666666")
    text(x, y - 0.6, v, size=6.5, weight="bold")

os.makedirs(OUT, exist_ok=True)
for ext in ("svg", "png"):
    path = os.path.join(OUT, f"wiring-diagram.{ext}")
    fig.savefig(path, dpi=200 if ext == "png" else None)
    print("wrote", path)
