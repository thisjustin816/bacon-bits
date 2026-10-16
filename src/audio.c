#pragma bank 4
#include "bb.h"
#include "tones.h"

uint8_t audio_row;
static const char * const voices[]={"PULSE 1","PULSE 2","WAVE SIN","WAVE SQ","NOISE 15","NOISE 7"};
static const char * const outputs[]={"BOTH","LEFT","RIGHT"};
static const char * const wave_levels[]={"MUTE","QUARTER","HALF","FULL"};
static const char * const fields[]={"VOICE","HZ","LEVEL","OUTPUT"};

/* GBDK's compact printf does not implement these width/long combinations. */
static char *decimal(char *out,uint32_t number) {
 char digits[10];
 uint8_t n=0;
 do {digits[n++]=(char)('0'+number%10UL);number/=10UL;} while(number);
 while(n)*out++=digits[--n];
 *out=0;
 return out;
}

static uint8_t wave_voice(void) {return tone_voice==2u || tone_voice==3u;}
static void draw_audio(void) {
 uint8_t row,y;
 char value[12],*end;
 tone_measure();
 for(row=0;row!=4;++row) {
  y=6u+row*2u;
  fill_bkg_rect(1,y,18,1,0);
  ui_cell(1,y,row==audio_row?71:0);
  ui_text(3,y,row==1u && tone_voice>=4u?"CLOCK":fields[row]);
  if(row==0) ui_text(10,y,voices[tone_voice]);
  else if(row==1) {
   end=decimal(value,tone_hundredths/100UL);
   if(tone_hundredths<100000UL) {
    *end++='.';*end++=(char)('0'+(tone_hundredths%100UL)/10UL);
    *end++=(char)('0'+tone_hundredths%10UL);*end=0;
   }
   ui_text(10,y,value);
  } else if(row==2) {
   if(wave_voice())ui_text(10,y,wave_levels[tone_level]);
   else {end=decimal(value,tone_level);*end++='/';*end++='1';*end++='5';*end=0;ui_text(10,y,value);}
  } else ui_text(10,y,outputs[tone_output]);
  if(row==audio_row) {
   if((row!=1u && row!=2u) || (row==1u?tone_index:tone_level)>0u)ui_cell(8,y,70);
   if((row!=1u && row!=2u) || (row==1u?tone_index+1u<tone_count():tone_level<(wave_voice()?3u:15u)))ui_cell(18,y,71);
  }
 }
 fill_bkg_rect(0,16,20,1,0);
 ui_text(tone_playing?6:7,16,tone_playing?"PLAYING":"SILENT");
}

static void change_audio(int8_t step) {
 uint8_t was_wave=wave_voice();
 if(audio_row==0) {
  tone_voice=(tone_voice+6u+step)%6u;
  if(was_wave!=wave_voice())tone_level=wave_voice()?3u:15u;
  if(tone_index>=tone_count())tone_index=tone_count()-1u;
 } else if(audio_row==1) {
  if(step<0 && tone_index) --tone_index;
  if(step>0 && tone_index+1u<tone_count()) ++tone_index;
 } else if(audio_row==2) {
  if(step<0 && tone_level) --tone_level;
  if(step>0 && tone_level<(wave_voice()?3u:15u)) ++tone_level;
 } else tone_output=(tone_output+3u+step)%3u;
 tone_apply();
}

void audio_run(void) BANKED {
 uint8_t keys,pressed,previous=0,repeat=0,directions;
 tone_voice=tone_index=tone_output=tone_playing=0;
 tone_level=15;audio_row=1;
 NR52_REG=0x80;tone_stop();
 ui_init();ui_text(4,4,"AUDIO RANGE");ui_box(5,14);draw_audio();
 for(;;) {
  vsync();keys=joypad();pressed=keys&~previous;
  directions=keys&(J_UP|J_DOWN|J_LEFT|J_RIGHT);
  if(directions && directions==(previous&(J_UP|J_DOWN|J_LEFT|J_RIGHT))) {
   if(++repeat>=24u) {pressed|=directions;repeat=18u;}
  } else repeat=0;
  previous=keys;
  if(pressed&J_B) {tone_playing=0;tone_stop();NR52_REG=0;return;}
  if(pressed&J_UP) audio_row=(audio_row+3u)&3u;
  if(pressed&J_DOWN) audio_row=(audio_row+1u)&3u;
  if(pressed&J_LEFT) change_audio(-1);
  if(pressed&J_RIGHT) change_audio(1);
  if(pressed&J_A) {tone_playing^=1u;tone_apply();}
  if(pressed) draw_audio();
 }
}
