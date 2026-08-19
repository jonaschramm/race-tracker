"""Assemble the final .kicad_sch from the placed components + wiring."""
from build_sch import COMPONENTS, PART_LIB, OUT_PATH, PROJECT_NAME, u
from libextract import get_flat_symbol
import wires as W

LINES = []


def w(s=""):
    LINES.append(s)


# ---------------------------------------------------------------------------
# lib_symbols cache
# ---------------------------------------------------------------------------
seen_lib_ids = set()
lib_blocks = []
for c in COMPONENTS.values():
    info = PART_LIB[c.ptype]
    lib_id = c.lib_id
    if lib_id in seen_lib_ids:
        continue
    seen_lib_ids.add(lib_id)
    lib_blocks.append(get_flat_symbol(info["libfile"], info["sym"], info["nickname"]))
if W.PWR_FLAGS:
    pf = PART_LIB["PWR_FLAG"]
    lib_blocks.append(get_flat_symbol(pf["libfile"], pf["sym"], pf["nickname"]))

w("(kicad_sch")
w("\t(version 20260306)")
w('\t(generator "eeschema")')
w('\t(generator_version "10.0")')
w(f'\t(uuid "{u()}")')
w('\t(paper "A2")')
w("\t(title_block")
w('\t\t(title "RaceTracker V3 -- ESP32-S3-WROOM-1 GPS/IMU Data Logger")')
w('\t\t(rev "0.1")')
w('\t\t(company "Objectix Software Solutions")')
w('\t\t(comment 1 "Jona Schramm")')
w('\t\t(comment 2 "ESP32-S3-WROOM-1-N8, USB-C, LiPo charging, microSD, Qwiic GPS")')
w("\t)")
w("\t(lib_symbols")
for blk in lib_blocks:
    LINES.append(blk.rstrip("\n"))
w("\t)")

# ---------------------------------------------------------------------------
# Symbol instances
# ---------------------------------------------------------------------------
for ref, c in COMPONENTS.items():
    info = PART_LIB[c.ptype]
    w("\t(symbol")
    w(f'\t\t(lib_id "{c.lib_id}")')
    w(f"\t\t(at {c.x} {c.y} {c.angle})")
    w("\t\t(unit 1)")
    w("\t\t(exclude_from_sim no)")
    w("\t\t(in_bom yes)")
    w("\t\t(on_board yes)")
    w("\t\t(in_pos_files yes)")
    w("\t\t(dnp no)")
    w(f'\t\t(uuid "{c.uuid}")')
    w(f'\t\t(property "Reference" "{ref}"')
    w(f"\t\t\t(at {c.x} {c.y - 4.5} 0)")
    w("\t\t\t(effects (font (size 1.27 1.27)))")
    w("\t\t)")
    w(f'\t\t(property "Value" "{c.value}"')
    w(f"\t\t\t(at {c.x} {c.y + 4.5} 0)")
    w("\t\t\t(effects (font (size 1.27 1.27)))")
    w("\t\t)")
    w(f'\t\t(property "Footprint" "{c.footprint or ""}"')
    w(f"\t\t\t(at {c.x} {c.y} 0)")
    w("\t\t\t(effects (font (size 1.27 1.27)) hide)")
    w("\t\t)")
    w('\t\t(property "Datasheet" ""')
    w(f"\t\t\t(at {c.x} {c.y} 0)")
    w("\t\t\t(effects (font (size 1.27 1.27)) hide)")
    w("\t\t)")
    from libextract import get_pins as _gp
    pininfo = ([("1", "pwr", "power_out", 0.0, 0.0, 90)] if info["libfile"] is None
               else _gp(info["libfile"], info["sym"]))
    for num, name, ptype, lx, ly, ang in pininfo:
        w(f'\t\t(pin "{num}"')
        w(f'\t\t\t(uuid "{u()}")')
        w("\t\t)")
    w("\t\t(instances")
    w(f'\t\t\t(project "{PROJECT_NAME}"')
    w('\t\t\t\t(path "/"')
    w(f'\t\t\t\t\t(reference "{ref}")')
    w("\t\t\t\t\t(unit 1)")
    w("\t\t\t\t)")
    w("\t\t\t)")
    w("\t\t)")
    w("\t)")

# ---------------------------------------------------------------------------
# Wires
# ---------------------------------------------------------------------------
for pts in W.WIRES:
    w("\t(wire")
    w("\t\t(pts")
    pts_str = " ".join(f"(xy {x} {y})" for x, y in pts)
    w(f"\t\t\t{pts_str}")
    w("\t\t)")
    w("\t\t(stroke (width 0) (type default))")
    w(f'\t\t(uuid "{u()}")')
    w("\t)")

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
for lbl in W.LABELS:
    x, y = lbl["pos"]
    w(f'\t(label "{lbl["text"]}"')
    w(f"\t\t(at {x} {y} 0)")
    w(f'\t\t(effects (font (size 1.27 1.27)) (justify {lbl["justify"]}))')
    w(f'\t\t(uuid "{u()}")')
    w("\t)")

# ---------------------------------------------------------------------------
# No-connects
# ---------------------------------------------------------------------------
for x, y in W.NO_CONNECTS:
    w("\t(no_connect")
    w(f"\t\t(at {x} {y})")
    w(f'\t\t(uuid "{u()}")')
    w("\t)")

# ---------------------------------------------------------------------------
# Junctions
# ---------------------------------------------------------------------------
for x, y in W.JUNCTIONS:
    w("\t(junction")
    w(f"\t\t(at {x} {y})")
    w("\t\t(diameter 0)")
    w('\t\t(color 0 0 0 0)')
    w(f'\t\t(uuid "{u()}")')
    w("\t)")

# ---------------------------------------------------------------------------
# PWR_FLAG instances
# ---------------------------------------------------------------------------
for i, (x, y) in enumerate(W.PWR_FLAGS):
    ref = f"#FLG{i + 1:02d}"
    w("\t(symbol")
    w('\t\t(lib_id "power:PWR_FLAG")')
    w(f"\t\t(at {x} {y} 0)")
    w("\t\t(unit 1)")
    w("\t\t(exclude_from_sim no)")
    w("\t\t(in_bom no)")
    w("\t\t(on_board no)")
    w("\t\t(in_pos_files no)")
    w("\t\t(dnp no)")
    w(f'\t\t(uuid "{u()}")')
    w(f'\t\t(property "Reference" "{ref}"')
    w(f"\t\t\t(at {x} {y - 3} 0)")
    w("\t\t\t(effects (font (size 1.27 1.27)) hide)")
    w("\t\t)")
    w('\t\t(property "Value" "PWR_FLAG"')
    w(f"\t\t\t(at {x} {y - 5} 0)")
    w("\t\t\t(effects (font (size 1.27 1.27)))")
    w("\t\t)")
    w('\t\t(property "Footprint" ""')
    w(f"\t\t\t(at {x} {y} 0)")
    w("\t\t\t(effects (font (size 1.27 1.27)) hide)")
    w("\t\t)")
    w('\t\t(property "Datasheet" ""')
    w(f"\t\t\t(at {x} {y} 0)")
    w("\t\t\t(effects (font (size 1.27 1.27)) hide)")
    w("\t\t)")
    w('\t\t(pin "1"')
    w(f'\t\t\t(uuid "{u()}")')
    w("\t\t)")
    w("\t\t(instances")
    w(f'\t\t\t(project "{PROJECT_NAME}"')
    w('\t\t\t\t(path "/"')
    w(f'\t\t\t\t\t(reference "{ref}")')
    w("\t\t\t\t\t(unit 1)")
    w("\t\t\t\t)")
    w("\t\t\t)")
    w("\t\t)")
    w("\t)")

w("\t(sheet_instances")
w('\t\t(path "/"')
w('\t\t\t(page "1")')
w("\t\t)")
w("\t)")
w("\t(embedded_fonts no)")
w(")")

out = "\n".join(LINES) + "\n"
with open(OUT_PATH, "w") as f:
    f.write(out)
print(f"Wrote {len(out)} bytes, {len(LINES)} lines to {OUT_PATH}")
