#!/usr/bin/env python3
"""Ersetzt die lib_id jedes MKR-referenz-abgeleiteten Bauteils in parts_v2.json
durch das passende Symbol aus dem echten Eagle-Import der Arduino-Referenz
(~/Downloads/ABX00023-cad-files/MKRWiFi1010V2.0-eagle-import.kicad_sym) --
auf Wunsch des Nutzers, weil die bisherigen selbstgezeichneten Symbole optisch
von der Eagle-Vorlage abweichen ("die sehen verschieden aus").

Pin-Nummern wurden vorher 1:1 gegen die bestehenden, ERC-geprueften v1-Symbole
geprueft (siehe project_kicad_rules Regel 23/24-Kontext) -- nur die Grafik
aendert sich, keine Elektrik. Custom-Bauteile ohne Eagle-Vorlage (SWD-Header,
MicroSD, e-Paper-Stecker, die neuen GPS/WiFi-Stecker, der USB-C-Stecker als
bewusste Abweichung von der Referenz-Micro-USB-Buchse) bleiben unveraendert.
"""
import json
from pathlib import Path

PARTS_JSON = Path(__file__).resolve().parent / "parts_v2.json"

# alte bare-lib_id (ohne "RaceTracker:") -> neue Eagle-Symbolname (bare)
# "None" bedeutet: Footprint-abhaengig, siehe FOOTPRINT_VARIANTS
DIRECT_MAP = {
    "ESD_PRTR5V0U2X": "PRTR5V0U2X,215",
    "R_GENERIC": "R-0402",
    "PTC_GENERIC": "PTC",
    "CONN_JST_PH_2P": "BATTERY",
    "DIODE_AC": "PMEG6020AELRX",
    "MOSFET_PMOS_DIODE_SIA817": "SIA817EDJ",
    "LED_AC": "LED-0603",
    "BQ24195L_QFN24": "BQ24195QFN-24",
    "L_GENERIC": "LSRP",
    "MOSFET_NCH_SOT523": "2N7002T-SOT523",
    "AP2112K_33_SOT25": "AP2112K-3.3",
    "SAMD21G18A_QFN48": "ATSAMD21G18A-48QFN",
    "FERRITE_GENERIC": "FERRITE0603",
    "CRYSTAL_32K768": "32.768KHZ",
    "SW_PUSH_PTS820": "TACTILE1PTS820-NH",
}

# Bauteiltyp -> {Footprint-Substring: Eagle-Symbolname}, wenn die Eagle-
# Bibliothek je Gehaeusegroesse ein eigenes (grafisch identisches) Symbol hat.
FOOTPRINT_VARIANT_MAP = {
    "C_GENERIC": {
        "C_0402": "C-0402",
        "C_0603": "C-0603",
        "C_0805": "C-0805",
    },
}

# Bleibt unveraendert (kein Eagle-Vorbild oder bewusste Design-Abweichung):
# USB_C_Receptacle_USB2.0_16P, CONN_SWD_1x5, MICROSD_PUSHPUSH,
# CONN_EPAPER_8P, CONN_GPS_8P, CONN_WIFI_8P


def map_lib_id(lib_id: str, footprint: str) -> str:
    bare = lib_id[len("RaceTracker:"):]
    if bare in FOOTPRINT_VARIANT_MAP:
        for substr, new_name in FOOTPRINT_VARIANT_MAP[bare].items():
            if substr in footprint:
                return f"RaceTracker:{new_name}"
        raise SystemExit(f"FEHLER: kein Eagle-Symbol fuer {bare} mit Footprint {footprint}")
    if bare in DIRECT_MAP:
        return f"RaceTracker:{DIRECT_MAP[bare]}"
    return lib_id  # unveraendert lassen


def main():
    data = json.loads(PARTS_JSON.read_text())
    changed = 0
    unchanged_refs = []
    for g in data["groups"]:
        for p in g["parts"]:
            new_lib_id = map_lib_id(p["lib_id"], p["footprint"])
            if new_lib_id != p["lib_id"]:
                p["lib_id"] = new_lib_id
                changed += 1
            else:
                unchanged_refs.append(p["ref"])

    PARTS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"{changed} Bauteile auf Eagle-Symbole umgestellt")
    print(f"{len(unchanged_refs)} unveraendert (custom/bewusste Abweichung): {unchanged_refs}")


if __name__ == "__main__":
    main()
