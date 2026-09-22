# SEPTA station display: context for Claude

You are probably running on the Raspberry Pi 5 that drives the display, or on
Ben's Mac. Sessions do not share history between machines, so this file is the
handoff.

## What this is

A 16-panel (4x4, 256x128) HUB75 LED departure board for the Swarthmore SEPTA
station, showing live Media/Wawa train information. Originally an E90 project by
Aurelien Carretta and Nicholas Fettig, advised by Prof. Emad Masroor. Ben
Greenberg ('29) is the named successor maintainer. The board was lost for a
while and recovered in September 2026.

## Hardware

- Raspberry Pi 5, user `fetcar`, repo at `/home/fetcar/septa-tracker`.
- Active3 triple HUB75 bonnet, 2 of its 3 ports used, panels in a serpentine
  daisy chain.
- One 5V/100A PSU powers the panels **and** the Pi, through wires soldered to
  the bonnet. Suspect this first if you see under-voltage.
- systemd unit `septa-display.service` starts the display at boot.

## Read this before changing anything

- **`LAB-GUIDE.md`** is the step-by-step operating guide. Start there.
- **`COMMANDS.md`** is the command cheat sheet, Pi and SSH forms.
- **`HARDWARE.md`** records confirmed hardware faults (under-voltage, heat,
  panel 14 red), the evidence for each, and what to buy.
- **`rpi5/TRACKING.md`** explains how the live train tracking works.
- **`pi/`** holds the maintenance scripts. `pi/doctor.sh` is read-only and is
  almost always the right first command.
- **`rpi5/tools/`** holds `panel-test.py` (dead pixel and wiring patterns) and
  `api-check.py` (why the board shows what it shows). Run both through
  `pi/try-script.sh` (panel-test, which needs the panels) or `pi/py.sh`
  (api-check, which does not).

## Traps that have already bitten this project

1. **Only one program may drive the panels.** Two at once produces a garbled mix
   of both pictures, which is exactly what happened in September 2026 when the
   old graduation slideshow service and the train board ran together. Use
   `pi/stop-panel.sh` and `pi/try-script.sh`, which enforce this.
2. **SEPTA sends `999 min` as a sentinel** meaning "no status for this train",
   in both the Arrivals and TrainView feeds. It is not a delay. Showing it
   literally gives `+999 MIN LATE`; clamping it to zero falsely claims the train
   is on time. It is surfaced as `NO STATUS` in gray. Do not "simplify" this.
3. **Panel-specific transforms are hardware-only.** `render()` in
   `rpi5/prod/swarthmore-tracked.py` swaps RGB to BGR, reorders rows, and flips
   180 degrees, but only when the piomatter library is present. On a laptop the
   simulator shows the un-transformed canvas. If red appears blue on the real
   panels, that is this code.
4. **The pixel map is fragile.** `build_map` / `combine_maps` encode the
   two-chain serpentine wiring. Errors scramble the picture into blocks. Compare
   against `rpi5/prod/swarthmore-bidirectional.py`, which is known good.
5. **Never put the Pi password in this repo.** It is public. The password is in
   the separate onboarding PDF.

## Running it

- On the Pi: `pi/try-script.sh <file>` to test, `pi/set-panel-script.sh <file>`
  to set what runs at boot.
- On a Mac: `./run-sim.sh` renders the board in a browser at
  http://127.0.0.1:8800, no hardware needed.
- Flicker experiments: `SEPTA_PLANES` and `SEPTA_TEMPORAL_PLANES` env vars
  (defaults 4 and 2).

## Open items

- Move the Pi's wifi off Nick's personal eduroam login to Swat Device (ITS).
  `pi/doctor.sh` prints the MAC address they need.
- Confirm heat and input voltage are sane before leaving it running unattended.
- SEPTA alert messages (expresses skipping Swarthmore) are still unused; both
  project documents call this the top missing feature, likely as a ticker.
- The tracking board and the `pi/` scripts have never run on the real hardware.
