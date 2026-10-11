import os

def check_footprint(lib_name, fp_pattern):
    path = os.path.join(r"C:\Program Files\KiCad\10.0\share\kicad\footprints", lib_name)
    if not os.path.exists(path):
        print(f"Lib {lib_name} not found")
        return
    matches = [f for f in os.listdir(path) if fp_pattern.lower() in f.lower()]
    print(f"[{lib_name}] {fp_pattern}: {matches[:5]}")

check_footprint("Package_DFN_QFN.pretty", "QFN-16-1EP_3x3mm")
check_footprint("Package_SON.pretty", "VSON-10_3x3mm")
check_footprint("Package_SO.pretty", "SOIC-16W")
check_footprint("Package_SO.pretty", "SOIC-16_")
check_footprint("Package_SO.pretty", "SOIC-8")
check_footprint("Package_TO_SOT_SMD.pretty", "SOT-23-6")
check_footprint("Package_TO_SOT_SMD.pretty", "SOT-23")
check_footprint("Connector_USB.pretty", "USB_C_Receptacle_HRO_TYPE-C-31-M-12")
check_footprint("Connector_JST.pretty", "JST_PH_B2B-PH-K_1x02")
import re
fp_path = r"C:\Program Files\KiCad\10.0\share\kicad\footprints\Button_Switch_SMD.pretty\SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm.kicad_mod"
if os.path.exists(fp_path):
    with open(fp_path, 'r', encoding='utf-8') as f:
        pads = set(re.findall(r'\(pad\s+"([^"]+)"', f.read()))
        print("Pads in 6x6 switch:", sorted(pads))

