#pragma bank 4
#include "tones.h"
#include "tone_table.h"
uint8_t tone_voice,tone_index,tone_level=15,tone_output,tone_playing;
uint16_t tone_register;
uint8_t tone_noise_clock;
uint32_t tone_hundredths;
static const uint8_t sine[16]={0x89,0xab,0xcd,0xee,0xff,0xee,0xdc,0xba,0x86,0x54,0x32,0x11,0x00,0x11,0x23,0x45};
uint8_t tone_count(void) {return tone_voice<4?sizeof(tone_steps)/sizeof(tone_steps[0]):sizeof(noise_steps);}
void tone_measure(void) {
 static const uint8_t divisors[8]={1,2,4,6,8,10,12,14};
 if(tone_voice<4) {
  tone_register=tone_steps[tone_index];
  tone_hundredths=(tone_voice<2?13107200UL:6553600UL)/(2048u-tone_register);
 } else {
  tone_noise_clock=noise_steps[tone_index];
  tone_hundredths=52428800UL/((uint32_t)divisors[tone_noise_clock&7u]<<(tone_noise_clock>>4));
 }
}
void tone_stop(void) {NR12_REG=NR22_REG=NR30_REG=NR42_REG=0;NR51_REG=0;}
void tone_apply(void) {
 uint8_t i,mask;
 tone_stop();tone_measure();
 if(!tone_playing)return;
 NR52_REG=0x80;NR50_REG=0x77;
 mask=tone_voice==0?0x11:tone_voice==1?0x22:tone_voice<4?0x44:0x88;
 if(tone_output==1)mask&=0xf0;
 else if(tone_output==2)mask&=0x0f;
 NR51_REG=mask;
 if(tone_voice<2) {
  if(tone_voice==0){NR10_REG=0;NR11_REG=0x80;NR12_REG=tone_level<<4;NR13_REG=tone_register;NR14_REG=0x80|(tone_register>>8);}
  else {NR21_REG=0x80;NR22_REG=tone_level<<4;NR23_REG=tone_register;NR24_REG=0x80|(tone_register>>8);}
 } else if(tone_voice<4) {
  NR30_REG=0;
  for(i=0;i<16;++i) *(volatile uint8_t *)(0xff30u+i)=tone_voice==2?sine[i]:(i<8?0xff:0);
  NR30_REG=0x80;
  NR32_REG=tone_level==0?0:tone_level==1?0x60:tone_level==2?0x40:0x20;
  NR33_REG=tone_register;NR34_REG=0x80|(tone_register>>8);
 } else {
  NR41_REG=0;NR42_REG=tone_level<<4;
  NR43_REG=tone_noise_clock|(tone_voice==5?8:0);NR44_REG=0x80;
 }
}
