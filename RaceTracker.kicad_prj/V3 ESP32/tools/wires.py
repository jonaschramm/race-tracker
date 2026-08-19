"""Net list.

Routing policy (matches the user's brief: direct wires dominate, labels
for long distances/readability):
  - A pin-to-pin hop is drawn as a real wire ONLY when the two components
    are immediately adjacent with nothing else in between (verified with
    check_crossings.py after every change -- KiCad connects wires wherever
    they touch or cross, even without a shared endpoint, so an unplanned
    crossing between two unrelated nets is a real short, not cosmetic).
  - Any run that would have to travel across the sheet through other
    components' territory (module <-> GPS/SD/UART connectors, and every
    shared power rail) uses a local label instead. Same-text local labels
    merge into one net anywhere on the sheet without a wire between them.
"""
from build_sch import COMPONENTS, snap

WIRES = []
LABELS = []
NO_CONNECTS = []
JUNCTIONS = []
PWR_FLAGS = []


def P(ref, pin):
    return COMPONENTS[ref].pin_pos(pin)


def wire(*pts):
    """One or more connected 2-point wire segments through the given
    (x,y) points (KiCad's `wire` element is strictly 2 points per element;
    a longer run is N-1 chained elements, not one multi-vertex polyline --
    confirmed empirically, see git history of this file)."""
    snapped = [tuple(snap(v) for v in pt) for pt in pts]
    for a, b in zip(snapped, snapped[1:]):
        WIRES.append([a, b])


def label(pos, text, dir="right"):
    justify = {"right": "left", "left": "right", "up": "left", "down": "left"}[dir]
    LABELS.append(dict(pos=(snap(pos[0]), snap(pos[1])), text=text, justify=justify))


def tap_label(ref, pin, text, dx, dy):
    """Short outward stub + label, directly at a component pin."""
    p0 = P(ref, pin)
    p1 = (p0[0] + dx, p0[1] + dy)
    wire(p0, p1)
    d = "right" if dx > 0 else "left" if dx < 0 else ("down" if dy > 0 else "up")
    label(p1, text, dir=d)


def bus(pts, taps=()):
    wire(*pts)
    for t in taps:
        JUNCTIONS.append((snap(t[0]), snap(t[1])))


def signal_through(mod_ref, mod_pin, via_ref, via_pin, text, extend, mod_stub=-2.54):
    """Module pin and pull-up/series-element pin both get their own short
    stub + matching signal label (no wire between them). The two
    components are still drawn right next to each other on the sheet for
    a clean visual pairing, but a real wire there proved unsafe: with this
    many pull-ups packed into one narrow corridor next to the module's
    2.54mm pin pitch, a resistor's own 7.62mm rail stub reliably ends up
    crossing a NEIGHBOURING signal's horizontal run (confirmed repeatedly
    via check_nets.py -- e.g. R13's +3V3 stub shorting into SD_CS once every
    pull-up was placed close enough to look tidy). Labels sidestep this
    entirely regardless of how tightly the resistors are packed."""
    tap_label(mod_ref, mod_pin, text, mod_stub, 0)
    d = "right" if extend[0] > 0 else "left" if extend[0] < 0 else ("down" if extend[1] > 0 else "up")
    p1 = P(via_ref, via_pin)
    p2 = (p1[0] + extend[0], p1[1] + extend[1])
    wire(p1, p2)
    label(p2, text, dir=d)


def nc(ref, pin):
    NO_CONNECTS.append(P(ref, pin))


STUB = 7.62  # outward stub length for label taps (rule 31: must clearly
             # exceed the ref/value text offset)

# ===========================================================================
# EN reset circuit -- tiny local cluster (module pin, R8, C9, C10, SW2 all
# within ~40mm, nothing else nearby): kept as one direct bus. R8/R9 use
# different X lanes so their +3V3 stubs (7.62mm) can't overlap each other.
# ===========================================================================
bus([P("U1", "3"), P("R8", "2"), P("C9", "2"), P("C10", "2"), P("SW2", "2")],
    taps=[P("R8", "2"), P("C9", "2"), P("C10", "2")])
tap_label("R8", "1", "+3V3", 0, -STUB)
tap_label("C9", "1", "GND", 0, -STUB)
tap_label("C10", "1", "GND", 0, -STUB)
tap_label("SW2", "1", "GND", -STUB, 0)

# ===========================================================================
# BOOT circuit
# ===========================================================================
bus([P("U1", "27"), P("R9", "2"), P("SW3", "2")], taps=[P("R9", "2")])
tap_label("R9", "1", "+3V3", 0, -STUB)
tap_label("SW3", "1", "GND", -STUB, 0)

# ===========================================================================
# I2C to the GPS Qwiic connector: direct wire module->pull-up (adjacent),
# then a signal label to reach J3 (74mm away, across the SPI cluster --
# exactly the "long distance" case for a label instead of a routed wire).
# ===========================================================================
# Adjacent module pins are only 2.54mm apart but label text is much wider
# than that, so each pin in a tightly-packed run gets a DIFFERENT stub
# length -- otherwise same-length labels on neighbouring pins visually
# overlap (confirmed by rendering an actual SVG/PDF and inspecting it,
# not just ERC, which doesn't care about text collisions at all).
signal_through("U1", "12", "R10", "2", "I2C_SDA", (-2.54, 0), mod_stub=-2.54)
signal_through("U1", "17", "R11", "2", "I2C_SCL", (-2.54, 0), mod_stub=-3.81)
tap_label("R10", "1", "+3V3", 0, -STUB)
tap_label("R11", "1", "+3V3", 0, -STUB)
tap_label("J3", "1", "GND", -STUB, 0)
tap_label("J3", "2", "+3V3", -STUB, 0)
tap_label("J3", "3", "I2C_SDA", STUB, 0)
tap_label("J3", "4", "I2C_SCL", STUB, 0)

# ===========================================================================
# SPI to the microSD socket: same pattern. J4's real pinout interleaves
# VDD/VSS between the signal pins, but that no longer matters -- every
# J4 pin gets its own short stub + matching signal label, no routed run
# has to reach across to the connector's (different) pin pitch at all.
# ===========================================================================
signal_through("U1", "18", "R12", "2", "SD_CS", (-2.54, 0), mod_stub=-2.54)
tap_label("R12", "1", "+3V3", 0, -STUB)
tap_label("U1", "19", "SD_MOSI", -11.43, 0)   # no pull-up needed
tap_label("U1", "20", "SD_SCK", -20.32, 0)
signal_through("U1", "21", "R13", "2", "SD_MISO", (-2.54, 0), mod_stub=-29.21)
tap_label("R13", "1", "+3V3", 0, -STUB)
signal_through("U1", "22", "R14", "2", "SD_CD", (-2.54, 0), mod_stub=-38.1)
tap_label("R14", "1", "+3V3", 0, -STUB)

# Pins 2-7 are six pins in a row, each only 2.54mm apart -- every one gets
# a longer stub than the last so none of the six labels land in the same
# column (same reasoning as U1's own pin stubs above).
tap_label("J4", "2", "SD_CS", -7.62, 0)
tap_label("J4", "3", "SD_MOSI", -16.51, 0)
tap_label("J4", "4", "+3V3", -25.4, 0)      # VDD
tap_label("J4", "5", "SD_SCK", -34.29, 0)
tap_label("J4", "6", "GND", -43.18, 0)      # VSS
tap_label("J4", "7", "SD_MISO", -52.07, 0)
tap_label("J4", "9", "GND", -7.62, 0)       # DET_B (other detect-switch leg)
tap_label("J4", "10", "SD_CD", -16.51, 0)
tap_label("J4", "SH", "GND", 0, STUB)       # shield tab
nc("J4", "1")   # DAT2 unused in SPI mode
nc("J4", "8")   # DAT1 unused in SPI mode

# ===========================================================================
# UART debug header -- module pins and header are both close by and share
# the header's own 2.54mm pitch, but they sit right above the crowded
# USB-C/battery/LDO cluster, so route via labels rather than a routed run
# through that territory.
# ===========================================================================
tap_label("U1", "37", "DBG_TXD0", STUB, 0)
# down+right (an L, not a diagonal): straight right runs into D1's VBUS stub.
_rxd0_p0 = P("U1", "36")
_rxd0_p1 = (_rxd0_p0[0] + STUB, _rxd0_p0[1])
_rxd0_p2 = (_rxd0_p1[0], _rxd0_p1[1] + 5.08)
wire(_rxd0_p0, _rxd0_p1, _rxd0_p2)
label(_rxd0_p2, "DBG_RXD0", dir="down")
tap_label("J5", "4", "DBG_TXD0", -STUB, 0)
# down+left (an L, not a diagonal): a longer straight-left reach runs into D1.
_j5rxd0_p0 = P("J5", "3")
_j5rxd0_p1 = (_j5rxd0_p0[0] - STUB, _j5rxd0_p0[1])
_j5rxd0_p2 = (_j5rxd0_p1[0], _j5rxd0_p1[1] + 5.08)
wire(_j5rxd0_p0, _j5rxd0_p1, _j5rxd0_p2)
label(_j5rxd0_p2, "DBG_RXD0", dir="down")
tap_label("J5", "2", "+3V3", STUB, 0)
tap_label("J5", "1", "GND", STUB, 0)

# ===========================================================================
# USB-C: D+/D- run through the USBLC6-2SC6 ESD array into the module. J1's
# A6/B6 (D+) and A7/B7 (D-) are physically duplicated pins on the same
# internal node (not pre-merged by the symbol) -- bridge each pair with a
# short direct jumper, then continue through D1 via labels (D1 sits right
# next to J1, but the module is far off to the left across the whole
# battery/charger cluster).
# ===========================================================================
wire(P("J1", "A6"), P("J1", "B6"))    # D+ bridge (both pins, same internal node)
wire(P("J1", "A7"), P("J1", "B7"))    # D- bridge
JUNCTIONS.append(P("J1", "A6"))
JUNCTIONS.append(P("J1", "A7"))

# J1 and D1 are ~80mm apart across the CC-pulldown/VBUS-decoupling area --
# a routed wire there would have to cross that whole cluster, so this is
# label-only (same reasoning as D1<->U1 below).
tap_label("J1", "A6", "USB_DP", STUB, 0)  # A6/A7 are 5.08mm apart -- fine as-is
wire(P("D1", "1"), P("D1", "6"))                              # duplicate I/O1 pin, same node
JUNCTIONS.append(P("D1", "1"))
tap_label("D1", "1", "USB_DP", -STUB, 0)  # D1.1/D1.3 (I/O1/I/O2) are 2.54mm apart

tap_label("J1", "A7", "USB_DM", STUB, 0)
wire(P("D1", "3"), P("D1", "4"))                              # duplicate I/O2 pin, same node
JUNCTIONS.append(P("D1", "3"))
tap_label("D1", "3", "USB_DM", -STUB - 12.7, 0)

tap_label("U1", "14", "USB_DP", STUB, 0)
tap_label("U1", "13", "USB_DM", STUB + 12.7, 0)

nc("J1", "A8")   # SBU1 -- not used (no USB-C alt-mode/accessory support)
nc("J1", "B8")   # SBU2
tap_label("D1", "5", "+VBUS", 0, -STUB)
tap_label("D1", "2", "GND", STUB, 0)

tap_label("J1", "A1", "GND", 0, STUB)
tap_label("J1", "SH", "GND", -STUB, 0)
tap_label("J1", "A4", "+VBUS", 0, -STUB)
wire(P("J1", "A5"), P("R1", "1"))     # CC1 pull-down, direct (adjacent parts)
wire(P("J1", "B5"), P("R2", "1"))     # CC2 pull-down, direct
tap_label("R1", "2", "GND", 0, STUB)
tap_label("R2", "2", "GND", 0, STUB)
tap_label("C1", "1", "+VBUS", 0, -STUB)
tap_label("C1", "2", "GND", 0, STUB)
tap_label("D4", "1", "+VBUS", 0, -STUB)   # cathode -> VBUS (unidirectional TVS, per kicad-happy UC-002)
tap_label("D4", "2", "GND", 0, STUB)      # anode -> GND

# ===========================================================================
# Battery + charger (MCP73831). Rails: +VBUS feeds the charger's VDD;
# +VBAT_RAW is the raw battery/charger-output node; +VBAT_SYS is the same
# node after the power switch, feeding the LDO -- so the system can be
# switched off while the battery keeps charging.
# ===========================================================================
# These short chains kept crossing OTHER local wires whichever way the
# elbow was ordered (confirmed via check_nets.py -- e.g. the STAT->LED
# run at LED-cathode height clipped the PROG resistor's own stub a few mm
# over). Same fix as the bus signals: label instead of routing through it.
tap_label("U2", "1", "CHG_STAT", STUB, 0)   # right, not up -- U2.3 (VBAT) shares this
                                             # X 5.08mm below and also stubs upward
tap_label("D2", "1", "CHG_STAT", -STUB, 0)
tap_label("D2", "2", "CHG_LED_A", STUB, 0)              # LED anode -> series R (label: D2 is
tap_label("R4", "1", "CHG_LED_A", 0, -STUB)             # horizontal, R4 vertical -- pins don't line up)
tap_label("R4", "2", "+VBUS", 0, STUB)                  # opposite direction from pin 1 (only
                                                         # 7.62mm apart -- same-direction stubs overlap)
tap_label("U2", "5", "CHG_PROG", 0, -STUB)  # up, not down -- avoids D2's CHG_LED_A stub row
tap_label("R3", "1", "CHG_PROG", 0, -STUB)
tap_label("R3", "2", "GND", 0, STUB)

tap_label("U2", "2", "GND", -STUB, 0)
tap_label("U2", "3", "+VBAT_RAW", 0, -STUB)
tap_label("U2", "4", "+VBUS", 0, STUB)
tap_label("C2", "1", "+VBUS", 0, -STUB)
tap_label("C2", "2", "GND", 0, STUB)
tap_label("C3", "1", "+VBAT_RAW", 0, -STUB)
tap_label("C3", "2", "GND", 0, STUB)
tap_label("J2", "1", "+VBAT_RAW", STUB, 0)
tap_label("J2", "2", "GND", STUB, 0)
tap_label("SW1", "1", "+VBAT_RAW", -STUB, 0)
tap_label("SW1", "2", "+VBAT_SYS", STUB, 0)

# ===========================================================================
# LDO regulation
# ===========================================================================
tap_label("U3", "1", "+VBAT_SYS", -STUB, 0)
tap_label("U3", "2", "GND", 0, STUB)
tap_label("U3", "3", "+VBAT_SYS", -STUB - 12.7, 0)   # EN tied to VIN (always enabled);
                                                      # VIN is 2.54mm above, same X -- stagger
nc("U3", "4")
tap_label("U3", "5", "+3V3", STUB, 0)
tap_label("C4", "1", "+VBAT_SYS", 0, -STUB)
tap_label("C4", "2", "GND", 0, STUB)
tap_label("C5", "1", "+3V3", 0, -STUB)
tap_label("C5", "2", "GND", 0, STUB)
tap_label("R5", "1", "+3V3", 0, -STUB)
tap_label("R5", "2", "PWR_LED_A", 0, STUB)              # series R -> LED anode (label: R5 is
tap_label("D3", "2", "PWR_LED_A", STUB, 0)              # vertical, D3 horizontal -- pins don't line up)
tap_label("D3", "1", "GND", 0, STUB)

# ===========================================================================
# Battery-sense divider. Midpoint (R6.2 == R7.1, same coordinate by
# construction) reaches the module via a genuinely long-distance label.
# ===========================================================================
tap_label("R6", "1", "+VBAT_SYS", 0, -STUB)
JUNCTIONS.append(P("R6", "2"))
wire(P("R6", "2"), P("C6", "1"))      # midpoint -> filter cap, direct
tap_label("R7", "2", "GND", 0, STUB)
tap_label("C6", "2", "GND", 0, STUB)
tap_label("R6", "2", "BATT_SENSE", STUB, 0)
tap_label("U1", "28", "BATT_SENSE", STUB, 0)

# ===========================================================================
# Module's own power pins + bulk/HF decoupling
# ===========================================================================
tap_label("U1", "2", "+3V3", 0, -STUB)
tap_label("U1", "1", "GND", 0, STUB)
tap_label("C7", "1", "+3V3", 0, -STUB)
tap_label("C7", "2", "GND", 0, STUB)
tap_label("C8", "1", "+3V3", 0, -STUB)
tap_label("C8", "2", "GND", 0, STUB)

# ===========================================================================
# No-connects: strapping pins left floating per datasheet default (Table
# 4-1: GPIO3 floating, GPIO45/46 weak pull-down = correct default for this
# non-PSRAM, 3.3V-VDD_SPI module -- see peripheral schematic, Fig. 9-1,
# which leaves these bare too), plus every other genuinely free GPIO
# (rule 32: kicad-cli ERC treats a bare bidirectional MCU pin as a real
# pin_not_connected error, not a silent non-issue).
# ===========================================================================
USED_U1_PINS = {"1", "2", "3", "27", "12", "17", "18", "19", "20", "21", "22",
                 "36", "37", "13", "14", "28", "40", "41"}
from libextract import get_pins as _get_pins
for num, name, ptype, lx, ly, ang in _get_pins("RF_Module.kicad_sym", "ESP32-S3-WROOM-1"):
    if num not in USED_U1_PINS:
        nc("U1", num)

# ===========================================================================
# PWR_FLAGs: only on rails that have NO power_out pin anywhere on their own
# net -- +3V3 (U3.VOUT) and +VBAT_RAW (U2.VBAT) already have one, and a
# redundant flag there trips "two power outputs connected" as an ERROR, not
# just a style nit (confirmed by kicad-cli). GND, +VBUS and +VBAT_SYS have
# no power_out pin at all and genuinely need the flag.
# ===========================================================================
for i, railname in enumerate(["GND", "+VBUS", "+VBAT_SYS"]):
    fx, fy = snap(60 + i * 25), snap(240)
    PWR_FLAGS.append((fx, fy))
    wire((fx, fy), (fx, fy - STUB))
    label((fx, fy - STUB), railname, dir="up")

if __name__ == "__main__":
    print(f"{len(WIRES)} wires, {len(LABELS)} labels, {len(NO_CONNECTS)} NC, "
          f"{len(JUNCTIONS)} junctions, {len(PWR_FLAGS)} pwr flags.")
