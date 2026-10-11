import pcbnew
import os
import traceback

fp_base = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
board = pcbnew.BOARD()
try:
    fp_str = "Battery:BatteryHolder_Keystone_1060_1x2032"
    lib, name = fp_str.split(":")
    lib_path = os.path.join(fp_base, lib + ".pretty")
    print("Loading from", lib_path, name)
    fp = pcbnew.FootprintLoad(lib_path, name)
    print("Loaded:", fp)
    fp.SetReference("BT1")
    print("Ref set")
    fp.SetValue("CR2032")
    print("Value set")
    x, y, ang = 87.5, 82.0, 0
    fp.SetPosition(pcbnew.VECTOR2I(int(x*1e6), int(y*1e6)))
    print("Position set")
    fp.SetOrientation(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
    print("Orientation set")
    fp.SetLayerAndFlip(pcbnew.B_Cu)
    print("SetLayerAndFlip done")
    board.Add(fp)
    print("board.Add done")
except Exception as e:
    traceback.print_exc()
