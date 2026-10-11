import re

with open(r'C:\Program Files\KiCad\10.0\share\kicad\demos\cm5_minima\Ethernet.kicad_sch', 'r', encoding='utf-8') as f:
    text = f.read()

# find a symbol definition
m = re.search(r'\n\t\(symbol\s+\(lib_id.*?\n\t\)', text, re.DOTALL)
if m:
    print("Found symbol instance:")
    print(m.group(0))
else:
    print("No symbol instance found")
