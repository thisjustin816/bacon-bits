#pragma bank 4
#include "bb.h"
#include "flicker_data.h"

uint8_t flicker_pattern,flicker_a=1,flicker_b=1,flicker_lead,flicker_cycle;
uint8_t flicker_speed=1,flicker_axis,flicker_cell=1,flicker_pair;
uint8_t flicker_level_a=31,flicker_level_b,flicker_compare=1;
uint8_t flicker_running,flicker_paused,flicker_ready,flicker_phase,flicker_elapsed;
uint8_t flicker_x,flicker_y;
uint16_t flicker_ticks;
static uint8_t seen;
static const char *const presets[]={"","Layers","Shadows","Fine detail","Color mix"};
static const char *const notes[]={"Keep settings","Alternating layers","Half-rate shadow","Pixel phase swap","Two color phases"};
static const char *const names[]={"Layers","Shadows","Detail","Color"};
static const char *const axes[]={"Horiz","Vert","Diag"};
static const char *const pairs[]={"Gray","Gold/sky","Red/blue"};

static uint8_t sample(uint8_t x,uint8_t y,uint8_t phase) {
 if(flicker_pattern==3)return phase?3:0;
 if(flicker_pattern==2)return (((x/flicker_cell)^(y/flicker_cell)^phase)&1u)?3:0;
 if(flicker_pattern==1)phase=0;
 if(!phase){if(y%8u==4 && x%16u<7)return 1;if(y%8u==7 && x%16u==2)return 2;}
 else if(x%16u<9 && ((uint8_t)(x-y)&15u)<2)return 2;
 return 0;
}
static void palettes(void) {
 palette_color_t p[4],sprite[4]={RGB_WHITE,RGB(21,21,21),RGB(10,10,10),RGB_BLACK};
 uint8_t a=flicker_level_a,b=flicker_level_b;
 if(_cpu!=CGB_TYPE){
  BGP_REG=(3u-a)|((3u-(a*2u+b)/3u)<<2)|((3u-(a+b*2u)/3u)<<4)|((3u-b)<<6);
  OBP0_REG=0xe4;return;
 }
 p[0]=RGB(a,a,a);p[3]=RGB(b,b,b);
 if(flicker_pair==1){p[0]=RGB(a,a*24u/31u,a*6u/31u);p[3]=RGB(b*19u/31u,b*26u/31u,b*30u/31u);}
 if(flicker_pair==2){p[0]=RGB(a,a*8u/31u,a*6u/31u);p[3]=RGB(b*6u/31u,b*15u/31u,b);}
 p[1]=RGB((a*2u+b)/3u,(a*2u+b)/3u,(a*2u+b)/3u);
 p[2]=RGB((a+b*2u)/3u,(a+b*2u)/3u,(a+b*2u)/3u);
 vsync();set_bkg_palette(0,1,p);set_sprite_palette(0,1,sprite);
}
static void actor(void) {
 uint8_t x=flicker_x+8u,y=flicker_y+16u;
 move_sprite(0,x,y);move_sprite(1,x+8u,y);
 move_sprite(2,x,y+8u);move_sprite(3,x+8u,y+8u);
 if(flicker_pattern==1 && !flicker_phase){move_sprite(4,x,y+16u);move_sprite(5,x+8u,y+16u);}
 else{move_sprite(4,0,0);move_sprite(5,0,0);}
 if(flicker_pattern==2)HIDE_SPRITES;else SHOW_SPRITES;
 /* The default VBlank copy precedes this frame's phase update. */
 refresh_OAM();
}
static void prepare(void) {
 uint8_t n=2,t,phase,x,y,k,lo,hi,c,tile[16],row[20],count;
 /* The full view replaces the settings map and the cover map. */
 flicker_ready=0;++ui_revision;HIDE_SPRITES;HIDE_WIN;SCX_REG=SCY_REG=0;VBK_REG=0;bb_cover_dirty=1;
 if(flicker_pattern==2){n=flicker_cell;if(!(n&1u))n>>=1;if(!(n&1u))n>>=1;}
 if(flicker_pattern==3)n=1;
 count=n*n;
 /* Stream each tile, then each map row; no second framebuffer in WRAM. */
 for(phase=0;phase<2;++phase)for(t=0;t<count;++t){
  for(y=0;y<8;++y){lo=hi=0;for(x=0;x<8;++x){c=sample((t%n)*8u+x,(t/n)*8u+y,phase);lo=(lo<<1)|(c&1u);hi=(hi<<1)|(c>>1);}tile[y*2u]=lo;tile[y*2u+1u]=hi;}
  set_bkg_data(112u+phase*count+t,1,tile);
 }
 set_bkg_data(210,sizeof(flicker_reference_tiles)/16,flicker_reference_tiles);
 set_sprite_data(225,6,flicker_actor);
 for(k=0;k<6;++k){set_sprite_tile(k,225u+k);set_sprite_prop(k,0);move_sprite(k,0,0);}SPRITES_8x8;
 for(k=0;k<2;++k){phase=k^1u;for(y=0;y<18;++y){
  for(x=0;x<20;++x){
   row[x]=112u+phase*count+(y%n)*n+x%n;
   if(flicker_pattern==3)row[x]=112u+(phase^(x>=10u));
   if(flicker_compare && y>=15)row[x]=flicker_reference_map[(y-15u)*20u+x];
  }
  set_tiles(0,y,20,1,(uint8_t *)(phase?0x9c00:0x9800),row);
  if(_cpu==CGB_TYPE){for(x=0;x<20;++x)row[x]=0;VBK_REG=1;set_tiles(0,y,20,1,(uint8_t *)(phase?0x9c00:0x9800),row);VBK_REG=0;}
 }
  if(!k){palettes();vsync();LCDC_REG|=8u;}
 }
 flicker_phase=flicker_lead;flicker_elapsed=0;flicker_ticks=0;
 flicker_x=64;flicker_y=52;flicker_paused=0;
 vsync();LCDC_REG=(LCDC_REG&~8u)|(flicker_phase?8u:0);actor();flicker_ready=1;
}
static void advance(void) {
 uint8_t cycle=0,limit=flicker_compare?96:120;
 ++flicker_ticks;
 if(++flicker_elapsed>=(flicker_phase?flicker_b:flicker_a)){
  flicker_elapsed=0;flicker_phase^=1;cycle=!flicker_phase;
 }
 if(!flicker_cycle || cycle){
  if(flicker_axis!=1){flicker_x+=flicker_speed;if(flicker_x>=144)flicker_x-=144;}
  if(flicker_axis!=0){flicker_y+=flicker_speed;if(flicker_y>=limit)flicker_y-=limit;}
 }
 LCDC_REG=(LCDC_REG&~8u)|(flicker_phase?8u:0);actor();
}
static void settings(uint8_t page,uint8_t sel) {
 char v[20],*end;uint16_t hz;
 uint8_t fresh=ui_page("Flicker",page==0?"1/4":page==1?"2/4":page==2?"3/4":"4/4",0xa0u|page);
 if(!page){if(fresh){
  set_bkg_data(112,sizeof(flicker_preview_tiles)/16,flicker_preview_tiles);
  set_bkg_tiles(2,6,16,6,flicker_preview_map);
  if(_cpu==CGB_TYPE){palette_color_t p[4]={RGB_WHITE,RGB(21,21,21),RGB(10,10,10),RGB_BLACK};vsync();set_bkg_palette(4,1,p);VBK_REG=1;fill_bkg_rect(2,6,16,6,4);VBK_REG=0;}
  ui_text(2,13,"Flicker");ui_text(12,13,"Dither");
 }}else if(page==1){
  end=ui_decimal(v,flicker_a);*end++=' ';*end++='f';*end++='r';*end=0;ui_field(0,"Phase A",v,sel==0);
  end=ui_decimal(v,flicker_b);*end++=' ';*end++='f';*end++='r';*end=0;ui_field(1,"Phase B",v,sel==1);
  ui_field(2,"Lead",flicker_lead?"B":"A",sel==2);ui_field(3,"Move on",flicker_cycle?"Cycle":"Frame",sel==3);
 }else if(page==2){
  ui_field(0,"Pattern",names[flicker_pattern],sel==0);
  ui_decimal(v,flicker_speed);ui_field(1,"Speed",v,sel==1);ui_text(13,9,flicker_cycle?"px/cyc":"px/fr");
  ui_field(2,"Axis",axes[flicker_axis],sel==2);end=ui_decimal(v,flicker_cell);*end++=' ';*end++='p';*end++='x';*end=0;ui_field(3,"Cell",v,sel==3);
 }else{
  ui_field(0,"Pair",_cpu==CGB_TYPE?pairs[flicker_pair]:"Gray",sel==0);
  ui_value(1,"Level A",flicker_level_a,sel==1);ui_value(2,"Level B",flicker_level_b,sel==2);
  ui_field(3,"Compare",flicker_compare?"Split":"Off",sel==3);
 }
 if(page==1){
  end=ui_decimal(v+5,100u*flicker_a/(flicker_a+flicker_b));v[0]='D';v[1]='u';v[2]='t';v[3]='y';v[4]=' ';*end++='%';*end=0;ui_line(16,v);
  hz=5973u/(flicker_a+flicker_b);v[0]='C';v[1]='y';v[2]='c';v[3]='l';v[4]='e';v[5]=' ';end=ui_decimal(v+6,hz/100u);*end++='.';*end++='0'+hz%100u/10u;*end++='0'+hz%10u;*end++=' ';*end++='H';*end++='z';*end=0;ui_line(17,v);
 }else{
  ui_status("Stopped");
  if(!page){end=ui_decimal(v,flicker_a);*end++='/';end=ui_decimal(end,flicker_b);*end++=' ';*end++='f';*end++='r';*end++=' ';*end++=' ';end=ui_decimal(end,100u*flicker_a/(flicker_a+flicker_b));*end++='%';*end++=' ';*end++='d';*end++='u';*end++='t';*end++='y';*end=0;ui_line(17,v);}
  if(page==2)ui_line(17,flicker_cycle?"Speed px/cycle":"Speed px/frame");
 }
}
static void stop(void) {
 vsync();HIDE_SPRITES;LCDC_REG&=~8u;SCX_REG=SCY_REG=0;VBK_REG=0;
 flicker_running=flicker_ready=flicker_paused=0;
}
static uint8_t adjust(uint8_t v,int8_t step,uint8_t low,uint8_t high) {
 if(step>0 && v<high)++v;if(step<0 && v>low)--v;return v;
}
void flicker_run(void) BANKED {
 uint8_t key,raw,candidate=0,old=0,press,page=0,sel=0,preset;int8_t step;
 preset=ui_presets("Flicker presets",presets,notes,seen);if(preset==255)return;seen=1;
 if(preset){
  flicker_pattern=preset-1;flicker_a=flicker_b=flicker_cell=1;flicker_lead=flicker_cycle=flicker_axis=0;
  flicker_speed=preset==1?1:0;flicker_pair=preset==4?1:0;flicker_compare=1;
  flicker_level_a=_cpu==CGB_TYPE?31:3;flicker_level_b=preset==4?flicker_level_a:0;
  if(_cpu!=CGB_TYPE && preset==4)flicker_level_b=0;
 }
 if(_cpu!=CGB_TYPE){flicker_level_a&=3;flicker_level_b&=3;}
 flicker_running=flicker_ready=flicker_paused=0;settings(page,sel);
 for(;;){
  vsync();raw=joypad();
  /* Let a chord settle without stalling the LCD phase clock. */
  key=raw==candidate?raw:old;candidate=raw;press=key&~old;old=key;
  if((key&(J_A|J_B|J_START|J_SELECT))==(J_A|J_B|J_START|J_SELECT)){
   if(flicker_running){stop();settings(page,sel);}if(bb_exit())return;old=candidate=0;continue;
  }
  if(flicker_running){
   if(press&J_B){stop();settings(page,sel);continue;}
   if(press&J_A)flicker_paused^=1;
   if(!flicker_paused || (press&J_RIGHT))advance();
   continue;
  }
  if(press&J_B)return;
  if(press&J_SELECT){page=(page+1u)&3u;sel=0;}
  if(page && (press&J_UP))sel=(sel+3u)&3u;
  if(page && (press&J_DOWN))sel=(sel+1u)&3u;
  if(page && (press&(J_LEFT|J_RIGHT))){step=(press&J_RIGHT)?1:-1;
   if(page==1){if(sel==0)flicker_a=adjust(flicker_a,step,1,60);else if(sel==1)flicker_b=adjust(flicker_b,step,1,60);else if(sel==2)flicker_lead^=1;else flicker_cycle^=1;}
   if(page==2){if(sel==0)flicker_pattern=(flicker_pattern+4u+step)%4u;else if(sel==1)flicker_speed=adjust(flicker_speed,step,0,8);else if(sel==2)flicker_axis=(flicker_axis+3u+step)%3u;else flicker_cell=adjust(flicker_cell,step,1,8);}
   if(page==3){if(sel==0 && _cpu==CGB_TYPE)flicker_pair=(flicker_pair+3u+step)%3u;else if(sel==1)flicker_level_a=adjust(flicker_level_a,step,0,_cpu==CGB_TYPE?31:3);else if(sel==2)flicker_level_b=adjust(flicker_level_b,step,0,_cpu==CGB_TYPE?31:3);else if(sel==3)flicker_compare^=1;}
  }
  if(press&J_A){flicker_running=1;prepare();}else if(press)settings(page,sel);
 }
}
