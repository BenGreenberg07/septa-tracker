# shellcheck shell=bash disable=SC2034
# Shared helpers for the pi/ scripts. Sourced by them, never run directly.

SERVICE="${SEPTA_SERVICE:-septa-display.service}"

if [ -t 1 ]; then
  RED=$'\e[31m'; YEL=$'\e[33m'; GRN=$'\e[32m'; CYN=$'\e[36m'
  DIM=$'\e[2m'; BOLD=$'\e[1m'; OFF=$'\e[0m'
else
  RED=; YEL=; GRN=; CYN=; DIM=; BOLD=; OFF=
fi

PROBLEMS=()
ok()      { echo "  ${GRN}OK${OFF}    $*"; }
warn()    { echo "  ${YEL}WARN${OFF}  $*"; PROBLEMS+=("$*"); }
bad()     { echo "  ${RED}BAD${OFF}   $*"; PROBLEMS+=("$*"); }
info()    { echo "        $*"; }
section() { echo; echo "${BOLD}$*${OFF}"; }
have()    { command -v "$1" >/dev/null 2>&1; }

# ---------------------------------------------------------------- health

# CPU temperature in degrees C, one decimal. Empty if unknown.
read_temp() {
  if have vcgencmd; then
    vcgencmd measure_temp 2>/dev/null | sed -E "s/temp=([0-9.]+).*/\1/"
  elif [ -r /sys/class/thermal/thermal_zone0/temp ]; then
    awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp
  fi
}

# Raw throttle bitmask such as 0x50005. Empty if unknown.
read_throttled() {
  have vcgencmd && vcgencmd get_throttled 2>/dev/null | sed -E 's/throttled=//'
}

# Voltage arriving at the Pi 5's power input, e.g. 5.08. Empty if unavailable.
read_input_volts() {
  have vcgencmd || return 0
  vcgencmd pmic_read_adc EXT5V_V 2>/dev/null | sed -nE 's/.*=([0-9.]+)V.*/\1/p'
}

read_arm_mhz() {
  have vcgencmd && vcgencmd measure_clock arm 2>/dev/null | awk -F= '{printf "%d", $2/1000000}'
}

# Fan speed as a percentage, for the Pi 5 Active Cooler. Empty if no fan.
read_fan() {
  local d cur max
  for d in /sys/class/thermal/cooling_device*; do
    [ "$(cat "$d/type" 2>/dev/null)" = "pwm-fan" ] || continue
    cur=$(cat "$d/cur_state" 2>/dev/null); max=$(cat "$d/max_state" 2>/dev/null)
    [ -n "$max" ] && [ "$max" -gt 0 ] && echo $(( cur * 100 / max ))
    return 0
  done
}

# Plain-English meaning of each throttle bit. "NOW" bits are happening at this
# moment; the lower-case ones happened at some point since the Pi last booted.
decode_throttled() {
  local v=$(( ${1:-0} ))
  (( v & 0x1 ))     && echo "UNDER-VOLTAGE NOW: the supply is sagging below 4.63 V"
  (( v & 0x2 ))     && echo "CPU SPEED CAPPED NOW, usually because of under-voltage"
  (( v & 0x4 ))     && echo "THROTTLED NOW: the Pi is slowing itself down"
  (( v & 0x8 ))     && echo "SOFT TEMPERATURE LIMIT NOW: hot enough to back off"
  (( v & 0x10000 )) && echo "under-voltage has happened since boot"
  (( v & 0x20000 )) && echo "CPU speed was capped at some point since boot"
  (( v & 0x40000 )) && echo "throttling has happened since boot"
  (( v & 0x80000 )) && echo "soft temperature limit was hit since boot"
  return 0
}

# One word for a temperature. The Pi 5 starts throttling at about 80 C and
# hard-limits at 85 C; 60-70 C under load is normal.
temp_word() {
  awk -v t="$1" 'BEGIN {
    if (t == "")      print "UNKNOWN";
    else if (t < 60)  print "COOL";
    else if (t < 70)  print "WARM";
    else if (t < 80)  print "HOT";
    else              print "THROTTLING";
  }'
}

temp_color() {
  case "$(temp_word "$1")" in
    COOL) printf '%s' "$GRN" ;;
    WARM) printf '%s' "$CYN" ;;
    HOT)  printf '%s' "$YEL" ;;
    *)    printf '%s' "$RED" ;;
  esac
}

# ------------------------------------------------------------ the panels

# "PID command" for every Python process that looks like a display program.
# Matches on python processes only, so these scripts never match themselves.
panel_procs() {
  pgrep -a python 2>/dev/null \
    | grep -E 'rpi5|septa|swarthmore|slideshow|commencement|piomatter' \
    | grep -v -E 'pgrep|grep'
}

# The command line systemd runs for the display service, e.g.
# "/home/fetcar/venv/bin/python /home/fetcar/septa-tracker/rpi5/prod/x.py".
service_cmd() {
  systemctl show -p ExecStart --value "$SERVICE" 2>/dev/null \
    | sed -nE 's/.*argv\[\]=([^;]*);.*/\1/p' | head -1 | sed -E 's/ +$//'
}

service_exists() {
  [ -n "$(systemctl list-unit-files "$SERVICE" --no-legend 2>/dev/null)" ]
}

# A Python interpreter that can drive the panels. Prefers the one the service
# already uses, since that is the one Nick set up with the piomatter library.
find_panel_python() {
  local cand first
  first=$(service_cmd | awk '{print $1}')
  for cand in "$first" \
              "$REPO/venv/bin/python" "$REPO/rpi5/venv/bin/python" \
              "$HOME/venv/bin/python" "$HOME/.venv/bin/python" \
              /usr/bin/python3; do
    [ -n "$cand" ] && [ -x "$cand" ] || continue
    if "$cand" -c "import adafruit_blinka_raspberry_pi5_piomatter" 2>/dev/null; then
      echo "$cand"; return 0
    fi
  done
  return 1
}
