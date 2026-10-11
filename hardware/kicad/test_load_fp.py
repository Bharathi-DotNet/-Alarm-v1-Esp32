import pcbnew
import os

fp_dir = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"

# Test loading an ESP32 footprint
rf_lib = os.path.join(fp_dir, "RF_Module.pretty")
fp = pcbnew.FootprintLoad(rf_lib, "ESP32-WROOM-32E")
if fp:
    print(f"Loaded footprint: {fp.GetReference()} / {fp.GetValue()}")
    print("Pad count:", len(fp.Pads()))
else:
    print("Failed to load footprint")
