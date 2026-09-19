# Live train tracking

Adds a position strip to the Swarthmore bidirectional board. For each
direction the board now shows not just *when* the next train is scheduled, but
*where it currently is* on the Media/Wawa line.

## How it works

Two SEPTA feeds are combined:

- `Arrivals/index.php?station=Swarthmore`: the next scheduled train per
  direction, including its `train_id`.
- `TrainView/index.php`: every active regional rail train's live GPS fix,
  `currentstop`, `nextstop` and `late` minutes, keyed by `trainno`.

`train_id` and `trainno` are the same number, so the scheduled train on the
board can be matched to its live GPS record.

`rpi5/septa_line.py` holds the Media/Wawa station chain (20 stops, Temple
through Wawa) with coordinates baked in from SEPTA's `get_locations.php`
rail_stations feed. `locate_train()` turns a GPS record into a fractional
index along that chain:

1. If `currentstop` and `nextstop` both resolve to stations, the GPS fix is
   projected onto that segment, so `16.89` means "89% of the way from Media
   to Moylan-Rose Valley".
2. If only one resolves, it snaps to that station.
3. With neither, it falls back to a nearest-segment search over the whole
   line, rejecting fixes more than 1.5 km off (those belong to another line).

SEPTA spells some stops differently across feeds ("Market East" vs "Jefferson
Station", "Gray 30th Street" vs "30th Street Station"), so `ALIASES` plus a
loose prefix match normalizes them.

## What you see

```
TO CENTER CITY                    9 MIN
4:28 PM  +4 MIN LATE            3 STOPS
 Media ●━━◆- - - - -◎- - - - - - - - -○ Chestnut H East
                   SWAT
```

The big line is the **direction and the countdown**, not the terminus. Every
northbound train out of Swarthmore runs to Center City; which suburb it carries
on to afterwards is not what anyone on this platform is deciding on. So the
terminus is demoted to the strip's right-hand anchor, where it is available as
context, and the space goes to the two things a waiting rider actually wants:
where this train is headed and how long until it gets here.

The countdown already has the delay folded in, so it is the real wait rather
than the timetable's. Countdown, delay chip and train marker all take the same
color, so a delay reads three ways at once.

- **Left anchor** is the train's first stop, **right anchor** its last, and
  **Swarthmore** the ringed yellow anchor between them.
- The filled marker is the train, placed by GPS along the approach, with a
  trail showing how much of it has been covered.
- The rail past Swarthmore is fainter than the approach: what happens after
  this platform is context, not the thing you are waiting for.
- Status reads `N STOPS`, `ARRIVING` when GPS puts the train here, or `SCHED`
  when the train has no GPS fix yet.
- With no train at all, the strip is suppressed rather than showing a bare rail.

Swarthmore sits at a fixed 150 px rather than its true proportional place on
the run, so the approach gets most of the width. That bias is deliberate.

### When SEPTA has no status

Both feeds use a **999-minute delay as a sentinel** meaning "no status for this
train", not a real delay. Rendering it literally produced a board that
read `+999 MIN LATE`. Worse, silently clamping it to zero would have claimed
the train was on time, which is a different lie.

So 999 is detected in both the Arrivals and TrainView feeds and surfaced as
`NO STATUS`, with the countdown and the marker drawn gray instead of green. The
countdown still runs off the timetable, which is genuinely known. The board says
what it knows and no more.

### Trains that join from another line

A southbound train may start at Norristown, which is not on the Media/Wawa
line at all. `journey_fraction()` measures progress over the stretch of the run
that *is* on this line, treating such a train as entering at Temple, while the
label still names the true first stop. So the marker position is honest about
Media/Wawa progress and the anchor is honest about where the train came from.

## Running it

On a laptop, double-click **Start Panel.command** in the repo root. It stops any
previous instance, creates the venv on first run, starts the board detached, and
opens the browser once the first frame is served. **Stop Panel.command** stops
it. Both are safe to run twice.

From a terminal instead:

```bash
./run-sim.sh
```

On the Pi 5, the same display script runs against the real panels:

```bash
source venv/bin/activate
python3 rpi5/prod/swarthmore-tracked.py
```

When the piomatter library is absent the script falls back to
`rpi5/sim/piomatter_sim.py`, which serves each frame at http://127.0.0.1:8800
with the LED grid drawn in. No code paths differ apart from the panel-specific
transforms (BGR channel order, row reordering, 180 degree flip), which are
applied only on hardware.

The GPS feed updates faster than the timetable, so the refresh cycle is 30
seconds rather than the original 60.

## Regenerating the showcase

`rpi5/tracking-scenarios.png` shows all ten board states. It is generated by
feeding synthetic records into the production drawing code, so it never drifts
from what the panel actually renders:

```bash
./venv/bin/python rpi5/tools/make-scenarios.py
```
