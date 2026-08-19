"""Extract and flatten KiCad system-library symbols for embedding in a
project's schematic `lib_symbols` cache (see project memory rule 23: every
lib_symbols entry must be keyed by the full "Nickname:SymbolName", not the
bare symbol name, or kicad-cli sch export svg/pdf silently draws nothing)."""
import re

KICAD_SYM_DIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"


def _find_block(text, key):
    start = text.index(key)
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return start, i + 1
    raise ValueError(f"unbalanced parens for {key}")


def _read_symbol_raw(libfile, symname):
    text = open(f"{KICAD_SYM_DIR}/{libfile}").read()
    key = f'(symbol "{symname}"'
    s, e = _find_block(text, key)
    return text[s:e]


def _all_blocks(text, key_regex):
    """Find all balanced top-level blocks in `text` whose opening line
    matches key_regex (a compiled regex matched at the start of a block,
    e.g. r'\\(property "'). Returns list of (start, end) spans."""
    spans = []
    for m in key_regex.finditer(text):
        start = m.start()
        if spans and start < spans[-1][1]:
            continue  # inside a block we already captured
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    spans.append((start, i + 1))
                    break
    return spans


def get_flat_symbol(libfile, symname, nickname, rename_to=None):
    """Return a self-contained lib_symbols entry for symname, with the
    top-level name prefixed "nickname:symname" (rule 23). If the symbol
    uses (extends "Base"), the base's pin/graphic sub-units are inlined
    so the cache entry has no external dependency."""
    raw = _read_symbol_raw(libfile, symname)
    final_name = rename_to or symname
    m = re.search(r'\(extends "([^"]+)"\)', raw)
    if not m:
        # already self-contained; just rename the top-level symbol
        out = raw.replace(f'(symbol "{symname}"', f'(symbol "{nickname}:{final_name}"', 1)
        return out

    base_name = m.group(1)
    base_raw = _read_symbol_raw(libfile, base_name)

    # properties: take the DERIVED symbol's own property blocks (Reference/
    # Value/Footprint/Datasheet/Description/keywords/fp_filters), but the
    # BASE symbol's pin_names/graphic+pin sub-units (the derived block has
    # none of its own - that's the point of "extends").
    prop_re = re.compile(r'\(property "')
    derived_props = "".join(raw[s:e] + "\n" for s, e in _all_blocks(raw, prop_re))

    # base sub-unit blocks: (symbol "Base_0_0" ...), (symbol "Base_1_1" ...) etc.
    subunit_re = re.compile(r'\(symbol "' + re.escape(base_name) + r'_\d+_\d+"')
    base_subunits = [base_raw[s:e] + "\n" for s, e in _all_blocks(base_raw, subunit_re)]
    renamed_subunits = [su.replace(base_name + "_", final_name + "_") for su in base_subunits]

    pin_names_re = re.compile(r'\(pin_names')
    pn_spans = _all_blocks(base_raw, pin_names_re)
    pin_names_block = (base_raw[pn_spans[0][0]:pn_spans[0][1]] + "\n") if pn_spans else ""

    header_attrs = "\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(duplicate_pin_numbers_are_jumpers no)\n"

    body = (
        f'\t(symbol "{nickname}:{final_name}"\n'
        + pin_names_block
        + header_attrs
        + derived_props
        + "".join(renamed_subunits)
        + "\t\t(embedded_fonts no)\n"
        + "\t)\n"
    )
    return body


def get_pins(libfile, symname):
    """Return [(number, name, electrical_type, local_x, local_y, angle), ...]
    resolving (extends "Base") automatically."""
    raw = _read_symbol_raw(libfile, symname)
    m = re.search(r'\(extends "([^"]+)"\)', raw)
    if m:
        raw = _read_symbol_raw(libfile, m.group(1))
    out = []
    for c in raw.split('(pin ')[1:]:
        ptype = c.split()[0]
        m_at = re.search(r'\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)', c)
        m_num = re.search(r'\(number "(\w+)"', c)
        m_name = re.search(r'\(name "([^"]*)"', c)
        out.append((m_num.group(1), m_name.group(1), ptype,
                    float(m_at.group(1)), float(m_at.group(2)), int(m_at.group(3))))
    return out


if __name__ == "__main__":
    # smoke test
    blk = get_flat_symbol("Regulator_Linear.kicad_sym", "AP2112K-3.3", "Regulator_Linear")
    print(blk[:2000])
