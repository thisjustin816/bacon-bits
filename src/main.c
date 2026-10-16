#include "bb.h"
#include "art.h"
#include "brand.h"
#include <string.h>

uint8_t selected_test,bb_keys,bb_raw_rumble;
uint16_t ui_revision;
static uint8_t saved_tiles[360], saved_attrs[360];
static palette_color_t saved_palette[4];
static const palette_color_t breakfast[16] = {
 RGB(31,30,27),RGB(31,24,6),RGB(23,9,7),RGB(8,5,4),
 RGB(19,26,30),RGB(31,30,27),RGB(23,9,7),RGB(8,5,4),
 RGB(31,30,27),RGB(28,27,23),RGB(23,9,7),RGB(8,5,4),
 RGB(31,24,6),RGB(31,30,27),RGB(23,9,7),RGB(8,5,4)
};
static const char * const labels[] = {"Platform","Link cable","Rumble","Audio range","Buttons","Display","SRAM test","Burn in","Cart LED","Infrared"};
void ui_cell(uint8_t x,uint8_t y,uint8_t tile) {set_bkg_tile_xy(x,y,tile);}
void ui_text(uint8_t x,uint8_t y,const char *s) {while(*s) ui_cell(x++,y,(uint8_t)*s++-32u);}
void ui_clear(void) {
 uint8_t x,y;
 /* Keep the brand visible while outgoing font references are removed. */
 if(_cpu==CGB_TYPE){VBK_REG=1;fill_bkg_rect(0,0,20,4,1);VBK_REG=0;}
 for(y=0;y<4;++y)for(x=0;x<4;++x)ui_cell(x,y,UI_BRAND+y*4+x);
 fill_bkg_rect(4,0,16,4,0);
 for(y=4;y!=18;++y) fill_bkg_rect(0,y,20,1,0);
 if(_cpu==CGB_TYPE) {VBK_REG=1;fill_bkg_rect(0,4,20,14,0);VBK_REG=0;}
}
void ui_box(uint8_t top,uint8_t bottom) {
 uint8_t y;
 fill_bkg_rect(1,top,18,1,(UI_CHROME+0));fill_bkg_rect(1,bottom,18,1,(UI_CHROME+0));
 ui_cell(0,top,(UI_CHROME+2));ui_cell(19,top,(UI_CHROME+3));ui_cell(0,bottom,(UI_CHROME+4));ui_cell(19,bottom,(UI_CHROME+5));
 for(y=top+1;y<bottom;++y) {ui_cell(0,y,(UI_CHROME+1));ui_cell(19,y,(UI_CHROME+1));}
}
void ui_header(void) {
 uint8_t x,y;
 for(y=0;y<4;++y)for(x=0;x<4;++x)ui_cell(x,y,UI_BRAND+y*4+x);
 ui_text(5,1,"Bacon Bits");ui_text(5,2,"Test Cartridge");
 for(y=4;y<18;++y)if(y==4 || y>=15)fill_bkg_rect(0,y,20,1,(UI_CHROME+10));
 if(_cpu==CGB_TYPE){VBK_REG=1;fill_bkg_rect(0,0,20,4,1);fill_bkg_rect(0,15,20,3,2);VBK_REG=0;}
}
void ui_init(void) {
 ++ui_revision;
 uint8_t i;
 HIDE_SPRITES;HIDE_WIN;SHOW_BKG;
 if(!bb_raw_rumble)for(i=0;i!=40;++i)move_sprite(i,0,0);
 SCX_REG=SCY_REG=0;VBK_REG=0;LCDC_REG|=0x10u;
 vsync();
 if(_cpu==CGB_TYPE) set_bkg_palette(0,4,breakfast);
 BGP_REG=0xe4;
 set_bkg_data(UI_BRAND,16,bb_brand);ui_clear();
 set_bkg_data(0,UI_FONT_COUNT,bb_font);set_bkg_data(UI_CHROME,11,bb_chrome);set_bkg_data(UI_PASS,3,bb_probes);
 ui_header();ui_scene_reset();DISPLAY_ON;
}
/* Menu-only punctuation slots hold half-cell shifts for odd-length labels.
   ui_init reloads the complete font before entering any test or dialog. */
static void menu_label(uint8_t item,const char *label,uint8_t *borrowed) {
 static const uint8_t slots[]={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,26,27,28,29,30,31,32,59,60};
 uint8_t count=strlen(label),x=(item&1u?10u:0u)+(10u-count)/2u,y=(item&2u)?15:9,i,r,tile[16],left,right;
 if(!(count&1u)){ui_text(x,y,label);return;}
 for(i=0;i<=count;++i){
  for(r=0;r<16;++r){left=i?bb_font[((uint8_t)label[i-1]-32u)*16u+r]:0;right=i<count?bb_font[((uint8_t)label[i]-32u)*16u+r]:0;tile[r]=(left<<4)|(right>>4);}
  set_bkg_data(slots[*borrowed],1,tile);ui_cell(x+i,y,slots[*borrowed]);++*borrowed;
 }
}
static void browser(uint8_t fresh) {
 uint8_t i,at,borrowed=0,group=selected_test/4u;
 if(fresh)ui_init();
 ui_scene(group==2?6:group==1?5:
#ifdef BB_MBC3
 7,
#else
 0,
#endif
(uint8_t)(bb_frame()/12u)&3u);
 for(i=0;i<4;++i){
  at=group*4u+i;if(at>=10)continue;if(fresh)menu_label(i,at==1?"Link":at==3?"Audio":at==6?"Save RAM":at==7?"Burn in":at==8?"Cart LED":at==9?"IR":
#ifdef BB_MBC3
 at==2?"Clock":
#endif
 labels[at],&borrowed);
 }
 ui_focus(selected_test&3u,fresh);
 if(fresh){fill_bkg_rect(0,17,20,1,(UI_CHROME+10));ui_text(7,17,group==2?"3 of 3":group==1?"2 of 3":"1 of 3");}
}

/* Every test shares the font and frame tiles, so the modal only borrows map cells. */
uint8_t bb_exit(void) NONBANKED {
 uint8_t keys,previous=0,choice=0,y,x,sprites;
 bb_keys=joypad();
 if((bb_keys&(J_A|J_B|J_START|J_SELECT))!=(J_A|J_B|J_START|J_SELECT)) return 0;
 sprites=LCDC_REG&2u;HIDE_SPRITES;
 VBK_REG=0;get_bkg_tiles(0,0,20,18,saved_tiles);
 if(_cpu==CGB_TYPE) {
  VBK_REG=1;get_bkg_tiles(0,0,20,18,saved_attrs);VBK_REG=0;
  vsync();for(x=0;x<8;++x) { BCPS_REG=56u+x; ((uint8_t *)saved_palette)[x]=BCPD_REG; }
  set_bkg_palette(7,1,breakfast);
 }
 fill_bkg_rect(2,5,16,8,0);
 for(x=3;x<17;++x) {ui_cell(x,5,(UI_CHROME+0));ui_cell(x,12,(UI_CHROME+0));}
 ui_cell(2,5,(UI_CHROME+2));ui_cell(17,5,(UI_CHROME+3));ui_cell(2,12,(UI_CHROME+4));ui_cell(17,12,(UI_CHROME+5));
 for(y=6;y<12;++y) {ui_cell(2,y,(UI_CHROME+1));ui_cell(17,y,(UI_CHROME+1));}
 {const char *s="Continue";x=5;while(*s)ui_cell(x++,7,(uint8_t)*s++-32u);}
 {const char *s="Test menu";x=5;while(*s)ui_cell(x++,10,(uint8_t)*s++-32u);}
 if(_cpu==CGB_TYPE){VBK_REG=1;fill_bkg_rect(2,5,16,8,7);VBK_REG=0;}
 while(joypad())vsync();
 for(;;) {
  ui_cell(3,7,choice?0:UI_CURSOR);ui_cell(3,10,choice?UI_CURSOR:0);
  vsync();keys=joypad();
  if((keys&~previous)&(J_UP|J_DOWN))choice^=1;
  if((keys&~previous)&J_B){choice=0;break;}
  if((keys&~previous)&J_A)break;
  previous=keys;
 }
 while(joypad())vsync();
 set_bkg_tiles(0,0,20,18,saved_tiles);
 if(_cpu==CGB_TYPE){VBK_REG=1;set_bkg_tiles(0,0,20,18,saved_attrs);VBK_REG=0;vsync();set_bkg_palette(7,1,saved_palette);}
 if(sprites)SHOW_SPRITES;
 bb_keys=0;return choice;
}

/* The assembly diagnostic polls its timer with interrupts disabled. */
uint8_t rumble_gate(void) NONBANKED {
 uint8_t leave;
 set_interrupts(VBL_IFLAG);enable_interrupts();
 leave=bb_exit();
 disable_interrupts();IE_REG=0;
 return leave;
}
void rumble_draw_gate(void) NONBANKED {
 set_interrupts(VBL_IFLAG);enable_interrupts();rumble_view();disable_interrupts();IE_REG=0;
}
static void rumble_run(void) {
 rumble_ui_reset();bb_raw_rumble=1;
 SWITCH_ROM(3);
 ((void (*)(void))0x4000u)();
 bb_raw_rumble=0;TAC_REG=0;SC_REG=0;
 *(volatile uint8_t *)0x4000u=0;
 set_interrupts(VBL_IFLAG);enable_interrupts();
 SWITCH_ROM(1);
}
void main(void) {
 uint8_t keys,previous=0,pressed,phase=255,last_group=0;
 NR52_REG=0;
 if(_cpu==CGB_TYPE){if(LCDC_REG&0x80u)vsync();set_bkg_palette(0,4,breakfast);}
 DISPLAY_ON;
 browser(1);
#ifdef BB_AUTORUN
 selected_test=BB_AUTORUN;
 if(selected_test==0)platform_run();
 else if(selected_test==1)link_run();
 else if(selected_test==2) {
#ifdef BB_MBC3
 rtc_run();
#else
 rumble_run();
#endif
 }
 else if(selected_test==3)audio_run();
   else if(selected_test==4)buttons_run();
   else if(selected_test==5)display_run();
   else if(selected_test==6)sram_run();
   else if(selected_test==7)burn_run();
   else if(selected_test==8)led_run();else ir_run();
 browser(1);
#endif
 for(;;) {
  vsync();keys=joypad();pressed=keys&~previous;previous=keys;
  if(pressed&(J_UP|J_DOWN)){selected_test=(selected_test+((pressed&J_DOWN)?2u:8u))%10u;browser((selected_test/4u)!=last_group);}
  if(pressed&(J_LEFT|J_RIGHT)) {
   selected_test=(selected_test+((pressed&J_RIGHT)?1u:9u))%10u;
   browser((selected_test/4u)!=last_group);
  }
  last_group=selected_test/4u;
  if(phase!=((uint8_t)(bb_frame()/12u)&3u)){phase=(uint8_t)(bb_frame()/12u)&3u;browser(0);}
  if(pressed&J_A) {
   while(joypad())vsync();NR52_REG=0;
   if(selected_test==0)platform_run();
   else if(selected_test==1)link_run();
   else if(selected_test==2) {
#ifdef BB_MBC3
 rtc_run();
#else
 rumble_run();
#endif
 }
   else if(selected_test==3)audio_run();
   else if(selected_test==4)buttons_run();
   else if(selected_test==5)display_run();
   else if(selected_test==6)sram_run();
   else if(selected_test==7)burn_run();
   else if(selected_test==8)led_run();else ir_run();
   NR52_REG=0;browser(1);previous=0;
  }
 }
}
