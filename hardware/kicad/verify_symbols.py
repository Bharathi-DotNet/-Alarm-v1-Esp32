import re

def get_sym_def(filepath, name):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    idx = text.find(f'(symbol "{name}"')
    if idx == -1: return None
    # find matching parenthesis for this symbol
    count = 0
    for i in range(idx, len(text)):
        if text[i] == '(':
            count += 1
        elif text[i] == ')':
            count -= 1
            if count == 0:
                return text[idx:i+1]
    return None

sym_files = {
    "ESP32-WROOM-32E": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\RF_Module.kicad_sym",
    "TPS63001": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Regulator_Switching.kicad_sym",
    "DS3231M": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Timer_RTC.kicad_sym",
    "MAX98357A": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Audio.kicad_sym",
    "CH340C": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Interface_USB.kicad_sym",
    "TP4056-42-ESOP8": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Battery_Management.kicad_sym",
    "DW01A": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Battery_Management.kicad_sym",
    "AO3401A": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Transistor_FET.kicad_sym",
    "USB_C_Receptacle_USB2.0_16P": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Connector.kicad_sym",
    "R": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym",
    "C": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym",
    "C_Polarized": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym",
    "L": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym",
    "D_Schottky": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym",
    "LED": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym",
    "SW_Push": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Switch.kicad_sym",
    "Conn_01x02_Pin": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Connector.kicad_sym",
    "Battery_Cell": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym",
    "TestPoint": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Connector.kicad_sym",
    "Q_NPN_BEC": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Device.kicad_sym",
    "Q_Dual_NMOS_G1S2G2D2S1D1": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Transistor_FET.kicad_sym",
    "+3V3": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\power.kicad_sym",
    "GND": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\power.kicad_sym",
    "PWR_FLAG": r"C:\Program Files\KiCad\10.0\share\kicad\symbols\power.kicad_sym"
}

for name, path in sym_files.items():
    s = get_sym_def(path, name)
    print(f"{name}: {'FOUND' if s else 'NOT FOUND'}")
