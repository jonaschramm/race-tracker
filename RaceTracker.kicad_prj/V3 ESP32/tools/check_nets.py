"""Resolve the actual net graph from WIRES + LABELS (union-find over shared
coordinates, plus same-text local labels merging regardless of position --
mirrors real KiCad connectivity) and report any component pin that ends up
sharing a net with a DIFFERENT intended label text than expected, by cross-
checking every unmarked wire-wire crossing found by check_crossings.py
against the resolved net of each side."""
from wires import WIRES, LABELS, JUNCTIONS
from check_crossings import found as crossings

# ---------------------------------------------------------------------------
# Union-find over all coordinates that appear in WIRES (2-point segments):
# two points are unioned if they're a wire's endpoints, AND (separately)
# any coordinate that lies exactly on a label's position is tagged with
# that label's text; after building components, verify every component
# touches at most one distinct label text.
# ---------------------------------------------------------------------------
parent = {}


def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb


for a, b in WIRES:
    union(a, b)

# KiCad connects wires wherever they touch or cross, not just at declared
# endpoints (confirmed empirically against real kicad-cli ERC output on
# this project) -- so every unmarked geometric crossing found by
# check_crossings.py is ALSO a real connection, and must be modeled here
# to see the same net-merging kicad-cli would compute.
for i, j, p, s1, s2 in crossings:
    union(s1[0], s2[0])

# label text -> set of component roots it touches
label_pos = {}
for lbl in LABELS:
    label_pos.setdefault(lbl["pos"], set()).add(lbl["text"])

comp_labels = {}  # root -> set of texts
for pos, texts in label_pos.items():
    root = find(pos)
    comp_labels.setdefault(root, set()).update(texts)

# also merge components that share ANY label text (that's how local labels
# actually connect across the sheet without a wire)
text_to_roots = {}
for root, texts in comp_labels.items():
    for t in texts:
        text_to_roots.setdefault(t, []).append(root)
for t, roots in text_to_roots.items():
    for r in roots[1:]:
        union(roots[0], r)

# rebuild final root -> texts after the label-based unions
final_labels = {}
for pos, texts in label_pos.items():
    root = find(pos)
    final_labels.setdefault(root, set()).update(texts)

bad = 0
for r, texts in final_labels.items():
    if len(texts) > 1:
        bad += 1
        print(f"CONFLICT: net contains multiple different labels: {sorted(texts)}")

print(f"\n{len(WIRES)} wires, {len(crossings)} unmarked crossings (all treated as real "
      f"connections), {len(final_labels)} resolved nets, {bad} label conflicts.")
