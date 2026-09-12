# Multiple daily QR alarms — protocol v3

## Behavior

Up to 10 independent daily alarms live on ESP32, each with a slot ID, local hour/minute, enabled flag, QR fingerprint and name. Duplicate HH:MM is rejected even when the other alarm is disabled; both app validation and firmware reject it without modifying existing records. Each alarm can fire once per local calendar day. Dismissal does not disable it, so it repeats the next day. ON/OFF does not replay a task already completed that day. Editing its time schedules a new occurrence; editing its name/QR alone retains its daily completion history.

There is one audible task at a time. If a different-time alarm becomes due while an earlier task is unfinished, it stays pending. Only the oldest pending alarm's matching QR dismisses that task, then the next pending task becomes active. Pending alarms cannot be edited, disabled or deleted. A shared QR does not dismiss all pending alarms in one scan. An unresolved alarm remains pending across midnight; no additional duplicate occurrence of that same alarm accumulates until it is dismissed.

All ten records are written as one `configV3` value in the `alarm` Preferences namespace. Each record includes its last-triggered day and pending state, so a normal reboot does not replay a completed alarm or forget an unfinished task. Physical power-loss/NVS fault testing is still required. Persistence failures reject edits and dismissal; trigger-state persistence failures keep ringing in RAM and retry. Testing CLEAR still stops ringing without a QR and erases the alarm namespace. This is deliberately a testing bypass.

On the first v3 boot, a valid v2 single alarm is copied into slot 0, preserving its time, enabled flag and QR. Name defaults to Alarm 1. Legacy settings without a QR are not enabled/migrated as a valid alarm. Invalid v3 storage is logged and not silently replaced from older data. Back up or inspect storage before production recovery; no physical migration has been performed by the agent.

## BLE commands

Service and characteristic UUIDs remain unchanged. All responses fit the default BLE read payload. Writes over 20 bytes use BEGIN / +19-character fragments / COMMIT with acknowledgments, a 140-character command limit, and 10-second inter-fragment timeout. Disconnect and invalid transfers clear the buffer.

- `LIST` -> `ALARMS:3:10`
- `GET:<id>` -> `EMPTY:<id>` or `A:<id>:HH:MM:<enabled>:<state>`
- State 0 = not pending, 1 = active audible task, 2 = waiting behind an earlier task.
- `NAME:<id>:<chunk>` -> `N:<id>:<chunk>:<up to 12 hex characters>`; chunks 0..3, UTF-8 hex name up to 24 bytes.
- `PUT:<id>:HH:MM:<enabled>:<hash-or-dash>:3:<name-hex>` -> `OK:PUT`. Dash keeps an existing slot's QR; a new slot requires a hash. Duplicate time -> `ERR:DUPLICATE`.
- `ON:<id>`, `OFF:<id>`, `DEL:<id>` -> corresponding OK result. Pending target -> `ERR:RINGING`.
- `STOP:<64-uppercase-hex SHA256 of exact UTF-8 QR>` -> `OK:STOP` only for the oldest pending task's match.
- `CLEAR` -> `OK:CLEAR` (testing only); storage erase failure -> `ERR:CLEAR_STORAGE`.
- `TIME:yyyyMMddHHmmss` -> `OK:TIME` after date validation and DS3231 readback (2000–2099). Phone local time is sampled just before transfer. A save is not sent if clock sync fails.

Bare legacy SET/GET/ENABLE/DISABLE commands are no longer supported. Update firmware and app together. QR hashing identifies the QR; this protocol does not add BLE authentication or replay protection.

## App

The new Rise screen shows daily alarm cards, enabled toggles, next alarm, active/pending tasks, Add/Edit dialog, QR association/replacement and deletion confirmation. Device data is refreshed every 10 seconds while connected and not editing. Names are refreshed on explicit refresh/mutations. The test reset is inside a separate expandable Testing tools section. Android's enable-Bluetooth prompt/auto-connect, one connection beep, offline operation and phone clock sync remain.

UI uses no remote fonts/images and requires no internet. Alarm names are limited to 24 UTF-8 bytes; overlong names show an error. Duplicate saves leave the editor open so the user can choose another time. The browser preview uses the actual Razor template with fixture data and is not a live BLE session.

## Validation

- PlatformIO ESP32 build passed: RAM 12.2%, flash 88.5% at the initial v3 build.
- Android ARM64 build passed; two preexisting CA1416 warnings remain in the unused custom BluetoothPermissions class.
- `tests/host/protocol_tests.cpp` compiles the actual firmware with hardware stubs. Passing cases include migration, 10 slots, duplicate add/edit/disabled rejection, QR retention, names, persistence failures, pending order, reload, daily repeat, year rollover, time validation, framing, clear and connection beep.
- `tests/ui-preview` links the actual AlarmProtocol and Razor page, checks duplicate/Unicode/invariant-format/response behavior and renders list, editor, empty and ringing states.
- Rendered phone-width list/editor and desktop ringing state were visually checked in the in-app browser. Actual phone camera, Bluetooth delivery, 24-hour recurrence and device reboot tests are not performed by these host checks.

Firmware build: `platformio run`. Android build from app directory: `dotnet build "QR code scanner.csproj" -f net10.0-android --no-restore -p:RuntimeIdentifier=android-arm64`.

Host C++ test: `g++ -std=c++17 -Itests/host/stubs tests/host/protocol_tests.cpp -o protocol_tests` then run it. On this PC the installed Emscripten compiler and Node execute the same tests.

Physical check after separately approved deployment: verify old alarm appears in slot 0; add two distinct times and QR codes; reject a duplicate including a disabled alarm; edit a name while retaining QR; test wrong/matching dismissal; verify later pending task cannot be skipped; verify next-day repeat and same-minute reboot do not duplicate a completed task; test 10-slot limit, deletion, Bluetooth prompt and testing reset. Firmware source and tests are integrated into the saved Documents PlatformIO project. App changes are in the saved MAUI project. No firmware upload or APK installation was performed for this revision.
