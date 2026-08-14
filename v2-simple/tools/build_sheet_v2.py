#!/usr/bin/env python3
"""Baut RaceTracker_v2.kicad_sch: ein einziges Blatt, 13 Gruppen, KEINE
Verbindungen (keine Wires/Labels/Power-Symbole/No-Connects) -- nur platzierte
Bauteilkoerper mit Referenz/Wert-Text und Gruppenueberschriften.

Ablauf:
  1. parts_v2.json laden (Bauteilliste je Gruppe, Werte aus v1 extrahiert)
  2. je Bauteiltyp Geometrie aus RaceTracker_v2.kicad_sym lesen (geometry.py)
  3. je Bauteil-Instanz eine Bounding-Box inkl. Referenz-/Wert-Text berechnen
  4. je Gruppe per Shelf-Packing ueberlappungsfrei anordnen
  5. Gruppen zu Baendern zusammensetzen, Baender von oben nach unten stapeln
  6. Papierformat waehlen (A2, sonst A1), Datei schreiben
"""
import json
import uuid
from pathlib import Path

from geometry import load_symbol_meta

TOOLS_DIR = Path(__file__).resolve().parent
KICAD_DIR = TOOLS_DIR.parent / "kicad"
PARTS_JSON = TOOLS_DIR / "parts_v2.json"
SYM_FILE = KICAD_DIR / "RaceTracker_v2.kicad_sym"
OUT_SCH = KICAD_DIR / "RaceTracker_v2.kicad_sch"

REF_FONT = 1.5
VAL_FONT = 1.1
HIDDEN_FONT = 1.27
HEADER_FONT = 2.5

CHAR_W_FACTOR = 1.0   # bewusst grosszuegig, um Text-Ueberlappungen zu vermeiden
LINE_H_FACTOR = 1.6

GAP_INTRA = 23.0       # Mindestabstand zwischen Bauteilkoerpern in einer Gruppe
                        # (bewusst grosszuegiger als reine Platzierung noetig haette:
                        # Netz-Labels beider Nachbarn muessen hier ohne Ueberlappung
                        # nach aussen wachsen koennen, siehe wire_v2.py)
GAP_GROUP_X = 28.0      # Mindestabstand zwischen Gruppen (horizontal)
GAP_GROUP_Y = 32.0      # Mindestabstand zwischen Baendern (vertikal)
HEADER_CLEARANCE = 16.0  # Platz fuer die Gruppenueberschrift ueber den Bauteilen
SUBUNIT_GAP = 20.0      # Abstand zwischen den beiden Koerpern eines Mehrfach-Symbols (U1/Q2)

PAD_EXTRA = {"U1": 45.0, "U5": 40.0}  # Freiraum-Ring um die grossen ICs

MARGIN_X = 20.0
MARGIN_TOP = 20.0
MARGIN_BOTTOM = 32.0

BANDS = [
    ["USB-C Eingang", "LiPo Eingang", "Power-Path"],
    ["Laderegler BQ24195L", "3V3-Versorgung", "Reset", "Programmierung",
     "SAMD21 + Entkopplung", "Quarz / RTC"],
    ["I2C-Pullups", "MicroSD", "Stecker extern", "Status-LEDs"],
]

MAX_ROW_WIDTH = {
    "USB-C Eingang": 150,
    "LiPo Eingang": 90,
    "Power-Path": 150,
    "Laderegler BQ24195L": 190,
    "3V3-Versorgung": 60,
    "SAMD21 + Entkopplung": 190,
    "Quarz / RTC": 70,
    "Reset": 90,
    "I2C-Pullups": 50,
    "Programmierung": 60,
    "MicroSD": 120,
    "Status-LEDs": 120,
    "Stecker extern": 160,
}


GRID = 1.27  # KiCad-Verbindungsraster -- project_kicad_rules Regel 8: alles
# muss darauf liegen, sonst "sieht verbunden aus, ist es aber nicht" (bzw.
# hier: kicad-cli erc meldet endpoint_off_grid für jeden Pin/jedes Wire-Ende
# daneben). Bauteil-Ursprung wird VOR dem Schreiben ins File gerundet, nicht
# die einzelnen Pins -- da lokale Pin-Offsets in den verwendeten Symbolen
# selbst schon Vielfache von GRID sind, reicht das, um am Pin exakt auf dem
# Raster zu landen.


def snap(v: float) -> float:
    return round(v / GRID) * GRID


def fmt(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    if s in ("", "-0"):
        return "0"
    return s


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def new_uuid() -> str:
    return str(uuid.uuid4())


def resolve_lib_name(lib_id: str) -> str:
    """Symbolname wie in RaceTracker_v2.kicad_sym gespeichert (Sonderfall USB-C)."""
    assert lib_id.startswith("RaceTracker:")
    bare = lib_id[len("RaceTracker:"):]
    return lib_id if bare == "USB_C_Receptacle_USB2.0_16P" else bare


def text_envelope(cx, cy, text, font_size):
    w = max(len(text), 1) * font_size * CHAR_W_FACTOR
    h = font_size * LINE_H_FACTOR
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def union_bbox(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def prop_block(name, value, x, y, font_size, hidden=False, indent="\t\t"):
    hide_line = f"\n{indent}\t(hide yes)" if hidden else ""
    return (
        f'{indent}(property "{name}" "{esc(value)}"\n'
        f"{indent}\t(at {fmt(x)} {fmt(y)} 0)\n"
        f"{indent}\t(show_name no)\n"
        f"{indent}\t(do_not_autoplace no)"
        f"{hide_line}\n"
        f"{indent}\t(effects\n"
        f"{indent}\t\t(font\n"
        f"{indent}\t\t\t(size {fmt(font_size)} {fmt(font_size)})\n"
        f"{indent}\t\t)\n"
        f"{indent}\t)\n"
        f"{indent})"
    )


def render_instance(lib_id, ref, value, footprint, x, y, unit, ref_off, val_off, pins):
    uid = new_uuid()
    lines = [
        "\t(symbol",
        f'\t\t(lib_id "{lib_id}")',
        f"\t\t(at {fmt(x)} {fmt(y)} 0)",
        f"\t\t(unit {unit})",
        "\t\t(body_style 1)",
        "\t\t(exclude_from_sim no)",
        "\t\t(in_bom yes)",
        "\t\t(on_board yes)",
        "\t\t(in_pos_files yes)",
        "\t\t(dnp no)",
        f'\t\t(uuid "{uid}")',
        prop_block("Reference", ref, x + ref_off[0], y + ref_off[1], REF_FONT),
        prop_block("Value", value, x + val_off[0], y + val_off[1], VAL_FONT),
        prop_block("Footprint", footprint, x, y, HIDDEN_FONT, hidden=True),
        prop_block("Datasheet", "", x, y, HIDDEN_FONT, hidden=True),
        prop_block("Description", "", x, y, HIDDEN_FONT),
    ]
    for p in pins:
        pin_uid = new_uuid()
        lines.append(f'\t\t(pin "{esc(p)}"\n\t\t\t(uuid "{pin_uid}")\n\t\t)')
    lines.append(
        "\t\t(instances\n"
        '\t\t\t(project "RaceTracker_v2"\n'
        '\t\t\t\t(path "/"\n'
        f'\t\t\t\t\t(reference "{esc(ref)}")\n'
        f"\t\t\t\t\t(unit {unit})\n"
        "\t\t\t\t)\n"
        "\t\t\t)\n"
        "\t\t)"
    )
    lines.append("\t)")
    return "\n".join(lines)


def render_text(s, x, y, size=HEADER_FONT):
    uid = new_uuid()
    return (
        f'\t(text "{esc(s)}"\n'
        "\t\t(exclude_from_sim no)\n"
        f"\t\t(at {fmt(x)} {fmt(y)} 0)\n"
        "\t\t(effects\n"
        "\t\t\t(font\n"
        f"\t\t\t\t(size {fmt(size)} {fmt(size)})\n"
        "\t\t\t)\n"
        "\t\t\t(justify left)\n"
        "\t\t)\n"
        f'\t\t(uuid "{uid}")\n'
        "\t)"
    )


TEXT_BODY_GAP = 1.0  # Mindestabstand zwischen Bauteilkoerper-Kante und eigenem Ref/Wert-Text


def safe_text_offsets(bbox, default_off):
    """Ref-/Wert-Offset relativ zum Bauteil-Ursprung, garantiert ausserhalb
    der eigenen Bounding-Box (statt der oft sehr knappen Symbol-Vorgabe --
    besonders bei kleinen Eagle-Passiv-Symbolen sass der Standardtext sonst
    auf dem eigenen Koerper)."""
    ref_half_h = (REF_FONT * LINE_H_FACTOR) / 2
    val_half_h = (VAL_FONT * LINE_H_FACTOR) / 2
    ref_y = bbox[3] + TEXT_BODY_GAP + ref_half_h
    val_y = bbox[1] - TEXT_BODY_GAP - val_half_h
    return (default_off[0], ref_y), (default_off[0], val_y)


def build_part_layout(part, meta):
    """Liefert Liste von (unit, local_x, local_y, pins, ref_off, val_off)
    sowie lokale Envelope (minx,miny,maxx,maxy) fuer das gesamte Bauteil
    (ein oder zwei Koerper)."""
    units = sorted(meta["units"].keys())

    if len(units) == 1:
        u = units[0]
        bbox = meta["units"][u]["bbox"]
        ref_off, _ = safe_text_offsets(bbox, meta["ref_offset"])
        _, val_off = safe_text_offsets(bbox, meta["value_offset"])
        ref_env = text_envelope(ref_off[0], ref_off[1], part["ref"], REF_FONT)
        val_env = text_envelope(val_off[0], val_off[1], part["value"], VAL_FONT)
        env = union_bbox(union_bbox(bbox, ref_env), val_env)
        if part["ref"] in PAD_EXTRA:
            p = PAD_EXTRA[part["ref"]]
            env = (env[0] - p, env[1] - p, env[2] + p, env[3] + p)
        placements = [(u, 0.0, 0.0, [p["number"] for p in meta["units"][u]["pins"]], ref_off, val_off)]
        return placements, env

    # Mehrfach-Symbol (aktuell nur Q2 / MOSFET_PMOS_DIODE_SIA817): zwei
    # Koerper nebeneinander, gleiche Referenz/Wert auf beiden.
    placements = []
    env = None
    cursor_x = 0.0
    for i, u in enumerate(units):
        bbox = meta["units"][u]["bbox"]
        w = bbox[2] - bbox[0]
        origin_x = cursor_x - bbox[0]
        ref_off, _ = safe_text_offsets(bbox, meta["ref_offset"])
        _, val_off = safe_text_offsets(bbox, meta["value_offset"])
        ref_env = text_envelope(origin_x + ref_off[0], ref_off[1], part["ref"], REF_FONT)
        val_env = text_envelope(origin_x + val_off[0], val_off[1], part["value"], VAL_FONT)
        body_env = (origin_x + bbox[0], bbox[1], origin_x + bbox[2], bbox[3])
        this_env = union_bbox(union_bbox(body_env, ref_env), val_env)
        env = this_env if env is None else union_bbox(env, this_env)
        placements.append((u, origin_x, 0.0, [p["number"] for p in meta["units"][u]["pins"]], ref_off, val_off))
        cursor_x += w + SUBUNIT_GAP
    return placements, env


def pack_group(parts, metas):
    """Shelf-Packing: liefert (instances, width, height).
    instances: Liste von dicts mit part, unit, x, y (gruppen-lokal), pins."""
    max_row_width = MAX_ROW_WIDTH.get(parts[0]["_group"], 140) if parts else 140
    x_cursor = 0.0
    y_cursor = HEADER_CLEARANCE
    row_height = 0.0
    max_width = 0.0
    instances = []
    for part in parts:
        meta = metas[part["lib_id"]]
        placements, env = build_part_layout(part, meta)
        w = env[2] - env[0]
        h = env[3] - env[1]
        if x_cursor > 0 and (x_cursor + w) > max_row_width:
            y_cursor += row_height + GAP_INTRA
            x_cursor = 0.0
            row_height = 0.0
        base_x = x_cursor - env[0]
        base_y = y_cursor - env[1]
        for unit, lx, ly, pins, ref_off, val_off in placements:
            instances.append({
                "part": part, "unit": unit,
                "x": base_x + lx, "y": base_y + ly,
                "pins": pins, "meta": meta,
                "ref_off": ref_off, "val_off": val_off,
            })
        x_cursor += w + GAP_INTRA
        row_height = max(row_height, h)
        max_width = max(max_width, x_cursor - GAP_INTRA)
    total_height = y_cursor + row_height
    return instances, max_width, total_height


def main():
    data = json.loads(PARTS_JSON.read_text())
    sym_lib_text = SYM_FILE.read_text()

    metas = {}
    for g in data["groups"]:
        for p in g["parts"]:
            p["_group"] = g["name"]
            if p["lib_id"] not in metas:
                metas[p["lib_id"]] = load_symbol_meta(sym_lib_text, resolve_lib_name(p["lib_id"]))

    group_layout = {}
    for g in data["groups"]:
        instances, w, h = pack_group(g["parts"], metas)
        group_layout[g["name"]] = {"instances": instances, "size": (w, h)}

    group_abs = {}
    y = 0.0
    content_w = 0.0
    for band in BANDS:
        x = 0.0
        band_h = 0.0
        for gname in band:
            w, h = group_layout[gname]["size"]
            group_abs[gname] = (x, y)
            x += w + GAP_GROUP_X
            band_h = max(band_h, h)
        content_w = max(content_w, x - GAP_GROUP_X)
        y += band_h + GAP_GROUP_Y
    content_h = y - GAP_GROUP_Y

    need_w = content_w + 2 * MARGIN_X
    need_h = content_h + MARGIN_TOP + MARGIN_BOTTOM
    if need_w <= 594 and need_h <= 420:
        paper, paper_w, paper_h = "A2", 594.0, 420.0
    elif need_w <= 841 and need_h <= 594:
        paper, paper_w, paper_h = "A1", 841.0, 594.0
    else:
        paper, paper_w, paper_h = "A0", 1189.0, 841.0

    off_x = MARGIN_X + (paper_w - need_w) / 2 if need_w < paper_w else MARGIN_X
    off_y = MARGIN_TOP

    text_blocks = []
    symbol_blocks = []
    all_boxes = []   # (kind, ref, minx,miny,maxx,maxy) fuer die Pruefung
    text_boxes = []

    for g in data["groups"]:
        gx, gy = group_abs[g["name"]]
        gx += off_x
        gy += off_y
        text_blocks.append(render_text(g["name"], gx, gy + 4))
        text_boxes.append((g["name"], gx, gy - 2, gx + len(g["name"]) * HEADER_FONT, gy + 8))
        for inst in group_layout[g["name"]]["instances"]:
            part = inst["part"]
            meta = inst["meta"]
            abs_x = snap(gx + inst["x"])
            abs_y = snap(gy + inst["y"])
            symbol_blocks.append(render_instance(
                part["lib_id"], part["ref"], part["value"], part["footprint"],
                abs_x, abs_y, inst["unit"], inst["ref_off"], inst["val_off"],
                inst["pins"],
            ))
            bbox = meta["units"][inst["unit"]]["bbox"]
            all_boxes.append((
                f'{part["ref"]}/u{inst["unit"]} body',
                abs_x + bbox[0], abs_y + bbox[1], abs_x + bbox[2], abs_y + bbox[3],
            ))
            ref_env = text_envelope(abs_x + inst["ref_off"][0], abs_y + inst["ref_off"][1], part["ref"], REF_FONT)
            val_env = text_envelope(abs_x + inst["val_off"][0], abs_y + inst["val_off"][1], part["value"], VAL_FONT)
            text_boxes.append((f'{part["ref"]}/u{inst["unit"]} Ref-Text', *ref_env))
            text_boxes.append((f'{part["ref"]}/u{inst["unit"]} Wert-Text', *val_env))

    # eindeutige Symbole fuer lib_symbols einsammeln
    used_lib_ids = sorted({p["lib_id"] for g in data["groups"] for p in g["parts"]})
    lib_symbol_texts = []
    for lib_id in used_lib_ids:
        name = resolve_lib_name(lib_id)
        token = f'(symbol "{name}"'
        idx = sym_lib_text.index(token)
        depth = 0
        j = idx
        while True:
            c = sym_lib_text[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        block = sym_lib_text[idx:j]
        # In der .kicad_sym stehen Symbole ohne Bibliotheks-Praefix (korrekt
        # fuer die Standalone-Bibliothek). Im lib_symbols-Cache einer .kicad_sch
        # muss der TOP-LEVEL-Name dagegen immer "Nickname:Symbolname" sein --
        # sonst zeichnet KiCads Plotter die Instanz nicht (nur ERC/Netlist
        # tolerieren den bloßen Namen). Sub-Unit-Namen (_1_1 etc.) bleiben roh.
        if not name.startswith("RaceTracker:"):
            block = block.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
        indented = "\n".join("\t\t" + line if line else line for line in block.splitlines())
        lib_symbol_texts.append(indented)

    root_uuid = new_uuid()
    header = (
        "(kicad_sch\n"
        "\t(version 20260306)\n"
        '\t(generator "eeschema")\n'
        '\t(generator_version "10.0")\n'
        f'\t(uuid "{root_uuid}")\n'
        f'\t(paper "{paper}")\n'
        "\t(title_block\n"
        '\t\t(title "Race Tracker Platine v2 - vereinfacht (GPS-Logger, keine Verbindungen)")\n'
        '\t\t(rev "0.1")\n'
        '\t\t(company "Objectix Software Solutions")\n'
        '\t\t(comment 1 "Jona Schramm")\n'
        '\t\t(comment 2 "Nur Platzierung -- Verdrahtung erfolgt manuell in KiCad")\n'
        "\t)\n"
        "\t(lib_symbols\n"
        + "\n".join(lib_symbol_texts) + "\n"
        "\t)\n"
    )

    body = "\n".join(text_blocks) + "\n" + "\n".join(symbol_blocks) + "\n"
    footer = (
        "\t(sheet_instances\n"
        '\t\t(path "/"\n'
        '\t\t\t(page "1")\n'
        "\t\t)\n"
        "\t)\n"
        "\t(embedded_fonts no)\n"
        ")\n"
    )

    out_text = header + body + footer
    OUT_SCH.write_text(out_text)

    opens, closes = out_text.count("("), out_text.count(")")
    n_parts = sum(len(g["parts"]) for g in data["groups"])
    n_instances = len(symbol_blocks)
    print(f"{n_parts} Bauteile -> {n_instances} Symbol-Instanzen, {len(text_blocks)} Gruppenkoepfe")
    print(f"Papierformat: {paper} ({paper_w}x{paper_h}mm), Inhalt braucht {need_w:.1f}x{need_h:.1f}mm")
    print(f"Klammernbalance: {opens} auf, {closes} zu ({'OK' if opens == closes else 'FEHLER'})")
    print(f"-> {OUT_SCH}")

    # Kollisionspruefung: Bauteilkoerper (Rechtecke, achsparallel)
    def overlap(a, b):
        return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

    def check(name, boxes):
        collisions = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if overlap(boxes[i][1:], boxes[j][1:]):
                    collisions.append((boxes[i][0], boxes[j][0]))
        print(f"Kollisionen {name}: {len(collisions)}")
        for a, b in collisions[:30]:
            print(f"  UEBERLAPP: {a} <-> {b}")
        return collisions

    def owner(label):
        return label.split(" ")[0]  # z.B. "R37/u1" aus "R37/u1 Ref-Text"

    body_collisions = check("Bauteilkoerper", all_boxes)
    text_collisions = check("Referenz-/Werttexte", text_boxes)
    all_cross = check("Text <-> Bauteilkoerper", all_boxes + text_boxes)
    # eigener Koerper<->eigener Text ueberlappt sich erwartungsgemaess (Text
    # sitzt am Bauteil) -- nur FREMD-Ueberlappungen sind ein echtes Problem.
    foreign_cross = [(a, b) for a, b in all_cross if owner(a) != owner(b)]
    print(f"davon fremde Text/Koerper-Ueberlappungen: {len(foreign_cross)}")
    for a, b in foreign_cross[:30]:
        print(f"  UEBERLAPP: {a} <-> {b}")

    return len(body_collisions) + len(text_collisions) + len(foreign_cross)


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
