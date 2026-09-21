#!/usr/bin/env bash
# Run a Python file with whichever interpreter on this Pi has the libraries.
#
#   ./pi/py.sh rpi5/tools/api-check.py
#
# The venv is not in the same place on every machine, so this finds it instead
# of guessing. For anything that drives the panels, use try-script.sh instead:
# it also stops the service first.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=/dev/null
source "$REPO/pi/lib.sh"

py=$(find_panel_python) || true

# Nothing with the panel library: fall back to anything that can at least do
# the API tools, which need requests, Pillow and numpy but no hardware.
if [ -z "$py" ]; then
  for cand in "$REPO/venv/bin/python" "$REPO/rpi5/venv/bin/python" \
              "$HOME/venv/bin/python" "$HOME/.venv/bin/python" /usr/bin/python3; do
    [ -x "$cand" ] || continue
    if "$cand" -c "import requests, PIL, numpy" 2>/dev/null; then py="$cand"; break; fi
  done
fi

if [ -z "$py" ]; then
  echo "Could not find a Python with the needed libraries. Run ./pi/doctor.sh"
  echo "and look at what the display service uses."
  exit 1
fi

exec "$py" "$@"
