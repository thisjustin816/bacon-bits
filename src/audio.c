#pragma bank 4
#include "bb.h"
#include "tones.h"
#include <string.h>
uint8_t audio_row,audio_page;
static uint8_t graph[1536],graph_previous[1536];
static uint8_t preview_phase=255,preview_level=255;
static uint8_t audio_seen;
static const char *const presets[]={"","Low end","Pulse pair","Stereo check","Burst check"};
static const char *const preset_notes[]={"Keep settings","32 Hz sine / full","440 Hz / 50% duty","440 Hz / left","Triangle / 30f gap"};
static uint16_t gate_started;
static uint8_t preview_voice=255,preview_shape=255,scroll_pending,scroll_map[96];
static const char * const voices[]={"Pulse 1","Pulse 2","Wave","Noise"};
static const char * const outputs[]={"Both","Left","Right"};
static const char * const wave_names[]={"Sine","Square","Triangle","Saw up","Saw down","Pulse 25"};
static const char * const duties[]={"12.5%","25%","50%","75%"};
static void preview(void) {
 uint8_t x,y,previous=24,i,sy,phase=tone_playing && tone_gate?(uint8_t)(bb_frame()/6u)&15u:0;
 uint8_t height=tone_voice==2?(tone_level==3?40:tone_level==2?20:tone_level==1?10:0):(uint8_t)((uint16_t)tone_level*40u/15u);
 uint16_t at;
 if(audio_page)return;
 if(preview_voice==tone_voice && preview_shape==tone_shape[tone_voice] && preview_level==tone_level){
  if(phase==preview_phase)return;
 }else{
  preview_voice=tone_voice;preview_shape=tone_shape[tone_voice];preview_level=tone_level;
  memset(graph,0,sizeof(graph));
  for(i=0;i<96;++i)graph[i*16u]=0x80;
  for(x=0;x<32;++x){y=24u+height/2u-(uint16_t)tone_sample(x)*height/15u;
   if(!x)previous=y;
   at=((uint16_t)(y&0x38u)<<5)+((uint16_t)(x>>1)<<4)+(y&7u)*2u;
   graph[at+1]|=(x&1u)?0x0f:0xf0;
   for(sy=y<previous?y:previous;sy<=(y>previous?y:previous);++sy){
    at=((uint16_t)(sy&0x38u)<<5)+((uint16_t)(x>>1)<<4)+(sy&7u)*2u;
    graph[at+1]|=(x&1u)?0x08:0x80;
   }previous=y;
  }
  for(i=0;i<96;++i)if(memcmp(graph+i*16u,graph_previous+i*16u,16)){set_bkg_data(UI_ART+i,1,graph+i*16u);memcpy(graph_previous+i*16u,graph+i*16u,16);}
 }
 preview_phase=phase;
 /* The loop copies this right after VBlank, before the beam reaches the
    graph, so a scroll step never shows half old and half new. */
 for(y=0;y<6;++y)for(x=0;x<16;++x)scroll_map[y*16u+x]=UI_ART+y*16+((x+phase)&15u);
 scroll_pending=1;
}
static void audio_front(void) {
 char value[12],*end;uint8_t i;
 static const uint8_t cursor_x[]={1,10,10,1},cursor_y[]={13,13,UI_DETAIL,UI_DETAIL};
 tone_measure();ui_text(2,UI_TOP,"Audio");
 ui_pad(2,13,voices[tone_voice],8);
 /* At most five characters, right-aligned to column 15, so the value never
    runs into its unit: 0.1 Hz below 1 kHz, then whole Hz, then kHz. */
 if(tone_hundredths>=10000000UL){end=ui_decimal(value,tone_hundredths/100000UL);*end++='k';*end=0;}
 else{end=ui_decimal(value,tone_hundredths/100u);if(tone_hundredths<100000UL){*end++='.';*end++='0'+tone_hundredths%100u/10u;*end=0;}}
 {uint8_t x=16u-(uint8_t)(end-value);if(x>11u)fill_bkg_rect(11,13,x-11u,1,0);ui_text(x,13,value);}ui_text(17,13,"Hz");preview();
 ui_status(tone_playing?(tone_gate?"Playing":"Rest"):"Silent");
 ui_corner(tone_voice<2?duties[tone_shape[tone_voice]]:tone_voice==2?wave_names[tone_shape[2]]:tone_shape[3]?"7 bit":"15 bit");
 ui_cell(0,UI_DETAIL,0);ui_pad(2,UI_DETAIL,outputs[tone_output],8);
 ui_text(11,UI_DETAIL,"Level");ui_count(17,UI_DETAIL,tone_level,2);
 for(i=0;i<4;++i)ui_cell(cursor_x[i],cursor_y[i],i==audio_row?UI_CURSOR:0);
}
static void draw_audio(void) {
 if(!audio_page){audio_front();return;}
 tone_measure();
 ui_field(0,"Shape",tone_voice<2?duties[tone_shape[tone_voice]]:tone_voice==2?wave_names[tone_shape[2]]:tone_shape[3]?"7 bit":"15 bit",audio_row==0);
 ui_field(1,"Steps",tone_voice==3?"Clocks":tone_fine?"Fine":"Preset",audio_row==1 && tone_voice!=3);
 if(tone_on)ui_value(2,"On fr",tone_on,audio_row==2);else ui_field(2,"On fr","Hold",audio_row==2);
 ui_value(3,"Gap fr",tone_gap,audio_row==3);
 ui_status(tone_playing?(tone_gate?"Playing":"Rest"):"Silent");
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
 preset=ui_presets("Audio presets",presets,preset_notes,audio_seen);if(preset==255)return;audio_seen=1;
 if(preset){tone_voice=0;tone_index=22;tone_level=15;tone_output=tone_fine=tone_on=tone_gap=0;tone_shape[0]=tone_shape[1]=2;
  if(preset==1){tone_voice=2;tone_index=0;tone_level=3;tone_shape[2]=0;}
  if(preset==3){tone_output=1;tone_level=8;}
  if(preset==4){tone_voice=2;tone_level=3;tone_shape[2]=2;tone_on=tone_gap=30;}
 }audio_row=1;audio_page=0;
 preview_voice=255;preview_phase=255;preview_level=255;memset(graph_previous,0xff,sizeof(graph_previous));tone_power();ui_screen("Audio","");draw_audio();
 for(;;) {
  /* Poll before the graph copy, which runs about 48 lines; polling after it
     leaves a gap long enough to miss a one-frame tap. */
  vsync();keys=joypad();
  if(scroll_pending && !audio_page){set_bkg_tiles(2,6,16,6,scroll_map);scroll_pending=0;}
  pressed=keys&~previous;directions=keys&15u;dirty=0;
  if(directions && directions==(previous&15u)){if(++repeat>=24u){pressed|=directions;repeat=18u;}}else repeat=0;previous=keys;
  if(pressed&J_B){tone_playing=0;tone_stop();NR52_REG=0;return;}
  if(pressed&J_SELECT){audio_page^=1;audio_row=0;ui_screen("Audio",audio_page?"Set":"");preview_voice=255;memset(graph_previous,0xff,sizeof(graph_previous));}
  if(pressed&J_UP){audio_row=(audio_row+3)&3u;if(audio_page && tone_voice==3 && audio_row==1)audio_row=0;}if(pressed&J_DOWN){audio_row=(audio_row+1)&3u;if(audio_page && tone_voice==3 && audio_row==1)audio_row=2;}
  if(pressed&J_LEFT)change_audio(-1);if(pressed&J_RIGHT)change_audio(1);
  if(pressed&J_A){tone_playing^=1;tone_gate=1;gate_started=bb_frame();tone_apply();}
  if(tone_playing && tone_on && (uint16_t)(bb_frame()-gate_started)>=(tone_gate?tone_on:tone_gap)){
   gate_started=bb_frame();if(tone_gate){tone_gate=0;if(!tone_gap)tone_playing=0;}else tone_gate=1;tone_apply();dirty=1;
  }
  if(pressed || dirty)draw_audio();
  else if(!audio_page && tone_playing)preview();
 }
}
