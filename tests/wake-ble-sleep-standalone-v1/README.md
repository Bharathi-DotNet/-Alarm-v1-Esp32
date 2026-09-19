# Standalone wake / BLE / deep-sleep test v1

This directory is a **new independent PlatformIO project**, prepared on 2026-09-19. Nothing is integrated into production firmware or MAUI. Do not use the parent project's Upload button to test it. No upload or serial access has been performed by the agent.

## Scope and compatibility

- Uses the current alarm control protocol copied into this project's `src/main.cpp`: same `AlarmPrototype` name, control service/characteristic UUIDs, TIME, framed PUT, ON/OFF/DEL, SNAP, QR STOP/STOPM, backup QR, emergency recovery and volume. Existing MAUI can manage test alarms without source changes.
- Ten daily alarms, unique times, save each successful operation immediately. Connected BLE remains awake through any number of edits. Nothing sleeps just because one alarm was saved.
- Test NVS namespaces: `wk-alarms`, `wk-mission`, `wk-auth`, `wk-volume`. Production namespaces and custom audio files are never opened. Test CLEAR clears only test alarms. Test data starts empty; assign test QR codes through the app.
- Default audible pulsed speaker tone only. No A2DP, microphone, Bluetooth voice announcements, or custom audio uploads. AUDIOSTATE reports DEFAULT; custom upload explicitly fails as unsupported. This is a lifecycle experiment, not a replacement production feature set.
- Same device identity means MAUI may initially display its old cached production list before the test snapshot replaces it. Wait for the live snapshot and use only test alarms. Finish outstanding production QR missions before testing; do not replay old offline dismissal requests. Refresh after returning to production firmware.

## Wiring assumption (power OFF before changing wires)

| Connection | ESP32 DevKit V1 |
|---|---|
| DS3231 VCC / GND | 3V3 / common GND |
| DS3231 SDA / SCL | GPIO21 / GPIO22 |
| DS3231 **INT/SQW** | GPIO33, external **10kΩ pullup to 3V3** |
| Momentary normally-open WAKE button | GPIO32 to GND; external **10kΩ pullup from GPIO32 to 3V3** |
| MAX98357A BCLK / LRC / DIN | GPIO18 / GPIO19 / GPIO23 |
| MAX98357A VIN / GND / SD | 3V3 / common GND / 3V3 |
| MAX98357A GAIN | Leave open for this test |
| Speaker | Amplifier + / − only; neither lead to GND |

Use the RTC **INT/SQW**, not its 32K output. Pullups must go to 3.3V, not 5V. If a button has four legs, verify the pressed pair; two pins on the same internal contact must not permanently short GPIO32 to GND. The GPIO23 legacy buzzer must be disconnected. RTC and its backup battery remain fitted. The amplifier is not physically power-gated by this test.

On classic ESP32, two pins in EXT1 ALL_LOW would require **both** to be low. Instead this project uses **EXT0 = RTC33 LOW** and **EXT1 = just GPIO32 ALL_LOW**. Either source independently wakes the device, and serial identifies which woke it. GPIOs are returned to digital mode using `rtc_gpio_deinit()` after wake. External pullups keep the levels defined during sleep; do not rely on the Arduino awake-only INPUT_PULLUP setting.

Reference: [Espressif ESP32 sleep modes, v4.4.2](https://docs.espressif.com/projects/esp-idf/en/v4.4.2/esp32/api-reference/system/sleep_modes.html). Vendored RTClib 2.1.4 and BusIO are independent copies of the installed libraries; original library files remain unchanged.

## State transitions

1. Power/reset/button wake starts BLE advertising. If nobody ever connects during this wake session, the timeout is 120 seconds from advertising startup.
2. A BLE connection cancels that timeout and keeps the ESP32 awake, including between operations.
3. **Actual BLE disconnection** starts a fresh 10-second grace and restarts advertising. Reconnection cancels grace. Merely switching app screens or backgrounding an app that retains its BLE connection does not count as a disconnect.
4. A pending/ringing alarm, failed pending-state save, unhealthy RTC, corrupt test storage, failed speaker initialization, or a held button prevents sleep.
5. When idle timeout expires, advertising stops, the loop allows 150ms for in-flight connection events, and rechecks the real BLE connection count and atomic connection flag. It programs the next enabled daily alarm into DS3231 Alarm1 with a date/HH:MM:SS match, then reads the alarm registers back. Alarm2 and both old flags are cleared.
6. Final RTC time and wake-pin checks prevent sleeping across a just-due alarm or with RTC INT already asserted. The button must be released continuously for at least 100ms. Persistent low RTC33 with an alarm scheduled blocks sleep and logs the reason (retries limited to once per second), rather than creating a wake loop.
7. No enabled alarms: both RTC alarms are disabled; sleep still arms the GPIO32 button. RTC must still be healthy in this conservative test.
8. RTC wake restores an armed occurrence even if booting crosses its minute boundary, persists it as pending, starts the speaker and advertises for QR dismissal. Already-pending alarms loaded from NVS also ring and never sleep. A dismissed occurrence does not replay the same day.
9. QR or emergency dismissal leaves the daily schedule intact. If still BLE-connected, stay awake. Once disconnected and grace expires, program the next enabled occurrence and sleep again.

A missing/lost-power RTC keeps Bluetooth available but blocks timed scheduling/sleep until fixed. A lost-power RTC is not silently set to compiler time: the app must successfully synchronize phone time. After RTC wiring repair, restart. No timer wake or pretend software-clock fallback is used.

## Build and automated tests (no device needed)

From PowerShell:

```powershell
& 'C:\Users\Bharathi\.platformio\penv\Scripts\platformio.exe' run -d 'C:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\tests\wake-ble-sleep-standalone-v1' -e wake-ble-sleep
& 'C:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\tests\wake-ble-sleep-standalone-v1\tests\run.ps1'
```

Host tests execute this project's copied protocol and shared sleep/scheduler policy. They cover multiple framed add/edit/delete operations on one connection, persistence reload, write failure, duplicate times, disconnect/reconnect deadlines, pending alarm and QR dismissal, no-enabled selection, late boot recovery, year rollover, clock moved backwards and millis rollover. Host tests do **not** simulate real radio, electrical interrupt levels, deep sleep or battery current.

## Physical test checklist (after separate upload authorization)

Uploading this standalone firmware replaces the running program on the board temporarily. Use a spare board if production alarms must remain available. Do not erase flash or repartition. The default partition layout matches the current saved project; ordinary upload preserves production NVS/filesystem data, but test firmware does not run production schedules.

1. Wire GPIO32/33 as above. Close other serial monitors. After explicit authorization, upload with the command below, replacing the port with the actual USB ESP32 port. COM3/COM4 Bluetooth serial ports are not firmware upload ports.
2. Monitor at 115200. Expect `[TEST] ... POWER/RESET`, RTC trusted status, speaker-ready and `[BLE] Advertising ... 120 seconds`. If RTC clock is untrusted, connect the app to synchronize first.
3. With trusted RTC and no enabled test alarms, leave BLE disconnected for 120 seconds. Expect `[RTC] No enabled alarm` and `[SLEEP] ENTER ... RTC33=0`. Board stops advertising.
4. Tap and release WAKE. Expect wake cause `BUTTON32` and advertising. Hold WAKE past timeout to confirm sleep is blocked while low; release to allow sleep. It must not repeatedly reboot while held.
5. Connect MAUI; stay connected for more than two minutes. Add at least three distinct alarms several minutes ahead; edit one, disable one, delete another, then add another. Confirm `[STORE] Alarm transaction committed` for each and verify the app snapshot. ESP32 must remain awake throughout.
6. Force a real BLE disconnect (turn phone Bluetooth off if closing the app leaves it connected). Expect `[BLE] Disconnected ... 10-second grace`. Reconnect within 10 seconds: stay awake. Disconnect again: a **new** full 10-second grace starts.
7. Allow sleep. Check `[RTC] Armed slot=...` selects the earliest **enabled** alarm and `[SLEEP] ... RTC33=1`. Keep the phone disconnected. At the due time expect `RTC33` wake, persistent pending alarm, speaker sound, BLE advertising. Leave it ringing past two minutes: no sleep.
8. Reconnect and scan a wrong QR: alarm continues. Scan its correct main or backup QR: it stops. While connected it stays awake. Disconnect: after grace, the next enabled alarm is programmed. Repeat over midnight/daily recurrence as a longer bench test.
9. Reset during ringing: persisted pending state should resume. Reset after QR dismissal: the same day's occurrence must not ring again. Power-cut recovery outside the due minute is not guaranteed; this experiment is not a general missed-alarm catch-up system.
10. Disable/delete all test alarms, disconnect, sleep; button wake must still work. Keep button held or intentionally assert RTC33 LOW only as a controlled fault test with the normal pullup present: a scheduled-RTC low pin must log a block and remain accessible over BLE.
11. Restore the original saved firmware using its own normal build/upload command when finished. Refresh MAUI to replace the test cache with the unchanged production schedule. Restoring code does not undo phone/RTC time synchronization performed during the test.

Commands reserved for a separately authorized physical test; **not executed**:

```powershell
& 'C:\Users\Bharathi\.platformio\penv\Scripts\platformio.exe' run -d 'C:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\tests\wake-ble-sleep-standalone-v1' -e wake-ble-sleep -t upload --upload-port COM5
& 'C:\Users\Bharathi\.platformio\penv\Scripts\platformio.exe' device monitor --port COM5 --baud 115200
```

## Limits / evidence

- Build and host results are recorded in `VALIDATION.md`. No claim of tested electrical wake, speaker audibility, BLE timing on a phone or measured battery savings until the checklist is run.
- Existing MAUI may keep or automatically reconnect BLE; that intentionally prevents sleep. Do not change the app to work around this in this phase; use an actual disconnect for the grace test.
- Holding connected mode or ringing consumes awake power. DevKit regulator/LED/USB chip and amplifier remain powered in ESP32 deep sleep; this is not a battery-life certification or final power design.
- Immediate wake/late BLE connection races must be exercised physically. The implementation stops advertising, drains events, checks the controller's connection count, and rechecks the atomic flag after serial flushing; host tests only validate policy decisions.
- `existing-files-before.json` records SHA256 of every pre-existing project file except `.pio`/`.git` generated caches. `verify_unchanged.py` checks those original files; all new source/config/tests/docs live here. No production or MAUI edits are required.

Update requirement: **ESP32 standalone test firmware only, after explicit upload go-ahead. MAUI update is not needed. Production integration has not been done.**
