"""Find any wire-segment pair that shares/crosses a coordinate without an
explicit JUNCTIONS marker there -- KiCad connects wires wherever they touch,
even a plain crossing with no shared endpoint, so every such point is a
potential accidental short."""
from wires import WIRES, JUNCTIONS

JSET = {(round(x, 3), round(y, 3)) for x, y in JUNCTIONS}


def seg_bbox(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))


def on_segment(p, a, b):
    # p collinear with a-b and within bbox (segments are axis-aligned or
    # diagonal; use cross product for collinearity, bbox for containment)
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(cross) > 1e-6:
        return False
    return (min(a[0], b[0]) - 1e-6 <= p[0] <= max(a[0], b[0]) + 1e-6 and
            min(a[1], b[1]) - 1e-6 <= p[1] <= max(a[1], b[1]) + 1e-6)


def seg_intersection_points(a, b, c, d):
    """Return list of intersection/overlap points between segment a-b and
    c-d (handles collinear overlap by returning the overlap endpoints)."""
    # Bounding-box reject
    bb1, bb2 = seg_bbox(a, b), seg_bbox(c, d)
    if bb1[2] < bb2[0] - 1e-6 or bb2[2] < bb1[0] - 1e-6 or bb1[3] < bb2[1] - 1e-6 or bb2[3] < bb1[1] - 1e-6:
        return []
    d1 = (b[0] - a[0], b[1] - a[1])
    d2 = (d[0] - c[0], d[1] - c[1])
    denom = d1[0] * d2[1] - d1[1] * d2[0]
    pts = []
    if abs(denom) < 1e-9:
        # parallel/collinear -- check collinearity then overlap
        cross = d1[0] * (c[1] - a[1]) - d1[1] * (c[0] - a[0])
        if abs(cross) > 1e-6:
            return []  # parallel but not collinear
        for p in (a, b, c, d):
            if on_segment(p, a, b) and on_segment(p, c, d):
                pts.append((round(p[0], 3), round(p[1], 3)))
        return list(set(pts))
    t = ((c[0] - a[0]) * d2[1] - (c[1] - a[1]) * d2[0]) / denom
    u = ((c[0] - a[0]) * d1[1] - (c[1] - a[1]) * d1[0]) / denom
    if -1e-6 <= t <= 1 + 1e-6 and -1e-6 <= u <= 1 + 1e-6:
        x = a[0] + t * d1[0]
        y = a[1] + t * d1[1]
        pts.append((round(x, 3), round(y, 3)))
    return pts


found = []
for i in range(len(WIRES)):
    a, b = WIRES[i]
    for j in range(i + 1, len(WIRES)):
        c, d = WIRES[j]
        # skip segments that are part of the same original bus call --
        # can't tell here, so just skip exact-shared-endpoint cases (those
        # are intentional polyline continuations) and only flag crossings
        # / overlaps NOT at a shared endpoint.
        shared_endpoints = {a, b} & {c, d}
        pts = seg_intersection_points(a, b, c, d)
        for p in pts:
            if p in shared_endpoints:
                continue  # normal polyline chain join, not a stray cross
            if p in JSET:
                continue  # explicitly marked junction -- intentional
            found.append((i, j, p, (a, b), (c, d)))

print(f"{len(WIRES)} wires, {len(found)} unmarked crossings found.")
for i, j, p, s1, s2 in found:
    print(f"  @ {p}: wire#{i} {s1}  x  wire#{j} {s2}")
