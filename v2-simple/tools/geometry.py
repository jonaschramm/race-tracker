#!/usr/bin/env python3
"""Liest Bounding-Box, Pins und Property-Offsets je Symbol aus
RaceTracker_v2.kicad_sym -- generisch per Klammer-Balancierung, unabhaengig
von Einzug/Whitespace im Quelltext.
"""
import re


def find_blocks(text: str, start_token: str):
    """Alle Klammern-balancierten Bloecke, die mit start_token beginnen."""
    blocks = []
    i = 0
    while True:
        idx = text.find(start_token, i)
        if idx == -1:
            break
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
        blocks.append(text[idx:j])
        i = j
    return blocks


def find_top_level_symbol(text: str, name: str) -> str:
    token = f'(symbol "{name}"'
    idx = text.index(token)
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
    return text[idx:j]


def extract_property_offset(sym_text: str, prop_name: str):
    """Property-Offset auf Symbol-Ebene (vor dem ersten verschachtelten Unit-Block)."""
    # Nur der Bereich vor der ersten Unit-Definition zaehlt als Top-Level.
    first_unit = re.search(r'\(symbol "[^"]+_\d+_\d+"', sym_text)
    head = sym_text[: first_unit.start()] if first_unit else sym_text
    m = re.search(
        rf'\(property "{prop_name}" "[^"]*"\s*\(at ([\-0-9.]+) ([\-0-9.]+) (-?[0-9.]+)\)',
        head,
    )
    if not m:
        return (0.0, 0.0)
    return (float(m.group(1)), float(m.group(2)))


def extract_units(sym_text: str, sym_name: str):
    """{unit_nr: {'pins': [...], 'bbox': (minx,miny,maxx,maxy)}}"""
    units = {}
    # Sub-Unit-Namen tragen nie das "RaceTracker:"-Praefix, auch wenn der
    # Top-Level-Name es hat (Projektregel 13: eingebettetes Systemsymbol).
    base_name = sym_name.split(":", 1)[-1]
    for m in re.finditer(rf'\(symbol "{re.escape(base_name)}_(\d+)_(\d+)"', sym_text):
        unit_nr = int(m.group(1))
        if unit_nr in units:
            continue
        unit_name = f"{base_name}_{unit_nr}_{m.group(2)}"
        unit_text = find_top_level_symbol_relaxed(sym_text, unit_name)
        pins = extract_pins(unit_text)
        bbox = extract_graphics_bbox(unit_text)
        for p in pins:
            bbox = union_point(bbox, p["x"], p["y"])
        units[unit_nr] = {"pins": pins, "bbox": bbox}
    return units


def find_top_level_symbol_relaxed(text: str, name: str) -> str:
    idx = text.index(f'(symbol "{name}"')
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
    return text[idx:j]


def extract_pins(unit_text: str):
    pins = []
    for block in find_blocks(unit_text, "(pin "):
        m_at = re.search(r"\(at ([\-0-9.]+) ([\-0-9.]+) (-?[0-9.]+)\)", block)
        m_num = re.search(r'\(number "([^"]*)"', block)
        m_name = re.search(r'\(name "([^"]*)"', block)
        if not (m_at and m_num):
            continue
        pins.append(
            {
                "number": m_num.group(1),
                "name": m_name.group(1) if m_name else "",
                "x": float(m_at.group(1)),
                "y": float(m_at.group(2)),
                "angle": float(m_at.group(3)),
            }
        )
    return pins


def union_point(bbox, x, y):
    if bbox is None:
        return (x, y, x, y)
    minx, miny, maxx, maxy = bbox
    return (min(minx, x), min(miny, y), max(maxx, x), max(maxy, y))


def extract_graphics_bbox(unit_text: str):
    bbox = None
    for kind in ("rectangle", "circle", "polyline", "arc"):
        for block in find_blocks(unit_text, f"({kind}"):
            for m in re.finditer(
                r"\((?:start|end|center|xy|mid)\s+([\-0-9.]+)\s+([\-0-9.]+)\)", block
            ):
                bbox = union_point(bbox, float(m.group(1)), float(m.group(2)))
            m_r = re.search(r"\(radius ([\-0-9.]+)\)", block)
            m_c = re.search(r"\(center ([\-0-9.]+) ([\-0-9.]+)\)", block)
            if m_r and m_c:
                r = float(m_r.group(1))
                cx, cy = float(m_c.group(1)), float(m_c.group(2))
                bbox = union_point(bbox, cx - r, cy - r)
                bbox = union_point(bbox, cx + r, cy + r)
    return bbox if bbox else (0.0, 0.0, 0.0, 0.0)


def load_symbol_meta(sym_lib_text: str, sym_name: str):
    sym_text = find_top_level_symbol(sym_lib_text, sym_name)
    ref_off = extract_property_offset(sym_text, "Reference")
    val_off = extract_property_offset(sym_text, "Value")
    all_units = extract_units(sym_text, sym_name)
    overall_bbox = None
    for u in all_units.values():
        b = u["bbox"]
        overall_bbox = union_point(overall_bbox, b[0], b[1])
        overall_bbox = union_point(overall_bbox, b[2], b[3])
    # Unit 0 ist KiCad-Konvention fuer "Grafik gemeinsam fuer alle Einheiten"
    # (z.B. der Koerper-Umriss von USB_C_Receptacle_USB2.0_16P) -- zaehlt fuer
    # die Bounding-Box, wird aber nie selbst als eigene Instanz platziert.
    placeable_units = {u: v for u, v in all_units.items() if u != 0}
    if not placeable_units:
        placeable_units = all_units
    return {
        "ref_offset": ref_off,
        "value_offset": val_off,
        "units": placeable_units,
        "bbox": overall_bbox,
    }
