import re

def print_all(filepath, name):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    pattern = rf'\(symbol\s+"{name}"(.*?)(?=\n\t\(symbol|\n\)$)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        pins = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at[^)]+\).*?\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"', match.group(1), re.DOTALL)
        print(f"\n=== {name} ===")
        for ptype, pname, pnum in pins:
            print(f"Pin {pnum:>4}: {pname:<16} ({ptype})")
    else:
        print(f"Not matched: {name}")

SYM_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
print_all(SYM_DIR + r"\Regulator_Switching.kicad_sym", "TPS63000")
print_all(SYM_DIR + r"\Transistor_FET.kicad_sym", "AO3401A")
print_all(SYM_DIR + r"\Transistor_BJT.kicad_sym", "MMBT3904")
print_all(SYM_DIR + r"\Timer_RTC.kicad_sym", "DS3231M")
