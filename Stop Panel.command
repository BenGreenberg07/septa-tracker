#!/usr/bin/env bash
# Double-click to stop the Swarthmore board.
PIDFILE="/tmp/septa-panel.pid"

stopped=0

if [ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null; then
  stopped=1
fi
rm -f "$PIDFILE"

# Catch anything started another way (run-sim.sh, a terminal, an older launcher).
if pkill -f swarthmore-tracked 2>/dev/null; then
  stopped=1
fi

# Belt and braces: free the port even if the process name has changed.
if lsof -ti:8800 2>/dev/null | xargs kill 2>/dev/null; then
  stopped=1
fi

if [ "$stopped" -eq 1 ]; then
  echo "Panel stopped."
else
  echo "No panel was running."
fi

sleep 2
