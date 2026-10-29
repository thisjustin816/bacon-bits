#include "bb.h"
#include "art.h"
#include "logo.h"
#include <string.h>

uint8_t selected_test,bb_keys,bb_raw_rumble;
uint16_t ui_revision;
uint8_t bb_tiles_dirty=UI_TILES_ALL,bb_cover_dirty=1,bb_header_dirty;
static uint8_t covered;
/* A blank window over rows 3-17 hides a screen while it is rebuilt, so a
   change shows the old screen, then the finished new one. */
void ui_cover(void) NONBANKED {
 if(bb_cover_dirty){LCDC_REG|=0x40u;fill_win_rect(0,0,20,15,0);if(_cpu==CGB_TYPE){VBK_REG=1;fill_win_rect(0,0,20,15,0);VBK_REG=0;}bb_cover_dirty=0;}
 LCDC_REG|=0x40u;WX_REG=7;WY_REG=24;
 /* Inside VBlank the change already lands on a frame boundary. */
 if(LY_REG<144u)vsync();
 SHOW_WIN;covered=1;
}
void ui_reveal(void) NONBANKED {if(covered){if(LY_REG<144u)vsync();HIDE_WIN;covered=0;}}
static uint8_t saved_tiles[360], saved_attrs[360];
static palette_color_t saved_palette[4];
static const palette_color_t breakfast[16] = {
 RGB(31,30,27),RGB(31,24,6),RGB(23,9,7),RGB(8,5,4),
 RGB(19,26,30),RGB(31,30,27),RGB(23,9,7),RGB(8,5,4),
 RGB(31,30,27),RGB(28,27,23),RGB(23,9,7),RGB(8,5,4),
 RGB(31,24,6),RGB(31,30,27),RGB(23,9,7),RGB(8,5,4)
};
#define BRAND_NAME "Bacon Bit Bench"
#ifdef BB_MBC3
#define CARD_2 "Clock"
#else
#define CARD_2 "Rumble"
#endif
#define CARD_0 "Platform"
#define CARD_1 "Link"
#define CARD_3 "Audio"
#define CARD_4 "Buttons"
#define CARD_5 "Display"
#define CARD_6 "SRAM"
#define CARD_7 "Burn in"
#define CARD_8 "Cart LED"
#define CARD_9 "Infrared"
#define CARD_10 "Flicker"
#define CARD_11 "Printer"
static const char * const labels[] = {CARD_0,CARD_1,CARD_2,CARD_3,CARD_4,CARD_5,CARD_6,CARD_7,CARD_8,CARD_9,CARD_10,CARD_11};
#define CARDS ((uint8_t)(sizeof(labels)/sizeof(labels[0])))
/* Menu-only punctuation slots hold half-cell shifts for odd-length labels.
   ui_init reloads the complete font before entering any test or dialog. */
static const uint8_t label_slots[]={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,26,27,28,29,30,31,32,59,60};
/* An odd label of n letters borrows n+1 slots; each browser page must fit. */
#define LABEL_SLOTS(s) (((sizeof(s)-1u)&1u)?sizeof(s):0u)
typedef char label_slots_fit[(LABEL_SLOTS(CARD_0)+LABEL_SLOTS(CARD_1)+LABEL_SLOTS(CARD_2)+LABEL_SLOTS(CARD_3)<=sizeof(label_slots)
 && LABEL_SLOTS(CARD_4)+LABEL_SLOTS(CARD_5)+LABEL_SLOTS(CARD_6)+LABEL_SLOTS(CARD_7)<=sizeof(label_slots)
 && LABEL_SLOTS(CARD_8)+LABEL_SLOTS(CARD_9)+LABEL_SLOTS(CARD_10)+LABEL_SLOTS(CARD_11)<=sizeof(label_slots))?1:-1];
void ui_cell(uint8_t x,uint8_t y,uint8_t tile) {set_bkg_tile_xy(x,y,tile);}
void ui_text(uint8_t x,uint8_t y,const char *s) {while(*s) ui_cell(x++,y,(uint8_t)*s++-32u);}
/* On Color the header is the logo, drawn from VRAM bank 1; on monochrome
   it is the name in the shared font. */
static void logo(void) {
 VBK_REG=1;fill_bkg_rect(0,0,20,3,0x09);VBK_REG=0;set_bkg_tiles(0,0,20,3,bb_logo_map);
}
void ui_clear(void) {
 uint8_t y;
 /* The heading stays resident while the body is redrawn: clearing its map
    cells would expose a blank header for several LCD frames. A full-screen
    test may have drawn over it, so the logo is put back first. */
 if(_cpu==CGB_TYPE)logo();
 for(y=3;y!=18;++y) fill_bkg_rect(0,y,20,1,0);
 if(_cpu==CGB_TYPE) {VBK_REG=1;fill_bkg_rect(0,3,20,15,0);VBK_REG=0;}
}
void ui_box(uint8_t top,uint8_t bottom) {
 uint8_t y;
 fill_bkg_rect(1,top,18,1,(UI_CHROME+0));fill_bkg_rect(1,bottom,18,1,(UI_CHROME+0));
 ui_cell(0,top,(UI_CHROME+2));ui_cell(19,top,(UI_CHROME+3));ui_cell(0,bottom,(UI_CHROME+4));ui_cell(19,bottom,(UI_CHROME+5));
 for(y=top+1;y<bottom;++y) {ui_cell(0,y,(UI_CHROME+1));ui_cell(19,y,(UI_CHROME+1));}
}
void ui_header(void) {
 if(_cpu==CGB_TYPE){logo();VBK_REG=1;fill_bkg_rect(0,16,20,2,2);VBK_REG=0;return;}
 fill_bkg_rect(0,0,20,1,0);fill_bkg_rect(0,2,20,1,0);fill_bkg_rect(0,1,2,1,0);fill_bkg_rect(17,1,3,1,0);
 ui_text(2,1,BRAND_NAME);
}
/* A full-screen view draws over the header. Put it back while the view still
   shows, so the cover never rises over a header from the view. */
static void restore_header(void) {
 if(!bb_header_dirty)return;
 bb_header_dirty=0;
 /* Starting in VBlank, the writes finish before the beam reaches the header. */
 vsync();
 /* The ramp pattern replaces palette 1, which the logo uses. */
 if(_cpu==CGB_TYPE){set_bkg_palette(1,1,breakfast+4);logo();}else ui_header();
}
void ui_init(void) {
 ++ui_revision;
 uint8_t i;
 restore_header();
 HIDE_SPRITES;SHOW_BKG;
 if(!bb_raw_rumble)for(i=0;i!=40;++i)move_sprite(i,0,0);
 SCX_REG=SCY_REG=0;VBK_REG=0;LCDC_REG|=0x10u;
 ui_cover();
 if(_cpu==CGB_TYPE) set_bkg_palette(0,4,breakfast);
 BGP_REG=0xe4;
 /* Reloading unchanged tiles keeps the body blank for frames, so only what
    was overwritten is restored. */
 ui_clear();
 if(bb_tiles_dirty&UI_TILES_ALL){set_bkg_data(0,UI_FONT_COUNT,bb_font);set_bkg_data(UI_CHROME,11,bb_chrome);set_bkg_data(UI_PASS,3,bb_probes);}
 else if(bb_tiles_dirty){for(i=0;i!=sizeof(label_slots);++i)set_bkg_data(label_slots[i],1,bb_font+label_slots[i]*16u);set_bkg_data(UI_FOCUS_EXTRA,4,bb_font+UI_FOCUS_EXTRA*16u);}
 bb_tiles_dirty=0;
 ui_header();ui_scene_reset();DISPLAY_ON;
}
static const uint8_t blank_tile[16];
static void menu_label(uint8_t item,const char *label,uint8_t *borrowed) {
 uint8_t count=strlen(label),x=(item&1u?10u:0u)+(10u-count)/2u,y=(item&2u)?15:9,i,r,tile[16];
 if(!(count&1u)){ui_text(x,y,label);return;}
 for(i=0;i<=count;++i){
  /* Row pointers keep the per-row work to a shift and an OR. */
  {const uint8_t *l=i?bb_font+((uint16_t)((uint8_t)label[i-1]-32u)<<4):blank_tile,*rt=i<count?bb_font+((uint16_t)((uint8_t)label[i]-32u)<<4):blank_tile;
   for(r=0;r<16;++r)tile[r]=(uint8_t)(l[r]<<4)|(rt[r]>>4);}
  set_bkg_data(label_slots[*borrowed],1,tile);bb_tiles_dirty|=UI_TILES_BORROWED;ui_cell(x+i,y,label_slots[*borrowed]);++*borrowed;
 }
}
static void browser(uint8_t fresh) {
 uint8_t i,at,borrowed=0,group=selected_test/4u,scene=group==2?6:group==1?5:
#ifdef BB_MBC3
 7;
#else
 0;
#endif
 if(fresh)ui_init();
 ui_scene(scene,(uint8_t)(bb_frame()/12u)&3u);
 for(i=0;i<4;++i){
  at=group*4u+i;if(at>=CARDS)continue;if(fresh)menu_label(i,labels[at],&borrowed);
 }
 ui_focus(selected_test&3u,fresh);
 if(fresh){
  fill_bkg_rect(0,17,20,1,0);ui_text(7,17,group==2?"3 of 3":group==1?"2 of 3":"1 of 3");
  /* A redraw outlasts one animation pose, so show the current one when uncovering. */
  ui_scene(scene,(uint8_t)(bb_frame()/12u)&3u);ui_reveal();
 }
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
 fill_bkg_rect(1,5,18,8,0);
 for(x=2;x<18;++x) {ui_cell(x,5,(UI_CHROME+0));ui_cell(x,12,(UI_CHROME+0));}
 ui_cell(1,5,(UI_CHROME+2));ui_cell(18,5,(UI_CHROME+3));ui_cell(1,12,(UI_CHROME+4));ui_cell(18,12,(UI_CHROME+5));
 for(y=6;y<12;++y) {ui_cell(1,y,(UI_CHROME+1));ui_cell(18,y,(UI_CHROME+1));}
 {const char *s="Continue";x=5;while(*s)ui_cell(x++,7,(uint8_t)*s++-32u);}
 {const char *s="Test menu";x=5;while(*s)ui_cell(x++,10,(uint8_t)*s++-32u);}
 if(_cpu==CGB_TYPE){VBK_REG=1;fill_bkg_rect(1,5,18,8,7);VBK_REG=0;}
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
/* The assembly program may load its own tiles, so restore every UI tile around it. */
static void rumble_run(void) {
 bb_tiles_dirty=UI_TILES_ALL;rumble_ui_reset();bb_raw_rumble=1;
 SWITCH_ROM(3);
 ((void (*)(void))0x4000u)();
 bb_raw_rumble=0;bb_tiles_dirty=UI_TILES_ALL;TAC_REG=0;SC_REG=0;
 *(volatile uint8_t *)0x4000u=0;
 set_interrupts(VBL_IFLAG);enable_interrupts();
 SWITCH_ROM(1);
}
void main(void) {
 uint8_t keys,previous=0,pressed,phase=255,last_group=0;
 NR52_REG=0;
 /* Nothing else writes tile data to VRAM bank 1, so the logo loads once.
    Without a boot ROM the LCD starts with $9000 tile addressing, so select
    $8000 first or the tiles land where the map never reads them. */
 LCDC_REG|=0x10u;
 if(_cpu==CGB_TYPE){if(LCDC_REG&0x80u)vsync();set_bkg_palette(0,4,breakfast);VBK_REG=1;set_bkg_data(0,BB_LOGO_TILES,bb_logo_tiles);VBK_REG=0;}
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
   else if(selected_test==8)led_run();else if(selected_test==9)ir_run();else if(selected_test==10)flicker_run();else printer_run();
 browser(1);
#endif
 for(;;) {
  vsync();keys=joypad();pressed=keys&~previous;previous=keys;
  if(pressed&(J_UP|J_DOWN)){if(pressed&J_DOWN){selected_test+=2u;if(selected_test>=CARDS)selected_test&=1u;}else selected_test=selected_test>=2u?selected_test-2u:selected_test+CARDS-2u;browser((selected_test/4u)!=last_group);}
  if(pressed&(J_LEFT|J_RIGHT)) {
   selected_test=(selected_test+((pressed&J_RIGHT)?1u:CARDS-1u))%CARDS;
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
   else if(selected_test==8)led_run();else if(selected_test==9)ir_run();else if(selected_test==10)flicker_run();else printer_run();
   NR52_REG=0;browser(1);previous=0;
  }
 }
}
