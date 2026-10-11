import os
import uuid
import re
import subprocess
from test_gen_init import lib_symbols_s, raw_pins

def u(): return str(uuid.uuid4())

def snap(val, step=2.54):
    return round(round(val / step) * step, 2)

class PerfectSchematicEngine:
    def __init__(self, title="ESP32 Anti-Cheat Smart Alarm Clock", rev="v1.0"):
        self.sheet_uuid = u()
        self.title = title
        self.rev = rev
        self.symbols = []
        self.wires = []
        self.labels = []
        self.no_connects = []
        self.texts = []

    def add_sym(self, lib_id, ref, val, footprint, x, y, rot=0, unit=1):
        x = snap(x)
        y = snap(y)
        sym_uuid = u()
        pins_dict = raw_pins[lib_id]
        
        if lib_id == "Transistor_FET:Q_Dual_NMOS_G1S2G2D2S1D1":
            target_pins = ['1', '5', '6'] if unit == 1 else ['3', '2', '4']
        else:
            target_pins = list(pins_dict.keys())

        pin_uuids = {pnum: u() for pnum in target_pins}
        pin_world = {}
        for pnum in target_pins:
            px, py, pang, ptype, pname = pins_dict[pnum]
            if rot == 0:
                dx, dy = px, -py
            elif rot == 90:
                dx, dy = -py, -px
            elif rot == 180:
                dx, dy = -px, py
            elif rot == 270:
                dx, dy = py, px
            else:
                raise ValueError(f"Invalid rot {rot}")
            pin_world[pnum] = (round(x + dx, 2), round(y + dy, 2))

        sym_obj = {
            "lib_id": lib_id,
            "ref": ref,
            "val": val,
            "footprint": footprint,
            "x": x,
            "y": y,
            "rot": rot,
            "unit": unit,
            "uuid": sym_uuid,
            "pin_uuids": pin_uuids,
            "pin_world": pin_world,
            "is_pwr": False
        }
        self.symbols.append(sym_obj)
        return sym_obj

    def add_pwr(self, lib_id, val, x, y, rot=0):
        x = round(x, 2)
        y = round(y, 2)
        sym_uuid = u()
        pins_dict = raw_pins[lib_id]
        pin_uuids = {pnum: u() for pnum in pins_dict.keys()}
        pin_world = {pnum: (x, y) for pnum in pins_dict.keys()}
        self.pwr_idx = getattr(self, "pwr_idx", 0) + 1
        ref = f"#PWR{self.pwr_idx:02d}" if "PWR_FLAG" not in lib_id else f"#FLG{self.pwr_idx:02d}"
        sym_obj = {
            "lib_id": lib_id,
            "ref": ref,
            "val": val,
            "footprint": "",
            "x": x,
            "y": y,
            "rot": rot,
            "unit": 1,
            "uuid": sym_uuid,
            "pin_uuids": pin_uuids,
            "pin_world": pin_world,
            "is_pwr": True
        }
        self.symbols.append(sym_obj)
        return sym_obj

    def add_label(self, name, x, y, rot=0):
        self.labels.append({
            "name": name,
            "x": round(x, 2),
            "y": round(y, 2),
            "rot": rot,
            "uuid": u()
        })

    def add_wire(self, x1, y1, x2, y2):
        self.wires.append({
            "x1": round(x1, 2),
            "y1": round(y1, 2),
            "x2": round(x2, 2),
            "y2": round(y2, 2),
            "uuid": u()
        })

    def add_nc(self, x, y):
        self.no_connects.append({
            "x": round(x, 2),
            "y": round(y, 2),
            "uuid": u()
        })

    def add_text(self, text, x, y, size=2.54):
        self.texts.append({
            "text": text,
            "x": snap(x),
            "y": snap(y),
            "size": size,
            "uuid": u()
        })

    def connect_pin(self, sym, pin_num, net_name):
        px, py = sym["pin_world"][pin_num]
        if net_name == "GND":
            self.add_pwr("power:GND", "GND", px, py)
        elif net_name == "+3V3":
            self.add_pwr("power:+3V3", "+3V3", px, py)
        else:
            self.add_label(net_name, px, py)

    def nc_pin(self, sym, pin_num):
        px, py = sym["pin_world"][pin_num]
        self.add_nc(px, py)

    def export(self):
        lines = [
            "(kicad_sch",
            "\t(version 20231120)",
            '\t(generator "kicad-cli")',
            '\t(generator_version "10.0")',
            f'\t(uuid "{self.sheet_uuid}")',
            '\t(paper "A3")',
            "\t(title_block",
            f'\t\t(title "{self.title}")',
            '\t\t(date "2026-09-22")',
            f'\t\t(rev "{self.rev}")',
            '\t\t(company "Production Hardware Design")',
            "\t)",
            lib_symbols_s
        ]

        for t in self.texts:
            lines.append(f'\t(text "{t["text"]}" (at {t["x"]:.2f} {t["y"]:.2f} 0) (effects (font (size {t["size"]:.2f} {t["size"]:.2f}) (bold yes))) (uuid "{t["uuid"]}"))')

        for s in self.symbols:
            is_pwr = s.get("is_pwr", False)
            hide_fp = ' (hide yes)' if s['footprint'] == "" or not is_pwr else ''
            ref_hide = ' (hide yes)' if is_pwr else ''
            lines.append('\t(symbol')
            lines.append(f'\t\t(lib_id "{s["lib_id"]}")')
            lines.append(f'\t\t(at {s["x"]:.2f} {s["y"]:.2f} {s["rot"]})')
            lines.append(f'\t\t(unit {s["unit"]})')
            lines.append('\t\t(exclude_from_sim no)')
            lines.append('\t\t(in_bom no)' if is_pwr else '\t\t(in_bom yes)')
            lines.append('\t\t(on_board yes)')
            lines.append('\t\t(dnp no)')
            lines.append(f'\t\t(uuid "{s["uuid"]}")')
            lines.append(f'\t\t(property "Reference" "{s["ref"]}" (at {s["x"]:.2f} {s["y"] - 2.54:.2f} 0) (effects (font (size 1.27 1.27)){ref_hide}))')
            lines.append(f'\t\t(property "Value" "{s["val"]}" (at {s["x"]:.2f} {s["y"] + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
            lines.append(f'\t\t(property "Footprint" "{s["footprint"]}" (at {s["x"]:.2f} {s["y"]:.2f} 0) (effects (font (size 1.27 1.27)){hide_fp}))')
            for pnum, pid in s["pin_uuids"].items():
                lines.append(f'\t\t(pin "{pnum}" (uuid "{pid}"))')
            lines.append('\t\t(instances')
            lines.append('\t\t\t(project "alarm_clock_v1"')
            lines.append(f'\t\t\t\t(path "/{self.sheet_uuid}/{s["uuid"]}"')
            lines.append(f'\t\t\t\t\t(reference "{s["ref"]}")')
            lines.append(f'\t\t\t\t\t(unit {s["unit"]})')
            lines.append('\t\t\t\t)')
            lines.append('\t\t\t)')
            lines.append('\t\t)')
            lines.append('\t)')

        for w in self.wires:
            lines.append(f'\t(wire (pts (xy {w["x1"]:.2f} {w["y1"]:.2f}) (xy {w["x2"]:.2f} {w["y2"]:.2f})) (stroke (width 0) (type default)) (uuid "{w["uuid"]}"))')

        for lb in self.labels:
            lines.append(f'\t(label "{lb["name"]}" (at {lb["x"]:.2f} {lb["y"]:.2f} {lb["rot"]}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{lb["uuid"]}"))')

        for nc in self.no_connects:
            lines.append(f'\t(no_connect (at {nc["x"]:.2f} {nc["y"]:.2f}) (uuid "{nc["uuid"]}"))')

        lines.append(")")
        return "\n".join(lines)

def build_alarm_clock():
    gen = PerfectSchematicEngine()

    # Section Headers
    gen.add_text("1. USB-C INPUT & ESD PROTECTION", 30, 25)
    gen.add_text("2. LI-ION CHARGER & BATTERY PROTECTION", 130, 25)
    gen.add_text("3. POWER-PATH (LOAD SHARING)", 235, 25)
    gen.add_text("4. 3.3V BUCK-BOOST REGULATOR (TPS63001)", 315, 25)

    gen.add_text("5. USB-TO-UART INTERFACE & AUTO-DOWNLOAD", 30, 115)
    gen.add_text("6. MAIN MCU (ESP32-WROOM-32E)", 150, 115)
    gen.add_text("7. REAL-TIME CLOCK (DS3231M & CR2032)", 310, 115)

    gen.add_text("8. I2S AUDIO AMPLIFIER (MAX98357A)", 30, 215)
    gen.add_text("9. WAKE BUTTON & USER CONTROLS", 185, 215)
    gen.add_text("10. TEST POINTS & POWER FLAGS", 295, 215)

    # =========================================================================
    # 1. USB-C RECEPTACLE & ESD PROTECTION
    # =========================================================================
    j1 = gen.add_sym("Connector:USB_C_Receptacle_USB2.0_16P", "J1", "USB_C_16P",
                     "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 50, 60, rot=0)
    for p in ["A4", "A9", "B4", "B9"]:
        gen.connect_pin(j1, p, "VBUS_RAW")
    for p in ["A1", "A12", "B1", "B12", "SH"]:
        gen.connect_pin(j1, p, "GND")
    gen.connect_pin(j1, "A5", "USB_CC1")
    gen.connect_pin(j1, "B5", "USB_CC2")
    gen.connect_pin(j1, "A6", "USB_DP_CON")
    gen.connect_pin(j1, "B6", "USB_DP_CON")
    gen.connect_pin(j1, "A7", "USB_DM_CON")
    gen.connect_pin(j1, "B7", "USB_DM_CON")
    gen.nc_pin(j1, "A8")
    gen.nc_pin(j1, "B8")

    r1 = gen.add_sym("Device:R", "R1", "5.1k (CC1)", "Resistor_SMD:R_0603_1608Metric", 75, 45, rot=0)
    gen.connect_pin(r1, "1", "USB_CC1")
    gen.connect_pin(r1, "2", "GND")

    r2 = gen.add_sym("Device:R", "R2", "5.1k (CC2)", "Resistor_SMD:R_0603_1608Metric", 85, 45, rot=0)
    gen.connect_pin(r2, "1", "USB_CC2")
    gen.connect_pin(r2, "2", "GND")

    f1 = gen.add_sym("Device:Polyfuse", "F1", "500mA PTC", "Fuse:Fuse_1812_4532Metric", 75, 70, rot=90)
    gen.connect_pin(f1, "1", "VBUS_RAW")
    gen.connect_pin(f1, "2", "VBUS")

    u9 = gen.add_sym("Power_Protection:USBLC6-2P6", "U9", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", 100, 60, rot=0)
    gen.connect_pin(u9, "1", "USB_DM_CON")
    gen.connect_pin(u9, "2", "GND")
    gen.connect_pin(u9, "3", "USB_DP_CON")
    gen.connect_pin(u9, "4", "USB_DP")
    gen.connect_pin(u9, "5", "VBUS")
    gen.connect_pin(u9, "6", "USB_DM")

    c1 = gen.add_sym("Device:C", "C1", "10uF", "Capacitor_SMD:C_0805_2012Metric", 115, 45, rot=0)
    gen.connect_pin(c1, "1", "VBUS")
    gen.connect_pin(c1, "2", "GND")

    c2 = gen.add_sym("Device:C", "C2", "100nF", "Capacitor_SMD:C_0603_1608Metric", 122, 45, rot=0)
    gen.connect_pin(c2, "1", "VBUS")
    gen.connect_pin(c2, "2", "GND")

    # =========================================================================
    # 2. LI-ION CHARGER & BATTERY PROTECTION
    # =========================================================================
    u3 = gen.add_sym("Battery_Management:TP4056-42-ESOP8", "U3", "TP4056",
                     "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm_ThermalVias", 155, 60, rot=0)
    gen.connect_pin(u3, "1", "GND") # TEMP to GND
    gen.connect_pin(u3, "2", "NET_PROG")
    gen.connect_pin(u3, "3", "GND")
    gen.connect_pin(u3, "4", "VBUS")
    gen.connect_pin(u3, "5", "VBAT_PROT")
    gen.connect_pin(u3, "6", "NET_STDBY")
    gen.connect_pin(u3, "7", "NET_CHRG")
    gen.connect_pin(u3, "8", "VBUS")
    gen.connect_pin(u3, "9", "GND")

    r3 = gen.add_sym("Device:R", "R3", "4.7k (255mA)", "Resistor_SMD:R_0603_1608Metric", 175, 75, rot=0)
    gen.connect_pin(r3, "1", "NET_PROG")
    gen.connect_pin(r3, "2", "GND")

    r4 = gen.add_sym("Device:R", "R4", "1k", "Resistor_SMD:R_0603_1608Metric", 140, 95, rot=0)
    gen.connect_pin(r4, "1", "VBUS")
    gen.connect_pin(r4, "2", "NET_LED_CHRG_A")

    d2 = gen.add_sym("Device:LED", "D2", "RED (CHRG)", "LED_SMD:LED_0603_1608Metric", 150, 95, rot=90)
    gen.connect_pin(d2, "2", "NET_LED_CHRG_A")
    gen.connect_pin(d2, "1", "NET_CHRG")

    r5 = gen.add_sym("Device:R", "R5", "1k", "Resistor_SMD:R_0603_1608Metric", 165, 95, rot=0)
    gen.connect_pin(r5, "1", "VBUS")
    gen.connect_pin(r5, "2", "NET_LED_STDBY_A")

    d3 = gen.add_sym("Device:LED", "D3", "GRN (FULL)", "LED_SMD:LED_0603_1608Metric", 175, 95, rot=90)
    gen.connect_pin(d3, "2", "NET_LED_STDBY_A")
    gen.connect_pin(d3, "1", "NET_STDBY")

    j2 = gen.add_sym("Connector:Conn_01x02_Pin", "J2", "JST_PH_BATT",
                     "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", 195, 45, rot=0)
    gen.connect_pin(j2, "1", "VBAT_PROT")
    gen.connect_pin(j2, "2", "BATT_NEG")

    c3 = gen.add_sym("Device:C", "C3", "10uF", "Capacitor_SMD:C_0805_2012Metric", 175, 45, rot=0)
    gen.connect_pin(c3, "1", "VBAT_PROT")
    gen.connect_pin(c3, "2", "GND")

    u4 = gen.add_sym("Battery_Management:DW01A", "U4", "DW01A", "Package_TO_SOT_SMD:SOT-23-6", 195, 75, rot=0)
    gen.connect_pin(u4, "1", "GATE_OD")
    gen.connect_pin(u4, "2", "NET_DW_CS")
    gen.connect_pin(u4, "3", "GATE_OC")
    gen.connect_pin(u4, "5", "NET_DW_VCC")
    gen.connect_pin(u4, "6", "BATT_NEG")

    r6 = gen.add_sym("Device:R", "R6", "100R", "Resistor_SMD:R_0603_1608Metric", 215, 65, rot=90)
    gen.connect_pin(r6, "1", "NET_DW_VCC")
    gen.connect_pin(r6, "2", "VBAT_PROT")

    c4 = gen.add_sym("Device:C", "C4", "100nF", "Capacitor_SMD:C_0603_1608Metric", 215, 80, rot=0)
    gen.connect_pin(c4, "1", "NET_DW_VCC")
    gen.connect_pin(c4, "2", "GND")

    r7 = gen.add_sym("Device:R", "R7", "1k", "Resistor_SMD:R_0603_1608Metric", 205, 95, rot=90)
    gen.connect_pin(r7, "1", "NET_DW_CS")
    gen.connect_pin(r7, "2", "GND")

    c5 = gen.add_sym("Device:C", "C5", "100nF", "Capacitor_SMD:C_0603_1608Metric", 195, 95, rot=0)
    gen.connect_pin(c5, "1", "NET_DW_CS")
    gen.connect_pin(c5, "2", "BATT_NEG")

    u5a = gen.add_sym("Transistor_FET:Q_Dual_NMOS_G1S2G2D2S1D1", "U5", "FS8205A",
                      "Package_SO:TSSOP-8_4.4x3mm_P0.65mm", 225, 40, rot=0, unit=1)
    gen.connect_pin(u5a, "1", "GATE_OC")
    gen.connect_pin(u5a, "5", "BATT_NEG")
    gen.connect_pin(u5a, "6", "NET_FS_DRAIN")

    u5b = gen.add_sym("Transistor_FET:Q_Dual_NMOS_G1S2G2D2S1D1", "U5", "FS8205A",
                      "Package_SO:TSSOP-8_4.4x3mm_P0.65mm", 225, 55, rot=0, unit=2)
    gen.connect_pin(u5b, "3", "GATE_OD")
    gen.connect_pin(u5b, "2", "GND")
    gen.connect_pin(u5b, "4", "NET_FS_DRAIN")

    # =========================================================================
    # 3. POWER-PATH (LOAD SHARING)
    # =========================================================================
    q1 = gen.add_sym("Transistor_FET:TP0610T", "Q1", "AO3401A", "Package_TO_SOT_SMD:SOT-23", 265, 50, rot=0)
    gen.connect_pin(q1, "1", "VBUS")
    gen.connect_pin(q1, "2", "VSYS")
    gen.connect_pin(q1, "3", "VBAT_PROT")

    r8 = gen.add_sym("Device:R", "R8", "100k (Gate PD)", "Resistor_SMD:R_0603_1608Metric", 255, 75, rot=0)
    gen.connect_pin(r8, "1", "VBUS")
    gen.connect_pin(r8, "2", "GND")

    d1 = gen.add_sym("Device:D_Schottky", "D1", "SS34 (3A/40V)", "Diode_SMD:D_SOD-123", 275, 50, rot=90)
    gen.connect_pin(d1, "2", "VBUS")
    gen.connect_pin(d1, "1", "VSYS")

    c6 = gen.add_sym("Device:C", "C6", "22uF", "Capacitor_SMD:C_0805_2012Metric", 285, 75, rot=0)
    gen.connect_pin(c6, "1", "VSYS")
    gen.connect_pin(c6, "2", "GND")

    # =========================================================================
    # 4. 3.3V BUCK-BOOST REGULATOR (TPS63001)
    # =========================================================================
    u2 = gen.add_sym("Regulator_Switching:TPS63000", "U2", "TPS63001",
                     "Package_SON:Texas_DRC0010J_ThermalVias", 355, 60, rot=0)
    gen.connect_pin(u2, "1", "+3V3")
    gen.connect_pin(u2, "2", "NET_TPS_L2")
    gen.connect_pin(u2, "3", "GND")
    gen.connect_pin(u2, "4", "NET_TPS_L1")
    gen.connect_pin(u2, "5", "VSYS")
    gen.connect_pin(u2, "6", "VSYS")
    gen.connect_pin(u2, "7", "GND") # PS/SYNC
    gen.connect_pin(u2, "8", "VSYS")
    gen.connect_pin(u2, "9", "GND")
    gen.connect_pin(u2, "10", "+3V3")
    gen.connect_pin(u2, "11", "GND")

    l1 = gen.add_sym("Device:L", "L1", "2.2uH (2.5A)", "Inductor_SMD:L_1210_3225Metric", 340, 45, rot=90)
    gen.connect_pin(l1, "1", "NET_TPS_L1")
    gen.connect_pin(l1, "2", "NET_TPS_L2")

    c7 = gen.add_sym("Device:C", "C7", "10uF", "Capacitor_SMD:C_0805_2012Metric", 325, 75, rot=0)
    gen.connect_pin(c7, "1", "VSYS")
    gen.connect_pin(c7, "2", "GND")

    c8 = gen.add_sym("Device:C", "C8", "100nF", "Capacitor_SMD:C_0603_1608Metric", 335, 75, rot=0)
    gen.connect_pin(c8, "1", "VSYS")
    gen.connect_pin(c8, "2", "GND")

    c9 = gen.add_sym("Device:C", "C9", "10uF", "Capacitor_SMD:C_0805_2012Metric", 380, 50, rot=0)
    gen.connect_pin(c9, "1", "+3V3")
    gen.connect_pin(c9, "2", "GND")

    c10 = gen.add_sym("Device:C", "C10", "10uF", "Capacitor_SMD:C_0805_2012Metric", 390, 50, rot=0)
    gen.connect_pin(c10, "1", "+3V3")
    gen.connect_pin(c10, "2", "GND")

    c11 = gen.add_sym("Device:C", "C11", "100nF", "Capacitor_SMD:C_0603_1608Metric", 400, 50, rot=0)
    gen.connect_pin(c11, "1", "+3V3")
    gen.connect_pin(c11, "2", "GND")

    # =========================================================================
    # 5. USB-TO-UART INTERFACE & AUTO-DOWNLOAD (CH340C)
    # =========================================================================
    u8 = gen.add_sym("Interface_USB:CH340C", "U8", "CH340C", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", 60, 150, rot=0)
    gen.connect_pin(u8, "1", "GND")
    gen.connect_pin(u8, "2", "UART_TX_CH340")
    gen.connect_pin(u8, "3", "UART_RX_CH340")
    gen.connect_pin(u8, "4", "NET_CH340_V3")
    gen.connect_pin(u8, "5", "USB_DP")
    gen.connect_pin(u8, "6", "USB_DM")
    gen.nc_pin(u8, "9")
    gen.nc_pin(u8, "10")
    gen.nc_pin(u8, "11")
    gen.nc_pin(u8, "12")
    gen.connect_pin(u8, "13", "DTR")
    gen.connect_pin(u8, "14", "RTS")
    gen.nc_pin(u8, "15")
    gen.connect_pin(u8, "16", "VBUS")

    c12 = gen.add_sym("Device:C", "C12", "100nF", "Capacitor_SMD:C_0603_1608Metric", 40, 135, rot=0)
    gen.connect_pin(c12, "1", "VBUS")
    gen.connect_pin(c12, "2", "GND")

    c13 = gen.add_sym("Device:C", "C13", "100nF", "Capacitor_SMD:C_0603_1608Metric", 40, 165, rot=0)
    gen.connect_pin(c13, "1", "NET_CH340_V3")
    gen.connect_pin(c13, "2", "GND")

    r9 = gen.add_sym("Device:R", "R9", "1k", "Resistor_SMD:R_0603_1608Metric", 90, 140, rot=90)
    gen.connect_pin(r9, "1", "UART_TX_CH340")
    gen.connect_pin(r9, "2", "ESP_RXD0")

    r10 = gen.add_sym("Device:R", "R10", "1k", "Resistor_SMD:R_0603_1608Metric", 90, 150, rot=90)
    gen.connect_pin(r10, "1", "UART_RX_CH340")
    gen.connect_pin(r10, "2", "ESP_TXD0")

    q2 = gen.add_sym("Transistor_BJT:Q_NPN_BEC", "Q2", "MMBT3904", "Package_TO_SOT_SMD:SOT-23", 115, 145, rot=0)
    gen.connect_pin(q2, "1", "NET_Q2_BASE")
    gen.connect_pin(q2, "2", "RTS")
    gen.connect_pin(q2, "3", "ESP_EN")

    r11 = gen.add_sym("Device:R", "R11", "10k", "Resistor_SMD:R_0603_1608Metric", 105, 145, rot=90)
    gen.connect_pin(r11, "1", "DTR")
    gen.connect_pin(r11, "2", "NET_Q2_BASE")

    q3 = gen.add_sym("Transistor_BJT:Q_NPN_BEC", "Q3", "MMBT3904", "Package_TO_SOT_SMD:SOT-23", 115, 165, rot=0)
    gen.connect_pin(q3, "1", "NET_Q3_BASE")
    gen.connect_pin(q3, "2", "DTR")
    gen.connect_pin(q3, "3", "ESP_IO0")

    r12 = gen.add_sym("Device:R", "R12", "10k", "Resistor_SMD:R_0603_1608Metric", 105, 165, rot=90)
    gen.connect_pin(r12, "1", "RTS")
    gen.connect_pin(r12, "2", "NET_Q3_BASE")

    # =========================================================================
    # 6. MAIN MCU (ESP32-WROOM-32E)
    # =========================================================================
    u1 = gen.add_sym("RF_Module:ESP32-WROOM-32E", "U1", "ESP32-WROOM-32E", "RF_Module:ESP32-WROOM-32E", 220, 160, rot=0)
    gen.connect_pin(u1, "2", "+3V3")
    gen.connect_pin(u1, "3", "ESP_EN")
    gen.nc_pin(u1, "4")
    gen.nc_pin(u1, "5")
    gen.nc_pin(u1, "6")
    gen.nc_pin(u1, "7")
    gen.connect_pin(u1, "8", "WAKE_BTN")  # GPIO32
    gen.connect_pin(u1, "9", "RTC_INT")   # GPIO33
    gen.nc_pin(u1, "10")
    gen.nc_pin(u1, "11")
    gen.connect_pin(u1, "12", "AMP_SD")   # GPIO27
    gen.nc_pin(u1, "13")
    gen.nc_pin(u1, "14")
    gen.nc_pin(u1, "16")
    gen.nc_pin(u1, "17")
    gen.nc_pin(u1, "18")
    gen.nc_pin(u1, "19")
    gen.nc_pin(u1, "20")
    gen.nc_pin(u1, "21")
    gen.nc_pin(u1, "22")
    gen.nc_pin(u1, "23")
    gen.nc_pin(u1, "24")
    gen.connect_pin(u1, "25", "ESP_IO0")  # GPIO0
    gen.nc_pin(u1, "26")
    gen.nc_pin(u1, "27")
    gen.nc_pin(u1, "28")
    gen.nc_pin(u1, "29")
    gen.connect_pin(u1, "30", "I2S_BCLK") # GPIO18
    gen.connect_pin(u1, "31", "I2S_LRC")  # GPIO19
    gen.nc_pin(u1, "32")
    gen.connect_pin(u1, "33", "I2C_SDA")  # GPIO21
    gen.connect_pin(u1, "34", "ESP_RXD0") # RXD0
    gen.connect_pin(u1, "35", "ESP_TXD0") # TXD0
    gen.connect_pin(u1, "36", "I2C_SCL")  # GPIO22
    gen.connect_pin(u1, "37", "I2S_DIN")  # GPIO23
    gen.connect_pin(u1, "[1,15,38,39]", "GND")

    c14 = gen.add_sym("Device:C", "C14", "10uF", "Capacitor_SMD:C_0805_2012Metric", 200, 120, rot=0)
    gen.connect_pin(c14, "1", "+3V3")
    gen.connect_pin(c14, "2", "GND")

    c15 = gen.add_sym("Device:C", "C15", "100nF", "Capacitor_SMD:C_0603_1608Metric", 210, 120, rot=0)
    gen.connect_pin(c15, "1", "+3V3")
    gen.connect_pin(c15, "2", "GND")

    r13 = gen.add_sym("Device:R", "R13", "10k (EN Pullup)", "Resistor_SMD:R_0603_1608Metric", 185, 135, rot=0)
    gen.connect_pin(r13, "1", "+3V3")
    gen.connect_pin(r13, "2", "ESP_EN")

    c16 = gen.add_sym("Device:C", "C16", "1uF (POR Delay)", "Capacitor_SMD:C_0603_1608Metric", 185, 150, rot=0)
    gen.connect_pin(c16, "1", "ESP_EN")
    gen.connect_pin(c16, "2", "GND")

    sw1 = gen.add_sym("Switch:SW_Push", "SW1", "RESET",
                      "Button_Switch_SMD:SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm", 185, 170, rot=90)
    gen.connect_pin(sw1, "1", "ESP_EN")
    gen.connect_pin(sw1, "2", "GND")

    r14 = gen.add_sym("Device:R", "R14", "10k (BOOT Pullup)", "Resistor_SMD:R_0603_1608Metric", 255, 135, rot=0)
    gen.connect_pin(r14, "1", "+3V3")
    gen.connect_pin(r14, "2", "ESP_IO0")

    sw2 = gen.add_sym("Switch:SW_Push", "SW2", "BOOT",
                      "Button_Switch_SMD:SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm", 255, 160, rot=90)
    gen.connect_pin(sw2, "1", "ESP_IO0")
    gen.connect_pin(sw2, "2", "GND")

    # =========================================================================
    # 7. REAL-TIME CLOCK (DS3231M & CR2032)
    # =========================================================================
    u7 = gen.add_sym("Timer_RTC:DS3231M", "U7", "DS3231M", "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm", 345, 160, rot=0)
    gen.nc_pin(u7, "1")
    gen.connect_pin(u7, "2", "+3V3")
    gen.connect_pin(u7, "3", "RTC_INT")
    gen.nc_pin(u7, "4")
    for p in ["5", "6", "7", "8", "9", "10", "11", "12", "13"]:
        gen.connect_pin(u7, p, "GND")
    gen.connect_pin(u7, "14", "NET_CR2032")
    gen.connect_pin(u7, "15", "I2C_SDA")
    gen.connect_pin(u7, "16", "I2C_SCL")

    c17 = gen.add_sym("Device:C", "C17", "100nF", "Capacitor_SMD:C_0603_1608Metric", 325, 140, rot=0)
    gen.connect_pin(c17, "1", "+3V3")
    gen.connect_pin(c17, "2", "GND")

    bt1 = gen.add_sym("Device:Battery_Cell", "BT1", "CR2032 (3V)", "Battery:BatteryHolder_Keystone_1060_1x2032", 380, 140, rot=0)
    gen.connect_pin(bt1, "1", "NET_CR2032")
    gen.connect_pin(bt1, "2", "GND")

    c18 = gen.add_sym("Device:C", "C18", "100nF", "Capacitor_SMD:C_0603_1608Metric", 395, 140, rot=0)
    gen.connect_pin(c18, "1", "NET_CR2032")
    gen.connect_pin(c18, "2", "GND")

    r15 = gen.add_sym("Device:R", "R15", "4.7k", "Resistor_SMD:R_0603_1608Metric", 325, 180, rot=0)
    gen.connect_pin(r15, "1", "+3V3")
    gen.connect_pin(r15, "2", "I2C_SDA")

    r16 = gen.add_sym("Device:R", "R16", "4.7k", "Resistor_SMD:R_0603_1608Metric", 335, 180, rot=0)
    gen.connect_pin(r16, "1", "+3V3")
    gen.connect_pin(r16, "2", "I2C_SCL")

    r17 = gen.add_sym("Device:R", "R17", "10k", "Resistor_SMD:R_0603_1608Metric", 345, 180, rot=0)
    gen.connect_pin(r17, "1", "+3V3")
    gen.connect_pin(r17, "2", "RTC_INT")

    # =========================================================================
    # 8. I2S AUDIO AMPLIFIER (MAX98357A)
    # =========================================================================
    u6 = gen.add_sym("Audio:MAX98357A", "U6", "MAX98357A",
                     "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm", 75, 250, rot=0)
    gen.connect_pin(u6, "1", "I2S_DIN")
    gen.connect_pin(u6, "2", "NET_GAIN")
    gen.connect_pin(u6, "3", "GND")
    gen.connect_pin(u6, "4", "AMP_SD")
    gen.connect_pin(u6, "7", "VSYS")
    gen.connect_pin(u6, "8", "VSYS")
    gen.connect_pin(u6, "9", "NET_SPK_P_FILT")
    gen.connect_pin(u6, "10", "NET_SPK_N_FILT")
    gen.connect_pin(u6, "11", "GND")
    gen.connect_pin(u6, "14", "I2S_LRC")
    gen.connect_pin(u6, "15", "GND")
    gen.connect_pin(u6, "16", "I2S_BCLK")
    gen.connect_pin(u6, "17", "GND")

    r18 = gen.add_sym("Device:R", "R18", "100k (12dB Gain)", "Resistor_SMD:R_0603_1608Metric", 50, 265, rot=0)
    gen.connect_pin(r18, "1", "NET_GAIN")
    gen.connect_pin(r18, "2", "GND")

    r19 = gen.add_sym("Device:R", "R19", "100k (SD Pull-Down)", "Resistor_SMD:R_0603_1608Metric", 60, 265, rot=0)
    gen.connect_pin(r19, "1", "AMP_SD")
    gen.connect_pin(r19, "2", "GND")

    c19 = gen.add_sym("Device:C_Polarized", "C19", "220uF Low-ESR",
                      "Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D", 50, 235, rot=0)
    gen.connect_pin(c19, "1", "VSYS")
    gen.connect_pin(c19, "2", "GND")

    c20 = gen.add_sym("Device:C", "C20", "10uF", "Capacitor_SMD:C_0805_2012Metric", 62, 235, rot=0)
    gen.connect_pin(c20, "1", "VSYS")
    gen.connect_pin(c20, "2", "GND")

    c21 = gen.add_sym("Device:C", "C21", "100nF", "Capacitor_SMD:C_0603_1608Metric", 72, 235, rot=0)
    gen.connect_pin(c21, "1", "VSYS")
    gen.connect_pin(c21, "2", "GND")

    fb1 = gen.add_sym("Device:FerriteBead", "FB1", "220R@100MHz", "Inductor_SMD:L_0603_1608Metric", 105, 245, rot=90)
    gen.connect_pin(fb1, "1", "NET_SPK_P_FILT")
    gen.connect_pin(fb1, "2", "SPK_P")

    fb2 = gen.add_sym("Device:FerriteBead", "FB2", "220R@100MHz", "Inductor_SMD:L_0603_1608Metric", 105, 255, rot=90)
    gen.connect_pin(fb2, "1", "NET_SPK_N_FILT")
    gen.connect_pin(fb2, "2", "SPK_N")

    c22 = gen.add_sym("Device:C", "C22", "100pF", "Capacitor_SMD:C_0603_1608Metric", 115, 240, rot=0)
    gen.connect_pin(c22, "1", "SPK_P")
    gen.connect_pin(c22, "2", "GND")

    c23 = gen.add_sym("Device:C", "C23", "100pF", "Capacitor_SMD:C_0603_1608Metric", 115, 260, rot=0)
    gen.connect_pin(c23, "1", "SPK_N")
    gen.connect_pin(c23, "2", "GND")

    j3 = gen.add_sym("Connector:Conn_01x02_Pin", "J3", "Speaker_4R_3W",
                     "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", 130, 250, rot=0)
    gen.connect_pin(j3, "1", "SPK_P")
    gen.connect_pin(j3, "2", "SPK_N")

    # =========================================================================
    # 9. USER WAKE BUTTON
    # =========================================================================
    sw3 = gen.add_sym("Switch:SW_Push", "SW3", "WAKE_BTN",
                      "Button_Switch_SMD:SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm", 215, 250, rot=90)
    gen.connect_pin(sw3, "1", "WAKE_BTN")
    gen.connect_pin(sw3, "2", "GND")

    r20 = gen.add_sym("Device:R", "R20", "10k (WAKE Pullup)", "Resistor_SMD:R_0603_1608Metric", 230, 240, rot=0)
    gen.connect_pin(r20, "1", "+3V3")
    gen.connect_pin(r20, "2", "WAKE_BTN")

    c24 = gen.add_sym("Device:C", "C24", "100nF (Debounce)", "Capacitor_SMD:C_0603_1608Metric", 230, 260, rot=0)
    gen.connect_pin(c24, "1", "WAKE_BTN")
    gen.connect_pin(c24, "2", "GND")

    # =========================================================================
    # 10. TEST POINTS & POWER FLAGS
    # =========================================================================
    tps = [
        ("TP1", "VBUS", 305, 235),
        ("TP2", "VBAT_PROT", 320, 235),
        ("TP3", "VSYS", 335, 235),
        ("TP4", "+3V3", 350, 235),
        ("TP5", "GND", 365, 235),
        ("TP6", "ESP_EN", 305, 265),
        ("TP7", "ESP_IO0", 320, 265),
        ("TP8", "RTC_INT", 335, 265),
        ("TP9", "WAKE_BTN", 350, 265),
        ("TP10", "AMP_SD", 365, 265)
    ]
    for ref, net, x, y in tps:
        tp = gen.add_sym("Connector:TestPoint", ref, net, "TestPoint:TestPoint_Pad_D1.0mm", x, y, rot=0)
        gen.connect_pin(tp, "1", net)

    # Power Flags
    pwr_flags = [
        ("VBUS", 385, 225),
        ("VSYS", 385, 235),
        ("GND", 385, 245),
        ("NET_CR2032", 385, 255),
        ("NET_DW_VCC", 385, 265),
        ("BATT_NEG", 385, 275)
    ]
    for net, x, y in pwr_flags:
        pf = gen.add_sym("power:PWR_FLAG", "#FLG?", "PWR_FLAG", "", x, y, rot=0)
        gen.connect_pin(pf, "1", net)

    output_path = r"c:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\hardware\kicad\alarm_clock_v1.kicad_sch"
    content = gen.export()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated perfect schematic at: {output_path}")
    return output_path

if __name__ == "__main__":
    sch_file = build_alarm_clock()
    print("\nRunning KiCad Electrical Rules Check (ERC)...")
    res = subprocess.run([r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", "sch", "erc", sch_file], capture_output=True, text=True)
    print("Return code:", res.returncode)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
