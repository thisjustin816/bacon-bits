#pragma bank 4
#include "tones.h"
#include "tone_table.h"
uint8_t tone_voice,tone_index,tone_level=15,tone_output,tone_playing;
uint8_t tone_shape[4]={2,2,0,0},tone_fine,tone_on,tone_gap,tone_gate=1;
uint16_t tone_register;
uint8_t tone_noise_clock;
uint32_t tone_hundredths;
static const uint8_t sine[32]={8,9,10,11,13,14,14,15,15,15,14,14,13,11,10,9,8,6,5,4,2,1,1,0,0,0,1,1,2,4,5,6};
uint8_t tone_count(void) {return tone_voice<3?sizeof(tone_steps)/sizeof(tone_steps[0]):sizeof(noise_steps);}
uint8_t tone_sample(uint8_t sample) {
 uint8_t shape=tone_shape[tone_voice],n;uint16_t lfsr;
 if(tone_voice<2)return sample<(shape==0?4:shape==1?8:shape==2?16:24)?15:0;
 if(tone_voice==2) {
  switch(shape) {
   case 0:return sine[sample];
   case 1:return sample<16?15:0;
   case 2:return sample<16?sample:31u-sample;
   case 3:return sample>>1;
   case 4:return 15u-(sample>>1);
   default:return sample<8?15:0;
  }
 }
 lfsr=0x7fff;
 for(n=0;n<=sample;++n) {uint8_t bit=(lfsr^(lfsr>>1))&1u;lfsr=(lfsr>>1)|((uint16_t)bit<<14);if(shape)lfsr=(lfsr&~0x40u)|((uint16_t)bit<<6);}
 return (lfsr&1u)?0:15;
}
void tone_measure(void) {
 static const uint8_t divisors[8]={1,2,4,6,8,10,12,14};
 if(tone_voice<3) {
  if(!tone_fine)tone_register=tone_steps[tone_index];
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
 if(!tone_playing || !tone_gate)return;
 NR52_REG=0x80;NR50_REG=0x77;
 mask=tone_voice==0?0x11:tone_voice==1?0x22:tone_voice==2?0x44:0x88;
 if(tone_output==1)mask&=0xf0;else if(tone_output==2)mask&=0x0f;NR51_REG=mask;
 if(tone_voice<2) {
  if(tone_voice==0){NR10_REG=0;NR11_REG=tone_shape[0]<<6;NR12_REG=tone_level<<4;NR13_REG=tone_register;NR14_REG=0x80|(tone_register>>8);}
  else {NR21_REG=tone_shape[1]<<6;NR22_REG=tone_level<<4;NR23_REG=tone_register;NR24_REG=0x80|(tone_register>>8);}
 } else if(tone_voice==2) {
  NR30_REG=0;
  for(i=0;i<16;++i)*(volatile uint8_t *)(0xff30u+i)=(tone_sample(i*2u)<<4)|tone_sample(i*2u+1u);
  NR30_REG=0x80;NR32_REG=tone_level==0?0:tone_level==1?0x60:tone_level==2?0x40:0x20;
  NR33_REG=tone_register;NR34_REG=0x80|(tone_register>>8);
 } else {NR41_REG=0;NR42_REG=tone_level<<4;NR43_REG=tone_noise_clock|(tone_shape[3]?8:0);NR44_REG=0x80;}
}
void burn_audio(uint8_t voice) BANKED {
 if(voice==255){tone_playing=0;tone_stop();NR52_REG=0;return;}
 tone_voice=voice;tone_index=22;tone_fine=0;tone_level=voice==2?3:8;tone_output=0;
 tone_gate=tone_playing=1;tone_on=tone_gap=0;tone_apply();
}
