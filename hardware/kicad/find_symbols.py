import os, re

base = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
targets = ["TPS6300", "DS3231", "MAX98357", "TP4056", "AO3401", "USB_C"]

for fname in os.listdir(base):
    if not fname.endswith(".kicad_sym"): continue
    fpath = os.path.join(base, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()
    for t in targets:
        matches = re.findall(rf'\(symbol\s+"([^"]*{t}[^"]*)"', text, re.IGNORECASE)
        if matches:
            for m in matches:
                print(f"[{fname}] -> {m}")
