import os
import uuid
import re

SYM_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"

def get_sym_def(filepath, name):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    idx = text.find(f'(symbol "{name}"')
    if idx == -1:
        raise ValueError(f"Symbol {name} not found in {filepath}")
    count = 0
    for i in range(idx, len(text)):
        if text[i] == '(':
            count += 1
        elif text[i] == ')':
            count -= 1
            if count == 0:
                return text[idx:i+1]
    raise ValueError(f"Could not extract {name}")

symbols_to_load = [
    ("ESP32-WROOM-32E", os.path.join(SYM_DIR, "RF_Module.kicad_sym"), "ESP32-WROOM-32E"),
    ("TPS63000", os.path.join(SYM_DIR, "Regulator_Switching.kicad_sym"), "TPS63000"),
    ("DS3231M", os.path.join(SYM_DIR, "Timer_RTC.kicad_sym"), "DS3231M"),
    ("MAX98357A", os.path.join(SYM_DIR, "Audio.kicad_sym"), "MAX98357A"),
    ("CH340C", os.path.join(SYM_DIR, "Interface_USB.kicad_sym"), "CH340C"),
    ("TP4056-42-ESOP8", os.path.join(SYM_DIR, "Battery_Management.kicad_sym"), "TP4056-42-ESOP8"),
    ("DW01A", os.path.join(SYM_DIR, "Battery_Management.kicad_sym"), "DW01A"),
    ("TP0610T", os.path.join(SYM_DIR, "Transistor_FET.kicad_sym"), "TP0610T"),
    ("Q_NPN_BEC", os.path.join(SYM_DIR, "Transistor_BJT.kicad_sym"), "Q_NPN_BEC"),
    ("Q_Dual_NMOS_G1S2G2D2S1D1", os.path.join(SYM_DIR, "Transistor_FET.kicad_sym"), "Q_Dual_NMOS_G1S2G2D2S1D1"),
    ("USB_C_Receptacle_USB2.0_16P", os.path.join(SYM_DIR, "Connector.kicad_sym"), "USB_C_Receptacle_USB2.0_16P"),
    ("USBLC6-2P6", os.path.join(SYM_DIR, "Power_Protection.kicad_sym"), "USBLC6-2P6"),
    ("R", os.path.join(SYM_DIR, "Device.kicad_sym"), "R"),
    ("C", os.path.join(SYM_DIR, "Device.kicad_sym"), "C"),
    ("C_Polarized", os.path.join(SYM_DIR, "Device.kicad_sym"), "C_Polarized"),
    ("L", os.path.join(SYM_DIR, "Device.kicad_sym"), "L"),
    ("D_Schottky", os.path.join(SYM_DIR, "Device.kicad_sym"), "D_Schottky"),
    ("LED", os.path.join(SYM_DIR, "Device.kicad_sym"), "LED"),
    ("SW_Push", os.path.join(SYM_DIR, "Switch.kicad_sym"), "SW_Push"),
    ("Conn_01x02_Pin", os.path.join(SYM_DIR, "Connector.kicad_sym"), "Conn_01x02_Pin"),
    ("Battery_Cell", os.path.join(SYM_DIR, "Device.kicad_sym"), "Battery_Cell"),
    ("TestPoint", os.path.join(SYM_DIR, "Connector.kicad_sym"), "TestPoint"),
    ("+3V3", os.path.join(SYM_DIR, "power.kicad_sym"), "+3V3"),
    ("GND", os.path.join(SYM_DIR, "power.kicad_sym"), "GND"),
    ("PWR_FLAG", os.path.join(SYM_DIR, "power.kicad_sym"), "PWR_FLAG")
]

lib_symbols_content = "\t(lib_symbols\n"
for key, fpath, sname in symbols_to_load:
    s_def = get_sym_def(fpath, sname)
    lib_symbols_content += "\t\t" + s_def + "\n"
lib_symbols_content += "\t)\n"

test_sch = f'''(kicad_sch
\t(version 20231120)
\t(generator "kicad-cli")
\t(generator_version "10.0")
\t(uuid "{uuid.uuid4()}")
\t(paper "A3")
\t(title_block
\t\t(title "ESP32 Smart Alarm Clock")
\t\t(date "2026-09-22")
\t\t(rev "v1.0")
\t)
{lib_symbols_content}
)'''

with open("test_lib.kicad_sch", "w", encoding="utf-8") as f:
    f.write(test_sch)

print("Saved test_lib.kicad_sch, testing with kicad-cli sch erc...")
