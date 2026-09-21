# Hardware notes: known faults, what to buy, and why

Findings from the lab session on 2026-09-21, with the evidence behind each one.
Raw temperature and voltage readings are in `~/septa-temp-log.csv` on the Pi.

---

## 1. The Pi is starved of power (confirmed, fix this first)

**What was measured.** During a full-white screen test, the Pi's input voltage
fell from 4.99 V to 4.64 V, the firmware raised UNDER-VOLTAGE and THROTTLED,
and the CPU dropped from 1500 MHz to 1000 MHz. The under-voltage threshold is
4.63 V, so it is right at the edge.

**Why white matters.** White lights the red, green and blue LEDs at once, so it
draws roughly three times the current of a single colour. The flicker tracked
brightness exactly: bad on white, absent on blue and green alone. That pattern
is a power problem, not a software one.

**Why it happens.** The panel supply is a 5 V / 100 A unit, far more than
sixteen panels need, so the supply is not the limit. The Pi's power was
soldered to the bonnet's power connection, which means it is fed *through* the
same wiring the panels draw through. Current through that wiring causes a
voltage drop, and the Pi sits at the end of it.

**Why it matters.** Throttling is the minor part. A Pi browning out repeatedly
is how SD cards get corrupted. Do not leave the display running unattended
until this is resolved.

**The fix, in order of preference:**

1. **Rewire, free.** Run a dedicated pair of wires from the PSU's output
   terminals straight to the Pi, short and thick (16 AWG ideal, 18 AWG
   minimum), instead of tapping off the bonnet. Then nudge the PSU's trim
   potentiometer up so the Pi sees about 5.1 V under a white screen. This keeps
   a single wall plug and adds nothing to the case.
2. **Separate supply, about $12.** An official Pi 5 27 W USB-C supply. Simple
   and certain, but it is a second AC adapter to fit and cool inside a
   weatherproof case, and the original team deliberately avoided needing two
   outlets at the station. A small power strip behind the display keeps it to
   one wall plug.

**Measure before buying.** With a white screen up, measure DC volts at the PSU
output terminals and at the Pi's power input:

- PSU near 5.0 V but the Pi at 4.6 V: the loss is in the wiring, so rewire.
- PSU itself sagging: turn the trim pot up.

The PSU's input side carries mains voltage. Stay on the DC side, and do this
with Ed Jaoudi or Prof. Masroor present.

---

## 2. The Pi runs hot (confirmed)

Over a 44 minute run: low 51.6 C, average 59.5 C, **high 71.9 C**, with no fan
fitted. The Pi 5 begins throttling around 80 C.

It is not critical on an open bench in September. It will get worse in a sealed
outdoor case, in summer, mounted in sun. This is separate from the power
problem and rewiring will not help it.

---

## 3. Panel 14 has no red at all (needs one more test)

The **entire panel** is dark on the red test pattern, while green and blue are
fine. That rules out a dead LED, which would affect single pixels. A HUB75
ribbon carries R1, G1, B1 for a panel's top half and R2, G2, B2 for the bottom
half, so a single loose pin kills one colour across half a panel. Losing red
across the whole panel means both red lines are out.

**The test that decides it:** look at the panels *after* number 14 in the
chain while red is showing.

- **Panels after 14 show red correctly** → red data passes through panel 14 but
  is not displayed by it. The fault is panel 14's own driver, so the panel
  needs replacing.
- **Panels after 14 also lost red** → the break is upstream: the ribbon into
  panel 14, or the previous panel's output. Reseat and swap cables.

Either way, reseating the ribbon at both ends costs nothing and is worth trying
first. **Power everything off before unplugging ribbons.** If a swapped cable
makes the fault move to a different panel, the cable is the culprit.

---

## 4. Scattered dead pixels (cosmetic, no action)

A few isolated dead pixels across the array. Normal for inexpensive panels and
invisible in ordinary use. Recorded so the next maintainer does not re-diagnose
them.

---

## What to buy

| Item | Approx | Why |
|---|---|---|
| Raspberry Pi 5 **Active Cooler** | $5 | Measured 71.9 C with no fan; throttling starts at 80 C, and a sealed case in summer will be hotter. Clips straight on, no wiring. Buy regardless of anything else. |
| **16 AWG wire** and ferrules | $5 | For the dedicated PSU-to-Pi feed in fix 1. Cheapest possible fix for the under-voltage. |
| Official **Pi 5 27 W USB-C supply** | $12 | Only if the rewire does not clear the under-voltage. Certain to work, at the cost of a second adapter in the case. |
| **Spare 64x32 HUB75 panel** | ~$20 | For panel 14 if the test points at the panel, and as a shelf spare. Must match: 64x32, HUB75, 1/16 scan, 256 x 128 mm. The original sixteen came from Walmart; the same model may not exist in two years, so a spare is cheap insurance. |
| **Spare HUB75 ribbon cables** | ~$8 | Common failure point, needed for the swap test above, and useful to have. |

A multimeter is needed for the voltage measurement, but the engineering lab has
these already.

---

## Still to verify

- Two-point voltage measurement under white load (section 1).
- Whether panels after 14 keep red (section 3).
- Temperature again after the Active Cooler is fitted, ideally inside the case.
- Visibility in rain, fog and snow. The original team only tested indoors, and
  the report flags this as unverified.
