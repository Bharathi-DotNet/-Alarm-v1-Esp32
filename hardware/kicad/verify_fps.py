import pcbnew
import os
from parse_netlist import components

fp_base = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"

missing = []
for ref, d in components.items():
    fp_str = d["footprint"]
    lib, name = fp_str.split(":")
    lib_path = os.path.join(fp_base, lib + ".pretty")
    fp = pcbnew.FootprintLoad(lib_path, name)
    if not fp:
        missing.append((ref, fp_str))

if missing:
    print(f"Missing {len(missing)} footprints: {missing}")
else:
    print(f"All {len(components)} footprints loaded successfully from KiCad libraries!")
