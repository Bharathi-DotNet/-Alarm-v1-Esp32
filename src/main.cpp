#include <Arduino.h>
#include <Wire.h>
#include <RTClib.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <Preferences.h>
#include <freertos/semphr.h>
#ifdef ARDUINO
#include <esp_partition.h>
#endif
#include "alarm_audio.h"
#include "speaker_voice.h"
#include "music_receiver.h"
#define SERVICE_UUID "12345678-1234-1234-1234-1234567890ab"
#define CHARACTERISTIC_UUID "abcd1234-1234-1234-1234-abcdef123456"
RTC_DS3231 rtc;
Preferences preferences;
Preferences emergencyPreferences;
String emergencyHash;
const int buzzerPin = 23;
const int maxAlarms = 10;
struct Alarm {
    bool used = false, enabled = false, ringing = false;
    int hour = 0, minute = 0;
    String hash, name, backup;
    uint32_t lastDay = 0;
};
Alarm alarms[maxAlarms];
SemaphoreHandle_t alarmMutex;
String pendingCommand;
bool receivingCommand = false, connectionBeep = false, storageDirty = false;
uint32_t lastFragment = 0, connectionBeepStarted = 0;
bool validHex(const String &s) {
    for (unsigned int i=0;i<s.length();++i)
        if (!((s[i]>='0'&&s[i]<='9')||(s[i]>='A'&&s[i]<='F'))) return false;
    return true;
}
bool validHash(const String &s) { return s.length()==64 && validHex(s); }
bool digits(const String &s) {
    if (!s.length()) return false;
    for (unsigned int i=0;i<s.length();++i) if (!isDigit(s[i])) return false;
    return true;
}
bool validName(const String &s) { return s.length()<=48 && s.length()%2==0 && validHex(s); }
String timeText(int h,int m) { char text[6]; snprintf(text,sizeof(text),"%02d:%02d",h,m); return String(text); }
bool validTime(const String &s) {
    return s.length()==5 && s[2]==':' && digits(s.substring(0,2)) && digits(s.substring(3)) &&
        s.substring(0,2).toInt()<24 && s.substring(3).toInt()<60;
}
int split(const String &s,char delimiter,String *parts,int capacity) {
    int n=0,start=0;
    for (unsigned int i=0;i<=s.length();++i) if (i==s.length()||s[i]==delimiter) {
        if(n==capacity) return -1;
        parts[n++]=s.substring(start,i); start=i+1;
    }
    return n;
}
int activeAlarm() {
    int active=-1;
    for(int i=0;i<maxAlarms;++i) if(alarms[i].used&&alarms[i].ringing) {
        if(active<0 || alarms[i].lastDay<alarms[active].lastDay ||
            (alarms[i].lastDay==alarms[active].lastDay &&
             alarms[i].hour*60+alarms[i].minute<alarms[active].hour*60+alarms[active].minute)) active=i;
    }
    return active;
}
bool duplicateTime(const Alarm *items,int id,int h,int m) {
    for(int i=0;i<maxAlarms;++i) if(i!=id&&items[i].used&&items[i].hour==h&&items[i].minute==m) return true;
    return false;
}
bool persist(const Alarm *items) {
    String config="4";
    for(int i=0;i<maxAlarms;++i) {
        config+="|";
        if(!items[i].used) { config+="-"; continue; }
        config+=timeText(items[i].hour,items[i].minute)+":"+(items[i].enabled?"1:":"0:")+
            items[i].hash+":"+items[i].name+":"+String(items[i].lastDay)+":"+(items[i].ringing?"1":"0")+":"+items[i].backup;
    }
    return preferences.putString("configV4",config)==config.length();
}
bool commit(const Alarm *next) {
    if(!persist(next)) return false;
    for(int i=0;i<maxAlarms;++i) alarms[i]=next[i];
    storageDirty=false; return true;
}
void loadAlarms() {
    for(auto &alarm:alarms) alarm=Alarm();
    storageDirty=false;
    String config=preferences.getString("configV4","");
    bool migrating=!config.length();
    if(migrating) config=preferences.getString("configV3","");
    if(config.length()) {
        String rows[11]; Alarm loaded[maxAlarms];
        bool valid=split(config,'|',rows,11)==11 && rows[0]==(migrating?"3":"4");
        for(int i=0;i<maxAlarms&&valid;++i) {
            if(rows[i+1]=="-") continue;
            String f[8];
            valid=split(rows[i+1],':',f,8)==(migrating?7:8) && validTime(f[0]+":"+f[1]) &&
                (f[2]=="0"||f[2]=="1") && validHash(f[3]) && validName(f[4]) &&
                digits(f[5]) && f[5].length()<=5 && f[5].toInt()<=47481 && (f[6]=="0"||f[6]=="1");
            if(!migrating) valid=valid && (!f[7].length() || validHash(f[7]));
            if(!valid) break;
            auto &a=loaded[i]; a.used=true; a.hour=f[0].toInt(); a.minute=f[1].toInt();
            a.enabled=f[2]=="1"; a.hash=f[3]; a.name=f[4]; a.lastDay=f[5].toInt(); a.ringing=f[6]=="1"; a.backup=migrating?String(""):f[7];
            valid=(!a.ringing||a.enabled) && !duplicateTime(loaded,i,a.hour,a.minute);
        }
        if(valid) { for(int i=0;i<maxAlarms;++i) alarms[i]=loaded[i]; if(migrating) storageDirty=!persist(alarms); }
        else Serial.println("[STORAGE] Invalid multi-alarm settings; reset or reconfigure required.");
        return;
    }
    // Migrate a configured single alarm without losing its QR or enabled state.
    String legacy=preferences.getString("configV2","");
    if(legacy.length()==72 && validTime(legacy.substring(0,5)) && legacy[5]==':' &&
        (legacy[6]=='0'||legacy[6]=='1') && legacy[7]==':' && validHash(legacy.substring(8))) {
        auto &a=alarms[0]; a.used=true; a.hour=legacy.substring(0,2).toInt(); a.minute=legacy.substring(3,5).toInt();
        a.enabled=legacy[6]=='1'; a.hash=legacy.substring(8); a.name="416C61726D2031";
        storageDirty=!persist(alarms);
    }
}
String executeCommand(const String &command) {
    static String snapshot;
    static uint32_t snapshotId=0;
    if(command=="SNAP") {
        snapshot=""; ++snapshotId;
        int active=activeAlarm();
        for(int id=0;id<maxAlarms;++id) {
            if(id) snapshot+="|";
            auto &a=alarms[id];
            if(!a.used) { snapshot+="E:"+String(id); continue; }
            snapshot+="A:"+String(id)+":"+timeText(a.hour,a.minute)+":"+(a.enabled?"1:":"0:")+
                String(!a.ringing?0:active==id?1:2)+":"+(a.backup.length()?"1:":"0:")+a.name;
        }
        return "SNAP:"+String(snapshotId)+":"+String((int)((snapshot.length()+159)/160));
    }
    if(command.startsWith("SNAPGET:")) {
        String fields[3];
        if(split(command,':',fields,3)!=3 || fields[1]!=String(snapshotId) || !snapshot.length() ||
            !digits(fields[2]) || fields[2].length()!=1) return "ERR:SNAPSHOT";
        unsigned int page=fields[2].toInt(),offset=page*160;
        if(offset>=snapshot.length()) return "ERR:SNAPSHOT";
        return "S:"+String(snapshotId)+":"+String(page)+":"+snapshot.substring(offset,offset+160);
    }
    if(command.startsWith("AUDIO")) return AlarmAudio::command(command,activeAlarm()>=0);
    if(command=="AUTH") return validHash(emergencyHash)?"AUTH:1":"AUTH:0";
    if(command.startsWith("PASS:")) {
        String fields[3];
        if(split(command,':',fields,3)!=3 || !validHash(fields[2])) return "ERR:FORMAT";
        if(emergencyHash.length()) {
            if(fields[1]!=emergencyHash) return "ERR:PASSWORD";
        } else {
            if(fields[1]!="-") return "ERR:PASSWORD";
            if(activeAlarm()>=0) return "ERR:RINGING";
        }
        if(emergencyPreferences.putString("password",fields[2])!=fields[2].length()) return "ERR:STORAGE";
        emergencyHash=fields[2]; return "OK:PASS";
    }
    if(command.startsWith("EMERGENCY:")) {
        String supplied=command.substring(10);
        if(!validHash(supplied)) return "ERR:FORMAT";
        if(!validHash(emergencyHash)) return "ERR:NO_PASSWORD";
        if(supplied!=emergencyHash) return "ERR:PASSWORD";
        int active=activeAlarm();
        if(active<0) return "ERR:NOT_RINGING";
        Alarm next[maxAlarms]; for(int i=0;i<maxAlarms;++i) next[i]=alarms[i];
        next[active].ringing=false;
        if(!commit(next)) return "ERR:STORAGE";
        connectionBeep=false; digitalWrite(buzzerPin,LOW);
        return "OK:EMERGENCY";
    }
    if(command=="CAPS") return "CAPS:BACKUP:4";
    if(command=="LIST") return "ALARMS:3:10";
    // Local calendar time matches the phone's local alarm time (no UTC conversion).
    if (command.startsWith("TIME:"))
    {
        if (command.length() != 19) return "ERR:TIME_FORMAT";
        for (unsigned int i = 5; i < 19; ++i)
            if (!isDigit(command[i])) return "ERR:TIME_FORMAT";
        int year = command.substring(5, 9).toInt();
        int month = command.substring(9, 11).toInt();
        int day = command.substring(11, 13).toInt();
        int hour = command.substring(13, 15).toInt();
        int minute = command.substring(15, 17).toInt();
        int second = command.substring(17, 19).toInt();
        if (year < 2000 || year > 2099 || month < 1 || month > 12 ||
            hour > 23 || minute > 59 || second > 59) return "ERR:TIME_FORMAT";
        const int days[] = {31,28,31,30,31,30,31,31,30,31,30,31};
        int maxDay = days[month - 1] + (month == 2 && year % 4 == 0 ? 1 : 0);
        if (day < 1 || day > maxDay) return "ERR:TIME_FORMAT";
        DateTime target(year, month, day, hour, minute, second);
        rtc.adjust(target);
        uint32_t actual = rtc.now().unixtime();
        uint32_t expected = target.unixtime();
        if (actual < expected || actual - expected > 1) return "ERR:RTC_SYNC";
        Serial.printf("[RTC] Synced to phone: %04d-%02d-%02d %02d:%02d:%02d\n",
            year, month, day, hour, minute, second);
        return "OK:TIME";
    }
    if(command=="CLEAR") {
        connectionBeep=false; digitalWrite(buzzerPin,LOW);
        for(auto &a:alarms) { a.ringing=false; a.enabled=false; }
        if(!preferences.clear()) return "ERR:CLEAR_STORAGE";
        for(auto &a:alarms) a=Alarm();
        storageDirty=false; return "OK:CLEAR";
    }
    if(command.startsWith("STOP:")) {
        String hash=command.substring(5);
        if(!validHash(hash)) return "ERR:FORMAT";
        int active=activeAlarm();
        if(active<0) return "ERR:NOT_RINGING";
        if(alarms[active].hash!=hash && alarms[active].backup!=hash) return "ERR:QR_MISMATCH";
        Alarm next[maxAlarms]; for(int i=0;i<maxAlarms;++i) next[i]=alarms[i];
        next[active].ringing=false;
        if(!commit(next)) return "ERR:STORAGE";
        connectionBeep=false; digitalWrite(buzzerPin,LOW);
        return "OK:STOP";
    }
    String f[9]; int count=split(command,':',f,9);
    if(count<2 || f[1].length()!=1 || !digits(f[1])) return "ERR:COMMAND";
    int id=f[1].toInt();
    auto &a=alarms[id];
    if(f[0]=="BACKUP" && count==2) return a.used ? "B:"+String(id)+":"+(a.backup.length()?"1":"0") : "ERR:NOT_FOUND";
    if(f[0]=="GET"&&count==2) {
        if(!a.used) return "EMPTY:"+String(id);
        int state=!a.ringing?0:(activeAlarm()==id?1:2);
        return "A:"+String(id)+":"+timeText(a.hour,a.minute)+":"+(a.enabled?"1:":"0:")+String(state);
    }
    if(f[0]=="NAME"&&count==3) {
        if(!a.used) return "ERR:NOT_FOUND";
        if(f[2].length()!=1 || !digits(f[2]) || f[2].toInt()>3) return "ERR:FORMAT";
        int chunk=f[2].toInt(),start=chunk*12;
        return "N:"+String(id)+":"+String(chunk)+":"+(start<(int)a.name.length()?a.name.substring(start,start+12):String(""));
    }
    if(f[0]!="PUT"&&f[0]!="ON"&&f[0]!="OFF"&&f[0]!="DEL") return "ERR:COMMAND";
    if(a.ringing) return "ERR:RINGING";
    Alarm next[maxAlarms]; for(int i=0;i<maxAlarms;++i) next[i]=alarms[i];
    if(f[0]=="PUT") {
        if((count!=8 && count!=9) || !validTime(f[2]+":"+f[3]) || (f[4]!="0"&&f[4]!="1") || !validName(f[7])) return "ERR:FORMAT";
        int hour=f[2].toInt(),minute=f[3].toInt();
        if(duplicateTime(alarms,id,hour,minute)) return "ERR:DUPLICATE";
        // Field 6 is reserved version token, making incompatible saves fail explicitly.
        if(!((f[6]=="3" && count==8) || (f[6]=="4" && count==9))) return "ERR:FORMAT";
        String backup=a.backup;
        if(count==9 && f[8]!="-") {
            if(f[8]!="0" && !validHash(f[8])) return "ERR:FORMAT";
            backup=f[8]=="0"?String(""):f[8];
        }
        String hash=f[5]=="-"&&a.used?a.hash:f[5];
        if(!validHash(hash)) return "ERR:QR_REQUIRED";
        auto &n=next[id];
        if(!a.used||a.hour!=hour||a.minute!=minute) n.lastDay=0;
        n.used=true; n.enabled=f[4]=="1"; n.hour=hour; n.minute=minute; n.hash=hash; n.name=f[7]; n.backup=backup;
    } else {
        if(count!=2) return "ERR:FORMAT";
        if(!a.used) return "ERR:NOT_FOUND";
        if(f[0]=="DEL") next[id]=Alarm();
        else next[id].enabled=f[0]=="ON";
    }
    if(!commit(next)) return "ERR:STORAGE";
    return "OK:"+f[0];
}
class AlarmServerCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer *) override
    {
        Serial.println("[BLE] Connected.");
    }
    void onDisconnect(BLEServer *) override
    {
        xSemaphoreTake(alarmMutex, portMAX_DELAY);
        pendingCommand = "";
        receivingCommand = false;
        AlarmAudio::abort();
        xSemaphoreGive(alarmMutex);
        BLEDevice::startAdvertising();
    }
};
class AudioUploadCallback : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* characteristic) override {
        auto bytes=characteristic->getValue();
        xSemaphoreTake(alarmMutex,portMAX_DELAY);
        AlarmAudio::chunk((const uint8_t*)bytes.data(),bytes.size(),activeAlarm()>=0);
        xSemaphoreGive(alarmMutex);
    }
};
class AlarmCommandCallback : public BLECharacteristicCallbacks
{
    void onWrite(BLECharacteristic *characteristic) override
    {
        String command = characteristic->getValue().c_str();
        xSemaphoreTake(alarmMutex, portMAX_DELAY);
        String response;
        // Framing keeps every write within the default 20-byte BLE payload.
        if (command == "BEGIN")
        {
            pendingCommand = "";
            receivingCommand = true;
            lastFragment = millis();
            response = "OK:BEGIN";
        }
        else if (command.startsWith("+") || command == "COMMIT")
        {
            if (!receivingCommand || millis() - lastFragment > 10000)
            {
                receivingCommand = false;
                pendingCommand = "";
                response = "ERR:TRANSFER";
            }
            else if (command == "COMMIT")
            {
                receivingCommand = false;
                response = executeCommand(pendingCommand);
                pendingCommand = "";
            }
            else if (command.length() < 2 || command.length() > 20 || pendingCommand.length() + command.length() - 1 > 200)
            {
                receivingCommand = false;
                pendingCommand = "";
                response = "ERR:FORMAT";
            }
            else
            {
                pendingCommand += command.substring(1);
                lastFragment = millis();
                response = "OK:PART";
            }
        }
        else
        {
            receivingCommand = false;
            pendingCommand = "";
            response = executeCommand(command);
        }
        // Log responses only; never print QR data or fingerprints.
        if(response!="OK:EMERGENCY") Serial.printf("[BLE] response=%s\n", response.c_str());
        characteristic->setValue(response.c_str());
        xSemaphoreGive(alarmMutex);
    }
};
void setup()
{
    Serial.begin(115200);
    pinMode(buzzerPin, OUTPUT);
    digitalWrite(buzzerPin, LOW);
    alarmMutex = xSemaphoreCreateMutex();
    Wire.begin(21, 22);
    if (!rtc.begin())
    {
        Serial.println("DS3231 NOT FOUND!");
        while (true) delay(1000);
    }
    if (rtc.lostPower())
    {
        Serial.println("[RTC] Lost power: restoring firmware compile time.");
        rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    }
    preferences.begin("alarm", false);
    loadAlarms();
    emergencyPreferences.begin("alarm-auth", false);
    emergencyHash=emergencyPreferences.getString("password", "");
    AlarmAudio::begin();
    Serial.println(SpeakerVoice::begin()?"[VOICE] Ready: BCLK26 LRC25 DIN27.":"[VOICE] Unavailable; using connection beep.");
    BLEDevice::init("AlarmPrototype");
    BLEServer *server = BLEDevice::createServer();
    server->setCallbacks(new AlarmServerCallbacks());
    BLEService *service = server->createService(SERVICE_UUID);
    BLECharacteristic *characteristic = service->createCharacteristic(
        CHARACTERISTIC_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE);
    characteristic->setCallbacks(new AlarmCommandCallback());
    characteristic->setValue(executeCommand("LIST").c_str());
    BLECharacteristic* audio=service->createCharacteristic(
        "abcd1234-1234-1234-1234-abcdef123457",BLECharacteristic::PROPERTY_WRITE);
    audio->setCallbacks(new AudioUploadCallback());
    service->start();
    BLEAdvertising *advertising = BLEDevice::getAdvertising();
    advertising->addServiceUUID(SERVICE_UUID);
    advertising->start();
    MusicReceiver::begin();
    Serial.println("Alarm ready. Scan a QR in the app to configure.");
}
void loop() {
    xSemaphoreTake(alarmMutex,portMAX_DELAY);
    DateTime now=rtc.now();
    uint32_t day=now.unixtime()/86400;
    bool changed=false;
    for(int i=0;i<maxAlarms;++i) {
        auto &a=alarms[i];
        if(a.used&&a.enabled&&!a.ringing&&day>a.lastDay&&now.hour()==a.hour&&now.minute()==a.minute) {
            a.ringing=true; a.lastDay=day; changed=true;
            Serial.printf("[ALARM] Due slot=%d; task pending.\n",i);
        }
    }
    static uint32_t lastRetry=0;
    if(changed || (storageDirty&&millis()-lastRetry>=5000)) {
        storageDirty=!persist(alarms); lastRetry=millis();
        if(storageDirty) Serial.println("[STORAGE] Could not persist pending state; retrying.");
    }
    static bool first=true; static uint32_t lastLog=0;
    if(first||millis()-lastLog>=5000) {
        first=false;lastLog=millis();
        Serial.printf("[ALARM] RTC=%02d:%02d:%02d active=%d\n",now.hour(),now.minute(),now.second(),activeAlarm());
    }
    bool ringing=activeAlarm()>=0;
    SpeakerVoice::setAlarmActive(ringing);
    if(ringing||(connectionBeep&&millis()-connectionBeepStarted>=150)) connectionBeep=false;
    digitalWrite(buzzerPin,(ringing?(millis()/500)%2==0:connectionBeep)?HIGH:LOW);
    xSemaphoreGive(alarmMutex);delay(20);
}
