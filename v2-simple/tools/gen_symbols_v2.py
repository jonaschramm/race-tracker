#!/usr/bin/env python3
"""Baut RaceTracker_v2.kicad_sym.

Uebernimmt Symbole 1:1 (Byte-fuer-Byte) aus zwei Quellen, je nachdem was
map_eagle_symbols.py fuer ein Bauteil in parts_v2.json eingetragen hat:

  - ../../reference/eagle/MKRWiFi1010V2.0-eagle-import.kicad_sym: die echte,
    per KiCad-Eagle-Import erzeugte Grafik der Arduino-MKR-Referenz -- auf
    Wunsch des Nutzers, weil die frueheren selbstgezeichneten Symbole optisch
    von der Vorlage abwichen. Pin-NUMMERN wurden vorher 1:1 gegen die
    bestehenden, ERC-geprueften v1-Symbole geprueft (nur die Grafik aendert
    sich, siehe project_kicad_rules Regel 23f).
  - ../../RaceTracker.kicad_prj/RaceTracker.kicad_sym: fuer Bauteile ohne
    Eagle-Vorbild (SWD-Header, MicroSD, e-Paper-Stecker) und den bewusst von
    der Referenz (Micro-USB) abweichenden USB-C-Stecker.

Pad-Namen/Pin-Stapelung werden so oder so nicht neu erzeugt -- das ist genau
die Stelle, an der es in diesem Projekt schon einmal schiefging (siehe
Projektregeln: Dioden/LEDs nutzen A/C statt 1/2, PTS820 hat die Schalt-
kontakte auf 5/6).

Neu hinzugefuegt werden nur zwei generische 8-polige Stecker (CONN_GPS_8P,
CONN_WIFI_8P), die es weder in v1 noch in der Eagle-Referenz gibt.
"""
import json
from pathlib import Path

V1_SYM = Path(__file__).resolve().parents[2] / "RaceTracker.kicad_prj" / "RaceTracker.kicad_sym"
EAGLE_SYM = Path(__file__).resolve().parents[2] / "reference" / "eagle" / "MKRWiFi1010V2.0-eagle-import.kicad_sym"
PARTS_JSON = Path(__file__).resolve().parent / "parts_v2.json"
OUT_SYM = Path(__file__).resolve().parents[1] / "kicad" / "RaceTracker_v2.kicad_sym"


def find_top_level_blocks(text: str):
    """Liefert {symbol_name: raw_text} fuer jeden Top-Level (symbol "NAME" ...)-Block.

    Der Einzug fuer Top-Level-Symbole ist je nach Herkunft der Datei
    unterschiedlich (v1-Bibliothek: 2 Leerzeichen; Eagle-Import: 1 Tab) --
    daher wird der kuerzeste vorkommende Einzug automatisch als
    "Top-Level" erkannt, statt eine feste Zeichenzahl anzunehmen.
    """
    occurrences = []
    i = 0
    while True:
        idx = text.find('(symbol "', i)
        if idx == -1:
            break
        name_start = idx + len('(symbol "')
        name_end = text.index('"', name_start)
        name = text[name_start:name_end]
        line_start = text.rfind("\n", 0, idx) + 1
        indent = idx - line_start
        occurrences.append((idx, name, indent))
        i = name_end
    if not occurrences:
        return {}
    top_indent = min(o[2] for o in occurrences)

    blocks = {}
    for idx, name, indent in occurrences:
        if indent != top_indent:
            continue
        depth = 0
        j = idx
        while True:
            c = text[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        blocks[name] = text[idx:j]
    return blocks


NEW_SYMBOLS = {
    "CONN_GPS_8P": '''  (symbol "CONN_GPS_8P" (in_bom yes) (on_board yes)
    (property "Reference" "J" (at 0 13.160 0) (effects (font (size 1.27 1.27))))
    (property "Value" "GPS 8-pol (extern)" (at 0 -13.160 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "CONN_GPS_8P_1_1"
      (rectangle (start -12.700 10.160) (end 12.700 -10.160)
        (stroke (width 0.254) (type default)) (fill (type background)))
      (pin passive line (at -15.240 6.350 0) (length 2.54)
        (name "SDA" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 3.810 0) (length 2.54)
        (name "SCL" (effects (font (size 1.27 1.27))))
        (number "3" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 1.270 0) (length 2.54)
        (name "TX" (effects (font (size 1.27 1.27))))
        (number "4" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 -1.270 0) (length 2.54)
        (name "RX" (effects (font (size 1.27 1.27))))
        (number "5" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 -3.810 0) (length 2.54)
        (name "PPS" (effects (font (size 1.27 1.27))))
        (number "6" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 -6.350 0) (length 2.54)
        (name "RESET" (effects (font (size 1.27 1.27))))
        (number "7" (effects (font (size 1.27 1.27))))
      )
      (pin power_in line (at 0.000 12.700 270) (length 2.54)
        (name "3V3" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin power_in line (at 0.000 -12.700 90) (length 2.54)
        (name "GND" (effects (font (size 1.27 1.27))))
        (number "8" (effects (font (size 1.27 1.27))))
      )
    )
  )
''',
    "CONN_WIFI_8P": '''  (symbol "CONN_WIFI_8P" (in_bom yes) (on_board yes)
    (property "Reference" "J" (at 0 13.160 0) (effects (font (size 1.27 1.27))))
    (property "Value" "WiFi 8-pol (extern)" (at 0 -13.160 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "CONN_WIFI_8P_1_1"
      (rectangle (start -12.700 10.160) (end 12.700 -10.160)
        (stroke (width 0.254) (type default)) (fill (type background)))
      (pin passive line (at -15.240 6.350 0) (length 2.54)
        (name "TX" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 3.810 0) (length 2.54)
        (name "RX" (effects (font (size 1.27 1.27))))
        (number "3" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 1.270 0) (length 2.54)
        (name "RTS" (effects (font (size 1.27 1.27))))
        (number "4" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 -1.270 0) (length 2.54)
        (name "CTS" (effects (font (size 1.27 1.27))))
        (number "5" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 -3.810 0) (length 2.54)
        (name "RESET" (effects (font (size 1.27 1.27))))
        (number "6" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at -15.240 -6.350 0) (length 2.54)
        (name "EN" (effects (font (size 1.27 1.27))))
        (number "7" (effects (font (size 1.27 1.27))))
      )
      (pin power_in line (at 0.000 12.700 270) (length 2.54)
        (name "3V3" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin power_in line (at 0.000 -12.700 90) (length 2.54)
        (name "GND" (effects (font (size 1.27 1.27))))
        (number "8" (effects (font (size 1.27 1.27))))
      )
    )
  )
''',
}


def main():
    v1_blocks = find_top_level_blocks(V1_SYM.read_text())
    eagle_blocks = find_top_level_blocks(EAGLE_SYM.read_text())

    parts = json.loads(PARTS_JSON.read_text())
    needed_lib_ids = set()
    for g in parts["groups"]:
        for p in g["parts"]:
            needed_lib_ids.add(p["lib_id"])

    body_parts = []
    from_v1, from_eagle, from_new = [], [], []
    missing = []
    for lib_id in sorted(needed_lib_ids):
        assert lib_id.startswith("RaceTracker:")
        name = lib_id[len("RaceTracker:"):]
        if name in NEW_SYMBOLS:
            from_new.append(name)
        elif name in v1_blocks:
            # Custom-Bauteile ohne Eagle-Vorbild (SWD-Header, MicroSD,
            # e-Paper-Stecker) und der bewusst abweichende USB-C-Stecker.
            body_parts.append(v1_blocks[name])
            from_v1.append(name)
        elif lib_id in v1_blocks:
            # Sonderfall USB-C: v1 hat den kompletten "RaceTracker:NAME"-Praefix
            # als woertlichen Symbolnamen gespeichert (siehe Projektregel 13,
            # eingebettetes System-Bibliothekssymbol).
            body_parts.append(v1_blocks[lib_id])
            from_v1.append(lib_id)
        elif name in eagle_blocks:
            body_parts.append(eagle_blocks[name])
            from_eagle.append(name)
        else:
            missing.append(name)

    if missing:
        raise SystemExit(f"FEHLER: Symbol(e) weder in v1- noch in Eagle-Bibliothek gefunden: {missing}")

    body_parts += [NEW_SYMBOLS[n] for n in from_new]

    out = '(kicad_symbol_lib (version 20231120) (generator "racetracker_v2_gen") (generator_version "8.0")\n'
    out += "\n".join(body_parts)
    out += "\n)\n"

    OUT_SYM.parent.mkdir(parents=True, exist_ok=True)
    OUT_SYM.write_text(out)

    opens, closes = out.count("("), out.count(")")
    print(f"{len(from_eagle)} Symbole aus der Eagle-Referenz, {len(from_v1)} aus v1 (custom/USB-C), {len(from_new)} neu -> {OUT_SYM}")
    print(f"Eagle: {sorted(from_eagle)}")
    print(f"v1:    {sorted(from_v1)}")
    print(f"Klammernbalance: {opens} auf, {closes} zu ({'OK' if opens == closes else 'FEHLER'})")


if __name__ == "__main__":
    main()
