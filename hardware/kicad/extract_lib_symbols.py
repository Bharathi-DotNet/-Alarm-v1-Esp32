import os
import uuid
import re

def u():
    return str(uuid.uuid4())

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

# Standard KiCad library paths
SYM_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"

symbols_needed = {
    "ESP32-WROOM-32E": (os.path.join(SYM_DIR, "RF_Module.kicad_sym"), "ESP32-WROOM-32E"),
    "TPS63001": (os.path.join(SYM_DIR, "Regulator_Switching.kicad_sym"), "TPS63001"),
    "DS3231M": (os.path.join(SYM_DIR, "Timer_RTC.kicad_sym"), "DS3231M"),
    "MAX98357A": (os.path.join(SYM_DIR, "Audio.kicad_sym"), "MAX98357A"),
    "CH340C": (os.path.join(SYM_DIR, "Interface_USB.kicad_sym"), "CH340C"),
    "TP4056-42-ESOP8": (os.path.join(SYM_DIR, "Battery_Management.kicad_sym"), "TP4056-42-ESOP8"),
    "DW01A": (os.path.join(SYM_DIR, "Battery_Management.kicad_sym"), "DW01A"),
    "AO3401A": (os.path.join(SYM_DIR, "Transistor_FET.kicad_sym"), "AO3401A"),
    "MMBT3904": (os.path.join(SYM_DIR, "Transistor_BJT.kicad_sym"), "MMBT3904"),
    "Q_Dual_NMOS_G1S2G2D2S1D1": (os.path.join(SYM_DIR, "Transistor_FET.kicad_sym"), "Q_Dual_NMOS_G1S2G2D2S1D1"),
    "USB_C_Receptacle_USB2.0_16P": (os.path.join(SYM_DIR, "Connector.kicad_sym"), "USB_C_Receptacle_USB2.0_16P"),
    "R": (os.path.join(SYM_DIR, "Device.kicad_sym"), "R"),
    "C": (os.path.join(SYM_DIR, "Device.kicad_sym"), "C"),
    "C_Polarized": (os.path.join(SYM_DIR, "Device.kicad_sym"), "C_Polarized"),
    "L": (os.path.join(SYM_DIR, "Device.kicad_sym"), "L"),
    "D_Schottky": (os.path.join(SYM_DIR, "Device.kicad_sym"), "D_Schottky"),
    "LED": (os.path.join(SYM_DIR, "Device.kicad_sym"), "LED"),
    "SW_Push": (os.path.join(SYM_DIR, "Switch.kicad_sym"), "SW_Push"),
    "Conn_01x02_Pin": (os.path.join(SYM_DIR, "Connector.kicad_sym"), "Conn_01x02_Pin"),
    "Battery_Cell": (os.path.join(SYM_DIR, "Device.kicad_sym"), "Battery_Cell"),
    "TestPoint": (os.path.join(SYM_DIR, "Connector.kicad_sym"), "TestPoint"),
    "+3V3": (os.path.join(SYM_DIR, "power.kicad_sym"), "+3V3"),
    "GND": (os.path.join(SYM_DIR, "power.kicad_sym"), "GND"),
    "PWR_FLAG": (os.path.join(SYM_DIR, "power.kicad_sym"), "PWR_FLAG")
}

lib_symbols_str = "\t(lib_symbols\n"
for key, (fpath, sym_name) in symbols_needed.items():
    s_def = get_sym_def(fpath, sym_name)
    # in lib_symbols, rename root symbol to key (e.g. (symbol "ESP32-WROOM-32E" ...)
    lib_symbols_str += "\t\t" + s_def + "\n"
lib_symbols_str += "\t)\n"

print("Extracted all symbol definitions successfully!")
print(f"Total symbol block size: {len(lib_symbols_str)} chars")
