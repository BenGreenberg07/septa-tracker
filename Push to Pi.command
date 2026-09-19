#!/usr/bin/env bash
# Double-click to send your code to the display.
#   1. Saves (commits) your changes, asking you for a short description.
#   2. Uploads them to GitHub (your fork, BenGreenberg07/septa-tracker).
#   3. If the Pi is reachable, tells it to pull them and restart the display.
cd "$(dirname "$0")" || exit 1
PI="${SEPTA_PI:-fetcar@septa-pi}"
HOST="${PI#*@}"
pause() { echo; read -r -n 1 -p "Press any key to close."; echo; }

if [ -n "$(git status --porcelain)" ]; then
  echo "Changed files:"; git status --short; echo
  read -r -p "Describe the change in a few words (blank to cancel): " msg
  [ -z "$msg" ] && { echo "Cancelled, nothing sent."; pause; exit 0; }
  git add -A && git commit --quiet -m "$msg" && echo "Saved."
fi

echo "Uploading to GitHub..."
git push --quiet origin main || { echo "Upload failed (see above)."; pause; exit 1; }
echo "Uploaded: $(git log -1 --format='%h %s')"
echo

if ! nc -z -G 5 "$HOST" 22 >/dev/null 2>&1; then
  echo "Couldn't reach the Pi at '$HOST'."
  echo "Your code IS on GitHub. To load it onto the display, on the Pi run:"
  echo "    cd ~/septa-tracker && ./pi/update.sh"
  echo
  echo "(To make this automatic: Tailscale on, and ./pi/setup-remote.sh done on the Pi.)"
  pause; exit 0
fi

if ! ssh -o BatchMode=yes -o ConnectTimeout=6 "$PI" true 2>/dev/null; then
  echo "The Pi is reachable, but it wants a password. Fix once with:"
  echo "    ssh-copy-id $PI"
  echo "Continuing with a password prompt..."
fi
ssh -t "$PI" 'cd ~/septa-tracker && ./pi/update.sh'
pause
