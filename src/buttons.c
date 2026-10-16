#pragma bank 7
#include "bb.h"
#include <string.h>
#include "button_data.h"
extern const unsigned char bb_font[];
uint32_t button_presses[8],button_short[8],button_gaps[8];
uint16_t button_held[8],button_longest[8],button_released[8];
uint32_t button_diagonal[4],button_opposites;
uint16_t button_diagonal_hold[4],button_diagonal_peak[4];
uint8_t button_diagonal_view;
static const uint8_t diagonal_bits[]={5,6,9,10};
static const char *const diagonal_names[]={"Up right","Up left","Dn right","Dn left"};
uint8_t button_page,button_pick,button_threshold=1,button_units,button_peak;
static const char *const names[8]={"Right","Left","Up","Down","A","B","Select","Start"};
static uint8_t drawn_directions=255;
static uint8_t updates[32][3];
static void live_dpad(uint8_t held) {
 const uint8_t *map=button_maps[held&15u],*old;
 uint8_t x,y,count=0,i;uint16_t n=0;
 if(drawn_directions==255){set_bkg_data(UI_ART,37,button_tiles);old=0;}
 else old=button_maps[drawn_directions];
 for(y=6;y<14;++y)for(x=1;x<19;++x){
  if(!old)ui_cell(x,y,map[n]);
  else if(old[n]!=map[n]){updates[count][0]=x;updates[count][1]=y;updates[count++][2]=map[n];}
  ++n;
 }
 if(count){vsync();for(i=0;i<count;++i)set_bkg_tile_xy(updates[i][0],updates[i][1],updates[i][2]);}
 drawn_directions=held&15u;
}
static uint8_t initialized;
static const char *const presets[]={"","Button check","Short events","Hold timing","Diagonals"};
static const char *const notes[]={"Keep counters","Live button states","1 frame threshold","Hold milliseconds","D-pad corners"};
static void clear_counts(void) {
 uint8_t i;button_opposites=0;memset(button_diagonal,0,sizeof(button_diagonal));memset(button_diagonal_hold,0,sizeof(button_diagonal_hold));memset(button_diagonal_peak,0,sizeof(button_diagonal_peak));memset(button_presses,0,sizeof(button_presses));memset(button_short,0,sizeof(button_short));memset(button_gaps,0,sizeof(button_gaps));
 memset(button_longest,0,sizeof(button_longest));memset(button_held,0,sizeof(button_held));for(i=0;i<8;++i)button_released[i]=65535;button_peak=0;
}
static void screen(void) {drawn_directions=255;ui_screen(button_page==3?"Diagonals":"Buttons",button_page==0?"1/4":button_page==1?"2/4":button_page==2?"3/4":"4/4");}
static void show(uint8_t held) {
 uint8_t i,n=0;uint32_t corner_value;char str[12],*end;
 if(button_page==0){
  static const uint8_t xs[]={15,13,11,11},ys[]={7,9,11,13};
  static const char *const labels[]={"A","B","Select","Start"};
  live_dpad(held);
  for(i=0;i<8;++i)if(held&(1u<<i))++n;
  for(i=0;i<4;++i){ui_cell(xs[i]-1,ys[i],(held&(16u<<i))?UI_ACTIVE:0);ui_text(xs[i],ys[i],labels[i]);}
  for(i=0;i<4;++i)ui_cell((i&1u)?2:8,(i&2u)?13:7,(held&15u)==diagonal_bits[i]?UI_PASS:UI_EMPTY);
  ui_status("Held");ui_number(6,16,n);ui_text(9,16,"Peak");ui_number(15,16,button_peak);
 }else if(button_page==1){for(i=0;i<4;++i)ui_value(i,names[(button_pick+i)&7u],button_presses[(button_pick+i)&7u],i==0);ui_status("Press counts");}
 else if(button_page==2){ui_field(0,"Button",names[button_pick],1);ui_value(1,button_units?"Hold ms":"Hold fr",button_units?((uint32_t)button_longest[button_pick]*16742UL)/1000UL:button_longest[button_pick],0);
  ui_value(2,"Short on",button_short[button_pick],0);
  ui_value(3,"Short off",button_gaps[button_pick],0);
  end=ui_decimal(str,button_threshold);*end++=' ';*end++='F';*end++='R';*end=0;ui_status("Short at most");ui_text(14,16,str);
 }else {
 static const char *const corners[]={"NE","NW","SE","SW"};
 ui_scene(4,0);
 for(i=0;i<4;++i){
  ui_cell((i&1u)?2:8,(i&2u)?13:7,(held&15u)==diagonal_bits[i]?UI_ACTIVE:UI_PASS);
  ui_text(11,6+2*i,corners[i]);fill_bkg_rect(14,6+2*i,5,1,0);
  corner_value=button_diagonal_view?(button_diagonal_view==2?((uint32_t)button_diagonal_peak[i]*16742UL)/1000UL:button_diagonal_peak[i]):button_diagonal[i];
  if(corner_value>99999UL)ui_text(14,6+2*i,"99K+");else ui_number(14,6+2*i,corner_value);
 }
 fill_bkg_rect(0,15,20,1,0);ui_text(1,15,"Opposites");ui_number(12,15,button_opposites);ui_status(button_diagonal_view==0?"Entry counts":button_diagonal_view==1?"Longest fr":"Longest ms");}

}
void buttons_run(void) BANKED {
 uint8_t key,previous=0,pressed,i,n,preset;uint16_t chord=0;uint16_t old,now,delta;
 preset=ui_presets("Button presets",presets,notes,initialized);if(preset==255)return;
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
   if(pressed&J_START){if(ui_confirm("Clear counts?"))clear_counts();screen();key=0;old=bb_frame();}
  }
  if(button_page==3 && (pressed&J_A))button_diagonal_view=(button_diagonal_view+1u)%3u;
  if((key&0xf0u)==0xf0u){if(chord<60)chord+=delta;if(chord>=60){if(bb_exit())return;screen();key=0;chord=0;old=bb_frame();}}else chord=0;
  if(key!=previous || pressed || (button_page>=2 && !(now&15u)))show(key);previous=key;
 }
}
