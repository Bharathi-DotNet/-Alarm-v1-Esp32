#pragma once
namespace MediaVoice {
static bool connected=false;
static void changed(bool value) {
    if(connected==value) return;
    connected=value;
    SpeakerVoice::request(value);
}
}
#ifdef ARDUINO
#include <esp_a2dp_api.h>
#include <esp_gap_bt_api.h>
#include <esp_avrc_api.h>
namespace MusicReceiver {
static std::atomic<int> rate{44100};
static void data(const uint8_t* bytes,uint32_t length) {
    if(!SpeakerVoice::worker || SpeakerVoice::alarmActive.load()) return;
    if(xSemaphoreTake(SpeakerVoice::audioMutex,0)!=pdTRUE) return;
    if(SpeakerVoice::alarmActive.load()) {
        xSemaphoreGive(SpeakerVoice::audioMutex); return;
    }
    static int currentRate=0;
    // Voice playback can change the shared I2S clock between music packets.
    uint32_t actual=(uint32_t)i2s_get_clk(SpeakerVoice::port);
    int requested=rate.load();
    if(currentRate!=requested || abs((int)actual-requested)>100) {
        if(i2s_set_clk(SpeakerVoice::port,requested,I2S_BITS_PER_SAMPLE_32BIT,I2S_CHANNEL_STEREO)!=ESP_OK) {
            xSemaphoreGive(SpeakerVoice::audioMutex); return;
        }
        currentRate=requested;
    }
    int32_t block[256];
    for(uint32_t offset=0;offset+3<length && !SpeakerVoice::alarmActive.load();) {
        size_t count=0;
        while(count<256 && offset+3<length) {
            int16_t left=(int16_t)(bytes[offset]|(bytes[offset+1]<<8));
            int16_t right=(int16_t)(bytes[offset+2]|(bytes[offset+3]<<8));
            int32_t mono=((int32_t)left+right)/2;
            block[count++]=mono*65536; block[count++]=mono*65536;
            offset+=4;
        }
        size_t written=0;
        if(i2s_write(SpeakerVoice::port,block,count*sizeof(int32_t),&written,pdMS_TO_TICKS(30))!=ESP_OK) break;
    }
    xSemaphoreGive(SpeakerVoice::audioMutex);
}
static void event(esp_a2d_cb_event_t event,esp_a2d_cb_param_t* param) {
    if(event==ESP_A2D_AUDIO_CFG_EVT) {
        uint8_t frequency=param->audio_cfg.mcc.cie.sbc[0];
        rate.store(frequency&0x80?16000:frequency&0x40?32000:frequency&0x20?44100:48000);
        Serial.printf("[MUSIC] Sample rate=%d\n",rate.load());
    }
    if(event==ESP_A2D_CONNECTION_STATE_EVT) {
        Serial.printf("[MUSIC] Connection state=%d\n",param->conn_stat.state);
        if(param->conn_stat.state==ESP_A2D_CONNECTION_STATE_CONNECTED) MediaVoice::changed(true);
        else if(param->conn_stat.state==ESP_A2D_CONNECTION_STATE_DISCONNECTED) MediaVoice::changed(false);
    }
}
static void begin() {
    // BLEDevice has already initialized the dual-mode Bluetooth stack.
    esp_err_t result=esp_avrc_ct_init();
    if(result==ESP_OK) result=esp_a2d_register_callback(event);
    if(result==ESP_OK) result=esp_a2d_sink_register_data_callback(data);
    if(result==ESP_OK) result=esp_a2d_sink_init();
    if(result==ESP_OK) result=esp_bt_gap_set_scan_mode(ESP_BT_CONNECTABLE,ESP_BT_GENERAL_DISCOVERABLE);
    Serial.printf("[MUSIC] %s; pair AlarmPrototype in phone Bluetooth settings.\n",esp_err_to_name(result));
}
}
#else
namespace MusicReceiver { inline void begin() {} }
#endif
