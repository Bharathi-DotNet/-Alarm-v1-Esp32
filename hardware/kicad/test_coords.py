import uuid

def u():
    return str(uuid.uuid4())

# Let's test resistor R at (100, 100).
# R in Device.kicad_sym:
# Pin 1 is at (0, 3.81, 270)
# Pin 2 is at (0, -3.81, 90)
# If placed at (100, 100, 0):
# Where are Pin 1 and Pin 2?
# In KiCad schematics:
# If Y is inverted: pin 1 is at (100, 100 - 3.81) = (100, 96.19)
# Let's test with a label or wire at (100, 96.19) and (100, 103.81)!

from test_lib_symbols import lib_symbols_content

def test_sch_coords(y1_offset, y2_offset):
    p1_uuid = u()
    p2_uuid = u()
    sch = f'''(kicad_sch
\t(version 20231120)
\t(generator "kicad-cli")
\t(generator_version "10.0")
\t(uuid "{u()}")
\t(paper "A4")
{lib_symbols_content}
\t(symbol
\t\t(lib_id "R")
\t\t(at 100.00 100.00 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{u()}")
\t\t(property "Reference" "R1"
\t\t\t(at 102.00 99.00 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "10k"
\t\t\t(at 102.00 101.00 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Resistor_SMD:R_0603_1608Metric"
\t\t\t(at 100.00 100.00 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pins
\t\t\t(pin "1" (uuid "{p1_uuid}"))
\t\t\t(pin "2" (uuid "{p2_uuid}"))
\t\t)
\t)
\t(label "NET1"
\t\t(at 100.00 {100.0 + y1_offset:.2f} 0)
\t\t(fields_autoplaced yes)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{u()}")
\t)
\t(label "NET2"
\t\t(at 100.00 {100.0 + y2_offset:.2f} 0)
\t\t(fields_autoplaced yes)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{u()}")
\t)
)'''
    with open("test_coords.kicad_sch", "w", encoding="utf-8") as f:
        f.write(sch)

test_sch_coords(-3.81, 3.81)
print("Wrote test_coords.kicad_sch with -3.81 and +3.81")
