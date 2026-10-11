with open(r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym", 'r', encoding='utf-8') as f:
    text = f.read()

import re
npns = re.findall(r'\(symbol "(Q_NPN[^"]*)"', text)
print(npns)
