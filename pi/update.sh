#!/usr/bin/env bash
# Pull the latest code from GitHub onto the Pi and restart the display.
#
#   ./pi/update.sh
#
# Safe to run any time, including the very first time, when the Pi still has
# Nick's copy of the code:
#   - Edits someone made directly on the Pi are never thrown away. They are
#     saved to a branch named pi-backup-<date> first.
#   - The Pi is pointed at your fork (BenGreenberg07). The original repo is
#     kept as "upstream".
#   - The display service is restarted so the new code is what runs.
#
# First time only, before the pi/ folder exists on the Pi, get it this way:
#   curl -fsSL https://raw.githubusercontent.com/BenGreenberg07/septa-tracker/main/pi/update.sh -o /tmp/update.sh
#   bash /tmp/update.sh

set -e
FORK="https://github.com/BenGreenberg07/septa-tracker"
UPSTREAM="https://github.com/Emadmasroor/septa-tracker"
SERVICE="${SEPTA_SERVICE:-septa-display.service}"

here="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"
if [ -d "$here/.git" ] && [ -d "$here/rpi5" ]; then REPO="$here"
else REPO="${SEPTA_REPO:-$HOME/septa-tracker}"; fi

B=$'\e[1m'; G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; O=$'\e[0m'
step() { echo; echo "${B}$*${O}"; }

if [ ! -d "$REPO/.git" ]; then
  if [ -e "$REPO" ]; then
    echo "${R}$REPO exists but is not a git checkout.${O} Not touching it."
    echo "Move it aside (mv $REPO ${REPO}-old) and run this again to get a fresh copy."
    exit 1
  fi
  step "No copy of the code yet, so downloading it to $REPO"
  git clone "$FORK" "$REPO"
fi
cd "$REPO"

step "1. Pointing the Pi at your fork"
current=$(git remote get-url origin 2>/dev/null || true)
if [ "$current" != "$FORK" ] && [ "$current" != "$FORK.git" ]; then
  if [ -n "$current" ] && ! git remote get-url upstream >/dev/null 2>&1; then
    git remote rename origin upstream
    echo "  Kept the old source as 'upstream': $current"
  else
    git remote remove origin 2>/dev/null || true
  fi
  git remote add origin "$FORK"
  echo "  Now pulling from $FORK"
else
  echo "  Already pulling from your fork."
fi
git remote get-url upstream >/dev/null 2>&1 || git remote add upstream "$UPSTREAM"
git fetch --quiet origin

stamp=$(date +%Y%m%d-%H%M%S)
step "2. Protecting anything edited directly on the Pi"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  git switch --quiet -c "pi-backup-$stamp"
  git -c user.name="septa-pi" -c user.email="septa-pi@localhost" \
      commit --quiet -a -m "Edits made directly on the Pi, saved by update.sh"
  echo "  ${Y}Found local edits.${O} Saved them on branch ${B}pi-backup-$stamp${O}:"
  git show --stat --format= HEAD | sed 's/^/    /'
  git switch --quiet - 2>/dev/null || true
else
  echo "  No local edits."
fi

# Get onto main, tracking the fork.
if [ "$(git branch --show-current)" != "main" ]; then
  if git show-ref --verify --quiet refs/heads/main; then git switch --quiet main
  else git switch --quiet -c main --track origin/main; fi
fi

# Commits made on the Pi but never pushed: keep them on a branch, then line up.
if ! git merge-base --is-ancestor HEAD origin/main; then
  git branch "pi-backup-commits-$stamp"
  echo "  ${Y}The Pi had commits that were never pushed.${O} Kept on ${B}pi-backup-commits-$stamp${O}."
  git reset --quiet --hard origin/main
fi

step "3. Updating the code"
before=$(git rev-parse HEAD)
git merge --quiet --ff-only origin/main
after=$(git rev-parse HEAD)
git branch --quiet --set-upstream-to=origin/main main 2>/dev/null || true
if [ "$before" = "$after" ]; then
  echo "  Already up to date: $(git log -1 --format='%h %s')"
else
  echo "  ${G}Updated.${O} New since last time:"
  git log --format='    %h  %s' "$before..$after"
fi
chmod +x pi/*.sh 2>/dev/null || true

step "4. Checking the Python libraries"
# shellcheck source=/dev/null
source "$REPO/pi/lib.sh"
if py=$(find_panel_python); then
  missing=$("$py" - <<'PY'
import importlib.util
print(" ".join(m for m in ("requests", "PIL", "numpy")
               if importlib.util.find_spec(m) is None))
PY
)
  if [ -n "$missing" ]; then
    pkgs=$(echo "$missing" | sed 's/PIL/pillow/')
    echo "  Installing: $pkgs"
    "$py" -m pip install --quiet $pkgs || sudo "$py" -m pip install --quiet $pkgs
  else
    echo "  All present ($py)."
  fi
else
  echo "  ${Y}Could not find the Python with the panel library.${O} Run ./pi/doctor.sh."
fi

step "5. Restarting the display"
if systemctl list-unit-files "$SERVICE" --no-legend 2>/dev/null | grep -q .; then
  if [ "$(systemctl is-enabled "$SERVICE" 2>/dev/null)" = "enabled" ] || \
     [ "$(systemctl is-active "$SERVICE" 2>/dev/null)" = "active" ]; then
    # Clear anything someone left running by hand, or the restart would put
    # two programs on the panels again.
    "$REPO/pi/stop-panel.sh" >/dev/null 2>&1 || true
    sudo systemctl restart "$SERVICE"
    sleep 4
    running=$(basename "$(service_cmd | awk '{print $NF}')" 2>/dev/null)
    echo "  Service is $(systemctl is-active "$SERVICE"), running: ${running:-unknown}"
    echo "  To change which program that is: ./pi/set-panel-script.sh <file>"
  else
    echo "  The service is switched off, so not starting it."
    echo "  Turn it on with: ./pi/set-panel-script.sh rpi5/prod/swarthmore-tracked.py"
  fi
else
  echo "  No display service yet. Set one up with:"
  echo "    ./pi/set-panel-script.sh rpi5/prod/swarthmore-tracked.py"
fi

echo; echo "${G}${B}Done.${O}"
