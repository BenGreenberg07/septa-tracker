#!/usr/bin/env bash
# Double-click to start the Swarthmore board. Detaches, so this window can close.
cd "$(dirname "$0")" || exit 1

PIDFILE="/tmp/septa-panel.pid"
URL="http://127.0.0.1:8800"

echo "Starting the Swarthmore board..."

# Clear any previous instance, so port 8800 is free.
pkill -f swarthmore-tracked >/dev/null 2>&1 && echo "  stopped a panel that was already running"
sleep 1

if [ ! -d venv ]; then
  echo "  first run: creating venv"
  python3 -m venv venv || { echo "FAILED: could not create venv"; sleep 8; exit 1; }
fi
./venv/bin/pip -q install requests pillow numpy >/dev/null 2>&1

nohup ./venv/bin/python rpi5/prod/swarthmore-tracked.py \
      > /tmp/septa-panel.log 2>&1 &
echo $! > "$PIDFILE"

# The first frame waits on the network and both SEPTA feeds, so give it a moment.
echo -n "  waiting for the first frame"
for _ in $(seq 1 30); do
  if curl -s -o /dev/null --max-time 2 "$URL"; then
    echo ""
    echo "Panel is up:  $URL"
    open "$URL"
    echo ""
    echo "Leave it running. Use 'Stop Panel.command' to stop it."
    sleep 3
    exit 0
  fi
  echo -n "."
  sleep 1
done

echo ""
echo "FAILED: the panel did not come up. Last lines of the log:"
tail -20 /tmp/septa-panel.log
echo ""
echo "Press any key to close."
read -r -n 1
