#include <Arduino.h>
#include <driver/i2s.h>
#include <math.h>
static const i2s_port_t audioPort = I2S_NUM_1;
void check(esp_err_t e) {
    if(e==ESP_OK) return;
    Serial.printf("SPEAKER ERROR: %s\n",esp_err_to_name(e));
    while(true) delay(1000);
}
// Both stereo slots contain the same low-amplitude tone, for any amp channel mode.
void play(float frequency, int ms) {
    int32_t samples[256*2];
    const int total=16000*ms/1000;
    for(int offset=0;offset<total;) {
        int count=min(256,total-offset);
        for(int i=0;i<count;++i) {
            int t=offset+i;
            float envelope=min(1.0f,min(t/160.0f,(total-1-t)/160.0f));
            int16_t value=frequency>0?(int16_t)(2000.0f*envelope*sinf(2.0f*PI*frequency*t/16000.0f)):0;
            // Preserve V2 amplitude by scaling signed PCM16 into PCM32 without signed shifts.
            samples[2*i]=samples[2*i+1]=(int32_t)value * 65536;
        }
        size_t bytes=0;
        check(i2s_write(audioPort,samples,count*2*sizeof(int32_t),&bytes,pdMS_TO_TICKS(1000)));
        if(bytes!=(size_t)count*2*sizeof(int32_t)) { Serial.println("SPEAKER ERROR: incomplete write"); while(true) delay(1000); }
        offset+=count;
    }
}
void setup() {
    pinMode(23,OUTPUT); digitalWrite(23,LOW);
    Serial.begin(115200); delay(1000);
    i2s_config_t config={};
    config.mode=(i2s_mode_t)(I2S_MODE_MASTER|I2S_MODE_TX);
    config.sample_rate=16000;
    config.bits_per_sample=I2S_BITS_PER_SAMPLE_32BIT;
    config.channel_format=I2S_CHANNEL_FMT_RIGHT_LEFT;
    config.communication_format=I2S_COMM_FORMAT_STAND_I2S;
    config.dma_buf_count=4; config.dma_buf_len=256;
    config.tx_desc_auto_clear=true;
    i2s_pin_config_t pins={};
    pins.mck_io_num=I2S_PIN_NO_CHANGE;
    pins.bck_io_num=26; pins.ws_io_num=25;
    pins.data_out_num=22; pins.data_in_num=I2S_PIN_NO_CHANGE;
    check(i2s_driver_install(audioPort,&config,0,nullptr));
    check(i2s_set_pin(audioPort,&pins));
    check(i2s_zero_dma_buffer(audioPort));
    Serial.println("SPEAKER TEST V4: BCLK=26, LRC=25, DIN=22. 32-bit stereo, 16kHz. Same volume as V2.");
    Serial.println("Two one-second tones every 5 seconds. Alarm and microphone capture are inactive.");
}
void loop() {
    Serial.println("PLAY: 600Hz then 900Hz");
    play(600,1000); play(0,500); play(900,1000); play(0,2500);
}
