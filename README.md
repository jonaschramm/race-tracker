# RaceTracker

Custom PCB data logger for motorcycle racing: GPS position + IMU motion data,
logged to a microSD card, with an e-Paper status display. Built around an
ESP32-S3 (WiFi/BT built in) so it can also stream/sync over WiFi.

## Current version: V3 (ESP32-S3)

**This is the active, current board.** Everything else in this repo (see
[History / older versions](#history--older-versions) below) is superseded —
kept for reference only, not under active development.

```
RaceTracker.kicad_prj/V3 ESP32/RaceTracker_v3/RaceTracker_v3.kicad_pro
```

Open that project file in KiCad (10.0.5 or newer) — schematic
(`RaceTracker_v3.kicad_sch`) and PCB (`RaceTracker_v3.kicad_pcb`) are
alongside it.

### Status

- Schematic: ERC clean (0 violations).
- PCB: fully routed by hand, `kicad-cli pcb drc --severity-all` → 0 errors
  (a handful of expected warnings only — see below).
- Board: 4-layer, ~56×66mm with rounded corner bosses for 4× M2 mounting
  holes.
- BOM: all 44 parts have a manufacturer part number and LCSC code (or
  DigiKey, where LCSC doesn't carry the part) in the schematic symbol
  properties — see `bom/bom.csv`.

**Known, expected DRC warnings (not bugs):**
- `lib_footprint_mismatch` on J1, J5, J6, SW1, U1 — these footprints were
  deliberately hand-adjusted to match real component pad geometry (pulled
  from the parts' own datasheets/reference designs) rather than the stock
  KiCad library footprint. **Do not run "Update Footprint from Library" on
  these** — it would silently overwrite the verified geometry.

### Key components

| Function | Part |
|---|---|
| MCU (WiFi + BT) | ESP32-S3-WROOM-1-N8 (U1) |
| IMU (6-axis) | Würth WSEN-ISDS (U4) |
| GPS | external module via J3 (2.54mm header, I2C) — no onboard GPS |
| Storage | microSD (J4) |
| Display | e-Paper via J6 (8-pin header) |
| Charging | MCP73831 Li-Ion charger (U2) + USB-C (J1) |
| 3.3V rail | AP2112K-3.3 LDO (U3) |
| Debug | UART via J5 (4-pin header) |

Pin-header connectors (J3, J5, J6) have their pin functions silkscreened
next to each pin so nothing gets miswired when the board is in hand without
the schematic open.

### Open items

Not yet done — flagging so nothing is assumed finished:

1. **RF review** — the ESP32-S3's on-board antenna keepout is respected on
   the PCB, but nobody with hands-on RF experience has reviewed the
   placement. Espressif's own guideline calls for **≥15mm clearance between
   the antenna and any metal** (enclosure, shielding) — the two mounting
   holes closest to the antenna (top-left/top-right) are only ~3mm away, so
   **use nylon/plastic M2 screws there**, not metal.
2. **Enclosure / mechanical design** — no current mechanical spec for a
   case; board dimensions have changed several times, don't reuse an old one.
3. **3D models / "finished" 3D view** — not started.
4. Two BOM values are assumptions, not confirmed: D2/D3 LED colors (set to
   red/green — schematic didn't specify a color) and SW1's exact MPN
   (couldn't verify its physical dimensions against the datasheet).
5. 27 pads show as "no net" against the schematic's auto-generated
   placeholder nets — reviewed at a glance as genuinely-unused pins
   (GPIO headroom, USB SBU lines), not individually re-verified.

## Repo layout

```
RaceTracker.kicad_prj/
├── *.kicad_sch, RaceTracker.kicad_pcb   ← V1 (SAMD21 + onboard GPS/WiFi modules) — historical
├── V3 ESP32/RaceTracker_v3/             ← V3 (ESP32-S3) — CURRENT, see above
└── V3 ESP32/tools/                      ← pcbnew scripting helpers used while building V3
v2-simple/                                ← V2 (SAMD21, simplified, external GPS/WiFi) — abandoned mid-layout, superseded by V3
reference/eagle/                          ← imported Eagle symbols (Arduino MKR WiFi 1010) used as a source for V1/V2 parts
bom/bom.csv                               ← current BOM with MPN/LCSC/pricing data (V3)
```

### History / older versions

- **V1** (`RaceTracker.kicad_prj/*.kicad_sch` at the repo root, tag
  `v1-full`): original design — Arduino MKR WiFi 1010 (SAMD21) + separate
  u-blox ZED-F9P RTK GPS module + MPU-6050 IMU. Fully routed, but heavier
  and pricier than needed for the actual use case.
- **V2 / `v2-simple`**: a pivot to drop the onboard GPS/WiFi modules in
  favor of external pluggable headers, still on the SAMD21. Placement-only;
  routing was never finished before the project moved to V3's ESP32-S3
  (which has WiFi/BT built in, removing the need for a separate radio
  module entirely). Kept for reference; not maintained.

## Branches

`main` tracks the current state (V3). Historical exploration happened on
`v2-simple` — merged into `main` and not separately maintained going forward.
