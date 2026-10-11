import os
import subprocess
from schematic_engine import SchematicGenerator

def build_alarm_clock_schematic():
    gen = SchematicGenerator(title="ESP32 Anti-Cheat Smart Alarm Clock", rev="v1.0")

    # =========================================================================
    # SECTION TITLES
    # =========================================================================
    gen.add_text("1. USB-C INPUT & ESD PROTECTION", 30, 25, size=2.54)
    gen.add_text("2. LI-ION CHARGER & BATTERY PROTECTION", 130, 25, size=2.54)
    gen.add_text("3. POWER-PATH (LOAD SHARING)", 230, 25, size=2.54)
    gen.add_text("4. 3.3V BUCK-BOOST REGULATOR (TPS63001)", 315, 25, size=2.54)

    gen.add_text("5. USB-TO-UART INTERFACE & AUTO-DOWNLOAD", 30, 115, size=2.54)
    gen.add_text("6. MAIN MCU (ESP32-WROOM-32E)", 150, 115, size=2.54)
    gen.add_text("7. REAL-TIME CLOCK (DS3231M & CR2032)", 310, 115, size=2.54)

    gen.add_text("8. I2S AUDIO AMPLIFIER (MAX98357A)", 30, 215, size=2.54)
    gen.add_text("9. WAKE BUTTON & USER CONTROLS", 185, 215, size=2.54)
    gen.add_text("10. TEST POINTS & POWER FLAGS", 295, 215, size=2.54)

    # =========================================================================
    # BLOCK 1: USB-C INPUT & ESD PROTECTION
    # =========================================================================
    # J1: USB-C Receptacle
    j1 = gen.add_sym("Connector:USB_C_Receptacle_USB2.0_16P", "J1", "USB_C_16P",
                     "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 50, 60, rot=0)
    # VBUS pins: A4, A9, B4, B9
    for p in ["A4", "A9", "B4", "B9"]:
        gen.connect_pin(j1, p, "VBUS_RAW")
    # GND pins: A1, A12, B1, B12, SH
    for p in ["A1", "A12", "B1", "B12", "SH"]:
        gen.connect_pin(j1, p, "GND")
    # CC pins
    gen.connect_pin(j1, "A5", "USB_CC1")
    gen.connect_pin(j1, "B5", "USB_CC2")
    # Data pins
    gen.connect_pin(j1, "A6", "USB_DP_CON")
    gen.connect_pin(j1, "B6", "USB_DP_CON")
    gen.connect_pin(j1, "A7", "USB_DM_CON")
    gen.connect_pin(j1, "B7", "USB_DM_CON")
    # SBU pins (NC)
    gen.nc_pin(j1, "A8")
    gen.nc_pin(j1, "B8")

    # CC Pull-downs
    r_cc1 = gen.add_sym("Device:R", "R_CC1", "5.1k", "Resistor_SMD:R_0603_1608Metric", 75, 45, rot=0)
    gen.connect_pin(r_cc1, "1", "USB_CC1")
    gen.connect_pin(r_cc1, "2", "GND")

    r_cc2 = gen.add_sym("Device:R", "R_CC2", "5.1k", "Resistor_SMD:R_0603_1608Metric", 85, 45, rot=0)
    gen.connect_pin(r_cc2, "1", "USB_CC2")
    gen.connect_pin(r_cc2, "2", "GND")

    # F1: Polyfuse PTC on VBUS
    f1 = gen.add_sym("Device:Polyfuse", "F1", "500mA", "Fuse:Fuse_1812_4532Metric", 75, 70, rot=90)
    gen.connect_pin(f1, "1", "VBUS_RAW")
    gen.connect_pin(f1, "2", "VBUS")

    # U9: USBLC6-2SC6 ESD Protection
    u9 = gen.add_sym("Power_Protection:USBLC6-2P6", "U9", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", 100, 60, rot=0)
    gen.connect_pin(u9, "1", "USB_DM_CON")
    gen.connect_pin(u9, "2", "GND")
    gen.connect_pin(u9, "3", "USB_DP_CON")
    gen.connect_pin(u9, "4", "USB_DP")
    gen.connect_pin(u9, "5", "VBUS")
    gen.connect_pin(u9, "6", "USB_DM")

    # VBUS Filter Caps
    c_vbus1 = gen.add_sym("Device:C", "C_VBUS1", "10uF", "Capacitor_SMD:C_0805_2012Metric", 115, 45, rot=0)
    gen.connect_pin(c_vbus1, "1", "VBUS")
    gen.connect_pin(c_vbus1, "2", "GND")

    c_vbus2 = gen.add_sym("Device:C", "C_VBUS2", "100nF", "Capacitor_SMD:C_0603_1608Metric", 122, 45, rot=0)
    gen.connect_pin(c_vbus2, "1", "VBUS")
    gen.connect_pin(c_vbus2, "2", "GND")

    # =========================================================================
    # BLOCK 2: LI-ION CHARGER & BATTERY PROTECTION
    # =========================================================================
    # U3: TP4056 Charger
    u3 = gen.add_sym("Battery_Management:TP4056-42-ESOP8", "U3", "TP4056",
                     "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm_ThermalVias", 155, 60, rot=0)
    gen.connect_pin(u3, "1", "GND") # TEMP to GND
    gen.connect_pin(u3, "2", "NET_PROG")
    gen.connect_pin(u3, "3", "GND")
    gen.connect_pin(u3, "4", "VBUS")
    gen.connect_pin(u3, "5", "VBAT_PROT")
    gen.connect_pin(u3, "6", "NET_STDBY")
    gen.connect_pin(u3, "7", "NET_CHRG")
    gen.connect_pin(u3, "8", "VBUS")
    gen.connect_pin(u3, "9", "GND") # EPAD

    # R_PROG (4.7k -> 255mA charge current)
    r_prog = gen.add_sym("Device:R", "R_PROG", "4.7k (255mA)", "Resistor_SMD:R_0603_1608Metric", 175, 75, rot=0)
    gen.connect_pin(r_prog, "1", "NET_PROG")
    gen.connect_pin(r_prog, "2", "GND")

    # Charge LEDs & Resistors (powered only from VBUS!)
    r_chrg = gen.add_sym("Device:R", "R_CHRG", "1k", "Resistor_SMD:R_0603_1608Metric", 140, 95, rot=0)
    gen.connect_pin(r_chrg, "1", "VBUS")
    gen.connect_pin(r_chrg, "2", "NET_LED_CHRG_A")

    d_chrg = gen.add_sym("Device:LED", "D_CHRG", "RED (CHRG)", "LED_SMD:LED_0603_1608Metric", 150, 95, rot=90)
    gen.connect_pin(d_chrg, "2", "NET_LED_CHRG_A") # Anode (pin 2 in KiCad LED)
    gen.connect_pin(d_chrg, "1", "NET_CHRG")        # Cathode (pin 1 in KiCad LED)

    r_stdby = gen.add_sym("Device:R", "R_STDBY", "1k", "Resistor_SMD:R_0603_1608Metric", 165, 95, rot=0)
    gen.connect_pin(r_stdby, "1", "VBUS")
    gen.connect_pin(r_stdby, "2", "NET_LED_STDBY_A")

    d_stdby = gen.add_sym("Device:LED", "D_STDBY", "GRN (FULL)", "LED_SMD:LED_0603_1608Metric", 175, 95, rot=90)
    gen.connect_pin(d_stdby, "2", "NET_LED_STDBY_A")
    gen.connect_pin(d_stdby, "1", "NET_STDBY")

    # J2: Battery Connector (JST-PH 2.0mm)
    j2 = gen.add_sym("Connector:Conn_01x02_Pin", "J2", "JST_PH_BATT",
                     "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", 195, 45, rot=0)
    gen.connect_pin(j2, "1", "VBAT_PROT")
    gen.connect_pin(j2, "2", "BATT_NEG")

    # Battery Protection IC U4: DW01A
    u4 = gen.add_sym("Battery_Management:DW01A", "U4", "DW01A", "Package_TO_SOT_SMD:SOT-23-6", 195, 75, rot=0)
    gen.connect_pin(u4, "1", "GATE_OD")
    gen.connect_pin(u4, "2", "NET_DW_CS")
    gen.connect_pin(u4, "3", "GATE_OC")
    gen.connect_pin(u4, "4", "NET_DW_VCC")
    gen.connect_pin(u4, "5", "BATT_NEG")
    gen.nc_pin(u4, "6") # TD

    r_dw_vcc = gen.add_sym("Device:R", "R_VDD", "100R", "Resistor_SMD:R_0603_1608Metric", 215, 65, rot=90)
    gen.connect_pin(r_dw_vcc, "1", "NET_DW_VCC")
    gen.connect_pin(r_dw_vcc, "2", "VBAT_PROT")

    c_dw_vcc = gen.add_sym("Device:C", "C_VDD", "100nF", "Capacitor_SMD:C_0603_1608Metric", 215, 80, rot=0)
    gen.connect_pin(c_dw_vcc, "1", "NET_DW_VCC")
    gen.connect_pin(c_dw_vcc, "2", "GND")

    r_dw_cs = gen.add_sym("Device:R", "R_CS", "1k", "Resistor_SMD:R_0603_1608Metric", 205, 95, rot=90)
    gen.connect_pin(r_dw_cs, "1", "NET_DW_CS")
    gen.connect_pin(r_dw_cs, "2", "GND")

    c_dw_cs = gen.add_sym("Device:C", "C_CS", "100nF", "Capacitor_SMD:C_0603_1608Metric", 195, 95, rot=0)
    gen.connect_pin(c_dw_cs, "1", "NET_DW_CS")
    gen.connect_pin(c_dw_cs, "2", "BATT_NEG")

    # Protection MOSFET U5: FS8205A Dual N-FET
    u5 = gen.add_sym("Transistor_FET:Q_Dual_NMOS_G1S2G2D2S1D1", "U5", "FS8205A",
                     "Package_SO:TSSOP-8_4.4x3mm_P0.65mm", 220, 45, rot=0)
    gen.connect_pin(u5, "1", "GATE_OC")
    gen.connect_pin(u5, "2", "GND")
    gen.connect_pin(u5, "3", "GATE_OD")
    gen.connect_pin(u5, "4", "NET_FS_DRAIN")
    gen.connect_pin(u5, "5", "BATT_NEG")
    gen.connect_pin(u5, "6", "NET_FS_DRAIN")

    # Output / decoupling caps for battery
    c_chg_out = gen.add_sym("Device:C", "C_CHG_OUT", "10uF", "Capacitor_SMD:C_0805_2012Metric", 175, 45, rot=0)
    gen.connect_pin(c_chg_out, "1", "VBAT_PROT")
    gen.connect_pin(c_chg_out, "2", "GND")

    # =========================================================================
    # BLOCK 3: POWER-PATH (LOAD SHARING)
    # =========================================================================
    # Q1: AO3401A P-MOSFET
    q1 = gen.add_sym("Transistor_FET:TP0610T", "Q1", "AO3401A", "Package_TO_SOT_SMD:SOT-23", 260, 50, rot=0)
    gen.connect_pin(q1, "1", "VBUS")      # Gate to VBUS
    gen.connect_pin(q1, "2", "VSYS")      # Source to VSYS
    gen.connect_pin(q1, "3", "VBAT_PROT") # Drain to Battery

    r_gate = gen.add_sym("Device:R", "R_GATE", "100k", "Resistor_SMD:R_0603_1608Metric", 250, 75, rot=0)
    gen.connect_pin(r_gate, "1", "VBUS")
    gen.connect_pin(r_gate, "2", "GND")

    # D1: SS34 Schottky Diode
    d1 = gen.add_sym("Device:D_Schottky", "D1", "SS34 (3A/40V)", "Diode_SMD:D_SOD-123", 275, 50, rot=90)
    gen.connect_pin(d1, "2", "VBUS") # Anode (pin 2 in KiCad)
    gen.connect_pin(d1, "1", "VSYS") # Cathode (pin 1 in KiCad)

    c_sys = gen.add_sym("Device:C", "C_SYS", "22uF", "Capacitor_SMD:C_0805_2012Metric", 285, 75, rot=0)
    gen.connect_pin(c_sys, "1", "VSYS")
    gen.connect_pin(c_sys, "2", "GND")

    # =========================================================================
    # BLOCK 4: 3.3V BUCK-BOOST REGULATOR (TPS63001)
    # =========================================================================
    u2 = gen.add_sym("Regulator_Switching:TPS63000", "U2", "TPS63001",
                     "Package_SON:Texas_DRC0010J_ThermalVias", 355, 60, rot=0)
    gen.connect_pin(u2, "1", "+3V3")     # VOUT
    gen.connect_pin(u2, "2", "VSYS")     # VINA
    gen.connect_pin(u2, "3", "GND")      # GND
    gen.connect_pin(u2, "4", "GND")      # PS/SYNC to GND (Power-Save Mode 30uA Iq)
    gen.connect_pin(u2, "5", "NET_TPS_L1")
    gen.connect_pin(u2, "6", "VSYS")     # VIN
    gen.connect_pin(u2, "7", "VSYS")     # EN
    gen.connect_pin(u2, "8", "NET_TPS_L2")
    gen.connect_pin(u2, "9", "GND")      # PGND
    gen.connect_pin(u2, "10", "+3V3")    # FB (Fixed 3.3V connects directly to VOUT)
    gen.connect_pin(u2, "11", "GND")     # EPAD

    # Inductor L1
    l1 = gen.add_sym("Device:L", "L1", "2.2uH (2.5A)", "Inductor_SMD:L_1210_3225Metric", 340, 45, rot=90)
    gen.connect_pin(l1, "1", "NET_TPS_L1")
    gen.connect_pin(l1, "2", "NET_TPS_L2")

    # Input Capacitors
    c_in1 = gen.add_sym("Device:C", "C_IN1", "10uF", "Capacitor_SMD:C_0805_2012Metric", 325, 75, rot=0)
    gen.connect_pin(c_in1, "1", "VSYS")
    gen.connect_pin(c_in1, "2", "GND")

    c_in2 = gen.add_sym("Device:C", "C_IN2", "100nF", "Capacitor_SMD:C_0603_1608Metric", 335, 75, rot=0)
    gen.connect_pin(c_in2, "1", "VSYS")
    gen.connect_pin(c_in2, "2", "GND")

    # Output Capacitors
    c_out1 = gen.add_sym("Device:C", "C_OUT1", "10uF", "Capacitor_SMD:C_0805_2012Metric", 380, 50, rot=0)
    gen.connect_pin(c_out1, "1", "+3V3")
    gen.connect_pin(c_out1, "2", "GND")

    c_out2 = gen.add_sym("Device:C", "C_OUT2", "10uF", "Capacitor_SMD:C_0805_2012Metric", 390, 50, rot=0)
    gen.connect_pin(c_out2, "1", "+3V3")
    gen.connect_pin(c_out2, "2", "GND")

    c_out3 = gen.add_sym("Device:C", "C_OUT3", "100nF", "Capacitor_SMD:C_0603_1608Metric", 400, 50, rot=0)
    gen.connect_pin(c_out3, "1", "+3V3")
    gen.connect_pin(c_out3, "2", "GND")

    # =========================================================================
    # BLOCK 5: USB-TO-UART INTERFACE & AUTO-DOWNLOAD (CH340C)
    # =========================================================================
    u8 = gen.add_sym("Interface_USB:CH340C", "U8", "CH340C", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", 60, 150, rot=0)
    gen.connect_pin(u8, "1", "GND")
    gen.connect_pin(u8, "2", "UART_TX_CH340")
    gen.connect_pin(u8, "3", "UART_RX_CH340")
    gen.connect_pin(u8, "4", "NET_CH340_V3")
    gen.connect_pin(u8, "5", "USB_DP")
    gen.connect_pin(u8, "6", "USB_DM")
    gen.nc_pin(u8, "7") # XI
    gen.nc_pin(u8, "8") # XO
    gen.nc_pin(u8, "9") # CTS
    gen.nc_pin(u8, "10") # DSR
    gen.nc_pin(u8, "11") # RI
    gen.nc_pin(u8, "12") # DCD
    gen.connect_pin(u8, "13", "DTR")
    gen.connect_pin(u8, "14", "RTS")
    gen.nc_pin(u8, "15") # R232
    gen.connect_pin(u8, "16", "VBUS") # Powered STRICTLY from VBUS

    # CH340C Capacitors
    c_uart_vcc = gen.add_sym("Device:C", "C_UART_VCC", "100nF", "Capacitor_SMD:C_0603_1608Metric", 40, 135, rot=0)
    gen.connect_pin(c_uart_vcc, "1", "VBUS")
    gen.connect_pin(c_uart_vcc, "2", "GND")

    c_v3 = gen.add_sym("Device:C", "C_V3", "100nF", "Capacitor_SMD:C_0603_1608Metric", 40, 165, rot=0)
    gen.connect_pin(c_v3, "1", "NET_CH340_V3")
    gen.connect_pin(c_v3, "2", "GND")

    # Series 1k isolation resistors (prevent phantom back-powering CH340C when USB is unplugged)
    r_tx = gen.add_sym("Device:R", "R_TX", "1k", "Resistor_SMD:R_0603_1608Metric", 90, 140, rot=90)
    gen.connect_pin(r_tx, "1", "UART_TX_CH340")
    gen.connect_pin(r_tx, "2", "ESP_RXD0")

    r_rx = gen.add_sym("Device:R", "R_RX", "1k", "Resistor_SMD:R_0603_1608Metric", 90, 150, rot=90)
    gen.connect_pin(r_rx, "1", "UART_RX_CH340")
    gen.connect_pin(r_rx, "2", "ESP_TXD0")

    # Auto-Reset / Download Transistors (MMBT3904)
    # Q2: Reset Control
    q2 = gen.add_sym("Transistor_BJT:Q_NPN_BEC", "Q2", "MMBT3904", "Package_TO_SOT_SMD:SOT-23", 115, 145, rot=0)
    gen.connect_pin(q2, "1", "NET_Q2_BASE")
    gen.connect_pin(q2, "2", "RTS")
    gen.connect_pin(q2, "3", "ESP_EN")

    r_dtr = gen.add_sym("Device:R", "R_DTR", "10k", "Resistor_SMD:R_0603_1608Metric", 105, 145, rot=90)
    gen.connect_pin(r_dtr, "1", "DTR")
    gen.connect_pin(r_dtr, "2", "NET_Q2_BASE")

    # Q3: Boot Mode Control
    q3 = gen.add_sym("Transistor_BJT:Q_NPN_BEC", "Q3", "MMBT3904", "Package_TO_SOT_SMD:SOT-23", 115, 165, rot=0)
    gen.connect_pin(q3, "1", "NET_Q3_BASE")
    gen.connect_pin(q3, "2", "DTR")
    gen.connect_pin(q3, "3", "ESP_IO0")

    r_rts = gen.add_sym("Device:R", "R_RTS", "10k", "Resistor_SMD:R_0603_1608Metric", 105, 165, rot=90)
    gen.connect_pin(r_rts, "1", "RTS")
    gen.connect_pin(r_rts, "2", "NET_Q3_BASE")

    # =========================================================================
    # BLOCK 6: MAIN MCU (ESP32-WROOM-32E)
    # =========================================================================
    u1 = gen.add_sym("RF_Module:ESP32-WROOM-32E", "U1", "ESP32-WROOM-32E", "RF_Module:ESP32-WROOM-32E", 220, 160, rot=0)
    gen.connect_pin(u1, "2", "+3V3")
    gen.connect_pin(u1, "3", "ESP_EN")
    gen.nc_pin(u1, "4") # SENSOR_VP
    gen.nc_pin(u1, "5") # SENSOR_VN
    gen.nc_pin(u1, "6") # IO34
    gen.nc_pin(u1, "7") # IO35
    gen.connect_pin(u1, "8", "WAKE_BTN")  # GPIO32 - Wake Button
    gen.connect_pin(u1, "9", "RTC_INT")   # GPIO33 - RTC Alarm Wake
    gen.nc_pin(u1, "10") # IO25
    gen.nc_pin(u1, "11") # IO26
    gen.connect_pin(u1, "12", "AMP_SD")   # GPIO27 - MAX98357A SD_MODE
    gen.nc_pin(u1, "13") # IO14
    gen.nc_pin(u1, "14") # IO12
    gen.nc_pin(u1, "16") # IO13
    gen.nc_pin(u1, "17") # NC
    gen.nc_pin(u1, "18") # NC
    gen.nc_pin(u1, "19") # NC
    gen.nc_pin(u1, "20") # NC
    gen.nc_pin(u1, "21") # NC
    gen.nc_pin(u1, "22") # NC
    gen.nc_pin(u1, "23") # IO15
    gen.nc_pin(u1, "24") # IO2
    gen.connect_pin(u1, "25", "ESP_IO0")  # GPIO0 - Bootloader
    gen.nc_pin(u1, "26") # IO4
    gen.nc_pin(u1, "27") # IO16
    gen.nc_pin(u1, "28") # IO17
    gen.nc_pin(u1, "29") # IO5
    gen.connect_pin(u1, "30", "I2S_BCLK") # GPIO18
    gen.connect_pin(u1, "31", "I2S_LRC")  # GPIO19
    gen.nc_pin(u1, "32") # NC
    gen.connect_pin(u1, "33", "I2C_SDA")  # GPIO21
    gen.connect_pin(u1, "34", "ESP_RXD0") # RXD0
    gen.connect_pin(u1, "35", "ESP_TXD0") # TXD0
    gen.connect_pin(u1, "36", "I2C_SCL")  # GPIO22
    gen.connect_pin(u1, "37", "I2S_DIN")  # GPIO23
    gen.connect_pin(u1, "[1,15,38,39]", "GND")

    # ESP32 Decoupling
    c_esp1 = gen.add_sym("Device:C", "C_ESP1", "10uF", "Capacitor_SMD:C_0805_2012Metric", 200, 120, rot=0)
    gen.connect_pin(c_esp1, "1", "+3V3")
    gen.connect_pin(c_esp1, "2", "GND")

    c_esp2 = gen.add_sym("Device:C", "C_ESP2", "100nF", "Capacitor_SMD:C_0603_1608Metric", 210, 120, rot=0)
    gen.connect_pin(c_esp2, "1", "+3V3")
    gen.connect_pin(c_esp2, "2", "GND")

    # EN Circuit (10k pull-up, 1uF delay cap, reset switch)
    r_en = gen.add_sym("Device:R", "R_EN", "10k", "Resistor_SMD:R_0603_1608Metric", 185, 135, rot=0)
    gen.connect_pin(r_en, "1", "+3V3")
    gen.connect_pin(r_en, "2", "ESP_EN")

    c_en = gen.add_sym("Device:C", "C_EN", "1uF (POR)", "Capacitor_SMD:C_0603_1608Metric", 185, 150, rot=0)
    gen.connect_pin(c_en, "1", "ESP_EN")
    gen.connect_pin(c_en, "2", "GND")

    sw_rst = gen.add_sym("Switch:SW_Push", "SW_RST", "RESET",
                         "Button_Switch_SMD:SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm", 185, 170, rot=90)
    gen.connect_pin(sw_rst, "1", "ESP_EN")
    gen.connect_pin(sw_rst, "2", "GND")

    # BOOT Circuit (10k pull-up, boot switch)
    r_boot = gen.add_sym("Device:R", "R_BOOT", "10k", "Resistor_SMD:R_0603_1608Metric", 255, 135, rot=0)
    gen.connect_pin(r_boot, "1", "+3V3")
    gen.connect_pin(r_boot, "2", "ESP_IO0")

    sw_boot = gen.add_sym("Switch:SW_Push", "SW_BOOT", "BOOT",
                          "Button_Switch_SMD:SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm", 255, 160, rot=90)
    gen.connect_pin(sw_boot, "1", "ESP_IO0")
    gen.connect_pin(sw_boot, "2", "GND")

    # =========================================================================
    # BLOCK 7: REAL-TIME CLOCK (DS3231M & CR2032)
    # =========================================================================
    u7 = gen.add_sym("Timer_RTC:DS3231M", "U7", "DS3231M", "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm", 345, 160, rot=0)
    gen.nc_pin(u7, "1") # 32KHZ
    gen.connect_pin(u7, "2", "+3V3")
    gen.connect_pin(u7, "3", "RTC_INT")
    gen.nc_pin(u7, "4") # ~RST
    for p in ["5", "6", "7", "8", "9", "10", "11", "12", "13"]:
        gen.connect_pin(u7, p, "GND")
    gen.connect_pin(u7, "14", "NET_CR2032")
    gen.connect_pin(u7, "15", "I2C_SDA")
    gen.connect_pin(u7, "16", "I2C_SCL")

    # DS3231 Decoupling
    c_rtc = gen.add_sym("Device:C", "C_RTC", "100nF", "Capacitor_SMD:C_0603_1608Metric", 325, 140, rot=0)
    gen.connect_pin(c_rtc, "1", "+3V3")
    gen.connect_pin(c_rtc, "2", "GND")

    # CR2032 Coin Cell Battery Holder BT1
    bt1 = gen.add_sym("Device:Battery_Cell", "BT1", "CR2032 (3V)", "Battery:BatteryHolder_Keystone_1060_1x2032", 380, 140, rot=0)
    gen.connect_pin(bt1, "1", "NET_CR2032") # Positive
    gen.connect_pin(bt1, "2", "GND")        # Negative

    c_vbat_rtc = gen.add_sym("Device:C", "C_VBAT_RTC", "100nF", "Capacitor_SMD:C_0603_1608Metric", 395, 140, rot=0)
    gen.connect_pin(c_vbat_rtc, "1", "NET_CR2032")
    gen.connect_pin(c_vbat_rtc, "2", "GND")

    # I2C & Interrupt Pull-ups
    r_sda = gen.add_sym("Device:R", "R_SDA", "4.7k", "Resistor_SMD:R_0603_1608Metric", 325, 180, rot=0)
    gen.connect_pin(r_sda, "1", "+3V3")
    gen.connect_pin(r_sda, "2", "I2C_SDA")

    r_scl = gen.add_sym("Device:R", "R_SCL", "4.7k", "Resistor_SMD:R_0603_1608Metric", 335, 180, rot=0)
    gen.connect_pin(r_scl, "1", "+3V3")
    gen.connect_pin(r_scl, "2", "I2C_SCL")

    r_rtc_int = gen.add_sym("Device:R", "R_RTC_INT", "10k", "Resistor_SMD:R_0603_1608Metric", 345, 180, rot=0)
    gen.connect_pin(r_rtc_int, "1", "+3V3")
    gen.connect_pin(r_rtc_int, "2", "RTC_INT")

    # =========================================================================
    # BLOCK 8: I2S AUDIO AMPLIFIER (MAX98357A)
    # =========================================================================
    u6 = gen.add_sym("Audio:MAX98357A", "U6", "MAX98357A",
                     "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm", 75, 250, rot=0)
    gen.connect_pin(u6, "1", "I2S_DIN")
    gen.connect_pin(u6, "2", "NET_GAIN")
    gen.connect_pin(u6, "3", "GND")
    gen.connect_pin(u6, "4", "AMP_SD")
    gen.nc_pin(u6, "5")
    gen.nc_pin(u6, "6")
    gen.connect_pin(u6, "7", "VSYS")
    gen.connect_pin(u6, "8", "VSYS")
    gen.connect_pin(u6, "9", "NET_SPK_P_FILT")
    gen.connect_pin(u6, "10", "NET_SPK_N_FILT")
    gen.connect_pin(u6, "11", "GND")
    gen.nc_pin(u6, "12")
    gen.nc_pin(u6, "13")
    gen.connect_pin(u6, "14", "I2S_LRC")
    gen.connect_pin(u6, "15", "GND")
    gen.connect_pin(u6, "16", "I2S_BCLK")
    gen.connect_pin(u6, "17", "GND") # EPAD

    # MAX98357A Gain (100k to GND -> 12dB gain)
    r_gain = gen.add_sym("Device:R", "R_GAIN", "100k (12dB)", "Resistor_SMD:R_0603_1608Metric", 50, 265, rot=0)
    gen.connect_pin(r_gain, "1", "NET_GAIN")
    gen.connect_pin(r_gain, "2", "GND")

    # Shutdown pull-down (100k to GND -> hard shutdown during deep sleep / boot)
    r_sd_pd = gen.add_sym("Device:R", "R_SD_PD", "100k (0uA Sleep)", "Resistor_SMD:R_0603_1608Metric", 60, 265, rot=0)
    gen.connect_pin(r_sd_pd, "1", "AMP_SD")
    gen.connect_pin(r_sd_pd, "2", "GND")

    # Audio Power Decoupling & Bulk Cap
    c_audio_bulk = gen.add_sym("Device:C_Polarized", "C_AUDIO_BULK", "220uF (Low ESR)",
                               "Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D", 50, 235, rot=0)
    gen.connect_pin(c_audio_bulk, "1", "VSYS")
    gen.connect_pin(c_audio_bulk, "2", "GND")

    c_audio1 = gen.add_sym("Device:C", "C_AUDIO1", "10uF", "Capacitor_SMD:C_0805_2012Metric", 62, 235, rot=0)
    gen.connect_pin(c_audio1, "1", "VSYS")
    gen.connect_pin(c_audio1, "2", "GND")

    c_audio2 = gen.add_sym("Device:C", "C_AUDIO2", "100nF", "Capacitor_SMD:C_0603_1608Metric", 72, 235, rot=0)
    gen.connect_pin(c_audio2, "1", "VSYS")
    gen.connect_pin(c_audio2, "2", "GND")

    # Output EMI Filter: Ferrite Beads & RF Caps
    fb1 = gen.add_sym("Device:FerriteBead", "FB1", "220R@100MHz", "Inductor_SMD:L_0603_1608Metric", 105, 245, rot=90)
    gen.connect_pin(fb1, "1", "NET_SPK_P_FILT")
    gen.connect_pin(fb1, "2", "SPK_P")

    fb2 = gen.add_sym("Device:FerriteBead", "FB2", "220R@100MHz", "Inductor_SMD:L_0603_1608Metric", 105, 255, rot=90)
    gen.connect_pin(fb2, "1", "NET_SPK_N_FILT")
    gen.connect_pin(fb2, "2", "SPK_N")

    c_spk1 = gen.add_sym("Device:C", "C_SPK1", "100pF", "Capacitor_SMD:C_0603_1608Metric", 115, 240, rot=0)
    gen.connect_pin(c_spk1, "1", "SPK_P")
    gen.connect_pin(c_spk1, "2", "GND")

    c_spk2 = gen.add_sym("Device:C", "C_SPK2", "100pF", "Capacitor_SMD:C_0603_1608Metric", 115, 260, rot=0)
    gen.connect_pin(c_spk2, "1", "SPK_N")
    gen.connect_pin(c_spk2, "2", "GND")

    # J3: Speaker Connector (4 Ohm 3W Speaker)
    j3 = gen.add_sym("Connector:Conn_01x02_Pin", "J3", "SPK_4R_3W",
                     "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", 130, 250, rot=0)
    gen.connect_pin(j3, "1", "SPK_P")
    gen.connect_pin(j3, "2", "SPK_N")

    # =========================================================================
    # BLOCK 9: USER WAKE BUTTON
    # =========================================================================
    sw_wake = gen.add_sym("Switch:SW_Push", "SW_WAKE", "WAKE_BTN",
                          "Button_Switch_SMD:SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm", 215, 250, rot=90)
    gen.connect_pin(sw_wake, "1", "WAKE_BTN")
    gen.connect_pin(sw_wake, "2", "GND")

    r_wake = gen.add_sym("Device:R", "R_WAKE", "10k", "Resistor_SMD:R_0603_1608Metric", 230, 240, rot=0)
    gen.connect_pin(r_wake, "1", "+3V3")
    gen.connect_pin(r_wake, "2", "WAKE_BTN")

    c_wake = gen.add_sym("Device:C", "C_WAKE", "100nF (Debounce)", "Capacitor_SMD:C_0603_1608Metric", 230, 260, rot=0)
    gen.connect_pin(c_wake, "1", "WAKE_BTN")
    gen.connect_pin(c_wake, "2", "GND")

    # =========================================================================
    # BLOCK 10: TEST POINTS & POWER FLAGS
    # =========================================================================
    tps = [
        ("TP1", "VBUS", 305, 235),
        ("TP2", "VBAT_PROT", 320, 235),
        ("TP3", "VSYS", 335, 235),
        ("TP4", "+3V3", 350, 235),
        ("TP5", "GND", 365, 235),
        ("TP6", "ESP_EN", 305, 265),
        ("TP7", "ESP_IO0", 320, 265),
        ("TP8", "RTC_INT", 335, 265),
        ("TP9", "WAKE_BTN", 350, 265),
        ("TP10", "AMP_SD", 365, 265)
    ]
    for ref, net, x, y in tps:
        tp = gen.add_sym("Connector:TestPoint", ref, net, "TestPoint:TestPoint_Pad_D1.0mm_OD2.0mm", x, y, rot=0)
        gen.connect_pin(tp, "1", net)

    # Power Flags (Required by KiCad ERC to declare driven power nets)
    pwr_flags = [
        ("VBUS", 385, 235),
        ("VBAT_PROT", 385, 245),
        ("VSYS", 385, 255),
        ("+3V3", 385, 265),
        ("GND", 385, 275)
    ]
    for net, x, y in pwr_flags:
        pf = gen.add_sym("power:PWR_FLAG", "#FLG?", "PWR_FLAG", "", x, y, rot=0)
        gen.connect_pin(pf, "1", net)

    # Export to alarm_clock_v1.kicad_sch
    output_path = r"c:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\hardware\kicad\alarm_clock_v1.kicad_sch"
    content = gen.export()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated full schematic at: {output_path}")
    print(f"Total symbols: {len(gen.symbols)}")
    print(f"Total labels: {len(gen.labels)}")
    print(f"Total no-connects: {len(gen.no_connects)}")
    return output_path

if __name__ == "__main__":
    sch_file = build_alarm_clock_schematic()
    print("\nRunning KiCad Electrical Rules Check (ERC)...")
    res = subprocess.run([r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", "sch", "erc", sch_file], capture_output=True, text=True)
    print("Return code:", res.returncode)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
