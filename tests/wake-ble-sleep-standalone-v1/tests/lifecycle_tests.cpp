#include "../src/main.cpp"
#include <cassert>
#include <iostream>
BLECharacteristic chr;
AlarmCommandCallback writer;
AlarmServerCallbacks connection;
String send(String c){chr.setValue(c.c_str());static_cast<BLECharacteristicCallbacks&>(writer).onWrite(&chr);return chr.getValue();}
String frame(String c){assert(send("BEGIN")=="OK:BEGIN");for(size_t i=0;i<c.length();i+=19)assert(send(String("+")+c.substring(i,std::min(i+19,c.length())))=="OK:PART");return send("COMMIT");}
String qr=std::string(64,'A'),bad=std::string(64,'B');
String save(int id,const char* time,bool on=true){return frame("PUT:"+String(id)+":"+time+":"+(on?"1:":"0:")+qr+":4:54657374:0");}
int main(){
 setup();assert(send("LIST")=="ALARMS:3:10");assert(send("AUDIOSTATE")=="AUDIO:DEFAULT");
 assert(!wakePolicy.expired(119999));assert(wakePolicy.expired(120000));
 connection.onConnect(nullptr);fakeMillis=300000;assert(!wakePolicy.expired(fakeMillis));
 assert(send("TIME:20260920065930")=="OK:TIME");
 assert(save(0,"07:00")=="OK:PUT");assert(save(1,"07:02")=="OK:PUT");assert(save(2,"07:01",false)=="OK:PUT");
 assert(save(3,"07:00")=="ERR:DUPLICATE");
 auto oldRevision=alarms[0].revision;
 assert(save(0,"07:03")=="OK:PUT");assert(alarms[0].revision>oldRevision);
 assert(send("DEL:1")=="OK:DEL");assert(save(4,"07:04")=="OK:PUT");
 loadAlarms();assert(alarms[0].hour==7&&alarms[0].minute==3&&!alarms[1].used&&!alarms[2].enabled&&alarms[4].used);
 uint32_t next=0;assert(WakeTest::selectNext(alarms,10,rtc.now().unixtime(),next)==0);
 auto before=preferences.values["configV4"];preferences.fail=true;
 assert(send("DEL:4")=="ERR:STORAGE");assert(alarms[4].used&&preferences.values["configV4"]==before);preferences.fail=false;
 assert(send("BEGIN")=="OK:BEGIN");assert(send("+PUT:5:")=="OK:PART");
 connection.onDisconnect(nullptr);assert(send("COMMIT")=="ERR:TRANSFER");
 assert(!wakePolicy.expired(fakeMillis+9999));assert(wakePolicy.expired(fakeMillis+10000));
 connection.onConnect(nullptr);assert(!wakePolicy.expired(fakeMillis+999999));
 fakeMillis+=7000;connection.onDisconnect(nullptr);
 assert(!wakePolicy.expired(fakeMillis+9999));assert(wakePolicy.expired(fakeMillis+10000));
 fakeMillis+=10000;
 assert(wakePolicy.canSleep(fakeMillis,false,false,true,true));
 assert(!wakePolicy.canSleep(fakeMillis,true,false,true,true));
 assert(!wakePolicy.canSleep(fakeMillis,false,true,true,true));
 assert(!wakePolicy.canSleep(fakeMillis,false,false,false,true));
 assert(!wakePolicy.canSleep(fakeMillis,false,false,true,false));
 assert(send("TIME:20260920070300")=="OK:TIME");loop();assert(activeAlarm()==0&&SpeakerVoice::alarmActive);
 assert(send("DEL:0")=="ERR:RINGING");assert(frame("STOP:"+bad)=="ERR:QR_MISMATCH");
 loadAlarms();assert(activeAlarm()==0); // Pending survives reset/reload.
 assert(!wakePolicy.canSleep(fakeMillis,activeAlarm()>=0,storageDirty,true,true));
 assert(frame("STOP:"+qr)=="OK:STOP");loop();assert(activeAlarm()<0&&!SpeakerVoice::alarmActive);
 assert(WakeTest::selectNext(alarms,10,rtc.now().unixtime(),next)==4);
 assert(send("OFF:4")=="OK:OFF");assert(send("OFF:0")=="OK:OFF");
 assert(WakeTest::selectNext(alarms,10,rtc.now().unixtime(),next)==-1); // Button-only sleep.
 assert(wakePolicy.canSleep(fakeMillis,false,false,true,true));
 // Armed occurrence catches boot lasting longer than the due minute; never replay it twice.
 Alarm a;a.used=true;a.enabled=true;a.revision=7;
 uint32_t epoch=DateTime(2026,12,31,23,59,0).unixtime();
 assert(!WakeTest::recoverDue(a,7,epoch,epoch-1));assert(!WakeTest::recoverDue(a,8,epoch,epoch+61));
 assert(WakeTest::recoverDue(a,7,epoch,epoch+65));assert(a.ringing);
 a.ringing=false;assert(!WakeTest::recoverDue(a,7,epoch,epoch+66));
 assert(WakeTest::nextOccurrence(epoch+30,23,59,a.lastDay)==epoch+86400);
 assert(WakeTest::nextOccurrence(epoch-86400,23,59,a.lastDay)==epoch+86400); // Clock moved back.
 assert(WakeTest::nextOccurrence(DateTime(2026,12,31,23,59,59).unixtime(),0,0,0)==DateTime(2027,1,1,0,0,0).unixtime());
 WakeTest::Policy wrap;wrap.boot(0xfffffff0u);assert(!wrap.expired(0xfffffff0u+119999u));assert(wrap.expired(0xfffffff0u+120000u));
 wrap.connect();wrap.disconnect(0xfffffff0u);assert(!wrap.expired(9983));assert(wrap.expired(9984));
 assert(send("CLEAR")=="OK:CLEAR");loadAlarms();assert(activeAlarm()<0&&!alarms[0].used);
 std::cout<<"PASS: lifecycle deadlines/reconnect/rollover, framed BLE multi-edit persistence, storage failure, next enabled alarm, pending sleep block/reload/QR, boot-late recovery and button-only sleep\n";
}
