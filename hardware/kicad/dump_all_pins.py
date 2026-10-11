import re

def print_pins(filepath, name):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    idx = text.find(f'(symbol "{name}"')
    end_idx = text.find('\n\t(symbol "', idx + 1)
    if end_idx == -1: end_idx = len(text)
    sym_text = text[idx:end_idx]
    pins = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at[^)]+\).*?\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"', sym_text, re.DOTALL)
    print(f"\n=== {name} ===")
    for ptype, pname, pnum in pins:
        print(f"Pin {pnum:>4}: {pname:<16} ({ptype})")

SYM_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
print_pins(SYM_DIR + r"\Regulator_Switching.kicad_sym", "TPS63001")
print_pins(SYM_DIR + r"\Audio.kicad_sym", "MAX98357A")
print_pins(SYM_DIR + r"\Battery_Management.kicad_sym", "TP4056-42-ESOP8")
print_pins(SYM_DIR + r"\Transistor_FET.kicad_sym", "AO3401A")
print_pins(SYM_DIR + r"\Transistor_BJT.kicad_sym", "MMBT3904")
print_pins(SYM_DIR + r"\Transistor_FET.kicad_sym", "Q_Dual_NMOS_G1S2G2D2S1D1")
print_pins(SYM_DIR + r"\Connector.kicad_sym", "USB_C_Receptacle_USB2.0_16P")
