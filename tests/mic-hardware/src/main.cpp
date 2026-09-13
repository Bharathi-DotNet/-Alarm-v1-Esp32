#include <Arduino.h>
#include <driver/i2s.h>
#include <math.h>
// Standalone diagnostic: no BLE, RTC or Preferences writes.
static const i2s_port_t port = I2S_NUM_0;
void requireOk(esp_err_t result, const char* operation) {
    if(result == ESP_OK) return;
    Serial.printf("[MIC ERROR] %s: %s\n", operation, esp_err_to_name(result));
    while(true) delay(1000);
}
void setup() {
    pinMode(23, OUTPUT); digitalWrite(23, LOW);
    Serial.begin(115200); delay(1000);
    i2s_config_t config = {};
    config.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
    config.sample_rate = 16000;
    config.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
    config.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
    config.communication_format = I2S_COMM_FORMAT_STAND_I2S;
    config.intr_alloc_flags = 0;
    config.dma_buf_count = 8;
    config.dma_buf_len = 256;
    config.use_apll = false;
    i2s_pin_config_t pins = {};
    pins.mck_io_num = I2S_PIN_NO_CHANGE;
    pins.bck_io_num = 18;
    pins.ws_io_num = 19;
    pins.data_out_num = I2S_PIN_NO_CHANGE;
    pins.data_in_num = 5;
    requireOk(i2s_driver_install(port, &config, 0, nullptr), "install");
    requireOk(i2s_set_pin(port, &pins), "pins");
    // Mic starts after receiving clocks. Discard startup samples.
    int32_t discard[256]; size_t bytes;
    for(int i=0;i<16;++i) i2s_read(port, discard, sizeof(discard), &bytes, pdMS_TO_TICKS(1000));
    Serial.println("MIC TEST V2: BCLK=18 WS=19 SD=5 BOTH CHANNELS, 16kHz; keep L/R=GND");
    Serial.println("Stay quiet 5 seconds; speak near the mic 5 seconds; repeat. Compare AC_RMS and peak.");
}

struct ChannelStats {
    double sum=0, squares=0;
    int32_t lo=8388607, hi=-8388608;
    uint32_t firstRaw=0;
    size_t count=0;
    void add(int32_t raw) {
        if(count==0) firstRaw=(uint32_t)raw;
        int32_t value=raw >> 8;
        sum+=value; squares+=(double)value*value;
        if(value<lo) lo=value;
        if(value>hi) hi=value;
        ++count;
    }
    void print(const char* label) {
        if(count==0) { Serial.printf("%s NO DATA\n",label); return; }
        double mean=sum/count, variance=squares/count-mean*mean;
        double rms=sqrt(variance>0?variance:0);
        Serial.printf("%s raw=0x%08lX min=%ld max=%ld AC_RMS=%.1f peakToPeak=%ld%s\n",
            label,(unsigned long)firstRaw,(long)lo,(long)hi,rms,(long)(hi-lo),hi==lo?" STUCK":"");
    }
};
void loop() {
    int32_t samples[512]; ChannelStats a,b;
    // Label interleaved slots A/B rather than assume driver channel ordering.
    for(int block=0;block<32;++block) {
        size_t bytes=0;
        esp_err_t result=i2s_read(port,samples,sizeof(samples),&bytes,pdMS_TO_TICKS(1000));
        if(result!=ESP_OK || bytes==0 || bytes%8!=0) {
            Serial.printf("[MIC ERROR] read=%s bytes=%u\n",esp_err_to_name(result),(unsigned)bytes);
            delay(500); return;
        }
        for(size_t i=0;i<bytes/sizeof(int32_t);i+=2) { a.add(samples[i]); b.add(samples[i+1]); }
    }
    a.print("SLOT_A"); b.print("SLOT_B"); Serial.println();
}
