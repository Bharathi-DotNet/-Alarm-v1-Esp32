import pcbnew
import os

board = pcbnew.BOARD()
net = pcbnew.NETINFO_ITEM(board, "+3V3")
board.Add(net)

fp_dir = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
res_lib = os.path.join(fp_dir, "Resistor_SMD.pretty")
fp = pcbnew.FootprintLoad(res_lib, "R_0603_1608Metric")
board.Add(fp)
fp.SetReference("R1")
fp.SetValue("10k")

# Assign net to pad 1
pad1 = fp.FindPadByNumber("1")
if pad1:
    pad1.SetNet(net)
    print(f"Pad 1 net: {pad1.GetNetname()}")

output_pcb = "test_board.kicad_pcb"
pcbnew.SaveBoard(output_pcb, board)
print("Saved test_board.kicad_pcb successfully")
