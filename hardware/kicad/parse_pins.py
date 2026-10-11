import re
import os

def get_pins(sym_file, sym_name):
    with open(sym_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find symbol block
    idx = content.find(f'(symbol "{sym_name}"')
    if idx == -1:
        print(f"Symbol {sym_name} not found in {sym_file}")
        return
    end_idx = content.find('\n\t(symbol "', idx + 1)
    if end_idx == -1:
        end_idx = len(content)
    sym_text = content[idx:end_idx]
    pins = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at[^)]+\).*?\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"', sym_text, re.DOTALL)
    print(f"\n=== {sym_name} ===")
    for ptype, name, num in pins:
        print(f"Pin {num:>2}: {name:<16} ({ptype})")

base = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
get_pins(os.path.join(base, "RF_Module.kicad_sym"), "ESP32-WROOM-32E")
get_pins(os.path.join(base, "Regulator_Switching.kicad_sym"), "TPS63001DRC")
get_pins(os.path.join(base, "Timer_RTC.kicad_sym"), "DS3231SN")
get_pins(os.path.join(base, "Audio.kicad_sym"), "MAX98357AETE")
get_pins(os.path.join(base, "Interface_USB.kicad_sym"), "CH340C")
get_pins(os.path.join(base, "Battery_Management.kicad_sym"), "TP4056")
get_pins(os.path.join(base, "Battery_Management.kicad_sym"), "DW01A")
get_pins(os.path.join(base, "Transistor_FET.kicad_sym"), "AO3401A")
get_pins(os.path.join(base, "Power_Protection.kicad_sym"), "USBLC6-2SC6")
