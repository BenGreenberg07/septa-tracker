# Command cheat sheet

Everything you need, in both forms: typed **on the Pi**, or run **from your Mac**
over SSH.

---

## Which machine am I on?

This catches everyone. A terminal window looks identical whether it is your Mac
or an SSH session into the Pi.

```bash
hostname
```

- `fetcar` means you are on **the Pi**.
- `Bens-MacBook-Air` means you are on **your Mac**.

The prompt tells you too: the Pi shows `fetcar@fetcar:~ $`, your Mac ends in `%`.
Type `exit` to leave an SSH session. If it still says `fetcar` afterwards you had
two sessions stacked up, so type `exit` again, or just open a fresh Terminal
window, which is always your Mac.

---

## Connecting from your Mac

```bash
ssh septa
```

`septa` is a shortcut defined in `~/.ssh/config` on your Mac, pointing at
`fetcar@100.96.20.121`. That Tailscale address never changes, whatever network
the Pi is on. Tailscale must be running on both machines.

Every command below marked "from your Mac" assumes that shortcut.

---

## The display

| What you want | On the Pi | From your Mac |
|---|---|---|
| Turn the screen on | `sudo systemctl start septa-display.service` | `ssh septa 'sudo systemctl start septa-display.service'` |
| Turn the screen off (Pi stays up) | `~/septa-tracker/pi/stop-panel.sh` | `ssh septa '~/septa-tracker/pi/stop-panel.sh'` |
| Restart it | `sudo systemctl restart septa-display.service` | `ssh septa 'sudo systemctl restart septa-display.service'` |
| Off, and stay off after reboot | `~/septa-tracker/pi/stop-panel.sh --disable` | `ssh septa '~/septa-tracker/pi/stop-panel.sh --disable'` |
| Which program runs at boot | `~/septa-tracker/pi/set-panel-script.sh --show` | `ssh septa '~/septa-tracker/pi/set-panel-script.sh --show'` |
| Set what runs at boot | `~/septa-tracker/pi/set-panel-script.sh rpi5/prod/swarthmore-tracked.py` | `ssh septa '~/septa-tracker/pi/set-panel-script.sh rpi5/prod/swarthmore-tracked.py'` |
| Undo that, back to the original | `~/septa-tracker/pi/set-panel-script.sh --revert` | `ssh septa '~/septa-tracker/pi/set-panel-script.sh --revert'` |

Turning it off with `stop-panel.sh` leaves the Pi running, so you keep SSH. It
comes back on by itself at the next reboot unless you used `--disable`.

---

## Getting new code onto the display

After Claude pushes a change, or after you push one:

**On the Pi**
```bash
cd ~/septa-tracker
./pi/update.sh
```

**From your Mac**
```bash
ssh septa 'cd ~/septa-tracker && ./pi/update.sh'
```

`update.sh` pulls from GitHub, backs up anything edited directly on the Pi, and
restarts the display. To watch a new version before making it permanent:

```bash
cd ~/septa-tracker && ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
```

Ctrl-C when done and the service takes over again. From your Mac, add `-t` so
Ctrl-C reaches it:

```bash
ssh -t septa 'cd ~/septa-tracker && ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py'
```

**Sending your own changes from the Mac**, from the repo folder:

```bash
git add -A && git commit -m "what you changed" && git push origin main
ssh septa 'cd ~/septa-tracker && ./pi/update.sh'
```

---

## Checking on it

| What you want | On the Pi | From your Mac |
|---|---|---|
| Full health check | `~/septa-tracker/pi/doctor.sh` | `ssh septa '~/septa-tracker/pi/doctor.sh'` |
| Live temperature and voltage | `~/septa-tracker/pi/temp.sh` | `ssh -t septa '~/septa-tracker/pi/temp.sh'` |
| One temperature reading | `~/septa-tracker/pi/temp.sh --once` | `ssh septa '~/septa-tracker/pi/temp.sh --once'` |
| Log temperature to a file | `~/septa-tracker/pi/temp.sh --log` | `ssh -t septa '~/septa-tracker/pi/temp.sh --log'` |
| Why is there no train dot | `~/septa-tracker/pi/py.sh rpi5/tools/api-check.py` | `ssh septa '~/septa-tracker/pi/py.sh rpi5/tools/api-check.py'` |
| Display program's log | `journalctl -u septa-display.service -n 50` | `ssh septa 'journalctl -u septa-display.service -n 50'` |
| Follow the log live | `journalctl -u septa-display.service -f` | `ssh -t septa 'journalctl -u septa-display.service -f'` |

`doctor.sh` and `api-check.py` change nothing and are safe while the display is
running. Use `-t` for anything you need to Ctrl-C out of.

---

## Testing the panels

These take over the screen, so run them through `try-script.sh`, which stops the
service first and restores it when you press Ctrl-C.

```bash
cd ~/septa-tracker
./pi/try-script.sh rpi5/tools/panel-test.py                 # cycle every pattern
./pi/try-script.sh rpi5/tools/panel-test.py --hold white    # find dead pixels
./pi/try-script.sh rpi5/tools/panel-test.py --hold black    # find stuck-on pixels
./pi/try-script.sh rpi5/tools/panel-test.py --hold red      # one colour at a time
./pi/try-script.sh rpi5/tools/panel-test.py --hold panels   # numbered panels 1-16
./pi/try-script.sh rpi5/tools/panel-test.py --list          # all pattern names
```

From your Mac, prefix with `ssh -t septa 'cd ~/septa-tracker && ` and close the
quote.

What each one tells you:

- **white**: any dark pixel is dead; a pink, green or blue pixel has one dead colour.
- **black**: anything still lit is stuck on.
- **red / green / blue**: a whole panel dark on one colour is a cable or driver
  fault, not dead LEDs. See HARDWARE.md.
- **panels**: numbers 1 to 16 so you can say which panel has the fault. Numbers
  out of order or mirrored means the pixel map is wrong, not the panels.
- **rows / cols**: a whole missing line is a ribbon cable or shift register.

Flicker experiments, trading colour depth against refresh rate:

```bash
SEPTA_PLANES=3 ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
SEPTA_TEMPORAL_PLANES=0 ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
```

Defaults are 4 and 2.

---

## Power off and on

**Never just pull the plug on a running Pi.** That is how SD cards get corrupted.
Shut it down first, wait about 10 seconds for the green activity LED to stop
blinking, then switch off at the PSU cable.

**On the Pi**
```bash
sudo shutdown -h now
```

**From your Mac**
```bash
ssh septa 'sudo shutdown -h now'
```

To turn it back on, flip the switch on the PSU cable. Everything restarts by
itself: the Pi boots, Tailscale reconnects at the same address, and the display
starts. Allow 30 to 60 seconds, since the display waits for the network before
its first fetch.

After a shutdown you cannot SSH in. The Pi is off, and only the physical switch
brings it back.

Reboot without powering off:

```bash
sudo reboot
```

---

## On your Mac only

```bash
cd ~/Documents/septa-tracker
./run-sim.sh
```

Renders the board in your browser at http://127.0.0.1:8800 with no hardware, for
working on the display away from the lab. Ctrl-C stops it.

Regenerate the picture of all board states:

```bash
./venv/bin/python rpi5/tools/make-scenarios.py
```

Note the Mac's virtual environment is `venv/`, while the Pi's is `rpi5/venv/`.
On the Pi use `./pi/py.sh <file>`, which finds the right one for you.

---

## If something looks wrong

| Symptom | First thing to run |
|---|---|
| Two pictures mixed together | `./pi/stop-panel.sh`, then start one thing |
| Screen blank, Pi reachable | `journalctl -u septa-display.service -n 50` |
| Cannot SSH | Is Tailscale running on both? Is the Pi powered on? |
| No train dot on the timeline | `./pi/py.sh rpi5/tools/api-check.py` |
| Board looks scrambled | `./pi/try-script.sh rpi5/prod/swarthmore-bidirectional.py` to compare |
| Anything else | `./pi/doctor.sh` |
