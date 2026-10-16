#include "bb.h"
#include "crc_table.h"
uint8_t bb_fast;
char *ui_decimal(char *out,uint32_t n) {
 char digits[10];uint8_t count=0;
 do {digits[count++]=(char)('0'+n%10UL);n/=10UL;}while(n);
 while(count)*out++=digits[--count];*out=0;return out;
}
void ui_number(uint8_t x,uint8_t y,uint32_t n) {char s[11];ui_decimal(s,n);ui_text(x,y,s);}
void ui_screen(const char *title,const char *page) {ui_init();ui_text(1,4,title);ui_text(16,4,page);ui_box(5,14);}
void ui_field(uint8_t row,const char *label,const char *value,uint8_t selected) {
 uint8_t y=6u+2u*row;fill_bkg_rect(1,y,18,1,0);
 ui_cell(1,y,selected?71:0);ui_text(2,y,label);ui_text(11,y,value);
}
void ui_value(uint8_t row,const char *label,uint32_t value,uint8_t selected) {char s[11];if(value>99999999UL){ui_field(row,label,"99M+",selected);return;}ui_decimal(s,value);ui_field(row,label,s,selected);}
void ui_status(const char *text) {fill_bkg_rect(0,16,20,1,0);ui_text(1,16,text);}
uint8_t ui_confirm(const char *message) {
 uint8_t key,old=0,yes=0;
 ui_screen("CONFIRM","");ui_text(2,6,message);ui_text(5,9,"NO");ui_text(5,12,"YES");
 while(joypad())vsync();
 for(;;){vsync();key=joypad();ui_cell(3,9,yes?0:71);ui_cell(3,12,yes?71:0);
  if((key&~old)&(J_UP|J_DOWN))yes^=1u;
  if((key&~old)&J_B){yes=0;break;}if((key&~old)&J_A)break;old=key;}
 while(joypad())vsync();return yes;
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
 ui_init();ui_text(1,4,title);ui_box(5,16);
 for(i=0;i<5;++i)ui_text(3,6+i*2,i?names[i]:(seen?"CONTINUE":"MANUAL"));
 ui_cell(1,6+pick*2,71);ui_text(1,17,notes[pick]);while(joypad())vsync();
 for(;;){vsync();key=joypad();n=key&~old;old=key;
  if(n&J_B){pick=255;break;}if(n&J_A)break;
  if(n&(J_UP|J_DOWN)){ui_cell(1,6+pick*2,0);pick=(pick+((n&J_UP)?4u:1u))%5u;ui_cell(1,6+pick*2,71);fill_bkg_rect(0,17,20,1,0);ui_text(1,17,notes[pick]);}
 }while(joypad())vsync();return pick;
}

uint16_t bb_frame(void) NONBANKED {uint16_t value;CRITICAL {value=sys_time;}return value;}
