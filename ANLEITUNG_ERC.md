# Anleitung: ERC durchführen und wie es weitergeht

## Teil 1 — Projekt öffnen

1. ZIP entpacken. Wichtig: **den kompletten Ordner** `RaceTracker.kicad_prj` behalten —
   die Bibliotheken werden über relative Pfade gefunden, einzelne Dateien allein funktionieren nicht.
2. `RaceTracker.kicad_pro` öffnen (nicht die `.kicad_sch` direkt).
3. KiCad meldet beim Öffnen, dass die Dateien von einer älteren Version stammen.
   **Das ist erwartet und kein Fehler** — KiCad 10 liest ältere Formate und hebt sie beim
   Speichern automatisch an. Umgekehrt ginge es nicht, deshalb schreibe ich bewusst das ältere Format.
4. Falls Symbole als rote Fragezeichen erscheinen: `Einstellungen → Symbolbibliotheken verwalten`
   → Reiter *Projektspezifische Bibliotheken* → Eintrag `RaceTracker` muss auf
   `${KIPRJMOD}/RaceTracker.kicad_sym` zeigen.

## Teil 2 — Annotation prüfen (vor der ERC)

Die Power-Symbole tragen `#PWR?` als Referenz und müssen einmal durchnummeriert werden:

1. `Werkzeuge → Schaltplan annotieren`
2. Bereich: *Gesamter Schaltplan*, Option: **nur unbeschriftete Symbole**
   (sonst werden meine Bauteilnamen R1, C12, U5 … überschrieben — die sollen bleiben,
   weil sie mit den Referenz-Schaltplänen und dem Prüfbericht übereinstimmen!)
3. `Annotation durchführen`

## Teil 3 — ERC laufen lassen

1. `Inspektieren → Electrical Rules Checker` (oder das Käfer-Symbol in der Werkzeugleiste)
2. Button **ERC ausführen**
3. Ergebnis speichern: Button **Bericht speichern…** → als `.rpt` oder `.txt`
4. **Diese Textdatei schick mir bitte.** Sie ist das mit Abstand nützlichste Feedback, weil
   sie exakt benennt, welches Netz und welcher Pin betroffen ist — Screenshots kann ich nur
   grob interpretieren.

### Was du in der ERC erwarten kannst (kein Grund zur Sorge)

| Meldung | Anzahl ca. | Warum sie kommt |
|---|---|---|
| *Pin nicht verbunden* | ~39 | Freie GPIOs und im Original unbeschaltete Pins (siehe Tabelle unten) |
| *Power-Pin nicht getrieben* | einige | Es fehlen noch PWR_FLAG-Symbole an den Einspeisepunkten |
| *Symbol hat keine Footprint-Zuordnung* | viele | Footprints sind teils noch nicht zugewiesen |

**PWR_FLAG ergänzen** (behebt „Power-Pin nicht getrieben"):
Setze je ein `PWR_FLAG`-Symbol an die Stelle, wo Energie ins Netz kommt —
also an `+5V` (am Ausgang der Sicherung F1), an `VBAT` (am Akkustecker J7) und
an `+3V3` / `+3V3D` (an den LDO-Ausgängen von U6 bzw. U3).

**No-Connect-Kreuze** (behebt „Pin nicht verbunden"):
Taste `Q` und dann auf die Pins klicken, die absichtlich frei bleiben sollen.
Bei den freien SAMD21-GPIOs würde ich das **nicht** machen — die brauchen wir noch
für das Sensors_Storage-Blatt.

## Teil 4 — Die 39 offenen Pins im Detail

Alle geprüft, keiner davon ist ein Fehler:

| Blatt | Bauteil | Pins | Einordnung |
|---|---|---|---|
| MCU_Radio | U1 (SAMD21) | 3, 9–12, 15, 16, 19, 20, 30–32, 47, 48 | **Freie GPIOs.** Gingen im MKR nur zu Steckleisten. Reserve für Sensors_Storage (CS-Leitungen, IMU-Interrupt) |
| MCU_Radio | U2 (NINA) | 2–5, 13, 25, 34 | ADC- und RMII-Pins, im Original ebenfalls unbeschaltet |
| GPS | U3 (ZED-F9P) | 4, 5, 6, 46 | ANT_DETECT, ANT_OFF, ANT_SHORT, TX_READY — im Original unbeschaltet |
| GPS | U3 | 26, 27, 39, 40, 42, 43, 47, 49, 50, 51 | UART2, USB, UART1, D_SEL, RESET, SAFEBOOT, EXTINT — gingen nur zu den entfallenen Steckern |
| Power | U5 (BQ24195L) | 2, 3 | USB-D+/D− des Ladereglers, im Original unbeschaltet |
| Power | J1 (USB-C) | SBU1, SBU2 | Seitenband-Pins, nur für Alt-Modes nötig — brauchen wir nicht |

**Wichtig zur Bewertung:** Bei `U3.42/43` (UART TX/RX des GPS) und `U3.49` (RESET) lohnt
die Überlegung, ob du sie doch an freie SAMD21-Pins führen willst. UART wäre ein zweiter
Datenpfad neben I2C, RESET erlaubt einen harten Neustart des GPS per Software.
Sag Bescheid, dann verdrahte ich sie.

## Teil 5 — Nächste Schritte, in dieser Reihenfolge

1. **ERC-Textbericht an mich** — damit ich sehe, was KiCad beanstandet, das meine eigenen
   Prüfungen strukturell nicht finden können.
2. **SWD-Programmierheader ergänzen.** Echter Blocker: ohne ihn lässt sich der SAMD21 nicht
   flashen. Das Referenzdesign hat nur unbestückte Testpads, weil Arduino werkseitig programmiert.
   Braucht 5 Pins: SWCLK, SWDIO, RESET, +3V3, GND.
3. **USB-C-Bauteil festlegen.** Der Footprint ist noch Platzhalter (`TBD_USBC_CONNECTOR`).
   Mit einer JLCPCB-Teilenummer oder einem Datenblatt baue ich den echten Footprint.
4. **Sensors_Storage-Blatt** (MPU-6050, MicroSD, e-Paper-Stecker, Status-LEDs).
   Der SPI-Bus liegt bereits als blattübergreifendes Netz bereit.
5. **Footprints allen Bauteilen zuweisen**, dann Netzliste erzeugen.
6. **Erst danach PCB-Layout.**

Ich würde Punkt 1 und 2 vorziehen, bevor wir das vierte Blatt bauen — sonst schleppen wir
mögliche Fehler in noch mehr Material mit.

## Teil 6 — Wie du mir am besten Rückmeldung gibst

Nach Nützlichkeit sortiert:

1. **ERC-Bericht als Textdatei.** Eindeutig, vollständig, direkt abarbeitbar.
2. **Ein konkretes Beispiel statt einer Sammelaussage.** „D2 hat keine Verbindung"
   führt mich sofort zur Ursache; „manche hängen in der Luft" kostet mich erst eine
   Suchrunde. Dein Hinweis genau dieser Art hat diesmal den Pad-Namen-Fehler aufgedeckt.
3. **Screenshots mit sichtbarem Blattrand**, nicht nur Ausschnitte — daran war
   vorher die schlechte Flächennutzung überhaupt erst erkennbar.
4. **Sagen, was bereits gut ist.** Sonst laufe ich Gefahr, etwas Funktionierendes
   wieder umzubauen.

Ein ehrlicher Hinweis noch: Ich kann die Dateien nie selbst öffnen oder rendern.
Meine Prüfungen (Netzabgleich gegen die Quelle, Verbindungsprüfung, Kollisionsprüfung)
laufen automatisiert über die erzeugten Dateien und finden genau die Fehlerklassen,
die ich vorher bedacht habe. Die ERC findet Klassen, die ich strukturell nicht sehe.
Deshalb ist dein ERC-Lauf kein Formalismus, sondern der eigentliche Test.
