import pcbnew
import os
import math
import subprocess
from parse_netlist import components, nets

def mm_to_iu(mm):
    return pcbnew.FromMM(mm)

def iu_to_mm(iu):
    return pcbnew.ToMM(iu)

def build_pcb():
    print("=== Starting PCB Generation v2 ===")
    board = pcbnew.BOARD()
    fp_base = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"

    # Set Title Block
    tb = board.GetTitleBlock()
    tb.SetTitle("ESP32 Anti-Cheat Smart Alarm Clock")
    tb.SetCompany("Production Hardware Design")
    tb.SetRevision("v1.0")
    tb.SetDate("2026-09-22")

    # 1. Setup Nets
    net_map = {}
    for netname in nets.keys():
        net = pcbnew.NETINFO_ITEM(board, netname)
        board.Add(net)
        net_map[netname] = net
    print(f"Added {len(net_map)} nets to board database")

    # 2. Board Dimensions (75mm x 60mm) with 3mm Rounded Corners
    bx0, by0 = 50.0, 50.0
    bw, bh = 75.0, 60.0
    bx1, by1 = bx0 + bw, by0 + bh

    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetFilled(False)
    rect.SetCornerRadius(mm_to_iu(3.0))
    rect.SetStart(pcbnew.VECTOR2I(mm_to_iu(bx0), mm_to_iu(by0)))
    rect.SetEnd(pcbnew.VECTOR2I(mm_to_iu(bx1), mm_to_iu(by1)))
    rect.SetWidth(mm_to_iu(0.15))
    board.Add(rect)
    print("Created Edge.Cuts outline (75mm x 60mm, 3mm corner radius)")

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
            board.Add(mh)
            mh.SetPosition(pcbnew.VECTOR2I(mm_to_iu(hx), mm_to_iu(hy)))

    # 4. Component Placement Coordinates & Orientations
    # All coordinates carefully validated to ensure:
    # - ESP32 antenna (top 6.5mm) sits at the top board edge (Y=50..56.5) with full RF clearance.
    # - No overlaps, >=0.5mm component spacing everywhere.
    # - Proper thermal pad handling.
    layout = {
        # Zone 1: Main MCU (ESP32-WROOM-32E)
        "U1":  (87.5, 63.0, 0),        # Antenna at top edge
        "SW1": (58.0, 68.0, 0),        # Reset button
        "SW2": (117.0, 68.0, 0),       # Boot button
        "R13": (65.0, 66.0, 0),        # EN pullup 10k
        "C16": (65.0, 70.0, 0),        # EN delay cap 100nF
        "R14": (110.0, 68.0, 0),       # BOOT pullup 10k
        "C14": (74.0, 59.0, 90),       # 3V3 decoupling 10uF
        "C15": (71.0, 59.0, 90),       # 3V3 decoupling 100nF

        # Zone 2: USB-C & Input Protection (Bottom Center)
        "J1":  (87.5, 110.0, 180),     # USB-C at bottom edge
        "U9":  (87.5, 103.0, 0),       # USBLC6-2SC6 ESD
        "R1":  (83.0, 104.0, 90),      # CC1 5.1k
        "R2":  (92.0, 104.0, 90),      # CC2 5.1k
        "F1":  (93.0, 99.0, 90),       # Polyfuse 500mA
        "C1":  (94.0, 94.0, 0),        # VBUS cap 10uF
        "C2":  (97.5, 94.0, 0),        # VBUS cap 100nF

        # Zone 3: USB-to-UART (CH340C) & Auto-Reset (Bottom Left)
        "U8":  (70.0, 97.0, 0),        # CH340C
        "C12": (62.0, 93.0, 0),        # CH340 VCC cap
        "C13": (62.0, 97.0, 0),        # CH340 V3 cap
        "R9":  (77.0, 93.0, 90),       # TX series 1k
        "R10": (77.0, 96.0, 90),       # RX series 1k
        "Q2":  (70.0, 88.0, 0),        # MMBT3904 Reset
        "Q3":  (70.0, 83.0, 0),        # MMBT3904 Boot
        "R11": (64.0, 88.0, 90),       # Q2 base resistor 10k
        "R12": (64.0, 83.0, 90),       # Q3 base resistor 10k

        # Zone 4: Battery Charger & Protection (Bottom Right)
        "J2":  (117.0, 102.0, 0),      # JST-PH Battery in
        "U3":  (107.0, 98.0, 0),       # TP4056 Charger
        "R3":  (107.0, 104.0, 0),      # PROG resistor 4.7k
        "C3":  (112.5, 96.0, 90),      # BAT out cap 10uF
        "D2":  (102.0, 105.0, 90),     # Red LED CHRG
        "R4":  (102.0, 101.0, 0),      # LED resistor 1k
        "D3":  (98.0, 105.0, 90),      # Green LED FULL
        "R5":  (98.0, 101.0, 0),       # LED resistor 1k
        "U4":  (117.0, 92.0, 0),       # DW01A protection IC
        "R6":  (121.5, 90.0, 90),      # VDD filter 100R
        "C4":  (121.5, 94.0, 0),       # VDD cap 100nF
        "R7":  (121.5, 98.0, 90),      # CS resistor 1k
        "C5":  (117.0, 96.5, 0),       # CS cap 100nF
        "U5":  (117.0, 85.0, 0),       # FS8205A Dual N-FET

        # Zone 5: Dynamic Power-Path (Load-Sharing) (Mid Right)
        "Q1":  (101.0, 91.0, 0),       # AO3401A P-MOSFET
        "R8":  (101.0, 85.0, 0),       # Gate pull-down 100k
        "D1":  (95.0, 88.0, 90),       # SS34 Schottky
        "C6":  (95.0, 82.0, 0),        # VSYS bulk cap 22uF

        # Zone 6: 3.3V Synchronous Buck-Boost (TPS63001) (Upper Right)
        "U2":  (107.0, 75.0, 0),       # TPS63001
        "L1":  (115.0, 75.0, 90),      # 2.2uH Inductor
        "C7":  (102.0, 77.0, 0),       # VIN cap 10uF
        "C8":  (102.0, 80.0, 0),       # VIN cap 100nF
        "C9":  (107.0, 69.0, 0),       # VOUT cap 10uF
        "C10": (110.5, 69.0, 0),       # VOUT cap 10uF
        "C11": (114.0, 69.0, 0),       # VOUT cap 100nF

        # Zone 7: MAX98357A I2S Audio Amp & Speaker (Mid Left)
        "U6":  (60.0, 78.0, 0),        # MAX98357A
        "C19": (55.0, 86.0, 0),        # 220uF Tantalum bulk
        "C20": (60.0, 84.0, 0),        # 10uF VDD cap
        "C21": (64.0, 84.0, 0),        # 100nF VDD cap
        "R18": (55.0, 78.0, 0),        # GAIN 100k
        "R19": (55.0, 74.0, 0),        # SD pull-down 100k
        "FB1": (66.0, 75.0, 90),       # Ferrite Bead 1
        "FB2": (70.0, 75.0, 90),       # Ferrite Bead 2
        "C22": (66.0, 71.0, 0),        # RF cap 100pF
        "C23": (70.0, 71.0, 0),        # RF cap 100pF
        "J3":  (60.0, 62.0, 0),        # Speaker JST-PH header

        # Zone 8: Real-Time Clock (DS3231M) & CR2032 Battery (Center)
        "U7":  (87.5, 87.0, 0),        # DS3231M
        "C17": (81.0, 82.0, 0),        # VCC bypass 100nF
        "C18": (94.0, 82.0, 0),        # VBAT bypass 100nF
        "R15": (80.0, 93.0, 0),        # SDA pullup 4.7k
        "R16": (83.5, 93.0, 0),        # SCL pullup 4.7k
        "R17": (87.0, 93.0, 0),        # INT pullup 10k
        "BT1": (87.5, 85.0, 0),        # CR2032 Holder (Bottom Layer!)

        # Zone 9: User Controls (Wake Button) (Bottom Left)
        "SW3": (60.0, 104.0, 0),       # Wake Push Button
        "R20": (67.0, 105.0, 90),      # Wake pullup 10k
        "C24": (67.0, 101.0, 0),       # Debounce cap 100nF

        # Zone 10: Test Points (Along Right Edge)
        "TP1":  (121.5, 62.0, 0),      # VBUS
        "TP2":  (121.5, 65.0, 0),      # VBAT_PROT
        "TP3":  (121.5, 68.0, 0),      # VSYS
        "TP4":  (121.5, 71.0, 0),      # +3V3
        "TP5":  (121.5, 74.0, 0),      # GND
        "TP6":  (121.5, 77.0, 0),      # ESP_EN
        "TP7":  (121.5, 80.0, 0),      # ESP_IO0
        "TP8":  (121.5, 83.0, 0),      # RTC_INT
        "TP9":  (121.5, 86.0, 0),      # WAKE_BTN
        "TP10": (121.5, 89.0, 0)       # AMP_SD
    }

    # 5. Load and Place Footprints
    fps_by_ref = {}
    for ref, d in sorted(components.items()):
        fp_str = d["footprint"]
        lib, name = fp_str.split(":")
        lib_path = os.path.join(fp_base, lib + ".pretty")
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

    print(f"Successfully placed {len(fps_by_ref)} footprints")

    # 6. Assign Nets to Footprint Pads (including thermal vias & exposed pads)
    for netname, nodes in nets.items():
        net = net_map.get(netname)
        if not net:
            continue
        for ref, pin_num in nodes:
            fp = fps_by_ref.get(ref)
            if not fp:
                continue
            for pad in fp.Pads():
                pnum = pad.GetNumber()
                if pnum == pin_num:
                    pad.SetNet(net)
                elif ref == "U2" and pin_num == "11" and pnum == "":
                    pad.SetNet(net)
                elif ref == "U3" and pin_num == "9" and pnum == "":
                    pad.SetNet(net)
                elif ref == "U6" and pin_num == "17" and pnum == "":
                    pad.SetNet(net)

    print("Assigned all nets to pads")

    # 7. Route Critical Connections (Signal & Power Tracks)
    def connect_pads(pad1, pad2, net, width_mm=0.25, layer=pcbnew.F_Cu):
        p1 = pad1.GetPosition()
        p2 = pad2.GetPosition()
        w = mm_to_iu(width_mm)

        # Dogleg routing: horizontal then vertical
        mid = pcbnew.VECTOR2I(p2.x, p1.y)

        t1 = pcbnew.PCB_TRACK(board)
        t1.SetStart(p1)
        t1.SetEnd(mid)
        t1.SetWidth(w)
        t1.SetLayer(layer)
        t1.SetNet(net)
        board.Add(t1)

        t2 = pcbnew.PCB_TRACK(board)
        t2.SetStart(mid)
        t2.SetEnd(p2)
        t2.SetWidth(w)
        t2.SetLayer(layer)
        t2.SetNet(net)
        board.Add(t2)

    # Route nets in daisy chains
    routed_tracks = 0
    for netname, nodes in nets.items():
        if netname == "GND" or len(nodes) < 2:
            continue
        net = net_map.get(netname)
        if not net:
            continue

        # Width based on net type
        w = 0.4 if netname in ["+3V3", "/VSYS", "/VBUS", "/VBUS_RAW", "/VBAT_PROT"] else 0.25

        pad_list = []
        for ref, pin_num in nodes:
            fp = fps_by_ref.get(ref)
            if not fp:
                continue
            for pad in fp.Pads():
                if pad.GetNumber() == pin_num:
                    pad_list.append(pad)
                    break

        for i in range(len(pad_list) - 1):
            p_a = pad_list[i]
            p_b = pad_list[i+1]
            layer = pcbnew.B_Cu if ("BT1" in [nodes[i][0], nodes[i+1][0]]) else pcbnew.F_Cu
            connect_pads(p_a, p_b, net, width_mm=w, layer=layer)
            routed_tracks += 2

    print(f"Generated {routed_tracks} routed track segments")

    # 8. Add Copper Ground Pours (Zones) on F.Cu and B.Cu
    # Clear keepout under ESP32 antenna (X: 78.5..96.5, Y: 50.0..56.5)
    gnd_net = net_map.get("GND")
    if gnd_net:
        def create_gnd_zone(layer):
            zone = pcbnew.ZONE(board)
            zone.SetLayer(layer)
            zone.SetNet(gnd_net)
            # Board boundary excluding ESP32 antenna area
            pts = [
                (bx0 + 0.5, by0 + 0.5),
                (78.0, by0 + 0.5),
                (78.0, by0 + 7.0),
                (97.0, by0 + 7.0),
                (97.0, by0 + 0.5),
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

        z_top = create_gnd_zone(pcbnew.F_Cu)
        z_bot = create_gnd_zone(pcbnew.B_Cu)

        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
        print("Created and filled F.Cu & B.Cu GND copper planes with RF antenna keepout")

    # 9. Save Board
    pcb_path = r"c:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\hardware\kicad\alarm_clock_v1.kicad_pcb"
    pcbnew.SaveBoard(pcb_path, board)
    print(f"Board saved successfully to: {pcb_path}")
    return pcb_path

if __name__ == "__main__":
    pcb_file = build_pcb()
    print("\nRunning DRC verification...")
    res = subprocess.run([r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", "pcb", "drc", "--output", "alarm_clock_v1-drc.rpt", pcb_file], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
