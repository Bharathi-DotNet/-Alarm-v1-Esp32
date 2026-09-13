# INMP441 diagnostic
Standalone firmware for existing ESP32 DOIT DevKit V1 wiring: 3.3V/GND, BCLK18, WS19, SD5, L/R grounded (left).
Build: platformio run -d tests/mic-hardware
Upload only after explicit approval; it temporarily replaces the alarm application. The diagnostic never writes Preferences/NVS. Restore the alarm firmware after testing. Missed alarms during this diagnostic are not serviced.
Monitor at 115200 baud. Compare five seconds quiet, five seconds speaking 10–20 cm from the microphone, then quiet again. AC_RMS and peakToPeak should rise reproducibly with voice. Nonzero readings alone do not prove a working microphone. Constant/stuck readings or persistent clipping indicate a wiring/configuration/power issue.
The test prints levels only and does not record speech. A listening/recording test is needed to assess intelligibility beyond basic acoustic response.
