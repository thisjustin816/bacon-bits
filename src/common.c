#include "bb.h"
#include "crc_table.h"
#include <string.h>
uint8_t bb_fast;
char *ui_decimal(char *out,uint32_t n) {
 char digits[10];uint8_t count=0;
 do {digits[count++]=(char)('0'+n%10UL);n/=10UL;}while(n);
 while(count)*out++=digits[--count];*out=0;return out;
}
uint8_t ui_number(uint8_t x,uint8_t y,uint32_t n) {
 static const uint32_t limit[]={1UL,10UL,100UL,1000UL,10000UL,100000UL,1000000UL,10000000UL,100000000UL,1000000000UL};
 char s[12],*end;uint8_t unit=0,width=19u-x;if(x>=19u)return x;
 while(width<10u && n>=limit[width-(unit!=0)]){
  if(width<3u || unit==3){ui_cell(x,y,'+'-32u);return x+1u;}n/=1000u;++unit;
 }
 end=ui_decimal(s,n);if(unit)*end++=" KMG"[unit];*end=0;ui_text(x,y,s);return x+(uint8_t)(end-s);
}
/* Live readings are rewritten in place and only the cells past the new text
   are blanked. Clearing a field first shows it empty for a frame. */
void ui_pad(uint8_t x,uint8_t y,const char *s,uint8_t width) {
 uint8_t end=x;while(*s && end<x+width)ui_cell(end++,y,(uint8_t)*s++-32u);
 if(end<x+width)fill_bkg_rect(end,y,x+width-end,1,0);
}
void ui_count(uint8_t x,uint8_t y,uint32_t n,uint8_t width) {
 uint8_t end=ui_number(x,y,n);if(end<x+width)fill_bkg_rect(end,y,x+width-end,1,0);
}
void ui_line(uint8_t y,const char *text) {ui_cell(0,y,0);ui_pad(1,y,text,19);}
/* The title and page count sit in the body box's top border, each with a
   blank cell either side so the border never touches a letter. */
void ui_frame(uint8_t bottom,const char *title,const char *page) {
 uint8_t n=strlen(page);
 ui_box(UI_TOP,bottom);ui_cell(1,UI_TOP,0);ui_text(2,UI_TOP,title);ui_cell(2u+strlen(title),UI_TOP,0);
 if(n){ui_cell(17u-n,UI_TOP,0);ui_text(18u-n,UI_TOP,page);ui_cell(18,UI_TOP,0);}
}
void ui_screen(const char *title,const char *page) {ui_init();ui_frame(UI_BOTTOM,title,page);}
/* A settings page redraws only when another screen or page was shown since;
   otherwise its fields are rewritten in place. Returns 1 after a redraw. */
uint8_t ui_page(const char *title,const char *page,uint8_t key) {
 static uint16_t revision;static uint8_t shown=255;
 if(revision==ui_revision && shown==key)return 0;
 ui_screen(title,page);revision=ui_revision;shown=key;return 1;
}
void ui_field(uint8_t row,const char *label,const char *value,uint8_t selected) {
 uint8_t y=UI_FIELD+2u*row;
 ui_cell(1,y,selected?UI_CURSOR:0);ui_pad(2,y,label,9);ui_pad(11,y,value,8);
}
void ui_value(uint8_t row,const char *label,uint32_t value,uint8_t selected) {char s[11];if(value>99999999UL){ui_field(row,label,"99M+",selected);return;}ui_decimal(s,value);ui_field(row,label,s,selected);}
/* The status sits in the bottom border as the title does in the top one.
   A shorter status puts back the border a longer one covered. */
void ui_status(const char *text) {
 static uint16_t revision;static uint8_t shown;
 uint8_t n=strlen(text);
 if(revision!=ui_revision)shown=0;
 if(n){ui_cell(1,UI_BOTTOM,0);ui_text(2,UI_BOTTOM,text);ui_cell(2u+n,UI_BOTTOM,0);}
 if(shown>n)fill_bkg_rect(n?3u+n:1u,UI_BOTTOM,n?shown-n:shown+2u,1,UI_CHROME+0);
 shown=n;revision=ui_revision;
}
/* A reading for the right end of the bottom border, such as a timer. */
void ui_corner(const char *text) {
 static uint16_t revision;static uint8_t shown;
 uint8_t n=strlen(text);
 if(revision!=ui_revision)shown=0;
 if(shown>n)fill_bkg_rect(17u-shown,UI_BOTTOM,shown-n,1,UI_CHROME+0);
 ui_cell(17u-n,UI_BOTTOM,0);ui_text(18u-n,UI_BOTTOM,text);ui_cell(18,UI_BOTTOM,0);
 shown=n;revision=ui_revision;
}
/* A button bounces as it closes, so one released reading proves nothing: the
   screen after a list would take the still-held button as a new press. */
static void ui_release(void) {uint8_t quiet=0;while(quiet<3u){vsync();quiet=joypad()?0:quiet+1u;}}
uint8_t ui_confirm(const char *message) {
 uint8_t key,old=0,yes=0;
 ui_screen("Confirm","");ui_text((20u-strlen(message))/2u,UI_FIELD,message);ui_text(5,9,"No");ui_text(5,12,"Yes");
 ui_release();
 for(;;){vsync();key=joypad();ui_cell(3,9,yes?0:UI_CURSOR);ui_cell(3,12,yes?UI_CURSOR:0);
  if((key&~old)&(J_UP|J_DOWN))yes^=1u;
  if((key&~old)&J_B){yes=0;break;}if((key&~old)&J_A)break;old=key;}
 ui_release();return yes;
}
uint16_t bb_rom_crc(uint8_t bank,uint16_t offset,uint16_t count,uint16_t crc) NONBANKED {
 uint8_t saved=CURRENT_BANK,value;uint16_t address;
 if(bank)SWITCH_ROM(bank);
 while(count--){address=bank?0x4000u+offset:offset;
  if(!(bank==0 && (offset==0x14eu || offset==0x14fu)) && !(bank==7 && offset<16u)) {
   value=*(const uint8_t *)address;crc=(crc<<8)^crc_table[(crc>>8)^value];
  }++offset;
 }
 SWITCH_ROM(saved);return crc;
}
void bb_cpu(uint8_t fast) NONBANKED {
 uint8_t mask;
 if(_cpu!=CGB_TYPE){bb_fast=0;return;}
 bb_fast=KEY1_REG>>7;if(bb_fast==!!fast)return;
 mask=IE_REG;disable_interrupts();IE_REG=0;IF_REG=0;P1_REG=0x30;KEY1_REG|=1;
 __asm .db 0x10,0x00 __endasm;
 bb_fast=KEY1_REG>>7;IE_REG=mask;enable_interrupts();
}

uint8_t ui_presets(const char *title,const char *const *names,const char *const *notes,uint8_t seen) {
 uint8_t i,pick=seen?0:1,key,old=0,n;
 ui_init();ui_frame(UI_BOTTOM,title,"");
 for(i=0;i<5;++i)ui_text(3,UI_FIELD+i*2,i?names[i]:(seen?"Continue":"Manual"));
 ui_cell(1,UI_FIELD+pick*2,UI_CURSOR);ui_text(1,UI_DETAIL,notes[pick]);ui_release();
 for(;;){vsync();key=joypad();n=key&~old;old=key;
  if(n&J_B){pick=255;break;}if(n&J_A)break;
  if(n&(J_UP|J_DOWN)){ui_cell(1,UI_FIELD+pick*2,0);pick=(pick+((n&J_UP)?4u:1u))%5u;ui_cell(1,UI_FIELD+pick*2,UI_CURSOR);ui_line(UI_DETAIL,notes[pick]);}
 }ui_release();return pick;
}

uint16_t bb_frame(void) NONBANKED {uint16_t value;CRITICAL {value=sys_time;}return value;}

/* MBC5 drives the motor from bit 3 of the SRAM bank register. The VBlank
   handler keeps the bank the main loop selected, so SRAM checks can run
   while the motor pulses. It must stay in bank 0: Burn In maps other ROM
   banks while it checksums them. */
uint8_t bb_ram_bank,bb_rumble_bit;
static uint8_t rumble_frames,rumble_phase;
static void rumble_tick(void) NONBANKED {
 if(++rumble_phase>=60u)rumble_phase=0;
 bb_rumble_bit=rumble_phase<rumble_frames?8u:0u;
 *(volatile uint8_t *)0x4000u=bb_ram_bank|bb_rumble_bit;
}
void bb_rumble_start(uint8_t frames) NONBANKED {rumble_frames=frames;rumble_phase=59;CRITICAL{add_VBL(rumble_tick);}}
void bb_rumble_stop(void) NONBANKED {CRITICAL{remove_VBL(rumble_tick);}bb_rumble_bit=0;*(volatile uint8_t *)0x4000u=bb_ram_bank;}

#undef joypad
uint8_t bb_joypad(void) NONBANKED {ui_reveal();return joypad();}
