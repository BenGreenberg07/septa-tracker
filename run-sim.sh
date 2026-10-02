#!/usr/bin/env bash
# Run the Swarthmore board on this machine, against the panel simulator.
#   ./run-sim.sh         the tracked board, with the line map
#   ./run-sim.sh big     the big-type board, countdowns only
set -e
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
./venv/bin/pip -q install requests pillow numpy
case "${1:-tracked}" in
  big)     script=rpi5/prod/swarthmore-big.py ;;
  tracked) script=rpi5/prod/swarthmore-tracked.py ;;
  *)       echo "usage: $0 [tracked|big]" >&2; exit 2 ;;
esac
exec ./venv/bin/python "$script"
