# Live train tracking

How the Swarthmore board knows *when* the next train comes and *where* it is
on the Media/Wawa line, and the two layouts that show it:

- `rpi5/prod/swarthmore-tracked.py`, the **tracked board**: countdowns plus a
  line map under each direction with the train placed by GPS.
- `rpi5/prod/swarthmore-big.py`, the **big-type board**: no map, countdowns
  about 41 LEDs tall, for reading from the far end of the platform.

The big-type board imports the tracked one and replaces only `render()`, so
everything below about fetching, timing and failure handling applies to both.

## Where the data comes from

Three SEPTA requests per refresh, every 30 seconds:

- `Arrivals/index.php?station=Swarthmore&results=20`: the next trains both
  ways, each with its `train_id`, scheduled time and status. One call with no
  `direction=` returns the `Northbound` and `Southbound` lists together, and
  `parse_trains()` picks a direction by key.
- `TrainView/index.php`: every active regional rail train's live GPS fix,
  `currentstop`, `nextstop` and `late` minutes, keyed by `trainno`.
- `Alerts/get_alert_data.php?req1=rr_route_med`: service messages for this
  line only (a few hundred bytes, where the full alert index is over 150 KB).

`train_id` and `trainno` are the same number, so the train on the board can be
matched to its live GPS record.

All three go through `septa_line.get_json()`: one shared session (so the
connection is reused), a project `User-Agent`, and a 10 second timeout.

### When SEPTA fails or says no

A failed refresh keeps the last good data on the board (it is marked stale
once it is old, below) and backs off: 30 s, 60, 120, 240, then every 5
minutes, dropping straight back to 30 s on the first success. A **429 or 403**
is SEPTA saying we are asking too often, which is different from a timeout: it
jumps straight to the 5 minute cap, or to SEPTA's `Retry-After` if that is
longer. Retrying a refusal at full speed is how a soft throttle becomes an IP
block. A failed alert fetch never costs a good train fetch, but a refused one
still slows everything down.

## Placing a train on the line

`rpi5/septa_line.py` holds the Media/Wawa station chain (Temple through Wawa)
with coordinates baked in from SEPTA's `get_locations.php` rail_stations feed.
`locate_train()` turns a GPS record into a fractional index along that chain:

1. If `currentstop` and `nextstop` both resolve to stations, the GPS fix is
   projected onto that segment, so `16.89` means "89% of the way from Media
   to Moylan-Rose Valley".
2. If only one resolves, it snaps to that station.
3. With neither, it falls back to a nearest-segment search over the whole
   line, rejecting fixes more than 1.5 km off (those belong to another line).

SEPTA spells some stops differently across feeds ("Market East" vs "Jefferson
Station", "Gray 30th Street" vs "30th Street Station"), so `ALIASES` plus a
loose prefix match normalizes them.

`track_train()` then works out `stops_away`, **signed by direction of
travel**: a Center City train runs down the indices and a Wawa train up them,
so once a train has passed Swarthmore it is `departed` rather than counting its
stops back up as though it were approaching again.

## The tracked board

```
[MED] (S) SWAT ENGR               09:46 PM
TO CENTER CITY                       6 MIN
9:49 PM +3 MIN LATE    THEN 10:52  3 STOPS
 *---*---■---*-(SWAT)-*---*---*---*---*
WAWA MEDIA    SWAT                    PENN
TO MEDIA/WAWA                       29 MIN
...
```

Each direction gets its heading and countdown in large type, then the
scheduled time, a delay chip, the next train after (`THEN 10:52`) and the live
status, then the line map.

**The map is fixed, not per train.** Each strip spans Penn Medicine to Wawa
with a dot at every stop and Swarthmore ringed in yellow. The span does not
follow the train: anchoring it on each train's origin and terminus made the
picture rearrange itself between arrivals, and for a through-running train it
named stations on other lines. A map that stays put can be read at a glance.

**Both maps run toward their own destination.** The Center City map is the
line drawn backwards (`WAWA` left, `PENN` right) and the Media/Wawa map forwards
(`PENN` left, `WAWA` right), so the right-hand end always matches the heading
above it and every train dot moves left to right. The stretch a train has
covered stays dimly lit with a short brightening tail into the dot.

**The stop name is printed under the dot**, worked out from the dot's own
position, never from TrainView's `currentstop`. That field names the last
station the train actually called at, which on an express can be several stops
behind where the GPS puts it. The full name is used when it fits, the
timetable short code otherwise. A train standing on a rail end recolours that
label instead of printing the same stop twice.

**One train, one colour.** Countdown, delay chip, dot, label and travelled
line all take their colour from the Arrivals delay: green on time, orange up
to 5 minutes late, red beyond. TrainView has its own `late` field, but the two
feeds disagree often enough that colouring the dot separately once put a green
dot under an orange countdown.

**The dot's shape says the same thing,** for the one in twelve men with
red-green colour blindness: a solid circle on time, a square a little late, a
triangle badly late, and a hollow ring when SEPTA has no status. All four stay
distinct in grayscale.

Status reads `N STOPS`, `ARRIVING` when GPS puts the train at Swarthmore,
`DEPARTED` once it has passed, or `SCHED` when the train has no GPS record yet
(SEPTA only reports trains that are actually running). With no train at all
the map is suppressed rather than showing a bare rail.

Small text is a 5x7 LED pixel font (`rpi5/pixelfont.py`), uppercase, as on
real departure boards: antialiased TrueType at 9 px smears into half-lit LEDs.

## The big-type board

```
[MED] (S) SWAT ENGR               09:46 PM
CENTER CITY                    ██
9:49 +3 LATE                    █    MIN
1 STOP  THEN 10:49             ███
MEDIA/WAWA                   ███ ███
10:12 +5 LATE                  █ █ █
12 STOPS                     ███ ███ MIN
```

The same data with the map removed and the countdown given the height it
freed: digits about 41 LEDs tall, readable from much further away than the
map's labels. Beside it, at 14 px: the direction, the scheduled time and delay,
the live status, and the train after if it fits. `NOW` replaces the number at
zero; a train more than 99 minutes out shows its clock time instead. Colours
follow the same one-train-one-colour rule.

## Saying when the board cannot be trusted

The header normally reads `SWAT ENGR`. It gives way, in order of how badly
each one undermines the board, to:

1. `NO DATA YET` before the first successful fetch.
2. `DATA n MIN OLD` once the last good fetch is over 3 minutes old. If the
   feed is old, so is everything else on the board.
3. `CLOCK OFF`, with the clock itself drawn red, when the Pi's clock and the
   timestamp in SEPTA's own response differ by more than 2 minutes. Every
   countdown is computed from that clock. A Pi 5 has no battery-backed clock,
   so a boot without network time starts at whenever it last shut down.
4. A **service alert**, paged across the whole header four seconds a page,
   starting from its first word whenever a new message arrives.

All times are taken in `America/New_York` explicitly (`local_now()`), whatever
zone the Pi is set to. SEPTA's timestamps are naive Philadelphia time, so a Pi
left on UTC would otherwise put every train hours out; the skew check still
catches a clock that is actually wrong.

### Service alerts

SEPTA's alert text is HTML: an `<h3>` title then a `<p>` body per item,
usually pasted from Word or Outlook, so the body is wrapped in nested
`<span>`s that split words mid-way (`train</span><span>s`). `clean_alert()`
removes inline tags without a space, turns block tags into one, joins each
title to its body with a colon, unescapes entities, and folds curly quotes and
dashes to ASCII for the pixel font. It was checked against all 309 rows of the
live alert index in October 2026.

The `last_updated` field is not reliable: in October 2026 the Media/Wawa row
said `2023-05-30` while carrying a current advisory about platform changes.
`./pi/py.sh rpi5/tools/api-check.py` prints the alert exactly as the board will
page it.

### When SEPTA has no status

Both feeds use a **999-minute delay as a sentinel** meaning "no status for this
train", not a real delay. Rendering it literally produced a board that
read `+999 MIN LATE`. Worse, silently clamping it to zero would have claimed
the train was on time, which is a different lie.

So 999 is detected in both the Arrivals and TrainView feeds and surfaced as
`NO STATUS`, with the countdown and the marker drawn gray instead of green. The
countdown still runs off the timetable, which is genuinely known. The board says
what it knows and no more.

## Overnight, and when it hangs

**Quiet hours.** From 00:30 to 05:00 the board drops to 25% brightness,
unless a train is due within 20 minutes either way, so a late last train or an
early first one is never shown dimmed. Scaling the frame cuts each LED's
on-time, which saves power and heat (the Pi has no fan). Override with
`SEPTA_QUIET_HOURS=01:00-05:30` and `SEPTA_QUIET_LEVEL=0.15`; a malformed
value never dims.

**Watchdog.** `Restart=always` catches a crash, not a hang. The main loop
sends systemd `WATCHDOG=1` after each frame actually goes out, so a hang in
drawing or the panel driver stops the pings and systemd restarts the display
after 90 seconds. A refresh thread stuck for ten minutes stops them too.
`pi/set-panel-script.sh` turns this on (`WatchdogSec=90`, `NotifyAccess=main`)
only for scripts that send the pings, and off for the original boards, which
would otherwise be killed for never pinging. Run by hand, the pings do
nothing.

## Running it

On a laptop, double-click **Start Panel.command** in the repo root, or from a
terminal:

```bash
./run-sim.sh          # the tracked board
./run-sim.sh big      # the big-type board
```

It serves each frame at http://127.0.0.1:8800 with the LED grid drawn in. It
does not hot-reload: stop and restart it after an edit. For a specific state,
import the module with `importlib` and call `render(state)` with a synthetic
state dict; that is how edge cases get checked.

On the Pi:

```bash
./pi/try-script.sh rpi5/prod/swarthmore-tracked.py     # or swarthmore-big.py
./pi/set-panel-script.sh rpi5/prod/swarthmore-big.py   # make it the default
```

When the piomatter library is absent the script falls back to
`rpi5/sim/piomatter_sim.py`. No code paths differ apart from the
panel-specific transforms (BGR channel order, row reordering, 180 degree flip),
which are applied only on hardware, so the simulator shows the plain canvas.

## Regenerating the showcase

`rpi5/tracking-scenarios.png` shows the tracked board's states. It is
generated by feeding synthetic records into the production drawing code, so it
never drifts from what the panel actually renders:

```bash
./venv/bin/python rpi5/tools/make-scenarios.py
```
