import pcbnew

board = pcbnew.BOARD()
netinfo = board.GetNetInfo()

# Add a net
net = pcbnew.NETINFO_ITEM(board, "GND")
board.Add(net)
print(f"Added net GND, netcode: {net.GetNetCode()}")

# Check finding net
found_net = board.FindNet("GND")
print("Found net:", found_net.GetNetname() if found_net else "None")
