#pragma once
#include <esp_sleep.h>
#include <driver/rtc_io.h>
#include <esp_bt.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
static constexpr gpio_num_t BUTTON=GPIO_NUM_32, RTC_INT=GPIO_NUM_27;
struct WakeRecord { uint32_t magic,epoch,revision; int slot; };
RTC_DATA_ATTR WakeRecord armed={0,0,0,-1};
static bool preparing=false, speakerReady=false;
static uint32_t prepareAt=0, buttonReleasedAt=0, retryAt=0;
static bool retryWaiting=false;
static bool releaseTracking=false;
static bool rtcResponds() { Wire.beginTransmission(0x68);return Wire.endTransmission()==0; }
static bool readReg(uint8_t reg,uint8_t &value) {
 Wire.beginTransmission(0x68);Wire.write(reg);
 if(Wire.endTransmission(false)!=0 || Wire.requestFrom(uint8_t(0x68),uint8_t(1))!=1) return false;
 value=Wire.read();return true;
}
static bool clearInterrupts() {
 rtc.disableAlarm(1);rtc.disableAlarm(2);rtc.clearAlarm(1);rtc.clearAlarm(2);
 rtc.writeSqwPinMode(DS3231_OFF);
 uint8_t ctrl=0,stat=0;
 return readReg(0x0e,ctrl)&&readReg(0x0f,stat)&&(ctrl&7)==4&&(stat&3)==0;
}
static void resumeAdvertising(const char* why) {
 Serial.printf("[SLEEP] Cancelled/blocked: %s\n",why);
 preparing=false;retryWaiting=true;retryAt=millis();BLEDevice::startAdvertising();
}
static bool healthyClock(DateTime &now) {
 if(!rtcAvailable||!rtcResponds()) {rtcTrusted=false;return false;}
 if(!rtcAvailable||!rtcResponds()) { return false; }
 now=rtc.now();
 if(!now.isValid()||rtc.lostPower()) {rtcTrusted=false;return false;}
 return rtcTrusted;
 if(!now.isValid()) { return false; }
 return true;
}
static bool programNext(DateTime now) {
 uint32_t when;int slot=WakeTest::selectNext(alarms,maxAlarms,now.unixtime(),when);
 armed={0,0,0,-1};
 if(!clearInterrupts()) return false;
 if(slot<0) {Serial.println("[RTC] No enabled alarm; next sleep is BUTTON wake only.");return true;}
 DateTime target(when);
 if(!target.isValid()||target.year()>2099||!rtc.setAlarm1(target,DS3231_A1_Date))return false;
 // setAlarm1 does not propagate I2C write failures; read back every alarm/control byte.
 uint8_t values[5];
 for(int i=0;i<4;++i) if(!readReg(0x07+i,values[i]))return false;
 if(!readReg(0x0e,values[4]))return false;
 auto bcd=[](uint8_t n){return uint8_t((n/10)*16+n%10);};
 if(values[0]!=bcd(target.second())||values[1]!=bcd(target.minute())||values[2]!=bcd(target.hour())||values[3]!=bcd(target.day())||(values[4]&7)!=5)return false;
 armed={0x574b5431,when,alarms[slot].revision,slot};
 Serial.printf("[RTC] Armed slot=%d for %04d-%02d-%02d %02d:%02d:%02d; INT33 active LOW.\n",slot,target.year(),target.month(),target.day(),target.hour(),target.minute(),target.second());
 return true;
}
static void recoverOccurrence(DateTime now,esp_sleep_wakeup_cause_t cause) {
 if(cause!=ESP_SLEEP_WAKEUP_EXT0&&cause!=ESP_SLEEP_WAKEUP_EXT1)return;
 if(armed.magic!=0x574b5431||armed.slot<0||armed.slot>=maxAlarms||now.unixtime()<armed.epoch)return;
 auto &a=alarms[armed.slot];
 if(WakeTest::recoverDue(a,armed.revision,armed.epoch,now.unixtime())) {
    storageDirty=true;
    Serial.printf("[WAKE] Restored armed occurrence slot=%d even if boot crossed minute boundary.\n",armed.slot);
 }
}
void setup() {
 WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Disable brownout reset for breadboard testing
 Serial.begin(115200);delay(100);
 auto cause=esp_sleep_get_wakeup_cause();
 Serial.println("\n=======================================================");
 if (cause == ESP_SLEEP_WAKEUP_EXT1) {
     Serial.println("⏰ [WAKE UP] ESP32 woke up by WAKE BUTTON PRESS (GPIO 32)!");
 } else if (cause == ESP_SLEEP_WAKEUP_EXT0) {
     Serial.println("⏰ [WAKE UP] ESP32 woke up by RTC ALARM TRIGGER (GPIO 33)!");
 } else {
     Serial.println("⏰ [POWER ON / RESET] ESP32 initialized / rebooted.");
 }
 Serial.printf("⏰ [WAKE CAUSE]: %d (%s)\n",int(cause),cause==ESP_SLEEP_WAKEUP_EXT0?"RTC33":cause==ESP_SLEEP_WAKEUP_EXT1?"BUTTON32":"POWER/RESET");
 if(cause==ESP_SLEEP_WAKEUP_EXT1)Serial.printf("[WAKE] EXT1 mask=0x%llx\n",esp_sleep_get_ext1_wakeup_status());
 rtc_gpio_deinit(BUTTON);rtc_gpio_deinit(RTC_INT);
 pinMode(BUTTON,INPUT_PULLUP);pinMode(RTC_INT,INPUT_PULLUP);
 gpio_pullup_en(BUTTON);gpio_pullup_en(RTC_INT);
 rtc_gpio_pullup_en(BUTTON);rtc_gpio_pullup_en(RTC_INT);
 Serial.printf("[WAKE] Pin Levels: Button(GPIO32)=%d, RTC_INT(GPIO27)=%d\n",digitalRead(BUTTON),digitalRead(RTC_INT));
 alarmMutex=xSemaphoreCreateMutex();Wire.begin(21,22);Wire.setTimeOut(50);
 rtcAvailable=rtc.begin();
 if(rtcAvailable) {
    if(rtc.lostPower()) {
        Serial.println("[RTC] Lost power: adjusting to firmware compile time.");
        rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    }
    DateTime now=rtc.now();
    rtcTrusted=now.isValid();
    bool fired=rtc.alarmFired(1);
    Serial.printf("⏰ [RTC TIME]: %04d-%02d-%02d %02d:%02d:%02d (Trusted=%d, A1flag=%d)\n",
        now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second(), rtcTrusted, fired);
    if(!clearInterrupts())Serial.println("[RTC] Note: cleared pending alarm flags.");
 } else Serial.println("[RTC] Missing: BLE available; clock/sleep scheduling blocked.");
 bool storageOk=preferences.begin("alarm",false);
 bool missionOk=missionPreferences.begin("mission",false);
 bool emergencyOk=emergencyPreferences.begin("alarm-auth",false);
 bool volumeOk=volumePreferences.begin("volume",false);
 storageOk=storageOk&&missionOk&&emergencyOk&&volumeOk;
 loadAlarms();configHealthy=configHealthy&&storageOk;
 emergencyHash=emergencyPreferences.getString("password","");
 int level=volumePreferences.getString("level","100").toInt();
 AudioSamples::volumePercent.store(level>=25&&level<=100?level:100);
 Serial.printf("[AUDIO] Restored volume: %d%%\n", AudioSamples::volumePercent.load());
 AlarmAudio::begin();
 if(rtcTrusted)recoverOccurrence(rtc.now(),cause);
 armed.magic=0;
 speakerReady=SpeakerVoice::begin();Serial.println(speakerReady?"[AUDIO] Ready: 25/26/33.":"[AUDIO] FAILED; sleep blocked.");
 if(speakerReady) {
     Serial.println("🔊 [AUDIO TEST] Step 1: Playing 3-second alarm tone on GPIO 25/26/33...");
     SpeakerVoice::playTestTone(3000);
     delay(400);
     Serial.println("🔊 [AUDIO TEST] Step 2: Playing voice announcement...");
     SpeakerVoice::request(true);
     delay(1800);
     Serial.println("🔊 [AUDIO TEST] Boot sound test completed.");
 }
 if(rtcTrusted)updateDue(rtc.now());else SpeakerVoice::setAlarmActive(activeAlarm()>=0);
 BLEDevice::init("AlarmPrototype");testServer=BLEDevice::createServer();testServer->setCallbacks(new AlarmServerCallbacks());
 auto svc=testServer->createService(SERVICE_UUID);
 auto chr=svc->createCharacteristic(CHARACTERISTIC_UUID,BLECharacteristic::PROPERTY_READ|BLECharacteristic::PROPERTY_WRITE);
 chr->setCallbacks(new AlarmCommandCallback());chr->setValue(executeCommand("LIST").c_str());
 BLECharacteristic* audio=svc->createCharacteristic("abcd1234-1234-1234-1234-abcdef123457",BLECharacteristic::PROPERTY_WRITE);
 audio->setCallbacks(new AudioUploadCallback());
 svc->start();
 auto adv=BLEDevice::getAdvertising();adv->addServiceUUID(SERVICE_UUID);wakePolicy.boot(millis());adv->start();
 MusicReceiver::begin();
 Serial.println("📡 [BLE ADVERTISING] Device Name: AlarmPrototype");
 Serial.println("🔊 [AUDIO COMMANDS] Type 't' in Serial Monitor for alarm tone, 'v' for voice!");
 Serial.println("⏳ [FALLBACK TIMER] 120s (2 minutes) countdown started. Will sleep if no app connects.");
 Serial.println("=======================================================\n");
}
void loop() {
 if (Serial.available()) {
     char cmd = Serial.read();
     if (cmd == 't' || cmd == 'T') {
         Serial.println("\n🔊 [TEST] Serial command: Playing 3-second alarm tone...");
         wakePolicy.boot(millis());
         SpeakerVoice::playTestTone(3000);
     } else if (cmd == 'v' || cmd == 'V') {
         Serial.println("\n🔊 [TEST] Serial command: Playing voice announcement...");
         wakePolicy.boot(millis());
         SpeakerVoice::request(true);
     }
 }
 xSemaphoreTake(alarmMutex,portMAX_DELAY);
 DateTime now(2000,1,1,0,0,0);bool clockOk=healthyClock(now);
 if(clockOk)updateDue(now);else SpeakerVoice::setAlarmActive(activeAlarm()>=0);
 bool released=digitalRead(BUTTON)==HIGH;
 if(!released)releaseTracking=false;
 else if(!releaseTracking){releaseTracking=true;buttonReleasedAt=millis();}
 bool stable=released&&uint32_t(millis()-buttonReleasedAt)>=100;
 if(retryWaiting&&uint32_t(millis()-retryAt)>=1000)retryWaiting=false;
 bool ready=!retryWaiting&&wakePolicy.canSleep(millis(),activeAlarm()>=0,storageDirty,clockOk&&configHealthy&&speakerReady,stable)&&!linkConnected.load();
 static uint32_t lastLog=0;
 if(uint32_t(millis()-lastLog)>=5000) {
    lastLog=millis();
    if (!linkConnected.load()) {
        uint32_t remSec = (wakePolicy.remainingMs(millis()) + 999) / 1000;
        if (wakePolicy.everConnected) {
            Serial.printf("⏳ [GRACE COUNTDOWN] BLE disconnected. Deep sleep in %u s (RTC=%02d:%02d:%02d)\n", remSec, now.hour(), now.minute(), now.second());
        } else {
            Serial.printf("⏳ [FALLBACK COUNTDOWN] Waiting for App... Deep sleep in %u s (RTC=%02d:%02d:%02d)\n", remSec, now.hour(), now.minute(), now.second());
        }
    } else {
        Serial.printf("📱 [APP CONNECTED] ESP32 awake & configuring. (RTC=%02d:%02d:%02d)\n", now.hour(), now.minute(), now.second());
    }
 }
 if (wakePolicy.expired(millis()) && !ready) {
    static uint32_t lastBlockLog = 0;
    if (uint32_t(millis() - lastBlockLog) >= 5000) {
        lastBlockLog = millis();
        Serial.println("⚠️ [SLEEP BLOCKED] Cannot sleep yet due to:");
        if (linkConnected.load()) Serial.println("   ❌ BLE link is flagged connected");
        if (activeAlarm() >= 0) Serial.printf("   ❌ Alarm is currently ringing (Slot %d)\n", activeAlarm());
        if (storageDirty) Serial.println("   ❌ Storage dirty (pending write)");
        if (!clockOk) Serial.println("   ❌ RTC Clock not responding or invalid time");
        if (!configHealthy) Serial.println("   ❌ Config invalid in storage");
        if (!speakerReady) Serial.println("   ❌ Speaker initialization failed");
        if (!stable) Serial.printf("   ❌ Wake Button (GPIO 32) reading LOW (Level=%d, need HIGH/released)\n", digitalRead(BUTTON));
        if (retryWaiting) Serial.println("   ❌ Retry cooldown waiting");
    }
 }
 if(!ready) { if(preparing)resumeAdvertising("link/alarm/storage/clock/button changed"); }
 else if(!preparing) {
    BLEDevice::getAdvertising()->stop();preparing=true;prepareAt=millis();
    Serial.println("[SLEEP] Target reached; advertising stopped; settling BLE events...");
 } else if(uint32_t(millis()-prepareAt)>=150) {
    if(testServer->getConnectedCount()!=0 || linkConnected.load())resumeAdvertising("BLE connected during preparation");
    else if(!programNext(now))resumeAdvertising("RTC alarm programming/readback failed");
    else {
        DateTime finalNow(2000,1,1,0,0,0);bool finalClock=healthyClock(finalNow);
        if(finalClock)updateDue(finalNow);
        bool rtcWake=armed.magic==0x574b5431;
        if(!finalClock||activeAlarm()>=0||storageDirty||digitalRead(BUTTON)==LOW||linkConnected.load()||testServer->getConnectedCount()!=0 ||
           (rtcWake&&(digitalRead(RTC_INT)==LOW||finalNow.unixtime()>=armed.epoch))) {
            resumeAdvertising("due alarm, low wake pin, clock failure or late connection");
        } else {
            esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);
            // Single-pin ALL_LOW implements active-low button independently of RTC EXT0.
            esp_err_t buttonResult=esp_sleep_enable_ext1_wakeup(1ULL<<32,ESP_EXT1_WAKEUP_ALL_LOW);
            esp_err_t rtcResult=rtcWake?esp_sleep_enable_ext0_wakeup(RTC_INT,0):ESP_OK;
            if(buttonResult!=ESP_OK||rtcResult!=ESP_OK)resumeAdvertising("wake source configuration failed");
            else {
                Serial.println("\n=======================================================");
                Serial.println("😴 [DEEP SLEEP] ENTERING DEEP SLEEP NOW to conserve battery!");
                if (rtcWake) {
                    DateTime target(armed.epoch);
                    Serial.printf("⏰ [NEXT SCHEDULED WAKE]: Slot %d at %04d-%02d-%02d %02d:%02d:%02d (RTC INT GPIO 33)\n",
                        armed.slot, target.year(), target.month(), target.day(), target.hour(), target.minute(), target.second());
                } else {
                    Serial.println("⏰ [NEXT SCHEDULED WAKE]: No alarm enabled. Wakeable by BUTTON (GPIO 32) only.");
                }
                Serial.println("🔘 [BUTTON WAKE]: Press WAKE button (GPIO 32) anytime to wake up.");
                Serial.println("💤 [GOODNIGHT] ESP32 entering sleep now. Zzzz...");
                Serial.println("=======================================================\n");
                // No active link, no pending alarm; callbacks blocked only for this final commit.
                Serial.flush();
                // A connect callback sets the atomic flag before taking the alarm mutex.
                // Recheck after slow UART flushing, immediately before committing to sleep.
                if(linkConnected.load()||testServer->getConnectedCount()!=0||digitalRead(BUTTON)==LOW||(rtcWake&&digitalRead(RTC_INT)==LOW)) {
                    resumeAdvertising("late link or asserted wake pin at final commit");
                    xSemaphoreGive(alarmMutex);delay(20);return;
                }
                i2s_zero_dma_buffer(I2S_NUM_1);i2s_stop(I2S_NUM_1);
                esp_deep_sleep_start();
            }
        }
    }
 }
 xSemaphoreGive(alarmMutex);delay(20);
}

