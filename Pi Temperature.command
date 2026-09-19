#!/usr/bin/env bash
# Double-click to watch the Pi's temperature live from your laptop. Ctrl-C to stop.
PI="${SEPTA_PI:-fetcar@septa-pi}"
# shellcheck disable=SC2088  # ~ expands on the Pi, which is intended
ssh -t "$PI" '~/septa-tracker/pi/temp.sh' || {
  echo; echo "Couldn't reach $PI. Is Tailscale on, on both the laptop and the Pi?"
  read -r -n 1 -p "Press any key to close."; }
