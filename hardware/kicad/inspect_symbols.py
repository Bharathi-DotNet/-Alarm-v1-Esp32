import re

def inspect(filepath, sym_name):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    idx = text.find(f'(symbol "{sym_name}"')
    if idx == -1:
        print(f"Symbol {sym_name} not found in {filepath}")
        return
    count = 0
    end_idx = len(text)
    for i in range(idx, len(text)):
        if text[i] == '(':
            count += 1
        elif text[i] == ')':
            count -= 1
            if count == 0:
                end_idx = i + 1
                break
    sym_chunk = text[idx:end_idx]
    print(f"=== {sym_name} ===")
    matches = re.findall(r'\(pin\s+(\w+)\s+(\w+)\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s*(\d*)\).*?\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"', sym_chunk, re.DOTALL)
    for ptype, pshape, px, py, pang, pname, pnum in matches:
        print(f"Pin {pnum:>4}: {pname:<10} ({ptype}) at ({px}, {py}, {pang})")

SYM_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
inspect(SYM_DIR + r"\Power_Protection.kicad_sym", "USBLC6-2P6")
with open(SYM_DIR + r"\Device.kicad_sym", 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find('(symbol "C_Polarized"')
print(text[idx+1000:idx+2500])
inspect(SYM_DIR + r"\Transistor_FET.kicad_sym", "AO3401A")
inspect(SYM_DIR + r"\Transistor_BJT.kicad_sym", "Q_NPN_BEC")


