import re
from test_gen_init import lib_defs

for k, text in lib_defs.items():
    sub_syms = re.findall(r'\(symbol\s+"([^"]+)"', text)
    units = set()
    for s in sub_syms:
        m = re.search(r'_(\d+)_\d+$', s)
        if m:
            units.add(int(m.group(1)))
    if len(units) > 1:
        print(f"{k} has {len(units)} units: {units}")
