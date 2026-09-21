# Lab guide: getting the SEPTA display running

Follow this top to bottom on your first lab visit. It takes about an hour. Every
command is typed **on the Pi** unless it says **on your Mac**.

> The Pi's password is in the onboarding PDF. Never put it in this repo: the
> repo is public.

---

## Before you go (at home, 10 min)

1. **Make a Tailscale account** at [tailscale.com](https://tailscale.com) (free;
   sign in with GitHub or Google). It's what lets your Mac reach the Pi.
2. **Install Tailscale on your Mac** and sign in with that account.
3. **Bring** your phone (its hotspot is the backup internet if campus wifi fails
   on the Pi), a USB keyboard and mouse if the lab doesn't have one, and the
   onboarding PDF.

---

## In the lab

### Step 1. Power on and log in (2 min)

Turn on the switch on the power supply's cable. The Pi runs off the same supply,
so it boots too. Log in as `fetcar` and open **Terminal**.

The panels may light up with the old graduation slideshow. That's expected;
it starts automatically at boot. Step 5 stops it.

### Step 2. Check the Pi has internet (1 min)

```bash
curl -sI https://github.com | head -1
```

You want something like `HTTP/2 200`. If nothing comes back, the Pi's wifi
login (Nick's personal eduroam account) has probably stopped working. For today,
connect the Pi to your phone's hotspot from the wifi icon at the top right.
The long-term fix is registering it on Swat Device with ITS; Step 4 prints the
MAC address they'll ask for.

### Step 3. Get your code onto the Pi (first time only, 2 min)

```bash
curl -fsSL https://raw.githubusercontent.com/BenGreenberg07/septa-tracker/main/pi/update.sh -o /tmp/update.sh
bash /tmp/update.sh
```

**What it does:** points the Pi's code folder (`~/septa-tracker`) at your
fork instead of the original repo. It saves any edits Nick left on the Pi to a
backup branch first, so nothing is lost. Then it downloads your code and
restarts the display service. The service keeps running whatever it ran
before; that gets changed in Step 10.

After this first time, updating is just `./pi/update.sh`.

### Step 4. Health check (2 min)

```bash
cd ~/septa-tracker
./pi/doctor.sh
```

**Take a photo of the output.** It changes nothing; it only reports. It has four
sections:

1. **What is driving the panels.** If it says **2 programs**, that's the
   garbled picture the professor saw: the slideshow and the train board both
   writing to the panels at once. It also checks for anything *else* set to
   start a display program at boot.
2. **Temperature and power.** CPU temperature, the voltage reaching the Pi,
   and the throttle status explained in plain English. Watch for
   **under-voltage**. The Pi is powered through wires soldered to the bonnet,
   and the report mentions voltage drops. Low voltage causes throttling and
   extra heat.
3. **Network.** IP address, which wifi it's on, whether the SEPTA API is
   reachable, and the **wifi MAC address** for ITS.
4. **Code.** Which version is on the Pi and whether it's pulling from your fork.

### Step 5. Stop everything (1 min)

```bash
./pi/stop-panel.sh
```

Stops the service and anything started by hand. The panels freeze or go dark.
Now nothing is fighting over them.

### Step 6. Start the temperature log (leave it running)

Open a **second Terminal window** and run:

```bash
cd ~/septa-tracker && ./pi/temp.sh --log
```

It prints a line every 2 seconds and saves every reading to
`~/septa-temp-log.csv`. Leave it running for the rest of the visit. Note the
temperature **now**, with nothing running: that's your baseline. When you
Ctrl-C it, it prints the low, average, and high, and says whether any
throttling happened.

| Label | Temperature | Meaning |
|---|---|---|
| COOL | under 60 C | fine |
| WARM | 60 to 70 C | normal under load |
| HOT | 70 to 80 C | needs a fan |
| THROTTLING | 80 C and up | the Pi is slowing itself down to survive |

### Step 7. Baseline: Nick's original board (5 min)

Back in the first window:

```bash
./pi/try-script.sh rpi5/prod/swarthmore-bidirectional.py
```

`try-script.sh` stops the service first, so your test can never fight it. Look
at three things:

- **Is the picture clean?** It should be, since only one program is running.
- **Flicker, judged by eye.** Phone cameras make LED flicker look far worse
  than it is.
- **Temperature** in the second window after about 5 minutes.

Press **Ctrl-C** to stop. The service goes back to how it was.

### Step 8. The new board (5 min)

```bash
./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
```

**This is its first run on real panels.** Check:

- **Colors.** Yellow headings and a green "ON TIME". If red and blue look
  swapped, the color-order handling is wrong.
- **Orientation.** Text right side up, with nothing scrambled into blocks.
- **The strip.** First stop on the left, Swarthmore in the middle, last stop on
  the right, with the train dot moving along it.

If anything looks wrong: Ctrl-C, take a photo, and send it to Claude.

### Step 9. Flicker experiments (optional, 10 min)

The panels trade color depth against refresh speed. Try each one, and note how
it looks and what the temperature does:

```bash
SEPTA_PLANES=3 ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
SEPTA_TEMPORAL_PLANES=0 ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
SEPTA_PLANES=3 SEPTA_TEMPORAL_PLANES=0 ./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
```

The defaults are `4` and `2`, which is what Nick used. These settings haven't
been tested on this hardware. If a value is rejected, the script stops with an
error; just try the next one.

### Step 10. Make the new board the one that starts at boot (1 min)

```bash
./pi/set-panel-script.sh rpi5/prod/swarthmore-tracked.py
```

It should end with **"Running, and it is the only program on the panels."**
This doesn't rewrite Nick's service; it adds a small override on top. To undo:
`./pi/set-panel-script.sh --revert`.

### Step 11. Reboot test (3 min)

This proves the garbled picture is fixed for good, not just for now.

```bash
sudo reboot
```

When it's back, log in and run:

```bash
cd ~/septa-tracker && ./pi/doctor.sh
```

Section 1 must say **exactly one program**.

### Step 12. Remote access (10 min)

```bash
./pi/setup-remote.sh
```

It turns on SSH and installs Tailscale. A link appears: open it (on the Pi or
your phone) and sign in with **the same Tailscale account as your Mac**.
Afterwards the Pi is always `septa-pi`, whatever IP address it got that day.

Then **on your Mac**:

```bash
ssh fetcar@septa-pi
```

If that logs you in, run this once **on your Mac** so you never have to type
the password again:

```bash
ssh-copy-id fetcar@septa-pi
```

If `ssh` doesn't connect, that's OK. The campus network may block it. Your
code still reaches the Pi through GitHub; see "Everyday" below.

### Step 13. Before you leave: on or off?

Press Ctrl-C in the temperature window to get the summary, then decide:

- **High under 70 C and no throttling:** fine to leave it running.
- **High of 70 to 80 C:** unplug it until it has a fan. Order the **Raspberry Pi
  5 Active Cooler** (about $5); it clips straight on.
- **Any under-voltage:** unplug it. The power wiring to the Pi needs fixing
  before it runs unattended.

Tell the professor what you found; the numbers are in `~/septa-temp-log.csv`.

---

## Getting my latest changes onto the display

Whenever Claude fixes something and pushes it, this is the whole routine. Run
it on the Pi:

```bash
cd ~/septa-tracker
./pi/update.sh
./pi/try-script.sh rpi5/prod/swarthmore-tracked.py
```

- `update.sh` pulls the new code and restarts the display service. It backs up
  anything edited directly on the Pi first, so nothing is lost.
- `try-script.sh` runs it in the foreground so you can watch it. Ctrl-C when
  you are happy, and the service takes over again.

If you are happy and want it to be what starts at boot:

```bash
./pi/set-panel-script.sh rpi5/prod/swarthmore-tracked.py
```

That is all. You do not need the long `curl` command again; that was only for
the very first time, before the Pi had `pi/update.sh`.

**If `update.sh` fails**, pull directly and try again:

```bash
cd ~/septa-tracker && git pull origin main
```

**If it complains about local changes**, park them and pull:

```bash
git stash && git pull origin main
```

### Changing code on your Mac

Edit, test locally with `./run-sim.sh` (the board renders at
http://127.0.0.1:8800, no hardware needed), then:

```bash
git add -A && git commit -m "what you changed" && git push origin main
```

Then run the three lines at the top of this section on the Pi.

## Script reference

**On the Pi** (in `~/septa-tracker/pi/`):

| Script | What it does | Changes anything? |
|---|---|---|
| `doctor.sh` | Health check: programs, heat, power, network, code | No |
| `temp.sh` | Live temperature; `--log` saves to CSV, `--once` reads once | No |
| `stop-panel.sh` | Stops everything on the panels; `--disable` also stops it at boot | Yes |
| `try-script.sh <file>` | Runs one program by hand, safely; Ctrl-C restores | Temporarily |
| `set-panel-script.sh <file>` | Chooses what runs at boot; `--show`, `--revert` | Yes |
| `update.sh` | Pulls your latest code from GitHub and restarts | Yes |
| `setup-remote.sh` | One-time SSH and Tailscale setup | Yes |
| `../rpi5/tools/panel-test.py` | Dead pixel and wiring test patterns (run via `try-script.sh`) | No |
| `../rpi5/tools/api-check.py` | Explains what the board is showing and why | No |

**On your Mac**:

| Command | What it does |
|---|---|
| `./run-sim.sh` | Renders the board in your browser, no Pi needed |
| `git push origin main` | Sends your changes to GitHub for the Pi to pull |
| `ssh fetcar@septa-pi ~/septa-tracker/pi/temp.sh` | Live temperature, remotely |
| `ssh fetcar@septa-pi ~/septa-tracker/pi/doctor.sh` | Health check, remotely |

---

## If something goes wrong

| What you see | What to do |
|---|---|
| Garbled mix of two pictures | `./pi/stop-panel.sh`, then run one thing. `doctor.sh` shows what else starts at boot. |
| "Could not find a Python that has the panel library" | Run `systemctl cat septa-display.service` and send the output to Claude. |
| Red and blue swapped | The color-order handling is wrong for these panels. Photo to Claude. |
| Picture scrambled into blocks | Pixel map problem. Run Nick's original (Step 7) to compare. |
| Want Nick's setup back | `./pi/set-panel-script.sh --revert`. His Pi-only edits are on a `pi-backup-*` branch. |
| Pi very hot | `./pi/stop-panel.sh`, unplug, and get the Active Cooler. |
