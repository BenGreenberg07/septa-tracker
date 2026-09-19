#!/usr/bin/env bash
# Choose which program the display runs automatically at boot.
#
#   ./pi/set-panel-script.sh rpi5/prod/swarthmore-tracked.py   switch to it
#   ./pi/set-panel-script.sh --show                            what runs now
#   ./pi/set-panel-script.sh --revert                          back to the original
#
# It does not rewrite Nick's service file. It adds a small override on top
# (/etc/systemd/system/<service>.d/panel-script.conf) that swaps only the
# program, so everything else he configured (auto-restart, wait for network,
# which user) stays, and --revert simply deletes the override.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$REPO/pi/lib.sh"

DROPIN_DIR="/etc/systemd/system/${SERVICE}.d"
DROPIN="$DROPIN_DIR/panel-script.conf"

show() {
  echo "At boot the display runs: ${CYN}$(service_cmd)${OFF}"
  [ -f "$DROPIN" ] && echo "${DIM}(chosen with this script; --revert goes back to the original)${OFF}"
}

confirm_one() {
  sleep 6
  echo
  state=$(systemctl is-active "$SERVICE")
  count=$(panel_procs | grep -c .)
  if [ "$state" = "active" ] && [ "$count" -eq 1 ]; then
    echo "${GRN}${BOLD}Running, and it is the only program on the panels.${OFF}"
  else
    echo "${RED}Service is '$state' with $count program(s) on the panels.${OFF} Last log lines:"
    sudo journalctl -u "$SERVICE" -n 15 --no-pager
    exit 1
  fi
}

case "$1" in
  ""|-h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  --show)       show; exit 0 ;;
  --revert)
    [ -f "$DROPIN" ] || { echo "Nothing to revert; the original is already in use."; show; exit 0; }
    sudo rm -f "$DROPIN"
    sudo systemctl daemon-reload
    "$REPO/pi/stop-panel.sh" >/dev/null
    sudo systemctl restart "$SERVICE"
    echo "Reverted to the original program."; show; confirm_one; exit 0 ;;
esac

script="$1"
case "$script" in /*) ;; *) script="$REPO/$script" ;; esac
[ -f "$script" ] || { echo "${RED}No such file:${OFF} $script"; exit 1; }
script="$(cd "$(dirname "$script")" && pwd)/$(basename "$script")"

py=$(find_panel_python) || {
  echo "${RED}Could not find a Python that has the panel library installed.${OFF}"; exit 1; }

if ! service_exists; then
  echo "No $SERVICE exists yet, so creating one."
  sudo tee "/etc/systemd/system/$SERVICE" >/dev/null <<UNIT
[Unit]
Description=SEPTA station display
Wants=network-online.target
After=network-online.target

[Service]
ExecStart=$py -u $script
WorkingDirectory=$(dirname "$script")
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
else
  sudo mkdir -p "$DROPIN_DIR"
  sudo tee "$DROPIN" >/dev/null <<CONF
# Written by pi/set-panel-script.sh on $(date '+%Y-%m-%d %H:%M').
# Delete this file (or run pi/set-panel-script.sh --revert) to go back.
[Service]
ExecStart=
ExecStart=$py -u $script
WorkingDirectory=$(dirname "$script")
CONF
fi

sudo systemctl daemon-reload
"$REPO/pi/stop-panel.sh" >/dev/null      # clear anything started by hand
sudo systemctl enable "$SERVICE" >/dev/null 2>&1
sudo systemctl restart "$SERVICE"
show
confirm_one
