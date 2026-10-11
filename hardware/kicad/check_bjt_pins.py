with open(r'C:\Program Files\KiCad\10.0\share\kicad\symbols\Transistor_BJT.kicad_sym', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('(symbol "MMBT3904"')
sym_chunk = text[idx:idx+2500]
pins = re.findall(r'\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"', sym_chunk, re.DOTALL)
print("MMBT3904 pins (name, number):", pins)
