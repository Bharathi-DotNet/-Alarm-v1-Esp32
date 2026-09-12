#include "../../src/main.cpp"
#include <cassert>
#include <iostream>
BLECharacteristic characteristic;
AlarmCommandCallback callback;
AlarmServerCallbacks server;
String send(String c){characteristic.setValue(c.c_str());static_cast<BLECharacteristicCallbacks&>(callback).onWrite(&characteristic);return characteristic.getValue();}
String transfer(String c){assert(send("BEGIN")=="OK:BEGIN");for(size_t i=0;i<c.length();i+=19)assert(send(String("+")+c.substring(i,std::min(i+19,c.length())))=="OK:PART");return send("COMMIT");}
String hash=std::string(64,'A'),wrong=std::string(64,'B');
String put(int id,const char* time,String qr=hash,const char* name="4D6F726E696E67",bool enabled=true){return transfer("PUT:"+String(id)+":"+time+":"+(enabled?"1:":"0:")+qr+":3:"+name);}
void clockAt(const char* value){assert(send(String("TIME:")+value)=="OK:TIME");}
int main(){
    setup();assert(send("LIST")=="ALARMS:3:10");assert(send("GET:0")=="EMPTY:0");
    preferences.values["configV2"]=String("07:00:1:")+hash;
    loadAlarms();assert(alarms[0].used&&alarms[0].enabled&&alarms[0].hash==hash);
    assert(send("GET:0")=="A:0:07:00:1:0");assert(preferences.values.count("configV3"));
    assert(send("OFF:0")=="OK:OFF");auto saved=preferences.values["configV3"];
    assert(put(1,"07:00")=="ERR:DUPLICATE");assert(!alarms[1].used&&preferences.values["configV3"]==saved);
    assert(put(1,"08:00",wrong)=="OK:PUT");assert(put(1,"07:00")=="ERR:DUPLICATE");assert(alarms[1].hour==8);
    assert(put(1,"08:10","-","E0AEAEE0AEBE")=="OK:PUT");assert(alarms[1].hash==wrong);
    assert(send("NAME:1:0")=="N:1:0:E0AEAEE0AEBE");assert(send("NAME:1:1")=="N:1:1:");
    assert(put(2,"09:00","-")=="ERR:QR_REQUIRED");
    for(int i=2;i<10;++i){char t[6];snprintf(t,6,"%02d:00",i+8);assert(put(i,t)=="OK:PUT");}
    assert(transfer(String("PUT:10:20:00:1:")+hash+":3:")=="ERR:COMMAND");
    assert(put(9,"24:00")=="ERR:FORMAT");assert(put(9,"17:60")=="ERR:FORMAT");
    assert(put(9,"17:00",hash,"XYZ")=="ERR:FORMAT");
    saved=preferences.values["configV3"];preferences.fail=true;
    assert(send("DEL:1")=="ERR:STORAGE");assert(alarms[1].used&&preferences.values["configV3"]==saved);preferences.fail=false;
    loadAlarms();assert(alarms[1].hour==8&&alarms[1].minute==10&&alarms[1].hash==wrong);
    assert(send("DEL:9")=="OK:DEL");assert(put(9,"19:00")=="OK:PUT");
    assert(send("CLEAR")=="OK:CLEAR");loadAlarms();assert(!alarms[0].used);
    clockAt("20260912065959");assert(put(0,"07:00")=="OK:PUT");assert(put(1,"07:01",wrong)=="OK:PUT");
    loop();assert(activeAlarm()<0);clockAt("20260912070000");loop();assert(activeAlarm()==0);
    assert(send("STOP")=="ERR:COMMAND");assert(transfer(String("STOP:")+wrong)=="ERR:QR_MISMATCH");
    assert(send("OFF:0")=="ERR:RINGING");assert(send("DEL:0")=="ERR:RINGING");assert(put(0,"09:00")=="ERR:RINGING");
    clockAt("20260912070100");loop();assert(alarms[1].ringing&&activeAlarm()==0);assert(send("GET:1")=="A:1:07:01:1:2");
    assert(transfer(String("STOP:")+wrong)=="ERR:QR_MISMATCH");
    loadAlarms();assert(activeAlarm()==0&&alarms[1].ringing); // interrupted task survives reload
    preferences.fail=true;assert(transfer(String("STOP:")+hash)=="ERR:STORAGE");assert(alarms[0].ringing);preferences.fail=false;
    assert(transfer(String("STOP:")+hash)=="OK:STOP");assert(activeAlarm()==1);
    assert(transfer(String("STOP:")+wrong)=="OK:STOP");assert(activeAlarm()<0);loop();assert(activeAlarm()<0);
    loadAlarms();loop();assert(activeAlarm()<0); // no duplicate task on same-day reboot
    assert(send("OFF:1")=="OK:OFF");assert(send("ON:1")=="OK:ON");loop();assert(activeAlarm()<0);
    clockAt("20260913070000");loop();assert(activeAlarm()==0);assert(transfer(String("STOP:")+hash)=="OK:STOP");
    clockAt("20260913070100");loop();assert(activeAlarm()==1);assert(transfer(String("STOP:")+wrong)=="OK:STOP");
    // Moving clock backwards must not replay a completed day.
    clockAt("20260912070000");loop();assert(activeAlarm()<0);
    assert(send("CLEAR")=="OK:CLEAR");clockAt("20261231235900");assert(put(0,"23:59")=="OK:PUT");loop();assert(activeAlarm()==0);
    assert(transfer(String("STOP:")+hash)=="OK:STOP");clockAt("20270101235900");loop();assert(activeAlarm()==0);
    assert(send("CLEAR")=="OK:CLEAR");assert(activeAlarm()<0&&buzzerValue==LOW);
    for(const char* invalid:{"TIME:202609121253", "TIME:20260229125300", "TIME:20260431125300", "TIME:19991231125300", "TIME:21000101125300", "TIME:20260012125300", "TIME:20260900125300", "TIME:20260912245300", "TIME:20260912126000", "TIME:20260912125360"})assert(send(invalid)=="ERR:TIME_FORMAT");
    clockAt("20280229000000");rtc.failAdjust=true;assert(send("TIME:20260912125300")=="ERR:RTC_SYNC");rtc.failAdjust=false;
    assert(send("BEGIN")=="OK:BEGIN");send("+PUT:0:");assert(send("COMMIT")=="ERR:FORMAT");
    send("BEGIN");fakeMillis+=10001;assert(send("+PUT:")=="ERR:TRANSFER");
    send("BEGIN");assert(send(String("+")+std::string(20,'A'))=="ERR:FORMAT");
    send("BEGIN");send("+PUT:0:");static_cast<BLEServerCallbacks&>(server).onDisconnect(nullptr);assert(send("COMMIT")=="ERR:TRANSFER");
    static_cast<BLEServerCallbacks&>(server).onConnect(nullptr);assert(connectionBeep&&buzzerValue==HIGH);fakeMillis+=151;loop();assert(!connectionBeep&&buzzerValue==LOW);
    send("CLEAR");assert(preferences.values.empty());
    std::cout<<"PASS: migration, 10 slots, duplicate add/edit/disabled rejection, QR retention, UTF8 names, atomic failures, pending order, persistence, daily repeat, year rollover, clock validation, framing, clear and connection beep\n";
}
