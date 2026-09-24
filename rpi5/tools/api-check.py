#!/usr/bin/env python3
"""Explain what the board is showing, and why there is or is not a train dot.

    ./pi/py.sh rpi5/tools/api-check.py     (on the Pi)
    ./venv/bin/python rpi5/tools/api-check.py   (on a Mac)

Uses the display's own fetching and matching code, so it tells you exactly what
the board decided, not an approximation of it. Needs no panels, so it is safe
to run while the display is up.

The dot appears only when the train the board picked also has a live GPS
record. SEPTA only reports a train once it is actually running, so a train
still sitting at its origin has no record and correctly shows SCHED.
"""

import importlib.util
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RPI5 = os.path.dirname(HERE)
sys.path.insert(0, RPI5)

spec = importlib.util.spec_from_file_location(
    "board", os.path.join(RPI5, "prod", "swarthmore-tracked.py"))
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
import septa_line as line

print(f"Now: {datetime.now():%a %d %b %Y, %I:%M %p}\n")

tv = line.fetch_trainview()
print(f"SEPTA is tracking {len(tv)} trains right now, of which these are on "
      "the Media/Wawa line:")
mw = {k: v for k, v in tv.items()
      if "Media" in (v.get("line") or "") or "Wawa" in (v.get("line") or "")}
if not mw:
    print("  none. No Media/Wawa train is moving, so no board can show a dot.")
for num, t in sorted(mw.items()):
    pos = line.locate_train(t)
    where = f"index {pos:.2f} on the line" if pos is not None else "not placeable"
    print(f"  train {num:>5}  {t.get('currentstop')} -> {t.get('nextstop')}"
          f"  | {where} | late {t.get('late')}")

for direction, label in (("N", "TO CENTER CITY"), ("S", "TO MEDIA/WAWA")):
    print(f"\n{'=' * 60}\n{label}")
    trains, feed_time = D.fetch_trains(direction)
    t = trains[0]
    if feed_time:
        skew = (datetime.now() - feed_time).total_seconds()
        print(f"  Feed clock  : {feed_time:%-I:%M %p}, this machine is "
              f"{skew:+.0f}s from it")
    print(f"  Board shows : {t['origin'] or '?'} -> {t['dest']} at {t['arrives']}"
          f"  (train id {t['train_id'] or 'none'})")
    if t.get("unknown"):
        print("  Status      : SEPTA reports no status for it (the 999 sentinel)")
    else:
        print(f"  Status      : {'on time' if not t['delay'] else str(t['delay']) + ' min late'}")

    if not t["train_id"]:
        print("  Dot         : no, there is no train to show")
        continue
    track = line.track_train(t["train_id"], tv, direction)
    if track:
        if track["departed"]:
            print(f"  Dot         : YES, but it has already left Swarthmore, "
                  f"between {track['current']} and {track['next']}")
        else:
            print(f"  Dot         : YES, {track['stops_away']} stop(s) away, "
                  f"between {track['current']} and {track['next']}")
    else:
        print(f"  Dot         : no, because train {t['train_id']} has no live GPS record")
        print("                This is correct if it has not started its run yet.")
        print(f"                (SEPTA is currently tracking: {', '.join(sorted(mw)) or 'no Media/Wawa trains'})")
