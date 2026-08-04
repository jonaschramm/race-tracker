# Prüfbericht zur Handvalidierung — Race Tracker Platine

Erzeugt aus denselben Daten wie die Schaltpläne. Zweck: du kannst jede Verbindung gegen die
Original-Referenzschaltpläne (Arduino MKR WiFi 1010 / SparkFun GPS-RTK-SMA) abhaken,
ohne die KiCad-Datei lesen zu müssen.

**So prüfst du:** Für jedes Netz unten steht, welche Bauteil-Pins zusammenhängen.
Die Spalte *Quelle* sagt, ob das exakt so im Referenz-Schaltplan steht.

## Blatt: Power

Bauteile auf diesem Blatt: **40**, Netze: **30**

| Netz | verbundene Bauteil-Pins | Quelle |
|---|---|---|
| `+3V3` | R24.1, R26.1, U6.OUT | identisch |
| `+3V3D` | U3.OUT, C8.1, C9.2, C33.1 | identisch |
| `+3V8` | U5.SYS, L2.2, C19.1, C20.1, C22.1, C32.1, R23.2, U3.EN, U3.IN, U6.EN, U6.IN | identisch |
| `+5V` | D1.4, F1.2, Q2.D, D3.C | identisch |
| `BATT_RAW` | J7.1, F2.1 | = `N$3` |
| `CC1` | R37.1 ⚠️ **nur 1 Anschluss** | manuell (Neuentwurf, s.u.) |
| `CC2` | R38.1 ⚠️ **nur 1 Anschluss** | manuell (Neuentwurf, s.u.) |
| `CHG_BOOT` | U5.BTST, C15.1 | = `N$18` |
| `CHG_CE` | U5.CE, R25.2 | = `N$24` |
| `CHG_ILIM` | U5.ILIM, R28.1 | = `N$19` |
| `CHG_OTG` | U5.OTG, R26.2, Q3.D | = `N$22` |
| `CHG_REGN` | U5.REGN, C16.1, R30.1 | = `N$21` |
| `CHG_SW` | U5.SW, L2.1, C15.2 | = `N$15` |
| `CHG_TS` | U5.TS1, U5.TS2, R29.2, R30.2 | = `N$23` |
| `CHG_VBUS` | Q2.S, Q2.C, R27.2, U5.VBUS, C14.1 | = `N$17` |
| `DL2_ANODE` | R23.1, DL2.A | = `N17798864` |
| `DL3_ANODE` | R27.1, DL3.A | = `N17834267` |
| `GND` | R37.2, R38.2, R1.1, C1.2, J7.2, J7.SH, D2.A, DL3.C, U5.PGND, U5.TH, C12.2, C13.2, C14.2, C16.2, C19.2, C20.2, C22.2, C32.2, R28.2, R29.1, R25.1, R1… | manuell (Neuentwurf, s.u.) |
| `I2C_SCL` | U5.SCL ⚠️ **nur 1 Anschluss** | = `PA09_S0_I2C_SCL` |
| `I2C_SDA` | U5.SDA ⚠️ **nur 1 Anschluss** | = `PA08_S0_I2C_SDA` |
| `PA18_OTG` | Q3.G ⚠️ **nur 1 Anschluss** | identisch |
| `PMICINT` | U5.INT, R24.2 | identisch |
| `STAT` | U5.STAT, DL2.C | identisch |
| `USB_N` | D1.3 ⚠️ **nur 1 Anschluss** | identisch |
| `USB_P` | D1.2 ⚠️ **nur 1 Anschluss** | identisch |
| `USB_SHIELD_RC` | D1.1, R1.2, C1.1 | = `N$1` |
| `VBAT` | F2.2, D2.C, U5.BAT | = `VBATT` |
| `VBUS_RAW` | F1.1 ⚠️ **nur 1 Anschluss** | = `N$2` |
| `VIN` | Q2.G, Q2.A, R19.2 | identisch |
| `VUSB1` | D3.A, U5.PMID, C12.1, C13.1 | identisch |

**Netze mit nur einem Anschluss auf Power** (8): `CC1`, `CC2`, `I2C_SCL`, `I2C_SDA`, `PA18_OTG`, `USB_N`, `USB_P`, `VBUS_RAW`

Das sind ungenutzte Pins (im Original gingen sie nur zu Steckverbindern, die wir weggelassen haben).
Sie sind **kein Fehler**, aber die ERC wird sie als „nicht verbunden“ melden — dort kannst du sie
mit einem No-Connect-Kreuz quittieren oder für spätere Erweiterungen offenlassen.

## Blatt: MCU_Radio

Bauteile auf diesem Blatt: **46**, Netze: **64**

| Netz | verbundene Bauteil-Pins | Quelle |
|---|---|---|
| `+3V3` | U1.VDDIN, U1.VDDIO@1, U1.VDDIO@2, C17.1, C18.1, C21.1, C24.1, C26.1, L3.1, R5.2, R21.1, R13.2, R14.2, R4.2, R15.1 | identisch |
| `+3V3D` | U2.VCC, U2.VCCIO, R7.2 | identisch |
| `DL1_ANODE` | R15.2, DL1.A | = `N$7` |
| `DL1_KATHODE` | Q1.D, DL1.C | = `N$10` |
| `EPD_BUSY` | U1.PA02 ⚠️ **nur 1 Anschluss** | = `PA02_AIN0` |
| `EPD_CS` | U1.PA06 ⚠️ **nur 1 Anschluss** | = `PA06_AIN6` |
| `EPD_DC` | U1.PA05 ⚠️ **nur 1 Anschluss** | = `PA05_AIN5` |
| `EPD_RST` | U1.PA04 ⚠️ **nur 1 Anschluss** | = `PA04_AIN4` |
| `GND` | U1.EP, U1.GND@1, U1.GND@2, U1.GND@3, U1.GNDANA, C17.2, C18.2, C21.2, C24.2, C26.2, C25.2, C23.2, C27.2, C5.2, C7.2, C6.2, R9.1, C3.1, C4.1, PB1.1, … | identisch |
| `I2C_SCL` | U1.PA09, R20.2, R13.1 | = `PA09_S0_I2C_SCL` |
| `I2C_SDA` | U1.PA08, R18.2, R14.1 | = `PA08_S0_I2C_SDA` |
| `IMU_INT` | U1.PB10 ⚠️ **nur 1 Anschluss** | = `PB10_TCC0-W4` |
| `LED_BLUE` | U2.RMII_RXD1/DAC17/GPIO26, DL4.RED_A | identisch |
| `LED_ERR` | U1.PA23 ⚠️ **nur 1 Anschluss** | = `PA23_TC4-W1` |
| `LED_FIX` | U1.PA21 ⚠️ **nur 1 Anschluss** | = `PA21_TCC0-W7` |
| `LED_GREEN` | U2.RMII_RXD0/DAC16/GPIO25, DL4.GREEN_A | identisch |
| `LED_REC` | U1.PA22 ⚠️ **nur 1 Anschluss** | = `PA22_TC4-W0` |
| `LED_RED` | U2.RMII_CRSDV/GPIO27, DL4.BLUE_A | identisch |
| `NINA_GPIO13` | U2.JTCLK/GPIO13, R18.1 | = `N$11` |
| `NINA_GPIO14` | U2.JTMS/GPIO14, R20.1 | = `N$12` |
| `NINA_GPIO15` | U2.JTDO/GPIO15, R22.2 | = `N$26` |
| `NINA_GPIO21` | U2.SPIV_HD/RMII_TXEN/GPIO21, R12.2 | = `N$27` |
| `NINA_GPIO4` | U2.RMII_MDIO/GPIO4, R17.1 | = `N$13` |
| `NINA_LPO` | U2.LPO_IN/GPIO32 ⚠️ **nur 1 Anschluss** | = `N$25` |
| `NINA_RESET_N` | U2.RESET_N, R7.1, Q5.D | = `N$9` |
| `NINA_SELFRST` | R11.1, R17.2, Q5.G | = `N$28` |
| `PA00_XIN32` | U1.PA00/XIN32, Y1.2, C3.2 | identisch |
| `PA01_XOUT32` | U1.PA01/XOUT32, Y1.1, C4.2 | identisch |
| `PA03_VREFA` | U1.PA03, C5.1, C7.1 | identisch |
| `PA10_TCC0-W2` | U1.PA10 ⚠️ **nur 1 Anschluss** | identisch |
| `PA11_TCC0-W3` | U1.PA11 ⚠️ **nur 1 Anschluss** | identisch |
| `PA12_S2_TX/MOSI` | U1.PA12, U2.GPIO12 | identisch |
| `PA13_S2_RX/MISO` | U1.PA13, U2.SPIV_DI/GPIO23 | identisch |
| `PA14_S2_RTS/CS` | U1.PA14, U2.SPIV_CS/GPIO5, U2.UART_CTS/RMII_TXD0/SPIV_D0/GPIO19 | identisch |
| `PA15_S2_CTS/SCK` | U1.PA15, U2.SPIV_CLK/GPIO18, U2.UART_RTS/RMII_TXD1/SPIV_WP/GPIO22 | identisch |
| `PA18_OTG` | U1.PA18, R21.2 | identisch |
| `PA20_TCC0-W6` | U1.PA20, R16.2, Q1.G | identisch |
| `PA27_GPIO0` | U1.PA27, U2.RMII_CLK/GPIO0 | identisch |
| `PA28_ACK` | U1.PA28, U2.GPIO33 | identisch |
| `PA30_SWCLK` | U1.PA30/SWCLK, R4.1, R12.1 | identisch |
| `PA31_SWDIO` | U1.PA31/SWDIO, R22.1 | identisch |
| `PB02_AIN10` | U1.PB02 ⚠️ **nur 1 Anschluss** | identisch |
| `PB03_AIN11` | U1.PB03 ⚠️ **nur 1 Anschluss** | identisch |
| `PB08_RST` | U1.PB08, R10.1, Q5.G | identisch |
| `PB09_FILT` | U1.PB09, C6.1, R8.1, R9.2 | = `N$6` |
| `PB22_S5_TX` | U1.PB22, U2.UART_RXD/GPIO3 | identisch |
| `PB23_S5_RX` | U1.PB23, U2.UART_TXD/GPIO1 | identisch |
| `RESET#` | R6.2, Q5.D | identisch |
| `RESETN` | U1.RESETN, R2.2, R3.2, R6.1, R5.1, C2.1 | identisch |
| `RESETN_TP` | R2.1 ⚠️ **nur 1 Anschluss** | = `N$4` |
| `RESET_BTN` | PB1.2, R3.1 | = `N17658775` |
| `RGB_KATH1` | DL4.RED_C, R34.2 | = `N$14` |
| `RGB_KATH2` | DL4.GREEN_C, R35.2 | = `N$16` |
| `RGB_KATH3` | DL4.BLUE_C, R36.2 | = `N$20` |
| `SD_CD` | U1.PB11 ⚠️ **nur 1 Anschluss** | = `PB11_TCC0-W5` |
| `SD_CS` | U1.PA07 ⚠️ **nur 1 Anschluss** | = `PA07_AIN7` |
| `SPI_MISO` | U1.PA19 ⚠️ **nur 1 Anschluss** | = `PA19_S1_MISO` |
| `SPI_MOSI` | U1.PA16 ⚠️ **nur 1 Anschluss** | = `PA16_S1_MOSI` |
| `SPI_SCK` | U1.PA17 ⚠️ **nur 1 Anschluss** | = `PA17_S1_SCK` |
| `USB_N` | U1.PA24/USB_DM ⚠️ **nur 1 Anschluss** | identisch |
| `USB_P` | U1.PA25/USB_DP ⚠️ **nur 1 Anschluss** | identisch |
| `VBAT` | R8.2 | = `VBATT` |
| `VDDANA_FILT` | U1.VDDANA, L3.2, C23.1, C27.1 | = `N17852357` |
| `VDDCORE_DEC` | U1.VDDCORE, C25.1 | = `N17852431` |

**Netze mit nur einem Anschluss auf MCU_Radio** (21): `EPD_BUSY`, `EPD_CS`, `EPD_DC`, `EPD_RST`, `IMU_INT`, `LED_ERR`, `LED_FIX`, `LED_REC`, `NINA_LPO`, `PA10_TCC0-W2`, `PA11_TCC0-W3`, `PB02_AIN10`, `PB03_AIN11`, `RESETN_TP`, `SD_CD`, `SD_CS`, `SPI_MISO`, `SPI_MOSI`, `SPI_SCK`, `USB_N`, `USB_P`

Das sind ungenutzte Pins (im Original gingen sie nur zu Steckverbindern, die wir weggelassen haben).
Sie sind **kein Fehler**, aber die ERC wird sie als „nicht verbunden“ melden — dort kannst du sie
mit einem No-Connect-Kreuz quittieren oder für spätere Erweiterungen offenlassen.

## Blatt: GPS

Bauteile auf diesem Blatt: **23**, Netze: **28**

| Netz | verbundene Bauteil-Pins | Quelle |
|---|---|---|
| `+3V3` | U3.VCC, U3.V_USB, C4.1, C5.2, C7.2, D2.A, R7.2, R8.2 | manuell (Neuentwurf, s.u.) |
| `D1_ANODE` | R11.1, D1.A | = `N$2` |
| `D3_ANODE` | R12.1, D3.A | = `N$1` |
| `D4_ANODE` | R13.1, D4.A | = `N$7` |
| `D_SEL` | U3.D_SEL ⚠️ **nur 1 Anschluss** | identisch |
| `GEO_LED_D` | R25.2, R13.2 | zusammengeführt: `FENCE_STAT`, `N$9` |
| `GND` | U3.GND, C4.2, C5.1, C7.1, C1.2, E1.GND, B1.-, C3.2, D1.C, D3.C, D4.C | identisch |
| `GPS_ANT_BIAS` | R14.1, FB1.2, C1.1 | = `ANT_VCC` |
| `GPS_GEO_STAT` | U3.GEO_STAT, R25.1 | = `N$20` |
| `GPS_PPS` | U3.TIMEPULSE, R21.1 | zusammengeführt: `N$21`, `PPS` |
| `GPS_RF` | U3.RF_IN, FB1.1, E1.SIGNAL | = `GPS_ANT1` |
| `GPS_RTK_STAT` | U3.RTK_STAT, R24.1 | = `N$19` |
| `GPS_TX2` | U3.TX2 ⚠️ **nur 1 Anschluss** | = `TX2_P` |
| `GPS_VBCKP` | U3.V_BKCP, B1.+, C3.1, R5.1 | = `BACKUP` |
| `I2C_SCL` | U3.SCL/CLK, R7.1 | manuell (Neuentwurf, s.u.) |
| `I2C_SDA` | U3.SDA/!CS!, R8.1 | manuell (Neuentwurf, s.u.) |
| `N$11` | U3.USB_D+ ⚠️ **nur 1 Anschluss** | identisch |
| `N$12` | U3.USB_D- ⚠️ **nur 1 Anschluss** | identisch |
| `N$13` | U3.V_RF, R14.2 | identisch |
| `N$14` | U3.RX2 ⚠️ **nur 1 Anschluss** | identisch |
| `N$15` | U3.EXTINT ⚠️ **nur 1 Anschluss** | identisch |
| `N$16` | U3.!RESET! ⚠️ **nur 1 Anschluss** | identisch |
| `N$18` | U3.!SAFEBOOT! ⚠️ **nur 1 Anschluss** | identisch |
| `N$6` | R5.2, D2.C | identisch |
| `PPS_LED_D` | R21.2, R11.2 | zusammengeführt: `N$4`, `PPS_STAT` |
| `RTK_LED_D` | R24.2, R12.2 | zusammengeführt: `N$3`, `RTK_STAT` |
| `RXLV` | U3.RX/MOSI ⚠️ **nur 1 Anschluss** | identisch |
| `TXLV` | U3.TX/MISO ⚠️ **nur 1 Anschluss** | identisch |

**Netze mit nur einem Anschluss auf GPS** (10): `D_SEL`, `GPS_TX2`, `N$11`, `N$12`, `N$14`, `N$15`, `N$16`, `N$18`, `RXLV`, `TXLV`

Das sind ungenutzte Pins (im Original gingen sie nur zu Steckverbindern, die wir weggelassen haben).
Sie sind **kein Fehler**, aber die ERC wird sie als „nicht verbunden“ melden — dort kannst du sie
mit einem No-Connect-Kreuz quittieren oder für spätere Erweiterungen offenlassen.

## Bewusst weggelassene Bauteile der Referenzdesigns

| Referenz | Bauteil | Warum weggelassen |
|---|---|---|
| MKR1010 | J2, J3, J4, J5 | MKR-Formfaktor-Steckleisten; wir verdrahten direkt statt über Header |
| MKR1010 | U4 (ECC508A) | Crypto-Chip laut deiner Entscheidung weggelassen (später als I2C-Chip nachrüstbar) |
| MKR1010 | R31, R32 | 0R-Jumper, die nur zur entfallenen Steckleiste J5 führten (tote Stummel) |
| MKR1010 | C28–C31 | im Original bereits als DNP (unbestückt) markiert |
| GPS-RTK | J5 (USB-C), U2 (LDO) | doppelt vorhanden — unser Board hat eigene USB-C-Buchse und eigene 3V3-Versorgung |
| GPS-RTK | J1–J4, J6, J7 | Qwiic-/Serial-/Debug-Stecker; nicht nötig bei Direktverdrahtung |
| GPS-RTK | R2,R3,R4,R6,R9,R10 | 33Ω-Serienwiderstände, die im Original nur zu diesen Steckern führten |
| GPS-RTK | E2 | zweite SMA-Buchse (externer Timepulse-Ausgang); du wolltest eine einzelne Antenne |
| GPS-RTK | D6 | ESD-Schutz für das entfallene eigene USB des SparkFun-Boards |
| GPS-RTK | Lötjumper PPS, PPS_LED, RTK, FENCE, JP5, PWR, SPI | siehe Warnung unten |

## ⚠️ Wichtig: korrigierter Fehler aus der Vorversion

In der vorherigen Version waren die drei GPS-Status-LEDs (PPS, RTK-Fix, Geofence) **elektrisch tot**.
Ursache: Im SparkFun-Original sitzen in jeder LED-Kette Lötjumper (standardmäßig geschlossene,
auftrennbare Kupferbrücken). Ich hatte diese Bauteile weggelassen — damit war die Kette an zwei
Stellen offen, das Signal vom ZED-F9P erreichte die LED nie.

Jetzt behoben: die Netze beidseits jedes entfernten Jumpers wurden zusammengeführt
(z. B. `PPS_STAT` + `N$4` → `PPS_LED_D`), was dem geschlossenen Jumper elektrisch entspricht.
**Bitte gegenprüfen:** ZED-F9P `TIMEPULSE` → R21 → R11 → D1 → GND (analog RTK_STAT→R24→R12→D3,
GEO_STAT→R25→R13→D4).

## Was noch offen ist

1. ~~**Sensors_Storage-Blatt** fehlt~~ ✓ erledigt — MPU-6050 (U7), MicroSD (J11), e-Paper-Stecker (J10), 3× Status-LEDs (DL10–12) vorhanden
2. ~~**SWD-Programmierheader** fehlt~~ ✓ erledigt — CONN_SWD_1x5 in MCU_Radio.kicad_sch
3. **USB-C-Footprint** ist noch Platzhalter (`TBD_USBC_CONNECTOR`) — braucht ein konkretes Bauteil
4. **Footprints zuweisen** — Großteil der Passiven (R, C, D, L) und einige Stecker haben noch kein Footprint im Schaltplan-Instanz
5. **ERC** in KiCad noch nicht gelaufen
6. **PCB-Layout**: erst nach ERC und vollständiger Footprint-Zuweisung sinnvoll

## Automatische Verbindungsprüfung

Prüft für jeden Bauteil-Pin: hat er im Original ein Netz — und ist dieses Netz im Schaltplan
auch tatsächlich zugeordnet? (Diese Prüfung deckte auf, dass alle LEDs und Dioden unverbunden
waren, weil meine Symbole `1`/`2` als Pad-Namen benutzten, die Quellen aber `A`/`C`.)

**Ergebnis: 0 Fehler.** Jeder Pin, der in der Quelle ein Netz hat, ist zugeordnet.

12 Pins sind ohne Netz — **auch im Original unbeschaltet**, also kein Fehler:

| Blatt | Bauteil | unbeschaltete Pins |
|---|---|---|
| GPS | U3 | ANT_DETECT, ANT_OFF, !ANT_SHORT!, TX_READY |
| MCU_Radio | U2 | ADC2/GPIO34, ADC3/GPIO39, ADC4/GPIO36, ANT, RMII_MDCLK/GPIO2, ADC34/GPI35 |
| Power | U5 | D+, D- |

Die ERC wird diese Pins als „nicht verbunden“ melden. Das ist erwartet — im KiCad-Schaltplan
kannst du sie mit einem No-Connect-Kreuz quittieren oder für Erweiterungen offenlassen.