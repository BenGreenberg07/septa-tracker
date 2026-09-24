#!/usr/bin/env python3
"""Render every state of the live-tracking strip into one showcase image.

Feeds synthetic train/track records straight into the production drawing code,
so what you see is exactly what the panel renders, not a mockup.
"""

import importlib.util
import math
import os
import sys

import numpy as np
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RPI5 = os.path.dirname(HERE)
sys.path.insert(0, RPI5)

spec = importlib.util.spec_from_file_location(
    "disp", os.path.join(RPI5, "prod", "swarthmore-tracked.py"))
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
import septa_line as line

SCALE = 3            # LEDs -> screen pixels
GAP = 1
BLOCK_H = 52         # one direction block, in LED rows

FONT_DIR = "/opt/homebrew/lib/python3.14/site-packages/matplotlib/mpl-data/fonts/ttf"
UI = os.path.join(FONT_DIR, "DejaVuSans.ttf")
UI_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


def train(dest, origin, arrives, delay, unknown=False, mins=None):
    from datetime import datetime, timedelta
    sched = None if mins is None else (
        datetime.now() + timedelta(minutes=mins - delay))
    return {"dest": dest, "origin": origin, "arrives": arrives,
            "delay": delay, "unknown": unknown, "sched_dt": sched,
            "train_id": "0000"}


def track(pos, late=0, unknown=False):
    stops = int(math.ceil(abs(pos - line.SWAT_IDX) - 1e-9))
    return {"pos": pos, "stops_away": stops, "current": "", "next": "",
            "late": late, "late_unknown": unknown, "dest": "",
            "at_swat": stops == 0}


I = {n: i for i, (n, _, _, _) in enumerate(line.LINE)}

# (caption, explanation, direction, train, track)
SCENARIOS = [
    ("Not in service yet",
     "No GPS fix for this train id yet, so the status reads SCHED and no marker "
     "is drawn. The journey anchors still show, so the run is visible before it moves.",
     "N", train("Doylestown", "Wawa", "3:19 PM", 0, mins=22), None),

    ("Just left the origin",
     "Pulled out of Wawa. The marker sits at the left anchor and the trail behind "
     "it starts to grow. The countdown is the headline number.",
     "N", train("Doylestown", "Wawa", "3:49 PM", 0, mins=18),
     track(I["Wawa"] - 0.2)),

    ("On the way, on time",
     "Roughly halfway from Wawa to Swarthmore. The leg past Swarthmore stays faint "
     "because it is not this platform's concern.",
     "N", train("Doylestown", "Wawa", "2:49 PM", 0, mins=11),
     track(I["Media"] + 0.4)),

    ("Running late",
     "Orange for a delay under six minutes. Countdown, delay chip and marker all "
     "carry the same color, so the delay reads three ways at once.",
     "N", train("Chestnut H East", "Media", "4:28 PM", 4, mins=9),
     track(I["Media"] - 0.6)),

    ("Badly delayed",
     "Six minutes or more turns everything red. The countdown already includes the "
     "delay, so it is the real wait rather than the timetable's.",
     "N", train("Doylestown", "Wawa", "3:49 PM", 12, mins=15),
     track(I["Wallingford"] + 0.4)),

    ("Nearly here",
     "Past Wallingford and closing on the ringed Swarthmore anchor, with the trail "
     "covering almost the whole approach.",
     "N", train("Lansdale", "Wawa", "3:19 PM", 1, mins=2),
     track(I["Wallingford"] - 0.2)),

    ("Arriving",
     "GPS has it at Swarthmore. The countdown reads NOW, the status flips to "
     "ARRIVING and the marker lands on the platform anchor.",
     "N", train("Doylestown", "Media", "2:49 PM", 0, mins=0),
     track(float(I["Swarthmore"]))),

    ("SEPTA has no status",
     "The feed returns a 999-minute delay as a sentinel meaning it has no status "
     "for this train. Showing that as a real delay would be nonsense, so the board "
     "says NO STATUS and everything goes gray rather than claiming on time.",
     "S", train("Wawa", "Temple U", "4:50 PM", 0, unknown=True, mins=11),
     track(I["Fernwood-Yeadon"] + 0.4, unknown=True)),

    ("Joined from another line",
     "A southbound run that started at Norristown, which is not on the Media/Wawa "
     "line. Progress is measured from where it joins at Temple, while the label "
     "still names the true first stop.",
     "S", train("Wawa", "Norristown", "3:12 PM", 0, mins=7),
     track(I["Secane"] + 0.3)),

    ("No trains left",
     "End of service. The strip is suppressed entirely and the board says so "
     "plainly instead of showing an empty rail.",
     "N", {"dest": "No trains", "origin": "", "arrives": "tonight", "delay": 0,
           "unknown": False, "sched_dt": None, "train_id": ""}, None),
]


def render_block(direction, tr, tk, heading):
    """Draw one direction block on a black canvas and return it as LED pixels."""
    canvas = Image.new("RGB", (D.WIDTH, BLOCK_H), D.BLACK)
    draw = ImageDraw.Draw(canvas)
    # draw_block takes the run of upcoming trains; these scenarios each
    # describe a single one, so it is passed as a one-train run.
    D.draw_block(draw, 0, heading, direction, [tr], tk)
    return np.asarray(canvas).copy()


def leds(arr):
    """Upscale so each LED is a lit square on a dark grid, like the real panel."""
    h, w, _ = arr.shape
    cell = SCALE + GAP
    out = np.zeros((h * cell, w * cell, 3), dtype=np.uint8)
    big = np.repeat(np.repeat(arr, SCALE, axis=0), SCALE, axis=1)
    ys = (np.arange(h * SCALE) // SCALE) * cell + (np.arange(h * SCALE) % SCALE)
    xs = (np.arange(w * SCALE) // SCALE) * cell + (np.arange(w * SCALE) % SCALE)
    out[np.ix_(ys, xs)] = big
    return Image.fromarray(out, "RGB")


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def main():
    panel_w = D.WIDTH * (SCALE + GAP)
    panel_h = BLOCK_H * (SCALE + GAP)

    f_title = ImageFont.truetype(UI_B, 31)
    f_sub = ImageFont.truetype(UI, 16)
    f_head = ImageFont.truetype(UI_B, 19)
    f_body = ImageFont.truetype(UI, 14)
    f_num = ImageFont.truetype(UI_B, 15)

    pad, col_gap, cols = 34, 40, 2
    canvas_w = pad * 2 + panel_w * cols + col_gap

    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    cells = []
    for name, desc, direction, tr, tk in SCENARIOS:
        body = wrap(probe, desc, f_body, panel_w - 30)
        cells.append({"name": name, "body": body, "dir": direction,
                      "train": tr, "track": tk,
                      "h": 28 + panel_h + 12 + len(body) * 19 + 26})

    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    head_h = 112
    total_h = head_h + sum(max(c["h"] for c in r) for r in rows) + pad - 10

    img = Image.new("RGB", (canvas_w, total_h), (16, 18, 22))
    draw = ImageDraw.Draw(img)

    draw.text((pad, 30), "Live train tracking on the Swarthmore board",
              font=f_title, fill=(238, 240, 244))
    draw.text((pad, 70),
              "Every state of the new position strip, drawn by the production "
              "display code at true panel resolution (256 x 128, 16 panels).",
              font=f_sub, fill=(138, 146, 158))

    y = head_h
    n = 0
    for row in rows:
        row_h = max(c["h"] for c in row)
        for ci, c in enumerate(row):
            n += 1
            x = pad + ci * (panel_w + col_gap)

            draw.ellipse([x, y + 2, x + 21, y + 23], fill=(46, 51, 60))
            nw = draw.textlength(str(n), font=f_num)
            draw.text((x + 11 - nw / 2, y + 5), str(n), font=f_num,
                      fill=(190, 196, 206))
            draw.text((x + 31, y + 3), c["name"], font=f_head, fill=(238, 240, 244))

            heading = "TO CENTER CITY" if c["dir"] == "N" else "TO MEDIA/WAWA"
            if c["track"] is not None and not c["track"].get("late_unknown"):
                c["track"]["late"] = c["train"]["delay"]
            block = leds(render_block(c["dir"], c["train"], c["track"], heading))
            by = y + 28
            draw.rectangle([x - 3, by - 3, x + panel_w + 2, by + panel_h + 2],
                           fill=(0, 0, 0), outline=(72, 78, 88))
            img.paste(block, (x, by))

            ty = by + panel_h + 13
            for ln in c["body"]:
                draw.text((x + 1, ty), ln, font=f_body, fill=(142, 150, 162))
                ty += 19
        y += row_h

    out = os.path.join(RPI5, "tracking-scenarios.png")
    img.save(out)
    print(f"wrote {out}  ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
