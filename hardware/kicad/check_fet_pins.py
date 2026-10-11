with open(r'C:\Program Files\KiCad\10.0\share\kicad\symbols\Transistor_FET.kicad_sym', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('(symbol "TP0610T_1_1"')
sym_chunk = text[idx:idx+1500]
pins = re.findall(r'\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"', sym_chunk, re.DOTALL)
print("P-MOSFET pins (name, number):", pins)
