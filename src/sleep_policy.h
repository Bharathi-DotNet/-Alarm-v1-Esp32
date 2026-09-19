#pragma once
#include <stdint.h>
namespace WakeTest {
struct Policy {
    bool connected=false, everConnected=false;
    uint32_t bootAt=0, disconnectedAt=0;
    void boot(uint32_t now) { connected=false; everConnected=false; bootAt=now; }
    void connect() { connected=true; everConnected=true; }
    void disconnect(uint32_t now) { if(connected) { connected=false; disconnectedAt=now; } }
    bool expired(uint32_t now) const {
        return !connected && uint32_t(now-(everConnected?disconnectedAt:bootAt)) >= (everConnected?10000u:120000u);
    }
    uint32_t remainingMs(uint32_t now) const {
        if (connected) return 0;
        uint32_t timeout = everConnected ? 10000u : 120000u;
        uint32_t elapsed = uint32_t(now - (everConnected ? disconnectedAt : bootAt));
        return elapsed >= timeout ? 0 : timeout - elapsed;
    }
    bool canSleep(uint32_t now,bool pending,bool dirty,bool healthy,bool buttonReleased) const {
        return expired(now) && !pending && !dirty && healthy && buttonReleased;
    }
};
// Local RTC calendar seconds. A completed occurrence cannot repeat after time moves back.
inline uint32_t nextOccurrence(uint32_t now,int hour,int minute,uint32_t lastDay) {
    uint32_t day=now/86400, target=day*86400+hour*3600+minute*60;
    if(target<=now) ++day;
    if(day<=lastDay) day=lastDay+1;
    return day*86400+hour*3600+minute*60;
}
template<class T> int selectNext(const T* alarms,int count,uint32_t now,uint32_t &when) {
 int best=-1;when=0;
 for(int i=0;i<count;++i) {
   const auto &a=alarms[i];if(!a.used||!a.enabled)continue;
   uint32_t candidate=nextOccurrence(now,a.hour,a.minute,a.lastDay);
   if(best<0||candidate<when){best=i;when=candidate;}
 }
 return best;
}
template<class T> bool recoverDue(T &a,uint32_t revision,uint32_t epoch,uint32_t now) {
 uint32_t day=epoch/86400;
 if(now<epoch||!a.used||!a.enabled||a.revision!=revision||a.lastDay>=day)return false;
 a.ringing=true;a.lastDay=day;return true;
}
}

