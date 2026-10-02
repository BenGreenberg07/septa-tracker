#!/usr/bin/env python3
"""Swarthmore departure board, big-type layout: no line map, huge countdowns.

The tracked board's line map carries a lot of 9 px text that cannot be read
from the far end of the platform. This layout gives each direction one
countdown in type roughly three times the height, readable from much further
away, and keeps only what still fits at a legible size: the direction, the
scheduled time and delay, how many stops out the train is, and the one after.

Everything except the drawing is shared with swarthmore-tracked.py: the same
fetching, backoff, stale-data and clock checks, alert paging, header, and main
loop (including the systemd watchdog, WATCHDOG=1). Run it exactly like that
board:

    ./pi/try-script.sh rpi5/prod/swarthmore-big.py          (on the Pi)
    ./pi/set-panel-script.sh rpi5/prod/swarthmore-big.py    (make it the default)
    ./run-sim.sh big                                         (on a Mac)
"""

import importlib.util
import os
import sys

import PIL.Image as Image
import PIL.ImageDraw as ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "swarthmore_tracked", os.path.join(HERE, "swarthmore-tracked.py"))
board = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(board)

WIDTH = board.WIDTH
FONT_HUGE = board._font(56)   # the countdown: digits about 41 LEDs tall
FONT_BIG = board._font(30)    # a clock time, when the train is too far out to count
FONT_LG = board.FONT_LG
FONT_SM = board.FONT_SM

# Each block is 52 rows: heading, two text lines, and the countdown beside them.
LINE2 = 20
LINE3 = 36
BASELINE = 50       # countdown baseline, from the top of the block


def short_time(train):
    """'10:09 PM' as '10:09'. AM/PM costs width the big type needs, and anyone
    close enough to read this line knows which half of the day it is."""
    return train["arrives"].rsplit(" ", 1)[0]


def train_color(train):
    """The same one-train-one-colour rule as the tracked board."""
    if train.get("unknown"):
        return board.GRAY
    return board.delay_color(train["delay"])


def draw_countdown(draw, y0, train):
    """The big number, right-aligned. Returns how wide it ended up."""
    right = WIDTH - 2
    base = y0 + BASELINE
    if train["dest"] == "No trains":
        w = draw.textlength("--", font=FONT_HUGE)
        draw.text((right, base), "--", font=FONT_HUGE, fill=board.FAINT, anchor="rs")
        return w

    color = train_color(train)
    mins = board.minutes_until(train)
    if mins is None:
        # Over 99 minutes out (or no scheduled time): a clock time reads
        # better than a three-digit countdown, and fits.
        text = short_time(train)
        draw.text((right, base), text, font=FONT_BIG, fill=color, anchor="rs")
        return draw.textlength(text, font=FONT_BIG)
    if mins == 0:
        draw.text((right, base), "NOW", font=FONT_HUGE, fill=color, anchor="rs")
        return draw.textlength("NOW", font=FONT_HUGE)

    # "MIN" sits on the digits' baseline, small, so the number itself gets
    # every pixel of height there is.
    mw = draw.textlength("MIN", font=FONT_SM)
    draw.text((right, base), "MIN", font=FONT_SM, fill=color, anchor="rs")
    digits = str(mins)
    dw = draw.textlength(digits, font=FONT_HUGE)
    draw.text((right - mw - 3, base), digits, font=FONT_HUGE, fill=color, anchor="rs")
    return dw + 3 + mw


def draw_big_block(draw, y0, heading, trains, track):
    train = trains[0]
    later = trains[1] if len(trains) > 1 else None
    no_train = train["dest"] == "No trains"

    used = draw_countdown(draw, y0, train)
    room = WIDTH - 2 - used - 6        # what the left-hand column may use

    draw.text((2, y0), heading, font=FONT_LG, fill=board.YELLOW)

    if no_train:
        draw.text((2, y0 + LINE2), "NONE TONIGHT", font=FONT_SM, fill=board.GRAY)
        return

    # Line 2: scheduled time and how late it is running.
    if train.get("unknown"):
        chip = "NO STATUS"
    elif train["delay"] > 0:
        chip = f"+{train['delay']} LATE"
    else:
        chip = "ON TIME"
    x = 2
    if board.minutes_until(train) is not None:   # else the big slot shows it
        when = short_time(train)
        draw.text((x, y0 + LINE2), when, font=FONT_SM, fill=board.WHITE)
        x += draw.textlength(when + " ", font=FONT_SM)
    chip = board.fit(draw, chip, FONT_SM, room - x)
    draw.text((x, y0 + LINE2), chip, font=FONT_SM, fill=train_color(train))

    # Line 3: where the train is, then the one after if there is room. A train
    # with no GPS yet says nothing here rather than a bare "SCHED".
    x = 2
    stat, stat_color = board.status_text(track, train)
    if stat and stat != "SCHED":
        draw.text((x, y0 + LINE3), stat, font=FONT_SM, fill=stat_color)
        x += draw.textlength(stat, font=FONT_SM) + 8
    if later and later["dest"] != "No trains":
        then = "THEN " + short_time(later)
        if x + draw.textlength(then, font=FONT_SM) <= room:
            draw.text((x, y0 + LINE3), "THEN", font=FONT_SM, fill=board.DIM)
            draw.text((x + draw.textlength("THEN ", font=FONT_SM), y0 + LINE3),
                      short_time(later), font=FONT_SM, fill=train_color(later))


def render(state):
    canvas = Image.new("RGB", (WIDTH, board.HEIGHT), board.BLACK)
    draw = ImageDraw.Draw(canvas)

    board.draw_header(canvas, draw, state)

    draw_big_block(draw, 22, "CENTER CITY", state["northbound"], state["track_n"])
    draw.line([(0, 74), (WIDTH, 74)], fill=board.GRAY, width=1)
    draw_big_block(draw, 76, "MEDIA/WAWA", state["southbound"], state["track_s"])

    return board.to_framebuffer(canvas)


if __name__ == "__main__":
    board.main(render)
