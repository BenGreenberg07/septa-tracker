#!/usr/bin/env python3
"""Swarthmore bidirectional departure board with live train tracking.

Extends the original bidirectional board with a progress strip under each
direction: the SEPTA TrainView GPS feed is projected onto the Media/Wawa
station chain, so the board shows which stop the incoming train is at (or
between) and how many stops it still has to go.

Runs unmodified on the Pi 5 (real HUB75 panels) and on a laptop, where a
simulator serves the frames as a web page.
"""

import os
import sys
import threading
import time
from datetime import datetime, timedelta

import numpy as np
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
RPI5 = os.path.dirname(HERE)
sys.path.insert(0, RPI5)

import septa_line as line

try:
    import adafruit_blinka_raspberry_pi5_piomatter as piomatter
    HARDWARE = True
except ImportError:
    from sim import piomatter_sim as piomatter
    HARDWARE = False

WIDTH = 256
HEIGHT = 128
N_ADDR_LINES = 4
N_LANES = 4  # 2 HUB75 ports x 2 lanes each

# Color depth vs refresh rate. Fewer planes refresh faster (less flicker) at
# the cost of color depth. Override without editing code, for example:
#   SEPTA_PLANES=3 ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
N_PLANES = int(os.environ.get("SEPTA_PLANES", 4))
N_TEMPORAL_PLANES = int(os.environ.get("SEPTA_TEMPORAL_PLANES", 2))

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/opt/homebrew/lib/python3.14/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSansMono-Bold.ttf",
]
FONT_TINY = 9
FONT_SMALL = 14
FONT_MEDIUM = 16
FONT_LARGE = 18

SEPTA_LOGO_PATH = os.path.join(RPI5, "septa.png")

# Written as plain RGB; converted for the panel's BGR pinout at flush time.
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 128, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (180, 180, 180)
DIM = (125, 131, 140)
FAINT = (85, 90, 98)

# SEPTA reports this many minutes late when it has no status for a train.
UNKNOWN_DELAY = 999
TAIL_LEN = 20  # px of fading trail behind the train dot
GARNET = (139, 0, 0)
CYAN = (0, 200, 255)
BLACK = (0, 0, 0)


def _font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT_LG = _font(FONT_LARGE)
FONT_MD = _font(FONT_MEDIUM)
FONT_SM = _font(FONT_SMALL)
FONT_TN = _font(FONT_TINY)


# ---------------------------------------------------------------- SEPTA data

def fetch_trains(direction):
    key = "Northbound" if direction == "N" else "Southbound"
    try:
        url = ("https://www3.septa.org/api/Arrivals/index.php"
               f"?station=Swarthmore&results=20&direction={direction}")
        return parse_trains(requests.get(url, timeout=10).json(), key)
    except Exception as e:
        print(f"API error ({direction}): {e}")
        return no_trains()


def parse_trains(data, direction_key, count=1):
    trains = []
    now = datetime.now()
    for value in data.values():
        if not isinstance(value, list):
            continue
        for entry_list in value:
            if not isinstance(entry_list, dict):
                continue
            for entry in entry_list.get(direction_key, []):
                dest = entry.get("destination") or ""
                ln = entry.get("line") or ""
                origin = entry.get("origin") or ""

                if direction_key == "Southbound":
                    if "Wawa" not in dest and "Media" not in dest:
                        continue
                elif ("Media" not in ln and "Wawa" not in ln
                      and "Media" not in origin and "Wawa" not in origin):
                    continue

                status = entry.get("status") or "On Time"
                unknown = False
                if status == "On Time":
                    delay = 0
                else:
                    try:
                        delay = int(status.split()[0])
                    except ValueError:
                        delay = 0
                    # SEPTA sends "999 min" as a sentinel when it has no status
                    # for a train, so it must not be shown as a real delay.
                    if delay >= UNKNOWN_DELAY:
                        delay, unknown = 0, True

                # Drop a train only once it has actually gone, which means the
                # delay counts. A train 10 minutes late is still 5 minutes away
                # when its scheduled time was 5 minutes ago, and that is exactly
                # the train a waiting passenger needs to see.
                sched_dt = None
                try:
                    sched_dt = datetime.strptime(entry["sched_time"],
                                                 "%Y-%m-%d %H:%M:%S.%f")
                    if sched_dt + timedelta(minutes=delay) < now:
                        continue
                except (KeyError, ValueError):
                    pass

                sched = entry["sched_time"][11:16]
                hour, minute = int(sched[:2]), int(sched[3:])
                ampm = "AM" if hour < 12 else "PM"
                arrives = f"{hour % 12 or 12}:{minute:02d} {ampm}"

                trains.append({
                    "dest": dest,
                    "origin": origin,
                    "arrives": arrives,
                    "delay": delay,
                    "sched_dt": sched_dt,
                    "unknown": unknown,
                    "train_id": str(entry.get("train_id") or ""),
                })
                if len(trains) == count:
                    return trains
    return trains or no_trains()


def no_trains():
    return [{"dest": "No trains", "origin": "", "arrives": "tonight",
             "delay": 0, "sched_dt": None, "unknown": False, "train_id": ""}]


# ------------------------------------------------------------ panel plumbing

def build_map(width, height, n_addr_lines, serpentine, row_offset=0):
    panel_height = 2 << n_addr_lines
    half_panel_height = 1 << n_addr_lines
    v_panels = height // panel_height
    pixels_across = width * v_panels
    result = []
    for i in range(half_panel_height):
        for j in range(pixels_across):
            panel_no = j // width
            panel_idx = j % width
            if serpentine and panel_no % 2:
                x = width - panel_idx - 1
                y0 = (panel_no + 1) * panel_height - i - 1
                y1 = (panel_no + 1) * panel_height - i - half_panel_height - 1
            else:
                x = panel_idx
                y0 = panel_no * panel_height + i
                y1 = panel_no * panel_height + i + half_panel_height
            result.append(x + width * (y0 + row_offset))
            result.append(x + width * (y1 + row_offset))
    return result, pixels_across


def combine_maps(m1, m2, pixels_across):
    result = []
    for addr in range(16):
        for x in range(pixels_across):
            idx = addr * pixels_across * 2 + x * 2
            result.append(m1[idx])
            result.append(m1[idx + 1])
            result.append(m2[idx])
            result.append(m2[idx + 1])
    return result


def reorder_rows(arr):
    reordered = np.zeros_like(arr)
    reordered[0:32] = arr[32:64]
    reordered[32:64] = arr[0:32]
    reordered[64:96] = arr[96:128]
    reordered[96:128] = arr[64:96]
    return reordered


def load_septa_logo(path, size=16):
    img = Image.open(path).convert("RGB")
    img = img.crop((0, 0, img.width, int(img.height * 0.68)))
    img = img.crop((50, 50, img.width - 80, img.height))
    ratio = img.width / img.height
    img = img.resize((int(size * ratio), size), Image.LANCZOS)
    arr = np.array(img)
    blue = arr[2, arr.shape[1] - 3].tolist()
    red = arr[2, 2].tolist()
    arr[0:2, 0:2] = red
    arr[-2:, 0:2] = red
    arr[0:2, -2:] = blue
    arr[-2:, -2:] = blue
    return Image.fromarray(arr)


def wait_for_network(timeout=60):
    import socket
    print("Waiting for network...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            socket.create_connection(("www3.septa.org", 80), timeout=5)
            print("Network ready.")
            return True
        except OSError:
            time.sleep(3)
    print("Network timeout, starting with fallback data.")
    return False


# --------------------------------------------------------------- the drawing

def minutes_until(train):
    """Minutes until the train actually gets here, delay included.

    None when there is no scheduled time to count down to, or when the train
    is far enough out that a countdown is less useful than the clock time.
    """
    sched = train.get("sched_dt")
    if sched is None:
        return None
    due = sched + timedelta(minutes=train.get("delay", 0))
    mins = (due - datetime.now()).total_seconds() / 60
    if mins < -1 or mins > 99:
        return None
    return int(max(0, round(mins)))


def shade(color, f):
    """color dimmed to fraction f, for tail and travelled-leg shading."""
    return tuple(int(c * f) for c in color)


def delay_color(minutes):
    if minutes <= 0:
        return GREEN
    return ORANGE if minutes < 6 else RED


def fit(draw, text, font, max_w):
    """Trim text until it fits max_w pixels."""
    while text and draw.textlength(text, font=font) > max_w:
        text = text[:-1]
    return text


def fit_words(draw, text, font, max_w):
    """Trim to whole words where possible, so names never end mid-word."""
    if draw.textlength(text, font=font) <= max_w:
        return text
    words = text.split()
    while len(words) > 1:
        words.pop()
        joined = " ".join(words)
        if draw.textlength(joined, font=font) <= max_w:
            return joined
    return fit(draw, text, font, max_w)


def stop_at(pos):
    """The stop nearest a position on the line: index, long name, short name.

    Taken from the position rather than TrainView's `currentstop`, which names
    the last station the train actually called at. An express runs past stops
    without calling, so `currentstop` can sit several stations behind the
    train while the dot has moved on, and a label drawn from it would name a
    place nowhere near its own marker.
    """
    i = int(round(pos))
    i = max(line.MAP_START, min(line.MAP_END, i))
    return i, line.LINE[i][0], line.LINE[i][1]


def draw_strip(draw, y, direction, train, track):
    """A fixed map of the line: Penn Medicine at the left, Wawa at the right,
    Swarthmore marked between them, and a dot at every stop in between.

    The span deliberately does not follow the train. Anchoring the right-hand
    end on each train's own terminus made the picture rearrange itself between
    arrivals, and for a through-running train it named a station on another
    line entirely. A platform map that stays put can be read at a glance.
    """
    x_left, x_right = 14, WIDTH - 14

    # Each strip runs toward its own destination, so both read left to right
    # and the right-hand end always matches the heading above it. That means
    # the Center City map is the line drawn backwards, Wawa end first.
    flip = direction == "N"

    def x_of(pos):
        f = line.map_fraction(pos)
        if flip:
            f = 1.0 - f
        return int(round(x_left + (x_right - x_left) * f))

    x_swat = x_of(line.SWAT_IDX)

    draw.line([(x_left, y), (x_right, y)], fill=DIM, width=1)

    # One dot per station, so the stops still to go can be counted off.
    for i in line.map_stops():
        if i == line.SWAT_IDX:
            continue
        x = x_of(i)
        draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=GRAY)

    # Swarthmore is the stop that matters on this platform, so it gets the ring.
    draw.ellipse([x_swat - 3, y - 3, x_swat + 3, y + 3], outline=YELLOW, fill=BLACK)
    draw.ellipse([x_swat - 1, y - 1, x_swat + 1, y + 1], fill=YELLOW)

    label_y = y + 4

    # Where the train is gets named under its own dot, so the strip can be
    # read without counting stops. It is worked out before the fixed labels
    # are drawn, because a fixed label it would land on top of is dropped:
    # the live position is worth more than a rail end anyone can infer.
    near, far = ("WAWA", "PENN") if flip else ("PENN", "WAWA")
    nw = draw.textlength(near, font=FONT_TN)
    sw = draw.textlength("SWAT", font=FONT_TN)
    fw = draw.textlength(far, font=FONT_TN)
    # Each rail label is tagged with the stop it names, so a train standing on
    # that stop can take the label over instead of printing beside it.
    near_i, far_i = (line.MAP_END, line.MAP_START) if flip else (line.MAP_START, line.MAP_END)
    fixed = [
        (2.0, nw, near, GRAY, near_i),
        (x_swat - sw / 2, sw, "SWAT", YELLOW, line.SWAT_IDX),
        (WIDTH - 2 - fw, fw, far, GRAY, far_i),
    ]

    def hits(x0, w, x1, w1):
        return x0 + w + 2 > x1 and x1 + w1 + 2 > x0

    here = ""
    here_x = 0.0
    here_w = 0.0
    taken = None          # a rail label the train is standing on
    if track:
        tx = x_of(track["pos"])
        if line.MAP_START <= track["pos"] <= line.MAP_END:
            at_i, full, short = stop_at(track["pos"])
            for fx, fwd, text, _, tag in fixed:
                if at_i == tag:
                    # Standing on a rail end: colour that label rather than
                    # print the same stop's name twice, side by side.
                    taken, here, here_x, here_w = tag, text, fx, fwd
                    break
            else:
                # Spell it out when there is room, and fall back to the
                # timetable short code rather than push a rail label off.
                for cand in (full, short):
                    if not cand:
                        continue
                    w = draw.textlength(cand, font=FONT_TN)
                    x0 = min(max(2.0, tx - w / 2), WIDTH - 2 - w)
                    here, here_x, here_w = cand, x0, w
                    if not any(hits(x0, w, fx, fwd) for fx, fwd, _, _, _ in fixed):
                        break

    for fx, fwd, text, fill, tag in fixed:
        if taken == tag:
            continue
        if here and hits(here_x, here_w, fx, fwd):
            continue
        draw.text((fx, label_y), text, font=FONT_TN, fill=fill)

    if not track:
        return

    # An unknown delay must not be drawn as an on-time green marker.
    color = GRAY if track.get("late_unknown") else delay_color(track["late"])

    # Both maps run toward the destination, so every train moves left to right.
    # The whole stretch it has covered on this map stays lit, dimly, with the
    # last stretch brightening into the dot: distance run at a glance, and
    # direction of travel without having to read the labels.
    if tx > x_left:
        draw.line([(x_left, y), (tx, y)], fill=shade(color, 0.45), width=1)
    for k in range(1, TAIL_LEN):
        x = tx - k
        if x < x_left:
            break
        draw.point((x, y), fill=shade(color, 1.0 - 0.55 * k / TAIL_LEN))

    draw.ellipse([tx - 3, y - 3, tx + 3, y + 3], fill=color)
    draw.ellipse([tx - 1, y - 1, tx + 1, y + 1], fill=BLACK)

    if here:
        draw.text((here_x, label_y), here, font=FONT_TN, fill=color)


def status_text(track, train):
    if train["dest"] == "No trains":
        return "", DIM
    if not track:
        return "SCHED", GRAY
    if track["at_swat"]:
        return "ARRIVING", GREEN
    n = track["stops_away"]
    return (f"{n} STOP" if n == 1 else f"{n} STOPS"), CYAN


def draw_block(draw, y0, heading, direction, train, track):
    """One direction: where it goes, when it gets here, and where it is now.

    The terminus deliberately does not get the big line. Every northbound
    train out of here runs to Center City; which suburb it carries on to
    afterwards is not what anyone on this platform is deciding on. So the
    direction gets the large type, the countdown gets the other half of it,
    and the terminus survives as the strip's right-hand anchor.
    """
    no_train = train["dest"] == "No trains"

    # Line 1: direction, large, with the countdown opposite it.
    draw.text((2, y0), heading, font=FONT_LG, fill=YELLOW)

    mins = None if no_train else minutes_until(train)
    if mins is not None:
        countdown = "NOW" if mins == 0 else f"{mins} MIN"
        cw = draw.textlength(countdown, font=FONT_LG)
        draw.text((WIDTH - 3 - cw, y0), countdown, font=FONT_LG,
                  fill=GRAY if train.get("unknown") else delay_color(train["delay"]))

    # Line 2: clock time, delay chip, and the live status.
    if no_train:
        draw.text((2, y0 + 19), "None tonight", font=FONT_SM, fill=GRAY)
    else:
        draw.text((2, y0 + 19), train["arrives"], font=FONT_SM, fill=WHITE)
        x = 2 + draw.textlength(train["arrives"], font=FONT_SM) + 6
        if train.get("unknown"):
            draw.text((x, y0 + 22), "NO STATUS", font=FONT_TN, fill=GRAY)
        elif train["delay"] > 0:
            chip = f"+{train['delay']} MIN LATE"
            draw.text((x, y0 + 22), chip, font=FONT_TN, fill=delay_color(train["delay"]))
        else:
            draw.text((x, y0 + 22), "ON TIME", font=FONT_TN, fill=GREEN)

        stat, stat_color = status_text(track, train)
        if stat:
            sw = draw.textlength(stat, font=FONT_TN)
            draw.text((WIDTH - 3 - sw, y0 + 22), stat, font=FONT_TN, fill=stat_color)

    # With no train to relate it to, a bare rail of stops is just noise.
    if train.get("train_id") or track:
        draw_strip(draw, y0 + 37, direction, train, track)


def to_framebuffer(canvas):
    """A Pillow canvas turned into bytes these panels display correctly.

    The transforms compensate for how this particular array is wired, so they
    apply only on real hardware; the simulator shows the plain canvas.
    """
    arr = np.asarray(canvas).copy()
    if HARDWARE:
        arr = arr[:, :, ::-1]              # RGB -> BGR for the Active3 pinout
        arr = reorder_rows(arr)
        arr = np.flipud(np.fliplr(arr))
    return np.ascontiguousarray(arr).copy()


def render(state):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    draw = ImageDraw.Draw(canvas)

    # Header
    draw.text((3, 2), "[MED]", font=FONT_SM, fill=YELLOW)
    text_w = int(draw.textlength("[MED]", font=FONT_SM))
    canvas.paste(septa_logo, (text_w + 10, 2))
    swat_x = text_w + 10 + septa_logo.width + 6
    draw.text((swat_x, 1), "SWAT ENGR", font=FONT_MD, fill=GARNET)
    now = datetime.now().strftime("%I:%M %p")
    tw = int(draw.textlength(now, font=FONT_SM))
    draw.text((WIDTH - tw - 3, 2), now, font=FONT_SM, fill=WHITE)
    draw.line([(0, 20), (WIDTH, 20)], fill=GRAY, width=1)

    draw_block(draw, 22, "TO CENTER CITY", "N",
               state["northbound"][0], state["track_n"])
    draw.line([(0, 73), (WIDTH, 73)], fill=GRAY, width=1)
    draw_block(draw, 76, "TO MEDIA/WAWA", "S",
               state["southbound"][0], state["track_s"])

    return to_framebuffer(canvas)


# --------------------------------------------------------------------- main

septa_logo = load_septa_logo(SEPTA_LOGO_PATH)

state = {
    "northbound": no_trains(),
    "southbound": no_trains(),
    "track_n": None,
    "track_s": None,
    "fetching": False,
}


def refresh():
    state["fetching"] = True
    try:
        nb = fetch_trains("N")
        sb = fetch_trains("S")
        tv = line.fetch_trainview()
        state["northbound"] = nb
        state["southbound"] = sb
        state["track_n"] = line.track_train(nb[0]["train_id"], tv) if nb[0]["train_id"] else None
        state["track_s"] = line.track_train(sb[0]["train_id"], tv) if sb[0]["train_id"] else None
    finally:
        state["fetching"] = False


def main():
    wait_for_network()
    refresh()

    m1, pixels_across = build_map(WIDTH, 64, N_ADDR_LINES, True, row_offset=64)
    m2, _ = build_map(WIDTH, 64, N_ADDR_LINES, True, row_offset=0)
    pixelmap = combine_maps(m2, m1, pixels_across)

    framebuffer = render(state)
    geometry = piomatter.Geometry(
        width=WIDTH, height=HEIGHT, n_addr_lines=N_ADDR_LINES,
        map=pixelmap, n_lanes=N_LANES, n_planes=N_PLANES,
        n_temporal_planes=N_TEMPORAL_PLANES,
    )
    matrix = piomatter.PioMatter(
        colorspace=piomatter.Colorspace.RGB888Packed,
        pinout=piomatter.Pinout.Active3,
        framebuffer=framebuffer,
        geometry=geometry,
    )

    last_fetch = time.time()
    try:
        while True:
            now = time.time()
            # GPS moves faster than the timetable, so poll on the shorter cycle.
            if now - last_fetch > 30 and not state["fetching"]:
                threading.Thread(target=refresh, daemon=True).start()
                last_fetch = now
            framebuffer[:] = render(state)
            matrix.show()
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
