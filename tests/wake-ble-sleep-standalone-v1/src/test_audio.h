#pragma once
#include <atomic>
namespace AudioSamples { inline std::atomic<int> volumePercent{100}; }
// Compatibility replies for current app; test deliberately has no custom upload/filesystem.
namespace AlarmAudio {
inline void abort() {}
inline String command(const String& c,bool) {
    if(c=="AUDIOSTATE") return "AUDIO:DEFAULT";
    if(c=="AUDIODEFAULT") return "OK:AUDIODEFAULT";
    return "ERR:AUDIO_UNSUPPORTED";
}
}
namespace SpeakerVoice {
inline std::atomic<bool> alarmActive{false};
inline void setAlarmActive(bool value) { alarmActive.store(value); }
inline bool request(bool) { return false; } // No connection voice assets in standalone.
#ifdef ARDUINO
}
#include <driver/i2s.h>
#include <math.h>
namespace SpeakerVoice {
inline void worker(void*) {
    int32_t block[512]; uint32_t sample=0;
    for(;;) {
        for(int i=0;i<256;++i,++sample) {
            int32_t pcm=alarmActive.load() && sample%16000<8000 ? int32_t(12000*sinf(2*3.14159265f*(sample%16)/16.0f)) : 0;
            int32_t value=int32_t(int64_t(pcm)*65536*AudioSamples::volumePercent.load()/100);
            block[2*i]=block[2*i+1]=value;
        }
        size_t sent=0;
        if(i2s_write(I2S_NUM_1,block,sizeof(block),&sent,pdMS_TO_TICKS(100))!=ESP_OK) vTaskDelay(pdMS_TO_TICKS(20));
    }
}
inline bool begin() {
    i2s_config_t c={}; c.mode=i2s_mode_t(I2S_MODE_MASTER|I2S_MODE_TX);
    c.sample_rate=16000; c.bits_per_sample=I2S_BITS_PER_SAMPLE_32BIT;
    c.channel_format=I2S_CHANNEL_FMT_RIGHT_LEFT;c.communication_format=I2S_COMM_FORMAT_STAND_I2S;
    c.dma_buf_count=4;c.dma_buf_len=256;c.tx_desc_auto_clear=true;
    if(i2s_driver_install(I2S_NUM_1,&c,0,nullptr)!=ESP_OK) return false;
    i2s_pin_config_t p={};p.mck_io_num=I2S_PIN_NO_CHANGE;p.bck_io_num=18;p.ws_io_num=19;p.data_out_num=23;p.data_in_num=I2S_PIN_NO_CHANGE;
    if(i2s_set_pin(I2S_NUM_1,&p)!=ESP_OK) return false;
    return xTaskCreate(worker,"test-tone",4096,nullptr,1,nullptr)==pdPASS;
}
#else
inline bool begin() { return true; }
#endif
}
