import re

def get_pin_coords(sym_text):
    # Returns {pnum: (x, y, angle)}
    matches = re.findall(r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s*(\d*)\).*?\(number\s+"([^"]+)"', sym_text, re.DOTALL)
    res = {}
    for x, y, ang, num in matches:
        res[num] = (float(x), float(y), int(ang) if ang else 0)
    return res

with open(r"c:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\hardware\kicad\extract_lib_symbols.py", "r", encoding="utf-8") as f:
    pass

from extract_lib_symbols import get_sym_def, SYM_DIR, os

chips = [
    ("ESP32-WROOM-32E", os.path.join(SYM_DIR, "RF_Module.kicad_sym"), "ESP32-WROOM-32E"),
    ("TPS63000", os.path.join(SYM_DIR, "Regulator_Switching.kicad_sym"), "TPS63000"),
    ("DS3231M", os.path.join(SYM_DIR, "Timer_RTC.kicad_sym"), "DS3231M"),
    ("MAX98357A", os.path.join(SYM_DIR, "Audio.kicad_sym"), "MAX98357A"),
    ("CH340C", os.path.join(SYM_DIR, "Interface_USB.kicad_sym"), "CH340C"),
    ("TP4056-42-ESOP8", os.path.join(SYM_DIR, "Battery_Management.kicad_sym"), "TP4056-42-ESOP8"),
    ("DW01A", os.path.join(SYM_DIR, "Battery_Management.kicad_sym"), "DW01A"),
    ("USB_C_Receptacle_USB2.0_16P", os.path.join(SYM_DIR, "Connector.kicad_sym"), "USB_C_Receptacle_USB2.0_16P"),
    ("R", os.path.join(SYM_DIR, "Device.kicad_sym"), "R"),
    ("C", os.path.join(SYM_DIR, "Device.kicad_sym"), "C"),
    ("SW_Push", os.path.join(SYM_DIR, "Switch.kicad_sym"), "SW_Push"),
    ("Conn_01x02_Pin", os.path.join(SYM_DIR, "Connector.kicad_sym"), "Conn_01x02_Pin"),
    ("TestPoint", os.path.join(SYM_DIR, "Connector.kicad_sym"), "TestPoint"),
    ("+3V3", os.path.join(SYM_DIR, "power.kicad_sym"), "+3V3"),
    ("GND", os.path.join(SYM_DIR, "power.kicad_sym"), "GND"),
    ("PWR_FLAG", os.path.join(SYM_DIR, "power.kicad_sym"), "PWR_FLAG")
]

for name, path, sname in chips:
    s = get_sym_def(path, sname)
    coords = get_pin_coords(s)
    print(f"[{name}] pins: {coords}")
