#!/usr/bin/env bash
# Run one display program by hand, safely, to test it. Ctrl-C to stop.
#
#   ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
#   ./pi/try-script.sh rpi5/prod/swarthmore-bidirectional.py   (Nick's original)
#
# It stops the service first, so your test never fights with it (that fight is
# what made the garbled picture). When you press Ctrl-C it puts the service
# back the way it was.
#
# Flicker experiments: color depth trades against refresh rate. Try
#   SEPTA_PLANES=3 ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
#   SEPTA_TEMPORAL_PLANES=0 ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
# (only the tracked script reads these; defaults are 4 and 2, as Nick had them).

REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$REPO/pi/lib.sh"

script="$1"
[ -z "$script" ] && { echo "Usage: ./pi/try-script.sh <path to a .py file>"; exit 1; }
case "$script" in /*) ;; *) script="$REPO/$script" ;; esac
[ -f "$script" ] || { echo "${RED}No such file:${OFF} $script"; exit 1; }

py=$(find_panel_python) || {
  echo "${RED}Could not find a Python that has the panel library installed.${OFF}"
  echo "Run ./pi/doctor.sh and look at what the service runs."
  exit 1
}

was_active=0
[ "$(systemctl is-active "$SERVICE" 2>/dev/null)" = "active" ] && was_active=1
"$REPO/pi/stop-panel.sh" >/dev/null || { echo "Could not clear the panels."; exit 1; }

restore() {
  echo
  if [ "$was_active" -eq 1 ]; then
    sudo systemctl start "$SERVICE" && echo "Put the service back: it is running again."
  else
    echo "The service was off before, so it is still off."
  fi
}
trap restore EXIT

echo "${BOLD}Running${OFF} $(basename "$script") ${DIM}with $py${OFF}"
[ -n "$SEPTA_PLANES$SEPTA_TEMPORAL_PLANES" ] && \
  echo "  planes=${SEPTA_PLANES:-4} temporal_planes=${SEPTA_TEMPORAL_PLANES:-2}"
echo "${DIM}Ctrl-C to stop. Watch the heat in another terminal: ./pi/temp.sh${OFF}"
echo

cd "$(dirname "$script")" || exit 1
# The panel library talks to hardware, so run as root, keeping our settings.
sudo --preserve-env=SEPTA_PLANES,SEPTA_TEMPORAL_PLANES "$py" -u "$script"
