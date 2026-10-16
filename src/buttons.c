#pragma bank 7
#include "bb.h"
#include <string.h>
extern const unsigned char bb_font[];
uint32_t button_presses[8],button_short[8],button_gaps[8];
uint16_t button_held[8],button_longest[8],button_released[8];
uint32_t button_diagonal[4],button_opposites;
uint16_t button_diagonal_hold[4],button_diagonal_peak[4];
uint8_t button_diagonal_view;
static const uint8_t diagonal_bits[]={5,6,9,10};
static const char *const diagonal_names[]={"UP RIGHT","UP LEFT","DN RIGHT","DN LEFT"};
uint8_t button_page,button_pick,button_threshold=1,button_units,button_peak;
static const char *const names[8]={"RIGHT","LEFT","UP","DOWN","A","B","SELECT","START"};
static const uint8_t xs[8]={6,2,4,4,14,12,8,11},ys[8]={9,9,7,11,8,10,12,12};
static const char *const labels[8]={"RT","LT","UP","DN","A","B","SE","ST"};
static uint8_t initialized;
static const char *const presets[]={"","BUTTON CHECK","SHORT EVENTS","HOLD TIMING","DIAGONALS"};
static const char *const notes[]={"KEEP COUNTERS","LIVE BUTTON STATES","1 FRAME THRESHOLD","HOLD MILLISECONDS","D-PAD CORNERS"};
static void clear_counts(void) {
 uint8_t i;button_opposites=0;memset(button_diagonal,0,sizeof(button_diagonal));memset(button_diagonal_hold,0,sizeof(button_diagonal_hold));memset(button_diagonal_peak,0,sizeof(button_diagonal_peak));memset(button_presses,0,sizeof(button_presses));memset(button_short,0,sizeof(button_short));memset(button_gaps,0,sizeof(button_gaps));
 memset(button_longest,0,sizeof(button_longest));memset(button_held,0,sizeof(button_held));for(i=0;i<8;++i)button_released[i]=65535;button_peak=0;
}
static void screen(void) {uint8_t data[128],i,j;ui_screen(button_page==3?"DIAGONALS":"BUTTONS",button_page==0?"1/4":button_page==1?"2/4":button_page==2?"3/4":"4/4");
 for(i=0;i<8;++i){for(j=0;j<128;++j)data[j]=bb_font[i*128u+j]^0xffu;set_bkg_data(160+i*8u,8,data);}}
static void show(uint8_t held) {
 uint8_t i,n=0,x;const char *s;char str[12],*end;
 if(button_page==0){
  for(i=0;i<8;++i){s=labels[i];x=xs[i];while(*s)ui_cell(x++,ys[i],(uint8_t)*s++-32u+((held&(1u<<i))?160u:0u));if(held&(1u<<i))++n;}
  for(i=0;i<4;++i)ui_cell((i&1u)?2:6,(i&2u)?11:7,(held&15u)==diagonal_bits[i]?72:73);
  ui_status("HELD");ui_number(6,16,n);ui_text(9,16,"PEAK");ui_number(15,16,button_peak);
 }else if(button_page==1){for(i=0;i<4;++i)ui_value(i,names[(button_pick+i)&7u],button_presses[(button_pick+i)&7u],i==0);ui_status("PRESS COUNTS");}
 else if(button_page==2){ui_field(0,"BUTTON",names[button_pick],1);ui_value(1,button_units?"HOLD MS":"HOLD FR",button_units?((uint32_t)button_longest[button_pick]*16742UL)/1000UL:button_longest[button_pick],0);
  ui_value(2,"SHORT ON",button_short[button_pick],0);
  ui_value(3,"SHORTOFF",button_gaps[button_pick],0);
  end=ui_decimal(str,button_threshold);*end++=' ';*end++='F';*end++='R';*end=0;ui_status("SHORT AT MOST");ui_text(14,16,str);
 }else {for(i=0;i<4;++i){ui_value(i,diagonal_names[i],button_diagonal_view?(button_diagonal_view==2?((uint32_t)button_diagonal_peak[i]*16742UL)/1000UL:button_diagonal_peak[i]):button_diagonal[i],0);ui_cell(1,6+2*i,(held&15u)==diagonal_bits[i]?72:73);}
 ui_text(1,15,"OPPOSITES");ui_number(12,15,button_opposites);ui_status(button_diagonal_view==0?"ENTRY COUNTS":button_diagonal_view==1?"LONGEST FR":"LONGEST MS");}
}
void buttons_run(void) BANKED {
 uint8_t key,previous=0,pressed,i,n,preset;uint16_t chord=0;uint16_t old,now,delta;
 preset=ui_presets("BUTTON PRESETS",presets,notes,initialized);if(preset==255)return;
 if(!initialized){clear_counts();initialized=1;}memset(button_held,0,sizeof(button_held));if(preset){button_pick=4;button_page=preset==4?3:(preset==2 || preset==3)?2:0;button_threshold=1;button_units=(preset==3);}
 screen();show(0);old=bb_frame();
 for(;;){vsync();now=bb_frame();delta=now-old;old=now;key=joypad();pressed=key&~previous;n=0;
  for(i=0;i<8;++i){uint8_t mask=1u<<i;
   if(key&mask){++n;if(!(previous&mask)){++button_presses[i];if(button_released[i]<=button_threshold)++button_gaps[i];button_held[i]=0;}
    button_held[i]=button_held[i]>65535u-delta?65535u:button_held[i]+delta;if(button_held[i]>button_longest[i])button_longest[i]=button_held[i];
   }else {if(previous&mask){if(button_held[i]<=button_threshold)++button_short[i];button_held[i]=0;button_released[i]=0;}
    button_released[i]=button_released[i]>65535u-delta?65535u:button_released[i]+delta;}
  }
  for(i=0;i<4;++i){if((key&15u)==diagonal_bits[i]){if((previous&15u)!=diagonal_bits[i])++button_diagonal[i];button_diagonal_hold[i]=button_diagonal_hold[i]>65535u-delta?65535u:button_diagonal_hold[i]+delta;if(button_diagonal_hold[i]>button_diagonal_peak[i])button_diagonal_peak[i]=button_diagonal_hold[i];}else button_diagonal_hold[i]=0;}
  if((((key&3u)==3u) || ((key&12u)==12u)) && !(((previous&3u)==3u) || ((previous&12u)==12u)))++button_opposites;
  if(n>button_peak)button_peak=n;
  if(pressed&J_SELECT){button_page=(button_page+1u)&3u;screen();}
  if(button_page==1 || button_page==2){if(pressed&J_LEFT)button_pick=(button_pick+7u)&7u;if(pressed&J_RIGHT)button_pick=(button_pick+1u)&7u;}
  if(button_page==2){if((pressed&J_UP)&&button_threshold<8)++button_threshold;if((pressed&J_DOWN)&&button_threshold>1)--button_threshold;
   if(pressed&J_A)button_units^=1;
   if(pressed&J_START){if(ui_confirm("CLEAR COUNTS?"))clear_counts();screen();key=0;old=bb_frame();}
  }
  if(button_page==3 && (pressed&J_A))button_diagonal_view=(button_diagonal_view+1u)%3u;
  if((key&0xf0u)==0xf0u){if(chord<60)chord+=delta;if(chord>=60){if(bb_exit())return;screen();key=0;chord=0;old=bb_frame();}}else chord=0;
  if(key!=previous || pressed || (button_page>=2 && !(now&15u)))show(key);previous=key;
 }
}
