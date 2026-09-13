#include <Arduino.h>
#include <driver/i2s.h>
constexpr int sampleRate=16000, sampleCount=sampleRate*3;
int16_t* recording=nullptr;
void check(esp_err_t e) {
 if(e==ESP_OK)return;
 Serial.printf("ERROR: %s\n",esp_err_to_name(e));
 while(true)delay(1000);
}
void configure(i2s_port_t port,bool receive,int bclk,int ws,int data) {
 i2s_config_t cfg={};
 cfg.mode=(i2s_mode_t)(I2S_MODE_MASTER|(receive?I2S_MODE_RX:I2S_MODE_TX));
 cfg.sample_rate=sampleRate;cfg.bits_per_sample=I2S_BITS_PER_SAMPLE_32BIT;
 cfg.channel_format=I2S_CHANNEL_FMT_RIGHT_LEFT;cfg.communication_format=I2S_COMM_FORMAT_STAND_I2S;
 cfg.dma_buf_count=4;cfg.dma_buf_len=256;cfg.tx_desc_auto_clear=true;
 i2s_pin_config_t pins={};pins.mck_io_num=I2S_PIN_NO_CHANGE;
 pins.bck_io_num=bclk;pins.ws_io_num=ws;
 pins.data_in_num=receive?data:I2S_PIN_NO_CHANGE;pins.data_out_num=receive?I2S_PIN_NO_CHANGE:data;
 check(i2s_driver_install(port,&cfg,0,nullptr));check(i2s_set_pin(port,&pins));
}
void recordAndPlay() {
 int32_t block[512];size_t bytes=0;
 // Discard previously queued microphone samples before recording.
 for(int n=0;n<8;++n)check(i2s_read(I2S_NUM_0,block,sizeof(block),&bytes,pdMS_TO_TICKS(1000)));
 Serial.println("RECORDING: Speak now for 3 seconds.");
 int position=0;int peak=0;
 while(position<sampleCount) {
  check(i2s_read(I2S_NUM_0,block,sizeof(block),&bytes,pdMS_TO_TICKS(1000)));
  if(!bytes||bytes%8){Serial.println("ERROR: Invalid mic read");return;}
  for(size_t i=0;i<bytes/4 && position<sampleCount;i+=2) {
   // SLOT_A is the working slot established by the user's stereo microphone test.
   int16_t v=(int16_t)(block[i]>>16);
   recording[position++]=v;peak=max(peak,abs((int)v));
  }
 }
 Serial.printf("RECORDED: peak=%d. Playing at limited volume.\n",peak);
 if(peak==0){Serial.println("No mic data. Check mic connections.");return;}
 // Only attenuate; avoid amplifying disconnected-input noise.
 float gain=peak>3500?3500.0f/peak:1.0f;
 for(int offset=0;offset<sampleCount;offset+=256) {
  int count=min(256,sampleCount-offset);
  for(int i=0;i<count;++i){
   int t=offset+i;
   float fade=min(1.0f,min(t/160.0f,(sampleCount-1-t)/160.0f));
   int32_t value=(int32_t)(recording[t]*gain*fade)*65536;
   block[2*i]=block[2*i+1]=value;
  }
  check(i2s_write(I2S_NUM_1,block,count*8,&bytes,pdMS_TO_TICKS(1000)));
  if(bytes!=(size_t)count*8){Serial.println("ERROR: Incomplete speaker write");return;}
 }
 memset(block,0,sizeof(block));
 for(int n=0;n<5;++n)check(i2s_write(I2S_NUM_1,block,sizeof(block),&bytes,pdMS_TO_TICKS(1000)));
 check(i2s_zero_dma_buffer(I2S_NUM_1));
 Serial.println("DONE. Send r to record again. Audio stays in RAM only.");
}
void setup(){
 pinMode(23,OUTPUT);digitalWrite(23,LOW);
 Serial.begin(115200);delay(1000);
 recording=(int16_t*)malloc(sampleCount*sizeof(int16_t));
 if(!recording){Serial.println("ERROR: Not enough recording RAM");while(true)delay(1000);}
 configure(I2S_NUM_0,true,18,19,5);configure(I2S_NUM_1,false,26,25,27);
 check(i2s_zero_dma_buffer(I2S_NUM_1));
 Serial.println("VOICE LOOPBACK V1: Mic18/19/5 SLOT_A; speaker26/25/27.");
 Serial.println("Alarm/BLE inactive. Send r to record 3 seconds and replay once.");
}
void loop(){
 if(Serial.available()){
  int command=Serial.read();
  if(command=='r'||command=='R')recordAndPlay();
 }
 delay(10);
}
