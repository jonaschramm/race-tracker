#!/usr/bin/env python3
"""Extrahiert Bauteildaten (Reference/Value/Footprint/MPN/lib_id) fuer alle in
v2 behaltenen Bauteile aus den fertigen, ERC-geprueften v1-Schaltplaenen.
Quelle der Wahrheit ist ../../RaceTracker.kicad_prj/*.kicad_sch -- dort liegen
die gegen Datenblaetter geprueften Werte. Nichts wird hier erfunden.
"""
import json
import re
from pathlib import Path

V1_DIR = Path(__file__).resolve().parents[2] / "RaceTracker.kicad_prj"
OUT_FILE = Path(__file__).resolve().parent / "parts_v2.json"

GROUPS = [
    ("USB-C Eingang", ["J1", "D1", "R37", "R38", "R1", "C1", "F1", "D4", "C34"]),
    ("LiPo Eingang", ["J7", "F2", "D2"]),
    ("Power-Path", ["Q2", "D3", "R27", "DL3"]),
    ("Laderegler BQ24195L", ["U5", "L2", "C12", "C13", "C14", "C15", "C16",
                             "C19", "C20", "C22", "C32", "R28", "R29", "R30",
                             "R24", "R23", "R25", "R26", "R19", "Q3", "DL2", "R21"]),
    ("3V3-Versorgung", ["U6"]),
    ("SAMD21 + Entkopplung", ["U1", "C17", "C18", "C21", "C24", "C25", "C26",
                              "L3", "C23", "C27", "C5", "C7", "C6", "R8", "R9"]),
    ("Quarz / RTC", ["Y1", "C3", "C4"]),
    ("Reset", ["PB1", "R3", "R6", "R5", "R10", "C2"]),
    ("I2C-Pullups", ["R13", "R14"]),
    ("Programmierung", ["J12", "R2", "R4"]),
    ("MicroSD", ["J10", "C43", "C44", "R40", "R43"]),
    ("Status-LEDs", ["DL10", "DL11", "DL12", "R44", "R45", "R46"]),
]

# Stecker extern (J20/J21/J22) sind neu bzw. wiederverwendet -- siehe
# gen_symbols_v2.py. J21 (e-Paper) nutzt das existierende CONN_EPAPER_8P-Symbol
# 1:1, das in v1 unter der Referenz J11 laeuft. J20/J22 sind neue generische
# 8-polige Stecker ohne v1-Vorlage.
NEW_CONNECTOR_GROUP = ("Stecker extern", ["J20", "J21", "J22"])
V1_EPAPER_REF = "J11"


def parse_sheet(path: Path):
    text = path.read_text()
    blocks = re.split(r"\n\t\(symbol\n", text)
    found = {}
    for b in blocks:
        m_ref = re.search(r'\(property "Reference" "([^"]+)"', b)
        if not m_ref:
            continue
        ref = m_ref.group(1)
        m_lib = re.search(r'\(lib_id "([^"]+)"\)', b)
        m_val = re.search(r'\(property "Value" "([^"]+)"', b)
        m_fp = re.search(r'\(property "Footprint" "([^"]*)"', b)
        m_mpn = re.search(r'\(property "MPN" "([^"]*)"', b)
        m_manuf = re.search(r'\(property "Manufacturer" "([^"]*)"', b)
        found[ref] = {
            "sheet": path.name,
            "lib_id": m_lib.group(1) if m_lib else None,
            "value": m_val.group(1) if m_val else "",
            "footprint": m_fp.group(1) if m_fp else "",
            "mpn": m_mpn.group(1) if m_mpn else "",
            "manufacturer": m_manuf.group(1) if m_manuf else "",
        }
    return found


def main():
    all_refs = {}
    for sheet in V1_DIR.glob("*.kicad_sch"):
        all_refs.update(parse_sheet(sheet))

    wanted = [ref for _, refs in GROUPS for ref in refs]
    missing = [r for r in wanted if r not in all_refs]
    if missing:
        raise SystemExit(f"FEHLER: in v1 nicht gefunden: {missing}")

    data = {"groups": []}
    for name, refs in GROUPS:
        data["groups"].append({
            "name": name,
            "parts": [{"ref": r, **all_refs[r]} for r in refs],
        })
    # Stecker extern: J21 wiederverwendbar, J20/J22 neu (kein v1-Eintrag)
    name, refs = NEW_CONNECTOR_GROUP
    parts = []
    if V1_EPAPER_REF in all_refs:
        j21 = dict(all_refs[V1_EPAPER_REF])
        j21["value"] = "e-Paper (steckbar) 8p"
        parts.append({"ref": "J21", **j21})
    else:
        raise SystemExit(f"FEHLER: e-Paper-Stecker {V1_EPAPER_REF} nicht in v1 gefunden")
    parts.append({"ref": "J20", "sheet": None, "lib_id": "RaceTracker:CONN_GPS_8P",
                  "value": "GPS 8p", "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
                  "mpn": "", "manufacturer": ""})
    parts.append({"ref": "J22", "sheet": None, "lib_id": "RaceTracker:CONN_WIFI_8P",
                  "value": "WiFi 8p", "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
                  "mpn": "", "manufacturer": ""})
    data["groups"].append({"name": name, "parts": parts})

    total = sum(len(g["parts"]) for g in data["groups"])
    OUT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"{total} Bauteile in {len(data['groups'])} Gruppen -> {OUT_FILE}")


if __name__ == "__main__":
    main()
