#!/usr/bin/env bash
# One-time setup so your laptop can reach this Pi from anywhere.
#
#   ./pi/setup-remote.sh
#
# Why this is needed: on campus wifi the Pi gets a different IP address each
# time it boots, and the network may block laptops from talking to other
# devices directly. Tailscale fixes both: the Pi always answers to the name
# "septa-pi", and it works from the lab, your dorm, or off campus.
#
# You need a free Tailscale account (sign in with Google or GitHub). Use the
# same account on your laptop.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$REPO/pi/lib.sh"
NAME="${1:-septa-pi}"

section "1. Turning on SSH (lets you log in remotely)"
sudo systemctl enable --now ssh && ok "SSH is on."

section "2. Installing Tailscale"
if have tailscale; then ok "Already installed."
else curl -fsSL https://tailscale.com/install.sh | sh || { bad "Install failed; is the Pi online?"; exit 1; }
fi

section "3. Connecting this Pi to your Tailscale account"
echo "  A link will appear below. Open it (on this Pi or your phone) and sign in."
sudo tailscale up --hostname="$NAME"

section "4. Done"
ip=$(tailscale ip -4 2>/dev/null | head -1)
ok "This Pi is now ${BOLD}$NAME${OFF} (also reachable as $ip)."
echo
echo "  On your laptop, with Tailscale installed and signed in to the same account:"
echo "    ssh $(whoami)@$NAME"
echo
echo "  To stop typing the password every time, run this once ON THE LAPTOP:"
echo "    ssh-copy-id $(whoami)@$NAME"
