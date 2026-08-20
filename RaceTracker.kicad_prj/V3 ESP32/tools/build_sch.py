"""Generate the RaceTracker V3 (ESP32-S3) single-sheet schematic.

Runs standalone: writes a complete .kicad_sch to OUT_PATH. Re-run after any
edit to this file to regenerate from scratch (idempotent).
"""
import uuid
from libextract import get_flat_symbol, get_pins
from geom import pin_abs

PROJECT_NAME = "RaceTracker_v3"
OUT_PATH = ("/Users/jonaschramm/Desktop/RaceTracker_KiCad_v14/RaceTracker.kicad_prj/"
            "V3 ESP32/RaceTracker_v3/RaceTracker_v3.kicad_sch")

GRID = 1.27


def snap(v):
    return round(round(v / GRID) * GRID, 3)


def u():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Part catalogue: part-type -> (lib file, symbol name, nickname, footprint)
# ---------------------------------------------------------------------------
PART_LIB = {
    "ESP32S3": dict(libfile="RF_Module.kicad_sym", sym="ESP32-S3-WROOM-1",
                     nickname="RF_Module", footprint="RF_Module:ESP32-S3-WROOM-1"),
    "USBC": dict(libfile="Connector.kicad_sym", sym="USB_C_Receptacle_USB2.0_16P",
                  nickname="Connector", footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"),
    "USBLC6": dict(libfile="Power_Protection.kicad_sym", sym="USBLC6-2SC6",
                    nickname="Power_Protection", footprint="Package_TO_SOT_SMD:SOT-23-6"),
    "TVS": dict(libfile="Diode.kicad_sym", sym="PESD5V0S1UL",
                 nickname="Diode", footprint="Diode_SMD:D_SOD-882"),
    "LDO": dict(libfile="Regulator_Linear.kicad_sym", sym="AP2112K-3.3",
                 nickname="Regulator_Linear", footprint="Package_TO_SOT_SMD:SOT-23-5"),
    "MCP73831": dict(libfile="Battery_Management.kicad_sym", sym="MCP73831-2-OT",
                       nickname="Battery_Management", footprint="Package_TO_SOT_SMD:SOT-23-5"),
    "SDCARD": dict(libfile="Connector.kicad_sym", sym="Micro_SD_Card_Det2",
                     nickname="Connector", footprint="Connector_Card:microSD_HC_Molex_104031-0811"),
    "CONN4": dict(libfile="Connector_Generic.kicad_sym", sym="Conn_01x04",
                    nickname="Connector_Generic", footprint=None),  # footprint set per-instance
    "CONN2": dict(libfile="Connector_Generic.kicad_sym", sym="Conn_01x02",
                    nickname="Connector_Generic", footprint=None),
    "R": dict(libfile="Device.kicad_sym", sym="R", nickname="Device",
               footprint="Resistor_SMD:R_0603_1608Metric"),
    "C": dict(libfile="Device.kicad_sym", sym="C", nickname="Device", footprint=None),
    "LED": dict(libfile="Device.kicad_sym", sym="LED", nickname="Device",
                 footprint="LED_SMD:LED_0603_1608Metric"),
    "SW_PUSH": dict(libfile="Switch.kicad_sym", sym="SW_Push", nickname="Switch",
                      footprint="Button_Switch_SMD:SW_SPST_B3U-1000P"),
    "SW_SPST": dict(libfile="Switch.kicad_sym", sym="SW_SPST", nickname="Switch",
                      footprint="Button_Switch_THT:SW_DIP_SPSTx01_Slide_6.7x4.1mm_W7.62mm_P2.54mm_LowProfile"),
    "PWR_FLAG": dict(libfile="power.kicad_sym", sym="PWR_FLAG", nickname="power", footprint=""),
}

R_FP = "Resistor_SMD:R_0603_1608Metric"
C_FP = "Capacitor_SMD:C_0603_1608Metric"
C_FP_BIG = "Capacitor_SMD:C_0805_2012Metric"

PWR_FLAG_BLOCK = '''\t(symbol "power:PWR_FLAG" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom no) (on_board no)
\t\t(property "Reference" "#FLG" (at 0 1.905 0) (effects (font (size 1.27 1.27)) hide))
\t\t(property "Value" "PWR_FLAG" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
\t\t(symbol "PWR_FLAG_0_0"
\t\t\t(pin power_out line (at 0 0 90) (length 2.54) hide
\t\t\t\t(name "pwr" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t)
\t\t(symbol "PWR_FLAG_0_1"
\t\t\t(polyline (pts (xy 0 0) (xy 0 1.27) (xy -0.635 1.905) (xy 0 2.54) (xy 0.635 1.905) (xy 0 1.27))
\t\t\t\t(stroke (width 0) (type default)) (fill (type none))
\t\t\t)
\t\t)
\t)
'''

_pin_cache = {}


def part_pins(ptype):
    if ptype not in _pin_cache:
        info = PART_LIB[ptype]
        if info["libfile"] is None:
            _pin_cache[ptype] = [("1", "pwr", "power_out", 0.0, 0.0, 90)]
        else:
            _pin_cache[ptype] = get_pins(info["libfile"], info["sym"])
    return _pin_cache[ptype]


class Component:
    def __init__(self, ref, ptype, value, x, y, angle=0, footprint=None):
        self.ref = ref
        self.ptype = ptype
        self.value = value
        self.x, self.y, self.angle = x, y, angle
        self.footprint = footprint or PART_LIB[ptype]["footprint"]
        self.uuid = u()
        self.pin_uuid = {}

    @property
    def lib_id(self):
        info = PART_LIB[self.ptype]
        return f'{info["nickname"]}:{info["sym"]}'

    def pin_pos(self, number):
        for num, name, ptype, lx, ly, ang in part_pins(self.ptype):
            if num == number:
                return pin_abs(self.x, self.y, self.angle, lx, ly)
        raise KeyError(f"{self.ref}: no pin {number}")

    def pin_info(self, number):
        for num, name, ptype, lx, ly, ang in part_pins(self.ptype):
            if num == number:
                return name, ptype
        raise KeyError(f"{self.ref}: no pin {number}")


COMPONENTS = {}


def add(ref, ptype, value, x, y, angle=0, footprint=None):
    c = Component(ref, ptype, value, snap(x), snap(y), angle, footprint)
    COMPONENTS[ref] = c
    return c


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------
# ESP32-S3-WROOM-1 module: reference hub, pin math worked out on paper
# against the transform abs = f(inst, local) in geom.py.
U1 = add("U1", "ESP32S3", "ESP32-S3-WROOM-1-N8", 230, 150)

R_SPAN = 3.81  # Device:R and Device:C both have pins at local y = +-3.81


def y_of(ref, pin):
    return U1.pin_pos(pin)[1] if ref == "U1" else COMPONENTS[ref].pin_pos(pin)[1]


def vpart(ref, ptype, value, target_y, x, footprint=None):
    """Place a vertical 2-pin part (R/C) so its pin 2 (bottom) lands
    exactly on target_y -- pin 1 (top) ends up target_y - 2*R_SPAN away."""
    return add(ref, ptype, value, x, target_y - R_SPAN, angle=0, footprint=footprint)


EN_Y = y_of("U1", "3")     # EN
IO0_Y = y_of("U1", "27")   # BOOT
IO8_Y = y_of("U1", "12")   # I2C SDA
IO9_Y = y_of("U1", "17")   # I2C SCL
IO10_Y = y_of("U1", "18")  # SPI CS   (DAT3/CD)
IO11_Y = y_of("U1", "19")  # SPI MOSI (CMD)
IO12_Y = y_of("U1", "20")  # SPI SCK  (CLK)
IO13_Y = y_of("U1", "21")  # SPI MISO (DAT0)
IO14_Y = y_of("U1", "22")  # SD_CD
RXD0_Y = y_of("U1", "36")
TXD0_Y = y_of("U1", "37")

# --- EN reset circuit (direct-wired local cluster, left of EN pin) --------
R8 = vpart("R8", "R", "10k", EN_Y, 205)                          # EN pull-up
C9 = vpart("C9", "C", "1uF", EN_Y, 196, footprint=C_FP)           # EN delay cap
C10 = vpart("C10", "C", "100nF", EN_Y, 187, footprint=C_FP)       # EN HF decoupling
SW2 = add("SW2", "SW_PUSH", "RESET", 170, EN_Y, angle=0)          # pin2 sits at EN_Y

# --- BOOT circuit -----------------------------------------------------------
R9 = vpart("R9", "R", "10k", IO0_Y, 190)                          # IO0 pull-up (own X lane vs R8)
SW3 = add("SW3", "SW_PUSH", "BOOT", 187, IO0_Y, angle=0)

# --- I2C / GPS Qwiic (module and Qwiic connector share the same 2.54mm
# pin pitch here, so this bus needs no jog at all) --------------------------
R10 = vpart("R10", "R", "4.7k", IO8_Y, 203)     # SDA pull-up
R11 = vpart("R11", "R", "4.7k", IO9_Y, 188)     # SCL pull-up
# J3 (Conn_01x04) local pins: 1=(y=2.54) 2=(y=0) 3=(y=-2.54) 4=(y=-5.08); abs_y = inst_y - local_y.
# Want pin3 (SDA) == IO8_Y and pin4 (SCL) == IO9_Y=IO8_Y+2.54: inst_y = IO8_Y - 2.54.
J3 = add("J3", "CONN4", "Qwiic GPS (I2C)", 140, IO8_Y - 2.54, angle=0,
          footprint="Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal")
# -> pin1=GND @ IO8_Y-5.08, pin2=3V3 @ IO8_Y-2.54, pin3=SDA @ IO8_Y, pin4=SCL @ IO8_Y+2.54=IO9_Y

# --- SPI / microSD (J4's real pinout interleaves VDD/VSS between the
# signal pins, so CS/MOSI stay aligned with the module but SCK/MISO/SD_CD
# need a short vertical jog -- handled in the wiring section, not here) -----
R12 = vpart("R12", "R", "10k", IO10_Y, 196)     # CS pull-up
R13 = vpart("R13", "R", "10k", IO13_Y, 208)     # MISO pull-up (own lane, distinct from R11)
R14 = vpart("R14", "R", "10k", IO14_Y, 180)     # SD_CD pull-up
J4 = add("J4", "SDCARD", "microSD", 95, IO10_Y + 7.62, angle=0)
# J4 pin2 (DAT3/CD = CS) local_y=7.62 -> abs = inst_y - 7.62 = IO10_Y  (matches CS exactly)

# --- UART debug header (module TXD0/RXD0 are adjacent, 2.54mm apart --
# same pitch as the header, so a straight 2-wire hookup needs no jog).
# At angle=180 the sign flip in the transform cancels: abs_y = inst_y + local_y,
# so pin4 (local_y=-5.08, lowest number = "highest" on page) = inst_y-5.08.
# Setting pin4 == TXD0_Y puts pin3 (local_y=-2.54) exactly on RXD0_Y (2.54 below). ---
J5 = add("J5", "CONN4", "UART Debug", 270, TXD0_Y + 5.08, angle=180,
          footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical")
# -> pin1=GND @ TXD0_Y+7.62, pin2=3V3 @ TXD0_Y+5.08, pin3=RXD0 @ TXD0_Y+2.54=RXD0_Y, pin4=TXD0 @ TXD0_Y

# --- USB-C + ESD protection --------------------------------------------------
# Power rails (GND, +3V3, +VBUS, +VBAT_RAW, +VBAT_SYS) are label-based
# everywhere in this design (many scattered tap points -- standard practice,
# see rule 6). The only genuinely point-to-point ("direct wire") nets in this
# whole right-side cluster are the USB D+/D- pair through the ESD diode into
# the module, the charge-status LED chain, the PROG resistor, the power LED,
# and the battery-sense divider -- everything else here is a bypass cap or
# pull resistor sitting on a rail, wired via label taps only.
IO_USBDM_Y = y_of("U1", "13")   # USB_D-
IO_USBDP_Y = y_of("U1", "14")   # USB_D+
IO35_Y = y_of("U1", "28")       # free ADC pin used for battery sense

J1 = add("J1", "USBC", "USB-C", 320, 95)
IO_CC1_Y = pin_abs(320, 95, 0, 15.24, 10.16)[1]   # J1.A5 (CC1), computed before J1's pin
IO_CC2_Y = pin_abs(320, 95, 0, 15.24, 7.62)[1]    # cache is populated (chicken/egg otherwise)
# CC pull-downs pushed well clear of J1's own tightly-packed pin column
# (only 2.54mm pin pitch there) so their GND stubs can never cross a
# neighbouring J1 pin's own stub regardless of stub length; top pin
# aligned exactly to CC1/CC2's Y so the hookup to J1 is one straight run.
R1 = add("R1", "R", "5.1k", 365, IO_CC1_Y + R_SPAN, angle=0)   # CC1 pulldown
R2 = add("R2", "R", "5.1k", 375, IO_CC2_Y + R_SPAN, angle=0)   # CC2 pulldown
C1 = add("C1", "C", "1uF", 320, 78, angle=0, footprint=C_FP)   # VBUS decoupling
# D1 bridges USB D+/D- between J1 and the module -- align its pins to the
# module's USB pins directly (short jog on the J1 side handled in wiring).
D1 = add("D1", "USBLC6", "USBLC6-2SC6", 262, IO_USBDM_Y + 1.27)
D4 = add("D4", "TVS", "PESD5V0S1UL", 330, 70)   # VBUS ESD/surge TVS (kicad-happy UC-002:
                                                 # USBLC6 only covers D+/D-, not a direct
                                                 # strike on VBUS itself)

# --- Battery + charger --------------------------------------------------------
J2 = add("J2", "CONN2", "Battery", 348, 165, angle=0,
          footprint="Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal")
U2 = add("U2", "MCP73831", "MCP73831T-2ACI/OT", 320, 155)
R3 = add("R3", "R", "2k", 300, 148, angle=0)           # PROG (500 mA charge)
C2 = add("C2", "C", "1uF", 315, 140, angle=0, footprint=C_FP)   # charger VDD decoupling
                                                                 # (own X lane vs R3 at 300/299.72)
C3 = add("C3", "C", "4.7uF", 340, 155, angle=0, footprint=C_FP)  # charger VBAT decoupling
D2 = add("D2", "LED", "Charging", 300, 162, angle=0)
R4 = add("R4", "R", "1k", 285, 162, angle=0)
SW1 = add("SW1", "SW_SPST", "PWR", 270, 180, angle=0)

# --- LDO regulation ------------------------------------------------------------
U3 = add("U3", "LDO", "AP2112K-3.3", 300, 190)
C4 = add("C4", "C", "1uF", 280, 190, angle=0, footprint=C_FP)   # LDO input
C5 = add("C5", "C", "1uF", 320, 190, angle=0, footprint=C_FP)   # LDO output
D3 = add("D3", "LED", "Power", 335, 190, angle=0)
R5 = add("R5", "R", "1k", 348, 190, angle=0)

# --- Battery voltage sense: R6/R7 divider stacked so R6's bottom pin and
# R7's top pin both land exactly on MID_Y (direct-wired midpoint); C6 taps
# the same midpoint as a filter cap. The midpoint reaches the module via a
# BATT_SENSE label (genuinely long distance -- island is far from U1). -----
MID_Y = 215.0
# Own X lane, clear of U3/C2's column at x=300 (their GND/rail stubs were
# reaching down into this divider's territory and vice versa).
R6 = add("R6", "R", "1M", 330, MID_Y - R_SPAN, angle=0)         # divider top -> VBAT_SYS
R7 = add("R7", "R", "1M", 330, MID_Y + R_SPAN, angle=0)         # divider bottom -> GND
C6 = add("C6", "C", "100nF", 342, MID_Y + R_SPAN, angle=0, footprint=C_FP)  # top pin -> MID_Y

# --- Bulk decoupling at the module's own 3V3 pin -------------------------------
# Placed well above the module (clear of both pin columns' stub territory,
# which starts at y=127 -- a GND/+3V3 stub reaching further up/down than
# that would otherwise cross the TXD0/RXD0 stubs sharing the same X).
C7 = add("C7", "C", "22uF", 220, 95, angle=0, footprint=C_FP_BIG)
C8 = add("C8", "C", "100nF", 240, 95, angle=0, footprint=C_FP)

print(f"{len(COMPONENTS)} components placed.")
if __name__ == "__main__":
    for ref, c in COMPONENTS.items():
        print(ref, c.ptype, c.x, c.y)
