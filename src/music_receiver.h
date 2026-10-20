#pragma once
#include <Preferences.h>

namespace MediaVoice {
static bool connected=false;
static void changed(bool value) {
    if(connected==value) return;
    connected=value;
    // Production: silent media connection state change
}
}
#ifdef ARDUINO
#include <esp_a2dp_api.h>
#include <esp_gap_bt_api.h>
#include <esp_avrc_api.h>
namespace MusicReceiver {
static std::atomic<int> rate{44100};
static std::atomic<uint32_t> receivedBytes{0}, outputBytes{0}, droppedBytes{0}, writeErrors{0};
static Preferences btPrefs;
static esp_bd_addr_t lastBda = {0};
static bool hasLastBda = false;
static std::atomic<bool> a2dpReady{false};

static bool connectLastDevice() {
    if (!a2dpReady.load()) return false;
    if (!hasLastBda) {
        btPrefs.begin("bt-audio", true);
        size_t len = btPrefs.getBytes("last_bda", lastBda, sizeof(lastBda));
        btPrefs.end();
        hasLastBda = (len == sizeof(lastBda));
    }
    if (hasLastBda) {
        Serial.printf("[MUSIC] Auto-connecting A2DP audio to phone: %02X:%02X:%02X:%02X:%02X:%02X\n",
            lastBda[0], lastBda[1], lastBda[2], lastBda[3], lastBda[4], lastBda[5]);
        esp_err_t res = esp_a2d_sink_connect(lastBda);
        return (res == ESP_OK);
    }
    return false;
}

static void data(const uint8_t* bytes,uint32_t length) {
    receivedBytes.fetch_add(length);
    if(!SpeakerVoice::worker || SpeakerVoice::alarmActive.load() || SpeakerVoice::isPlaying.load()) { droppedBytes.fetch_add(length); return; }
    if(xSemaphoreTake(SpeakerVoice::audioMutex,0)!=pdTRUE) { droppedBytes.fetch_add(length); return; }
    if(SpeakerVoice::alarmActive.load() || SpeakerVoice::isPlaying.load()) {
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
    for(uint32_t offset=0;offset+3<length && !SpeakerVoice::alarmActive.load() && !SpeakerVoice::isPlaying.load();) {
        size_t count=0;
        while(count<256 && offset+3<length) {
            int16_t left=(int16_t)(bytes[offset]|(bytes[offset+1]<<8));
            int16_t right=(int16_t)(bytes[offset+2]|(bytes[offset+3]<<8));
            int32_t mono=AudioSamples::music(left,right);
            block[count++]=mono; block[count++]=mono;
            offset+=4;
        }
        size_t sent=0, total=count*sizeof(int32_t);
        while(sent<total) {
            size_t written=0;
            esp_err_t result=i2s_write(SpeakerVoice::port,reinterpret_cast<uint8_t*>(block)+sent,
                total-sent,&written,pdMS_TO_TICKS(80));
            sent+=written;
            outputBytes.fetch_add(written);
            if(result!=ESP_OK || !written) { ++writeErrors; break; }
        }
        if(sent!=total) break;
    }
    xSemaphoreGive(SpeakerVoice::audioMutex);
}
static void event(esp_a2d_cb_event_t event,esp_a2d_cb_param_t* param) {
    if(event==ESP_A2D_PROF_STATE_EVT) {
        if(param->a2d_prof_stat.init_state==ESP_A2D_INIT_SUCCESS) {
            a2dpReady.store(true);
            Serial.println("[MUSIC] A2DP sink initialized; attempting auto-reconnect...");
            connectLastDevice();
        }
    }
    if(event==ESP_A2D_AUDIO_STATE_EVT)
        Serial.printf("[MUSIC] Audio state=%d (started=%d)\n",param->audio_stat.state,ESP_A2D_AUDIO_STATE_STARTED);
    if(event==ESP_A2D_AUDIO_CFG_EVT) {
        uint8_t frequency=param->audio_cfg.mcc.cie.sbc[0];
        rate.store(frequency&0x80?16000:frequency&0x40?32000:frequency&0x20?44100:48000);
        Serial.printf("[MUSIC] Sample rate=%d\n",rate.load());
    }
    if(event==ESP_A2D_CONNECTION_STATE_EVT) {
        Serial.printf("[MUSIC] Connection state=%d\n",param->conn_stat.state);
        if(param->conn_stat.state==ESP_A2D_CONNECTION_STATE_CONNECTED) MediaVoice::changed(true);
        else if(param->conn_stat.state==ESP_A2D_CONNECTION_STATE_DISCONNECTED) MediaVoice::changed(false);
        if(param->conn_stat.state==ESP_A2D_CONNECTION_STATE_CONNECTED) {
            MediaVoice::changed(true);
            // Save the phone's MAC address so ESP32 can auto-reconnect A2DP
            memcpy(lastBda, param->conn_stat.remote_bda, sizeof(esp_bd_addr_t));
            hasLastBda = true;
            btPrefs.begin("bt-audio", false);
            btPrefs.putBytes("last_bda", lastBda, sizeof(lastBda));
            btPrefs.end();
            Serial.printf("[MUSIC] Saved phone MAC for auto-reconnect: %02X:%02X:%02X:%02X:%02X:%02X\n",
                lastBda[0], lastBda[1], lastBda[2], lastBda[3], lastBda[4], lastBda[5]);
        }
        else if(param->conn_stat.state==ESP_A2D_CONNECTION_STATE_DISCONNECTED) {
            MediaVoice::changed(false);
        }
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
static void report() {
    Serial.printf("[MUSIC] Last interval: received=%u output=%u dropped=%u errors=%u speaker=%s alarm=%d\n",
        (unsigned)receivedBytes.exchange(0),(unsigned)outputBytes.exchange(0),
        (unsigned)droppedBytes.exchange(0),(unsigned)writeErrors.exchange(0),
        SpeakerVoice::worker?"ready":"unavailable",SpeakerVoice::alarmActive.load()?1:0);
}
}
#else
namespace MusicReceiver {
inline void begin() {}
inline void report() {}
inline bool connectLastDevice() { return false; }
}
#endif
