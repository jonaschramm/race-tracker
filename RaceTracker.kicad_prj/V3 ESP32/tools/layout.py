"""Shelf-packing layout engine using REAL (no-text) courtyard bounding
boxes measured via fp_bbox.py -- not guessed sizes. Fixes the first PCB
placement attempt's 43 DRC violations (several components were placed
closer together than their real footprints, especially rotated ones whose
courtyard isn't centered on the footprint origin)."""

# (half_width, half_height, center_offset_x, center_offset_y) at rotation=0,
# measured from fp_bbox.py's no-text bounding box.
BBOX = {
    "R0603": (3.01 / 2, 1.51 / 2, 0, 0),
    "C0603": (3.01 / 2, 1.51 / 2, 0, 0),
    "C0805": (3.45 / 2, 2.01 / 2, 0, 0),
    "SW_TACT": (4.85 / 2, 3.35 / 2, 0, 0),
    "SW_SLIDE": (9.78 / 2, 4.79 / 2, 3.81, 0),
    "USBC": (10.69 / 2, 9.47 / 2, 0, -0.56),
    "JST_PH2": (9.25 / 2, 10.25 / 2, 0, 0),
    "JST_SH4": (7.85 / 2, 6.61 / 2, 0, 0),
    "MICROSD": (13.73 / 2, 16.32 / 2, 0, -1.59),
    "PINHDR4": (3.59 / 2, 11.21 / 2, 0, 3.81),
    "SOT236": (4.15 / 2, 3.62 / 2, 0, -0.09),
    "SOD882": (1.70 / 2, 1.34 / 2, 0, 0),
    "LED0603": (3.05 / 2, 1.59 / 2, 0, 0),
    "SOT235": (4.15 / 2, 3.62 / 2, 0, -0.09),
}

REF_KIND = {
    "R8": "R0603", "R9": "R0603", "R10": "R0603", "R11": "R0603", "R12": "R0603",
    "R13": "R0603", "R14": "R0603", "R1": "R0603", "R2": "R0603", "R3": "R0603",
    "R4": "R0603", "R5": "R0603", "R6": "R0603", "R7": "R0603",
    "C9": "C0603", "C10": "C0603", "C1": "C0603", "C2": "C0603", "C3": "C0603",
    "C4": "C0603", "C5": "C0603", "C6": "C0603", "C8": "C0603", "C7": "C0805",
    "SW2": "SW_TACT", "SW3": "SW_TACT", "SW1": "SW_SLIDE",
    "J1": "USBC", "J2": "JST_PH2", "J3": "JST_SH4", "J4": "MICROSD", "J5": "PINHDR4",
    "D1": "SOT236", "D4": "SOD882", "D2": "LED0603", "D3": "LED0603",
    "U2": "SOT235", "U3": "SOT235",
}

GAP = 2.0  # mm, minimum edge-to-edge gap between courtyards


def half_extent(ref, rotation):
    kind = REF_KIND[ref]
    hw, hh, ox, oy = BBOX[kind]
    if rotation == 90 or rotation == 270:
        # 90-degree rotation swaps width/height; offset (ox,oy) rotates too
        # (CW rotation, world_x=local_y, world_y=-local_x per project rule 17).
        return hh, hw, (oy if rotation == 90 else -oy), (-ox if rotation == 90 else ox)
    return hw, hh, ox, oy


def shelf_pack(refs, zone_x0, zone_y0, zone_w, rotations=None):
    """Lay out `refs` left-to-right, wrapping to a new row (shelf) when the
    current row would exceed zone_w. Returns {ref: (x, y)} -- the CENTER
    position to pass to SetPosition (already corrected for each footprint's
    own bbox-center offset, so the bbox itself lands exactly in the packed
    slot regardless of an off-origin courtyard)."""
    rotations = rotations or {}
    positions = {}
    cursor_x = zone_x0 + GAP
    cursor_y = zone_y0 + GAP
    row_max_h = 0.0
    for ref in refs:
        rot = rotations.get(ref, 0)
        hw, hh, ox, oy = half_extent(ref, rot)
        w = 2 * hw
        if cursor_x + w > zone_x0 + zone_w and cursor_x > zone_x0 + GAP:
            cursor_x = zone_x0 + GAP
            cursor_y += row_max_h + GAP
            row_max_h = 0.0
        # bbox left edge must sit at cursor_x -> footprint center = cursor_x + hw - ox
        fp_center_x = cursor_x + hw - ox
        fp_center_y = cursor_y + hh - oy
        positions[ref] = (round(fp_center_x, 3), round(fp_center_y, 3))
        cursor_x += w + GAP
        row_max_h = max(row_max_h, 2 * hh)
    zone_h_used = (cursor_y - zone_y0) + row_max_h + GAP
    return positions, zone_h_used
