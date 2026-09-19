# Validation — standalone wake/BLE/sleep v1

Prepared 2026-09-19. No upload, serial monitor, device-port access or physical testing was performed.

- Final PlatformIO `wake-ble-sleep` build: SUCCESS, 10.04 seconds; RAM 40,420 / 327,680 bytes (12.3%), flash 1,201,189 / 1,310,720 bytes (91.6%).
- Host tests: PASS. Actual copied protocol plus shared policy/scheduler tested for framed multiple CRUD operations per connection, persistence reload, failed writes, duplicate rejection, 120-second initial timeout, 10-second disconnect grace, reconnect cancellation, unsigned millis rollover, disabled alarm exclusion, pending sleep prevention, QR dismissal, recovery after minute-boundary boot, backward clock and year rollover, no-enabled button-only selection.
- `verify_unchanged.py`: checked all 35 pre-existing project files captured before creation (excluding generated .pio/.git directories); changes: **0**. No MAUI files were written.
- Full source/config/local library copies, host stubs, docs and generated build files reside in this new directory. No includes of mutable parent-project source are needed.
- Firmware SHA256: `fc0b586315e4a5c910aa9f28ef28095e917602ce9f903ea741222f1b6cf5edde`.

Not established by these checks: actual wake cause/pin electrical behavior, measured timing of phone BLE events, late-connect radio race behavior, speaker audibility, DS3231 interrupt assertion or battery current. Run the README bench checklist only after separate upload go-ahead. Host tests are not a hardware simulator.

Next action is user-authorized physical testing; implementation work is complete for this standalone iteration. Production integration is intentionally not performed.
