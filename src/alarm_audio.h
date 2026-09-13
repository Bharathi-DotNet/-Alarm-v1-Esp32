#pragma once
#ifdef ARDUINO
#include <LittleFS.h>
#include <Preferences.h>
namespace AlarmAudio {
static Preferences settings;
static File upload;
static bool ready=false, failed=false;
static String selected="", staging="";
static uint32_t expected=0, received=0, expectedCrc=0, crc=0xffffffff, lastWrite=0;
static uint32_t updateCrc(uint32_t value,const uint8_t* data,size_t size) {
    for(size_t i=0;i<size;++i) {
        value^=data[i];
        for(int bit=0;bit<8;++bit) value=(value>>1)^((value&1)?0xedb88320u:0);
    }
    return value;
}
static bool validFile(const String& path,uint32_t size,uint32_t checksum) {
    File file=LittleFS.open(path,"r");
    if(!file || size<3200 || size>320000 || size%2 || file.size()!=size) return false;
    uint8_t block[512]; uint32_t value=0xffffffff,total=0;
    while(file.available()) {
        size_t n=file.read(block,sizeof(block)); if(!n) return false;
        value=updateCrc(value,block,n); total+=n;
    }
    return total==size && ~value==checksum;
}
static void abort() {
    if(upload) upload.close();
    if(staging.length()) LittleFS.remove(staging);
    staging=""; expected=received=0; failed=false;
}
static void begin() {
    settings.begin("alarm-audio",false);
    // Only format an unused, erased partition. Never auto-format stored audio.
    ready=LittleFS.begin(false);
    if(!ready) {
        const esp_partition_t* partition=esp_partition_find_first(ESP_PARTITION_TYPE_DATA,ESP_PARTITION_SUBTYPE_DATA_SPIFFS,nullptr);
        bool blank=partition!=nullptr; uint8_t bytes[256];
        for(size_t offset=0;blank && offset<partition->size;offset+=sizeof(bytes)) {
            if(esp_partition_read(partition,offset,bytes,sizeof(bytes))!=ESP_OK) { blank=false; break; }
            for(uint8_t b:bytes) if(b!=0xff) { blank=false; break; }
        }
        if(blank && LittleFS.format()) ready=LittleFS.begin(false);
    }
    String metadata=settings.getString("selected","");
    char slot=0; unsigned int size=0,checksum=0;
    if(ready && sscanf(metadata.c_str(),"%c:%u:%u",&slot,&size,&checksum)==3 && (slot=='A'||slot=='B')) {
        String path=slot=='A'?"/alarmA.pcm":"/alarmB.pcm";
        if(validFile(path,size,checksum)) selected=path;
    }
    Serial.printf("[AUDIO] Storage=%s; alarm sound=%s\n",ready?"ready":"unavailable",selected.length()?"custom":"default");
}
static File open() { return selected.length()?LittleFS.open(selected,"r"):File(); }
static String command(const String& input,bool ringing) {
    if(input=="AUDIOCAP") return ready?"AUDIO:1:320000":"ERR:AUDIO_STORAGE";
    if(input=="AUDIOSTATE") return selected.length()?"AUDIO:CUSTOM":"AUDIO:DEFAULT";
    if(input=="AUDIOABORT") { abort(); return "OK:AUDIOABORT"; }
    if(input=="AUDIOPOS") return failed?"ERR:AUDIO_TRANSFER":"P:"+String(received);
    if(ringing) { abort(); return "ERR:RINGING"; }
    if(!ready) return "ERR:AUDIO_STORAGE";
    if(input=="AUDIODEFAULT") {
        if(settings.putString("selected","default")!=7) return "ERR:AUDIO_STORAGE";
        selected=""; abort(); return "OK:AUDIODEFAULT";
    }
    if(input.startsWith("AUDIOBEGIN:")) {
        unsigned int size=0,checksum=0; char extra=0;
        if(sscanf(input.c_str(),"AUDIOBEGIN:%u:%u%c",&size,&checksum,&extra)!=2 || size<3200 || size>320000 || size%2) return "ERR:FORMAT";
        abort(); staging=selected=="/alarmA.pcm"?"/alarmB.pcm":"/alarmA.pcm";
        LittleFS.remove(staging);
        if(LittleFS.totalBytes()-LittleFS.usedBytes()<size+32768) { staging=""; return "ERR:AUDIO_STORAGE"; }
        upload=LittleFS.open(staging,"w");
        if(!upload) { staging=""; return "ERR:AUDIO_STORAGE"; }
        expected=size; expectedCrc=checksum; crc=0xffffffff; lastWrite=millis();
        return "OK:AUDIOBEGIN";
    }
    if(input=="AUDIOCOMMIT") {
        if(!upload || failed || received!=expected || ~crc!=expectedCrc) { abort(); return "ERR:AUDIO_TRANSFER"; }
        upload.flush(); upload.close();
        if(!validFile(staging,expected,expectedCrc)) { abort(); return "ERR:AUDIO_TRANSFER"; }
        char metadata[40]; snprintf(metadata,sizeof(metadata),"%c:%u:%u",staging=="/alarmA.pcm"?'A':'B',expected,expectedCrc);
        if(settings.putString("selected",metadata)!=strlen(metadata)) { abort(); return "ERR:AUDIO_STORAGE"; }
        selected=staging; staging=""; abort(); return "OK:AUDIOCOMMIT";
    }
    return "ERR:COMMAND";
}
static void chunk(const uint8_t* bytes,size_t size,bool ringing) {
    if(ringing || !upload || failed || millis()-lastWrite>120000 || size<5) { failed=true; return; }
    uint32_t offset=(uint32_t)bytes[0]|((uint32_t)bytes[1]<<8)|((uint32_t)bytes[2]<<16)|((uint32_t)bytes[3]<<24);
    if(offset!=received || received+size-4>expected || upload.write(bytes+4,size-4)!=size-4) { failed=true; return; }
    crc=updateCrc(crc,bytes+4,size-4); received+=size-4; lastWrite=millis();
}
}
#else
namespace AlarmAudio {
inline void begin() {}
inline void abort() {}
inline String command(const String&,bool) { return "ERR:AUDIO_STORAGE"; }
inline void chunk(const uint8_t*,size_t,bool) {}
}
#endif
