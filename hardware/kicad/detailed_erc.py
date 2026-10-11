with open('alarm_clock_v1.kicad_sch', 'r', encoding='utf-8') as f:
    text = f.read()

import re
labels = re.findall(r'\(label\s+"([^"]+)"\s+\(at\s+([-\d.]+)\s+([-\d.]+)', text)
pwrs = re.findall(r'\(symbol\s+\(lib_id\s+"power:([^"]+)".*?\(at\s+([-\d.]+)\s+([-\d.]+)', text, re.DOTALL)

for name, x, y in labels:
    if 'BATT_NEG' in name:
        print(f"BATT_NEG label at ({x}, {y})")

for name, x, y in pwrs:
    print(f"PWR {name} at ({x}, {y})")

