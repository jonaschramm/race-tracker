# Race Tracker Platine — Projektkontext

> Diese Datei ist das **Projektgedächtnis**. Claude Code liest sie automatisch beim Start
> in diesem Verzeichnis. Sie ersetzt den Chatverlauf von claude.ai, der sich nicht
> übertragen lässt.

**Autor:** Jona Schramm · Objectix Software Solutions

## Was das Projekt ist

Eigene 4-Lagen-Platine: GPS/IMU-Datenlogger für den Renneinsatz auf einem Motorrad.
Ersetzt einen Breadboard-Prototyp (Arduino MKR WiFi 1010 + SparkFun GPS-RTK-SMA +
MPU-6050 + MicroSD + Waveshare e-Paper) durch ein integriertes Custom-Board.

**Stand (2026-08-04):** Alle 4 Schaltplan-Blätter fertig. SWD-Header vorhanden. ERC noch nicht gelaufen. Footprints für viele Passive fehlen. PCB-Layout noch nicht begonnen.

## Grundprinzip: ableiten, nicht erfinden

Kritische Chips werden **nicht neu entworfen**, sondern aus offengelegten
Referenz-Schaltplänen übernommen. Keine erfundenen Bauteilwerte oder Pin-Zuordnungen.

| Blatt | Quelle | Status |
|---|---|---|
| Power | `MKRWiFi1010V2_0.sch` (EAGLE) | aus Referenz abgeleitet ✓ |
| MCU_Radio | `MKRWiFi1010V2_0.sch` (EAGLE) | aus Referenz abgeleitet ✓ |
| GPS | `Qwiic_GPS-RTK-SMA_-_ublox_ZED-F9P.sch` (EAGLE) | aus Referenz abgeleitet ✓ |
| Sensors_Storage | **keine Referenzdatei** | ⚠️ aus Datenblättern, ungeprüft |

**Die EAGLE-Quelldateien fehlen in diesem Repo** (Lizenz/Größe). Lade sie nach:
- Arduino: https://content.arduino.cc/assets/MKRWiFi1010-reference.zip
- SparkFun: https://github.com/sparkfun/Qwiic_GPS-RTK2 (Branch `Add-SMA`, Ordner `Hardware/`)

Ablage: `reference/eagle/`. Die daraus extrahierten Netzlisten liegen bereits
als JSON in `reference/extract/` und `reference/extract_gps/` — damit läuft der
Generator auch ohne die Originaldateien.

## Wie das hier funktioniert

Die `.kicad_sch`-Dateien werden **vollständig generiert**. Von Hand editieren lohnt
nicht — beim nächsten Lauf ist es weg. Änderungen gehören in die Skripte.

```bash
cd tools
python3 build_lib_v2.py        # Symbolbibliothek (Pin-Stapelung, Power-Symbole)
python3 build_sensors_lib.py   # zusätzliche Symbole für Sensors_Storage + SWD
python3 build_footprints.py    # Footprints aus den EAGLE-.brd-Dateien
python3 build_v2.py            # alle 4 Schaltplan-Blätter
python3 build_report.py        # Prüfbericht
```

Prüfwerkzeuge (nach jedem Lauf ausführen):

```bash
python3 final_check.py       # Netze: zerfallen / kurzgeschlossen  -> muss 0/0 sein
python3 verify_output.py     # offene Pins, lose Drahtenden
python3 check_connections.py # Symbol-Pads gegen Quelldatei
```

### Architektur der Skripte

| Datei | Aufgabe |
|---|---|
| `gen_symbols_v2.py` | Symbol-Bausteine, Pin-Typ-Logik, Pin-Stapelung, Power-Symbole |
| `build_lib_v2.py` | erzeugt `RaceTracker.kicad_sym` aus den Referenz-Netzlisten |
| `build_sensors_lib.py` | MPU-6050, MicroSD, e-Paper, SWD-Header (nicht referenzbasiert!) |
| `sheet_v3.py` | **Layout-Engine**: Platzierung, Sammelschienen, Routing, Knotenpunkte |
| `build_v2.py` | Netz-Umbenennungen + welches Bauteil auf welches Blatt |
| `netcheck.py` | rekonstruiert Netze geometrisch aus der fertigen Datei (KiCad-Logik) |

## Hart erkaufte Erkenntnisse — bitte nicht rückgängig machen

Diese Punkte haben je mehrere ERC-Runden gekostet:

1. **Pin-Stapelung.** Der ZED-F9P hat 56 GND-Pads auf einem logischen Pin. Ohne
   Stapelung entstehen 56 Labels und der Plan ist unlesbar. Versteckte Duplikate
   müssen `passive` sein, nicht `power_in` — sonst legt KiCad implizite Netze an.
2. **Pad-Namen aus der Quelle übernehmen.** Dioden/LEDs heißen dort `A`/`C`, nicht `1`/`2`;
   die GPS-Ferritperle `P1`/`P2`; der Taster PTS820 hat die Schaltkontakte auf Pad **5/6**
   (1–4 ist nur Gehäusemasse). Passt das nicht, ist das Bauteil **stumm unverbunden**.
3. **Knotenpunkte nur innerhalb desselben Netzes.** Ein Knoten verbindet alles, was dort
   liegt — netzübergreifend gesetzt erzeugt er Kurzschlüsse.
4. **T-Verbindungen brauchen einen Knotenpunkt.** Endet ein Draht mitten auf einem anderen,
   wertet KiCad das ohne Knoten nicht als Verbindung.
5. **Duplikate nur innerhalb desselben Netzes entfernen.** Sonst löscht ein Netz das
   Drahtstück eines anderen, das zufällig gleich liegt.
6. **Labels sitzen direkt am Pin, ohne Stichleitung.** Jede Stichleitung kann ein fremdes
   Netz berühren. Überdeckende Beschriftungen sind kosmetisch, ein Kurzschluss nicht.
7. **Referenzen projektweit eindeutig.** Beide Referenzentwürfe nummerieren ab 1 —
   GPS-Bauteile liegen deshalb im 100er-Bereich (`U103`, `R114`).
8. **Alles auf 1,27 mm-Raster.** Off-Grid-Punkte sind die klassische Ursache für
   „sieht verbunden aus, ist es aber nicht".
9. **PWR_FLAG-Merker pro Layout-Versuch zurücksetzen.** Das Papierformat wird durch
   Probieren bestimmt; ein verworfener Versuch darf die Flags nicht verbrauchen.

## Bewusste Entscheidungen

- **USB-C statt Micro-USB** (Referenz hat Micro-USB), CC1/CC2-Pulldowns R37/R38 je 5,1 kΩ
- **Zwei 3V3-Schienen**: `+3V3` (SAMD21 + Rest), `+3V3D` (nur NINA-W102, Rauschisolierung)
- **ECC508A weggelassen** — später als I2C-Chip nachrüstbar
- **Lötjumper der Referenzen weggelassen**, Netze beidseits zusammengeführt
  (ohne das wären die GPS-Status-LEDs elektrisch tot)
- **SparkFun-Redundanz weggelassen**: eigener USB-C, eigener LDO, Qwiic-Stecker
- **e-Paper steckbar** (8-polig), nicht fest verlötet
- **No-Connect-Kreuze** auf allen bewusst freien Pins — willst du einen nutzen, Kreuz löschen

## Bus-Belegung

- **I2C** `I2C_SDA`/`I2C_SCL`: ZED-F9P 0x42, MPU-6050 0x68, BQ24195L 0x6B — kein Konflikt
- **SPI** `SPI_MOSI`(PA16)/`SPI_SCK`(PA17)/`SPI_MISO`(PA19): MicroSD + e-Paper
- **CS/Steuerung**: `SD_CS`(PA07), `SD_CD`(PB11), `EPD_CS`(PA06), `EPD_DC`(PA05),
  `EPD_RST`(PA04), `EPD_BUSY`(PA02), `IMU_INT`(PB10)
- **Status-LEDs**: `LED_FIX`(PA21), `LED_REC`(PA22), `LED_ERR`(PA23)

⚠️ Die CS-/Steuerpins habe **ich** frei gewählt. Wenn die Prototyp-Firmware feste Pins
hat, hier anpassen statt die Firmware umzuschreiben.

## Offene Punkte

1. **USB-C-Footprint** ist Platzhalter (`TBD_USBC_CONNECTOR`) — braucht eine konkrete Teilenummer (z. B. JLCPCB-Nummer oder Datenblatt-MPN).
2. **ERC in KiCad ausführen** — Bericht als `.rpt` speichern und in Repo einchecken. Vorher Annotation (nur unbeschriftete Symbole) und PWR_FLAGs ergänzen.
3. **Footprints zuweisen** — Großteil der Passiven und einige Stecker haben noch leeres Footprint-Feld. Danach Netzliste erzeugen.
4. **Sensors_Storage gegen Datenblätter prüfen** (MPU-6050, MicroSD-Buchse, e-Paper-Stecker) — dieses Blatt ist nicht referenzbasiert und bisher ungeprüft.
5. **PCB-Layout**: 4 Lagen, Antennen-Keepouts um NINA-W102 und ZED-F9P nicht verhandelbar, abgewinkelte SMA-Buchse, M2/M2.5-Befestigungslöcher in den Ecken.
6. **Gegenprüfung durch eine Person mit KiCad-Erfahrung vor der Bestellung.**

Bereits erledigt (Stand 2026-08-04):
- ✓ Alle 4 Schaltplan-Blätter fertig (Power, MCU_Radio, GPS, Sensors_Storage)
- ✓ SWD-Programmierheader (CONN_SWD_1x5) in MCU_Radio vorhanden
- ✓ MPU-6050, MicroSD, e-Paper-Stecker, Status-LEDs in Sensors_Storage eingebaut

## Arbeitsweise

- KiCad-Version des Nutzers: **10.0.5**. Geschrieben wird Format `20231120` (KiCad 8) —
  KiCad liest ältere Formate und hebt sie beim Speichern an. Die Versionswarnung beim
  Öffnen ist erwartet, kein Fehler.
- **ERC ist der eigentliche Test.** Die Skripte prüfen nur, was jemand vorher bedacht hat.
  Nach jeder Änderung: in KiCad öffnen, ERC laufen lassen, Bericht auswerten.
- Beim Annotieren **nur unbeschriftete Symbole** wählen — sonst überschreibt KiCad die
  Bauteilnamen, die mit den Referenz-Schaltplänen und dem Prüfbericht übereinstimmen.
