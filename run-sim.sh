#!/usr/bin/env bash
# Run the Swarthmore board on this machine, against the panel simulator.
set -e
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
./venv/bin/pip -q install requests pillow numpy
exec ./venv/bin/python rpi5/prod/swarthmore-tracked.py
