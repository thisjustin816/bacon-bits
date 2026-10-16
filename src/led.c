#pragma bank 3
#include "bb.h"
uint8_t led_red=255,led_green=128,led_blue=0,led_mode,led_active,led_sent[3];
static uint8_t led_period=60,seen,last_page=255;
static const char *const presets[]={"","Primary colors","White levels","Color cycle","Pulse"};
static const char *const notes[]={"Keep settings","Red green blue","16 white levels","RGB transitions","On off / 1 second"};
/* insideGadgets MBC5 RGB: CS=bit 3, data=bit 2, clock=bit 1 at $6000. */
void led_send(uint8_t red,uint8_t green,uint8_t blue) BANKED {
 led_sent[0]=red;led_sent[1]=green;led_sent[2]=blue;
#ifndef BB_MBC3
 volatile uint8_t *port=(volatile uint8_t *)0x6000u;uint8_t c,i,v;
 *port=8;*port=0;
 for(c=0;c<3;++c){v=c==0?red:c==1?green:blue;for(i=0;i<8;++i){*port=(v&128u)?6:2;*port=0;v<<=1;}}
 *port=8;
#else
 red;green;blue;
#endif
}
static void output(uint8_t phase){uint8_t level;
 if(led_mode==1){led_red=phase%3==0?255:0;led_green=phase%3==1?255:0;led_blue=phase%3==2?255:0;}
 else if(led_mode==2){level=(phase&15u)*17u;led_red=led_green=led_blue=level;}
 else if(led_mode==3){level=(phase&15u)*17u;switch((phase>>4)%3){case 0:led_red=255-level;led_green=level;led_blue=0;break;case 1:led_red=0;led_green=255-level;led_blue=level;break;default:led_red=level;led_green=0;led_blue=255-level;}}
 led_send(led_mode==4 && (phase&1u)?0:led_red,led_mode==4 && (phase&1u)?0:led_green,led_mode==4 && (phase&1u)?0:led_blue);
}
static void view(uint8_t detail,uint8_t row){
 uint8_t red=led_active?led_sent[0]:led_red,green=led_active?led_sent[1]:led_green,blue=led_active?led_sent[2]:led_blue;
 if(last_page!=detail){ui_screen("Cart LED",detail?"Set":"");last_page=detail;}
 if(detail){ui_value(0,"Red",led_red,row==0);ui_value(1,"Green",led_green,row==1);ui_value(2,"Blue",led_blue,row==2);ui_value(3,"Every fr",led_period,row==3);}
 else {ui_hardware(0,0);ui_text(11,6,"Red");fill_bkg_rect(11,7,7,1,0);ui_number(11,7,red);ui_text(11,9,"Green");fill_bkg_rect(11,10,7,1,0);ui_number(11,10,green);ui_text(11,12,"Blue");fill_bkg_rect(11,13,7,1,0);ui_number(11,13,blue);}
 if(!detail && _cpu==CGB_TYPE){palette_color_t colors[4]={RGB(31,30,27),0,RGB(23,9,7),RGB(8,5,4)};
  colors[1]=led_active?RGB(red>>3,green>>3,blue>>3):RGB(12,11,10);vsync();set_bkg_palette(6,1,colors);VBK_REG=1;fill_bkg_rect(1,6,8,8,6);VBK_REG=0;}
 ui_status(led_active?"Command sent":"Output off");
}
void led_run(void) BANKED {
 last_page=255;
 uint8_t key,old=0,n,row=0,detail=0,phase=0,preset;uint16_t since=0;
#ifdef BB_MBC3
 ui_screen("Cart LED","");ui_text(2,7,"MBC5 RGB cart");ui_text(2,10,"Required");while(joypad())vsync();while(!(joypad()&J_B))vsync();while(joypad())vsync();return;
#endif
 preset=ui_presets("LED presets",presets,notes,seen);if(preset==255)return;seen=1;if(preset){led_mode=preset;led_period=60;}
 led_active=0;view(detail,row);
 for(;;){vsync();key=joypad();n=key&~old;old=key;
  if(n&J_B){if(led_active)led_send(0,0,0);led_active=0;return;}
  if(n&J_SELECT){detail^=1;row=0;view(detail,row);}
  if(detail){if(n&J_UP)row=(row+3u)&3u;if(n&J_DOWN)row=(row+1u)&3u;
   if(n&(J_LEFT|J_RIGHT)){int8_t step=n&J_RIGHT?1:-1;uint8_t *value=row==0?&led_red:row==1?&led_green:row==2?&led_blue:&led_period;
    if((step>0 && *value<255)||(step<0 && *value>(row==3?1:0)))*value+=step;
    if(row<3)led_mode=0;if(led_active)output(phase);
   }
  }
  if(n&J_A){led_active^=1;phase=0;since=bb_frame();if(led_active)output(phase);else led_send(0,0,0);}
  if(led_active && led_mode && (uint16_t)(bb_frame()-since)>=led_period){since=bb_frame();output(++phase);view(detail,row);}
  else if(n)view(detail,row);
 }
}
