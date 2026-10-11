import os
import uuid
import re
import subprocess

def u():
    return str(uuid.uuid4())

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

def get_pin_info(sym_text):
    # Returns {pnum: (px, py, angle, ptype, pname)}
    matches = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s*(\d*)\).*?\(name\s+"([^"]*)".*?\(number\s+"([^"]+)"', sym_text, re.DOTALL)
    res = {}
    for ptype, x, y, ang, name, num in matches:
        res[num] = (float(x), float(y), int(ang) if ang else 0, ptype, name)
    return res

# Collect all symbols needed
symbols_spec = [
    ("RF_Module:ESP32-WROOM-32E", os.path.join(SYM_DIR, "RF_Module.kicad_sym"), "ESP32-WROOM-32E"),
    ("Regulator_Switching:TPS63000", os.path.join(SYM_DIR, "Regulator_Switching.kicad_sym"), "TPS63000"),
    ("Timer_RTC:DS3231M", os.path.join(SYM_DIR, "Timer_RTC.kicad_sym"), "DS3231M"),
    ("Audio:MAX98357A", os.path.join(SYM_DIR, "Audio.kicad_sym"), "MAX98357A"),
    ("Interface_USB:CH340C", os.path.join(SYM_DIR, "Interface_USB.kicad_sym"), "CH340C"),
    ("Battery_Management:TP4056-42-ESOP8", os.path.join(SYM_DIR, "Battery_Management.kicad_sym"), "TP4056-42-ESOP8"),
    ("Battery_Management:DW01A", os.path.join(SYM_DIR, "Battery_Management.kicad_sym"), "DW01A"),
    ("Transistor_FET:TP0610T", os.path.join(SYM_DIR, "Transistor_FET.kicad_sym"), "TP0610T"),
    ("Transistor_BJT:Q_NPN_BEC", os.path.join(SYM_DIR, "Transistor_BJT.kicad_sym"), "Q_NPN_BEC"),
    ("Transistor_FET:Q_Dual_NMOS_G1S2G2D2S1D1", os.path.join(SYM_DIR, "Transistor_FET.kicad_sym"), "Q_Dual_NMOS_G1S2G2D2S1D1"),
    ("Connector:USB_C_Receptacle_USB2.0_16P", os.path.join(SYM_DIR, "Connector.kicad_sym"), "USB_C_Receptacle_USB2.0_16P"),
    ("Power_Protection:USBLC6-2P6", os.path.join(SYM_DIR, "Power_Protection.kicad_sym"), "USBLC6-2P6"),
    ("Device:R", os.path.join(SYM_DIR, "Device.kicad_sym"), "R"),
    ("Device:C", os.path.join(SYM_DIR, "Device.kicad_sym"), "C"),
    ("Device:C_Polarized", os.path.join(SYM_DIR, "Device.kicad_sym"), "C_Polarized"),
    ("Device:L", os.path.join(SYM_DIR, "Device.kicad_sym"), "L"),
    ("Device:D_Schottky", os.path.join(SYM_DIR, "Device.kicad_sym"), "D_Schottky"),
    ("Device:LED", os.path.join(SYM_DIR, "Device.kicad_sym"), "LED"),
    ("Device:Polyfuse", os.path.join(SYM_DIR, "Device.kicad_sym"), "Polyfuse"),
    ("Device:FerriteBead", os.path.join(SYM_DIR, "Device.kicad_sym"), "FerriteBead"),
    ("Switch:SW_Push", os.path.join(SYM_DIR, "Switch.kicad_sym"), "SW_Push"),
    ("Connector:Conn_01x02_Pin", os.path.join(SYM_DIR, "Connector.kicad_sym"), "Conn_01x02_Pin"),
    ("Device:Battery_Cell", os.path.join(SYM_DIR, "Device.kicad_sym"), "Battery_Cell"),
    ("Connector:TestPoint", os.path.join(SYM_DIR, "Connector.kicad_sym"), "TestPoint"),
    ("power:+3V3", os.path.join(SYM_DIR, "power.kicad_sym"), "+3V3"),
    ("power:GND", os.path.join(SYM_DIR, "power.kicad_sym"), "GND"),
    ("power:PWR_FLAG", os.path.join(SYM_DIR, "power.kicad_sym"), "PWR_FLAG")
]

# Build lib_symbols
lib_defs = {}
raw_pins = {}
lib_symbols_s = "\t(lib_symbols\n"
for full_id, fpath, sname in symbols_spec:
    s_raw = get_sym_def(fpath, sname)
    # rename root symbol to full_id
    s_renamed = s_raw.replace(f'(symbol "{sname}"', f'(symbol "{full_id}"', 1)
    # For MAX98357A, make exposed pad pin 17 passive (same as pins 11 and 15) to prevent unspecified-power_in warning
    if "MAX98357A" in sname:
        s_renamed = s_renamed.replace('(pin unspecified line\n\t\t\t\t(at 2.54 -12.7 90)\n\t\t\t\t(length 2.54)\n\t\t\t\t(name "PAD"',
                                      '(pin passive line\n\t\t\t\t(at 2.54 -12.7 90)\n\t\t\t\t(length 2.54)\n\t\t\t\t(name "PAD"')
    lib_defs[full_id] = s_renamed
    raw_pins[full_id] = get_pin_info(s_renamed)
    lib_symbols_s += "\t\t" + s_renamed + "\n"
lib_symbols_s += "\t)\n"

print(f"Loaded {len(symbols_spec)} symbols, lib_symbols block size: {len(lib_symbols_s)} chars")
