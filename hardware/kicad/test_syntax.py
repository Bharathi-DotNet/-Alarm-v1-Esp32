import uuid
import subprocess

def u():
    return str(uuid.uuid4())

sheet_uuid = u()
r1_uuid = u()
p1_uuid = u()
p2_uuid = u()

# Let's extract symbol R from Device.kicad_sym and name it "Device:R"
from extract_lib_symbols import get_sym_def, SYM_DIR, os

r_def = get_sym_def(os.path.join(SYM_DIR, "Device.kicad_sym"), "R")
# rename (symbol "R" to (symbol "Device:R"
r_def = r_def.replace('(symbol "R"', '(symbol "Device:R"', 1)

sch_text = f'''(kicad_sch
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
\t\t(at 100 100 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{r1_uuid}")
\t\t(property "Reference" "R1"
\t\t\t(at 102 99 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "10k"
\t\t\t(at 102 101 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Resistor_SMD:R_0603_1608Metric"
\t\t\t(at 100 100 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1"
\t\t\t(uuid "{p1_uuid}")
\t\t)
\t\t(pin "2"
\t\t\t(uuid "{p2_uuid}")
\t\t)
\t\t(instances
\t\t\t(project "alarm_clock_v1"
\t\t\t\t(path "/{sheet_uuid}/{r1_uuid}"
\t\t\t\t\t(reference "R1")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
\t(label "NET1"
\t\t(at 100 96.19 0)
\t\t(fields_autoplaced yes)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{u()}")
\t)
\t(label "NET2"
\t\t(at 100 103.81 0)
\t\t(fields_autoplaced yes)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{u()}")
\t)
)'''

with open("test_syntax.kicad_sch", "w", encoding="utf-8") as f:
    f.write(sch_text)

print("Saved test_syntax.kicad_sch, running kicad-cli sch erc...")
res = subprocess.run([r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", "sch", "erc", "test_syntax.kicad_sch"], capture_output=True, text=True)
print("Return code:", res.returncode)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
