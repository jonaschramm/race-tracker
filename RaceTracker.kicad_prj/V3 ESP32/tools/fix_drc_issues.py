#!/usr/bin/env /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Surgical fix for the 6 real DRC violations found after the user's manual
PCB placement edits -- loads the board IN PLACE and only touches what's
broken (rule 19: LoadBoard + edit specific footprints + save preserves
everything else exactly, doesn't discard the user's manual work)."""
import pcbnew

PCB_PATH = ("/Users/jonaschramm/Desktop/RaceTracker_KiCad_v14/RaceTracker.kicad_prj/"
            "V3 ESP32/New Version with WROOM/New Version with WROOM.kicad_pcb")

board = pcbnew.LoadBoard(PCB_PATH)

by_ref = {fp.GetReference(): fp for fp in board.GetFootprints()}


def mm(v):
    return pcbnew.FromMM(v)


def show(ref):
    fp = by_ref[ref]
    pos = fp.GetPosition()
    print(f"{ref}: pos=({pcbnew.ToMM(pos.x):.3f},{pcbnew.ToMM(pos.y):.3f}) "
          f"rot={fp.GetOrientationDegrees():.1f}")
    rf = fp.Reference()
    rp = rf.GetPosition()
    print(f"   ref field: pos=({pcbnew.ToMM(rp.x):.3f},{pcbnew.ToMM(rp.y):.3f}) "
          f"angle={rf.GetTextAngleDegrees():.1f}")


for r in ["R14", "J1", "D2", "U1", "SW1"]:
    show(r)

# (Fix 1, R14 edge clearance, already applied and confirmed by DRC in a
# prior run of this script -- not repeated here, since it used a relative
# offset that isn't safe to re-apply.)

# --- Fix 2: J1's Reference silkscreen text sits at Y=-0.045 (just past
# the Y=0 top board edge). J1's own body courtyard is Y=[0.30,9.78] --
# move the text below the connector instead of above it.
j1 = by_ref["J1"]
rf = j1.Reference()
rf.SetPosition(pcbnew.VECTOR2I(mm(19.0), mm(5.6)))
print("J1 reference field moved to (19.0,5.6)mm (left of the connector body, "
      "clear of the R1/R2/C1 ref-text row below it)")

# --- Fix 3: D2's reference field (Y=36.11) overlaps U1's reference field
# text (at 40.04,35.40, since U1 is rotated). D2's own courtyard is
# Y=[36.74,38.34] -- move D2's ref text below its body instead of above.
d2 = by_ref["D2"]
rf = d2.Reference()
rp = rf.GetPosition()
rf.SetPosition(pcbnew.VECTOR2I(rp.x, mm(39.6)))
print("D2 reference field moved to Y=39.6mm (below D2's body, clear of U1's ref text)")

# --- Fix 4: SW1's reference field (27.505,34.403) sits directly over
# U1's pads 3/4/5 (~25.9-28.5, Y=33.65). SW1's own courtyard is
# Y=[35.10,39.90] -- move the ref text below the switch body instead of
# above it (where U1's pad row currently is).
sw1 = by_ref["SW1"]
rf = sw1.Reference()
rf.SetPosition(pcbnew.VECTOR2I(mm(34.0), mm(37.5)))
print("SW1 reference field moved to (34.0,37.5)mm (right of its body, clear "
      "of U1's pads above and C4/C5's ref text below)")

pcbnew.SaveBoard(PCB_PATH, board)
print(f"\nSaved to {PCB_PATH}")
