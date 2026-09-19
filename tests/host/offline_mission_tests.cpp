#include "../../src/main.cpp"
#include <cassert>
#include <iostream>
int main() {
    setup();
    String hash=std::string(64,'A');
    assert(executeCommand("MISSIONCAP")=="MISSION:1");
    assert(executeCommand(String("PUT:0:07:00:1:")+hash+":4:54657374:0")=="OK:PUT");
    assert(executeCommand(String("PUT:1:07:01:1:")+hash+":4:54657374:0")=="OK:PUT");
    auto revision=alarms[0].revision;
    assert(revision>0);
    rtc.adjust(DateTime(2026,9,14,7,0,0)); loop();
    auto day=alarms[0].lastDay;
    String stop=String("STOPM:0:")+String(revision)+":"+String(day)+":"+hash;
    preferences.fail=true;
    assert(executeCommand(stop)=="ERR:STORAGE"); assert(alarms[0].ringing);
    preferences.fail=false;
    assert(executeCommand(stop)=="OK:STOPM"); assert(!alarms[0].ringing);
    // Lost acknowledgment and a reboot: the exact same command is idempotent.
    loadAlarms(); assert(alarms[0].revision==revision);
    rtc.adjust(DateTime(2026,9,14,7,1,0)); loop(); assert(alarms[1].ringing);
    assert(executeCommand(stop)=="OK:STOPM"); assert(alarms[1].ringing);
    rtc.adjust(DateTime(2026,9,15,7,0,0)); loop(); assert(alarms[0].ringing);
    assert(executeCommand(stop)=="ERR:STALE_MISSION"); assert(alarms[0].ringing);
    auto newDay=alarms[0].lastDay;
    assert(executeCommand(String("STOPM:0:")+String(revision)+":"+String(newDay)+":"+hash)=="ERR:MISSION_WAITING");
    // CLEAR must not recycle configuration revisions.
    assert(executeCommand("CLEAR")=="OK:CLEAR");
    assert(executeCommand(String("PUT:0:07:00:1:")+hash+":4:54657374:0")=="OK:PUT");
    assert(alarms[0].revision>revision);
    assert(executeCommand(stop)=="ERR:STALE_MISSION");
    // Old v4 rows remain readable; must be re-saved to acquire an offline revision.
    preferences.values["configV4"]=String("4|07:00:1:")+hash+":54657374:0:0:|-|-|-|-|-|-|-|-|-";
    loadAlarms(); assert(alarms[0].used && alarms[0].revision==0);
    std::cout << "PASS: storage failure, reboot, lost acknowledgment, duplicate QR across alarms, stale day, pending order, revision reuse and v4 migration\n";
}
