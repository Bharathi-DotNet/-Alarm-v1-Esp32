#pragma once
#include <string>
#include <map>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cctype>
#include <algorithm>
class String {
    std::string s;
public:
    String(const char* v=""):s(v){} String(std::string v):s(v){}
    size_t length()const{return s.size();} char operator[](size_t i)const{return s[i];}
    String substring(size_t a,size_t b=std::string::npos)const{return s.substr(a,b==std::string::npos?b:b-a);}
    int toInt()const{return std::atoi(s.c_str());} const char* c_str()const{return s.c_str();}
    bool startsWith(const char* p)const{return s.rfind(p,0)==0;}
    String& operator+=(String v){s+=v.s;return *this;}
    friend String operator+(String a,String b){return a.s+b.s;}
    friend bool operator==(String a,String b){return a.s==b.s;}
    friend bool operator!=(String a,String b){return !(a==b);}
};
inline uint32_t fakeMillis=0;
inline int buzzerValue=0;
inline uint32_t millis(){return fakeMillis;}
inline void delay(int n){fakeMillis+=n;}
inline void digitalWrite(int,int v){buzzerValue=v;}
inline void pinMode(int,int){}
inline bool isDigit(char c){return c>='0'&&c<='9';}
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define F(x) x
struct SerialType{void begin(int){} void println(const char*){} template<typename... Args> void printf(const char*,Args...){}};
inline SerialType Serial;
struct WireType{void begin(int,int){}};
inline WireType Wire;
class DateTime{public:int h=7,m=0,s=0,y=2026,mo=9,d=12;
DateTime(){} DateTime(const char*,const char*){}
DateTime(int year,int month,int day,int hour,int minute,int second):h(hour),m(minute),s(second),y(year),mo(month),d(day){}
int hour(){return h;} int minute(){return m;} int second(){return s;}
uint32_t unixtime(){uint32_t days=0;for(int i=2000;i<y;++i)days+=365+(i%4==0);int ds[]={31,28,31,30,31,30,31,31,30,31,30,31};for(int i=1;i<mo;++i)days+=ds[i-1]+(i==2&&y%4==0);return 946684800u+(days+d-1)*86400+h*3600+m*60+s;}};
class RTC_DS3231{public:DateTime time;bool failAdjust=false;bool begin(){return true;} bool lostPower(){return false;} void adjust(DateTime value){if(!failAdjust)time=value;} DateTime now(){return time;}};
class Preferences{public:std::map<std::string,String> values; bool fail=false;
bool clear(){if(fail)return false;values.clear();return true;}
void begin(const char*,bool){} size_t putString(const char* k,String v){if(fail)return 0;values[k]=v;return v.length();}
String getString(const char* k,const char* fallback){auto i=values.find(k);return i==values.end()?String(fallback):i->second;}
int getInt(const char*,int fallback){return fallback;}};
using SemaphoreHandle_t=int;
inline int xSemaphoreCreateMutex(){return 1;}
inline void xSemaphoreTake(int,int){} inline void xSemaphoreGive(int){}
#define portMAX_DELAY 0
class BLECharacteristic;
class BLECharacteristicCallbacks{public:virtual void onWrite(BLECharacteristic*){}};
class BLECharacteristic{public:std::string value;static constexpr int PROPERTY_READ=1,PROPERTY_WRITE=2;
std::string getValue(){return value;} void setValue(const char* s){value=s;}
void setCallbacks(BLECharacteristicCallbacks*){}};
class BLEServer;
class BLEServerCallbacks{public:virtual void onConnect(BLEServer*){}virtual void onDisconnect(BLEServer*){}};
class BLEService{public:BLECharacteristic* createCharacteristic(const char*,int){static BLECharacteristic c;return &c;} void start(){}};
class BLEServer{public:void setCallbacks(BLEServerCallbacks*){} BLEService* createService(const char*){static BLEService s;return &s;}};
class BLEAdvertising{public:void addServiceUUID(const char*){} void start(){}};
class BLEDevice{public:static void init(const char*){} static BLEServer* createServer(){static BLEServer s;return &s;}
static BLEAdvertising* getAdvertising(){static BLEAdvertising a;return &a;} static void startAdvertising(){}};
