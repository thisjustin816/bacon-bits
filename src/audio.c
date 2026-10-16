#pragma bank 4
#include "bb.h"
#include "tones.h"
#include <string.h>
uint8_t audio_row,audio_page;
static uint8_t graph[256];
static uint8_t audio_seen;
static const char *const presets[]={"","LOW END","PULSE PAIR","STEREO CHECK","BURST CHECK"};
static const char *const preset_notes[]={"KEEP SETTINGS","32 HZ SINE / FULL","440 HZ / 50% DUTY","440 HZ / LEFT","TRIANGLE / 30F GAP"};
static uint16_t gate_started;
static uint8_t preview_voice=255,preview_shape=255;
static const char * const voices[]={"PULSE 1","PULSE 2","WAVE","NOISE"};
static const char * const outputs[]={"BOTH","LEFT","RIGHT"};
static const char * const wave_levels[]={"MUTE","QUARTER","HALF","FULL"};
static const char * const wave_names[]={"SINE","SQUARE","TRIANGLE","SAW UP","SAW DOWN","PULSE 25"};
static const char * const duties[]={"12.5%","25%","50%","75%"};
static void preview(void) {
 uint8_t x,y,previous=7,i,samples[32];uint16_t at;
 if(preview_voice==tone_voice && preview_shape==tone_shape[tone_voice])return;
 preview_voice=tone_voice;preview_shape=tone_shape[tone_voice];
 for(i=0;i<32;++i)samples[i]=tone_sample(i);
 memset(graph,0,sizeof(graph));
 for(i=0;i<16;++i)graph[i*16u+14u]=0xff;
 for(x=0;x<128;++x){y=7u-samples[x>>2]*7u/15u;at=(uint16_t)(x>>3)*16u;
  if(y<previous)for(i=y;i<=previous;++i){graph[at+i*2u]|=0x80u>>(x&7u);graph[at+i*2u+1u]|=0x80u>>(x&7u);}
  else for(i=previous;i<=y;++i){graph[at+i*2u]|=0x80u>>(x&7u);graph[at+i*2u+1u]|=0x80u>>(x&7u);}
  previous=y;
 }
 set_bkg_data(80,16,graph);for(i=0;i<16;++i)ui_cell(2+i,15,80+i);
}
static void draw_audio(void) {
 uint8_t row;char value[12],*end;
 tone_measure();fill_bkg_rect(1,4,18,1,0);ui_text(1,4,"AUDIO RANGE");ui_text(16,4,audio_page?"2/2":"1/2");
 for(row=0;row<4;++row) {
  if(!audio_page) {
   if(row==0)ui_field(row,"VOICE",voices[tone_voice],row==audio_row);
   else if(row==1){end=ui_decimal(value,tone_hundredths/100UL);
    if(tone_hundredths<100000UL){*end++='.';*end++='0'+(tone_hundredths%100UL)/10UL;*end++='0'+tone_hundredths%10UL;*end=0;}
    ui_field(row,tone_voice==3?"CLOCK":"HZ",value,row==audio_row);
   } else if(row==2){if(tone_voice==2)ui_field(row,"LEVEL",wave_levels[tone_level],row==audio_row);
    else {end=ui_decimal(value,tone_level);*end++='/';*end++='1';*end++='5';*end=0;ui_field(row,"LEVEL",value,row==audio_row);}}
   else ui_field(row,"OUTPUT",outputs[tone_output],row==audio_row);
  } else {
   if(row==0)ui_field(row,"SHAPE",tone_voice<2?duties[tone_shape[tone_voice]]:tone_voice==2?wave_names[tone_shape[2]]:tone_shape[3]?"7 BIT":"15 BIT",row==audio_row);
   else if(row==1)ui_field(row,"STEPS",tone_voice==3?"CLOCKS":tone_fine?"FINE":"PRESET",row==audio_row && tone_voice!=3);
   else if(row==2){if(tone_on)ui_value(row,"ON FR",tone_on,row==audio_row);else ui_field(row,"ON FR","HOLD",row==audio_row);}
   else ui_value(row,"GAP FR",tone_gap,row==audio_row);
  }
 }
 preview();ui_status(tone_playing?(tone_gate?"PLAYING":"REST"):"SILENT");
}
static void change_audio(int8_t step) {
 uint8_t wave=tone_voice==2;
 if(!audio_page) {
  if(audio_row==0){tone_voice=(tone_voice+4u+step)&3u;if(wave!=(tone_voice==2))tone_level=tone_voice==2?3:15;
   if(tone_index>=tone_count())tone_index=tone_count()-1u;if(tone_voice==3)tone_fine=0;}
  else if(audio_row==1){if(tone_fine){if(step<0 && tone_register)--tone_register;if(step>0 && tone_register<2047)++tone_register;}
   else {if(step<0 && tone_index)--tone_index;if(step>0 && tone_index+1u<tone_count())++tone_index;}}
  else if(audio_row==2){if(step<0 && tone_level)--tone_level;if(step>0 && tone_level<(tone_voice==2?3:15))++tone_level;}
  else tone_output=(tone_output+3u+step)%3u;
 } else {
  if(audio_row==0)tone_shape[tone_voice]=(tone_shape[tone_voice]+(tone_voice<2?4u:tone_voice==2?6u:2u)+step)%(tone_voice<2?4u:tone_voice==2?6u:2u);
  else if(audio_row==1 && tone_voice<3)tone_fine^=1u;
  else if(audio_row==2){if(step<0 && tone_on)--tone_on;if(step>0 && tone_on<120)++tone_on;}
  else if(audio_row==3){if(step<0 && tone_gap)--tone_gap;if(step>0 && tone_gap<120)++tone_gap;}
 }
 tone_gate=1;gate_started=bb_frame();tone_apply();
}
void audio_run(void) BANKED {
 uint8_t keys,pressed,previous=0,repeat=0,directions,dirty,preset;
 if(!audio_seen){
 tone_voice=tone_index=tone_output=tone_playing=tone_fine=tone_on=tone_gap=0;
 tone_shape[0]=tone_shape[1]=2;tone_shape[2]=tone_shape[3]=0;tone_gate=1;tone_level=15;}
 tone_playing=0;tone_gate=1;
 preset=ui_presets("AUDIO PRESETS",presets,preset_notes,audio_seen);if(preset==255)return;audio_seen=1;
 if(preset){tone_voice=0;tone_index=22;tone_level=15;tone_output=tone_fine=tone_on=tone_gap=0;tone_shape[0]=tone_shape[1]=2;
  if(preset==1){tone_voice=2;tone_index=0;tone_level=3;tone_shape[2]=0;}
  if(preset==3){tone_output=1;tone_level=8;}
  if(preset==4){tone_voice=2;tone_level=3;tone_shape[2]=2;tone_on=tone_gap=30;}
 }audio_row=1;audio_page=0;
 preview_voice=255;NR52_REG=0x80;tone_stop();ui_screen("AUDIO RANGE","1/2");draw_audio();
 for(;;) {
  vsync();keys=joypad();pressed=keys&~previous;directions=keys&15u;dirty=0;
  if(directions && directions==(previous&15u)){if(++repeat>=24u){pressed|=directions;repeat=18u;}}else repeat=0;previous=keys;
  if(pressed&J_B){tone_playing=0;tone_stop();NR52_REG=0;return;}
  if(pressed&J_SELECT){audio_page^=1;audio_row=0;}
  if(pressed&J_UP){audio_row=(audio_row+3)&3u;if(audio_page && tone_voice==3 && audio_row==1)audio_row=0;}if(pressed&J_DOWN){audio_row=(audio_row+1)&3u;if(audio_page && tone_voice==3 && audio_row==1)audio_row=2;}
  if(pressed&J_LEFT)change_audio(-1);if(pressed&J_RIGHT)change_audio(1);
  if(pressed&J_A){tone_playing^=1;tone_gate=1;gate_started=bb_frame();tone_apply();}
  if(tone_playing && tone_on && (uint16_t)(bb_frame()-gate_started)>=(tone_gate?tone_on:tone_gap)){
   gate_started=bb_frame();if(tone_gate){tone_gate=0;if(!tone_gap)tone_playing=0;}else tone_gate=1;tone_apply();dirty=1;
  }
  if(pressed || dirty)draw_audio();
 }
}
