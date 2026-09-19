# Physical test started after explicit user authorization

Standalone firmware uploaded successfully on COM5 (CP210x), ESP32-D0WD-V3 revision3.1 MAC8c:94:df:96:06:dc. Upload hash verified; SUCCESS32.02seconds. Production source and MAUI unchanged.

Serial repeatedly reports:
```
[STATE] connected=0 pending=-1 dirty=0 clock=1 buttonReleased=0 sleepEligible=0
```
RTC clock is usable; no pending test alarm or storage write. GPIO32 reads continuously low; held-button protection correctly prevents sleep. User was asked to release/check the normally-open GPIO32-to-GND button and external10k pullup to3V3. No physical button wake, RTC wake, phone BLE connection/CRUD or QR/audio acceptance has yet been verified. Test firmware remains installed. Further testing awaits button wiring/release confirmation.
