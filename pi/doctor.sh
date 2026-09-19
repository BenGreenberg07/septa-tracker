#!/usr/bin/env bash
# Health check for the SEPTA display Pi. Read-only: it changes nothing.
#
#   ./pi/doctor.sh
#
# Answers four questions, in the order they matter:
#   1. What is driving the panels right now, and is it more than one thing?
#   2. Is the Pi too hot, or not getting enough power?
#   3. Is it online, and can you reach it from your laptop?
#   4. Which version of the code is it running?

REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$REPO/pi/lib.sh"

echo "${BOLD}SEPTA display health check${OFF}   $(date '+%a %b %d, %I:%M %p')"

# ------------------------------------------------------------------ 1
section "1. What is driving the panels"

if service_exists; then
  state=$(systemctl is-active "$SERVICE" 2>/dev/null)
  boot=$(systemctl is-enabled "$SERVICE" 2>/dev/null)
  info "Service $SERVICE is ${BOLD}$state${OFF}, and on boot it is ${BOLD}$boot${OFF}."
  info "It runs: ${CYN}$(service_cmd)${OFF}"
  if [ -n "$(systemctl show -p DropInPaths --value "$SERVICE")" ]; then
    info "${DIM}(set by pi/set-panel-script.sh; the original is kept underneath)${OFF}"
  fi
else
  warn "No $SERVICE found, so nothing starts the display at boot."
fi

main_pid=$(systemctl show -p MainPID --value "$SERVICE" 2>/dev/null)
procs=$(panel_procs)
count=$(printf '%s' "$procs" | grep -c . )

if [ "$count" -eq 0 ]; then
  info "No display program is running, so the panels are idle."
else
  echo
  info "Display programs running now:"
  while read -r pid cmd; do
    [ -z "$pid" ] && continue
    if [ "$pid" = "$main_pid" ]; then who="started by the service"; else who="started by hand"; fi
    info "  PID $pid  ${DIM}($who)${OFF}  $cmd"
  done <<< "$procs"
fi

if [ "$count" -gt 1 ]; then
  bad "$count programs are driving the panels at once. This is the garbled"
  info "picture. Fix: ./pi/stop-panel.sh, then run only one thing."
elif [ "$count" -eq 1 ]; then
  ok "Exactly one program owns the panels."
fi

# Other things that could launch a second copy at boot, besides the service.
others=()
if have crontab; then
  crontab -l 2>/dev/null | grep -v '^#' | grep -q -i python && others+=("your crontab (crontab -l)")
  sudo -n crontab -l 2>/dev/null | grep -v '^#' | grep -q -i python && others+=("root's crontab (sudo crontab -l)")
fi
[ -f /etc/rc.local ] && grep -v '^#' /etc/rc.local | grep -q -i python && others+=("/etc/rc.local")
for f in "$HOME"/.config/autostart/*.desktop; do
  [ -f "$f" ] && grep -q -i -E 'python|septa|rpi5' "$f" && others+=("$f")
done
extra_units=$(systemctl list-unit-files --type=service --no-legend 2>/dev/null \
  | awk '{print $1}' | grep -i -E 'septa|panel|matrix|slideshow|commencement|display' \
  | grep -v -x "$SERVICE")
for u in $extra_units; do
  [ "$(systemctl is-enabled "$u" 2>/dev/null)" = "enabled" ] && others+=("service $u")
done

if [ "${#others[@]}" -gt 0 ]; then
  warn "Something else may also start a display program at boot:"
  for o in "${others[@]}"; do info "  - $o"; done
else
  ok "Nothing else is set to start a display program at boot."
fi

# ------------------------------------------------------------------ 2
section "2. Temperature and power"

t=$(read_temp)
if [ -n "$t" ]; then
  word=$(temp_word "$t")
  line="CPU is ${t} C, $(temp_color "$t")${word}${OFF}"
  case "$word" in
    COOL|WARM) ok "$line" ;;
    HOT)       warn "$line. Under 70 C is the goal; add a fan (Pi 5 Active Cooler)." ;;
    *)         bad  "$line. It is slowing itself down to survive." ;;
  esac
else
  warn "Could not read the temperature (is this a Raspberry Pi?)"
fi

fan=$(read_fan)
if [ -n "$fan" ]; then info "Fan is at ${fan}%."; else info "No fan detected."; fi

v=$(read_input_volts)
if [ -n "$v" ]; then
  if awk -v v="$v" 'BEGIN{exit !(v < 4.9)}'; then
    bad "Power input is ${v} V. Below about 4.9 V the Pi starts to struggle; check"
    info "the wires from the big PSU to the bonnet (thin or long wires sag)."
  else
    ok "Power input is ${v} V."
  fi
fi

mhz=$(read_arm_mhz)
[ -n "$mhz" ] && info "CPU is running at ${mhz} MHz (full speed on a Pi 5 is 2400)."

th=$(read_throttled)
if [ -z "$th" ]; then
  warn "Could not read the throttle status."
elif [ "$(( th ))" -eq 0 ]; then
  ok "Throttle status $th: no power or heat trouble since boot."
else
  if (( th & 0xF )); then bad "Throttle status $th: trouble happening RIGHT NOW."
  else warn "Throttle status $th: trouble happened earlier since boot."; fi
  decode_throttled "$th" | while read -r l; do info "  - $l"; done
fi

# ------------------------------------------------------------------ 3
section "3. Network"

info "Hostname:  $(hostname)"
info "IP:        $(hostname -I 2>/dev/null | awk '{print $1}')  ${DIM}(changes between boots on campus wifi)${OFF}"
ssid=$(iwgetid -r 2>/dev/null || nmcli -t -f active,ssid dev wifi 2>/dev/null | sed -n 's/^yes://p')
info "Wifi:      ${ssid:-not connected}"
mac=$(cat /sys/class/net/wlan0/address 2>/dev/null)
[ -n "$mac" ] && info "Wifi MAC:  $mac  ${DIM}(ITS needs this to register the Pi on Swat Device)${OFF}"

code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
  "https://www3.septa.org/api/Arrivals/index.php?station=Swarthmore&results=1")
if [ "$code" = "200" ]; then ok "The SEPTA API is reachable."
else bad "Cannot reach the SEPTA API (got '${code:-no answer}'). The board has no data."; fi

if [ "$(systemctl is-active ssh 2>/dev/null)" = "active" ]; then ok "SSH is on."
else warn "SSH is off. Run ./pi/setup-remote.sh to turn it on."; fi

if have tailscale && tailscale status >/dev/null 2>&1; then
  ok "Tailscale is up: reach this Pi as ${BOLD}$(hostname)${OFF} or $(tailscale ip -4 2>/dev/null | head -1)"
else
  warn "Tailscale is not set up, so your laptop cannot reliably reach this Pi."
  info "Run ./pi/setup-remote.sh."
fi

# ------------------------------------------------------------------ 4
section "4. Code"

if git -C "$REPO" rev-parse >/dev/null 2>&1; then
  info "Folder:    $REPO"
  info "From:      $(git -C "$REPO" remote get-url origin 2>/dev/null)"
  info "Version:   $(git -C "$REPO" log -1 --format='%h  %s  (%cr)')"
  dirty=$(git -C "$REPO" status --porcelain --untracked-files=no | wc -l | tr -d ' ')
  [ "$dirty" -gt 0 ] && warn "$dirty file(s) were edited directly on the Pi; pi/update.sh will back them up."
  git -C "$REPO" remote get-url origin 2>/dev/null | grep -q BenGreenberg07 \
    || warn "Still pulling from the original repo. Run ./pi/update.sh to switch to yours."
fi

# ------------------------------------------------------------ summary
echo
if [ "${#PROBLEMS[@]}" -eq 0 ]; then
  echo "${GRN}${BOLD}All clear.${OFF}"
else
  echo "${BOLD}${#PROBLEMS[@]} thing(s) to look at${OFF}, listed above with WARN or BAD."
fi
