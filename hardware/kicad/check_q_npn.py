import re

def get_pins_from_def(sym_text):
    return re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at[^)]+\).*?\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"', sym_text, re.DOTALL)

with open(r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym", 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('(symbol "Q_NPN"')
end_idx = text.find('\n\t(symbol "', idx + 1)
sym_text = text[idx:end_idx]
print(get_pins_from_def(sym_text))
