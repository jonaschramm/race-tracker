#!/usr/bin/env /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Place every footprint on the PCB from the real net list -- NO routing.

Board: 70 x 85mm. U1 (ESP32-S3-WROOM-1) rotated 90 deg so its antenna
faces the LEFT edge; the official KiCad footprint already carries an
enforced keepout rule area (tracks/vias/pads/copperpour/footprints all
forbidden) covering local X[-27.75,-6.75] Y[-24,24] relative to the module
center -- after the 90 deg CW rotation (pcbnew rotates footprints
clockwise, not the standard-math CCW convention -- verified empirically in
this project before) that keepout occupies world X[cx-27.75, cx-6.75],
Y[cy-24, cy+24]. Nothing else is placed in that rectangle.
"""
import sys
sys.path.insert(0, "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages")
import pcbnew
import xml.etree.ElementTree as ET

FP_ROOT = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
NETLIST_XML = "/tmp/v3_netlist.xml"
OUT_PCB = ("/Users/jonaschramm/Desktop/RaceTracker_KiCad_v14/RaceTracker.kicad_prj/"
           "V3 ESP32/RaceTracker_v3/RaceTracker_v3.kicad_pcb")

BOARD_W = 70.0
BOARD_H = 97.0  # bottom zone (14 refs: EN/BOOT + I2C/SPI connectors+pullups)
                # needs more height than the first 85mm attempt gave it

# ref -> "LibNickname:FootprintName" (must match the schematic's Footprint
# property exactly -- pulled from build_sch.py's own PART_LIB/instance data)
FOOTPRINTS = {
    "U1": "RF_Module:ESP32-S3-WROOM-1",
    "R8": "Resistor_SMD:R_0603_1608Metric", "R9": "Resistor_SMD:R_0603_1608Metric",
    "R10": "Resistor_SMD:R_0603_1608Metric", "R11": "Resistor_SMD:R_0603_1608Metric",
    "R12": "Resistor_SMD:R_0603_1608Metric", "R13": "Resistor_SMD:R_0603_1608Metric",
    "R14": "Resistor_SMD:R_0603_1608Metric", "R1": "Resistor_SMD:R_0603_1608Metric",
    "R2": "Resistor_SMD:R_0603_1608Metric", "R3": "Resistor_SMD:R_0603_1608Metric",
    "R4": "Resistor_SMD:R_0603_1608Metric", "R5": "Resistor_SMD:R_0603_1608Metric",
    "R6": "Resistor_SMD:R_0603_1608Metric", "R7": "Resistor_SMD:R_0603_1608Metric",
    "C9": "Capacitor_SMD:C_0603_1608Metric", "C10": "Capacitor_SMD:C_0603_1608Metric",
    "C1": "Capacitor_SMD:C_0603_1608Metric", "C2": "Capacitor_SMD:C_0603_1608Metric",
    "C3": "Capacitor_SMD:C_0603_1608Metric", "C4": "Capacitor_SMD:C_0603_1608Metric",
    "C5": "Capacitor_SMD:C_0603_1608Metric", "C6": "Capacitor_SMD:C_0603_1608Metric",
    "C8": "Capacitor_SMD:C_0603_1608Metric", "C7": "Capacitor_SMD:C_0805_2012Metric",
    "SW2": "Button_Switch_SMD:SW_SPST_B3U-1000P", "SW3": "Button_Switch_SMD:SW_SPST_B3U-1000P",
    "SW1": "Button_Switch_THT:SW_DIP_SPSTx01_Slide_6.7x4.1mm_W7.62mm_P2.54mm_LowProfile",
    "J1": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "J2": "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
    "J3": "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
    "J4": "Connector_Card:microSD_HC_Molex_104031-0811",
    "J5": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "D1": "Package_TO_SOT_SMD:SOT-23-6", "D4": "Diode_SMD:D_SOD-882",
    "D2": "LED_SMD:LED_0603_1608Metric", "D3": "LED_SMD:LED_0603_1608Metric",
    "U2": "Package_TO_SOT_SMD:SOT-23-5", "U3": "Package_TO_SOT_SMD:SOT-23-5",
}

VALUES = {
    "U1": "ESP32-S3-WROOM-1-N8", "R8": "10k", "R9": "10k", "R10": "4.7k", "R11": "4.7k",
    "R12": "10k", "R13": "10k", "R14": "10k", "R1": "5.1k", "R2": "5.1k", "R3": "2k",
    "R4": "1k", "R5": "1k", "R6": "1M", "R7": "1M", "C9": "1uF", "C10": "100nF",
    "C1": "1uF", "C2": "1uF", "C3": "4.7uF", "C4": "1uF", "C5": "1uF", "C6": "100nF",
    "C8": "100nF", "C7": "22uF", "SW2": "RESET", "SW3": "BOOT", "SW1": "PWR",
    "J1": "USB-C", "J2": "Battery", "J3": "Qwiic GPS (I2C)", "J4": "microSD",
    "J5": "UART Debug", "D1": "USBLC6-2SC6", "D4": "PESD5V0S1UL", "D2": "Charging",
    "D3": "Power", "U2": "MCP73831T-2ACI/OT", "U3": "AP2112K-3.3",
}

# Positions come from a real shelf-packer (layout.py) driven by measured
# (no-text) courtyard bounding boxes -- the first attempt at hand-picked
# coordinates produced 43 DRC violations (courtyard overlaps + a pad short)
# because several guessed gaps were smaller than the footprints' real
# extents, especially after 90-degree rotation where the courtyard isn't
# centered on the footprint origin (SW_SLIDE, PINHDR4, MICROSD, U1 itself).
from layout import shelf_pack

U1_POS = (32, 40)
U1_ROT = 90
# U1's real (no-text) bbox at rotation=0: half-extents (24.025, 20.625),
# center offset (0, -7.15) -- includes the enforced antenna keepout zone,
# not just the module body. After the 90 deg CW rotation this becomes
# world half-extents (20.625, 24.025) with center offset (-7.15, 0), i.e.
# real occupied rectangle X[4.23,45.48] Y[15.98,64.03] for U1_POS=(32,40).
U1_X_MIN, U1_X_MAX = 4.2, 45.5
U1_Y_MIN, U1_Y_MAX = 16.0, 64.0

ROTATIONS = {"R6": 90, "R7": 90, "J5": 90}

TOP_REFS = ["J1", "R1", "R2", "C1", "D1", "D4"]
RIGHT_REFS = ["U2", "R3", "C2", "C3", "D2", "R4", "J2",
              "SW1", "U3", "C4", "C5", "D3", "R5",
              "R6", "R7", "C6", "C7", "C8"]
BOTTOM_REFS = ["R8", "C9", "C10", "SW2", "R9", "SW3",
               "R10", "R11", "J3", "R12", "R13", "R14", "J4", "J5"]

top_pos, top_h = shelf_pack(TOP_REFS, 2, 2, BOARD_W - 4, ROTATIONS)
right_pos, right_h = shelf_pack(RIGHT_REFS, U1_X_MAX + 2, U1_Y_MIN, BOARD_W - (U1_X_MAX + 2) - 2, ROTATIONS)
bottom_pos, bottom_h = shelf_pack(BOTTOM_REFS, 2, U1_Y_MAX + 2, BOARD_W - 4, ROTATIONS)

POSITIONS = {"U1": (U1_POS[0], U1_POS[1], U1_ROT)}
for ref, (x, y) in top_pos.items():
    POSITIONS[ref] = (x, y, ROTATIONS.get(ref, 0))
for ref, (x, y) in right_pos.items():
    POSITIONS[ref] = (x, y, ROTATIONS.get(ref, 0))
for ref, (x, y) in bottom_pos.items():
    POSITIONS[ref] = (x, y, ROTATIONS.get(ref, 0))

print(f"zone heights used: top={top_h:.1f}mm (avail {U1_Y_MIN-2:.1f}) "
      f"right={right_h:.1f}mm (avail {U1_Y_MAX-U1_Y_MIN:.1f}) "
      f"bottom={bottom_h:.1f}mm (avail {BOARD_H-U1_Y_MAX-2:.1f})")

# ---------------------------------------------------------------------------
board = pcbnew.BOARD()

# Board outline
outline = pcbnew.PCB_SHAPE(board)
outline.SetShape(pcbnew.SHAPE_T_RECT)
outline.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(0), pcbnew.FromMM(0)))
outline.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(BOARD_W), pcbnew.FromMM(BOARD_H)))
outline.SetLayer(pcbnew.Edge_Cuts)
outline.SetWidth(pcbnew.FromMM(0.15))
board.Add(outline)

# ---------------------------------------------------------------------------
# Net list: ref -> {pin_number: net_name}, from the real kicad-cli-exported
# netlist (authoritative -- see project_kicad_rules.md rule 12).
tree = ET.parse(NETLIST_XML)
root = tree.getroot()
pin_nets = {}
for net in root.find("nets").findall("net"):
    name = net.get("name")
    if name.startswith("unconnected-") or not name:
        continue
    for node in net.findall("node"):
        ref = node.get("ref")
        pin = node.get("pin")
        pin_nets.setdefault(ref, {})[pin] = name

net_cache = {}


def get_net(name):
    if name not in net_cache:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        net_cache[name] = n
    return net_cache[name]


placed = 0
missing = []
for ref, fpid in FOOTPRINTS.items():
    lib_nick, fp_name = fpid.split(":", 1)
    lib_path = f"{FP_ROOT}/{lib_nick}.pretty"
    fp = pcbnew.FootprintLoad(lib_path, fp_name)
    if fp is None:
        missing.append((ref, fpid))
        continue
    fp.SetReference(ref)
    fp.SetValue(VALUES.get(ref, ""))
    board.Add(fp)  # must Add() before Flip()/rotate manipulation (rule 21)

    x, y, rot = POSITIONS[ref]
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientationDegrees(rot)

    for pad in fp.Pads():
        pad_name = pad.GetNumber()
        net_name = pin_nets.get(ref, {}).get(pad_name)
        if net_name:
            pad.SetNet(get_net(net_name))
    placed += 1

print(f"Placed {placed}/{len(FOOTPRINTS)} footprints.")
if missing:
    print("MISSING FOOTPRINTS:", missing)

pcbnew.SaveBoard(OUT_PCB, board)
print(f"Saved to {OUT_PCB}")
