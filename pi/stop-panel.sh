#!/usr/bin/env bash
# Stop everything that is driving the panels, so that nothing is.
#
#   ./pi/stop-panel.sh             stop now; the service still starts on next boot
#   ./pi/stop-panel.sh --disable   stop now, and do not start at boot either
#
# This is the fix for the garbled picture: two programs were writing to the
# panels at once. Stop everything, then start exactly one thing.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$REPO/pi/lib.sh"

if service_exists; then
  sudo systemctl stop "$SERVICE" && echo "Stopped $SERVICE."
  if [ "$1" = "--disable" ]; then
    sudo systemctl disable "$SERVICE" >/dev/null 2>&1 && echo "It will no longer start at boot."
  fi
fi

# Anything started by hand (a terminal, an old tab someone forgot about).
pids=$(panel_procs | awk '{print $1}')
if [ -n "$pids" ]; then
  echo "Stopping programs started by hand: $(echo $pids)"
  sudo kill $pids 2>/dev/null
  sleep 3
  left=$(panel_procs | awk '{print $1}')
  [ -n "$left" ] && { echo "Forcing: $(echo $left)"; sudo kill -9 $left 2>/dev/null; sleep 1; }
fi

if [ -z "$(panel_procs)" ]; then
  echo "${GRN}Nothing is driving the panels now.${OFF} They will freeze or go dark."
else
  echo "${RED}Something is still running:${OFF}"; panel_procs
  exit 1
fi
