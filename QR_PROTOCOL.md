# QR alarm protocol and validation

The ESP32 retains one alarm. The app scans a QR during setup and sends the uppercase SHA-256 hex digest of its exact UTF-8 text (no trimming or case normalization). The device stores time, enabled state and digest together under Preferences namespace `alarm`, key `configV2`. Saving enables the alarm. Legacy settings retain their time but stay disabled until a QR is associated. Replacing the alarm replaces its QR. The prior one-shot/completed behavior remains unchanged; recurrence was not added.

The app also provides an explicit **Stop & Clear Alarm** button. It sends `CLEAR`, stops the buzzer without a QR, erases the alarm Preferences namespace (including legacy keys), and returns `OK:CLEAR`. The app clears its time field only after acknowledgment. Reboot after clear stays disabled with no QR; the protocol uses 00:00 for the empty time. If NVS erasure fails, ringing still stops and the response is `ERR:CLEAR_STORAGE`; retry before restarting because old settings may remain.

Commands:
- `SET:HH:MM:<64-character digest>` -> `OK:SET`
- `STOP:<64-character digest>` -> `OK:STOP` only while ringing with a matching digest
- `ENABLE`, `DISABLE` -> corresponding `OK:` acknowledgment
- `GET` -> `STATE:HH:MM:<enabled>:<hasQr>:<ringing>` (flags are 0/1)

SET, ENABLE and DISABLE are rejected while ringing. Bare STOP and the old time-only SET no longer work. Serial STOP is removed. GET does not disclose the saved digest. A digest is a QR identity, not BLE client authentication; this protocol does not add pairing or replay protection.

For commands over 20 ASCII bytes, write `BEGIN` and read `OK:BEGIN`, then write chunks of up to 19 command characters prefixed with `+`, reading `OK:PART` each time. Write `COMMIT` and read the operation result. Transfers expire after 10 seconds between chunks and are cleared on disconnect, invalid framing or a new BEGIN. App transactions are serialized and use writes with response. Error results never count as success.

## Automated checks

`tests/host/protocol_tests.cpp` includes the real firmware source with fake Arduino/BLE/RTC/NVS dependencies. It tests setup, settings reload, invalid times, missing QR, incorrect and correct dismissal, ringing mutation guards, storage failure, incomplete/expired/oversized transfers and disconnect recovery. These mocks do not validate radio timing, physical NVS power-loss behavior or camera behavior.

Run with a C++17 host compiler, for example:

```
g++ -std=c++17 -Itests/host/stubs tests/host/protocol_tests.cpp -o protocol_tests
./protocol_tests
```

In this task, the installed .NET Emscripten C++ compiler compiled the same tests to WebAssembly, executed with Node; all assertions passed.

Firmware build: `platformio run` passed (RAM 12.0%, flash 87.9%). Existing locally installed RTClib/Adafruit BusIO dependencies were reused.

Android build (from app directory):

```
dotnet build "QR code scanner.csproj" -f net10.0-android --no-restore -p:RuntimeIdentifier=android-arm64 -v minimal
```

Passed and produced an ARM64 APK. Four existing CA1416 warnings remain in Android MainActivity/BluetoothPermissions. The default multi-runtime build returned failure without a compiler error; specifying ARM64 succeeded.

## Physical checks still required

After separately approved firmware/app deployment: set an alarm with QR A, reconnect and restart the ESP32 to verify its association survives; let it ring; scan QR B and verify it keeps ringing; scan A and verify silence and acknowledgment. Try cancelling setup and dismissal, Android Back, rapid repeated detections, disconnect during save, and disabling/changing time while ringing. Repeat with a QR containing Unicode and punctuation. Check camera permission denial and Bluetooth permission behavior on the target phone.

The latest reset changes are integrated into both the saved PlatformIO project and saved MAUI project. Firmware and Android ARM64 builds passed, and reset tests passed for ringing, restart, legacy settings erasure, repeated clear, transfer cancellation and storage failure. This revision has not been uploaded or installed on hardware. Both the firmware and app need updating before using the reset button.

## Phone clock synchronization

The app sends `TIME:yyyyMMddHHmmss` using the phone's current local Gregorian date/time after connecting or refreshing, and immediately before saving an alarm (after QR scanning). The 19-byte command fits the default BLE payload. The timestamp is sampled after acquiring the BLE command lock and discovering the characteristic. Clock sync and SET use the same serialized transaction; SET is not sent if clock acknowledgment fails.

Firmware validates dates in 2000–2099 including leap days, updates the DS3231 and reads it back, allowing up to one second of elapsed time. Responses: `OK:TIME`, `ERR:TIME_FORMAT`, `ERR:RTC_SYNC`. RTC reads and writes share the alarm mutex. Sync does not clear or rearm a completed alarm, change the saved QR/time, or dismiss one already ringing. Existing exact-minute trigger semantics remain: moving the clock forward past a scheduled minute does not introduce catch-up ringing.

The serial monitor prints `[RTC] Synced to phone:` after success; compare this and subsequent `[ALARM] RTC=` logs with phone time. Ordinary BLE transport latency may add a small delay; this is not a precision clock synchronization protocol. Firmware and Android ARM64 builds and host protocol regression tests passed, including invalid dates, leap day, failed RTC write, corrected-time trigger and ringing/completion preservation. Physical synchronization still needs confirmation after updating both firmware and app; neither was deployed by this change.
