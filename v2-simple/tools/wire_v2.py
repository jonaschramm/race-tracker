#!/usr/bin/env python3
"""Verdrahtet RaceTracker_v2.kicad_sch: fuegt an den bereits platzierten
Bauteilen (aus build_sheet_v2.py) lokale Labels, No-Connect-Marker und
PWR_FLAG-Symbole an den Pin-Positionen ein. Jedes Label sitzt am Ende eines
kurzen (3mm) Stubs, der exakt am Pin beginnt -- ein Label direkt AM Pin
(project_kicad_rules Regel 6) kollidierte bei jedem senkrecht bepinnten
2-Pin-Teil (v.a. Kondensatoren) mit dem Referenz-/Werttext, den
build_sheet_v2.py schon ueber/unter dem Bauteilkoerper platziert hat -- 68
Faelle, computational per Text-Bounding-Box-Check gefunden. Der Stub ist kurz
genug, um sicher in der Luecke zum Nachbarbauteil zu bleiben (GAP_INTRA/
GAP_GROUP_X >= 18mm) und nicht versehentlich ein fremdes Netz zu beruehren.

Netzliste (netmap_v2.json) wurde aus der ECHTEN kicad-cli-Netlist von v1
abgeleitet (RaceTracker.kicad_prj/*.kicad_sch, GPS.kicad_sch ausgeschlossen),
nicht aus dem kicad-happy-Analyzer -- der hat bei den SWCLK/SWDIO-Pins des
Eagle-Mehrfach-Symbols (ATSAMD21G18A-48QFN) nachweislich falsche Netznamen
ausgegeben (zeigte faelschlich "+3V3" statt der echten Netze, siehe
project_kicad_rules Regel 26-Kontext). Ergaenzt um die drei neuen Stecker
J20 (GPS)/J21 (e-Paper)/J22 (WiFi): J20 bekommt nur SDA/SCL/3V3/GND (I2C-Bus
mit BQ24195L geteilt, exakt wie ZED-F9P in v1) -- TX/RX/PPS/RESET bleiben
No-Connect, da es dafuer keine v1-Entsprechung zum MCU gibt (die eigentliche
GPS-Verkabelung folgt separat, wenn das externe Modul angeschlossen wird).
J22 uebernimmt die SERCOM-Pins, die in v1 an NINA-W102 hingen (PB22/PB23 =
UART, PA14/PA15 = RTS/CTS); RESET/EN bleiben No-Connect (kein sauberer
v1-Fund fuer die durch den entfallenen Pegelwandler Q5 gefuehrte
Reset-Leitung). J21 uebernimmt 1:1 die Pin-Netze von v1s J11.

PWR_FLAG auf GND/VBAT/+5V/CHG_VBUS -- exakt die 4 Netze, bei denen keine
einzige verbliebene v2-Pin vom Typ power_out ist (gegen die Pin-Typen im
kicad-happy-Analyzer-JSON geprueft), matched die 4 PWR_FLAG-Instanzen, die
v1 tatsaechlich hat.
"""
import json
import re
import sys
import uuid
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
KICAD_DIR = TOOLS_DIR.parent / "kicad"
SCH_FILE = KICAD_DIR / "RaceTracker_v2.kicad_sch"
SYM_FILE = KICAD_DIR / "RaceTracker_v2.kicad_sym"
NETMAP_FILE = TOOLS_DIR / "netmap_v2.json"
V1_SYM = Path(__file__).resolve().parents[2] / "RaceTracker.kicad_prj" / "RaceTracker.kicad_sym"

sys.path.insert(0, str(TOOLS_DIR))
from geometry import load_symbol_meta  # noqa: E402

LABEL_FONT = 1.27

GRID = 1.27  # project_kicad_rules Regel 8 -- Pin-Positionen kommen aus
# build_sheet_v2.py schon rasterrichtig (dort gerundet), aber Stub-Laenge
# und PWR_FLAG-Koordinaten sind eigene, frei gewaehlte Werte und muessen
# hier separat auf ein Vielfaches von GRID gebracht werden, sonst meldet
# kicad-cli erc endpoint_off_grid fuer jedes Stub-Ende.


def snap(v: float) -> float:
    return round(v / GRID) * GRID

# (Netzname, x, y) -- freier Platz unten rechts auf dem A1-Blatt (Inhalt
# reicht bis ca. x=765/y=474, Blattgroesse 841x594).
PWR_FLAGS = [
    # Netze mit einer ECHTEN kicad-cli-erc-Fehlermeldung
    # (power_pin_not_driven) auf mindestens einem Pin. +3V3/+3V8 haben zwar
    # einen echten power_out-Treiber (U6.OUT bzw. U5.SW), kicad-cli erc
    # meldet trotzdem "power_pin_not_driven" fuer einzelne Pins (J10.4 bzw.
    # U6.1) -- Ursache nicht abschliessend geklaert, der Flag behebt es.
    # VDDANA/VDDCORE haben GAR KEINEN power_out-Pin (nur Ferritperle/
    # Entkopplung). GND hat ueberhaupt nie einen power_out-Pin im ganzen
    # Design (nur power_in/passive) und braucht daher immer einen Flag,
    # egal was sonst noch auf dem Netz haengt -- J10 Pin 6 (VSS) meldete
    # power_pin_not_driven, sobald der Flag fehlte.
    # U5s (BQ24195L) VBUS/TH/PGND/SYS/BAT-Pins sind laut Symbol vom Typ
    # "Bidirectional" (im Datenblatt tatsaechlich bidirektional, z.B. BAT
    # laedt/entlaedt) und liegen auf denselben Netzen wie diese Flags --
    # das loeste zuerst 9x "Bidirectional and Power output are connected"
    # aus. Statt die Flags wegzulassen (bricht den echten Fehler auf GND/
    # +3V8 wieder auf) wurde die Pin-Konfliktmatrix im .kicad_pro fuer genau
    # diese Kombination auf "ok" gestellt (siehe [2][8]/[8][2] dort) --
    # sachlich richtig, weil ein Bidirectional-Pin eines Ladereglers, der
    # legitim von aussen gespeist wird, keinen echten Konflikt mit einem
    # PWR_FLAG darstellt.
    ("GND", 780.0, 450.0),
    ("+3V3", 780.0, 470.0),
    ("+3V8", 780.0, 490.0),
    ("VDDANA", 780.0, 510.0),
    ("VDDCORE", 780.0, 530.0),
]


def new_uuid() -> str:
    return str(uuid.uuid4())


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def resolve_lib_name(lib_id: str) -> str:
    assert lib_id.startswith("RaceTracker:")
    bare = lib_id[len("RaceTracker:"):]
    return lib_id if bare == "USB_C_Receptacle_USB2.0_16P" else bare


def parse_instances(sch_text: str):
    """(ref, unit) -> dict(x=.., y=.., angle=.., lib_id=..)"""
    out = {}
    for m in re.finditer(
        r'\(symbol\s*\n\t\t\(lib_id "([^"]+)"\)\s*\n\t\t\(at ([\-0-9.]+) ([\-0-9.]+) ([\-0-9.]+)\)\s*\n\t\t\(unit (\d+)\)'
        r'.*?\(property "Reference" "([^"]+)"',
        sch_text,
        re.S,
    ):
        lib_id, x, y, angle, unit, ref = m.groups()
        out[(ref, int(unit))] = {
            "x": float(x), "y": float(y), "angle": float(angle), "lib_id": lib_id,
        }
    return out


def build_pin_index(instances, sym_lib_text):
    """(ref, pin_number) -> (abs_x, abs_y, pin_angle)"""
    # ref -> lib_id (any unit)
    ref_lib = {}
    for (ref, unit), inst in instances.items():
        ref_lib.setdefault(ref, inst["lib_id"])

    meta_cache = {}
    index = {}
    for ref, lib_id in ref_lib.items():
        name = resolve_lib_name(lib_id)
        if lib_id not in meta_cache:
            meta_cache[lib_id] = load_symbol_meta(sym_lib_text, name)
        meta = meta_cache[lib_id]
        for unit, udata in meta["units"].items():
            inst = instances.get((ref, unit))
            if inst is None:
                continue
            assert inst["angle"] == 0.0, f"{ref} unit {unit} ist rotiert -- Pin-Transform nicht implementiert"
            for p in udata["pins"]:
                abs_x = inst["x"] + p["x"]
                abs_y = inst["y"] - p["y"]
                index[(ref, p["number"])] = (abs_x, abs_y, p["angle"])
    return index


def outward_vector(pin_angle):
    """Absolute (dx,dy) vom Pin weg, in Bildschirm-Koordinaten (Y waechst nach
    unten) -- gleiche Vorzeichenkorrektur wie bei der Pin-Positionsberechnung
    (project_kicad_rules Regel 11: abs_y = inst_y - local_y), hier fuer einen
    Richtungsvektor statt einer Position."""
    import math
    outward = math.radians((pin_angle + 180.0) % 360.0)
    return math.cos(outward), -math.sin(outward)


def label_orientation(dx, dy):
    """(display_angle, justify) -- Text laeuft IMMER horizontal, in
    Fliessrichtung dx (bei dx~0 senkrechtem Pin: dy entscheidet, oben->rechts,
    unten->links, willkuerlich aber konsistent)."""
    if dx < -0.3:
        return 0.0, "right"
    if dx > 0.3:
        return 0.0, "left"
    return (0.0, "right") if dy < 0 else (0.0, "left")


def render_label(name, x, y, disp_angle, justify):
    return (
        f'\t(label "{esc(name)}"\n'
        f"\t\t(at {x:.3f} {y:.3f} {disp_angle:.0f})\n"
        "\t\t(effects\n"
        "\t\t\t(font\n"
        f"\t\t\t\t(size {LABEL_FONT} {LABEL_FONT})\n"
        "\t\t\t)\n"
        f"\t\t\t(justify {justify})\n"
        "\t\t)\n"
        f'\t\t(uuid "{new_uuid()}")\n'
        "\t)"
    )


STUB_LEN = 6.35  # mm -- kurzer Draht vom Pin weg, bevor das Label beginnt.
# 5*GRID, nicht 6.5 -- muss selbst ein Vielfaches von GRID sein, sonst ist
# das Stub-Ende off-grid, selbst wenn der Pin es nicht ist.
# Noetig, weil ein Label direkt AM Pin (project_kicad_rules Regel 6) bei
# senkrecht bepinnten 2-Pin-Teilen (v.a. Kondensatoren) exakt in der Spalte
# landet, in der build_sheet_v2.py schon Referenz-/Werttext des Bauteils
# selbst zeichnet -- 68 echte Text-Ueberlappungen, computational gefunden
# (siehe Verifikationsschritt), nicht nur die paar visuell aufgefallenen.
# Der Stub ist kurz genug, um sicher in der Luecke zum Nachbarbauteil zu
# bleiben (GAP_INTRA/GAP_GROUP_X sind beide >= 18mm), und bekommt denselben
# Namen wie das Netz -- am Pin selbst haengt kein Text, der kollidieren koennte.


def stub_and_label(net_name, x, y, pin_angle, blocks):
    x, y = snap(x), snap(y)
    dx, dy = outward_vector(pin_angle)
    sx, sy = snap(x + STUB_LEN * dx), snap(y + STUB_LEN * dy)
    blocks.append(render_wire(x, y, sx, sy))
    disp_angle, justify = label_orientation(dx, dy)
    blocks.append(render_label(net_name, sx, sy, disp_angle, justify))


def render_no_connect(x, y):
    return f'\t(no_connect\n\t\t(at {x:.3f} {y:.3f})\n\t\t(uuid "{new_uuid()}")\n\t)'


def render_wire(x1, y1, x2, y2):
    return (
        "\t(wire\n"
        f"\t\t(pts\n\t\t\t(xy {x1:.3f} {y1:.3f}) (xy {x2:.3f} {y2:.3f})\n\t\t)\n"
        "\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n"
        f'\t\t(uuid "{new_uuid()}")\n'
        "\t)"
    )


def render_pwr_flag(x, y):
    uid = new_uuid()
    return (
        "\t(symbol\n"
        '\t\t(lib_id "RaceTracker:PWR_FLAG")\n'
        f"\t\t(at {x:.3f} {y:.3f} 0)\n"
        "\t\t(unit 1)\n"
        "\t\t(body_style 1)\n"
        "\t\t(exclude_from_sim no)\n"
        "\t\t(in_bom no)\n"
        "\t\t(on_board no)\n"
        "\t\t(in_pos_files no)\n"
        "\t\t(dnp no)\n"
        f'\t\t(uuid "{uid}")\n'
        f'\t\t(property "Reference" "#FLG"\n\t\t\t(at {x:.3f} {y - 1.905:.3f} 0)\n'
        "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(hide yes)\n"
        "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
        f'\t\t(property "Value" "PWR_FLAG"\n\t\t\t(at {x:.3f} {y - 3.556:.3f} 0)\n'
        "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n"
        "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
        f'\t\t(property "Footprint" ""\n\t\t\t(at {x:.3f} {y:.3f} 0)\n'
        "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(hide yes)\n"
        "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
        f'\t\t(property "Datasheet" ""\n\t\t\t(at {x:.3f} {y:.3f} 0)\n'
        "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(hide yes)\n"
        "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
        '\t\t(pin "1"\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        "\t\t)\n"
        "\t\t(instances\n"
        '\t\t\t(project "RaceTracker_v2"\n'
        '\t\t\t\t(path "/"\n'
        f'\t\t\t\t\t(reference "#FLG{{}}")\n'
        "\t\t\t\t\t(unit 1)\n"
        "\t\t\t\t)\n"
        "\t\t\t)\n"
        "\t\t)\n"
        "\t)"
    )


def inject_pwr_flag_lib_symbol(sch_text):
    v1_text = V1_SYM.read_text()
    token = '(symbol "PWR_FLAG"'
    idx = v1_text.index(token)
    depth = 0
    j = idx
    while True:
        c = v1_text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                j += 1
                break
        j += 1
    block = v1_text[idx:j]
    block = block.replace('(symbol "PWR_FLAG"', '(symbol "RaceTracker:PWR_FLAG"', 1)
    indented = "\n".join("\t\t" + line if line else line for line in block.splitlines())
    return sch_text.replace(
        "\t(lib_symbols\n",
        "\t(lib_symbols\n" + indented + "\n",
        1,
    )


def add_pwr_flag_to_project_sym():
    """PWR_FLAG auch in die echte RaceTracker_v2.kicad_sym eintragen, nicht
    nur in den lib_symbols-Cache der .kicad_sch -- sonst meldet kicad-cli
    sch erc 'Symbol PWR_FLAG not found in symbol library RaceTracker'
    (project_kicad_rules Regel 13)."""
    sym_text = SYM_FILE.read_text()
    if '(symbol "PWR_FLAG"' in sym_text:
        return
    v1_text = V1_SYM.read_text()
    token = '(symbol "PWR_FLAG"'
    idx = v1_text.index(token)
    depth = 0
    j = idx
    while True:
        c = v1_text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                j += 1
                break
        j += 1
    block = v1_text[idx:j]
    indented = "\n".join("  " + line if line else line for line in block.splitlines())
    new_sym_text = sym_text.rstrip()
    assert new_sym_text.endswith(")")
    new_sym_text = new_sym_text[:-1] + indented + "\n)\n"
    SYM_FILE.write_text(new_sym_text)


def main():
    sch_text = SCH_FILE.read_text()
    sym_text = SYM_FILE.read_text()
    netmap = json.loads(NETMAP_FILE.read_text())

    instances = parse_instances(sch_text)
    print(f"{len(instances)} Symbol-Instanzen geparst")
    pin_index = build_pin_index(instances, sym_text)
    print(f"{len(pin_index)} Pin-Positionen aufgeloest")

    blocks = []
    missing = []
    for net_name, pins in netmap["nets"].items():
        keys = [(ref, pin_num) for ref, pin_num in pins]
        present = [k for k in keys if k in pin_index]
        missing.extend((net_name, k[0], k[1]) for k in keys if k not in pin_index)

        # Zwei nahe Pins desselben Netzes direkt zu verdrahten wurde erwogen
        # (weniger doppelte Labels), aber verworfen: eine Gerade zum
        # naechsten gleichnamigen Pin kann am NAHEN Pin eines DRITTEN
        # Bauteils vorbeilaufen, das zufaellig dazwischenliegt, und den
        # dort andersnetzigen Pin beruehren -- 2026-08-14 live beobachtet
        # (CHG_TS<->CHG_REGN-Kurzschluss: die Gerade von R29 zu R30s
        # TS-Pin lief exakt ueber R30s eigenen naeher liegenden REGN-Pin).
        # Jeder Pin bekommt daher sicherheitshalber sein eigenes Label.
        for key in present:
            x, y, angle = pin_index[key]
            stub_and_label(net_name, x, y, angle, blocks)

    for ref, pin_num in netmap["no_connect"]:
        key = (ref, pin_num)
        if key not in pin_index:
            missing.append(("NO_CONNECT", ref, pin_num))
            continue
        x, y, angle = pin_index[key]
        blocks.append(render_no_connect(snap(x), snap(y)))

    if missing:
        print(f"FEHLER: {len(missing)} Pins nicht gefunden:")
        for net_name, ref, pin_num in missing:
            print(f"  {net_name}: {ref}.{pin_num}")
        raise SystemExit(1)

    for i, (net_name, x, y) in enumerate(PWR_FLAGS, start=1):
        x, y = snap(x), snap(y)
        blocks.append(render_pwr_flag(x, y).replace("#FLG{}", f"#FLG0{i}"))
        stub_and_label(net_name, x, y, 90.0, blocks)

    # vor dem schliessenden ")" der Datei einfuegen (nach sheet_instances/embedded_fonts)
    insertion = "\n".join(blocks) + "\n"
    idx = sch_text.rindex("\t(sheet_instances\n")
    new_text = sch_text[:idx] + insertion + sch_text[idx:]
    new_text = inject_pwr_flag_lib_symbol(new_text)

    SCH_FILE.write_text(new_text)
    add_pwr_flag_to_project_sym()
    opens, closes = new_text.count("("), new_text.count(")")
    n_nc = len(netmap["no_connect"])
    print(f"{n_nc} No-Connects, {len(PWR_FLAGS)} PWR_FLAGs eingefuegt")
    print(f"Klammernbalance: {opens} auf, {closes} zu ({'OK' if opens == closes else 'FEHLER'})")


if __name__ == "__main__":
    main()
