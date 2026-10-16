#pragma bank 4
#include "bb.h"
#include <string.h>
uint8_t display_pattern,display_color,display_width,display_axis,display_speed=1,display_interval=30,display_invert,display_running,display_ready;
static uint8_t row_tiles[32],row_attrs[32],patterns[256];
static uint8_t seen;
static const char *const presets[]={"","Pixel check","Color range","Motion check","Flicker check"};
static const char *const notes[]={"Keep settings","1 pixel checker","32 gray levels","2 px per frame","30 frame interval"};
static const char *const names[]={"Solid","Grid","Checker","Stripes","Ramps","Scroll","Flicker"};
static const char *const colors[]={"White","Black","Gray","Red","Green","Blue"};
static void palettes(uint8_t flip) {
 palette_color_t p[4];uint8_t i,j,k;uint16_t c;
 if(_cpu!=CGB_TYPE){BGP_REG=(flip^display_invert)?0x1b:0xe4;return;}
 if(display_pattern==4){for(i=0;i<8;++i){for(j=0;j<4;++j){k=i*4u+j;if(display_invert)k=31u-k;p[j]=display_color==3?RGB(k,0,0):display_color==4?RGB(0,k,0):display_color==5?RGB(0,0,k):RGB(k,k,k);}vsync();set_bkg_palette(i,1,p);}return;}
 switch(display_color){case 1:c=RGB_BLACK;break;case 2:c=RGB(16,16,16);break;case 3:c=RGB_RED;break;case 4:c=RGB_GREEN;break;case 5:c=RGB_BLUE;break;default:c=RGB_WHITE;}
 p[0]=(flip^display_invert)?RGB_BLACK:c;p[1]=p[0];p[2]=p[3]=(flip^display_invert)?c:RGB_BLACK;
 vsync();set_bkg_palette(0,1,p);
}
static void prepare(void) {
 uint8_t tile,x,y,px,py,on,kind,width=1u<<display_width;
 display_ready=0;HIDE_SPRITES;HIDE_WIN;SCX_REG=SCY_REG=0;VBK_REG=0;
 for(tile=0;tile<16;++tile){for(y=0;y<8;++y){uint8_t bits=0;
  for(x=0;x<8;++x){px=(tile&3u)*8u+x;py=(tile>>2)*8u+y;kind=display_pattern;
   if(kind==0 || kind==6)on=0;
   else if(kind==1)on=(px%width==0 || py%width==0);
   else if(kind==2)on=((px/width)^(py/width))&1u;
   else if(kind==3)on=((display_axis?py:px)/width)&1u;
   else if(kind==4)on=0;
   else on=((display_axis?py:px)%32u)<width;
   if(on)bits|=0x80u>>x;
  }patterns[tile*16u+y*2u]=patterns[tile*16u+y*2u+1u]=bits;
 }}set_bkg_data(80,16,patterns);
 if(display_pattern==4){for(tile=0;tile<2;++tile){for(y=0;y<8;++y){uint8_t c=tile*2u+y/4u;patterns[y*2u]=(c&1)?255:0;patterns[y*2u+1u]=(c&2)?255:0;}set_bkg_data(96+tile,1,patterns);}}
 for(y=0;y<32;++y){
  for(x=0;x<32;++x){row_tiles[x]=display_pattern==4?96+(y&1u):80+(x&3u)+((y&3u)<<2);row_attrs[x]=display_pattern==4?((y>>1)&7u):0;}
  VBK_REG=0;set_bkg_tiles(0,y,32,1,row_tiles);if(_cpu==CGB_TYPE){VBK_REG=1;set_bkg_tiles(0,y,32,1,row_attrs);VBK_REG=0;}
 }
 palettes(0);display_ready=1;
}
static void settings(uint8_t page,uint8_t selected) {
 char v[8],*end;ui_screen("Display",page?"2/2":"1/2");
 if(!page){ui_field(0,"Pattern",names[display_pattern],selected==0);ui_field(1,"Color",colors[display_color],selected==1);
  end=ui_decimal(v,1u<<display_width);*end++=' ';*end++='P';*end++='X';*end=0;ui_field(2,"Width",v,selected==2);ui_field(3,"Axis",display_axis?"Vert":"Horiz",selected==3);
 }else {ui_value(0,"Px/frame",display_speed,selected==0);ui_value(1,"Every fr",display_interval,selected==1);ui_field(2,"Invert",display_invert?"Yes":"No",selected==2);ui_field(3,"Mode","Full LCD",0);}
}
void display_run(void) BANKED {
 uint8_t key,old=0,press,page=0,sel=0,phase=0;uint16_t since=0;
 {uint8_t preset=ui_presets("Display presets",presets,notes,seen);if(preset==255)return;seen=1;
 if(preset){display_width=display_axis=display_color=display_invert=0;display_speed=2;display_interval=30;display_pattern=preset==1?2:preset==2?4:preset==3?5:6;}}
 display_running=0;settings(page,sel);
 for(;;){vsync();key=joypad();press=key&~old;old=key;
  if(!display_running){if(press&J_B)return;if(press&J_SELECT){page^=1;sel=0;}
   if(press&J_UP)sel=(sel+(page?2u:3u))%(page?3u:4u);if(press&J_DOWN)sel=(sel+1u)%(page?3u:4u);
   if(press&(J_LEFT|J_RIGHT)){int8_t step=(press&J_RIGHT)?1:-1;
    if(!page){if(sel==0)display_pattern=(display_pattern+7u+step)%7u;else if(sel==1)display_color=(display_color+6u+step)%6u;else if(sel==2)display_width=(display_width+5u+step)%5u;else display_axis^=1;}
    else {if(sel==0){if(step<0 && display_speed>1)--display_speed;if(step>0 && display_speed<8)++display_speed;}
     else if(sel==1){if(step<0 && display_interval>1)--display_interval;if(step>0 && display_interval<60)++display_interval;}else if(sel==2)display_invert^=1;}
   }
   if(press&J_A){display_running=1;phase=0;prepare();since=bb_frame();}else if(press)settings(page,sel);
  }else {if(press&J_B){display_running=display_ready=0;SCX_REG=SCY_REG=0;settings(page,sel);continue;}
   if(press&J_SELECT){display_invert^=1;palettes(phase);}
   if(press&(J_LEFT|J_RIGHT)){display_pattern=(display_pattern+((press&J_RIGHT)?1u:6u))%7u;prepare();since=bb_frame();}
   if(display_pattern==5){if(display_axis)SCY_REG+=display_speed;else SCX_REG+=display_speed;}
   if(display_pattern==6 && (uint16_t)(bb_frame()-since)>=display_interval){phase^=1;palettes(phase);since=bb_frame();}
  }
 }
}
