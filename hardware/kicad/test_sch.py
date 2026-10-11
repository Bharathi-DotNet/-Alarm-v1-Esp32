import os

sch_template = '''(kicad_sch
	(version 20231120)
	(generator "kicad-cli")
	(generator_version "10.0")
	(uuid "91b452be-cf44-486f-a89e-26f59bf5bbcb")
	(paper "A3")
	(title_block
		(title "ESP32 Anti-Cheat Smart Alarm Clock")
		(date "2026-09-22")
		(rev "v1.0")
		(company "Production Hardware Design")
	)
)'''
test_path = r"c:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\hardware\kicad\test.kicad_sch"
with open(test_path, "w", encoding="utf-8") as f:
    f.write(sch_template)

print("Wrote test.kicad_sch")
