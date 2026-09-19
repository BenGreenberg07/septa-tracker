#!/usr/bin/env bash
# Double-click to run the Pi's health check from your laptop.
PI="${SEPTA_PI:-fetcar@septa-pi}"
# shellcheck disable=SC2088  # ~ expands on the Pi, which is intended
ssh -t "$PI" '~/septa-tracker/pi/doctor.sh' || echo "Couldn't reach $PI. Is Tailscale on, on both the laptop and the Pi?"
echo; read -r -n 1 -p "Press any key to close."
