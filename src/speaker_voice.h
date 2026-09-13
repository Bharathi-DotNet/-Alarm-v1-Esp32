#pragma once
#ifdef ARDUINO
#include <driver/i2s.h>
#include <atomic>
#include <math.h>
#include "connection_voice_data.h"
namespace SpeakerVoice {
static TaskHandle_t worker=nullptr;
static SemaphoreHandle_t audioMutex=nullptr;
static std::atomic<bool> alarmActive{false};
static std::atomic<int> pendingAnnouncement{0};
static void setAlarmActive(bool value) { alarmActive.store(value); }
static const i2s_port_t port=I2S_NUM_1;
static void run(void*) {
    for(;;) {
        ulTaskNotifyTake(pdTRUE,pdMS_TO_TICKS(20));
        int voiceRequested=pendingAnnouncement.exchange(0);
        if(!alarmActive.load() && !voiceRequested) continue;
        xSemaphoreTake(audioMutex,portMAX_DELAY);
        static int32_t block[256*2];
        bool failed=false;
        if(alarmActive.load()) {
            i2s_set_clk(port,16000,I2S_BITS_PER_SAMPLE_32BIT,I2S_CHANNEL_STEREO);
            // Own the speaker for the entire alarm, including the silent gaps.
            // This works without an A2DP connection or incoming music packets.
            Serial.println("[AUDIO] Alarm tone started.");
            uint32_t sample=0;
            File custom=AlarmAudio::open();
            static uint8_t pcm[512];
            while(alarmActive.load()) {
                bool customBlock=false;
                if(custom) {
                    size_t filled=0;
                    while(filled<sizeof(pcm)) {
                        if(!custom.available() && !custom.seek(0)) break;
                        size_t n=custom.read(pcm+filled,sizeof(pcm)-filled);
                        if(!n) break;
                        filled+=n;
                    }
                    customBlock=filled==sizeof(pcm);
                    if(!customBlock) { custom.close(); Serial.println("[AUDIO] Custom read failed; using default tone."); }
                }
                for(size_t i=0;i<256;++i,++sample) {
                    uint32_t phase=sample%16000;
                    int32_t value=customBlock ? (int16_t)(pcm[2*i]|(pcm[2*i+1]<<8)) :
                        (phase<8000 ? (int32_t)(18000.0f*sinf(2.0f*3.14159265f*(sample%16)/16.0f)) : 0);
                    block[2*i]=block[2*i+1]=value*65536;
                }
                size_t bytes=0;
                if(i2s_write(port,block,sizeof(block),&bytes,pdMS_TO_TICKS(250))!=ESP_OK || bytes!=sizeof(block)) {
                    failed=true; break;
                }
            }
            Serial.printf("[AUDIO] Alarm tone ended; stack free minimum=%u bytes.\n",(unsigned)uxTaskGetStackHighWaterMark(nullptr));
        } else {
        i2s_set_clk(port,8000,I2S_BITS_PER_SAMPLE_32BIT,I2S_CHANNEL_STEREO);
        const int8_t* voice=voiceRequested==2?disconnectionVoice:connectionVoice;
        size_t voiceLength=voiceRequested==2?sizeof(disconnectionVoice):sizeof(connectionVoice);
        for(size_t offset=0;offset<voiceLength && !alarmActive.load();offset+=256) {
            size_t n=min((size_t)256,voiceLength-offset);
            for(size_t i=0;i<n;++i) block[2*i]=block[2*i+1]=(int32_t)voice[offset+i]*16777216;
            size_t bytes=0;
            if(i2s_write(port,block,n*8,&bytes,pdMS_TO_TICKS(250))!=ESP_OK || bytes!=n*8) { failed=true; break; }
        }
        }
        // Flush the tail with silence without repeating the last DMA samples.
        memset(block,0,sizeof(block));
        for(int i=0;i<5;++i) { size_t bytes=0; i2s_write(port,block,sizeof(block),&bytes,pdMS_TO_TICKS(250)); }
        i2s_zero_dma_buffer(port);
        xSemaphoreGive(audioMutex);
        if(failed) Serial.println("[VOICE] Audio write failed.");
    }
}
static bool begin() {
    audioMutex=xSemaphoreCreateMutex();
    if(!audioMutex) return false;
    i2s_config_t cfg={};
    cfg.mode=(i2s_mode_t)(I2S_MODE_MASTER|I2S_MODE_TX);
    cfg.sample_rate=16000; cfg.bits_per_sample=I2S_BITS_PER_SAMPLE_32BIT;
    cfg.channel_format=I2S_CHANNEL_FMT_RIGHT_LEFT;
    cfg.communication_format=I2S_COMM_FORMAT_STAND_I2S;
    cfg.dma_buf_count=4; cfg.dma_buf_len=256; cfg.tx_desc_auto_clear=true;
    if(i2s_driver_install(port,&cfg,0,nullptr)!=ESP_OK) return false;
    i2s_pin_config_t pins={}; pins.mck_io_num=I2S_PIN_NO_CHANGE;
    pins.bck_io_num=26; pins.ws_io_num=25; pins.data_out_num=27; pins.data_in_num=I2S_PIN_NO_CHANGE;
    if(i2s_set_pin(port,&pins)!=ESP_OK) { i2s_driver_uninstall(port); return false; }
    i2s_zero_dma_buffer(port);
    if(xTaskCreate(run,"connection-voice",12288,nullptr,1,&worker)!=pdPASS) { worker=nullptr; i2s_driver_uninstall(port); return false; }
    return true;
}
static bool request(bool connected=true) { if(!worker || alarmActive.load()) return false; pendingAnnouncement.store(connected?1:2); xTaskNotifyGive(worker); return true; }
}
#else
// Host tests exercise routing and fallback; real I2S is validated by the ESP32 build/device.
namespace SpeakerVoice {
inline bool alarmActive=false;
inline void setAlarmActive(bool value) { alarmActive=value; }
inline bool available=true;
inline int requests=0;
inline bool begin(){return available;}
inline bool request(bool=true){if(!available || alarmActive)return false;++requests;return true;}
}
#endif
