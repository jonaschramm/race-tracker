#!/usr/bin/env /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Print each footprint's real courtyard bounding box (width, height in mm,
centered on the footprint origin) so placement can use real geometry
instead of guessed sizes."""
import pcbnew

FP_ROOT = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

FOOTPRINTS = {
    "ESP32S3": "RF_Module:ESP32-S3-WROOM-1",
    "R0603": "Resistor_SMD:R_0603_1608Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "SW_TACT": "Button_Switch_SMD:SW_SPST_B3U-1000P",
    "SW_SLIDE": "Button_Switch_THT:SW_DIP_SPSTx01_Slide_6.7x4.1mm_W7.62mm_P2.54mm_LowProfile",
    "USBC": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "JST_PH2": "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
    "JST_SH4": "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
    "MICROSD": "Connector_Card:microSD_HC_Molex_104031-0811",
    "PINHDR4": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "SOT236": "Package_TO_SOT_SMD:SOT-23-6",
    "SOD882": "Diode_SMD:D_SOD-882",
    "LED0603": "LED_SMD:LED_0603_1608Metric",
    "SOT235": "Package_TO_SOT_SMD:SOT-23-5",
}

board = pcbnew.BOARD()
for key, fpid in FOOTPRINTS.items():
    lib_nick, fp_name = fpid.split(":", 1)
    fp = pcbnew.FootprintLoad(f"{FP_ROOT}/{lib_nick}.pretty", fp_name)
    if fp is None:
        print(f"{key:10s} MISSING {fpid}")
        continue
    board.Add(fp)
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    fp.SetOrientationDegrees(0)
    bb_all = fp.GetBoundingBox()
    bb_nt = fp.GetBoundingBox(False, False)
    w, h = pcbnew.ToMM(bb_all.GetWidth()), pcbnew.ToMM(bb_all.GetHeight())
    w2, h2 = pcbnew.ToMM(bb_nt.GetWidth()), pcbnew.ToMM(bb_nt.GetHeight())
    cx2, cy2 = pcbnew.ToMM(bb_nt.GetCenter().x), pcbnew.ToMM(bb_nt.GetCenter().y)
    print(f"{key:10s} with_text=({w:6.2f}x{h:5.2f}) no_text=({w2:6.2f}x{h2:5.2f}) "
          f"center=({cx2:.2f},{cy2:.2f})  {fpid}")
