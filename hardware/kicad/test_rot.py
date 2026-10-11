import uuid
import subprocess
from extract_lib_symbols import get_sym_def, SYM_DIR, os

def u(): return str(uuid.uuid4())

r_def = get_sym_def(os.path.join(SYM_DIR, "Device.kicad_sym"), "R")
r_def = r_def.replace('(symbol "R"', '(symbol "Device:R"', 1)

# R has pin 1 at (0, 3.81), pin 2 at (0, -3.81)
# At angle 90 (horizontal resistor):
# Pin 1 should be at (-3.81, 0) or (3.81, 0)?
# Let's test with test_rot.kicad_sch!

for ang in [90, 180, 270]:
    sheet_uuid = u()
    r1_uuid = u()
    sch = f'''(kicad_sch
\t(version 20231120)
\t(generator "kicad-cli")
\t(generator_version "10.0")
\t(uuid "{sheet_uuid}")
\t(paper "A4")
\t(lib_symbols
\t\t{r_def}
\t)
\t(symbol
\t\t(lib_id "Device:R")
\t\t(at 127 127 {ang})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{r1_uuid}")
\t\t(property "Reference" "R1" (at 127 127 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "10k" (at 127 127 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 127 127 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t(pin "1" (uuid "{u()}"))
\t\t(pin "2" (uuid "{u()}"))
\t\t(instances (project "alarm_clock_v1" (path "/{sheet_uuid}/{r1_uuid}" (reference "R1") (unit 1))))
\t)
)'''
    with open("test_rot.kicad_sch", "w", encoding="utf-8") as f:
        f.write(sch)
    subprocess.run([r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", "sch", "erc", "test_rot.kicad_sch"], capture_output=True, text=True)
    with open("test_rot-erc.rpt", "r", encoding="utf-8") as f:
        rpt = f.read()
    for line in rpt.splitlines():
        if "Symbol R1 Pin" in line:
            print(f"Angle {ang}: {line.strip()}")
