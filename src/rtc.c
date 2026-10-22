#pragma bank 1
#include "bb.h"
#include <string.h>
uint8_t rtc_data[5],rtc_saved[5],rtc_valid,rtc_dirty,rtc_running,rtc_mode;
uint16_t rtc_ticks,rtc_latch_errors,rtc_halt_errors,rtc_observations,rtc_window=10,rtc_day=511;
uint8_t rtc_rollover_seen;
uint8_t rtc_hour=23,rtc_minute=59,rtc_second=58,rtc_seed_halt,rtc_seed_carry;
static uint8_t seen,held[5],journal[16],last_page=255;
static uint16_t started;
static const char *const presets[]={"","Live clock","Latch hold","Halt check","Day rollover"};
static const char *const notes[]={"Keep settings","Read only / 10 sec","Hold latch / 3 sec","Temporary halt","511 days 23:59:58"};
static void spacing(void) __naked {__asm
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 ret
 __endasm;}
static uint8_t fetch(uint8_t reg) __naked {reg;__asm
 ld (#0x4000),a
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 nop
 ld a,(#0xa000)
 ret
 __endasm;}
static void enable(void){*(volatile uint8_t *)0x0000=0x0a;spacing();}
static void close(void){*(volatile uint8_t *)0x4000=0;*(volatile uint8_t *)0x0000=0;}
void rtc_read(uint8_t latch) BANKED {uint8_t i;enable();
 if(latch){*(volatile uint8_t *)0x6000=0;spacing();*(volatile uint8_t *)0x6000=1;spacing();}
 for(i=0;i<5;++i){rtc_data[i]=fetch(8+i);spacing();}close();
 rtc_valid=rtc_data[0]<60 && rtc_data[1]<60 && rtc_data[2]<24;
}
static void store(uint8_t reg,uint8_t value){*(volatile uint8_t *)0x4000=reg;spacing();*(volatile uint8_t *)0xa000=value;spacing();}
static void write_clock(const uint8_t *data){uint8_t i;enable();store(12,data[4]|64);for(i=0;i<4;++i)store(8+i,data[i]);store(12,data[4]&0xc1);close();}
static uint8_t check_journal(void){uint8_t i,c=0x96;for(i=0;i<15;++i)c=(c<<1|c>>7)^journal[i];return c;}
static uint8_t journal_load(void){uint8_t i;enable();*(volatile uint8_t *)0x4000=0;for(i=0;i<16;++i)journal[i]=*(volatile uint8_t *)(0xbff0u+i);close();
 if(journal[0]!='R'||journal[1]!='T'||journal[2]!=1||journal[15]!=check_journal())return 0;
 for(i=0;i<5;++i)rtc_saved[i]=journal[3+i];return 1;
}
static void journal_save(void){uint8_t i;memset(journal,0,16);journal[0]='R';journal[1]='T';journal[2]=1;for(i=0;i<5;++i)journal[3+i]=rtc_saved[i];journal[15]=check_journal();
 enable();*(volatile uint8_t *)0x4000=0;*(volatile uint8_t *)0xbff0=0;for(i=1;i<16;++i)*(volatile uint8_t *)(0xbff0u+i)=journal[i];*(volatile uint8_t *)0xbff0='R';close();}
static void journal_clear(void){enable();*(volatile uint8_t *)0x4000=0;*(volatile uint8_t *)0xbff0=0;close();}
static uint32_t seconds(const uint8_t *data){return (((uint32_t)data[3]+((uint16_t)(data[4]&1u)<<8))*24u+data[2])*3600u+(uint16_t)data[1]*60u+data[0];}
static void advance(uint8_t *data,uint16_t elapsed){uint32_t total;uint16_t day;uint8_t flags=data[4]&0xc0;
 if(flags&64)return;total=seconds(data)+elapsed;day=total/86400UL;if(day>511)flags|=128;day&=511;data[3]=day;data[4]=flags|(day>>8);total%=86400UL;data[2]=total/3600u;total%=3600u;data[1]=total/60u;data[0]=total%60u;}
void rtc_restore(void) BANKED {uint16_t elapsed;if(!rtc_dirty)return;
 elapsed=(uint32_t)(uint16_t)(bb_frame()-started)*70224UL/4194304UL;advance(rtc_saved,elapsed);write_clock(rtc_saved);journal_clear();rtc_dirty=0;
}
static void clear_results(void){rtc_ticks=rtc_latch_errors=rtc_halt_errors=rtc_observations=0;rtc_rollover_seen=0;}
static void finish(void){
 if(rtc_mode==1){rtc_read(1);if(rtc_valid && rtc_data[0]!=held[0])++rtc_ticks;}
 rtc_running=0;rtc_restore();rtc_read(1);
}
static uint8_t start(void){uint8_t seed[5];rtc_read(1);if(!rtc_valid)return 0;
 if(rtc_mode>=2){if(!ui_confirm(rtc_mode==2?"Halt clock test?":"Change RTC time?"))return 0;
  rtc_read(1);memcpy(rtc_saved,rtc_data,5);journal_save();rtc_dirty=1;started=bb_frame();
  memcpy(seed,rtc_data,5);
  if(rtc_mode==2)seed[4]|=64;
  else {seed[0]=rtc_second;seed[1]=rtc_minute;seed[2]=rtc_hour;seed[3]=rtc_day;seed[4]=(rtc_day>>8)|(rtc_seed_halt?64:0)|(rtc_seed_carry?128:0);}
  write_clock(seed);rtc_read(1);
 }
 memcpy(held,rtc_data,5);clear_results();return 1;
}
static void pair(uint8_t x,uint8_t y,uint8_t n){ui_cell(x,y,'0'-32+n/10);ui_cell(x+1,y,'0'-32+n%10);}
static void view(uint8_t page,uint8_t row){
 /* SDCC 4.5 passes the wrong upper word when a ternary picks this 16-bit
    count in a call that also takes a ternary string, so it gets a local. */
 uint16_t changed=rtc_mode==2?rtc_halt_errors:rtc_latch_errors;
 if(last_page!=page){ui_screen("Clock",page?"Set":"");last_page=page;}
 if(!page){ui_hardware(2,rtc_data[0]&3u);pair(10,7,rtc_data[2]%24);ui_text(12,7,":");pair(13,7,rtc_data[1]%60);ui_text(15,7,":");pair(16,7,rtc_data[0]%60);
  ui_text(10,9,"Day");ui_count(14,9,(uint16_t)rtc_data[3]+((uint16_t)(rtc_data[4]&1u)<<8),3);ui_pad(10,11,!rtc_valid?"Unknown":rtc_data[4]&64?"Halted":"Ticking",8);ui_line(15,!rtc_valid?"Flags unknown":rtc_data[4]&128?"Carry set":"Carry clear");
 }else if(page==1){ui_field(0,"Mode",rtc_mode==0?"Live":rtc_mode==1?"Latch":rtc_mode==2?"Halt":"Rollover",row==0);ui_value(1,"Window s",rtc_window,row==1);ui_value(2,"Seed day",rtc_day,row==2);ui_value(3,rtc_mode==1 || rtc_mode==2?"Samples":"Ticks",rtc_mode==1 || rtc_mode==2?rtc_observations:rtc_ticks,0);}
 else if(page==2){ui_value(0,"Hour",rtc_hour,row==0);ui_value(1,"Minute",rtc_minute,row==1);ui_value(2,"Second",rtc_second,row==2);ui_field(3,"Halt",rtc_seed_halt?"Yes":"No",row==3);}
 else {ui_field(0,"Carry",rtc_seed_carry?"Set":"Clear",row==0);ui_value(1,"Changed",changed,0);ui_value(2,"Flags",rtc_data[4],0);ui_field(3,"Restore",rtc_dirty?"Pending":"Clean",0);}
 ui_status(!rtc_valid?"Invalid RTC data":rtc_halt_errors?"Halt changed":rtc_latch_errors?"Latch changed":rtc_rollover_seen?"Rollover seen":rtc_running?"Observing":rtc_mode==1 && rtc_observations>=2?"Latch held":rtc_mode==2 && rtc_observations>=2?"Halt held":rtc_ticks?"Tick observed":rtc_mode==3?"No wrap yet":(rtc_data[4]&64)?"RTC halted":"No tick yet");
}
void rtc_run(void) BANKED {
 last_page=255;
 uint8_t preset,key,old=0,n,page=0,row=0,i,last_second,was_fast=KEY1_REG>>7;uint16_t since,updated;
 bb_cpu(0);rtc_running=rtc_dirty=0;
 if(journal_load()){if(ui_confirm("Restore saved RTC?")){write_clock(rtc_saved);journal_clear();}else{bb_cpu(was_fast);return;}}
 preset=ui_presets("Clock presets",presets,notes,seen);if(preset==255){bb_cpu(was_fast);return;}seen=1;
 if(preset){rtc_mode=preset-1;rtc_window=preset==2?3:10;rtc_day=511;rtc_hour=23;rtc_minute=59;rtc_second=58;rtc_seed_halt=rtc_seed_carry=0;clear_results();}
 rtc_read(1);last_second=rtc_data[0];updated=bb_frame();view(page,row);since=updated;
 for(;;){vsync();key=joypad();n=key&~old;old=key;
  if(n&J_B)break;
  if(n&J_SELECT){page=(page+1u)&3u;row=0;}
  if(page && !rtc_running){if(n&J_UP)row=(row+3u)&3u;if(n&J_DOWN)row=(row+1u)&3u;
   if(n&(J_LEFT|J_RIGHT)){int8_t add=(n&J_RIGHT)?1:-1;
    if(page==1){if(row==0){rtc_mode=(rtc_mode+4u+add)&3u;clear_results();}else if(row==1){if(add>0 && rtc_window<120)++rtc_window;if(add<0 && rtc_window>1)--rtc_window;}else if(row==2){if(add>0 && rtc_day<511)++rtc_day;if(add<0 && rtc_day)--rtc_day;}}
    else if(page==2){uint8_t *v=row==0?&rtc_hour:row==1?&rtc_minute:&rtc_second;if(row==3)rtc_seed_halt^=1;else if((add>0 && *v<(row==0?23:59))||(add<0 && *v))*v+=add;}
    else if(row==0)rtc_seed_carry^=1;
   }
  }
  if(n&J_A){if(rtc_running){finish();}else{rtc_running=start();since=bb_frame();last_second=rtc_data[0];}view(page,row);}
  if((uint16_t)(bb_frame()-updated)>=30){updated=bb_frame();rtc_read(!(rtc_running && rtc_mode==1));
   if(rtc_running){++rtc_observations;if(rtc_data[0]!=last_second){++rtc_ticks;last_second=rtc_data[0];}
    if(rtc_mode==2 && memcmp(rtc_data,held,5))++rtc_halt_errors;
    if(rtc_mode==3 && seconds(rtc_data)<seconds(held) && (rtc_data[4]&128))rtc_rollover_seen=1;
    if(rtc_mode==1)for(i=0;i<5;++i)if(rtc_data[i]!=held[i]){if(rtc_latch_errors<65535)++rtc_latch_errors;break;}
    if((uint16_t)(updated-since)>=(uint16_t)rtc_window*60u){finish();}
   }
   view(page,row);
  }else if(n)view(page,row);
 }
 rtc_restore();close();bb_cpu(was_fast);
}
