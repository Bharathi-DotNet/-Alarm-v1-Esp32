import pcbnew
import os
import math
import re
import subprocess
from parse_netlist import components, nets

def mm_to_iu(mm):
    return int(round(mm * 1e6))

def iu_to_mm(iu):
    return iu / 1e6

def create_board():
    print("create_board: starting...")
    board = pcbnew.BOARD()
    fp_base = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"

    # Set Title Block
    tb = board.GetTitleBlock()
    tb.SetTitle("ESP32 Anti-Cheat Smart Alarm Clock")
    tb.SetCompany("Production Hardware Design")
    tb.SetRevision("v1.0")
    tb.SetDate("2026-09-22")
    print("create_board: title block set")

    # 1. Setup Nets
    net_map = {}
    for netname in nets.keys():
        net = pcbnew.NETINFO_ITEM(board, netname)
        board.Add(net)
        net_map[netname] = net
    print(f"create_board: {len(net_map)} nets added")

    # 2. Board Dimensions (75mm x 60mm)
    bx0, by0 = 50.0, 50.0
    bw, bh = 75.0, 60.0
    bx1, by1 = bx0 + bw, by0 + bh
    r = 3.0

    def add_edge_line(x1, y1, x2, y2):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm_to_iu(0.15))
        seg.SetStart(pcbnew.VECTOR2I(mm_to_iu(x1), mm_to_iu(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(mm_to_iu(x2), mm_to_iu(y2)))
        board.Add(seg)

    def add_edge_arc(cx, cy, sx, sy, ex, ey):
        arc = pcbnew.PCB_SHAPE(board)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        arc.SetLayer(pcbnew.Edge_Cuts)
        arc.SetWidth(mm_to_iu(0.15))
        arc.SetCenter(pcbnew.VECTOR2I(mm_to_iu(cx), mm_to_iu(cy)))
        arc.SetStart(pcbnew.VECTOR2I(mm_to_iu(sx), mm_to_iu(sy)))
        arc.SetEnd(pcbnew.VECTOR2I(mm_to_iu(ex), mm_to_iu(ey)))
        board.Add(arc)

    add_edge_line(bx0 + r, by0, bx1 - r, by0)
    add_edge_line(bx1, by0 + r, bx1, by1 - r)
    add_edge_line(bx1 - r, by1, bx0 + r, by1)
    add_edge_line(bx0, by1 - r, bx0, by0 + r)

    add_edge_arc(bx1 - r, by0 + r, bx1 - r, by0, bx1, by0 + r)
    add_edge_arc(bx1 - r, by1 - r, bx1, by1 - r, bx1 - r, by1)
    add_edge_arc(bx0 + r, by1 - r, bx1 - r, by1, bx0, by1 - r)
    add_edge_arc(bx0 + r, by0 + r, bx0, by0 + r, bx0 + r, by0)
    print("create_board: Edge.Cuts created")

    # 3. Add 4 Mounting Holes (M2.5, 2.7mm drill, 5.0mm pad)
    hole_lib = os.path.join(fp_base, "MountingHole.pretty")
    for mh_ref, (hx, hy) in [
        ("H1", (bx0 + 4.0, by0 + 4.0)),
        ("H2", (bx1 - 4.0, by0 + 4.0)),
        ("H3", (bx0 + 4.0, by1 - 4.0)),
        ("H4", (bx1 - 4.0, by1 - 4.0))
    ]:
        mh = pcbnew.FootprintLoad(hole_lib, "MountingHole_2.7mm_M2.5_Pad")
        if mh:
            mh.SetReference(mh_ref)
            mh.SetPosition(pcbnew.VECTOR2I(mm_to_iu(hx), mm_to_iu(hy)))
            board.Add(mh)
    # 4. Component Placement Coordinates & Orientations
    layout = {
        # Zone 1: Main MCU (ESP32-WROOM-32E) & Antenna
        "U1":  (87.5, 68.0, 0),       # Antenna at top edge
        "SW1": (60.0, 58.0, 0),       # Reset button
        "SW2": (115.0, 58.0, 0),      # Boot button
        "R13": (66.0, 58.0, 90),      # EN pullup
        "C16": (66.0, 62.0, 0),       # EN delay
        "R14": (109.0, 58.0, 90),     # BOOT pullup
        "C14": (80.0, 60.0, 0),       # 3V3 decoupling 10uF
        "C15": (83.0, 60.0, 0),       # 3V3 decoupling 100nF

        # Zone 2: USB-C & Input Protection
        "J1":  (87.5, 110.0, 180),    # USB-C at bottom edge
        "U9":  (87.5, 102.5, 0),      # USBLC6-2SC6 ESD
        "R1":  (81.5, 105.0, 90),     # CC1 5.1k
        "R2":  (93.5, 105.0, 90),     # CC2 5.1k
        "F1":  (94.0, 100.5, 90),     # Polyfuse 500mA
        "C1":  (95.0, 95.0, 0),       # VBUS cap 10uF
        "C2":  (98.5, 95.0, 0),       # VBUS cap 100nF

        # Zone 3: USB-to-UART (CH340C) & Auto-Reset
        "U8":  (70.0, 97.0, 0),       # CH340C
        "C12": (60.0, 94.0, 0),       # CH340 VCC cap
        "C13": (60.0, 100.0, 0),      # CH340 V3 cap
        "R9":  (77.0, 94.0, 90),      # TX series 1k
        "R10": (77.0, 97.0, 90),      # RX series 1k
        "Q2":  (72.0, 87.0, 0),       # MMBT3904 Reset
        "Q3":  (72.0, 81.0, 0),       # MMBT3904 Boot
        "R11": (66.0, 87.0, 90),      # Q2 base resistor 10k
        "R12": (66.0, 81.0, 90),      # Q3 base resistor 10k

        # Zone 4: Battery Charger & Protection
        "J2":  (116.0, 102.0, 0),     # JST-PH Battery in
        "U3":  (106.0, 96.0, 0),      # TP4056 Charger
        "R3":  (106.0, 104.0, 0),     # PROG resistor 4.7k
        "C3":  (112.0, 96.0, 0),      # BAT out cap 10uF
        "D2":  (101.0, 107.0, 90),    # Red LED CHRG
        "R4":  (101.0, 102.0, 0),     # LED resistor 1k
        "D3":  (106.0, 107.0, 90),    # Green LED FULL
        "R5":  (106.0, 102.0, 0),     # LED resistor 1k
        "U4":  (116.0, 92.0, 0),      # DW01A protection IC
        "R6":  (121.0, 90.0, 90),     # VDD filter 100R
        "C4":  (121.0, 94.0, 0),      # VDD cap 100nF
        "R7":  (121.0, 98.0, 90),     # CS resistor 1k
        "C5":  (116.0, 97.0, 0),      # CS cap 100nF
        "U5":  (116.0, 84.0, 0),      # FS8205A Dual N-FET

        # Zone 5: Dynamic Power-Path (Load-Sharing)
        "Q1":  (98.0, 88.0, 0),       # AO3401A P-MOSFET
        "R8":  (98.0, 82.0, 0),       # Gate pull-down 100k
        "D1":  (92.0, 88.0, 90),      # SS34 Schottky
        "C6":  (92.0, 82.0, 0),       # VSYS bulk cap 22uF

        # Zone 6: 3.3V Synchronous Buck-Boost (TPS63001)
        "U2":  (106.0, 72.0, 0),      # TPS63001
        "L1":  (116.0, 72.0, 90),     # 2.2uH Inductor
        "C7":  (101.0, 76.0, 0),      # VIN cap 10uF
        "C8":  (101.0, 80.0, 0),      # VIN cap 100nF
        "C9":  (106.0, 64.0, 0),      # VOUT cap 10uF
        "C10": (109.5, 64.0, 0),      # VOUT cap 10uF
        "C11": (113.0, 64.0, 0),      # VOUT cap 100nF

        # Zone 7: MAX98357A I2S Audio Amp & Speaker
        "U6":  (62.0, 74.0, 0),       # MAX98357A
        "C19": (56.0, 80.0, 0),       # 220uF Tantalum bulk
        "C20": (62.0, 82.0, 0),       # 10uF VDD cap
        "C21": (66.0, 82.0, 0),       # 100nF VDD cap
        "R18": (56.0, 74.0, 0),       # GAIN 100k
        "R19": (56.0, 70.0, 0),       # SD pull-down 100k
        "FB1": (68.0, 68.0, 90),      # Ferrite Bead 1
        "FB2": (72.0, 68.0, 90),      # Ferrite Bead 2
        "C22": (68.0, 64.0, 0),       # RF cap 100pF
        "C23": (72.0, 64.0, 0),       # RF cap 100pF
        "J3":  (58.0, 60.0, 0),       # Speaker JST-PH header

        # Zone 8: Real-Time Clock (DS3231M) & CR2032 Battery
        "U7":  (87.5, 82.0, 0),       # DS3231M
        "C17": (82.0, 76.0, 0),       # VCC bypass 100nF
        "C18": (93.0, 76.0, 0),       # VBAT bypass 100nF
        "R15": (81.0, 88.0, 0),       # SDA pullup 4.7k
        "R16": (84.5, 88.0, 0),       # SCL pullup 4.7k
        "R17": (88.0, 88.0, 0),       # INT pullup 10k
        "BT1": (87.5, 82.0, 0),       # CR2032 Holder (placed on Bottom Layer!)

        # Zone 9: User Controls
        "SW3": (58.0, 104.0, 0),      # Wake Push Button
        "R20": (65.0, 105.0, 90),     # Wake pullup 10k
        "C24": (65.0, 101.0, 0),      # Debounce cap 100nF

        # Zone 10: Test Points (Organized along right edge)
        "TP1":  (121.5, 64.0, 0),
        "TP2":  (121.5, 68.0, 0),
        "TP3":  (121.5, 72.0, 0),
        "TP4":  (121.5, 76.0, 0),
        "TP5":  (121.5, 80.0, 0),
        "TP6":  (121.5, 84.0, 0),
        "TP7":  (121.5, 88.0, 0),
        "TP8":  (121.5, 92.0, 0),
        "TP9":  (121.5, 96.0, 0),
        "TP10": (121.5, 100.0, 0)
    }
    print("create_board: starting footprint loading and placement...")

    # 5. Load and Place All Footprints
    fps_by_ref = {}
    import traceback
    for ref, d in sorted(components.items()):
        fp_str = d["footprint"]
        lib, name = fp_str.split(":")
        lib_path = os.path.join(fp_base, lib + ".pretty")
        print(f"Loading {ref}: {fp_str}...")
        try:
            fp = pcbnew.FootprintLoad(lib_path, name)
            if not fp:
                print(f"FAILED TO LOAD: {fp_str} for {ref}")
                continue
            
            fp.SetReference(ref)
            fp.SetValue(d["val"])

            board.Add(fp)
            if ref in layout:
                x, y, ang = layout[ref]
                fp.SetPosition(pcbnew.VECTOR2I(mm_to_iu(x), mm_to_iu(y)))
                fp.SetOrientation(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
                if ref == "BT1":
                    fp.SetLayerAndFlip(pcbnew.B_Cu)

            fps_by_ref[ref] = fp
            print(f"Successfully added {ref}")
        except Exception as e:
            print(f"EXCEPTION ON {ref}: {e}")
            traceback.print_exc()
            break
    print(f"create_board: {len(fps_by_ref)} footprints placed")

    # 6. Assign Nets to Footprint Pads
    for netname, nodes in nets.items():
        net = net_map.get(netname)
        if not net:
            continue
        for ref, pin_num in nodes:
            fp = fps_by_ref.get(ref)
            if not fp:
                continue
            pad = fp.FindPadByNumber(pin_num)
            if pad:
                pad.SetNet(net)
    print("create_board: nets assigned to pads")

    # 7. Add Copper Ground Pours (Zones) on F.Cu and B.Cu
    gnd_net = net_map.get("GND")
    if gnd_net:
        def create_gnd_zone(layer):
            zone = pcbnew.ZONE(board)
            zone.SetLayer(layer)
            zone.SetNet(gnd_net)
            pts = [
                (bx0 + 0.5, by0 + 0.5),
                (79.0, by0 + 0.5),
                (79.0, by0 + 6.5),
                (96.0, by0 + 6.5),
                (96.0, by0 + 0.5),
                (bx1 - 0.5, by0 + 0.5),
                (bx1 - 0.5, by1 - 0.5),
                (bx0 + 0.5, by1 - 0.5)
            ]
            poly = pcbnew.SHAPE_LINE_CHAIN()
            for x, y in pts:
                poly.Append(mm_to_iu(x), mm_to_iu(y))
            poly.SetClosed(True)
            zone.AddPolygon(poly)
            board.Add(zone)
            return zone

        create_gnd_zone(pcbnew.F_Cu)
        create_gnd_zone(pcbnew.B_Cu)
        print("create_board: ground zones created")

    # 8. Save the completed board
    pcb_path = r"c:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\hardware\kicad\alarm_clock_v1.kicad_pcb"
    pcbnew.SaveBoard(pcb_path, board)
    print(f"Successfully generated PCB layout at: {pcb_path}")
    return pcb_path

if __name__ == "__main__":
    pcb_file = create_board()
    print("\nRunning KiCad Design Rules Check (DRC)...")
    res = subprocess.run([r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", "pcb", "drc", pcb_file], capture_output=True, text=True)
    print("Return code:", res.returncode)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
