#include "bb.h"
#include "art.h"
#include <string.h>

extern const unsigned char bb_icon_0[],bb_icon_1[],bb_icon_2[],bb_icon_3[],bb_icon_4[],bb_icon_5[],bb_icon_6[],bb_icon_7[];
uint8_t selected_test,bb_keys;
static uint8_t saved_tiles[360], saved_attrs[360], saved_patterns[1280];
static palette_color_t saved_palette[4];
static const palette_color_t breakfast[8] = {
 RGB(31,30,27),RGB(31,24,6),RGB(23,9,7),RGB(8,5,4),
 RGB(19,26,30),RGB(31,27,9),RGB(31,30,27),RGB(8,5,4)
};
static const char * const labels[] = {"PLATFORM","LINK SUSTAIN","RUMBLE","AUDIO RANGE","BUTTONS","DISPLAY","SRAM TEST","BURN IN"};
static const char * const details[] = {"IDENTIFY HARDWARE","CHECK BOTH SIDES","COMPARE PULSES","CHECK TONE RANGE","CHECK EVERY BUTTON","CHECK THE SCREEN","CHECK SAVED DATA","RUN REPEATED CHECKS"};
static const unsigned char * const pictures[]={bb_icon_0,bb_icon_1,bb_icon_2,bb_icon_3,bb_icon_4,bb_icon_5,bb_icon_6,bb_icon_7};

void ui_cell(uint8_t x,uint8_t y,uint8_t tile) {set_bkg_tile_xy(x,y,tile);}
void ui_text(uint8_t x,uint8_t y,const char *s) {while(*s) ui_cell(x++,y,(uint8_t)*s++-32u);}
void ui_clear(void) {
 uint8_t y;
 VBK_REG=0;
 for(y=0;y!=18;++y) fill_bkg_rect(0,y,20,1,0);
 if(_cpu==CGB_TYPE) {VBK_REG=1;fill_bkg_rect(0,0,20,18,0);VBK_REG=0;}
}
void ui_box(uint8_t top,uint8_t bottom) {
 uint8_t y;
 fill_bkg_rect(1,top,18,1,64);fill_bkg_rect(1,bottom,18,1,64);
 ui_cell(0,top,66);ui_cell(19,top,67);ui_cell(0,bottom,68);ui_cell(19,bottom,69);
 for(y=top+1;y<bottom;++y) {ui_cell(0,y,65);ui_cell(19,y,65);}
}
void ui_header(void) {
 uint8_t x,y;
 ui_text(1,1,"BACON BITS");
 fill_bkg_rect(0,2,20,1,74);
 for(y=0;y<3;++y) for(x=0;x<8;++x) ui_cell(12+x,y,128+y*8+x);
 if(_cpu==CGB_TYPE) {VBK_REG=1;fill_bkg_rect(0,0,20,3,1);VBK_REG=0;}
}
void ui_init(void) {
 uint8_t i;
 HIDE_SPRITES;HIDE_WIN;SHOW_BKG;
 for(i=0;i!=40;++i)move_sprite(i,0,0);
 SCX_REG=SCY_REG=0;VBK_REG=0;LCDC_REG|=0x10u;
 vsync();
 if(_cpu==CGB_TYPE) set_bkg_palette(0,2,breakfast);
 BGP_REG=0xe4;
 set_bkg_data(0,64,bb_font);set_bkg_data(64,11,bb_chrome);set_bkg_data(128,24,bb_sunrise);
 ui_clear();ui_header();DISPLAY_ON;
}
static uint8_t icon_slot;
static void browser(uint8_t fresh) {
 uint8_t x,y;
 if(fresh) { ui_init();ui_box(4,14);icon_slot=80; }
 else {icon_slot=240u-icon_slot;fill_bkg_rect(1,5,18,1,0);fill_bkg_rect(0,16,20,1,0);}
 ui_text((20-strlen(labels[selected_test]))/2,5,labels[selected_test]);
 SWITCH_ROM(1);set_bkg_data(icon_slot,48,pictures[selected_test]);
 for(y=0;y<6;++y)for(x=0;x<8;++x)ui_cell(6+x,7+y,icon_slot+y*8+x);
 ui_cell(1,9,70);ui_cell(18,9,71);
 for(x=0;x<4;++x)ui_cell(6+x*2,13,(selected_test&3u)==x?72:73);
 ui_text((20-strlen(details[selected_test]))/2,16,details[selected_test]);
 ui_number(8,3,selected_test+1u);ui_text(9,3,"/8");
}

/* The modal borrows tiles 128-207 and restores both patterns and maps. */
uint8_t bb_exit(void) NONBANKED {
 uint8_t keys,previous=0,choice=0,y,x,sprites;
 bb_keys=joypad();
 if((bb_keys&(J_A|J_B|J_START|J_SELECT))!=(J_A|J_B|J_START|J_SELECT)) return 0;
 sprites=LCDC_REG&2u;HIDE_SPRITES;
 VBK_REG=0;get_bkg_tiles(0,0,20,18,saved_tiles);get_bkg_data(128,80,saved_patterns);
 if(_cpu==CGB_TYPE) {
  VBK_REG=1;get_bkg_tiles(0,0,20,18,saved_attrs);VBK_REG=0;
  vsync();for(x=0;x<8;++x) { BCPS_REG=56u+x; ((uint8_t *)saved_palette)[x]=BCPD_REG; }
  set_bkg_palette(7,1,breakfast);
 }
 set_bkg_data(128,64,bb_font);set_bkg_data(192,10,bb_chrome);
 fill_bkg_rect(2,5,16,8,128);
 for(x=3;x<17;++x) {ui_cell(x,5,192);ui_cell(x,12,192);}
 ui_cell(2,5,194);ui_cell(17,5,195);ui_cell(2,12,196);ui_cell(17,12,197);
 for(y=6;y<12;++y) {ui_cell(2,y,193);ui_cell(17,y,193);}
 {const char *s="CONTINUE";x=5;while(*s)ui_cell(x++,7,(uint8_t)*s++-32u+128u);}
 {const char *s="TEST MENU";x=5;while(*s)ui_cell(x++,10,(uint8_t)*s++-32u+128u);}
 if(_cpu==CGB_TYPE){VBK_REG=1;fill_bkg_rect(2,5,16,8,7);VBK_REG=0;}
 while(joypad())vsync();
 for(;;) {
  ui_cell(3,7,choice?128:199);ui_cell(3,10,choice?199:128);
  vsync();keys=joypad();
  if((keys&~previous)&(J_UP|J_DOWN))choice^=1;
  if((keys&~previous)&J_B){choice=0;break;}
  if((keys&~previous)&J_A)break;
  previous=keys;
 }
 while(joypad())vsync();
 set_bkg_data(128,80,saved_patterns);set_bkg_tiles(0,0,20,18,saved_tiles);
 if(_cpu==CGB_TYPE){VBK_REG=1;set_bkg_tiles(0,0,20,18,saved_attrs);VBK_REG=0;vsync();set_bkg_palette(7,1,saved_palette);}
 if(sprites)SHOW_SPRITES;
 return choice;
}

/* The assembly diagnostic polls its timer with interrupts disabled. */
uint8_t rumble_gate(void) NONBANKED {
 uint8_t leave;
 set_interrupts(VBL_IFLAG);enable_interrupts();
 leave=bb_exit();
 disable_interrupts();IE_REG=0;
 return leave;
}
static void rumble_run(void) {
 SWITCH_ROM(3);
 ((void (*)(void))0x4000u)();
 TAC_REG=0;SC_REG=0;
 *(volatile uint8_t *)0x4000u=0;
 set_interrupts(VBL_IFLAG);enable_interrupts();
 SWITCH_ROM(1);
}
void main(void) {
 uint8_t keys,previous=0,pressed;
 NR52_REG=0;
 DISPLAY_ON;
 browser(1);
#ifdef BB_AUTORUN
 selected_test=BB_AUTORUN;
 if(selected_test==0)platform_run();
 else if(selected_test==1)link_run();
 else if(selected_test==2)rumble_run();
 else if(selected_test==3)audio_run();
   else if(selected_test==4)buttons_run();
   else if(selected_test==5)display_run();
   else if(selected_test==6)sram_run();
   else burn_run();
 browser(1);
#endif
 for(;;) {
  vsync();keys=joypad();pressed=keys&~previous;previous=keys;
  if(pressed&(J_LEFT|J_RIGHT)) {
   selected_test=(selected_test+((pressed&J_RIGHT)?1u:7u))&7u;
   browser(0);
  }
  if(pressed&J_A) {
   while(joypad())vsync();NR52_REG=0;
   if(selected_test==0)platform_run();
   else if(selected_test==1)link_run();
   else if(selected_test==2)rumble_run();
   else if(selected_test==3)audio_run();
   else if(selected_test==4)buttons_run();
   else if(selected_test==5)display_run();
   else if(selected_test==6)sram_run();
   else burn_run();
   NR52_REG=0;browser(1);previous=0;
  }
 }
}
