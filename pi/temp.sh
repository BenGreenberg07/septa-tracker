#!/usr/bin/env bash
# Live temperature and power monitor. Ctrl-C to stop; it prints a summary.
#
#   ./pi/temp.sh            one line every 2 seconds
#   ./pi/temp.sh 10         one line every 10 seconds
#   ./pi/temp.sh --log      also save every reading to ~/septa-temp-log.csv
#   ./pi/temp.sh --once     print a single reading and exit
#
# Run it in a second terminal while the display is on, so you can see how hot
# each version of the code makes the Pi.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$REPO/pi/lib.sh"

every=2; log=""; once=0
for a in "$@"; do
  case "$a" in
    --log)  log="$HOME/septa-temp-log.csv" ;;
    --once) once=1 ;;
    ''|*[!0-9]*) ;;
    *)      every="$a" ;;
  esac
done

if [ -n "$log" ] && [ ! -f "$log" ]; then
  echo "time,temp_c,input_volts,cpu_mhz,fan_pct,throttled,panel_program" > "$log"
fi

n=0; sum=0; lo=""; hi=""; worst=0; start=$(date +%s)

summary() {
  echo
  if [ "$n" -gt 0 ]; then
    mins=$(( ($(date +%s) - start) / 60 ))
    avg=$(awk -v s="$sum" -v n="$n" 'BEGIN{printf "%.1f", s/n}')
    echo "${BOLD}Over ${mins} min:${OFF} low ${lo} C, average ${avg} C, high ${hi} C ($(temp_word "$hi"))"
    if (( worst & 0xF000F )); then
      echo "${RED}Power or heat trouble occurred during this run:${OFF}"
      decode_throttled "$worst" | sed 's/^/  - /'
    else
      echo "${GRN}No throttling or under-voltage during this run.${OFF}"
    fi
  fi
  [ -n "$log" ] && echo "Readings saved to $log"
  exit 0
}
trap summary INT TERM

[ "$once" -eq 0 ] && echo "${DIM}Reading every ${every}s. Ctrl-C to stop.${OFF}"

while true; do
  t=$(read_temp); v=$(read_input_volts); m=$(read_arm_mhz); f=$(read_fan); th=$(read_throttled)
  prog=$(panel_procs | head -1 | grep -o -E '[^/ ]+\.py' | head -1)

  now_flags="none"
  if [ -n "$th" ] && (( th & 0xF )); then
    now_flags="${RED}$(decode_throttled "$th" | grep NOW | cut -d: -f1 | paste -sd, -)${OFF}"
  fi

  printf '%s  %s%5s C %-10s%s  %s V  %4s MHz  fan %3s  now: %s  %s\n' \
    "$(date +%H:%M:%S)" "$(temp_color "$t")" "${t:-?}" "$(temp_word "$t")" "$OFF" \
    "${v:- ?  }" "${m:-?}" "${f:+$f%}" "$now_flags" "${DIM}${prog:-no program}${OFF}"

  if [ -n "$t" ]; then
    n=$((n + 1)); sum=$(awk -v a="$sum" -v b="$t" 'BEGIN{print a+b}')
    [ -z "$lo" ] || awk -v a="$t" -v b="$lo" 'BEGIN{exit !(a<b)}' && lo="$t"
    [ -z "$hi" ] || awk -v a="$t" -v b="$hi" 'BEGIN{exit !(a>b)}' && hi="$t"
  fi
  [ -n "$th" ] && worst=$(( worst | th ))

  [ -n "$log" ] && echo "$(date -Iseconds),$t,$v,$m,$f,$th,${prog}" >> "$log"
  [ "$once" -eq 1 ] && exit 0
  sleep "$every"
done
