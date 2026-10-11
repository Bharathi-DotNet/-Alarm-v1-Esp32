import sys
import traceback

try:
    import pcbnew
    print("1. pcbnew imported")
    
    board = pcbnew.BOARD()
    print("2. BOARD created")
    
    from parse_netlist import components, nets
    print(f"3. Netlist parsed: {len(components)} components, {len(nets)} nets")
    
    import generate_pcb
    print("4. generate_pcb imported")
    
    generate_pcb.create_board()
    print("5. Board created successfully")
except Exception as e:
    print("CAUGHT EXCEPTION:")
    traceback.print_exc()
    sys.exit(1)
