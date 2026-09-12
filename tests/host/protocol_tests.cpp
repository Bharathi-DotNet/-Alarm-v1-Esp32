#include "../../src/main.cpp"
#include <cassert>
#include <iostream>
BLECharacteristic characteristic;
AlarmCommandCallback callback;
String send(String command){characteristic.setValue(command.c_str());static_cast<BLECharacteristicCallbacks&>(callback).onWrite(&characteristic);return characteristic.getValue();}
String transfer(String command){assert(send("BEGIN")=="OK:BEGIN");for(size_t i=0;i<command.length();i+=19)assert(send(String("+")+command.substring(i,std::min(i+19,command.length())))=="OK:PART");return send("COMMIT");}
int main(){
    String hash=std::string(64,'A'), wrong=std::string(64,'B');
    setup(); assert(!alarmEnabled); assert(send("ENABLE")=="ERR:QR_REQUIRED");
    assert(send("SET:07:00")=="ERR:FORMAT");
    assert(transfer(String("SET:24:00:")+hash)=="ERR:FORMAT");
    assert(transfer(String("SET:07:60:")+hash)=="ERR:FORMAT");
    assert(transfer(String("SET:xx:00:")+hash)=="ERR:FORMAT");
    assert(transfer(String("SET:07:00:")+hash)=="OK:SET");
    assert(send("GET")=="STATE:07:00:1:1:0");
    alarmEnabled=false;qrHash="";alarmHour=3;setup();
    assert(alarmEnabled&&qrHash==hash&&alarmHour==7); // NVS reload
    assert(transfer(String("STOP:")+hash)=="ERR:NOT_RINGING");
    loop();assert(alarmTriggered);
    assert(send("STOP")=="ERR:COMMAND");
    assert(transfer(String("STOP:")+wrong)=="ERR:QR_MISMATCH");assert(alarmTriggered);
    assert(send("DISABLE")=="ERR:RINGING");assert(send("ENABLE")=="ERR:RINGING");
    assert(transfer(String("SET:09:30:")+wrong)=="ERR:RINGING");assert(qrHash==hash);
    assert(transfer(String("STOP:")+hash)=="OK:STOP");assert(!alarmTriggered&&buzzerValue==LOW);
    loop();assert(!alarmTriggered); // no re-trigger in same minute
    assert(send("DISABLE")=="OK:DISABLE");
    auto saved=preferences.values["configV2"];
    preferences.fail=true;assert(transfer(String("SET:08:30:")+wrong)=="ERR:STORAGE");
    assert(qrHash==hash&&!alarmEnabled&&preferences.values["configV2"]==saved);preferences.fail=false;
    assert(send("BEGIN")=="OK:BEGIN");assert(send("+SET:09:30:")=="OK:PART");
    assert(send("COMMIT")=="ERR:FORMAT");assert(qrHash==hash);
    send("BEGIN");fakeMillis+=10001;assert(send("+SET")=="ERR:TRANSFER");
    send("BEGIN");assert(send(String("+")+std::string(20,'A'))=="ERR:FORMAT");
    send("BEGIN");send("+SET:09:30:");AlarmServerCallbacks server;
    static_cast<BLEServerCallbacks&>(server).onDisconnect(nullptr);assert(send("COMMIT")=="ERR:TRANSFER");
    assert(transfer(String("SET:09:30:")+wrong)=="OK:SET");assert(qrHash==wrong);
    alarmEnabled=false;qrHash="";setup();assert(qrHash==wrong&&alarmEnabled&&alarmMinute==30);
    alarmTriggered=true;buzzerValue=HIGH;
    preferences.values["hour"]="22";preferences.values["minute"]="44";
    send("BEGIN");send("+SET:08:30:");
    assert(send("CLEAR")=="OK:CLEAR");
    assert(!alarmTriggered&&!alarmEnabled&&qrHash.length()==0&&buzzerValue==LOW);
    assert(preferences.values.empty());assert(send("COMMIT")=="ERR:TRANSFER");
    assert(send("GET")=="STATE:00:00:0:0:0");
    setup();assert(send("GET")=="STATE:00:00:0:0:0");loop();assert(!alarmTriggered);
    assert(send("ENABLE")=="ERR:QR_REQUIRED");assert(send("CLEAR")=="OK:CLEAR");
    assert(transfer(String("SET:07:00:")+hash)=="OK:SET");loop();assert(alarmTriggered);
    preferences.fail=true;assert(send("CLEAR")=="ERR:CLEAR_STORAGE");
    assert(!alarmTriggered&&!alarmEnabled&&buzzerValue==LOW&&qrHash==hash);
    preferences.fail=false;assert(send("CLEAR")=="OK:CLEAR");assert(preferences.values.empty());
    auto connect = [&](){static_cast<BLEServerCallbacks&>(server).onConnect(nullptr);};
    connect();assert(connectionBeep&&buzzerValue==HIGH);
    fakeMillis+=149;loop();assert(buzzerValue==HIGH);
    loop();assert(!connectionBeep&&buzzerValue==LOW);
    loop();assert(buzzerValue==LOW); // no repeated beep during existing connection
    static_cast<BLEServerCallbacks&>(server).onDisconnect(nullptr);
    connect();assert(connectionBeep&&buzzerValue==HIGH);
    assert(send("CLEAR")=="OK:CLEAR");loop();assert(!connectionBeep&&buzzerValue==LOW);
    alarmTriggered=true;fakeMillis=500;buzzerValue=LOW;
    connect();assert(!connectionBeep&&alarmTriggered&&buzzerValue==LOW);
    loop();assert(buzzerValue==LOW); // connection must not alter alarm cadence
    fakeMillis=1000;loop();assert(buzzerValue==HIGH);
    send("CLEAR");connect();alarmTriggered=true;loop();assert(!connectionBeep);
    send("CLEAR");
    assert(send("TIME:20260912125300")=="OK:TIME");
    assert(rtc.now().hour()==12&&rtc.now().minute()==53);
    auto beforeInvalid=rtc.now().unixtime();
    for(const char* invalid:{"TIME:202609121253", "TIME:20260912125300X", "TIME:20260229125300", "TIME:20260431125300", "TIME:19991231125300", "TIME:21000101125300", "TIME:20260012125300", "TIME:20260900125300", "TIME:20260912245300", "TIME:20260912126000", "TIME:20260912125360", "TIME:2026091212xx00"})
        assert(send(invalid)=="ERR:TIME_FORMAT");
    assert(rtc.now().unixtime()==beforeInvalid);
    assert(send("TIME:20280229000000")=="OK:TIME");
    rtc.failAdjust=true;assert(send("TIME:20260912125300")=="ERR:RTC_SYNC");rtc.failAdjust=false;
    assert(send("TIME:20260912125300")=="OK:TIME");
    assert(transfer(String("SET:12:54:")+hash)=="OK:SET");loop();assert(!alarmTriggered);
    auto configBeforeSync=preferences.values["configV2"];
    assert(send("TIME:20260912125400")=="OK:TIME");loop();assert(alarmTriggered);
    assert(send("TIME:20260912125900")=="OK:TIME");assert(alarmTriggered&&!alarmCompleted);
    assert(preferences.values["configV2"]==configBeforeSync);
    assert(transfer(String("STOP:")+hash)=="OK:STOP");
    assert(send("TIME:20260912125400")=="OK:TIME");loop();assert(!alarmTriggered&&alarmCompleted);
    send("CLEAR");
    std::cout<<"PASS: clock sync, invalid dates, leap year, RTC failure, corrected-time trigger, ringing/completion preservation\n";
    std::cout<<"PASS: one connection beep, timeout, reconnect, clear cancellation and ringing priority\n";
    std::cout<<"PASS: clear while ringing, idempotence, cleared restart, legacy erasure, transfer cancellation, clear storage failure\n";
    std::cout<<"PASS: setup, persistence, rejection, matching dismissal, storage failure, framing and disconnect recovery\n";
}
